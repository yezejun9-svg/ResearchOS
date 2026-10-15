package domain

import (
	"database/sql"
	"encoding/json"
	"strings"
)

const runtimePauseProtocol = "RESEARCHOS_PAUSE_V1"

// The ordinary Task state graph remains unchanged. This exception belongs only
// to the transaction that just created the same Run's exact paused successor.
func (s *Service) pauseTaskTransition(tx *sql.Tx, old, next Object) (bool, error) {
	if old["status"] != "BLOCKED" || next["status"] != "RUNNING" || old["task_type"] != "mu_turn" || next["task_type"] != old["task_type"] || old["project_id"] != next["project_id"] || old["id"] != next["id"] || Str(old, "active_run_id") == "" || next["active_run_id"] != old["active_run_id"] {
		return false, nil
	}
	installed, err := pauseInstalled(tx)
	if err != nil || !installed {
		return false, err
	}
	project := Str(old, "project_id")
	run, err := load(tx, project, "Run", Str(old, "active_run_id"))
	if err != nil {
		return false, err
	}
	if run["status"] != "QUEUED" || run["task_id"] != old["id"] || run["cancel_requested_at"] != nil {
		return false, nil
	}
	goal, err := load(tx, project, "Goal", Str(old, "goal_id"))
	if err != nil {
		return false, err
	}
	if goal["status"] != "ACTIVE" {
		return false, nil
	}
	rows, err := configurationBackupRows(tx, `SELECT * FROM runtime_checkpoint_activations WHERE project=? AND run=? AND epoch=?`, project, run["id"], run["lease_epoch"])
	if err != nil || len(rows) != 1 {
		return false, err
	}
	a := rows[0]
	intent, err := pauseIntent(tx, project, Str(run, "id"), a["previous_epoch"])
	if err != nil {
		return false, err
	}
	previous, _ := Num(a, "previous_epoch")
	epoch, _ := Num(a, "epoch")
	if intent == nil || intent["state"] != "RESUME_PREPARED" || epoch != previous+1 || Hash(intent["successor_epoch"]) != Hash(epoch) || a["task"] != old["id"] || intent["task"] != old["id"] || a["pause_id"] != intent["pause_id"] || a["generation"] != intent["generation"] || a["session_id"] != intent["session_id"] {
		return false, nil
	}
	var raw, hash string
	if err = tx.QueryRow(`SELECT body,body_hash FROM runtime_pause_receipts WHERE project=? AND pause_id=? AND kind='STATE_TRANSITION' ORDER BY sequence DESC LIMIT 1`, project, intent["pause_id"]).Scan(&raw, &hash); err != nil {
		return false, err
	}
	witness, err := Decode([]byte(raw))
	if err != nil || Hash(witness) != hash || witness["intent_hash"] != Hash(intent) || witness["state"] != "RESUME_PREPARED" || Hash(witness["revision"]) != Hash(intent["revision"]) {
		return false, nil
	}
	if _, err = freshPauseActor(tx, Str(a, "principal"), project, Str(old, "id"), Str(run, "id")); err != nil {
		return false, err
	}
	d, err := runtimeDispatch(tx, project, Str(run, "id"), epoch)
	if err != nil {
		return false, err
	}
	manifest, _ := d["manifest"].(map[string]any)
	admission, _ := manifest["admission"].(map[string]any)
	marker, _ := admission["sealed_pause_activation"].(map[string]any)
	if d["state"] != "PREPARED" || d["worker"] != "" || d["journal_locator"] != "" || Hash(d["identity"]) != Hash(Object{}) || d["dispatch_key"] != a["dispatch_key"] || d["manifest_hash"] != a["manifest_hash"] || marker["pause_id"] != a["pause_id"] || Hash(marker["previous_epoch"]) != Hash(previous) || marker["checkpoint_hash"] != a["checkpoint_hash"] {
		return false, nil
	}
	if err = tx.QueryRow(`SELECT body,body_hash FROM runtime_pause_receipts WHERE project=? AND pause_id=? AND kind='RESUME_CONSUMED' ORDER BY sequence DESC LIMIT 1`, project, intent["pause_id"]).Scan(&raw, &hash); err != nil {
		return false, err
	}
	consumed, err := Decode([]byte(raw))
	if err != nil || Hash(consumed) != hash || consumed["request_key"] != a["request_key"] || Hash(consumed["epoch"]) != Hash(epoch) || consumed["dispatch_key"] != d["dispatch_key"] {
		return false, nil
	}
	var count int
	if err = tx.QueryRow(`SELECT count(*) FROM client_queue_fences WHERE project=? AND task_id=? AND run_id=? AND generation=? AND session_id=? AND runtime_epoch=? AND dispatch_key=? AND manifest_hash=? AND state='OPEN' AND restore_fenced=0`, project, old["id"], run["id"], a["generation"], a["session_id"], epoch, a["dispatch_key"], a["manifest_hash"]).Scan(&count); err != nil || count != 1 {
		return false, err
	}
	_, use, err := s.artifactUse(tx, project, run, Str(a, "checkpoint_artifact"), false)
	if err != nil {
		return false, err
	}
	if use["receipt_hash"] != a["carry_use_receipt_hash"] || use["principal_id"] != a["carry_use_principal"] || a["checkpoint_hash"] != intent["checkpoint_hash"] || a["checkpoint_use_receipt_hash"] != intent["checkpoint_use_receipt_hash"] || a["checkpoint_use_principal"] != intent["checkpoint_use_principal"] {
		return false, nil
	}
	if err = tx.QueryRow(`SELECT body FROM resource_checkpoint_carries WHERE project=? AND run=? AND epoch=?`, project, run["id"], epoch).Scan(&raw); err != nil {
		return false, err
	}
	carry, err := Decode([]byte(raw))
	if err != nil {
		return false, err
	}
	ref, _ := carry["artifact_ref"].(map[string]any)
	return carry["actor"] == a["principal"] && carry["from_use_receipt_hash"] == a["checkpoint_use_receipt_hash"] && Hash(carry["from_epoch"]) == Hash(previous) && Hash(carry["to_epoch"]) == Hash(epoch) && carry["new_upload_key"] == use["storage_key"] && ref["id"] == a["checkpoint_artifact"] && ref["content_hash"] == a["checkpoint_hash"], nil
}

