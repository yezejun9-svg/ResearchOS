package decision

import "math"

// QualificationAuditInput contains aggregate evidence only. It is NOT an
// invocation capability or a Qualification result accepted by the domain.
// Callers must obtain independent provenance outside this descriptive audit.
type QualificationAuditInput struct {
	Requested              Scope           `json:"requested_scope"`
	Observed               Scope           `json:"observed_scope"`
	EvidenceMode           string          `json:"evidence_mode"`
	LabelBasis             string          `json:"label_basis"`
	IndependentHoldout     bool            `json:"independent_holdout"`
	DisjointSourceFamilies bool            `json:"disjoint_source_families"`
	UsedForTuning          bool            `json:"used_for_tuning"`
	Development            int64           `json:"development_count"`
	Holdout                int64           `json:"holdout_count"`
	RecordedInvocations    int64           `json:"recorded_invocations"`
	Correct                int64           `json:"correct"`
	FalseAccept            int64           `json:"false_accept"`
	FalseReject            int64           `json:"false_reject"`
	Abstain                int64           `json:"abstain"`
	Errors                 int64           `json:"errors"` // errors are included in abstentions by the frozen service
	CriticalFalseAccept    int64           `json:"critical_false_accept"`
	NegativeLabels         int64           `json:"negative_label_count"`
	AcceptActions          int64           `json:"nonabstained_accept_count"`
	RejectActions          int64           `json:"nonabstained_reject_count"`
	LatencyMS              int64           `json:"latency_ms"`
	ActualCost             *float64        `json:"actual_cost"`
	NegativeCoverage       map[string]bool `json:"negative_coverage"`
}

type QualificationAudit struct {
	Scope                   Scope    `json:"scope"`
	Status                  string   `json:"status"`
	Reasons                 []string `json:"reasons"`
	MaximumMode             string   `json:"maximum_mode"`
	AutomaticAuthority      string   `json:"automatic_authority"`
	FalseAcceptOverHoldout  *float64 `json:"false_accept_over_holdout"`
	FalseAcceptOverNegative *float64 `json:"false_accept_over_negative_labels"`
	DisagreementRate        *float64 `json:"disagreement_rate"`
	AbstainRate             *float64 `json:"abstain_rate"`
	AcceptCoverage          *float64 `json:"accept_coverage"`
	MeanLatencyMS           *float64 `json:"mean_latency_ms"`
	ActualCost              *float64 `json:"actual_cost"`
}

func ratio(a, b int64) *float64 {
	if b <= 0 {
		return nil
	}
	r := float64(a) / float64(b)
	return &r
}

