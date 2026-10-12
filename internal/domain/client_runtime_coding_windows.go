//go:build windows

package domain

import (
	"context"
	"database/sql"
	"encoding/json"
	"path"
	"strings"
	"time"
)

// RuntimeCodingIntent is private trusted-parent input. Neither the model nor a
// public V2/Native3 command can create it or broaden these exact file lists.
type RuntimeCodingIntent struct {
	ClientID         string               `json:"client_id"`
	ExpectedRevision int64                `json:"expected_revision"`
	WriterEpoch      int64                `json:"writer_epoch"`
	ConfigRevision   int64                `json:"config_revision"`
	WorkspaceRef     string               `json:"workspace_ref"`
	ReadPaths        []string             `json:"read_paths"`
	WritePaths       []string             `json:"write_paths"`
	MaxReadBytes     int64                `json:"max_read_bytes"`
	MaxWriteBytes    int64                `json:"max_write_bytes"`
	MaxToolCalls     int64                `json:"max_tool_calls"`
	MaxOutputTokens  int64                `json:"max_output_tokens"`
	Checks           []RuntimeCodingCheck `json:"checks"`
}

type RuntimeCodingCheck struct {
	ID             string   `json:"id"`
	Package        string   `json:"package"`
	TestPattern    string   `json:"test_pattern"`
	SourcePaths    []string `json:"source_paths"`
	ToolchainRoot  string   `json:"toolchain_root"`
	VendorRoot     string   `json:"vendor_root,omitempty"`
	TimeoutSeconds int64    `json:"timeout_seconds"`
	ProcessLimit   int64    `json:"process_limit"`
	MemoryMiB      int64    `json:"memory_mib"`
	MaxTextBytes   int64    `json:"max_text_bytes"`
}

type RuntimeCodingFreezer func(context.Context, WorkspaceBinding, RuntimeCodingIntent) (Object, error)

type runtimeCodingConfirmation struct {
	Schema            string              `json:"schema"`
	RequestID         string              `json:"request_id"`
	ProjectID         string              `json:"project_id"`
	SessionID         string              `json:"session_id"`
	ModelRef          string              `json:"model_config_ref"`
	Owner             string              `json:"owner"`
	OwnerRoot         string              `json:"owner_root"`
	HostID            string              `json:"host_id"`
	ParentHash        string              `json:"parent_hash"`
	SessionHash       string              `json:"session_hash"`
	ConfigurationHash string              `json:"configuration_hash"`
	WorkspaceHash     string              `json:"workspace_hash"`
	Intent            RuntimeCodingIntent `json:"intent"`
	Frozen            Object              `json:"frozen"`
	Assets            RuntimeSetupAssets  `json:"assets"`
	IssuedAt          string              `json:"issued_at"`
	ExpiresAt         string              `json:"expires_at"`
}

const runtimeCodingSchema = "researchos.explicit-workspace-coding.v1"

func runtimeCodingPath(p string) bool {
	return p != "" && p != "." && path.Clean(p) == p && !strings.HasPrefix(p, "/") && !strings.HasPrefix(p, "../") && !strings.ContainsAny(p, "\\:\x00*?[]")
}

