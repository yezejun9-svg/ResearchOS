package main

// W12-02 declared-versus-emitted roster reconciliation.
//
// ok() appends its label only when the condition already held, and the phase returns early whenever a
// precondition cannot be built. Both let a row vanish while the report still says PASS with fewer ids -
// the self-certifying-table defect a previous card was rejected for, and exactly what a mutant that makes an
// assertion vacuous relies on. So the roster is read out of this package's own source and reconciled in both
// directions.
//
// Rule: every ok() row must be emitted. A skip() row is the disclosure of an unbuildable precondition and may
// legitimately never fire on a healthy run, so it is checked only the other way - nothing may be emitted that
// no source line declares.

import (
	"os"
	"path/filepath"
	"regexp"
	"strings"
)

var w1202RosterPattern = regexp.MustCompile(`\b(ok|skip)\("(W1202-[A-Z0-9_-]+)"`)

// w1202GuardRows are diagnostics of this file rather than card assertions. They can only fire when the guard
// itself cannot work, so they are exempt from completeness in both directions - stating that here is what
// keeps the guard from manufacturing its own coverage.
var w1202GuardRows = map[string]bool{
	"W1202-GUARD-SOURCE-UNREADABLE":   true,
	"W1202-ROSTER-COMPLETE-AND-EXACT": true,
}

// w1202AnyLiteral catches every W1202- id written anywhere in the source, including ids handed to a helper
// as an argument (orchestrationGraph emits the caller's own admission label). Completeness is still held only
// by the ok() set; this widens what counts as declared so an emitted id cannot be "undeclared" merely because
// it sits in a call argument rather than in an ok() call.
var w1202AnyLiteral = regexp.MustCompile(`"(W1202-[A-Z0-9_-]+)"`)

func w1202DeclaredRows() (asserted map[string]bool, disclosed map[string]bool, declared map[string]bool) {
	asserted, disclosed, declared = map[string]bool{}, map[string]bool{}, map[string]bool{}
	for _, name := range []string{"w1202.go", "w1202_roster.go", "w1202_recovery.go"} {
		src, e := os.ReadFile(filepath.Join(repoRoot(), "tests", "resources", "check", name))
		if e != nil {
			return nil, nil, nil
		}
		for _, m := range w1202AnyLiteral.FindAllStringSubmatch(string(src), -1) {
			declared[m[1]] = true
		}
		for _, m := range w1202RosterPattern.FindAllStringSubmatch(string(src), -1) {
			if m[1] == "skip" {
				disclosed[m[2]] = true
			} else {
				asserted[m[2]] = true
			}
		}
	}
	return asserted, disclosed, declared
}

func w1202RosterOK() {
	asserted, disclosed, declared := w1202DeclaredRows()
	if len(asserted) < 20 {
		ok("W1202-GUARD-SOURCE-UNREADABLE", false,
			itoa(len(asserted))+" assertion ids parsed from source; refusing to reconcile")
		return
	}
	emitted := map[string]bool{}
	for _, id := range ids {
		emitted[id] = true
	}
	// The dispatcher refuses a report with a repeated id, so the guard checks that too: a second call into a
	// helper that emits its own card's witness is exactly how a duplicate sneaks in.
	seen, dupes := map[string]bool{}, []string{}
	for _, id := range ids {
		if seen[id] {
			dupes = append(dupes, id)
		}
		seen[id] = true
	}
	missing, extra := []string{}, []string{}
	for id := range asserted {
		if w1202GuardRows[id] || emitted[id] {
			continue
		}
		missing = append(missing, id)
	}
	for _, id := range ids {
		if !strings.HasPrefix(id, "W1202-") || w1202GuardRows[id] || declared[id] {
			continue
		}
		extra = append(extra, id)
	}
	ok("W1202-ROSTER-COMPLETE-AND-EXACT", len(missing) == 0 && len(extra) == 0 && len(dupes) == 0,
		"declared but never emitted: "+strings.Join(missing, ","),
		"emitted but undeclared: "+strings.Join(extra, ","),
		"emitted more than once: "+strings.Join(dupes, ","),
		itoa(len(asserted))+" asserted in source, "+itoa(len(ids))+" emitted, "+
			itoa(len(disclosed))+" disclosed-only, "+itoa(len(declared))+" declared anywhere")
}

func itoa(n int) string {
	if n <= 0 {
		return "0"
	}
	digits := ""
	for n > 0 {
		digits = string(rune('0'+n%10)) + digits
		n /= 10
	}
	return digits
}
