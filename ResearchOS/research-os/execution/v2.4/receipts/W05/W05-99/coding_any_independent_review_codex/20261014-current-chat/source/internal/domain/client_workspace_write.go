package domain

import (
	"context"
	"database/sql"
	"path/filepath"
	"strings"
)

// This is an in-process port. A renderer cannot supply an absolute path,
// durable intent identity, or authorization callback.
type ClientWorkspaceWriteInput struct {
	WorkspacePath, Access, RelativePath, IntentKey, ScopeHash string
	ExpectedHash                                              *string
	CreateIfMissing                                           bool
	Content                                                   []byte
	Revalidate                                                func(context.Context) error
}
type ClientWorkspaceWriteResult struct {
	BeforeHash *string
	AfterHash  string
}
type ClientWorkspaceWriter interface {
	WorkspaceWrite(context.Context, ClientWorkspaceWriteInput) (ClientWorkspaceWriteResult, error)
}
type ClientWorkspaceWriteAuthority interface {
	AuthorizeWorkspaceWrite(context.Context, *sql.Tx, string, string, string, Object, string, int) error
}
type ClientTaskInputAuthority interface {
	FreezeClientTaskInputs(context.Context, *sql.Tx, string, string) ([]any, error)
}

func (s *ClientService) clientWorkspaceWriteScope(ctx context.Context, tx *sql.Tx, env *Envelope, principal string, payload Object) (Principal, *WorkspaceBinding, Object, error) {
	p, b, err := s.clientWorkspaceBinding(ctx, tx, env, principal, Str(payload, "workspace_ref"), true)
	if err != nil {
		return p, nil, nil, err
	}
	if b.Access != "READ_WRITE" {
		return p, nil, nil, Fail(403, "POLICY_DENIED", "workspace is read-only")
	}
	task, err := s.Domain.readObject(tx, p, deref(env.ProjectID), "Task", Str(payload, "task_id"))
	if err != nil {
		return p, nil, nil, err
	}
	switch Str(task, "status") {
	case "DRAFT", "READY", "BLOCKED", "NEEDS_REVALIDATION":
	case "ACCEPTED":
		return p, nil, nil, Fail(403, "ARTIFACT_IMMUTABLE", "accepted task output requires an authorized follow-up task")
	default:
		return p, nil, nil, Fail(409, "SESSION_BUSY", "task is not currently editable; pause and settle it first")
	}
	for _, field := range []string{"input_refs", "requirement_refs"} {
		for _, value := range Arr(task, field) {
			if err = s.Domain.effective(tx, deref(env.ProjectID), value.(map[string]any)); err != nil {
				return p, nil, nil, Fail(409, "CONTENT_CONFLICT", "task inputs changed; revalidate the task before saving")
			}
		}
	}
	// Other sessions sharing this authorized root must also be settled. Holding
	// the command transaction prevents the scheduler from starting a new run
	// between this gate and file publication.
	rows, err := tx.QueryContext(ctx, `SELECT DISTINCT r.id,r.body,w.body FROM client_sessions c JOIN domain_objects r ON r.project=c.project_id AND r.kind='Run' AND r.id=c.run_id JOIN domain_objects w ON w.project='' AND w.kind='WorkspaceBinding' AND w.id=c.workspace_ref`)
	if err != nil {
		return p, nil, nil, err
	}
	type runRow struct {
		id   string
		body Object
	}
	var runs []runRow
	for rows.Next() {
		var id, raw, bindingRaw string
		if err = rows.Scan(&id, &raw, &bindingRaw); err != nil {
			break
		}
		var other *WorkspaceBinding
		other, err = decodeBinding(bindingRaw)
		if err != nil {
			break
		}
		if !strings.EqualFold(filepath.Clean(other.RealPath), filepath.Clean(b.RealPath)) {
			continue
		}
		var run Object
		run, err = Decode([]byte(raw))
		if err != nil {
			break
		}
		runs = append(runs, runRow{id, run})
	}
	if err == nil {
		err = rows.Err()
	}
	rows.Close()
	if err != nil {
		return p, nil, nil, err
	}
	for _, run := range runs {
		if !runTerminal(run.body) || run.body["children_stopped"] != true || run.body["queue_empty"] != true || effectsReconciled(tx, Str(run.body, "project_id"), run.id) != nil {
			return p, nil, nil, Fail(409, "SESSION_BUSY", "workspace runtime must be stopped and reconciled before manual editing")
		}
	}
	authority, ok := s.SessionRuntime.(ClientWorkspaceWriteAuthority)
	if !ok {
		return p, nil, nil, Fail(503, "HOST_UNAVAILABLE", "current task write authority unavailable")
	}
	if err = authority.AuthorizeWorkspaceWrite(ctx, tx, principal, deref(env.ProjectID), deref(env.SessionID), task, Str(payload, "relative_path"), len([]byte(Str(payload, "text")))); err != nil {
		return p, nil, nil, err
	}
	return p, b, task, nil
}

