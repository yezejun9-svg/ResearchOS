//go:build windows

package domain

import (
	"context"
	"database/sql"
	"strings"
)

func (c *RuntimeCoordinator) sessionModel(tx *sql.Tx, project, modelRef string) (Object, Object, error) {
	var selected, profile Object
	for _, route := range c.config.Routes {
		if route.ProjectID != project {
			continue
		}
		runtime, e := load(tx, project, "RuntimeRegistration", route.RuntimeID)
		if e != nil {
			return nil, nil, e
		}
		_, artifact, e := c.service.currentRuntimeBinding(tx, project, runtime)
		if e != nil {
			continue
		}
		candidate, e := runtimeProfileBody(tx, project, artifact)
		if e != nil {
			return nil, nil, e
		}
		config, _ := candidate["model_config"].(map[string]any)
		if candidate["backend"] != runtimeMuBackend || Str(config, "ref") != modelRef {
			continue
		}
		if selected != nil {
			return nil, nil, Fail(409, "MODEL_UNAVAILABLE", "model configuration maps to multiple runtimes")
		}
		if e = validateRuntimeModelConfig(candidate); e != nil {
			return nil, nil, e
		}
		if candidate["command_id"] != route.CommandID {
			return nil, nil, Fail(403, "FORBIDDEN", "model command differs from host route")
		}
		selected, profile = runtime, candidate
	}
	if selected == nil {
		return nil, nil, Fail(503, "MODEL_UNAVAILABLE", "model configuration has no bound host runtime")
	}
	return selected, profile, nil
}

func (c *RuntimeCoordinator) ValidateBinding(ctx context.Context, tx *sql.Tx, principal, project, workspaceRef, modelConfigRef string) error {
	if c.config.WorkspaceAuthority == nil {
		return Fail(503, "RESOURCE_UNAVAILABLE", "host workspace authority unavailable")
	}
	b, e := c.service.binding(ctx, tx, workspaceRef)
	if e != nil {
		return e
	}
	if b.PrincipalID != principal || b.ProjectID == nil || *b.ProjectID != project || b.Status != WorkspaceActive {
		return Fail(403, "FORBIDDEN", "current project workspace binding required")
	}
	if e = c.config.WorkspaceAuthority.ConfirmPath(ctx, b.RealPath, b.Access); e != nil {
		return Fail(403, "WORKSPACE_REVOKED", "workspace authorization is no longer current")
	}
	_, _, e = c.sessionModel(tx, project, modelConfigRef)
	return e
}

func (c *RuntimeCoordinator) AdmitTurn(ctx context.Context, tx *sql.Tx, project, modelConfigRef string, task Object) error {
	runtime, _, e := c.sessionModel(tx, project, modelConfigRef)
	if e != nil {
		return e
	}
	_, e = c.service.currentRuntimeAdmission(tx, project, task, runtime, []any{"start"}, "session.send")
	return e
}

func (c *RuntimeCoordinator) sessionTaskRoute(tx *sql.Tx, project string, task Object, runtimeID string) error {
	var modelRef string
	if e := tx.QueryRow("SELECT model_config_ref FROM client_sessions WHERE project_id=? AND task_id=?", project, task["id"]).Scan(&modelRef); e != nil {
		return Fail(403, "FORBIDDEN", "model task has no current session binding")
	}
	runtime, _, e := c.sessionModel(tx, project, modelRef)
	if e != nil {
		return e
	}
	if runtime["id"] != runtimeID {
		return Fail(403, "FORBIDDEN", "task session selects a different model runtime")
	}
	return nil
}

var _ ClientSessionRuntime = (*RuntimeCoordinator)(nil)

// Repair the client view from canonical Run state on the existing coordinator
// scan. This is a projection only: it never claims, resumes, or accepts work.
func (c *RuntimeCoordinator) projectCurrentSessionRuns(ctx context.Context) error {
	if c.config.ClientSchema == nil {
		return nil
	}
	tx, err := c.service.DB.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	var installed int
	if err = tx.QueryRow("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='client_sessions'").Scan(&installed); err != nil {
		return err
	}
	if installed == 0 {
		return nil
	}
	rows, err := tx.Query(`SELECT r.project,r.body FROM client_sessions s
		JOIN domain_objects t ON t.project=s.project_id AND t.kind='Task' AND t.id=s.task_id
		JOIN domain_objects r ON r.project=t.project AND r.kind='Run' AND r.id=json_extract(t.body,'$.active_run_id')
		WHERE json_extract(t.body,'$.task_type')='mu_turn'`)
	if err != nil {
		return err
	}
	type currentRun struct {
		project string
		run     Object
	}
	runs := []currentRun{}
	for rows.Next() {
		var project, raw string
		if err = rows.Scan(&project, &raw); err != nil {
			rows.Close()
			return err
		}
		run, e := Decode([]byte(raw))
		if e != nil {
			rows.Close()
			return e
		}
		runs = append(runs, currentRun{project, run})
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return err
	}
	for _, current := range runs {
		artifacts := Empty()
		if runTerminal(current.run) {
			artifacts = Arr(current.run, "result_artifact_ids")
		}
		if err = c.projectSessionRun(tx, current.project, current.run, artifacts); err != nil {
			return err
		}
	}
	if err = c.projectHistoricalSessionUsage(tx); err != nil {
		return err
	}
	return tx.Commit()
}