func ValidateRuntimeCodingIntent(in RuntimeCodingIntent) error {
	bad := func() error {
		return Fail(422, "GATE_FAILED", "explicit bounded coding paths, calls and offline checks required")
	}
	if in.ClientID == "" || in.ExpectedRevision < 1 || in.WriterEpoch < 1 || in.ConfigRevision < 1 || in.WorkspaceRef == "" || in.MaxReadBytes < 1 || in.MaxReadBytes > 64<<10 || in.MaxWriteBytes < 1 || in.MaxWriteBytes > 64<<10 || in.MaxToolCalls < 1 || in.MaxToolCalls > 32 || in.MaxOutputTokens < 1 || in.MaxOutputTokens > 8192 || len(in.ReadPaths) < 1 || len(in.ReadPaths) > 512 || len(in.WritePaths) < 1 || len(in.WritePaths) > 64 || len(in.Checks) < 1 || len(in.Checks) > 8 {
		return bad()
	}
	read, write := map[string]bool{}, map[string]bool{}
	for _, p := range in.ReadPaths {
		k := strings.ToLower(p)
		if !runtimeCodingPath(p) || read[k] {
			return bad()
		}
		read[k] = true
	}
	for _, p := range in.WritePaths {
		k := strings.ToLower(p)
		if !runtimeCodingPath(p) || write[k] || !read[k] {
			return bad()
		}
		write[k] = true
	}
	ids := map[string]bool{}
	for _, check := range in.Checks {
		if check.ID == "" || len(check.ID) > 128 || ids[check.ID] || !strings.HasPrefix(check.Package, "./") || !runtimeCodingPath(strings.TrimPrefix(check.Package, "./")) || check.TestPattern == "" || len(check.TestPattern) > 128 || len(check.SourcePaths) < 1 || len(check.SourcePaths) > 512 || check.ToolchainRoot == "" || check.TimeoutSeconds < 1 || check.TimeoutSeconds > 120 || check.ProcessLimit < 2 || check.ProcessLimit > 32 || check.MemoryMiB < 256 || check.MemoryMiB > 1024 || check.MaxTextBytes < 1 || check.MaxTextBytes > 8192 {
			return bad()
		}
		ids[check.ID] = true
		seen := map[string]bool{}
		for _, p := range check.SourcePaths {
			k := strings.ToLower(p)
			if !runtimeCodingPath(p) || seen[k] || !read[k] || k == "vendor" || strings.HasPrefix(k, "vendor/") {
				return bad()
			}
			seen[k] = true
		}
	}
	return nil
}

func (c *RuntimeCoordinator) codingBinding(ctx context.Context, tx *sql.Tx, p Principal, candidate RuntimeSetupCandidate, in RuntimeCodingIntent) (clientConfigurationRecord, WorkspaceBinding, string, error) {
	var binding WorkspaceBinding
	record, e := c.service.runtimeSetupConfiguration(ctx, tx, p, candidate, c.config.ClientSchema, c.config.ConfigurationAuthority)
	if e != nil {
		return record, binding, "", e
	}
	sess, e := loadClientSession(ctx, tx, candidate.SessionID, candidate.ProjectID)
	if e != nil || sess.revision != in.ExpectedRevision || sess.epoch != in.WriterEpoch || sess.writerClientID != in.ClientID || sess.sealed || sess.archived {
		return record, binding, "", Fail(409, "VERSION_CONFLICT", "original current session writer and revision required")
	}
	var workspace string
	if e = tx.QueryRowContext(ctx, `SELECT workspace_ref FROM client_sessions WHERE id=? AND project_id=?`, candidate.SessionID, candidate.ProjectID).Scan(&workspace); e != nil {
		return record, binding, "", e
	}
	if workspace != in.WorkspaceRef {
		return record, binding, "", Fail(403, "FORBIDDEN", "coding intent must select the current session workspace")
	}
	b, e := c.service.binding(ctx, tx, workspace)
	if e != nil {
		return record, binding, "", e
	}
	if b.PrincipalID != p.ID || b.ProjectID == nil || *b.ProjectID != candidate.ProjectID || b.Access != "READ_WRITE" || b.Status != WorkspaceActive || c.config.WorkspaceAuthority == nil {
		return record, binding, "", Fail(403, "FORBIDDEN", "current Owner READ_WRITE workspace required")
	}
	if e = c.config.WorkspaceAuthority.ConfirmPath(ctx, b.RealPath, b.Access); e != nil {
		return record, binding, "", e
	}
	client := &ClientService{Domain: c.service, Doc: c.config.ClientSchema, ConfigurationAuthority: c.config.ConfigurationAuthority}
	head, e := readClientConfigurationHead(ctx, tx, c.config.ClientSchema, record.Owner, p.ID)
	if e != nil {
		return record, binding, "", e
	}
	if in.ConfigRevision != head.Revision+1 {
		return record, binding, "", Fail(409, "CONFIG_CONFLICT", "new coding configuration must advance the current head exactly once")
	}
	env := &Envelope{ClientID: &in.ClientID, ProjectID: &candidate.ProjectID, SessionID: &candidate.SessionID, ExpectedRevision: &in.ExpectedRevision, WriterEpoch: &in.WriterEpoch}
	if e = client.configurationSettled(ctx, tx, env, p.ID, sess); e != nil {
		return record, binding, "", e
	}
	if e = localQualificationIdle(tx); e != nil {
		return record, binding, "", e
	}
	return record, *b, Hash(Object{"session": candidate.SessionID, "revision": sess.revision, "writer": sess.writerClientID, "epoch": sess.epoch, "run": sess.runID}), nil
}

