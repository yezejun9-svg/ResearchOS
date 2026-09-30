//go:build windows

package supervisor

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"strings"
	"testing"

	rt "researchos.local/research-os/adapters/runtime"
)

// All tests in this file are public synthetic journal/callback tests. They
// launch no process and supply no release admission or recovery authority.
func recoveryJournalFixture(t *testing.T) (*ReleaseJournal, ReleaseState) {
	t.Helper()
	root := t.TempDir()
	op, stable, candidate := releaseHash("operation"), releaseHash("stable"), releaseHash("candidate")
	a := ReleaseAdmission{Project: "public-test", CandidateID: "candidate", Operation: op, ExpectedEpoch: 7, StableSHA256: stable, CandidateSHA256: candidate}
	data := filepath.Join(root, "data")
	s := ReleaseState{Epoch: 8, Operation: op, Phase: "CANARY", Active: candidate, ActivePath: filepath.Join(root, "never-start-candidate.exe"), LastGood: stable, LastGoodPath: filepath.Join(root, "never-start-stable.exe"), Candidate: candidate, CandidatePath: filepath.Join(root, "never-start-candidate.exe"), Data: data, Admission: releaseHash(a), AdmissionBundle: &a}
	s.Cutover = &ReleaseCutover{Operation: op, Epoch: 8, Root: data, Database: filepath.Join(data, "researchos.sqlite"), ManifestSHA256: releaseHash("manifest"), Migrations: []int{1}, Purpose: json.RawMessage(`{"scope":"SYNTHETIC_PUBLIC_STORAGE_ONLY"}`)}
	j, err := OpenReleaseJournal(filepath.Join(root, "release-state"))
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { j.Close() })
	if err = j.Append(s); err != nil {
		t.Fatal(err)
	}
	return j, s
}

func TestW16RecoveryContextLegacyJournalBytes(t *testing.T) {
	// Literal pre-context JSON field order is the journal's old hash contract.
	const oldState = `{"epoch":1,"operation":"bootstrap","phase":"STABLE","active":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","active_path":"C:\\fixture\\stable.exe","last_known_good":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","last_known_good_path":"C:\\fixture\\stable.exe","data":"C:\\fixture\\data"}`
	var s ReleaseState
	if err := json.Unmarshal([]byte(oldState), &s); err != nil {
		t.Fatal(err)
	}
	raw, err := json.Marshal(s)
	if err != nil || string(raw) != oldState {
		t.Fatal("old state bytes changed", string(raw), err)
	}
	unsigned := `{"sequence":1,"previous":"","state":` + oldState + `,"hash":""}`
	h := sha256.Sum256([]byte(unsigned))
	want := hex.EncodeToString(h[:])
	row := releaseEntry{Sequence: 1, State: s}
	if entryHash(row) != want {
		t.Fatal("old journal hash changed")
	}
	row.Hash = want
	journalRaw, _ := json.Marshal(row)
	root := t.TempDir()
	if err = os.WriteFile(filepath.Join(root, "release.journal"), append(journalRaw, '\n'), 0600); err != nil {
		t.Fatal(err)
	}
	if err = os.WriteFile(filepath.Join(root, "active.json"), journalRaw, 0600); err != nil {
		t.Fatal(err)
	}
	j, err := OpenReleaseJournal(root)
	if err != nil {
		t.Fatal(err)
	}
	defer j.Close()
	got, err := os.ReadFile(filepath.Join(root, "release.journal"))
	if err != nil || !bytes.Equal(got, append(journalRaw, '\n')) || j.State().RestoreContext != nil {
		t.Fatal("old journal rewritten", err)
	}
}

