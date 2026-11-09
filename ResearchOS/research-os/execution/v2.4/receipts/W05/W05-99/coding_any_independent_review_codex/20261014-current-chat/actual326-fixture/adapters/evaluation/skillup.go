package evaluation

import (
	"bytes"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"go.yaml.in/yaml/v3"
	"math"
	"os"
	"path/filepath"
	"reflect"
	"researchos.local/research-os/internal/canonical"
	"strings"
	"time"
)

// SkillUpRun is frozen by the host before invoking the fixed skill-up binary.
// One native result.json belongs to one iteration; Variant selects exactly one
// configuration without collapsing the other native rows.
type SkillUpRun struct {
	Manifest           Manifest
	Variant            string
	Iteration          int
	Attempt            int
	EngineName         string
	ProviderName       string
	ModelName          string
	FrozenEvalHash     string
	ObservedHash       string
	BinaryHash         string
	ObservedBinaryHash string
}

const SkillUpSourceRevision = "7f1ff9b8e2d7c654728de526867f2f7e7b78ea51"

// ReadSkillUpResult selects the exact native iteration artifact. The caller
// supplies an attempt-specific output root; result.json has no iteration field.
func ReadSkillUpResult(outputRoot string, iteration int) ([]byte, string, error) {
	if iteration < 1 || !filepath.IsAbs(outputRoot) {
		return nil, "", errors.New("absolute output root and positive iteration required")
	}
	path := filepath.Join(outputRoot, fmt.Sprintf("iteration-%d", iteration), "result.json")
	info, err := os.Lstat(path)
	if err != nil {
		return nil, "", err
	}
	if !info.Mode().IsRegular() || info.Size() > 16<<20 {
		return nil, "", errors.New("native result must be a bounded regular file")
	}
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, "", err
	}
	return raw, Digest(raw), nil
}

// ValidateSkillUpConfig checks the exact eval.yaml bytes before a fixture run.
// The narrow W10 path accepts only local skills/cases and no MCP or environment
// injected egress. Provider egress still requires a separately qualified runner.
func ValidateSkillUpConfig(raw []byte, engine, provider, model string) (string, error) {
	var root yaml.Node
	if err := yaml.Unmarshal(raw, &root); err != nil {
		return "", err
	}
	if len(root.Content) != 1 || root.Content[0].Kind != yaml.MappingNode {
		return "", errors.New("skill-up YAML mapping required")
	}
	allowed := map[string]bool{"schema_version": true, "environment": true, "mcp": true, "skills": true, "engine": true, "cases": true, "report": true}
	for i := 0; i < len(root.Content[0].Content); i += 2 {
		if !allowed[root.Content[0].Content[i].Value] {
			return "", errors.New("unqualified skill-up eval setting")
		}
	}
	var cfg struct {
		SchemaVersion string `yaml:"schema_version"`
		Environment   struct {
			Type string            `yaml:"type"`
			Env  map[string]string `yaml:"env"`
		} `yaml:"environment"`
		MCP struct {
			Servers []any `yaml:"servers"`
		} `yaml:"mcp"`
		Skills []struct {
			Source string `yaml:"source"`
			Path   string `yaml:"path"`
		} `yaml:"skills"`
		Engine struct {
			Name  string `yaml:"name"`
			Model struct {
				Provider string `yaml:"provider"`
				Name     string `yaml:"name"`
			} `yaml:"model"`
		} `yaml:"engine"`
		Cases struct {
			Files    []string `yaml:"files"`
			Defaults struct {
				TimeoutSeconds int `yaml:"timeout_seconds"`
				MaxTurns       int `yaml:"max_turns"`
			} `yaml:"defaults"`
			Parallelism int `yaml:"parallelism"`
		} `yaml:"cases"`
		Report struct {
			Formats []string `yaml:"formats"`
		} `yaml:"report"`
	}
	decoder := yaml.NewDecoder(bytes.NewReader(raw))
	decoder.KnownFields(true)
	if err := decoder.Decode(&cfg); err != nil {
		return "", err
	}
	if cfg.SchemaVersion != "v1alpha1" || cfg.Environment.Type != "none" || len(cfg.Environment.Env) != 0 || len(cfg.MCP.Servers) != 0 || cfg.Engine.Name != engine || cfg.Engine.Model.Provider != provider || cfg.Engine.Model.Name != model || len(cfg.Skills) != 1 || cfg.Skills[0].Source != "local_path" || cfg.Skills[0].Path != "." || len(cfg.Cases.Files) == 0 || cfg.Cases.Parallelism != 1 || cfg.Cases.Defaults.TimeoutSeconds < 1 || cfg.Cases.Defaults.MaxTurns < 1 || len(cfg.Report.Formats) != 1 || cfg.Report.Formats[0] != "json" {
		return "", errors.New("skill-up eval configuration or egress policy changed")
	}
	for _, path := range cfg.Cases.Files {
		p := strings.ReplaceAll(path, "\\", "/")
		if !strings.HasPrefix(p, "evals/cases/") || strings.Contains(p, "..") || !strings.HasSuffix(p, ".yaml") || strings.Contains(p, ":") {
			return "", errors.New("skill-up case escaped frozen local path")
		}
	}
	return Digest(raw), nil
}

