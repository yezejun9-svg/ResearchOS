// w0502.go is the W05-02 construction suite: it builds the real CLI with the pinned toolchain and
// drives it as a subprocess, so every assertion below is about observable behaviour - the diff text
// it prints, the exit code it returns, the bytes on disk before and after - not about internal
// function calls. This card's write step is blocked (workspace.write has no domain handler), and the
// suite asserts that refusal as the required behaviour: a run whose write was refused must report it,
// must exit non-zero, and must leave the target file byte-identical.
package main

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"

	rosruntime "researchos.local/research-os/adapters/runtime"
)

// lockedGo resolves Go from execution/toolchains/locked.json and verifies the digest, refusing to
// fall back to PATH. A suite that built with whatever `go` was on PATH could pass on a host that the
// pinned toolchain would reject.
func lockedGo(t string) (string, string) {
	root := repoRoot()
	raw, e := os.ReadFile(filepath.Join(root, "execution", "toolchains", "locked.json"))
	if e != nil {
		return "", "locked toolchain table unreadable: " + e.Error()
	}
	var tbl struct {
		Tools struct {
			Go struct {
				Path   string `json:"path"`
				Sha256 string `json:"sha256"`
			} `json:"go"`
		} `json:"tools"`
	}
	if e := json.Unmarshal(raw, &tbl); e != nil {
		return "", "locked table is not valid JSON: " + e.Error()
	}
	p := tbl.Tools.Go.Path
	if p == "" {
		return "", "locked table names no go path"
	}
	b, e := os.ReadFile(p)
	if e != nil {
		return "", "pinned go binary missing: " + e.Error()
	}
	sum := sha256.Sum256(b)
	if hex.EncodeToString(sum[:]) != tbl.Tools.Go.Sha256 {
		return "", "pinned go binary hash does not match the locked table"
	}
	return p, "verified"
}

func digestFile(p string) string {
	b, e := os.ReadFile(p)
	if e != nil {
		return "UNREADABLE:" + e.Error()
	}
	sum := sha256.Sum256(b)
	return hex.EncodeToString(sum[:])
}

type cliRun struct {
	stdout   string
	stderr   string
	exitCode int
	couldRun bool
}

func runCLI(bin string, dir string, args ...string) cliRun {
	cmd := exec.Command(bin, args...)
	cmd.Dir = dir
	cmd.Env = os.Environ()
	var so, se strings.Builder
	cmd.Stdout = &so
	cmd.Stderr = &se
	e := cmd.Run()
	code := 0
	if ee, isExit := e.(*exec.ExitError); isExit {
		code = ee.ExitCode()
	} else if e != nil {
		return cliRun{stdout: so.String(), stderr: se.String() + " | spawn: " + e.Error(), exitCode: -1, couldRun: false}
	}
	return cliRun{stdout: so.String(), stderr: se.String(), exitCode: code, couldRun: true}
}

func lastJSONLine(s string) map[string]any {
	lines := strings.Split(strings.TrimRight(s, "\n"), "\n")
	for i := len(lines) - 1; i >= 0; i-- {
		t := strings.TrimSpace(lines[i])
		if strings.HasPrefix(t, "{") {
			var m map[string]any
			if json.Unmarshal([]byte(t), &m) == nil {
				return m
			}
		}
	}
	return map[string]any{}
}

func firstAttempt(rep map[string]any) map[string]any {
	if a, okA := rep["attempts"].([]any); okA && len(a) > 0 {
		if m, okM := a[0].(map[string]any); okM {
			return m
		}
	}
	return map[string]any{}
}