func (c *RuntimeCoordinator) codingAssets(tx *sql.Tx, project, model string) (RuntimeSetupAssets, error) {
	var assets RuntimeSetupAssets
	runtime, profile, e := c.sessionModel(tx, project, model)
	if e != nil {
		return assets, e
	}
	for _, route := range c.runtimeRoutes() {
		if route.ProjectID == project && route.RuntimeID == Str(runtime, "id") {
			assets = RuntimeSetupAssets{Executable: route.Executable, BundleFile: route.BundleFile, BuildHash: Str(profile, "build_hash"), BundleHash: Str(profile, "bundle_hash")}
			return assets, checkRuntimeSetupAssets(assets)
		}
	}
	return assets, Fail(503, "MODEL_UNAVAILABLE", "original installed runtime assets unavailable")
}

func (c *RuntimeCoordinator) PrepareRuntimeCoding(ctx context.Context, token, parentHash string, candidate RuntimeSetupCandidate, in RuntimeCodingIntent, freeze RuntimeCodingFreezer) (Object, error) {
	if e := ValidateRuntimeCodingIntent(in); e != nil {
		return nil, e
	}
	if parentHash == "" || freeze == nil {
		return nil, Fail(403, "FORBIDDEN", "trusted parent and host coding freezer required")
	}
	c.scanMu.Lock()
	defer c.scanMu.Unlock()
	if c.quiesced || c.qualificationActive || c.config.ManagedStartupHold {
		return nil, Fail(409, "RESOURCE_BLOCKED", "runtime is fenced")
	}
	tx, e := c.service.DB.BeginTx(ctx, nil)
	if e != nil {
		return nil, e
	}
	p, e := authenticate(tx, token)
	if e != nil {
		tx.Rollback()
		return nil, e
	}
	record, binding, sessionHash, e := c.codingBinding(ctx, tx, p, candidate, in)
	if e != nil {
		tx.Rollback()
		return nil, e
	}
	root, e := currentAuthorityRoot(tx, p.ID)
	if e != nil {
		tx.Rollback()
		return nil, e
	}
	assets, e := c.codingAssets(tx, candidate.ProjectID, candidate.ModelRef)
	tx.Rollback()
	if e != nil {
		return nil, e
	}
	frozen, e := freeze(ctx, binding, in)
	if e != nil {
		return nil, e
	}
	now := time.Now().UTC()
	r := runtimeCodingConfirmation{Schema: runtimeCodingSchema, RequestID: ID(), ProjectID: candidate.ProjectID, SessionID: candidate.SessionID, ModelRef: candidate.ModelRef, Owner: p.ID, OwnerRoot: root, HostID: record.Owner, ParentHash: parentHash, SessionHash: sessionHash, ConfigurationHash: record.ConfigHash, WorkspaceHash: Hash(binding), Intent: in, Frozen: frozen, Assets: assets, IssuedAt: now.Format(time.RFC3339Nano), ExpiresAt: now.Add(time.Minute).Format(time.RFC3339Nano)}
	tx, e = c.service.DB.BeginTx(ctx, nil)
	if e != nil {
		return nil, e
	}
	defer tx.Rollback()
	if _, _, e = c.validateCodingConfirmation(ctx, tx, token, parentHash, r); e != nil {
		return nil, e
	}
	if _, e = tx.ExecContext(ctx, `INSERT INTO idempotency(principal,project,operation,key,request_hash,status,body,headers,created_at) VALUES(?,?,'host:coding-confirmation',?,?,200,?,'{}',?)`, p.ID, candidate.ProjectID, r.RequestID, Hash(r), Bytes(r), Now()); e != nil {
		return nil, e
	}
	if e = tx.Commit(); e != nil {
		return nil, e
	}
	return codingConfirmationProjection(r), nil
}