type skillUpResult struct {
	SchemaVersion string `json:"schema_version"`
	EngineName    string `json:"engine_name"`
	ModelName     string `json:"model_name"`
	Requested     struct {
		Engine   string `json:"engine"`
		Provider string `json:"provider"`
		Model    string `json:"model"`
	} `json:"requested_configuration"`
	Applied struct {
		Engine string `json:"engine"`
		Model  string `json:"model"`
	} `json:"applied_configuration"`
	Cases []struct {
		CaseID        string `json:"case_id"`
		Status        string `json:"status"`
		Configuration string `json:"configuration"`
		DurationMS    int64  `json:"duration_ms"`
		Error         string `json:"error"`
		Grading       *struct {
			Status  string `json:"status"`
			Summary struct {
				Passed   int     `json:"passed"`
				Failed   int     `json:"failed"`
				Total    int     `json:"total"`
				PassRate float64 `json:"pass_rate"`
			} `json:"summary"`
			Assertions []struct {
				Text   string `json:"text"`
				Passed bool   `json:"passed"`
			} `json:"assertion_results"`
		} `json:"grading"`
	} `json:"case_results"`
}

func (s SkillUpRun) validate() error {
	if err := s.Manifest.Validate(); err != nil {
		return err
	}
	if s.Manifest.Engine["name"] != "SKILL_UP" || s.Manifest.Engine["version"] != SkillUpSourceRevision || s.Manifest.Engine["config_hash"] != s.FrozenEvalHash || s.Iteration < 1 || s.Attempt < 1 ||
		(s.Variant != "with_skill" && s.Variant != "without_skill") ||
		s.EngineName == "" || s.ProviderName == "" || s.ModelName == "" ||
		s.FrozenEvalHash == "" || s.FrozenEvalHash != s.ObservedHash ||
		len(s.BinaryHash) != 71 || !strings.HasPrefix(s.BinaryHash, "sha256:") || s.BinaryHash != s.ObservedBinaryHash {
		return errors.New("skill-up invocation differs from frozen configuration")
	}
	if _, err := hex.DecodeString(s.BinaryHash[7:]); err != nil {
		return err
	}
	return nil
}

