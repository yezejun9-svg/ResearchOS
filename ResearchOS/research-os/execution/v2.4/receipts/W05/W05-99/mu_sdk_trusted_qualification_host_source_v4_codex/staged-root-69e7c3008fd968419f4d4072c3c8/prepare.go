//go:build windows

package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"

	"researchos.local/research-os/internal/domain"
)

func prepare(ctx context.Context, s seed, digest string) (domain.Object, error) {
	if s.DraftGoalID == "" {
		return nil, errors.New("legacy prepare requires an already-created CLI draft goal")
	}
	if err := verifyEvidenceWorkspace(s); err != nil {
		return nil, err
	}
	e, err := openEnvironment(ctx, s)
	if err != nil {
		return nil, err
	}
	defer e.close()
	// The data-root lease now serializes this check and the durable claim below.
	// A concurrent prepare can no longer observe absent state before waiting.
	if _, err = os.Stat(statePath(s)); err == nil {
		return nil, errors.New("qualification preparation already claimed; inspect private state, no retry")
	} else if !errors.Is(err, os.ErrNotExist) {
		return nil, err
	}
	if err = e.startHTTP(e.handler(nil)); err != nil {
		return nil, err
	}
	if err = verifyCLIProject(ctx, e, s); err != nil {
		return nil, err
	}
	v := state{Schema: schema, SeedSHA256: digest, HostInstanceID: e.host.InstanceID(), OwnerID: e.ownerID, ProjectID: s.ProjectID, DraftGoalID: s.DraftGoalID, Phase: "PREPARE_CLAIMED"}
	if err = saveState(s, v); err != nil {
		return nil, err
	}
	// Once claimed, a failure is an observable partial setup. No automatic
	// second prepare call may create a duplicate goal, runtime or sealed profile.
	if err = prepareObjects(ctx, e, s, &v); err != nil {
		return nil, err
	}
	v.Phase = "PREPARED"
	if err = saveState(s, v); err != nil {
		return nil, err
	}
	return domain.Object{"status": "PREPARED", "project_id": v.ProjectID, "draft_goal_id": v.DraftGoalID, "qualification_goal_id": v.QualificationGoalID, "qualification_task_id": v.TaskID, "runtime_id": v.RuntimeID, "profile_artifact_id": v.ProfileID, "profile_hash": v.ProfileHash, "host_instance_id": v.HostInstanceID, "state_path": statePath(s), "provider_requests": 0}, nil
}

func verifyEvidenceWorkspace(s seed) error {
	dir, err := os.Lstat(s.WorkspaceDir)
	if err != nil {
		return err
	}
	if !dir.IsDir() || dir.Mode()&os.ModeSymlink != 0 {
		return errors.New("witness workspace must be a real directory")
	}
	canonical, err := filepath.EvalSymlinks(s.WorkspaceDir)
	if err != nil {
		return err
	}
	if !strings.EqualFold(filepath.Clean(canonical), filepath.Clean(s.WorkspaceDir)) {
		return errors.New("witness workspace reparse path refused")
	}
	entries, err := os.ReadDir(s.WorkspaceDir)
	if err != nil {
		return err
	}
	if len(entries) != 1 || entries[0].Name() != "evidence.txt" || entries[0].IsDir() {
		return errors.New("isolated workspace must contain exactly evidence.txt")
	}
	info, err := os.Lstat(filepath.Join(s.WorkspaceDir, "evidence.txt"))
	if err != nil {
		return err
	}
	if !info.Mode().IsRegular() || info.Mode()&os.ModeSymlink != 0 {
		return errors.New("witness must be a regular, non-link file")
	}
	hash, n, err := fileHash(filepath.Join(s.WorkspaceDir, "evidence.txt"))
	if err != nil {
		return err
	}
	if n != s.WitnessBytes || !strings.EqualFold(strings.TrimPrefix(s.WitnessSHA256, "sha256:"), hash) {
		return errors.New("workspace witness differs from pin")
	}
	return nil
}

func verifyCLIProject(ctx context.Context, e *environment, s seed) error {
	if err := verifyCLIProjectBase(ctx, e, s); err != nil {
		return err
	}
	if s.DraftGoalID == "" {
		return errors.New("CLI draft goal ID required")
	}
	goal, err := e.get(ctx, e.ownerToken, "/goals/"+s.DraftGoalID)
	if err != nil {
		return err
	}
	if goal["project_id"] != s.ProjectID || goal["status"] != "DRAFT" {
		return errors.New("target CLI goal is not a DRAFT in the same project")
	}
	return nil
}

