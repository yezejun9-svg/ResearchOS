package domain

import (
	"context"
	"database/sql"
	"encoding/base64"
	"encoding/json"
	"errors"
	"strings"
	"time"
	"unicode/utf8"
)

// ClientSessionRuntime is supplied by the host composition root. It must only
// inspect current bindings/admission in this transaction: it must never launch a
// worker, make a provider request, or open a second database transaction.
type ClientSessionRuntime interface {
	ValidateBinding(ctx context.Context, tx *sql.Tx, principal, project, workspaceRef, modelConfigRef string) error
	AdmitTurn(ctx context.Context, tx *sql.Tx, project, modelConfigRef string, task Object) error
}

func clientPrincipal(ctx context.Context, tx *sql.Tx, id, project string, owner bool) (Principal, error) {
	p := Principal{ID: id}
	var roles string
	if err := tx.QueryRowContext(ctx, "SELECT roles,can_create_project FROM auth_principals WHERE id=? AND revoked=0", id).Scan(&roles, &p.CanCreateProject); err != nil {
		return p, Fail(403, "FORBIDDEN", "current principal required")
	}
	if err := json.Unmarshal([]byte(roles), &p.Roles); err != nil {
		return p, err
	}
	rows, err := tx.QueryContext(ctx, "SELECT project,task,run,restricted FROM auth_grants WHERE principal=?", id)
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
	if !p.Allowed(project, "", "", false) || owner && !p.HasRole("OWNER") {
		return p, Fail(403, "FORBIDDEN", "current project Owner required for session writes")
	}
	return p, nil
}

// The original creation receipt is the existing durable principal attribution.
// Older administratively mapped sessions retain their existing project grants.
func clientSessionOwner(ctx context.Context, tx *sql.Tx, project, session, principal string) error {
	var owner string
	err := tx.QueryRowContext(ctx, `SELECT principal FROM idempotency WHERE project=? AND operation='v2:session.create' AND json_extract(body,'$.result.session_id')=?`, project, session).Scan(&owner)
	if err != nil && err != sql.ErrNoRows {
		return err
	}
	if err == nil && owner != principal {
		return Fail(403, "FORBIDDEN", "session belongs to another principal")
	}
	return nil
}

func clientFault(env *Envelope, err error) (*Response, error) {
	var f *Fault
	if !errors.As(err, &f) {
		return nil, err
	}
	code := f.Code
	if _, ok := recoveryByCode[code]; !ok {
		code = "RESOURCE_BLOCKED"
	}
	return NewTypedRejection(env, code, f.Message), nil
}

func (s *ClientService) checkClientBinding(ctx context.Context, tx *sql.Tx, principal, project, workspace, model string) error {
	if s.Domain == nil || s.SessionRuntime == nil {
		return Fail(503, "MODEL_UNAVAILABLE", "host session runtime binding is unavailable")
	}
	b, err := s.Domain.binding(ctx, tx, workspace)
	if err != nil {
		return Fail(404, "NOT_FOUND", "authorized workspace binding unavailable")
	}
	if b.PrincipalID != principal || b.ProjectID == nil || *b.ProjectID != project {
		return Fail(403, "FORBIDDEN", "workspace is not bound to this principal and project")
	}
	if b.Status != WorkspaceActive {
		return Fail(403, "WORKSPACE_REVOKED", "workspace binding revoked")
	}
	return s.SessionRuntime.ValidateBinding(ctx, tx, principal, project, workspace, model)
}

