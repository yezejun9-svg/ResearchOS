// Read-only W11-02 resource/aggregate probe. No start/configure command exists.
package main

import (
	"encoding/json"
	"fmt"
	"os"
	"researchos.local/research-os/adapters/decision"
	"researchos.local/research-os/adapters/protectedstore"
)

const archive = "execution/verifier/W11/frozen-live-ac9d6153/aggregate.stdout.json"
const archiveHash = "sha256:22b5f70744cec75c825ed865dba56bd79ff27b3022a07f78811ed28e5ee04d8a"

const readinessPath = "execution/v2.4/receipts/W11/W11-02/imported-service-readiness-20261005T195606Z/readiness.json"
const readinessHash = "sha256:ab1c7a28bcb9cc7a1f55a844ed757868c6c792269d1625d1df3772df6d701884"

func reports(s protectedstore.SafeSummary, mode string) []any {
	out := []any{}
	if s.Frozen == nil {
		return out
	}
	for _, k := range s.Frozen.Keys {
		i := decision.QualificationAuditInput{Requested: k.Scope, Observed: k.Scope, EvidenceMode: mode, LabelBasis: "OBJECTIVE", IndependentHoldout: true, DisjointSourceFamilies: true, Development: k.DevelopmentCount, Holdout: k.Planned, RecordedInvocations: k.RecordedInvocations, Correct: k.Correct, FalseAccept: k.FalseAccept, FalseReject: k.FalseReject, Abstain: k.Abstain, Errors: k.Errors, CriticalFalseAccept: k.CriticalFalseAccept, NegativeLabels: k.NegativeLabelCount, AcceptActions: k.NonAbstainedAcceptCount, RejectActions: k.NonAbstainedRejectCount, LatencyMS: k.LatencyMS}
		out = append(out, map[string]any{"aggregate_input": i, "audit": decision.AuditQualification(i), "development_metrics": k.Development, "authority_basis": "existing fixed protected evaluator; audit cannot create domain qualification"})
	}
	return out
}

func main() {
	refresh := len(os.Args) == 2 && os.Args[1] == "--refresh-aggregate"
	if len(os.Args) != 1 && !refresh {
		fmt.Fprintln(os.Stderr, "only explicit --refresh-aggregate is accepted")
		os.Exit(2)
	}
	raw, e := os.ReadFile(archive)
	if e != nil || decision.Digest(raw) != archiveHash {
		fmt.Fprintln(os.Stderr, "pinned public aggregate unavailable or changed")
		os.Exit(1)
	}
	old, e := protectedstore.ParseSafeSummary(raw)
	if e != nil {
		fmt.Fprintln(os.Stderr, "pinned aggregate violates frozen schema")
		os.Exit(1)
	}
	readinessRaw, err := os.ReadFile(readinessPath)
	if err != nil || decision.Digest(readinessRaw) != readinessHash {
		fmt.Fprintln(os.Stderr, "recorded readiness evidence unavailable or changed")
		os.Exit(1)
	}
	var readiness struct {
		ArtifactHashes map[string]string `json:"artifact_hashes"`
	}
	if json.Unmarshal(readinessRaw, &readiness) != nil {
		os.Exit(1)
	}
	for name, hash := range readiness.ArtifactHashes {
		// The fixed hash above pins this list; all listed files are public logs.
		body, err := os.ReadFile("execution/v2.4/receipts/W11/W11-02/imported-service-readiness-20261005T195606Z/" + name)
		if err != nil || decision.Digest(body) != "sha256:"+hash {
			fmt.Fprintln(os.Stderr, "readiness command evidence changed")
			os.Exit(1)
		}
	}
	state := "RECORDED_STOPPED_START_PERMISSION_DENIED"
	query := "NOT_REPEATED_NO_NEW_STATE"
	mode := "RECORDED_LIVE_WINDOWS_READINESS_NOT_NEW_MEASUREMENT"
	var live any
	currentReports := []any{}
	if refresh {
		query = "aggregate"
		mode = "LIVE_WINDOWS_READ_ONLY_EXISTING_AGGREGATE"
		current, err := protectedstore.QueryFrozenService("aggregate")
		state = "UNAVAILABLE"
		if err == nil {
			state = current.Frozen.RunState
			live = current
			currentReports = reports(current, "CURRENT_PROTECTED_LIVE")
		}
	}
	missing := []any{}
	for _, language := range []string{"zh", "zh-en"} {
		// No authorized model/rubric or independent dataset exists for this
		// purpose in the fixed evaluator. Do not borrow evidence-validity keys.
		x := decision.QualificationAuditInput{Requested: decision.Scope{TaskType: "reuse_selection", Language: language, Provider: "typesafe"}, EvidenceMode: "NOT_RUN"}
		missing = append(missing, map[string]any{"audit": decision.AuditQualification(x), "provider_authorization": "NOT_ESTABLISHED_FOR_NEW_RUN", "model_revision": nil, "rubric_revision": nil, "development_count": nil, "holdout_count": nil, "real_invocations": nil, "actual_cost": nil, "latency_ms": nil, "resource_status": "NO_PURPOSE_RUN_OR_CASES_REGISTERED_IN_FIXED_EVALUATOR"})
	}
	json.NewEncoder(os.Stdout).Encode(map[string]any{
		"schema": "researchos.w1102-readiness.v1", "status": "BLOCKED", "environment_mode": mode,
		"new_provider_calls": 0, "formal_label_body_accessed": false, "automatic_authority": "NONE", "maximum_mode": "ADVISORY",
		"service_query": query, "service_state": state, "current_summary": live, "current_key_reports": currentReports,
		"recorded_readiness": map[string]any{"path": readinessPath, "sha256": readinessHash, "observed_at": "2026-10-05T19:56:06.708438+00:00", "block_reason": "OS_SERVICE_CONTROL_PERMISSION"},
		"archive":            map[string]any{"path": archive, "sha256": archiveHash, "mode": "ARCHIVED_LIVE_NOT_NEW_MEASUREMENT", "key_reports": reports(old, "ARCHIVED_LIVE")},
		"reuse_selection":    missing, "credential_status": "NOT_PROBED_NO_NEW_PROVIDER_AUTHORIZATION",
		"limitations": []string{"No W11-02 real inference was authorized or dispatched.", "The existing evaluator cannot run reuse_selection or new independent holdout keys.", "The existing 30 development + 15 holdout samples per language cannot qualify a key.", "Descriptive audits do not call domain acceptance or grant BOUNDED_AUTO."},
	})
}
