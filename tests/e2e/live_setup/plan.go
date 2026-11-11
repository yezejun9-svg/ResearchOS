//go:build windows

package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"time"

	"researchos.local/research-os/internal/domain"
)

func (s *setup) preparePlan(ctx context.Context) error {
	if !s.credentialFresh() {
		return errors.New("LIVE provider credential is absent or revoked")
	}
	api, err := s.startAPI(ctx, nil)
	if err != nil {
		return err
	}
	defer api.close()
	base := api.path("")
	if err := s.ensureBudgetCap(ctx, api, base+"/budget-policy"); err != nil {
		return err
	}
	if s.state.RequirementID == "" {
		body := domain.Object{"requirement_key": "W14-LIVE-RUNTIME-QUALIFICATION", "text": "A real Mu runtime must complete a bounded model turn in the isolated W14 candidate and receive independent service acceptance before coding use.", "basis": "USER_STATED", "source_refs": domain.Empty(), "rationale": "LIVE runtime qualification is explicitly authorized; no execution result is presumed", "supersedes_id": nil, "acceptance_check_ids": domain.Empty()}
		req, err := api.postWithState(ctx, s.ownerToken, base+"/requirements", body, 201)
		if err != nil {
			return err
		}
		s.state.RequirementID = domain.Str(req, "id")
		if err := s.saveState(); err != nil {
			return err
		}
	}
	requirement, err := api.get(ctx, s.ownerToken, base+"/requirements/"+s.state.RequirementID)
	if err != nil {
		return err
	}
	if requirement["status"] != "ACCEPTED" {
		requirement, err = api.postWithSubject(ctx, s.ownerToken, base+"/requirements/"+s.state.RequirementID+"/actions", requirement, domain.Object{"action": "ACCEPT", "reason": "explicit W14 LIVE qualification setup", "source_validation_refs": domain.Empty()}, 200)
		if err != nil {
			return err
		}
	}
	if s.state.RuntimeID == "" {
		reg, err := api.postWithState(ctx, s.ownerToken, base+"/runtimes", domain.Object{"name": "W14 Mu SDK LIVE", "adapter": "mu-sdk", "adapter_revision": "windows-appcontainer-v1", "capabilities": []any{"start", "context_rebuild"}, "platform": "windows-amd64", "measurement_mode": "LIVE", "credential_ref": s.state.CredentialRef}, 201)
		if err != nil {
			return err
		}
		s.state.RuntimeID = domain.Str(reg, "id")
		if err := s.saveState(); err != nil {
			return err
		}
	}
	reg, err := api.get(ctx, s.ownerToken, base+"/runtimes/"+s.state.RuntimeID)
	if err != nil {
		return err
	}
	if s.state.ProfileID == "" {
		if s.state.ExecutorID == "" {
			s.state.ExecutorID = "w14-live-executor-" + domain.ID()
			if err := s.svc.ProvisionPrincipal(ctx, domain.Principal{ID: s.state.ExecutorID, Roles: []string{"EXECUTOR"}, Grants: []domain.Grant{{ProjectID: s.state.ProjectID}}}); err != nil {
				return err
			}
			if err := s.saveState(); err != nil {
				return err
			}
		}
		profileToken, err := s.svc.IssueCredential(ctx, s.state.ExecutorID, privateTokenTTL())
		if err != nil {
			return err
		}
		profileBody, err := s.frozenProfile(reg)
		if err != nil {
			return err
		}
		upload, raw, err := api.uploadJSON(ctx, profileToken, profileBody)
		if err != nil {
			return err
		}
		artifact, err := api.postWithState(ctx, profileToken, base+"/artifacts", domain.Object{"run_id": nil, "kind": "REPORT", "evidence_kind": "GENERATED", "measurement_mode": "LIVE", "content_hash": upload["content_hash"], "storage_key": upload["storage_key"], "media_type": "application/json", "byte_size": len(raw), "input_refs": domain.Empty(), "source_refs": domain.Empty(), "produced_by": s.state.ExecutorID, "access_class": "PROJECT"}, 201)
		if err != nil {
			return err
		}
		s.state.ProfileID, s.state.ProfileHash = domain.Str(artifact, "id"), domain.Str(artifact, "content_hash")
		if err := s.saveState(); err != nil {
			return err
		}
	}
	profile, err := api.get(ctx, s.ownerToken, base+"/artifacts/"+s.state.ProfileID)
	if err != nil {
		return err
	}
	if profile["content_hash"] != s.state.ProfileHash {
		return errors.New("stored profile hash changed")
	}
	profileRef := domain.Ref(profile, "Artifact")
	if s.state.TaskID == "" && s.state.GoalID != "" {
		id, err := s.recoverQualificationTask(ctx, profileRef, domain.Ref(requirement, "Requirement"))
		if err != nil {
			return err
		}
		if id != "" {
			s.state.TaskID = id
			if err := s.saveState(); err != nil {
				return err
			}
		}
	}
	if s.state.TaskID == "" {
		contract := liveTurnContract()
		var goal domain.Object
		if s.state.GoalID == "" {
			goal, err = api.postWithState(ctx, s.ownerToken, base+"/goals", domain.Object{"title": "W14 LIVE Mu runtime qualification", "original_intent": "This is a one-call LIVE runtime qualification. Respond with one brief sentence that confirms you received this task. Do not use tools or edit files. Independent service verification follows.", "scope": "PROJECT", "requirement_refs": []any{domain.Ref(requirement, "Requirement")}, "problem_ids": []any{"w14-live-runtime"}, "deliverables": []any{"verified Mu turn receipt"}, "acceptance_contract": contract}, 201)
			if err != nil {
				return err
			}
			s.state.GoalID = domain.Str(goal, "id")
			if err := s.saveState(); err != nil {
				return err
			}
		} else {
			goal, err = api.get(ctx, s.ownerToken, base+"/goals/"+s.state.GoalID)
			if err != nil {
				return err
			}
			contract = goal["acceptance_contract"].(map[string]any)
		}
		if goal["status"] != "ACTIVE" {
			goal, err = api.postWithSubject(ctx, s.ownerToken, base+"/goals/"+s.state.GoalID+"/actions", goal, domain.Object{"action": "ACTIVATE", "reason": "bounded W14 LIVE qualification plan"}, 200)
			if err != nil {
				return err
			}
		}
		if err := s.ensureBudgetCap(ctx, api, base+"/goals/"+domain.Str(goal, "id")+"/budget-policy"); err != nil {
			return err
		}
		task, err := api.postWithSubject(ctx, s.ownerToken, base+"/tasks", goal, domain.Object{"goal_id": goal["id"], "title": "W14 LIVE Mu qualification", "task_type": "runtime_qualification", "stage": "verification", "dependency_task_ids": domain.Empty(), "requirement_refs": []any{domain.Ref(requirement, "Requirement")}, "input_refs": []any{profileRef}, "acceptance_contract": contract, "origin_problem_id": "w14-live-runtime", "candidate_id": "w14-live-runtime", "stop_policy": domain.Object{"wall_time_seconds": 180, "max_attempts": 1, "max_parallel_runs": 1, "stop_conditions": []any{"no progress", "wall-time"}}}, 201)
		if err != nil {
			return err
		}
		s.state.TaskID = domain.Str(task, "id")
		if err := s.saveState(); err != nil {
			return err
		}
	}
	task, err := api.get(ctx, s.ownerToken, base+"/tasks/"+s.state.TaskID)
	if err != nil {
		return err
	}
	if task["goal_id"] != s.state.GoalID || task["task_type"] != "runtime_qualification" || domain.Hash(task["input_refs"]) != domain.Hash([]any{profileRef}) || domain.Hash(task["requirement_refs"]) != domain.Hash([]any{domain.Ref(requirement, "Requirement")}) {
		return errors.New("persisted qualification task does not match frozen goal, profile and requirement")
	}
	if task["context_bundle_id"] == nil {
		schedulerToken, err := s.ensureScheduler(ctx)
		if err != nil {
			return err
		}
		state, err := api.projectState(ctx, s.ownerToken)
		if err != nil {
			return err
		}
		if _, err := api.postWithSubject(ctx, schedulerToken, base+"/context-bundles", state, domain.Object{"task_id": task["id"], "expected_project_state_revision": state["revision"]}, 201); err != nil {
			return err
		}
	}
	for _, item := range []struct {
		id           *string
		role, prefix string
		taskScoped   bool
	}{{&s.state.ExecutorID, "EXECUTOR", "w14-live-executor", false}, {&s.state.SchedulerID, "SCHEDULER", "w14-live-scheduler", false}, {&s.state.VerifierID, "VERIFIER", "w14-live-verifier", false}} {
		if *item.id != "" {
			continue
		}
		identifier := item.prefix + "-" + domain.ID()
		grant := domain.Grant{ProjectID: s.state.ProjectID}
		if item.taskScoped {
			grant.TaskID = s.state.TaskID
		}
		if err := s.svc.ProvisionPrincipal(ctx, domain.Principal{ID: identifier, Roles: []string{item.role}, Grants: []domain.Grant{grant}}); err != nil {
			return err
		}
		*item.id = identifier
		if err := s.saveState(); err != nil {
			return err
		}
	}
	var planned int
	if err := s.db.QueryRowContext(ctx, "SELECT count(*) FROM runtime_qualification_plans WHERE project=? AND task=? AND runtime=?", s.state.ProjectID, s.state.TaskID, s.state.RuntimeID).Scan(&planned); err != nil {
		return err
	}
	if planned == 0 {
		if err := s.svc.RegisterRuntimeQualificationPlan(ctx, s.ownerToken, s.state.ProjectID, s.state.TaskID, s.state.RuntimeID, profileRef, []any{"start", "context_rebuild"}, time.Hour, ""); err != nil {
			return err
		}
	} else if planned != 1 {
		return errors.New("ambiguous qualification plan")
	}
	if err := s.refreshCoordinatorConfig(ctx); err != nil {
		return err
	}
	s.state.PlanReady = true
	return s.saveState()
}

