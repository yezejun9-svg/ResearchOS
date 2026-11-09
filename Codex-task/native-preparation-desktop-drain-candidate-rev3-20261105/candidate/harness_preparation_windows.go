//go:build windows

package domain

import (
	"bytes"
	"context"
	"database/sql"
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

// A Desktop exit may leave the consumed STARTED dispatch on disk only when the
// original private C5 settlement is still fully represented by durable facts.
// Uploaded LOG bytes or a terminal Task alone are never an eligibility source.
func (s *Service) stoppedHarnessPreparationInTx(tx *sql.Tx, project, runID string, epoch int64, dataRoot string) error {
	bad := func() error { return errors.New("desktop exit requires original stopped native preparation proof") }
	dispatch, err := runtimeDispatch(tx, project, runID, epoch)
	if err != nil {
		return err
	}
	identity, ok := dispatch["identity"].(map[string]any)
	sequence, seqErr := Num(dispatch, "observation_sequence")
	manifest, okManifest := dispatch["manifest"].(map[string]any)
	if !ok || !okManifest || seqErr != nil || dispatch["state"] != "STARTED" ||
		Str(dispatch, "worker") == "" || dispatch["journal_locator"] != dispatch["dispatch_key"] ||
		sequence != 0 || dispatch["observation_hash"] != "" || len(identity) != 0 {
		return bad()
	}
	if err = harnessPreparationMarkerAbsent(dataRoot, Str(dispatch, "journal_locator")); err != nil {
		return err
	}
	run, err := load(tx, project, "Run", runID)
	if err != nil {
		return err
	}
	taskID := Str(run, "task_id")
	if taskID == "" || run["status"] != "FAILED" || run["external_run_id"] != nil ||
		run["exit_code"] != nil || len(Arr(run, "result_artifact_ids")) != 0 ||
		run["children_stopped"] != true || run["queue_empty"] != true ||
		Str(run, "ended_at") == "" || Str(run, "runtime_settled_at") == "" ||
		run["execution_report"] != "Native preparation failed before model launch; no automatic replay." ||
		Hash(run["lease_epoch"]) != Hash(epoch) {
		return bad()
	}
	task, err := load(tx, project, "Task", taskID)
	if err != nil {
		return err
	}
	if task["task_type"] != "harness_turn" || task["active_run_id"] != runID ||
		(task["status"] != "FAILED" && task["status"] != "DEFERRED_NO_PROGRESS") {
		return bad()
	}
	record, err := harnessTaskInput(tx, project, task)
	if err != nil {
		return err
	}
	source, sourceOK := record["source_binding"].(map[string]any)
	admission, admissionOK := manifest["admission"].(map[string]any)
	if !sourceOK || !admissionOK {
		return bad()
	}
	profile, profileOK := admission["profile"].(map[string]any)
	ref, refOK := admission["profile_ref"].(map[string]any)
	contract, contractOK := task["acceptance_contract"].(map[string]any)
	if !profileOK || !refOK || !contractOK || admission["admission_kind"] != "HOST_HARNESS_V1" ||
		manifest["task_id"] != taskID || manifest["runtime_id"] != run["runtime_id"] ||
		manifest["executor_principal_id"] != run["executor_principal_id"] ||
		manifest["context_bundle_id"] != run["context_bundle_id"] ||
		manifest["checkpoint_artifact_id"] != run["checkpoint_artifact_id"] ||
		manifest["contract_hash"] != contract["contract_hash"] ||
		Hash(manifest["input_refs"]) != Hash(run["input_refs"]) ||
		Hash(record["profile_ref"]) != Hash(ref) || admission["profile_hash"] != Hash(ref) ||
		record["runtime_id"] != run["runtime_id"] || record["principal_id"] != profile["harness_owner"] ||
		source["principal_id"] != record["principal_id"] || source["project_id"] != project ||
		!preparedAbandonmentDigest(Str(source, "canonical_path_sha256")) ||
		profile["native_transport"] != rt.CodexRPCTransport ||
		validateRuntimeDispatchProfile(profile) != nil {
		return bad()
	}
	artifact, err := version(tx, project, ref)
	if err != nil {
		return err
	}
	frozen, err := runtimeProfileBody(tx, project, artifact)
	if err != nil || Hash(frozen) != Hash(profile) {
		return bad()
	}
	if err = clientQueueSettled(tx, project, runID); err != nil {
		return err
	}
	var observations, effects, uploads int
	if err = tx.QueryRow("SELECT count(*) FROM runtime_observations WHERE project=? AND run=?", project, runID).Scan(&observations); err != nil {
		return err
	}
	if err = tx.QueryRow("SELECT count(*) FROM resource_effects WHERE project=? AND run=?", project, runID).Scan(&effects); err != nil {
		return err
	}
	if err = tx.QueryRow("SELECT count(*) FROM runtime_uploads WHERE project=? AND run=?", project, runID).Scan(&uploads); err != nil {
		return err
	}
	if observations != 0 || effects != 0 || uploads != 0 {
		return bad()
	}
	// The reason is written by C5 in the same transaction as the sealed audit.
	// It is the internal anchor; matching-looking uploaded bytes cannot mint it.
	const prefix = "native preparation failed before model launch: "
	reason := Str(dispatch, "reason")
	if !strings.HasPrefix(reason, prefix) {
		return bad()
	}
	rows, err := tx.Query(`SELECT u.bytes,u.content_hash,u.principal,u.sealed,a.body
		FROM uploaded_content u LEFT JOIN domain_objects a
		ON a.project=u.project AND a.kind='Artifact' AND json_extract(a.body,'$.storage_key')=u.storage_key
		WHERE u.project=? AND instr(CAST(u.bytes AS TEXT),'researchos.native-preparation-outcome.v1')>0`, project)
	if err != nil {
		return err
	}
	defer rows.Close()
	matched := 0
	for rows.Next() {
		var raw []byte
		var contentHash, principal string
		var sealed int
		var artifactRaw sql.NullString
		if err = rows.Scan(&raw, &contentHash, &principal, &sealed, &artifactRaw); err != nil {
			return err
		}
		if !bytes.Contains(raw, []byte(`"researchos.native-preparation-outcome.v1"`)) {
			continue
		}
		audit, decodeErr := Decode(raw)
		if decodeErr != nil || audit["schema"] != "researchos.native-preparation-outcome.v1" ||
			reason != prefix+Str(audit, "reason")+"; proof="+Hash(audit) {
			continue
		}
		matched++
		if matched != 1 || sealed != 1 || !artifactRaw.Valid || contentHash != Digest(raw) || !bytes.Equal(raw, Bytes(audit)) ||
			principal != record["principal_id"] || !harnessPreparationAuditMatches(audit, project, taskID, runID, epoch, dispatch, record, profile) {
			return bad()
		}
		stored, decodeErr := Decode([]byte(artifactRaw.String))
		size, sizeErr := Num(stored, "byte_size")
		if decodeErr != nil || sizeErr != nil || stored["kind"] != "LOG" || stored["measurement_mode"] != "LIVE" ||
			stored["evidence_kind"] != "OBSERVED" || stored["content_hash"] != contentHash ||
			stored["produced_by"] != principal || stored["validity"] != "CURRENT" ||
			Str(stored, "sealed_at") == "" || size != int64(len(raw)) {
			return bad()
		}
	}
	if err = rows.Err(); err != nil {
		return err
	}
	if matched != 1 {
		return bad()
	}
	return nil
}

func harnessPreparationAuditMatches(audit Object, project, taskID, runID string, epoch int64, dispatch, record, profile Object) bool {
	// Exact C5 shape excludes injected outcome fields, including model results.
	if len(audit) != 23 || audit["phase"] != "PREPARATION_FAILED" ||
		!harnessKnownPreparationReason(Str(audit, "reason")) ||
		audit["project_id"] != project || audit["task_id"] != taskID || audit["run_id"] != runID ||
		audit["epoch"] != strconv.FormatInt(epoch, 10) || audit["dispatch_key"] != dispatch["dispatch_key"] ||
		audit["manifest_hash"] != dispatch["manifest_hash"] || audit["worker"] != dispatch["worker"] ||
		audit["source_binding_hash"] != Hash(record["source_binding"]) ||
		audit["synthetic_source_path_sha256"] != record["source_binding"].(map[string]any)["canonical_path_sha256"] ||
		audit["expected_native_sha256"] != profile["build_hash"] ||
		audit["requested_template_sha256"] != profile["requested_config_sha256"] ||
		!preparedAbandonmentDigest(Str(audit, "expected_helper_sha256")) ||
		Str(audit, "host_boot") == "" || len(Str(audit, "host_boot")) > 128 ||
		audit["model_start_delegated"] != false {
		return false
	}
	pathHash := audit["qualification_receipt_path_sha256"]
	if pathHash != nil && !preparedAbandonmentDigest(Str(audit, "qualification_receipt_path_sha256")) {
		return false
	}
	pid, err := Num(audit, "qualification_pid")
	if err != nil || pid < 0 || pid > 1<<32-1 {
		return false
	}
	noChild, ok := audit["qualification_no_child"].(bool)
	if !ok {
		return false
	}
	jobZero, jobOK := audit["qualification_job_zero"].(bool)
	streams, streamsOK := audit["streams_drained"].(bool)
	cleanup, cleanupOK := audit["cleanup_complete"].(bool)
	return jobOK && streamsOK && cleanupOK && (noChild && pid == 0 || !noChild && pid > 0 && jobZero && streams && cleanup)
}

// C5 alone may settle the Host's zero local launch hold. This is called only
// after its private stopped proof and original dispatch fence are accepted,
// in the same transaction as the audit and terminal projection.
func (s *Service) releaseStoppedHarnessLocalLaunch(tx *sql.Tx, project string, run, task Object, epoch int64, alreadySettled bool) error {
	bad := func() error { return errors.New("native preparation local launch hold is missing or conflicted") }
	runID := Str(run, "id")
	request := "runtime-local-launch/" + runID + "/" + strconv.FormatInt(epoch, 10)
	goal, err := load(tx, project, "Goal", Str(task, "goal_id"))
	if err != nil {
		return err
	}
	scopes, leaves, err := runBudgetScopes(tx, project, runID)
	if err != nil {
		return err
	}
	policy := Str(goal, "budget_policy_id")
	if policy == "" || !leaves[policy] {
		return bad()
	}
	currency := "USD"
	for _, p := range scopes {
		if p["cap"] != nil {
			cap, ok := p["cap"].(map[string]any)
			if !ok {
				return bad()
			}
			currency = Str(cap, "currency")
			break
		}
	}
	rows, err := tx.Query(`SELECT id,body FROM domain_objects WHERE project=? AND kind='BudgetLedgerEntry' AND json_extract(body,'$.provider_request_id')=? ORDER BY rowid`, project, request)
	if err != nil {
		return err
	}
	history := []Object{}
	for rows.Next() {
		var id, raw string
		if err = rows.Scan(&id, &raw); err != nil {
			rows.Close()
			return err
		}
		item, decodeErr := Decode([]byte(raw))
		if decodeErr != nil {
			rows.Close()
			return decodeErr
		}
		if id == "" || item["id"] != id || item["receipt_hash"] != Receipt(item) {
			rows.Close()
			return bad()
		}
		history = append(history, item)
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return err
	}
	if len(history) < 1 || len(history) > 2 {
		return bad()
	}
	hold := history[0]
	money, ok := hold["money"].(map[string]any)
	if !ok {
		return bad()
	}
	amount, err := moneyAmount(money)
	if err != nil || amount.Sign() != 0 || currency == "" || money["currency"] != currency ||
		hold["operation"] != "RESERVE" || hold["project_id"] != project || hold["run_id"] != runID ||
		hold["provider_request_id"] != request || hold["provider_event_id"] != request ||
		hold["reservation_id"] != nil || hold["cost_basis"] != "UPPER_BOUND" || hold["policy_id"] != policy || Str(hold, "occurred_at") == "" {
		return bad()
	}
	if len(history) == 2 {
		release := history[1]
		closedMoney, ok := release["money"].(map[string]any)
		if !ok {
			return bad()
		}
		closedAmount, moneyErr := moneyAmount(closedMoney)
		if moneyErr != nil || closedAmount.Sign() != 0 || Hash(closedMoney) != Hash(money) ||
			release["operation"] != "RELEASE" || release["project_id"] != project || release["run_id"] != runID ||
			release["provider_request_id"] != request || release["provider_event_id"] != request+"/released" ||
			release["reservation_id"] != hold["id"] || release["cost_basis"] != "ACTUAL" || release["policy_id"] != policy || Str(release, "occurred_at") == "" {
			return bad()
		}
		return nil
	}
	if alreadySettled {
		return bad()
	}
	var reusedEvent int
	if err = tx.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='BudgetLedgerEntry' AND json_extract(body,'$.provider_event_id')=?", project, request+"/released").Scan(&reusedEvent); err != nil {
		return err
	}
	if reusedEvent != 0 {
		return bad()
	}
	_, err = s.appendBudget(tx, project, Object{"policy_id": policy, "run_id": runID, "operation": "RELEASE",
		"money": money, "provider_request_id": request, "provider_event_id": request + "/released",
		"reservation_id": hold["id"], "cost_basis": "ACTUAL", "occurred_at": Now()})
	return err
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
		if err = c.service.releaseStoppedHarnessLocalLaunch(tx, f.project, run, task, f.epoch, true); err != nil {
			return err
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
	if err = c.service.releaseStoppedHarnessLocalLaunch(tx, f.project, run, task, f.epoch, false); err != nil {
		return err
	}
	if err = c.harnessTerminalInTx(tx, f.project, task, run); err != nil {
		return err
	}
	return tx.Commit()
}