func codingConfirmationProjection(r runtimeCodingConfirmation) Object {
	return Object{"state": "AWAITING_CODING_CONFIRMATION", "request_id": r.RequestID, "request_hash": Hash(r), "expires_at": r.ExpiresAt, "project_id": r.ProjectID, "session_id": r.SessionID, "old_model_config_ref": r.ModelRef, "scope": r.Intent, "frozen_checks": r.Frozen["check_summaries"], "normal_max_model_calls": 8, "qualification_model_calls": 1, "qualification_tool_calls": 0, "model_calls": 0}
}

func (c *RuntimeCoordinator) validateCodingConfirmation(ctx context.Context, tx *sql.Tx, token, parentHash string, r runtimeCodingConfirmation) (Principal, WorkspaceBinding, error) {
	p, e := authenticate(tx, token)
	if e != nil {
		return p, WorkspaceBinding{}, e
	}
	bad := func() (Principal, WorkspaceBinding, error) {
		return p, WorkspaceBinding{}, Fail(412, "STALE_INPUT", "coding confirmation, original parent, Owner, session or workspace changed")
	}
	if r.Schema != runtimeCodingSchema || r.Owner != p.ID || r.ParentHash != parentHash || r.RequestID == "" {
		return bad()
	}
	root, e := currentAuthorityRoot(tx, p.ID)
	if e != nil || root != r.OwnerRoot {
		return bad()
	}
	if e = validateLocalConfirmationTime(LocalRuntimeQualificationRequest{IssuedAt: r.IssuedAt, ExpiresAt: r.ExpiresAt}); e != nil {
		return bad()
	}
	record, binding, sessionHash, e := c.codingBinding(ctx, tx, p, RuntimeSetupCandidate{ProjectID: r.ProjectID, SessionID: r.SessionID, PrincipalID: p.ID, ModelRef: r.ModelRef}, r.Intent)
	if e != nil {
		return p, binding, e
	}
	if record.Owner != r.HostID || record.ConfigHash != r.ConfigurationHash || sessionHash != r.SessionHash || Hash(binding) != r.WorkspaceHash {
		return bad()
	}
	if e = checkRuntimeSetupAssets(r.Assets); e != nil {
		return p, binding, e
	}
	return p, binding, nil
}

func (c *RuntimeCoordinator) loadCodingConfirmation(ctx context.Context, tx *sql.Tx, token, project, id, digest string) (runtimeCodingConfirmation, error) {
	var r runtimeCodingConfirmation
	p, e := resourcePrincipal(tx, token, project, "OWNER")
	if e != nil {
		return r, e
	}
	var hash, body string
	e = tx.QueryRowContext(ctx, `SELECT request_hash,body FROM idempotency WHERE principal=? AND project=? AND operation='host:coding-confirmation' AND key=?`, p.ID, project, id).Scan(&hash, &body)
	if e != nil || json.Unmarshal([]byte(body), &r) != nil || hash != digest || Hash(r) != hash || r.Owner != p.ID || r.ProjectID != project || r.RequestID != id {
		return r, Fail(412, "STALE_INPUT", "exact original coding confirmation required")
	}
	return r, nil
}

