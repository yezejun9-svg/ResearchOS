//go:build windows

package main

// This optional fixture uses the actual fixed Mu SDK, AppContainer, coordinator,
// typed HTTP boundary and native Host. The model is an explicit loopback fixture.
// It grants no LIVE provider or construction acceptance authority.
import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"net/http/httptest"
	"os"
	"os/signal"
	"path/filepath"
	"sync/atomic"
	"time"

	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/host"
)

const permissionWrittenText = "Desktop 允许后的实际工具写入\n"

type permissionProfile struct {
	server   *httptest.Server
	calls    atomic.Int32
	expected string
}

func newPermissionProfile(source []byte) (*permissionProfile, error) {
	p := &permissionProfile{expected: domain.Digest(source)}
	p.server = httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/__researchos_fixture_readiness__" {
			w.WriteHeader(404)
			return
		}
		if r.URL.Path != "/v1/chat/completions" || r.Header.Get("Authorization") != "Bearer permission-loopback-fixture" {
			w.WriteHeader(403)
			return
		}
		var body domain.Object
		if json.NewDecoder(r.Body).Decode(&body) != nil || body["model"] != "fixture-model" {
			w.WriteHeader(400)
			return
		}
		n := p.calls.Add(1)
		delta, finish := domain.Object{"role": "assistant", "content": "qualified loopback fixture"}, "stop"
		if n == 2 {
			arguments := domain.Object{"path": "source.txt", "expected_hash": p.expected, "content": permissionWrittenText}
			delta = domain.Object{"role": "assistant", "tool_calls": []any{domain.Object{"index": 0, "id": "permission-original-write", "type": "function", "function": domain.Object{"name": "write", "arguments": string(domain.Bytes(arguments))}}}}
			finish = "tool_calls"
		} else if n == 3 {
			delta["content"] = "工具已报告实际写入；独立验收仍待进行。"
		} else if n != 1 {
			w.WriteHeader(409)
			return
		}
		w.Header().Set("Content-Type", "text/event-stream")
		for i, part := range []domain.Object{delta, {}} {
			var stop any
			if i == 1 {
				stop = finish
			}
			fmt.Fprintf(w, "data: %s\n\n", domain.Bytes(domain.Object{"id": "fixture-response", "object": "chat.completion.chunk", "created": 1, "model": "fixture-model", "choices": []any{domain.Object{"index": 0, "delta": part, "finish_reason": stop}}}))
		}
		fmt.Fprint(w, "data: [DONE]\n\n")
	}))
	return p, nil
}

func (p *permissionProfile) configure(config, profile domain.Object) (string, string, error) {
	node, bundle := os.Getenv("RESEARCHOS_NODE"), os.Getenv("RESEARCHOS_MU_BUNDLE")
	if node == "" || bundle == "" {
		return "", "", errors.New("explicit locked RESEARCHOS_NODE and immutable RESEARCHOS_MU_BUNDLE required")
	}
	node, err := filepath.EvalSymlinks(node)
	if err != nil {
		return "", "", err
	}
	binary, err := os.ReadFile(node)
	if err != nil {
		return "", "", err
	}
	raw, err := os.ReadFile(bundle)
	if err != nil {
		return "", "", err
	}
	config["provider"], config["model"], config["endpoint"] = "openai", "fixture-model", p.server.URL+"/v1/chat/completions"
	config["max_calls"], config["max_output_tokens"] = 4, 512
	config["tools"] = []any{domain.Object{"type": "function", "function": domain.Object{"name": "write", "description": "Write one exact authorized file after original-action permission", "parameters": domain.Object{"type": "object", "properties": domain.Object{"path": domain.Object{"type": "string"}, "expected_hash": domain.Object{"type": "string"}, "content": domain.Object{"type": "string"}}, "required": []any{"path", "expected_hash", "content"}, "additionalProperties": false}}}}
	profile["build_hash"], profile["bundle_hash"], profile["model"] = domain.Digest(binary), domain.Digest(raw), config["model"]
	profile["argv"] = []any{"--preserve-symlinks-main", "--preserve-symlinks", "{bundle}", "{manifest}"}
	profile["model_qualification"] = domain.Object{"route": config["route"], "model_config_hash": domain.Hash(config), "max_calls": 1}
	profile["effect_routes"] = append(domain.Arr(profile, "effect_routes"), domain.Object{"id": config["route"], "capability": "TOOL", "credential_revision": "local-tools-v1", "upper_bound": domain.Object{"amount": "0", "currency": "USD"}})
	profile["tool_policy"] = domain.Object{"max_calls": 1, "read_paths": []any{"source.txt"}, "write_paths": []any{"source.txt"}, "max_read_bytes": 4096, "max_write_bytes": 4096, "user_confirmation_tools": []any{"write"}}
	profile["timeout_seconds"] = 180
	return node, bundle, nil
}