// cliPhaseW0502 owns every W0502-* assertion. It is called only for this card's selector so the two
// suites can never lend each other's assertion ids.
func cliPhaseW0502(ctx context.Context) {
	routingW0502OK()
	gp, why := lockedGo("go")
	ok("W0502-TOOLCHAIN-GO-FROM-LOCKED-TABLE", gp != "", why)
	if gp == "" {
		notVerified = append(notVerified, "the whole W05-02 suite: the pinned go binary was unavailable, so nothing was built or run")
		return
	}
	tmp, e := os.MkdirTemp("", "w0502-cli-")
	if e != nil {
		ok("W0502-SANDBOX-CREATED", false, e)
		return
	}
	defer os.RemoveAll(tmp)
	bin := filepath.Join(tmp, "roscli.exe")
	build := exec.Command(gp, "build", "-o", bin, "./apps/cli")
	build.Dir = repoRoot()
	build.Env = append(os.Environ(), "GOTOOLCHAIN=local", "GOFLAGS=-buildvcs=false")
	bOut, bErr := build.CombinedOutput()
	built := bErr == nil
	ok("W0502-CLI-BUILDS-WITH-PINNED-GO", built, string(bOut), fmt.Sprint(bErr))
	if !built {
		notVerified = append(notVerified, "every W05-02 CLI behaviour assertion: the binary did not build")
		return
	}

	work := filepath.Join(tmp, "work")
	_ = os.MkdirAll(filepath.Join(work, "sub"), 0o755)
	target := filepath.Join(work, "sub", "a.txt")
	original := "one\ntwo\nthree\n"
	if e = os.WriteFile(target, []byte(original), 0o600); e != nil {
		ok("W0502-FIXTURE-WRITTEN", false, e)
		return
	}
	ok("W0502-FIXTURE-WRITTEN", true, len(original))
	before := digestFile(target)

	// The check command is itself a pinned binary, invoked with an argument it cannot misread.
	verdict := runCLI(bin, work, "task", "-dir", work, "-file", "sub/a.txt",
		"-replace", "two=>TWO", "-check", gp+" env GOVERSION")
	rep := lastJSONLine(verdict.stdout)
	ok("W0502-TASK-RUN-COMPLETES", verdict.couldRun, verdict.stderr)

	diff := stringOf(rep["diff"])
	hasHunk := strings.Contains(diff, "@@ -1,3 +1,3 @@")
	hasRemoval := strings.Contains(diff, "\n-two\n")
	hasAddition := strings.Contains(diff, "\n+TWO\n")
	unchangedLines := strings.Contains(diff, " one\n") && strings.Contains(diff, " three\n")
	ok("W0502-DIFF-IS-A-REAL-UNIFIED-HUNK", hasHunk && hasRemoval && hasAddition && unchangedLines, diff)

	att := firstAttempt(rep)
	outStr := stringOf(att["check_output"])
	code, _ := att["check_exit"].(float64)
	checkRan := att["check_exit"] != nil && int(code) == 0 && strings.HasPrefix(strings.TrimSpace(outStr), "go1.")
	ok("W0502-CHECK-COMMAND-REALLY-RAN", checkRan, int(code), outStr)
	// A check that could not start must never be recorded as a passing check.
	ok("W0502-CHECK-EXIT-CODE-IS-CAPTURED-NOT-INVENTED",
		att["check_exit"] != nil && !strings.Contains(stringOf(att["write_error"]), "CHECK_EXEC_FAILED"), att)

	status := stringOf(rep["status"])
	written, _ := att["written"].(bool)
	ok("W0502-REFUSED-WRITE-IS-REPORTED-NOT-PASSED",
		status == "BLOCKED_WRITE_ROUTE_NOT_ROUTED" && !written && verdict.exitCode == 3, status, verdict.exitCode, written)
	ok("W0502-REFUSAL-NAMES-THE-MISSING-ROUTE",
		strings.Contains(stringOf(att["write_error"]), "workspace.write") &&
			strings.Contains(stringOf(rep["detail"]), "workspace.write"), rep["detail"])
	after := digestFile(target)
	ok("W0502-REFUSED-WRITE-LEAVES-THE-BYTES-IDENTICAL", before == after, before, after)
	// The card's first negative, in the form this build can actually produce: a candidate exists
	// (a real diff was shown) while nothing reached disk.
	candHash := stringOf(rep["candidate_hash"])
	ok("W0502-CANDIDATE-EXISTS-WITHOUT-TOUCHING-DISK",
		strings.HasPrefix(candHash, "sha256:") && candHash != "sha256:"+before && !written, candHash, before)

	missing := runCLI(bin, work, "task", "-dir", work, "-file", "sub/a.txt",
		"-replace", "not-there=>X", "-check", gp+" env GOVERSION")
	ok("W0502-MISSING-PATTERN-FAILS-LOUDLY",
		missing.exitCode != 0 && strings.Contains(missing.stdout, "PATTERN_NOT_FOUND"), missing.exitCode, firstLine(missing.stdout))
	ok("W0502-MISSING-PATTERN-LEFT-THE-BYTES-ALONE", digestFile(target) == before, digestFile(target))

	negative := runCLI(bin, work, "task", "-dir", work, "-file", "sub/a.txt",
		"-replace", "two=>TWO", "-check", gp+" env GOVERSION", "-repairs", "-1")
	ok("W0502-NEGATIVE-REPAIR-BUDGET-IS-REFUSED",
		negative.exitCode == 2 && strings.Contains(negative.stdout, "INVALID_REQUEST"), negative.exitCode, firstLine(negative.stdout))

	noCheck := runCLI(bin, work, "task", "-dir", work, "-file", "sub/a.txt", "-replace", "two=>TWO")
	ok("W0502-TASK-WITHOUT-A-CHECK-IS-REFUSED",
		noCheck.exitCode == 2 && strings.Contains(noCheck.stdout, "-check is required"), noCheck.exitCode, firstLine(noCheck.stdout))

	unimpl := runCLI(bin, work, "task", "-dir", work, "-file", "sub/a.txt",
		"-replace", "two=>TWO", "-check", filepath.Join(tmp, "no-such-check-exe"))
	ok("W0502-UNCHECKABLE-CHECK-IS-NOT-A-FAILING-CHECK",
		unimpl.exitCode != 0 && (strings.Contains(unimpl.stdout, "CHECK_EXEC_FAILED") || strings.Contains(unimpl.stderr, "CHECK_EXEC_FAILED")),
		unimpl.exitCode, firstLine(unimpl.stdout), firstLine(unimpl.stderr))
	ok("W0502-BAD-CHECK-LEFT-THE-BYTES-ALONE", digestFile(target) == before, digestFile(target))

	untouched := runCLI(bin, work, "chat")
	ok("W0502-UNIMPLEMENTED-COMMAND-STILL-REFUSES", untouched.exitCode == 3 &&
		strings.Contains(untouched.stdout, "NOT_IMPLEMENTED"), untouched.exitCode, firstLine(untouched.stdout))

	// Help must list what actually runs and keep naming what does not, so the surface cannot
	// overclaim by omission.
	help := runCLI(bin, work, "help")
	ok("W0502-HELP-LISTS-TASK-AND-STILL-NAMES-UNIMPLEMENTED-COMMANDS",
		help.exitCode == 0 && strings.Contains(help.stdout, "task") &&
			strings.Contains(help.stdout, "NOT_IMPLEMENTED") && strings.Contains(help.stdout, "chat"),
		help.exitCode, help.stdout)

	cancelCascadeW0502(bin, tmp)

	// The namespace property: whatever this run emitted, none of it may be W05-01's.
	own := 0
	for _, i := range ids {
		if strings.HasPrefix(i, "W0502-") {
			own++
		}
	}
	lent := []string{}
	for _, i := range ids {
		if strings.HasPrefix(i, "W0501-") {
			lent = append(lent, i)
		}
	}
	ok("W0502-SUITE-EMITS-ONLY-ITS-OWN-ASSERTION-IDS", own > 0 && len(lent) == 0, lent)
}

