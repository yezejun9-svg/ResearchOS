//go:build windows

package supervisor

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"reflect"
	"slices"
	"strings"

	"golang.org/x/sys/windows"
)

// ReleaseState is mechanical deployment state. It is never a domain acceptance
// receipt and is not writable by the candidate in a production installation.
type ReleaseState struct {
	Epoch           uint64                `json:"epoch"`
	Operation       string                `json:"operation"`
	Phase           string                `json:"phase"`
	Active          string                `json:"active"`
	ActivePath      string                `json:"active_path"`
	Candidate       string                `json:"candidate,omitempty"`
	CandidatePath   string                `json:"candidate_path,omitempty"`
	LastGood        string                `json:"last_known_good"`
	LastGoodPath    string                `json:"last_known_good_path"`
	Data            string                `json:"data"`
	Backup          string                `json:"backup,omitempty"`
	Cutover         *ReleaseCutover       `json:"cutover,omitempty"`
	Admission       string                `json:"admission,omitempty"`
	AdmissionBundle *ReleaseAdmission     `json:"admission_bundle,omitempty"`
	DrainReceipt    string                `json:"drain_receipt,omitempty"`
	DrainNonce      string                `json:"drain_nonce,omitempty"`
	PID             uint32                `json:"pid,omitempty"`
	CreatedNS       int64                 `json:"created_ns,omitempty"`
	ImageSHA256     string                `json:"image_sha256,omitempty"`
	Frozen          []string              `json:"frozen,omitempty"`
	RestoreContext  *ReleaseRestoreResult `json:"restore_context,omitempty"`
}

type releaseEntry struct {
	Sequence uint64       `json:"sequence"`
	Previous string       `json:"previous"`
	State    ReleaseState `json:"state"`
	Hash     string       `json:"hash"`
}

func releaseHash(v any) string {
	b, _ := json.Marshal(v)
	h := sha256.Sum256(b)
	return hex.EncodeToString(h[:])
}

// ReleaseDigest is the raw lowercase SHA-256 used by the private journal and
// effect ledger. Domain Artifact digests use a separate sha256: prefix.
func ReleaseDigest(v any) string { return releaseHash(v) }

func entryHash(e releaseEntry) string {
	e.Hash = ""
	return releaseHash(e)
}

func validDigest(v string) bool {
	if len(v) != 64 {
		return false
	}
	_, e := hex.DecodeString(v)
	return e == nil && strings.ToLower(v) == v
}

func validReleaseState(s ReleaseState) error {
	if s.RestoreContext != nil {
		if err := validRestoreResult(s, *s.RestoreContext); err != nil {
			return err
		}
	}
	if b := s.Cutover; b != nil {
		if s.AdmissionBundle == nil || b.Operation != s.Operation || b.Epoch != s.Epoch || !validDigest(b.ManifestSHA256) || !filepath.IsAbs(b.Root) || b.Database != filepath.Join(b.Root, "researchos.sqlite") || len(b.Migrations) == 0 || len(b.Purpose) == 0 {
			return errors.New("cutover snapshot binding invalid")
		}
	}
	if s.Epoch == 0 || !validDigest(s.Active) || !validDigest(s.LastGood) || s.Data == "" || !filepath.IsAbs(s.Data) || !filepath.IsAbs(s.ActivePath) || !filepath.IsAbs(s.LastGoodPath) {
		return errors.New("incomplete release slot")
	}
	if s.Candidate != "" && !validDigest(s.Candidate) {
		return errors.New("invalid candidate digest")
	}
	if s.Candidate != "" && !filepath.IsAbs(s.CandidatePath) {
		return errors.New("candidate path missing")
	}
	if s.Admission != "" && !validDigest(s.Admission) {
		return errors.New("invalid admission digest")
	}
	if (s.Admission == "") != (s.AdmissionBundle == nil) {
		return errors.New("partial admission bundle")
	}
	if s.AdmissionBundle != nil && (releaseHash(*s.AdmissionBundle) != s.Admission || s.AdmissionBundle.ExpectedEpoch+1 != s.Epoch || s.AdmissionBundle.CandidateSHA256 != s.Candidate || s.AdmissionBundle.StableSHA256 != s.LastGood) {
		return errors.New("admission bundle differs from slot")
	}
	if s.DrainReceipt != "" && !validDigest(s.DrainReceipt) {
		return errors.New("invalid drain receipt")
	}
	if s.DrainNonce != "" && !validDigest(s.DrainNonce) {
		return errors.New("invalid drain nonce")
	}
	if s.ImageSHA256 != "" && !validDigest(s.ImageSHA256) {
		return errors.New("invalid process image digest")
	}
	for _, v := range s.Frozen {
		if !validDigest(v) {
			return errors.New("invalid frozen digest")
		}
	}
	switch s.Phase {
	case "STARTING", "STABLE", "PREPARED", "DRAIN_UNKNOWN", "DRAINED", "EXIT_UNKNOWN", "SWITCHED", "CANARY", "ROLLBACK_PREPARED", "RECOVERING", "ROLLED_BACK", "STOPPED":
	default:
		return errors.New("unknown release phase")
	}
	if (s.PID == 0) != (s.CreatedNS == 0) {
		return errors.New("partial process identity")
	}
	return nil
}