func (s *ClientService) createClientSession(ctx context.Context, tx *sql.Tx, env *Envelope, principal string) (*Response, error) {
	project := deref(env.ProjectID)
	if _, err := clientPrincipal(ctx, tx, principal, project, true); err != nil {
		return clientFault(env, err)
	}
	var p struct {
		Workspace string `json:"workspace_ref"`
		Model     string `json:"model_config_ref"`
		Title     string `json:"title"`
	}
	if err := json.Unmarshal(env.Payload, &p); err != nil {
		return nil, err
	}
	if err := s.checkClientBinding(ctx, tx, principal, project, p.Workspace, p.Model); err != nil {
		return clientFault(env, err)
	}
	if s.Host.LeaseTTL <= 0 || s.Host.CoreBuildID == "" {
		return NewTypedRejection(env, "HOST_UNAVAILABLE", "host session policy unavailable"), nil
	}
	now := time.Now().UTC()
	expires := now.Add(s.Host.LeaseTTL)
	sid, native := ID(), ID()
	if err := MapClientSession(ctx, tx, ClientSession{ID: sid, ProjectID: project, Revision: 1, WriterEpoch: 1, WriterClientID: deref(env.ClientID), CreatedAt: now, UpdatedAt: now, LeaseExpiresAt: &expires, UpstreamSession: native, WorkspaceRef: &p.Workspace, ModelConfigRef: &p.Model, Title: &p.Title, CoreBuildID: &s.Host.CoreBuildID, Protocol: ProtocolV2}); err != nil {
		return nil, err
	}
	snap, err := BuildSessionSnapshot(ctx, tx, s.Doc, project, sid)
	if err != nil {
		return nil, err
	}
	return &Response{ProtocolVersion: strptr(ProtocolV2), CommandID: env.CommandID, Method: env.Method, Status: strptr("COMPLETED"), SessionID: &sid, Revision: revPtr(1), Result: snap}, nil
}

func (s *ClientService) listClientSessions(ctx context.Context, tx *sql.Tx, env *Envelope, principal string) (*Response, error) {
	project := deref(env.ProjectID)
	if _, err := clientPrincipal(ctx, tx, principal, project, false); err != nil {
		return clientFault(env, err)
	}
	var p struct {
		Cursor *string `json:"cursor"`
		Limit  int     `json:"limit"`
	}
	if err := json.Unmarshal(env.Payload, &p); err != nil {
		return nil, err
	}
	after := ""
	if p.Cursor != nil {
		raw, err := base64.RawURLEncoding.DecodeString(*p.Cursor)
		var cursor []string
		if err != nil || json.Unmarshal(raw, &cursor) != nil || len(cursor) != 3 || cursor[0] != project || cursor[1] != principal || cursor[2] == "" {
			return NewTypedRejection(env, "CURSOR_INVALID", "session cursor does not belong to this scope"), nil
		}
		after = cursor[2]
	}
	rows, err := tx.QueryContext(ctx, `SELECT s.id FROM client_sessions s WHERE s.project_id=? AND s.id>? AND NOT EXISTS (SELECT 1 FROM idempotency i WHERE i.project=s.project_id AND i.operation='v2:session.create' AND json_extract(i.body,'$.result.session_id')=s.id AND i.principal<>?) ORDER BY s.id LIMIT ?`, project, after, principal, p.Limit+1)
	if err != nil {
		return nil, err
	}
	ids := []string{}
	for rows.Next() {
		var id string
		if err = rows.Scan(&id); err != nil {
			rows.Close()
			return nil, err
		}
		ids = append(ids, id)
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return nil, err
	}
	var cursor any
	if len(ids) > p.Limit {
		ids = ids[:p.Limit]
		cursor = base64.RawURLEncoding.EncodeToString(Bytes([]string{project, principal, ids[len(ids)-1]}))
	}
	items := Empty()
	for _, id := range ids {
		snap, err := BuildSessionSnapshot(ctx, tx, s.Doc, project, id)
		if err != nil {
			return nil, err
		}
		items = append(items, snap)
	}
	return &Response{ProtocolVersion: strptr(ProtocolV2), CommandID: env.CommandID, Method: env.Method, Status: strptr("COMPLETED"), Result: Object{"items": items, "next_cursor": cursor}}, nil
}

func clientTurnContract() Object {
	c := Object{"contract_revision": 1, "checks": []any{Object{"check_id": "mu-turn-output", "kind": "DETERMINISTIC", "required": true, "expected": "Bounded Mu response with exact user-message provenance and reconciled model/tool effects; execution is not independent acceptance", "command_key": "mu.turn-output-v1", "rubric_ref": nil, "qualification_id": nil, "not_applicable_reason": nil}}, "require_independent_verifier": true, "version_policy": "EXACT", "frozen_at": Now()}
	c["contract_hash"] = contractDigest(c)
	return c
}

