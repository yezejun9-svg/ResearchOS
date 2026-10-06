// coding_task.go is the CLI-side coding-task engine for W05-02: it really reads a file from disk,
// really renders a unified diff of the proposed change, really runs a check command and captures its
// exit code, and lets a failing check drive a bounded number of repairs.
//
// It deliberately contains no file-writing code path. Every mutation is offered to an
// AuthoritativeWriter, and the only production implementation on this build refuses with
// ErrWriteRouteNotRouted, because internal/domain routes no workspace.write handler yet (see
// execution/v2.4/receipts/W05/W05-02/HANDLER_LOCATION.md). A local os.WriteFile fallback would
// create exactly the second writer that W05-02 step 3 exists to prevent, so there is none to remove.
package main

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
)

// ErrWriteRouteNotRouted names the absence rather than hiding it behind a generic error, so a
// caller can distinguish "the product refused" from "this engine broke".
var ErrWriteRouteNotRouted = errors.New("NOT_IMPLEMENTED: workspace.write has no handler on this host build")

// WriteRequest mirrors the frozen WorkspaceWritePayload field-for-field (client.protocol.schema.json
// $defs.WorkspaceWritePayload) so the seam does not need a translation layer once the domain route
// exists. ExpectedContentHash is nil only when CreateIfMissing is set, matching the contract's
// "sha256:... or null" and the create-only reading of create_if_missing.
type WriteRequest struct {
	WorkspaceRef        string
	RelativePath        string
	TaskID              string
	ExpectedContentHash *string
	Text                string
	CreateIfMissing     bool
}

type WriteResult struct {
	BeforeHash string
	AfterHash  string
}

type AuthoritativeWriter interface {
	Write(ctx context.Context, req WriteRequest) (WriteResult, error)
}

// NotRoutedWriter is the production writer on this build: it refuses, and it refuses the same way
// for every request, so no input can talk it into a write.
type NotRoutedWriter struct{ Reason string }

func (w NotRoutedWriter) Write(_ context.Context, req WriteRequest) (WriteResult, error) {
	if w.Reason != "" {
		return WriteResult{}, fmt.Errorf("%w (%s)", ErrWriteRouteNotRouted, w.Reason)
	}
	return WriteResult{}, ErrWriteRouteNotRouted
}

// Checker runs a real verification command in a real directory and reports its exit code plus
// combined output. A nil error means the process ran; a non-zero exit is a failing check, not a
// failure to check.
type Checker func(ctx context.Context, dir string) (exitCode int, output string, err error)

func CommandChecker(argv ...string) Checker {
	return func(ctx context.Context, dir string) (int, string, error) {
		if len(argv) == 0 {
			return -1, "", errors.New("NO_CHECK_COMMAND_CONFIGURED")
		}
		cmd := exec.CommandContext(ctx, argv[0], argv[1:]...)
		cmd.Dir = dir
		out, err := cmd.CombinedOutput()
		var ee *exec.ExitError
		if errors.As(err, &ee) {
			// The check ran and said no. That is a failing check, not a failure to check.
			return ee.ExitCode(), string(out), nil
		}
		if err != nil {
			// The check never ran. Reporting exit -1 here would let an unstartable command pose as
			// a failing verification and drive the repair loop on nothing.
			return -1, string(out), fmt.Errorf("CHECK_EXEC_FAILED: %w", err)
		}
		return 0, string(out), nil
	}
}

type Attempt struct {
	Number      int    `json:"number"`
	Diff        string `json:"diff"`
	CheckExit   int    `json:"check_exit"`
	CheckOutput string `json:"check_output"`
	Written     bool   `json:"written"`
	WriteError  string `json:"write_error,omitempty"`
}

type TaskReport struct {
	RelativePath  string    `json:"relative_path"`
	BeforeHash    string    `json:"before_hash"`
	CandidateHash string    `json:"candidate_hash"`
	Diff          string    `json:"diff"`
	Attempts      []Attempt `json:"attempts"`
	RepairsUsed   int       `json:"repairs_used"`
	Status        string    `json:"status"`
	Detail        string    `json:"detail,omitempty"`
	ElapsedMS     int64     `json:"elapsed_ms"`
}

