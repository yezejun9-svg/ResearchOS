package skills

import "fmt"

// Compare checks paired pass/fail observations from one frozen suite. The
// verifier must bind these observations to a sealed, independently accepted run.
func Compare(ids []string, before, after []string, negative map[string]bool) error {
	if len(ids) == 0 || len(ids) != len(before) || len(ids) != len(after) || len(negative) == 0 {
		return fmt.Errorf("complete paired suite and negative cases required")
	}
	seen, improved := map[string]bool{}, false
	for i, id := range ids {
		if id == "" || seen[id] || (before[i] != "0" && before[i] != "1") || (after[i] != "0" && after[i] != "1") {
			return fmt.Errorf("invalid paired case")
		}
		seen[id] = true
		if before[i] == "1" && after[i] != "1" {
			return fmt.Errorf("baseline regression: %s", id)
		}
		if negative[id] && after[i] != "1" {
			return fmt.Errorf("negative case failed: %s", id)
		}
		improved = improved || before[i] == "0" && after[i] == "1"
	}
	for id := range negative {
		if !seen[id] {
			return fmt.Errorf("negative case absent: %s", id)
		}
	}
	if !improved {
		return fmt.Errorf("no paired improvement")
	}
	return nil
}
