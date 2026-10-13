//go:build windows

package domain

import (
	"context"
	"database/sql"
	"errors"
	"path/filepath"
	"strings"

	"github.com/santhosh-tekuri/jsonschema/v6"
	rt "researchos.local/research-os/adapters/runtime"
)

func validateRuntimeToolArguments(config, payload Object) error {
	args, ok := payload["arguments"].(map[string]any)
	if len(payload) != 2 || !ok {
		return Fail(400, "INVALID_REQUEST", "tool request requires only name and arguments")
	}
	name := Str(payload, "name")
	if name != "read" && name != "write" && name != "edit" && name != "run_check" {
		return Fail(403, "FORBIDDEN", "tool is not implemented by this host")
	}
	var schema any
	for _, item := range Arr(config, "tools") {
		tool, _ := item.(map[string]any)
		fn, _ := tool["function"].(map[string]any)
		if fn["name"] == name {
			if schema != nil {
				return Fail(403, "FORBIDDEN", "duplicate frozen tool definition")
			}
			schema = fn["parameters"]
		}
	}
	if schema == nil {
		return Fail(403, "FORBIDDEN", "tool absent from frozen model schema")
	}
	compiler := jsonschema.NewCompiler()
	compiler.UseLoader(localOnly{})
	compiler.AssertFormat()
	compiler.DefaultDraft(jsonschema.Draft2020)
	const location = "https://researchos.local/runtime-tool.json"
	if e := compiler.AddResource(location, schema); e != nil {
		return Fail(403, "FORBIDDEN", "invalid frozen tool schema")
	}
	doc, e := compiler.Compile(location)
	if e != nil {
		return Fail(403, "FORBIDDEN", "frozen tool schema cannot be compiled locally")
	}
	if doc.Validate(args) != nil {
		return Fail(400, "INVALID_REQUEST", "arguments do not match the frozen tool schema")
	}
	return nil
}

func (c *RuntimeCoordinator) runtimeToolGate(ctx context.Context, tx *sql.Tx, route RuntimeCoordinatorRoute, task, dispatch Object, frame rt.BridgeFrame, payload Object) (RuntimeToolRequest, error) {
	var request RuntimeToolRequest
	profile := dispatch["manifest"].(map[string]any)["admission"].(map[string]any)["profile"].(map[string]any)
	config, _ := profile["model_config"].(map[string]any)
	if task["task_type"] != "mu_turn" || c.config.WorkspaceAuthority == nil {
		return request, Fail(403, "FORBIDDEN", "tools require a current authenticated session workspace")
	}
	if e := validateRuntimeToolArguments(config, payload); e != nil {
		return request, e
	}
	policy, ok := profile["tool_policy"].(map[string]any)
	if !ok {
		return request, Fail(403, "FORBIDDEN", "frozen tool policy required")
	}
	limit, e := Num(policy, "max_calls")
	if e != nil || limit < 1 || limit > 32 {
		return request, Fail(403, "FORBIDDEN", "bounded tool calls required")
	}
	var calls int64
	runID := Str(dispatch["manifest"].(map[string]any), "run_id")
	if e = tx.QueryRow(`SELECT count(DISTINCT effect_key) FROM resource_effects WHERE project=? AND run=? AND effect_key<>? AND json_extract(body,'$.payload.capability')='TOOL'`, route.ProjectID, runID, frame.Key).Scan(&calls); e != nil {
		return request, e
	}
	if calls >= limit {
		return request, Fail(403, "FORBIDDEN", "frozen tool call limit exhausted")
	}
	var sessionID, workspace, model string
	if e = tx.QueryRow(`SELECT s.id,s.workspace_ref,s.model_config_ref FROM client_sessions s WHERE s.project_id=? AND s.task_id=? AND s.run_id=? AND s.archived_at IS NULL AND s.sealed_at IS NULL`, route.ProjectID, task["id"], runID).Scan(&sessionID, &workspace, &model); e != nil {
		return request, Fail(403, "FORBIDDEN", "tool session provenance unavailable")
	}
	principal, e := clientSessionCreationPrincipal(ctx, tx, route.ProjectID, sessionID)
	if e != nil {
		return request, Fail(403, "FORBIDDEN", "tool session provenance unavailable")
	}
	if model != Str(config, "ref") {
		return request, Fail(403, "FORBIDDEN", "session model changed")
	}
	if _, e = clientPrincipal(ctx, tx, principal, route.ProjectID, true); e != nil {
		return request, e
	}
	if e = c.ValidateBinding(ctx, tx, principal, route.ProjectID, workspace, model); e != nil {
		return request, e
	}
	if e = c.validateCodingWorkspace(ctx, tx, principal, route.ProjectID, sessionID, workspace, profile); e != nil {
		return request, e
	}
	binding, e := c.service.binding(ctx, tx, workspace)
	if e != nil {
		return request, e
	}
	request = RuntimeToolRequest{WorkspacePath: binding.RealPath, Access: binding.Access, Name: Str(payload, "name"), Arguments: payload["arguments"].(map[string]any), Policy: policy,
		IntentKey: "runtime-tool/" + Hash(Object{"project_id": route.ProjectID, "run_id": runID, "effect_key": frame.Key})}
	return request, nil
}

