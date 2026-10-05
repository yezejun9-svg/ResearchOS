//go:build windows

package main

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"time"

	"researchos.local/research-os/internal/domain"
)

// qualify consumes one approved plan. A begun run is never launched twice.
func (s *setup) qualify(ctx context.Context) error {
	if !s.state.PlanReady || s.state.ProjectID == "" || s.state.WorkspaceRef == "" || !s.credentialFresh() {
		return errors.New("LIVE plan, exact workspace and credential must be prepared before qualification")
	}
	if s.state.Qualified {
		return s.authorizeCodingPurpose(ctx)
	}
	api, err := s.startAPI(ctx, nil)
	if err != nil {
		return err
	}
	defer api.close()
	if s.state.RunID == "" {
		var prior string
		err = s.db.QueryRowContext(ctx, "SELECT id FROM domain_objects WHERE project=? AND kind='Run' AND json_extract(body,'$.task_id')=? LIMIT 1", s.state.ProjectID, s.state.TaskID).Scan(&prior)
		if err == nil {
			s.state.RunID = prior
			if err = s.saveState(); err != nil {
				return err
			}
		} else if !errors.Is(err, sql.ErrNoRows) {
			return err
		}
	}
	if s.state.RunID == "" {
		if err = s.dispatchQualification(ctx, api); err != nil {
			return err
		}
	}
	settled, err := api.get(ctx, s.ownerToken, api.path("/runs/"+s.state.RunID))
	if err != nil {
		return err
	}
	if settled["status"] != "SETTLED" || len(domain.Arr(settled, "result_artifact_ids")) == 0 {
		return fmt.Errorf("LIVE qualification run is %v, independent acceptance cannot proceed", settled["status"])
	}
	task, err := api.get(ctx, s.ownerToken, api.path("/tasks/"+s.state.TaskID))
	if err != nil {
		return err
	}
	artifactID, ok := domain.Arr(settled, "result_artifact_ids")[0].(string)
	if !ok || artifactID == "" {
		return errors.New("settled run has no result artifact ID")
	}
	result, err := api.get(ctx, s.ownerToken, api.path("/artifacts/"+artifactID))
	if err != nil {
		return err
	}
	verifierToken, err := s.svc.IssueCredential(ctx, s.state.VerifierID, 15*time.Minute)
	if err != nil {
		return err
	}
	if s.state.AcceptanceID == "" {
		project, err := api.projectState(ctx, s.ownerToken)
		if err != nil {
			return err
		}
		contract, ok := task["acceptance_contract"].(map[string]any)
		if !ok {
			return errors.New("qualification task has no frozen acceptance contract")
		}
		checks := domain.Empty()
		for _, item := range domain.Arr(contract, "checks") {
			check, ok := item.(map[string]any)
			if !ok {
				return errors.New("invalid frozen acceptance check")
			}
			checks = append(checks, domain.Object{"check_id": check["check_id"], "status": "NOT_RUN", "evidence_refs": domain.Empty(), "command_key": check["command_key"], "actual": "request independent service computation", "exit_code": nil, "started_at": nil, "finished_at": nil})
		}
		body := domain.Object{"subject_ref": domain.Ref(task, "Task"), "run_id": s.state.RunID, "contract_hash": contract["contract_hash"], "input_refs": task["input_refs"], "artifact_refs": []any{domain.Ref(result, "Artifact")}, "checks": checks, "verdict": "PASS", "executor_principal_ids": []any{s.state.ExecutorID}, "independence_basis": "DETERMINISTIC_SERVICE", "blocking_conflict_ids": domain.Empty(), "qualification_ids": domain.Empty(), "policy_revision": project["policy_revision"], "measurement_mode": "LIVE", "reason": "independent frozen Mu turn verification"}
		receipt, err := api.postWithSubject(ctx, verifierToken, api.path("/acceptances"), task, body, 201)
		if err != nil {
			return err
		}
		s.state.AcceptanceID = domain.Str(receipt, "id")
		if err = s.saveState(); err != nil {
			return err
		}
		if receipt["verdict"] != "PASS" {
			return errors.New("independent LIVE acceptance did not pass")
		}
	} else {
		receipt, err := api.get(ctx, verifierToken, api.path("/acceptances/"+s.state.AcceptanceID))
		if err != nil {
			return err
		}
		if receipt["verdict"] != "PASS" {
			return errors.New("existing LIVE acceptance did not pass")
		}
	}
	var logRaw string
	err = s.db.QueryRowContext(ctx, "SELECT body FROM domain_objects WHERE project=? AND kind='Artifact' AND json_extract(body,'$.run_id')=? AND json_extract(body,'$.kind')='LOG'", s.state.ProjectID, s.state.RunID).Scan(&logRaw)
	if err != nil {
		return fmt.Errorf("runtime LOG artifact unavailable: %w", err)
	}
	var logArtifact domain.Object
	if err = json.Unmarshal([]byte(logRaw), &logArtifact); err != nil {
		return err
	}
	registration, err := api.get(ctx, verifierToken, api.path("/runtimes/"+s.state.RuntimeID))
	if err != nil {
		return err
	}
	qualified := registration
	if registration["status"] == "AVAILABLE" {
		ids := domain.Arr(registration, "qualification_ids")
		if len(ids) != 1 || ids[0] != s.state.AcceptanceID {
			return errors.New("available runtime has a different qualification receipt")
		}
	} else {
		qualified, err = api.postWithSubject(ctx, verifierToken, api.path("/runtimes/"+s.state.RuntimeID+"/qualify"), registration, domain.Object{"qualification_ids": []any{s.state.AcceptanceID}, "supports_resume": false, "resume_evidence_ref": nil, "receipt_artifact_ref": domain.Ref(logArtifact, "Artifact")}, 200)
		if err != nil {
			return err
		}
	}
	if qualified["status"] != "AVAILABLE" {
		return errors.New("runtime remained unavailable after qualification")
	}
	if err := s.authorizeCodingPurpose(ctx); err != nil {
		return err
	}
	s.state.Qualified = true
	return s.saveState()
}

