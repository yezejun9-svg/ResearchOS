package domain

import (
	"encoding/json"
	"os"
	"sort"
	"strings"
	"testing"
)

// registryEntry is the subset of a commands.json entry this card's routing rule depends on.
type registryEntry struct {
	State     string              `json:"state"`
	Argv      []string            `json:"argv"`
	Selectors map[string][]string `json:"selectors"`
}

func w0601RegistryRow(t *testing.T, path, key string) registryEntry {
	t.Helper()
	b, e := os.ReadFile(path)
	if e != nil {
		t.Fatalf("%s: %v", path, e)
	}
	var doc struct {
		Commands map[string]registryEntry `json:"commands"`
	}
	if e = json.Unmarshal(b, &doc); e != nil {
		t.Fatalf("%s: %v", path, e)
	}
	entry, ok := doc.Commands[key]
	if !ok {
		t.Fatalf("%s has no %s key", path, key)
	}
	return entry
}

// selectorRows flattens a selectors map into sorted "field:value" rows.
func selectorRows(s map[string][]string) []string {
	rows := []string{}
	for field, values := range s {
		for _, v := range values {
			rows = append(rows, field+":"+v)
		}
	}
	sort.Strings(rows)
	return rows
}

// difference returns rows present in want but absent in have.
func difference(want, have []string) []string {
	h := map[string]bool{}
	for _, x := range have {
		h[x] = true
	}
	missing := []string{}
	for _, x := range want {
		if !h[x] {
			missing = append(missing, x)
		}
	}
	sort.Strings(missing)
	return missing
}

func TestW06CardRoutingTruthTable(t *testing.T) {
	const key = "test.orchestration"
	legacy := w0601RegistryRow(t, "../../execution/commands.json", key)
	v24 := w0601RegistryRow(t, "../../execution/v2.4/commands.json", key)
	legacyRows, v24Rows := selectorRows(legacy.Selectors), selectorRows(v24.Selectors)

	// The dispatcher picks one registry by key (dispatch.py:65 `if key in ...commands`), so adding the v2.4
	// entry re-routes EVERY selector of this key, not only the new one. Nothing pre-existing may be lost.
	shadowed := difference(legacyRows, v24Rows)
	orchestrationAssert(t, "W06-01-ROUTING-V24-SELECTOR-SUPERSET", []string{}, shadowed,
		Object{"legacy_rows": legacyRows, "v24_rows": v24Rows})
	// Positive control: the same comparison must report a removal, otherwise the row above is vacuous.
	control := make([]string, 0, len(v24Rows))
	for _, r := range v24Rows {
		if r != "check_id:W06-G01" {
			control = append(control, r)
		}
	}
	orchestrationAssert(t, "W06-01-ROUTING-SUPERSET-DETECTS-REMOVAL", []string{"check_id:W06-G01"},
		difference(legacyRows, control), Object{"reason": "synthetic shadowing of an accepted selector"})

	// Binding this card may add exactly one selector row and must not widen any other gate for free.
	added := difference(v24Rows, legacyRows)
	orchestrationAssert(t, "W06-01-ROUTING-OWNED-SELECTOR-EXACTLY-W06-01", []string{"check_id:W06-01"}, added,
		Object{"added": added, "not_added": []string{"check_id:W06-G03", "check_id:W12-H04"}})
	// Positive control: an extra widened row is detected by the same comparison.
	orchestrationAssert(t, "W06-01-ROUTING-WIDENING-DETECTED", []string{"check_id:W06-01", "check_id:W06-G03"},
		difference(append(append([]string{}, v24Rows...), "check_id:W06-G03"), legacyRows),
		Object{"reason": "synthetic widening of the live gate selector"})

	// The wrapper's W06-01 branch runs the test names it reads from the frozen roster, so each named function
	// must exist in this package's source: a ghost name would silently drop ids from the card's own gate.
	expected := jsonMap(t, "../../tests/orchestration/expected.json")
	owned := []string{}
	for name, ids := range expected {
		if hasPrefixedID(ids, "W06-01-") {
			owned = append(owned, name)
		}
	}
	sort.Strings(owned)
	source := []string{}
	for _, file := range w0601SourceFiles(t) {
		for name := range expected {
			if strings.Contains(file, "func "+name+"(") {
				source = append(source, name)
			}
		}
	}
	source = dedupeSorted(source)
	orchestrationAssert(t, "W06-01-ROUTING-ROSTER-NAMES-ARE-REAL-TESTS", owned, source,
		Object{"owned_tests": owned, "card_files": len(w0601SourceFiles(t)), "roster_ids": len(allIDs(expected, owned))})
	// Positive control: the same scan reports a name that exists nowhere, otherwise the row above could be
	// satisfied by a scan that always finds everything.
	ghost := append([]string{"TestW06GhostNotInAnySourceFile"}, owned...)
	found := []string{}
	for _, file := range w0601SourceFiles(t) {
		for _, name := range ghost {
			if strings.Contains(file, "func "+name+"(") {
				found = append(found, name)
			}
		}
	}
	orchestrationAssert(t, "W06-01-ROUTING-GHOST-NAME-DETECTED", []string{"TestW06GhostNotInAnySourceFile"},
		difference(ghost, dedupeSorted(found)), Object{"reason": "ghost roster name must be reported missing"})
}

func hasPrefixedID(ids []any, prefix string) bool {
	for _, id := range ids {
		if s, ok := id.(string); ok && strings.HasPrefix(s, prefix) {
			return true
		}
	}
	return false
}

func allIDs(expected map[string][]any, names []string) []string {
	out := []string{}
	for _, name := range names {
		for _, id := range expected[name] {
			if s, ok := id.(string); ok {
				out = append(out, s)
			}
		}
	}
	sort.Strings(out)
	return out
}

func dedupeSorted(in []string) []string {
	seen := map[string]bool{}
	out := []string{}
	for _, x := range in {
		if !seen[x] {
			seen[x] = true
			out = append(out, x)
		}
	}
	sort.Strings(out)
	return out
}

func jsonMap(t *testing.T, path string) map[string][]any {
	t.Helper()
	b, e := os.ReadFile(path)
	if e != nil {
		t.Fatalf("%s: %v", path, e)
	}
	var doc map[string][]any
	if e = json.Unmarshal(b, &doc); e != nil {
		t.Fatalf("%s: %v", path, e)
	}
	return doc
}

// w0601SourceFiles returns the contents of this card's acceptance test files, which are the only place the
// owned roster names may be defined.
func w0601SourceFiles(t *testing.T) []string {
	t.Helper()
	entries, e := os.ReadDir(".")
	if e != nil {
		t.Fatal(e)
	}
	out := []string{}
	for _, entry := range entries {
		name := entry.Name()
		if strings.HasPrefix(name, "acceptance_") && strings.Contains(name, "w0601") && strings.HasSuffix(name, "_test.go") {
			b, e := os.ReadFile(name)
			if e != nil {
				t.Fatalf("%s: %v", name, e)
			}
			out = append(out, string(b))
		}
	}
	if len(out) == 0 {
		t.Fatal("no acceptance*w0601*_test.go source files found")
	}
	return out
}
