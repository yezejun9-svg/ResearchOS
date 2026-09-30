//go:build windows

package supervisor

import (
	"context"
	"encoding/json"
	"errors"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

type fixtureBarrier struct{ driver ProcessDriver }

func (b fixtureBarrier) Drain(_ context.Context, p ProcessIdentity, operation string) (string, error) {
	alive, err := b.driver.Alive(p)
	if err != nil || !alive {
		return "", errors.New("stable OS process absent at drain")
	}
	return releaseHash("fixture-drained:" + operation), nil
}
func (b fixtureBarrier) Ready(_ context.Context, p ProcessIdentity, _ string) error {
	for i := 0; i < 40; i++ {
		alive, err := b.driver.Alive(p)
		if err != nil {
			return err
		}
		if alive {
			return nil
		}
		time.Sleep(10 * time.Millisecond)
	}
	return errors.New("fixture child not ready")
}
func (b fixtureBarrier) Compatible(_ context.Context, s ReleaseState) error {
	if s.Data == "" || s.Backup == "" {
		return errors.New("fixture compatibility evidence absent")
	}
	return nil
}

func buildReleaseFixture(t *testing.T, name, variant string) string {
	t.Helper()
	goexe := os.Getenv("RESEARCHOS_GO")
	if goexe == "" {
		goexe = "go"
	}
	path := filepath.Join(t.TempDir(), name+".exe")
	cmd := exec.Command(goexe, "build", "-trimpath", "-buildvcs=false", "-ldflags=-X main.variant="+variant, "-o", path, "./ops/canary/release_fixture")
	cmd.Dir = filepath.Join("..", "..")
	cmd.Env = append(os.Environ(), "GOTOOLCHAIN=local", "GOENV=off", "GOFLAGS=-mod=readonly")
	if b, e := cmd.CombinedOutput(); e != nil {
		t.Fatalf("build fixture: %v\n%s", e, b)
	}
	return path
}

func openFixtureEngine(t *testing.T, root string, driver ProcessDriver) (*ReleaseJournal, *ReleaseEngine) {
	t.Helper()
	j, e := OpenReleaseJournal(root)
	if e != nil {
		t.Fatal(e)
	}
	engine, e := NewReleaseEngine(j, driver, fixtureBarrier{driver}, func(a ReleaseAdmission) error {
		if a.VerifierReceiptSHA256 != releaseHash("independent-fixture-review") {
			return errors.New("verifier receipt unknown")
		}
		return nil
	})
	if e != nil {
		t.Fatal(e)
	}
	return j, engine
}

func fixtureAdmission(s ReleaseState, candidate string) ReleaseAdmission {
	return ReleaseAdmission{Operation: "operation-1", ExpectedEpoch: s.Epoch, StableSHA256: s.Active, CandidateSHA256: candidate,
		BackupReceiptSHA256: releaseHash("isolated-fixture-backup"), VerifierReceiptSHA256: releaseHash("independent-fixture-review"),
		HoldoutProofSHA256: releaseHash("private-fixture-proof"), SameSchema: true, NoUnknownEffects: true, ExpiresUTC: time.Now().Add(time.Hour).UTC()}
}

func TestReleaseFixtureNativeSwitchRestartRollback(t *testing.T) {
	stable := buildReleaseFixture(t, "stable", "stable")
	candidate := buildReleaseFixture(t, "candidate", "candidate")
	_, candidateHash, e := exactImage(candidate)
	if e != nil {
		t.Fatal(e)
	}
	root := filepath.Join(t.TempDir(), "supervisor")
	data := filepath.Join(t.TempDir(), "data")
	driver := NativeFixtureDriver{Args: func(token, data string) []string { return []string{token, data} }}
	j, engine := openFixtureEngine(t, root, driver)
	defer func() { _ = j.Close() }()
	ctx := context.Background()
	if e = engine.BootstrapFixture(ctx, stable, data); e != nil {
		t.Fatal(e)
	}
	defer func() {
		s := j.State()
		if s.PID != 0 {
			_ = driver.Stop(processIn(s))
		}
	}()
	initial := j.State()
	admission := fixtureAdmission(initial, candidateHash)
	if _, e = engine.PrepareFixture(admission, candidate); e != nil {
		t.Fatal(e)
	}
	if _, e = engine.SwitchFixture(ctx, admission.Operation); e != nil {
		t.Fatal(e)
	}
	canary := j.State()
	if canary.Phase != "CANARY" || canary.Active != candidateHash || canary.PID == initial.PID || canary.Epoch != 2 {
		t.Fatalf("candidate process not active: %+v", canary)
	}
	if alive, e := driver.Alive(processIn(initial)); e != nil || alive {
		t.Fatalf("stable still alive: %v %v", alive, e)
	}
	if e = j.Close(); e != nil {
		t.Fatal(e)
	}
	j, engine = openFixtureEngine(t, root, driver)
	if recovered, e := engine.Reconcile(); e != nil || recovered.PID != canary.PID {
		t.Fatalf("restart reconcile: %+v %v", recovered, e)
	}
	if _, e = engine.SwitchFixture(ctx, admission.Operation); e == nil {
		t.Fatal("duplicate switch was accepted")
	}
	if _, e = engine.RollbackFixture(ctx, admission.Operation); e != nil {
		t.Fatal(e)
	}
	rolled := j.State()
	if rolled.Phase != "ROLLED_BACK" || rolled.Active != initial.Active || rolled.PID == canary.PID || len(rolled.Frozen) != 1 || rolled.Frozen[0] != candidateHash {
		t.Fatalf("rollback not observed: %+v", rolled)
	}
	if alive, e := driver.Alive(processIn(canary)); e != nil || alive {
		t.Fatalf("candidate still alive: %v %v", alive, e)
	}
	admission2 := fixtureAdmission(rolled, candidateHash)
	admission2.Operation = "renamed-operation"
	if _, e = engine.PrepareFixture(admission2, candidate); e == nil || !strings.Contains(e.Error(), "frozen") {
		t.Fatalf("frozen candidate reopened: %v", e)
	}
	if e = j.Close(); e != nil {
		t.Fatal(e)
	}
}

func TestReleaseJournalTamperAndExclusiveLock(t *testing.T) {
	root := filepath.Join(t.TempDir(), "state")
	j, e := OpenReleaseJournal(root)
	if e != nil {
		t.Fatal(e)
	}
	if other, e := OpenReleaseJournal(root); e == nil {
		other.Close()
		t.Fatal("second supervisor got lock")
	}
	h := releaseHash("stable")
	s := ReleaseState{Epoch: 1, Phase: "STABLE", Operation: "bootstrap", Active: h, ActivePath: filepath.Join(root, "stable.exe"), LastGood: h, LastGoodPath: filepath.Join(root, "stable.exe"), Data: root}
	if e = j.Append(s); e != nil {
		t.Fatal(e)
	}
	j.Close()
	view := filepath.Join(root, "active.json")
	if e = os.WriteFile(view, []byte(`{"sequence":999}`), 0600); e != nil {
		t.Fatal(e)
	}
	if reopened, e := OpenReleaseJournal(root); e == nil {
		reopened.Close()
		t.Fatal("tampered descriptor accepted")
	}
}

func TestReleaseJournalRecoversCompleteAppendWithoutDescriptor(t *testing.T) {
	root := filepath.Join(t.TempDir(), "state")
	j, e := OpenReleaseJournal(root)
	if e != nil {
		t.Fatal(e)
	}
	h := releaseHash("stable")
	s := ReleaseState{Epoch: 1, Phase: "STABLE", Operation: "bootstrap", Active: h, ActivePath: filepath.Join(root, "stable.exe"), LastGood: h, LastGoodPath: filepath.Join(root, "stable.exe"), Data: root}
	if e = j.Append(s); e != nil {
		t.Fatal(e)
	}
	s.Phase = "PREPARED"
	s.Candidate = releaseHash("candidate")
	s.CandidatePath = filepath.Join(root, "candidate.exe")
	if e = j.Append(s); e != nil {
		t.Fatal(e)
	}
	raw, e := os.ReadFile(filepath.Join(root, "release.journal"))
	if e != nil {
		t.Fatal(e)
	}
	var previous releaseEntry
	if e = json.Unmarshal([]byte(strings.Split(string(raw), "\n")[0]), &previous); e != nil {
		t.Fatal(e)
	}
	if e = j.writeDescriptor(previous); e != nil {
		t.Fatal(e)
	}
	j.Close()
	reopened, e := OpenReleaseJournal(root)
	if e != nil {
		t.Fatalf("complete append not reconciled: %v", e)
	}
	if reopened.Sequence() != 2 || reopened.State().Phase != "PREPARED" {
		t.Fatal("journal did not recover last complete entry")
	}
	reopened.Close()
}

type countDriver struct{ starts int }

func (d *countDriver) Start(_, _, _ string) (ProcessIdentity, error) {
	d.starts++
	return ProcessIdentity{}, nil
}
func (*countDriver) Alive(ProcessIdentity) (bool, error) { return false, nil }
func (*countDriver) Stop(ProcessIdentity) error          { return nil }

func TestReleaseUnknownStartNeverReplayed(t *testing.T) {
	root := filepath.Join(t.TempDir(), "state")
	j, e := OpenReleaseJournal(root)
	if e != nil {
		t.Fatal(e)
	}
	defer j.Close()
	h := releaseHash("candidate")
	s := ReleaseState{Epoch: 2, Phase: "SWITCHED", Operation: "operation-1", Active: h, ActivePath: filepath.Join(root, "candidate.exe"), LastGood: releaseHash("stable"), LastGoodPath: filepath.Join(root, "stable.exe"), Candidate: h, CandidatePath: filepath.Join(root, "candidate.exe"), Data: root}
	if e = j.Append(s); e != nil {
		t.Fatal(e)
	}
	d := &countDriver{}
	engine, e := NewReleaseEngine(j, d, fixtureBarrier{d}, func(ReleaseAdmission) error { return nil })
	if e != nil {
		t.Fatal(e)
	}
	if _, e = engine.Reconcile(); e == nil || d.starts != 0 {
		t.Fatalf("uncertain launch replayed: %v starts=%d", e, d.starts)
	}
	if _, e = engine.RollbackFixture(context.Background(), s.Operation); e == nil || d.starts != 0 {
		t.Fatalf("unknown child allowed rollback launch: %v starts=%d", e, d.starts)
	}
}

func TestReleaseAdmissionRevokedBeforeDispatch(t *testing.T) {
	root := filepath.Join(t.TempDir(), "state")
	j, e := OpenReleaseJournal(root)
	if e != nil {
		t.Fatal(e)
	}
	defer j.Close()
	stable, candidate := releaseHash("stable"), releaseHash("candidate")
	a := ReleaseAdmission{Operation: "op", ExpectedEpoch: 1, StableSHA256: stable, CandidateSHA256: candidate, BackupReceiptSHA256: releaseHash("backup"), VerifierReceiptSHA256: releaseHash("review"), HoldoutProofSHA256: releaseHash("holdout"), SameSchema: true, NoUnknownEffects: true, ExpiresUTC: time.Now().Add(time.Hour).UTC()}
	s := ReleaseState{Epoch: 2, Phase: "PREPARED", Operation: "op", Active: stable, ActivePath: filepath.Join(root, "stable.exe"), LastGood: stable, LastGoodPath: filepath.Join(root, "stable.exe"), Candidate: candidate, CandidatePath: filepath.Join(root, "candidate.exe"), Data: root, Admission: releaseHash(a), AdmissionBundle: &a, PID: 123, CreatedNS: 456, ImageSHA256: stable}
	if e = j.Append(s); e != nil {
		t.Fatal(e)
	}
	d := &countDriver{}
	engine, e := NewReleaseEngine(j, d, fixtureBarrier{d}, func(ReleaseAdmission) error { return errors.New("revoked") })
	if e != nil {
		t.Fatal(e)
	}
	if _, e = engine.SwitchFixture(context.Background(), a.Operation); e == nil || d.starts != 0 || j.State().Phase != "PREPARED" {
		t.Fatalf("revoked admission dispatched: %v starts=%d", e, d.starts)
	}
}