// Only the authenticated HTTP mutation supplies this metadata. Internal task
// drivers cannot manufacture native pause authority from a correlation ID.
type taskRequestMeta struct{ Key, Hash string }

func pauseInstalled(tx *sql.Tx) (bool, error) {
	var n int
	err := tx.QueryRow(`SELECT count(*) FROM sqlite_master WHERE type='table' AND name='runtime_pause_intents'`).Scan(&n)
	return n == 1, err
}

func pauseIntent(tx *sql.Tx, project, run string, epoch any) (Object, error) {
	ok, err := pauseInstalled(tx)
	if err != nil {
		return nil, err
	}
	if !ok {
		return nil, nil
	}
	rows, err := configurationBackupRows(tx, `SELECT * FROM runtime_pause_intents WHERE project=? AND run=? AND epoch=?`, project, run, epoch)
	if err != nil || len(rows) == 0 {
		return nil, err
	}
	return rows[0], nil
}

func appendPauseReceipt(tx *sql.Tx, intent Object, kind string, detail Object) error {
	var seq int64
	var previous any
	var hash string
	err := tx.QueryRow(`SELECT sequence,body_hash FROM runtime_pause_receipts WHERE project=? AND pause_id=? ORDER BY sequence DESC LIMIT 1`, intent["project"], intent["pause_id"]).Scan(&seq, &hash)
	if err != nil && err != sql.ErrNoRows {
		return err
	}
	if err == nil {
		previous = hash
	}
	body := Merge(Object{}, detail)
	body["project"], body["pause_id"], body["kind"], body["sequence"] = intent["project"], intent["pause_id"], kind, seq+1
	_, err = tx.Exec(`INSERT INTO runtime_pause_receipts(receipt_id,project,pause_id,sequence,kind,body,body_hash,previous_receipt_hash,created_at) VALUES(?,?,?,?,?,?,?,?,?)`, ID(), intent["project"], intent["pause_id"], seq+1, kind, string(Bytes(body)), Hash(body), previous, Now())
	return err
}

func pauseWitness(tx *sql.Tx, intent Object) error {
	return appendPauseReceipt(tx, intent, "STATE_TRANSITION", Object{"state": intent["state"], "revision": intent["revision"], "intent_hash": Hash(intent)})
}

