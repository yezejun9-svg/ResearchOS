//go:build windows

package domain

import (
	"context"
	"database/sql"
	"encoding/hex"
	"strings"
	"sync"
	"time"
	"unicode/utf8"

	rt "researchos.local/research-os/adapters/runtime"
)

const runtimePermissionLifetime = 2 * time.Minute

type runtimePermissionKey struct {
	coordinator          *RuntimeCoordinator
	project, run, effect string
}

type runtimePermissionWaiter struct {
	session, request, digest, lease string
	epoch                           int64
}

// A waiter is process-local proof that the original STARTED effect is still
// blocked before RunTool. Restart recovery never resumes or replays this effect.
var runtimePermissionWaiters sync.Map

func permissionSelection(policy Object, tool string) (bool, error) {
	raw, present := policy["user_confirmation_tools"]
	if !present {
		return false, nil
	}
	list, ok := raw.([]any)
	if !ok {
		return false, Fail(403, "POLICY_DENIED", "frozen confirmation policy must be an array")
	}
	selected := false
	seen := map[string]bool{}
	for _, value := range list {
		name, ok := value.(string)
		if !ok || name != "write" && name != "edit" || seen[name] {
			return false, Fail(403, "POLICY_DENIED", "frozen confirmation policy contains an invalid tool")
		}
		seen[name] = true
		selected = selected || name == tool
	}
	return selected, nil
}

func permissionStaticToolGate(request RuntimeToolRequest) error {
	if request.Access != "READ_WRITE" {
		return Fail(403, "POLICY_DENIED", "workspace is not writable")
	}
	path := Str(request.Arguments, "path")
	if path == "" || strings.HasPrefix(path, "/") || strings.Contains(path, "\\") || strings.Contains(path, ":") || strings.Contains(path, "//") || path == "." || strings.HasPrefix(path, "../") || strings.Contains(path, "/../") || strings.HasSuffix(path, "/..") || strings.HasPrefix(path, "./") || strings.Contains(path, "/./") {
		return Fail(403, "POLICY_DENIED", "tool path is not a canonical relative path")
	}
	allowed := false
	for _, value := range Arr(request.Policy, "write_paths") {
		allowed = allowed || value == path
	}
	if !allowed {
		return Fail(403, "POLICY_DENIED", "tool path is outside frozen write permission")
	}
	max, err := Num(request.Policy, "max_write_bytes")
	if err != nil || max < 1 {
		return Fail(403, "POLICY_DENIED", "frozen write byte limit is unavailable")
	}
	expected, present := request.Arguments["expected_hash"]
	if !present || expected == nil && request.Name == "edit" {
		return Fail(400, "INVALID_REQUEST", "original write hash is unavailable")
	}
	if expected != nil {
		hash, ok := expected.(string)
		if !ok || len(hash) != len("sha256:")+64 || !strings.HasPrefix(hash, "sha256:") {
			return Fail(400, "INVALID_REQUEST", "original write hash is invalid")
		}
		if _, err := hex.DecodeString(strings.TrimPrefix(hash, "sha256:")); err != nil {
			return Fail(400, "INVALID_REQUEST", "original write hash is invalid")
		}
	}
	if request.Name == "write" {
		content, ok := request.Arguments["content"].(string)
		if !ok || !utf8.ValidString(content) || int64(len(content)) > max || len(content) > 2<<20 {
			return Fail(403, "POLICY_DENIED", "original content exceeds frozen write byte bound")
		}
	} else if _, ok := request.Arguments["old_text"].(string); !ok {
		return Fail(400, "INVALID_REQUEST", "original edit text is invalid")
	} else if _, ok := request.Arguments["new_text"].(string); !ok {
		return Fail(400, "INVALID_REQUEST", "original edit text is invalid")
	}
	for key := range request.Arguments {
		if key != "path" && key != "expected_hash" && key != "content" && (request.Name == "write" || key != "old_text" && key != "new_text") {
			return Fail(400, "INVALID_REQUEST", "original tool has unsupported arguments")
		}
		if request.Name == "edit" && key == "content" {
			return Fail(400, "INVALID_REQUEST", "original edit has unsupported content")
		}
	}
	return nil
}