// ReleaseJournal holds an exclusive OS handle for its whole lifetime. The
// append log is authoritative; the atomic descriptor is only a fast view.
type ReleaseJournal struct {
	root string
	lock *os.File
	last releaseEntry
}

func OpenReleaseJournal(root string) (*ReleaseJournal, error) {
	abs, e := filepath.Abs(root)
	if e != nil {
		return nil, e
	}
	if e = EnsureRestoreDirectory(abs); e != nil {
		return nil, e
	}
	actual, e := filepath.EvalSymlinks(abs)
	if e != nil || !strings.EqualFold(filepath.Clean(actual), filepath.Clean(abs)) {
		return nil, errors.New("plain supervisor state directory required")
	}
	p, e := windows.UTF16PtrFromString(filepath.Join(abs, "supervisor.lock"))
	if e != nil {
		return nil, e
	}
	h, e := windows.CreateFile(p, windows.GENERIC_READ|windows.GENERIC_WRITE, 0, nil, windows.OPEN_ALWAYS, windows.FILE_ATTRIBUTE_NORMAL, 0)
	if e != nil {
		return nil, fmt.Errorf("another supervisor owns state: %w", e)
	}
	j := &ReleaseJournal{root: abs, lock: os.NewFile(uintptr(h), "supervisor.lock")}
	if e = j.load(); e != nil {
		j.Close()
		return nil, e
	}
	return j, nil
}

func (j *ReleaseJournal) Close() error        { return j.lock.Close() }
func (j *ReleaseJournal) State() ReleaseState { return cloneReleaseState(j.last.State) }
func (j *ReleaseJournal) Sequence() uint64    { return j.last.Sequence }

// Keep journal ownership at both API boundaries. Explicit cloning preserves
// RawMessage bytes and nil slices, unlike a JSON round trip. New mutable fields
// on ReleaseState or its nested values must be copied here as well.
func cloneReleaseState(s ReleaseState) ReleaseState {
	s.Frozen = slices.Clone(s.Frozen)
	if s.Cutover != nil {
		b := *s.Cutover
		b.Purpose = slices.Clone(b.Purpose)
		b.Migrations = slices.Clone(b.Migrations)
		s.Cutover = &b
	}
	if s.AdmissionBundle != nil {
		a := *s.AdmissionBundle
		s.AdmissionBundle = &a
	}
	if s.RestoreContext != nil {
		r := *s.RestoreContext
		s.RestoreContext = &r
	}
	return s
}

