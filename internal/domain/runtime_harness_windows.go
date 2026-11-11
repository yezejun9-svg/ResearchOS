//go:build windows

package domain

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	rt "researchos.local/research-os/adapters/runtime"
)

const harnessBackend = "codex-cli-readonly-v1"
const harnessAdapter = "codex-cli-harness-v1"

type harnessV1 struct{ c *RuntimeCoordinator }
type harnessRoute struct {
	runtimeID, executor, scheduler, executorToken, schedulerToken string
	profileRef                                                    Object
}

func (c *RuntimeCoordinator) HarnessV1() HarnessAPI { return &harnessV1{c: c} }
func (h *harnessV1) auth(ctx context.Context, token, project string) (*sql.Tx, Principal, error) {
	tx, err := h.c.service.DB.BeginTx(ctx, nil)
	if err != nil {
		return nil, Principal{}, err
	}
	p, err := authenticate(tx, token)
	if err != nil {
		tx.Rollback()
		return nil, p, harnessFail(401, "HOST_AUTH_REQUIRED", "current Host credential required")
	}
	if p.DeviceID != "" || !p.HasRole("OWNER") || project != "" && !p.Allowed(project, "", "", false) {
		tx.Rollback()
		return nil, p, harnessFail(403, "FORBIDDEN", "current local project Owner required")
	}
	if h.c.config.HarnessAuthority == nil {
		tx.Rollback()
		return nil, p, harnessFail(503, "HARNESS_UNAVAILABLE", "Host Harness authority unavailable")
	}
	actual, err := h.c.config.HarnessAuthority.HarnessPrincipal(ctx)
	if err != nil || actual != p.ID {
		tx.Rollback()
		return nil, p, harnessFail(403, "FORBIDDEN", "actual local Host principal required")
	}
	return tx, p, nil
}
func (h *harnessV1) workspace(ctx context.Context, tx *sql.Tx, p Principal, project, ref string) (*WorkspaceBinding, error) {
	b, err := h.c.service.binding(ctx, tx, ref)
	if err != nil {
		return nil, harnessFail(404, "NOT_FOUND", "registered workspace reference not found")
	}
	if b.PrincipalID != p.ID || b.ProjectID == nil || *b.ProjectID != project || b.Status != WorkspaceActive || (b.Access != "READ_ONLY" && b.Access != "READ_WRITE") {
		return nil, harnessFail(403, "WORKSPACE_REVOKED", "current project workspace binding required")
	}
	if h.c.config.WorkspaceAuthority == nil {
		return nil, harnessFail(503, "HARNESS_UNAVAILABLE", "workspace authority unavailable")
	}
	if err = h.c.config.WorkspaceAuthority.ConfirmPath(ctx, b.RealPath, "READ_ONLY"); err != nil {
		return nil, harnessScopeError(err)
	}
	// A configured production qualifier is bound to one reviewed synthetic
	// source. Existing unconfigured Go fixture drivers retain their test scope.
	if source, qualified := rt.CodexNativeQualificationSource(h.c.config.HarnessDriver); qualified && b.RealPath != source {
		return nil, harnessFail(403, "WORKSPACE_REVOKED", "qualified native source differs from current workspace")
	}
	return b, nil
}
func harnessReadiness(driver rt.CodexDriver) (rt.CodexDescriptor, rt.CodexReadiness) {
	descriptor := rt.CodexDescriptor{}
	snapshot := rt.CodexReadiness{}
	if driver != nil {
		descriptor, snapshot = driver.Descriptor(), driver.ReadinessSnapshot()
	}
	return descriptor, rt.EvaluateCodexReadiness(descriptor, snapshot, rt.CodexExpectedPolicyIdentity(descriptor))
}
func harnessPolicyMatches(profile map[string]any, identity rt.CodexPolicyIdentity) bool {
	sandbox, command := rt.CodexNativeSandboxID, rt.CodexNativeCommandID
	if identity.Transport == rt.CodexRPCTransport {
		sandbox, command = rt.CodexRPCSandboxID, rt.CodexRPCCommandID
		if profile["native_transport"] != identity.Transport || profile["helper_contract"] != identity.HelperContract {
			return false
		}
	}
	return profile["sandbox"] == sandbox && profile["command_id"] == command &&
		profile["native_policy_revision"] == identity.Revision && profile["windows_sandbox"] == identity.WindowsSandbox &&
		profile["permission_profile"] == identity.PermissionProfile && profile["requested_config_sha256"] == identity.RequestedConfigSHA256 &&
		profile["build_hash"] == identity.BinarySHA256
}
func harnessNull(s string) any {
	if s == "" {
		return nil
	}
	return s
}
func (h *harnessV1) Capabilities(ctx context.Context, token string) (Object, error) {
	tx, _, err := h.auth(ctx, token, "")
	if err != nil {
		return nil, err
	}
	tx.Rollback()
	descriptor, readiness := harnessReadiness(h.c.config.HarnessDriver)
	ready := rt.CodexAllowsPreparation(readiness)
	reasons := Empty()
	if !ready {
		reasons = append(reasons, readiness.Reason)
	} else if readiness.State == "PREPARATION_READY" {
		reasons = append(reasons, "PER_RUN_PERMISSION_CHECK_REQUIRED")
	}
	auth := descriptor.AuthState
	if auth == "" {
		auth = "UNPROBED"
	}
	return harnessEnvelope(Object{"harness_id": "codex", "display_name": "Codex CLI", "backend": harnessBackend,
		"installation":   Object{"present": descriptor.Present, "version": harnessNull(descriptor.Version), "executable_sha256": harnessNull(descriptor.ExecutableHash), "checked_at": harnessNull(descriptor.AuthCheckedAt)},
		"authentication": Object{"state": auth, "kind": harnessNull(descriptor.AuthKind), "checked_at": harnessNull(descriptor.AuthCheckedAt)},
		"verification":   Object{"execution": "UNVERIFIED", "workspace_read_scope": "UNVERIFIED", "cancellation": "UNVERIFIED", "checked_at": nil},
		"capabilities":   Object{"readonly_turn": true, "event_stream": true, "cancel": true, "task_history": true, "request_lookup": true, "token_delta": false, "write": false, "resume": false, "pause": false, "per_tool_approval": false, "file_diff": false, "file_list": false, "file_artifacts": false, "attachments": false},
		"security_scope": Object{"mode": "workspace-read", "profile_id": "codex-workspace-read-v1", "config_source": "HOST_FIXED", "hooks": "PLATFORM_POLICY", "mcp": "PLATFORM_POLICY", "native_auth": "CLI_OWNED", "enforcement_verified": false},
		"can_submit":     ready, "reason_codes": reasons}), nil
}
func (h *harnessV1) ensureRuntime(ctx context.Context, token string, p Principal, project string) (harnessRoute, error) {
	h.c.harnessMu.Lock()
	defer h.c.harnessMu.Unlock()
	if h.c.harnessRoutes == nil {
		h.c.harnessRoutes = map[string]harnessRoute{}
	}
	executor, err := h.c.service.EnsureRuntimeSetupPrincipal(ctx, token, project, "EXECUTOR")
	if err != nil {
		return harnessRoute{}, err
	}
	scheduler, err := h.c.service.EnsureRuntimeSetupPrincipal(ctx, token, project, "SCHEDULER")
	if err != nil {
		return harnessRoute{}, err
	}
	executorToken, err := h.c.service.IssueCredential(ctx, executor, 15*time.Minute)
	if err != nil {
		return harnessRoute{}, err
	}
	schedulerToken, err := h.c.service.IssueCredential(ctx, scheduler, 15*time.Minute)
	if err != nil {
		return harnessRoute{}, err
	}
	descriptor := h.c.config.HarnessDriver.Descriptor()
	identity := rt.CodexExpectedPolicyIdentity(descriptor)
	tx, err := h.c.service.DB.BeginTx(ctx, nil)
	if err != nil {
		return harnessRoute{}, err
	}
	defer tx.Rollback()
	var registration Object
	var raw string
	name := "Codex readonly Host MXC V2 " + p.ID
	if identity.Transport == rt.CodexRPCTransport {
		name = "Codex readonly Host MXC RPC V3 " + p.ID
	}
	err = tx.QueryRowContext(ctx, "SELECT body FROM domain_objects WHERE project=? AND kind='RuntimeRegistration' AND json_extract(body,'$.adapter')=? AND json_extract(body,'$.name')=?", project, harnessAdapter, name).Scan(&raw)
	var profileRef Object
	if err == nil {
		registration, err = Decode([]byte(raw))
		if err != nil {
			return harnessRoute{}, err
		}
		profileRef, _, err = h.c.service.currentRuntimeBinding(tx, project, registration)
		if err != nil {
			return harnessRoute{}, err
		}
		artifact, err := version(tx, project, profileRef)
		if err != nil {
			return harnessRoute{}, err
		}
		profile, err := runtimeProfileBody(tx, project, artifact)
		if err != nil {
			return harnessRoute{}, err
		}
		if profile["backend"] != harnessBackend || !harnessPolicyMatches(profile, identity) {
			return harnessRoute{}, harnessFail(409, "STATE_CONFLICT", "native profile changed")
		}
	} else if errors.Is(err, sql.ErrNoRows) {
		registration, _, _, err = h.c.service.runtimeOperation(tx, p, project, "", Object{"name": name, "adapter": harnessAdapter, "adapter_revision": harnessBackend, "capabilities": []any{"start"}, "platform": "windows-amd64", "measurement_mode": "LIVE", "credential_ref": nil}, "registerRuntime", ID())
		if err != nil {
			return harnessRoute{}, err
		}
		// AVAILABLE here denotes the distinct owner-authorized Harness backend,
		// not a Mu/model qualification or an independently accepted model result.
		registration["status"] = "AVAILABLE"
		if err = bump(registration); err != nil {
			return harnessRoute{}, err
		}
		if err = h.c.service.put(tx, "RuntimeRegistration", registration); err != nil {
			return harnessRoute{}, err
		}
		root, err := currentAuthorityRoot(tx, p.ID)
		if err != nil {
			return harnessRoute{}, err
		}
		sandbox, command := rt.CodexNativeSandboxID, rt.CodexNativeCommandID
		if identity.Transport == rt.CodexRPCTransport {
			sandbox, command = rt.CodexRPCSandboxID, rt.CodexRPCCommandID
		}
		profile := Object{"runtime_id": registration["id"], "technical_hash": runtimeTechnicalHash(registration), "adapter": harnessAdapter, "adapter_revision": harnessBackend, "platform": "windows-amd64", "build_hash": descriptor.ExecutableHash, "sandbox": sandbox, "native_policy_revision": identity.Revision, "requested_config_sha256": identity.RequestedConfigSHA256, "windows_sandbox": identity.WindowsSandbox, "permission_profile": identity.PermissionProfile, "credential_revision": "CLI_OWNED", "backend": harnessBackend, "model": "CLI_DEFAULT", "command_id": command, "argv": []any{"HOST_FIXED"}, "outputs": []any{"codex-result.json"}, "timeout_seconds": 300, "permissions": Object{"scope": "workspace-read", "hooks": "PLATFORM_POLICY", "mcp": "PLATFORM_POLICY"}, "harness_owner": p.ID, "owner_root": root, "consent_expires_at": time.Now().UTC().Add(24 * time.Hour).Format(time.RFC3339Nano)}
		if identity.Transport == rt.CodexRPCTransport {
			profile["native_transport"], profile["helper_contract"] = identity.Transport, identity.HelperContract
		}
		artifact, err := h.c.service.sealRuntimeSetupProfile(tx, p, project, profile)
		if err != nil {
			return harnessRoute{}, err
		}
		profileRef = Ref(artifact, "Artifact")
		if _, err = tx.ExecContext(ctx, "INSERT INTO runtime_bindings(project,runtime,profile_ref,profile_hash,technical_hash,owner) VALUES(?,?,?,?,?,?)", project, registration["id"], string(Bytes(profileRef)), Hash(profileRef), runtimeTechnicalHash(registration), p.ID); err != nil {
			return harnessRoute{}, err
		}
	} else {
		return harnessRoute{}, err
	}
	if err = tx.Commit(); err != nil {
		return harnessRoute{}, err
	}
	route := harnessRoute{runtimeID: Str(registration, "id"), executor: executor, scheduler: scheduler, executorToken: executorToken, schedulerToken: schedulerToken, profileRef: profileRef}
	h.c.harnessRoutes[project+"/"+p.ID] = route
	return route, nil
}
func (h *harnessV1) Submit(ctx context.Context, token string, in HarnessSubmit) (Object, error) {
	if err := in.Validate(); err != nil {
		return nil, err
	}
	tx, p, err := h.auth(ctx, token, in.ProjectID)
	if err != nil {
		return nil, err
	}
	replay, err := harnessReplay(tx, p.ID, in.ProjectID, "harness:v1:submit", in.RequestID, Hash(in))
	if err != nil || replay != nil {
		tx.Rollback()
		return replay, err
	}
	_, err = h.workspace(ctx, tx, p, in.ProjectID, in.WorkspaceRef)
	tx.Rollback()
	if err != nil {
		return nil, err
	}
	caps, err := h.Capabilities(ctx, token)
	if err != nil {
		return nil, err
	}
	if caps["data"].(Object)["can_submit"] != true {
		return nil, harnessFail(503, "HARNESS_UNAVAILABLE", "Codex login and controlled readonly policy required")
	}
	route, err := h.ensureRuntime(ctx, token, p, in.ProjectID)
	if err != nil {
		return nil, err
	}
	tx, p, err = h.auth(ctx, token, in.ProjectID)
	if err != nil {
		return nil, err
	}
	defer tx.Rollback()
	if err = resourceWriteLock(tx); err != nil {
		return nil, err
	}
	replay, err = harnessReplay(tx, p.ID, in.ProjectID, "harness:v1:submit", in.RequestID, Hash(in))
	if err != nil || replay != nil {
		return replay, err
	}
	binding, err := h.workspace(ctx, tx, p, in.ProjectID, in.WorkspaceRef)
	if err != nil {
		return nil, err
	}
	record := Object{"schema": "researchos.harness-submit.v1", "request": in, "principal_id": p.ID, "runtime_id": route.runtimeID, "profile_ref": route.profileRef, "source_binding": harnessSourceBinding(binding)}
	input, err := h.c.service.serverArtifactMode(tx, in.ProjectID, p.ID, "MANIFEST", "LIVE", Bytes(record), Empty())
	if err != nil {
		return nil, err
	}
	requirement, err := h.c.service.createRequirement(tx, in.ProjectID, Object{"requirement_key": "HARNESS-" + in.RequestID, "text": in.Prompt, "basis": "USER_STATED", "source_refs": Empty(), "rationale": "Authenticated finite Codex readonly task", "supersedes_id": nil, "acceptance_check_ids": Empty()})
	if err != nil {
		return nil, err
	}
	requirement, err = h.c.service.actRequirement(tx, in.ProjectID, Str(requirement, "id"), Object{"action": "ACCEPT", "source_validation_refs": Empty()})
	if err != nil {
		return nil, err
	}
	reqRef := Ref(requirement, "Requirement")
	contract := harnessExecutionContract()
	problem := "harness-" + strings.TrimPrefix(Hash(Object{"project": in.ProjectID, "principal": p.ID, "request": in.RequestID}), "sha256:")
	goal, err := h.c.service.createGoal(tx, in.ProjectID, Object{"title": "Codex readonly task", "original_intent": in.Prompt, "scope": "PROJECT", "requirement_refs": []any{reqRef}, "problem_ids": []any{problem}, "deliverables": []any{"One observed Codex readonly response"}, "acceptance_contract": contract})
	if err != nil {
		return nil, err
	}
	task, err := h.c.service.createTask(tx, in.ProjectID, Object{"goal_id": goal["id"], "title": "Codex readonly task", "task_type": "harness_turn", "stage": "delivery", "dependency_task_ids": Empty(), "requirement_refs": []any{reqRef}, "input_refs": []any{Ref(input, "Artifact"), route.profileRef, reqRef}, "acceptance_contract": contract, "origin_problem_id": problem, "candidate_id": in.RequestID, "stop_policy": Object{"wall_time_seconds": 300, "max_attempts": 1, "max_parallel_runs": 1, "stop_conditions": []any{"turn complete", "authority lost", "execution unknown", "Owner cancellation"}}})
	if err != nil {
		return nil, err
	}
	if _, err = h.c.service.actGoal(tx, in.ProjectID, Str(goal, "id"), Object{"action": "ACTIVATE", "reason": "Authenticated Harness V1 readonly task"}); err != nil {
		return nil, err
	}
	state, err := singleton(tx, in.ProjectID, "ProjectState")
	if err != nil {
		return nil, err
	}
	if _, err = h.c.service.createContext(tx, p, in.ProjectID, Object{"task_id": task["id"], "expected_project_state_revision": state["revision"]}); err != nil {
		return nil, err
	}
	task, err = load(tx, in.ProjectID, "Task", Str(task, "id"))
	if err != nil {
		return nil, err
	}
	task, err = h.c.service.orchestrateTask(tx, in.ProjectID, task, Object{"action": "SUBMIT"})
	if err != nil {
		return nil, err
	}
	view, err := h.taskView(tx, in.ProjectID, task, record, in.RequestID)
	if err != nil {
		return nil, err
	}
	sequence, err := h.emit(tx, p.ID, in.ProjectID, task, nil, "TASK_QUEUED", Object{"status": "QUEUED", "task": view})
	if err != nil {
		return nil, err
	}
	revision, _ := Num(task, "revision")
	ack := harnessEnvelope(Object{"task_ref": harnessRef(in.ProjectID, Str(task, "id")), "request_id": in.RequestID, "task_revision": strconv.FormatInt(revision, 10), "status": "QUEUED", "run": nil})
	headers := Object{"harness_task_id": task["id"], "harness_creation_sequence": strconv.FormatInt(sequence, 10)}
	if _, err = tx.ExecContext(ctx, "INSERT INTO idempotency(principal,project,operation,key,request_hash,status,body,headers,created_at) VALUES(?,?,?,?,?,202,?,?,?)", p.ID, in.ProjectID, "harness:v1:submit", in.RequestID, Hash(in), string(Bytes(ack)), string(Bytes(headers)), Now()); err != nil {
		return nil, err
	}
	return ack, tx.Commit()
}
func harnessReplay(tx *sql.Tx, principal, project, operation, key, hash string) (Object, error) {
	var stored, raw string
	err := tx.QueryRow("SELECT request_hash,body FROM idempotency WHERE principal=? AND project=? AND operation=? AND key=?", principal, project, operation, key).Scan(&stored, &raw)
	if errors.Is(err, sql.ErrNoRows) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	if stored != hash {
		return nil, harnessFail(409, "IDEMPOTENCY_CONFLICT", "request_id already binds a different payload")
	}
	return Decode([]byte(raw))
}
func (h *harnessV1) record(tx *sql.Tx, principal, project, id string) (Object, Object, string, error) {
	task, err := load(tx, project, "Task", id)
	if err != nil || task["task_type"] != "harness_turn" {
		return nil, nil, "", harnessFail(404, "NOT_FOUND", "Harness task not found")
	}
	var requestID string
	err = tx.QueryRow("SELECT key FROM idempotency WHERE principal=? AND project=? AND operation='harness:v1:submit' AND json_extract(body,'$.data.task_ref.task_id')=?", principal, project, id).Scan(&requestID)
	if err != nil {
		return nil, nil, "", harnessFail(404, "NOT_FOUND", "Harness task not found")
	}
	record, err := harnessTaskInput(tx, project, task)
	return task, record, requestID, err
}
func (h *harnessV1) taskView(tx *sql.Tx, project string, task, record Object, requestID string) (Object, error) {
	var request HarnessSubmit
	if json.Unmarshal(Bytes(record["request"]), &request) != nil {
		return nil, errors.New("invalid native submission")
	}
	var run Object
	state := "QUEUED"
	var result any
	var failure any
	if id := Str(task, "active_run_id"); id != "" {
		var err error
		run, err = load(tx, project, "Run", id)
		if err != nil {
			return nil, err
		}
		switch Str(run, "status") {
		case "QUEUED":
			state = "STARTING"
		case "RUNNING":
			state = "RUNNING"
		case "CANCEL_REQUESTED":
			state = "CANCEL_REQUESTED"
		case "SETTLED":
			state = "COMPLETED"
		case "FAILED":
			state = "FAILED"
		case "CANCELLED":
			state = "CANCELLED"
		}
		dispatch, e := runtimeDispatch(tx, project, Str(run, "id"), run["lease_epoch"])
		if e == nil && (dispatch["state"] == "UNKNOWN" || !runTerminal(run) && Str(dispatch, "reason") != "") {
			state = "UNKNOWN"
		}
		for _, id := range Arr(run, "result_artifact_ids") {
			a, err := load(tx, project, "Artifact", id.(string))
			if err != nil {
				return nil, err
			}
			var raw []byte
			if err = tx.QueryRow("SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1", project, a["storage_key"]).Scan(&raw); err != nil {
				return nil, err
			}
			if Digest(raw) != a["content_hash"] {
				return nil, errors.New("native result seal changed")
			}
			data, err := Decode(raw)
			if err == nil && data["schema"] == "researchos.codex-result.v1" {
				result = Object{"assistant_text": Str(data, "assistant_text"), "cli_thread_id": harnessNull(Str(data, "cli_thread_id"))}
			}
		}
	} else if task["status"] == "CANCELLED" {
		state = "CANCELLED"
	} else if task["status"] == "BLOCKED" {
		state = "BLOCKED"
	}
	terminal := state == "COMPLETED" || state == "FAILED" || state == "CANCELLED" || state == "UNKNOWN" || state == "BLOCKED"
	if state == "FAILED" || state == "UNKNOWN" || state == "BLOCKED" {
		code := "HARNESS_UNAVAILABLE"
		message := "Codex execution requires inspection; no automatic replay"
		if state == "UNKNOWN" {
			code = "EXECUTION_UNKNOWN"
		}
		if state == "FAILED" && run != nil && run["execution_report"] == "Native preparation failed before model launch; no automatic replay." {
			message = "Native preparation failed before model launch; no automatic replay"
		}
		failure = harnessErrorValue(harnessFail(503, code, message))
	}
	rev, _ := Num(task, "revision")
	return Object{"task_ref": harnessRef(project, Str(task, "id")), "request_id": requestID, "harness_id": "codex", "workspace_ref": request.WorkspaceRef, "prompt": request.Prompt, "scope": "workspace-read", "ephemeral": true, "status": state, "terminal": terminal, "task_revision": strconv.FormatInt(rev, 10), "run": harnessRunRef(run), "created_at": task["created_at"], "updated_at": task["updated_at"], "result": result, "failure": failure}, nil
}
func (h *harnessV1) Get(ctx context.Context, token, project, id string) (Object, error) {
	if !harnessLabel(project, 128) || !harnessLabel(id, 128) {
		return nil, harnessFail(400, "INVALID_REQUEST", "project/task required")
	}
	tx, p, err := h.auth(ctx, token, project)
	if err != nil {
		return nil, err
	}
	defer tx.Rollback()
	task, record, request, err := h.record(tx, p.ID, project, id)
	if err != nil {
		return nil, err
	}
	data, err := h.taskView(tx, project, task, record, request)
	return harnessEnvelope(data), err
}
func (h *harnessV1) List(ctx context.Context, token string, in HarnessList) (Object, error) {
	if !harnessLabel(in.ProjectID, 128) || in.Limit < 1 || in.Limit > 100 {
		return nil, harnessFail(400, "INVALID_REQUEST", "project/limit invalid")
	}
	cursor, err := HarnessDecimal(in.Cursor, false)
	if err != nil {
		return nil, err
	}
	if in.RequestID != "" && !harnessRequestID(in.RequestID) {
		return nil, harnessFail(400, "INVALID_REQUEST", "request_id invalid")
	}
	tx, p, err := h.auth(ctx, token, in.ProjectID)
	if err != nil {
		return nil, err
	}
	defer tx.Rollback()
	query := "SELECT key,json_extract(body,'$.data.task_ref.task_id'),CAST(json_extract(headers,'$.harness_creation_sequence') AS INTEGER) FROM idempotency WHERE principal=? AND project=? AND operation='harness:v1:submit'"
	args := []any{p.ID, in.ProjectID}
	if in.RequestID != "" {
		query += " AND key=?"
		args = append(args, in.RequestID)
	} else if cursor != 0 {
		query += " AND CAST(json_extract(headers,'$.harness_creation_sequence') AS INTEGER)<?"
		args = append(args, cursor)
	}
	query += " ORDER BY CAST(json_extract(headers,'$.harness_creation_sequence') AS INTEGER) DESC LIMIT ?"
	args = append(args, in.Limit+1)
	rows, err := tx.QueryContext(ctx, query, args...)
	if err != nil {
		return nil, err
	}
	type entry struct {
		request, id string
		seq         int64
	}
	var entries []entry
	for rows.Next() {
		var e entry
		if err = rows.Scan(&e.request, &e.id, &e.seq); err != nil {
			rows.Close()
			return nil, err
		}
		entries = append(entries, e)
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return nil, err
	}
	more := len(entries) > in.Limit
	if more {
		entries = entries[:in.Limit]
	}
	items := Empty()
	next := in.Cursor
	for _, e := range entries {
		task, record, _, err := h.record(tx, p.ID, in.ProjectID, e.id)
		if err != nil {
			return nil, err
		}
		view, err := h.taskView(tx, in.ProjectID, task, record, e.request)
		if err != nil {
			return nil, err
		}
		items = append(items, view)
		next = strconv.FormatInt(e.seq, 10)
	}
	var lookup any
	if in.RequestID != "" {
		state := "NOT_FOUND"
		if len(items) > 0 {
			state = "FOUND"
		}
		lookup = Object{"request_id": in.RequestID, "state": state}
	}
	return harnessEnvelope(Object{"items": items, "next_cursor": next, "has_more": more, "lookup": lookup}), nil
}

