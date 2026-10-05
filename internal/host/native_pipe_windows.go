//go:build windows

package host

// Named-pipe native transport (22 §28: "Windows 默认使用仅当前 OS SID 可访问的 named pipe").
// Two independent gates protect the boundary: the pipe DACL grants only the current user's SID,
// and every accepted connection is re-authenticated by asking the OS which process is on the other
// end. A DACL alone would still admit another process owned by the same account, and a PID check
// alone would trust the client's word about where the pipe came from, so both are required.

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"strings"
	"time"
	"unsafe"

	"golang.org/x/sys/windows"

	"researchos.local/research-os/internal/auth"
)

const (
	pipePrefix        = `\\.\pipe\ResearchOSHost-v1-`
	pipeClientAccess  = windows.PIPE_ACCESS_DUPLEX
	pipeACL           = "0xC0100000" // GENERIC_READ|GENERIC_WRITE|SYNCHRONIZE for this user only
	pipeConnectWait   = 3 * time.Second
	pipeFrameDeadline = 5 * time.Second
	frameHeaderBytes  = 0
)

var ErrPipeUnavailable = errors.New("NATIVE_TRANSPORT_UNAVAILABLE")

// PipeName derives an instance-specific name so two hosts on one machine cannot hijack each
// other's bridge.
func PipeName(instanceID string) string { return pipePrefix + strings.TrimPrefix(instanceID, "host-") }

func currentSIDStringForPipe() string {
	tu, err := windows.GetCurrentProcessToken().GetTokenUser()
	if err != nil || tu.User.Sid == nil || !tu.User.Sid.IsValid() {
		return "S-1-0-0" // the null SID: a pipe nobody can open beats an open pipe
	}
	return tu.User.Sid.String()
}

func newNativePipe(pipeName string) (windows.Handle, error) {
	sd, err := windows.SecurityDescriptorFromString("D:P(A;;" + pipeACL + ";;;" + currentSIDStringForPipe() + ")")
	if err != nil {
		return 0, err
	}
	name, err := windows.UTF16PtrFromString(pipeName)
	if err != nil {
		return 0, err
	}
	attrs := windows.SecurityAttributes{
		Length:             uint32(unsafe.Sizeof(windows.SecurityAttributes{})),
		SecurityDescriptor: sd,
		InheritHandle:      0,
	}
	h, err := windows.CreateNamedPipe(name,
		pipeClientAccess|windows.FILE_FLAG_FIRST_PIPE_INSTANCE,
		windows.PIPE_TYPE_MESSAGE|windows.PIPE_READMODE_MESSAGE|windows.PIPE_REJECT_REMOTE_CLIENTS,
		windows.PIPE_UNLIMITED_INSTANCES, MaxNativeFrameBytes, MaxNativeFrameBytes,
		uint32(pipeFrameDeadline/time.Millisecond), &attrs)
	if err != nil {
		return 0, fmt.Errorf("%w: %v", ErrPipeUnavailable, err)
	}
	return h, nil
}

// ServeNative accepts one request/reply exchange per connection until ctx is cancelled. Message
// mode means a frame boundary is enforced by the OS, so no length prefix negotiable by a client.
func (h *Host) ServeNative(ctx context.Context, pipeName string) error {
	for {
		select {
		case <-ctx.Done():
			return ctx.Err()
		default:
		}
		ph, err := newNativePipe(pipeName)
		if err != nil {
			return err
		}
		if err := connectPipe(ph, ctx); err != nil {
			windows.CloseHandle(ph)
			if ctx.Err() != nil {
				return ctx.Err()
			}
			continue
		}
		h.serveNativeConnection(ph)
		windows.FlushFileBuffers(ph)
		windows.DisconnectNamedPipe(ph)
		windows.CloseHandle(ph)
	}
}

// connectPipe blocks until a client connects. Cancellation takes effect between connections:
// the OS gives the pipe its own instance timeout from CreateNamedPipe, so a half-open listener
// cannot outlive the host session.
func connectPipe(ph windows.Handle, ctx context.Context) error {
	select {
	case <-ctx.Done():
		return ctx.Err()
	default:
	}
	err := windows.ConnectNamedPipe(ph, nil)
	if err == windows.ERROR_PIPE_CONNECTED {
		return nil // the client beat us to it; the pipe is already connected
	}
	return err
}