func (c *RuntimeCoordinator) createToolPermission(ctx context.Context, route RuntimeCoordinatorRoute, runID, lease string, epoch int64, frame rt.BridgeFrame, payload Object, request RuntimeToolRequest) (runtimePermissionKey, runtimePermissionWaiter, error) {
	key := runtimePermissionKey{c, route.ProjectID, runID, frame.Key}
	var waiter runtimePermissionWaiter
	if err := permissionStaticToolGate(request); err != nil {
		return key, waiter, err
	}
	tx, run, dispatch, err := c.dispatchGate(ctx, route, runID, lease, epoch)
	if err != nil {
		return key, waiter, err
	}
	defer tx.Rollback()
	task, err := load(tx, route.ProjectID, "Task", Str(run, "task_id"))
	if err != nil {
		return key, waiter, err
	}
	current, err := c.runtimeToolGate(ctx, tx, route, task, dispatch, frame, payload)
	if err != nil || current.IntentKey != request.IntentKey || Hash(current.Policy) != Hash(request.Policy) || current.Access != request.Access || current.WorkspacePath != request.WorkspacePath {
		return key, waiter, Fail(403, "POLICY_DENIED", "frozen tool authority changed before asking")
	}
	selected, err := permissionSelection(current.Policy, current.Name)
	if err != nil || !selected {
		return key, waiter, Fail(403, "POLICY_DENIED", "tool no longer requires this permission path")
	}
	intent, err := latestEffect(tx, route.ProjectID, runID, frame.Key)
	if err != nil || intent["state"] != "STARTED" {
		return key, waiter, Fail(409, "STATE_CONFLICT", "original tool effect is not waiting")
	}
	if intent["permission"] != nil {
		return key, waiter, Fail(409, "STATE_CONFLICT", "original tool permission scope already exists")
	}
	var sessionID, workspaceRef, modelRef string
	err = tx.QueryRowContext(ctx, `SELECT s.id,s.workspace_ref,s.model_config_ref FROM client_sessions s WHERE s.project_id=? AND s.task_id=? AND s.run_id=? AND s.archived_at IS NULL AND s.sealed_at IS NULL`, route.ProjectID, task["id"], runID).Scan(&sessionID, &workspaceRef, &modelRef)
	if err != nil {
		return key, waiter, err
	}
	principalID, err := clientSessionCreationPrincipal(ctx, tx, route.ProjectID, sessionID)
	if err != nil {
		return key, waiter, Fail(403, "FORBIDDEN", "tool permission session provenance unavailable")
	}
	principal, err := clientPrincipal(ctx, tx, principalID, route.ProjectID, true)
	if err != nil {
		return key, waiter, err
	}
	binding, err := c.service.binding(ctx, tx, workspaceRef)
	if err != nil {
		return key, waiter, err
	}
	manifest, _ := dispatch["manifest"].(map[string]any)
	admission, _ := manifest["admission"].(map[string]any)
	mode := Str(admission, "mode")
	arguments, err := sealPermissionArtifact(c.service, tx, principal, route.ProjectID, Bytes(request.Arguments), mode)
	if err != nil {
		return key, waiter, err
	}
	now := time.Now().UTC()
	expires := now.Add(runtimePermissionLifetime)
	if deadline, ok := ctx.Deadline(); ok && deadline.Before(expires) {
		expires = deadline.UTC()
	}
	if !expires.After(now) {
		return key, waiter, Fail(409, "RESOURCE_BLOCKED", "original tool walltime already elapsed")
	}
	scope := Object{"project_id": route.ProjectID, "task_id": task["id"], "run_id": runID, "tool_name": request.Name,
		"arguments_artifact_ref": Ref(arguments, "Artifact"), "workspace_ref": workspaceRef, "allowed_relative_paths": []any{Str(request.Arguments, "path")},
		"input_refs": permissionTaskInputs(task), "model_config_ref": modelRef, "issued_at": now.Format(time.RFC3339Nano),
		"expires_at": expires.Format(time.RFC3339Nano), "max_uses": 1, "authority": "USER_DECIDABLE"}
	if c.config.ClientSchema == nil {
		return key, waiter, Fail(503, "RESOURCE_UNAVAILABLE", "permission protocol schema unavailable")
	}
	if err = c.config.ClientSchema.ValidateDef("PermissionActionScope", normalizeNumbers(scope)); err != nil {
		return key, waiter, err
	}
	artifact, err := sealPermissionArtifact(c.service, tx, principal, route.ProjectID, Bytes(scope), mode)
	if err != nil {
		return key, waiter, err
	}
	resource, err := c.service.createResourceRequest(tx, principal, route.ProjectID, Object{"category": "PERMISSION", "account_ref": nil,
		"reason_code": "ORIGINAL_TOOL_" + strings.TrimPrefix(Digest([]byte(runID+"/"+frame.Key)), "sha256:"),
		"summary":     "Confirm " + request.Name + " on " + Str(request.Arguments, "path"), "blocked_task_ids": []any{task["id"]},
		"continuable_task_ids": Empty(), "completed_artifact_refs": []any{Ref(artifact, "Artifact"), Ref(arguments, "Artifact")},
		"requested_capability": "Confirm one original workspace tool action", "estimated_cost": nil, "cost_known": false, "resume_checkpoint_ref": nil})
	if err != nil {
		return key, waiter, err
	}
	if err = c.service.event(tx, route.ProjectID, "ResourceRequest", resource, principalID, ID(), "RESOURCE_REQUESTED"); err != nil {
		return key, waiter, err
	}
	waiter = runtimePermissionWaiter{session: sessionID, request: Str(resource, "id"), digest: Hash(scope), lease: lease, epoch: epoch}
	intent["permission"] = Object{"session_id": sessionID, "request_id": waiter.request, "scope_ref": Ref(artifact, "Artifact"),
		"action_digest": waiter.digest, "task_ref": Ref(task, "Task"), "binding_revision": binding.Revision, "principal_id": principalID,
		"decision": nil, "consumed": false}
	if err = effectAppend(tx, route.ProjectID, runID, frame.Key, intent); err != nil {
		return key, waiter, err
	}
	prompt, err := permissionPrompt(c.config.ClientSchema, intent, intent["permission"].(map[string]any), scope, resource)
	if err != nil {
		return key, waiter, err
	}
	if err = appendPermissionEvent(ctx, tx, c.config.ClientSchema, route.ProjectID, sessionID, runID, "PERMISSION_REQUIRED", prompt); err != nil {
		return key, waiter, err
	}
	// Publish the in-process waiter before the transaction becomes visible. A
	// prompt observed immediately after commit must already have its original
	// broker waiter; a failed commit removes that private marker again.
	runtimePermissionWaiters.Store(key, waiter)
	if err = tx.Commit(); err != nil {
		runtimePermissionWaiters.Delete(key)
		return key, waiter, err
	}
	return key, waiter, nil
}

