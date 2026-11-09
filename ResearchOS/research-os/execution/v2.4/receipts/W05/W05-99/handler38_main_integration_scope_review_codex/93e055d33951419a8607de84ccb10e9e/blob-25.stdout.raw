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

func clientAuthenticatedPrincipal(ctx context.Context, tx *sql.Tx, id string) (Principal, error) {
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
	return p, nil
}

func clientPrincipal(ctx context.Context, tx *sql.Tx, id, project string, owner bool) (Principal, error) {
	p, err := clientAuthenticatedPrincipal(ctx, tx, id)
	if err != nil {
		return p, err
	}
	if !p.Allowed(project, "", "", false) || owner && !p.HasRole("OWNER") {
		return p, Fail(403, "FORBIDDEN", "current project Owner required for session writes")
	}
	return p, nil
}

// A real project-level goal.start can create a mapped session. Its response has
// a null top-level session_id and the created identity in result.snapshot. A
// session-scoped goal.start has a non-null top-level session_id, so it is never
// mistaken for a second creation receipt. Conflicting receipts fail closed.
func clientSessionCreationPrincipal(ctx context.Context, tx *sql.Tx, project, session string) (string, error) {
	rows, err := tx.QueryContext(ctx, `SELECT project,principal FROM idempotency WHERE
		(operation='v2:session.create' AND json_extract(body,'$.status')='COMPLETED' AND json_extract(body,'$.result.session_id')=?) OR
		(operation='v2:goal.start' AND json_extract(body,'$.status')='COMPLETED' AND json_extract(body,'$.session_id') IS NULL AND json_extract(body,'$.result.snapshot.session_id')=?)`, session, session)
	if err != nil {
		return "", err
	}
	defer rows.Close()
	owner := ""
	count := 0
	for rows.Next() {
		var receiptProject, receiptOwner string
		if err = rows.Scan(&receiptProject, &receiptOwner); err != nil {
			return "", err
		}
		if receiptProject != project || receiptOwner == "" {
			return "", Fail(403, "FORBIDDEN", "session creation attribution conflicts with its project")
		}
		owner = receiptOwner
		count++
	}
	if err = rows.Err(); err != nil {
		return "", err
	}
	if count == 0 {
		return "", sql.ErrNoRows
	}
	if count != 1 {
		return "", Fail(403, "FORBIDDEN", "session has conflicting creation receipts")
	}
	return owner, nil
}

