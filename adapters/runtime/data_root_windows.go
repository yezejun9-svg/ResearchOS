//go:build windows

package runtime

import (
	"errors"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"unsafe"

	"golang.org/x/sys/windows"
	"researchos.local/research-os/internal/qualificationmaintenancejournal"
)

// Copies of DataRootLease share one private owner and OS handle.
type DataRootLease struct{ owner *dataRootLeaseOwner }

// DataRootLeaseIdentity is a process-local witness for one live owner
// generation. No caller can construct a matching value from JSON or a path.
type DataRootLeaseIdentity struct {
	owner      *dataRootLeaseOwner
	generation uint64
	root       string
}

type dataRootLeaseOwner struct {
	mu         sync.Mutex
	root       string
	file       *os.File
	closed     bool
	generation uint64
	borrowKind dataRootBorrowKind
	borrow     *dataRootBorrowState
}

type dataRootBorrowKind uint8

const (
	noDataRootBorrow dataRootBorrowKind = iota
	legacyDataRootBorrow
	maintenanceDataRootBorrow
)

type dataRootBorrowState struct {
	owner      *dataRootLeaseOwner
	generation uint64
	kind       dataRootBorrowKind
	released   bool
	guards     []dataRootIdentityGuard
}

type dataRootFileID struct {
	volume uint64
	file   [16]byte
}
type dataRootIdentityGuard struct {
	path     string
	handle   windows.Handle
	identity dataRootFileID
}

func dataRootNativeIdentity(h windows.Handle) (dataRootFileID, error) {
	var raw struct {
		VolumeSerialNumber uint64
		FileID             [16]byte
	}
	if err := windows.GetFileInformationByHandleEx(h, windows.FileIdInfo, (*byte)(unsafe.Pointer(&raw)), uint32(unsafe.Sizeof(raw))); err != nil {
		return dataRootFileID{}, err
	}
	return dataRootFileID{volume: raw.VolumeSerialNumber, file: raw.FileID}, nil
}

func openDataRootGuard(path string, directory bool) (dataRootIdentityGuard, error) {
	wide, err := windows.UTF16PtrFromString(path)
	if err != nil {
		return dataRootIdentityGuard{}, err
	}
	h, err := windows.CreateFile(wide, windows.GENERIC_READ,
		windows.FILE_SHARE_READ|windows.FILE_SHARE_WRITE, nil, windows.OPEN_EXISTING,
		windows.FILE_FLAG_OPEN_REPARSE_POINT|windows.FILE_FLAG_BACKUP_SEMANTICS, 0)
	if err != nil {
		return dataRootIdentityGuard{}, err
	}
	fail := func(err error) (dataRootIdentityGuard, error) {
		windows.CloseHandle(h)
		return dataRootIdentityGuard{}, err
	}
	var info windows.ByHandleFileInformation
	if err := windows.GetFileInformationByHandle(h, &info); err != nil {
		return fail(err)
	}
	if info.FileAttributes&windows.FILE_ATTRIBUTE_REPARSE_POINT != 0 || (info.FileAttributes&windows.FILE_ATTRIBUTE_DIRECTORY != 0) != directory {
		return fail(errors.New("maintenance source reparse or kind mismatch"))
	}
	id, err := dataRootNativeIdentity(h)
	if err != nil {
		return fail(err)
	}
	return dataRootIdentityGuard{path: path, handle: h, identity: id}, nil
}

func dataRootGuardPaths(root, database string) []string {
	var parts []string
	for p := root; ; p = filepath.Dir(p) {
		parts = append(parts, p)
		if filepath.Dir(p) == p {
			break
		}
	}
	for i, j := 0, len(parts)-1; i < j; i, j = i+1, j-1 {
		parts[i], parts[j] = parts[j], parts[i]
	}
	return append(parts, database)
}

func closeDataRootGuards(guards []dataRootIdentityGuard) {
	for i := len(guards) - 1; i >= 0; i-- {
		windows.CloseHandle(guards[i].handle)
	}
}

func openDataRootGuards(root, database string) ([]dataRootIdentityGuard, error) {
	paths := dataRootGuardPaths(root, database)
	guards := make([]dataRootIdentityGuard, 0, len(paths))
	for i, path := range paths {
		g, err := openDataRootGuard(path, i < len(paths)-1)
		if err != nil {
			closeDataRootGuards(guards)
			return nil, err
		}
		guards = append(guards, g)
	}
	return guards, nil
}

func checkDataRootGuards(guards []dataRootIdentityGuard) error {
	if len(guards) == 0 {
		return errors.New("maintenance source identity guards missing")
	}
	for i, g := range guards {
		fresh, err := openDataRootGuard(g.path, i < len(guards)-1)
		if err != nil {
			return err
		}
		id := fresh.identity
		windows.CloseHandle(fresh.handle)
		if id != g.identity {
			return errors.New("maintenance source native identity changed")
		}
	}
	return nil
}

