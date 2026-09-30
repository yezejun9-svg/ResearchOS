// Package evaluation reconciles runner output. It has no acceptance authority.
package evaluation

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"reflect"
	"researchos.local/research-os/internal/canonical"
	"time"
)

type Object = map[string]any

func Digest(b []byte) string { h := sha256.Sum256(b); return "sha256:" + hex.EncodeToString(h[:]) }
func Bytes(v any) []byte {
	b, e := json.Marshal(v)
	if e != nil {
		panic(e)
	}
	return b
}

// Manifest is frozen before invocation and comes from the authorized host, never the candidate.
type Manifest struct {
	ProjectID     string   `json:"project_id"`
	ExperimentID  string   `json:"experiment_id"`
	RunID         string   `json:"run_id"`
	Engine        Object   `json:"engine"`
	DatasetHash   string   `json:"dataset_hash"`
	CandidateHash string   `json:"candidate_hash"`
	BaselineHash  string   `json:"baseline_hash"`
	RubricHash    string   `json:"rubric_hash"`
	Expected      []string `json:"expected_case_ids"`
}
type Result struct {
	CaseID  string   `json:"case_id"`
	Verdict string   `json:"verdict"`
	Hard    *bool    `json:"hard_checks_passed"`
	Score   *float64 `json:"score"`
	Reason  string   `json:"reason"`
	Latency *int64   `json:"latency_ms"`
	Cost    any      `json:"cost"`
	Output  any      `json:"output_artifact_ref"`
}

func (m Manifest) Validate() error {
	if m.ProjectID == "" || m.ExperimentID == "" || m.RunID == "" || len(m.Expected) == 0 {
		return errors.New("nonempty identity and expected IDs required")
	}
	if m.Engine["name"] != "NATIVE" && m.Engine["name"] != "PROMPTFOO" {
		return errors.New("unqualified engine")
	}
	if s, ok := m.Engine["version"].(string); !ok || s == "" {
		return errors.New("fixed engine version required")
	}
	for _, h := range []any{m.DatasetHash, m.CandidateHash, m.BaselineHash, m.RubricHash, m.Engine["config_hash"]} {
		s, ok := h.(string)
		if !ok || len(s) != 71 || s[:7] != "sha256:" {
			return errors.New("SHA-256 binding required")
		}
		if _, e := hex.DecodeString(s[7:]); e != nil {
			return e
		}
	}
	ids := map[string]bool{}
	for _, id := range m.Expected {
		if id == "" || ids[id] {
			return errors.New("empty or duplicate expected ID")
		}
		ids[id] = true
	}
	return nil
}

