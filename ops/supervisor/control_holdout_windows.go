//go:build windows

package supervisor

import (
	"bytes"
	"context"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	"golang.org/x/sys/windows"
	"researchos.local/research-os/evaluation/evolution"
	"researchos.local/research-os/internal/store"
	sandbox "researchos.local/research-os/ops/experiment_sandbox"
)

type ControlInvocation struct {
	Request            evolution.ControlRequest `json:"request"`
	InputHash          string                   `json:"input_hash"`
	BuildHash          string                   `json:"build_hash"`
	SourceHash         string                   `json:"source_hash"`
	ImagePath          string                   `json:"image_path"`
	Identity           sandbox.Identity         `json:"suspended_identity"`
	Raw                string                   `json:"raw"`
	RawHash            string                   `json:"raw_hash"`
	OutputDatabaseHash string                   `json:"output_database_hash"`
	OutputStateHash    string                   `json:"output_state_hash"`
	Receipt            sandbox.Receipt          `json:"receipt"`
}
type ControlPair struct {
	Baseline  ControlInvocation `json:"baseline"`
	Candidate ControlInvocation `json:"candidate"`
}
type ControlProof struct {
	Profile             string                   `json:"profile"`
	Revision            string                   `json:"revision"`
	Binding             evolution.ControlBinding `json:"binding"`
	PlanHash            string                   `json:"plan_hash"`
	InputsHash          string                   `json:"inputs_hash"`
	LabelsHash          string                   `json:"labels_hash"`
	PublicSuiteHash     string                   `json:"public_suite_hash"`
	PolicyHash          string                   `json:"policy_hash"`
	StableHash          string                   `json:"stable_hash"`
	CandidateHash       string                   `json:"candidate_hash"`
	StableSourceHash    string                   `json:"stable_source_hash"`
	CandidateSourceHash string                   `json:"candidate_source_hash"`
	Pairs               []ControlPair            `json:"pairs"`
}
type ControlVerdict struct {
	Revision         string   `json:"revision"`
	Total            int      `json:"total"`
	BaselineCorrect  int      `json:"baseline_correct"`
	CandidateCorrect int      `json:"candidate_correct"`
	BaselineValues   []string `json:"baseline_values"`
	CandidateValues  []string `json:"candidate_values"`
	RequiredPassed   bool     `json:"required_passed"`
	OutcomesEqual    bool     `json:"outcomes_equal"`
	Gain             bool     `json:"gain"`
}

func invokeControl(ctx context.Context, binary []byte, sourceHash string, bundle evolution.ControlBundle, c evolution.ControlCase) (ControlInvocation, error) {
	v := ControlInvocation{Request: evolution.ControlRequest{Binding: bundle.Binding, Case: c}, BuildHash: evolution.Digest(binary), SourceHash: sourceHash}
	if err := bundle.Validate(); err != nil {
		return v, err
	}
	if err := evolution.ValidateControlCase(c, bundle.Binding); err != nil {
		return v, err
	}
	work, err := os.MkdirTemp("", "researchos-control-replay-")
	if err != nil {
		return v, err
	}
	defer os.RemoveAll(work) // work is this invocation's newly created OS-temp child.
	input, output := filepath.Join(work, "input"), filepath.Join(work, "output")
	for _, dir := range []string{input, output} {
		if err = os.Mkdir(dir, 0700); err != nil {
			return v, err
		}
	}
	for name, raw := range bundle.Files {
		path := filepath.Join(input, filepath.FromSlash(name))
		if err = os.MkdirAll(filepath.Dir(path), 0700); err != nil {
			return v, err
		}
		if err = os.WriteFile(path, raw, 0600); err != nil {
			return v, err
		}
	}
	request := evolution.Bytes(v.Request)
	v.InputHash = evolution.Digest(request)
	executable, requestPath := filepath.Join(input, "control.exe"), filepath.Join(input, "current-case.json")
	if err = os.WriteFile(executable, binary, 0600); err != nil {
		return v, err
	}
	if err = os.WriteFile(requestPath, request, 0600); err != nil {
		return v, err
	}
	process, err := sandbox.Start(ctx, sandbox.Command{Executable: executable, Args: []string{"--fixture-control-replay", requestPath}, InputDirectory: input, OutputDirectory: output, Timeout: 10 * time.Second}, sandbox.StartOptions{BeforeResume: func(id sandbox.Identity) error {
		created, alive, err := processCreated(id.PID)
		if err != nil || !alive || created != id.Created {
			return fmt.Errorf("CONTROL_SUSPENDED_IDENTITY")
		}
		h, err := windows.OpenProcess(windows.PROCESS_QUERY_LIMITED_INFORMATION, false, id.PID)
		if err != nil {
			return err
		}
		defer windows.CloseHandle(h)
		buf := make([]uint16, 32768)
		size := uint32(len(buf))
		if err = windows.QueryFullProcessImageName(h, 0, &buf[0], &size); err != nil {
			return err
		}
		image := windows.UTF16ToString(buf[:size])
		expected := filepath.Join(id.StagingDirectory, "input", "control.exe")
		if !strings.EqualFold(filepath.Clean(image), filepath.Clean(expected)) {
			return fmt.Errorf("CONTROL_IMAGE_PATH")
		}
		actual, hash, err := exactImage(image)
		if err != nil || "sha256:"+hash != v.BuildHash {
			return fmt.Errorf("CONTROL_IMAGE_BYTES")
		}
		v.ImagePath, v.Identity = actual, id
		return nil
	}})
	if err != nil {
		return v, err
	}
	v.Receipt, err = process.Wait(context.Background())
	v.Raw, v.RawHash = string(v.Receipt.Stdout), evolution.Digest(v.Receipt.Stdout)
	if err != nil {
		return v, err
	}
	if v.Receipt.ExitCode != 0 || !v.Receipt.Stopped || v.Receipt.TimedOut {
		return v, fmt.Errorf("CONTROL_REPLAY_PROCESS exit=%d stopped=%v timeout=%v stderr=%s", v.Receipt.ExitCode, v.Receipt.Stopped, v.Receipt.TimedOut, v.Receipt.Stderr)
	}
	path := filepath.Join(output, "replay-data", "researchos.sqlite")
	info, err := os.Lstat(path)
	if err != nil || !info.Mode().IsRegular() || info.Size() > 32*1024*1024 {
		return v, fmt.Errorf("CONTROL_OUTPUT_DATABASE")
	}
	real, err := filepath.EvalSymlinks(path)
	if err != nil || !strings.EqualFold(real, path) {
		return v, fmt.Errorf("CONTROL_OUTPUT_REPARSE")
	}
	// The external host reads the copied DB after the candidate has stopped.
	db, err := store.Open(path)
	if err != nil {
		return v, err
	}
	v.OutputStateHash, err = evolution.ControlDatabaseHash(db)
	closeErr := db.Close()
	if err != nil {
		return v, err
	}
	if closeErr != nil {
		return v, closeErr
	}
	raw, err := os.ReadFile(path)
	if err != nil {
		return v, err
	}
	v.OutputDatabaseHash = evolution.Digest(raw)
	_, err = checkControlInvocation(v, c, bundle.Binding, v.BuildHash, sourceHash)
	return v, err
}

