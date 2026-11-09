//go:build windows

package recoveryauthority

import (
	"context"
	"crypto/hmac"
	"crypto/sha256"
	"encoding/binary"
	"encoding/hex"
	"encoding/json"
	"errors"
	"io"
	"os"
	"strconv"
	"strings"
	"time"
	"unsafe"

	"golang.org/x/sys/windows"
)

const pipePrefix = `\\.\pipe\ResearchOS.PreparedAdoption.`

type inheritedBootstrap struct {
	Purpose string
	Pipe    string
	Key     []byte
	Peer    ProcessIdentity
}
type bootstrapFrame struct {
	Grant      json.RawMessage `json:"grant"`
	Adoption   Adoption        `json:"adoption"`
	OwnerToken string          `json:"owner_token"`
}
type wireFrame struct {
	Purpose string          `json:"purpose"`
	Payload json.RawMessage `json:"payload"`
	MAC     string          `json:"mac"`
}

func validPipe(s string) bool {
	if !strings.HasPrefix(s, pipePrefix) {
		return false
	}
	b, e := hexNonce(strings.TrimPrefix(s, pipePrefix))
	return e == nil && len(b) == 32
}
func readBootstrap() (inheritedBootstrap, error) {
	var b inheritedBootstrap
	value := os.Getenv(bootstrapEnv)
	_ = os.Unsetenv(bootstrapEnv)
	n, e := strconv.ParseUint(value, 10, 64)
	if e != nil || n == 0 {
		return b, errors.New("AUTHORITY_PRIVATE_INHERITANCE_REQUIRED")
	}
	h := windows.Handle(n)
	if kind, e := windows.GetFileType(h); e != nil || kind != windows.FILE_TYPE_PIPE {
		return b, errors.New("AUTHORITY_BOOTSTRAP_PIPE")
	}
	if e = windows.SetHandleInformation(h, windows.HANDLE_FLAG_INHERIT, 0); e != nil {
		return b, e
	}
	f := os.NewFile(uintptr(h), "private-adoption-bootstrap")
	defer f.Close()
	raw, e := io.ReadAll(io.LimitReader(f, 8193))
	if e != nil || len(raw) > 8192 {
		return b, errors.New("AUTHORITY_BOOTSTRAP_SIZE")
	}
	if e = strict(raw, &b); e != nil || len(b.Key) != 32 || !validPipe(b.Pipe) {
		return b, errors.New("AUTHORITY_BOOTSTRAP_FORMAT")
	}
	return b, nil
}
func writeFrame(w io.Writer, key []byte, purpose string, value any) error {
	if len(key) != 32 {
		return errors.New("AUTHORITY_TRANSPORT_KEY")
	}
	payload := encoded(value)
	mac := hmac.New(sha256.New, key)
	mac.Write([]byte(purpose + "/transport\x00"))
	mac.Write(payload)
	raw := encoded(wireFrame{Purpose: purpose, Payload: payload, MAC: hex.EncodeToString(mac.Sum(nil))})
	if len(raw) > maxFrame {
		return errors.New("AUTHORITY_FRAME_SIZE")
	}
	var length [4]byte
	binary.BigEndian.PutUint32(length[:], uint32(len(raw)))
	if _, e := w.Write(length[:]); e != nil {
		return e
	}
	_, e := w.Write(raw)
	return e
}
func readFrame(r io.Reader, key []byte, purpose string, value any) error {
	if len(key) != 32 {
		return errors.New("AUTHORITY_TRANSPORT_KEY")
	}
	var length [4]byte
	if _, e := io.ReadFull(r, length[:]); e != nil {
		return e
	}
	n := binary.BigEndian.Uint32(length[:])
	if n == 0 || n > maxFrame {
		return errors.New("AUTHORITY_FRAME_SIZE")
	}
	raw := make([]byte, n)
	if _, e := io.ReadFull(r, raw); e != nil {
		return e
	}
	var f wireFrame
	if e := strict(raw, &f); e != nil {
		return e
	}
	mac := hmac.New(sha256.New, key)
	mac.Write([]byte(purpose + "/transport\x00"))
	mac.Write(f.Payload)
	got, e := hex.DecodeString(f.MAC)
	if e != nil || f.Purpose != purpose || !hmac.Equal(got, mac.Sum(nil)) {
		return errors.New("AUTHORITY_FRAME_AUTHENTICATION")
	}
	return strict(f.Payload, value)
}
func privateSecurity() (*windows.SecurityAttributes, error) {
	u, e := windows.GetCurrentProcessToken().GetTokenUser()
	if e != nil {
		return nil, e
	}
	sid := u.User.Sid.String()
	sd, e := windows.SecurityDescriptorFromString("O:" + sid + "D:P(A;;GA;;;" + sid + ")")
	if e != nil {
		return nil, e
	}
	return &windows.SecurityAttributes{Length: uint32(unsafe.Sizeof(windows.SecurityAttributes{})), SecurityDescriptor: sd}, nil
}
func maintenanceJob() (windows.Handle, error) {
	h, e := windows.CreateJobObject(nil, nil)
	if e != nil {
		return 0, e
	}
	limits := windows.JOBOBJECT_EXTENDED_LIMIT_INFORMATION{}
	limits.BasicLimitInformation.LimitFlags = windows.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
	if _, e = windows.SetInformationJobObject(h, windows.JobObjectExtendedLimitInformation, uintptr(unsafe.Pointer(&limits)), uint32(unsafe.Sizeof(limits))); e != nil {
		windows.CloseHandle(h)
		return 0, e
	}
	return h, nil
}
func createPrivate(name string) (windows.Handle, error) {
	if !validPipe(name) {
		return 0, errors.New("AUTHORITY_PIPE_NAME")
	}
	sa, e := privateSecurity()
	if e != nil {
		return 0, e
	}
	ptr, e := windows.UTF16PtrFromString(name)
	if e != nil {
		return 0, e
	}
	return windows.CreateNamedPipe(ptr, windows.PIPE_ACCESS_DUPLEX|windows.FILE_FLAG_FIRST_PIPE_INSTANCE|windows.FILE_FLAG_OVERLAPPED, windows.PIPE_TYPE_BYTE|windows.PIPE_READMODE_BYTE|windows.PIPE_WAIT|windows.PIPE_REJECT_REMOTE_CLIENTS, 1, 65536, 65536, 0, sa)
}
func acceptPrivate(ctx context.Context, h windows.Handle, expected ProcessIdentity) (*os.File, error) {
	event, e := windows.CreateEvent(nil, 1, 0, nil)
	if e != nil {
		return nil, e
	}
	defer windows.CloseHandle(event)
	overlap := windows.Overlapped{HEvent: event}
	e = windows.ConnectNamedPipe(h, &overlap)
	if errors.Is(e, windows.ERROR_IO_PENDING) {
		for {
			status, waitErr := windows.WaitForSingleObject(event, 100)
			if waitErr != nil || ctx.Err() != nil {
				_ = windows.CancelIoEx(h, &overlap)
				_, _ = windows.WaitForSingleObject(event, windows.INFINITE)
				if waitErr != nil {
					return nil, waitErr
				}
				return nil, ctx.Err()
			}
			if status == windows.WAIT_OBJECT_0 {
				break
			}
		}
		var transferred uint32
		if e = windows.GetOverlappedResult(h, &overlap, &transferred, false); e != nil {
			return nil, e
		}
	} else if e != nil && !errors.Is(e, windows.ERROR_PIPE_CONNECTED) {
		return nil, e
	}
	var pid uint32
	if e = windows.GetNamedPipeClientProcessId(h, &pid); e != nil || pid != expected.PID {
		return nil, errors.New("AUTHORITY_PIPE_CLIENT_PID")
	}
	peer, e := windows.OpenProcess(windows.PROCESS_QUERY_LIMITED_INFORMATION, false, pid)
	if e != nil {
		return nil, e
	}
	defer windows.CloseHandle(peer)
	observed, e := process(peer)
	if e != nil || !sameProcess(observed, expected) {
		return nil, errors.New("AUTHORITY_PIPE_CLIENT_BIRTH_IMAGE")
	}
	f := os.NewFile(uintptr(h), "private-adoption-server")
	deadline := time.Now().Add(10 * time.Second)
	if d, ok := ctx.Deadline(); ok && d.Before(deadline) {
		deadline = d
	}
	if e = f.SetDeadline(deadline); e != nil {
		return nil, e
	}
	return f, nil
}
func dialPrivate(ctx context.Context, name string, expected ProcessIdentity) (*os.File, error) {
	if !validPipe(name) {
		return nil, errors.New("AUTHORITY_PIPE_NAME")
	}
	ptr, e := windows.UTF16PtrFromString(name)
	if e != nil {
		return nil, e
	}
	// No retries: a missing parent endpoint cannot create an alternate authority.
	h, e := windows.CreateFile(ptr, windows.GENERIC_READ|windows.GENERIC_WRITE, 0, nil, windows.OPEN_EXISTING, windows.FILE_FLAG_OVERLAPPED, 0)
	if e != nil {
		return nil, e
	}
	var pid uint32
	if e = windows.GetNamedPipeServerProcessId(h, &pid); e != nil || pid != expected.PID {
		windows.CloseHandle(h)
		return nil, errors.New("AUTHORITY_PIPE_SERVER_PID")
	}
	f := os.NewFile(uintptr(h), "private-adoption-client")
	deadline := time.Now().Add(10 * time.Second)
	if d, ok := ctx.Deadline(); ok && d.Before(deadline) {
		deadline = d
	}
	if e = f.SetDeadline(deadline); e != nil {
		f.Close()
		return nil, e
	}
	return f, nil
}