// Older administratively mapped sessions retain their existing project grants.
func clientSessionOwner(ctx context.Context, tx *sql.Tx, project, session, principal string) error {
	owner, err := clientSessionCreationPrincipal(ctx, tx, project, session)
	if err == sql.ErrNoRows {
		return nil
	}
	if err != nil {
		return err
	}
	if owner != principal {
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
	if gate, ok := s.SessionRuntime.(interface{ ClientIntakeOpen() bool }); ok && !gate.ClientIntakeOpen() {
		return Fail(409, "RESOURCE_BLOCKED", "runtime intake fenced for release")
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
	sid, err := s.createBoundClientSession(ctx, tx, env, principal, p.Workspace, p.Model, p.Title)
	if err != nil {
		return clientFault(env, err)
	}
	snap, err := BuildSessionSnapshot(ctx, tx, s.Doc, project, sid)
	if err != nil {
		return nil, err
	}
	return &Response{ProtocolVersion: strptr(ProtocolV2), CommandID: env.CommandID, Method: env.Method, Status: strptr("COMPLETED"), SessionID: &sid, Revision: revPtr(1), Result: snap}, nil
}

// Both session.create and a project-level goal.start mint the same durable
// mapped session. Their own successful idempotency receipts attribute creation;
// this helper never manufactures a session.create command or receipt.
func (s *ClientService) createBoundClientSession(ctx context.Context, tx *sql.Tx, env *Envelope, principal, workspace, model, title string) (string, error) {
	project := deref(env.ProjectID)
	if err := s.checkClientCreationBinding(ctx, tx, principal, project, workspace, model); err != nil {
		return "", err
	}
	if s.Host.LeaseTTL <= 0 || s.Host.CoreBuildID == "" {
		return "", Fail(503, "HOST_UNAVAILABLE", "host session policy unavailable")
	}
	now := time.Now().UTC()
	expires := now.Add(s.Host.LeaseTTL)
	sid, native := ID(), ID()
	if err := MapClientSession(ctx, tx, ClientSession{ID: sid, ProjectID: project, Revision: 1, WriterEpoch: 1, WriterClientID: deref(env.ClientID), CreatedAt: now, UpdatedAt: now, LeaseExpiresAt: &expires, UpstreamSession: native, WorkspaceRef: &workspace, ModelConfigRef: &model, Title: &title, CoreBuildID: &s.Host.CoreBuildID, Protocol: ProtocolV2}); err != nil {
		return "", err
	}
	return sid, nil
}

func (s *ClientService) checkClientCreationBinding(ctx context.Context, tx *sql.Tx, principal, project, workspace, model string) error {
	if model == "" || s.Domain == nil {
		return Fail(503, "MODEL_UNAVAILABLE", "explicit model binding required")
	}
	var n int
	if err := tx.QueryRowContext(ctx, `SELECT (SELECT count(*) FROM host_model_configurations WHERE model_config_ref=?)+(SELECT count(*) FROM idempotency WHERE operation='v2:host.configure' AND json_extract(body,'$.status')='COMPLETED' AND json_extract(body,'$.result.model_config_ref')=?)`, model, model).Scan(&n); err != nil {
		return err
	}
	if n == 0 {
		return s.checkClientBinding(ctx, tx, principal, project, workspace, model)
	}
	if _, err := s.visibleClientConfiguration(ctx, tx, principal, model); err != nil {
		return err
	}
	b, err := s.Domain.binding(ctx, tx, workspace)
	if err != nil || b.ProjectID == nil || *b.ProjectID != project || b.PrincipalID != principal || b.Status != WorkspaceActive {
		return Fail(403, "WORKSPACE_REVOKED", "current project workspace binding required")
	}
	return nil
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
	rows, err := tx.QueryContext(ctx, `SELECT s.id FROM client_sessions s WHERE s.project_id=? AND s.id>? AND NOT EXISTS
		(SELECT 1 FROM idempotency i WHERE i.project=s.project_id AND i.principal<>? AND json_extract(i.body,'$.status')='COMPLETED' AND
		 ((i.operation='v2:session.create' AND json_extract(i.body,'$.result.session_id')=s.id) OR
		 (i.operation='v2:goal.start' AND json_extract(i.body,'$.session_id') IS NULL AND json_extract(i.body,'$.result.snapshot.session_id')=s.id)))
		ORDER BY s.id LIMIT ?`, project, after, principal, p.Limit+1)
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
	for _, id := range ids {
		owner, attributionErr := clientSessionCreationPrincipal(ctx, tx, project, id)
		if attributionErr != nil && attributionErr != sql.ErrNoRows {
			return nil, attributionErr
		}
		if owner != "" && owner != principal {
			return nil, Fail(403, "FORBIDDEN", "session belongs to another principal")
		}
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
		if payload.Delivery != "NORMAL" {
			if err = s.SessionRuntime.AdmitTurn(ctx, tx, sess.project, model, task); err != nil {
				return clientFault(env, err)
			}
			return s.enqueueClientMessage(ctx, tx, env, principal, sess, task, payload.Text, payload.Delivery, payload.Attachments)
		}
		if !clientTurnSettled(tx, sess.project, sess.sessionID, task) {
			return NewTypedRejection(env, "SESSION_BUSY", "the previous turn requires settlement or explicit cancellation"), nil
		}
	}
	if payload.Delivery != "NORMAL" {
		return NewTypedRejection(env, "SESSION_BUSY", "an original task is required"), nil
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
	// Freeze every completed prior USER/ASSISTANT message before this turn's
	// USER event exists. The bounded journal copy enters the new Task as a real
	// sandbox artifact input; a first turn has no history ref.
	historyArtifact, err := s.clientHistoryArtifact(ctx, tx, p, sess.project, sess.sessionID, sess.watermark)
	if err != nil {
		return clientFault(env, err)
	}
	sourceRefs := append(Empty(), refs...)
	if historyArtifact != nil {
		refs = append(refs, Ref(historyArtifact, "Artifact"))
	}
	// The authenticated NORMAL message authorizes one finite response. The
	// shared builder preserves its Requirement/Goal/Task/runtime gates.
	created, err := s.buildFiniteClientGoal(ctx, tx, env, p, sess, model, finiteGoalSpec{
		Objective: payload.Text, Title: "Client message", Deliverable: "One finite Mu response to the authenticated client message",
		RequirementKey: "SESSION-" + ID(), Rationale: "Authenticated Owner NORMAL message for one finite Mu turn",
		ProblemID: ID(), CandidateID: sess.sessionID, SourceRefs: sourceRefs, InputRefs: refs, Contract: clientTurnContract(),
	})
	if err != nil {
		return clientFault(env, err)
	}
	task, blocked := created.Task, created.Blocked
	messageID := ID()
	for _, part := range []Object{{"phase": "START", "text": "", "content_offset_utf8_bytes": 0}, {"phase": "DELTA", "text": payload.Text, "content_offset_utf8_bytes": 0}, {"phase": "END", "text": "", "content_offset_utf8_bytes": len([]byte(payload.Text))}} {
		part["message_id"], part["role"], part["part_index"] = messageID, "USER", 0
		if err = s.journal(ctx, tx, env, sess, "MESSAGE", part); err != nil {
			return nil, err
		}
		sess.revision++
		sess.watermark++
	}
	if err = s.Domain.sealSessionTranscript(ctx, tx, s.Doc, sess.project, sess.sessionID, principal); err != nil {
		return nil, err
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

// A finite response can finish before its Task receives independent acceptance.
// Keep that acceptance pending while requiring actual process/effect settlement
// and durable terminal projection before replacing the session's current Task.
func clientTurnSettled(tx *sql.Tx, project, sessionID string, task Object) bool {
	installed, err := clientQueueInstalled(tx)
	if err != nil {
		return false
	}
	if installed {
		var pending int
		if err = tx.QueryRow(`SELECT (SELECT count(*) FROM client_queue_fences f WHERE f.project=? AND f.task_id=? AND (restore_fenced<>0 OR state='RECONCILING' OR EXISTS(SELECT 1 FROM client_command_queue q WHERE q.generation=f.generation AND q.state NOT IN ('CONSUMED','DROPPED'))))+(SELECT count(*) FROM client_control_requests c,json_each(c.task_ids) t WHERE c.project=? AND c.session_id=? AND t.value=? AND c.state<>'CONFIRMED')`, project, task["id"], project, sessionID, task["id"]).Scan(&pending); err != nil || pending != 0 {
			return false
		}
	}

	runID := Str(task, "active_run_id")
	if runID == "" {
		return task["status"] == "ACCEPTED" || task["status"] == "CANCELLED" || task["status"] == "FAILED"
	}
	run, err := load(tx, project, "Run", runID)
	if err != nil || !runTerminal(run) || run["children_stopped"] != true || run["queue_empty"] != true || effectsReconciled(tx, project, runID) != nil {
		return false
	}
	if run["status"] == "CANCELLED" {
		if Str(run, "cancel_confirmed_at") == "" {
			return false
		}
	} else if Str(run, "runtime_settled_at") == "" {
		return false
	}
	// Report and client projection use separate commits. Until projection is
	// recovered, retaining this binding prevents a following turn hiding results.
	var projected int
	runRevision, err := Num(run, "revision")
	if err != nil {
		return false
	}
	err = tx.QueryRow(`SELECT count(*) FROM outbox WHERE project=? AND json_extract(body,'$.session_id')=?
		AND json_extract(body,'$.run_id')=? AND json_extract(body,'$.kind')='RUN_STATE'
		AND json_extract(body,'$.payload.revision')=? AND json_extract(body,'$.payload.status')=?`,
		project, sessionID, runID, runRevision, run["status"]).Scan(&projected)
	return err == nil && projected > 0
}
