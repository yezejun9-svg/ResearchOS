package domain

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"time"
)

// The coordinator inspects the original dispatch in the caller's transaction.
// It never launches a replacement run or treats a UI decision as a policy grant.
type ClientPermissionAuthority interface {
	CheckPermission(context.Context, *sql.Tx, string, string, Object, Object, Object) (bool, error)
}

func permissionTaskInputs(task Object) []any {
	return mergeUnique(Arr(task, "input_refs"), Arr(task, "requirement_refs"))
}

func sealPermissionArtifact(s *Service, tx *sql.Tx, p Principal, project string, raw []byte, mode string) (Object, error) {
	if mode != "LIVE" && mode != "FIXTURE" {
		return nil, Fail(409, "STATE_CONFLICT", "permission evidence requires the original measurement mode")
	}
	upload, err := s.upload(tx, p, project, raw)
	if err != nil {
		return nil, err
	}
	return s.seal(tx, p, project, Object{"run_id": nil, "kind": "REPORT", "evidence_kind": "OBSERVED", "measurement_mode": mode,
		"storage_key": upload["storage_key"], "content_hash": upload["content_hash"], "byte_size": len(raw), "media_type": "application/json",
		"input_refs": Empty(), "source_refs": Empty(), "produced_by": p.ID, "access_class": "PROJECT"})
}

func permissionArtifact(tx *sql.Tx, project string, ref Object) (Object, Object, error) {
	if ref == nil || ref["entity_type"] != "Artifact" {
		return nil, nil, Fail(409, "STATE_CONFLICT", "permission artifact reference unavailable")
	}
	a, err := version(tx, project, ref)
	if err != nil {
		return nil, nil, err
	}
	var raw []byte
	if err = tx.QueryRow("SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=?", project, a["storage_key"]).Scan(&raw); err != nil {
		return nil, nil, err
	}
	if len(raw) > 4<<20 || Digest(raw) != Str(a, "content_hash") || Hash(Ref(a, "Artifact")) != Hash(ref) {
		return nil, nil, Fail(409, "STATE_CONFLICT", "permission artifact differs from its sealed reference")
	}
	body, err := Decode(raw)
	return a, body, err
}

func loadClientPermission(tx *sql.Tx, project, sessionID, requestID string) (intent, record, scope, request Object, err error) {
	defer func() { err = permissionMissing(err) }()
	rows, err := tx.Query(`SELECT x.body FROM resource_effects x WHERE x.project=?
		AND json_extract(x.body,'$.permission.session_id')=? AND json_extract(x.body,'$.permission.request_id')=?
		AND x.sequence=(SELECT max(y.sequence) FROM resource_effects y WHERE y.project=x.project AND y.run=x.run AND y.effect_key=x.effect_key)`, project, sessionID, requestID)
	if err != nil {
		return
	}
	var bodies []string
	for rows.Next() {
		var raw string
		if err = rows.Scan(&raw); err != nil {
			break
		}
		bodies = append(bodies, raw)
	}
	if err == nil {
		err = rows.Err()
	}
	rows.Close()
	if err != nil {
		return
	}
	if len(bodies) != 1 {
		err = Fail(404, "NOT_FOUND", "original permission action is not available in this session")
		return
	}
	intent, err = Decode([]byte(bodies[0]))
	if err != nil {
		return
	}
	record, _ = intent["permission"].(map[string]any)
	ref, _ := record["scope_ref"].(map[string]any)
	_, scope, err = permissionArtifact(tx, project, ref)
	if err != nil {
		return
	}
	request, err = load(tx, project, "ResourceRequest", requestID)
	if err != nil {
		return
	}
	if request["category"] != "PERMISSION" || scope["project_id"] != project || scope["task_id"] != intent["task_id"] || scope["run_id"] != intent["run_id"] || Hash(scope) != record["action_digest"] {
		err = Fail(409, "STATE_CONFLICT", "permission scope does not match the original effect")
		return
	}
	linked := false
	for _, v := range Arr(request, "completed_artifact_refs") {
		linked = linked || Hash(v) == Hash(ref)
	}
	if !linked {
		err = Fail(409, "STATE_CONFLICT", "resource request does not contain the frozen scope")
		return
	}
	argsRef, _ := scope["arguments_artifact_ref"].(map[string]any)
	var arguments Object
	_, arguments, err = permissionArtifact(tx, project, argsRef)
	if err != nil {
		return
	}
	outer, _ := intent["payload"].(map[string]any)
	original, _ := outer["payload"].(map[string]any)
	if outer["capability"] != "TOOL" || original["name"] != scope["tool_name"] || Hash(original["arguments"]) != Hash(arguments) {
		err = Fail(409, "STATE_CONFLICT", "frozen arguments differ from the original tool request")
	}
	return
}