func (j *ReleaseJournal) load() error {
	b, e := os.ReadFile(filepath.Join(j.root, "release.journal"))
	if errors.Is(e, os.ErrNotExist) {
		return nil
	}
	if e != nil {
		return e
	}
	if len(b) == 0 || b[len(b)-1] != '\n' {
		return errors.New("incomplete release journal")
	}
	var previous releaseEntry
	for _, line := range strings.Split(strings.TrimSuffix(string(b), "\n"), "\n") {
		var row releaseEntry
		if e = json.Unmarshal([]byte(line), &row); e != nil {
			return fmt.Errorf("invalid release journal: %w", e)
		}
		if row.Sequence != j.last.Sequence+1 || row.Previous != j.last.Hash || row.Hash != entryHash(row) || validReleaseState(row.State) != nil {
			return errors.New("release journal chain invalid")
		}
		if j.last.Sequence != 0 && row.State.Epoch < j.last.State.Epoch {
			return errors.New("release epoch regressed")
		}
		if err := restoreContextTransition(j.last.State, row.State); err != nil {
			return err
		}
		previous, j.last = j.last, row
	}
	view, e := os.ReadFile(filepath.Join(j.root, "active.json"))
	if errors.Is(e, os.ErrNotExist) {
		return j.writeDescriptor(j.last)
	}
	if e != nil {
		return e
	}
	var descriptor releaseEntry
	if json.Unmarshal(view, &descriptor) != nil {
		return errors.New("release descriptor invalid")
	}
	if reflect.DeepEqual(descriptor, previous) {
		return j.writeDescriptor(j.last)
	}
	if !reflect.DeepEqual(descriptor, j.last) {
		return errors.New("release descriptor differs from journal")
	}
	return nil
}

func (j *ReleaseJournal) Append(s ReleaseState) error {
	s = cloneReleaseState(s)
	if e := validReleaseState(s); e != nil {
		return e
	}
	if j.last.Sequence != 0 && s.Epoch < j.last.State.Epoch {
		return errors.New("release epoch regressed")
	}
	if err := restoreContextTransition(j.last.State, s); err != nil {
		return err
	}
	row := releaseEntry{Sequence: j.last.Sequence + 1, Previous: j.last.Hash, State: s}
	row.Hash = entryHash(row)
	b, _ := json.Marshal(row)
	f, e := os.OpenFile(filepath.Join(j.root, "release.journal"), os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0600)
	if e != nil {
		return e
	}
	if _, e = f.Write(append(b, '\n')); e == nil {
		e = f.Sync()
	}
	if c := f.Close(); e == nil {
		e = c
	}
	if e != nil {
		return e
	}
	j.last = row
	return j.writeDescriptor(row)
}

func restoreContextTransition(previous, next ReleaseState) error {
	if previous.RestoreContext != nil && (next.Operation != previous.Operation || !reflect.DeepEqual(next.RestoreContext, previous.RestoreContext)) {
		return errors.New("restore context is immutable; recovery authorization required")
	}
	return nil
}

// RestoreContextPaths uses one deterministic destination per cutover. A lost
// restore acknowledgement must never manufacture a second recovery point.
func RestoreContextPaths(s ReleaseState) (directory, destination string, err error) {
	b := s.Cutover
	if b == nil || s.AdmissionBundle == nil || !validDigest(s.Operation) || b.Operation != s.Operation || b.Epoch != s.Epoch || !filepath.IsAbs(b.Root) || b.Database != filepath.Join(b.Root, "researchos.sqlite") {
		return "", "", errors.New("restore context cutover binding unavailable")
	}
	host := filepath.Dir(b.Root)
	return filepath.Join(host, "release-state", "recoveries", s.Operation), filepath.Join(host, "restored-"+s.Operation), nil
}

func validRestoreResult(s ReleaseState, r ReleaseRestoreResult) error {
	dir, dest, err := RestoreContextPaths(s)
	if err != nil {
		return err
	}
	if r.Operation != s.Operation || r.Epoch != s.Epoch || r.SourceRoot != s.Cutover.Root || r.Destination != dest || r.ContextPath != filepath.Join(dir, "context.json") || !validDigest(r.ContextSHA256) || r.ManifestSHA256 != s.Cutover.ManifestSHA256 || !validDigest(r.ManifestSHA256) || s.Data != r.SourceRoot {
		return errors.New("restore context result binding changed")
	}
	if s.RestoreContext != nil && (s.Phase != "RECOVERING" || s.PID != 0 || s.CreatedNS != 0 || s.ImageSHA256 != "") {
		return errors.New("restore context cannot authorize an active release slot")
	}
	return nil
}

