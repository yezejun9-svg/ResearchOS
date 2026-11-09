//go:build windows

package qualificationmaintenancejournal

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

func replacementFixture(t *testing.T) (string, replacementPlan) {
	t.Helper()
	root := t.TempDir()
	for _, path := range []string{filepath.Join(root, "host"), filepath.Join(root, "host", ReplacementNamespace)} {
		if err := createPrivateDirectory(path); err != nil {
			t.Fatal(err)
		}
	}
	install := replacementInstallation{Schema: "fixture", ServiceID: "first", Protocol: "v1", Executable: "worker.exe", ExecutableHash: digest([]byte("worker")), SourceCommit: "fixture", Arguments: []string{"--first"}}
	installHash, err := hash(install)
	if err != nil {
		t.Fatal(err)
	}
	old := replacementRegistration{Schema: "researchos.runtime-verifier-registration.v1", OwnerHost: "host", OwnerPrincipal: "owner", ServiceRoot: "service", InstallHash: installHash, Installation: install}
	oldBytes, err := json.MarshalIndent(old, "", "  ")
	if err != nil {
		t.Fatal(err)
	}
	install.Executable, install.ExecutableHash, install.SourceCommit = "worker-2.exe", digest([]byte("worker-2")), "fixture-2"
	newHash, err := hash(install)
	if err != nil {
		t.Fatal(err)
	}
	next := old
	next.Installation, next.InstallHash = install, newHash
	newBytes, err := json.MarshalIndent(next, "", "  ")
	if err != nil {
		t.Fatal(err)
	}
	oldHash, _ := hash(old)
	nextHash, _ := hash(next)
	p := replacementPlan{Schema: replacementPlanSchema, HistorySequence: 1, OperationID: "00112233445566778899aabbccddeeff", CreatedAt: time.Now().UTC().Format(time.RFC3339Nano),
		DataRoot: root, HostPath: filepath.Join(root, "host"), DBPath: filepath.Join(root, "researchos.sqlite"), HostID: "host", Owner: "owner", Root: "service", SchemaVersion: 24,
		StateSHA256: digest([]byte("state")), OldBytes: oldBytes, OldSHA256: digest(oldBytes), OldHash: oldHash, OldInstallationHash: installHash,
		ManifestSHA256: digest([]byte("manifest")), Installation: install, NewBytes: newBytes, NewSHA256: digest(newBytes), NewHash: nextHash, NewInstallationHash: newHash}
	if err := replacementPlanValid(p, root, p.OperationID); err != nil {
		t.Fatal(err)
	}
	if err := createPrivateFile(filepath.Join(root, "host", "runtime-verifier-installation.json"), oldBytes); err != nil {
		t.Fatal(err)
	}
	return root, p
}

func writeReplacementFixture(t *testing.T, p replacementPlan, states ...string) (string, string) {
	t.Helper()
	dir := filepath.Join(p.DataRoot, "host", ReplacementNamespace, p.OperationID)
	if err := createPrivateDirectory(dir); err != nil {
		t.Fatal(err)
	}
	raw, err := json.Marshal(p)
	if err != nil {
		t.Fatal(err)
	}
	for name, body := range map[string][]byte{"plan.json": raw, "old-registration.bin": p.OldBytes, "new-registration.bin": p.NewBytes} {
		if err := createPrivateFile(filepath.Join(dir, name), body); err != nil {
			t.Fatal(err)
		}
	}
	planDigest := digest(raw)
	previous := ""
	for i, state := range states {
		event := replacementEvent{Schema: replacementEventSchema, Sequence: i + 1, Previous: previous, OperationID: p.OperationID, PlanSHA256: planDigest,
			OldSHA256: p.OldSHA256, NewSHA256: p.NewSHA256, State: state, At: time.Now().UTC().Format(time.RFC3339Nano)}
		event.Hash, err = hash(event)
		if err != nil {
			t.Fatal(err)
		}
		body, err := json.Marshal(event)
		if err != nil {
			t.Fatal(err)
		}
		if err := createPrivateFile(filepath.Join(dir, eventFileName(event)), body); err != nil {
			t.Fatal(err)
		}
		previous = event.Hash
	}
	return planDigest, previous
}