func (s *ClientService) writeClientWorkspace(ctx context.Context, tx *sql.Tx, env *Envelope, principal string, sess *clientSessionRow) (*Response, error) {
	writer, ok := s.WorkspaceFiles.(ClientWorkspaceWriter)
	if !ok {
		return NewTypedRejection(env, "HOST_UNAVAILABLE", "shared workspace writer unavailable"), nil
	}
	payload, err := Decode(env.Payload)
	if err != nil {
		return nil, err
	}
	p, b, task, err := s.clientWorkspaceWriteScope(ctx, tx, env, principal, payload)
	if err != nil {
		return clientFault(env, err)
	}
	// Verify the existing projection before any irreversible OS publication.
	if _, err = BuildSessionSnapshot(ctx, tx, s.Doc, sess.project, sess.sessionID); err != nil {
		return nil, err
	}
	var expected *string
	if v, ok := payload["expected_content_hash"].(string); ok {
		expected = &v
	}
	raw := []byte(Str(payload, "text"))
	request := ClientWorkspaceWriteInput{WorkspacePath: b.RealPath, Access: b.Access, RelativePath: Str(payload, "relative_path"),
		IntentKey: "client-workspace/" + Hash(Object{"principal": principal, "project": sess.project, "session": sess.sessionID, "command": deref(env.CommandID)}),
		ScopeHash: Hash(env), ExpectedHash: expected, CreateIfMissing: payload["create_if_missing"] == true, Content: raw}
	request.Revalidate = func(checkCtx context.Context) error {
		_, current, currentTask, e := s.clientWorkspaceWriteScope(checkCtx, tx, env, principal, payload)
		if e != nil {
			return e
		}
		if current.Revision != b.Revision || current.RealPath != b.RealPath || Hash(Ref(currentTask, "Task")) != Hash(Ref(task, "Task")) {
			return Fail(409, "CONTENT_CONFLICT", "workspace or task changed before publication")
		}
		return nil
	}
	proof, err := writer.WorkspaceWrite(ctx, request)
	if err != nil {
		return clientFault(env, workspaceFileFault(err))
	}
	if proof.AfterHash != Digest(raw) {
		return NewTypedRejection(env, "EXTERNAL_WRITE_RACE", "workspace publication proof differs from the candidate; retain the draft"), nil
	}
	artifact, err := s.sealWorkspaceContent(tx, p, sess.project, raw, "SOURCE_SNAPSHOT", "text/plain; charset=utf-8")
	if err != nil {
		return nil, err
	} // rollback SQL; same command recovers the durable physical intent
	ev := &SessionEvent{EventID: strptr(ID()), SessionID: env.SessionID, Sequence: revPtr(sess.watermark + 1), CoreBuildID: strptr(s.Host.CoreBuildID), ProtocolVersion: strptr(ProtocolV2), Kind: strptr("ARTIFACT"), CommandID: env.CommandID,
		Payload: Bytes(Object{"artifact_ref": Ref(artifact, "Artifact"), "availability": "AVAILABLE"})}
	if err = AppendSessionEvent(ctx, tx, s.Doc, sess.project, ev, sess.epoch, sess.revision); err != nil {
		return nil, err
	}
	snapshot, err := BuildSessionSnapshot(ctx, tx, s.Doc, sess.project, sess.sessionID)
	if err != nil {
		return nil, err
	}
	var before any
	if proof.BeforeHash != nil {
		before = *proof.BeforeHash
	}
	return &Response{ProtocolVersion: strptr(ProtocolV2), CommandID: env.CommandID, Method: env.Method, Status: strptr("COMPLETED"), SessionID: env.SessionID, Revision: revPtr(sess.revision + 1),
		Result: Object{"workspace_ref": b.AuthorizedRef, "relative_path": request.RelativePath, "task_id": task["id"], "before_hash": before, "after_hash": proof.AfterHash, "draft_artifact_ref": Ref(artifact, "Artifact"), "snapshot": snapshot}}, nil
}
