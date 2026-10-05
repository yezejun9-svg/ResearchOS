package decision

import (
	"math"
	"slices"
	"testing"
)

func auditFixture() QualificationAuditInput {
	s := Scope{TaskType: "reuse_selection", Language: "zh", Provider: "typesafe", ModelRevision: "fixture-revision", RubricRevision: "fixture-rubric"}
	return QualificationAuditInput{Requested: s, Observed: s, EvidenceMode: "CURRENT_PROTECTED_LIVE", LabelBasis: "OBJECTIVE", IndependentHoldout: true, DisjointSourceFamilies: true, Development: 60, Holdout: 30, RecordedInvocations: 30, Correct: 30, NegativeLabels: 15, AcceptActions: 15, RejectActions: 15, LatencyMS: 3000, NegativeCoverage: map[string]bool{"license_unknown": true, "platform_mismatch": true, "integration_unavailable": true, "no_benefit": true, "missing_evidence": true, "readme_injection": true, "timeout": true, "abstain": true, "cross_scope_qualification": true}}
}

func TestW1102QualificationAudit(t *testing.T) {
	// These are invented numerical fixtures, never independent labels or LIVE
	// measurements. The positive branch proves reporting only cannot grant.
	base := auditFixture()
	r := AuditQualification(base)
	assert(t, "W1102-REPORT-NEVER-GRANTS", []any{"REVIEWABLE", "ADVISORY", "NONE"}, []any{r.Status, r.MaximumMode, r.AutomaticAuthority})
	assert(t, "W1102-UNKNOWN-COST-NULL", true, r.ActualCost == nil)
	assert(t, "W1102-LATENCY", float64(100), *r.MeanLatencyMS)
	cases := []struct {
		id, reason string
		change     func(*QualificationAuditInput)
	}{
		{"SMOKE12", "HOLDOUT_BELOW_30_PER_KEY", func(x *QualificationAuditInput) { x.Development = 12; x.Holdout = 12 }},
		{"MODEL-VOTE", "INDEPENDENT_LABEL_BASIS_REQUIRED", func(x *QualificationAuditInput) { x.LabelBasis = "MODEL_MAJORITY" }},
		{"DEVELOPMENT-AS-HOLDOUT", "INDEPENDENT_UNSEEN_HOLDOUT_REQUIRED", func(x *QualificationAuditInput) { x.IndependentHoldout = false }},
		{"FAMILY-OVERLAP", "INDEPENDENT_UNSEEN_HOLDOUT_REQUIRED", func(x *QualificationAuditInput) { x.DisjointSourceFamilies = false }},
		{"HOLDOUT-TUNING", "INDEPENDENT_UNSEEN_HOLDOUT_REQUIRED", func(x *QualificationAuditInput) { x.UsedForTuning = true }},
		{"FIXTURE-AS-LIVE", "CURRENT_PROTECTED_LIVE_NOT_ESTABLISHED", func(x *QualificationAuditInput) { x.EvidenceMode = "FIXTURE" }},
		{"ARCHIVE-AS-NEW-LIVE", "CURRENT_PROTECTED_LIVE_NOT_ESTABLISHED", func(x *QualificationAuditInput) { x.EvidenceMode = "ARCHIVED_LIVE" }},
		{"CROSS-PURPOSE", "CROSS_KEY_EVIDENCE", func(x *QualificationAuditInput) { x.Observed.TaskType = "evidence-validity" }},
		{"CROSS-LANGUAGE", "CROSS_KEY_EVIDENCE", func(x *QualificationAuditInput) { x.Observed.Language = "zh-en" }},
		{"CROSS-PROVIDER", "CROSS_KEY_EVIDENCE", func(x *QualificationAuditInput) { x.Observed.Provider = "other" }},
		{"CROSS-MODEL", "CROSS_KEY_EVIDENCE", func(x *QualificationAuditInput) { x.Observed.ModelRevision = "other" }},
		{"CROSS-RUBRIC", "CROSS_KEY_EVIDENCE", func(x *QualificationAuditInput) { x.Observed.RubricRevision = "other" }},
		{"MISSING-KEY", "INCOMPLETE_KEY", func(x *QualificationAuditInput) { x.Requested.RubricRevision = "" }},
		{"INSUFFICIENT-DEV", "DEVELOPMENT_BELOW_60_PER_KEY", func(x *QualificationAuditInput) { x.Development = 59 }},
		{"INCOMPLETE-CALLS", "INCOMPLETE_REAL_INVOCATIONS", func(x *QualificationAuditInput) { x.RecordedInvocations = 29 }},
		{"CRITICAL-ERROR", "CRITICAL_FALSE_ACCEPT", func(x *QualificationAuditInput) {
			x.Correct = 29
			x.FalseAccept = 1
			x.CriticalFalseAccept = 1
			x.AcceptActions = 16
			x.RejectActions = 14
		}},
		{"FALSE-ACCEPT-OVER-5", "FALSE_ACCEPT_ABOVE_5_PERCENT", func(x *QualificationAuditInput) {
			x.Correct = 28
			x.FalseAccept = 2
			x.AcceptActions = 17
			x.RejectActions = 13
		}},
		{"DISAGREEMENT-OVER-5", "DISAGREEMENT_ABOVE_5_PERCENT", func(x *QualificationAuditInput) {
			x.Correct = 28
			x.FalseReject = 2
			x.AcceptActions = 13
			x.RejectActions = 17
		}},
		{"ALL-ABSTAIN", "NO_VERIFIED_ACCEPT_ACTIONS", func(x *QualificationAuditInput) {
			x.Correct = 0
			x.Abstain = 30
			x.AcceptActions = 0
			x.RejectActions = 0
		}},
		{"COUNT-MISMATCH", "INVALID_COUNTS_OR_METRICS", func(x *QualificationAuditInput) { x.Correct = 31 }},
		{"OVERFLOW", "INVALID_COUNTS_OR_METRICS", func(x *QualificationAuditInput) { x.FalseAccept = math.MaxInt64 }},
		{"NEGATIVE-COST", "INVALID_COUNTS_OR_METRICS", func(x *QualificationAuditInput) { v := -1.; x.ActualCost = &v }},
	}
	for _, tc := range cases {
		t.Run(tc.id, func(t *testing.T) {
			x := auditFixture()
			tc.change(&x)
			r := AuditQualification(x)
			assert(t, "W1102-"+tc.id, []any{"BLOCKED", true, "NONE"}, []any{r.Status, slices.Contains(r.Reasons, tc.reason), r.AutomaticAuthority})
		})
	}
	for _, name := range []string{"license_unknown", "platform_mismatch", "integration_unavailable", "no_benefit", "missing_evidence", "readme_injection", "timeout", "abstain", "cross_scope_qualification"} {
		x := auditFixture()
		delete(x.NegativeCoverage, name)
		r := AuditQualification(x)
		assert(t, "W1102-REUSE-"+name, []any{"BLOCKED", true}, []any{r.Status, slices.Contains(r.Reasons, "MISSING_REUSE_NEGATIVE:"+name)})
	}
	x := auditFixture()
	x.Correct = 29
	x.FalseAccept = 1
	x.AcceptActions = 16
	x.RejectActions = 14
	r = AuditQualification(x)
	assert(t, "W1102-DENOMINATORS", []float64{1. / 30, 1. / 15}, []float64{*r.FalseAcceptOverHoldout, *r.FalseAcceptOverNegative})
	x = auditFixture()
	x.NegativeLabels = 30
	r = AuditQualification(x)
	assert(t, "W1102-LABEL-COUNTS", true, slices.Contains(r.Reasons, "INVALID_COUNTS_OR_METRICS"))
	x = auditFixture()
	x.Holdout = 40
	x.RecordedInvocations = 40
	x.Correct = 38
	x.FalseAccept = 2
	x.AcceptActions = 22
	x.RejectActions = 18
	x.NegativeLabels = 20
	r = AuditQualification(x)
	assert(t, "W1102-EXACT-5-PERCENT", "REVIEWABLE", r.Status)
}
