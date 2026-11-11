package main

// Exact selectors keep development suites, accepted legacy fixtures, and v2.4 LIVE
// requirements separate. An unknown selector must never borrow another suite's assertions.
import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

type runtimeRoute string

const (
	runtimeServed  runtimeRoute = "served"
	runtimeFixture runtimeRoute = "legacy-fixture"
	runtimeV24Live runtimeRoute = "v24-live-preflight"
)

func selectRuntimeRoute(task, check, caseID string) (runtimeRoute, error) {
	if (check == "") == (caseID == "") {
		return "", fmt.Errorf("exactly one check_id or case_id is required")
	}
	if task == "W12" && check == "" && caseID == "C11" {
		return runtimeFixture, nil
	}
	if task != "W05" {
		return "", fmt.Errorf("unsupported test.runtime task/selector combination")
	}
	if caseID == "A04" {
		return runtimeV24Live, nil
	}
	switch check {
	case "W05-01", "W05-02":
		return runtimeServed, nil
	case "W05-G01":
		return runtimeFixture, nil
	case "W05-G02", "W05-H08", "W05-P01", "W05-U02":
		return runtimeV24Live, nil
	}
	return "", fmt.Errorf("unsupported test.runtime task/selector combination")
}

// Resolve the interpreter from the project lock on every invocation. Neither PATH
// nor an unverified environment override can select a different Python binary.
func lockedPython(root string) (string, error) {
	raw, err := os.ReadFile(filepath.Join(root, "execution", "toolchains", "locked.json"))
	if err != nil {
		return "", fmt.Errorf("read Python tool lock: %w", err)
	}
	var lock struct {
		Tools map[string]struct {
			Path   string `json:"path"`
			SHA256 string `json:"sha256"`
		} `json:"tools"`
	}
	if err = json.Unmarshal(raw, &lock); err != nil {
		return "", fmt.Errorf("parse Python tool lock: %w", err)
	}
	tool, exists := lock.Tools["python"]
	digest, hashErr := hex.DecodeString(tool.SHA256)
	if !exists || !filepath.IsAbs(tool.Path) || hashErr != nil || len(digest) != sha256.Size {
		return "", fmt.Errorf("Python lock requires an absolute path and SHA256")
	}
	info, err := os.Stat(tool.Path)
	if err != nil || !info.Mode().IsRegular() {
		return "", fmt.Errorf("locked Python is not a regular file")
	}
	binary, err := os.ReadFile(tool.Path)
	if err != nil {
		return "", fmt.Errorf("read locked Python: %w", err)
	}
	actual := sha256.Sum256(binary)
	if !strings.EqualFold(hex.EncodeToString(actual[:]), tool.SHA256) {
		return "", fmt.Errorf("locked Python SHA256 mismatch")
	}
	return tool.Path, nil
}

func runtimePythonCommand(root, script, mode string) (*exec.Cmd, error) {
	python, err := lockedPython(root)
	if err != nil {
		return nil, err
	}
	cmd := exec.Command(python, "-X", "utf8", filepath.Join(root, filepath.FromSlash(script)), "--mode", mode)
	cmd.Dir = root
	cmd.Env = os.Environ()
	return cmd, nil
}

func runtimeRoutingBlocked(reason, detail string) {
	_ = json.NewEncoder(os.Stdout).Encode(map[string]any{
		"status": "BLOCKED", "reason_code": reason, "reason": detail,
		"assertion_ids": []string{}, "passed_assertion_ids": []string{}, "passed": false,
	})
}

// Keep this entry point for main.go and the served W05-01/02 suites.
func routeLegacy() (int, bool) {
	route, err := selectRuntimeRoute(os.Getenv("RESEARCHOS_TASK_ID"), os.Getenv("RESEARCHOS_CHECK_ID"), os.Getenv("RESEARCHOS_CASE_ID"))
	if err != nil {
		runtimeRoutingBlocked("INVALID_SELECTOR", err.Error())
		return 2, true
	}
	if route == runtimeServed {
		return 0, false
	}
	script, mode := "ops/ci/runtime.py", "fixture"
	if route == runtimeV24Live {
		script, mode = "ops/ci/runtime_v24.py", "live"
	}
	cmd, err := runtimePythonCommand(repoRoot(), script, mode)
	if err != nil {
		runtimeRoutingBlocked("TOOLCHAIN_ERROR", err.Error())
		return 3, true
	}
	cmd.Stdout, cmd.Stderr = os.Stdout, os.Stderr
	if err = cmd.Run(); err != nil {
		if exit, isExit := err.(*exec.ExitError); isExit {
			return exit.ExitCode(), true
		}
		runtimeRoutingBlocked("TOOLCHAIN_ERROR", err.Error())
		return 3, true
	}
	return 0, true
}

type runtimeRouteRow struct {
	task, check, caseID string
	want                runtimeRoute
	valid               bool
}

func runtimeRouteRows() []runtimeRouteRow {
	return []runtimeRouteRow{
		{"W05", "W05-01", "", runtimeServed, true},
		{"W05", "W05-02", "", runtimeServed, true},
		{"W05", "W05-G01", "", runtimeFixture, true},
		{"W12", "", "C11", runtimeFixture, true},
		{"W05", "W05-G02", "", runtimeV24Live, true},
		{"W05", "W05-H08", "", runtimeV24Live, true},
		{"W05", "W05-P01", "", runtimeV24Live, true},
		{"W05", "W05-U02", "", runtimeV24Live, true},
		{"W05", "", "A04", runtimeV24Live, true},
		{"W12", "W05-G01", "", "", false},
		{"W12", "", "A04", "", false},
		{"W05", "", "C11", "", false},
		{"W05", "W05-01", "A04", "", false},
		{"W05", "W05-G02", "A04", "", false},
		{"W05", "W99-DOES-NOT-EXIST", "", "", false},
		{"W12", "", "", "", false},
		{"W05", "", "", "", false},
		{"", "", "A04", "", false},
		{"", "W05-01", "", "", false},
		{"", "", "", "", false},
	}
}

func runtimeRoutingMismatches() []string {
	bad := []string{}
	for _, row := range runtimeRouteRows() {
		got, err := selectRuntimeRoute(row.task, row.check, row.caseID)
		if (err == nil) != row.valid || got != row.want {
			bad = append(bad, fmt.Sprintf("%s/%s/%s: got %s error=%v, want %s valid=%t", row.task, row.check, row.caseID, got, err, row.want, row.valid))
		}
	}
	return bad
}

func routingTruthTableOK() {
	bad := runtimeRoutingMismatches()
	ok("W0501-ROUTING-TRUTH-TABLE", len(bad) == 0, bad)
}
