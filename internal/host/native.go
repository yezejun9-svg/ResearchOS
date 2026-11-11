package host

// The native bridge is the only entrance for provider credential material and for the
// user-chosen workspace directory (22 §NativeBridge, 04 §鉴权). Frames are validated for
// sender, shape and version; the pinned contract defs decide the shape, so the bridge cannot
// grow a private dialect. Nothing that crosses this boundary is echoed back in plaintext:
// responses carry references and states only.

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	"researchos.local/research-os/internal/auth"
	"researchos.local/research-os/internal/domain"
)

const (
	KindUserBootstrapRequest    = "NATIVE_USER_BOOTSTRAP_REQUEST"
	KindUserBootstrapResult     = "NATIVE_USER_BOOTSTRAP_RESULT"
	KindCredentialImportRequest = "NATIVE_CREDENTIAL_IMPORT_REQUEST"
	KindCredentialImportResult  = "NATIVE_CREDENTIAL_IMPORT_RESULT"
	KindWorkspaceChooseRequest  = "NATIVE_WORKSPACE_CHOOSE_REQUEST"
	KindWorkspaceChooseResult   = "NATIVE_WORKSPACE_CHOOSE_RESULT"
	MaxNativeFrameBytes         = 8192
	sessionFileName             = "session.json"
	nativeProtocolVersion       = "researchos-client/2"
)

var (
	ErrFrameTooLarge  = errors.New("CONTENT_TOO_LARGE")
	ErrFrameUntrusted = errors.New("UNTRUSTED_TRANSPORT")
	ErrFrameShape     = errors.New("INVALID_REQUEST")
	ErrCredentialKind = errors.New("CREDENTIAL_MISSING")
)

// NativeFrame is the transport envelope: a kind, the calling client's identity, and a payload
// that must satisfy the pinned definition for that kind. Extra fields are refused, which is what
// "verify sender and frame" means concretely for this host.
type NativeFrame struct {
	Kind     string          `json:"kind"`
	ClientID string          `json:"client_id"`
	Payload  json.RawMessage `json:"payload"`
}

type credentialImportRequest struct {
	ProviderID           string  `json:"provider_id"`
	CredentialKind       string  `json:"credential_kind"`
	CredentialValue      string  `json:"credential_value"`
	ReplaceCredentialRef *string `json:"replace_credential_ref"`
}

type workspaceChooseRequest struct {
	RequestedPath   *string `json:"requested_path"`
	RequestedAccess string  `json:"requested_access"`
}

// SessionFile is where the host keeps the current short credential for local clients: a
// 0600 file under the current-user DACL, exactly the mechanism the existing host already uses.
// It is never a bridge field, so a renderer cannot obtain it, and the reply schema is the
// published one with credential_exposed_to_renderer=false.
func (h *Host) SessionFile() string { return filepath.Join(h.dir, sessionFileName) }

func (h *Host) writeSessionFile(s Session) error {
	raw, err := json.Marshal(map[string]any{"token": s.Token, "principal_id": s.PrincipalID,
		"expires_at": s.ExpiresAt.UTC().Format(time.RFC3339Nano), "issued_at": s.IssuedAt.UTC().Format(time.RFC3339Nano)})
	if err != nil {
		return err
	}
	path := h.SessionFile()
	tmp := path + ".tmp"
	f, err := os.OpenFile(tmp, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0o600)
	if err != nil {
		return err
	}
	if _, err := f.Write(raw); err != nil {
		f.Close()
		os.Remove(tmp)
		return err
	}
	if err := f.Sync(); err != nil {
		f.Close()
		os.Remove(tmp)
		return err
	}
	if err := f.Close(); err != nil {
		os.Remove(tmp)
		return err
	}
	if err := privateFile(tmp); err != nil {
		os.Remove(tmp)
		return err
	}
	return os.Rename(tmp, path)
}

// ReadSessionFile is the client-side counterpart: the local user's own file, never a listing of
// anything else, and the only reason the user must not copy a token from a log or the console.
func (h *Host) ReadSessionFile() (Session, error) {
	var out struct {
		Token     string `json:"token"`
		Principal string `json:"principal_id"`
		ExpiresAt string `json:"expires_at"`
	}
	if err := readPrivate(h.dir, sessionFileName, &out); err != nil {
		return Session{}, err
	}
	exp, err := time.Parse(time.RFC3339Nano, out.ExpiresAt)
	if err != nil {
		return Session{}, err
	}
	return Session{Token: out.Token, PrincipalID: out.Principal, ExpiresAt: exp}, nil
}