// DataRootSourceBorrow is process-local; copies share its consumed state.
type DataRootSourceBorrow struct{ state *dataRootBorrowState }

func AcquireDataRootLease(directory string) (*DataRootLease, error) {
	f, err := LockDataRoot(directory)
	if err != nil {
		return nil, err
	}
	root, err := filepath.Abs(directory)
	if err != nil {
		_ = f.Close()
		return nil, err
	}
	return &DataRootLease{owner: &dataRootLeaseOwner{root: filepath.Clean(root), file: f}}, nil
}

func acquireDataRootLeaseForOwnInspection(directory string, permit qualificationmaintenancejournal.InspectionPermit) (*DataRootLease, error) {
	root, err := filepath.Abs(directory)
	if err != nil {
		return nil, err
	}
	root = filepath.Clean(root)
	f, actual, err := lockDataRootRaw(root)
	if err != nil {
		return nil, err
	}
	if _, err := permit.Check(actual); err != nil {
		_ = f.Close()
		return nil, err
	}
	return &DataRootLease{owner: &dataRootLeaseOwner{root: actual, file: f}}, nil
}

// This lease exposes only a strict read of one existing replacement transition.
// The host recovery path retains all its separate plan and mutation checks.
func AcquireDataRootLeaseForReplacementRecovery(directory, operation, planDigest string, planBytes []byte) (*DataRootLease, error) {
	root, err := filepath.Abs(directory)
	if err != nil {
		return nil, err
	}
	permit, _, err := qualificationmaintenancejournal.OpenOwnReplacementInspection(filepath.Clean(root), operation, planDigest, planBytes)
	if err != nil {
		return nil, err
	}
	return acquireDataRootLeaseForOwnInspection(directory, permit)
}

func AcquireDataRootLeaseForQualificationRecovery(directory, operation, planDigest string) (*DataRootLease, error) {
	root, err := filepath.Abs(directory)
	if err != nil {
		return nil, err
	}
	permit, _, err := qualificationmaintenancejournal.OpenOwnInspection(filepath.Clean(root), qualificationmaintenancejournal.QualificationNamespace, operation, planDigest)
	if err != nil {
		return nil, err
	}
	return acquireDataRootLeaseForOwnInspection(directory, permit)
}

func (l *DataRootLease) Root() string {
	if l == nil || l.owner == nil {
		return ""
	}
	o := l.owner
	o.mu.Lock()
	defer o.mu.Unlock()
	if o.closed {
		return ""
	}
	return o.root
}

func (o *dataRootLeaseOwner) heldLocked() bool {
	if o.closed || o.file == nil {
		return false
	}
	_, err := o.file.Stat()
	return err == nil
}

func (l *DataRootLease) Held() bool {
	if l == nil || l.owner == nil {
		return false
	}
	o := l.owner
	o.mu.Lock()
	defer o.mu.Unlock()
	return o.heldLocked()
}

func (l *DataRootLease) MaintenanceIdentity() (DataRootLeaseIdentity, error) {
	if l == nil || l.owner == nil {
		return DataRootLeaseIdentity{}, errors.New("control data-root lease required")
	}
	o := l.owner
	o.mu.Lock()
	defer o.mu.Unlock()
	if !o.heldLocked() || o.root == "" {
		return DataRootLeaseIdentity{}, errors.New("control data-root lease unavailable")
	}
	return DataRootLeaseIdentity{owner: o, generation: o.generation, root: o.root}, nil
}

func (w DataRootLeaseIdentity) Matches(l *DataRootLease) error {
	if w.owner == nil || l == nil || l.owner == nil || l.owner != w.owner {
		return errors.New("control data-root lease identity mismatch")
	}
	o := l.owner
	o.mu.Lock()
	defer o.mu.Unlock()
	if !o.heldLocked() || o.generation != w.generation || o.root != w.root {
		return errors.New("control data-root lease generation changed")
	}
	return nil
}

func (l *DataRootLease) reserve(directory string, kind dataRootBorrowKind) (*dataRootBorrowState, error) {
	if l == nil || l.owner == nil {
		return nil, errors.New("control data-root lease required")
	}
	root, err := filepath.Abs(directory)
	if err != nil {
		return nil, err
	}
	o := l.owner
	o.mu.Lock()
	defer o.mu.Unlock()
	if !o.heldLocked() || !strings.EqualFold(filepath.Clean(root), o.root) {
		return nil, errors.New("control data-root lease unavailable or mismatched")
	}
	if o.borrowKind != noDataRootBorrow {
		return nil, errors.New("control data-root lease already borrowed")
	}
	o.generation++
	b := &dataRootBorrowState{owner: o, generation: o.generation, kind: kind}
	o.borrow, o.borrowKind = b, kind
	return b, nil
}