func pauseCAS(tx *sql.Tx, intent Object, next string, fields Object) (Object, error) {
	// Fixed allowed columns prevent caller-controlled SQL identifiers.
	allowed := map[string]bool{}
	for _, k := range []string{"checkpoint_sequence", "checkpoint_artifact", "checkpoint_use_receipt_hash", "checkpoint_use_principal", "checkpoint_hash", "checkpoint_bytes", "native_session_ref", "sdk_session_id", "queue_cut", "command_ledger_hash", "sdk_watermarks_json", "model_calls", "tool_calls", "journal_checkpoint_hash", "successor_epoch"} {
		allowed[k] = true
	}
	query := `UPDATE runtime_pause_intents SET state=?,revision=revision+1,updated_at=?`
	args := []any{next, Now()}
	for k, v := range fields {
		if !allowed[k] {
			return nil, Fail(400, "INVALID_REQUEST", "unknown pause projection column")
		}
		query += "," + k + "=?"
		args = append(args, v)
	}
	query += ` WHERE project=? AND pause_id=? AND state=? AND revision=?`
	args = append(args, intent["project"], intent["pause_id"], intent["state"], intent["revision"])
	r, err := tx.Exec(query, args...)
	if err != nil {
		return nil, err
	}
	n, err := r.RowsAffected()
	if err != nil {
		return nil, err
	}
	if n != 1 {
		return nil, Fail(409, "STATE_CONFLICT", "pause revision changed")
	}
	fresh, err := pauseIntent(tx, Str(intent, "project"), Str(intent, "run"), intent["epoch"])
	if err != nil {
		return nil, err
	}
	return fresh, pauseWitness(tx, fresh)
}

func freshPauseActor(tx *sql.Tx, actor, project, task, run string) (Principal, error) {
	p := Principal{ID: actor}
	var roles string
	if err := tx.QueryRow(`SELECT roles,can_create_project FROM auth_principals WHERE id=? AND revoked=0`, actor).Scan(&roles, &p.CanCreateProject); err != nil {
		return p, Fail(403, "FORBIDDEN", "pause actor revoked")
	}
	if err := json.Unmarshal([]byte(roles), &p.Roles); err != nil {
		return p, err
	}
	rows, err := tx.Query(`SELECT project,task,run,restricted FROM auth_grants WHERE principal=?`, actor)
	if err != nil {
		return p, err
	}
	for rows.Next() {
		var g Grant
		if err = rows.Scan(&g.ProjectID, &g.TaskID, &g.RunID, &g.Restricted); err != nil {
			rows.Close()
			return p, err
		}
		p.Grants = append(p.Grants, g)
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return p, err
	}
	if err = constrainRemotePrincipal(tx, &p); err != nil {
		return p, err
	}
	if !p.HasRole("OWNER") || !p.Allowed(project, task, run, false) {
		return p, Fail(403, "FORBIDDEN", "current Owner task authority required")
	}
	return p, nil
}

