// Tests for the W05-02 CLI coding-task engine. The diff is checked two ways: against an exact
// expected rendering, and against the real patch tool - git apply must turn the original file into
// the candidate byte-for-byte, which a decorative diff cannot survive. The write seam is tested for
// the property that matters most on this build: a refused write leaves the file untouched, so no
// path exists by which the CLI could become a second writer.
package main

import (
	"context"
	"encoding/json"
	"errors"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
)

func lockedGit(t *testing.T) string {
	t.Helper()
	root := repoRoot(t)
	raw, err := os.ReadFile(filepath.Join(root, "execution", "toolchains", "locked.json"))
	if err != nil {
		t.Skipf("locked toolchain table unreadable: %v", err)
	}
	var tbl struct {
		Tools struct {
			Git struct {
				Path          string `json:"path"`
				VersionOutput string `json:"version_output"`
			} `json:"git"`
		} `json:"tools"`
	}
	if err := json.Unmarshal(raw, &tbl); err != nil {
		t.Fatalf("locked table is not valid JSON: %v", err)
	}
	p := tbl.Tools.Git.Path
	if p == "" {
		t.Fatal("locked table names no git path; refusing to fall back to PATH")
	}
	if _, err := os.Stat(p); err != nil {
		t.Skipf("pinned git binary is not present: %v", err)
	}
	return p
}

func repoRoot(t *testing.T) string {
	t.Helper()
	wd, err := os.Getwd()
	if err != nil {
		t.Fatal(err)
	}
	return filepath.Dir(filepath.Dir(wd))
}

func TestUnifiedDiffExact(t *testing.T) {
	before := "one\ntwo\nthree\nfour\nfive\nsix\nseven\neight\n"
	after := "one\ntwo\nTWO\nfour\nfive\nsix\nseven\neight\nnine\n"
	got := UnifiedDiff("f.txt", before, after)
	want := "--- a/f.txt\n+++ b/f.txt\n@@ -1,5 +1,5 @@\n one\n two\n-three\n+TWO\n four\n five\n@@ -6,3 +6,4 @@\n six\n seven\n eight\n+nine\n"
	if got != want {
		t.Fatalf("diff rendering changed:\n got:\n%s\nwant:\n%s", got, want)
	}
	if UnifiedDiff("f.txt", before, before) != "--- a/f.txt\n+++ b/f.txt\n" {
		t.Fatal("an unchanged file must produce no hunks")
	}
}

// The patch must be a real patch: git apply has to reproduce the candidate exactly.
func TestUnifiedDiffAppliesWithRealGit(t *testing.T) {
	before := "alpha\nbravo\ncharlie\ndelta\necho\nfoxtrot\ngolf\nhotel\nindia\n"
	after := "alpha\nbravo\nCHARLIE\ndelta\necho\nfoxtrot\ngolf\nhotel\nindia\njuliett\nkilo\n"
	dir := t.TempDir()
	orig := filepath.Join(dir, "f.txt")
	if err := os.WriteFile(orig, []byte(before), 0o600); err != nil {
		t.Fatal(err)
	}
	patch := UnifiedDiff("f.txt", before, after)
	pf := filepath.Join(dir, "change.patch")
	if err := os.WriteFile(pf, []byte(patch), 0o600); err != nil {
		t.Fatal(err)
	}
	git := lockedGit(t)
	// Pin line endings: on Windows git apply otherwise rewrites the applied file to CRLF, which is
	// git's checkout behaviour, not a defect in the patch, and would make a byte-exact claim lie.
	c := exec.Command(git, "-c", "core.autocrlf=false", "-c", "core.eol=lf",
		"-C", dir, "apply", "-p1", "--whitespace=nowarn", "change.patch")
	c.Env = append(os.Environ(), "GIT_CONFIG_NOSYSTEM=1")
	if out, err := c.CombinedOutput(); err != nil {
		t.Fatalf("git apply refused our own diff (%v):\n%s\n--- patch ---\n%s", err, out, patch)
	}
	got, err := os.ReadFile(orig)
	if err != nil {
		t.Fatal(err)
	}
	if string(got) != after {
		t.Fatalf("applied file is not the candidate:\n got %q\nwant %q", got, after)
	}
}

