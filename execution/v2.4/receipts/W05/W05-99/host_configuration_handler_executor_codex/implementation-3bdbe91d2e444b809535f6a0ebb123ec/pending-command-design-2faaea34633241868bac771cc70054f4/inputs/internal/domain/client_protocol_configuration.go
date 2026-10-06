package domain

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"net"
	"net/url"
	"strconv"
	"strings"
	"time"
	"unicode"
)

// Supplied only by host composition. Database authorization belongs to the
// caller's transaction. The port returns metadata, never credential material.
type ClientConfigurationAuthority interface {
	ConfigurationMetadata(context.Context, string, string, *string) (ClientConfigurationMetadata, error)
}
type ClientConfigurationMetadata struct {
	OwnerHost, Principal string
	Credential           *ClientCredentialMetadata
}
type ClientCredentialMetadata struct {
	Ref, Provider, Kind, Status string
	CheckedAt                   string
}

func validateClientConfigurationScope(env *Envelope) error {
	if env.ProjectID == nil && env.SessionID == nil && env.ExpectedRevision == nil && env.WriterEpoch == nil {
		return nil
	}
	if env.ProjectID == nil || env.SessionID == nil || deref(env.ProjectID) == "" || deref(env.SessionID) == "" || env.ExpectedRevision == nil || env.WriterEpoch == nil || *env.ExpectedRevision < 1 || *env.ExpectedRevision > clientConfigurationMaxRevision || *env.WriterEpoch < 1 || *env.WriterEpoch > clientConfigurationMaxRevision {
		return fmt.Errorf("INVALID_REQUEST:configuration scope requires four nulls or a complete session writer")
	}
	return nil
}

func clientConfigurationEndpoint(base string) (string, error) {
	bad := func() (string, error) { return "", fmt.Errorf("CONFIGURATION_ENDPOINT") }
	if !strings.HasPrefix(base, "https://") || strings.ContainsAny(base, "?#\\") || strings.ContainsFunc(base, func(r rune) bool { return unicode.IsControl(r) || unicode.IsSpace(r) }) {
		return bad()
	}
	u, e := url.Parse(base)
	if e != nil || !u.IsAbs() || u.Scheme != "https" || u.Opaque != "" || u.Host == "" || u.Hostname() == "" || u.User != nil || u.RawPath != "" || strings.Contains(u.Path, "%") || strings.Contains(u.Host, "%") {
		return bad()
	}
	for _, r := range u.Host {
		if r > 127 {
			return bad()
		}
	}
	if strings.HasPrefix(u.Host, "[") {
		end := strings.IndexByte(u.Host, ']')
		if end < 0 || net.ParseIP(u.Host[1:end]) == nil {
			return bad()
		}
		if end+1 < len(u.Host) && u.Host[end+1] != ':' {
			return bad()
		}
	} else if strings.Count(u.Host, ":") > 1 || strings.ContainsAny(u.Host, "[]") {
		return bad()
	}
	port := u.Port()
	if strings.HasSuffix(u.Host, ":") {
		return bad()
	}
	if port != "" {
		for _, r := range port {
			if r < '0' || r > '9' {
				return bad()
			}
		}
		n, e := strconv.Atoi(port)
		if e != nil || n < 1 || n > 65535 {
			return bad()
		}
	}
	if strings.Contains(u.Path, "//") {
		return bad()
	}
	for _, segment := range strings.Split(u.Path, "/") {
		if segment == "." || segment == ".." {
			return bad()
		}
	}
	if strings.HasSuffix(strings.ToLower(strings.TrimSuffix(u.Path, "/")), "/chat/completions") {
		return bad()
	}
	return strings.TrimSuffix(base, "/") + "/chat/completions", nil
}

func (s *ClientService) configurationOwner(ctx context.Context, tx *sql.Tx, principal string) (string, error) {
	p, e := clientAuthenticatedPrincipal(ctx, tx, principal)
	if e != nil {
		return "", e
	}
	if !p.HasRole("OWNER") {
		return "", Fail(403, "FORBIDDEN", "configuration requires the current Owner")
	}
	if s.ConfigurationAuthority == nil {
		return "", Fail(503, "HOST_UNAVAILABLE", "host configuration authority unavailable")
	}
	m, e := s.ConfigurationAuthority.ConfigurationMetadata(ctx, principal, "", nil)
	if e != nil {
		return "", e
	}
	if m.Principal != principal || validateClientConfigurationOwner(m.OwnerHost, principal) != nil {
		return "", Fail(403, "FORBIDDEN", "configuration host identity differs")
	}
	return m.OwnerHost, nil
}

