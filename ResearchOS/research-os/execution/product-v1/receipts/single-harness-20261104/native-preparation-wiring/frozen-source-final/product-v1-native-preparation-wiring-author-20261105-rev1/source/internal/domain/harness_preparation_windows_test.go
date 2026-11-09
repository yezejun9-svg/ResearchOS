//go:build windows

package domain

import (
	"context"
	"os"
	"path/filepath"
	"strconv"
	"testing"

	rt "researchos.local/research-os/adapters/runtime"
)

// Claim without invoking a driver. This exercises the real Host submission,
// dispatch manifest and transactional projection with inert Go-only facts.
func harnessPreparationFixture(t *testing.T) (*fixture, *RuntimeCoordinator, harnessPreparationFence, rt.CodexPreparationFailure) {
	t.Helper()
	f, c, binding, driver := harnessRPCTurnFixture(t)
	driver.descriptor.ExecutableHash = Digest([]byte("inert native metadata fixture"))
	driver.snapshot.PolicyIdentity = rt.CodexRPCPolicyIdentity(driver.descriptor.ExecutableHash)
	taskID, _ := harnessSubmitFixture(t, f, c, binding, "inert preparation fixture")
	port := &harnessV1{c: c}
	authTx, owner, err := port.auth(context.Background(), f.token, f.project)
	if err != nil {
		t.Fatal(err)
	}
	authTx.Rollback()
	route, err := port.ensureRuntime(context.Background(), f.token, owner, f.project)
	if err != nil {
		t.Fatal(err)
	}
	tx, err := f.db.BeginTx(context.Background(), nil)
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback()
	if err = resourceWriteLock(tx); err != nil {
		t.Fatal(err)
	}
	scheduler, err := resourcePrincipal(tx, route.schedulerToken, f.project, "SCHEDULER")
	if err != nil {
		t.Fatal(err)
	}
	task, err := load(tx, f.project, "Task", taskID)
	if err != nil {
		t.Fatal(err)
	}
	claim, err := f.s.claimTaskMode(tx, scheduler, f.project, taskID, Object{"runtime_id": route.runtimeID, "executor_principal_id": route.executor, "context_bundle_id": task["context_bundle_id"]}, ID(), false)
	if err != nil {
		t.Fatal(err)
	}
	run := claim["run"].(map[string]any)
	runID := Str(run, "id")
	epoch, _ := Num(run, "lease_epoch")
	dispatch, err := runtimeDispatch(tx, f.project, runID, epoch)
	if err != nil {
		t.Fatal(err)
	}
	worker, locator := ID(), Str(dispatch, "dispatch_key")
	if _, err = tx.Exec("UPDATE runtime_dispatches SET state='STARTED',worker=?,journal_locator=?,updated_at=? WHERE project=? AND run=? AND epoch=?", worker, locator, Now(), f.project, runID, epoch); err != nil {
		t.Fatal(err)
	}
	if err = tx.Commit(); err != nil {
		t.Fatal(err)
	}
	if err = os.MkdirAll(filepath.Join(c.config.DataRoot, "runtime-dispatches", locator), 0700); err != nil {
		t.Fatal(err)
	}
	inputTx, err := f.db.BeginTx(context.Background(), nil)
	if err != nil {
		t.Fatal(err)
	}
	task, err = load(inputTx, f.project, "Task", taskID)
	if err != nil {
		t.Fatal(err)
	}
	record, err := harnessTaskInput(inputTx, f.project, task)
	inputTx.Rollback()
	if err != nil {
		t.Fatal(err)
	}
	policy := rt.CodexRPCPolicyIdentity(driver.descriptor.ExecutableHash)
	fence := harnessPreparationFence{project: f.project, runID: runID, taskID: taskID, worker: worker, locator: locator,
		manifestHash: Str(dispatch, "manifest_hash"), epoch: epoch,
		launch: rt.CodexLaunch{TaskID: taskID, RunID: runID, Epoch: strconv.FormatInt(epoch, 10), Workspace: binding.RealPath, SourceBindingHash: Hash(record["source_binding"])}, policy: policy}
	proof := rt.CodexPreparationFailure{Reason: "QUALIFICATION_POLICY_VIOLATION", NoQualificationChild: true, NoModelDelegation: true,
		TaskID: taskID, RunID: runID, Epoch: strconv.FormatInt(epoch, 10), SourceBindingHash: fence.launch.SourceBindingHash,
		NativeHash: policy.BinarySHA256, HelperHash: Digest([]byte("inert shipped helper")), SyntheticSource: binding.RealPath,
		TemplateHash: policy.RequestedConfigSHA256, HostBoot: "inert-host-boot", QualificationReceiptPath: "inert-private-receipt"}
	return f, c, fence, proof
}