func permissionPrompt(doc *SchemaDoc, intent, record, scope, request Object) (Object, error) {
	allowed := Empty()
	policy := scope["authority"] == "USER_DECIDABLE"
	expiry, err := time.Parse(time.RFC3339Nano, Str(scope, "expires_at"))
	if policy && err == nil && expiry.After(time.Now()) && intent["state"] == "STARTED" && record["decision"] == nil && (request["status"] == "OPEN" || request["status"] == "ACKNOWLEDGED") {
		allowed = []any{"ALLOW_ONCE", "DENY"}
	}
	prompt := Object{"request": request, "task_id": scope["task_id"], "run_id": scope["run_id"], "action_digest": record["action_digest"],
		"action_artifact_ref": record["scope_ref"], "allowed_responses": allowed, "policy_allows_user_decision": policy, "action_scope": scope}
	if doc != nil {
		if err = doc.ValidateDef("PermissionPrompt", normalizeNumbers(prompt)); err != nil {
			return nil, fmt.Errorf("PERMISSION_SCHEMA:%w", err)
		}
	}
	return prompt, nil
}

func snapshotPermissions(ctx context.Context, tx *sql.Tx, doc *SchemaDoc, project, sessionID string) ([]any, error) {
	rows, err := tx.QueryContext(ctx, `SELECT DISTINCT json_extract(x.body,'$.permission.request_id') FROM resource_effects x
		JOIN domain_objects r ON r.project=x.project AND r.kind='ResourceRequest' AND r.id=json_extract(x.body,'$.permission.request_id')
		WHERE x.project=? AND json_extract(x.body,'$.permission.session_id')=? AND json_extract(r.body,'$.status') IN ('OPEN','ACKNOWLEDGED')
		AND x.sequence=(SELECT max(y.sequence) FROM resource_effects y WHERE y.project=x.project AND y.run=x.run AND y.effect_key=x.effect_key)
		ORDER BY r.id`, project, sessionID)
	if err != nil {
		return nil, err
	}
	var ids []string
	for rows.Next() {
		var id string
		if err = rows.Scan(&id); err != nil {
			break
		}
		ids = append(ids, id)
	}
	if err == nil {
		err = rows.Err()
	}
	rows.Close()
	if err != nil {
		return nil, err
	}
	out := Empty()
	for _, id := range ids {
		intent, record, scope, request, e := loadClientPermission(tx, project, sessionID, id)
		if e != nil {
			return nil, e
		}
		prompt, e := permissionPrompt(doc, intent, record, scope, request)
		if e != nil {
			return nil, e
		}
		out = append(out, prompt)
	}
	return out, nil
}

func appendPermissionEvent(ctx context.Context, tx *sql.Tx, doc *SchemaDoc, project, sessionID, runID, kind string, payload Object) error {
	var build string
	var revision, epoch, watermark int64
	if err := tx.QueryRowContext(ctx, "SELECT core_build_id,revision,writer_epoch,event_watermark FROM client_sessions WHERE project_id=? AND id=?", project, sessionID).Scan(&build, &revision, &epoch, &watermark); err != nil {
		return err
	}
	ev := &SessionEvent{EventID: strptr(ID()), SessionID: &sessionID, Sequence: int64ptr(watermark + 1), CoreBuildID: &build,
		ProtocolVersion: strptr(ProtocolV2), RunID: strptr(runID), Kind: &kind, Payload: Bytes(payload)}
	return AppendSessionEvent(ctx, tx, doc, project, ev, epoch, revision)
}