func (c *RuntimeCoordinator) projectSessionRun(tx *sql.Tx, project string, run Object, artifacts []any, unavailable ...string) error {
	task, err := load(tx, project, "Task", Str(run, "task_id"))
	if err != nil {
		return err
	}
	if task["task_type"] != "mu_turn" {
		return nil
	}
	if err = c.projectSessionEffects(tx, project, run, nil); err != nil {
		return err
	}
	var sid, build string
	var revision, epoch, watermark int64
	e := tx.QueryRow("SELECT id,core_build_id,revision,writer_epoch,event_watermark FROM client_sessions WHERE project_id=? AND task_id=?", project, run["task_id"]).Scan(&sid, &build, &revision, &epoch, &watermark)
	if e == sql.ErrNoRows {
		return nil
	}
	if e != nil {
		return e
	}
	if c.config.ClientSchema == nil {
		return Fail(503, "HOST_UNAVAILABLE", "typed runtime event schema unavailable")
	}
	if _, e = tx.Exec("UPDATE client_sessions SET run_id=? WHERE id=? AND project_id=?", run["id"], sid, project); e != nil {
		return e
	}
	emit := func(kind string, payload Object) error {
		watermark++
		ev := &SessionEvent{EventID: strptr(ID()), SessionID: &sid, Sequence: &watermark, CoreBuildID: &build, ProtocolVersion: strptr(ProtocolV2), RunID: strptr(Str(run, "id")), Kind: &kind, Payload: Bytes(payload)}
		if err := AppendSessionEvent(context.Background(), tx, c.config.ClientSchema, project, ev, epoch, revision); err != nil {
			return err
		}
		revision++
		return nil
	}
	var projected int
	runRevision, e := Num(run, "revision")
	if e != nil {
		return e
	}
	if e = tx.QueryRow(`SELECT count(*) FROM outbox WHERE project=? AND json_extract(body,'$.session_id')=? AND json_extract(body,'$.run_id')=?
		AND json_extract(body,'$.kind')='RUN_STATE' AND json_extract(body,'$.payload.revision')=?`, project, sid, run["id"], runRevision).Scan(&projected); e != nil {
		return e
	}
	state := Object{"run_id": run["id"], "status": run["status"], "revision": run["revision"], "cancel_requested_at": run["cancel_requested_at"], "cancel_confirmed_at": run["cancel_confirmed_at"], "settled_at": run["runtime_settled_at"], "children_stopped": run["children_stopped"], "queue_empty": run["queue_empty"]}
	if projected == 0 {
		if e = emit("RUN_STATE", state); e != nil {
			return e
		}
	}
	for _, reason := range unavailable {
		if e = tx.QueryRow(`SELECT count(*) FROM outbox WHERE project=? AND json_extract(body,'$.session_id')=? AND json_extract(body,'$.run_id')=?
			AND json_extract(body,'$.kind')='ERROR' AND json_extract(body,'$.payload.message')=?`, project, sid, run["id"], reason).Scan(&projected); e != nil {
			return e
		}
		if projected == 0 {
			if e = emit("ERROR", Object{"code": "RESOURCE_BLOCKED", "message": reason, "retryable": false,
				"recovery": "WAIT_FOR_SETTLEMENT", "current_revision": nil, "current_writer_epoch": nil,
				"resource_request_id": nil, "retry_after_ms": nil, "correlation_id": run["id"]}); e != nil {
				return e
			}
		}
	}
	for _, id := range artifacts {
		if e = tx.QueryRow(`SELECT count(*) FROM outbox WHERE project=? AND json_extract(body,'$.session_id')=? AND json_extract(body,'$.run_id')=?
			AND json_extract(body,'$.kind')='ARTIFACT' AND json_extract(body,'$.payload.artifact_ref.id')=?`, project, sid, run["id"], id).Scan(&projected); e != nil {
			return e
		}
		if projected != 0 {
			continue
		}
		artifact, err := load(tx, project, "Artifact", id.(string))
		if err != nil {
			return err
		}
		if e = emit("ARTIFACT", Object{"artifact_ref": Ref(artifact, "Artifact"), "availability": "AVAILABLE"}); e != nil {
			return e
		}
		if run["status"] != "SETTLED" {
			continue
		}
		var raw []byte
		if e = tx.QueryRow("SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1", project, artifact["storage_key"]).Scan(&raw); e != nil {
			return e
		}
		if Digest(raw) != artifact["content_hash"] {
			return Fail(422, "CONTENT_HASH_MISMATCH", "session result changed")
		}
		result, err := Decode(raw)
		if err != nil {
			return err
		}
		messages := Arr(result, "messages")
		if len(messages) == 0 {
			continue
		}
		final, ok := messages[len(messages)-1].(map[string]any)
		if !ok || final["role"] != "assistant" || final["stopReason"] != "stop" {
			continue
		}
		var text strings.Builder
		for _, v := range Arr(final, "content") {
			p, ok := v.(map[string]any)
			if ok && p["type"] == "text" {
				text.WriteString(Str(p, "text"))
			}
		}
		if text.Len() == 0 {
			continue
		}
		messageID := ID()
		offset := 0
		part := func(phase, value string) error {
			return emit("MESSAGE", Object{"message_id": messageID, "role": "ASSISTANT", "phase": phase, "part_index": 0, "content_offset_utf8_bytes": offset, "text": value})
		}
		if e = part("START", ""); e != nil {
			return e
		}
		runes := []rune(text.String())
		for len(runes) > 0 {
			n := min(len(runes), 16384)
			chunk := string(runes[:n])
			if e = part("DELTA", chunk); e != nil {
				return e
			}
			offset += len([]byte(chunk))
			runes = runes[n:]
		}
		if e = part("END", ""); e != nil {
			return e
		}
		if e = c.service.sealSessionTranscript(context.Background(), tx, c.config.ClientSchema, project, sid, Str(run, "executor_principal_id")); e != nil {
			return e
		}
	}
	return nil
}