// AuditQualification reports missing evidence and frozen numerical gates for
// ONE exact key. Even a REVIEWABLE report has no automatic authority. The
// protected service and independent domain acceptance remain the trust boundary.
func AuditQualification(in QualificationAuditInput) QualificationAudit {
	r := QualificationAudit{Scope: in.Requested, Status: "BLOCKED", Reasons: []string{}, MaximumMode: "ADVISORY", AutomaticAuthority: "NONE", ActualCost: in.ActualCost}
	add := func(reason string) { r.Reasons = append(r.Reasons, reason) }
	if !in.Requested.Valid() || !in.Observed.Valid() {
		add("INCOMPLETE_KEY")
	}
	if in.Requested != in.Observed {
		add("CROSS_KEY_EVIDENCE")
	}
	if in.EvidenceMode != "CURRENT_PROTECTED_LIVE" {
		add("CURRENT_PROTECTED_LIVE_NOT_ESTABLISHED")
	}
	if in.LabelBasis != "OBJECTIVE" && in.LabelBasis != "HUMAN_TRACEABLE" {
		add("INDEPENDENT_LABEL_BASIS_REQUIRED")
	}
	if !in.IndependentHoldout || !in.DisjointSourceFamilies || in.UsedForTuning {
		add("INDEPENDENT_UNSEEN_HOLDOUT_REQUIRED")
	}
	if in.Development < 60 {
		add("DEVELOPMENT_BELOW_60_PER_KEY")
	}
	if in.Holdout < 30 {
		add("HOLDOUT_BELOW_30_PER_KEY")
	}
	valid := true
	// Bounded arithmetic also rejects malicious overflow in submitted counters.
	for _, n := range []int64{in.Development, in.Holdout, in.RecordedInvocations, in.Correct, in.FalseAccept, in.FalseReject, in.Abstain, in.Errors, in.CriticalFalseAccept, in.NegativeLabels, in.AcceptActions, in.RejectActions} {
		if n < 0 || n > 1000000000 {
			valid = false
		}
	}
	if in.LatencyMS < 0 || in.ActualCost != nil && (math.IsNaN(*in.ActualCost) || math.IsInf(*in.ActualCost, 0) || *in.ActualCost < 0) {
		valid = false
	}
	if in.ActualCost != nil && (math.IsNaN(*in.ActualCost) || math.IsInf(*in.ActualCost, 0)) {
		// Keep the rejection serializable: JSON cannot represent nonfinite
		// costs, and an invalid measurement must not prevent its own receipt.
		r.ActualCost = nil
	}
	if valid && (in.Correct+in.FalseAccept+in.FalseReject+in.Abstain != in.Holdout || in.AcceptActions+in.RejectActions+in.Abstain != in.Holdout || in.CriticalFalseAccept > in.FalseAccept || in.FalseAccept > in.NegativeLabels || in.NegativeLabels > in.Holdout || in.Errors > in.Abstain || in.FalseAccept > in.AcceptActions || in.FalseReject > in.RejectActions || in.RecordedInvocations > in.Holdout) {
		valid = false
	}
	if valid && (in.AcceptActions-in.FalseAccept+in.FalseReject > in.Holdout-in.NegativeLabels || in.RejectActions-in.FalseReject+in.FalseAccept > in.NegativeLabels) {
		valid = false
	}
	if !valid {
		add("INVALID_COUNTS_OR_METRICS")
	} else {
		r.FalseAcceptOverHoldout = ratio(in.FalseAccept, in.Holdout)
		r.FalseAcceptOverNegative = ratio(in.FalseAccept, in.NegativeLabels)
		r.DisagreementRate = ratio(in.FalseAccept+in.FalseReject, in.Holdout)
		r.AbstainRate = ratio(in.Abstain, in.Holdout)
		r.AcceptCoverage = ratio(in.AcceptActions, in.Holdout)
		r.MeanLatencyMS = ratio(in.LatencyMS, in.RecordedInvocations)
		if in.RecordedInvocations != in.Holdout || in.RecordedInvocations == 0 {
			add("INCOMPLETE_REAL_INVOCATIONS")
		}
		if in.CriticalFalseAccept != 0 {
			add("CRITICAL_FALSE_ACCEPT")
		}
		if in.FalseAccept*20 > in.Holdout {
			add("FALSE_ACCEPT_ABOVE_5_PERCENT")
		}
		// W11-02 additionally requires disagreement <= 5%; the A08 false
		// acceptance denominator is retained separately, never substituted.
		if (in.FalseAccept+in.FalseReject)*20 > in.Holdout {
			add("DISAGREEMENT_ABOVE_5_PERCENT")
		}
		if in.AcceptActions == 0 {
			add("NO_VERIFIED_ACCEPT_ACTIONS")
		}
	}
	if in.Requested.TaskType == "reuse_selection" {
		for _, name := range []string{"license_unknown", "platform_mismatch", "integration_unavailable", "no_benefit", "missing_evidence", "readme_injection", "timeout", "abstain", "cross_scope_qualification"} {
			if !in.NegativeCoverage[name] {
				add("MISSING_REUSE_NEGATIVE:" + name)
			}
		}
	}
	if len(r.Reasons) == 0 {
		r.Status = "REVIEWABLE"
	}
	return r
}