// Propose builds the candidate content for one attempt. It receives the previous attempt's check
// output so a failing check can actually drive the next edit, which is what makes the repair bounded
// rather than merely repeated.
type Propose func(attempt int, base string, lastCheckOutput string) (string, error)

type CodingTask struct {
	Dir        string
	Workspace  string
	TaskID     string
	Writer     AuthoritativeWriter
	Check      Checker
	MaxRepairs int
}

func (t *CodingTask) Run(ctx context.Context, rel string, propose Propose) (TaskReport, error) {
	if t.Writer == nil {
		return TaskReport{}, errors.New("NO_AUTHORITATIVE_WRITER_INSTALLED")
	}
	if t.Check == nil {
		return TaskReport{}, errors.New("NO_CHECKER_INSTALLED")
	}
	if t.MaxRepairs < 0 {
		return TaskReport{}, errors.New("NEGATIVE_REPAIR_BUDGET")
	}
	started := time.Now()
	abs := filepath.Join(t.Dir, filepath.FromSlash(rel))
	raw, err := os.ReadFile(abs)
	existed := err == nil
	if err != nil && !errors.Is(err, os.ErrNotExist) {
		return TaskReport{}, fmt.Errorf("READ_FAILED: %w", err)
	}
	base := string(raw)
	rep := TaskReport{RelativePath: rel, BeforeHash: contentHash(base), Status: "RUNNING"}
	var lastOut string
	budget := t.MaxRepairs + 1
	for n := 1; n <= budget; n++ {
		if cErr := ctx.Err(); cErr != nil {
			rep.Status = "CANCELLED"
			rep.Detail = cErr.Error()
			rep.ElapsedMS = time.Since(started).Milliseconds()
			return rep, nil
		}
		cand, pErr := propose(n, base, lastOut)
		if pErr != nil {
			return rep, fmt.Errorf("PROPOSAL_FAILED: %w", pErr)
		}
		diff := UnifiedDiff(rel, base, cand)
		rep.CandidateHash = contentHash(cand)
		rep.Diff = diff
		var want *string
		if existed {
			h := rep.BeforeHash
			want = &h
		}
		written := false
		writeErr := ""
		_, wErr := t.Writer.Write(ctx, WriteRequest{
			WorkspaceRef: t.Workspace, RelativePath: rel, TaskID: t.TaskID,
			ExpectedContentHash: want, Text: cand, CreateIfMissing: !existed,
		})
		if wErr == nil {
			written = true
		} else {
			writeErr = wErr.Error()
		}
		code, out, cErr := t.Check(ctx, t.Dir)
		if cErr != nil {
			return rep, fmt.Errorf("CHECK_EXEC_FAILED: %w", cErr)
		}
		rep.Attempts = append(rep.Attempts, Attempt{Number: n, Diff: diff, CheckExit: code,
			CheckOutput: out, Written: written, WriteError: writeErr})
		if n > 1 {
			rep.RepairsUsed = n - 1
		}
		if !written {
			rep.Status = "BLOCKED_WRITE_ROUTE_NOT_ROUTED"
			rep.Detail = writeErr
			rep.ElapsedMS = time.Since(started).Milliseconds()
			return rep, nil
		}
		if code == 0 {
			rep.Status = "PASS"
			rep.ElapsedMS = time.Since(started).Milliseconds()
			return rep, nil
		}
		lastOut = out
	}
	rep.Status = "REPAIR_BUDGET_EXHAUSTED"
	rep.ElapsedMS = time.Since(started).Milliseconds()
	return rep, nil
}

func contentHash(s string) string {
	sum := sha256.Sum256([]byte(s))
	return "sha256:" + hex.EncodeToString(sum[:])
}

