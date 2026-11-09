//go:build windows

package domain

import (
	"context"
	"database/sql"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"
)

type RuntimeSetupCandidate struct{ ProjectID, SessionID, PrincipalID, ModelRef string }
type RuntimeSetupAssets struct{ Executable, BundleFile, BuildHash, BundleHash string }
type RuntimeSetupResult struct {
	ProjectID, ModelRef, RuntimeID, TaskID string
	ProfileRef                             Object
}

// RuntimeSetupCandidates reads only committed product sessions. A default-only
// configuration has no project authority and does not prepare any runtime yet.
func (s *Service) RuntimeSetupCandidates(ctx context.Context, ownerHost string) ([]RuntimeSetupCandidate, error) {
	rows, err := s.DB.QueryContext(ctx, `SELECT s.project_id,s.id,m.principal,s.model_config_ref FROM client_sessions s JOIN host_model_configurations m ON m.model_config_ref=s.model_config_ref WHERE m.owner_host_ref=? ORDER BY s.project_id,s.id`, ownerHost)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	out := []RuntimeSetupCandidate{}
	seen := map[string]bool{}
	for rows.Next() {
		var c RuntimeSetupCandidate
		if err = rows.Scan(&c.ProjectID, &c.SessionID, &c.PrincipalID, &c.ModelRef); err != nil {
			return nil, err
		}
		key := runtimeSetupKey(c.ProjectID, c.ModelRef)
		if !seen[key] {
			out = append(out, c)
			seen[key] = true
		}
	}
	return out, rows.Err()
}

func (s *Service) runtimeSetupConfiguration(ctx context.Context, tx *sql.Tx, p Principal, candidate RuntimeSetupCandidate, schema *SchemaDoc, authority ClientConfigurationAuthority) (clientConfigurationRecord, error) {
	bad := func() (clientConfigurationRecord, error) {
		return clientConfigurationRecord{}, Fail(403, "FORBIDDEN", "runtime setup requires this Owner's current committed session")
	}
	if p.ID != candidate.PrincipalID || !p.HasRole("OWNER") || !p.Allowed(candidate.ProjectID, "", "", false) {
		return bad()
	}
	client := &ClientService{Domain: s, Doc: schema, ConfigurationAuthority: authority}
	sess, err := loadClientSession(ctx, tx, candidate.SessionID, candidate.ProjectID)
	if err != nil {
		return bad()
	}
	if err = client.validateSessionConfiguration(ctx, tx, p.ID, sess, true); err != nil {
		return clientConfigurationRecord{}, err
	}
	var model string
	if err = tx.QueryRowContext(ctx, `SELECT model_config_ref FROM client_sessions WHERE id=? AND project_id=?`, candidate.SessionID, candidate.ProjectID).Scan(&model); err != nil || model != candidate.ModelRef {
		return bad()
	}
	record, err := client.visibleClientConfiguration(ctx, tx, p.ID, candidate.ModelRef)
	if err != nil {
		return record, err
	}
	endpoint, err := clientConfigurationEndpoint(record.Payload.BaseURL, record.Payload.Credential)
	if err != nil || record.Payload.Credential != nil || !clientConfigurationLoopbackModelEndpoint(endpoint) {
		return record, Fail(503, "MODEL_UNAVAILABLE", "automatic runtime preparation requires a credential-free numeric loopback model; other providers need a configured host runtime")
	}
	return record, nil
}

// ValidateRuntimeSetup is read-only and lets the trusted host refuse foreign,
// revoked or remote configurations before inspecting resources or provisioning.
func (s *Service) ValidateRuntimeSetup(ctx context.Context, token string, candidate RuntimeSetupCandidate, schema *SchemaDoc, authority ClientConfigurationAuthority) error {
	tx, err := s.DB.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	p, err := authenticate(tx, token)
	if err != nil {
		return err
	}
	_, err = s.runtimeSetupConfiguration(ctx, tx, p, candidate, schema, authority)
	return err
}

func checkRuntimeSetupAssets(assets RuntimeSetupAssets) error {
	for _, pair := range [][2]string{{assets.Executable, assets.BuildHash}, {assets.BundleFile, assets.BundleHash}} {
		if !filepath.IsAbs(pair[0]) || len(pair[1]) != 71 || !strings.HasPrefix(pair[1], "sha256:") {
			return Fail(503, "MODEL_UNAVAILABLE", "runtime assets are not hash-pinned")
		}
		resolved, err := filepath.EvalSymlinks(pair[0])
		if err != nil || !strings.EqualFold(filepath.Clean(resolved), filepath.Clean(pair[0])) {
			return Fail(503, "MODEL_UNAVAILABLE", "runtime asset path is unavailable or changed")
		}
		raw, err := os.ReadFile(pair[0])
		if err != nil || Digest(raw) != pair[1] {
			return Fail(503, "MODEL_UNAVAILABLE", "runtime asset bytes differ from the host build metadata")
		}
	}
	return nil
}

