package evolution

import "fmt"

// These values live in the protected fixture store. They are not the public
// development Suite and are never part of a candidate request together.
const HoldoutRevision = "private-c20-fixture-v1"
const HoldoutReleaseRevision = "private-r2-fixture-v1"

func ValidHoldoutRevision(revision string) bool {
	return revision == HoldoutRevision || revision == HoldoutReleaseRevision
}

type HoldoutInputs struct {
	Revision string `json:"revision"`
	Cases    []Case `json:"cases"`
}

type HoldoutLabel struct {
	ID       string `json:"id"`
	Expected int    `json:"expected"`
}

type HoldoutLabels struct {
	Revision string         `json:"revision"`
	Labels   []HoldoutLabel `json:"labels"`
}

// ValidateHoldout makes the objective labels independently recomputable and
// refuses reuse of any public development case ID.
func ValidateHoldout(inputs HoldoutInputs, labels HoldoutLabels) error {
	if !ValidHoldoutRevision(inputs.Revision) || labels.Revision != inputs.Revision || len(inputs.Cases) < 2 || len(inputs.Cases) != len(labels.Labels) {
		return fmt.Errorf("frozen private C20 input/label count or revision invalid")
	}
	public := map[string]bool{}
	for _, c := range Suite() {
		public[c.Input.ID] = true
	}
	seen := map[string]bool{}
	for i, c := range inputs.Cases {
		expected := c.A + c.B
		validOperation := c.Operation == "add"
		if inputs.Revision == HoldoutReleaseRevision && c.Operation == "multiply" {
			expected = c.A * c.B
			validOperation = true
		}
		if c.ID == "" || seen[c.ID] || public[c.ID] || !validOperation || c.Text != "" || labels.Labels[i].ID != c.ID || labels.Labels[i].Expected != expected {
			return fmt.Errorf("private C20 case %d is public, duplicate, or not objectively labeled", i)
		}
		seen[c.ID] = true
	}
	return nil
}
