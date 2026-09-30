//go:build windows

package domain

import (
	"context"
	"database/sql"
	"fmt"

	"researchos.local/research-os/evaluation/evolution"
	"researchos.local/research-os/ops/supervisor"
)

func (s *Service) controlHoldoutInputs(tx *sql.Tx, project string, x, h Object, inputsRaw, labelsRaw []byte) (evolution.ControlBundle, evolution.ControlInputs, evolution.ControlLabels, error) {
	var inputs evolution.ControlInputs
	var labels evolution.ControlLabels
	bundle, _, err := s.controlHostInputs(tx, project, h)
	if err != nil {
		return bundle, inputs, labels, err
	}
	if err = evolution.StrictControlJSON(inputsRaw, &inputs); err != nil {
		return bundle, inputs, labels, err
	}
	if err = evolution.StrictControlJSON(labelsRaw, &labels); err != nil {
		return bundle, inputs, labels, err
	}
	if err = evolution.ValidateControlDataset(inputs, labels); err != nil {
		return bundle, inputs, labels, err
	}
	if inputs.Revision != evolution.ControlPrivateRevision || inputs.Binding != bundle.Binding || Digest(inputsRaw) != Digest(evolution.Bytes(inputs)) || Digest(labelsRaw) != Digest(evolution.Bytes(labels)) {
		return bundle, inputs, labels, fmt.Errorf("CONTROL_PRIVATE_INPUT_BINDING")
	}
	return bundle, inputs, labels, nil
}

func controlHoldoutSummary(v supervisor.ControlVerdict) Object {
	return Object{"revision": v.Revision, "profile": evolution.ControlProfile, "measurement_mode": "FIXTURE", "model_revision": "NONE", "total": v.Total, "baseline_correct": v.BaselineCorrect, "candidate_correct": v.CandidateCorrect, "outcomes_equal": v.OutcomesEqual, "gain": v.Gain}
}

func (s *Service) controlHoldoutFrozen(tx *sql.Tx, project string, x, h Object, inputsRaw, labelsRaw []byte) (Object, error) {
	bundle, _, _, err := s.controlHoldoutInputs(tx, project, x, h, inputsRaw, labelsRaw)
	if err != nil {
		return nil, err
	}
	stableSource, candidateSource, err := s.controlBuildSources(tx, project, x, h)
	if err != nil {
		return nil, err
	}
	return Object{"revision": evolution.ControlPrivateRevision, "evaluation_profile": evolution.ControlProfile, "protocol": evolution.ControlProtocol, "control_binding": bundle.Binding, "stable_source_hash": stableSource, "candidate_source_hash": candidateSource, "public_suite_hash": evolutionSuiteHash(h), "policy_hash": evolutionPolicyHash(h)}, nil
}

func (s *Service) evaluateControlHoldout(ctx context.Context, project string, x Object, inputsRaw, labelsRaw, stable, trial []byte) ([]byte, Object, error) {
	tx, err := s.DB.BeginTx(ctx, nil)
	if err != nil {
		return nil, nil, err
	}
	defer tx.Rollback()
	h, err := s.evolutionCurrent(tx, project, x)
	if err != nil {
		return nil, nil, err
	}
	bundle, inputs, labels, err := s.controlHoldoutInputs(tx, project, x, h, inputsRaw, labelsRaw)
	if err != nil {
		return nil, nil, err
	}
	stableSource, candidateSource, err := s.controlBuildSources(tx, project, x, h)
	if err != nil {
		return nil, nil, err
	}
	if err = tx.Rollback(); err != nil {
		return nil, nil, err
	}
	proof, err := supervisor.EvaluateControl(ctx, stable, trial, stableSource, candidateSource, bundle, inputs, Digest(labelsRaw), Hash(evolutionPlan(x)), evolutionSuiteHash(h))
	if err != nil {
		return nil, nil, err
	}
	verdict, err := supervisor.CheckControl(proof, inputs, labels, Hash(evolutionPlan(x)), Digest(stable), Digest(trial), stableSource, candidateSource, evolutionSuiteHash(h))
	if err != nil {
		return nil, nil, err
	}
	return Bytes(proof), controlHoldoutSummary(verdict), nil
}

func (s *Service) controlHoldoutVerdict(ctx context.Context, tx *sql.Tx, project string, x, h, frozen, evaluated Object) (Object, string, error) {
	if frozen["revision"] != evolution.ControlPrivateRevision || frozen["evaluation_profile"] != evolution.ControlProfile || frozen["protocol"] != evolution.ControlProtocol || frozen["model_revision"] != "NONE" || frozen["plan_hash"] != Hash(evolutionPlan(x)) || frozen["stable_hash"] != x["stable_artifact_ref"].(map[string]any)["content_hash"] || frozen["candidate_hash"] != x["candidate_artifact_ref"].(map[string]any)["content_hash"] || frozen["public_suite_hash"] != evolutionSuiteHash(h) || frozen["policy_hash"] != evolutionPolicyHash(h) || Hash(frozen["control_binding"]) != Hash(h["control_binding"]) || evaluated["plan_hash"] != frozen["plan_hash"] || evaluated["verifier_id"] != frozen["verifier_id"] {
		return nil, "", Fail(422, "GATE_FAILED", "control holdout frozen binding changed")
	}
	if err := s.evolutionHoldoutVerifierCurrent(tx, project, x, Str(frozen, "verifier_id")); err != nil {
		return nil, "", err
	}
	_, inputsRaw, err := s.evolutionPrivateBytes(ctx, tx, project, frozen["input_ref"].(map[string]any))
	if err != nil {
		return nil, "", err
	}
	_, labelsRaw, err := s.evolutionPrivateBytes(ctx, tx, project, frozen["labels_ref"].(map[string]any))
	if err != nil {
		return nil, "", err
	}
	_, proofRaw, err := s.evolutionPrivateBytes(ctx, tx, project, evaluated["proof_ref"].(map[string]any))
	if err != nil {
		return nil, "", err
	}
	if frozen["inputs_hash"] != Digest(inputsRaw) || frozen["labels_hash"] != Digest(labelsRaw) || evaluated["proof_hash"] != Digest(proofRaw) {
		return nil, "", fmt.Errorf("CONTROL_PRIVATE_BYTES_CHANGED")
	}
	_, inputs, labels, err := s.controlHoldoutInputs(tx, project, x, h, inputsRaw, labelsRaw)
	if err != nil {
		return nil, "", err
	}
	stableSource, candidateSource, err := s.controlBuildSources(tx, project, x, h)
	if err != nil {
		return nil, "", err
	}
	if frozen["stable_source_hash"] != stableSource || frozen["candidate_source_hash"] != candidateSource {
		return nil, "", fmt.Errorf("CONTROL_SOURCE_BINDING_CHANGED")
	}
	var proof supervisor.ControlProof
	if err = evolution.StrictControlJSON(proofRaw, &proof); err != nil {
		return nil, "", err
	}
	v, err := supervisor.CheckControl(proof, inputs, labels, Hash(evolutionPlan(x)), Str(x["stable_artifact_ref"].(map[string]any), "content_hash"), Str(x["candidate_artifact_ref"].(map[string]any), "content_hash"), stableSource, candidateSource, evolutionSuiteHash(h))
	if err != nil {
		return nil, "", err
	}
	summary := controlHoldoutSummary(v)
	if evaluated["summary_hash"] != Hash(summary) {
		return nil, "", fmt.Errorf("CONTROL_SUMMARY_CHANGED")
	}
	return summary, Digest(proofRaw), nil
}