func (s *Service) requestRuntimePause(tx *sql.Tx, p Principal, project string, task Object, body Object, meta []taskRequestMeta) (Object, bool, error) {
	if task["task_type"] != "mu_turn" || Str(task, "active_run_id") == "" {
		return nil, false, nil
	}
	run, err := load(tx, project, "Run", Str(task, "active_run_id"))
	if err != nil {
		return nil, true, err
	}
	if runTerminal(run) {
		return nil, false, nil
	}
	if len(meta) != 1 || meta[0].Key == "" || meta[0].Hash == "" {
		return nil, true, Fail(403, "FORBIDDEN", "authenticated pause request metadata required")
	}
	if _, err = freshPauseActor(tx, p.ID, project, Str(task, "id"), Str(run, "id")); err != nil {
		return nil, true, err
	}
	ok, err := pauseInstalled(tx)
	if err != nil {
		return nil, true, err
	}
	if !ok {
		return nil, true, Fail(503, "RESOURCE_UNAVAILABLE", "pause storage unavailable")
	}
	if run["status"] != "RUNNING" || task["status"] != "RUNNING" {
		return nil, true, Fail(409, "STATE_CONFLICT", "active running Mu required")
	}
	d, err := runtimeDispatch(tx, project, Str(run, "id"), run["lease_epoch"])
	if err != nil {
		return nil, true, err
	}
	var session, generation, state, dk, mh, identity string
	var epoch, fenced int64
	err = tx.QueryRow(`SELECT session_id,generation,state,runtime_epoch,dispatch_key,manifest_hash,process_identity,restore_fenced FROM client_queue_fences WHERE project=? AND task_id=? AND run_id=?`, project, task["id"], run["id"]).Scan(&session, &generation, &state, &epoch, &dk, &mh, &identity, &fenced)
	if err != nil {
		return nil, true, err
	}
	id, err := Decode([]byte(identity))
	if err != nil {
		return nil, true, err
	}
	if state != "OPEN" || fenced != 0 || Hash(epoch) != Hash(run["lease_epoch"]) || dk != d["dispatch_key"] || mh != d["manifest_hash"] || len(id) == 0 || Hash(id) != Hash(d["identity"]) {
		return nil, true, Fail(409, "STATE_CONFLICT", "pause queue identity is not active")
	}
	var raw, hash string
	err = tx.QueryRow(`SELECT body,body_hash FROM client_control_receipts WHERE generation=? AND receipt_id=? AND kind='HOST_PAUSE_CAPABILITY'`, generation, dk+":pause-capability").Scan(&raw, &hash)
	if err != nil {
		return nil, true, Fail(409, "STATE_CONFLICT", "worker pause capability not acknowledged")
	}
	cap, err := Decode([]byte(raw))
	if err != nil {
		return nil, true, err
	}
	if Hash(cap) != hash || cap["pause_protocol"] != runtimePauseProtocol || cap["dispatch_key"] != dk || cap["manifest_hash"] != mh || Hash(cap["process_identity"]) != Hash(id) || Hash(cap["runtime_epoch"]) != Hash(epoch) {
		return nil, true, Fail(409, "GATE_FAILED", "pause capability binding mismatch")
	}
	input := strings.TrimPrefix(Str(cap, "original_input_hash"), "sha256:")
	if len(input) != 64 {
		return nil, true, Fail(409, "GATE_FAILED", "original input hash missing")
	}
	pause := ID()
	now := Now()
	_, err = tx.Exec(`INSERT INTO runtime_pause_intents(project,pause_id,task,run,epoch,session_id,generation,principal,request_key,request_hash,runtime,dispatch_key,manifest_hash,process_identity_hash,original_input_hash,state,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'PAUSE_REQUESTED',?,?)`, project, pause, task["id"], run["id"], epoch, session, generation, p.ID, meta[0].Key, meta[0].Hash, run["runtime_id"], dk, mh, Hash(id), input, now, now)
	if err != nil {
		return nil, true, err
	}
	intent, err := pauseIntent(tx, project, Str(run, "id"), epoch)
	if err != nil {
		return nil, true, err
	}
	if err = pauseWitness(tx, intent); err != nil {
		return nil, true, err
	}
	if err = recordPauseEffectCutoff(tx, intent); err != nil {
		return nil, true, err
	}
	_, err = tx.Exec(`INSERT INTO orchestration_task_controls(project,task,action,reason,requested_at) VALUES(?,?,'PAUSE',?,?) ON CONFLICT(project,task) DO UPDATE SET action='PAUSE',reason=excluded.reason,requested_at=excluded.requested_at WHERE orchestration_task_controls.action<>'CANCEL'`, project, task["id"], body["reason"], now)
	if err != nil {
		return nil, true, err
	}
	task["status"] = "BLOCKED"
	if err = bump(task); err != nil {
		return nil, true, err
	}
	return task, true, s.put(tx, "Task", task)
}