func (c *RuntimeCoordinator) ConfirmRuntimeCoding(ctx context.Context, token, parentHash, project, id, digest string, freeze RuntimeCodingFreezer) (Object, error) {
	if freeze == nil {
		return nil, Fail(403, "FORBIDDEN", "host coding freezer unavailable")
	}
	c.scanMu.Lock()
	defer c.scanMu.Unlock()
	if c.quiesced || c.qualificationActive || c.config.ManagedStartupHold {
		return nil, Fail(409, "RESOURCE_BLOCKED", "runtime is fenced")
	}
	tx, e := c.service.DB.BeginTx(ctx, nil)
	if e != nil {
		return nil, e
	}
	r, e := c.loadCodingConfirmation(ctx, tx, token, project, id, digest)
	if e != nil {
		tx.Rollback()
		return nil, e
	}
	_, binding, e := c.validateCodingConfirmation(ctx, tx, token, parentHash, r)
	tx.Rollback()
	if e != nil {
		return nil, e
	}
	current, e := freeze(ctx, binding, r.Intent)
	if e != nil {
		return nil, e
	}
	if Hash(current) != Hash(r.Frozen) {
		return nil, Fail(412, "STALE_INPUT", "coding source, toolchain or vendor changed after visible confirmation")
	}
	tx, e = c.service.DB.BeginTx(ctx, nil)
	if e != nil {
		return nil, e
	}
	defer tx.Rollback()
	p, _, e := c.validateCodingConfirmation(ctx, tx, token, parentHash, r)
	if e != nil {
		return nil, e
	}
	var consumed int
	if e = tx.QueryRowContext(ctx, `SELECT count(*) FROM idempotency WHERE principal=? AND project=? AND operation='host:coding-installation' AND key=?`, p.ID, project, id).Scan(&consumed); e != nil {
		return nil, e
	}
	if consumed != 0 {
		return nil, Fail(409, "STATE_CONFLICT", "coding confirmation already consumed; inspect original status")
	}
	client := &ClientService{Doc: c.config.ClientSchema, Domain: c.service, ConfigurationAuthority: c.config.ConfigurationAuthority, SessionRuntime: c, Host: ClientHostInfo{LeaseTTL: MaxCodingWriterTTL}}
	if e = tx.QueryRowContext(ctx, `SELECT core_build_id FROM client_sessions WHERE id=? AND project_id=?`, r.SessionID, project).Scan(&client.Host.CoreBuildID); e != nil {
		return nil, e
	}
	record, e := client.visibleClientConfiguration(ctx, tx, p.ID, r.ModelRef)
	if e != nil {
		return nil, e
	}
	payload := record.Payload
	payload.Revision = r.Intent.ConfigRevision
	env, e := DecodeEnvelope(Bytes(&Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: &r.Intent.ClientID, ProjectID: &project, SessionID: &r.SessionID, ExpectedRevision: &r.Intent.ExpectedRevision, WriterEpoch: &r.Intent.WriterEpoch, Method: strptr("host.configure"), Payload: Bytes(payload)}))
	if e != nil {
		return nil, e
	}
	response, replayed, e := client.Execute(ctx, tx, env, p.ID)
	if e != nil {
		return nil, e
	}
	if replayed || deref(response.Status) != "COMPLETED" {
		return nil, Fail(409, "STATE_CONFLICT", "original configuration CAS refused coding installation")
	}
	newRef := Str(response.Result, "model_config_ref")
	policy, ok := r.Frozen["tool_policy"].(map[string]any)
	if !ok {
		return nil, Fail(422, "GATE_FAILED", "frozen coding tool policy absent")
	}
	authorization := Object{"schema": runtimeCodingSchema, "confirmation_id": id, "confirmation_hash": digest, "owner": p.ID, "owner_root": r.OwnerRoot, "owner_host": r.HostID, "parent_hash": parentHash, "project_id": project, "session_id": r.SessionID, "workspace_ref": r.Intent.WorkspaceRef, "workspace_hash": r.WorkspaceHash, "model_config_ref": newRef, "original_model_config_ref": r.ModelRef, "configuration_command_id": deref(env.CommandID), "intent": r.Intent, "tool_policy": policy, "freeze_hash": Hash(r.Frozen)}
	if _, e = tx.ExecContext(ctx, `INSERT INTO idempotency(principal,project,operation,key,request_hash,status,body,headers,created_at) VALUES(?,?,'host:coding-authorization',?,?,200,?,'{}',?)`, p.ID, project, newRef, Hash(authorization), Bytes(authorization), Now()); e != nil {
		return nil, e
	}
	prepared, e := c.service.prepareClientRuntimeTx(ctx, tx, p, RuntimeSetupCandidate{ProjectID: project, SessionID: r.SessionID, PrincipalID: p.ID, ModelRef: newRef}, r.Assets, c.config.ClientSchema, c.config.ConfigurationAuthority)
	if e != nil {
		return nil, e
	}
	result := Object{"state": "CODING_CONFIGURED", "request_id": id, "request_hash": digest, "project_id": project, "session_id": r.SessionID, "model_config_ref": newRef, "old_model_config_ref": r.ModelRef, "runtime_id": prepared.RuntimeID, "runtime_status": "REGISTERED", "profile_ref": prepared.ProfileRef, "revision": response.Revision, "config_revision": r.Intent.ConfigRevision, "configuration_command_id": deref(env.CommandID), "scope": r.Intent, "frozen_checks": r.Frozen["check_summaries"], "normal_max_model_calls": 8, "qualification_model_calls": 1, "qualification_tool_calls": 0, "model_calls": 0}
	if _, e = tx.ExecContext(ctx, `INSERT INTO idempotency(principal,project,operation,key,request_hash,status,body,headers,created_at) VALUES(?,?,'host:coding-installation',?,?,200,?,'{}',?)`, p.ID, project, id, digest, Bytes(result), Now()); e != nil {
		return nil, e
	}
	if e = validateLocalConfirmationTime(LocalRuntimeQualificationRequest{IssuedAt: r.IssuedAt, ExpiresAt: r.ExpiresAt}); e != nil {
		return nil, e
	}
	if e = tx.Commit(); e != nil {
		return nil, e
	}
	return result, nil
}

