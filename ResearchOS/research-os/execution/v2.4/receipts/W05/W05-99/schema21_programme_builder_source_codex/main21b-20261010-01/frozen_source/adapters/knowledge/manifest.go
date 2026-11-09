package knowledge

import "fmt"

// Outcome is one extractor result for one frozen source revision. A zero exit
// status is deliberately absent: process success says nothing about coverage.
type Outcome struct {
	SourceID  string
	Processed bool
	Failure   string
}

type Coverage struct {
	Status    string
	Processed []string
	Failed    []string
}

func Reconcile(expected []string, outcomes []Outcome) (Coverage, error) {
	if len(expected) == 0 {
		return Coverage{}, fmt.Errorf("expected source manifest is empty")
	}
	seen := make(map[string]bool, len(expected))
	for _, id := range expected {
		if id == "" || seen[id] {
			return Coverage{}, fmt.Errorf("empty or duplicate expected source")
		}
		seen[id] = true
	}
	if len(outcomes) != len(expected) {
		return Coverage{}, fmt.Errorf("one extraction outcome required per source")
	}
	got := make(map[string]bool, len(outcomes))
	c := Coverage{Status: "COMPLETE", Processed: []string{}, Failed: []string{}}
	for _, o := range outcomes {
		if !seen[o.SourceID] || got[o.SourceID] || o.Processed && o.Failure != "" || !o.Processed && o.Failure == "" {
			return Coverage{}, fmt.Errorf("invalid source extraction outcome")
		}
		got[o.SourceID] = true
		if o.Processed {
			c.Processed = append(c.Processed, o.SourceID)
		} else {
			c.Failed = append(c.Failed, o.SourceID)
			c.Status = "PARTIAL"
		}
	}
	return c, nil
}