func (h *harnessV1) emit(tx *sql.Tx, actor, project string, task, run Object, kind string, data Object) (int64, error) {
	state, err := singleton(tx, project, "ProjectState")
	if err != nil {
		return 0, err
	}
	sequence, _ := Num(state, "event_sequence")
	var maximum int64
	if err = tx.QueryRow("SELECT COALESCE(MAX(sequence),0) FROM outbox WHERE project=?", project).Scan(&maximum); err != nil {
		return 0, err
	}
	if maximum > sequence {
		sequence = maximum
	}
	if sequence == 1<<63-1 {
		return 0, errors.New("event sequence exhausted")
	}
	sequence++
	payload := Object{"status": nil, "text": nil, "tool": nil, "task": nil, "error": nil}
	for k, v := range data {
		if _, ok := payload[k]; !ok {
			return 0, errors.New("unknown harness event field")
		}
		payload[k] = v
	}
	eventID := ID()
	event := Object{"event_id": eventID, "task_ref": harnessRef(project, Str(task, "id")), "run": harnessRunRef(run), "sequence": strconv.FormatInt(sequence, 10), "timestamp": Now(), "kind": kind, "payload": payload}
	artifact, err := h.c.service.serverArtifactMode(tx, project, actor, "LOG", "LIVE", Bytes(Object{"schema": "researchos.harness-event.v1", "event": event}), Empty())
	if err != nil {
		return 0, err
	}
	if err = bump(state); err != nil {
		return 0, err
	}
	state["event_sequence"] = sequence
	if err = h.c.service.put(tx, "ProjectState", state); err != nil {
		return 0, err
	}
	envelope := Object{"id": eventID, "project_id": project, "revision": 1, "created_at": Now(), "sequence": sequence, "event_type": "TASK_CHANGED", "aggregate_ref": Ref(task, "Task"), "actor_id": actor, "correlation_id": eventID, "causation_id": nil, "event_data_artifact_ref": Ref(artifact, "Artifact")}
	envelope["receipt_hash"] = Receipt(envelope)
	if err = h.c.service.put(tx, "EventEnvelope", envelope); err != nil {
		return 0, err
	}
	if _, err = tx.Exec("INSERT INTO outbox(project,sequence,id,body) VALUES(?,?,?,?)", project, sequence, eventID, string(Bytes(envelope))); err != nil {
		return 0, err
	}
	_, err = tx.Exec("INSERT INTO event_state_snapshots(project,event_id,revision,body) VALUES(?,?,?,?)", project, eventID, state["revision"], string(Bytes(state)))
	return sequence, err
}
func (h *harnessV1) readEvents(tx *sql.Tx, project, id string) ([]Object, error) {
	rows, err := tx.Query("SELECT body FROM outbox WHERE project=? AND json_extract(body,'$.aggregate_ref.entity_type')='Task' AND json_extract(body,'$.aggregate_ref.id')=? AND json_extract(body,'$.event_data_artifact_ref.id') IS NOT NULL ORDER BY sequence LIMIT 5001", project, id)
	if err != nil {
		return nil, err
	}
	var envelopes []Object
	for rows.Next() {
		var raw string
		if err = rows.Scan(&raw); err != nil {
			rows.Close()
			return nil, err
		}
		ev, err := Decode([]byte(raw))
		if err != nil {
			rows.Close()
			return nil, err
		}
		envelopes = append(envelopes, ev)
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return nil, err
	}
	if len(envelopes) > 5000 {
		return nil, errors.New("harness event budget exceeded")
	}
	events := make([]Object, 0, len(envelopes))
	for _, ev := range envelopes {
		if ev["receipt_hash"] != Receipt(ev) {
			return nil, errors.New("event receipt changed")
		}
		ref, ok := ev["event_data_artifact_ref"].(map[string]any)
		if !ok {
			return nil, errors.New("event data missing")
		}
		artifact, err := version(tx, project, ref)
		if err != nil {
			return nil, err
		}
		var raw []byte
		if err = tx.QueryRow("SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1", project, artifact["storage_key"]).Scan(&raw); err != nil {
			return nil, err
		}
		if Digest(raw) != artifact["content_hash"] {
			return nil, errors.New("event data seal changed")
		}
		wrapper, err := Decode(raw)
		if err != nil {
			return nil, err
		}
		if wrapper["schema"] != "researchos.harness-event.v1" {
			continue
		}
		event, ok := wrapper["event"].(map[string]any)
		if !ok {
			return nil, errors.New("native event malformed")
		}
		seq, _ := Num(ev, "sequence")
		if event["event_id"] != ev["id"] || event["sequence"] != strconv.FormatInt(seq, 10) || Hash(event["task_ref"]) != Hash(harnessRef(project, id)) {
			return nil, errors.New("native event binding changed")
		}
		events = append(events, event)
	}
	return events, nil
}
func (h *harnessV1) Events(ctx context.Context, token string, in HarnessEvents) (Object, error) {
	if !harnessLabel(in.ProjectID, 128) || !harnessLabel(in.TaskID, 128) || in.Limit < 1 || in.Limit > 500 {
		return nil, harnessFail(400, "INVALID_REQUEST", "project/task/limit invalid")
	}
	cursor, err := HarnessDecimal(in.Cursor, false)
	if err != nil {
		return nil, err
	}
	tx, p, err := h.auth(ctx, token, in.ProjectID)
	if err != nil {
		return nil, err
	}
	defer tx.Rollback()
	task, record, request, err := h.record(tx, p.ID, in.ProjectID, in.TaskID)
	if err != nil {
		return nil, err
	}
	view, err := h.taskView(tx, in.ProjectID, task, record, request)
	if err != nil {
		return nil, err
	}
	events, err := h.readEvents(tx, in.ProjectID, in.TaskID)
	if err != nil {
		return nil, err
	}
	tail := int64(0)
	found := cursor == 0
	for _, event := range events {
		seq, _ := HarnessDecimal(Str(event, "sequence"), true)
		if seq > tail {
			tail = seq
		}
		if seq == cursor {
			found = true
		}
	}
	if cursor > tail || !found {
		return harnessEnvelope(Object{"task_ref": harnessRef(in.ProjectID, in.TaskID), "events": Empty(), "next_cursor": strconv.FormatInt(tail, 10), "has_more": false, "end": view["terminal"], "reset": true, "snapshot": view}), nil
	}
	page := Empty()
	more := false
	next := cursor
	terminalSeen := false
	for _, event := range events {
		seq, _ := HarnessDecimal(Str(event, "sequence"), true)
		if seq <= cursor {
			if event["kind"] == "TASK_TERMINAL" {
				terminalSeen = true
			}
			continue
		}
		if len(page) >= in.Limit {
			more = true
			break
		}
		page = append(page, event)
		next = seq
		if event["kind"] == "TASK_TERMINAL" {
			terminalSeen = true
		}
	}
	return harnessEnvelope(Object{"task_ref": harnessRef(in.ProjectID, in.TaskID), "events": page, "next_cursor": strconv.FormatInt(next, 10), "has_more": more, "end": view["terminal"] == true && !more && terminalSeen, "reset": false, "snapshot": nil}), nil
}
func (h *harnessV1) Cancel(ctx context.Context, token, project, id string, in HarnessCancel) (Object, error) {
	if !harnessLabel(project, 128) || !harnessLabel(id, 128) {
		return nil, harnessFail(400, "INVALID_REQUEST", "project/task required")
	}
	if err := in.Validate(); err != nil {
		return nil, err
	}
	tx, p, err := h.auth(ctx, token, project)
	if err != nil {
		return nil, err
	}
	defer tx.Rollback()
	if err = resourceWriteLock(tx); err != nil {
		return nil, err
	}
	hash := Hash(Object{"task_id": id, "request": in})
	replay, err := harnessReplay(tx, p.ID, project, "harness:v1:cancel", in.RequestID, hash)
	if err != nil || replay != nil {
		return replay, err
	}
	task, record, request, err := h.record(tx, p.ID, project, id)
	if err != nil {
		return nil, err
	}
	view, err := h.taskView(tx, project, task, record, request)
	if err != nil {
		return nil, err
	}
	revision, _ := Num(task, "revision")
	conflict := func() error {
		value := strconv.FormatInt(revision, 10)
		var run Object
		if current, ok := view["run"].(map[string]any); ok {
			run = current
		}
		return &HarnessError{Status: 409, Code: "STATE_CONFLICT", Message: "current task/run changed", TaskRef: harnessRef(project, id), Revision: &value, Run: run}
	}
	if strconv.FormatInt(revision, 10) != in.ExpectedTaskRevision {
		return nil, conflict()
	}
	current, hasRun := view["run"].(map[string]any)
	if hasRun {
		if in.ExpectedRunID == nil || *in.ExpectedRunID != Str(current, "run_id") || *in.ExpectedEpoch != Str(current, "epoch") {
			return nil, conflict()
		}
	} else if in.ExpectedRunID != nil {
		return nil, conflict()
	}
	disposition := "ALREADY_TERMINAL"
	if view["terminal"] != true {
		if !hasRun {
			task["status"] = "CANCELLED"
			if err = bump(task); err != nil {
				return nil, err
			}
			if err = h.c.service.put(tx, "Task", task); err != nil {
				return nil, err
			}
			view, err = h.taskView(tx, project, task, record, request)
			if err != nil {
				return nil, err
			}
			if _, err = h.emit(tx, p.ID, project, task, nil, "TASK_TERMINAL", Object{"status": "CANCELLED", "task": view}); err != nil {
				return nil, err
			}
			disposition = "CANCELLED_BEFORE_LAUNCH"
		} else {
			run, _, _, err := h.c.service.runtimeOperation(tx, p, project, Str(current, "run_id"), Object{"reason": "Authenticated Host V1 cancellation"}, "cancelRun", ID())
			if err != nil {
				return nil, err
			}
			task, err = load(tx, project, "Task", id)
			if err != nil {
				return nil, err
			}
			view, err = h.taskView(tx, project, task, record, request)
			if err != nil {
				return nil, err
			}
			if _, err = h.emit(tx, p.ID, project, task, run, "RUN_STATE", Object{"status": "CANCEL_REQUESTED"}); err != nil {
				return nil, err
			}
			disposition = "CANCEL_REQUESTED"
		}
	}
	response := harnessEnvelope(Object{"task": view, "disposition": disposition})
	if _, err = tx.Exec("INSERT INTO idempotency(principal,project,operation,key,request_hash,status,body,headers,created_at) VALUES(?,?,?,?,?,200,?,'{}',?)", p.ID, project, "harness:v1:cancel", in.RequestID, hash, string(Bytes(response)), Now()); err != nil {
		return nil, err
	}
	return response, tx.Commit()
}

