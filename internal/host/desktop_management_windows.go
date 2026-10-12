//go:build windows

package host

import (
	"bufio"
	"context"
	"errors"
	"fmt"
	"io"
	"os"
	"strconv"
	"time"

	"golang.org/x/sys/windows"
	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/ops/supervisor"
)

const DesktopManagementProtocol = "researchos-desktop-management/1"
const DesktopManagementMaxFrame = 64 << 10

// This channel exists only when the privileged parent launched control with
// dedicated inherited pipes. It is never served on HTTP or the Native3 pipe.
type DesktopManagementFrame struct {
	Protocol    string `json:"protocol"`
	MessageID   string `json:"message_id"`
	Operation   string `json:"operation"`
	HostID      string `json:"host_id"`
	ProjectID   string `json:"project_id,omitempty"`
	SessionID   string `json:"session_id,omitempty"`
	ModelRef    string `json:"model_config_ref,omitempty"`
	RequestID   string `json:"request_id,omitempty"`
	RequestHash string `json:"request_hash,omitempty"`
}

type DesktopManagement struct {
	host          *Host
	service       *domain.Service
	coordinator   *domain.RuntimeCoordinator
	apiURL        string
	installation  RuntimeVerifierInstallation
	input, output *os.File
	parent, self  supervisor.ProcessIdentity
	shutdown      func(context.Context) error
}

// NewDesktopManagement captures the real OS parent before serving any frame.
// No PID, executable path, authority token or key comes from a wire field.
func NewDesktopManagement(h *Host, s *domain.Service, c *domain.RuntimeCoordinator, apiURL string, install RuntimeVerifierInstallation, input, output *os.File, shutdown func(context.Context) error) (*DesktopManagement, error) {
	if h == nil || s == nil || c == nil || input == nil || output == nil {
		return nil, errors.New("managed composition unavailable")
	}
	for _, f := range []*os.File{input, output} {
		kind, e := windows.GetFileType(windows.Handle(f.Fd()))
		if e != nil || kind != windows.FILE_TYPE_PIPE {
			return nil, errors.New("dedicated inherited pipe transport required")
		}
	}
	parent, e := supervisor.ObserveProcess(uint32(os.Getppid()))
	if e != nil {
		return nil, e
	}
	self, e := supervisor.ObserveProcess(uint32(os.Getpid()))
	if e != nil {
		return nil, e
	}
	d := &DesktopManagement{host: h, service: s, coordinator: c, apiURL: apiURL, installation: install, input: input, output: output, parent: parent, self: self, shutdown: shutdown}
	if e = d.verifyParent(); e != nil {
		return nil, e
	}
	if e = verifyRuntimeVerifierImage(install); e != nil {
		return nil, e
	}
	return d, nil
}

func (d *DesktopManagement) verifyParent() error {
	now, e := supervisor.ObserveProcess(d.parent.PID)
	if e != nil || now != d.parent || uint32(os.Getppid()) != d.parent.PID {
		return errors.New("original Desktop parent process identity unavailable")
	}
	peer, e := d.host.peerLookup(d.parent.PID)
	if e != nil || !d.host.Identity().SameUser(peer) {
		return ErrHostIdentity
	}
	return nil
}

func decodeDesktopManagement(raw []byte) (DesktopManagementFrame, error) {
	var f DesktopManagementFrame
	if len(raw) < 1 || len(raw) > DesktopManagementMaxFrame {
		return f, errors.New("bounded management frame required")
	}
	if e := decodeRuntimeManaged(raw, &f); e != nil {
		return f, e
	}
	if f.Protocol != DesktopManagementProtocol || f.MessageID == "" || len(f.MessageID) > 128 || f.HostID == "" {
		return f, errors.New("management protocol, message and exact Host required")
	}
	switch f.Operation {
	case "PREPARE":
		if f.ProjectID == "" || f.SessionID == "" || f.ModelRef == "" || f.RequestID != "" || f.RequestHash != "" {
			return f, errors.New("PREPARE requires only original project, session and model")
		}
	case "CONFIRM", "STATUS":
		if f.ProjectID == "" || f.RequestID == "" || f.RequestHash == "" || f.SessionID != "" || f.ModelRef != "" {
			return f, errors.New("exact prepared request identity required")
		}
	case "SHUTDOWN":
		if f.ProjectID != "" || f.SessionID != "" || f.ModelRef != "" || f.RequestID != "" || f.RequestHash != "" {
			return f, errors.New("SHUTDOWN accepts no execution scope")
		}
	default:
		return f, errors.New("unsupported private management operation")
	}
	return f, nil
}

func (d *DesktopManagement) write(value domain.Object) error {
	raw := domain.Bytes(value)
	if len(raw) > DesktopManagementMaxFrame {
		return errors.New("management response exceeded frame limit")
	}
	_, e := d.output.Write(append(raw, '\n'))
	return e
}

