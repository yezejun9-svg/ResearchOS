//go:build windows

package domain

import (
	"context"
	"database/sql"
	"errors"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	rt "researchos.local/research-os/adapters/runtime"
)

// recoverCheckpoints imports host-persisted checkpoint bytes as an old-epoch
// contribution. Attaching its recovery pointer does not renew execution rights.
func (c *RuntimeCoordinator) recoverCheckpoints(ctx context.Context, project, runID, directory string, epoch int64) error {
	paths, e := filepath.Glob(filepath.Join(directory, "checkpoint-*.json"))
	if e != nil || len(paths) == 0 {
		return e
	}
	tx, e := c.service.DB.BeginTx(ctx, nil)
	if e != nil {
		return e
	}
	defer tx.Rollback()
	if e = resourceWriteLock(tx); e != nil {
		return e
	}
	dispatch, e := runtimeDispatch(tx, project, runID, epoch)
	if e != nil {
		return e
	}
	var latest Object
	var latestSequence int64
	for _, path := range paths {
		actual, err := filepath.EvalSymlinks(path)
		if err != nil || !strings.EqualFold(actual, path) {
			return errors.New("host checkpoint reparse rejected")
		}
		info, err := os.Stat(path)
		if err != nil || !info.Mode().IsRegular() || info.Size() > 128*1024 {
			return errors.New("host checkpoint exceeds bound")
		}
		raw, err := os.ReadFile(path)
		if err != nil {
			return err
		}
		fact, err := Decode(raw)
		if err != nil {
			return err
		}
		sequence, err := Num(fact, "sequence")
		payload, ok := fact["payload"].(map[string]any)
		if err != nil || sequence <= 0 || !ok || filepath.Base(path) != "checkpoint-"+strconv.FormatInt(sequence, 10)+".json" || fact["project_id"] != project || fact["run_id"] != runID || Hash(fact["epoch"]) != Hash(epoch) || fact["manifest_hash"] != dispatch["manifest_hash"] || fact["dispatch_key"] != dispatch["dispatch_key"] || fact["content_hash"] != Digest(Bytes(payload)) {
			return errors.New("host checkpoint binding mismatch")
		}
		artifact, err := c.recoverArtifact(tx, project, dispatch, Bytes(payload), "CHECKPOINT")
		if err != nil {
			return err
		}
		if sequence > latestSequence {
			latestSequence, latest = sequence, artifact
		}
	}
	run, e := load(tx, project, "Run", runID)
	if e != nil {
		return e
	}
	if latest != nil && Hash(run["lease_epoch"]) == Hash(epoch) && !runTerminal(run) && run["checkpoint_artifact_id"] != latest["id"] {
		task, err := load(tx, project, "Task", Str(run, "task_id"))
		if err != nil {
			return err
		}
		if task["active_run_id"] == runID {
			run["checkpoint_artifact_id"] = latest["id"]
			if e = bump(run); e != nil {
				return e
			}
			if e = c.service.put(tx, "Run", run); e != nil {
				return e
			}
			manifest := dispatch["manifest"].(map[string]any)
			if e = c.service.event(tx, project, "Run", run, Str(manifest, "executor_principal_id"), Str(dispatch, "dispatch_key"), "RUN_CHANGED"); e != nil {
				return e
			}
		}
	}
	return tx.Commit()
}

