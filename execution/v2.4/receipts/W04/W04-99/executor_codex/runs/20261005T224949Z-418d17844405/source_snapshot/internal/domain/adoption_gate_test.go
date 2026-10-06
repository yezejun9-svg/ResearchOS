package domain

// W08-01 · the third counter-example on the card: 缺网络跳过复用门自研 must not be presentable as a decision. The
// research stage is where a blocked network gets recorded (RESEARCH_BLOCKED or coverage PARTIAL), so a projection
// that shows REUSE_DECISION as completed while RESEARCH never produced a result is showing a shortcut, not a
// judgement.

import (
	"strings"
	"testing"
)

func TestW0801ProjectionRefusesAReuseDecisionWithoutResearch(t *testing.T) {
	cases := []struct {
		name       string
		research   Object
		wantStatus string
	}{
		{"row says not started", stageRow(StageResearch, StageNotStarted, 1), StageNotStarted},
		{"row says failed", stageRow(StageResearch, StageFailed, 1), StageFailed},
		{"no row at all", nil, "ABSENT"},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			rows := baselineRows()
			rows[2] = stageRow(StageReuseDecision, StageCompleted, 2)
			if tc.research == nil {
				rows = []Object{rows[0], rows[2], rows[3]}
			} else {
				rows[1] = tc.research
			}
			_, e := ProjectStages(rows, validReuseDecision())
			if e == nil {
				t.Fatalf("a completed reuse decision over %s research was presented", tc.wantStatus)
			}
			if want := "while RESEARCH is " + tc.wantStatus; !strings.Contains(e.Error(), want) {
				t.Fatalf("refusal %q does not name %q", e.Error(), want)
			}
		})
	}
}

func TestW0801ProjectionAcceptsAPartialResearchStageAsABasis(t *testing.T) {
	// PARTIAL means the attempt was made and some coverage is missing; that is a different claim from never
	// researching, so the gate must not refuse it. The gap it leaves is stated in the decision itself.
	rows := baselineRows()
	rows[1] = stageRow(StageResearch, StagePartial, 1)
	rows[2] = stageRow(StageReuseDecision, StageCompleted, 2)
	decision := validReuseDecision()
	decision["decision"] = "CUSTOM_GAP"
	decision["remaining_gap"] = "no upstream project covers offline arXiv indexing"
	turns, e := ProjectStages(rows, decision)
	if e != nil {
		t.Fatalf("a partial research stage was refused as if it were absent: %v", e)
	}
	if got := statusOf(t, turns, StageReuseDecision); got.Status != StageCompleted {
		t.Fatalf("the completed decision was not presented: %+v", got)
	}
}
