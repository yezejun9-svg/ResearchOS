//go:build windows

package recoveryboundary

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"sort"
	"strings"
	"sync"
	"syscall"
	"time"
	"unsafe"

	"golang.org/x/sys/windows"
	"golang.org/x/sys/windows/registry"
	rt "researchos.local/research-os/adapters/runtime"
	"researchos.local/research-os/internal/qualificationmaintenancejournal"
)

type nativeHold struct {
	path     string
	handle   windows.Handle
	identity FileIdentity
}
type quiescenceOwner struct {
	mu     sync.Mutex
	closed bool
	lease  rt.DataRootLeaseIdentity
	plan   EntryFencePlan
	post   BootWitness
	holds  []nativeHold
}

// CurrentQuiescence has no public constructor or serializable authority.
// Value copies share one owner; Close consumes every copy's held native state.
type CurrentQuiescence struct{ owner *quiescenceOwner }

type boundaryRecord struct {
	Plan       EntryFencePlan  `json:"plan"`
	Pre        BootWitness     `json:"pre"`
	Post       BootWitness     `json:"post"`
	Events     []BoundaryEvent `json:"events"`
	Generation uint64          `json:"generation"`
}

type nativeSecurityQueryError struct {
	status windows.NTStatus
	needed uint32
}

func (e *nativeSecurityQueryError) Error() string {
	return fmt.Sprintf("NtQuerySecurityObject status %#x length %d: %v", uint32(e.status), e.needed, e.status.Errno())
}
func (e *nativeSecurityQueryError) Unwrap() error { return e.status.Errno() }

const maxBoundaryPlanBytes = 32 << 20

func nativeSecurityDescriptor(h windows.Handle, includeSACL bool) ([]byte, string, string, error) {
	if err := ntQuerySecurityObject.Find(); err != nil {
		return nil, "", "", err
	}
	raw := make([]byte, 64<<10)
	var needed uint32
	flags := windows.OWNER_SECURITY_INFORMATION | windows.GROUP_SECURITY_INFORMATION | windows.DACL_SECURITY_INFORMATION
	if includeSACL {
		flags |= windows.SACL_SECURITY_INFORMATION
	}
	status, _, _ := ntQuerySecurityObject.Call(uintptr(h), uintptr(flags), uintptr(unsafe.Pointer(&raw[0])), uintptr(len(raw)), uintptr(unsafe.Pointer(&needed)))
	if result := windows.NTStatus(status); result != 0 || needed < 20 || needed > uint32(len(raw)) {
		if result != 0 {
			return nil, "", "", &nativeSecurityQueryError{status: result, needed: needed}
		}
		return nil, "", "", errors.New("NtQuerySecurityObject length invalid")
	}
	raw = raw[:needed]
	semantic, err := nativeSecuritySemanticSHA256(raw)
	if err != nil {
		return nil, "", "", err
	}
	sd := (*windows.SECURITY_DESCRIPTOR)(unsafe.Pointer(&raw[0]))
	if !sd.IsValid() {
		return nil, "", "", errors.New("native security descriptor invalid")
	}
	sddl := sd.String()
	runtime.KeepAlive(raw)
	return raw, sddl, semantic, nil
}

func nativeSecurityFromSDDL(sddl string) ([]byte, string, error) {
	sd, err := windows.SecurityDescriptorFromString(sddl)
	if err != nil {
		return nil, "", err
	}
	raw := append([]byte(nil), unsafe.Slice((*byte)(unsafe.Pointer(sd)), sd.Length())...)
	semantic, err := nativeSecuritySemanticSHA256(raw)
	runtime.KeepAlive(sd)
	return raw, semantic, err
}

func nativeFileID(h windows.Handle) (uint64, string, error) {
	var x struct {
		VolumeSerialNumber uint64
		FileID             [16]byte
	}
	if err := windows.GetFileInformationByHandleEx(h, windows.FileIdInfo, (*byte)(unsafe.Pointer(&x)), uint32(unsafe.Sizeof(x))); err != nil {
		return 0, "", err
	}
	return x.VolumeSerialNumber, hex.EncodeToString(x.FileID[:]), nil
}

func finalPath(h windows.Handle) (string, error) {
	buf := make([]uint16, 512)
	for len(buf) <= 32768 {
		n, e := windows.GetFinalPathNameByHandle(h, &buf[0], uint32(len(buf)), 0)
		if e != nil {
			return "", e
		}
		if n == 0 {
			return "", errors.New("empty final path")
		}
		if int(n) < len(buf) {
			return windows.UTF16ToString(buf[:n]), nil
		}
		buf = make([]uint16, int(n)+1)
	}
	return "", errors.New("final path exceeds Windows bound")
}

func openNative(path string, directory bool, hashFile bool) (nativeHold, error) {
	return openNativeAccess(path, directory, hashFile, 0)
}

func openNativeAccess(path string, directory bool, hashFile bool, extraAccess uint32) (nativeHold, error) {
	if !filepath.IsAbs(path) || filepath.Clean(path) != path {
		return nativeHold{}, errors.New("native path is not canonical absolute")
	}
	if strings.Contains(path[len(filepath.VolumeName(path)):], ":") {
		return nativeHold{}, errors.New("alternate data stream forbidden")
	}
	w, e := windows.UTF16PtrFromString(path)
	if e != nil {
		return nativeHold{}, e
	}
	// No FILE_SHARE_DELETE: the live owner pins every opened component against
	// rename/delete until the caller's actual outer transaction has returned.
	access := uint32(windows.READ_CONTROL | windows.FILE_READ_ATTRIBUTES | windows.FILE_READ_DATA | extraAccess)
	h, e := windows.CreateFile(w, access|windows.ACCESS_SYSTEM_SECURITY,
		windows.FILE_SHARE_READ|windows.FILE_SHARE_WRITE, nil, windows.OPEN_EXISTING,
		windows.FILE_FLAG_OPEN_REPARSE_POINT|windows.FILE_FLAG_BACKUP_SEMANTICS, 0)
	saclStatus := "READABLE"
	var saclUnavailableStage string
	var saclUnavailableWin32 uint32
	var saclUnavailableNTSTATUS uint32
	if errors.Is(e, windows.ERROR_ACCESS_DENIED) || errors.Is(e, windows.ERROR_PRIVILEGE_NOT_HELD) {
		var errno syscall.Errno
		if !errors.As(e, &errno) {
			return nativeHold{}, e
		}
		saclUnavailableWin32 = uint32(errno)
		saclUnavailableStage = "OPEN"
		saclStatus = "UNAVAILABLE"
		h, e = windows.CreateFile(w, access,
			windows.FILE_SHARE_READ|windows.FILE_SHARE_WRITE, nil, windows.OPEN_EXISTING,
			windows.FILE_FLAG_OPEN_REPARSE_POINT|windows.FILE_FLAG_BACKUP_SEMANTICS, 0)
	}
	if e != nil {
		return nativeHold{}, e
	}
	fail := func(e error) (nativeHold, error) { windows.CloseHandle(h); return nativeHold{}, e }
	rawSD, sddl, semantic, e := nativeSecurityDescriptor(h, saclStatus == "READABLE")
	if e != nil && saclStatus == "READABLE" && (errors.Is(e, windows.ERROR_ACCESS_DENIED) || errors.Is(e, windows.ERROR_PRIVILEGE_NOT_HELD)) {
		var queryErr *nativeSecurityQueryError
		var errno syscall.Errno
		if !errors.As(e, &queryErr) || !errors.As(e, &errno) {
			return fail(e)
		}
		saclStatus = "UNAVAILABLE"
		saclUnavailableStage = "QUERY"
		saclUnavailableWin32 = uint32(errno)
		saclUnavailableNTSTATUS = uint32(queryErr.status)
		if closeErr := windows.CloseHandle(h); closeErr != nil {
			return nativeHold{}, closeErr
		}
		h, e = windows.CreateFile(w, access,
			windows.FILE_SHARE_READ|windows.FILE_SHARE_WRITE, nil, windows.OPEN_EXISTING,
			windows.FILE_FLAG_OPEN_REPARSE_POINT|windows.FILE_FLAG_BACKUP_SEMANTICS, 0)
		if e != nil {
			return nativeHold{}, e
		}
		rawSD, sddl, semantic, e = nativeSecurityDescriptor(h, false)
	}
	if e != nil {
		return fail(e)
	}
	var info windows.ByHandleFileInformation
	if e = windows.GetFileInformationByHandle(h, &info); e != nil {
		return fail(e)
	}
	if info.FileAttributes&windows.FILE_ATTRIBUTE_REPARSE_POINT != 0 || (info.FileAttributes&windows.FILE_ATTRIBUTE_DIRECTORY != 0) != directory {
		return fail(errors.New("reparse point or file kind mismatch"))
	}
	if !directory && info.NumberOfLinks != 1 {
		return fail(errors.New("hard-linked boundary file forbidden"))
	}
	v, id, e := nativeFileID(h)
	if e != nil {
		return fail(e)
	}
	final, e := finalPath(h)
	if e != nil {
		return fail(e)
	}
	x := FileIdentity{Path: path, FinalUTF16: final, Volume: v, FileID: id, SecurityDescriptor: sddl, NativeSecurityDescriptor: rawSD, NativeSecuritySHA256: semantic, SACLReadStatus: saclStatus, SACLUnavailableStage: saclUnavailableStage, SACLUnavailableWin32: saclUnavailableWin32, SACLUnavailableNTSTATUS: saclUnavailableNTSTATUS, Directory: directory}
	if hashFile {
		if directory {
			return fail(errors.New("cannot hash directory"))
		}
		s := sha256.New()
		var total int64
		buf := make([]byte, 64<<10)
		for {
			var n uint32
			e = windows.ReadFile(h, buf, &n, nil)
			if e != nil {
				return fail(e)
			}
			if n == 0 {
				break
			}
			total += int64(n)
			if total > 128<<20 {
				return fail(errors.New("hash input exceeds bound"))
			}
			_, _ = s.Write(buf[:n])
		}
		x.SHA256 = hex.EncodeToString(s.Sum(nil))
	}
	return nativeHold{path: path, handle: h, identity: x}, nil
}

func closeHolds(holds []nativeHold) error {
	var out error
	for i := len(holds) - 1; i >= 0; i-- {
		out = errors.Join(out, windows.CloseHandle(holds[i].handle))
	}
	return out
}

func identityEqual(a, b FileIdentity) bool {
	return strings.EqualFold(a.Path, b.Path) && strings.EqualFold(a.FinalUTF16, b.FinalUTF16) && a.Volume == b.Volume && a.FileID == b.FileID && a.SHA256 == b.SHA256 && a.SecurityDescriptor == b.SecurityDescriptor && a.NativeSecuritySHA256 == b.NativeSecuritySHA256 && a.SACLReadStatus == b.SACLReadStatus && a.SACLUnavailableStage == b.SACLUnavailableStage && a.SACLUnavailableWin32 == b.SACLUnavailableWin32 && a.SACLUnavailableNTSTATUS == b.SACLUnavailableNTSTATUS && a.Directory == b.Directory
}
func identityCoreEqual(a, b FileIdentity) bool {
	a.SecurityDescriptor = ""
	b.SecurityDescriptor = ""
	a.NativeSecurityDescriptor = nil
	b.NativeSecurityDescriptor = nil
	a.NativeSecuritySHA256 = ""
	b.NativeSecuritySHA256 = ""
	return identityEqual(a, b)
}

func pathAncestors(path string) []string {
	var xs []string
	for p := filepath.Dir(path); ; p = filepath.Dir(p) {
		xs = append(xs, p)
		if filepath.Dir(p) == p {
			break
		}
	}
	for i, j := 0, len(xs)-1; i < j; i, j = i+1, j-1 {
		xs[i], xs[j] = xs[j], xs[i]
	}
	return xs
}

