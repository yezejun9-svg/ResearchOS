package main

import (
	"encoding/json"
	"os"
	"os/exec"
	"strings"
)

// Require the real HTTP and client witnesses individually. An early return,
// renamed/duplicate assertion or missing client is a failed construction check.
var w1202RecoveryRows = []string{
	"W1202-HTTP-BRANCH-CONTINUES", "W1202-HTTP-RESOLVE-IDEMPOTENT",
	"W1202-HTTP-CONTINUITY", "W1202-HTTP-SINGLE-SWITCH", "W1202-HTTP-OLD-EXECUTOR-REFUSED",
	"W1202-HTTP-UNAUTHORIZED", "W1202-HTTP-WRONG-PURPOSE", "W1202-HTTP-STALE-RUN",
	"W1202-HTTP-UNKNOWN-EFFECT", "W1202-HTTP-PARTIAL-MULTI-TASK", "W1202-HTTP-GENERIC-EVIDENCE",
	"W1202-PUBLIC-CREATE-NOTICE-DEDUP", "W1202-NOTICE-EXACT-RECIPIENTS", "W1202-MERGE-PRESERVES-NEW-CHECKPOINT",
	"W1202-CLI-REAL-HTTP", "W1202-CLI-CONTINUITY", "W1202-CLI-SINGLE-SWITCH",
	"W1202-DESKTOP-CLIENT-REAL-HTTP", "W1202-DESKTOP-CLIENT-CONTINUITY", "W1202-DESKTOP-CLIENT-SINGLE-SWITCH",
}

var w1202ValueRows = []string{
	"W1202-U09-BASELINE-GATES", "W1202-U09-CAS-EVIDENCE", "W1202-U09-THREE-CARDS",
	"W1202-U09-TWO-ROUNDS-REPLAN", "W1202-U09-EARLY-OBSERVATION",
}

func w1202RecoveryPhase() {
	goExe := os.Getenv("RESEARCHOS_GO")
	if goExe == "" {
		goExe = "go"
	}
	cmd := exec.Command(goExe, "test", "./internal/domain", "-run", "^TestW12Recovery", "-count=1", "-v", "-timeout=3m")
	cmd.Dir = repoRoot()
	raw, err := cmd.CombinedOutput()
	// Preserve every observed row in dispatcher stderr, including failing tests.
	os.Stderr.Write(raw)
	ok("W1202-RECOVERY-CHILD-EXIT", err == nil, err)
	seen, malformed := map[string]int{}, false
	for _, line := range strings.Split(string(raw), "\n") {
		if !strings.HasPrefix(line, "W12_ASSERTION ") {
			continue
		}
		var row struct {
			ID       string `json:"assertion_id"`
			Status   string `json:"status"`
			Expected any    `json:"expected"`
			Actual   any    `json:"actual"`
		}
		if json.Unmarshal([]byte(strings.TrimPrefix(line, "W12_ASSERTION ")), &row) != nil || row.ID == "" {
			malformed = true
			continue
		}
		seen[row.ID]++
		if row.Status != "PASS" {
			malformed = true
		}
	}
	complete := len(seen) == len(w1202RecoveryRows)
	for _, id := range w1202RecoveryRows {
		if seen[id] != 1 {
			complete = false
			continue
		}
		if !malformed && err == nil {
			ok(id, true)
		}
	}
	ok("W1202-RECOVERY-EXACT-WITNESSES", complete && !malformed && err == nil, seen)
	w1202ValuePhase()
	skip("W1202-NATIVE-WINDOW-NOT-EXERCISED", "Desktop client module and production bundle are covered; native window lifecycle stays with the Windows acceptance cards")
}

func w1202ValuePhase() {
	cmd := exec.Command("python", "-B", "-X", "utf8", "tests/resources/value_checkpoint_test.py")
	cmd.Dir = repoRoot()
	raw, err := cmd.CombinedOutput()
	os.Stderr.Write(raw)
	lines := strings.Split(strings.TrimSpace(string(raw)), "\n")
	var report struct {
		Status string   `json:"status"`
		IDs    []string `json:"assertion_ids"`
		Count  int      `json:"assertions"`
	}
	valid := len(lines) > 0 && json.Unmarshal([]byte(lines[len(lines)-1]), &report) == nil && err == nil && report.Status == "PASS" && report.Count == len(w1202ValueRows) && len(report.IDs) == len(w1202ValueRows)
	seen := map[string]int{}
	for _, id := range report.IDs {
		seen[id]++
	}
	for _, id := range w1202ValueRows {
		if seen[id] != 1 {
			valid = false
		}
	}
	ok("W1202-U09-CHILD-EXACT-WITNESSES", valid, err, report)
	if valid {
		for _, id := range w1202ValueRows {
			ok(id, true)
		}
	}
}