// PrepareClientRuntime is a trusted host operation. It performs no provider IO,
// creates no Run and grants no availability. All domain creation, profile seal,
// context freeze and plan registration commit together through existing gates.
func (s *Service) PrepareClientRuntime(ctx context.Context, token string, candidate RuntimeSetupCandidate, assets RuntimeSetupAssets, schema *SchemaDoc, authority ClientConfigurationAuthority) (RuntimeSetupResult, error) {
	var result RuntimeSetupResult
	if err := checkRuntimeSetupAssets(assets); err != nil {
		return result, err
	}
	tx, err := s.DB.BeginTx(ctx, nil)
	if err != nil {
		return result, err
	}
	defer tx.Rollback()
	p, err := authenticate(tx, token)
	if err != nil {
		return result, err
	}
	result, err = s.prepareClientRuntimeTx(ctx, tx, p, candidate, assets, schema, authority)
	if err != nil {
		return result, err
	}
	return result, tx.Commit()
}

// The caller owns the transaction. Coding installation uses this same path
// after its original host.configure CAS, before publishing the new reference.
func (s *Service) prepareClientRuntimeTx(ctx context.Context, tx *sql.Tx, p Principal, candidate RuntimeSetupCandidate, assets RuntimeSetupAssets, schema *SchemaDoc, authority ClientConfigurationAuthority) (RuntimeSetupResult, error) {
	var result RuntimeSetupResult
	record, err := s.runtimeSetupConfiguration(ctx, tx, p, candidate, schema, authority)
	if err != nil {
		return result, err
	}
	project := candidate.ProjectID
	coding, err := runtimeCodingAuthorization(ctx, tx, p.ID, project, record.Ref)
	if err != nil {
		return result, err
	}
	key := Hash([]any{"researchos.local-runtime-setup.v1", record.Owner, p.ID, project, record.Ref})
	// The existing immutable profile and plan are the persistence index. Neither
	// a second queue nor an editable host-state cache becomes business authority.
	rows, err := tx.Query(`SELECT id FROM domain_objects WHERE project=? AND kind='RuntimeRegistration' AND json_extract(body,'$.name')=?`, project, "Local configured model "+record.Ref)
	if err != nil {
		return result, err
	}
	ids := []string{}
	for rows.Next() {
		var id string
		if err = rows.Scan(&id); err != nil {
			rows.Close()
			return result, err
		}
		ids = append(ids, id)
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return result, err
	}
	found := false
	for _, id := range ids {
		runtime, e := load(tx, project, "RuntimeRegistration", id)
		if e != nil {
			return result, e
		}
		ref, artifact, e := s.currentRuntimeBinding(tx, project, runtime)
		if e != nil {
			return result, e
		}
		profile, e := runtimeProfileBody(tx, project, artifact)
		if e != nil {
			return result, e
		}
		setup, _ := profile["host_setup"].(map[string]any)
		if setup["key"] != key {
			continue
		}
		if Hash(profile["coding_authorization"]) != Hash(coding) {
			return result, Fail(412, "STALE_INPUT", "prepared coding authorization differs from its immutable configuration")
		}
		if found {
			return result, Fail(409, "MODEL_UNAVAILABLE", "multiple prepared runtimes bind this configuration")
		}
		found = true
		if setup["config_hash"] != record.ConfigHash || profile["build_hash"] != assets.BuildHash || profile["bundle_hash"] != assets.BundleHash || runtime["status"] == "REVOKED" || runtime["status"] == "UNAVAILABLE" {
			return result, Fail(412, "STALE_INPUT", "prepared runtime changed; explicit new qualification is required")
		}
		var taskID string
		if e = tx.QueryRow(`SELECT task FROM runtime_qualification_plans WHERE project=? AND runtime=?`, project, id).Scan(&taskID); e != nil {
			return result, Fail(503, "MODEL_UNAVAILABLE", "prepared runtime plan is missing")
		}
		plan, _, root, e := qualificationPlan(tx, project, taskID, id)
		if e != nil {
			return result, e
		}
		ownerRoot, e := authorityRoot(tx, p.ID)
		if e != nil || root != ownerRoot || Hash(plan["profile_ref"]) != Hash(ref) {
			return result, Fail(412, "STALE_INPUT", "prepared runtime plan authority changed")
		}
		task, e := load(tx, project, "Task", taskID)
		if e != nil || qualificationTaskHash(task) != plan["task_hash"] {
			return result, Fail(412, "STALE_INPUT", "prepared runtime qualification inputs changed")
		}
		result = RuntimeSetupResult{ProjectID: project, ModelRef: record.Ref, RuntimeID: id, TaskID: taskID, ProfileRef: ref}
	}
	if found {
		return result, nil
	}

	registration := Object{"name": "Local configured model " + record.Ref, "adapter": "codex-cli", "adapter_revision": runtimeBridgeRevision, "capabilities": []any{"start", "context_rebuild"}, "platform": "windows-amd64", "measurement_mode": "LIVE", "credential_ref": nil}
	if err = s.Contracts.Validate("CreateRuntimeRequest", registration); err != nil {
		return result, err
	}
	runtime, _, _, err := s.runtimeOperation(tx, p, project, "", registration, "registerRuntime", ID())
	if err != nil {
		return result, err
	}
	endpoint, _ := clientConfigurationEndpoint(record.Payload.BaseURL, nil)
	routeID := "local-model-" + strings.TrimPrefix(key, "sha256:")[:24]
	model := Object{"ref": record.Ref, "api": "openai-completions", "provider": record.Payload.Provider, "model": record.Payload.Model, "endpoint": endpoint, "route": routeID, "max_output_tokens": 512, "max_calls": 1, "tools": Empty()}
	profile := Object{"runtime_id": runtime["id"], "technical_hash": runtimeTechnicalHash(runtime), "adapter": runtime["adapter"], "adapter_revision": runtimeBridgeRevision, "platform": "windows-amd64", "build_hash": assets.BuildHash, "bundle_hash": assets.BundleHash, "sandbox": runtimeSandboxProfile, "credential_revision": "none", "backend": runtimeMuBackend, "model": record.Payload.Model, "model_config": model, "command_id": "mu-local-model-v1", "argv": []any{"--preserve-symlinks-main", "--preserve-symlinks", "{bundle}", "{manifest}"}, "effect_routes": []any{Object{"id": routeID, "capability": "MODEL", "credential_revision": "none", "upper_bound": nil}}, "permissions": Object{"network": "none", "environment": "staging-only", "capabilities": Empty(), "process_limit": 1, "memory_mib": 256}, "timeout_seconds": 60, "outputs": []any{"result.json"}, "max_cost": nil, "model_qualification": Object{"route": routeID, "model_config_hash": Hash(model), "max_calls": 1}, "host_setup": Object{"schema": "researchos.local-runtime-setup.v1", "key": key, "owner_host": record.Owner, "principal": p.ID, "model_config_ref": record.Ref, "config_hash": record.ConfigHash, "configuration_command_id": record.CommandID, "configuration_request_hash": record.RequestHash, "initial_session_id": candidate.SessionID}}
	if coding != nil {
		if err = applyRuntimeCodingProfile(profile, coding); err != nil {
			return result, err
		}
	}
	if err = validateRuntimeDispatchProfile(profile); err != nil {
		return result, err
	}
	artifact, err := s.sealRuntimeSetupProfile(tx, p, project, profile)
	if err != nil {
		return result, err
	}
	profileRef := Ref(artifact, "Artifact")
	// This is an observed committed model selection, never a fabricated user
	// research goal or an independently accepted runtime result.
	requirement, err := s.createRequirement(tx, project, Object{"requirement_key": "LOCAL-RUNTIME-" + strings.TrimPrefix(key, "sha256:")[:24], "text": "This project's committed session selects model configuration " + record.Ref + "; prepare its bounded local runtime without dispatch.", "basis": "OBSERVED", "source_refs": []any{profileRef}, "rationale": "Trusted host verified the original configuration and session receipts; execution and independent runtime acceptance remain pending.", "supersedes_id": nil, "acceptance_check_ids": Empty()})
	if err != nil {
		return result, err
	}
	requirement, err = s.actRequirement(tx, project, Str(requirement, "id"), Object{"action": "ACCEPT", "source_validation_refs": []any{profileRef}})
	if err != nil {
		return result, err
	}
	contract := clientTurnContract()
	goal, err := s.createGoal(tx, project, Object{"title": "Local runtime qualification: " + record.Payload.Model, "original_intent": "Verify one bounded response from the selected local model through the frozen Mu worker, with exact context provenance and reconciled effects. This is runtime qualification only; do not use tools or change files.", "scope": "PROJECT", "requirement_refs": []any{Ref(requirement, "Requirement")}, "problem_ids": []any{routeID}, "deliverables": []any{"Hash-bound native runtime qualification evidence awaiting independent verification"}, "acceptance_contract": contract})
	if err != nil {
		return result, err
	}
	if _, err = s.actGoal(tx, project, Str(goal, "id"), Object{"action": "ACTIVATE", "reason": "Offline host preparation of the explicitly selected local model; no Run is authorized or dispatched by preparation"}); err != nil {
		return result, err
	}
	task, err := s.createTask(tx, project, Object{"goal_id": goal["id"], "title": "Qualify selected local model runtime", "task_type": "runtime_qualification", "stage": "verification", "dependency_task_ids": Empty(), "requirement_refs": []any{Ref(requirement, "Requirement")}, "input_refs": []any{profileRef}, "acceptance_contract": contract, "origin_problem_id": routeID, "candidate_id": record.Ref, "stop_policy": Object{"wall_time_seconds": 90, "max_attempts": 1, "max_parallel_runs": 1, "stop_conditions": []any{"one bounded call", "configuration drift", "unknown effect requires reconciliation"}}})
	if err != nil {
		return result, err
	}
	state, err := singleton(tx, project, "ProjectState")
	if err != nil {
		return result, err
	}
	if _, err = s.createContext(tx, p, project, Object{"task_id": task["id"], "expected_project_state_revision": state["revision"]}); err != nil {
		return result, err
	}
	if err = s.registerRuntimeQualificationPlanTx(tx, p, project, Str(task, "id"), Str(runtime, "id"), profileRef, []any{"start", "context_rebuild"}, 24*time.Hour, ""); err != nil {
		return result, err
	}
	if err = s.event(tx, project, "RuntimeRegistration", runtime, p.ID, ID(), "PROJECT_UPDATED"); err != nil {
		return result, err
	}
	result = RuntimeSetupResult{ProjectID: project, ModelRef: record.Ref, RuntimeID: Str(runtime, "id"), TaskID: Str(task, "id"), ProfileRef: profileRef}
	return result, nil
}

