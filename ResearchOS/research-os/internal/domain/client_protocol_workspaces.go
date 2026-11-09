package domain

import (
	"context"
	"database/sql"
)

// clientWorkspaceProjection reads only this command's authenticated principal's
// durable metadata. It deliberately uses the caller's transaction, including
// uncommitted registration/bootstrap changes, and never touches the filesystem.
func (s *ClientService) clientWorkspaceProjection(ctx context.Context, tx *sql.Tx, env *Envelope, principal string) ([]any, error) {
	p, err := clientAuthenticatedPrincipal(ctx, tx, principal)
	if err != nil {
		return nil, err
	}
	if p.DeviceID != "" {
		return nil, Fail(403, "FORBIDDEN", "local workspace metadata requires a local principal")
	}
	project := deref(env.ProjectID)
	if project != "" && !p.Allowed(project, "", "", false) {
		return nil, Fail(403, "FORBIDDEN", "current project grant required")
	}
	// CASE keeps malformed foreign JSON out of json_extract. The predicate is
	// evaluated in SQLite, before a foreign body could be read or decoded here.
	rows, err := tx.QueryContext(ctx, `SELECT id,revision,body FROM domain_objects
		WHERE project='' AND kind=? AND
		CASE WHEN json_valid(body) THEN json_extract(body,'$.principal_id') ELSE NULL END = ?
		ORDER BY id`, KindWorkspaceBinding, p.ID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	items := []any{}
	bad := func() error { return Fail(409, "RESOURCE_BLOCKED", "authorized workspace metadata is invalid") }
	for rows.Next() {
		var id, raw string
		var revision int64
		if err := rows.Scan(&id, &revision, &raw); err != nil {
			return nil, err
		}
		body, err := Decode([]byte(raw))
		if err != nil {
			return nil, bad()
		}
		// decodeBinding's compatibility defaults are intentionally insufficient
		// for a public projection: malformed own rows must not become empty or
		// silently turn a bound project into an unbound one.
		if body["principal_id"] != p.ID {
			return nil, bad()
		}
		v, hasProject := body["project_id"]
		if !hasProject {
			return nil, bad()
		}
		if v != nil {
			if text, ok := v.(string); !ok || text == "" {
				return nil, bad()
			}
		}
		binding, err := decodeBinding(raw)
		if err != nil || binding.AuthorizedRef != id || binding.PrincipalID != p.ID || binding.Revision != revision || revision < 1 {
			return nil, bad()
		}
		reply := binding.Reply()
		if s.Doc == nil || s.Doc.ValidateDef("WorkspaceBinding", reply) != nil || len(reply) != 7 {
			return nil, bad()
		}
		if binding.ProjectID != nil {
			if !p.Allowed(*binding.ProjectID, "", "", false) || project != "" && *binding.ProjectID != project {
				continue
			}
		} else if project != "" {
			continue
		}
		if len(items) == 1000 {
			return nil, Fail(409, "RESOURCE_BLOCKED", "authorized workspace list exceeds the published limit")
		}
		items = append(items, reply)
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	return items, nil
}
