package domain

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"net"
	"net/url"
	"sort"
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

// This unexported value is made only at Execute's authenticated transaction
// boundary. It describes that single dispatch, never durable creation or
// qualification. The original response remains the sole committed authority.
type pendingClientCommandKey struct{}
type pendingClientCommand struct {
	tx              *sql.Tx
	service         *ClientService
	principal, hash string
	raw             []byte
	entry           map[string]map[string]bool
}

func clientCommandMembership(ctx context.Context, tx *sql.Tx, project string) (map[string]map[string]bool, error) {
	out := map[string]map[string]bool{"Task": {}, "Goal": {}, "Requirement": {}, "Session": {}, "Artifact": {}}
	rows, e := tx.QueryContext(ctx, `SELECT kind,id FROM domain_objects WHERE project=? AND kind IN('Task','Goal','Requirement','Artifact') UNION ALL SELECT 'Session',id FROM client_sessions WHERE project_id=?`, project, project)
	if e != nil {
		return nil, e
	}
	defer rows.Close()
	for rows.Next() {
		var kind, id string
		if e = rows.Scan(&kind, &id); e != nil {
			return nil, e
		}
		out[kind][id] = true
	}
	return out, rows.Err()
}

func (s *ClientService) pendingCommandContext(ctx context.Context, tx *sql.Tx, env *Envelope, principal string) (context.Context, error) {
	if deref(env.Method) != "session.send" && deref(env.Method) != "goal.start" {
		return ctx, nil
	}
	if deref(env.ProjectID) == "" {
		return ctx, nil
	}
	req, e := validateClientIdentityRequest(s.Doc, env.originalRaw, env)
	if e != nil {
		return nil, e
	}
	entry, e := clientCommandMembership(ctx, tx, deref(env.ProjectID))
	if e != nil {
		return nil, e
	}
	return context.WithValue(ctx, pendingClientCommandKey{}, &pendingClientCommand{tx: tx, service: s, principal: principal, hash: req.hash, raw: append([]byte(nil), env.originalRaw...), entry: entry}), nil
}

func firstClientObject(tx *sql.Tx, project, kind, id string) (Object, error) {
	var raw string
	if e := tx.QueryRow(`SELECT body FROM domain_versions WHERE project=? AND kind=? AND id=? AND revision=1`, project, kind, id).Scan(&raw); e != nil {
		return nil, e
	}
	return Decode([]byte(raw))
}