func (s *ClientService) configureClientHost(ctx context.Context, tx *sql.Tx, env *Envelope, principal string, sess *clientSessionRow) (*Response, error) {
	if e := validateClientConfigurationScope(env); e != nil {
		return NewTypedRejection(env, "INVALID_REQUEST", "invalid configuration scope"), nil
	}
	owner, e := s.configurationOwner(ctx, tx, principal)
	if e != nil {
		return clientFault(env, e)
	}
	p, _, e := parseClientConfiguration(s.Doc, env.Payload)
	if e != nil {
		return NewTypedRejection(env, "INVALID_REQUEST", "invalid configuration payload"), nil
	}
	if _, e = clientConfigurationEndpoint(p.BaseURL); e != nil {
		return NewTypedRejection(env, "INVALID_REQUEST", "invalid provider base URL"), nil
	}
	if p.Credential != nil {
		m, e := s.ConfigurationAuthority.ConfigurationMetadata(ctx, principal, p.Provider, p.Credential)
		if e != nil {
			return clientFault(env, e)
		}
		if m.OwnerHost != owner || m.Principal != principal || m.Credential == nil || m.Credential.Ref != *p.Credential || m.Credential.Provider != p.Provider || (m.Credential.Kind != "API_KEY" && m.Credential.Kind != "OAUTH_TOKEN") {
			return NewTypedRejection(env, "CREDENTIAL_MISSING", "credential metadata does not match this host and provider"), nil
		}
		if m.Credential.Status != "AVAILABLE" {
			code := "CREDENTIAL_MISSING"
			if m.Credential.Status == "REVOKED" {
				code = "CREDENTIAL_REVOKED"
			}
			return NewTypedRejection(env, code, "credential is unavailable"), nil
		}
	}
	if env.SessionID != nil {
		if sess == nil {
			return NewTypedRejection(env, "NOT_FOUND", "session unavailable"), nil
		}
		if _, e = clientPrincipal(ctx, tx, principal, sess.project, true); e != nil {
			return clientFault(env, e)
		}
		if e = s.validateSessionConfiguration(ctx, tx, principal, sess, true); e != nil {
			return clientFault(env, e)
		}
		if e = s.configurationSettled(ctx, tx, env, principal, sess); e != nil {
			return clientFault(env, e)
		}
	}
	r, e := stageScopedClientConfiguration(ctx, tx, s.Doc, owner, principal, env.originalRaw, env)
	if e != nil {
		return clientFault(env, e)
	}
	var revision *int64
	if sess != nil {
		result, e := tx.ExecContext(ctx, `UPDATE client_sessions SET model_config_ref=?,revision=revision+1,updated_at=? WHERE id=? AND project_id=? AND revision=? AND writer_epoch=? AND writer_client_id=? AND sealed_at IS NULL AND archived_at IS NULL`, r.Ref, Now(), sess.sessionID, sess.project, sess.revision, sess.epoch, deref(env.ClientID))
		if e != nil {
			return nil, e
		}
		n, e := result.RowsAffected()
		if e != nil {
			return nil, e
		}
		if n != 1 {
			return NewTypedRejection(env, "VERSION_CONFLICT", "session changed while saving configuration"), nil
		}
		revision = revPtr(sess.revision + 1)
	}
	return &Response{ProtocolVersion: strptr(ProtocolV2), CommandID: env.CommandID, Method: env.Method, Status: strptr("COMPLETED"), SessionID: env.SessionID, Revision: revision, Result: clientConfigurationProjection(r)}, nil
}

