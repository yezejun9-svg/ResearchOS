//go:build windows

package main

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"sync"
	"time"

	localworkspace "researchos.local/research-os/adapters/local_workspace"
	"researchos.local/research-os/internal/api"
	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/host"
)

const fixtureModelRef = "w13-local-model-fixture-v1"

type switchableHandler struct {
	mu sync.RWMutex
	h  http.Handler
}

func (s *switchableHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	s.mu.RLock()
	h := s.h
	s.mu.RUnlock()
	h.ServeHTTP(w, r)
}

func (s *switchableHandler) swap(h http.Handler) {
	s.mu.Lock()
	s.h = h
	s.mu.Unlock()
}

type fixtureAPI struct {
	client               *http.Client
	base, token, project string
}

func (a fixtureAPI) call(ctx context.Context, method, path, tag string, body any, want int) (domain.Object, error) {
	var raw []byte
	if body != nil {
		if value, ok := body.([]byte); ok {
			raw = value
		} else {
			raw = domain.Bytes(body)
		}
	}
	req, err := http.NewRequestWithContext(ctx, method, a.base+path, bytes.NewReader(raw))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Authorization", "Bearer "+a.token)
	if method != http.MethodGet {
		req.Header.Set("Idempotency-Key", domain.ID())
	}
	if tag != "" {
		req.Header.Set("If-Match", tag)
	}
	if body != nil {
		req.Header.Set("Content-Type", "application/json")
	}
	response, err := a.client.Do(req)
	if err != nil {
		return nil, err
	}
	defer response.Body.Close()
	data, err := io.ReadAll(io.LimitReader(response.Body, 4<<20))
	if err != nil {
		return nil, err
	}
	var result domain.Object
	if err := json.Unmarshal(data, &result); err != nil {
		return nil, fmt.Errorf("fixture %s %s invalid JSON: %w", method, path, err)
	}
	if response.StatusCode != want {
		return nil, fmt.Errorf("fixture %s %s HTTP %d expected %d: %s", method, path, response.StatusCode, want, data)
	}
	return result, nil
}

func (a fixtureAPI) path(tail string) string { return "/v1/projects/" + a.project + tail }

func (a fixtureAPI) stateTag(ctx context.Context) (string, error) {
	state, err := a.call(ctx, http.MethodGet, a.path("/state"), "", nil, 200)
	if err != nil {
		return "", err
	}
	revision, err := domain.Num(state, "revision")
	if err != nil {
		return "", err
	}
	return `"r` + strconv.FormatInt(revision, 10) + `"`, nil
}

func fixtureTag(value domain.Object) (string, error) {
	revision, err := domain.Num(value, "revision")
	if err != nil {
		return "", err
	}
	return `"r` + strconv.FormatInt(revision, 10) + `"`, nil
}

func (a fixtureAPI) postState(ctx context.Context, path string, body any, want int) (domain.Object, error) {
	tag, err := a.stateTag(ctx)
	if err != nil {
		return nil, err
	}
	return a.call(ctx, http.MethodPost, path, tag, body, want)
}

func (a fixtureAPI) postSubject(ctx context.Context, path string, subject domain.Object, body any, want int) (domain.Object, error) {
	tag, err := fixtureTag(subject)
	if err != nil {
		return nil, err
	}
	return a.call(ctx, http.MethodPost, path, tag, body, want)
}

func fixtureContract() domain.Object {
	contract := domain.Object{"contract_revision": 1, "checks": []any{domain.Object{
		"check_id": "fixture-scope", "kind": "DETERMINISTIC", "required": true,
		"expected":    "No fixture provider execution; scoped desktop workspace write only",
		"command_key": "w13.fixture-scope", "rubric_ref": nil, "qualification_id": nil,
		"not_applicable_reason": nil,
	}}, "require_independent_verifier": true, "version_policy": "EXACT", "frozen_at": domain.Now()}
	contract["contract_hash"] = domain.Hash(contract)
	return contract
}