type recordingWriter struct {
	reqs []WriteRequest
	once bool
}

func (w *recordingWriter) Write(_ context.Context, req WriteRequest) (WriteResult, error) {
	w.reqs = append(w.reqs, req)
	h := contentHash(req.Text)
	before := ""
	if req.ExpectedContentHash != nil {
		before = *req.ExpectedContentHash
	}
	return WriteResult{BeforeHash: before, AfterHash: h}, nil
}

func newTask(dir string, w AuthoritativeWriter, checks ...int) *CodingTask {
	i := 0
	return &CodingTask{Dir: dir, Workspace: "ws://test", TaskID: "W05-02", Writer: w,
		MaxRepairs: len(checks),
		Check: func(context.Context, string) (int, string, error) {
			code := 0
			if i < len(checks) {
				code = checks[i]
			} else if len(checks) > 0 {
				code = checks[len(checks)-1]
			}
			i++
			return code, "check attempt " + itoa(i), nil
		}}
}

func itoa(n int) string { return strings.TrimSpace(strings.Repeat("x", 0) + intToString(n)) }

func intToString(n int) string {
	if n == 0 {
		return "0"
	}
	neg := n < 0
	if neg {
		n = -n
	}
	var b []byte
	for n > 0 {
		b = append([]byte{byte('0' + n%10)}, b...)
		n /= 10
	}
	if neg {
		return "-" + string(b)
	}
	return string(b)
}

func TestCodingTaskPassesAndCarriesRealDiff(t *testing.T) {
	dir := t.TempDir()
	rel := "pkg/a.txt"
	_ = os.MkdirAll(filepath.Join(dir, "pkg"), 0o755)
	original := "one\ntwo\n"
	if err := os.WriteFile(filepath.Join(dir, filepath.FromSlash(rel)), []byte(original), 0o600); err != nil {
		t.Fatal(err)
	}
	w := &recordingWriter{}
	task := newTask(dir, w, 0)
	rep, err := task.Run(context.Background(), rel, func(int, string, string) (string, error) {
		return strings.Replace(original, "two", "TWO", 1), nil
	})
	if err != nil {
		t.Fatal(err)
	}
	if rep.Status != "PASS" || len(rep.Attempts) != 1 || rep.RepairsUsed != 0 {
		t.Fatalf("expected a single passing attempt, got %+v", rep)
	}
	if rep.BeforeHash != contentHash(original) || rep.CandidateHash != contentHash(strings.Replace(original, "two", "TWO", 1)) {
		t.Fatal("hashes are not the real sha256 of the bytes read and proposed")
	}
	if !strings.Contains(rep.Diff, "-two") || !strings.Contains(rep.Diff, "+TWO") {
		t.Fatalf("diff does not describe the change: %q", rep.Diff)
	}
	if !strings.Contains(rep.Attempts[0].CheckOutput, "check attempt") {
		t.Fatal("the check output was not captured")
	}
	if len(w.reqs) != 1 || w.reqs[0].CreateIfMissing {
		t.Fatalf("expected one update request, got %+v", w.reqs)
	}
	if w.reqs[0].ExpectedContentHash == nil || *w.reqs[0].ExpectedContentHash != rep.BeforeHash {
		t.Fatal("an update must carry the expected content hash the write is conditioned on")
	}
}