func (s *ClientService) clientConfigurationStatus(ctx context.Context, tx *sql.Tx, principal string) (int64, []any, []any, error) {
	owner, e := s.configurationOwner(ctx, tx, principal)
	if e != nil {
		return 0, nil, nil, e
	}
	head, e := readClientConfigurationHead(ctx, tx, s.Doc, owner, principal)
	if e != nil {
		return 0, nil, nil, e
	}
	rows, e := tx.QueryContext(ctx, `SELECT model_config_ref FROM host_model_configurations WHERE owner_host_ref=? AND principal=? ORDER BY config_revision DESC,model_config_ref`, owner, principal)
	if e != nil {
		return 0, nil, nil, e
	}
	refs := []string{}
	for rows.Next() {
		var r string
		if e = rows.Scan(&r); e != nil {
			rows.Close()
			return 0, nil, nil, e
		}
		refs = append(refs, r)
	}
	e = rows.Err()
	rows.Close()
	if e != nil {
		return 0, nil, nil, e
	}
	all := make(map[string]clientConfigurationRecord, len(refs))
	for _, ref := range refs {
		r, e := readClientConfiguration(ctx, tx, s.Doc, owner, principal, ref)
		if e != nil {
			return 0, nil, nil, e
		}
		all[ref] = r
	}
	selected := []string{}
	if head.Ref != "" {
		selected = append(selected, head.Ref)
	}
	for _, ref := range refs {
		if ref != head.Ref && len(selected) < 100 {
			selected = append(selected, ref)
		}
	}
	configs, creds := Empty(), Empty()
	seen := map[string]bool{}
	for _, ref := range selected {
		r := all[ref]
		configs = append(configs, clientConfigurationProjection(r))
		if r.Payload.Credential == nil || seen[*r.Payload.Credential] {
			continue
		}
		seen[*r.Payload.Credential] = true
		m, e := s.ConfigurationAuthority.ConfigurationMetadata(ctx, principal, r.Payload.Provider, r.Payload.Credential)
		if e != nil {
			return 0, nil, nil, e
		}
		if m.Principal != principal || m.OwnerHost != owner || m.Credential == nil || m.Credential.Ref != *r.Payload.Credential || m.Credential.Provider != r.Payload.Provider {
			return 0, nil, nil, Fail(403, "FORBIDDEN", "credential metadata scope differs")
		}
		var checked any
		if m.Credential.CheckedAt != "" {
			checked = m.Credential.CheckedAt
		}
		creds = append(creds, Object{"credential_ref": m.Credential.Ref, "provider_id": m.Credential.Provider, "status": m.Credential.Status, "last_checked_at": checked})
	}
	return head.Revision, configs, creds, nil
}

func (s *ClientService) visibleClientConfiguration(ctx context.Context, tx *sql.Tx, principal, ref string) (clientConfigurationRecord, error) {
	owner, e := s.configurationOwner(ctx, tx, principal)
	if e != nil {
		return clientConfigurationRecord{}, e
	}
	r, e := readClientConfiguration(ctx, tx, s.Doc, owner, principal, ref)
	if e != nil {
		return r, Fail(503, "MODEL_UNAVAILABLE", "configuration provenance unavailable")
	}
	return r, nil
}

