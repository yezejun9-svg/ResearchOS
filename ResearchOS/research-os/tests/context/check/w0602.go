package main

// w0602.go is the W06-02 half of this construction check: session single-writer ownership, a handoff that cannot
// overtake a producing writer, watermark reconnect completeness and idempotency-keyed writes.
//
// The properties live in internal/domain (session_service.go and its test), because that is where the authoritative
// store is, and this phase runs them through the pinned Go toolchain the same way the accepted W06 fixture harness
// does. Nothing here re-implements the guard: the ids this phase reports are the ids the domain test emits, and a
// row that does not say PASS is recorded as a failure with its own evidence rather than dropped.

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

const w0602TestName = "TestW0602SessionSingleWriterHandoff"

// w0602Roster is the frozen id list for this card. It is deliberately explicit: a test that stops emitting an id
// must show up as a missing row, not as a smaller passing page.
var w0602Roster = []string{
	"W06-02-INDEX-SUBSTRATE-GAP-MEASURED",
	"W06-02-SESSION-OPENED-WITH-EPOCH-ONE",
	"W06-02-READ-ATTACH-CLAIMS-NOTHING",
	"W06-02-TAKEOVER-REFUSED-WHILE-RUN-LIVE",
	"W06-02-REFUSED-TAKEOVER-LEFT-ONE-WRITER",
	"W06-02-STOP-CONFIRM-REFUSED-UNTIL-STORE-SAYS-SETTLED",
	"W06-02-STOP-CONFIRMATION-LANDED-FOR-A-SETTLED-RUN",
	"W06-02-TAKEOVER-AFTER-CONFIRMED-STOP-ADVANCES-EPOCH-ONCE",
	"W06-02-HANDOFF-RECORDED-IN-THE-SAME-STREAM",
	"W06-02-STALE-EPOCH-WRITE-REFUSED",
	"W06-02-NON-WRITER-CLIENT-REFUSED",
	"W06-02-DUPLICATE-COMMAND-CHARGES-ONCE",
	"W06-02-SAME-KEY-DIFFERENT-REQUEST-REFUSED",
	"W06-02-CONCURRENT-CLAIMS-NEVER-LOST-AN-UPDATE",
	"W06-02-RACE-LOSER-CANNOT-WRITE",
	"W06-02-EPOCH-CANNOT-REGRESS",
	"W06-02-RECONNECT-PAGE-REPORTS-ITS-OWN-GAP",
	"W06-02-COMPLETENESS-CLAIM-MATCHES-THE-STREAM",
	"W06-02-WATERMARK-AHEAD-OF-STREAM-REFUSED",
	"W06-02-SESSIONS-SHARING-A-CLIENT-STAY-INDEPENDENT",
	"W06-02-PRINCIPAL-WITHOUT-GRANT-REFUSED",
	"W06-02-ATTACH-BY-PRINCIPAL-WITHOUT-GRANT-REFUSED",
	"W06-02-TAKEOVER-OF-SEALED-SESSION-REFUSED",
	"W06-02-LIST-IS-BOUNDED-AND-HONEST",
}