// A prior successful createTask may precede a process interruption. Recover
// only the unique, exact task from the production journal; never create a
// second task when the Goal already has a conflicting qualification task.
func (s *setup) recoverQualificationTask(ctx context.Context, profileRef, requirementRef domain.Object) (string, error) {
	rows, err := s.db.QueryContext(ctx, "SELECT body FROM domain_objects WHERE project=? AND kind='Task' AND json_extract(body,'$.goal_id')=? AND json_extract(body,'$.task_type')='runtime_qualification'", s.state.ProjectID, s.state.GoalID)
	if err != nil {
		return "", err
	}
	defer rows.Close()
	count := 0
	id := ""
	for rows.Next() {
		var raw string
		if err := rows.Scan(&raw); err != nil {
			return "", err
		}
		var task domain.Object
		if err := json.Unmarshal([]byte(raw), &task); err != nil {
			return "", err
		}
		count++
		if domain.Hash(task["input_refs"]) != domain.Hash([]any{profileRef}) || domain.Hash(task["requirement_refs"]) != domain.Hash([]any{requirementRef}) {
			return "", errors.New("existing runtime qualification task conflicts with frozen W14 inputs")
		}
		id = domain.Str(task, "id")
	}
	if err := rows.Err(); err != nil {
		return "", err
	}
	if count > 1 {
		return "", errors.New("multiple W14 qualification tasks exist; refusing duplicate creation")
	}
	return id, nil
}