// recoverArtifact writes an immutable historical contribution from validated
// host bytes. It neither impersonates a live lease nor exposes an HTTP bypass.
func (c *RuntimeCoordinator) recoverArtifact(tx *sql.Tx, project string, dispatch Object, raw []byte, kind string) (Object, error) {
	manifest := dispatch["manifest"].(map[string]any)
	admission := manifest["admission"].(map[string]any)
	runID, principal := Str(manifest, "run_id"), Str(manifest, "executor_principal_id")
	digest := Digest(raw)
	var prior string
	e := tx.QueryRow("SELECT a.body FROM artifact_uses u JOIN domain_objects a ON a.project=u.project AND a.kind='Artifact' AND a.id=u.artifact WHERE u.project=? AND u.run=? AND u.epoch=? AND u.principal=? AND json_extract(a.body,'$.content_hash')=? AND json_extract(a.body,'$.kind')=?", project, runID, manifest["epoch"], principal, digest, kind).Scan(&prior)
	if e == nil {
		return Decode([]byte(prior))
	}
	if e != sql.ErrNoRows {
		return nil, e
	}
	inputs := Arr(manifest, "input_refs")
	for _, v := range inputs {
		ref, ok := v.(map[string]any)
		if !ok {
			return nil, errors.New("historical input ref malformed")
		}
		a, e := version(tx, project, ref)
		if e != nil {
			return nil, e
		}
		if a["access_class"] == "VERIFIER_ONLY" {
			return nil, Fail(403, "FORBIDDEN", "historical input is protected")
		}
	}
	upload, e := c.service.upload(tx, Principal{ID: principal}, project, raw)
	if e != nil {
		return nil, e
	}
	if _, e = tx.Exec("INSERT INTO runtime_uploads(storage_key,project,run,epoch) VALUES(?,?,?,?)", upload["storage_key"], project, runID, manifest["epoch"]); e != nil {
		return nil, e
	}
	validity := "CURRENT"
	for _, v := range inputs {
		if e = c.service.effective(tx, project, v.(map[string]any)); e != nil {
			validity = "STALE"
		}
	}
	artifact := Merge(Base(project), Object{"run_id": runID, "kind": kind, "evidence_kind": "GENERATED", "measurement_mode": admission["mode"], "content_hash": digest, "storage_key": upload["storage_key"], "media_type": "application/octet-stream", "byte_size": len(raw), "input_refs": inputs, "source_refs": Empty(), "produced_by": principal, "access_class": "PROJECT", "validity": validity, "sealed_at": Now()})
	e = tx.QueryRow("SELECT body FROM domain_objects WHERE project=? AND kind='Artifact' AND json_extract(body,'$.content_hash')=? AND json_extract(body,'$.kind')=?", project, digest, kind).Scan(&prior)
	if e == nil {
		existing, e := Decode([]byte(prior))
		if e != nil {
			return nil, e
		}
		for _, field := range []string{"kind", "evidence_kind", "measurement_mode", "access_class", "media_type"} {
			if existing[field] != artifact[field] {
				return nil, Fail(409, "STATE_CONFLICT", "historical contribution cannot elevate canonical provenance")
			}
		}
		artifact = existing
	} else if e == sql.ErrNoRows {
		if e = c.service.put(tx, "Artifact", artifact); e != nil {
			return nil, e
		}
		for _, ref := range inputs {
			if _, e = c.service.impactLink(tx, project, Object{"from_ref": Ref(artifact, "Artifact"), "to_ref": ref, "relation": "DERIVED_FROM", "basis": "DETERMINISTIC", "evidence_refs": Empty()}); e != nil {
				return nil, e
			}
		}
	} else {
		return nil, e
	}
	if _, e = tx.Exec("UPDATE uploaded_content SET sealed=1 WHERE storage_key=?", upload["storage_key"]); e != nil {
		return nil, e
	}
	use := Object{"project_id": project, "artifact_ref": Ref(artifact, "Artifact"), "run_id": runID, "lease_epoch": manifest["epoch"], "principal_id": principal, "storage_key": upload["storage_key"], "content_hash": digest, "byte_size": len(raw), "input_refs": inputs, "source_refs": Empty(), "run_input_refs": inputs, "context_bundle_id": manifest["context_bundle_id"], "measurement_mode": admission["mode"], "evidence_kind": "GENERATED", "access_class": "PROJECT", "created_at": Now()}
	use["receipt_hash"] = Receipt(use)
	_, e = tx.Exec("INSERT INTO artifact_uses(project,artifact,run,epoch,principal,storage_key,receipt_hash,body) VALUES(?,?,?,?,?,?,?,?)", project, artifact["id"], runID, manifest["epoch"], principal, upload["storage_key"], use["receipt_hash"], string(Bytes(use)))
	return artifact, e
}

