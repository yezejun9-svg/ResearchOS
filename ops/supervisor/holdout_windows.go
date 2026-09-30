//go:build windows

package supervisor

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"researchos.local/research-os/evaluation/evolution"
	"researchos.local/research-os/internal/canonical"
	sandbox "researchos.local/research-os/ops/experiment_sandbox"
	"time"
)

type HoldoutInvocation struct {
	Request   evolution.Request `json:"request"`
	BuildHash string            `json:"build_hash"`
	InputHash string            `json:"input_hash"`
	RawHash   string            `json:"raw_hash"`
	Raw       string            `json:"raw"`
	Receipt   sandbox.Receipt   `json:"receipt"`
}

type HoldoutPair struct {
	Baseline  HoldoutInvocation `json:"baseline"`
	Candidate HoldoutInvocation `json:"candidate"`
}

// Full proof is VERIFIER_ONLY. The ordinary regression observation receives
// only a fixed aggregate, never these cases, labels, raw rows, or blob refs.
type HoldoutProof struct {
	Revision      string        `json:"revision"`
	ModelRevision string        `json:"model_revision"`
	PlanHash      string        `json:"plan_hash"`
	InputsHash    string        `json:"inputs_hash"`
	LabelsHash    string        `json:"labels_hash"`
	StableHash    string        `json:"stable_hash"`
	CandidateHash string        `json:"candidate_hash"`
	PublicSuite   string        `json:"public_suite_hash"`
	PolicyHash    string        `json:"policy_hash"`
	Pairs         []HoldoutPair `json:"pairs"`
}

type BenefitRow struct {
	ID               string `json:"id"`
	Expected         int    `json:"expected"`
	BaselineOutcome  int    `json:"baseline_outcome"`
	CandidateOutcome int    `json:"candidate_outcome"`
	BaselineScore    int    `json:"baseline_score"`
	CandidateScore   int    `json:"candidate_score"`
	BaselineRubric   string `json:"baseline_rubric"`
	CandidateRubric  string `json:"candidate_rubric"`
	InputHash        string `json:"input_hash"`
}

type HoldoutVerdict struct {
	Revision         string       `json:"revision"`
	Total            int          `json:"total"`
	BaselineCorrect  int          `json:"baseline_correct"`
	CandidateCorrect int          `json:"candidate_correct"`
	OutcomesEqual    bool         `json:"outcomes_equal"`
	Gain             bool         `json:"gain"`
	Rows             []BenefitRow `json:"rows"`
}

func invokeHoldout(ctx context.Context, binary []byte, c evolution.Case) (HoldoutInvocation, error) {
	v := HoldoutInvocation{BuildHash: evolution.Digest(binary)}
	work, err := os.MkdirTemp("", "researchos-c20-single-")
	if err != nil {
		return v, err
	}
	defer os.RemoveAll(work)
	input, output := filepath.Join(work, "input"), filepath.Join(work, "output")
	for _, path := range []string{input, output} {
		if err = os.Mkdir(path, 0700); err != nil {
			return v, err
		}
	}
	v.Request = evolution.Request{Phase: "REGRESSION", Cases: []evolution.Case{c}}
	request := evolution.Bytes(v.Request)
	v.InputHash = evolution.Digest(request)
	executable, requestPath := filepath.Join(input, "candidate.exe"), filepath.Join(input, "current-question.json")
	if err = os.WriteFile(executable, binary, 0600); err != nil {
		return v, err
	}
	if err = os.WriteFile(requestPath, request, 0600); err != nil {
		return v, err
	}
	v.Receipt, err = sandbox.Run(ctx, sandbox.Command{Executable: executable, Args: []string{requestPath}, InputDirectory: input, OutputDirectory: output, Timeout: 1500 * time.Millisecond})
	v.Raw, v.RawHash = string(v.Receipt.Stdout), evolution.Digest(v.Receipt.Stdout)
	if err != nil {
		return v, err
	}
	if _, err = checkHoldoutInvocation(v, c, v.BuildHash); err != nil {
		return v, err
	}
	return v, nil
}

// EvaluateHoldout executes both sealed builds for each private question. Each
// invocation creates a new zero-capability AppContainer and sees one case only.
func EvaluateHoldout(ctx context.Context, stable, candidate []byte, inputs evolution.HoldoutInputs, labelsHash, planHash string) (HoldoutProof, error) {
	proof := HoldoutProof{Revision: inputs.Revision, ModelRevision: "NONE", PlanHash: planHash,
		InputsHash: evolution.Digest(evolution.Bytes(inputs)), LabelsHash: labelsHash,
		StableHash: evolution.Digest(stable), CandidateHash: evolution.Digest(candidate),
		PublicSuite: evolution.Digest(evolution.Bytes(evolution.Suite())), PolicyHash: evolution.Digest(evolution.Bytes(evolution.Policy()))}
	for _, c := range inputs.Cases {
		baseline, err := invokeHoldout(ctx, stable, c)
		if err != nil {
			return proof, err
		}
		trial, err := invokeHoldout(ctx, candidate, c)
		if err != nil {
			return proof, err
		}
		proof.Pairs = append(proof.Pairs, HoldoutPair{Baseline: baseline, Candidate: trial})
	}
	return proof, nil
}