// A failing check must drive a further attempt that actually sees the failure output, and the
// budget must stop it - bounded, not open-ended.
func TestFailingCheckDrivesBoundedRepair(t *testing.T) {
	dir := t.TempDir()
	rel := "a.txt"
	if err := os.WriteFile(filepath.Join(dir, rel), []byte("x\n"), 0o600); err != nil {
		t.Fatal(err)
	}
	seen := []string{}
	w := &recordingWriter{}
	task := newTask(dir, w, 1, 1, 0)
	rep, err := task.Run(context.Background(), rel, func(n int, base, last string) (string, error) {
		seen = append(seen, last)
		return strings.Repeat("x", n) + "\n", nil
	})
	if err != nil {
		t.Fatal(err)
	}
	if rep.Status != "PASS" || len(rep.Attempts) != 3 || rep.RepairsUsed != 2 {
		t.Fatalf("expected 3 attempts with 2 repairs, got %+v", rep)
	}
	if seen[0] != "" || !strings.Contains(seen[1], "check attempt") || !strings.Contains(seen[2], "check attempt") {
		t.Fatalf("the repair proposal did not receive the previous check output: %q", seen)
	}
}

func TestRepairBudgetExhaustsRatherThanLooping(t *testing.T) {
	dir := t.TempDir()
	if err := os.WriteFile(filepath.Join(dir, "a.txt"), []byte("x\n"), 0o600); err != nil {
		t.Fatal(err)
	}
	task := newTask(dir, &recordingWriter{}, 1) // every check fails
	rep, err := task.Run(context.Background(), "a.txt", func(n int, base, _ string) (string, error) {
		return strings.Repeat("x", n) + "\n", nil
	})
	if err != nil {
		t.Fatal(err)
	}
	if rep.Status != "REPAIR_BUDGET_EXHAUSTED" || len(rep.Attempts) != 2 {
		t.Fatalf("expected an exhausted budget after 2 attempts, got %+v", rep)
	}
}

// The property that keeps this engine from becoming a second writer: when the authoritative writer
// refuses, nothing on disk changes and the report says why instead of reporting success.
func TestRefusedWriterLeavesTheFileUntouched(t *testing.T) {
	dir := t.TempDir()
	rel := "a.txt"
	original := "keep\nme\n"
	full := filepath.Join(dir, rel)
	if err := os.WriteFile(full, []byte(original), 0o600); err != nil {
		t.Fatal(err)
	}
	task := newTask(dir, NotRoutedWriter{Reason: "no workspace.write handler"}, 0)
	rep, err := task.Run(context.Background(), rel, func(int, string, string) (string, error) {
		return "overwritten\n", nil
	})
	if err != nil {
		t.Fatal(err)
	}
	if rep.Status != "BLOCKED_WRITE_ROUTE_NOT_ROUTED" {
		t.Fatalf("expected the refusal to be reported, got %q", rep.Status)
	}
	if !strings.Contains(rep.Detail, "workspace.write") {
		t.Fatalf("the report must name the missing route, got %q", rep.Detail)
	}
	if rep.Attempts[0].Written {
		t.Fatal("an attempt whose write was refused may not claim it wrote")
	}
	got, err := os.ReadFile(full)
	if err != nil {
		t.Fatal(err)
	}
	if string(got) != original {
		t.Fatalf("the file was modified despite the refusal: %q", got)
	}
}

// A missing file must be requested as a create with a null expected hash, matching the contract's
// create_if_missing semantics rather than pretending a hash was seen.
func TestCreateRequestCarriesNoExpectedHash(t *testing.T) {
	dir := t.TempDir()
	w := &recordingWriter{}
	task := newTask(dir, w, 0)
	if _, err := task.Run(context.Background(), "new.txt", func(int, string, string) (string, error) {
		return "fresh\n", nil
	}); err != nil {
		t.Fatal(err)
	}
	if len(w.reqs) != 1 || !w.reqs[0].CreateIfMissing || w.reqs[0].ExpectedContentHash != nil {
		t.Fatalf("expected a create with no expected hash, got %+v", w.reqs)
	}
}

func TestCancellationStopsBeforeAnotherAttempt(t *testing.T) {
	dir := t.TempDir()
	if err := os.WriteFile(filepath.Join(dir, "a.txt"), []byte("x\n"), 0o600); err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	task := newTask(dir, &recordingWriter{}, 0)
	rep, err := task.Run(ctx, "a.txt", func(int, string, string) (string, error) { return "y\n", nil })
	if err != nil {
		t.Fatal(err)
	}
	if rep.Status != "CANCELLED" || len(rep.Attempts) != 0 {
		t.Fatalf("a cancelled run must not attempt, got %+v", rep)
	}
}

