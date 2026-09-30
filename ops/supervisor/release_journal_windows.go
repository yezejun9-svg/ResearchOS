//go:build windows

package supervisor

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"reflect"
	"strings"

	"golang.org/x/sys/windows"
)

// ReleaseState is mechanical deployment state. It is never a domain acceptance
// receipt and is not writable by the candidate in a production installation.
type ReleaseState struct {
	Epoch           uint64            `json:"epoch"`
	Operation       string            `json:"operation"`
	Phase           string            `json:"phase"`
	Active          string            `json:"active"`
	ActivePath      string            `json:"active_path"`
	Candidate       string            `json:"candidate,omitempty"`
	CandidatePath   string            `json:"candidate_path,omitempty"`
	LastGood        string            `json:"last_known_good"`
	LastGoodPath    string            `json:"last_known_good_path"`
	Data            string            `json:"data"`
	Backup          string            `json:"backup,omitempty"`
	Admission       string            `json:"admission,omitempty"`
	AdmissionBundle *ReleaseAdmission `json:"admission_bundle,omitempty"`
	DrainReceipt    string            `json:"drain_receipt,omitempty"`
	DrainNonce      string            `json:"drain_nonce,omitempty"`
	PID             uint32            `json:"pid,omitempty"`
	CreatedNS       int64             `json:"created_ns,omitempty"`
	ImageSHA256     string            `json:"image_sha256,omitempty"`
	Frozen          []string          `json:"frozen,omitempty"`
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
	case "STARTING", "STABLE", "PREPARED", "DRAIN_UNKNOWN", "DRAINED", "EXIT_UNKNOWN", "SWITCHED", "CANARY", "ROLLBACK_PREPARED", "RECOVERING", "ROLLED_BACK":
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
	if e = os.MkdirAll(abs, 0700); e != nil {
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
func (j *ReleaseJournal) State() ReleaseState { return j.last.State }
func (j *ReleaseJournal) Sequence() uint64    { return j.last.Sequence }

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
	if e := validReleaseState(s); e != nil {
		return e
	}
	if j.last.Sequence != 0 && s.Epoch < j.last.State.Epoch {
		return errors.New("release epoch regressed")
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