func (s *setup) ensureScheduler(ctx context.Context) (string, error) {
	if s.state.SchedulerID == "" {
		id := "w14-live-scheduler-" + domain.ID()
		if err := s.svc.ProvisionPrincipal(ctx, domain.Principal{ID: id, Roles: []string{"SCHEDULER"}, Grants: []domain.Grant{{ProjectID: s.state.ProjectID}}}); err != nil {
			return "", err
		}
		s.state.SchedulerID = id
		if err := s.saveState(); err != nil {
			return "", err
		}
	}
	return s.svc.IssueCredential(ctx, s.state.SchedulerID, privateTokenTTL())
}

func (s *setup) ensureBudgetCap(ctx context.Context, api *localAPI, path string) error {
	policy, err := api.get(ctx, s.ownerToken, path)
	if err != nil {
		return err
	}
	if policy["mode"] == "CAPPED" && policy["enforcement"] == "STRICT" && policy["unknown_cost_action"] == "BLOCK" && domain.Hash(policy["cap"]) == domain.Hash(domain.Object{"amount": "1.80", "currency": "USD"}) {
		return nil
	}
	_, err = api.call(ctx, s.ownerToken, http.MethodPut, path, tag(policy), domain.Object{"mode": "CAPPED", "cap": domain.Object{"amount": "1.80", "currency": "USD"}, "enforcement": "STRICT", "period": "LIFETIME", "timezone": "Asia/Shanghai", "effective_from": domain.Now(), "unknown_cost_action": "BLOCK"}, http.StatusOK)
	return err
}

func liveTurnContract() domain.Object {
	c := domain.Object{"contract_revision": 1, "checks": []any{domain.Object{"check_id": "mu-turn-output", "kind": "DETERMINISTIC", "required": true, "expected": "Bounded Mu response with exact user-message provenance and reconciled model/tool effects; execution is not independent acceptance", "command_key": "mu.turn-output-v1", "rubric_ref": nil, "qualification_id": nil, "not_applicable_reason": nil}}, "require_independent_verifier": true, "version_policy": "EXACT", "frozen_at": time.Now().UTC().Format(time.RFC3339Nano)}
	c["contract_hash"] = domain.Hash(c)
	return c
}