// fixtureModelProfile creates real domain objects and an immutable runtime
// binding. Its inert bundle and non-routable endpoint are metadata only. No
// qualification, worker start, model request or provider probe is performed.
func fixtureModelProfile(ctx context.Context, svc *domain.Service, h *host.Host, client *http.Client, base, token, project, dataDir string, permission *permissionProfile) (*domain.RuntimeCoordinator, error) {
	a := fixtureAPI{client: client, base: base, token: token, project: project}
	reg, err := a.postState(ctx, a.path("/runtimes"), domain.Object{
		"name": "W13 desktop inert Mu profile", "adapter": "codex-cli",
		"adapter_revision": "windows-appcontainer-v1", "capabilities": []any{"start", "context_rebuild"},
		"platform": "windows-amd64", "measurement_mode": "FIXTURE", "credential_ref": nil,
	}, 201)
	if err != nil {
		return nil, err
	}
	executorID, schedulerID := "w13-executor-"+domain.ID(), "w13-scheduler-"+domain.ID()
	if err := svc.ProvisionPrincipal(ctx, domain.Principal{ID: executorID, Roles: []string{"EXECUTOR"}, Grants: []domain.Grant{{ProjectID: project}}}); err != nil {
		return nil, err
	}
	if err := svc.ProvisionPrincipal(ctx, domain.Principal{ID: schedulerID, Roles: []string{"SCHEDULER"}, Grants: []domain.Grant{{ProjectID: project}}}); err != nil {
		return nil, err
	}
	executorToken, err := svc.IssueCredential(ctx, executorID, 15*time.Minute)
	if err != nil {
		return nil, err
	}
	schedulerToken, err := svc.IssueCredential(ctx, schedulerID, 15*time.Minute)
	if err != nil {
		return nil, err
	}
	producer := fixtureAPI{client: client, base: base, token: executorToken, project: project}
	exe, err := os.Executable()
	if err != nil {
		return nil, err
	}
	exeBytes, err := os.ReadFile(exe)
	if err != nil {
		return nil, err
	}
	bundle := filepath.Join(dataDir, "inert-model-bundle.mjs")
	bundleBytes := []byte("// Inert W13 metadata. Never executed.\n")
	if err := os.WriteFile(bundle, bundleBytes, 0600); err != nil {
		return nil, err
	}
	config := domain.Object{"ref": fixtureModelRef, "api": "openai-completions", "provider": "w13-fixture", "model": "inert-local-model", "endpoint": "http://127.0.0.1:1/v1/chat/completions", "route": "w13-inert-model", "max_output_tokens": 64, "max_calls": 1, "tools": domain.Empty()}
	profile := domain.Object{
		"runtime_id": reg["id"], "technical_hash": domain.Hash([]any{reg["adapter"], reg["adapter_revision"], reg["capabilities"], reg["platform"], reg["measurement_mode"], reg["credential_ref"]}),
		"adapter": reg["adapter"], "adapter_revision": reg["adapter_revision"], "platform": "windows-amd64",
		"build_hash": domain.Digest(exeBytes), "sandbox": "appcontainer-zero-capabilities-v1", "credential_revision": "none",
		"backend": "mu-sdk-broker-v1", "model": config["model"], "command_id": "w13-inert-mu-fixture",
		"argv": []any{"{bundle}", "{manifest}"}, "bundle_hash": domain.Digest(bundleBytes),
		"model_config": config, "model_qualification": domain.Object{"route": config["route"], "model_config_hash": domain.Hash(config), "max_calls": 1},
		"effect_routes":   []any{domain.Object{"id": config["route"], "capability": "MODEL", "credential_revision": "none", "upper_bound": domain.Object{"amount": "1", "currency": "USD"}}},
		"permissions":     domain.Object{"network": "none", "environment": "staging-only", "capabilities": domain.Empty(), "process_limit": 1, "memory_mib": 256},
		"timeout_seconds": 15, "outputs": []any{"result.json"},
		"tool_policy": domain.Object{"max_calls": 1, "read_paths": []any{"source.txt"}, "write_paths": []any{"source.txt"}, "max_read_bytes": 4096, "max_write_bytes": 4096},
	}
	if permission != nil {
		exe, bundle, err = permission.configure(config, profile)
		if err != nil {
			return nil, err
		}
	}
	raw := domain.Bytes(profile)
	upload, err := producer.call(ctx, http.MethodPost, a.path("/content"), "", raw, 201)
	if err != nil {
		return nil, err
	}
	artifact, err := producer.postState(ctx, a.path("/artifacts"), domain.Object{
		"run_id": nil, "kind": "REPORT", "evidence_kind": "GENERATED", "measurement_mode": "FIXTURE",
		"content_hash": upload["content_hash"], "storage_key": upload["storage_key"],
		"media_type": "application/json", "byte_size": len(raw), "input_refs": domain.Empty(), "source_refs": domain.Empty(),
		"produced_by": executorID, "access_class": "PROJECT",
	}, 201)
	if err != nil {
		return nil, err
	}
	profileRef := domain.Ref(artifact, "Artifact")
	req, err := a.postState(ctx, a.path("/requirements"), domain.Object{
		"requirement_key": "W13-DESKTOP-WORKSPACE-FIXTURE", "text": "Verify a bounded desktop workspace write without executing a provider",
		"basis": "USER_STATED", "source_refs": domain.Empty(), "rationale": "W13 temporary fixture",
		"supersedes_id": nil, "acceptance_check_ids": domain.Empty(),
	}, 201)
	if err != nil {
		return nil, err
	}
	req, err = a.postSubject(ctx, a.path("/requirements/"+domain.Str(req, "id")+"/actions"), req,
		domain.Object{"action": "ACCEPT", "reason": "W13 fixture", "source_validation_refs": domain.Empty()}, 200)
	if err != nil {
		return nil, err
	}
	contract := fixtureContract()
	if permission != nil {
		contract = permissionContract()
	}
	goal, err := a.postState(ctx, a.path("/goals"), domain.Object{
		"title": "W13 inert runtime qualification plan", "original_intent": "Establish a frozen write boundary without dispatch",
		"scope": "PROJECT", "requirement_refs": []any{domain.Ref(req, "Requirement")},
		"problem_ids": []any{"w13-write-fixture"}, "deliverables": []any{"No provider execution"}, "acceptance_contract": contract,
	}, 201)
	if err != nil {
		return nil, err
	}
	goal, err = a.postSubject(ctx, a.path("/goals/"+domain.Str(goal, "id")+"/actions"), goal,
		domain.Object{"action": "ACTIVATE", "reason": "W13 fixture"}, 200)
	if err != nil {
		return nil, err
	}
	task, err := a.postSubject(ctx, a.path("/tasks"), goal, domain.Object{
		"goal_id": goal["id"], "title": "W13 frozen runtime metadata", "task_type": "runtime_qualification",
		"stage": "verification", "dependency_task_ids": domain.Empty(), "requirement_refs": []any{domain.Ref(req, "Requirement")},
		"input_refs": []any{profileRef}, "acceptance_contract": contract, "origin_problem_id": "w13-write-fixture",
		"candidate_id": "w13-write-fixture", "stop_policy": domain.Object{"wall_time_seconds": 60, "max_attempts": 1,
			"max_parallel_runs": 1, "stop_conditions": []any{"no progress"}},
	}, 201)
	if err != nil {
		return nil, err
	}
	state, err := a.call(ctx, http.MethodGet, a.path("/state"), "", nil, 200)
	if err != nil {
		return nil, err
	}
	stateRevision, err := domain.Num(state, "revision")
	if err != nil {
		return nil, err
	}
	schedulerAPI := fixtureAPI{client: client, base: base, token: schedulerToken, project: project}
	_, err = schedulerAPI.postSubject(ctx, a.path("/context-bundles"), state,
		domain.Object{"task_id": task["id"], "expected_project_state_revision": stateRevision}, 201)
	if err != nil {
		return nil, err
	}
	if err := svc.RegisterRuntimeQualificationPlan(ctx, token, project, domain.Str(task, "id"), domain.Str(reg, "id"), profileRef, []any{"start", "context_rebuild"}, time.Hour, ""); err != nil {
		return nil, err
	}
	doc, err := api.ClientProtocolDocument()
	if err != nil {
		return nil, err
	}
	authority := localworkspace.NewAuthority(h)
	coordinatorConfig := domain.RuntimeCoordinatorConfig{
		DataRoot: dataDir, APIURL: base, SchedulerToken: schedulerToken,
		Routes: []domain.RuntimeCoordinatorRoute{{ProjectID: project, RuntimeID: domain.Str(reg, "id"), ExecutorID: executorID,
			ExecutorToken: executorToken, CommandID: "w13-inert-mu-fixture", Executable: exe, BundleFile: bundle}},
		WorkspaceAuthority: authority, RunTool: h.ExecuteRuntimeTool, ClientSchema: doc,
	}
	if permission != nil {
		coordinatorConfig.Providers = permission.providers(project, domain.Str(reg, "id"), config)
	}
	coordinator, err := svc.NewRuntimeCoordinator(ctx, coordinatorConfig)
	if err != nil {
		return nil, err
	}
	if coordinator == nil {
		return nil, errors.New("fixture coordinator unavailable")
	}
	if permission != nil {
		if err := qualifyPermissionProfile(ctx, svc, coordinator, coordinatorConfig.Routes[0], a, producer, task, reg, executorID, token); err != nil {
			coordinator.Close()
			return nil, err
		}
	}
	return coordinator, nil
}