func (s *Service) requestRuntimeResume(tx *sql.Tx, p Principal, project string, task Object, meta []taskRequestMeta) (Object, bool, error) {
	if Str(task, "active_run_id") == "" {
		return nil, false, nil
	}
	run, err := load(tx, project, "Run", Str(task, "active_run_id"))
	if err != nil {
		return nil, true, err
	}
	intent, err := pauseIntent(tx, project, Str(run, "id"), run["lease_epoch"])
	if err != nil {
		return nil, true, err
	}
	if intent == nil {
		return nil, false, nil
	}
	if intent["state"] != "PAUSED_CONFIRMED" || task["status"] != "BLOCKED" {
		return nil, true, Fail(409, "STATE_CONFLICT", "confirmed pause required")
	}
	if len(meta) != 1 || meta[0].Key == "" || meta[0].Hash == "" {
		return nil, true, Fail(403, "FORBIDDEN", "authenticated resume request metadata required")
	}
	if _, err = freshPauseActor(tx, p.ID, project, Str(task, "id"), Str(run, "id")); err != nil {
		return nil, true, err
	}
	var count int
	if err = tx.QueryRow(`SELECT count(*) FROM runtime_pause_receipts r WHERE project=? AND pause_id=? AND kind='RESUME_REQUESTED' AND NOT EXISTS(SELECT 1 FROM runtime_pause_receipts f WHERE f.project=r.project AND f.pause_id=r.pause_id AND f.kind='RESUME_REJECTED' AND json_extract(f.body,'$.request_key')=json_extract(r.body,'$.request_key'))`, project, intent["pause_id"]).Scan(&count); err != nil {
		return nil, true, err
	}
	if count != 0 {
		return nil, true, Fail(409, "STATE_CONFLICT", "resume request already recorded")
	}
	err = appendPauseReceipt(tx, intent, "RESUME_REQUESTED", Object{"principal": p.ID, "request_key": meta[0].Key, "request_hash": meta[0].Hash, "pause_revision": intent["revision"], "checkpoint_hash": intent["checkpoint_hash"], "task_revision": task["revision"]})
	return task, true, err
}

func cancelTaskPauses(tx *sql.Tx, project, task string) error {
	ok, err := pauseInstalled(tx)
	if err != nil || !ok {
		return err
	}
	rows, err := configurationBackupRows(tx, `SELECT * FROM runtime_pause_intents WHERE project=? AND task=? AND state NOT IN ('CANCELLED','RESUMED')`, project, task)
	if err != nil {
		return err
	}
	for _, intent := range rows {
		if _, err = pauseCAS(tx, intent, "CANCELLED", nil); err != nil {
			return err
		}
	}
	return nil
}

func pauseOperationGate(tx *sql.Tx, project string, run Object, operation string) error {
	intent, err := pauseIntent(tx, project, Str(run, "id"), run["lease_epoch"])
	if err != nil || intent == nil {
		return err
	}
	switch intent["state"] {
	case "PAUSE_REQUESTED", "CHECKPOINT_SEALED":
		if operation == "heartbeat" || operation == "upload" || operation == "seal" {
			return nil
		}
	case "RESUMED":
		return nil
	}
	return Fail(409, "STATE_CONFLICT", "paused execution authority is fenced")
}

func pauseEffectAdmission(tx *sql.Tx, project, run, key string, epoch any) error {
	intent, err := pauseIntent(tx, project, run, epoch)
	if err != nil || intent == nil || intent["state"] == "RESUMED" {
		return err
	}
	if intent["state"] == "PAUSE_REQUESTED" {
		prior, e := latestEffect(tx, project, run, key)
		if e == nil && Hash(prior["epoch"]) == Hash(epoch) {
			admitted, cutoffErr := pauseEffectInCutoff(tx, intent, prior, false)
			if cutoffErr != nil {
				return cutoffErr
			}
			if admitted {
				return nil
			}
		}
		if e != nil && e != sql.ErrNoRows {
			return e
		}
	}
	return Fail(409, "STATE_CONFLICT", "pause cutoff prohibits new effect admission")
}

func recordPauseEffectCutoff(tx *sql.Tx, intent Object) error {
	rows, err := configurationBackupRows(tx, `SELECT body FROM resource_effects x WHERE project=? AND run=? AND sequence=(SELECT max(y.sequence) FROM resource_effects y WHERE y.project=x.project AND y.run=x.run AND y.effect_key=x.effect_key) ORDER BY effect_key`, intent["project"], intent["run"])
	if err != nil {
		return err
	}
	entries := Empty()
	for _, row := range rows {
		effect, err := Decode([]byte(Str(row, "body")))
		if err != nil {
			return err
		}
		if Hash(effect["epoch"]) == Hash(intent["epoch"]) {
			entries = append(entries, Object{"key": effect["key"], "sequence": effect["sequence"], "request_hash": effect["request_hash"], "state": effect["state"], "epoch": effect["epoch"]})
		}
	}
	return appendPauseReceipt(tx, intent, "EFFECT_CUTOFF", Object{"effects": entries})
}