const MaxCodingWriterTTL = time.Minute

// Status never installs a profile, changes the writer, or replays a confirmation.
func (c *RuntimeCoordinator) RuntimeCodingStatus(ctx context.Context, token, parentHash, project, id, digest string) (Object, error) {
	tx, e := c.service.DB.BeginTx(ctx, nil)
	if e != nil {
		return nil, e
	}
	defer tx.Rollback()
	r, e := c.loadCodingConfirmation(ctx, tx, token, project, id, digest)
	if e != nil {
		return nil, e
	}
	root, e := currentAuthorityRoot(tx, r.Owner)
	if e != nil || root != r.OwnerRoot || parentHash != r.ParentHash {
		return nil, Fail(403, "FORBIDDEN", "original coding Owner and parent required")
	}
	meta, e := c.config.ConfigurationAuthority.ConfigurationMetadata(ctx, r.Owner, "", nil)
	if e != nil || meta.OwnerHost != r.HostID {
		return nil, Fail(403, "FORBIDDEN", "original coding Host required")
	}
	var body, hash string
	e = tx.QueryRowContext(ctx, `SELECT body,request_hash FROM idempotency WHERE principal=? AND project=? AND operation='host:coding-installation' AND key=?`, r.Owner, project, id).Scan(&body, &hash)
	if e == sql.ErrNoRows {
		out := codingConfirmationProjection(r)
		if validateLocalConfirmationTime(LocalRuntimeQualificationRequest{IssuedAt: r.IssuedAt, ExpiresAt: r.ExpiresAt}) != nil {
			out["state"] = "EXPIRED"
		}
		return out, nil
	}
	if e != nil {
		return nil, e
	}
	if hash != digest {
		return nil, Fail(412, "STALE_INPUT", "coding installation identity changed")
	}
	return Decode([]byte(body))
}

