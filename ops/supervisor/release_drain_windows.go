//go:build windows

package supervisor

import (
	"context"
	"crypto/hmac"
	"crypto/rand"
	"crypto/sha256"
	"encoding/binary"
	"encoding/hex"
	"encoding/json"
	"errors"
	"io"
	"os"
	"strings"
	"time"
	"unsafe"

	"golang.org/x/sys/windows"
)

const drainPipePrefix = `\\.\pipe\researchos-r2-fixture-`

type DrainFrame struct {
	Kind      string                 `json:"kind"`
	Operation string                 `json:"operation"`
	Epoch     uint64                 `json:"epoch"`
	Root      string                 `json:"root"`
	Nonce     string                 `json:"nonce"`
	Receipt   string                 `json:"receipt,omitempty"`
	State     string                 `json:"state,omitempty"`
	MAC       string                 `json:"mac"`
	Readiness *DrainReadiness        `json:"readiness,omitempty"`
	Release   *ReleasePrivateMessage `json:"release,omitempty"`
}

// ReleasePrivateMessage is carried only on the inherited, peer-checked pipe.
// FIXTURE actions are not a public API or an authorization flag.
type ReleasePrivateMessage struct {
	Project     string            `json:"project,omitempty"`
	Candidate   string            `json:"candidate,omitempty"`
	Request     json.RawMessage   `json:"request,omitempty"`
	Snapshot    *ReleaseState     `json:"snapshot,omitempty"`
	Admission   *ReleaseAdmission `json:"admission,omitempty"`
	Cutover     *ReleaseCutover   `json:"cutover,omitempty"`
	Observation *ReleaseReceipt   `json:"observation,omitempty"`
	Result      json.RawMessage   `json:"result,omitempty"`
	Error       string            `json:"error,omitempty"`
}

type ReleaseCutover struct {
	Operation      string          `json:"operation"`
	Epoch          uint64          `json:"epoch"`
	Root           string          `json:"root"`
	Database       string          `json:"database"`
	Directory      string          `json:"directory"`
	KeyPath        string          `json:"key_path"`
	ManifestSHA256 string          `json:"manifest_sha256"`
	Purpose        json.RawMessage `json:"purpose"`
	Migrations     []int           `json:"migrations"`
}

// These types describe a restored, fenced copy. They grant no release or
// reconciliation authority and are not messages accepted by the control pipe.
type RestorePathIdentity struct {
	Path      string `json:"path"`
	FileID    string `json:"file_id"`
	Directory bool   `json:"directory"`
}

type RestoreTableDelta struct {
	Table        string `json:"table"`
	BeforeSHA256 string `json:"before_sha256"`
	AfterSHA256  string `json:"after_sha256"`
	BeforeRows   int    `json:"before_rows"`
	AfterRows    int    `json:"after_rows"`
}

type ReleaseRestoreContext struct {
	Format                    string              `json:"format"`
	Status                    string              `json:"status"`
	Operation                 string              `json:"operation"`
	Project                   string              `json:"project"`
	Candidate                 string              `json:"candidate"`
	AdmissionSHA256           string              `json:"admission_sha256"`
	ManifestSHA256            string              `json:"manifest_sha256"`
	Manifest                  RestorePathIdentity `json:"manifest"`
	ManifestRawSHA256         string              `json:"manifest_raw_sha256"`
	PurposeSHA256             string              `json:"purpose_sha256"`
	SnapshotEpoch             uint64              `json:"snapshot_epoch"`
	HostEpoch                 uint64              `json:"host_epoch"`
	SourceRoot                RestorePathIdentity `json:"source_root"`
	SourceDatabase            RestorePathIdentity `json:"source_database"`
	DestinationRoot           RestorePathIdentity `json:"destination_root"`
	DestinationDatabase       RestorePathIdentity `json:"destination_database"`
	SourceDatabaseSHA256      string              `json:"source_database_sha256"`
	DestinationDatabaseSHA256 string              `json:"destination_database_sha256"`
	Report                    RestorePathIdentity `json:"report"`
	ReportSHA256              string              `json:"report_sha256"`
	BeforeInventory           json.RawMessage     `json:"before_inventory"`
	AfterInventory            json.RawMessage     `json:"after_inventory"`
	BeforeRowsSHA256          string              `json:"before_rows_sha256"`
	AfterRowsSHA256           string              `json:"after_rows_sha256"`
	AllowedDelta              []RestoreTableDelta `json:"allowed_delta"`
}