// verifiedNativePeer is an in-process capability produced from the OS transport,
// not from NativeFrame.ClientID or the legacy success boolean. It proves only the
// observed peer user, not a client instance, credential binding or writer grant.
type verifiedNativePeer struct {
	host       *Host
	generation [32]byte
	identity   auth.Identity
	pid        uint32
}

func (p verifiedNativePeer) validFor(h *Host) bool {
	return h != nil && p.host == h && p.pid != 0 &&
		h.bootGeneration != ([32]byte{}) && p.generation == h.bootGeneration &&
		verifiableKind(p.identity.Kind) && p.identity.Ref != "" &&
		h.identity.SameUser(p.identity)
}

// Only the OS transport calls this in production. A failed lookup or comparison
// never produces a capability, including when a caller supplies a matching label.
func (h *Host) verifyNativePeer(pid uint32) (verifiedNativePeer, error) {
	if h == nil || pid == 0 || h.peerLookup == nil || h.bootGeneration == ([32]byte{}) {
		return verifiedNativePeer{}, ErrFrameUntrusted
	}
	identity, err := h.peerLookup(pid)
	if err != nil {
		return verifiedNativePeer{}, fmt.Errorf("%w: peer identity unresolved: %v", ErrFrameUntrusted, err)
	}
	peer := verifiedNativePeer{host: h, generation: h.bootGeneration, identity: identity, pid: pid}
	if !peer.validFor(h) {
		return verifiedNativePeer{}, ErrHostIdentity
	}
	return peer, nil
}

// The peer remains attached at the handler dispatch boundary. A nil peer is an
// explicitly unproven legacy invocation, never a substitute for native evidence.
type nativeInvocation struct {
	frame NativeFrame
	peer  *verifiedNativePeer
}

// HandleNative preserves the legacy adapter for the existing operations. Its
// boolean does not mint or populate verifiedNativePeer.
func (h *Host) HandleNative(raw []byte, clientVerified bool, selectionHook func(path string) (string, error)) ([]byte, error) {
	if len(raw) == 0 || len(raw) > MaxNativeFrameBytes {
		return nil, ErrFrameTooLarge
	}
	if !clientVerified {
		return nil, ErrFrameUntrusted
	}
	invocation, err := h.prepareNativeInvocation(raw, nil)
	if err != nil {
		return nil, err
	}
	return h.dispatchNative(invocation, selectionHook)
}

func (h *Host) handleVerifiedNative(raw []byte, peer verifiedNativePeer, selectionHook func(string) (string, error)) ([]byte, error) {
	if !peer.validFor(h) {
		return nil, ErrFrameUntrusted
	}
	invocation, err := h.prepareNativeInvocation(raw, &peer)
	if err != nil {
		return nil, err
	}
	return h.dispatchNative(invocation, selectionHook)
}

func (h *Host) prepareNativeInvocation(raw []byte, peer *verifiedNativePeer) (nativeInvocation, error) {
	if len(raw) == 0 || len(raw) > MaxNativeFrameBytes {
		return nativeInvocation{}, ErrFrameTooLarge
	}
	if peer != nil && !peer.validFor(h) {
		return nativeInvocation{}, ErrFrameUntrusted
	}
	var frame NativeFrame
	dec := json.NewDecoder(bytesReader(raw))
	dec.DisallowUnknownFields()
	if err := dec.Decode(&frame); err != nil {
		return nativeInvocation{}, fmt.Errorf("%w: %v", ErrFrameShape, err)
	}
	if frame.ClientID == "" {
		return nativeInvocation{}, fmt.Errorf("%w: client_id is required", ErrFrameShape)
	}
	if def, ok := nativeRequestDefs[frame.Kind]; ok {
		_ = def
		if err := h.validateNativeRequest(frame.Kind, frame.Payload); err != nil {
			return nativeInvocation{}, err
		}
	}
	return nativeInvocation{frame: frame, peer: peer}, nil
}