func checkHoldoutInvocation(v HoldoutInvocation, c evolution.Case, buildHash string) (evolution.Response, error) {
	if v.BuildHash != buildHash || v.Request.Phase != "REGRESSION" || len(v.Request.Cases) != 1 || v.Request.Cases[0] != c || len(v.Request.ProtectedPaths) != 0 || v.InputHash != evolution.Digest(evolution.Bytes(v.Request)) || v.RawHash != evolution.Digest([]byte(v.Raw)) || !bytes.Equal(v.Receipt.Stdout, []byte(v.Raw)) {
		return evolution.Response{}, fmt.Errorf("private single-question input/build/raw binding changed")
	}
	if v.Receipt.ExitCode != 0 || !v.Receipt.Stopped || v.Receipt.TimedOut || len(v.Receipt.Capabilities) != 0 || v.Receipt.PID == 0 || v.Receipt.SID == "" {
		return evolution.Response{}, fmt.Errorf("private AppContainer execution invalid")
	}
	canonicalRaw, err := canonical.JSON([]byte(v.Raw))
	if err != nil {
		return evolution.Response{}, err
	}
	var rows []evolution.Response
	decoder := json.NewDecoder(bytes.NewReader(canonicalRaw))
	decoder.DisallowUnknownFields()
	if err = decoder.Decode(&rows); err != nil || len(rows) != 1 || rows[0].ID != c.ID || rows[0].Rubric == "" {
		return evolution.Response{}, fmt.Errorf("private single-question output invalid: %v", err)
	}
	return rows[0], nil
}

// CheckHoldout recomputes the objective outcome from private raw processes;
// model self-scores are retained as evidence but never count as improvement.
func CheckHoldout(proof HoldoutProof, inputs evolution.HoldoutInputs, labels evolution.HoldoutLabels, planHash, stableHash, candidateHash string) (HoldoutVerdict, error) {
	v := HoldoutVerdict{Revision: inputs.Revision, OutcomesEqual: true}
	if err := evolution.ValidateHoldout(inputs, labels); err != nil {
		return v, err
	}
	if proof.Revision != inputs.Revision || proof.ModelRevision != "NONE" || proof.PlanHash != planHash || proof.InputsHash != evolution.Digest(evolution.Bytes(inputs)) || proof.LabelsHash != evolution.Digest(evolution.Bytes(labels)) || proof.StableHash != stableHash || proof.CandidateHash != candidateHash || proof.PublicSuite != evolution.Digest(evolution.Bytes(evolution.Suite())) || proof.PolicyHash != evolution.Digest(evolution.Bytes(evolution.Policy())) || len(proof.Pairs) != len(inputs.Cases) {
		return v, fmt.Errorf("private proof version, frozen inputs, or build binding changed")
	}
	seenSID := map[string]bool{}
	for i, c := range inputs.Cases {
		pair := proof.Pairs[i]
		baseline, err := checkHoldoutInvocation(pair.Baseline, c, stableHash)
		if err != nil {
			return v, err
		}
		candidate, err := checkHoldoutInvocation(pair.Candidate, c, candidateHash)
		if err != nil {
			return v, err
		}
		for _, sid := range []string{pair.Baseline.Receipt.SID, pair.Candidate.Receipt.SID} {
			if seenSID[sid] {
				return v, fmt.Errorf("private questions reused an AppContainer")
			}
			seenSID[sid] = true
		}
		want := labels.Labels[i].Expected
		if baseline.Value == want {
			v.BaselineCorrect++
		}
		if candidate.Value == want {
			v.CandidateCorrect++
		}
		v.OutcomesEqual = v.OutcomesEqual && baseline.Value == candidate.Value
		v.Rows = append(v.Rows, BenefitRow{ID: c.ID, Expected: want, BaselineOutcome: baseline.Value, CandidateOutcome: candidate.Value,
			BaselineScore: baseline.SelfScore, CandidateScore: candidate.SelfScore, BaselineRubric: baseline.Rubric,
			CandidateRubric: candidate.Rubric, InputHash: pair.Baseline.InputHash})
	}
	v.Total = len(inputs.Cases)
	v.Gain = objectiveHoldoutGain(v.Rows)
	return v, nil
}

// Improvement requires a newly correct objective answer without losing any
// answer the stable build already got right. Self-scores never enter this gate.
func objectiveHoldoutGain(rows []BenefitRow) bool {
	newCorrect := false
	for _, row := range rows {
		baselineCorrect := row.BaselineOutcome == row.Expected
		candidateCorrect := row.CandidateOutcome == row.Expected
		if baselineCorrect && !candidateCorrect {
			return false
		}
		if !baselineCorrect && candidateCorrect {
			newCorrect = true
		}
	}
	return newCorrect
}