func (h *harness) w0602Phase(ctx context.Context) {
	goexe := os.Getenv("RESEARCHOS_GO")
	if goexe == "" {
		goexe = filepath.Join(".local", "tools", "go1.27.1", "go", "bin", "go.exe")
	}
	cmd := exec.CommandContext(ctx, goexe, "test", "./internal/domain", "-run", "^"+w0602TestName+"$",
		"-v", "-count=1", "-timeout", "8m")
	cmd.Dir = repoRoot()
	env := os.Environ()
	env = append(env, "GOTOOLCHAIN=local", "GOENV=off")
	cmd.Env = env
	out, err := cmd.Output()
	if err != nil {
		stderr := ""
		if ee, ok := err.(*exec.ExitError); ok {
			stderr = string(ee.Stderr)
		}
		ok("W0602-DOMAIN-CHECK-RAN", false, "go test exited: "+err.Error(), w0602Truncate(stderr, 500))
		return
	}
	ok("W0602-DOMAIN-CHECK-RAN", true)

	type row struct {
		AssertionID string `json:"assertion_id"`
		Status      string `json:"status"`
		Expected    any    `json:"expected"`
		Actual      any    `json:"actual"`
		Evidence    any    `json:"evidence"`
	}
	emitted := map[string]row{}
	malformed := []string{}
	for _, line := range strings.Split(string(out), "\n") {
		if !strings.HasPrefix(line, "W06_ASSERTION ") {
			continue
		}
		var r row
		if e := json.Unmarshal([]byte(strings.TrimPrefix(line, "W06_ASSERTION ")), &r); e != nil {
			malformed = append(malformed, w0602Truncate(line, 200))
			continue
		}
		if r.AssertionID == "" || (r.Status != "PASS" && r.Status != "FAIL") {
			malformed = append(malformed, r.AssertionID)
			continue
		}
		emitted[r.AssertionID] = r
	}
	ok("W0602-ROWS-WELL-FORMED", len(malformed) == 0, malformed)

	present := []string{}
	for _, id := range w0602Roster {
		if _, seen := emitted[id]; seen {
			present = append(present, id)
		}
	}
	missing := []string{}
	for _, want := range w0602Roster {
		if _, seen := emitted[want]; !seen {
			missing = append(missing, want)
		}
	}
	unknown := []string{}
	for id := range emitted {
		found := false
		for _, want := range w0602Roster {
			if id == want {
				found = true
				break
			}
		}
		if !found {
			unknown = append(unknown, id)
		}
	}
	// The roster is checked by set equality, so an id that stopped being emitted cannot be hidden by a longer page.
	ok("W0602-ROSTER-MATCHES-EMITTED-SET", len(missing) == 0 && len(unknown) == 0 && len(present) == len(w0602Roster),
		fmt.Sprintf("present=%d roster=%d", len(present), len(w0602Roster)),
		"missing="+strings.Join(missing, ","), "unknown="+strings.Join(unknown, ","))

	red := []string{}
	for _, id := range w0602Roster {
		if r, seen := emitted[id]; seen && r.Status != "PASS" {
			red = append(red, id+" want="+w0602Truncate(fmt.Sprint(r.Expected), 160)+" got="+w0602Truncate(fmt.Sprint(r.Actual), 160))
		}
	}
	ok("W0602-NO-ROW-RED", len(red) == 0, strings.Join(red, " | "))

	// Every emitted id must belong to this card. A borrowed id from another card would make this selector look
	// stronger than it is, so the prefix rule is asserted rather than assumed.
	foreign := []string{}
	for id := range emitted {
		if !strings.HasPrefix(id, "W06-02-") {
			foreign = append(foreign, id)
		}
	}
	ok("W0602-EMITTED-IDS-ARE-THIS-CARDS", len(foreign) == 0, strings.Join(foreign, ","))

	// Positive control on the two set checks above: the same comparisons must be capable of failing. A roster entry
	// that was not emitted has to show as missing, and an id that is not on the roster has to show as unknown.
	syntheticMissing := []string{}
	for _, want := range append([]string{"W06-02-CONTROL-NAME-THAT-DOES-NOT-EXIST"}, w0602Roster...) {
		if _, seen := emitted[want]; !seen {
			syntheticMissing = append(syntheticMissing, want)
		}
	}
	ok("W0602-MISSING-DETECTION-CONTROL", len(syntheticMissing) == 1 && syntheticMissing[0] == "W06-02-CONTROL-NAME-THAT-DOES-NOT-EXIST",
		strings.Join(syntheticMissing, ","))
	syntheticUnknown := []string{}
	for _, candidate := range append(w0602Roster, "W04-01-Foreign-Id") {
		found := false
		for _, want := range w0602Roster {
			if candidate == want {
				found = true
				break
			}
		}
		if !found {
			syntheticUnknown = append(syntheticUnknown, candidate)
		}
	}
	ok("W0602-FOREIGN-DETECTION-CONTROL", len(syntheticUnknown) == 1 && syntheticUnknown[0] == "W04-01-Foreign-Id",
		strings.Join(syntheticUnknown, ","))

	// Routing: this phase only runs for the selector this card owns, which is what keeps the already accepted
	// W04-01 and W04-02 answers identical after this card landed.
	ok("W0602-ROUTING-SELECTOR-OWNED", os.Getenv("RESEARCHOS_CHECK_ID") == "W06-02" && servedChecks["W06-02"],
		"check_id="+os.Getenv("RESEARCHOS_CHECK_ID"), "served="+fmt.Sprint(servedChecks["W06-02"]))

	for _, id := range w0602Roster {
		if r, seen := emitted[id]; seen && r.Status == "PASS" {
			ok(id, true)
		} else {
			ok(id, false, "row did not report PASS")
		}
	}
}

func w0602Truncate(s string, n int) string {
	if len(s) <= n {
		return s
	}
	return s[:n] + "..."
}