// ObserveRestorePath reuses Windows handle identity. Resolving the opened path
// also rejects parent junction aliases; metadata alone never grants authority.
func ObserveRestorePath(path string, directory bool) (RestorePathIdentity, error) {
	var result RestorePathIdentity
	if !filepath.IsAbs(path) || filepath.Clean(path) != path {
		return result, errors.New("plain absolute recovery path required")
	}
	name, err := windows.UTF16PtrFromString(path)
	if err != nil {
		return result, err
	}
	// Check the opened component itself before following it, including junctions.
	attributes, err := windows.GetFileAttributes(name)
	if err != nil || attributes&windows.FILE_ATTRIBUTE_REPARSE_POINT != 0 {
		return result, errors.New("recovery reparse point rejected")
	}
	h, err := windows.CreateFile(name, windows.FILE_READ_ATTRIBUTES, windows.FILE_SHARE_READ|windows.FILE_SHARE_WRITE|windows.FILE_SHARE_DELETE, nil, windows.OPEN_EXISTING, windows.FILE_FLAG_BACKUP_SEMANTICS, 0)
	if err != nil {
		return result, err
	}
	defer windows.CloseHandle(h)
	var info windows.ByHandleFileInformation
	if err = windows.GetFileInformationByHandle(h, &info); err != nil {
		return result, err
	}
	if (info.FileAttributes&windows.FILE_ATTRIBUTE_DIRECTORY != 0) != directory {
		return result, errors.New("recovery path kind changed")
	}
	buffer := make([]uint16, 32768)
	n, err := windows.GetFinalPathNameByHandle(h, &buffer[0], uint32(len(buffer)), 0)
	if err != nil || n == 0 || n >= uint32(len(buffer)) {
		return result, errors.New("recovery native path resolution failed")
	}
	resolved := windows.UTF16ToString(buffer[:n])
	if strings.HasPrefix(resolved, `\\?\UNC\`) {
		resolved = `\\` + strings.TrimPrefix(resolved, `\\?\UNC\`)
	} else {
		resolved = strings.TrimPrefix(resolved, `\\?\`)
	}
	if !strings.EqualFold(filepath.Clean(resolved), path) {
		return result, errors.New("recovery path alias rejected")
	}
	return RestorePathIdentity{Path: path, FileID: fmt.Sprintf("%08x:%08x:%08x", info.VolumeSerialNumber, info.FileIndexHigh, info.FileIndexLow), Directory: directory}, nil
}

// EnsureRestoreDirectory validates the existing ancestor before any write,
// then creates and checks one component at a time. It grants no protection
// against a hostile process concurrently replacing directories for this user.
func EnsureRestoreDirectory(path string) error {
	if !filepath.IsAbs(path) || filepath.Clean(path) != path {
		return errors.New("plain absolute recovery directory required")
	}
	missing := []string{}
	ancestor := path
	for {
		_, err := os.Lstat(ancestor)
		if err == nil {
			break
		}
		if !os.IsNotExist(err) {
			return err
		}
		parent := filepath.Dir(ancestor)
		if parent == ancestor {
			return errors.New("recovery ancestor unavailable")
		}
		missing = append(missing, ancestor)
		ancestor = parent
	}
	identity, err := ObserveRestorePath(ancestor, true)
	if err != nil {
		return err
	}
	for i := len(missing) - 1; i >= 0; i-- {
		if err = restorePathUnchanged(identity); err != nil {
			return err
		}
		if err = os.Mkdir(missing[i], 0700); err != nil {
			return err
		}
		identity, err = ObserveRestorePath(missing[i], true)
		if err != nil {
			return err
		}
	}
	return nil
}

func restorePathUnchanged(want RestorePathIdentity) error {
	got, err := ObserveRestorePath(want.Path, want.Directory)
	if err != nil || got != want {
		return errors.New("recovery native file identity changed")
	}
	return nil
}

// RestoreFileDigest verifies the identity around a read-only file hash. It is
// used while the source root is leased and before the restored writer starts.
func RestoreFileDigest(want RestorePathIdentity) (string, error) {
	h := sha256.New()
	if err := readRestoreFile(want, func(r io.Reader) error { _, err := io.Copy(h, r); return err }); err != nil {
		return "", err
	}
	return hex.EncodeToString(h.Sum(nil)), nil
}

// ReadRestoreFile returns actual bytes from the handle whose identity is checked.
func ReadRestoreFile(want RestorePathIdentity) ([]byte, error) {
	var raw []byte
	err := readRestoreFile(want, func(r io.Reader) error { var err error; raw, err = io.ReadAll(r); return err })
	return raw, err
}

func readRestoreFile(want RestorePathIdentity, consume func(io.Reader) error) error {
	if want.Directory {
		return errors.New("recovery file required")
	}
	if err := restorePathUnchanged(want); err != nil {
		return err
	}
	f, err := os.Open(want.Path)
	if err != nil {
		return err
	}
	defer f.Close()
	var info windows.ByHandleFileInformation
	if err = windows.GetFileInformationByHandle(windows.Handle(f.Fd()), &info); err != nil || fmt.Sprintf("%08x:%08x:%08x", info.VolumeSerialNumber, info.FileIndexHigh, info.FileIndexLow) != want.FileID {
		return errors.New("recovery hash handle identity changed")
	}
	if err = consume(f); err != nil {
		return err
	}
	return restorePathUnchanged(want)
}

// ValidateReleaseRestoreResult verifies immutable bytes and native identities,
// not a current actor, business gain, generation qualification or OS isolation.
func ValidateReleaseRestoreResult(s ReleaseState, result ReleaseRestoreResult) (ReleaseRestoreContext, error) {
	var c ReleaseRestoreContext
	if err := validRestoreResult(s, result); err != nil {
		return c, err
	}
	raw, err := os.ReadFile(result.ContextPath)
	if err != nil || ReleaseBytesDigest(raw) != result.ContextSHA256 {
		return c, errors.New("restore context missing or changed")
	}
	if err = json.Unmarshal(raw, &c); err != nil {
		return c, err
	}
	a, b := s.AdmissionBundle, s.Cutover
	if c.Format != ReleaseRestoreContextFormat || c.Status != RecoveryAuthorizationBlocked || c.Operation != s.Operation || c.Project != a.Project || c.Candidate != a.CandidateID || c.AdmissionSHA256 != s.Admission || releaseHash(*a) != s.Admission || c.ManifestSHA256 != b.ManifestSHA256 || c.PurposeSHA256 != ReleaseBytesDigest(b.Purpose) || c.SnapshotEpoch != a.ExpectedEpoch || c.HostEpoch != s.Epoch || c.SnapshotEpoch+1 != c.HostEpoch {
		return c, errors.New("restore context lineage changed")
	}
	if c.Manifest.Path != filepath.Join(b.Directory, "manifest.json") || b.Directory != filepath.Join(filepath.Dir(b.Root), "release-state", "cutovers", s.Operation) || c.Manifest.Directory || !validDigest(c.ManifestRawSHA256) {
		return c, errors.New("restore manifest location changed")
	}
	manifestRaw, err := ReadRestoreFile(c.Manifest)
	if err != nil || ReleaseBytesDigest(manifestRaw) != c.ManifestRawSHA256 {
		return c, errors.New("restore manifest bytes or identity changed")
	}
	var manifest struct {
		Purpose    json.RawMessage `json:"purpose"`
		Migrations []int           `json:"migrations"`
	}
	if json.Unmarshal(manifestRaw, &manifest) != nil || releaseHash(manifest.Purpose) != releaseHash(b.Purpose) || !reflect.DeepEqual(manifest.Migrations, b.Migrations) {
		return c, errors.New("restore manifest purpose or migrations changed")
	}
	if c.SourceRoot.Path != b.Root || !c.SourceRoot.Directory || c.SourceDatabase.Path != b.Database || c.DestinationRoot.Path != result.Destination || !c.DestinationRoot.Directory || c.DestinationDatabase.Path != filepath.Join(result.Destination, "researchos.sqlite") || c.Report.Path != filepath.Join(result.Destination, "restore-report.json") {
		return c, errors.New("restore context location changed")
	}
	for _, p := range []RestorePathIdentity{c.SourceRoot, c.SourceDatabase, c.DestinationRoot, c.DestinationDatabase, c.Report} {
		if err = restorePathUnchanged(p); err != nil {
			return c, err
		}
	}
	for _, file := range []struct {
		path   RestorePathIdentity
		digest string
	}{{c.SourceDatabase, c.SourceDatabaseSHA256}, {c.DestinationDatabase, c.DestinationDatabaseSHA256}, {c.Report, c.ReportSHA256}} {
		digest, e := RestoreFileDigest(file.path)
		if e != nil || !validDigest(file.digest) || digest != file.digest {
			return c, errors.New("restore context file bytes changed")
		}
	}
	if !validDigest(c.BeforeRowsSHA256) || !validDigest(c.AfterRowsSHA256) || len(c.AllowedDelta) == 0 {
		return c, errors.New("restore context recovery delta absent")
	}
	previousTable := ""
	for _, delta := range c.AllowedDelta {
		if delta.Table <= previousTable || !validDigest(delta.BeforeSHA256) || !validDigest(delta.AfterSHA256) || delta.BeforeSHA256 == delta.AfterSHA256 || delta.BeforeRows < 0 || delta.AfterRows < 0 {
			return c, errors.New("restore context recovery delta invalid")
		}
		switch delta.Table {
		case "auth_credentials", "retrieval_roots", "backup_restore_barriers", "evolution_slots":
		default:
			return c, errors.New("restore context recovery delta outside allowed tables")
		}
		previousTable = delta.Table
	}
	reportRaw, err := os.ReadFile(c.Report.Path)
	if err != nil || ReleaseBytesDigest(reportRaw) != c.ReportSHA256 {
		return c, errors.New("restore report bytes changed")
	}
	var report struct {
		Status string          `json:"status"`
		Before json.RawMessage `json:"before"`
		After  json.RawMessage `json:"after"`
	}
	if json.Unmarshal(reportRaw, &report) != nil || report.Status != "RESTORED_RECONCILIATION_REQUIRED" || releaseHash(report.Before) != releaseHash(c.BeforeInventory) || releaseHash(report.After) != releaseHash(c.AfterInventory) {
		return c, errors.New("restore report inventory binding changed")
	}
	return c, nil
}

// BindRestoreContext is idempotent for the same context only. It deliberately
// keeps Data at the source root: the restored copy has no recovery authority.
func (j *ReleaseJournal) BindRestoreContext(result ReleaseRestoreResult) error {
	s := j.State()
	if _, err := ValidateReleaseRestoreResult(s, result); err != nil {
		return err
	}
	if s.RestoreContext != nil {
		if *s.RestoreContext != result {
			return errors.New("restore context already bound differently")
		}
		return nil
	}
	s.RestoreContext = &result
	s.Phase = "RECOVERING"
	clearProcess(&s)
	return j.Append(s)
}

func (j *ReleaseJournal) writeDescriptor(row releaseEntry) error {
	b, _ := json.Marshal(row)
	temp := filepath.Join(j.root, "active.tmp")
	f, e := os.OpenFile(temp, os.O_CREATE|os.O_TRUNC|os.O_WRONLY, 0600)
	if e != nil {
		return e
	}
	if _, e = f.Write(b); e == nil {
		e = f.Sync()
	}
	if c := f.Close(); e == nil {
		e = c
	}
	if e != nil {
		return e
	}
	a, _ := windows.UTF16PtrFromString(temp)
	z, _ := windows.UTF16PtrFromString(filepath.Join(j.root, "active.json"))
	return windows.MoveFileEx(a, z, windows.MOVEFILE_REPLACE_EXISTING|windows.MOVEFILE_WRITE_THROUGH)
}