func (s *setup) frozenProfile(reg domain.Object) (domain.Object, error) {
	node, err := exec.LookPath("node")
	if err != nil {
		return nil, fmt.Errorf("native Node executable unavailable: %w", err)
	}
	node, err = filepath.EvalSymlinks(node)
	if err != nil {
		return nil, err
	}
	node, err = filepath.Abs(node)
	if err != nil {
		return nil, err
	}
	build, err := os.ReadFile(node)
	if err != nil {
		return nil, err
	}
	bundle := filepath.Join(s.repo, ".local/w1401-mu-worker/mu-worker.mjs")
	bundleRaw, err := os.ReadFile(bundle)
	if err != nil {
		return nil, fmt.Errorf("real Mu bundle unavailable: %w", err)
	}
	policyRaw, err := os.ReadFile(s.policyPath)
	if err != nil {
		return nil, err
	}
	var frozen domain.Object
	if err := json.Unmarshal(policyRaw, &frozen); err != nil {
		return nil, err
	}
	checks := domain.Arr(frozen, "checks")
	if len(checks) != 1 {
		return nil, errors.New("expected exactly one pinned native Go check")
	}
	check, ok := checks[0].(map[string]any)
	if !ok {
		return nil, errors.New("invalid pinned native Go check")
	}
	readPaths := []any{}
	for _, item := range domain.Arr(check, "source_paths") {
		source, ok := item.(map[string]any)
		if !ok || domain.Str(source, "path") == "" {
			return nil, errors.New("invalid pinned source path")
		}
		readPaths = append(readPaths, source["path"])
	}
	// This file must be authored through the LIVE host tool by the product agent.
	// Its prior absence is expected; the frozen check runs after that write.
	const doctorTest = "apps/cli/doctor_live_test.go"
	for _, path := range readPaths {
		if path == doctorTest {
			return nil, errors.New("doctor test already appears in pinned preflight; resolve duplicate")
		}
	}
	readPaths = append(readPaths, doctorTest)
	check["source_paths"] = append(domain.Arr(check, "source_paths"), domain.Object{"path": doctorTest})
	argv := domain.Arr(check, "argv")
	if len(argv) < 9 || argv[len(argv)-2] != "^TestW14CLIRepeatedMessagesHaveDistinctStableCommands$" {
		return nil, errors.New("pinned preflight selector changed")
	}
	argv[len(argv)-2] = "^(TestW14CLIRepeatedMessagesHaveDistinctStableCommands|TestW14DoctorLiveHostHandshake)$"
	check["argv"] = argv
	config := liveModelConfig()
	modelBound := domain.Object{"amount": "0.10", "currency": "USD"}
	profile := domain.Object{"runtime_id": reg["id"], "technical_hash": domain.Hash([]any{reg["adapter"], reg["adapter_revision"], reg["capabilities"], reg["platform"], reg["measurement_mode"], reg["credential_ref"]}), "adapter": reg["adapter"], "adapter_revision": "windows-appcontainer-v1", "platform": "windows-amd64", "build_hash": domain.Digest(build), "sandbox": "appcontainer-zero-capabilities-v1", "credential_revision": s.state.CredentialRef, "backend": "mu-sdk-broker-v1", "model": "deepseek-flash", "command_id": "w14-live-mu-sdk", "argv": []any{"--preserve-symlinks-main", "--preserve-symlinks", "{bundle}", "{manifest}"}, "bundle_hash": domain.Digest(bundleRaw), "model_config": config, "model_qualification": domain.Object{"route": config["route"], "model_config_hash": domain.Hash(config), "max_calls": 1}, "effect_routes": []any{domain.Object{"id": config["route"], "capability": "MODEL", "credential_revision": s.state.CredentialRef, "upper_bound": modelBound}, domain.Object{"id": config["route"], "capability": "TOOL", "credential_revision": "none", "upper_bound": domain.Object{"amount": "0", "currency": "USD"}}}, "permissions": domain.Object{"network": "none", "environment": "staging-only", "capabilities": domain.Empty(), "process_limit": 1, "memory_mib": 256}, "timeout_seconds": 900, "outputs": []any{"result.json"}, "max_cost": modelBound, "tool_policy": domain.Object{"max_calls": 32, "read_paths": readPaths, "write_paths": []any{"apps/cli/main.go", doctorTest}, "max_read_bytes": 65536, "max_write_bytes": 65536, "checks": checks}}
	return profile, nil
}