func TestW16RecoveryContextJournalImmutableFence(t *testing.T) {
	for _, mutation := range []string{"remove", "digest", "destination", "phase", "process"} {
		t.Run(mutation, func(t *testing.T) {
			j, s := recoveryJournalFixture(t)
			directory, destination, err := RestoreContextPaths(s)
			if err != nil {
				t.Fatal(err)
			}
			s.Phase = "RECOVERING"
			s.RestoreContext = &ReleaseRestoreResult{Operation: s.Operation, Epoch: s.Epoch, SourceRoot: s.Data, Destination: destination, ContextPath: filepath.Join(directory, "context.json"), ContextSHA256: releaseHash("synthetic-reference-only"), ManifestSHA256: s.Cutover.ManifestSHA256}
			if err = j.Append(s); err != nil {
				t.Fatal(err)
			}
			r := *s.RestoreContext
			s.RestoreContext = &r
			switch mutation {
			case "remove":
				s.RestoreContext = nil
			case "digest":
				s.RestoreContext.ContextSHA256 = releaseHash("changed")
			case "destination":
				s.Data = destination
			case "phase":
				s.Phase = "STABLE"
			case "process":
				s.PID, s.CreatedNS = 123, 456
			}
			if err = j.Append(s); err == nil {
				t.Fatal("context mutation appended")
			}
			// Recompute the chain to prove load validates the transition itself,
			// rather than merely noticing a stale hash or stale descriptor.
			row := releaseEntry{Sequence: j.last.Sequence + 1, Previous: j.last.Hash, State: s}
			row.Hash = entryHash(row)
			raw, _ := json.Marshal(row)
			file, err := os.OpenFile(filepath.Join(j.root, "release.journal"), os.O_APPEND|os.O_WRONLY, 0600)
			if err != nil {
				t.Fatal(err)
			}
			_, err = file.Write(append(raw, '\n'))
			file.Close()
			if err != nil {
				t.Fatal(err)
			}
			if err = os.WriteFile(filepath.Join(j.root, "active.json"), raw, 0600); err != nil {
				t.Fatal(err)
			}
			j.Close()
			reopened, err := OpenReleaseJournal(j.root)
			if err == nil {
				reopened.Close()
				t.Fatal("context mutation loaded")
			}
		})
	}
}

func TestW16RecoveryContextCallbackFailureAndLegacy(t *testing.T) {
	t.Run("typed-error-never-falls-back", func(t *testing.T) {
		j, s := recoveryJournalFixture(t)
		calls, legacyCalls := 0, 0
		d := &ControlFixtureDriver{Journal: j, RestoreWithContext: func(_ context.Context, _ ReleaseState, lease *rt.DataRootLease) (ReleaseRestoreResult, error) {
			calls++
			if !lease.Held() || lease.Root() != s.Data {
				t.Fatal("original source not leased")
			}
			return ReleaseRestoreResult{}, errors.New("BLOCKED_RESTORE_OUTCOME_UNKNOWN")
		}, Restore: func(context.Context, ReleaseState, *rt.DataRootLease) (string, error) { legacyCalls++; return "", nil }}
		engine, err := NewReleaseEngine(j, d, d, func(ReleaseAdmission) error { return nil })
		if err != nil {
			t.Fatal(err)
		}
		got, err := engine.RollbackFixture(context.Background(), s.Operation)
		if err == nil || !strings.Contains(err.Error(), "BLOCKED_RESTORE_OUTCOME_UNKNOWN") || calls != 1 || legacyCalls != 0 || got.Phase != "RECOVERING" || got.Data != s.Data || got.PID != 0 || got.RestoreContext != nil {
			t.Fatal("uncertain restore escaped", got, err, calls, legacyCalls)
		}
	})
	t.Run("legacy-synthetic-callback-compatible", func(t *testing.T) {
		j, s := recoveryJournalFixture(t)
		destination := filepath.Join(filepath.Dir(s.Data), "legacy-copy")
		d := &ControlFixtureDriver{Journal: j, Restore: func(context.Context, ReleaseState, *rt.DataRootLease) (string, error) { return destination, nil }}
		if err := d.Compatible(context.Background(), s); err != nil {
			t.Fatal(err)
		}
		if j.State().Data != destination || j.State().RestoreContext != nil {
			t.Fatal("legacy callback behavior changed")
		}
	})
	for _, callbackFails := range []bool{false, true} {
		name := "success"
		if callbackFails {
			name = "error"
		}
		t.Run("changed-operation-"+name, func(t *testing.T) {
			j, s := recoveryJournalFixture(t)
			d := &ControlFixtureDriver{Journal: j, Restore: func(context.Context, ReleaseState, *rt.DataRootLease) (string, error) {
				changed := j.State()
				changed.Operation = releaseHash("other-operation")
				cutover := *changed.Cutover
				cutover.Operation = changed.Operation
				changed.Cutover = &cutover
				if err := j.Append(changed); err != nil {
					t.Fatal(err)
				}
				if callbackFails {
					return "", errors.New("restore interrupted")
				}
				return s.Data, nil
			}}
			engine, err := NewReleaseEngine(j, d, d, func(ReleaseAdmission) error { return nil })
			if err != nil {
				t.Fatal(err)
			}
			got, err := engine.RollbackFixture(context.Background(), s.Operation)
			if err == nil || !strings.Contains(err.Error(), "restore changed journal operation or epoch") || got.Operation == s.Operation || j.State().Operation != got.Operation {
				t.Fatal("stale operation overwritten", got, err)
			}
		})
	}
}
