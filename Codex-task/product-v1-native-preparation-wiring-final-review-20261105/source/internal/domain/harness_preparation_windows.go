//go:build windows

package domain

import (
	"context"
	"errors"
	"os"
	"path/filepath"
	"strconv"
	"strings"

	rt "researchos.local/research-os/adapters/runtime"
)

// A preparation failure is a consumed attempt, never a model-process result.
// Only runHarness may call this after the concrete B3 handle has terminated.
type harnessPreparationFence struct {
	project, runID, taskID, worker, locator, manifestHash string
	epoch                                                 int64
	launch                                                rt.CodexLaunch
	policy                                                rt.CodexPolicyIdentity
}

func harnessKnownPreparationReason(reason string) bool {
	switch reason {
	case "QUALIFICATION_REQUIRED", "QUALIFICATION_SCOPE_MISMATCH", "QUALIFICATION_BOOTSTRAP_BLOCKED",
		"QUALIFICATION_POLICY_VIOLATION", "QUALIFICATION_CONTROL_INVALID", "QUALIFICATION_INCOMPLETE",
		"QUALIFICATION_IDENTITY_CHANGED", "QUALIFICATION_CLEANUP_UNKNOWN", "QUALIFICATION_RECEIPT_UNCERTAIN",
		"QUALIFICATION_CANCELLED_BEFORE_RPC", "QUALIFICATION_TIME_BUDGET_EXHAUSTED", "QUALIFICATION_TEMPLATE_CHANGED":
		return true
	}
	return false
}

func harnessPreparationProofMatches(f harnessPreparationFence, proof rt.CodexPreparationFailure) bool {
	return f.policy.Transport == rt.CodexRPCTransport && harnessKnownPreparationReason(proof.Reason) && proof.NoModelDelegation &&
		proof.TaskID == f.taskID && proof.RunID == f.runID && proof.Epoch == strconv.FormatInt(f.epoch, 10) &&
		proof.SourceBindingHash == f.launch.SourceBindingHash && proof.SyntheticSource == f.launch.Workspace &&
		proof.NativeHash == f.policy.BinarySHA256 && proof.TemplateHash == f.policy.RequestedConfigSHA256 &&
		preparedAbandonmentDigest(proof.NativeHash) && preparedAbandonmentDigest(proof.HelperHash) &&
		proof.HostBoot != "" && len(proof.HostBoot) <= 128 &&
		(proof.NoQualificationChild && proof.QualificationPID == 0 ||
			!proof.NoQualificationChild && proof.QualificationPID != 0 && proof.QualificationJobZero && proof.StreamsDrained && proof.CleanupComplete)
}