func (h *Host) serveNativeConnection(ph windows.Handle) {
	pid, err := namedPipeClientPID(ph)
	if err != nil {
		_ = writeNativeFrame(ph, errorFrame(ErrFrameUntrusted))
		return
	}
	// The peer is asked of the OS, never of the client: the DACL only proves "a process this user
	// can open the pipe to", so the resolved principal must also equal the principal the host
	// bootstrapped for. A lookup that fails is a refusal, not a maybe.
	peer, err := h.peerLookup(pid)
	if err != nil {
		_ = writeNativeFrame(ph, errorFrame(fmt.Errorf("%w: peer identity unresolved: %v", ErrFrameUntrusted, err)))
		return
	}
	if !h.Identity().SameUser(peer) {
		_ = writeNativeFrame(ph, errorFrame(ErrHostIdentity))
		return
	}
	raw, err := readNativeFrame(ph)
	if err != nil {
		return
	}
	// The path in a frame is only an initial suggestion. The Shell dialog runs
	// in this trusted, same-user host process and requires an explicit choice.
	reply, err := h.HandleNative(raw, true, chooseNativeFolderWindows)
	if err != nil {
		reply = errorFrame(err)
	}
	_ = writeNativeFrame(ph, reply)
}

func namedPipeClientPID(ph windows.Handle) (uint32, error) {
	var pid uint32
	if err := windows.GetNamedPipeClientProcessId(ph, &pid); err != nil {
		return 0, err
	}
	return pid, nil
}

func readNativeFrame(ph windows.Handle) ([]byte, error) {
	buf := make([]byte, MaxNativeFrameBytes)
	var got uint32
	if err := windows.ReadFile(ph, buf, &got, nil); err != nil {
		return nil, err
	}
	if got == 0 || int(got) > MaxNativeFrameBytes {
		return nil, ErrFrameTooLarge
	}
	return append([]byte(nil), buf[:got]...), nil
}

func writeNativeFrame(ph windows.Handle, payload []byte) error {
	if len(payload) == 0 || len(payload) > MaxNativeFrameBytes {
		return ErrFrameTooLarge
	}
	var written uint32
	return windows.WriteFile(ph, payload, &written, nil)
}

// DialNative is the client side used by the local CLI/Desktop and by qualification.
func DialNative(pipeName string, request []byte) ([]byte, error) {
	if len(request) == 0 || len(request) > MaxNativeFrameBytes {
		return nil, ErrFrameTooLarge
	}
	deadline := time.Now().Add(pipeConnectWait)
	for {
		f, err := os.OpenFile(pipeName, os.O_RDWR, 0)
		if err == nil {
			defer f.Close()
			if _, err := f.Write(request); err != nil {
				return nil, fmt.Errorf("%w: write: %v", ErrPipeUnavailable, err)
			}
			buf := make([]byte, MaxNativeFrameBytes)
			n, err := f.Read(buf)
			if err != nil && n == 0 {
				return nil, fmt.Errorf("%w: read: %v", ErrPipeUnavailable, err)
			}
			return append([]byte(nil), buf[:n]...), nil
		}
		if time.Now().After(deadline) {
			return nil, fmt.Errorf("%w: open: %v", ErrPipeUnavailable, err)
		}
		time.Sleep(20 * time.Millisecond)
	}
}

func errorFrame(err error) []byte {
	code := "INTERNAL_ERROR"
	switch {
	case errors.Is(err, ErrFrameUntrusted), errors.Is(err, ErrHostIdentity), errors.Is(err, auth.ErrMismatch):
		code = "UNAUTHENTICATED"
	case errors.Is(err, ErrFrameShape), errors.Is(err, ErrCredentialKind):
		code = "INVALID_REQUEST"
	case errors.Is(err, ErrFrameTooLarge):
		code = "CONTENT_TOO_LARGE"
	case errors.Is(err, ErrMultipleOwners), errors.Is(err, ErrNoOwner), errors.Is(err, ErrOwnerTaken), errors.Is(err, ErrNotBound):
		code = "POLICY_DENIED"
	case errors.Is(err, ErrUntrustedPathChoice):
		code = "FORBIDDEN"
	case errors.Is(err, ErrSelectionUsed):
		code = "SELECTION_ALREADY_USED"
	case errors.Is(err, ErrSelectionExpired):
		code = "SELECTION_EXPIRED"
	case errors.Is(err, ErrSelectionForeign):
		code = "FORBIDDEN"
	case errors.Is(err, ErrRootRevoked):
		code = "WORKSPACE_REVOKED"
	case errors.Is(err, ErrPathEscape), errors.Is(err, ErrPathReparsePoint):
		code = "PATH_OUT_OF_SCOPE"
	}
	b, _ := json.Marshal(map[string]any{"kind": "NATIVE_ERROR",
		"error": map[string]any{"code": code, "message": err.Error()}})
	return b
}