func stringOf(v any) string {
	s, _ := v.(string)
	return s
}

func firstLine(s string) string {
	s = strings.TrimSpace(s)
	if i := strings.IndexByte(s, '\n'); i >= 0 {
		return s[:i]
	}
	return s
}

// routingW0502OK asserts this card's routing as data, under this card's own id: the selector the
// dispatcher forwards either has a suite here or is forwarded to the legacy harness, and an id nobody
// serves must never be answered with another card's assertions.
func routingW0502OK() {
	rows := []struct {
		task, check, caseID string
		legacy              bool
		why                 string
	}{
		{"W05", "W05-02", "", false, "this card is served by this program"},
		{"W05", "W05-01", "", false, "the accepted W05-01 id stays served by this program"},
		{"W12", "W05-G01", "", true, "an accepted W12 check id stays with the legacy harness"},
		{"W12", "", "C11", true, "case C11 stays with the legacy harness"},
		{"", "", "A04", true, "the live case stays with the legacy harness"},
		{"W05", "W99-DOES-NOT-EXIST", "", true, "an id with no suite here is forwarded, never borrowed"},
	}
	bad := []string{}
	for _, r := range rows {
		if got := routesToLegacy(r.check, r.caseID, r.task); got != r.legacy {
			bad = append(bad, r.why+" routed "+boolText(got)+" want "+boolText(r.legacy))
		}
	}
	ok("W0502-SELECTOR-ROUTING-IS-DATA-NOT-ACCIDENT", len(bad) == 0, bad)
}