func (p *permissionProfile) providers(project, runtime string, config domain.Object) []domain.RuntimeProviderRoute {
	model := domain.RuntimeProviderRoute{ID: domain.Str(config, "route"), ProjectID: project, RuntimeID: runtime, Purpose: "runtime_qualification", Capability: "MODEL", CredentialRevision: "none", Endpoint: domain.Str(config, "endpoint"), BearerToken: "permission-loopback-fixture", UpperBound: domain.Object{"amount": "1", "currency": "USD"}, MeasurementMode: "FIXTURE", ModelConfig: config}
	turn := model
	turn.Purpose = "mu_turn"
	tool := turn
	tool.Capability = "TOOL"
	tool.CredentialRevision = "local-tools-v1"
	tool.UpperBound = domain.Object{"amount": "0", "currency": "USD"}
	tool.BearerToken = ""
	tool.Endpoint = ""
	tool.ModelConfig = nil
	return []domain.RuntimeProviderRoute{model, turn, tool}
}

func permissionContract() domain.Object {
	c := domain.Object{"contract_revision": 1, "checks": []any{domain.Object{"check_id": "mu-turn-output", "kind": "DETERMINISTIC", "required": true, "expected": "Bounded Mu response with exact user-message provenance and reconciled model/tool effects; execution is not independent acceptance", "command_key": "mu.turn-output-v1", "rubric_ref": nil, "qualification_id": nil, "not_applicable_reason": nil}}, "require_independent_verifier": true, "version_policy": "EXACT", "frozen_at": domain.Now()}
	c["contract_hash"] = domain.Hash(c)
	return c
}

func qualifyPermissionProfile(ctx context.Context, s *domain.Service, c *domain.RuntimeCoordinator, route domain.RuntimeCoordinatorRoute, a, producer fixtureAPI, task, reg domain.Object, executor, ownerToken string) error {
	run, lease, err := s.BeginRuntimeQualification(ctx, ownerToken, a.project, domain.Str(task, "id"), domain.Str(reg, "id"), executor)
	if err != nil {
		return err
	}
	if err = c.RunAdmitted(ctx, route, run, lease); err != nil {
		return err
	}
	task, err = a.call(ctx, http.MethodGet, a.path("/tasks/"+domain.Str(task, "id")), "", nil, 200)
	if err != nil {
		return err
	}
	run, err = a.call(ctx, http.MethodGet, a.path("/runs/"+domain.Str(run, "id")), "", nil, 200)
	if err != nil {
		return err
	}
	if task["status"] != "EXECUTION_REPORTED" || len(domain.Arr(run, "result_artifact_ids")) == 0 {
		return errors.New("loopback SDK qualification did not settle with actual output")
	}
	artifact, err := a.call(ctx, http.MethodGet, a.path("/artifacts/"+domain.Arr(run, "result_artifact_ids")[0].(string)), "", nil, 200)
	if err != nil {
		return err
	}
	verifier := "w13-fixture-verifier-" + domain.ID()
	if err = s.ProvisionPrincipal(ctx, domain.Principal{ID: verifier, Roles: []string{"VERIFIER"}, Grants: []domain.Grant{{ProjectID: a.project}}}); err != nil {
		return err
	}
	verifierToken, err := s.IssueCredential(ctx, verifier, 15*time.Minute)
	if err != nil {
		return err
	}
	v := a
	v.token = verifierToken
	state, err := a.call(ctx, http.MethodGet, a.path("/state"), "", nil, 200)
	if err != nil {
		return err
	}
	contract := task["acceptance_contract"].(map[string]any)
	checks := domain.Empty()
	for _, value := range domain.Arr(contract, "checks") {
		check := value.(map[string]any)
		checks = append(checks, domain.Object{"check_id": check["check_id"], "status": "NOT_RUN", "evidence_refs": domain.Empty(), "command_key": check["command_key"], "actual": "request actual deterministic service computation for FIXTURE runtime", "exit_code": nil, "started_at": nil, "finished_at": nil})
	}
	receipt, err := v.postSubject(ctx, a.path("/acceptances"), task, domain.Object{"subject_ref": domain.Ref(task, "Task"), "run_id": run["id"], "contract_hash": contract["contract_hash"], "input_refs": task["input_refs"], "artifact_refs": []any{domain.Ref(artifact, "Artifact")}, "checks": checks, "verdict": "PASS", "executor_principal_ids": []any{executor}, "independence_basis": "DETERMINISTIC_SERVICE", "blocking_conflict_ids": domain.Empty(), "qualification_ids": domain.Empty(), "policy_revision": state["policy_revision"], "measurement_mode": "FIXTURE", "reason": "Actual deterministic loopback SDK fixture qualification; no LIVE resource"}, 201)
	if err != nil {
		return err
	}
	if receipt["verdict"] != "PASS" {
		return errors.New("actual FIXTURE qualification rejected")
	}
	var logRaw string
	if err = s.DB.QueryRowContext(ctx, "SELECT body FROM domain_objects WHERE project=? AND kind='Artifact' AND json_extract(body,'$.run_id')=? AND json_extract(body,'$.kind')='LOG'", a.project, run["id"]).Scan(&logRaw); err != nil {
		return err
	}
	log, err := domain.Decode([]byte(logRaw))
	if err != nil {
		return err
	}
	reg, err = v.postSubject(ctx, a.path("/runtimes/"+domain.Str(reg, "id")+"/qualify"), reg, domain.Object{"qualification_ids": []any{receipt["id"]}, "supports_resume": false, "resume_evidence_ref": nil, "receipt_artifact_ref": domain.Ref(log, "Artifact")}, 200)
	if err != nil {
		return err
	}
	if reg["status"] != "AVAILABLE" {
		return errors.New("FIXTURE runtime unavailable")
	}
	return s.AuthorizeRuntimePurpose(ctx, ownerToken, a.project, route.RuntimeID, "mu_turn", time.Now().Add(30*time.Minute))
}