func (c *RuntimeCoordinator) recoverTerminal(ctx context.Context, project, runID string, epoch int64, directory string, j rt.BridgeJournal) error {
	if err := c.recoverClientQueue(ctx, project, runID, epoch, j); err != nil {
		return err
	}
	if e := c.ingestObservation(ctx, project, runID, epoch, j); e != nil {
		return e
	}
	observation, e := j.Observation()
	if e != nil {
		return e
	}
	files := []struct {
		kind string
		raw  []byte
	}{{"LOG", Bytes(observation)}}
	for _, a := range j.Artifacts {
		raw, e := os.ReadFile(filepath.Join(directory, "output", a.Path))
		if e != nil || Digest(raw) != a.Hash || int64(len(raw)) != a.Size {
			return errors.New("historical output changed after terminal validation")
		}
		files = append(files, struct {
			kind string
			raw  []byte
		}{"REPORT", raw})
	}
	tx, e := c.service.DB.BeginTx(ctx, nil)
	if e != nil {
		return e
	}
	defer tx.Rollback()
	if e = resourceWriteLock(tx); e != nil {
		return e
	}
	dispatch, e := runtimeDispatch(tx, project, runID, epoch)
	if e != nil {
		return e
	}
	ids := Empty()
	var log Object
	for _, f := range files {
		artifact, e := c.recoverArtifact(tx, project, dispatch, f.raw, f.kind)
		if e != nil {
			return e
		}
		if f.kind == "LOG" {
			log = artifact
		} else {
			ids = append(ids, artifact["id"])
		}
	}
	// These immutable contributions commit even when the current epoch or
	// authority has moved on. A separate transaction decides current completion.
	if e = tx.Commit(); e != nil {
		return e
	}
	tx, e = c.service.DB.BeginTx(ctx, nil)
	if e != nil {
		return e
	}
	defer tx.Rollback()
	if e = resourceWriteLock(tx); e != nil {
		return e
	}
	run, e := load(tx, project, "Run", runID)
	if e != nil {
		return e
	}
	if Hash(run["lease_epoch"]) != Hash(epoch) {
		return nil
	}
	if runTerminal(run) {
		// The report may have committed before a crash interrupted client projection.
		// Replaying the canonical terminal Run is idempotent and grants no new work.
		if e = c.projectSessionRun(tx, project, run, Arr(run, "result_artifact_ids")); e != nil {
			return e
		}
		return tx.Commit()
	}
	task, e := load(tx, project, "Task", Str(run, "task_id"))
	if e != nil {
		return e
	}
	if task["active_run_id"] != runID {
		return nil
	}
	if e = effectsReconciled(tx, project, runID); e != nil {
		return nil
	}
	if _, e = c.service.currentDispatchAdmission(tx, project, task, run, dispatch, "recovery-report"); e != nil {
		return nil
	}
	executor := Principal{ID: Str(run, "executor_principal_id"), Roles: []string{"EXECUTOR"}, Grants: []Grant{{ProjectID: project, TaskID: Str(run, "task_id"), RunID: runID}}}
	op := "reportRun"
	body := Object{"lease_epoch": epoch, "runtime_settled": true, "execution_report": "Recovered exact terminal host facts; no execution lease renewed.", "exit_code": j.Receipt.ExitCode, "result_artifact_ids": ids, "checkpoint_artifact_id": run["checkpoint_artifact_id"]}
	if run["status"] == "CANCEL_REQUESTED" {
		if observation["state"] != "CANCELLED" {
			return nil
		}
		op = "acknowledgeRunCancellation"
		body["receipt_artifact_ref"] = Ref(log, "Artifact")
	}
	if observation["state"] != "SETTLED" && observation["state"] != "FAILED" && op != "acknowledgeRunCancellation" {
		return nil
	}
	if _, _, _, e = c.service.runtimeOperationMode(tx, executor, project, runID, body, op, ID(), true); e != nil {
		return e
	}
	latest, e := load(tx, project, "Run", runID)
	if e != nil {
		return e
	}
	if e = c.projectSessionRun(tx, project, latest, Arr(latest, "result_artifact_ids")); e != nil {
		return e
	}
	return tx.Commit()
}

