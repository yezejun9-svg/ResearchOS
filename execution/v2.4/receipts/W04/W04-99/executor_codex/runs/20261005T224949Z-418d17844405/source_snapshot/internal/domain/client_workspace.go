package domain

import (
	"context"
	"database/sql"
	"errors"
	"io/fs"
	"mime"
	"net/http"
	"path"
	"strings"
	"time"
)

// ClientWorkspaceFiles receives only paths from the domain's current binding.
// The native host independently checks its pinned OS root on every operation.
type ClientWorkspaceFiles interface {
	WorkspaceTree(context.Context, string, string, Object) (Object, error)
	WorkspaceRead(context.Context, string, string, Object) (Object, error)
	WorkspaceDiff(context.Context, string, string, Object) (Object, []byte, error)
	WorkspaceContent(context.Context, string, string, string, int64) ([]byte, error)
}

func workspaceFileFault(err error) error {
	if err == nil {
		return nil
	}
	var fault *Fault
	if errors.As(err, &fault) {
		return err
	}
	if errors.Is(err, fs.ErrNotExist) {
		return Fail(404, "NOT_FOUND", "workspace file unavailable")
	}
	if errors.Is(err, fs.ErrPermission) {
		return Fail(403, "FORBIDDEN", "workspace file access denied")
	}
	code, _, _ := strings.Cut(err.Error(), ":")
	if _, known := recoveryByCode[code]; known {
		return Fail(409, code, err.Error())
	}
	if code == "GIT_UNAVAILABLE" {
		return Fail(503, "HOST_UNAVAILABLE", "local Git unavailable")
	}
	return Fail(503, "HOST_UNAVAILABLE", "workspace operation could not be completed")
}

func (s *ClientService) clientWorkspaceBinding(ctx context.Context, tx *sql.Tx, env *Envelope, principal, ref string, owner bool) (Principal, *WorkspaceBinding, error) {
	if s.Domain == nil || s.WorkspaceAuthority == nil || s.WorkspaceFiles == nil {
		return Principal{}, nil, Fail(503, "HOST_UNAVAILABLE", "trusted workspace file host unavailable")
	}
	p, err := clientPrincipal(ctx, tx, principal, deref(env.ProjectID), owner)
	if err != nil {
		return p, nil, err
	}
	// Files are local OS-authorized data. A project/device grant alone does not
	// give a remote connection permission to browse this machine's workspace.
	if p.DeviceID != "" {
		return p, nil, Fail(403, "FORBIDDEN", "local workspace authority required")
	}
	b, err := s.Domain.binding(ctx, tx, ref)
	if err != nil {
		return p, nil, err
	}
	if b.PrincipalID != principal || b.ProjectID == nil || *b.ProjectID != deref(env.ProjectID) {
		return p, nil, Fail(403, "FORBIDDEN", "workspace is not bound to this principal and project")
	}
	if b.Status != WorkspaceActive {
		return p, nil, Fail(403, "WORKSPACE_REVOKED", "workspace binding revoked")
	}
	if deref(env.SessionID) != "" {
		var sessionWorkspace sql.NullString
		err = tx.QueryRowContext(ctx, "SELECT workspace_ref FROM client_sessions WHERE id=? AND project_id=?", deref(env.SessionID), deref(env.ProjectID)).Scan(&sessionWorkspace)
		if errors.Is(err, sql.ErrNoRows) {
			return p, nil, Fail(404, "NOT_FOUND", "session unavailable")
		}
		if err != nil {
			return p, nil, err
		}
		if !sessionWorkspace.Valid || sessionWorkspace.String != b.AuthorizedRef {
			return p, nil, Fail(403, "FORBIDDEN", "workspace differs from the session binding")
		}
		if owner {
			var lease sql.NullString
			if err = tx.QueryRowContext(ctx, "SELECT lease_expires_at FROM client_sessions WHERE id=?", deref(env.SessionID)).Scan(&lease); err != nil {
				return p, nil, err
			}
			expires, parseErr := time.Parse(time.RFC3339Nano, lease.String)
			if parseErr != nil || !expires.After(time.Now()) {
				return p, nil, Fail(409, "LEASE_EXPIRED", "writer lease expired; acquire a current lease")
			}
		}
	}
	if err = s.WorkspaceAuthority.ConfirmPath(ctx, b.RealPath, b.Access); err != nil {
		return p, nil, typedFromAuthority(err)
	}
	return p, b, nil
}