// The journal stores a small, immutable reference to the host-owned context.
// The context contains inventories, never protected bodies or credentials.
type ReleaseRestoreResult struct {
	Operation      string `json:"operation"`
	Epoch          uint64 `json:"epoch"`
	SourceRoot     string `json:"source_root"`
	Destination    string `json:"destination"`
	ContextPath    string `json:"context_path"`
	ContextSHA256  string `json:"context_sha256"`
	ManifestSHA256 string `json:"manifest_sha256"`
}

const ReleaseRestoreContextFormat = "R2_RESTORE_CONTEXT_FENCE_V1"
const RecoveryAuthorizationBlocked = "BLOCKED_RECOVERY_AUTHORIZATION"

type DrainReadiness struct {
	Process         ProcessIdentity `json:"process"`
	Listener        string          `json:"listener"`
	LeaseHeld       bool            `json:"lease_held"`
	StartupComplete bool            `json:"startup_complete"`
}

func NewDrainPipeName() (string, error) {
	var nonce [16]byte
	if _, e := rand.Read(nonce[:]); e != nil {
		return "", e
	}
	return drainPipePrefix + hex.EncodeToString(nonce[:]), nil
}

func validDrainPipeName(name string) bool {
	if !strings.HasPrefix(name, drainPipePrefix) || len(name) != len(drainPipePrefix)+32 {
		return false
	}
	_, e := hex.DecodeString(strings.TrimPrefix(name, drainPipePrefix))
	return e == nil
}

func DrainFrameSign(key []byte, frame DrainFrame) (DrainFrame, error) {
	if len(key) != 32 {
		return frame, errors.New("32-byte inherited drain capability required")
	}
	frame.MAC = ""
	raw, e := json.Marshal(frame)
	if e != nil {
		return frame, e
	}
	h := hmac.New(sha256.New, key)
	_, _ = h.Write(raw)
	frame.MAC = hex.EncodeToString(h.Sum(nil))
	return frame, nil
}

func DrainFrameValid(key []byte, frame DrainFrame) bool {
	if !validDigest(frame.MAC) {
		return false
	}
	mac := frame.MAC
	want, e := DrainFrameSign(key, frame)
	return e == nil && hmac.Equal([]byte(mac), []byte(want.MAC))
}

func WriteDrainFrame(w io.Writer, frame DrainFrame) error {
	raw, e := json.Marshal(frame)
	if e != nil {
		return e
	}
	if len(raw) > 8192 {
		return errors.New("drain frame too large")
	}
	var lenbuf [4]byte
	binary.BigEndian.PutUint32(lenbuf[:], uint32(len(raw)))
	if _, e = w.Write(lenbuf[:]); e != nil {
		return e
	}
	_, e = w.Write(raw)
	return e
}

func ReadDrainFrame(r io.Reader) (DrainFrame, error) {
	var frame DrainFrame
	var lenbuf [4]byte
	if _, e := io.ReadFull(r, lenbuf[:]); e != nil {
		return frame, e
	}
	n := binary.BigEndian.Uint32(lenbuf[:])
	if n == 0 || n > 8192 {
		return frame, errors.New("drain frame length invalid")
	}
	raw := make([]byte, n)
	if _, e := io.ReadFull(r, raw); e != nil {
		return frame, e
	}
	if e := json.Unmarshal(raw, &frame); e != nil {
		return frame, e
	}
	return frame, nil
}

func ObserveProcess(pid uint32) (ProcessIdentity, error) {
	created, alive, e := processCreated(pid)
	if e != nil || !alive {
		return ProcessIdentity{}, errors.New("process not alive for identity observation")
	}
	h, e := windows.OpenProcess(windows.PROCESS_QUERY_LIMITED_INFORMATION, false, pid)
	if e != nil {
		return ProcessIdentity{}, e
	}
	defer windows.CloseHandle(h)
	hash, e := processImageDigest(h)
	if e != nil {
		return ProcessIdentity{}, e
	}
	return ProcessIdentity{PID: pid, CreatedNS: created, ImageSHA256: hash}, nil
}