func (s *Service) sealRuntimeSetupProfile(tx *sql.Tx, p Principal, project string, body Object) (Object, error) {
	upload, err := s.upload(tx, p, project, Bytes(body))
	if err != nil {
		return nil, err
	}
	b := Object{"kind": "MANIFEST", "evidence_kind": "GENERATED", "measurement_mode": "LIVE", "media_type": "application/json", "storage_key": upload["storage_key"], "content_hash": upload["content_hash"], "byte_size": upload["byte_size"], "produced_by": p.ID, "run_id": nil, "input_refs": Empty(), "source_refs": Empty(), "access_class": "PROJECT"}
	if err = s.Contracts.Validate("CreateArtifactRequest", b); err != nil {
		return nil, fmt.Errorf("runtime profile seal: %w", err)
	}
	return s.seal(tx, p, project, b)
}

// EnsureRuntimeSetupPrincipal provisions only host-owned scheduler/executor
// roles. Their lineage is the Owner's root, so neither can pass as an independent
// verifier. Existing revoked or changed identities are never recreated.
func (s *Service) EnsureRuntimeSetupPrincipal(ctx context.Context, ownerToken, project, role string) (string, error) {
	if role != "SCHEDULER" && role != "EXECUTOR" {
		return "", Fail(403, "FORBIDDEN", "runtime setup cannot provision this role")
	}
	tx, err := s.DB.BeginTx(ctx, nil)
	if err != nil {
		return "", err
	}
	p, err := authenticate(tx, ownerToken)
	if err != nil || !p.HasRole("OWNER") || !p.Allowed(project, "", "", false) {
		tx.Rollback()
		return "", Fail(403, "FORBIDDEN", "current project Owner required")
	}
	ownerRoot, err := authorityRoot(tx, p.ID)
	if err != nil {
		tx.Rollback()
		return "", err
	}
	id := "local-" + strings.ToLower(role) + "-" + strings.TrimPrefix(Hash([]any{p.ID, project, role}), "sha256:")[:32]
	var count int
	err = tx.QueryRow("SELECT count(*) FROM auth_principals WHERE id=?", id).Scan(&count)
	if err == nil && count != 0 {
		current, e := clientAuthenticatedPrincipal(ctx, tx, id)
		if e != nil || len(current.Roles) != 1 || !current.HasRole(role) || current.CanCreateProject {
			err = Fail(403, "FORBIDDEN", "host runtime principal is revoked or changed")
		} else if e = runtimeSetupGrants(tx, current, project, role); e != nil {
			err = e
		}
	}
	tx.Rollback()
	if err != nil {
		return "", err
	}
	if count == 0 {
		if err = s.ProvisionPrincipal(ctx, Principal{ID: id, Roles: []string{role}, Grants: []Grant{{ProjectID: project}}}); err != nil {
			return "", err
		}
	}
	var root, parent string
	err = s.DB.QueryRowContext(ctx, "SELECT root,parent FROM orchestration_identity WHERE principal=?", id).Scan(&root, &parent)
	if err == sql.ErrNoRows {
		err = s.RegisterExecutionIdentity(ctx, id, p.ID)
	} else if err == nil && (parent != p.ID || root != ownerRoot) {
		err = Fail(403, "FORBIDDEN", "host runtime identity lineage changed")
	}
	if err != nil {
		return "", err
	}
	return id, nil
}

