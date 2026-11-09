//go:build windows

// This one-off verifier reads only the sealed 104b83f fixture evidence. It does
// not launch control, open an authority database, provision a grant, or write to
// the CanaryStore. Private payloads remain in memory and never enter the report.
package main

import (
	"bytes"
	"context"
	"encoding/json"
	"io"
	"os"
	"path/filepath"
	"strings"

	"golang.org/x/sys/windows"
	"researchos.local/research-os/adapters/protectedstore"
	"researchos.local/research-os/evaluation/evolution"
	"researchos.local/research-os/internal/canonical"
	"researchos.local/research-os/ops/supervisor"
)

const sealedStore = `D:\作品集\ResearchOS\research-os\.local\control-business-proof-104b83f-private`
const receiptHash = "sha256:5ab69b86ff951f412450d3e2af272009bfffb99cbfe12ef8a4a161899175760a"
const suiteHash = "sha256:47e6eb08c4de1c3570bcb3bd4f5a871511b8fae1b8ab34f3a9f32108fa666d09"

type report struct {
	Schema            string `json:"schema"`
	Status            string `json:"status"`
	Failure           string `json:"failure"`
	Scope             string `json:"scope"`
	CurrentAuthority  string `json:"current_authority"`
	CurrentVerifier   string `json:"current_verifier"`
	CurrentOS         string `json:"current_os"`
	DeletedOutputDB   string `json:"deleted_output_database"`
	AuthorityLog      string `json:"authority_log_authenticity"`
	ProofHash         string `json:"proof_hash,omitempty"`
	InputsHash        string `json:"inputs_hash,omitempty"`
	LabelsHash        string `json:"labels_hash,omitempty"`
	Total             int    `json:"total"`
	BaselineCorrect   int    `json:"baseline_correct"`
	CandidateCorrect  int    `json:"candidate_correct"`
	RequiredPassed    bool   `json:"required_passed"`
	OutcomesEqual     bool   `json:"outcomes_equal"`
	Gain              bool   `json:"gain"`
	ExternalBinding   bool   `json:"external_binding"`
	HistoricalBinding bool   `json:"historical_receipt_binding"`
	SummaryBinding    bool   `json:"summary_binding"`
}

func closedReport() report {
	return report{Schema: "researchos.control-private-recomputation.v1", Status: "FAILED", Failure: "ARGUMENTS", Scope: "HISTORICAL_RECEIPT_ONLY", CurrentAuthority: "UNVERIFIED", CurrentVerifier: "UNVERIFIED", CurrentOS: "UNVERIFIED", DeletedOutputDB: "UNVERIFIED", AuthorityLog: "UNVERIFIED"}
}

// Reject missing paths and any reparse component before invoking OpenCanary.
// OpenCanary then independently holds all ancestors and validates the existing
// owner-only ACL. Its create=false path contains no file/key/index/ACL writes.
func plainPath(path string, directory bool) bool {
	if !filepath.IsAbs(path) || filepath.Clean(path) != path || strings.HasPrefix(path, `\\`) {
		return false
	}
	for current := path; ; current = filepath.Dir(current) {
		name, err := windows.UTF16PtrFromString(current)
		if err != nil {
			return false
		}
		attrs, err := windows.GetFileAttributes(name)
		if err != nil || attrs&windows.FILE_ATTRIBUTE_REPARSE_POINT != 0 {
			return false
		}
		if current == path && (attrs&windows.FILE_ATTRIBUTE_DIRECTORY != 0) != directory {
			return false
		}
		if filepath.Dir(current) == current {
			break
		}
	}
	return true
}

func publicBytes(path, expected string) ([]byte, bool) {
	if !plainPath(path, false) {
		return nil, false
	}
	f, err := os.Open(path)
	if err != nil {
		return nil, false
	}
	defer f.Close()
	raw, err := io.ReadAll(io.LimitReader(f, 8*1024*1024+1))
	return raw, err == nil && len(raw) <= 8*1024*1024 && evolution.Digest(raw) == expected
}

func hashObject(value any) string {
	raw, err := canonical.JSON(evolution.Bytes(value))
	if err != nil {
		return ""
	}
	return evolution.Digest(raw)
}