func harnessPreparationMarkerAbsent(root, locator string) error {
	if locator == "" || locator == "." || locator == ".." || filepath.Base(locator) != locator || strings.ContainsAny(locator, `/\`) {
		return errors.New("invalid native dispatch locator")
	}
	if root == "" || !filepath.IsAbs(root) || filepath.Clean(root) != root {
		return errors.New("invalid native data root")
	}
	parent := filepath.Join(root, "runtime-dispatches", locator)
	// A pre-model qualification can fail before B1 creates its model directory.
	// Check every existing ancestor for a reparse or permission surprise; an
	// absent child is ordinary no-delegation evidence, not a fabricated marker.
	for i, path := range []string{root, filepath.Dir(parent), parent} {
		info, err := os.Lstat(path)
		if errors.Is(err, os.ErrNotExist) && i > 0 {
			return nil
		}
		if err != nil || !info.IsDir() || info.Mode()&os.ModeSymlink != 0 {
			return errors.New("native dispatch directory uncertain")
		}
		actual, err := filepath.EvalSymlinks(path)
		if err != nil || !strings.EqualFold(filepath.Clean(actual), filepath.Clean(path)) {
			return errors.New("native dispatch ancestor reparse changed")
		}
	}
	for _, name := range []string{"native-turn-authorization.json", "native-turn-write-intent.json"} {
		_, err := os.Lstat(filepath.Join(parent, name))
		if err == nil || !errors.Is(err, os.ErrNotExist) {
			return errors.New("native turn marker exists or is uncertain")
		}
	}
	return nil
}

func harnessPreparationAudit(f harnessPreparationFence, proof rt.CodexPreparationFailure) Object {
	var receiptPathDigest any
	if proof.QualificationReceiptPath != "" {
		receiptPathDigest = Digest([]byte(proof.QualificationReceiptPath))
	}
	return Object{"schema": "researchos.native-preparation-outcome.v1", "phase": "PREPARATION_FAILED",
		"reason": proof.Reason, "project_id": f.project, "task_id": f.taskID, "run_id": f.runID,
		"epoch": strconv.FormatInt(f.epoch, 10), "dispatch_key": f.locator, "manifest_hash": f.manifestHash,
		"worker": f.worker, "source_binding_hash": proof.SourceBindingHash,
		"synthetic_source_path_sha256": Digest([]byte(proof.SyntheticSource)),
		"expected_native_sha256":       proof.NativeHash, "expected_helper_sha256": proof.HelperHash,
		"requested_template_sha256": proof.TemplateHash, "host_boot": proof.HostBoot,
		"qualification_pid": proof.QualificationPID, "qualification_job_zero": proof.QualificationJobZero,
		"qualification_no_child": proof.NoQualificationChild, "streams_drained": proof.StreamsDrained,
		"cleanup_complete": proof.CleanupComplete, "model_start_delegated": false,
		"qualification_receipt_path_sha256": receiptPathDigest}
}

func (c *RuntimeCoordinator) finishHarnessPreparationFailure(f harnessPreparationFence, proof rt.CodexPreparationFailure) error {
	if !harnessPreparationProofMatches(f, proof) {
		return Fail(412, "STALE_INPUT", "native preparation proof differs from consumed launch")
	}
	if err := harnessPreparationMarkerAbsent(c.config.DataRoot, f.locator); err != nil {
		return err
	}
	audit := harnessPreparationAudit(f, proof)
	terminalReason := "native preparation failed before model launch: " + proof.Reason + "; proof=" + Hash(audit)
	tx, err := c.service.DB.BeginTx(context.Background(), nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	if err = resourceWriteLock(tx); err != nil {
		return err
	}
	run, err := load(tx, f.project, "Run", f.runID)
	if err != nil {
		return err
	}
	if Hash(run["lease_epoch"]) != Hash(f.epoch) || run["task_id"] != f.taskID ||
		run["external_run_id"] != nil || run["exit_code"] != nil || len(Arr(run, "result_artifact_ids")) != 0 {
		return Fail(409, "STATE_CONFLICT", "native preparation Run ownership changed")
	}
	task, err := load(tx, f.project, "Task", f.taskID)
	if err != nil {
		return err
	}
	if task["active_run_id"] != f.runID || task["task_type"] != "harness_turn" {
		return Fail(409, "STATE_CONFLICT", "native preparation Task ownership changed")
	}
	record, err := harnessTaskInput(tx, f.project, task)
	if err != nil {
		return err
	}
	if Hash(record["source_binding"]) != f.launch.SourceBindingHash ||
		record["runtime_id"] != run["runtime_id"] {
		return Fail(412, "STALE_INPUT", "original native submission changed")
	}
	dispatch, err := runtimeDispatch(tx, f.project, f.runID, f.epoch)
	if err != nil {
		return err
	}
	sequence, seqErr := Num(dispatch, "observation_sequence")
	manifest := dispatch["manifest"].(map[string]any)
	profile := manifest["admission"].(map[string]any)["profile"].(map[string]any)
	if seqErr != nil || sequence != 0 || dispatch["state"] != "STARTED" || dispatch["worker"] != f.worker ||
		dispatch["journal_locator"] != f.locator || dispatch["dispatch_key"] != f.locator ||
		dispatch["manifest_hash"] != f.manifestHash || dispatch["observation_hash"] != "" ||
		len(dispatch["identity"].(map[string]any)) != 0 ||
		manifest["task_id"] != f.taskID || manifest["runtime_id"] != run["runtime_id"] ||
		!harnessPolicyMatches(profile, f.policy) {
		return Fail(409, "STATE_CONFLICT", "original native dispatch is no longer an unobserved preparation")
	}
	if err = clientQueueSettled(tx, f.project, f.runID); err != nil {
		return err
	}
	if run["status"] == "FAILED" && (task["status"] == "FAILED" || task["status"] == "DEFERRED_NO_PROGRESS") && dispatch["reason"] == terminalReason &&
		run["execution_report"] == "Native preparation failed before model launch; no automatic replay." &&
		run["children_stopped"] == true && run["queue_empty"] == true {
		var count int
		if err = tx.QueryRow("SELECT count(*) FROM uploaded_content WHERE project=? AND sealed=1 AND content_hash=?", f.project, Digest(Bytes(audit))).Scan(&count); err != nil {
			return err
		}
		if count != 1 {
			return Fail(409, "STATE_CONFLICT", "native preparation audit missing or duplicated")
		}
		if err = c.harnessTerminalInTx(tx, f.project, task, run); err != nil {
			return err
		}
		return tx.Commit()
	}
	if (run["status"] != "QUEUED" && run["status"] != "RUNNING") || task["status"] != "RUNNING" || dispatch["reason"] != "" {
		return Fail(409, "STATE_CONFLICT", "native preparation already settled or conflicted")
	}
	// A marker is only counterevidence. The concrete handle and unchanged empty
	// dispatch identity are the positive proof of no model delegation.
	if err = harnessPreparationMarkerAbsent(c.config.DataRoot, f.locator); err != nil {
		return err
	}
	if _, err = c.service.serverArtifactMode(tx, f.project, Str(record, "principal_id"), "LOG", "LIVE", Bytes(audit), Empty()); err != nil {
		return err
	}
	if err = bump(run); err != nil {
		return err
	}
	run["status"] = "FAILED"
	run["execution_report"] = "Native preparation failed before model launch; no automatic replay."
	run["exit_code"] = nil
	run["result_artifact_ids"] = Empty()
	run["runtime_settled_at"] = Now()
	run["children_stopped"] = true
	run["queue_empty"] = true
	run["ended_at"] = Now()
	if err = c.service.put(tx, "Run", run); err != nil {
		return err
	}
	if err = c.service.event(tx, f.project, "Run", run, Str(record, "principal_id"), ID(), "RUN_CHANGED"); err != nil {
		return err
	}
	if err = c.service.taskFailed(tx, f.project, task, "native preparation failed before model launch"); err != nil {
		return err
	}
	if err = bump(task); err != nil {
		return err
	}
	if err = c.service.put(tx, "Task", task); err != nil {
		return err
	}
	if err = c.service.event(tx, f.project, "Task", task, Str(record, "principal_id"), ID(), "TASK_CHANGED"); err != nil {
		return err
	}
	changed, err := tx.Exec("UPDATE runtime_dispatches SET reason=?,updated_at=? WHERE project=? AND run=? AND epoch=? AND state='STARTED' AND worker=? AND journal_locator=? AND observation_sequence=0 AND observation_hash='' AND identity='{}' AND reason=''", terminalReason, Now(), f.project, f.runID, f.epoch, f.worker, f.locator)
	if err != nil {
		return err
	}
	n, err := changed.RowsAffected()
	if err != nil || n != 1 {
		return Fail(409, "STATE_CONFLICT", "native preparation dispatch changed during settlement")
	}
	if err = c.harnessTerminalInTx(tx, f.project, task, run); err != nil {
		return err
	}
	return tx.Commit()
}
