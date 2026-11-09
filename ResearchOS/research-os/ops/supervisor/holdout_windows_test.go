//go:build windows

package supervisor

import "testing"

func TestObjectiveHoldoutGain(t *testing.T) {
	for _, tc := range []struct {
		name string
		rows []BenefitRow
		want bool
	}{
		{"newly-correct-with-stable-win-preserved", []BenefitRow{
			{Expected: 5, BaselineOutcome: 4, CandidateOutcome: 5, BaselineScore: 10, CandidateScore: 10},
			{Expected: 8, BaselineOutcome: 8, CandidateOutcome: 8, BaselineScore: 10, CandidateScore: 10},
		}, true},
		{"score-only-inflation", []BenefitRow{
			{Expected: 5, BaselineOutcome: 5, CandidateOutcome: 5, BaselineScore: 10, CandidateScore: 100},
			{Expected: 8, BaselineOutcome: 8, CandidateOutcome: 8, BaselineScore: 10, CandidateScore: 100},
		}, false},
		{"new-win-with-regression", []BenefitRow{
			{Expected: 5, BaselineOutcome: 4, CandidateOutcome: 5},
			{Expected: 8, BaselineOutcome: 8, CandidateOutcome: 7},
		}, false},
	} {
		t.Run(tc.name, func(t *testing.T) {
			if got := objectiveHoldoutGain(tc.rows); got != tc.want {
				t.Fatalf("objective gain = %v, want %v", got, tc.want)
			}
		})
	}
}