// Resolve the original creation, then only successful scoped configuration
// receipts for THIS session. Current head, naming patterns and other sessions
// are never sources of historical authority.
func (s *ClientService) validateSessionConfiguration(ctx context.Context, tx *sql.Tx, principal string, sess *clientSessionRow, rebind bool) error {
	owner, e := clientSessionCreationPrincipal(ctx, tx, sess.project, sess.sessionID)
	if e != nil || owner != principal {
		return Fail(503, "MODEL_UNAVAILABLE", "original session creation unavailable")
	}
	var model, workspace string
	if e = tx.QueryRowContext(ctx, `SELECT COALESCE(model_config_ref,''),COALESCE(workspace_ref,'') FROM client_sessions WHERE id=? AND project_id=?`, sess.sessionID, sess.project).Scan(&model, &workspace); e != nil {
		return e
	}
	if s.Domain == nil {
		return Fail(503, "HOST_UNAVAILABLE", "domain service unavailable")
	}
	b, e := s.Domain.binding(ctx, tx, workspace)
	if e != nil || b.ProjectID == nil || *b.ProjectID != sess.project || b.PrincipalID != principal || b.Status != WorkspaceActive {
		return Fail(403, "WORKSPACE_REVOKED", "session workspace is unavailable")
	}
	rows, e := tx.QueryContext(ctx, `SELECT key,request_hash,body,headers FROM idempotency WHERE principal=? AND project=? AND (operation='v2:session.create' OR operation='v2:goal.start' OR operation='v2:host.configure')`, principal, sess.project)
	if e != nil {
		return e
	}
	type receipt struct{ key, hash, body, headers string }
	rs := []receipt{}
	for rows.Next() {
		var r receipt
		if e = rows.Scan(&r.key, &r.hash, &r.body, &r.headers); e != nil {
			rows.Close()
			return e
		}
		rs = append(rs, r)
	}
	e = rows.Err()
	rows.Close()
	if e != nil {
		return e
	}
	creation := false
	typed := false
	bound := ""
	bindingRevision := int64(0)
	for _, r := range rs {
		var response Response
		if json.Unmarshal([]byte(r.body), &response) != nil {
			return Fail(503, "MODEL_UNAVAILABLE", "original session response corrupt")
		}
		if deref(response.Status) != "COMPLETED" {
			continue
		}
		method := deref(response.Method)
		sid := deref(response.SessionID)
		revision := int64(0)
		ref := ""
		isCreation := false
		if method == "session.create" && Str(response.Result, "session_id") == sess.sessionID {
			isCreation = true
			revision = 1
			ref = Str(response.Result, "model_config_ref")
		}
		if method == "goal.start" && response.SessionID == nil {
			snap, _ := response.Result["snapshot"].(map[string]any)
			if Str(snap, "session_id") == sess.sessionID {
				isCreation = true
				revision, _ = Num(snap, "revision")
				ref = Str(snap, "model_config_ref")
			}
		}
		if method == "host.configure" && sid == sess.sessionID {
			if response.Revision == nil {
				return Fail(503, "MODEL_UNAVAILABLE", "configuration revision missing")
			}
			revision = *response.Revision
			ref = Str(response.Result, "model_config_ref")
		}
		if ref == "" {
			continue
		}
		if isCreation {
			creation = true
		}
		req, known, e := readClientCommandEnvelope(s.Doc, r.headers)
		if e != nil {
			return e
		}
		if known {
			if req.hash != r.hash || deref(req.env.CommandID) != r.key || deref(req.env.ProjectID) != sess.project || deref(req.env.Method) != method {
				return Fail(503, "MODEL_UNAVAILABLE", "original session request differs")
			}
			var n int
			if e = tx.QueryRowContext(ctx, `SELECT count(*) FROM client_command_identities WHERE principal=? AND command_id=? AND request_hash=? AND project=? AND method=?`, principal, r.key, r.hash, sess.project, method).Scan(&n); e != nil || n != 1 {
				return Fail(503, "MODEL_UNAVAILABLE", "original session identity missing")
			}
			if _, e = decodeClientIdentityResponse(s.Doc, req, []byte(r.body)); e != nil {
				return e
			}
			if method == "session.create" {
				var payload map[string]any
				if json.Unmarshal(req.env.Payload, &payload) != nil || Str(payload, "model_config_ref") != ref {
					return Fail(503, "MODEL_UNAVAILABLE", "creation configuration differs")
				}
			}
		}
		var count int
		if e = tx.QueryRowContext(ctx, `SELECT (SELECT count(*) FROM host_model_configurations WHERE model_config_ref=?)+(SELECT count(*) FROM idempotency WHERE operation='v2:host.configure' AND json_extract(body,'$.status')='COMPLETED' AND json_extract(body,'$.result.model_config_ref')=?)`, ref, ref).Scan(&count); e != nil {
			return e
		}
		if method == "host.configure" || count > 0 {
			if !known {
				return Fail(503, "MODEL_UNAVAILABLE", "typed session original request unavailable")
			}
			record, e := s.visibleClientConfiguration(ctx, tx, principal, ref)
			if e != nil {
				return e
			}
			if method == "host.configure" && (record.CommandID != r.key || req.env.SessionID == nil || *req.env.SessionID != sess.sessionID || req.env.ExpectedRevision == nil || *req.env.ExpectedRevision+1 != revision) {
				return Fail(503, "MODEL_UNAVAILABLE", "scoped configuration differs")
			}
			typed = true
		}
		if revision > bindingRevision {
			bindingRevision = revision
			bound = ref
		} else if revision == bindingRevision && bound != ref {
			return Fail(503, "MODEL_UNAVAILABLE", "session binding history ambiguous")
		}
	}
	if !creation || bound != model {
		return Fail(503, "MODEL_UNAVAILABLE", "session differs from original binding history")
	}
	if typed {
		_, e = s.visibleClientConfiguration(ctx, tx, principal, model)
		return e
	}
	if rebind {
		return nil
	}
	if verifier, ok := s.SessionRuntime.(interface {
		ValidateLegacySession(context.Context, *sql.Tx, string, string, string, string) error
	}); ok {
		return verifier.ValidateLegacySession(ctx, tx, principal, sess.project, sess.sessionID, model)
	}
	return Fail(503, "MODEL_UNAVAILABLE", "original legacy profile provenance unavailable")
}