func pauseEffectInCutoff(tx *sql.Tx, intent, effect Object, prepared bool) (bool, error) {
	var raw, hash string
	err := tx.QueryRow(`SELECT body,body_hash FROM runtime_pause_receipts WHERE project=? AND pause_id=? AND kind='EFFECT_CUTOFF'`, intent["project"], intent["pause_id"]).Scan(&raw, &hash)
	if err != nil {
		return false, err
	}
	cut, err := Decode([]byte(raw))
	if err != nil || Hash(cut) != hash {
		return false, Fail(409, "GATE_FAILED", "pause effect cutoff proof changed")
	}
	for _, v := range Arr(cut, "effects") {
		e, ok := v.(map[string]any)
		if !ok {
			return false, Fail(409, "GATE_FAILED", "pause effect cutoff malformed")
		}
		if e["key"] == effect["key"] && e["request_hash"] == effect["request_hash"] && Hash(e["epoch"]) == Hash(effect["epoch"]) {
			if !prepared {
				return true, nil
			}
			return e["state"] == "PREPARED" && effect["state"] == "PREPARED" && Hash(e["sequence"]) == Hash(effect["sequence"]), nil
		}
	}
	return false, nil
}

func pausePreparedEffectMayBegin(tx *sql.Tx, project string, run, task, effect Object) (bool, error) {
	if task["status"] != "BLOCKED" || task["active_run_id"] != run["id"] || Hash(run["lease_epoch"]) != Hash(effect["epoch"]) {
		return false, nil
	}
	intent, err := pauseIntent(tx, project, Str(run, "id"), run["lease_epoch"])
	if err != nil || intent == nil {
		return false, err
	}
	if intent["state"] != "PAUSE_REQUESTED" {
		return false, nil
	}
	return pauseEffectInCutoff(tx, intent, effect, true)
}

func pauseEffectsSettled(tx *sql.Tx, project, run string) error {
	var n int
	err := tx.QueryRow(`SELECT count(*) FROM resource_effects x WHERE project=? AND run=? AND sequence=(SELECT max(y.sequence) FROM resource_effects y WHERE y.project=x.project AND y.run=x.run AND y.effect_key=x.effect_key) AND json_extract(body,'$.state') NOT IN ('CONFIRMED','NOT_APPLIED')`, project, run).Scan(&n)
	if err != nil {
		return err
	}
	if n != 0 {
		return Fail(409, "STATE_CONFLICT", "pause requires all admitted effects reconciled")
	}
	return nil
}

func provenRuntimePause(tx *sql.Tx, project string, run Object) (bool, error) {
	intent, err := pauseIntent(tx, project, Str(run, "id"), run["lease_epoch"])
	if err != nil || intent == nil {
		return false, err
	}
	if intent["state"] != "PAUSED_CONFIRMED" {
		return false, nil
	}
	var raw, hash string
	err = tx.QueryRow(`SELECT body,body_hash FROM runtime_pause_receipts WHERE project=? AND pause_id=? AND kind='STATE_TRANSITION' AND json_extract(body,'$.revision')=?`, project, intent["pause_id"], intent["revision"]).Scan(&raw, &hash)
	if err != nil {
		return false, err
	}
	witness, err := Decode([]byte(raw))
	if err != nil || Hash(witness) != hash || witness["intent_hash"] != Hash(intent) {
		return false, Fail(409, "GATE_FAILED", "pause current witness missing")
	}
	err = tx.QueryRow(`SELECT body,body_hash FROM runtime_pause_receipts WHERE project=? AND pause_id=? AND kind='NATIVE_STOPPED'`, project, intent["pause_id"]).Scan(&raw, &hash)
	if err != nil {
		return false, err
	}
	proof, err := Decode([]byte(raw))
	if err != nil || Hash(proof) != hash {
		return false, Fail(409, "GATE_FAILED", "pause stop witness changed")
	}
	observation, _ := proof["observation"].(map[string]any)
	if observation == nil || observation["state"] != "PAUSED" || observation["children_stopped"] != true || observation["streams_drained"] != true || observation["cleanup_complete"] != true {
		return false, Fail(409, "GATE_FAILED", "pause native stop incomplete")
	}
	if _, err = nativeDispatchProof(tx, project, run, observation); err != nil {
		return false, err
	}
	return true, pauseEffectsSettled(tx, project, Str(run, "id"))
}