func eventFileName(event replacementEvent) string {
	return fmt.Sprintf("%04d-%s.json", event.Sequence, strings.ToLower(event.State))
}

func TestReplacementOwnPendingChecksExactCurrentTransition(t *testing.T) {
	for _, applied := range []bool{false, true} {
		t.Run(map[bool]string{false: "before_publish", true: "after_publish"}[applied], func(t *testing.T) {
			root, first := replacementFixture(t)
			_, terminal := writeReplacementFixture(t, first, "PREPARED", "PUBLISHING", "COMMITTED")
			firstDir := filepath.Join(root, "host", ReplacementNamespace, first.OperationID)
			if err := createPrivateFile(filepath.Join(firstDir, "actual-backup.bin"), first.OldBytes); err != nil {
				t.Fatal(err)
			}
			target := filepath.Join(root, "host", "runtime-verifier-installation.json")
			if err := os.WriteFile(target, first.NewBytes, 0600); err != nil {
				t.Fatal(err)
			}
			firstRaw, _ := os.ReadFile(filepath.Join(firstDir, "plan.json"))
			second := first
			second.OperationID = "ffeeddccbbaa99887766554433221100"
			second.HistorySequence = 2
			second.PredecessorOperation = first.OperationID
			second.PredecessorPlanSHA256 = digest(firstRaw)
			second.PredecessorTerminalHash = terminal
			second.OldBytes, second.OldSHA256, second.OldHash, second.OldInstallationHash = first.NewBytes, first.NewSHA256, first.NewHash, first.NewInstallationHash
			second.Installation.Executable, second.Installation.ExecutableHash, second.Installation.SourceCommit = "worker-3.exe", digest([]byte("worker-3")), "fixture-3"
			second.NewInstallationHash, _ = hash(second.Installation)
			var next replacementRegistration
			if err := json.Unmarshal(second.OldBytes, &next); err != nil {
				t.Fatal(err)
			}
			next.Installation, next.InstallHash = second.Installation, second.NewInstallationHash
			second.NewHash, _ = hash(next)
			second.NewBytes, _ = json.MarshalIndent(next, "", "  ")
			second.NewSHA256 = digest(second.NewBytes)
			if err := replacementPlanValid(second, root, second.OperationID); err != nil {
				t.Fatal(err)
			}
			digest, _ := writeReplacementFixture(t, second, "PREPARED", "PUBLISHING")
			secondDir := filepath.Join(root, "host", ReplacementNamespace, second.OperationID)
			if applied {
				if err := createPrivateFile(filepath.Join(secondDir, "actual-backup.bin"), second.OldBytes); err != nil {
					t.Fatal(err)
				}
				if err := os.WriteFile(target, second.NewBytes, 0600); err != nil {
					t.Fatal(err)
				}
			} else if err := createPrivateFile(filepath.Join(secondDir, "stage.bin"), second.NewBytes); err != nil {
				t.Fatal(err)
			}
			if err := CheckOrdinary(root); err == nil {
				t.Fatal("ordinary acquisition admitted pending replacement")
			}
			permit, status, err := OpenOwnInspection(root, ReplacementNamespace, second.OperationID, digest)
			if err != nil || status.State != "PUBLISHING" || status.Applied != applied {
				t.Fatalf("own pending transition: %#v %v", status, err)
			}
			if _, err := permit.Check(root); err != nil {
				t.Fatal(err)
			}
			if _, _, err := OpenOwnInspection(root, QualificationNamespace, second.OperationID, digest); err == nil {
				t.Fatal("C own permit exempted replacement pending operation")
			}
			if _, _, err := OpenOwnInspection(root, ReplacementNamespace, first.OperationID, digest); err == nil {
				t.Fatal("wrong operation/plan admitted")
			}
			if err := os.WriteFile(target, []byte("changed"), 0600); err != nil {
				t.Fatal(err)
			}
			if _, err := permit.Check(root); err == nil {
				t.Fatal("target drift admitted by cached permit")
			}
		})
	}
}