// cancelCascadeW0502 drives card step 4 from the outside: a real worker writing a real file, a real
// cancel, then the claim that matters - nothing wrote afterwards. Every absence here is paired with a
// positive control, because "the file stopped growing" is worthless unless it was proven to be growing
// in the first place.
func cancelCascadeW0502(bin, tmp string) {
	dir := filepath.Join(tmp, "cancel")
	if e := os.MkdirAll(dir, 0o755); e != nil {
		ok("W0502-CANCEL-SANDBOX", false, e)
		return
	}
	ok("W0502-CANCEL-SANDBOX", true, dir)
	r := runCLI(bin, dir, "run", "-dir", dir, "-job", "ros-w0502-cascade", "-queue", "3",
		"-cancel-after", "350ms", "-observe-after", "400ms", "-settle", "8s")
	rep := lastJSONLine(r.stdout)
	order := []string{}
	if v, isList := rep["order"].([]any); isList {
		for _, x := range v {
			if s, isStr := x.(string); isStr {
				order = append(order, s)
			}
		}
	}
	num := func(k string) int { f, _ := rep[k].(float64); return int(f) }
	arr, _ := rep["remaining_pids"].([]any)
	ticks := num("ticks_at_cancel")
	ok("W0502-CASCADE-RUNS-IN-REQUIRED-ORDER",
		len(order) >= 4 && order[0] == "clear_queue" && order[1] == "abort" &&
			order[2] == "settled" && order[3] == "child_confirmed", order, r.exitCode)
	ok("W0502-WORKER-WAS-REALLY-WRITING-BEFORE-THE-CANCEL", ticks > 0 && num("worker_pid") > 0, ticks, num("worker_pid"))
	ok("W0502-JOB-SETTLES-EMPTY-WITH-A-REAL-EXIT-CODE",
		rep["settled"] == true && len(arr) == 0 && num("worker_exit_code") == 137,
		rep["settled"], arr, num("worker_exit_code"))
	ok("W0502-QUEUED-WORK-IS-DROPPED-RATHER-THAN-RUN", num("queued_dropped") == 3, num("queued_dropped"))
	ok("W0502-WORKER-WRITES-NOTHING-AFTER-SETTLEMENT",
		num("writes_after_cancel") == 0 && num("ticks_after_settle") == ticks && r.exitCode == 0,
		num("writes_after_cancel"), ticks, num("ticks_after_settle"), r.exitCode)

	orphan := filepath.Join(tmp, "orphan")
	_ = os.MkdirAll(orphan, 0o755)
	cmd := exec.Command(bin, "run", "-dir", orphan, "-job", "ros-w0502-orphan", "-queue", "5",
		"-cancel-after", "30s", "-observe-after", "0s", "-settle", "8s")
	cmd.Dir = orphan
	if e := cmd.Start(); e != nil {
		ok("W0502-ORPHAN-PARENT-STARTED", false, e)
		return
	}
	ok("W0502-ORPHAN-PARENT-STARTED", true, cmd.Process.Pid)
	tf := filepath.Join(orphan, "worker-ticks.log")
	wrote := 0
	deadline := time.Now().Add(8 * time.Second)
	for time.Now().Before(deadline) {
		if s, e := os.Stat(tf); e == nil && s.Size() > 0 {
			wrote = int(s.Size())
			break
		}
		time.Sleep(50 * time.Millisecond)
	}
	ok("W0502-ORPHAN-WORKER-WAS-WRITING-BEFORE-THE-PARENT-DIED", wrote > 0, wrote)
	_ = cmd.Process.Kill()
	_, _ = cmd.Process.Wait()
	atDeath := wrote
	if s, e := os.Stat(tf); e == nil {
		atDeath = int(s.Size())
	}
	time.Sleep(1500 * time.Millisecond)
	later := atDeath
	if s, e := os.Stat(tf); e == nil {
		later = int(s.Size())
	}
	ok("W0502-NO-ORPHAN-WRITE-AFTER-THE-PARENT-DIES", later == atDeath, atDeath, later)

	in, e1 := os.Open(os.DevNull)
	out, e2 := os.Create(filepath.Join(tmp, "order-stdout.log"))
	errFile, e3 := os.Create(filepath.Join(tmp, "order-stderr.log"))
	if e1 != nil || e2 != nil || e3 != nil {
		ok("W0502-ORDER-GUARD-HANDLES", false, e1, e2, e3)
		return
	}
	child, e := rosruntime.StartChild("ros-w0502-order", rosruntime.Command{
		Executable: bin,
		Args:       []string{"worker", "-file", filepath.Join(tmp, "order-ticks.log"), "-every", "40ms"},
		Directory:  tmp}, os.Environ(), out, errFile, in)
	if e != nil {
		ok("W0502-CANCEL-REFUSED-BEFORE-THE-QUEUE-WAS-CLEARED", false, "child did not start: "+e.Error())
		in.Close()
		out.Close()
		errFile.Close()
		return
	}
	_, e = child.Cancel(2 * time.Second)
	ok("W0502-CANCEL-REFUSED-BEFORE-THE-QUEUE-WAS-CLEARED",
		e != nil && strings.Contains(e.Error(), "CANCEL_ORDER_VIOLATED"), e)
	child.ClearQueue()
	late := child.Admit("after-clear")
	ok("W0502-QUEUE-REFUSES-ADMISSION-AFTER-CLEAR",
		late != nil && strings.Contains(late.Error(), "CANCEL_ORDER_VIOLATED"), late)
	_, e = child.Cancel(2 * time.Second)
	ok("W0502-CASCADE-COMPLETES-ONCE-THE-ORDER-IS-HONOURED", e == nil, e)
	child.Close()
}