// NormalizeSkillUp consumes the unmodified iteration-N/result.json bytes.
// Every expected case remains a row; extra configurations are retained in the
// sealed raw artifact, while unknown IDs, duplicate IDs, and absent rows fail
// the integrity gate. SKIP is an execution error, never evidence of success.
func NormalizeSkillUp(s SkillUpRun, rawExport []byte, rawHash string, exit *int, duration int64) (Object, error) {
	if err := s.validate(); err != nil {
		return nil, err
	}
	if duration < 0 {
		return nil, errors.New("negative duration")
	}
	strict, err := canonical.JSON(rawExport)
	if err != nil {
		return nil, fmt.Errorf("skill-up result JSON: %w", err)
	}
	var native skillUpResult
	if err = json.Unmarshal(strict, &native); err != nil {
		return nil, err
	}
	if native.SchemaVersion != "v1alpha1" || native.EngineName != s.EngineName ||
		native.Requested.Engine != s.EngineName || native.Applied.Engine != s.EngineName ||
		native.Requested.Provider != s.ProviderName || native.Requested.Model != s.ModelName || native.Applied.Model != s.ModelName ||
		native.ModelName == "" || native.Cases == nil {
		return nil, errors.New("skill-up native report/configuration mismatch")
	}
	wantModel := s.ModelName
	if native.Requested.Provider != "" {
		wantModel = native.Requested.Provider + "/" + s.ModelName
	}
	if native.ModelName != wantModel {
		return nil, errors.New("skill-up reported model changed")
	}
	known := map[string]bool{}
	for _, id := range s.Manifest.Expected {
		known[id] = true
	}
	rows := map[string]Result{}
	seenNative := map[string]bool{}
	counts := Object{"expected_count": len(s.Manifest.Expected), "observed_count": 0, "pass_count": 0, "fail_count": 0, "error_count": 0, "abstain_count": 0, "missing_count": 0, "duplicate_count": 0}
	status := "COMPLETE"
	if Digest(rawExport) != rawHash {
		status = "INVALID"
	}
	for _, c := range native.Cases {
		if c.Configuration != "with_skill" && c.Configuration != "without_skill" {
			status = "INVALID"
			continue
		}
		if !known[c.CaseID] {
			status = "INVALID"
			continue
		}
		key := c.Configuration + "\x00" + c.CaseID
		if seenNative[key] {
			status = "INVALID"
			if c.Configuration == s.Variant {
				counts["duplicate_count"] = counts["duplicate_count"].(int) + 1
			}
			continue
		}
		seenNative[key] = true
		if c.Configuration != s.Variant {
			continue
		}
		if _, exists := rows[c.CaseID]; exists {
			counts["duplicate_count"] = counts["duplicate_count"].(int) + 1
			status = "INVALID"
			continue
		}
		r := Result{CaseID: c.CaseID, Reason: "skill-up " + c.Status}
		if c.DurationMS < 0 {
			status = "INVALID"
		} else {
			latency := c.DurationMS
			r.Latency = &latency
		}
		switch c.Status {
		case "PASS":
			r.Verdict = "PASS"
			if c.Grading == nil || c.Grading.Status != "PASS" || c.Grading.Summary.Total == 0 ||
				len(c.Grading.Assertions) == 0 || c.Grading.Summary.Passed != c.Grading.Summary.Total ||
				c.Grading.Summary.Failed != 0 || c.Grading.Summary.Total != len(c.Grading.Assertions) {
				r.Verdict = "FAIL"
				r.Reason = "skill-up PASS lacks valid hard checks"
				status = "INVALID"
			} else {
				all := true
				for _, a := range c.Grading.Assertions {
					all = all && a.Passed && strings.TrimSpace(a.Text) != ""
				}
				if !all {
					r.Verdict = "FAIL"
					r.Reason = "skill-up hard check failed"
					status = "INVALID"
				}
			}
		case "FAIL":
			r.Verdict = "FAIL"
		case "ERROR", "SKIP":
			r.Verdict = "ERROR"
		default:
			r.Verdict = "ERROR"
			r.Reason = "invalid skill-up status"
			status = "INVALID"
		}
		if c.Status == "FAIL" && (c.Grading == nil || c.Grading.Status != "FAIL") {
			status = "INVALID"
		}
		if c.Status == "SKIP" && c.Grading != nil && c.Grading.Status != "SKIP" {
			status = "INVALID"
		}
		if c.Grading != nil {
			p := c.Grading.Summary.PassRate
			if math.IsNaN(p) || math.IsInf(p, 0) || p < 0 || p > 1 {
				status = "INVALID"
			} else {
				r.Score = &p
			}
		}
		hard := r.Verdict == "PASS"
		r.Hard = &hard
		rows[c.CaseID] = r
	}
	results := make([]Result, 0, len(s.Manifest.Expected))
	for _, id := range s.Manifest.Expected {
		r, ok := rows[id]
		if !ok {
			r = Result{CaseID: id, Verdict: "MISSING", Reason: "no completed skill-up output received"}
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
	return Object{"schema_version": "2.4.0", "report_id": fmt.Sprintf("eval-%d", time.Now().UnixNano()), "project_id": s.Manifest.ProjectID, "experiment_id": s.Manifest.ExperimentID, "run_id": s.Manifest.RunID, "external_eval_id": nil, "engine": s.Manifest.Engine, "dataset_split": "DEVELOPMENT", "access_class": "PROJECT", "dataset_hash": s.Manifest.DatasetHash, "candidate_hash": s.Manifest.CandidateHash, "baseline_hash": s.Manifest.BaselineHash, "rubric_hash": s.Manifest.RubricHash, "expected_case_ids": s.Manifest.Expected, "results": results, "counts": counts, "duration_ms": duration, "cost": nil, "exit_code": exit, "integrity_status": status, "raw_artifact_refs": []any{}, "created_at": time.Now().UTC().Format(time.RFC3339Nano)}, nil
}

func ValidateSkillUp(s SkillUpRun, report Object, rawExport []byte, rawHash string) error {
	if report["schema_version"] != "2.4.0" || report["dataset_split"] != "DEVELOPMENT" || report["access_class"] != "PROJECT" {
		return errors.New("skill-up development report required")
	}
	var parsed struct {
		Manifest
		Results  []Result `json:"results"`
		Counts   Object   `json:"counts"`
		Status   string   `json:"integrity_status"`
		Exit     *int     `json:"exit_code"`
		Duration int64    `json:"duration_ms"`
	}
	if err := json.Unmarshal(Bytes(report), &parsed); err != nil {
		return err
	}
	if !reflect.DeepEqual(parsed.Manifest, s.Manifest) {
		return errors.New("skill-up manifest changed")
	}
	check, err := NormalizeSkillUp(s, rawExport, rawHash, parsed.Exit, parsed.Duration)
	if err != nil {
		return err
	}
	if parsed.Status != "COMPLETE" || check["integrity_status"] != "COMPLETE" || !bytes.Equal(Bytes(parsed.Results), Bytes(check["results"])) || !bytes.Equal(Bytes(parsed.Counts), Bytes(check["counts"])) {
		return errors.New("skill-up result/counts incomplete or changed")
	}
	return nil
}