func TestHarnessPreparationFailureAtomicTerminalAndRestart(t *testing.T) {
	f, c, fence, proof := harnessPreparationFixture(t)
	if err := c.finishHarnessPreparationFailure(fence, proof); err != nil {
		t.Fatal(err)
	}
	view := harnessViewFixture(t, f, c, fence.taskID)
	if view["status"] != "FAILED" || view["result"] != nil || view["terminal"] != true || view["failure"].(map[string]any)["code"] != "HARNESS_UNAVAILABLE" {
		t.Fatal("failed preparation projected as model result", view)
	}
	var dispatchState, identity, reason string
	if err := f.db.QueryRow("SELECT state,identity,reason FROM runtime_dispatches WHERE project=? AND run=? AND epoch=?", f.project, fence.runID, fence.epoch).Scan(&dispatchState, &identity, &reason); err != nil {
		t.Fatal(err)
	}
	if dispatchState != "STARTED" || identity != "{}" || reason == "" {
		t.Fatal("consumed dispatch changed identity", dispatchState, identity, reason)
	}
	var logs, modelResults int
	if err := f.db.QueryRow("SELECT count(*) FROM uploaded_content WHERE sealed=1 AND CAST(bytes AS TEXT) LIKE '%researchos.native-preparation-outcome.v1%'").Scan(&logs); err != nil {
		t.Fatal(err)
	}
	if err := f.db.QueryRow("SELECT count(*) FROM uploaded_content WHERE sealed=1 AND CAST(bytes AS TEXT) LIKE '%researchos.codex-result.v1%'").Scan(&modelResults); err != nil {
		t.Fatal(err)
	}
	if logs != 1 || modelResults != 0 {
		t.Fatal("preparation audit or model result count", logs, modelResults)
	}
	events, err := c.HarnessV1().Events(context.Background(), f.token, HarnessEvents{ProjectID: f.project, TaskID: fence.taskID, Cursor: "0", Limit: 100})
	if err != nil {
		t.Fatal(err)
	}
	terminal := 0
	for _, item := range Arr(events["data"].(map[string]any), "items") {
		if item.(map[string]any)["kind"] == "TASK_TERMINAL" {
			terminal++
		}
	}
	if terminal != 1 {
		t.Fatal("expected exactly one terminal event", terminal)
	}
	if err := c.Recover(context.Background()); err != nil {
		t.Fatal(err)
	}
	if err := c.Scan(context.Background()); err != nil {
		t.Fatal(err)
	}
	c.workers.Wait()
	var runs, logsAfter int
	if err := f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='Run' AND json_extract(body,'$.task_id')=?", f.project, fence.taskID).Scan(&runs); err != nil {
		t.Fatal(err)
	}
	if err := f.db.QueryRow("SELECT count(*) FROM uploaded_content WHERE sealed=1 AND CAST(bytes AS TEXT) LIKE '%researchos.native-preparation-outcome.v1%'").Scan(&logsAfter); err != nil {
		t.Fatal(err)
	}
	if runs != 1 || logsAfter != 1 {
		t.Fatal("terminal preparation relaunched or duplicated", runs, logsAfter)
	}
}

func TestHarnessPreparationFailureRejectsConflictsAndRollsBack(t *testing.T) {
	f, c, fence, proof := harnessPreparationFixture(t)
	stale := proof
	stale.SourceBindingHash = Digest([]byte("different binding"))
	if err := c.finishHarnessPreparationFailure(fence, stale); err == nil {
		t.Fatal("changed source accepted")
	}
	stale = proof
	stale.NoModelDelegation = false
	if err := c.finishHarnessPreparationFailure(fence, stale); err == nil {
		t.Fatal("delegated model accepted")
	}
	marker := filepath.Join(c.config.DataRoot, "runtime-dispatches", fence.locator, "native-turn-authorization.json")
	if err := os.WriteFile(marker, []byte("conflicting turn"), 0600); err != nil {
		t.Fatal(err)
	}
	if err := c.finishHarnessPreparationFailure(fence, proof); err == nil {
		t.Fatal("model turn marker accepted")
	}
	if err := os.Remove(marker); err != nil {
		t.Fatal(err)
	}
	// Abort the final outbox event. Earlier LOG and Run/Task writes must roll back.
	if _, err := f.db.Exec("CREATE TRIGGER preparation_event_abort BEFORE INSERT ON outbox BEGIN SELECT RAISE(ABORT,'inert event fault'); END"); err != nil {
		t.Fatal(err)
	}
	if err := c.finishHarnessPreparationFailure(fence, proof); err == nil {
		t.Fatal("event fault falsely committed failure")
	}
	if _, err := f.db.Exec("DROP TRIGGER preparation_event_abort"); err != nil {
		t.Fatal(err)
	}
	var status string
	if err := f.db.QueryRow("SELECT json_extract(body,'$.status') FROM domain_objects WHERE project=? AND kind='Run' AND id=?", f.project, fence.runID).Scan(&status); err != nil {
		t.Fatal(err)
	}
	if status != "QUEUED" {
		t.Fatal("partial failed Run survived rollback", status)
	}
	var logs int
	if err := f.db.QueryRow("SELECT count(*) FROM uploaded_content WHERE sealed=1 AND CAST(bytes AS TEXT) LIKE '%researchos.native-preparation-outcome.v1%'").Scan(&logs); err != nil {
		t.Fatal(err)
	}
	if logs != 0 {
		t.Fatal("partial audit survived rollback", logs)
	}
	if err := c.finishHarnessPreparationFailure(fence, proof); err != nil {
		t.Fatal("original consumed attempt could not settle", err)
	}
}