// Native Harness tasks share this Coordinator's scan lease and claimTaskMode.
// The sealed Host submission selects this branch; generic task labels do not.
func (c *RuntimeCoordinator) scanHarness(ctx context.Context) error {
	if c.config.HarnessDriver == nil || c.config.HarnessAuthority == nil {
		return nil
	}
	owner, err := c.config.HarnessAuthority.HarnessPrincipal(ctx)
	if err != nil {
		return err
	}
	_, readiness := harnessReadiness(c.config.HarnessDriver)
	if !rt.CodexAllowsPreparation(readiness) {
		return nil
	}
	rows, err := c.service.DB.QueryContext(ctx, "SELECT project,id FROM domain_objects WHERE kind='Task' AND json_extract(body,'$.status')='READY' AND json_extract(body,'$.task_type')='harness_turn' ORDER BY rowid")
	if err != nil {
		return err
	}
	type candidate struct{ project, id string }
	items := []candidate{}
	for rows.Next() {
		var item candidate
		if err = rows.Scan(&item.project, &item.id); err != nil {
			break
		}
		items = append(items, item)
	}
	err = errors.Join(err, rows.Err())
	rows.Close()
	if err != nil {
		return err
	}
	port := &harnessV1{c: c}
	for _, item := range items {
		token, err := c.service.IssueCredential(ctx, owner, 15*time.Minute)
		if err != nil {
			return err
		}
		tx, p, err := port.auth(ctx, token, item.project)
		if err != nil {
			return err
		}
		task, record, requestID, err := port.record(tx, p.ID, item.project, item.id)
		if err != nil {
			tx.Rollback()
			continue
		}
		binding, err := port.workspace(ctx, tx, p, item.project, Str(record["request"].(map[string]any), "workspace_ref"))
		validSource := err == nil && harnessSourceBindingMatches(record, binding)
		tx.Rollback()
		if !validSource {
			continue
		}
		route, err := port.ensureRuntime(ctx, token, p, item.project)
		if err != nil {
			return err
		}
		// A historical V2 Task keeps its original runtime/profile binding. The
		// new RPC V3 route must never claim or silently upgrade it.
		if record["runtime_id"] != route.runtimeID || Hash(record["profile_ref"]) != Hash(route.profileRef) {
			continue
		}
		tx, err = c.service.DB.BeginTx(ctx, nil)
		if err != nil {
			return err
		}
		if err = resourceWriteLock(tx); err != nil {
			tx.Rollback()
			return err
		}
		scheduler, err := resourcePrincipal(tx, route.schedulerToken, item.project, "SCHEDULER")
		if err != nil {
			tx.Rollback()
			return err
		}
		task, err = load(tx, item.project, "Task", item.id)
		if err != nil {
			tx.Rollback()
			return err
		}
		result, err := c.service.claimTaskMode(tx, scheduler, item.project, item.id, Object{"runtime_id": route.runtimeID, "executor_principal_id": route.executor, "context_bundle_id": task["context_bundle_id"]}, ID(), false)
		if err != nil {
			tx.Rollback()
			var fault *Fault
			if errors.As(err, &fault) {
				continue
			}
			return err
		}
		run := result["run"].(map[string]any)
		task, err = load(tx, item.project, "Task", item.id)
		if err != nil {
			tx.Rollback()
			return err
		}
		view, err := port.taskView(tx, item.project, task, record, requestID)
		if err == nil {
			_, err = port.emit(tx, p.ID, item.project, task, run, "RUN_STARTED", Object{"status": "STARTING", "task": view})
		}
		if err != nil {
			tx.Rollback()
			return err
		}
		if err = tx.Commit(); err != nil {
			return err
		}
		c.boundary("harness_claim_committed", run)
		c.workers.Add(1)
		go func(project string, route harnessRoute, run Object, lease string) {
			defer c.workers.Done()
			if err := c.runHarness(ctx, project, route, run, lease); err != nil {
				select {
				case c.errors <- err:
				default:
				}
			}
		}(item.project, route, run, Str(result, "lease_token"))
	}
	return nil
}
func (c *RuntimeCoordinator) harnessGate(ctx context.Context, project string, route harnessRoute, runID, lease string, epoch int64) (*sql.Tx, Object, Object, error) {
	tx, err := c.service.DB.BeginTx(ctx, nil)
	if err != nil {
		return nil, nil, nil, err
	}
	fail := func(err error) (*sql.Tx, Object, Object, error) { tx.Rollback(); return nil, nil, nil, err }
	if err = resourceWriteLock(tx); err != nil {
		return fail(err)
	}
	executor, err := resourcePrincipal(tx, route.executorToken, project, "EXECUTOR")
	if err != nil {
		return fail(err)
	}
	run, err := currentRun(tx, executor, project, runID)
	if err != nil {
		return fail(err)
	}
	if run["runtime_id"] != route.runtimeID || runTerminal(run) || run["status"] == "CANCEL_REQUESTED" || run["status"] == "RECONCILING" || run["status"] == "LOST" {
		return fail(Fail(409, "STATE_CONFLICT", "native Run cannot execute"))
	}
	if err = runtimeLease(tx, executor, project, run, Object{"lease_token": lease, "lease_epoch": epoch}); err != nil {
		return fail(err)
	}
	dispatch, err := runtimeDispatch(tx, project, runID, epoch)
	if err != nil {
		return fail(err)
	}
	task, err := load(tx, project, "Task", Str(run, "task_id"))
	if err != nil {
		return fail(err)
	}
	admission, err := c.service.currentDispatchAdmission(tx, project, task, run, dispatch, "native-launch")
	if err != nil {
		return fail(err)
	}
	if admission["admission_kind"] != "HOST_HARNESS_V1" {
		return fail(Fail(403, "FORBIDDEN", "native admission required"))
	}
	descriptor, readiness := harnessReadiness(c.config.HarnessDriver)
	profile := admission["profile"].(map[string]any)
	if !rt.CodexAllowsPreparation(readiness) || !harnessPolicyMatches(profile, rt.CodexExpectedPolicyIdentity(descriptor)) {
		return fail(Fail(503, "HARNESS_UNAVAILABLE", "native policy readiness changed"))
	}
	record, err := harnessTaskInput(tx, project, task)
	if err != nil {
		return fail(err)
	}
	actual, err := c.config.HarnessAuthority.HarnessPrincipal(ctx)
	if err != nil || actual != record["principal_id"] {
		return fail(Fail(403, "FORBIDDEN", "current native Host owner required"))
	}
	principal, err := clientAuthenticatedPrincipal(ctx, tx, actual)
	if err != nil {
		return fail(err)
	}
	binding, err := (&harnessV1{c: c}).workspace(ctx, tx, principal, project, Str(record["request"].(map[string]any), "workspace_ref"))
	if err != nil {
		return fail(err)
	}
	if !harnessSourceBindingMatches(record, binding) {
		return fail(Fail(412, "STALE_INPUT", "native source binding changed or missing"))
	}
	return tx, run, dispatch, nil
}
func harnessNativeIdentity(i rt.CodexIdentity) Object {
	return Object{"pid": i.PID, "process_created_ns": strconv.FormatInt(i.Created, 10), "job": i.Job}
}
func (c *RuntimeCoordinator) runHarness(ctx context.Context, project string, route harnessRoute, run Object, lease string) (runErr error) {
	runID := Str(run, "id")
	epoch, _ := Num(run, "lease_epoch")
	defer func() {
		if runErr != nil {
			_ = c.harnessUnknown(context.Background(), project, runID, epoch, "native completion requires reconciliation")
		}
	}()
	tx, current, dispatch, err := c.harnessGate(ctx, project, route, runID, lease, epoch)
	if err != nil {
		_ = c.harnessUnknown(context.Background(), project, runID, epoch, "native launch authority unavailable")
		return err
	}
	task, err := load(tx, project, "Task", Str(current, "task_id"))
	if err != nil {
		tx.Rollback()
		return err
	}
	record, err := harnessTaskInput(tx, project, task)
	if err != nil {
		tx.Rollback()
		return err
	}
	request := record["request"].(map[string]any)
	principal, err := clientAuthenticatedPrincipal(ctx, tx, Str(record, "principal_id"))
	if err != nil {
		tx.Rollback()
		return err
	}
	binding, err := (&harnessV1{c: c}).workspace(ctx, tx, principal, project, Str(request, "workspace_ref"))
	if err != nil {
		tx.Rollback()
		return err
	}
	if !harnessSourceBindingMatches(record, binding) {
		tx.Rollback()
		return c.harnessUnknown(ctx, project, runID, epoch, "native source binding changed")
	}
	profile := dispatch["manifest"].(map[string]any)["admission"].(map[string]any)["profile"].(map[string]any)
	descriptor, readiness := harnessReadiness(c.config.HarnessDriver)
	if !rt.CodexAllowsPreparation(readiness) || !harnessPolicyMatches(profile, rt.CodexExpectedPolicyIdentity(descriptor)) {
		tx.Rollback()
		return c.harnessUnknown(ctx, project, runID, epoch, "native executable or policy changed")
	}
	worker := ID()
	locator := Str(dispatch, "dispatch_key")
	changed, err := tx.Exec("UPDATE runtime_dispatches SET state='STARTED',worker=?,journal_locator=?,updated_at=? WHERE project=? AND run=? AND epoch=? AND state='PREPARED' AND worker=''", worker, locator, Now(), project, runID, epoch)
	if err != nil {
		tx.Rollback()
		return err
	}
	n, err := changed.RowsAffected()
	if err != nil || n != 1 {
		tx.Rollback()
		return Fail(409, "STATE_CONFLICT", "native dispatch attempted; no relaunch")
	}
	if err = tx.Commit(); err != nil {
		return err
	}
	child, cancel := context.WithCancel(ctx)
	defer cancel()
	handle, err := c.config.HarnessDriver.Start(child, rt.CodexLaunch{TaskID: Str(task, "id"), RunID: runID, Epoch: strconv.FormatInt(epoch, 10), Workspace: binding.RealPath, Prompt: Str(request, "prompt"), Directory: filepath.Join(c.config.DataRoot, "runtime-dispatches", locator), SourceBindingHash: Hash(record["source_binding"]), Timeout: 300 * time.Second}, rt.CodexCallbacks{
		BeforeResume: func(identity rt.CodexIdentity) error {
			tx, run, fresh, err := c.harnessGate(child, project, route, runID, lease, epoch)
			if err != nil {
				return err
			}
			defer tx.Rollback()
			freshBinding, bindErr := (&harnessV1{c: c}).workspace(child, tx, principal, project, Str(request, "workspace_ref"))
			if bindErr != nil || !harnessSourceBindingMatches(record, freshBinding) || freshBinding.RealPath != binding.RealPath || freshBinding.Revision != binding.Revision {
				return Fail(412, "STALE_INPUT", "native source changed before resume")
			}
			if fresh["state"] != "STARTED" || fresh["worker"] != worker || len(fresh["identity"].(map[string]any)) != 0 {
				return Fail(409, "STATE_CONFLICT", "native launch fence consumed")
			}
			if _, err = tx.Exec("UPDATE runtime_dispatches SET identity=?,updated_at=? WHERE project=? AND run=? AND epoch=? AND worker=? AND state='STARTED'", string(Bytes(harnessNativeIdentity(identity))), Now(), project, runID, epoch, worker); err != nil {
				return err
			}
			executor, err := authenticate(tx, route.executorToken)
			if err != nil {
				return err
			}
			run, _, _, err = c.service.runtimeOperation(tx, executor, project, runID, Object{"lease_token": lease, "lease_epoch": epoch, "external_run_id": nil, "checkpoint_artifact_id": nil}, "heartbeatRun", ID())
			if err != nil {
				return err
			}
			task, err := load(tx, project, "Task", Str(run, "task_id"))
			if err != nil {
				return err
			}
			_, err = (&harnessV1{c: c}).emit(tx, principal.ID, project, task, run, "RUN_STATE", Object{"status": "RUNNING"})
			if err != nil {
				return err
			}
			return tx.Commit()
		},
		BeforeModelTurn: func(evidence rt.CodexTurnEvidence) error {
			if child.Err() != nil || evidence.TaskID != Str(task, "id") || evidence.RunID != runID || evidence.Epoch != strconv.FormatInt(epoch, 10) ||
				evidence.SourceBindingHash != Hash(record["source_binding"]) || evidence.PolicyIdentity != rt.CodexExpectedPolicyIdentity(c.config.HarnessDriver.Descriptor()) {
				return Fail(412, "STALE_INPUT", "native turn evidence changed before first prompt")
			}
			tx, current, fresh, err := c.harnessGate(child, project, route, runID, lease, epoch)
			if err != nil {
				return err
			}
			defer tx.Rollback()
			if current["status"] == "CANCEL_REQUESTED" || runTerminal(current) || fresh["state"] != "STARTED" || fresh["worker"] != worker ||
				fresh["journal_locator"] != locator || Hash(fresh["identity"]) != Hash(harnessNativeIdentity(evidence.Process)) {
				return Fail(409, "STATE_CONFLICT", "native turn fence no longer owns original Run and process")
			}
			currentTask, err := load(tx, project, "Task", Str(current, "task_id"))
			if err != nil {
				return err
			}
			if currentTask["status"] != "RUNNING" {
				return Fail(409, "STATE_CONFLICT", "native Task is not eligible for a first turn")
			}
			freshBinding, err := (&harnessV1{c: c}).workspace(child, tx, principal, project, Str(request, "workspace_ref"))
			if err != nil || !harnessSourceBindingMatches(record, freshBinding) || freshBinding.RealPath != binding.RealPath || freshBinding.Revision != binding.Revision {
				return Fail(412, "STALE_INPUT", "native source changed before first prompt")
			}
			if err := writeHarnessTurnAuthorization(c.config.DataRoot, locator, evidence, fresh, worker); err != nil {
				return err
			}
			_, err = c.service.serverArtifactMode(tx, project, principal.ID, "LOG", "LIVE", Bytes(Object{
				"schema": "researchos.native-turn-authorization.v1", "run_id": runID,
				"epoch": epoch, "dispatch_key": fresh["dispatch_key"],
				"evidence_hash": Hash(evidence), "state": "HOST_TURN_AUTHORIZATION_CONSUMED",
			}), Empty())
			if err != nil {
				return err
			}
			return tx.Commit()
		},
		Event: func(event rt.CodexEvent) error {
			tx, err := c.service.DB.BeginTx(context.Background(), nil)
			if err != nil {
				return err
			}
			defer tx.Rollback()
			if err = resourceWriteLock(tx); err != nil {
				return err
			}
			run, err := load(tx, project, "Run", runID)
			if err != nil {
				return err
			}
			if Hash(run["lease_epoch"]) != Hash(epoch) || runTerminal(run) {
				return errors.New("native event epoch closed")
			}
			task, err := load(tx, project, "Task", Str(run, "task_id"))
			if err != nil {
				return err
			}
			payload := Object{"text": event.Text}
			if event.Kind == "TOOL_EVENT" {
				payload = Object{"tool": Object{"id": event.ToolID, "name": event.ToolName, "phase": event.ToolPhase, "summary": event.Text}}
			}
			_, err = (&harnessV1{c: c}).emit(tx, principal.ID, project, task, run, event.Kind, payload)
			if err != nil {
				return err
			}
			return tx.Commit()
		}})
	if err != nil {
		_ = c.harnessUnknown(context.Background(), project, runID, epoch, "native launch acknowledgement unavailable")
		return err
	}
	pulseDone := make(chan struct{})
	stopPulse := make(chan struct{})
	go func() {
		defer close(pulseDone)
		tick := time.NewTicker(150 * time.Millisecond)
		defer tick.Stop()
		lastHeartbeat := time.Now()
		for {
			select {
			case <-stopPulse:
				return
			case <-child.Done():
				handle.Cancel()
				return
			case <-tick.C:
				tx, run, _, err := c.harnessGate(context.Background(), project, route, runID, lease, epoch)
				if err != nil {
					handle.Cancel()
					return
				}
				if time.Since(lastHeartbeat) >= 10*time.Second {
					executor, e := authenticate(tx, route.executorToken)
					if e == nil {
						_, _, _, e = c.service.runtimeOperation(tx, executor, project, runID, Object{"lease_token": lease, "lease_epoch": epoch, "external_run_id": run["external_run_id"], "checkpoint_artifact_id": nil}, "heartbeatRun", ID())
					}
					if e == nil {
						e = tx.Commit()
					} else {
						tx.Rollback()
					}
					if e != nil {
						handle.Cancel()
						return
					}
					lastHeartbeat = time.Now()
				} else {
					tx.Rollback()
				}
			}
		}
	}()
	// Wait for stopped/drained ownership even after request or parent cancellation.
	result, waitErr := handle.Wait(context.Background())
	close(stopPulse)
	<-pulseDone
	if preparation, known := rt.CodexPreparationFailureForHandle(handle); known {
		return c.finishHarnessPreparationFailure(harnessPreparationFence{
			project: project, runID: runID, taskID: Str(task, "id"), worker: worker,
			locator: locator, manifestHash: Str(dispatch, "manifest_hash"), epoch: epoch,
			launch: rt.CodexLaunch{TaskID: Str(task, "id"), RunID: runID, Epoch: strconv.FormatInt(epoch, 10),
				Workspace: binding.RealPath, SourceBindingHash: Hash(record["source_binding"])},
			policy: rt.CodexExpectedPolicyIdentity(descriptor),
		}, preparation)
	}
	if waitErr != nil || !result.Stopped || !result.StreamsDrained || !result.CleanupComplete || result.State == "UNKNOWN" {
		_ = c.harnessUnknown(context.Background(), project, runID, epoch, "native terminal facts incomplete")
		return errors.Join(waitErr, errors.New("native outcome unknown"))
	}
	tx, err = c.service.DB.BeginTx(context.Background(), nil)
	if err != nil {
		return err
	}
	dispatch, err = runtimeDispatch(tx, project, runID, epoch)
	if err != nil {
		tx.Rollback()
		return err
	}
	if Hash(dispatch["identity"]) != Hash(harnessNativeIdentity(result.Identity)) {
		tx.Rollback()
		return c.harnessUnknown(context.Background(), project, runID, epoch, "native result identity mismatch")
	}
	resultBytes := Bytes(Object{"schema": "researchos.codex-result.v1", "assistant_text": result.Assistant, "cli_thread_id": result.ThreadID, "execution_state": result.State, "failure": result.Failure})
	artifact, err := c.recoverArtifact(tx, project, dispatch, resultBytes, "REPORT")
	if err != nil {
		tx.Rollback()
		return err
	}
	if err = tx.Commit(); err != nil {
		return err
	}
	state := "FAILED"
	if result.State == "COMPLETED" {
		state = "SETTLED"
	} else if result.State == "CANCELLED" {
		state = "CANCELLED"
	}
	observation := Object{"spec": Object{"run_id": runID, "task_id": task["id"], "epoch": epoch}, "state": state, "dispatch_key": dispatch["dispatch_key"], "manifest_hash": dispatch["manifest_hash"], "worker": dispatch["worker"], "identity": dispatch["identity"], "observation_sequence": 1, "children_stopped": true, "streams_drained": true, "cleanup_complete": true, "queue_empty": true, "ended": Now(), "exit_code": result.ExitCode, "protocol": Object{"settled": state == "SETTLED"}, "artifacts": []any{Object{"content_hash": artifact["content_hash"], "byte_size": artifact["byte_size"]}}}
	if err = c.service.observeRuntime(context.Background(), project, runID, epoch, observation, true); err != nil {
		return err
	}
	return c.finishHarness(context.Background(), project, runID, epoch)
}
func (c *RuntimeCoordinator) harnessUnknown(ctx context.Context, project, runID string, epoch int64, reason string) error {
	// Harness UNKNOWN is one durable projection, not an acknowledged terminal
	// state followed by a best-effort event. Preserve the original queue fence
	// and historical OBSERVED proof; any event failure rolls this transaction
	// back while the already-claimed Run/dispatch still prevents a new launch.
	tx, err := c.service.DB.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	if err = resourceWriteLock(tx); err != nil {
		return err
	}
	abandoned, err := preparedRunAbandonmentExists(tx, project, runID, epoch)
	if err != nil {
		return err
	}
	if abandoned {
		return nil
	}
	if err = unknownClientRunQueue(tx, project, runID, reason); err != nil {
		return err
	}
	if _, err = tx.Exec("UPDATE runtime_dispatches SET state=CASE WHEN state='OBSERVED' THEN state ELSE 'UNKNOWN' END,reason=?,updated_at=? WHERE project=? AND run=? AND epoch=?", reason, Now(), project, runID, epoch); err != nil {
		return err
	}
	run, err := load(tx, project, "Run", runID)
	if err != nil {
		return err
	}
	if Hash(run["lease_epoch"]) == Hash(epoch) && !runTerminal(run) {
		if err = c.projectSessionRun(tx, project, run, nil, "Runtime outcome is unconfirmed: "+reason+"; wait for effect and process reconciliation."); err != nil {
			return err
		}
	}
	task, err := load(tx, project, "Task", Str(run, "task_id"))
	if err != nil {
		return err
	}
	if err = c.harnessTerminalInTx(tx, project, task, run); err != nil {
		return err
	}
	return tx.Commit()
}
func (c *RuntimeCoordinator) harnessTerminalEvent(ctx context.Context, project, runID string) error {
	tx, err := c.service.DB.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	if err = resourceWriteLock(tx); err != nil {
		return err
	}
	run, err := load(tx, project, "Run", runID)
	if err != nil {
		return err
	}
	task, err := load(tx, project, "Task", Str(run, "task_id"))
	if err != nil {
		return err
	}
	if err = c.harnessTerminalInTx(tx, project, task, run); err != nil {
		return err
	}
	return tx.Commit()
}
func (c *RuntimeCoordinator) harnessTerminalInTx(tx *sql.Tx, project string, task, run Object) error {
	port := &harnessV1{c: c}
	record, err := harnessTaskInput(tx, project, task)
	if err != nil {
		return err
	}
	request := record["request"].(map[string]any)
	view, err := port.taskView(tx, project, task, record, Str(request, "request_id"))
	if err != nil {
		return err
	}
	if view["terminal"] != true {
		return nil
	}
	events, err := port.readEvents(tx, project, Str(task, "id"))
	if err != nil {
		return err
	}
	for _, event := range events {
		if event["kind"] == "TASK_TERMINAL" {
			prior, _ := event["payload"].(map[string]any)
			if prior["status"] == view["status"] && Hash(event["run"]) == Hash(harnessRunRef(run)) {
				return nil
			}
		}
	}
	_, err = port.emit(tx, Str(record, "principal_id"), project, task, run, "TASK_TERMINAL", Object{"status": view["status"], "task": view, "error": view["failure"]})
	return err
}
func (c *RuntimeCoordinator) finishHarness(ctx context.Context, project, runID string, epoch int64) error {
	tx, err := c.service.DB.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	if err = resourceWriteLock(tx); err != nil {
		return err
	}
	run, err := load(tx, project, "Run", runID)
	if err != nil {
		return err
	}
	if Hash(run["lease_epoch"]) != Hash(epoch) {
		return errors.New("native epoch changed")
	}
	task, err := load(tx, project, "Task", Str(run, "task_id"))
	if err != nil {
		return err
	}
	if runTerminal(run) {
		if err = c.harnessTerminalInTx(tx, project, task, run); err != nil {
			return err
		}
		return tx.Commit()
	}
	observation, err := runtimeObservation(tx, project, run)
	if err != nil {
		return err
	}
	dispatch, err := nativeDispatchProof(tx, project, run, observation)
	if err != nil {
		return err
	}
	ids := Empty()
	for _, value := range Arr(observation, "artifacts") {
		item := value.(map[string]any)
		var id string
		if err = tx.QueryRow("SELECT a.id FROM artifact_uses u JOIN domain_objects a ON a.project=u.project AND a.kind='Artifact' AND a.id=u.artifact WHERE u.project=? AND u.run=? AND u.epoch=? AND json_extract(a.body,'$.content_hash')=? AND json_extract(a.body,'$.byte_size')=CAST(? AS INTEGER)", project, runID, epoch, item["content_hash"], item["byte_size"]).Scan(&id); err != nil {
			return err
		}
		ids = append(ids, id)
	}
	executor := Principal{ID: Str(run, "executor_principal_id"), Roles: []string{"EXECUTOR"}, Grants: []Grant{{ProjectID: project, TaskID: Str(task, "id"), RunID: runID}}}
	body := Object{"lease_epoch": epoch, "runtime_settled": true, "execution_report": "Host observed native Codex process completion; business acceptance remains separate.", "exit_code": observation["exit_code"], "result_artifact_ids": ids, "checkpoint_artifact_id": run["checkpoint_artifact_id"]}
	op := "reportRun"
	if run["status"] == "CANCEL_REQUESTED" {
		if observation["state"] != "CANCELLED" {
			return errors.New("cancellation completion requires exact stopped receipt")
		}
		receipt, err := c.recoverArtifact(tx, project, dispatch, Bytes(observation), "LOG")
		if err != nil {
			return err
		}
		body["receipt_artifact_ref"] = Ref(receipt, "Artifact")
		op = "acknowledgeRunCancellation"
	} else if observation["state"] == "CANCELLED" {
		return errors.New("stopped native Run without committed cancellation remains unknown")
	}
	run, _, _, err = c.service.runtimeOperationMode(tx, executor, project, runID, body, op, ID(), true)
	if err != nil {
		return err
	}
	task, err = load(tx, project, "Task", Str(run, "task_id"))
	if err != nil {
		return err
	}
	if err = c.harnessTerminalInTx(tx, project, task, run); err != nil {
		return err
	}
	return tx.Commit()
}