func TestEngineRefusesToRunWithoutItsDependencies(t *testing.T) {
	dir := t.TempDir()
	if _, err := (&CodingTask{Dir: dir}).Run(context.Background(), "a.txt", func(int, string, string) (string, error) { return "", nil }); err == nil {
		t.Fatal("no writer installed must be an error, not a silent no-op")
	}
	if _, err := (&CodingTask{Dir: dir, Writer: NotRoutedWriter{}}).Run(context.Background(), "a.txt", func(int, string, string) (string, error) { return "", nil }); err == nil {
		t.Fatal("no checker installed must be an error")
	}
	if _, err := (&CodingTask{Dir: dir, Writer: NotRoutedWriter{}, Check: CommandChecker(), MaxRepairs: -1}).Run(
		context.Background(), "a.txt", func(int, string, string) (string, error) { return "", nil }); err == nil {
		t.Fatal("a negative repair budget must be an error")
	}
	if _, _, err := CommandChecker()(context.Background(), dir); err == nil || !strings.Contains(err.Error(), "NO_CHECK_COMMAND_CONFIGURED") {
		t.Fatalf("an empty check command must fail loudly, got %v", err)
	}
}

// A proposal error must surface as an error, never as a zero-assertion "success".
func TestProposalFailureIsAnError(t *testing.T) {
	dir := t.TempDir()
	_ = os.WriteFile(filepath.Join(dir, "a.txt"), []byte("x\n"), 0o600)
	task := newTask(dir, &recordingWriter{}, 0)
	_, err := task.Run(context.Background(), "a.txt", func(int, string, string) (string, error) {
		return "", errors.New("MODEL_REFUSED")
	})
	if err == nil || !strings.Contains(err.Error(), "PROPOSAL_FAILED") {
		t.Fatalf("expected PROPOSAL_FAILED, got %v", err)
	}
}

// A check that cannot start must not look like a check that ran and said no, or an unstartable
// command would drive the repair loop on nothing and the report would pose as a verification.
func TestCheckThatCannotStartIsNotAFailingCheck(t *testing.T) {
	code, out, err := CommandChecker("Z:/definitely/not/a/real/binary.exe")(context.Background(), t.TempDir())
	if err == nil || !strings.Contains(err.Error(), "CHECK_EXEC_FAILED") {
		t.Fatalf("expected CHECK_EXEC_FAILED, got code %d out %q err %v", code, out, err)
	}
	dir := t.TempDir()
	_ = os.WriteFile(filepath.Join(dir, "a.txt"), []byte("x\n"), 0o600)
	task := newTask(dir, &recordingWriter{}, 0)
	task.Check = CommandChecker("Z:/definitely/not/a/real/binary.exe")
	if _, err := task.Run(context.Background(), "a.txt", func(int, string, string) (string, error) { return "y\n", nil }); err == nil ||
		!strings.Contains(err.Error(), "CHECK_EXEC_FAILED") {
		t.Fatalf("the engine must surface the unstartable check as an error, got %v", err)
	}
}

// The opposite side: a command that really runs and really fails must be captured as an exit code
// with no error, because that is the signal a bounded repair is supposed to react to.
func TestCheckThatFailsIsCapturedAsAnExitCode(t *testing.T) {
	dir := t.TempDir()
	git := lockedGit(t)
	code, out, err := CommandChecker(git, "-C", dir, "rev-parse", "--verify", "HEAD")(context.Background(), dir)
	if err != nil {
		t.Fatalf("a running check must not error: %v (%s)", err, out)
	}
	if code == 0 {
		t.Fatalf("expected a non-zero exit from git rev-parse in a non-repository, got 0 (%s)", out)
	}
	if out == "" {
		t.Fatal("the failing check produced no captured output to drive a repair")
	}
}

var _ = io.Discard
