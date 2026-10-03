package main

// Forwarding keeps binding W05-01 to the name test.runtime from shadowing the selectors that the
// accepted v2.0 harness already serves: task_id W12 and case_id C11 route to ops/ci/runtime.py
// unchanged. The rule is asserted as data, so an edit that silently swallows an accepted selector
// fails a named assertion instead of quietly returning NOT_IMPLEMENTED.

import (
	"os"
	"os/exec"
)

// servedChecks names the cards this program answers itself. W05-02 was added by W05-02; anything not
// listed here is forwarded to the accepted legacy harness, so a selector this program cannot serve is
// never answered with another card's assertions.
var servedChecks = map[string]bool{"W05-01": true, "W05-02": true}

func routesToLegacy(check, caseID, taskID string) bool {
	if servedChecks[check] {
		return false
	}
	return check != "" || caseID != "" || taskID != ""
}

func routeLegacy() (int, bool) {
	check := os.Getenv("RESEARCHOS_CHECK_ID")
	caseID := os.Getenv("RESEARCHOS_CASE_ID")
	taskID := os.Getenv("RESEARCHOS_TASK_ID")
	if !routesToLegacy(check, caseID, taskID) {
		return 0, false
	}
	cmd := exec.Command("python", "-X", "utf8", "ops/ci/runtime.py", "--mode", "fixture")
	cmd.Env = os.Environ()
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if e := cmd.Run(); e != nil {
		if exit, isExit := e.(*exec.ExitError); isExit {
			return exit.ExitCode(), true
		}
		return 3, true
	}
	return 0, true
}

func routingTruthTableOK() {
	rows := []struct {
		task, check, caseID string
		legacy              bool
		why                 string
	}{
		{"W05", "W05-01", "", false, "this card is served by this program"},
		{"W12", "W05-G01", "", true, "an accepted W05 check id stays with the legacy harness"},
		{"W12", "", "C11", true, "case C11 stays with the legacy harness"},
		{"W12", "", "", true, "the bare task selector stays with the legacy harness"},
		{"", "", "A04", true, "the live case stays with the legacy harness, which gates it on RESEARCHOS_RUNTIME_LIVE"},
	}
	bad := []string{}
	for _, r := range rows {
		if got := routesToLegacy(r.check, r.caseID, r.task); got != r.legacy {
			bad = append(bad, r.why+" routed "+boolText(got)+" want "+boolText(r.legacy))
		}
	}
	ok("W0501-ROUTING-TRUTH-TABLE", len(bad) == 0, bad)
}

func boolText(b bool) string {
	if b {
		return "legacy"
	}
	return "served"
}