func verifyCLIProjectBase(ctx context.Context, e *environment, s seed) error {
	discovered, err := os.ReadFile(s.DiscoveryFile)
	if err != nil {
		return err
	}
	var firstHost struct {
		URL            string `json:"url"`
		PID            int    `json:"pid"`
		DataDir        string `json:"data_dir"`
		HostInstanceID string `json:"host_instance_id"`
	}
	if err = json.Unmarshal(discovered, &firstHost); err != nil {
		return err
	}
	if firstHost.HostInstanceID != e.host.InstanceID() || !strings.EqualFold(filepath.Clean(firstHost.DataDir), filepath.Clean(e.lease.Root())) || firstHost.PID < 1 || !strings.HasPrefix(firstHost.URL, "http://127.0.0.1:") {
		return errors.New("CLI initial discovery differs from actual same-SID Host")
	}
	raw, err := os.ReadFile(s.CLIConfigFile)
	if err != nil {
		return err
	}
	var cli struct {
		ProjectID    string `json:"project_id"`
		WorkspaceRef string `json:"workspace_ref"`
	}
	if err = json.Unmarshal(raw, &cli); err != nil {
		return err
	}
	if cli.ProjectID != s.ProjectID || cli.WorkspaceRef != s.WorkspaceRef {
		return errors.New("CLI project/workspace differs from seed")
	}
	var bindingRaw string
	err = e.db.QueryRowContext(ctx, "SELECT body FROM domain_objects WHERE kind='WorkspaceBinding' AND json_extract(body,'$.authorized_workspace_ref')=?", s.WorkspaceRef).Scan(&bindingRaw)
	if err != nil {
		return err
	}
	var binding domain.Object
	if err = json.Unmarshal([]byte(bindingRaw), &binding); err != nil {
		return err
	}
	if binding["project_id"] != s.ProjectID || binding["status"] != "ACTIVE" || !strings.EqualFold(filepath.Clean(domain.Str(binding, "real_path")), filepath.Clean(s.WorkspaceDir)) {
		return errors.New("CLI workspace binding differs from exact isolated directory")
	}
	return checkUnlimited(ctx, e, "/budget-policy")
}

func checkUnlimited(ctx context.Context, e *environment, path string) error {
	p, err := e.get(ctx, e.ownerToken, path)
	if err != nil {
		return err
	}
	if p["mode"] != "UNLIMITED_AMOUNT" || p["cap"] != nil || p["unknown_cost_action"] != "ALLOW_AND_RECORD" {
		return errors.New("unknown-cost trial requires existing unlimited budget ancestry")
	}
	return nil
}

func qualificationContract() domain.Object {
	c := domain.Object{"contract_revision": 1, "checks": []any{domain.Object{"check_id": "mu-turn-output", "kind": "DETERMINISTIC", "required": true, "expected": "Bounded Mu response with exact user-message provenance and reconciled model/tool effects; execution is not independent acceptance", "command_key": "mu.turn-output-v1", "rubric_ref": nil, "qualification_id": nil, "not_applicable_reason": nil}}, "require_independent_verifier": true, "version_policy": "EXACT", "frozen_at": time.Now().UTC().Format(time.RFC3339Nano)}
	c["contract_hash"] = domain.Hash(c)
	return c
}