func (c *RuntimeCoordinator) waitToolPermission(ctx context.Context, route RuntimeCoordinatorRoute, key runtimePermissionKey, waiter runtimePermissionWaiter) bool {
	defer runtimePermissionWaiters.Delete(key)
	expiry := runtimePermissionLifetime
	if cutoff, ok := ctx.Deadline(); ok {
		if remaining := time.Until(cutoff); remaining < expiry {
			expiry = remaining
		}
	}
	if expiry <= 0 {
		return false
	}
	deadline := time.NewTimer(expiry)
	defer deadline.Stop()
	tick := time.NewTicker(200 * time.Millisecond)
	defer tick.Stop()
	for {
		select {
		case <-ctx.Done():
			return false
		case <-deadline.C:
			return false
		case <-tick.C:
		}
		tx, _, _, err := c.dispatchGate(ctx, route, key.run, waiter.lease, waiter.epoch)
		if err != nil {
			return false
		}
		intent, err := latestEffect(tx, key.project, key.run, key.effect)
		blocked := false
		if err == nil {
			blocked, err = otherBlockingPermissionResources(tx, key.project, key.run, waiter.request)
		}
		tx.Rollback()
		if err != nil || intent["state"] != "STARTED" {
			return false
		}
		record, ok := intent["permission"].(map[string]any)
		if !ok || record["session_id"] != waiter.session || record["request_id"] != waiter.request || record["action_digest"] != waiter.digest {
			return false
		}
		switch record["decision"] {
		case "ALLOW_ONCE":
			if record["consumed"] != true {
				return false
			}
			if !blocked {
				return true
			}
		case "DENY":
			return false
		case nil:
		default:
			return false
		}
	}
}