func (c *RuntimeCoordinator) brokerTool(ctx context.Context, route RuntimeCoordinatorRoute, provider RuntimeProviderRoute, runID, lease string, epoch int64, bridge *rt.Bridge, frame rt.BridgeFrame, payload, intent, dispatch Object) (Object, error) {
	unknown := func(reason string) (Object, error) {
		if e := c.service.ObserveEffect(context.Background(), route.ProjectID, runID, frame.Key, "UNKNOWN", Object{"dispatch_key": dispatch["dispatch_key"], "epoch": epoch, "reason": reason}); e != nil {
			return nil, e
		}
		return nil, Fail(409, "STATE_CONFLICT", "tool outcome UNKNOWN; automatic retry prohibited")
	}
	notApplied := func(reason string) (Object, error) {
		return c.recordNotAppliedEffect(route, provider, runID, epoch, bridge, frame, intent, dispatch, "HOST_TOOL_NOT_APPLIED", reason)
	}
	tx, run, current, e := c.dispatchGate(ctx, route, runID, lease, epoch, runtimePauseGatePurpose{kind: "effect-continue", effectKey: frame.Key, requestHash: Str(intent, "request_hash")})
	if e != nil {
		return notApplied("tool authority ended before host dispatch")
	}
	task, e := load(tx, route.ProjectID, "Task", Str(run, "task_id"))
	var request RuntimeToolRequest
	if e == nil {
		request, e = c.runtimeToolGate(ctx, tx, route, task, current, frame, payload)
	}
	tx.Rollback()
	if e != nil {
		return notApplied("tool binding ended before host dispatch")
	}
	permissionGranted := false
	selected, selectionErr := permissionSelection(request.Policy, request.Name)
	if selectionErr != nil {
		return notApplied("frozen confirmation policy is invalid")
	}
	if selected {
		key, waiter, err := c.createToolPermission(ctx, route, runID, lease, epoch, frame, payload, request)
		if err != nil {
			return notApplied("frozen tool permission could not be requested")
		}
		if !c.waitToolPermission(ctx, route, key, waiter) {
			c.closeToolPermission(context.Background(), route, key, waiter)
			return notApplied("original tool permission was denied, expired or revoked")
		}
		permissionGranted = true
	}
	// Physical publication rechecks the original run and lease after acquiring
	// its file guards. The child cannot supply or replace this callback.
	request.Revalidate = func(checkCtx context.Context) error {
		checkTx, checkRun, checkDispatch, err := c.dispatchGate(checkCtx, route, runID, lease, epoch, runtimePauseGatePurpose{kind: "effect-continue", effectKey: frame.Key, requestHash: Str(intent, "request_hash")})
		if err != nil {
			return err
		}
		defer checkTx.Rollback()
		checkTask, err := load(checkTx, route.ProjectID, "Task", Str(checkRun, "task_id"))
		if err != nil {
			return err
		}
		current, err := c.runtimeToolGate(checkCtx, checkTx, route, checkTask, checkDispatch, frame, payload)
		if err != nil {
			return err
		}
		if current.IntentKey != request.IntentKey || current.WorkspacePath != request.WorkspacePath || current.Access != request.Access || Hash(current.Policy) != Hash(request.Policy) {
			return Fail(403, "FORBIDDEN", "tool authority changed before physical publication")
		}
		if permissionGranted {
			latest, err := latestEffect(checkTx, route.ProjectID, runID, frame.Key)
			if err != nil || latest["state"] != "STARTED" {
				return Fail(409, "RESOURCE_BLOCKED", "original permitted effect is no longer active")
			}
			record, _ := latest["permission"].(map[string]any)
			if record == nil || record["decision"] != "ALLOW_ONCE" || record["consumed"] != true {
				return Fail(403, "FORBIDDEN", "original one-use permission was not consumed")
			}
			blocked, err := otherBlockingPermissionResources(checkTx, route.ProjectID, runID, Str(Object(record), "request_id"))
			if err != nil || blocked {
				return Fail(409, "RESOURCE_BLOCKED", "another resource still blocks the original task")
			}
		}
		return nil
	}
	if e = request.Revalidate(ctx); e != nil {
		return notApplied("tool authority changed before host dispatch")
	}
	result, e := c.config.RunTool(ctx, request)
	if e != nil {
		var witnessed *RuntimeToolFailure
		if errors.As(e, &witnessed) && witnessed.Outcome == "NOT_APPLIED" {
			return notApplied("host refused the tool before any side effect")
		}
		return unknown("host tool did not return a complete result")
	}
	evidence := result["host_evidence"]
	delete(result, "host_evidence")
	if evidence != nil && len(Bytes(evidence)) > 4*1024*1024 {
		return unknown("host tool evidence exceeds persistence bound")
	}
	reply := Object{"sequence": frame.Sequence, "key": frame.Key, "state": "CONFIRMED", "payload": result}
	raw := Bytes(result)
	if len(Bytes(reply)) > 64*1024 {
		return unknown("tool reply exceeds bridge frame limit")
	}
	for _, secret := range []string{c.schedulerCredential(route.ProjectID), route.ExecutorToken} {
		if secret != "" && strings.Contains(string(raw), secret) {
			return unknown("tool result contained host credential material")
		}
	}
	receipt := Object{"key": frame.Key, "epoch": epoch, "run_id": runID, "receipt_id": Digest(raw), "state": "CONFIRMED", "host_tool": request.Name, "actual_cost": provider.UpperBound, "payload": result}
	fact := Object{"version": 1, "project_id": route.ProjectID, "run_id": runID, "epoch": epoch, "dispatch_key": dispatch["dispatch_key"], "manifest_hash": dispatch["manifest_hash"], "effect_key": frame.Key, "request_hash": intent["request_hash"], "reservation_id": intent["reservation_id"], "provider_response_hash": Digest(raw), "receipt": receipt}
	if evidence != nil {
		fact["host_tool_evidence"] = evidence
		fact["host_tool_evidence_hash"] = Hash(evidence)
	}
	if e = writeRuntimeFact(filepath.Join(bridge.Directory(), "effect-"+strings.TrimPrefix(Digest([]byte(frame.Key)), "sha256:")+".json"), Bytes(fact)); e != nil {
		return unknown("tool result persistence failed")
	}
	if e = c.ingestEffectFact(context.Background(), fact); e != nil {
		return nil, e
	}
	tx, _, _, e = c.dispatchGate(ctx, route, runID, lease, epoch, runtimePauseGatePurpose{kind: "effect-finish", effectKey: frame.Key, requestHash: Str(intent, "request_hash")})
	if e != nil {
		return nil, e
	}
	tx.Rollback()
	return reply, nil
}
