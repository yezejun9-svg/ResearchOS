//go:build windows

// Package supervisor is a bounded development process coordinator. The host
// identity is not an installed independent OS release service; LIVE is closed.
package supervisor

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"researchos.local/research-os/evaluation/evolution"
	sandbox "researchos.local/research-os/ops/experiment_sandbox"
	"time"
)

type Invocation struct {
	Request   evolution.Request `json:"request"`
	BuildHash string            `json:"build_hash"`
	InputHash string            `json:"input_hash"`
	RawHash   string            `json:"raw_hash"`
	Raw       string            `json:"raw"`
	Receipt   sandbox.Receipt   `json:"receipt"`
	Error     string            `json:"error"`
}
type Pair struct {
	Scope           string           `json:"scope"`
	HostPID         int              `json:"host_pid"`
	SuiteHash       string           `json:"suite_hash"`
	PolicyHash      string           `json:"policy_hash"`
	Baseline        Invocation       `json:"baseline"`
	Candidate       Invocation       `json:"candidate"`
	BaselineResult  evolution.Result `json:"baseline_result"`
	CandidateResult evolution.Result `json:"candidate_result"`
	Improved        bool             `json:"improved"`
	StablePreserved bool             `json:"stable_preserved"`
	ProtectedHashes []string         `json:"protected_hashes"`
}

func Invoke(ctx context.Context, binary []byte, phase string, protected []string) Invocation {
	v := Invocation{BuildHash: evolution.Digest(binary)}
	work, e := os.MkdirTemp("", "researchos-w16-process-")
	if e != nil {
		v.Error = e.Error()
		return v
	}
	defer os.RemoveAll(work)
	input, output := filepath.Join(work, "input"), filepath.Join(work, "output")
	for _, dir := range []string{input, output} {
		if e = os.Mkdir(dir, 0700); e != nil {
			v.Error = e.Error()
			return v
		}
	}
	program, path := filepath.Join(input, "candidate.exe"), filepath.Join(input, "request.json")
	v.Request = evolution.Inputs(phase, protected)
	raw := evolution.Bytes(v.Request)
	v.InputHash = evolution.Digest(raw)
	for p, b := range map[string][]byte{program: binary, path: raw} {
		if e = os.WriteFile(p, b, 0600); e != nil {
			v.Error = e.Error()
			return v
		}
	}
	v.Receipt, e = sandbox.Run(ctx, sandbox.Command{Executable: program, Args: []string{path}, InputDirectory: input, OutputDirectory: output, Timeout: 1500 * time.Millisecond})
	v.Raw = string(v.Receipt.Stdout)
	v.RawHash = evolution.Digest(v.Receipt.Stdout)
	if e != nil {
		v.Error = e.Error()
	} else if v.Receipt.ExitCode != 0 || !v.Receipt.Stopped || v.Receipt.TimedOut {
		v.Error = fmt.Sprintf("candidate exit=%d stopped=%v timeout=%v", v.Receipt.ExitCode, v.Receipt.Stopped, v.Receipt.TimedOut)
	}
	return v
}
func Verify(v Invocation, expectedHash string) (evolution.Result, error) {
	if v.InputHash != evolution.Digest(evolution.Bytes(v.Request)) || string(evolution.Bytes(v.Request.Cases)) != string(evolution.Bytes(evolution.Inputs(v.Request.Phase, nil).Cases)) || (v.Request.Phase != "REGRESSION" && v.Request.Phase != "CANARY" && v.Request.Phase != "HEALTH") {
		return evolution.Result{}, fmt.Errorf("frozen native input evidence invalid")
	}
	if v.Error != "" || v.BuildHash != expectedHash || v.RawHash != evolution.Digest([]byte(v.Raw)) || v.Raw != string(v.Receipt.Stdout) || v.Receipt.ExitCode != 0 || !v.Receipt.Stopped || v.Receipt.TimedOut || len(v.Receipt.Capabilities) != 0 || v.Receipt.PID == 0 || v.Receipt.SID == "" {
		return evolution.Result{}, fmt.Errorf("native invocation evidence invalid")
	}
	return evolution.Check([]byte(v.Raw))
}
func Evaluate(ctx context.Context, stable, candidate []byte) (Pair, error) {
	p := Pair{Scope: evolution.Scope, HostPID: os.Getpid(), SuiteHash: evolution.Digest(evolution.Bytes(evolution.Suite())), PolicyHash: evolution.Digest(evolution.Bytes(evolution.Policy()))}
	root, e := os.MkdirTemp("", "researchos-w16-authority-")
	if e != nil {
		return p, e
	}
	defer os.RemoveAll(root)
	paths := []string{}
	for name, raw := range map[string][]byte{"suite.json": evolution.Bytes(evolution.Suite()), "labels.json": evolution.Bytes(evolution.Suite()), "permissions.json": []byte(`{"release":"host-only"}`), "stable.exe": stable} {
		path := filepath.Join(root, name)
		if e = os.WriteFile(path, raw, 0600); e != nil {
			return p, e
		}
		paths = append(paths, path)
		p.ProtectedHashes = append(p.ProtectedHashes, evolution.Digest(raw))
	}
	p.Baseline = Invoke(ctx, stable, "REGRESSION", paths)
	p.BaselineResult, e = Verify(p.Baseline, evolution.Digest(stable))
	if e != nil {
		return p, e
	}
	p.Candidate = Invoke(ctx, candidate, "REGRESSION", paths)
	p.CandidateResult, e = Verify(p.Candidate, evolution.Digest(candidate))
	p.StablePreserved = true
	for i, path := range paths {
		b, err := os.ReadFile(path)
		if err != nil || evolution.Digest(b) != p.ProtectedHashes[i] {
			p.StablePreserved = false
		}
	}
	if e != nil {
		return p, e
	}
	if !p.StablePreserved {
		return p, fmt.Errorf("protected host inputs changed")
	}
	p.Improved = evolution.Improved(p.BaselineResult, p.CandidateResult)
	return p, nil
}