func recompute(args []string) report {
	r := closedReport()
	if len(args) != 6 || args[0] != "--store" || args[2] != "--public-receipt" || args[4] != "--public-suite" || args[1] != sealedStore {
		return r
	}
	r.Failure = "PATH_OR_PUBLIC_BYTES"
	if !plainPath(args[1], true) {
		return r
	}
	receiptRaw, ok := publicBytes(args[3], receiptHash)
	if !ok {
		return r
	}
	suiteRaw, ok := publicBytes(args[5], suiteHash)
	if !ok {
		return r
	}
	var receipt struct {
		Candidate map[string]any `json:"candidate"`
		Execution struct {
			Proof       supervisor.ControlProof `json:"control_proof"`
			PlanHash    string                  `json:"plan_hash"`
			SuiteHash   string                  `json:"suite_hash"`
			PolicyHash  string                  `json:"policy_hash"`
			HoldoutHash string                  `json:"holdout_proof_hash"`
			Summary     json.RawMessage         `json:"holdout_summary"`
		} `json:"execution"`
		ProofHash string `json:"private_proof_hash"`
		ProofRef  struct {
			Hash string `json:"content_hash"`
		} `json:"private_proof_ref"`
		Summary json.RawMessage `json:"private_summary"`
	}
	var suite evolution.ControlSuite
	r.Failure = "PUBLIC_BINDING"
	// Receipt bytes are fixed above; only the subset needed for verification is
	// decoded. The suite and all private objects use strict typed decoding.
	if json.Unmarshal(receiptRaw, &receipt) != nil || evolution.StrictControlJSON(suiteRaw, &suite) != nil || evolution.ValidateControlDataset(suite.Inputs, suite.Labels) != nil {
		return r
	}
	p := receipt.Execution.Proof
	plan := map[string]any{}
	for _, key := range []string{"scope", "candidate_artifact_ref", "stable_artifact_ref", "isolated_workspace_id", "baseline_suite_ref", "baseline_policy_hash", "changed_paths_manifest_ref", "experiment_id", "migration_plan_ref", "rollback_plan_ref", "independent_supervisor_id"} {
		value, exists := receipt.Candidate[key]
		if !exists {
			return r
		}
		plan[key] = value
	}
	project, ok := receipt.Candidate["project_id"].(string)
	if !ok || project == "" || p.Profile != evolution.ControlProfile || p.Revision != evolution.ControlPublicRevision || p.Binding.Protocol != evolution.ControlProtocol || suite.Inputs.Revision != evolution.ControlPublicRevision || p.Binding != suite.Inputs.Binding || hashObject(plan) != p.PlanHash || receipt.Execution.PlanHash != p.PlanHash || receipt.Execution.SuiteHash != suiteHash || p.PublicSuiteHash != suiteHash || receipt.Execution.PolicyHash != p.PolicyHash || receipt.ProofHash != receipt.Execution.HoldoutHash || receipt.ProofHash != receipt.ProofRef.Hash {
		return r
	}
	if _, err := supervisor.CheckControl(p, suite.Inputs, suite.Labels, p.PlanHash, p.StableHash, p.CandidateHash, p.StableSourceHash, p.CandidateSourceHash, suiteHash); err != nil {
		return r
	}
	r.Failure = "STORE_BOUNDARY"
	store, err := protectedstore.OpenCanary(args[1])
	if err != nil {
		return r
	}
	defer store.Close()
	ctx := context.Background()
	boundary, err := store.Boundary(ctx)
	if err != nil || boundary.Mode != "CANARY_ONLY" || boundary.IndependentIdentity || !boundary.UnrestrictedSameUserCanRead || store.Ready(ctx, "FIXTURE") != nil {
		return r
	}
	entries, err := os.ReadDir(args[1])
	if err != nil {
		return r
	}
	byHash := map[string]protectedstore.Blob{}
	r.Failure = "UNIQUE_PRIVATE_METADATA"
	for _, entry := range entries {
		if entry.IsDir() || !strings.HasSuffix(entry.Name(), ".json") {
			continue
		}
		ticket := "ps1:" + strings.TrimSuffix(entry.Name(), ".json")
		blob, err := store.Describe(ctx, project, ticket)
		if err != nil || blob.MeasurementMode != "FIXTURE" || blob.MediaType != "application/json" {
			return r
		}
		if _, duplicate := byHash[blob.Hash]; duplicate {
			return r
		}
		byHash[blob.Hash] = blob
	}
	if len(byHash) != 3 {
		return r
	}
	proofBlob, ok := byHash[receipt.ProofHash]
	if !ok {
		return r
	}
	proofRaw, err := store.Read(ctx, proofBlob)
	if err != nil {
		return r
	}
	var proof supervisor.ControlProof
	r.Failure = "PRIVATE_BINDING"
	if evolution.StrictControlJSON(proofRaw, &proof) != nil || proof.Profile != evolution.ControlProfile || proof.Revision != evolution.ControlPrivateRevision || proof.Binding != p.Binding || evolution.Digest(proofRaw) != receipt.ProofHash || proof.InputsHash == proof.LabelsHash || proof.InputsHash == receipt.ProofHash || proof.LabelsHash == receipt.ProofHash {
		return r
	}
	inputBlob, inputFound := byHash[proof.InputsHash]
	labelBlob, labelFound := byHash[proof.LabelsHash]
	if !inputFound || !labelFound {
		return r
	}
	inputRaw, err := store.Read(ctx, inputBlob)
	if err != nil {
		return r
	}
	labelRaw, err := store.Read(ctx, labelBlob)
	if err != nil {
		return r
	}
	var inputs evolution.ControlInputs
	var labels evolution.ControlLabels
	if evolution.StrictControlJSON(inputRaw, &inputs) != nil || evolution.StrictControlJSON(labelRaw, &labels) != nil || inputs.Revision != evolution.ControlPrivateRevision || labels.Revision != evolution.ControlPrivateRevision || inputs.Binding != p.Binding || labels.Binding != p.Binding {
		return r
	}
	r.Failure = "PRIVATE_RECOMPUTATION"
	v, err := supervisor.CheckControl(proof, inputs, labels, p.PlanHash, p.StableHash, p.CandidateHash, p.StableSourceHash, p.CandidateSourceHash, suiteHash)
	if err != nil {
		return r
	}
	summary := map[string]any{"revision": v.Revision, "profile": evolution.ControlProfile, "measurement_mode": "FIXTURE", "model_revision": "NONE", "total": v.Total, "baseline_correct": v.BaselineCorrect, "candidate_correct": v.CandidateCorrect, "outcomes_equal": v.OutcomesEqual, "gain": v.Gain}
	want, err := canonical.JSON(evolution.Bytes(summary))
	if err != nil {
		return r
	}
	r.Failure = "FULL_SUMMARY_BINDING"
	for _, raw := range []json.RawMessage{receipt.Summary, receipt.Execution.Summary} {
		got, err := canonical.JSON(raw)
		if err != nil || !bytes.Equal(want, got) {
			return r
		}
	}
	r.Status, r.Failure = "RECOMPUTED", "NONE"
	r.ProofHash, r.InputsHash, r.LabelsHash = receipt.ProofHash, proof.InputsHash, proof.LabelsHash
	r.Total, r.BaselineCorrect, r.CandidateCorrect = v.Total, v.BaselineCorrect, v.CandidateCorrect
	r.RequiredPassed, r.OutcomesEqual, r.Gain = v.RequiredPassed, v.OutcomesEqual, v.Gain
	r.ExternalBinding, r.HistoricalBinding, r.SummaryBinding = true, true, true
	return r
}

func main() {
	defer func() {
		if recover() != nil {
			r := closedReport()
			r.Failure = "INTERNAL_FAILURE"
			_ = json.NewEncoder(os.Stdout).Encode(r)
			os.Exit(1)
		}
	}()
	r := recompute(os.Args[1:])
	if json.NewEncoder(os.Stdout).Encode(r) != nil || r.Status != "RECOMPUTED" {
		os.Exit(1)
	}
}