func otherBlockingPermissionResources(tx *sql.Tx, project, runID, currentRequest string) (bool, error) {
	var taskID string
	if err := tx.QueryRow(`SELECT json_extract(body,'$.task_id') FROM domain_objects WHERE project=? AND kind='Run' AND id=?`, project, runID).Scan(&taskID); err != nil {
		return false, err
	}
	var count int
	err := tx.QueryRow(`SELECT count(*) FROM domain_objects r, json_each(r.body,'$.blocked_task_ids') b
		WHERE r.project=? AND r.kind='ResourceRequest' AND r.id<>? AND json_extract(r.body,'$.status') IN ('OPEN','ACKNOWLEDGED') AND b.value=?`, project, currentRequest, taskID).Scan(&count)
	return count != 0, err
}

func (c *RuntimeCoordinator) closeToolPermission(ctx context.Context, route RuntimeCoordinatorRoute, key runtimePermissionKey, waiter runtimePermissionWaiter) {
	tx, err := c.service.DB.BeginTx(ctx, nil)
	if err != nil {
		return
	}
	defer tx.Rollback()
	intent, err := latestEffect(tx, key.project, key.run, key.effect)
	if err != nil {
		return
	}
	record, _ := intent["permission"].(map[string]any)
	if record == nil || record["request_id"] != waiter.request || record["decision"] != nil {
		return
	}
	resource, err := load(tx, key.project, "ResourceRequest", waiter.request)
	if err != nil || resource["status"] != "OPEN" && resource["status"] != "ACKNOWLEDGED" {
		return
	}
	principalID := Str(record, "principal_id")
	principal, err := clientPrincipal(ctx, tx, principalID, key.project, true)
	if err != nil {
		return
	}
	dispatch, err := runtimeDispatch(tx, key.project, key.run, waiter.epoch)
	if err != nil {
		return
	}
	manifest, _ := dispatch["manifest"].(map[string]any)
	admission, _ := manifest["admission"].(map[string]any)
	mode := Str(admission, "mode")
	evidence, err := sealPermissionArtifact(c.service, tx, principal, key.project, Bytes(Object{"schema": "researchos.permission-expired.v1",
		"action_digest": waiter.digest, "run_id": key.run, "effect_key": key.effect, "reason": "original waiter ended before a user decision", "observed_at": Now()}), mode)
	if err != nil {
		return
	}
	resolved, err := c.service.resolveResourceRequest(tx, principal, key.project, waiter.request, Object{"resolution_evidence_refs": []any{Ref(evidence, "Artifact")}, "reason": "original waiter ended"})
	if err != nil {
		return
	}
	if err = c.service.event(tx, key.project, "ResourceRequest", resolved, principalID, ID(), "RESOURCE_REQUESTED"); err != nil {
		return
	}
	record["decision"] = "EXPIRED"
	intent["permission"] = record
	if err = effectAppend(tx, key.project, key.run, key.effect, intent); err != nil {
		return
	}
	_ = tx.Commit()
}