// Serve processes one explicit action at a time. Once CONFIRM is admitted the
// host context (not pipe lifetime) owns settlement. EOF cannot cancel a sent
// effect, mint another request, restart control, or erase its durable result.
func (d *DesktopManagement) Serve(ctx context.Context) error {
	if e := d.verifyParent(); e != nil {
		return e
	}
	identity := func(p supervisor.ProcessIdentity) domain.Object {
		return domain.Object{"PID": p.PID, "CreatedNS": strconv.FormatInt(p.CreatedNS, 10), "ImageSHA256": p.ImageSHA256}
	}
	if e := d.write(domain.Object{"protocol": DesktopManagementProtocol, "kind": "READY", "host_id": d.host.InstanceID(), "control_process": identity(d.self), "parent_process": identity(d.parent), "mode": "IN_PLACE", "confirmation_ttl_seconds": 60}); e != nil {
		return e
	}
	scanner := bufio.NewScanner(d.input)
	scanner.Buffer(make([]byte, 4096), DesktopManagementMaxFrame+1)
	done := make(chan struct{})
	defer close(done)
	go func() {
		select {
		case <-ctx.Done():
			d.input.Close()
		case <-done:
		}
	}()
	for scanner.Scan() {
		if e := ctx.Err(); e != nil {
			return e
		}
		if e := d.verifyParent(); e != nil {
			return e
		}
		frame, e := decodeDesktopManagement(scanner.Bytes())
		if e != nil {
			return fmt.Errorf("management frame rejected: %w", e)
		}
		if frame.HostID != d.host.InstanceID() {
			return errors.New("management Host identity changed")
		}
		result, e := d.handle(ctx, frame)
		reply := domain.Object{"protocol": DesktopManagementProtocol, "message_id": frame.MessageID, "operation": frame.Operation, "host_id": d.host.InstanceID(), "kind": "RESULT", "result": result}
		if e != nil {
			reply["kind"] = "ERROR"
			reply["error"] = domain.Object{"code": "MANAGEMENT_REJECTED", "message": e.Error()}
		}
		if writeErr := d.write(reply); writeErr != nil {
			return writeErr
		}
		if frame.Operation == "SHUTDOWN" && e == nil {
			return nil
		}
	}
	if e := scanner.Err(); e != nil {
		return e
	}
	return io.EOF
}

func (d *DesktopManagement) handle(ctx context.Context, f DesktopManagementFrame) (domain.Object, error) {
	if f.Operation == "SHUTDOWN" {
		if d.shutdown == nil {
			return nil, errors.New("safe shutdown unavailable")
		}
		return domain.Object{"state": "SHUTDOWN_ACCEPTED"}, d.shutdown(ctx)
	}
	if _, e := d.host.reverify(); e != nil {
		return nil, e
	}
	owner := d.host.boundPrincipal()
	if owner == "" {
		return nil, ErrNoOwner
	}
	metadata, e := d.host.ConfigurationMetadata(ctx, owner, "", nil)
	if e != nil || metadata.OwnerHost != f.HostID {
		return nil, ErrHostIdentity
	}
	token, e := d.service.IssueCredential(ctx, owner, time.Minute)
	if e != nil {
		return nil, e
	}
	defer d.host.revokeCredentialByHash(context.Background(), owner, domain.Digest([]byte(token)))
	switch f.Operation {
	case "PREPARE":
		if e = d.coordinator.PrepareLocalRuntimeOffline(ctx); e != nil {
			return nil, e
		}
		request, e := d.coordinator.PreparedLocalQualification(ctx, token, domain.RuntimeSetupCandidate{ProjectID: f.ProjectID, SessionID: f.SessionID, PrincipalID: owner, ModelRef: f.ModelRef}, 600)
		if e != nil {
			return nil, e
		}
		return domain.Object{"state": "AWAITING_CONFIRMATION", "request": request, "request_hash": domain.Hash(request), "model_calls": 1, "tools": domain.Empty(), "purpose": "mu_turn", "purpose_seconds": 600, "cost_basis": "UNKNOWN", "money": nil}, nil
	case "STATUS":
		return d.coordinator.LocalQualificationStatus(ctx, token, f.ProjectID, f.RequestID, f.RequestHash)
	case "CONFIRM":
		request, e := d.coordinator.LoadLocalConfirmation(ctx, token, f.ProjectID, f.RequestID, f.RequestHash)
		if e != nil {
			return nil, e
		}
		bounded, cancel := context.WithTimeout(ctx, 3*time.Minute)
		defer cancel()
		return d.host.QualifyLocalRuntime(bounded, d.service, d.coordinator, d.apiURL, request, d.installation)
	}
	return nil, errors.New("unsupported operation")
}