func (s *ClientService) readClientWorkspace(ctx context.Context, tx *sql.Tx, env *Envelope, principal string) (*Response, error) {
	payload, err := Decode(env.Payload)
	if err != nil {
		return nil, err
	}
	p, binding, err := s.clientWorkspaceBinding(ctx, tx, env, principal, Str(payload, "workspace_ref"), false)
	if err != nil {
		return clientFault(env, err)
	}
	var result Object
	switch deref(env.Method) {
	case "workspace.tree":
		result, err = s.WorkspaceFiles.WorkspaceTree(ctx, binding.RealPath, binding.Access, payload)
		if err == nil {
			result["root_revision"] = binding.Revision
		}
	case "workspace.read":
		result, err = s.WorkspaceFiles.WorkspaceRead(ctx, binding.RealPath, binding.Access, payload)
	case "workspace.diff":
		var full []byte
		result, full, err = s.WorkspaceFiles.WorkspaceDiff(ctx, binding.RealPath, binding.Access, payload)
		if err == nil && result["truncated"] == true {
			var artifact Object
			artifact, err = s.sealWorkspaceContent(tx, p, deref(env.ProjectID), full, "REPORT", "text/x-diff; charset=utf-8")
			if err == nil {
				result["full_diff_artifact_ref"] = Ref(artifact, "Artifact")
			}
		}
	}
	if err != nil {
		return clientFault(env, workspaceFileFault(err))
	}
	revision := binding.Revision
	if deref(env.SessionID) != "" {
		if err = tx.QueryRowContext(ctx, "SELECT revision FROM client_sessions WHERE id=? AND project_id=?", deref(env.SessionID), deref(env.ProjectID)).Scan(&revision); err != nil {
			return nil, err
		}
	}
	return &Response{ProtocolVersion: strptr(ProtocolV2), CommandID: env.CommandID, Method: env.Method,
		Status: strptr("COMPLETED"), SessionID: env.SessionID, Revision: revPtr(revision), Result: result}, nil
}

func (s *ClientService) sealWorkspaceContent(tx *sql.Tx, p Principal, project string, raw []byte, kind, media string) (Object, error) {
	upload, err := s.Domain.upload(tx, p, project, raw)
	if err != nil {
		return nil, err
	}
	return s.Domain.seal(tx, p, project, Object{"run_id": nil, "kind": kind, "evidence_kind": "OBSERVED", "measurement_mode": "LIVE",
		"storage_key": upload["storage_key"], "content_hash": upload["content_hash"], "byte_size": len(raw), "media_type": media,
		"input_refs": Empty(), "source_refs": Empty(), "produced_by": p.ID, "access_class": "PROJECT"})
}

func (s *ClientService) importClientArtifact(ctx context.Context, tx *sql.Tx, env *Envelope, principal string, sess *clientSessionRow) (*Response, error) {
	payload, err := Decode(env.Payload)
	if err != nil {
		return nil, err
	}
	p, binding, err := s.clientWorkspaceBinding(ctx, tx, env, principal, Str(payload, "workspace_ref"), true)
	if err != nil {
		return clientFault(env, err)
	}
	raw, err := s.WorkspaceFiles.WorkspaceContent(ctx, binding.RealPath, binding.Access, Str(payload, "relative_path"), 64<<20)
	if err != nil {
		return clientFault(env, workspaceFileFault(err))
	}
	if expected := Str(payload, "expected_content_hash"); expected != "" && expected != Digest(raw) {
		return NewTypedRejection(env, "CONTENT_CONFLICT", "workspace file differs from the selected content hash"), nil
	}
	media := mime.TypeByExtension(strings.ToLower(path.Ext(Str(payload, "relative_path"))))
	if media == "" {
		media = http.DetectContentType(raw)
	}
	// Both attachments and Goal contracts are sealed source material. Importing
	// them never creates execution authority or starts a model.
	artifact, err := s.sealWorkspaceContent(tx, p, sess.project, raw, "SOURCE_SNAPSHOT", media)
	if err != nil {
		return clientFault(env, err)
	}
	ev := &SessionEvent{EventID: strptr(ID()), SessionID: env.SessionID, Sequence: revPtr(sess.watermark + 1),
		CoreBuildID: strptr(s.Host.CoreBuildID), ProtocolVersion: strptr(ProtocolV2), Kind: strptr("ARTIFACT"), CommandID: env.CommandID,
		Payload: Bytes(Object{"artifact_ref": Ref(artifact, "Artifact"), "availability": "AVAILABLE"})}
	if err = AppendSessionEvent(ctx, tx, s.Doc, sess.project, ev, sess.epoch, sess.revision); err != nil {
		return nil, err
	}
	return &Response{ProtocolVersion: strptr(ProtocolV2), CommandID: env.CommandID, Method: env.Method, Status: strptr("COMPLETED"),
		SessionID: env.SessionID, Revision: revPtr(sess.revision + 1), Result: Object{"artifact_ref": Ref(artifact, "Artifact"), "byte_size": len(raw), "media_type": media}}, nil
}
