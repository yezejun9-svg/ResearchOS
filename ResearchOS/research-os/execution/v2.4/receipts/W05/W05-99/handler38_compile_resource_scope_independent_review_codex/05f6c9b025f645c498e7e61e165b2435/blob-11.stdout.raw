package skills

import "fmt"

// FixtureRubric is the service-owned minimum for W15 fixture qualification.
// A skill artifact and its Experiment may add cases, but cannot redefine these
// mandatory cases or their negative classification.
func FixtureRubric() ([]string, map[string]bool) {
	return []string{"stable", "improved", "injection"}, map[string]bool{"injection": true}
}

// TrustedSuite preserves the service rubric and every case and negative case
// qualified by the current active version. Additional candidate cases are
// allowed, while a candidate declaration cannot remove inherited obligations.
func TrustedSuite(candidate, declaredNegative, previous, previousNegative []string) (map[string]bool, error) {
	minimum, negative := FixtureRubric()
	required := map[string]bool{}
	for _, id := range append(append(minimum, previous...), previousNegative...) {
		required[id] = true
	}
	for _, id := range previousNegative {
		negative[id] = true
	}
	seen := map[string]bool{}
	for _, id := range candidate {
		if id == "" || seen[id] {
			return nil, fmt.Errorf("unique suite cases required")
		}
		seen[id] = true
	}
	for id := range required {
		if !seen[id] {
			return nil, fmt.Errorf("trusted suite case absent: %s", id)
		}
	}
	declared := map[string]bool{}
	for _, id := range declaredNegative {
		if !seen[id] || declared[id] {
			return nil, fmt.Errorf("invalid negative case: %s", id)
		}
		declared[id] = true
		negative[id] = true
	}
	for id := range negative {
		if !declared[id] {
			return nil, fmt.Errorf("trusted negative case absent: %s", id)
		}
	}
	return negative, nil
}