func openPlanHolds(p EntryFencePlan) ([]nativeHold, error) {
	all := []FileIdentity{p.DataRoot, p.Database, p.Helper}
	all = append(all, p.Ancestors...)
	for _, t := range p.Targets {
		all = append(all, t.File)
	}
	want := map[string]FileIdentity{}
	for _, x := range all {
		semantic, e := nativeSecuritySemanticSHA256(x.NativeSecurityDescriptor)
		if e != nil || semantic != x.NativeSecuritySHA256 {
			return nil, fmt.Errorf("native security preimage invalid for %s: %w", x.Path, e)
		}
		sd := (*windows.SECURITY_DESCRIPTOR)(unsafe.Pointer(&x.NativeSecurityDescriptor[0]))
		if !sd.IsValid() || sd.String() != x.SecurityDescriptor {
			return nil, fmt.Errorf("native security preimage and SDDL disagree for %s", x.Path)
		}
		want[strings.ToLower(x.Path)] = x
	}
	for _, target := range p.Targets {
		_, semantic, e := nativeSecurityFromSDDL(target.InstalledSD)
		if e != nil || semantic != target.InstalledNativeSecuritySHA256 {
			return nil, fmt.Errorf("installed native descriptor digest invalid for %s: %w", target.File.Path, e)
		}
	}
	for _, x := range all {
		for _, a := range pathAncestors(x.Path) {
			if _, ok := want[strings.ToLower(a)]; !ok {
				return nil, fmt.Errorf("ancestor absent from frozen inventory: %s", a)
			}
		}
	}
	keys := make([]string, 0, len(want))
	for k := range want {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	var holds []nativeHold
	for _, k := range keys {
		x := want[k]
		h, e := openNative(x.Path, x.Directory, !x.Directory)
		if e != nil {
			closeHolds(holds)
			return nil, fmt.Errorf("open boundary identity %s: %w", x.Path, e)
		}
		matches := identityEqual(x, h.identity)
		if !matches {
			for _, target := range p.Targets {
				if strings.EqualFold(target.File.Path, x.Path) && identityCoreEqual(x, h.identity) && target.InstalledSD == h.identity.SecurityDescriptor && target.InstalledNativeSecuritySHA256 == h.identity.NativeSecuritySHA256 {
					matches = true
					break
				}
			}
		}
		if !matches {
			windows.CloseHandle(h.handle)
			closeHolds(holds)
			return nil, fmt.Errorf("boundary identity drift: %s", x.Path)
		}
		holds = append(holds, h)
	}
	return holds, nil
}

func checkHolds(holds []nativeHold) error {
	if len(holds) == 0 {
		return errors.New("native boundary holds missing")
	}
	for _, h := range holds {
		fresh, e := openNative(h.path, h.identity.Directory, !h.identity.Directory)
		if e != nil {
			return e
		}
		same := identityEqual(h.identity, fresh.identity)
		if e = windows.CloseHandle(fresh.handle); e != nil {
			return e
		}
		if !same {
			return fmt.Errorf("native boundary identity changed: %s", h.path)
		}
	}
	return nil
}

func registryRestartApps(businessSID string) (uint32, error) {
	if _, e := windows.StringToSid(businessSID); e != nil {
		return 0, e
	}
	k, e := registry.OpenKey(registry.USERS, businessSID+`\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon`, registry.QUERY_VALUE)
	if e != nil {
		return 0, e
	}
	defer k.Close()
	v, _, e := k.GetIntegerValue("RestartApps")
	if e != nil || v > 1 {
		return 0, errors.New("RestartApps registry state unavailable")
	}
	return uint32(v), nil
}

var getTick = windows.NewLazySystemDLL("kernel32.dll").NewProc("GetTickCount64")
var ntSystem = windows.NewLazySystemDLL("ntdll.dll").NewProc("NtQuerySystemInformation")
var ntSetSecurityObject = windows.NewLazySystemDLL("ntdll.dll").NewProc("NtSetSecurityObject")
var ntQuerySecurityObject = windows.NewLazySystemDLL("ntdll.dll").NewProc("NtQuerySecurityObject")
var getApplicationRestartSettings = windows.NewLazySystemDLL("kernel32.dll").NewProc("GetApplicationRestartSettings")

func restartSettingsForProcess(h windows.Handle) (string, uint32, bool, error) {
	var size, flags uint32
	r, _, _ := getApplicationRestartSettings.Call(uintptr(h), 0, uintptr(unsafe.Pointer(&size)), uintptr(unsafe.Pointer(&flags)))
	if uint32(r) == 0x80070490 {
		return "", 0, false, nil
	} // HRESULT_FROM_WIN32(ERROR_NOT_FOUND)
	if uint32(r) != 0 || size == 0 || size > 1025 {
		return "", 0, false, fmt.Errorf("restart registration size/status invalid: %#x/%d", uint32(r), size)
	}
	buf := make([]uint16, size)
	r, _, _ = getApplicationRestartSettings.Call(uintptr(h), uintptr(unsafe.Pointer(&buf[0])), uintptr(unsafe.Pointer(&size)), uintptr(unsafe.Pointer(&flags)))
	if uint32(r) != 0 || size == 0 || size > uint32(len(buf)) || flags&^uint32(0xf) != 0 {
		return "", 0, false, fmt.Errorf("restart registration read/status invalid: %#x/%d/%#x", uint32(r), size, flags)
	}
	return windows.UTF16ToString(buf[:size]), flags, true, nil
}

func bootClock() (uint64, time.Time, error) {
	u, _, e := getTick.Call()
	if e != windows.ERROR_SUCCESS && e != nil {
		return 0, time.Time{}, e
	}
	var x struct {
		BootTime          int64
		CurrentTime       int64
		TimeZoneBias      int64
		CurrentTimeZoneID uint32
		Reserved          uint32
		BootTimeBias      uint64
		SleepTimeBias     uint64
	}
	r, _, e := ntSystem.Call(3, uintptr(unsafe.Pointer(&x)), unsafe.Sizeof(x), 0)
	if r != 0 {
		return 0, time.Time{}, fmt.Errorf("NtQuerySystemInformation status %#x: %v", r, e)
	}
	if x.BootTime <= 0 {
		return 0, time.Time{}, errors.New("native boot time unavailable")
	}
	return uint64(u), time.Unix(0, (x.BootTime-116444736000000000)*100).UTC(), nil
}

func witness(p EntryFencePlan, fenceHash string) (BootWitness, error) {
	u, b, e := bootClock()
	if e != nil {
		return BootWitness{}, e
	}
	r, e := registryRestartApps(p.BusinessSID)
	if e != nil {
		return BootWitness{}, e
	}
	return BootWitness{Schema: WitnessSchema, OperationID: p.OperationID, PlanSHA256: p.PlanSHA256, HelperSHA256: p.Helper.SHA256, UTC: time.Now().UTC(), UptimeMilliseconds: u, LastBootUTC: b, RestartApps: r, FenceSHA256: fenceHash}, nil
}

func stateRoot(p EntryFencePlan) (string, error) {
	base := os.Getenv("ProgramData")
	if base == "" || !filepath.IsAbs(base) {
		return "", errors.New("ProgramData unavailable")
	}
	if !validOperation(p.OperationID) {
		return "", errors.New("operation invalid")
	}
	h := digest([]byte(strings.ToLower(p.DataRoot.FinalUTF16) + "\x00" + p.DataRoot.FileID))
	return filepath.Join(base, "ResearchOS", "RecoveryBoundary", h, p.OperationID), nil
}

func readRecord(p EntryFencePlan) (boundaryRecord, error) {
	var r boundaryRecord
	dir, e := stateRoot(p)
	if e != nil {
		return r, e
	}
	// The operation directory and every record must be independently protected.
	if e = checkManagedChain(p); e != nil {
		return r, e
	}
	if e = checkAcceptanceFiles(p); e != nil {
		return r, e
	}
	entries, e := os.ReadDir(dir)
	if e != nil {
		return r, e
	}
	if len(entries) < 2 || len(entries) > 24 {
		return r, errors.New("boundary state inventory invalid")
	}
	for _, entry := range entries {
		if entry.IsDir() || (entry.Name() != "plan.json" && entry.Name() != "pre.json" && entry.Name() != "post.json" && entry.Name() != "full-restart-complete.json" && entry.Name() != "source-accepted.json" && entry.Name() != "native-accepted.json" && entry.Name() != "backup-verified.json" && entry.Name() != "recovery-ready.json" && !strings.HasPrefix(entry.Name(), "event-")) {
			return r, errors.New("unknown boundary state entry")
		}
	}
	raw, _, e := readManagedFile(filepath.Join(dir, "plan.json"), p.ManagementSID, maxBoundaryPlanBytes)
	if e != nil {
		return r, errors.New("boundary plan file unavailable")
	}
	if e = json.Unmarshal(raw, &r.Plan); e != nil {
		return r, e
	}
	if r.Plan.OperationID != p.OperationID || r.Plan.PlanSHA256 != p.PlanSHA256 {
		return r, errors.New("boundary record plan mismatch")
	}
	pre, _, e := readManagedFile(filepath.Join(dir, "pre.json"), p.ManagementSID, 16<<10)
	if e != nil {
		return r, errors.New("boundary pre witness unavailable")
	}
	if e = json.Unmarshal(pre, &r.Pre); e != nil {
		return r, e
	}
	post, _, e := readManagedFile(filepath.Join(dir, "post.json"), p.ManagementSID, 16<<10)
	if e == nil {
		if e = json.Unmarshal(post, &r.Post); e != nil {
			return r, e
		}
	} else if !errors.Is(e, os.ErrNotExist) {
		return r, e
	}
	for i := 1; i <= 16; i++ {
		name := fmt.Sprintf("event-%02d.json", i)
		raw, _, e := readManagedFile(filepath.Join(dir, name), p.ManagementSID, 16<<10)
		if errors.Is(e, os.ErrNotExist) {
			break
		}
		if e != nil {
			return r, errors.New("boundary event missing or oversized")
		}
		var ev BoundaryEvent
		if e = json.Unmarshal(raw, &ev); e != nil {
			return r, e
		}
		r.Events = append(r.Events, ev)
	}
	if e = ValidateEvents(r.Events, p.OperationID, p.PlanSHA256); e != nil {
		return r, e
	}
	fullRestartRaw, _, fullRestartErr := readManagedFile(filepath.Join(dir, "full-restart-complete.json"), p.ManagementSID, 16<<10)
	if fullRestartErr != nil && !errors.Is(fullRestartErr, os.ErrNotExist) {
		return r, fullRestartErr
	}
	if !r.Post.UTC.IsZero() && (fullRestartErr != nil || digest(fullRestartRaw) != r.Post.FullRestartEvidenceSHA256) {
		return r, errors.New("FullRestart evidence drift")
	}
	if len(entries) != 6+len(r.Events)+boolInt(!r.Post.UTC.IsZero())+boolInt(fullRestartErr == nil) {
		return r, errors.New("boundary event inventory gap")
	}
	return r, nil
}
func boolInt(b bool) int {
	if b {
		return 1
	}
	return 0
}

func checkManagedDirectory(path, sid string) error {
	h, e := openNative(path, true, false)
	if e != nil {
		return e
	}
	defer windows.CloseHandle(h.handle)
	sd := (*windows.SECURITY_DESCRIPTOR)(unsafe.Pointer(&h.identity.NativeSecurityDescriptor[0]))
	return checkManagedDescriptor(sd, sid)
}

func checkManagedDescriptor(sd *windows.SECURITY_DESCRIPTOR, sid string) error {
	if sd == nil {
		return errors.New("management descriptor missing")
	}
	owner, _, e := sd.Owner()
	if e != nil || owner == nil || owner.String() != sid {
		return errors.New("boundary management owner mismatch")
	}
	control, _, e := sd.Control()
	if e != nil || control&windows.SE_DACL_PROTECTED == 0 {
		return errors.New("boundary state DACL not protected")
	}
	acl, _, e := sd.DACL()
	if e != nil || acl == nil || acl.AceCount < 1 || acl.AceCount > 2 {
		return errors.New("boundary state DACL inventory invalid")
	}
	managerFull := false
	for i := uint32(0); i < uint32(acl.AceCount); i++ {
		var ace *windows.ACCESS_ALLOWED_ACE
		if e = windows.GetAce(acl, i, &ace); e != nil {
			return e
		}
		if ace.Header.AceType != windows.ACCESS_ALLOWED_ACE_TYPE || ace.Header.AceFlags&windows.INHERIT_ONLY_ACE != 0 {
			return errors.New("boundary state ACE type forbidden")
		}
		trustee := (*windows.SID)(unsafe.Pointer(&ace.SidStart)).String()
		if trustee != sid && trustee != "S-1-5-18" {
			return errors.New("boundary state nonmanagement ACE forbidden")
		}
		if trustee == sid && uint32(ace.Mask)&0x001f01ff == 0x001f01ff {
			managerFull = true
		} // FILE_ALL_ACCESS
	}
	if !managerFull {
		return errors.New("boundary state manager full access absent")
	}
	return nil
}

// Every state/attestation file is read from the same pinned native handle
// whose owner, protected DACL and non-reparse/single-link identity passed.
func readManagedFile(path, managerSID string, limit int) ([]byte, FileIdentity, error) {
	h, err := openNativeAccess(path, false, false, 0)
	if errors.Is(err, windows.ERROR_FILE_NOT_FOUND) {
		return nil, FileIdentity{}, os.ErrNotExist
	}
	if err != nil {
		return nil, FileIdentity{}, err
	}
	defer windows.CloseHandle(h.handle)
	sd := (*windows.SECURITY_DESCRIPTOR)(unsafe.Pointer(&h.identity.NativeSecurityDescriptor[0]))
	if err = checkManagedDescriptor(sd, managerSID); err != nil {
		return nil, FileIdentity{}, fmt.Errorf("unprotected boundary file %s: %w", path, err)
	}
	raw, err := readPinnedBounded(h.handle, limit)
	if err != nil {
		return nil, FileIdentity{}, err
	}
	h.identity.SHA256 = digest(raw)
	return raw, h.identity, nil
}

func readPinnedBounded(handle windows.Handle, limit int) ([]byte, error) {
	var raw []byte
	buf := make([]byte, 32<<10)
	for {
		var n uint32
		if err := windows.ReadFile(handle, buf, &n, nil); err != nil {
			return nil, err
		}
		if n == 0 {
			break
		}
		if len(raw)+int(n) > limit {
			return nil, errors.New("boundary file exceeds read limit")
		}
		raw = append(raw, buf[:n]...)
	}
	return raw, nil
}

func checkManagedChain(p EntryFencePlan) error {
	dir, e := stateRoot(p)
	if e != nil {
		return e
	}
	base := os.Getenv("ProgramData")
	for _, path := range pathAncestors(dir) {
		if strings.EqualFold(path, base) {
			continue
		}
		if strings.HasPrefix(strings.ToLower(path), strings.ToLower(base)+string(filepath.Separator)) {
			if e = checkManagedDirectory(path, p.ManagementSID); e != nil {
				return e
			}
		}
	}
	return checkManagedDirectory(dir, p.ManagementSID)
}

func checkCurrentBoot(post BootWitness, businessSID string) error {
	u, b, e := bootClock()
	if e != nil {
		return e
	}
	if b.Before(post.LastBootUTC.Add(-2*time.Second)) || b.After(post.LastBootUTC.Add(2*time.Second)) || u < post.UptimeMilliseconds {
		return errors.New("current boot differs from post witness")
	}
	if time.Since(post.UTC) < 0 || time.Since(post.UTC) > MaxElapsed {
		return errors.New("post witness expired")
	}
	r, e := registryRestartApps(businessSID)
	if e != nil {
		return e
	}
	if r != post.RestartApps {
		return errors.New("RestartApps state changed")
	}
	return nil
}

func checkPreCurrent(pre BootWitness, businessSID string) error {
	u, b, e := bootClock()
	if e != nil {
		return e
	}
	if b.Before(pre.LastBootUTC.Add(-2*time.Second)) || b.After(pre.LastBootUTC.Add(2*time.Second)) || u < pre.UptimeMilliseconds {
		return errors.New("pre witness boot changed before arm")
	}
	if time.Since(pre.UTC) < 0 || time.Since(pre.UTC) > MaxElapsed {
		return errors.New("pre witness expired before arm")
	}
	r, e := registryRestartApps(businessSID)
	if e != nil {
		return e
	}
	if r != pre.RestartApps {
		return errors.New("RestartApps changed before arm")
	}
	return nil
}

func checkFence(p EntryFencePlan, holds []nativeHold) error {
	byPath := map[string]FileIdentity{}
	for _, h := range holds {
		byPath[strings.ToLower(h.path)] = h.identity
	}
	for _, t := range p.Targets {
		x, ok := byPath[strings.ToLower(t.File.Path)]
		if !ok || !identityCoreEqual(x, t.File) || t.InstalledSD == "" || x.SecurityDescriptor != t.InstalledSD || x.NativeSecuritySHA256 != t.InstalledNativeSecuritySHA256 {
			return errors.New("fence target readback mismatch")
		}
		expected, e := denyDescriptor(t.File.SecurityDescriptor, p.BusinessSID, p.ManagementSID, t.Mode)
		if e != nil || expected != x.SecurityDescriptor {
			return errors.New("business SID exact deny descriptor absent")
		}
	}
	return nil
}

func businessEnabledGroupDigest(p EntryFencePlan) (string, error) {
	claimed := append([]string(nil), p.BusinessGroupSIDs...)
	sort.Strings(claimed)
	for i, sid := range claimed {
		if _, err := windows.StringToSid(sid); err != nil || (i > 0 && sid == claimed[i-1]) {
			return "", errors.New("invalid business enabled group inventory")
		}
	}
	raw, _ := json.Marshal(claimed)
	return digest(raw), nil
}

// Before plan, inspect a live exact official executable's token. Later phases
// use the protected pre witness because the fence deliberately stops that app.
func verifiedBusinessGroups(p EntryFencePlan) (map[string]bool, error) {
	expected, err := businessEnabledGroupDigest(p)
	if err != nil {
		return nil, err
	}
	dir, err := stateRoot(p)
	if err != nil {
		return nil, err
	}
	var pre BootWitness
	if raw, _, readErr := readManagedFile(filepath.Join(dir, "pre.json"), p.ManagementSID, 16<<10); readErr == nil {
		if len(raw) > 16<<10 || json.Unmarshal(raw, &pre) != nil || pre.OperationID != p.OperationID || pre.PlanSHA256 != p.PlanSHA256 || pre.BusinessEnabledSIDsSHA256 != expected {
			return nil, errors.New("business token witness mismatch")
		}
		// The pre token was captured before the fence. A restart may change
		// group activation, so an active business logon token must still match.
		shape, captureErr := inspectExistingBusinessProcess(p, expected, pre)
		if captureErr != nil {
			return nil, captureErr
		}
		if postRaw, _, postErr := readManagedFile(filepath.Join(dir, "post.json"), p.ManagementSID, 16<<10); postErr == nil {
			var post BootWitness
			if len(postRaw) > 16<<10 || json.Unmarshal(postRaw, &post) != nil || post.OperationID != p.OperationID || post.PlanSHA256 != p.PlanSHA256 || sameCurrentProcessWitness(post, shape) != nil {
				return nil, errors.New("current business process identity differs from post witness")
			}
		} else if !errors.Is(postErr, os.ErrNotExist) {
			return nil, postErr
		}
		return shape.EffectiveSIDs, nil
	} else if !errors.Is(readErr, os.ErrNotExist) {
		return nil, readErr
	} else {
		shape, captureErr := captureOfficialBusinessToken(p, expected)
		if captureErr != nil {
			return nil, captureErr
		}
		return shape.EffectiveSIDs, nil
	}
}

func tokenGroupState(token windows.Token, businessSID string) (string, map[string]bool, string, error) {
	user, userErr := token.GetTokenUser()
	groups, groupsErr := token.GetTokenGroups()
	if userErr != nil || groupsErr != nil {
		return "", nil, "", errors.Join(userErr, groupsErr)
	}
	if user.User.Sid.String() != businessSID {
		return "", nil, "", errors.New("native token user differs from frozen business SID")
	}
	return potentialGroupState(groups.AllGroups(), businessSID)
}

// A normal disabled group may be enabled later with AdjustTokenGroups. Only
// USE_FOR_DENY_ONLY is irreversibly excluded from ALLOW ACE matching.
func potentialGroupState(groups []windows.SIDAndAttributes, businessSID string) (string, map[string]bool, string, error) {
	var stable []string
	var logonSID string
	potential := map[string]bool{businessSID: true}
	for _, group := range groups {
		if group.Attributes&windows.SE_GROUP_LOGON_ID == windows.SE_GROUP_LOGON_ID {
			if logonSID != "" {
				return "", nil, "", errors.New("multiple token logon SIDs")
			}
			logonSID = group.Sid.String()
		}
		if group.Attributes&windows.SE_GROUP_USE_FOR_DENY_ONLY == 0 {
			potential[group.Sid.String()] = true
			// Logon SID and integrity label are per logon/boot. Keep them in
			// the current potential-access map, but not in the frozen hash.
			if group.Attributes&(windows.SE_GROUP_LOGON_ID|windows.SE_GROUP_INTEGRITY) == 0 {
				stable = append(stable, group.Sid.String())
			}
		}
	}
	if logonSID == "" {
		return "", nil, "", errors.New("token logon SID unavailable")
	}
	sort.Strings(stable)
	raw, _ := json.Marshal(stable)
	return digest(raw), potential, logonSID, nil
}

type businessTokenShape struct {
	SessionID        uint32
	ElevationType    uint32
	IntegritySID     string
	LogonSID         string
	PrivilegesSHA256 string
	GroupsSHA256     string
	EffectiveSIDs    map[string]bool
	ProcessID        uint32
	ProcessCreated   time.Time
	ProcessImageSHA  string
}

func tokenInfoBytes(token windows.Token, class uint32) ([]byte, error) {
	buf := make([]byte, 128)
	for {
		var size uint32
		err := windows.GetTokenInformation(token, class, &buf[0], uint32(len(buf)), &size)
		if err == nil {
			if size > uint32(len(buf)) {
				return nil, errors.New("token information size invalid")
			}
			return buf[:size], nil
		}
		if !errors.Is(err, windows.ERROR_INSUFFICIENT_BUFFER) || size > 64<<10 || size <= uint32(len(buf)) {
			return nil, err
		}
		buf = make([]byte, size)
	}
}

func tokenSecurityShape(token windows.Token, pid uint32, businessSID string) (businessTokenShape, error) {
	var shape businessTokenShape
	var session, elevation, size uint32
	if err := windows.ProcessIdToSessionId(pid, &session); err != nil {
		return shape, err
	}
	if err := windows.GetTokenInformation(token, windows.TokenElevationType, (*byte)(unsafe.Pointer(&elevation)), 4, &size); err != nil || size != 4 {
		return shape, errors.Join(err, errors.New("token elevation type unavailable"))
	}
	labelBytes, err := tokenInfoBytes(token, windows.TokenIntegrityLevel)
	if err != nil || len(labelBytes) < int(unsafe.Sizeof(windows.Tokenmandatorylabel{})) {
		return shape, errors.Join(err, errors.New("token integrity label unavailable"))
	}
	groupSHA, effective, logonSID, err := tokenGroupState(token, businessSID)
	if err != nil {
		return shape, err
	}
	privBytes, err := tokenInfoBytes(token, windows.TokenPrivileges)
	if err != nil || len(privBytes) < int(unsafe.Sizeof(windows.Tokenprivileges{})) {
		return shape, errors.Join(err, errors.New("token privileges unavailable"))
	}
	var privilegeLines []string
	for _, priv := range (*windows.Tokenprivileges)(unsafe.Pointer(&privBytes[0])).AllPrivileges() {
		privilegeLines = append(privilegeLines, fmt.Sprintf("%08x:%08x:%08x", uint32(priv.Luid.HighPart), priv.Luid.LowPart, priv.Attributes))
	}
	sort.Strings(privilegeLines)
	privJSON, _ := json.Marshal(privilegeLines)
	shape = businessTokenShape{SessionID: session, ElevationType: elevation, IntegritySID: (*windows.Tokenmandatorylabel)(unsafe.Pointer(&labelBytes[0])).Label.Sid.String(), LogonSID: logonSID, PrivilegesSHA256: digest(privJSON), GroupsSHA256: groupSHA, EffectiveSIDs: effective}
	return shape, nil
}

// Existing Explorer supplies a fresh business process token after restart.
// Its current PID, session and logon SID are evidence, never compared to the
// pre-restart values. Elevated-admin cross-account TOKEN_QUERY is probed.
func inspectExistingBusinessProcess(p EntryFencePlan, expected string, pre BootWitness) (businessTokenShape, error) {
	var zero businessTokenShape
	if pre.BusinessLogonSID == "" || !validDigest(pre.BusinessPrivilegesSHA256) || pre.BusinessIntegritySID == "" {
		return zero, errors.New("pre business token shape unavailable")
	}
	systemRoot, rootErr := windows.GetSystemWindowsDirectory()
	if rootErr != nil || !filepath.IsAbs(systemRoot) || filepath.Clean(systemRoot) != systemRoot {
		return zero, errors.Join(rootErr, errors.New("native system root unavailable"))
	}
	explorerPath := filepath.Join(systemRoot, "explorer.exe")
	_, currentBoot, err := bootClock()
	if err != nil {
		return zero, err
	}
	snapshot, err := windows.CreateToolhelp32Snapshot(windows.TH32CS_SNAPPROCESS, 0)
	if err != nil {
		return zero, err
	}
	defer windows.CloseHandle(snapshot)
	var entry windows.ProcessEntry32
	entry.Size = uint32(unsafe.Sizeof(entry))
	if err = windows.Process32First(snapshot, &entry); err != nil {
		return zero, err
	}
	var matched *businessTokenShape
	for {
		if strings.EqualFold(windows.UTF16ToString(entry.ExeFile[:]), "explorer.exe") {
			proc, openErr := windows.OpenProcess(windows.PROCESS_QUERY_LIMITED_INFORMATION, false, entry.ProcessID)
			if openErr != nil {
				return zero, fmt.Errorf("Explorer candidate inaccessible: %w", openErr)
			}
			buf := make([]uint16, 32768)
			n := uint32(len(buf))
			imageErr := windows.QueryFullProcessImageName(proc, 0, &buf[0], &n)
			if imageErr != nil {
				windows.CloseHandle(proc)
				return zero, imageErr
			}
			if !strings.EqualFold(windows.UTF16ToString(buf[:n]), explorerPath) {
				windows.CloseHandle(proc)
				goto nextProcess
			}
			var created, exited, kernel, userTime windows.Filetime
			if err = windows.GetProcessTimes(proc, &created, &exited, &kernel, &userTime); err != nil || time.Unix(0, created.Nanoseconds()).Before(currentBoot.Add(-2*time.Second)) {
				windows.CloseHandle(proc)
				return zero, errors.Join(err, errors.New("Explorer creation predates current boot"))
			}
			var token windows.Token
			tokenErr := windows.OpenProcessToken(proc, windows.TOKEN_QUERY, &token)
			if tokenErr != nil {
				windows.CloseHandle(proc)
				return zero, tokenErr
			}
			user, userErr := token.GetTokenUser()
			if userErr != nil {
				token.Close()
				windows.CloseHandle(proc)
				return zero, userErr
			}
			if user.User.Sid.String() != p.BusinessSID {
				token.Close()
				windows.CloseHandle(proc)
				goto nextProcess
			}
			shape, shapeErr := tokenSecurityShape(token, entry.ProcessID, p.BusinessSID)
			closeErr := token.Close()
			if shapeErr != nil || closeErr != nil {
				windows.CloseHandle(proc)
				return zero, errors.Join(shapeErr, closeErr)
			}
			imageSHA, imageErr := osProcessImageIdentity(explorerPath)
			closeErr = windows.CloseHandle(proc)
			if imageErr != nil || closeErr != nil {
				return zero, errors.Join(imageErr, closeErr)
			}
			shape.ProcessID = entry.ProcessID
			shape.ProcessCreated = time.Unix(0, created.Nanoseconds()).UTC()
			shape.ProcessImageSHA = imageSHA
			if err := sameBusinessPermissionSemantics(pre, shape, expected); err != nil {
				return zero, err
			}
			if matched != nil {
				if matched.SessionID != shape.SessionID || matched.LogonSID != shape.LogonSID || matched.ProcessImageSHA != shape.ProcessImageSHA {
					return zero, errors.New("multiple current business Explorer sessions ambiguous")
				}
				if shape.ProcessCreated.Before(matched.ProcessCreated) {
					matched = &shape
				}
			} else {
				matched = &shape
			}
		}
	nextProcess:
		err = windows.Process32Next(snapshot, &entry)
		if errors.Is(err, windows.ERROR_NO_MORE_FILES) {
			break
		}
		if err != nil {
			return zero, err
		}
	}
	if matched == nil {
		return zero, errors.New("current business Explorer token unavailable")
	}
	return *matched, nil
}

func sameBusinessPermissionSemantics(pre BootWitness, current businessTokenShape, expected string) error {
	if current.LogonSID == "" || current.IntegritySID == "" || current.GroupsSHA256 != expected || current.ElevationType != pre.BusinessElevationType || current.IntegritySID != pre.BusinessIntegritySID || current.PrivilegesSHA256 != pre.BusinessPrivilegesSHA256 {
		return errors.New("current business token permission semantics differ from pre witness")
	}
	return nil
}

func sameCurrentProcessWitness(post BootWitness, current businessTokenShape) error {
	if post.BusinessEnabledSIDsSHA256 != current.GroupsSHA256 || post.BusinessSessionID != current.SessionID || post.BusinessLogonSID != current.LogonSID || post.BusinessProcessPID != current.ProcessID || !post.BusinessProcessCreatedUTC.Equal(current.ProcessCreated) || post.BusinessProcessImageSHA256 != current.ProcessImageSHA {
		return errors.New("current business process identity changed")
	}
	return nil
}

// Windows may legitimately hard-link its own Explorer image. Read identity
// from one held native handle without applying the product target's hard-link
// ban to this OS image.
func osProcessImageIdentity(path string) (string, error) {
	ptr, err := windows.UTF16PtrFromString(path)
	if err != nil {
		return "", err
	}
	h, err := windows.CreateFile(ptr, windows.FILE_READ_DATA|windows.FILE_READ_ATTRIBUTES,
		windows.FILE_SHARE_READ|windows.FILE_SHARE_WRITE, nil, windows.OPEN_EXISTING,
		windows.FILE_FLAG_OPEN_REPARSE_POINT, 0)
	if err != nil {
		return "", err
	}
	defer windows.CloseHandle(h)
	var info windows.ByHandleFileInformation
	if err = windows.GetFileInformationByHandle(h, &info); err != nil {
		return "", err
	}
	if info.FileAttributes&(windows.FILE_ATTRIBUTE_DIRECTORY|windows.FILE_ATTRIBUTE_REPARSE_POINT) != 0 {
		return "", errors.New("OS process image is directory or reparse point")
	}
	volume, fileID, err := nativeFileID(h)
	if err != nil {
		return "", err
	}
	final, err := finalPath(h)
	if err != nil {
		return "", err
	}
	sum := sha256.New()
	buf := make([]byte, 64<<10)
	var total int64
	for {
		var n uint32
		if err = windows.ReadFile(h, buf, &n, nil); err != nil {
			return "", err
		}
		if n == 0 {
			break
		}
		total += int64(n)
		if total > 128<<20 {
			return "", errors.New("OS process image exceeds hash bound")
		}
		_, _ = sum.Write(buf[:n])
	}
	return digest([]byte(fmt.Sprintf("%s|%d|%s|%x", strings.ToLower(final), volume, fileID, sum.Sum(nil)))), nil
}

func inspectLiveBusinessToken(p EntryFencePlan, expected string) error {
	_, err := captureOfficialBusinessToken(p, expected)
	return err
}

func captureOfficialBusinessToken(p EntryFencePlan, expected string) (businessTokenShape, error) {
	var zero businessTokenShape
	snapshot, err := windows.CreateToolhelp32Snapshot(windows.TH32CS_SNAPPROCESS, 0)
	if err != nil {
		return zero, err
	}
	defer windows.CloseHandle(snapshot)
	var entry windows.ProcessEntry32
	entry.Size = uint32(unsafe.Sizeof(entry))
	if err = windows.Process32First(snapshot, &entry); err != nil {
		return zero, err
	}
	for {
		for _, target := range p.Targets {
			if target.Mode != "executable" || !strings.EqualFold(windows.UTF16ToString(entry.ExeFile[:]), filepath.Base(target.File.Path)) {
				continue
			}
			proc, openErr := windows.OpenProcess(windows.PROCESS_QUERY_LIMITED_INFORMATION, false, entry.ProcessID)
			if openErr != nil {
				return zero, openErr
			}
			buf := make([]uint16, 32768)
			n := uint32(len(buf))
			nameErr := windows.QueryFullProcessImageName(proc, 0, &buf[0], &n)
			if nameErr != nil {
				windows.CloseHandle(proc)
				return zero, nameErr
			}
			if !strings.EqualFold(windows.UTF16ToString(buf[:n]), target.File.Path) {
				windows.CloseHandle(proc)
				continue
			}
			var token windows.Token
			tokenErr := windows.OpenProcessToken(proc, windows.TOKEN_QUERY, &token)
			var created, exited, kernel, userTime windows.Filetime
			timeErr := windows.GetProcessTimes(proc, &created, &exited, &kernel, &userTime)
			windows.CloseHandle(proc)
			if tokenErr != nil || timeErr != nil {
				if tokenErr == nil {
					token.Close()
				}
				return zero, errors.Join(tokenErr, timeErr)
			}
			shape, shapeErr := tokenSecurityShape(token, entry.ProcessID, p.BusinessSID)
			closeErr := token.Close()
			if shapeErr != nil || closeErr != nil {
				return zero, errors.Join(shapeErr, closeErr)
			}
			if shape.GroupsSHA256 != expected {
				return zero, errors.New("actual business token enabled groups differ from frozen inventory")
			}
			shape.ProcessID = entry.ProcessID
			shape.ProcessCreated = time.Unix(0, created.Nanoseconds()).UTC()
			shape.ProcessImageSHA = digest([]byte(fmt.Sprintf("%s|%d|%s|%s", strings.ToLower(target.File.FinalUTF16), target.File.Volume, target.File.FileID, target.File.SHA256)))
			return shape, nil
		}
		err = windows.Process32Next(snapshot, &entry)
		if errors.Is(err, windows.ERROR_NO_MORE_FILES) {
			return zero, errors.New("exact official process token unavailable for ancestor proof")
		}
		if err != nil {
			return zero, err
		}
	}
}

func checkAncestorControl(p EntryFencePlan, holds []nativeHold) error {
	enabled, err := verifiedBusinessGroups(p)
	if err != nil {
		return err
	}
	return checkAncestorACL(p, holds, enabled)
}

func checkAncestorACL(p EntryFencePlan, holds []nativeHold, enabled map[string]bool) error {
	protected := map[string]bool{}
	for _, a := range p.Ancestors {
		protected[strings.ToLower(a.Path)] = true
	}
	protected[strings.ToLower(p.DataRoot.Path)] = true
	for _, h := range holds {
		if !protected[strings.ToLower(h.path)] {
			continue
		}
		sd, e := windows.SecurityDescriptorFromString(h.identity.SecurityDescriptor)
		if e != nil {
			return e
		}
		owner, _, e := sd.Owner()
		osAnchor := filepath.Dir(h.path) == h.path || strings.EqualFold(h.path, filepath.Join(filepath.VolumeName(h.path)+`\`, "Users"))
		ownerTrusted := owner != nil && (owner.String() == p.ManagementSID || owner.String() == "S-1-5-18" || (osAnchor && owner.String() == "S-1-5-80-956008885-3418522649-1831038044-1853292631-2271478464"))
		if e != nil || !ownerTrusted || enabled[owner.String()] {
			return fmt.Errorf("ancestor owner can revoke boundary: %s", h.path)
		}
		acl, _, e := sd.DACL()
		if e != nil || acl == nil {
			return fmt.Errorf("ancestor DACL unavailable: %s", h.path)
		}
		for i := uint32(0); i < uint32(acl.AceCount); i++ {
			var ace *windows.ACCESS_ALLOWED_ACE
			if e = windows.GetAce(acl, i, &ace); e != nil {
				return e
			}
			if ace.Header.AceFlags&windows.INHERIT_ONLY_ACE != 0 || ace.Header.AceType == windows.ACCESS_DENIED_ACE_TYPE {
				continue
			}
			if ace.Header.AceType != windows.ACCESS_ALLOWED_ACE_TYPE {
				return fmt.Errorf("ancestor ACL ACE unsupported: %s", h.path)
			}
			trustee := (*windows.SID)(unsafe.Pointer(&ace.SidStart)).String()
			if !enabled[trustee] {
				continue
			}
			forbidden := uint32(0x40 | windows.WRITE_DAC | windows.WRITE_OWNER | windows.GENERIC_ALL) // FILE_DELETE_CHILD; GENERIC_WRITE maps to file writes only.
			if filepath.Dir(h.path) != h.path {
				forbidden |= windows.DELETE
			}
			if uint32(ace.Mask)&forbidden != 0 {
				return fmt.Errorf("business group can replace ancestor: %s", h.path)
			}
		}
	}
	return nil
}

func preflightManagementRestore(p EntryFencePlan) error {
	for _, t := range p.Targets {
		original, e := windows.SecurityDescriptorFromString(t.File.SecurityDescriptor)
		if e != nil {
			return e
		}
		owner, _, e := original.Owner()
		if e != nil || owner == nil {
			return errors.New("original target owner unavailable for restore preflight")
		}
		access := uint32(windows.WRITE_DAC)
		if owner.String() != p.ManagementSID {
			access |= windows.WRITE_OWNER
		}
		h, e := openNativeAccess(t.File.Path, false, true, access)
		if e != nil {
			return fmt.Errorf("management cannot open target for reversible ACL operation: %w", e)
		}
		matched := identityEqual(h.identity, t.File)
		closeErr := windows.CloseHandle(h.handle)
		if closeErr != nil {
			return closeErr
		}
		if !matched {
			return errors.New("management ACL preflight target identity drift")
		}
		if owner.String() != p.ManagementSID {
			if e = ensureOwnerRestorable(p.ManagementSID, owner); e != nil {
				return fmt.Errorf("management cannot restore original owner before APPLYING: %w", e)
			}
		}
	}
	return nil
}

func ownerAssignableWithoutRestore(token windows.Token, owner *windows.SID) (bool, error) {
	user, err := token.GetTokenUser()
	if err != nil {
		return false, err
	}
	if user.User.Sid.Equals(owner) {
		return true, nil
	}
	groups, err := token.GetTokenGroups()
	if err != nil {
		return false, err
	}
	for _, group := range groups.AllGroups() {
		if group.Sid.Equals(owner) && group.Attributes&windows.SE_GROUP_OWNER != 0 && group.Attributes&windows.SE_GROUP_ENABLED != 0 && group.Attributes&windows.SE_GROUP_USE_FOR_DENY_ONLY == 0 {
			return true, nil
		}
	}
	return false, nil
}

// NtSetSecurityObject can restore a foreign original owner only while the actual
// mutation process token has SeRestorePrivilege enabled. A WRITE_OWNER handle
// alone proves only that it can assign an eligible owner.
func ensureOwnerRestorable(managementSID string, originalOwner *windows.SID) error {
	var token windows.Token
	if err := windows.OpenProcessToken(windows.CurrentProcess(), windows.TOKEN_QUERY|windows.TOKEN_ADJUST_PRIVILEGES, &token); err != nil {
		return err
	}
	defer token.Close()
	user, err := token.GetTokenUser()
	if err != nil || user.User.Sid.String() != managementSID {
		return errors.New("owner restore token is not frozen management SID")
	}
	eligible, err := ownerAssignableWithoutRestore(token, originalOwner)
	if err != nil || eligible {
		return err
	}
	name, err := windows.UTF16PtrFromString("SeRestorePrivilege")
	if err != nil {
		return err
	}
	var luid windows.LUID
	if err = windows.LookupPrivilegeValue(nil, name, &luid); err != nil {
		return err
	}
	privilegePresent := func() (bool, bool, error) {
		raw, err := tokenInfoBytes(token, windows.TokenPrivileges)
		if err != nil || len(raw) < 4 {
			return false, false, errors.Join(err, errors.New("restore privilege inventory unavailable"))
		}
		for _, privilege := range (*windows.Tokenprivileges)(unsafe.Pointer(&raw[0])).AllPrivileges() {
			if privilege.Luid == luid {
				return true, privilege.Attributes&windows.SE_PRIVILEGE_ENABLED != 0, nil
			}
		}
		return false, false, nil
	}
	present, enabled, err := privilegePresent()
	if err != nil {
		return err
	}
	if !present {
		return errors.New("SeRestorePrivilege not assigned to management token")
	}
	if !enabled {
		state := windows.Tokenprivileges{PrivilegeCount: 1, Privileges: [1]windows.LUIDAndAttributes{{Luid: luid, Attributes: windows.SE_PRIVILEGE_ENABLED}}}
		if err = windows.AdjustTokenPrivileges(token, false, &state, 0, nil, nil); err != nil {
			return fmt.Errorf("enable SeRestorePrivilege: %w", err)
		}
		_, enabled, err = privilegePresent()
		if err != nil {
			return err
		}
	}
	if !enabled {
		return errors.New("SeRestorePrivilege absent after enable readback")
	}
	return nil
}

func preflightInstalledRestore(p EntryFencePlan, byPath map[string]FileIdentity) error {
	for _, target := range p.Targets {
		observed := byPath[strings.ToLower(target.File.Path)]
		if observed.SecurityDescriptor == target.File.SecurityDescriptor && observed.NativeSecuritySHA256 == target.File.NativeSecuritySHA256 {
			continue
		}
		original, err := windows.SecurityDescriptorFromString(target.File.SecurityDescriptor)
		if err != nil {
			return err
		}
		owner, _, err := original.Owner()
		if err != nil || owner == nil {
			return errors.New("disarm original owner unavailable")
		}
		access := uint32(windows.WRITE_DAC)
		if owner.String() != p.ManagementSID {
			access |= windows.WRITE_OWNER
		}
		h, err := openNativeAccess(target.File.Path, false, true, access)
		if err != nil {
			return fmt.Errorf("disarm mutation handle unavailable: %w", err)
		}
		matching := identityCoreEqual(h.identity, target.File) && h.identity.SecurityDescriptor == target.InstalledSD && h.identity.NativeSecuritySHA256 == target.InstalledNativeSecuritySHA256
		closeErr := windows.CloseHandle(h.handle)
		if closeErr != nil || !matching {
			return errors.Join(closeErr, errors.New("disarm mutation handle identity or installed descriptor drift"))
		}
		if owner.String() != p.ManagementSID {
			if err = ensureOwnerRestorable(p.ManagementSID, owner); err != nil {
				return fmt.Errorf("disarm original owner not restorable: %w", err)
			}
		}
	}
	return nil
}

func denyDescriptor(original, sidText, managementSID, mode string) (string, error) {
	sid, e := windows.StringToSid(sidText)
	if e != nil {
		return "", e
	}
	sd, e := windows.SecurityDescriptorFromString(original)
	if e != nil {
		return "", e
	}
	old, _, e := sd.DACL()
	if e != nil {
		return "", e
	}
	mask := windows.ACCESS_MASK(windows.FILE_EXECUTE)
	if mode == "script" {
		mask = windows.ACCESS_MASK(windows.FILE_READ_DATA)
	} else if mode != "executable" {
		return "", errors.New("unknown target mode")
	}
	if managementSID != sidText {
		mask |= windows.ACCESS_MASK(windows.WRITE_DAC | windows.WRITE_OWNER | windows.DELETE | windows.FILE_WRITE_DATA | windows.FILE_APPEND_DATA)
	}
	ace := windows.EXPLICIT_ACCESS{AccessPermissions: mask, AccessMode: windows.DENY_ACCESS, Inheritance: windows.NO_INHERITANCE,
		Trustee: windows.TRUSTEE{TrusteeForm: windows.TRUSTEE_IS_SID, TrusteeType: windows.TRUSTEE_IS_USER, TrusteeValue: windows.TrusteeValueFromSID(sid)}}
	entries := []windows.EXPLICIT_ACCESS{ace}
	if managementSID != sidText {
		manager, e := windows.StringToSid(managementSID)
		if e != nil {
			return "", e
		}
		entries = append(entries, windows.EXPLICIT_ACCESS{AccessPermissions: windows.ACCESS_MASK(windows.FILE_READ_DATA | windows.FILE_READ_ATTRIBUTES | windows.READ_CONTROL | windows.WRITE_DAC | windows.WRITE_OWNER), AccessMode: windows.GRANT_ACCESS, Inheritance: windows.NO_INHERITANCE,
			Trustee: windows.TRUSTEE{TrusteeForm: windows.TRUSTEE_IS_SID, TrusteeType: windows.TRUSTEE_IS_USER, TrusteeValue: windows.TrusteeValueFromSID(manager)}})
	}
	acl, e := windows.ACLFromEntries(entries, old)
	if e != nil {
		return "", e
	}
	// Protecting a DACL makes formerly inherited ACEs explicit on the object.
	// Normalize the planned descriptor to the native readback representation.
	for i := uint32(0); i < uint32(acl.AceCount); i++ {
		var item *windows.ACCESS_ALLOWED_ACE
		if e = windows.GetAce(acl, i, &item); e != nil {
			return "", e
		}
		item.Header.AceFlags &^= windows.INHERITED_ACE
	}
	abs, e := sd.ToAbsolute()
	if e != nil {
		return "", e
	}
	if managementSID != sidText {
		manager, e := windows.StringToSid(managementSID)
		if e != nil {
			return "", e
		}
		if e = abs.SetOwner(manager, false); e != nil {
			return "", e
		}
	}
	if e = abs.SetDACL(acl, true, false); e != nil {
		return "", e
	}
	if e = abs.SetControl(windows.SE_DACL_PROTECTED, windows.SE_DACL_PROTECTED); e != nil {
		return "", e
	}
	installed, e := abs.ToSelfRelative()
	if e != nil {
		return "", e
	}
	return installed.String(), nil
}

// OpenCurrentQuiescence reopens a protected BOOT_OBSERVED record. It then
// retains native no-delete holds through the caller's actual outer transaction.
func OpenCurrentQuiescence(ctx context.Context, held *rt.DataRootLease, dataRoot, database, operationID, planSHA256 string) (*CurrentQuiescence, error) {
	if e := ctx.Err(); e != nil {
		return nil, e
	}
	if held == nil || !held.Held() || held.Root() != dataRoot || database != filepath.Join(dataRoot, "researchos.sqlite") || !validOperation(operationID) || !validDigest(planSHA256) {
		return nil, errors.New("current quiescence held lease or binding invalid")
	}
	lease, e := held.MaintenanceIdentity()
	if e != nil {
		return nil, e
	}
	// Discovery is by fixed ProgramData inventory. We never accept a path from
	// a caller or a JSON supplied capability.
	p, e := discoverPlan(dataRoot, operationID, planSHA256)
	if e != nil {
		return nil, e
	}
	if e = ValidatePlan(p); e != nil {
		return nil, e
	}
	if e = managedToken(p); e != nil {
		return nil, e
	}
	if p.DataRoot.Path != dataRoot || p.Database.Path != database {
		return nil, errors.New("current quiescence source mismatch")
	}
	holds, e := openPlanHolds(p)
	if e != nil {
		return nil, e
	}
	fail := func(e error) (*CurrentQuiescence, error) { return nil, errors.Join(e, closeHolds(holds)) }
	r, e := readRecord(p)
	if e != nil {
		return fail(e)
	}
	if len(r.Events) == 0 || r.Events[len(r.Events)-1].State != "BOOT_OBSERVED" {
		return fail(errors.New("boundary not boot observed"))
	}
	if e = ValidateRestart(r.Pre, r.Post); e != nil {
		return fail(e)
	}
	if e = checkCurrentBoot(r.Post, p.BusinessSID); e != nil {
		return fail(e)
	}
	if e = checkNoOfficialProcess(p); e != nil {
		return fail(e)
	}
	if e = checkFence(p, holds); e != nil {
		return fail(e)
	}
	if e = checkAncestorControl(p, holds); e != nil {
		return fail(e)
	}
	if e = checkHolds(holds); e != nil {
		return fail(e)
	}
	if e = lease.Matches(held); e != nil {
		return fail(e)
	}
	q := &CurrentQuiescence{owner: &quiescenceOwner{lease: lease, plan: p, post: r.Post, holds: holds}}
	return q, nil
}

func discoverPlan(root, operation, sha string) (EntryFencePlan, error) {
	var p EntryFencePlan
	base := os.Getenv("ProgramData")
	if base == "" {
		return p, errors.New("ProgramData unavailable")
	}
	parent := filepath.Join(base, "ResearchOS", "RecoveryBoundary")
	entries, e := os.ReadDir(parent)
	if e != nil {
		return p, e
	}
	if len(entries) > 128 {
		return p, errors.New("boundary root inventory too large")
	}
	var found int
	for _, entry := range entries {
		if !entry.IsDir() || !validDigest(entry.Name()) {
			return p, errors.New("unknown boundary root inventory")
		}
		path := filepath.Join(parent, entry.Name(), operation, "plan.json")
		h, e := openNativeAccess(path, false, false, 0)
		if errors.Is(e, os.ErrNotExist) {
			continue
		}
		if errors.Is(e, windows.ERROR_FILE_NOT_FOUND) || errors.Is(e, windows.ERROR_PATH_NOT_FOUND) {
			continue
		}
		if e != nil {
			return p, errors.New("boundary plan unavailable")
		}
		raw, readErr := readPinnedBounded(h.handle, maxBoundaryPlanBytes)
		if readErr != nil {
			windows.CloseHandle(h.handle)
			return p, readErr
		}
		var candidate EntryFencePlan
		if e = json.Unmarshal(raw, &candidate); e != nil {
			windows.CloseHandle(h.handle)
			return p, e
		}
		if candidate.OperationID == operation && candidate.PlanSHA256 == sha && candidate.DataRoot.Path == root {
			sd := (*windows.SECURITY_DESCRIPTOR)(unsafe.Pointer(&h.identity.NativeSecurityDescriptor[0]))
			if e = checkManagedDescriptor(sd, candidate.ManagementSID); e != nil {
				windows.CloseHandle(h.handle)
				return p, errors.New("discovered boundary plan file not protected or changed")
			}
			p = candidate
			found++
		}
		if e = windows.CloseHandle(h.handle); e != nil {
			return p, e
		}
	}
	if found != 1 {
		return p, errors.New("exact boundary operation not found")
	}
	return p, nil
}

// ReadBoundaryPlan returns evidence for a C preflight. Its return value is
// serializable data, never authority to enter a transaction.
func ReadBoundaryPlan(dataRoot, operationID, boundaryPlanSHA256 string) (EntryFencePlan, string, error) {
	var zero EntryFencePlan
	if !filepath.IsAbs(dataRoot) || !validOperation(operationID) || !validDigest(boundaryPlanSHA256) {
		return zero, "", errors.New("boundary selector invalid")
	}
	p, e := discoverPlan(dataRoot, operationID, boundaryPlanSHA256)
	if e != nil {
		return zero, "", e
	}
	if e = ValidatePlan(p); e != nil {
		return zero, "", e
	}
	if e = checkManagedChain(p); e != nil {
		return zero, "", e
	}
	if e = checkAcceptanceFiles(p); e != nil {
		return zero, "", e
	}
	r, e := readRecord(p)
	if e != nil {
		return zero, "", e
	}
	state := r.Events[len(r.Events)-1].State
	if state == "BOOT_OBSERVED" {
		if e = ValidateRestart(r.Pre, r.Post); e != nil {
			return zero, "", e
		}
		if e = checkCurrentBoot(r.Post, p.BusinessSID); e != nil {
			return zero, "", e
		}
	}
	return p, state, nil
}

func (q *CurrentQuiescence) Check(ctx context.Context, held *rt.DataRootLease, dataRoot, database, operationID, planSHA256 string) error {
	if e := ctx.Err(); e != nil {
		return e
	}
	if q == nil || q.owner == nil {
		return errors.New("current quiescence absent")
	}
	o := q.owner
	o.mu.Lock()
	defer o.mu.Unlock()
	if o.closed || o.plan.DataRoot.Path != dataRoot || o.plan.Database.Path != database || o.plan.OperationID != operationID || o.plan.PlanSHA256 != planSHA256 {
		return errors.New("current quiescence binding stale")
	}
	if e := managedToken(o.plan); e != nil {
		return e
	}
	if e := o.lease.Matches(held); e != nil {
		return e
	}
	if e := checkHolds(o.holds); e != nil {
		return e
	}
	r, e := readRecord(o.plan)
	if e != nil {
		return e
	}
	if len(r.Events) == 0 || r.Events[len(r.Events)-1].State != "BOOT_OBSERVED" || r.Post != o.post {
		return errors.New("current quiescence state changed")
	}
	if e = ValidateRestart(r.Pre, r.Post); e != nil {
		return e
	}
	if e = checkCurrentBoot(r.Post, o.plan.BusinessSID); e != nil {
		return e
	}
	if e = checkNoOfficialProcess(o.plan); e != nil {
		return e
	}
	if e = checkFence(o.plan, o.holds); e != nil {
		return e
	}
	return checkAncestorControl(o.plan, o.holds)
}

func (q *CurrentQuiescence) Close() error {
	if q == nil || q.owner == nil {
		return errors.New("current quiescence absent")
	}
	o := q.owner
	o.mu.Lock()
	defer o.mu.Unlock()
	if o.closed {
		return errors.New("current quiescence already closed")
	}
	o.closed = true
	err := closeHolds(o.holds)
	o.holds = nil
	return err
}

// MarkCDurable is called only after the outer SQL transaction has actually
// returned. It reads the independently durable C journal; a caller bool or
// returned SQL result is insufficient to advance the external fence record.
func MarkCDurable(ctx context.Context, q *CurrentQuiescence, held *rt.DataRootLease, dataRoot, database, operationID, boundaryPlanSHA256, cPlanDigest string) error {
	if q == nil || q.owner == nil {
		return errors.New("current quiescence absent")
	}
	r, err := readRecord(q.owner.plan)
	if err != nil {
		return err
	}
	state := r.Events[len(r.Events)-1].State
	if state == "BOOT_OBSERVED" {
		if err = q.Check(ctx, held, dataRoot, database, operationID, boundaryPlanSHA256); err != nil {
			return err
		}
	} else if state == "C_HELD" {
		if err = ctx.Err(); err != nil {
			return err
		}
		if err = managedToken(q.owner.plan); err != nil {
			return err
		}
		q.owner.mu.Lock()
		defer q.owner.mu.Unlock()
		if q.owner.closed || q.owner.plan.DataRoot.Path != dataRoot || q.owner.plan.Database.Path != database || q.owner.plan.OperationID != operationID || q.owner.plan.PlanSHA256 != boundaryPlanSHA256 {
			return errors.New("current quiescence binding stale")
		}
		if err = q.owner.lease.Matches(held); err != nil {
			return err
		}
		if err = checkHolds(q.owner.holds); err != nil {
			return err
		}
		if err = checkCurrentBoot(q.owner.post, q.owner.plan.BusinessSID); err != nil {
			return err
		}
		if err = checkFence(q.owner.plan, q.owner.holds); err != nil {
			return err
		}
		if err = checkAncestorControl(q.owner.plan, q.owner.holds); err != nil {
			return err
		}
	} else {
		return errors.New("boundary not awaiting C durable")
	}
	if !strings.HasPrefix(cPlanDigest, "sha256:") || !validDigest(strings.TrimPrefix(cPlanDigest, "sha256:")) {
		return errors.New("C plan digest invalid")
	}
	_, status, err := qualificationmaintenancejournal.OpenOwnInspection(dataRoot, qualificationmaintenancejournal.QualificationNamespace, operationID, cPlanDigest)
	if err != nil {
		return err
	}
	if !status.Terminal || !status.Applied || status.State != "DURABLE" {
		return errors.New("C journal is not durable")
	}
	if err = qualificationmaintenancejournal.CheckOrdinary(dataRoot); err != nil {
		return err
	}
	r, err = readRecord(q.owner.plan)
	if err != nil {
		return err
	}
	if state == "BOOT_OBSERVED" {
		if r.Events[len(r.Events)-1].State != "BOOT_OBSERVED" {
			return errors.New("boundary state changed before C durable")
		}
		if err = appendEvent(q.owner.plan, r.Events, "C_HELD"); err != nil {
			return err
		}
		r, err = readRecord(q.owner.plan)
		if err != nil {
			return err
		}
	}
	if r.Events[len(r.Events)-1].State != "C_HELD" {
		return errors.New("boundary C held state changed")
	}
	return appendEvent(q.owner.plan, r.Events, "C_DURABLE")
}

func managedToken(p EntryFencePlan) error {
	token := windows.GetCurrentProcessToken()
	if !token.IsElevated() {
		return errors.New("trusted management elevation required")
	}
	u, e := token.GetTokenUser()
	if e != nil {
		return e
	}
	if u.User.Sid.String() != p.ManagementSID || p.BusinessSID == p.ManagementSID {
		return errors.New("management SID cannot be business owner")
	}
	return nil
}

func checkAcceptanceFiles(p EntryFencePlan) error {
	dir, e := stateRoot(p)
	if e != nil {
		return e
	}
	items := []struct{ name, sha, kind string }{
		{"source-accepted.json", p.SourceAcceptanceSHA256, "source"},
		{"native-accepted.json", p.NativeAcceptanceSHA256, "native"},
		{"backup-verified.json", p.BackupManifestSHA256, "online-backup"},
		{"recovery-ready.json", p.RecoveryPackageSHA256, "management-recovery"},
	}
	for _, item := range items {
		raw, identity, e := readManagedFile(filepath.Join(dir, item.name), p.ManagementSID, 16<<10)
		if e != nil {
			return fmt.Errorf("%s: %w", item.name, e)
		}
		if identity.SHA256 != item.sha {
			return fmt.Errorf("acceptance digest mismatch: %s", item.name)
		}
		var proof BoundaryAttestation
		if e = json.Unmarshal(raw, &proof); e != nil {
			return e
		}
		if e = validateAttestation(p, item.kind, proof); e != nil {
			return fmt.Errorf("%s: %w", item.name, e)
		}
	}
	return nil
}

func validateAttestation(p EntryFencePlan, kind string, proof BoundaryAttestation) error {
	core, e := PlanCoreSHA256(p)
	if e != nil || proof.Schema != "researchos.boundary-attestation.v1" || proof.Kind != kind || proof.Status != "ACCEPTED" || proof.OperationID != p.OperationID || proof.PlanCoreSHA256 != core || proof.Issuer == "" || proof.Issuer == p.ManagementSID || !validDigest(proof.EvidenceSHA256) || proof.RecordedUTC.IsZero() {
		return errors.New("external acceptance report unqualified")
	}
	if kind == "online-backup" && (proof.BackupID == "" || !validDigest(proof.RestoreTestSHA256) || !validDigest(proof.CredentialProbeSHA256)) {
		return errors.New("online backup has no restoration and credential proof")
	}
	return nil
}

func readFullRestartEvidence(p EntryFencePlan, pre BootWitness, now time.Time) (string, error) {
	dir, e := stateRoot(p)
	if e != nil {
		return "", e
	}
	path := filepath.Join(dir, "full-restart-complete.json")
	raw, identity, e := readManagedFile(path, p.ManagementSID, 16<<10)
	if e != nil {
		return "", e
	}
	var evidence struct {
		Schema          string    `json:"schema"`
		OperationID     string    `json:"operation_id"`
		Method          string    `json:"method"`
		ConfirmedByUser bool      `json:"confirmed_by_user"`
		CompletedUTC    time.Time `json:"completed_utc"`
	}
	if e = json.Unmarshal(raw, &evidence); e != nil {
		return "", e
	}
	if evidence.Schema != "researchos.full-restart-complete.v1" || evidence.OperationID != p.OperationID || evidence.Method != "FullRestart" || !evidence.ConfirmedByUser || evidence.CompletedUTC.Before(pre.UTC) || evidence.CompletedUTC.After(now) {
		return "", errors.New("explicit FullRestart completion evidence invalid")
	}
	return identity.SHA256, nil
}

func fenceDigest(p EntryFencePlan) string {
	var parts []string
	for _, t := range p.Targets {
		parts = append(parts, strings.ToLower(t.File.FinalUTF16)+"\x00"+t.File.FileID+"\x00"+t.InstalledSD+"\x00"+t.InstalledNativeSecuritySHA256)
	}
	sort.Strings(parts)
	return digest([]byte(strings.Join(parts, "\n")))
}

func writeExclusiveJSON(path, managementSID string, value any) error {
	raw, e := json.Marshal(value)
	if e != nil {
		return e
	}
	limit := 256 << 10
	if filepath.Base(path) == "plan.json" {
		limit = maxBoundaryPlanBytes
	}
	if len(raw) > limit {
		return errors.New("boundary record oversized")
	}
	sd, e := windows.SecurityDescriptorFromString("O:" + managementSID + "D:P(A;;FA;;;" + managementSID + ")(A;;FA;;;SY)")
	if e != nil {
		return e
	}
	if e = checkManagedDescriptor(sd, managementSID); e != nil {
		return e
	}
	ptr, e := windows.UTF16PtrFromString(path)
	if e != nil {
		return e
	}
	attributes := windows.SecurityAttributes{SecurityDescriptor: sd}
	attributes.Length = uint32(unsafe.Sizeof(attributes))
	h, e := windows.CreateFile(ptr, windows.GENERIC_WRITE|windows.READ_CONTROL, windows.FILE_SHARE_READ,
		&attributes, windows.CREATE_NEW, windows.FILE_ATTRIBUTE_NORMAL, 0)
	if e != nil {
		return e
	}
	closed := false
	defer func() {
		if !closed {
			windows.CloseHandle(h)
		}
	}()
	data := append(raw, '\n')
	var n uint32
	if e = windows.WriteFile(h, data, &n, nil); e != nil || n != uint32(len(data)) {
		return errors.Join(e, errors.New("managed record write incomplete"))
	}
	if e = windows.FlushFileBuffers(h); e != nil {
		return e
	}
	readback, e := windows.GetSecurityInfo(h, windows.SE_FILE_OBJECT, windows.OWNER_SECURITY_INFORMATION|windows.DACL_SECURITY_INFORMATION)
	if e != nil {
		return e
	}
	if e = checkManagedDescriptor(readback, managementSID); e != nil {
		return e
	}
	closed = true
	return windows.CloseHandle(h)
}

func appendEvent(p EntryFencePlan, events []BoundaryEvent, state string) error {
	if e := ValidateEvents(events, p.OperationID, p.PlanSHA256); e != nil && len(events) > 0 {
		return e
	}
	previous, previousHash := "", ""
	if len(events) > 0 {
		previous = events[len(events)-1].State
		previousHash = events[len(events)-1].SHA256
	}
	if !transition(previous, state) {
		return errors.New("boundary phase transition invalid")
	}
	e := BoundaryEvent{Schema: EventSchema, Sequence: uint64(len(events) + 1), PreviousSHA256: previousHash, OperationID: p.OperationID, PlanSHA256: p.PlanSHA256, State: state, UTC: time.Now().UTC()}
	e.SHA256 = digest([]byte(fmt.Sprintf("%s\x00%d\x00%s\x00%s\x00%s\x00%s\x00%s", e.Schema, e.Sequence, e.PreviousSHA256, e.OperationID, e.PlanSHA256, e.State, e.UTC.UTC().Format(time.RFC3339Nano))))
	dir, err := stateRoot(p)
	if err != nil {
		return err
	}
	return writeExclusiveJSON(filepath.Join(dir, fmt.Sprintf("event-%02d.json", e.Sequence)), p.ManagementSID, e)
}

func setTargetDescriptor(expected FileIdentity, desiredSD string, desiredNativeRaw []byte) (outErr error) {
	var sd *windows.SECURITY_DESCRIPTOR
	var desiredSemantic string
	var e error
	if len(desiredNativeRaw) > 0 {
		desiredSemantic, e = nativeSecuritySemanticSHA256(desiredNativeRaw)
		if e != nil {
			return e
		}
		sd = (*windows.SECURITY_DESCRIPTOR)(unsafe.Pointer(&desiredNativeRaw[0]))
		if !sd.IsValid() || sd.String() != desiredSD {
			return errors.New("desired native security preimage differs from plan SDDL")
		}
	} else {
		sd, e = windows.SecurityDescriptorFromString(desiredSD)
		if e != nil {
			return e
		}
		_, desiredSemantic, e = nativeSecurityFromSDDL(desiredSD)
		if e != nil {
			return e
		}
	}
	owner, _, e := sd.Owner()
	if e != nil || owner == nil {
		return errors.New("target owner descriptor missing")
	}
	dacl, _, e := sd.DACL()
	if e != nil || dacl == nil {
		return errors.Join(e, errors.New("target DACL descriptor missing"))
	}
	prior, e := windows.SecurityDescriptorFromString(expected.SecurityDescriptor)
	if e != nil {
		return e
	}
	priorOwner, _, e := prior.Owner()
	if e != nil || priorOwner == nil {
		return errors.New("expected target owner descriptor missing")
	}
	priorControl, _, e := prior.Control()
	if e != nil {
		return e
	}
	control, _, e := sd.Control()
	if e != nil {
		return e
	}
	if (priorControl&windows.SE_DACL_AUTO_INHERITED != 0) != (control&windows.SE_DACL_AUTO_INHERITED != 0) {
		return errors.New("target DACL auto-inheritance class drift")
	}
	access := uint32(windows.WRITE_DAC)
	flags := windows.SECURITY_INFORMATION(windows.DACL_SECURITY_INFORMATION)
	if !priorOwner.Equals(owner) {
		access |= windows.WRITE_OWNER
		flags |= windows.OWNER_SECURITY_INFORMATION
	}
	hold, e := openNativeAccess(expected.Path, false, true, access)
	if e != nil {
		return fmt.Errorf("target mutation open READ_CONTROL|READ_DATA|WRITE_DAC plus owner-change access %#x: %w", access, e)
	}
	defer func() { outErr = errors.Join(outErr, windows.CloseHandle(hold.handle)) }()
	if !identityEqual(hold.identity, expected) {
		return errors.New("target same-handle native identity or descriptor changed before mutation")
	}
	if control&windows.SE_DACL_AUTO_INHERITED != 0 {
		// SetSecurityInfo retains the auto-inherited class. NtSetSecurityObject
		// clears it on this filesystem, so the frozen descriptor selects one
		// path before mutation; there is no failure-time fallback.
		setFlags := flags | windows.UNPROTECTED_DACL_SECURITY_INFORMATION
		if control&windows.SE_DACL_PROTECTED != 0 {
			setFlags = flags | windows.PROTECTED_DACL_SECURITY_INFORMATION
		}
		if e = windows.SetSecurityInfo(hold.handle, windows.SE_FILE_OBJECT, setFlags, owner, nil, dacl, nil); e != nil {
			return fmt.Errorf("target mutation SetSecurityInfo owner/DACL: %w", e)
		}
	} else {
		if e = ntSetSecurityObject.Find(); e != nil {
			return fmt.Errorf("NtSetSecurityObject unavailable: %w", e)
		}
		r, _, _ := ntSetSecurityObject.Call(uintptr(hold.handle), uintptr(flags), uintptr(unsafe.Pointer(sd)))
		runtime.KeepAlive(sd)
		if status := windows.NTStatus(r); status != 0 {
			return fmt.Errorf("target mutation NtSetSecurityObject status %#x: %w", uint32(status), status.Errno())
		}
	}
	_, readbackSDDL, readbackSemantic, e := nativeSecurityDescriptor(hold.handle, hold.identity.SACLReadStatus == "READABLE")
	if e != nil {
		return fmt.Errorf("target mutation GetSecurityInfo readback: %w", e)
	}
	if readbackSDDL != desiredSD || readbackSemantic != desiredSemantic {
		return fmt.Errorf("target descriptor same-handle readback mismatch: expected SDDL %q semantic %s observed SDDL %q semantic %s", desiredSD, desiredSemantic, readbackSDDL, readbackSemantic)
	}
	v, id, e := nativeFileID(hold.handle)
	if e != nil {
		return e
	}
	final, e := finalPath(hold.handle)
	if e != nil {
		return e
	}
	if v != expected.Volume || id != expected.FileID || !strings.EqualFold(final, expected.FinalUTF16) {
		return errors.New("target native identity changed during ACL mutation")
	}
	return nil
}

func checkNoOfficialProcess(p EntryFencePlan) error {
	snapshot, e := windows.CreateToolhelp32Snapshot(windows.TH32CS_SNAPPROCESS, 0)
	if e != nil {
		return e
	}
	defer windows.CloseHandle(snapshot)
	var entry windows.ProcessEntry32
	entry.Size = uint32(unsafe.Sizeof(entry))
	if e = windows.Process32First(snapshot, &entry); e != nil {
		return e
	}
	for {
		name := windows.UTF16ToString(entry.ExeFile[:])
		for _, t := range p.Targets {
			if t.Mode != "executable" || !strings.EqualFold(name, filepath.Base(t.File.Path)) {
				continue
			}
			proc, err := windows.OpenProcess(windows.PROCESS_QUERY_LIMITED_INFORMATION, false, entry.ProcessID)
			if err != nil {
				return fmt.Errorf("candidate official process inaccessible: %w", err)
			}
			buf := make([]uint16, 32768)
			n := uint32(len(buf))
			err = windows.QueryFullProcessImageName(proc, 0, &buf[0], &n)
			closeErr := windows.CloseHandle(proc)
			if err != nil || closeErr != nil {
				return errors.Join(err, closeErr)
			}
			if strings.EqualFold(windows.UTF16ToString(buf[:n]), t.File.Path) {
				return errors.New("official entry process remains live")
			}
		}
		e = windows.Process32Next(snapshot, &entry)
		if errors.Is(e, windows.ERROR_NO_MORE_FILES) {
			break
		}
		if e != nil {
			return e
		}
	}
	return nil
}

func checkRestartRegistrations(p EntryFencePlan) error {
	snapshot, e := windows.CreateToolhelp32Snapshot(windows.TH32CS_SNAPPROCESS, 0)
	if e != nil {
		return e
	}
	defer windows.CloseHandle(snapshot)
	var entry windows.ProcessEntry32
	entry.Size = uint32(unsafe.Sizeof(entry))
	if e = windows.Process32First(snapshot, &entry); e != nil {
		return e
	}
	for {
		name := windows.UTF16ToString(entry.ExeFile[:])
		for _, t := range p.Targets {
			if t.Mode != "executable" || !strings.EqualFold(name, filepath.Base(t.File.Path)) {
				continue
			}
			proc, err := windows.OpenProcess(windows.PROCESS_QUERY_LIMITED_INFORMATION|windows.PROCESS_VM_READ, false, entry.ProcessID)
			if err != nil {
				return fmt.Errorf("official restart candidate inaccessible: %w", err)
			}
			buf := make([]uint16, 32768)
			n := uint32(len(buf))
			err = windows.QueryFullProcessImageName(proc, 0, &buf[0], &n)
			if err != nil {
				windows.CloseHandle(proc)
				return err
			}
			if strings.EqualFold(windows.UTF16ToString(buf[:n]), t.File.Path) {
				args, _, registered, readErr := restartSettingsForProcess(proc)
				if readErr != nil {
					windows.CloseHandle(proc)
					return readErr
				}
				if registered {
					match := false
					for _, sha := range t.RestartArgsSHA256 {
						if sha == digest([]byte(args)) {
							match = true
							break
						}
					}
					if !match {
						windows.CloseHandle(proc)
						return errors.New("runtime RestartApps argv outside frozen entry inventory")
					}
				}
			}
			if err = windows.CloseHandle(proc); err != nil {
				return err
			}
		}
		e = windows.Process32Next(snapshot, &entry)
		if errors.Is(e, windows.ERROR_NO_MORE_FILES) {
			break
		}
		if e != nil {
			return e
		}
	}
	return nil
}

// RunPhase is the fixed management helper state machine. The caller supplies
// only the exact root/operation/plan selector, never SQL or a target path.
func RunPhase(ctx context.Context, phase, dataRoot, operationID, planSHA256 string) (stateOut string, errOut error) {
	if e := ctx.Err(); e != nil {
		return "", e
	}
	if phase != "plan" && phase != "arm" && phase != "observe" && phase != "status" && phase != "disarm-request" {
		return "", errors.New("unsupported boundary phase")
	}
	if !filepath.IsAbs(dataRoot) || filepath.Clean(dataRoot) != dataRoot || !validOperation(operationID) || !validDigest(planSHA256) {
		return "", errors.New("boundary selector invalid")
	}
	p, e := discoverPlan(dataRoot, operationID, planSHA256)
	if e != nil {
		return "", e
	}
	if e = ValidatePlan(p); e != nil {
		return "", e
	}
	dir, e := stateRoot(p)
	if e != nil {
		return "", e
	}
	if e = checkManagedChain(p); e != nil {
		return "", e
	}
	if e = checkAcceptanceFiles(p); e != nil {
		return "", e
	}
	if phase == "plan" {
		if e = managedToken(p); e != nil {
			return "", e
		}
		entries, e := os.ReadDir(dir)
		if e != nil {
			return "", e
		}
		if len(entries) != 5 {
			return "", errors.New("plan staging inventory not exact")
		}
		holds, e := openPlanHolds(p)
		if e != nil {
			return "", e
		}
		defer func() { errOut = errors.Join(errOut, closeHolds(holds)) }()
		if e = checkAncestorControl(p, holds); e != nil {
			return "", e
		}
		for _, t := range p.Targets {
			expected, e := denyDescriptor(t.File.SecurityDescriptor, p.BusinessSID, p.ManagementSID, t.Mode)
			if e != nil || expected != t.InstalledSD {
				return "", errors.New("fence descriptor plan mismatch")
			}
			_, installedNative, e := nativeSecurityFromSDDL(expected)
			if e != nil || installedNative != t.InstalledNativeSecuritySHA256 {
				return "", errors.New("fence native semantic plan mismatch")
			}
		}
		pre, e := witness(p, fenceDigest(p))
		if e != nil {
			return "", e
		}
		pre.BusinessEnabledSIDsSHA256, e = businessEnabledGroupDigest(p)
		if e != nil {
			return "", e
		}
		shape, e := captureOfficialBusinessToken(p, pre.BusinessEnabledSIDsSHA256)
		if e != nil {
			return "", e
		}
		pre.BusinessSessionID = shape.SessionID
		pre.BusinessElevationType = shape.ElevationType
		pre.BusinessIntegritySID = shape.IntegritySID
		pre.BusinessLogonSID = shape.LogonSID
		pre.BusinessPrivilegesSHA256 = shape.PrivilegesSHA256
		pre.BusinessProcessPID = shape.ProcessID
		pre.BusinessProcessCreatedUTC = shape.ProcessCreated
		pre.BusinessProcessImageSHA256 = shape.ProcessImageSHA
		if pre.UptimeMilliseconds < uint64(MaxPostUptime/time.Millisecond) {
			return "", errors.New("pre uptime insufficient")
		}
		if e = writeExclusiveJSON(filepath.Join(dir, "pre.json"), p.ManagementSID, pre); e != nil {
			return "", e
		}
		if e = appendEvent(p, nil, "PREPARED"); e != nil {
			return "", e
		}
		return "PREPARED", nil
	}
	r, e := readRecord(p)
	if e != nil {
		return "", e
	}
	state := r.Events[len(r.Events)-1].State
	if phase == "status" {
		return state, nil
	}
	if e = managedToken(p); e != nil {
		return "", e
	}
	switch phase {
	case "arm":
		if state != "PREPARED" {
			return "", errors.New("arm requires PREPARED")
		}
		if e = checkPreCurrent(r.Pre, p.BusinessSID); e != nil {
			return "", e
		}
		if e = checkRestartRegistrations(p); e != nil {
			return "", e
		}
		holds, e := openPlanHolds(p)
		if e != nil {
			return "", e
		}
		defer func() { errOut = errors.Join(errOut, closeHolds(holds)) }()
		if e = checkAncestorControl(p, holds); e != nil {
			return "", e
		}
		if e = preflightManagementRestore(p); e != nil {
			return "", e
		}
		if e = appendEvent(p, r.Events, "APPLYING"); e != nil {
			return "", e
		}
		for _, t := range p.Targets {
			if e = setTargetDescriptor(t.File, t.InstalledSD, nil); e != nil {
				return "", e
			}
			h, e := openNativeAccess(t.File.Path, false, true, windows.WRITE_DAC|windows.WRITE_OWNER)
			if e != nil {
				return "", e
			}
			ok := identityCoreEqual(t.File, h.identity) && h.identity.SecurityDescriptor == t.InstalledSD && h.identity.NativeSecuritySHA256 == t.InstalledNativeSecuritySHA256
			closeErr := windows.CloseHandle(h.handle)
			if closeErr != nil {
				return "", closeErr
			}
			if !ok {
				return "", errors.New("arm native readback mismatch")
			}
		}
		r, e = readRecord(p)
		if e != nil {
			return "", e
		}
		if e = appendEvent(p, r.Events, "ARMED"); e != nil {
			return "", e
		}
		return "ARMED", nil
	case "observe":
		if state != "ARMED" {
			return "", errors.New("observe requires ARMED")
		}
		holds, e := openPlanHolds(p)
		if e != nil {
			return "", e
		}
		defer func() { errOut = errors.Join(errOut, closeHolds(holds)) }()
		if e = checkFence(p, holds); e != nil {
			return "", e
		}
		if e = checkAncestorControl(p, holds); e != nil {
			return "", e
		}
		if e = checkNoOfficialProcess(p); e != nil {
			return "", e
		}
		post, e := witness(p, fenceDigest(p))
		if e != nil {
			return "", e
		}
		currentBusiness, e := inspectExistingBusinessProcess(p, r.Pre.BusinessEnabledSIDsSHA256, r.Pre)
		if e != nil {
			return "", e
		}
		post.BusinessEnabledSIDsSHA256 = currentBusiness.GroupsSHA256
		post.BusinessSessionID = currentBusiness.SessionID
		post.BusinessElevationType = currentBusiness.ElevationType
		post.BusinessIntegritySID = currentBusiness.IntegritySID
		post.BusinessLogonSID = currentBusiness.LogonSID
		post.BusinessPrivilegesSHA256 = currentBusiness.PrivilegesSHA256
		post.BusinessProcessPID = currentBusiness.ProcessID
		post.BusinessProcessCreatedUTC = currentBusiness.ProcessCreated
		post.BusinessProcessImageSHA256 = currentBusiness.ProcessImageSHA
		post.FullRestartEvidenceSHA256, e = readFullRestartEvidence(p, r.Pre, post.UTC)
		if e != nil {
			return "", e
		}
		if e = ValidateRestart(r.Pre, post); e != nil {
			return "", e
		}
		if e = writeExclusiveJSON(filepath.Join(dir, "post.json"), p.ManagementSID, post); e != nil {
			return "", e
		}
		if e = appendEvent(p, r.Events, "BOOT_OBSERVED"); e != nil {
			return "", e
		}
		return "BOOT_OBSERVED", nil
	case "disarm-request":
		if state == "PREPARED" || state == "APPLYING" || state == "ARMED" || state == "BOOT_OBSERVED" {
			// The only abort path is a proven pre-BEGIN path under the same
			// exclusive root lock used by C. Any journal, even malformed or
			// terminal, requires exact C recovery rather than a no-effect claim.
			lease, leaseErr := rt.AcquireDataRootLease(p.DataRoot.Path)
			if leaseErr != nil {
				return "", leaseErr
			}
			defer func() { errOut = errors.Join(errOut, lease.Close()) }()
			ownJournal := filepath.Join(p.DataRoot.Path, "host", qualificationmaintenancejournal.QualificationNamespace, p.OperationID)
			if _, statErr := os.Lstat(ownJournal); statErr == nil {
				return "", errors.New("C journal exists; pre-BEGIN abort forbidden")
			} else if !errors.Is(statErr, os.ErrNotExist) {
				return "", statErr
			}
			if e = qualificationmaintenancejournal.CheckOrdinary(p.DataRoot.Path); e != nil {
				return "", e
			}
			if e = appendEvent(p, r.Events, "BOUNDARY_ABORTED"); e != nil {
				return "", e
			}
			r, e = readRecord(p)
			if e != nil {
				return "", e
			}
			state = "BOUNDARY_ABORTED"
		}
		if state != "C_DURABLE" && state != "BOUNDARY_ABORTED" && state != "DISARMING" {
			return "", errors.New("disarm requires durable C or explicit boundary abort")
		}
		if state == "C_DURABLE" {
			if e = checkExactCDurable(p); e != nil {
				return "", e
			}
		}
		if state == "DISARMING" {
			// A resumable partial restore is only legal if the earlier event
			// records a durable C or explicit, non-success abort.
			if len(r.Events) < 2 || (r.Events[len(r.Events)-2].State != "C_DURABLE" && r.Events[len(r.Events)-2].State != "BOUNDARY_ABORTED") {
				return "", errors.New("disarm predecessor invalid")
			}
			if r.Events[len(r.Events)-2].State == "C_DURABLE" {
				if e = checkExactCDurable(p); e != nil {
					return "", e
				}
			}
		}
		holds, e := openPlanHolds(p)
		if e != nil {
			return "", e
		}
		defer func() { errOut = errors.Join(errOut, closeHolds(holds)) }()
		if e = checkAncestorControl(p, holds); e != nil {
			return "", e
		}
		byPath := map[string]FileIdentity{}
		for _, h := range holds {
			byPath[strings.ToLower(h.path)] = h.identity
		}
		for _, t := range p.Targets {
			x := byPath[strings.ToLower(t.File.Path)]
			if !identityCoreEqual(x, t.File) || (x.SecurityDescriptor != t.File.SecurityDescriptor || x.NativeSecuritySHA256 != t.File.NativeSecuritySHA256) && (x.SecurityDescriptor != t.InstalledSD || x.NativeSecuritySHA256 != t.InstalledNativeSecuritySHA256) {
				return "", errors.New("disarm target differs from exact before/installed descriptor")
			}
		}
		if e = preflightInstalledRestore(p, byPath); e != nil {
			return "", e
		}
		if state != "DISARMING" {
			if e = appendEvent(p, r.Events, "DISARMING"); e != nil {
				return "", e
			}
		}
		for _, t := range p.Targets {
			x := byPath[strings.ToLower(t.File.Path)]
			if x.SecurityDescriptor == t.File.SecurityDescriptor && x.NativeSecuritySHA256 == t.File.NativeSecuritySHA256 {
				continue
			}
			expected := t.File
			expected.SecurityDescriptor = t.InstalledSD
			expected.NativeSecurityDescriptor = nil
			expected.NativeSecuritySHA256 = t.InstalledNativeSecuritySHA256
			if e = setTargetDescriptor(expected, t.File.SecurityDescriptor, t.File.NativeSecurityDescriptor); e != nil {
				return "", e
			}
			h, e := openNative(t.File.Path, false, true)
			if e != nil {
				return "", e
			}
			ok := identityEqual(t.File, h.identity)
			closeErr := windows.CloseHandle(h.handle)
			if closeErr != nil {
				return "", closeErr
			}
			if !ok {
				return "", errors.New("disarm exact descriptor readback mismatch")
			}
		}
		r, e = readRecord(p)
		if e != nil {
			return "", e
		}
		if e = appendEvent(p, r.Events, "CLOSED"); e != nil {
			return "", e
		}
		return "CLOSED", nil
	}
	return "", errors.New("unreachable boundary phase")
}

func checkExactCDurable(p EntryFencePlan) error {
	path := filepath.Join(p.DataRoot.Path, "host", qualificationmaintenancejournal.QualificationNamespace, p.OperationID, "plan.json")
	raw, e := os.ReadFile(path)
	if e != nil || len(raw) > 256<<10 {
		return errors.New("C journal plan unavailable")
	}
	var view struct {
		PlanHash string `json:"plan_hash"`
	}
	if e = json.Unmarshal(raw, &view); e != nil {
		return e
	}
	_, status, e := qualificationmaintenancejournal.OpenOwnInspection(p.DataRoot.Path, qualificationmaintenancejournal.QualificationNamespace, p.OperationID, view.PlanHash)
	if e != nil {
		return e
	}
	if status.State != "DURABLE" || !status.Terminal || !status.Applied {
		return errors.New("exact C operation not durable")
	}
	return qualificationmaintenancejournal.CheckOrdinary(p.DataRoot.Path)
}