func (c *RuntimeCoordinator) CheckPermission(ctx context.Context, tx *sql.Tx, project, sessionID string, intent, record, scope Object) (bool, bool, error) {
	key := runtimePermissionKey{c, project, Str(intent, "run_id"), Str(intent, "key")}
	value, ok := runtimePermissionWaiters.Load(key)
	if !ok {
		return false, false, nil
	}
	waiter := value.(runtimePermissionWaiter)
	if waiter.session != sessionID || waiter.request != record["request_id"] || waiter.digest != record["action_digest"] || Hash(scope) != waiter.digest || intent["state"] != "STARTED" {
		return false, false, Fail(409, "RESOURCE_BLOCKED", "original tool waiter differs from permission scope")
	}
	var route *RuntimeCoordinatorRoute
	routes := c.runtimeRoutes()
	for i := range routes {
		candidate := &routes[i]
		if candidate.ProjectID != project {
			continue
		}
		run, err := load(tx, project, "Run", key.run)
		if err != nil {
			return false, false, err
		}
		if candidate.RuntimeID == run["runtime_id"] {
			if route != nil {
				return false, false, Fail(409, "RESOURCE_BLOCKED", "ambiguous runtime route")
			}
			route = candidate
		}
	}
	if route == nil {
		return false, false, Fail(409, "RESOURCE_BLOCKED", "original runtime route ended")
	}
	executor, err := authenticate(tx, route.ExecutorToken)
	if err != nil {
		return false, false, err
	}
	run, err := currentRun(tx, executor, project, key.run)
	if err != nil {
		return false, false, err
	}
	if runTerminal(run) || run["status"] == "CANCEL_REQUESTED" || runtimeLease(tx, executor, project, run, Object{"lease_token": waiter.lease, "lease_epoch": waiter.epoch}) != nil {
		return false, false, Fail(409, "RESOURCE_BLOCKED", "original run lease ended")
	}
	dispatch, err := runtimeDispatch(tx, project, key.run, waiter.epoch)
	if err != nil {
		return false, false, err
	}
	manifest, _ := dispatch["manifest"].(map[string]any)
	admission, _ := manifest["admission"].(map[string]any)
	artifactRef, _ := record["scope_ref"].(map[string]any)
	artifact, _, err := permissionArtifact(tx, project, artifactRef)
	if err != nil || artifact["measurement_mode"] != admission["mode"] {
		return false, false, Fail(403, "POLICY_DENIED", "original permission evidence mode differs from frozen dispatch")
	}
	task, err := load(tx, project, "Task", Str(run, "task_id"))
	if err != nil {
		return false, false, err
	}
	wire, ok := intent["payload"].(map[string]any)
	if !ok || wire["capability"] != "TOOL" {
		return false, false, Fail(409, "RESOURCE_BLOCKED", "original effect is not a tool")
	}
	payload, ok := wire["payload"].(map[string]any)
	if !ok {
		return false, false, Fail(409, "RESOURCE_BLOCKED", "original tool payload unavailable")
	}
	request, err := c.runtimeToolGate(ctx, tx, *route, task, dispatch, rt.BridgeFrame{Key: key.effect}, payload)
	if err != nil {
		return false, false, err
	}
	paths := Arr(scope, "allowed_relative_paths")
	selected, err := permissionSelection(request.Policy, request.Name)
	if err != nil || !selected || permissionStaticToolGate(request) != nil || request.Name != scope["tool_name"] || Hash(request.Arguments) != permissionArgumentsHash(tx, project, scope) || len(paths) != 1 || Str(request.Arguments, "path") != paths[0] {
		return false, false, Fail(403, "POLICY_DENIED", "original frozen tool permission is no longer valid")
	}
	blocked, err := otherBlockingPermissionResources(tx, project, key.run, waiter.request)
	if err != nil {
		return false, false, err
	}
	return true, !blocked, nil
}

func permissionArgumentsHash(tx *sql.Tx, project string, scope Object) string {
	ref, _ := scope["arguments_artifact_ref"].(map[string]any)
	_, arguments, err := permissionArtifact(tx, project, ref)
	if err != nil {
		return ""
	}
	return Hash(arguments)
}

var _ ClientPermissionAuthority = (*RuntimeCoordinator)(nil)