func (s *ClientService) configurationSettled(ctx context.Context, tx *sql.Tx, env *Envelope, principal string, sess *clientSessionRow) error {
	var lease string
	if e := tx.QueryRowContext(ctx, `SELECT COALESCE(lease_expires_at,'') FROM client_sessions WHERE id=?`, sess.sessionID).Scan(&lease); e != nil {
		return e
	}
	until, e := time.Parse(time.RFC3339Nano, lease)
	if e != nil || !until.After(time.Now()) {
		return Fail(409, "LEASE_EXPIRED", "writer lease expired")
	}
	rows, e := tx.QueryContext(ctx, `SELECT DISTINCT t.body FROM domain_objects t WHERE t.project=? AND t.kind='Task' AND (t.id=(SELECT task_id FROM client_sessions WHERE id=?) OR t.id IN(SELECT json_extract(body,'$.result.task_id') FROM idempotency WHERE project=? AND json_extract(body,'$.session_id')=? AND json_extract(body,'$.status')='COMPLETED') OR t.id IN(SELECT task_id FROM client_queue_fences WHERE project=? AND session_id=?))`, sess.project, sess.sessionID, sess.project, sess.sessionID, sess.project, sess.sessionID)
	if e != nil {
		return e
	}
	tasks := []Object{}
	for rows.Next() {
		var raw string
		if e = rows.Scan(&raw); e != nil {
			rows.Close()
			return e
		}
		task, e := Decode([]byte(raw))
		if e != nil {
			rows.Close()
			return e
		}
		tasks = append(tasks, task)
	}
	e = rows.Err()
	rows.Close()
	if e != nil {
		return e
	}
	for _, task := range tasks {
		if !clientTurnSettled(tx, sess.project, sess.sessionID, task) {
			return Fail(409, "SESSION_BUSY", "session task is not settled")
		}
	}
	var pending int
	e = tx.QueryRowContext(ctx, `SELECT (SELECT count(*) FROM client_command_queue WHERE project=? AND session_id=? AND state NOT IN('CONSUMED','DROPPED'))+(SELECT count(*) FROM client_control_requests WHERE project=? AND session_id=? AND state<>'CONFIRMED')+(SELECT count(*) FROM client_queue_fences WHERE project=? AND session_id=? AND (restore_fenced<>0 OR state='RECONCILING'))`, sess.project, sess.sessionID, sess.project, sess.sessionID, sess.project, sess.sessionID).Scan(&pending)
	if e != nil {
		return e
	}
	if pending != 0 {
		return Fail(409, "SESSION_BUSY", "session controls remain unresolved")
	}
	// Permission facts are related to the original Session even after its head
	// Task/Run has advanced; inspect the complete relation, not just the head.
	e = tx.QueryRowContext(ctx, `SELECT count(*) FROM resource_effects x JOIN domain_objects r ON r.project=x.project AND r.kind='ResourceRequest' AND r.id=json_extract(x.body,'$.permission.request_id') WHERE x.project=? AND json_extract(x.body,'$.permission.session_id')=? AND json_extract(r.body,'$.status') IN('OPEN','ACKNOWLEDGED')`, sess.project, sess.sessionID).Scan(&pending)
	if e != nil {
		return e
	}
	if pending > 0 {
		return Fail(409, "SESSION_BUSY", "session permission remains unresolved")
	}
	return nil
}