// UnifiedDiff renders a real line-oriented unified diff with @@ hunks and three context lines,
// computed from a least-common-subsequence walk. Very large inputs degrade to a whole-file replace
// rather than blowing up quadratic space, and that degradation is reported in the header so the
// output can never be mistaken for a minimal diff.
func UnifiedDiff(name, before, after string) string {
	a, b := splitLines(before), splitLines(after)
	if len(a)*len(b) > 4_000_000 {
		return replaceDiff(name, a, b)
	}
	ops := diffOps(a, b)
	return renderHunks(name, a, b, ops, 3)
}

func splitLines(s string) []string {
	if s == "" {
		return nil
	}
	lines := strings.Split(s, "\n")
	if strings.HasSuffix(s, "\n") {
		lines = lines[:len(lines)-1]
	}
	return lines
}

func replaceDiff(name string, a, b []string) string {
	var sb strings.Builder
	fmt.Fprintf(&sb, "--- a/%s\n+++ b/%s\n", name, name)
	sb.WriteString("# whole-file replace: input too large for a minimal line diff on this build\n")
	fmt.Fprintf(&sb, "@@ -1,%d +1,%d @@\n", len(a), len(b))
	for _, l := range a {
		sb.WriteString("-" + l + "\n")
	}
	for _, l := range b {
		sb.WriteString("+" + l + "\n")
	}
	return sb.String()
}

// diffOps returns one edit per element of an alignment of a and b.
func diffOps(a, b []string) []string {
	n, m := len(a), len(b)
	table := make([][]int, n+1)
	for i := range table {
		table[i] = make([]int, m+1)
	}
	for i := n - 1; i >= 0; i-- {
		for j := m - 1; j >= 0; j-- {
			if a[i] == b[j] {
				table[i][j] = table[i+1][j+1] + 1
			} else if table[i+1][j] >= table[i][j+1] {
				table[i][j] = table[i+1][j]
			} else {
				table[i][j] = table[i][j+1]
			}
		}
	}
	ops := make([]string, 0, n+m)
	i, j := 0, 0
	for i < n && j < m {
		switch {
		case a[i] == b[j]:
			ops = append(ops, " ")
			i, j = i+1, j+1
		case table[i+1][j] >= table[i][j+1]:
			ops = append(ops, "-")
			i++
		default:
			ops = append(ops, "+")
			j++
		}
	}
	for ; i < n; i++ {
		ops = append(ops, "-")
	}
	for ; j < m; j++ {
		ops = append(ops, "+")
	}
	return ops
}

// renderHunks groups the alignment into hunks with ctxLines of context, merging hunks whose context
// would overlap. Line numbers are 1-based and counts are the lengths the patch tool expects.
func renderHunks(name string, a, b []string, ops []string, ctxLines int) string {
	type row struct {
		kind byte
		old  int // index into a, -1 for insertions
		new  int // index into b, -1 for deletions
		text string
	}
	rows := make([]row, 0, len(ops))
	oi, ni := 0, 0
	for _, op := range ops {
		switch op[0] {
		case ' ':
			rows = append(rows, row{' ', oi, ni, a[oi]})
			oi, ni = oi+1, ni+1
		case '-':
			rows = append(rows, row{'-', oi, -1, a[oi]})
			oi++
		case '+':
			rows = append(rows, row{'+', -1, ni, b[ni]})
			ni++
		}
	}
	var sb strings.Builder
	fmt.Fprintf(&sb, "--- a/%s\n+++ b/%s\n", name, name)
	changed := func(i int) bool { return rows[i].kind != ' ' }
	for i := 0; i < len(rows); i++ {
		if !changed(i) {
			continue
		}
		start := i - ctxLines
		if start < 0 {
			start = 0
		}
		end := i
		trailing := 0
		for end < len(rows) {
			if !changed(end) {
				trailing++
				if trailing > ctxLines {
					break
				}
			} else {
				trailing = 0
			}
			end++
		}
		end = end - trailing + ctxLines
		if end > len(rows) {
			end = len(rows)
		}
		if start > 0 && !changed(start-1) {
			// keep the window as computed; nothing to trim
		}
		oldStart, oldCount, newStart, newCount := 0, 0, 0, 0
		for k := start; k < end; k++ {
			switch rows[k].kind {
			case ' ':
				if oldCount == 0 && newCount == 0 {
					oldStart, newStart = rows[k].old+1, rows[k].new+1
				}
				oldCount++
				newCount++
			case '-':
				if oldCount == 0 && newCount == 0 {
					oldStart, newStart = rows[k].old+1, rows[k].new+2
				}
				oldCount++
			case '+':
				if oldCount == 0 && newCount == 0 {
					oldStart, newStart = rows[k].old+2, rows[k].new+1
				}
				newCount++
			}
		}
		if oldStart == 0 {
			oldStart = 1
		}
		if newStart == 0 {
			newStart = 1
		}
		fmt.Fprintf(&sb, "@@ -%d,%d +%d,%d @@\n", oldStart, oldCount, newStart, newCount)
		for k := start; k < end; k++ {
			sb.WriteString(string(rows[k].kind) + rows[k].text + "\n")
		}
		i = end - 1
	}
	return sb.String()
}