func runtimeCodingAuthorization(ctx context.Context, tx *sql.Tx, principal, project, model string) (Object, error) {
	var raw, digest string
	e := tx.QueryRowContext(ctx, `SELECT body,request_hash FROM idempotency WHERE principal=? AND project=? AND operation='host:coding-authorization' AND key=?`, principal, project, model).Scan(&raw, &digest)
	if e == sql.ErrNoRows {
		return nil, nil
	}
	if e != nil {
		return nil, e
	}
	a, e := Decode([]byte(raw))
	if e != nil {
		return nil, e
	}
	root, e := currentAuthorityRoot(tx, principal)
	if e != nil || Hash(a) != digest || a["schema"] != runtimeCodingSchema || a["owner"] != principal || a["owner_root"] != root || a["project_id"] != project || a["model_config_ref"] != model || Str(a, "session_id") == "" || Str(a, "workspace_ref") == "" || Str(a, "confirmation_id") == "" {
		return nil, Fail(403, "FORBIDDEN", "original immutable coding authorization unavailable")
	}
	var in RuntimeCodingIntent
	if json.Unmarshal(Bytes(a["intent"]), &in) != nil || ValidateRuntimeCodingIntent(in) != nil || in.WorkspaceRef != a["workspace_ref"] {
		return nil, Fail(422, "GATE_FAILED", "coding intent differs from original scope")
	}
	policy, ok := a["tool_policy"].(map[string]any)
	if !ok || Hash(policy["read_paths"]) != Hash(in.ReadPaths) || Hash(policy["write_paths"]) != Hash(in.WritePaths) || Hash(policy["max_read_bytes"]) != Hash(in.MaxReadBytes) || Hash(policy["max_write_bytes"]) != Hash(in.MaxWriteBytes) || Hash(policy["max_calls"]) != Hash(in.MaxToolCalls) || len(Arr(policy, "checks")) != len(in.Checks) {
		return nil, Fail(422, "GATE_FAILED", "coding policy differs from explicit original limits")
	}
	return a, nil
}

func runtimeCodingTools(in RuntimeCodingIntent) []any {
	text := Object{"type": "string"}
	hash := Object{"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"}
	file := Object{"type": "string", "minLength": 1}
	function := func(name, description string, properties Object, required []any) Object {
		return Object{"type": "function", "function": Object{"name": name, "description": description, "parameters": Object{"type": "object", "properties": properties, "required": required, "additionalProperties": false}}}
	}
	checks := Empty()
	for _, check := range in.Checks {
		checks = append(checks, check.ID)
	}
	return []any{
		function("read", "Read an explicitly authorized workspace file. Use next_offset to continue a bounded read.", Object{"path": file, "offset": Object{"type": "integer", "minimum": 0}, "limit": Object{"type": "integer", "minimum": 1, "maximum": in.MaxReadBytes}}, []any{"path"}),
		function("write", "Write an explicitly authorized file with its current content hash; null creates an absent file.", Object{"path": file, "content": Object{"type": "string", "maxLength": in.MaxWriteBytes}, "expected_hash": Object{"anyOf": []any{hash, Object{"type": "null"}}}}, []any{"path", "content", "expected_hash"}),
		function("edit", "Replace exactly one old_text occurrence in an explicitly authorized file using its current content hash.", Object{"path": file, "old_text": Object{"type": "string", "minLength": 1}, "new_text": text, "expected_hash": hash}, []any{"path", "old_text", "new_text", "expected_hash"}),
		function("run_check", "Run one previously frozen offline Go check in an isolated sandbox; no command arguments are accepted.", Object{"check_id": Object{"type": "string", "enum": checks}}, []any{"check_id"}),
	}
}

func applyRuntimeCodingProfile(profile, authorization Object) error {
	var in RuntimeCodingIntent
	if json.Unmarshal(Bytes(authorization["intent"]), &in) != nil || ValidateRuntimeCodingIntent(in) != nil {
		return Fail(422, "GATE_FAILED", "explicit coding authorization malformed")
	}
	config, ok := profile["model_config"].(map[string]any)
	if !ok {
		return Fail(422, "GATE_FAILED", "coding model configuration unavailable")
	}
	config["tools"], config["max_calls"], config["max_output_tokens"] = runtimeCodingTools(in), 8, in.MaxOutputTokens
	profile["command_id"], profile["timeout_seconds"] = "mu-local-coding-v1", 900
	profile["tool_policy"], profile["coding_authorization"] = authorization["tool_policy"], authorization
	profile["effect_routes"] = append(Arr(profile, "effect_routes"), Object{"id": config["route"], "capability": "TOOL", "credential_revision": "local-tools-v1", "upper_bound": Object{"amount": "0", "currency": "USD"}})
	profile["model_qualification"] = Object{"route": config["route"], "model_config_hash": Hash(config), "max_calls": 1}
	return nil
}