func EvaluateControl(ctx context.Context, stable, candidate []byte, stableSource, candidateSource string, bundle evolution.ControlBundle, inputs evolution.ControlInputs, labelsHash, planHash, publicSuiteHash string) (ControlProof, error) {
	p := ControlProof{Profile: evolution.ControlProfile, Revision: inputs.Revision, Binding: bundle.Binding, PlanHash: planHash, InputsHash: evolution.Digest(evolution.Bytes(inputs)), LabelsHash: labelsHash, PublicSuiteHash: publicSuiteHash, PolicyHash: evolution.Digest(evolution.Bytes(evolution.ControlPolicy(bundle.Binding, publicSuiteHash))), StableHash: evolution.Digest(stable), CandidateHash: evolution.Digest(candidate), StableSourceHash: stableSource, CandidateSourceHash: candidateSource, Pairs: []ControlPair{}}
	if inputs.Binding != bundle.Binding {
		return p, fmt.Errorf("CONTROL_INPUT_SNAPSHOT")
	}
	for _, c := range inputs.Cases {
		base, err := invokeControl(ctx, stable, stableSource, bundle, c)
		if err != nil {
			return p, err
		}
		trial, err := invokeControl(ctx, candidate, candidateSource, bundle, c)
		if err != nil {
			return p, err
		}
		p.Pairs = append(p.Pairs, ControlPair{Baseline: base, Candidate: trial})
	}
	return p, nil
}