func preparedProfile(s seed, registration domain.Object) (domain.Object, error) {
	var profile domain.Object
	if err := json.Unmarshal(s.ProfileRaw, &profile); err != nil {
		return nil, err
	}
	if containsSecretField(profile) {
		return nil, errors.New("public profile includes secret-bearing field")
	}
	node, bundle := s.NodeRaw, s.BundleRaw
	config, ok := profile["model_config"].(map[string]any)
	if !ok {
		return nil, errors.New("profile has no model_config")
	}
	if config["provider"] != s.Provider || domain.Str(config, "route") == "" || domain.Str(config, "endpoint") == "" || config["api"] != "openai-completions" {
		return nil, errors.New("public model configuration differs from provider")
	}
	// The total Root trial is one qualification MODEL effect and two ordinary
	// MODEL effects. The profile permits at most two calls within an ordinary Run;
	// Root's outer controller must enforce the cross-Run total of three.
	config["max_calls"] = 2
	config["max_output_tokens"] = 2730
	config["tools"] = []any{domain.Object{"type": "function", "function": domain.Object{"name": "read", "description": "Read only the pinned witness file", "parameters": domain.Object{"type": "object", "properties": domain.Object{"path": domain.Object{"type": "string"}, "offset": domain.Object{"type": "integer", "minimum": 0}, "limit": domain.Object{"type": "integer", "minimum": 1, "maximum": 65536}}, "required": []any{"path"}, "additionalProperties": false}}}}
	profile["model_config"] = config
	profile["runtime_id"] = registration["id"]
	profile["technical_hash"] = domain.Hash([]any{registration["adapter"], registration["adapter_revision"], registration["capabilities"], registration["platform"], registration["measurement_mode"], registration["credential_ref"]})
	profile["adapter"], profile["adapter_revision"], profile["platform"] = registration["adapter"], registration["adapter_revision"], registration["platform"]
	profile["credential_revision"], profile["backend"], profile["model"] = s.CredentialRef, "mu-sdk-broker-v1", config["model"]
	profile["build_hash"], profile["bundle_hash"] = domain.Digest(node), domain.Digest(bundle)
	profile["sandbox"], profile["command_id"] = "appcontainer-zero-capabilities-v1", "mu-sdk-trial"
	profile["argv"] = []any{"--preserve-symlinks-main", "--preserve-symlinks", "{bundle}", "{manifest}"}
	profile["max_cost"] = nil // Explicit UNKNOWN; no fabricated zero price.
	profile["timeout_seconds"] = 90
	profile["model_qualification"] = domain.Object{"route": config["route"], "model_config_hash": domain.Hash(config), "max_calls": 1}
	profile["effect_routes"] = []any{domain.Object{"id": config["route"], "capability": "MODEL", "credential_revision": s.CredentialRef, "upper_bound": nil}, domain.Object{"id": config["route"], "capability": "TOOL", "credential_revision": "none", "upper_bound": domain.Object{"amount": "0", "currency": "USD"}}}
	profile["permissions"] = domain.Object{"network": "none", "environment": "staging-only", "capabilities": domain.Empty(), "process_limit": 1, "memory_mib": 256}
	if profile["outputs"] == nil {
		profile["outputs"] = []any{"result.json"}
	}
	policy, ok := profile["tool_policy"].(map[string]any)
	if !ok {
		return nil, errors.New("pinned profile lacks tool_policy")
	}
	policy["read_paths"] = []any{"evidence.txt"}
	policy["write_paths"] = domain.Empty()
	policy["checks"] = domain.Empty()
	policy["user_confirmation_tools"] = domain.Empty()
	policy["max_calls"] = 1
	policy["max_read_bytes"] = 4096
	policy["max_write_bytes"] = 4096
	profile["tool_policy"] = policy
	return profile, nil
}

func containsSecretField(value any) bool {
	switch typed := value.(type) {
	case map[string]any:
		for k, v := range typed {
			switch strings.ToLower(k) {
			case "bearer_token", "api_key", "authorization", "credential_value", "secret", "access_token", "refresh_token":
				return true
			}
			if containsSecretField(v) {
				return true
			}
		}
	case []any:
		for _, v := range typed {
			if containsSecretField(v) {
				return true
			}
		}
	}
	return false
}