func (s *ClientService) pendingClientTask(ctx context.Context, tx *sql.Tx, project, model string, task Object) (*clientSessionRow, string, error) {
	bad := func() (*clientSessionRow, string, error) {
		return nil, "", Fail(503, "MODEL_UNAVAILABLE", "original in-flight command evidence unavailable")
	}
	p, ok := ctx.Value(pendingClientCommandKey{}).(*pendingClientCommand)
	if !ok || p == nil || p.tx != tx || p.service == nil || p.service.Domain != s.Domain {
		return bad()
	}
	env, e := decodeClientIdentityEnvelope(s.Doc, p.raw)
	if e != nil {
		return bad()
	}
	req, e := validateClientIdentityRequest(s.Doc, p.raw, env)
	if e != nil || req.hash != p.hash || deref(env.ProjectID) != project {
		return bad()
	}
	owner, e := clientPrincipal(ctx, tx, p.principal, project, true)
	if e != nil {
		return bad()
	}
	var identities, journals int
	if e = tx.QueryRowContext(ctx, `SELECT count(*) FROM client_command_identities WHERE principal=? AND command_id=? AND protocol=? AND project=? AND method=? AND operation=? AND request_hash=?`, p.principal, deref(env.CommandID), ProtocolV2, project, deref(env.Method), "v2:"+deref(env.Method), p.hash).Scan(&identities); e != nil || identities != 1 {
		return bad()
	}
	if e = tx.QueryRowContext(ctx, `SELECT count(*) FROM idempotency WHERE principal=? AND key=? AND substr(operation,1,3)='v2:'`, p.principal, deref(env.CommandID)).Scan(&journals); e != nil || journals != 0 {
		return bad()
	}
	current, e := clientCommandMembership(ctx, tx, project)
	if e != nil {
		return bad()
	}
	added := map[string][]string{}
	for kind, ids := range current {
		for id := range ids {
			if !p.entry[kind][id] {
				added[kind] = append(added[kind], id)
			}
		}
	}
	if len(added["Task"]) != 1 || added["Task"][0] != Str(task, "id") || len(added["Goal"]) != 1 || added["Goal"][0] != Str(task, "goal_id") {
		return bad()
	}
	actual, e := load(tx, project, "Task", Str(task, "id"))
	if e != nil || Hash(actual) != Hash(task) {
		return bad()
	}
	first, e := firstClientObject(tx, project, "Task", Str(task, "id"))
	if e != nil || s.Domain.Contracts.Validate("Task", first) != nil {
		return bad()
	}
	for _, field := range []string{"id", "project_id", "goal_id", "title", "task_type", "stage", "dependency_task_ids", "requirement_refs", "input_refs", "acceptance_contract", "stop_policy", "no_progress_record_id", "binding"} {
		if Hash(first[field]) != Hash(task[field]) {
			return bad()
		}
	}
	goal, e := firstClientObject(tx, project, "Goal", Str(task, "goal_id"))
	if e != nil || s.Domain.Contracts.Validate("Goal", goal) != nil {
		return bad()
	}
	stop := Object{"wall_time_seconds": 900, "max_attempts": 1, "max_parallel_runs": 1, "stop_conditions": []any{"turn complete", "model or tool effect unknown", "lease or authority lost", "Owner cancellation"}}
	if first["task_type"] != "mu_turn" || first["stage"] != "delivery" || len(Arr(first, "dependency_task_ids")) != 0 || Hash(first["stop_policy"]) != Hash(stop) || Hash(first["acceptance_contract"]) != Hash(goal["acceptance_contract"]) || Hash(first["requirement_refs"]) != Hash(goal["requirement_refs"]) {
		return bad()
	}
	refs := Arr(first, "requirement_refs")
	if len(refs) != 1 {
		return bad()
	}
	ref, ok := refs[0].(map[string]any)
	if !ok || ref["entity_type"] != "Requirement" {
		return bad()
	}
	requirement, e := version(tx, project, ref)
	if e != nil || requirement["status"] != "ACCEPTED" {
		return bad()
	}
	originalRequirement, e := firstClientObject(tx, project, "Requirement", Str(requirement, "id"))
	if e != nil || s.Domain.Contracts.Validate("Requirement", originalRequirement) != nil {
		return bad()
	}
	progress, e := firstClientObject(tx, project, "NoProgressRecord", Str(first, "no_progress_record_id"))
	if e != nil || s.Domain.Contracts.Validate("NoProgressRecord", progress) != nil {
		return bad()
	}
	if progress["input_hash"] != Hash(first["input_refs"]) || progress["key_hash"] != Hash([]any{progress["origin_problem_id"], progress["candidate_id"], Hash(first["input_refs"])}) || Hash(goal["problem_ids"]) != Hash([]any{progress["origin_problem_id"]}) {
		return bad()
	}
	var payload Object
	if json.Unmarshal(env.Payload, &payload) != nil {
		return bad()
	}
	sid := deref(env.SessionID)
	objective, title, deliverable := "", "", ""
	if deref(env.Method) == "session.send" {
		if payload["delivery"] != "NORMAL" || sid == "" || !p.entry["Session"][sid] || len(added["Session"]) != 0 || len(added["Requirement"]) != 1 || added["Requirement"][0] != Str(requirement, "id") || progress["candidate_id"] != sid {
			return bad()
		}
		objective = Str(payload, "text")
		title = "Client message"
		deliverable = "One finite Mu response to the authenticated client message"
		if !strings.HasPrefix(Str(originalRequirement, "requirement_key"), "SESSION-") {
			return bad()
		}
		contract, _ := first["acceptance_contract"].(map[string]any)
		expected := clientTurnContract()
		for key, value := range expected {
			if key != "frozen_at" && key != "contract_hash" && Hash(contract[key]) != Hash(value) {
				return bad()
			}
		}
	} else if deref(env.Method) == "goal.start" {
		if payload["start_as_draft"] != false {
			return bad()
		}
		objective = Str(payload, "objective")
		title = objective
		deliverable = "One bounded Mu response to the exact Owner objective; independent acceptance remains separate"
		contracts := []string{}
		for _, id := range Arr(payload, "contract_artifact_ids") {
			text, ok := id.(string)
			if !ok {
				return bad()
			}
			contracts = append(contracts, text)
		}
		contract, source, e := s.goalContracts(tx, owner, project, contracts)
		if e != nil {
			return bad()
		}
		actualContract, _ := first["acceptance_contract"].(map[string]any)
		for key, value := range contract {
			if key != "frozen_at" && key != "contract_hash" && Hash(actualContract[key]) != Hash(value) {
				return bad()
			}
		}
		if Hash(originalRequirement["source_refs"]) != Hash(source) {
			return bad()
		}
		keyRefs := append(Empty(), source...)
		sort.Slice(keyRefs, func(i, j int) bool { return Hash(keyRefs[i]) < Hash(keyRefs[j]) })
		identity := Digest(Bytes(Object{"project": project, "principal": p.principal, "objective": objective, "contracts": keyRefs}))
		if progress["candidate_id"] != "goal-candidate-"+identity[:32] || progress["origin_problem_id"] != "goal-problem-"+identity[:32] || originalRequirement["requirement_key"] != "GOAL-"+identity[:32] {
			return bad()
		}
		if sid == "" {
			if len(added["Session"]) != 1 {
				return bad()
			}
			sid = added["Session"][0]
		} else if !p.entry["Session"][sid] || len(added["Session"]) != 0 {
			return bad()
		}
	} else {
		return bad()
	}
	if objective == "" || goal["original_intent"] != objective || goal["title"] != title || first["title"] != title || Hash(goal["deliverables"]) != Hash([]any{deliverable}) || originalRequirement["text"] != objective || requirement["text"] != objective {
		return bad()
	}
	contract, _ := first["acceptance_contract"].(map[string]any)
	if contract["contract_hash"] != contractDigest(contract) {
		return bad()
	}
	input := Arr(first, "input_refs")
	source := Arr(originalRequirement, "source_refs")
	inputSources := append(Empty(), source...)
	if deref(env.Method) == "session.send" {
		attachments := Arr(payload, "attachment_artifact_ids")
		if len(attachments) != len(source) {
			return bad()
		}
		for i, id := range attachments {
			r, ok := source[i].(map[string]any)
			if !ok || r["id"] != id {
				return bad()
			}
		}
		transcript, e := replaySessionTranscript(ctx, tx, s.Doc, project, sid)
		if e != nil {
			return nil, "", e
		}
		messages := 0
		for _, v := range transcript.messages {
			m, _ := v.(map[string]any)
			if m["role"] == "USER" || m["role"] == "ASSISTANT" {
				messages++
			}
		}
		if messages > 0 {
			if len(input) <= len(source) {
				return bad()
			}
			historyRef, ok := input[len(source)].(map[string]any)
			if !ok || p.entry["Artifact"][Str(historyRef, "id")] {
				return bad()
			}
			if e = s.pendingHistoryInput(ctx, tx, project, sid, historyRef, transcript); e != nil {
				return nil, "", e
			}
			inputSources = append(inputSources, historyRef)
		}
	}
	expectedInput := append(inputSources, refs...)
	if authority, ok := s.SessionRuntime.(ClientTaskInputAuthority); ok {
		frozen, e := authority.FreezeClientTaskInputs(ctx, tx, project, model)
		if e != nil {
			return nil, "", e
		}
		expectedInput = append(expectedInput, frozen...)
	}
	if Hash(input) != Hash(expectedInput) {
		return bad()
	}
	for _, value := range source {
		r, ok := value.(map[string]any)
		if !ok || r["entity_type"] != "Artifact" {
			return bad()
		}
		artifact, e := version(tx, project, r)
		if e != nil || artifact["sealed_at"] == nil || s.Domain.effective(tx, project, r) != nil {
			return bad()
		}
	}
	sess, e := loadClientSession(ctx, tx, sid, project)
	if e != nil || sess.sealed || sess.archived || sess.writerClientID != deref(env.ClientID) {
		return bad()
	}
	var actualModel, workspace, lease string
	var boundTask, boundRun sql.NullString
	if e = tx.QueryRowContext(ctx, `SELECT model_config_ref,workspace_ref,lease_expires_at,task_id,run_id FROM client_sessions WHERE id=? AND project_id=?`, sid, project).Scan(&actualModel, &workspace, &lease, &boundTask, &boundRun); e != nil || actualModel != model {
		return bad()
	}
	until, e := time.Parse(time.RFC3339Nano, lease)
	if e != nil || !until.After(time.Now()) {
		return bad()
	}
	if deref(env.SessionID) != "" {
		if env.ExpectedRevision == nil || env.WriterEpoch == nil || sess.revision != *env.ExpectedRevision || sess.epoch != *env.WriterEpoch {
			return bad()
		}
		if e = s.validateSessionConfiguration(ctx, tx, p.principal, sess, false); e != nil {
			return nil, "", e
		}
	} else {
		if sess.revision != 1 || sess.epoch != 1 || sess.watermark != 0 || boundTask.Valid || boundRun.Valid {
			return bad()
		}
		if _, e = clientSessionCreationPrincipal(ctx, tx, project, sid); e != sql.ErrNoRows {
			return bad()
		}
		binding, e := s.Domain.binding(ctx, tx, workspace)
		if e != nil || binding.ClientID != deref(env.ClientID) {
			return bad()
		}
		if e = s.checkClientCreationBinding(ctx, tx, p.principal, project, workspace, model); e != nil {
			return nil, "", e
		}
	}
	if e = s.checkClientBinding(ctx, tx, p.principal, project, workspace, model); e != nil {
		return nil, "", e
	}
	return sess, p.principal, nil
}

