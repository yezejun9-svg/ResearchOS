//go:build windows

package supervisor

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"time"
)

type ReleaseReceipt struct {
	Format          string    `json:"format"`
	Operation       string    `json:"operation"`
	Epoch           uint64    `json:"epoch"`
	Sequence        uint64    `json:"sequence"`
	JournalHash     string    `json:"journal_hash"`
	ActiveSHA256    string    `json:"active_sha256"`
	LastGoodSHA256  string    `json:"last_known_good_sha256"`
	CandidateSHA256 string    `json:"candidate_sha256"`
	PID             uint32    `json:"pid"`
	CreatedNS       int64     `json:"created_ns"`
	ImageSHA256     string    `json:"image_sha256"`
	ProcessAlive    bool      `json:"process_alive"`
	ObservedUTC     time.Time `json:"observed_utc"`
}

func ReleaseBytesDigest(b []byte) string { h := sha256.Sum256(b); return hex.EncodeToString(h[:]) }

func releaseReceiptFile(root, operation string) string {
	return filepath.Join(root, "receipts", operation+".json")
}

// WriteFixtureReceipt persists the raw host observation before the domain
// projection. A repeat reads the existing bytes; it does not re-run a switch.
func WriteFixtureReceipt(root string, j *ReleaseJournal, d ProcessDriver) (ReleaseReceipt, string, error) {
	s := j.State()
	if s.Phase != "CANARY" || s.Operation == "" || s.PID == 0 || s.ImageSHA256 != s.Active {
		return ReleaseReceipt{}, "", errors.New("active canary process absent")
	}
	alive, e := d.Alive(processIn(s))
	if e != nil || !alive {
		return ReleaseReceipt{}, "", errors.New("candidate process not observed alive")
	}
	path := releaseReceiptFile(root, s.Operation)
	if b, e := os.ReadFile(path); e == nil {
		return readFixtureReceiptBytes(b, j, d, s.Operation)
	} else if !errors.Is(e, os.ErrNotExist) {
		return ReleaseReceipt{}, "", e
	}
	r := ReleaseReceipt{Format: "R2_NATIVE_FIXTURE_RECEIPT_V1", Operation: s.Operation, Epoch: s.Epoch, Sequence: j.Sequence(), JournalHash: j.last.Hash, ActiveSHA256: s.Active, LastGoodSHA256: s.LastGood, CandidateSHA256: s.Candidate, PID: s.PID, CreatedNS: s.CreatedNS, ImageSHA256: s.ImageSHA256, ProcessAlive: true, ObservedUTC: time.Now().UTC()}
	b, e := json.Marshal(r)
	if e != nil {
		return r, "", e
	}
	if e = os.MkdirAll(filepath.Dir(path), 0700); e != nil {
		return r, "", e
	}
	f, e := os.OpenFile(path, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if errors.Is(e, os.ErrExist) {
		return ReadFixtureReceipt(root, j, d, s.Operation)
	}
	if e != nil {
		return r, "", e
	}
	if _, e = f.Write(b); e == nil {
		e = f.Sync()
	}
	if c := f.Close(); e == nil {
		e = c
	}
	if e != nil {
		return r, "", e
	}
	return r, ReleaseBytesDigest(b), nil
}

func readFixtureReceiptBytes(b []byte, j *ReleaseJournal, d ProcessDriver, operation string) (ReleaseReceipt, string, error) {
	var r ReleaseReceipt
	if e := json.Unmarshal(b, &r); e != nil {
		return r, "", e
	}
	s := j.State()
	if r.Format != "R2_NATIVE_FIXTURE_RECEIPT_V1" || r.Operation != operation || s.Operation != operation || s.Phase != "CANARY" || r.Epoch != s.Epoch || r.Sequence != j.Sequence() || r.JournalHash != j.last.Hash || r.ActiveSHA256 != s.Active || r.CandidateSHA256 != s.Candidate || r.LastGoodSHA256 != s.LastGood || r.PID != s.PID || r.CreatedNS != s.CreatedNS || r.ImageSHA256 != s.ImageSHA256 || !r.ProcessAlive {
		return r, "", errors.New("raw release receipt does not match supervisor journal")
	}
	alive, e := d.Alive(processIn(s))
	if e != nil || !alive {
		return r, "", errors.New("observed candidate process no longer alive")
	}
	return r, ReleaseBytesDigest(b), nil
}

func ReadFixtureReceipt(root string, j *ReleaseJournal, d ProcessDriver, operation string) (ReleaseReceipt, string, error) {
	b, e := os.ReadFile(releaseReceiptFile(root, operation))
	if e != nil {
		return ReleaseReceipt{}, "", e
	}
	return readFixtureReceiptBytes(b, j, d, operation)
}