func (h *Host) dispatchNative(invocation nativeInvocation, selectionHook func(string) (string, error)) ([]byte, error) {
	if invocation.peer != nil && !invocation.peer.validFor(h) {
		return nil, ErrFrameUntrusted
	}
	frame := invocation.frame
	var reply []byte
	var undo func()
	var err error
	switch frame.Kind {
	case KindUserBootstrapRequest:
		reply, undo, err = h.nativeBootstrap(frame.ClientID)
	case KindCredentialImportRequest:
		reply, undo, err = h.nativeCredentialImport(frame.Payload)
	case KindWorkspaceChooseRequest:
		reply, undo, err = h.nativeWorkspaceChoose(context.Background(), frame.ClientID, frame.Payload, selectionHook)
	default:
		return nil, fmt.Errorf("%w: unknown native kind %s", ErrFrameShape, frame.Kind)
	}
	if err != nil {
		if undo != nil {
			undo()
		}
		return nil, err
	}
	// Every reply is graded in read direction against the published result definition before it
	// leaves the host, so no handler can hand credential material to a client. The verdict is
	// load-bearing: a reply the contract refuses also has its staged local state withdrawn, so a
	// nonconforming handler cannot reserve a credential, root or selection in advance and keep it.
	if err := h.validateNativeReply(reply); err != nil {
		if undo != nil {
			undo()
		}
		return nil, err
	}
	return reply, nil
}

func (h *Host) nativeBootstrap(clientID string) ([]byte, func(), error) {
	res, err := h.BootstrapOwner(context.Background())
	if err != nil {
		return nil, nil, err
	}
	undo := h.stageSessionUndo(res.Session)
	// BootstrapOwner already issued and durably wrote this session. Rewriting
	// it here would create a second, unnecessary credential-file operation.
	// The bridge reply must not carry the credential: the durable 0600 file is the only local
	// handoff, so the field is cleared before the response is assembled.
	res.Session.Token = ""
	reply, err := json.Marshal(map[string]any{
		"kind": KindUserBootstrapResult,
		"payload": map[string]any{
			"authenticated_principal_ref":    res.PrincipalRef,
			"client_id":                      clientID,
			"host_instance_id":               h.InstanceID(),
			"protocol_version":               h.protocolVersion,
			"credential_exposed_to_renderer": false,
		},
	})
	if err != nil {
		undo()
		return nil, nil, err
	}
	return reply, undo, nil
}

// stageSessionUndo returns the withdrawal for a session handed out by this call: the private
// 0600 file is removed and the credential it carried is revoked, so a refused reply never leaves
// a live token behind. Only rows this host just issued are touched.
func (h *Host) stageSessionUndo(s Session) func() {
	principal, token := s.PrincipalID, s.Token
	return func() {
		if token == "" {
			return
		}
		_ = h.revokeCredentialByHash(context.Background(), principal, domain.Digest([]byte(token)))
		if _, err := os.Stat(h.SessionFile()); err == nil {
			if raw, rerr := os.ReadFile(h.SessionFile()); rerr == nil && bytesContains(raw, []byte(token)) {
				os.Remove(h.SessionFile())
			}
		}
	}
}

func bytesContains(a, b []byte) bool { return strings.Contains(string(a), string(b)) }

func (h *Host) nativeCredentialImport(payload []byte) ([]byte, func(), error) {
	var req credentialImportRequest
	dec := json.NewDecoder(bytesReader(payload))
	dec.DisallowUnknownFields()
	if err := dec.Decode(&req); err != nil {
		return nil, nil, fmt.Errorf("%w: %v", ErrFrameShape, err)
	}
	if req.ProviderID == "" || req.CredentialKind == "" {
		return nil, nil, ErrFrameShape
	}
	if req.CredentialKind != "API_KEY" && req.CredentialKind != "OAUTH_TOKEN" {
		return nil, nil, ErrCredentialKind
	}
	buf := []byte(req.CredentialValue)
	req.CredentialValue = ""
	ref, err := h.vault.Store(req.ProviderID, req.CredentialKind, buf, h.nowUTC())
	if err != nil {
		return nil, nil, err
	}
	undo := func() { _ = h.vault.Revoke(ref) }
	if req.ReplaceCredentialRef != nil {
		if err := h.vault.Revoke(*req.ReplaceCredentialRef); err != nil {
			undo()
			return nil, nil, err
		}
	}
	reply, err := json.Marshal(map[string]any{
		"kind":    KindCredentialImportResult,
		"payload": map[string]any{"credential_ref": ref, "provider_id": req.ProviderID, "status": "AVAILABLE"},
	})
	if err != nil {
		undo()
		return nil, nil, err
	}
	return reply, undo, nil
}