// Purpose grants are separate from runtime qualification and bind only the
// ordinary mu_turn task type. Refreshing them never redispatches a Run.
func (s *setup) authorizeCodingPurpose(ctx context.Context) error {
	if err := s.refreshCoordinatorConfig(ctx); err != nil {
		return err
	}
	var receiptRaw, planRaw string
	if err := s.db.QueryRowContext(ctx, "SELECT body FROM domain_objects WHERE project=? AND kind='AcceptanceReceipt' AND id=?", s.state.ProjectID, s.state.AcceptanceID).Scan(&receiptRaw); err != nil {
		return err
	}
	if err := s.db.QueryRowContext(ctx, "SELECT plan FROM runtime_qualification_plans WHERE project=? AND task=? AND runtime=?", s.state.ProjectID, s.state.TaskID, s.state.RuntimeID).Scan(&planRaw); err != nil {
		return err
	}
	var receipt, plan domain.Object
	if err := json.Unmarshal([]byte(receiptRaw), &receipt); err != nil {
		return err
	}
	if err := json.Unmarshal([]byte(planRaw), &plan); err != nil {
		return err
	}
	created, err := time.Parse(time.RFC3339Nano, domain.Str(receipt, "created_at"))
	if err != nil {
		return err
	}
	valid, err := domain.Num(plan, "max_validity_seconds")
	if err != nil || valid <= 0 {
		return errors.New("invalid frozen qualification lifetime")
	}
	expires := created.Add(time.Duration(valid) * time.Second).Add(-time.Second)
	if oneHour := time.Now().Add(time.Hour); oneHour.Before(expires) {
		expires = oneHour
	}
	if !expires.After(time.Now()) {
		return errors.New("qualification expired before coding purpose authorization")
	}
	return s.svc.AuthorizeRuntimePurpose(ctx, s.ownerToken, s.state.ProjectID, s.state.RuntimeID, "mu_turn", expires)
}

func (s *setup) dispatchQualification(ctx context.Context, api *localAPI) error {
	if err := s.refreshCoordinatorConfig(ctx); err != nil {
		return err
	}
	configRaw, err := os.ReadFile(filepath.Join(s.dataRoot, "host", "live_coordinator.json"))
	if err != nil {
		return err
	}
	var config domain.RuntimeCoordinatorConfig
	if err = json.Unmarshal(configRaw, &config); err != nil {
		return err
	}
	authority, schema, _, err := s.authority()
	if err != nil {
		return err
	}
	config.APIURL, config.WorkspaceAuthority, config.ClientSchema = api.url, authority, schema
	config.ModelCredential, config.RunTool = s.host.ModelCredential, s.host.ExecuteRuntimeTool
	coordinator, err := s.svc.NewRuntimeCoordinatorWithLease(ctx, config, s.lease)
	if err != nil {
		return err
	}
	defer coordinator.Close()
	run, lease, err := s.svc.BeginRuntimeQualification(ctx, s.ownerToken, s.state.ProjectID, s.state.TaskID, s.state.RuntimeID, s.state.ExecutorID)
	if err != nil {
		return err
	}
	s.state.RunID = domain.Str(run, "id")
	if s.state.RunID == "" {
		return errors.New("qualification began without a run ID")
	}
	if err = s.saveState(); err != nil {
		return err
	}
	if len(config.Routes) != 1 {
		return errors.New("LIVE coordinator route is not unique")
	}
	if err = coordinator.RunAdmitted(ctx, config.Routes[0], run, lease); err != nil {
		return fmt.Errorf("LIVE qualification dispatch failed without retry: %w", err)
	}
	return nil
}