func (s *ClientService) sendClientMessage(ctx context.Context, tx *sql.Tx, env *Envelope, principal string, sess *clientSessionRow) (*Response, error) {
	p, err := clientPrincipal(ctx, tx, principal, sess.project, true)
	if err != nil {
		return clientFault(env, err)
	}
	var payload struct {
		Text        string   `json:"text"`
		Attachments []string `json:"attachment_artifact_ids"`
		Delivery    string   `json:"delivery"`
	}
	if err = json.Unmarshal(env.Payload, &payload); err != nil {
		return nil, err
	}
	if payload.Delivery != "NORMAL" {
		return NewTypedRejection(env, "NOT_IMPLEMENTED", "STEER and FOLLOW_UP require a qualified runtime queue"), nil
	}
	if strings.TrimSpace(payload.Text) == "" || utf8.RuneCountInString(payload.Text) > 16384 {
		return NewTypedRejection(env, "CONTENT_TOO_LARGE", "message must contain 1 to 16384 characters"), nil
	}
	var workspace, model string
	var lease, previous sql.NullString
	if err = tx.QueryRowContext(ctx, "SELECT workspace_ref,model_config_ref,lease_expires_at,task_id FROM client_sessions WHERE id=? AND project_id=?", sess.sessionID, sess.project).Scan(&workspace, &model, &lease, &previous); err != nil {
		return nil, err
	}
	expires, parseErr := time.Parse(time.RFC3339Nano, lease.String)
	if parseErr != nil || !expires.After(time.Now()) {
		return NewTypedRejection(env, "LEASE_EXPIRED", "writer lease expired; acquire a current writer lease"), nil
	}
	if err = s.checkClientBinding(ctx, tx, principal, sess.project, workspace, model); err != nil {
		return clientFault(env, err)
	}
	if previous.Valid {
		task, err := load(tx, sess.project, "Task", previous.String)
		if err != nil {
			return nil, err
		}
		if task["status"] != "ACCEPTED" && task["status"] != "CANCELLED" && task["status"] != "FAILED" {
			return NewTypedRejection(env, "SESSION_BUSY", "the previous turn requires settlement or explicit cancellation"), nil
		}
	}
	refs := Empty()
	seen := map[string]bool{}
	for _, id := range payload.Attachments {
		if seen[id] {
			return NewTypedRejection(env, "INVALID_REQUEST", "duplicate attachment"), nil
		}
		seen[id] = true
		a, err := s.Domain.readObject(tx, p, sess.project, "Artifact", id)
		if err != nil {
			return clientFault(env, err)
		}
		if err = s.Domain.effective(tx, sess.project, Ref(a, "Artifact")); err != nil {
			return clientFault(env, err)
		}
		refs = append(refs, Ref(a, "Artifact"))
	}
	// The authenticated NORMAL message authorizes precisely this finite response.
	// It neither approves a model-created requirement nor enables goal continuation.
	req, err := s.Domain.createRequirement(tx, sess.project, Object{"requirement_key": "SESSION-" + ID(), "text": payload.Text, "basis": "USER_STATED", "source_refs": refs, "rationale": "Authenticated Owner NORMAL message for one finite Mu turn", "supersedes_id": nil, "acceptance_check_ids": Empty()})
	if err != nil {
		return nil, err
	}
	req, err = s.Domain.actRequirement(tx, sess.project, Str(req, "id"), Object{"action": "ACCEPT", "source_validation_refs": Empty()})
	if err != nil {
		return nil, err
	}
	refs = append(refs, Ref(req, "Requirement"))
	contract, problem := clientTurnContract(), ID()
	goal, err := s.Domain.createGoal(tx, sess.project, Object{"title": "Client message", "original_intent": payload.Text, "scope": "PROJECT", "requirement_refs": []any{Ref(req, "Requirement")}, "problem_ids": []any{problem}, "deliverables": []any{"One finite Mu response to the authenticated client message"}, "acceptance_contract": contract})
	if err != nil {
		return nil, err
	}
	task, err := s.Domain.createTask(tx, sess.project, Object{"goal_id": goal["id"], "title": "Client message", "task_type": "mu_turn", "stage": "delivery", "dependency_task_ids": Empty(), "requirement_refs": []any{Ref(req, "Requirement")}, "input_refs": refs, "acceptance_contract": contract, "origin_problem_id": problem, "candidate_id": sess.sessionID, "stop_policy": Object{"wall_time_seconds": 300, "max_attempts": 1, "max_parallel_runs": 1, "stop_conditions": []any{"turn complete", "model or tool effect unknown", "lease or authority lost", "Owner cancellation"}}})
	if err != nil {
		return nil, err
	}
	if _, err = s.Domain.actGoal(tx, sess.project, Str(goal, "id"), Object{"action": "ACTIVATE", "reason": "Authenticated finite client message"}); err != nil {
		return nil, err
	}
	state, err := singleton(tx, sess.project, "ProjectState")
	if err != nil {
		return nil, err
	}
	if _, err = s.Domain.createContext(tx, p, sess.project, Object{"task_id": task["id"], "expected_project_state_revision": state["revision"]}); err != nil {
		return nil, err
	}
	task, err = load(tx, sess.project, "Task", Str(task, "id"))
	if err != nil {
		return nil, err
	}
	task, err = s.Domain.orchestrateTask(tx, sess.project, task, Object{"action": "SUBMIT"})
	if err != nil {
		return nil, err
	}
	blocked := s.SessionRuntime.AdmitTurn(ctx, tx, sess.project, model, task)
	if blocked != nil {
		var fault *Fault
		if !errors.As(blocked, &fault) {
			return nil, blocked
		}
		if task["status"] != "BLOCKED" {
			task["status"] = "BLOCKED"
			if err = bump(task); err != nil {
				return nil, err
			}
			if err = s.Domain.put(tx, "Task", task); err != nil {
				return nil, err
			}
		}
	}
	if _, err = tx.ExecContext(ctx, "UPDATE client_sessions SET goal_id=?,task_id=?,run_id=NULL WHERE id=? AND project_id=?", goal["id"], task["id"], sess.sessionID, sess.project); err != nil {
		return nil, err
	}
	sess.runID = ""
	messageID := ID()
	for _, part := range []Object{{"phase": "START", "text": "", "content_offset_utf8_bytes": 0}, {"phase": "DELTA", "text": payload.Text, "content_offset_utf8_bytes": 0}, {"phase": "END", "text": "", "content_offset_utf8_bytes": len([]byte(payload.Text))}} {
		part["message_id"], part["role"], part["part_index"] = messageID, "USER", 0
		if err = s.journal(ctx, tx, env, sess, "MESSAGE", part); err != nil {
			return nil, err
		}
		sess.revision++
		sess.watermark++
	}
	if blocked != nil || task["status"] == "BLOCKED" {
		errorPayload := Object{"code": "RESOURCE_BLOCKED", "message": "Message saved; its Task is BLOCKED until the selected runtime has current qualification and permission", "retryable": false, "recovery": "RESOLVE_RESOURCE", "current_revision": sess.revision, "current_writer_epoch": sess.epoch, "resource_request_id": nil, "retry_after_ms": nil, "correlation_id": deref(env.CommandID)}
		if err = s.journal(ctx, tx, env, sess, "ERROR", errorPayload); err != nil {
			return nil, err
		}
		sess.revision++
		sess.watermark++
	}
	if err = s.Domain.event(tx, sess.project, "Task", task, principal, deref(env.CommandID), "TASK_CHANGED"); err != nil {
		return nil, err
	}
	snap, err := BuildSessionSnapshot(ctx, tx, s.Doc, sess.project, sess.sessionID)
	if err != nil {
		return nil, err
	}
	return &Response{ProtocolVersion: strptr(ProtocolV2), CommandID: env.CommandID, Method: env.Method, Status: strptr("COMPLETED"), SessionID: env.SessionID, Revision: revPtr(sess.revision), Result: Object{"message_id": messageID, "queue_position": 0, "run_id": nil, "snapshot": snap}}, nil
}