func liveToolSchemas() []any {
	stringProp := domain.Object{"type": "string"}
	pathProp := domain.Object{"type": "string", "description": "Exact frozen candidate-relative path"}
	fn := func(name, description string, parameters domain.Object) any {
		return domain.Object{"type": "function", "function": domain.Object{"name": name, "description": description, "parameters": parameters}}
	}
	schema := func(properties domain.Object, required ...string) domain.Object {
		r := []any{}
		for _, v := range required {
			r = append(r, v)
		}
		return domain.Object{"type": "object", "properties": properties, "required": r, "additionalProperties": false}
	}
	return []any{
		fn("read", "Read a frozen candidate file with UTF-8 byte pagination", schema(domain.Object{"path": pathProp, "offset": domain.Object{"type": "integer", "minimum": 0}, "limit": domain.Object{"type": "integer", "minimum": 1, "maximum": 65536}}, "path")),
		fn("write", "Create or replace one allowed candidate file with expected hash", schema(domain.Object{"path": pathProp, "expected_hash": domain.Object{"type": []any{"string", "null"}}, "content": stringProp}, "path", "expected_hash", "content")),
		fn("edit", "Replace exactly one UTF-8 occurrence under a content hash", schema(domain.Object{"path": pathProp, "expected_hash": stringProp, "old_text": stringProp, "new_text": stringProp}, "path", "expected_hash", "old_text", "new_text")),
		fn("run_check", "Run one frozen native Go check by ID", schema(domain.Object{"check_id": stringProp}, "check_id")),
	}
}

func liveModelConfig() domain.Object {
	return domain.Object{"ref": "w14-deepseek-flash-live-v1", "api": "openai-completions", "provider": "deepseek", "model": "deepseek-flash", "endpoint": "https://api.deepseek.com/chat/completions", "route": "w14-deepseek-model", "max_output_tokens": 8192, "max_calls": 16, "tools": liveToolSchemas()}
}

func (s *setup) refreshCoordinatorConfig(ctx context.Context) error {
	if s.state.ProjectID == "" || s.state.RuntimeID == "" || s.state.ExecutorID == "" || s.state.SchedulerID == "" || s.state.CredentialRef == "" {
		return errors.New("LIVE coordinator bindings incomplete")
	}
	executorToken, err := s.svc.IssueCredential(ctx, s.state.ExecutorID, privateTokenTTL())
	if err != nil {
		return err
	}
	schedulerToken, err := s.svc.IssueCredential(ctx, s.state.SchedulerID, privateTokenTTL())
	if err != nil {
		return err
	}
	node, err := exec.LookPath("node")
	if err != nil {
		return err
	}
	node, err = filepath.EvalSymlinks(node)
	if err != nil {
		return err
	}
	node, err = filepath.Abs(node)
	if err != nil {
		return err
	}
	model := liveModelConfig()
	modelProvider := func(purpose string) domain.RuntimeProviderRoute {
		return domain.RuntimeProviderRoute{ID: "w14-deepseek-model", ProjectID: s.state.ProjectID, RuntimeID: s.state.RuntimeID, Purpose: purpose, Capability: "MODEL", CredentialRevision: s.state.CredentialRef, Endpoint: "https://api.deepseek.com/chat/completions", CredentialRef: s.state.CredentialRef, UpperBound: domain.Object{"amount": "0.10", "currency": "USD"}, MeasurementMode: "LIVE", ModelConfig: model}
	}
	toolProvider := domain.RuntimeProviderRoute{ID: "w14-deepseek-model", ProjectID: s.state.ProjectID, RuntimeID: s.state.RuntimeID, Purpose: "mu_turn", Capability: "TOOL", CredentialRevision: "none", UpperBound: domain.Object{"amount": "0", "currency": "USD"}, MeasurementMode: "LIVE"}
	config := domain.RuntimeCoordinatorConfig{DataRoot: s.dataRoot, SchedulerToken: schedulerToken, Routes: []domain.RuntimeCoordinatorRoute{{ProjectID: s.state.ProjectID, RuntimeID: s.state.RuntimeID, ExecutorID: s.state.ExecutorID, ExecutorToken: executorToken, CommandID: "w14-live-mu-sdk", Executable: node, BundleFile: filepath.Join(s.repo, ".local/w1401-mu-worker/mu-worker.mjs")}}, Providers: []domain.RuntimeProviderRoute{modelProvider("runtime_qualification"), modelProvider("mu_turn"), toolProvider}}
	if err := s.updatePrivateCoordinatorConfig(config); err != nil {
		return err
	}
	return nil
}
