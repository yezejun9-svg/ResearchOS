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

func w1202DeclaredRows() (asserted map[string]bool, disclosed map[string]bool) {
	asserted, disclosed = map[string]bool{}, map[string]bool{}
	for _, name := range []string{"w1202.go", "w1202_roster.go"} {
		src, e := os.ReadFile(filepath.Join(repoRoot(), "tests", "resources", "check", name))
		if e != nil {
			return nil, nil
		}
		for _, m := range w1202RosterPattern.FindAllStringSubmatch(string(src), -1) {
			if m[1] == "skip" {
				disclosed[m[2]] = true
			} else {
				asserted[m[2]] = true
			}
		}
	}
	return asserted, disclosed
}

func w1202RosterOK() {
	asserted, disclosed := w1202DeclaredRows()
	if len(asserted) < 20 {
		ok("W1202-GUARD-SOURCE-UNREADABLE", true,
			itoa(len(asserted))+" assertion ids parsed from source; refusing to reconcile")
		return
	}
	emitted := map[string]bool{}
	for _, id := range ids {
		emitted[id] = true
	}
	missing, extra := []string{}, []string{}
	for id := range asserted {
		if w1202GuardRows[id] || emitted[id] {
			continue
		}
		missing = append(missing, id)
	}
	for _, id := range ids {
		if !strings.HasPrefix(id, "W1202-") || w1202GuardRows[id] || asserted[id] || disclosed[id] {
			continue
		}
		extra = append(extra, id)
	}
	ok("W1202-ROSTER-COMPLETE-AND-EXACT", len(missing) == 0 && len(extra) == 0,
		"declared but never emitted: "+strings.Join(missing, ","),
		"emitted but undeclared: "+strings.Join(extra, ","),
		itoa(len(asserted))+" asserted in source, "+itoa(len(ids))+" emitted, "+
			itoa(len(disclosed))+" disclosed-only")
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