// nativeWorkspaceChoose resolves the chosen directory here, never in the client: the host is the
// component that can see real paths, links and permissions.
func (h *Host) nativeWorkspaceChoose(ctx context.Context, clientID string, payload []byte, chooser func(string) (string, error)) ([]byte, func(), error) {
	var req workspaceChooseRequest
	dec := json.NewDecoder(bytesReader(payload))
	dec.DisallowUnknownFields()
	if err := dec.Decode(&req); err != nil {
		return nil, nil, fmt.Errorf("%w: %v", ErrFrameShape, err)
	}
	if req.RequestedAccess != AccessReadOnly && req.RequestedAccess != AccessReadWrite {
		return nil, nil, ErrFrameShape
	}
	path := ""
	if req.RequestedPath != nil {
		// A client-named directory is only a hint: without a real chooser the host would be
		// binding whatever path a caller typed, which is the "public OWNER registration" failure
		// mode in filesystem form, so the request is refused rather than trusted.
		if chooser == nil {
			return nil, nil, fmt.Errorf("%w: a client-named path needs a user chooser", ErrUntrustedPathChoice)
		}
		path = *req.RequestedPath
	}
	if chooser != nil {
		picked, err := chooser(path)
		if err != nil {
			return nil, nil, err
		}
		path = picked
	}
	if path == "" {
		return nil, nil, fmt.Errorf("%w: no directory was chosen", ErrFrameShape)
	}
	real, err := filepath.Abs(path)
	if err != nil {
		return nil, nil, err
	}
	real, err = filepath.EvalSymlinks(real)
	if err != nil {
		return nil, nil, err
	}
	if reparse, err := chainHasReparsePoint(real); err != nil {
		return nil, nil, err
	} else if reparse {
		return nil, nil, ErrPathReparsePoint
	}
	ref, err := h.roots.nextRef()
	if err != nil {
		return nil, nil, err
	}
	created, err := h.roots.Register(ref, real, req.RequestedAccess, h.nowUTC())
	if err != nil {
		return nil, nil, err
	}
	rec, err := h.selections.Issue(h.identity.Ref, clientID, real, real, req.RequestedAccess, h.nowUTC())
	if err != nil {
		_ = h.roots.Revoke(created.Ref)
		return nil, nil, err
	}
	undo := func() {
		_ = h.roots.Revoke(created.Ref)
		h.selections.Withdraw(rec.Ref)
	}
	reply, err := json.Marshal(map[string]any{
		"kind":    KindWorkspaceChooseResult,
		"payload": map[string]any{"selection_ref": rec.Ref, "display_path": rec.DisplayPath, "expires_at": rec.ExpiresAt},
	})
	if err != nil {
		undo()
		return nil, nil, err
	}
	return reply, undo, nil
}

// ConsumeSelection is the host-side redemption of a selection reference; a later command that
// carries one can only use it once, by the same principal and client, before it expires.
func (h *Host) ConsumeSelection(ref, clientID string) (*SelectionRecord, error) {
	return h.selections.Consume(ref, h.identity.Ref, clientID, h.nowUTC())
}

// Roots exposes the binding list for host diagnostics (references and states only).
func (h *Host) Roots() []*RootBinding { return h.roots.List() }

// ImportCredential is the in-process equivalent of the native credential frame, used by the
// host's own configuration path. Material never outlives the call.
func (h *Host) ImportCredential(provider, kind, value string, replace string) (string, error) {
	buf := []byte(value)
	ref, err := h.vault.Store(provider, kind, buf, h.nowUTC())
	if err != nil {
		return "", err
	}
	if replace != "" {
		if err := h.vault.Revoke(replace); err != nil {
			return "", err
		}
	}
	return ref, nil
}

// CredentialStatus is the only credential view any other layer may publish.
func (h *Host) CredentialStatus(ref string) string { return h.vault.Status(ref) }

// OpenCredential stays package-private on purpose: only host-internal adapter code may recover
// plaintext, and no protocol response, event or log line has a path to it.
func (h *Host) openCredentialForProvider(ref string) ([]byte, error) { return h.vault.open(ref) }