func (s *ClientService) respondClientPermission(ctx context.Context, tx *sql.Tx, env *Envelope, principal string, sess *clientSessionRow) (*Response, error) {
	if s.Domain == nil || s.Doc == nil {
		return NewTypedRejection(env, "HOST_UNAVAILABLE", "permission authority unavailable"), nil
	}
	body, err := Decode(env.Payload)
	if err != nil {
		return nil, err
	}
	if err = s.Doc.ValidateDef("RespondPermissionPayload", normalizeNumbers(body)); err != nil {
		return NewTypedRejection(env, "INVALID_REQUEST", "invalid original-action decision"), nil
	}
	intent, record, scope, request, err := loadClientPermission(tx, sess.project, sess.sessionID, Str(body, "resource_request_id"))
	if err != nil {
		return clientFault(env, err)
	}
	if err = s.Doc.ValidateDef("PermissionActionScope", normalizeNumbers(scope)); err != nil {
		return NewTypedRejection(env, "POLICY_DENIED", "frozen permission scope is invalid"), nil
	}
	if Hash(request["revision"]) != Hash(body["resource_request_revision"]) || record["action_digest"] != body["action_digest"] {
		return NewTypedRejection(env, "STALE_REVISION", "permission request or frozen action changed"), nil
	}
	if scope["authority"] != "USER_DECIDABLE" {
		return NewTypedRejection(env, "POLICY_DENIED", "this policy decision cannot be changed by user confirmation"), nil
	}
	if (request["status"] != "OPEN" && request["status"] != "ACKNOWLEDGED") || intent["state"] != "STARTED" || record["decision"] != nil {
		return NewTypedRejection(env, "RESOURCE_BLOCKED", "original permission action is already closed or cannot resume"), nil
	}
	expires, err := time.Parse(time.RFC3339Nano, Str(scope, "expires_at"))
	if err != nil || !expires.After(time.Now()) {
		return NewTypedRejection(env, "RESOURCE_BLOCKED", "original permission action expired"), nil
	}
	p, binding, err := s.clientWorkspaceBinding(ctx, tx, env, principal, Str(scope, "workspace_ref"), true)
	if err != nil {
		return clientFault(env, err)
	}
	if record["principal_id"] != principal || Hash(record["binding_revision"]) != Hash(binding.Revision) {
		return NewTypedRejection(env, "FORBIDDEN", "original action principal or workspace authority changed"), nil
	}
	var taskID, model string
	if err = tx.QueryRowContext(ctx, "SELECT task_id,model_config_ref FROM client_sessions WHERE id=? AND project_id=?", sess.sessionID, sess.project).Scan(&taskID, &model); err != nil {
		return nil, err
	}
	if taskID != scope["task_id"] || sess.runID != scope["run_id"] || model != scope["model_config_ref"] {
		return NewTypedRejection(env, "RESOURCE_BLOCKED", "session no longer owns the original task and run"), nil
	}
	task, err := s.Domain.readObject(tx, p, sess.project, "Task", taskID)
	if err != nil {
		return clientFault(env, err)
	}
	run, err := s.Domain.readObject(tx, p, sess.project, "Run", sess.runID)
	if err != nil {
		return clientFault(env, err)
	}
	if Hash(Ref(task, "Task")) != Hash(record["task_ref"]) || Hash(permissionTaskInputs(task)) != Hash(scope["input_refs"]) || task["active_run_id"] != sess.runID || task["status"] != "RUNNING" || runTerminal(run) || run["status"] == "CANCEL_REQUESTED" || Hash(run["lease_epoch"]) != Hash(intent["epoch"]) {
		return NewTypedRejection(env, "RESOURCE_BLOCKED", "original task, inputs or run authority changed"), nil
	}
	for _, value := range Arr(scope, "input_refs") {
		if err = s.Domain.effective(tx, sess.project, value.(map[string]any)); err != nil {
			return NewTypedRejection(env, "RESOURCE_BLOCKED", "original permission inputs are no longer current"), nil
		}
	}
	if err = s.Domain.taskContextForRun(tx, sess.project, run); err != nil {
		return clientFault(env, err)
	}
	authority, ok := s.SessionRuntime.(ClientPermissionAuthority)
	if !ok {
		return NewTypedRejection(env, "HOST_UNAVAILABLE", "original runtime permission authority unavailable"), nil
	}
	waiting, err := authority.CheckPermission(ctx, tx, sess.project, sess.sessionID, intent, record, scope)
	if err != nil {
		return clientFault(env, err)
	}
	decision := Str(body, "decision")
	if decision == "ALLOW_ONCE" && !waiting {
		return NewTypedRejection(env, "RESOURCE_BLOCKED", "original tool is no longer waiting or required resources are unavailable"), nil
	}
	scopeRef, _ := record["scope_ref"].(map[string]any)
	scopeArtifact, err := version(tx, sess.project, scopeRef)
	if err != nil {
		return clientFault(env, err)
	}
	resolution, err := sealPermissionArtifact(s.Domain, tx, p, sess.project, Bytes(Object{"schema": "researchos.permission-decision.v1",
		"resource_request_ref": Ref(request, "ResourceRequest"), "action_digest": record["action_digest"], "action_artifact_ref": record["scope_ref"],
		"effect_key": intent["key"], "run_id": intent["run_id"], "task_id": intent["task_id"], "decision": decision, "reason": body["reason"], "decided_by": principal, "decided_at": Now()}), Str(scopeArtifact, "measurement_mode"))
	if err != nil {
		return clientFault(env, err)
	}
	request, err = s.Domain.resolveResourceRequest(tx, p, sess.project, Str(request, "id"), Object{"resolution_evidence_refs": []any{Ref(resolution, "Artifact")}, "reason": body["reason"]})
	if err != nil {
		return clientFault(env, err)
	}
	if err = s.Domain.event(tx, sess.project, "ResourceRequest", request, principal, deref(env.CommandID), "RESOURCE_REQUESTED"); err != nil {
		return nil, err
	}
	record["decision"], record["decision_artifact_ref"], record["decided_by"] = decision, Ref(resolution, "Artifact"), principal
	record["consumed"] = decision == "ALLOW_ONCE"
	intent["permission"] = record
	if err = effectAppend(tx, sess.project, sess.runID, Str(intent, "key"), intent); err != nil {
		return nil, err
	}
	if decision == "DENY" {
		cancelled, _, _, e := s.Domain.runtimeOperation(tx, p, sess.project, sess.runID, Object{"reason": "Owner denied original tool action"}, "cancelRun", deref(env.CommandID))
		if e != nil {
			return clientFault(env, e)
		}
		if err = s.Domain.event(tx, sess.project, "Run", cancelled, principal, deref(env.CommandID), "RUN_CHANGED"); err != nil {
			return nil, err
		}
	}
	result := Object{"request": request, "decision": decision, "resolution_artifact_ref": Ref(resolution, "Artifact"), "action_digest": record["action_digest"],
		"consumed": decision == "ALLOW_ONCE", "resumption_scheduled": decision == "ALLOW_ONCE" && waiting}
	if err = s.journal(ctx, tx, env, sess, "PERMISSION_RESOLVED", result); err != nil {
		return nil, err
	}
	return &Response{ProtocolVersion: strptr(ProtocolV2), CommandID: env.CommandID, Method: env.Method, Status: strptr("COMPLETED"),
		SessionID: env.SessionID, Revision: revPtr(sess.revision + 1), Result: result}, nil
}

// Keep ordinary missing rows in the typed error domain without obscuring SQL errors.
func permissionMissing(err error) error {
	if errors.Is(err, sql.ErrNoRows) {
		return Fail(404, "NOT_FOUND", "original permission record unavailable")
	}
	return err
}