func (c *RuntimeCoordinator) recoverEffects(ctx context.Context, project, run, directory string, epoch int64) error {
	paths, e := filepath.Glob(filepath.Join(directory, "effect-*.json"))
	if e != nil {
		return e
	}
	for _, path := range paths {
		actual, e := filepath.EvalSymlinks(path)
		if e != nil || !strings.EqualFold(actual, path) {
			return errors.New("host effect receipt reparse rejected")
		}
		info, e := os.Stat(path)
		if e != nil || !info.Mode().IsRegular() || info.Size() > runtimeFactMaxBytes {
			return errors.New("host effect receipt exceeds bound")
		}
		raw, e := os.ReadFile(path)
		if e != nil {
			return e
		}
		fact, e := Decode(raw)
		if e != nil {
			return e
		}
		if fact["project_id"] != project || fact["run_id"] != run || Hash(fact["epoch"]) != Hash(epoch) {
			return errors.New("host effect receipt scope mismatch")
		}
		if e = c.ingestEffectFact(ctx, fact); e != nil {
			return e
		}
	}
	tx, e := c.service.DB.BeginTx(ctx, nil)
	if e != nil {
		return e
	}
	defer tx.Rollback()
	if e = resourceWriteLock(tx); e != nil {
		return e
	}
	rows, e := tx.Query("SELECT body FROM resource_effects x WHERE project=? AND run=? AND sequence=(SELECT max(sequence) FROM resource_effects y WHERE y.project=x.project AND y.run=x.run AND y.effect_key=x.effect_key) AND json_extract(body,'$.state')='STARTED' AND json_extract(body,'$.epoch')=?", project, run, epoch)
	if e != nil {
		return e
	}
	pending := []Object{}
	for rows.Next() {
		var raw string
		if e = rows.Scan(&raw); e != nil {
			rows.Close()
			return e
		}
		effect, e := Decode([]byte(raw))
		if e != nil {
			rows.Close()
			return e
		}
		pending = append(pending, effect)
	}
	e = rows.Err()
	rows.Close()
	if e != nil {
		return e
	}
	for _, effect := range pending {
		effect["state"] = "UNKNOWN"
		effect["receipt"] = Object{"reason": "control restarted without trusted provider receipt", "epoch": epoch, "at": time.Now().UTC().Format(time.RFC3339Nano)}
		if e = effectAppend(tx, project, run, Str(effect, "key"), effect); e != nil {
			return e
		}
	}
	return tx.Commit()
}

// recoverHarness consumes only Host-ingested observations and sealed original
// ArtifactUse rows. An untrusted CLI disk receipt cannot authorize recovery.
func (c *RuntimeCoordinator) recoverHarness(ctx context.Context, project, runID string, epoch int64) (bool, error) {
	tx, err := c.service.DB.BeginTx(ctx, nil)
	if err != nil {
		return false, err
	}
	dispatch, err := runtimeDispatch(tx, project, runID, epoch)
	if err != nil {
		tx.Rollback()
		return false, err
	}
	admission := dispatch["manifest"].(map[string]any)["admission"].(map[string]any)
	if admission["admission_kind"] != "HOST_HARNESS_V1" {
		tx.Rollback()
		return false, nil
	}
	run, err := load(tx, project, "Run", runID)
	if err != nil {
		tx.Rollback()
		return true, err
	}
	_, observationErr := runtimeObservation(tx, project, run)
	terminal := runTerminal(run)
	tx.Rollback()
	if terminal || observationErr == nil {
		return true, c.finishHarness(ctx, project, runID, epoch)
	}
	return true, c.harnessUnknown(ctx, project, runID, epoch, "native terminal observation absent after restart; no relaunch")
}