func servePermissionFixture(ctx context.Context, db *sql.DB, c *domain.RuntimeCoordinator, h *host.Host, client *http.Client, base, token, project, session, ref, root, dataDir, addr string, p *permissionProfile) error {
	snap, err := command(ctx, client, base, token, "session.get", "permission-before-send", &project, &session, nil, nil, domain.Object{})
	if err != nil {
		return err
	}
	revision, err := domain.Num(snap, "revision")
	if err != nil {
		return err
	}
	writer := snap["writer"].(map[string]any)
	epoch, err := domain.Num(writer, "epoch")
	if err != nil {
		return err
	}
	_, err = command(ctx, client, base, token, "session.send", "permission-original-turn", &project, &session, revision, epoch, domain.Object{"text": "Write the exact source.txt bytes through the authorized write tool; wait for the original-action permission.", "attachment_artifact_ids": domain.Empty(), "delivery": "NORMAL"})
	if err != nil {
		return err
	}
	if err = c.Scan(ctx); err != nil {
		return err
	}
	var prompt domain.Object
	deadline := time.Now().Add(45 * time.Second)
	for time.Now().Before(deadline) {
		snap, err = command(ctx, client, base, token, "session.get", "permission-wait-"+domain.ID(), &project, &session, nil, nil, domain.Object{})
		if err != nil {
			return err
		}
		pending := domain.Arr(snap, "pending_permissions")
		if len(pending) == 1 {
			prompt = pending[0].(map[string]any)
			break
		}
		time.Sleep(100 * time.Millisecond)
	}
	if prompt == nil {
		return errors.New("actual original tool permission was not produced")
	}
	discovery := filepath.Join(dataDir, "discovery.json")
	if err = writeDiscovery(discovery, addr, dataDir, h.InstanceID()); err != nil {
		return err
	}
	output := domain.Object{"ready": true, "fixture": "W13 original tool permission with real Mu/Host and loopback FIXTURE model", "base_url": base, "discovery_file": discovery, "project_id": project, "session_id": session, "workspace_ref": ref, "workspace_root": root, "source_path": "source.txt", "expected_written_text": permissionWrittenText, "original_task_id": prompt["task_id"], "original_run_id": prompt["run_id"], "prompt": prompt, "measurement_mode": "FIXTURE", "provider_kind": "LOOPBACK_FIXTURE", "external_provider_calls": 0, "loopback_model_calls_before_ui": p.calls.Load(), "credential_file": h.SessionFile(), "limitations": []any{"Folder selection uses a FIXTURE callback", "Actual deterministic qualification applies only to this loopback FIXTURE runtime", "Construction independent acceptance and LIVE provider qualification are NOT_RUN"}}
	if err = json.NewEncoder(os.Stdout).Encode(output); err != nil {
		return err
	}
	wait, stop := signal.NotifyContext(context.Background(), os.Interrupt)
	defer stop()
	<-wait.Done()
	return nil
}