// Normalize preserves one row per expected ID. Unknown/duplicate rows remain in the hashed raw export.
func Normalize(m Manifest, observed Manifest, rawExport []byte, rawHash string, exit *int, duration int64) (Object, error) {
	if e := m.Validate(); e != nil {
		return nil, e
	}
	if duration < 0 {
		return nil, errors.New("negative duration")
	}

	strict, e := canonical.JSON(rawExport)
	if e != nil {
		return nil, fmt.Errorf("raw export JSON: %w", e)
	}
	var raw []Result
	decoder := json.NewDecoder(bytes.NewReader(strict))
	decoder.DisallowUnknownFields()
	if e = decoder.Decode(&raw); e != nil {
		return nil, fmt.Errorf("raw result contract: %w", e)
	}
	if raw == nil {
		return nil, errors.New("raw result array required")
	}
	counts := Object{"expected_count": len(m.Expected), "observed_count": 0, "pass_count": 0, "fail_count": 0, "error_count": 0, "abstain_count": 0, "missing_count": 0, "duplicate_count": 0}
	status := "COMPLETE"
	if !reflect.DeepEqual(m, observed) || Digest(rawExport) != rawHash {
		status = "INVALID"
	}
	ids := map[string]bool{}
	for _, id := range m.Expected {
		ids[id] = true
	}
	rows := map[string]Result{}
	for _, r := range raw {
		if !ids[r.CaseID] {
			status = "INVALID"
			continue
		}
		if _, ok := rows[r.CaseID]; ok {
			counts["duplicate_count"] = counts["duplicate_count"].(int) + 1
			status = "INVALID"
			continue
		}
		if r.Reason == "" || (r.Score != nil && (*r.Score < 0 || *r.Score > 1)) || (r.Latency != nil && *r.Latency < 0) {
			status = "INVALID"
		}
		switch r.Verdict {
		case "PASS", "FAIL", "ERROR", "ABSTAIN", "MISSING":
		default:
			status = "INVALID"
			r.Verdict = "ERROR"
			r.Reason = "invalid runner verdict"
		}
		if r.Verdict == "PASS" && (r.Hard == nil || !*r.Hard) {
			r.Verdict = "FAIL"
			r.Reason = "deterministic hard gate not passed"
		}
		rows[r.CaseID] = r
	}
	results := []Result{}
	for _, id := range m.Expected {
		r, ok := rows[id]
		if !ok {
			r = Result{CaseID: id, Verdict: "MISSING", Reason: "no completed output received"}
		}
		results = append(results, r)
		key := map[string]string{"PASS": "pass_count", "FAIL": "fail_count", "ERROR": "error_count", "ABSTAIN": "abstain_count", "MISSING": "missing_count"}[r.Verdict]
		counts[key] = counts[key].(int) + 1
		if r.Verdict != "MISSING" {
			counts["observed_count"] = counts["observed_count"].(int) + 1
		}
	}
	if status != "INVALID" && (counts["missing_count"].(int) > 0 || exit == nil) {
		status = "INCOMPLETE"
	}
	report := Object{"schema_version": "2.0.0", "report_id": fmt.Sprintf("eval-%d", time.Now().UnixNano()), "project_id": m.ProjectID, "experiment_id": m.ExperimentID, "run_id": m.RunID, "external_eval_id": nil, "engine": m.Engine, "dataset_split": "DEVELOPMENT", "access_class": "PROJECT", "dataset_hash": m.DatasetHash, "candidate_hash": m.CandidateHash, "baseline_hash": m.BaselineHash, "rubric_hash": m.RubricHash, "expected_case_ids": m.Expected, "results": results, "counts": counts, "duration_ms": duration, "cost": nil, "exit_code": exit, "integrity_status": status, "raw_artifact_refs": []any{}, "created_at": time.Now().UTC().Format(time.RFC3339Nano)}
	return report, nil
}

// Validate is a verifier-side recheck of serialized reports against the frozen manifest.
func Validate(m Manifest, report Object, rawExport []byte, rawHash string) error {
	b := Bytes(report)
	var parsed struct {
		Manifest
		Results  []Result `json:"results"`
		Counts   Object   `json:"counts"`
		Status   string   `json:"integrity_status"`
		Exit     *int     `json:"exit_code"`
		Duration int64    `json:"duration_ms"`
	}
	if e := json.Unmarshal(b, &parsed); e != nil {
		return e
	}
	normalized, e := Normalize(m, parsed.Manifest, rawExport, rawHash, parsed.Exit, parsed.Duration)
	if e != nil {
		return e
	}
	if report["dataset_split"] != "DEVELOPMENT" || report["access_class"] != "PROJECT" {
		return errors.New("formal holdout unavailable before W17")
	}
	if normalized["integrity_status"] != "COMPLETE" || parsed.Status != "COMPLETE" || !reflect.DeepEqual(Bytes(normalized["counts"]), Bytes(parsed.Counts)) {
		return errors.New("invalid or incomplete report/counts")
	}
	if !reflect.DeepEqual(Bytes(normalized["results"]), Bytes(parsed.Results)) {
		return errors.New("result hard gate changed")
	}
	return nil
}

// Summary emits allowlisted structured development fields only; never arbitrary reasons or case contents.
func Summary(report Object, artifactRef any) Object {
	s := Object{"schema_version": "2.0.0", "report_artifact_ref": artifactRef, "limitations": []string{"DEVELOPMENT_ONLY; no Jev or holdout qualification"}}
	for _, k := range []string{"project_id", "experiment_id", "run_id", "dataset_split", "counts", "dataset_hash", "candidate_hash", "baseline_hash", "rubric_hash", "integrity_status", "duration_ms", "cost", "created_at"} {
		s[k] = report[k]
	}
	return s
}