func prepareObjects(ctx context.Context, e *environment, s seed, v *state) error {
	baseReq := domain.Object{"requirement_key": "MU-TRIAL-QUALIFICATION-" + domain.ID(), "text": "Qualify the isolated Mu SDK model through one real native MODEL effect and independent service verification.", "basis": "USER_STATED", "source_refs": domain.Empty(), "rationale": "Root authorized a bounded real trial; no result is presumed", "supersedes_id": nil, "acceptance_check_ids": domain.Empty()}
	requirement, err := e.postState(ctx, e.ownerToken, "/requirements", baseReq, http.StatusCreated)
	if err != nil {
		return err
	}
	v.RequirementID = domain.Str(requirement, "id")
	if err = saveState(s, *v); err != nil {
		return err
	}
	requirement, err = e.postSubject(ctx, e.ownerToken, "/requirements/"+v.RequirementID+"/actions", requirement, domain.Object{"action": "ACCEPT", "reason": "bounded real qualification", "source_validation_refs": domain.Empty()}, http.StatusOK)
	if err != nil {
		return err
	}
	contract := qualificationContract()
	goal, err := e.postState(ctx, e.ownerToken, "/goals", domain.Object{"title": "Isolated Mu SDK runtime qualification", "original_intent": s.QualificationPrompt, "scope": "PROJECT", "requirement_refs": []any{domain.Ref(requirement, "Requirement")}, "problem_ids": []any{"mu-sdk-trial"}, "deliverables": []any{"independent runtime qualification receipt"}, "acceptance_contract": contract}, http.StatusCreated)
	if err != nil {
		return err
	}
	v.QualificationGoalID = domain.Str(goal, "id")
	if err = saveState(s, *v); err != nil {
		return err
	}
	goal, err = e.postSubject(ctx, e.ownerToken, "/goals/"+v.QualificationGoalID+"/actions", goal, domain.Object{"action": "ACTIVATE", "reason": "bounded real runtime qualification"}, http.StatusOK)
	if err != nil {
		return err
	}
	if err = checkUnlimited(ctx, e, "/goals/"+v.QualificationGoalID+"/budget-policy"); err != nil {
		return err
	}
	registration, err := e.postState(ctx, e.ownerToken, "/runtimes", domain.Object{"name": "Mu SDK bounded real trial", "adapter": "mu-sdk", "adapter_revision": "windows-appcontainer-v1", "capabilities": []any{"start", "context_rebuild"}, "platform": "windows-amd64", "measurement_mode": "LIVE", "credential_ref": s.CredentialRef}, http.StatusCreated)
	if err != nil {
		return err
	}
	v.RuntimeID = domain.Str(registration, "id")
	if err = saveState(s, *v); err != nil {
		return err
	}
	v.ExecutorID = "mu-trial-executor-" + domain.ID()
	v.SchedulerID = "mu-trial-scheduler-" + domain.ID()
	v.VerifierID = "mu-trial-verifier-" + domain.ID()
	for _, p := range []struct{ id, role string }{{v.ExecutorID, "EXECUTOR"}, {v.SchedulerID, "SCHEDULER"}, {v.VerifierID, "VERIFIER"}} {
		if err = e.svc.ProvisionPrincipal(ctx, domain.Principal{ID: p.id, Roles: []string{p.role}, Grants: []domain.Grant{{ProjectID: s.ProjectID}}}); err != nil {
			return err
		}
	}
	if err = saveState(s, *v); err != nil {
		return err
	}
	executorToken, err := e.svc.IssueCredential(ctx, v.ExecutorID, 15*time.Minute)
	if err != nil {
		return err
	}
	profile, err := preparedProfile(s, registration)
	if err != nil {
		return err
	}
	upload, raw, err := e.uploadJSON(ctx, executorToken, profile)
	if err != nil {
		return err
	}
	artifact, err := e.postState(ctx, executorToken, "/artifacts", domain.Object{"run_id": nil, "kind": "REPORT", "evidence_kind": "GENERATED", "measurement_mode": "LIVE", "content_hash": upload["content_hash"], "storage_key": upload["storage_key"], "media_type": "application/json", "byte_size": len(raw), "input_refs": domain.Empty(), "source_refs": domain.Empty(), "produced_by": v.ExecutorID, "access_class": "PROJECT"}, http.StatusCreated)
	if err != nil {
		return err
	}
	v.ProfileID, v.ProfileHash = domain.Str(artifact, "id"), domain.Str(artifact, "content_hash")
	if err = saveState(s, *v); err != nil {
		return err
	}
	task, err := e.postSubject(ctx, e.ownerToken, "/tasks", goal, domain.Object{"goal_id": goal["id"], "title": "One real Mu SDK qualification turn", "task_type": "runtime_qualification", "stage": "verification", "dependency_task_ids": domain.Empty(), "requirement_refs": []any{domain.Ref(requirement, "Requirement")}, "input_refs": []any{domain.Ref(artifact, "Artifact")}, "acceptance_contract": contract, "origin_problem_id": "mu-sdk-trial", "candidate_id": "mu-sdk-trial", "stop_policy": domain.Object{"wall_time_seconds": 90, "max_attempts": 1, "max_parallel_runs": 1, "stop_conditions": []any{"no progress", "wall-time"}}}, http.StatusCreated)
	if err != nil {
		return err
	}
	v.TaskID = domain.Str(task, "id")
	if err = saveState(s, *v); err != nil {
		return err
	}
	schedulerToken, err := e.svc.IssueCredential(ctx, v.SchedulerID, 15*time.Minute)
	if err != nil {
		return err
	}
	projectState, err := e.get(ctx, e.ownerToken, "/state")
	if err != nil {
		return err
	}
	if _, err = e.postSubject(ctx, schedulerToken, "/context-bundles", projectState, domain.Object{"task_id": task["id"], "expected_project_state_revision": projectState["revision"]}, http.StatusCreated); err != nil {
		return err
	}
	task, err = e.get(ctx, e.ownerToken, "/tasks/"+v.TaskID)
	if err != nil {
		return err
	}
	if task["status"] != "DRAFT" || task["context_bundle_id"] == nil {
		return errors.New("qualification task not a context-bound DRAFT")
	}
	if err = e.svc.RegisterRuntimeQualificationPlan(ctx, e.ownerToken, s.ProjectID, v.TaskID, v.RuntimeID, domain.Ref(artifact, "Artifact"), []any{"start", "context_rebuild"}, time.Hour, ""); err != nil {
		return fmt.Errorf("trusted qualification plan: %w", err)
	}
	return nil
}