func (s *ClientService) pendingHistoryInput(ctx context.Context, tx *sql.Tx, project, sid string, ref Object, transcript *sessionTranscript) error {
	bad := func() error {
		return Fail(503, "MODEL_UNAVAILABLE", "in-flight history differs from original Session journal")
	}
	if ref["entity_type"] != "Artifact" {
		return bad()
	}
	artifact, e := version(tx, project, ref)
	if e != nil || artifact["sealed_at"] == nil {
		return bad()
	}
	var raw []byte
	if e = tx.QueryRowContext(ctx, `SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1`, project, artifact["storage_key"]).Scan(&raw); e != nil || len(raw) > maxClientHistoryBytes || Digest(raw) != artifact["content_hash"] {
		return bad()
	}
	history, e := Decode(raw)
	if e != nil || history["schema"] != "researchos.session-history.v1" || history["origin"] != "SESSION_MESSAGE_JOURNAL" || history["session_id"] != sid {
		return bad()
	}
	var watermark int64
	if e = tx.QueryRowContext(ctx, `SELECT event_watermark FROM client_sessions WHERE id=? AND project_id=?`, sid, project).Scan(&watermark); e != nil {
		return e
	}
	before, e := Num(history, "before_sequence")
	if e != nil || before != watermark {
		return bad()
	}
	expected := map[string]Object{}
	for i, value := range transcript.messages {
		m, _ := value.(map[string]any)
		if m["role"] != "USER" && m["role"] != "ASSISTANT" {
			continue
		}
		if m["complete"] != true {
			return bad()
		}
		text := ""
		for _, part := range Arr(m, "parts") {
			p, _ := part.(map[string]any)
			if p["complete"] != true {
				return bad()
			}
			text += Str(p, "text")
		}
		sequence, _ := transcript.sequences[i].(map[string]any)
		expected[Str(m, "message_id")] = Object{"message_id": m["message_id"], "role": m["role"], "text": text, "start_sequence": sequence["start_sequence"], "end_sequence": sequence["end_sequence"]}
	}
	for _, value := range Arr(history, "messages") {
		m, ok := value.(map[string]any)
		if !ok {
			return bad()
		}
		id := Str(m, "message_id")
		want, ok := expected[id]
		if !ok || Hash(m) != Hash(want) {
			return bad()
		}
		delete(expected, id)
	}
	if len(expected) != 0 {
		return bad()
	}
	return nil
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
		if e := requireClientOriginalHeader(ctx, tx, principal, r.key, known); e != nil {
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

// Public snapshots contain goal_id, never task_id. The original command's
// TASK_CHANGED EventEnvelope binds a particular immutable Task version to that
// Goal, principal and command. A different Task sharing a Goal is not that proof.
func (s *ClientService) originalSessionTasks(ctx context.Context, tx *sql.Tx, principal, project, sid string) ([]Object, error) {
	rows, e := tx.QueryContext(ctx, `SELECT key,body,request_hash,headers,operation FROM idempotency WHERE principal=? AND project=? AND operation IN('v2:session.send','v2:goal.start') AND json_extract(body,'$.status')='COMPLETED' AND (json_extract(body,'$.session_id')=? OR json_extract(body,'$.result.snapshot.session_id')=?)`, principal, project, sid, sid)
	if e != nil {
		return nil, e
	}
	type original struct{ command, goal, method, raw, hash, headers string }
	originals := []original{}
	for rows.Next() {
		var command, raw, hash, headers, operation string
		if e = rows.Scan(&command, &raw, &hash, &headers, &operation); e != nil {
			rows.Close()
			return nil, e
		}
		r, err := Decode([]byte(raw))
		if err != nil {
			rows.Close()
			return nil, err
		}
		if Str(r, "command_id") != command || operation != "v2:"+Str(r, "method") || s.Doc.ValidateDef("CommandResponse", r) != nil {
			rows.Close()
			return nil, Fail(503, "MODEL_UNAVAILABLE", "original Task response locator differs")
		}
		result, _ := r["result"].(map[string]any)
		snapshot, _ := result["snapshot"].(map[string]any)
		goal := Str(snapshot, "goal_id")
		if goal != "" {
			originals = append(originals, original{command, goal, Str(r, "method"), raw, hash, headers})
		}
	}
	e = rows.Err()
	rows.Close()
	if e != nil {
		return nil, e
	}
	bad := func() error { return Fail(503, "MODEL_UNAVAILABLE", "original command Task provenance unavailable") }
	tasks := []Object{}
	seen := map[string]bool{}
	queuedTargets := map[string]string{}
	for _, original := range originals {
		req, known, err := readClientCommandEnvelope(s.Doc, original.headers)
		if err != nil {
			return nil, err
		}
		if e := requireClientOriginalHeader(ctx, tx, principal, original.command, known); e != nil {
			return nil, e
		}
		if known {
			if req.hash != original.hash || deref(req.env.ProjectID) != project || deref(req.env.CommandID) != original.command || deref(req.env.Method) != original.method {
				return nil, bad()
			}
			if _, err = decodeClientIdentityResponse(s.Doc, req, []byte(original.raw)); err != nil {
				return nil, err
			}
			var n int
			if err = tx.QueryRowContext(ctx, `SELECT count(*) FROM client_command_identities WHERE principal=? AND command_id=? AND project=? AND method=? AND request_hash=?`, principal, original.command, project, original.method, original.hash).Scan(&n); err != nil || n != 1 {
				return nil, bad()
			}
		}

		// A queued command appends input to its existing Task. Its original
		// response and exact queue admission must agree, but neither creates
		// Task provenance. Resolve its target only against the producer set
		// collected below; queue/current-head rows cannot manufacture it.
		response, err := Decode([]byte(original.raw))
		if err != nil {
			return nil, err
		}
		result, _ := response["result"].(map[string]any)
		queuePosition, _ := Num(result, "queue_position")
		if original.method == "session.send" && queuePosition > 0 {
			var taskID, goalID, hash, delivery, message, content, contentHash string
			var sequence, epoch int64
			err = tx.QueryRowContext(ctx, `SELECT q.task_id,q.goal_id,q.request_hash,q.delivery,q.message_id,q.content,q.content_hash,q.queue_sequence,q.accepted_writer_epoch FROM client_command_queue q JOIN client_queue_fences f ON f.project=q.project AND f.task_id=q.task_id AND f.session_id=q.session_id AND f.generation=q.generation WHERE q.principal=? AND q.project=? AND q.command_id=? AND q.session_id=?`, principal, project, original.command, sid).Scan(&taskID, &goalID, &hash, &delivery, &message, &content, &contentHash, &sequence, &epoch)
			if err != nil || hash != original.hash || goalID != original.goal || sequence != queuePosition || message != Str(result, "message_id") || Digest([]byte(content)) != contentHash || (delivery != "STEER" && delivery != "FOLLOW_UP") {
				return nil, bad()
			}
			if known {
				payload, err := Decode(req.env.Payload)
				if err != nil || payload["delivery"] != delivery || deref(req.env.SessionID) != sid || derefI64(req.env.WriterEpoch, 0) != epoch {
					return nil, bad()
				}
				accepted, err := Decode([]byte(content))
				if err != nil || accepted["text"] != payload["text"] || len(Arr(accepted, "attachments")) != len(Arr(payload, "attachment_artifact_ids")) {
					return nil, bad()
				}
				for i, value := range Arr(accepted, "attachments") {
					attachment, ok := value.(map[string]any)
					if !ok {
						return nil, bad()
					}
					ref, ok := attachment["ref"].(map[string]any)
					if !ok || ref["entity_type"] != "Artifact" || ref["id"] != Arr(payload, "attachment_artifact_ids")[i] {
						return nil, bad()
					}
				}
			}
			queuedTargets[taskID] = goalID
			continue
		}
		if known && original.method == "session.send" {
			payload, err := Decode(req.env.Payload)
			if err != nil || payload["delivery"] != "NORMAL" {
				return nil, bad()
			}
		}
		rows, e = tx.QueryContext(ctx, `SELECT body FROM outbox WHERE project=? AND json_extract(body,'$.event_type')='TASK_CHANGED' AND json_extract(body,'$.actor_id')=? AND json_extract(body,'$.correlation_id')=?`, project, principal, original.command)
		if e != nil {
			return nil, e
		}
		events := []Object{}
		for rows.Next() {
			var raw string
			if e = rows.Scan(&raw); e != nil {
				rows.Close()
				return nil, e
			}
			event, err := Decode([]byte(raw))
			if err != nil {
				rows.Close()
				return nil, err
			}
			events = append(events, event)
		}
		e = rows.Err()
		rows.Close()
		if e != nil {
			return nil, e
		}
		for _, event := range events {
			if s.Domain.Contracts.Validate("EventEnvelope", event) != nil || event["receipt_hash"] != Receipt(event) {
				return nil, bad()
			}
			stored, err := firstClientObject(tx, project, "EventEnvelope", Str(event, "id"))
			if err != nil || Hash(stored) != Hash(event) {
				return nil, bad()
			}
			ref, ok := event["aggregate_ref"].(map[string]any)
			if !ok || ref["entity_type"] != "Task" {
				return nil, bad()
			}
			published, err := version(tx, project, ref)
			if err != nil || published["goal_id"] != original.goal {
				return nil, bad()
			}
			first, err := firstClientObject(tx, project, "Task", Str(published, "id"))
			if err != nil || first["goal_id"] != original.goal || first["task_type"] != "mu_turn" || Hash(first["input_refs"]) != Hash(published["input_refs"]) {
				return nil, bad()
			}
			progress, err := firstClientObject(tx, project, "NoProgressRecord", Str(first, "no_progress_record_id"))
			if err != nil || progress["input_hash"] != Hash(first["input_refs"]) || progress["key_hash"] != Hash([]any{progress["origin_problem_id"], progress["candidate_id"], Hash(first["input_refs"])}) {
				return nil, bad()
			}
			goal, err := firstClientObject(tx, project, "Goal", original.goal)
			if err != nil || Hash(goal["problem_ids"]) != Hash([]any{progress["origin_problem_id"]}) {
				return nil, bad()
			}
			if original.method == "session.send" {
				if progress["candidate_id"] != sid {
					return nil, bad()
				}
			} else {
				refs := Arr(first, "requirement_refs")
				if len(refs) != 1 {
					return nil, bad()
				}
				rr, ok := refs[0].(map[string]any)
				if !ok {
					return nil, bad()
				}
				requirement, err := firstClientObject(tx, project, "Requirement", Str(rr, "id"))
				if err != nil {
					return nil, bad()
				}
				source := append(Empty(), Arr(requirement, "source_refs")...)
				sort.Slice(source, func(i, j int) bool { return Hash(source[i]) < Hash(source[j]) })
				identity := Digest(Bytes(Object{"project": project, "principal": principal, "objective": goal["original_intent"], "contracts": source}))
				if progress["candidate_id"] != "goal-candidate-"+identity[:32] || progress["origin_problem_id"] != "goal-problem-"+identity[:32] {
					return nil, bad()
				}
			}
			current, err := load(tx, project, "Task", Str(first, "id"))
			if err != nil || current["goal_id"] != original.goal || Hash(current["input_refs"]) != Hash(first["input_refs"]) {
				return nil, bad()
			}
			if !seen[Str(current, "id")] {
				tasks = append(tasks, current)
				seen[Str(current, "id")] = true
			}
		}
		if len(events) == 0 {
			var n int
			if e = tx.QueryRowContext(ctx, `SELECT count(*) FROM domain_objects WHERE project=? AND kind='Task' AND json_extract(body,'$.goal_id')=?`, project, original.goal).Scan(&n); e != nil {
				return nil, e
			}
			if n > 0 {
				return nil, bad()
			}
		}
	}

	for id, goal := range queuedTargets {
		if !seen[id] {
			return nil, bad()
		}
		for _, task := range tasks {
			if Str(task, "id") == id && Str(task, "goal_id") != goal {
				return nil, bad()
			}
		}
	}
	return tasks, nil
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
	originalTasks, e := s.originalSessionTasks(ctx, tx, principal, sess.project, sess.sessionID)
	if e != nil {
		return e
	}
	rows, e := tx.QueryContext(ctx, `SELECT DISTINCT t.body FROM domain_objects t WHERE t.project=? AND t.kind='Task' AND (t.id=(SELECT task_id FROM client_sessions WHERE id=?) OR json_extract(t.body,'$.goal_id') IN(SELECT COALESCE(json_extract(body,'$.result.goal_id'),json_extract(body,'$.result.snapshot.goal_id')) FROM idempotency WHERE project=? AND operation IN('v2:goal.start','v2:session.send') AND json_extract(body,'$.status')='COMPLETED' AND (json_extract(body,'$.session_id')=? OR json_extract(body,'$.result.snapshot.session_id')=?)) OR t.id IN(SELECT task_id FROM client_queue_fences WHERE project=? AND session_id=?))`, sess.project, sess.sessionID, sess.project, sess.sessionID, sess.sessionID, sess.project, sess.sessionID)
	if e != nil {
		return e
	}
	tasks := originalTasks
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
		// A later active_run_id cannot hide an older generation's unresolved
		// effects or child process. Reuse the actual settlement predicate for
		// each canonical Run belonging to the original Task, without writes.
		runs, err := tx.QueryContext(ctx, `SELECT id FROM domain_objects WHERE project=? AND kind='Run' AND json_extract(body,'$.task_id')=?`, sess.project, Str(task, "id"))
		if err != nil {
			return err
		}
		ids := []string{}
		for runs.Next() {
			var id string
			if err = runs.Scan(&id); err != nil {
				runs.Close()
				return err
			}
			ids = append(ids, id)
		}
		err = runs.Err()
		runs.Close()
		if err != nil {
			return err
		}
		for _, id := range ids {
			historical := Object{}
			for k, v := range task {
				historical[k] = v
			}
			historical["active_run_id"] = id
			if !clientTurnSettled(tx, sess.project, sess.sessionID, historical) {
				return Fail(409, "SESSION_BUSY", "earlier session run is not settled")
			}
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
	rows, e = tx.QueryContext(ctx, `SELECT q.state,q.command_id,q.generation,COALESCE(r.kind,''),COALESCE(r.body,''),COALESCE(r.body_hash,'') FROM client_command_queue q LEFT JOIN client_control_receipts r ON r.receipt_id=q.last_receipt_id AND r.project=q.project AND r.generation=q.generation AND r.command_id=q.command_id WHERE q.project=? AND q.session_id=?`, sess.project, sess.sessionID)
	if e != nil {
		return e
	}
	type terminalReceipt struct{ state, command, generation, kind, body, hash string }
	receipts := []terminalReceipt{}
	for rows.Next() {
		var r terminalReceipt
		if e = rows.Scan(&r.state, &r.command, &r.generation, &r.kind, &r.body, &r.hash); e != nil {
			rows.Close()
			return e
		}
		receipts = append(receipts, r)
	}
	e = rows.Err()
	rows.Close()
	if e != nil {
		return e
	}
	for _, r := range receipts {
		if Digest([]byte(r.body)) != r.hash {
			return Fail(409, "SESSION_BUSY", "queue settlement receipt unavailable")
		}
		if r.state == "DROPPED" && r.kind == "CANCEL_FENCE" {
			if e = s.validatePreSDKConfigurationDrop(ctx, tx, principal, sess, r.command, r.generation, r.body); e != nil {
				return e
			}
		} else if (r.state == "CONSUMED" && r.kind != "command.consumed") || (r.state == "DROPPED" && r.kind != "command.cleared") {
			return Fail(409, "SESSION_BUSY", "queue settlement receipt unavailable")
		}
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

// An input cancelled while still ENQUEUED has never entered the SDK. Its actual
// host producer records CANCEL_FENCE, not command.cleared. Require the original
// transition and cancellation command, alongside the settlement checks above.
func (s *ClientService) validatePreSDKConfigurationDrop(ctx context.Context, tx *sql.Tx, principal string, sess *clientSessionRow, command, generation, raw string) error {
	bad := func() error { return Fail(409, "SESSION_BUSY", "preSDK cancellation proof unavailable") }
	body, e := Decode([]byte(raw))
	if e != nil || len(body) != 3 || body["from"] != "ENQUEUED" || body["to"] != "DROPPED" {
		return bad()
	}
	var task, goal, fence, queuePrincipal string
	var previous sql.NullString
	var sealed, accepted, sequence int64
	e = tx.QueryRowContext(ctx, `SELECT q.task_id,q.goal_id,q.principal,q.queue_sequence,f.state,f.sealed_through,f.accepted_through,r.previous_receipt_id FROM client_command_queue q JOIN client_queue_fences f ON f.project=q.project AND f.session_id=q.session_id AND f.task_id=q.task_id AND f.generation=q.generation JOIN client_control_receipts r ON r.receipt_id=q.last_receipt_id AND r.project=q.project AND r.generation=q.generation AND r.command_id=q.command_id WHERE q.project=? AND q.session_id=? AND q.command_id=? AND q.generation=? AND q.state='DROPPED' AND f.restore_fenced=0`, sess.project, sess.sessionID, command, generation).Scan(&task, &goal, &queuePrincipal, &sequence, &fence, &sealed, &accepted, &previous)
	if e != nil || queuePrincipal != principal || body["task_id"] != task || previous.Valid || fence != "CANCEL_FENCED" || sealed != accepted || sequence < 1 || sequence > sealed {
		return bad()
	}
	var receipts int
	if e = tx.QueryRowContext(ctx, `SELECT count(*) FROM client_control_receipts WHERE project=? AND generation=? AND command_id=?`, sess.project, generation, command).Scan(&receipts); e != nil {
		return e
	}
	if receipts != 1 {
		return bad()
	}
	rows, e := tx.QueryContext(ctx, `SELECT c.command_id,c.request_hash,c.task_ids,c.target_id,c.original_response,c.final_response,i.headers,i.body,i.request_hash FROM client_control_requests c JOIN idempotency i ON i.principal=c.principal AND i.project=c.project AND i.key=c.command_id AND i.operation='v2:session.control' WHERE c.principal=? AND c.project=? AND c.session_id=? AND c.state='CONFIRMED'`, principal, sess.project, sess.sessionID)
	if e != nil {
		return e
	}
	type control struct{ command, hash, tasks, target, original, final, headers, journal, journalHash string }
	controls := []control{}
	for rows.Next() {
		var r control
		if e = rows.Scan(&r.command, &r.hash, &r.tasks, &r.target, &r.original, &r.final, &r.headers, &r.journal, &r.journalHash); e != nil {
			rows.Close()
			return e
		}
		controls = append(controls, r)
	}
	e = rows.Err()
	rows.Close()
	if e != nil {
		return e
	}
	for _, c := range controls {
		var tasks []string
		if json.Unmarshal([]byte(c.tasks), &tasks) != nil {
			return bad()
		}
		member := false
		for _, id := range tasks {
			if id == task {
				member = true
			}
		}
		if !member {
			continue
		}
		req, known, e := readClientCommandEnvelope(s.Doc, c.headers)
		if e != nil || !known || req.hash != c.hash || c.hash != c.journalHash || deref(req.env.CommandID) != c.command || deref(req.env.Method) != "session.control" || deref(req.env.SessionID) != sess.sessionID || deref(req.env.ProjectID) != sess.project {
			return bad()
		}
		payload, e := Decode(req.env.Payload)
		if e != nil || payload["action"] != "CANCEL" || payload["target_id"] != c.target {
			return bad()
		}
		actual, e := load(tx, sess.project, "Task", task)
		if e != nil || Str(actual, "goal_id") != goal || (c.target != goal && c.target != Str(actual, "active_run_id")) {
			return bad()
		}
		if c.original != c.journal {
			return bad()
		}
		if _, e = lookupClientCommandIdentity(ctx, tx, s.Doc, principal, req.env.originalRaw, req.env); e != nil {
			return bad()
		}
		final, e := decodeClientIdentityResponse(s.Doc, req, []byte(c.final))
		if e != nil || deref(final.Status) != "COMPLETED" || final.Result["action"] != "CANCEL" || final.Result["target_id"] != c.target || final.Result["control_request_id"] != "ctrl-"+c.command || final.Result["settled"] != true || final.Result["children_stopped"] != true || final.Result["queue_empty"] != true {
			return bad()
		}
		return nil
	}
	return bad()
}