func drainSecurity() (*windows.SecurityAttributes, error) {
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

// AcceptDrainPipe binds a single same-user fixture connection to the exact
// supervisor PID/creation/image. A missing ACK never causes another command.
func AcceptDrainPipe(ctx context.Context, name string, expected ProcessIdentity) (*os.File, error) {
	if !validDrainPipeName(name) {
		return nil, errors.New("fixture drain pipe name invalid")
	}
	sa, e := drainSecurity()
	if e != nil {
		return nil, e
	}
	ptr, e := windows.UTF16PtrFromString(name)
	if e != nil {
		return nil, e
	}
	h, e := windows.CreateNamedPipe(ptr, windows.PIPE_ACCESS_DUPLEX|windows.FILE_FLAG_FIRST_PIPE_INSTANCE|windows.FILE_FLAG_OVERLAPPED, windows.PIPE_TYPE_BYTE|windows.PIPE_READMODE_BYTE|windows.PIPE_WAIT|windows.PIPE_REJECT_REMOTE_CLIENTS, 1, 8192, 8192, 0, sa)
	if e != nil {
		return nil, e
	}
	ok := false
	defer func() {
		if !ok {
			_ = windows.CloseHandle(h)
		}
	}()
	event, e := windows.CreateEvent(nil, 1, 0, nil)
	if e != nil {
		return nil, e
	}
	defer windows.CloseHandle(event)
	overlap := windows.Overlapped{HEvent: event}
	if e = windows.ConnectNamedPipe(h, &overlap); errors.Is(e, windows.ERROR_IO_PENDING) {
		for {
			status, err := windows.WaitForSingleObject(event, 100)
			if err != nil || ctx.Err() != nil {
				_ = windows.CancelIoEx(h, &overlap)
				_, _ = windows.WaitForSingleObject(event, windows.INFINITE)
				if err != nil {
					return nil, err
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
		return nil, errors.New("drain client PID differs")
	}
	alive, e := (NativeFixtureDriver{}).Alive(expected)
	if e != nil || !alive {
		return nil, errors.New("drain client identity changed")
	}
	ok = true
	return os.NewFile(uintptr(h), name), nil
}

// DialDrainPipe only retries creation/readiness. Once connected, business
// frames have one send; a missing response is an unknown outcome.
func DialDrainPipe(name string, expected ProcessIdentity) (*os.File, error) {
	return dialDrainPipeUntil(name, expected, time.Now().Add(2*time.Second))
}

func dialDrainPipeUntil(name string, expected ProcessIdentity, deadline time.Time) (*os.File, error) {
	if !validDrainPipeName(name) {
		return nil, errors.New("fixture drain pipe name invalid")
	}
	ptr, e := windows.UTF16PtrFromString(name)
	if e != nil {
		return nil, e
	}
	for {
		h, openErr := windows.CreateFile(ptr, windows.GENERIC_READ|windows.GENERIC_WRITE, 0, nil, windows.OPEN_EXISTING, windows.FILE_FLAG_OVERLAPPED, 0)
		if openErr == nil {
			var pid uint32
			if e = windows.GetNamedPipeServerProcessId(h, &pid); e != nil || pid != expected.PID {
				_ = windows.CloseHandle(h)
				return nil, errors.New("drain server PID differs")
			}
			alive, checkErr := (NativeFixtureDriver{}).Alive(expected)
			if checkErr != nil || !alive {
				_ = windows.CloseHandle(h)
				return nil, errors.New("drain server identity changed")
			}
			return os.NewFile(uintptr(h), name), nil
		}
		if time.Now().After(deadline) || (!errors.Is(openErr, windows.ERROR_FILE_NOT_FOUND) && !errors.Is(openErr, windows.ERROR_PIPE_BUSY)) {
			return nil, openErr
		}
		time.Sleep(20 * time.Millisecond)
	}
}
