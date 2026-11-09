//go:build windows

package domain

import (
	"context"
	"database/sql"
	"fmt"

	"researchos.local/research-os/evaluation/evolution"
	"researchos.local/research-os/ops/supervisor"
)

type evolutionRegressionOutcome struct {
	BaselineResult  evolution.Result
	CandidateResult evolution.Result
	Improved        bool
}

func (s *Service) evolutionHostContract(tx *sql.Tx, project string, h, c Object, phase string) error {
	ids, err := s.evolutionHostCaseIDs(tx, project, h)
	if err != nil {
		return err
	}
	if controlHost(h) && phase != "REGRESSION" {
		return Fail(503, "RESOURCE_UNAVAILABLE", "control profile has no qualified canary adapter")
	}
	return evolutionCheckContractFor(c, phase, ids, evolutionHostExpected(h, phase))
}

func (s *Service) evaluateEvolutionRegression(ctx context.Context, project string, x, h Object, stable, candidate []byte, record Object) (evolutionRegressionOutcome, error) {
	if !controlHost(h) {
		pair, err := supervisor.Evaluate(ctx, stable, candidate)
		record["pair"] = pair
		return evolutionRegressionOutcome{BaselineResult: pair.BaselineResult, CandidateResult: pair.CandidateResult, Improved: pair.Improved}, err
	}
	tx, err := s.DB.BeginTx(ctx, nil)
	if err != nil {
		return evolutionRegressionOutcome{}, err
	}
	defer tx.Rollback()
	origin, err := s.controlCurrentGate(tx, h, x)
	if err != nil {
		return evolutionRegressionOutcome{}, err
	}
	if origin != nil {
		record["current_control_origin"] = origin
	}
	bundle, suite, err := s.controlHostInputs(tx, project, h)
	if err != nil {
		return evolutionRegressionOutcome{}, err
	}
	stableSource, candidateSource, err := s.controlBuildSources(tx, project, x, h)
	if err != nil {
		return evolutionRegressionOutcome{}, err
	}
	if err = tx.Rollback(); err != nil {
		return evolutionRegressionOutcome{}, err
	}
	proof, err := supervisor.EvaluateControl(ctx, stable, candidate, stableSource, candidateSource, bundle, suite.Inputs, Digest(evolution.Bytes(suite.Labels)), Hash(evolutionPlan(x)), evolutionSuiteHash(h))
	if err != nil {
		return evolutionRegressionOutcome{}, err
	}
	record["control_proof"], record["evaluation_profile"] = proof, evolution.ControlProfile
	v, err := supervisor.CheckControl(proof, suite.Inputs, suite.Labels, Hash(evolutionPlan(x)), Digest(stable), Digest(candidate), stableSource, candidateSource, evolutionSuiteHash(h))
	if err != nil {
		return evolutionRegressionOutcome{}, err
	}
	return evolutionRegressionOutcome{BaselineResult: evolution.Result{Values: v.BaselineValues, RequiredPassed: v.BaselineCorrect == v.Total, Correct: v.BaselineCorrect}, CandidateResult: evolution.Result{Values: v.CandidateValues, RequiredPassed: v.RequiredPassed, Correct: v.CandidateCorrect}, Improved: v.Gain}, nil
}

func (s *Service) controlRecordValid(tx *sql.Tx, project string, x, h, r Object) error {
	origin, currentErr := s.controlCurrentGate(tx, h, x)
	if currentErr != nil {
		return currentErr
	}
	if origin != nil {
		stored, ok := r["current_control_origin"].(map[string]any)
		if !ok || !controlSameExcept(origin, stored, "delta_hash") {
			return fmt.Errorf("CONTROL_CURRENT_RECORD_ORIGIN")
		}
	}
	if r["phase"] != "REGRESSION" || r["evaluation_profile"] != evolution.ControlProfile || r["pair"] != nil {
		return Fail(422, "GATE_FAILED", "control execution cannot use calculator proof")
	}
	_, suite, err := s.controlHostInputs(tx, project, h)
	if err != nil {
		return err
	}
	stableSource, candidateSource, err := s.controlBuildSources(tx, project, x, h)
	if err != nil {
		return err
	}
	var proof supervisor.ControlProof
	if err = evolution.StrictControlJSON(Bytes(r["control_proof"]), &proof); err != nil {
		return err
	}
	v, err := supervisor.CheckControl(proof, suite.Inputs, suite.Labels, Hash(evolutionPlan(x)), Str(r, "baseline_hash"), Str(r, "candidate_hash"), stableSource, candidateSource, evolutionSuiteHash(h))
	if err != nil {
		return err
	}
	holdout, proofHash, err := s.evolutionHoldoutVerdict(context.Background(), tx, project, x)
	if err != nil {
		return err
	}
	if holdout == nil || Hash(r["holdout_summary"]) != Hash(holdout) || r["holdout_proof_hash"] != proofHash || r["improved"] != (v.Gain && holdout["gain"] == true) || r["required_passed"] != v.RequiredPassed {
		return fmt.Errorf("CONTROL_DERIVED_VERDICT")
	}
	observation, ok := r["observation"].(map[string]any)
	if !ok {
		return fmt.Errorf("CONTROL_OBSERVATION")
	}
	rows := Arr(observation, "observations")
	if len(rows) != 1 {
		return fmt.Errorf("CONTROL_CORRECTNESS_METRIC")
	}
	row, ok := rows[0].(map[string]any)
	if !ok {
		return fmt.Errorf("CONTROL_CORRECTNESS_ROW")
	}
	ids, err := s.evolutionHostCaseIDs(tx, project, h)
	if err != nil {
		return err
	}
	if Hash(row["case_ids"]) != Hash(ids) || Hash(row["baseline"]) != Hash(v.BaselineValues) || Hash(row["candidate"]) != Hash(v.CandidateValues) {
		return fmt.Errorf("CONTROL_RAW_OBSERVATION_BINDING")
	}
	return nil
}