func TestHarnessPreparationProofRejectsUnknownAndIncompleteFacts(t *testing.T) {
	_, _, fence, proof := harnessPreparationFixture(t)
	cases := []rt.CodexPreparationFailure{proof}
	change := proof
	change.Reason = "untrusted"
	cases = append(cases, change)
	change = proof
	change.NoQualificationChild = false
	cases = append(cases, change)
	change = proof
	change.NativeHash = Digest([]byte("wrong native"))
	cases = append(cases, change)
	change = proof
	change.HelperHash = "not-a-digest"
	cases = append(cases, change)
	change = proof
	change.SyntheticSource += "-other"
	cases = append(cases, change)
	if !harnessPreparationProofMatches(fence, cases[0]) {
		t.Fatal("known no-child fact rejected")
	}
	for i, candidate := range cases[1:] {
		if harnessPreparationProofMatches(fence, candidate) {
			t.Fatalf("conflicting fact %d accepted", i)
		}
	}
}

func TestHarnessQualifiedSyntheticSourceRejectsOtherWorkspaceBeforeTask(t *testing.T) {
	f, c, binding, _ := harnessRPCTurnFixture(t)
	oldID, _ := harnessSubmitFixture(t, f, c, binding, "historical inert fixture")
	root := t.TempDir()
	source := filepath.Join(root, "S")
	if err := os.Mkdir(source, 0700); err != nil {
		t.Fatal(err)
	}
	helper := filepath.Join(source, "qualification-helper.exe")
	exe := filepath.Join(root, "inert-codex.exe")
	if err := os.WriteFile(helper, []byte("inert helper"), 0600); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(exe, []byte("inert executable metadata"), 0600); err != nil {
		t.Fatal(err)
	}
	descriptor := rt.CodexDescriptor{Present: true, Version: "0.166.0", ExecutableHash: Digest([]byte("inert executable metadata")), AuthState: "LOGGED_IN", AuthKind: "chatgpt", ConfigurationControlled: true}
	driver, err := rt.NewCodexRPCWithNativeQualification(rt.CodexRPCOptions{Executable: exe, Descriptor: descriptor, NormalHome: os.Getenv("USERPROFILE")}, rt.CodexNativeQualificationOptions{
		ApprovedRoot: root, SyntheticSource: source, ShippedHelper: helper, ShippedHelperSHA256: Digest([]byte("inert helper")), HostBuildSHA256: Digest([]byte("inert Host")),
	})
	if err != nil {
		t.Fatal("inert constructor", err)
	}
	if configured, ok := rt.CodexNativeQualificationSource(driver); !ok || configured != source {
		t.Fatal("concrete scope accessor changed", configured, ok)
	}
	c.config.HarnessDriver = driver
	var before, after int
	if err := f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='Task'", f.project).Scan(&before); err != nil {
		t.Fatal(err)
	}
	_, err = c.HarnessV1().Submit(context.Background(), f.token, HarnessSubmit{RequestID: "qualified-wrong-workspace", ProjectID: f.project, WorkspaceRef: binding.AuthorizedRef, HarnessID: "codex", Scope: "workspace-read", Prompt: "inert request"})
	if err == nil {
		t.Fatal("other workspace admitted before Task")
	}
	if err := f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='Task'", f.project).Scan(&after); err != nil {
		t.Fatal(err)
	}
	if before != after {
		t.Fatal("rejected source created a Task", before, after)
	}
	if view := harnessViewFixture(t, f, c, oldID); view["task_ref"].(map[string]any)["task_id"] != oldID {
		t.Fatal("historical Task unreadable", view)
	}
}