func validateLocalQualificationProfile(profile Object) error {
	if e := validateRuntimeDispatchProfile(profile); e != nil {
		return e
	}
	config, _ := profile["model_config"].(map[string]any)
	calls, e := Num(config, "max_calls")
	if e != nil {
		return e
	}
	qualification, _ := profile["model_qualification"].(map[string]any)
	qCalls, e := Num(qualification, "max_calls")
	if e != nil || qCalls != 1 || qualification["route"] != config["route"] || qualification["model_config_hash"] != Hash(config) || profile["backend"] != runtimeMuBackend || profile["credential_revision"] != "none" {
		return Fail(422, "GATE_FAILED", "exact one-model-call qualification profile required")
	}
	if profile["coding_authorization"] == nil {
		if calls != 1 || len(Arr(config, "tools")) != 0 {
			return Fail(422, "GATE_FAILED", "original local model-only profile required")
		}
		return nil
	}
	a, ok := profile["coding_authorization"].(map[string]any)
	var in RuntimeCodingIntent
	if !ok || a["schema"] != runtimeCodingSchema || json.Unmarshal(Bytes(a["intent"]), &in) != nil || ValidateRuntimeCodingIntent(in) != nil || calls != 8 || Hash(config["tools"]) != Hash(runtimeCodingTools(in)) || Hash(profile["tool_policy"]) != Hash(a["tool_policy"]) || config["ref"] != a["model_config_ref"] {
		return Fail(422, "GATE_FAILED", "exact explicit coding profile with separate one-call model qualification required")
	}
	return nil
}

// Called at admission and again immediately before each host tool effect. The
// same model reference never transfers this authority to another workspace or
// session. Older model-only profiles keep their original binding semantics.
func (c *RuntimeCoordinator) validateCodingWorkspace(ctx context.Context, tx *sql.Tx, principal, project, session, workspace string, profile Object) error {
	a, ok := profile["coding_authorization"].(map[string]any)
	setup, _ := profile["host_setup"].(map[string]any)
	if !ok {
		if setup == nil {
			return nil
		}
		original, e := runtimeCodingAuthorization(ctx, tx, Str(setup, "principal"), project, Str(setup, "model_config_ref"))
		if e != nil {
			return e
		}
		if original != nil {
			return Fail(403, "FORBIDDEN", "coding profile lost original authorization")
		}
		return nil
	}
	config, _ := profile["model_config"].(map[string]any)
	original, e := runtimeCodingAuthorization(ctx, tx, principal, project, Str(config, "ref"))
	if e != nil {
		return e
	}
	if original == nil || Hash(original) != Hash(a) || a["workspace_ref"] != workspace || (session != "" && a["session_id"] != session) {
		return Fail(403, "FORBIDDEN", "coding authority belongs to the original session and workspace")
	}
	b, e := c.service.binding(ctx, tx, workspace)
	if e != nil {
		return e
	}
	if b.Access != "READ_WRITE" || b.Status != WorkspaceActive || Hash(b) != a["workspace_hash"] || c.config.WorkspaceAuthority == nil {
		return Fail(403, "WORKSPACE_REVOKED", "original coding workspace binding changed")
	}
	return c.config.WorkspaceAuthority.ConfirmPath(ctx, b.RealPath, b.Access)
}

func (c *RuntimeCoordinator) validateCodingSession(ctx context.Context, tx *sql.Tx, principal, project, session string) error {
	var model, workspace string
	if e := tx.QueryRowContext(ctx, `SELECT model_config_ref,workspace_ref FROM client_sessions WHERE id=? AND project_id=?`, session, project).Scan(&model, &workspace); e != nil {
		return e
	}
	// Preserve existing ordinary fixture/legacy behavior unless the current
	// model has the immutable explicit coding authorization.
	a, e := runtimeCodingAuthorization(ctx, tx, principal, project, model)
	if e != nil || a == nil {
		return e
	}
	_, profile, e := c.sessionModel(tx, project, model)
	if e != nil {
		return e
	}
	return c.validateCodingWorkspace(ctx, tx, principal, project, session, workspace, profile)
}
