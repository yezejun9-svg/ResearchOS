package skills

import "testing"

func TestTrustedSuitePreservesBaselineAndMandatoryNegatives(t *testing.T) {
	cases := []struct {
		name, want                                  string
		suite, negative, previous, previousNegative []string
	}{
		{"first-version-negative-relabel", "reject", []string{"stable", "improved", "injection"}, []string{"stable"}, nil, nil},
		{"upgrade-suite-shrink", "reject", []string{"stable", "new-improvement", "injection"}, []string{"injection"}, []string{"stable", "improved", "injection"}, []string{"injection"}},
		{"upgrade-adds-case", "allow", []string{"stable", "improved", "injection", "new-improvement"}, []string{"injection"}, []string{"stable", "improved", "injection"}, []string{"injection"}},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			negative, err := TrustedSuite(tc.suite, tc.negative, tc.previous, tc.previousNegative)
			if tc.want == "reject" && err == nil || tc.want == "allow" && (err != nil || !negative["injection"]) {
				t.Fatalf("TrustedSuite negative=%v err=%v, want %s", negative, err, tc.want)
			}
		})
	}
}