// createRuntimeRun adds a narrow executor grant in its claim transaction. Only
// those exact current or historical Run bindings may accompany the base grant.
func runtimeSetupGrants(tx *sql.Tx, p Principal, project, role string) error {
	base := 0
	for _, grant := range p.Grants {
		if grant == (Grant{ProjectID: project}) {
			base++
			continue
		}
		if role != "EXECUTOR" || grant.ProjectID != project || grant.Restricted || grant.TaskID == "" || grant.RunID == "" {
			return Fail(403, "FORBIDDEN", "host runtime principal has an unrelated grant")
		}
		run, e := load(tx, project, "Run", grant.RunID)
		if e != nil || run["task_id"] != grant.TaskID || run["executor_principal_id"] != p.ID {
			return Fail(403, "FORBIDDEN", "host runtime grant has no matching executor Run")
		}
		task, e := load(tx, project, "Task", grant.TaskID)
		if e != nil {
			return e
		}
		var runtime, taskID string
		if e = tx.QueryRow(`SELECT runtime,task FROM runtime_qualification_plans WHERE project=? AND runtime=?`, project, run["runtime_id"]).Scan(&runtime, &taskID); e != nil {
			return Fail(403, "FORBIDDEN", "host runtime grant lacks its prepared runtime plan")
		}
		reg, e := load(tx, project, "RuntimeRegistration", runtime)
		if e != nil {
			return e
		}
		var raw string
		if e = tx.QueryRow(`SELECT profile_ref FROM runtime_bindings WHERE project=? AND runtime=?`, project, runtime).Scan(&raw); e != nil {
			return e
		}
		ref, e := Decode([]byte(raw))
		if e != nil {
			return e
		}
		artifact, e := version(tx, project, ref)
		if e != nil {
			return e
		}
		profile, e := runtimeProfileBody(tx, project, artifact)
		setup, _ := profile["host_setup"].(map[string]any)
		owner := Str(setup, "principal")
		expected := "local-executor-" + strings.TrimPrefix(Hash([]any{owner, project, "EXECUTOR"}), "sha256:")[:32]
		root, rootErr := authorityRoot(tx, owner)
		actualRoot, lineageErr := authorityRoot(tx, p.ID)
		if e != nil || owner == "" || expected != p.ID || rootErr != nil || lineageErr != nil || root != actualRoot || profile["technical_hash"] != runtimeTechnicalHash(reg) {
			return Fail(403, "FORBIDDEN", "host runtime grant is not from this prepared Owner lineage")
		}
		if task["task_type"] == "runtime_qualification" {
			var count int
			if taskID != grant.TaskID || tx.QueryRow(`SELECT count(*) FROM runtime_qualification_runs WHERE project=? AND task=? AND run=? AND runtime=? AND epoch=?`, project, grant.TaskID, grant.RunID, runtime, run["lease_epoch"]).Scan(&count) != nil || count != 1 {
				return Fail(403, "FORBIDDEN", "qualification grant differs from its original claim")
			}
		} else if task["task_type"] == "mu_turn" {
			dispatch, e := runtimeDispatch(tx, project, grant.RunID, run["lease_epoch"])
			manifest, _ := dispatch["manifest"].(map[string]any)
			admission, _ := manifest["admission"].(map[string]any)
			permission, _ := admission["permission"].(map[string]any)
			if e != nil || manifest["task_id"] != grant.TaskID || manifest["executor_principal_id"] != p.ID || manifest["runtime_id"] != runtime || admission["profile_hash"] != Hash(ref) || permission["purpose"] != "mu_turn" || permission["authorized_by"] != owner {
				return Fail(403, "FORBIDDEN", "normal turn grant lacks its original qualified dispatch binding")
			}
		} else {
			return Fail(403, "FORBIDDEN", "host runtime grant has an unsupported task purpose")
		}
	}
	if base != 1 {
		return Fail(403, "FORBIDDEN", "host runtime principal requires its exact base project grant")
	}
	return nil
}