// Borrow is reserved for the in-process runtime coordinator.
func (l *DataRootLease) Borrow(directory string) error {
	_, err := l.reserve(directory, legacyDataRootBorrow)
	return err
}

func (l *DataRootLease) ReturnBorrow() error {
	if l == nil || l.owner == nil {
		return errors.New("control data-root lease required")
	}
	o := l.owner
	o.mu.Lock()
	defer o.mu.Unlock()
	if o.closed || o.borrowKind != legacyDataRootBorrow || o.borrow == nil || o.borrow.released {
		return errors.New("control data-root legacy borrow not active")
	}
	o.borrow.released = true
	o.borrow, o.borrowKind = nil, noDataRootBorrow
	return nil
}

func (l *DataRootLease) Close() error {
	if l == nil || l.owner == nil {
		return errors.New("control data-root lease required")
	}
	o := l.owner
	o.mu.Lock()
	defer o.mu.Unlock()
	if o.closed {
		return nil
	}
	if o.borrowKind != noDataRootBorrow {
		return errors.New("control data-root lease still borrowed")
	}
	o.closed = true
	if o.file == nil {
		return errors.New("control data-root lease file missing")
	}
	return o.file.Close()
}

// CheckMaintenanceReady is read-only and requires the same live OS lock used
// by normal Core. A checked path alone never creates a maintenance borrow.
func (l *DataRootLease) CheckMaintenanceReady(database string) error {
	if l == nil || l.owner == nil || !l.Held() {
		return errors.New("maintenance data-root lease required")
	}
	root := l.Root()
	if root == "" || !filepath.IsAbs(database) || filepath.Clean(database) != database ||
		!strings.EqualFold(database, filepath.Join(root, "researchos.sqlite")) {
		return errors.New("maintenance database path mismatch")
	}
	guards, err := openDataRootGuards(root, database)
	if err != nil {
		return err
	}
	defer closeDataRootGuards(guards)
	if err := checkDataRootGuards(guards); err != nil {
		return err
	}
	return qualificationmaintenancejournal.CheckOrdinary(root)
}

func (l *DataRootLease) BorrowMaintenanceSource(database string) (*DataRootSourceBorrow, error) {
	if err := l.CheckMaintenanceReady(database); err != nil {
		return nil, err
	}
	root := l.Root()
	guards, err := openDataRootGuards(root, database)
	if err != nil {
		return nil, err
	}
	if err := checkDataRootGuards(guards); err != nil {
		closeDataRootGuards(guards)
		return nil, err
	}
	if err := qualificationmaintenancejournal.CheckOrdinary(root); err != nil {
		closeDataRootGuards(guards)
		return nil, err
	}
	state, err := l.reserve(root, maintenanceDataRootBorrow)
	if err != nil {
		closeDataRootGuards(guards)
		return nil, err
	}
	state.guards = guards
	return &DataRootSourceBorrow{state: state}, nil
}

func (b *DataRootSourceBorrow) Check(database string) error {
	if b == nil || b.state == nil {
		return errors.New("maintenance source borrow required")
	}
	s := b.state
	o := s.owner
	if o == nil {
		return errors.New("maintenance source borrow owner missing")
	}
	o.mu.Lock()
	defer o.mu.Unlock()
	if s.released || s.kind != maintenanceDataRootBorrow || !o.heldLocked() || o.borrow != s || o.generation != s.generation || o.borrowKind != maintenanceDataRootBorrow {
		return errors.New("maintenance source borrow stale")
	}
	if !strings.EqualFold(filepath.Clean(database), filepath.Join(o.root, "researchos.sqlite")) {
		return errors.New("maintenance database identity mismatch")
	}
	return checkDataRootGuards(s.guards)
}

func (b *DataRootSourceBorrow) Release() error {
	if b == nil || b.state == nil {
		return errors.New("maintenance source borrow required")
	}
	s := b.state
	o := s.owner
	if o == nil {
		return errors.New("maintenance source borrow owner missing")
	}
	o.mu.Lock()
	defer o.mu.Unlock()
	if s.released || s.kind != maintenanceDataRootBorrow || o.borrow != s || o.generation != s.generation || o.borrowKind != maintenanceDataRootBorrow {
		return errors.New("maintenance source borrow stale")
	}
	s.released = true
	closeDataRootGuards(s.guards)
	s.guards = nil
	o.borrow, o.borrowKind = nil, noDataRootBorrow
	return nil
}