// runCodingTask is the CLI surface for one coding task. The edit is supplied by the caller as a
// deterministic old=>new replacement because no model backend is installed on this build; the point
// of the command is the pipeline around the edit - real read, real diff, real check, bounded repair -
// and it refuses rather than pretending a write happened.
func runCodingTask(args []string) {
	fs := flag.NewFlagSet("task", flag.ContinueOnError)
	dir := fs.String("dir", ".", "directory the task operates in")
	rel := fs.String("file", "", "file to change, relative to -dir")
	replace := fs.String("replace", "", "deterministic edit as old=>new (no model backend on this build)")
	check := fs.String("check", "", "check command to run against the directory after each candidate")
	repairs := fs.Int("repairs", 1, "maximum number of repairs a failing check may drive")
	ws := fs.String("workspace", "cli://local", "workspace ref the write is authorised against")
	if err := fs.Parse(args); err != nil {
		os.Exit(2)
	}
	fail := func(msg string) {
		fmt.Println("task: INVALID_REQUEST: " + msg)
		os.Exit(2)
	}
	if *rel == "" {
		fail("-file is required")
	}
	if *check == "" {
		fail("-check is required; a coding task with no verification is not a checked change")
	}
	parts := strings.SplitN(*replace, "=>", 2)
	if len(parts) != 2 {
		fail("-replace must be old=>new")
	}
	if *repairs < 0 {
		fail("-repairs must not be negative")
	}
	argv := strings.Fields(*check)
	task := &CodingTask{Dir: *dir, Workspace: *ws, TaskID: "W05-02",
		Writer:     NotRoutedWriter{Reason: "internal/domain routes no workspace.write handler"},
		Check:      CommandChecker(argv...),
		MaxRepairs: *repairs}
	rep, err := task.Run(context.Background(), filepath.ToSlash(*rel), func(_ int, base, _ string) (string, error) {
		if !strings.Contains(base, parts[0]) {
			return "", fmt.Errorf("PATTERN_NOT_FOUND: %q is not in %s", parts[0], *rel)
		}
		return strings.Replace(base, parts[0], parts[1], 1), nil
	})
	if err != nil {
		fmt.Println("task: " + err.Error())
		os.Exit(1)
	}
	fmt.Print(rep.Diff)
	line, _ := json.Marshal(rep)
	fmt.Println(string(line))
	switch rep.Status {
	case "PASS":
		os.Exit(0)
	case "REPAIR_BUDGET_EXHAUSTED":
		os.Exit(4)
	case "CANCELLED":
		os.Exit(130)
	case "BLOCKED_WRITE_ROUTE_NOT_ROUTED":
		fmt.Println("task: the candidate was NOT written; workspace.write has no handler on this host build (obligation W05-02-domain-write-route)")
		os.Exit(3)
	default:
		os.Exit(1)
	}
}