func checkControlInvocation(v ControlInvocation, c evolution.ControlCase, binding evolution.ControlBinding, buildHash, sourceHash string) (evolution.ControlReplayResult, error) {
	var result evolution.ControlReplayResult
	if v.BuildHash != buildHash || v.SourceHash != sourceHash || v.Request.Binding != binding || !bytes.Equal(evolution.Bytes(v.Request.Case), evolution.Bytes(c)) || v.InputHash != evolution.Digest(evolution.Bytes(v.Request)) || v.RawHash != evolution.Digest([]byte(v.Raw)) || v.Raw != string(v.Receipt.Stdout) {
		return result, fmt.Errorf("CONTROL_INPUT_BUILD_RAW_BINDING")
	}
	r, id := v.Receipt, v.Identity
	if r.ExitCode != 0 || !r.Stopped || r.TimedOut || !r.StreamsDrained || !r.CleanupComplete || !r.OutputCopied || len(r.Capabilities) != 0 || r.PID == 0 || r.Created == 0 || r.SID == "" || id.PID != r.PID || id.Created != r.Created || id.Job != r.Job || id.SID != r.SID || id.Profile != r.Profile || !strings.EqualFold(v.ImagePath, r.Executable) || !strings.EqualFold(v.ImagePath, filepath.Join(id.StagingDirectory, "input", "control.exe")) || !strings.EqualFold(r.Directory, filepath.Join(id.StagingDirectory, "output")) || len(r.Args) != 2 || r.Args[0] != "--fixture-control-replay" || !strings.EqualFold(r.Args[1], filepath.Join(id.StagingDirectory, "input", "current-case.json")) {
		return result, fmt.Errorf("CONTROL_NATIVE_PROCESS_PROOF")
	}
	if len(v.OutputDatabaseHash) != 71 || len(v.OutputStateHash) != 71 {
		return result, fmt.Errorf("CONTROL_EXTERNAL_STATE_PROOF")
	}
	if err := evolution.StrictControlJSON([]byte(v.Raw), &result); err != nil {
		return result, err
	}
	if result.Binding != binding || result.CaseID != c.ID || len(result.Results) != len(c.Steps) {
		return result, fmt.Errorf("CONTROL_REPLAY_OUTPUT_BINDING")
	}
	return result, nil
}

func CheckControl(proof ControlProof, inputs evolution.ControlInputs, labels evolution.ControlLabels, planHash, stableHash, candidateHash, stableSource, candidateSource, publicSuiteHash string) (ControlVerdict, error) {
	v := ControlVerdict{Revision: inputs.Revision, OutcomesEqual: true, RequiredPassed: true, BaselineValues: []string{}, CandidateValues: []string{}}
	if err := evolution.ValidateControlDataset(inputs, labels); err != nil {
		return v, err
	}
	if proof.Profile != evolution.ControlProfile || proof.Revision != inputs.Revision || proof.Binding != inputs.Binding || proof.PlanHash != planHash || proof.InputsHash != evolution.Digest(evolution.Bytes(inputs)) || proof.LabelsHash != evolution.Digest(evolution.Bytes(labels)) || proof.StableHash != stableHash || proof.CandidateHash != candidateHash || proof.StableSourceHash != stableSource || proof.CandidateSourceHash != candidateSource || proof.PublicSuiteHash != publicSuiteHash || proof.PolicyHash != evolution.Digest(evolution.Bytes(evolution.ControlPolicy(inputs.Binding, publicSuiteHash))) || len(proof.Pairs) != len(inputs.Cases) {
		return v, fmt.Errorf("CONTROL_PROOF_FROZEN_BINDING")
	}
	seen := map[string]bool{}
	newCorrect, regressed := false, false
	for i, c := range inputs.Cases {
		pair, label := proof.Pairs[i], labels.Labels[i]
		base, err := checkControlInvocation(pair.Baseline, c, inputs.Binding, stableHash, stableSource)
		if err != nil {
			return v, err
		}
		trial, err := checkControlInvocation(pair.Candidate, c, inputs.Binding, candidateHash, candidateSource)
		if err != nil {
			return v, err
		}
		for _, sid := range []string{pair.Baseline.Receipt.SID, pair.Candidate.Receipt.SID} {
			if seen[sid] {
				return v, fmt.Errorf("CONTROL_REUSED_APPCONTAINER")
			}
			seen[sid] = true
		}
		bOK, cOK := pair.Baseline.OutputStateHash == inputs.Binding.ProjectionHash, pair.Candidate.OutputStateHash == inputs.Binding.ProjectionHash
		for j, want := range label.Results {
			w, err := evolution.ControlSemantic(want)
			if err != nil {
				return v, err
			}
			b, err := evolution.ControlSemantic(base.Results[j])
			if err != nil {
				return v, err
			}
			c, err := evolution.ControlSemantic(trial.Results[j])
			if err != nil {
				return v, err
			}
			bOK = bOK && bytes.Equal(b, w)
			cOK = cOK && bytes.Equal(c, w)
			v.OutcomesEqual = v.OutcomesEqual && bytes.Equal(b, c)
		}
		v.OutcomesEqual = v.OutcomesEqual && (pair.Baseline.OutputStateHash == pair.Candidate.OutputStateHash)
		bValue, cValue := "0", "0"
		if bOK {
			v.BaselineCorrect++
			bValue = "1"
		}
		if cOK {
			v.CandidateCorrect++
			cValue = "1"
		}
		v.BaselineValues = append(v.BaselineValues, bValue)
		v.CandidateValues = append(v.CandidateValues, cValue)
		v.RequiredPassed = v.RequiredPassed && (!label.Required || cOK)
		regressed = regressed || (bOK && !cOK)
		newCorrect = newCorrect || (!bOK && cOK)
	}
	v.Total = len(inputs.Cases)
	v.Gain = newCorrect && !regressed && v.RequiredPassed
	return v, nil
}
