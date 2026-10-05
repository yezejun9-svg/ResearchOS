//go:build windows

package host

import (
	"context"
	"errors"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"researchos.local/research-os/internal/domain"
)

func runtimeCheckTestPolicy(root, treeHash, buildHash string) domain.Object {
	return domain.Object{"read_paths": []any{"go.mod", "sample_test.go"}, "checks": []any{domain.Object{
		"id": "doctor-unit", "executable": "go", "build_hash": buildHash,
		"toolchain_root": root, "toolchain_hash": treeHash,
		"argv":         []any{"-C", "${SOURCE}", "test", "-p=2", "-count=1", "-run", "^TestPass$", "./..."},
		"source_paths": []any{domain.Object{"path": "go.mod"}, domain.Object{"path": "sample_test.go"}},
		"resources":    domain.Object{"timeout_seconds": 120, "process_limit": 32, "memory_mib": 1024, "max_text_bytes": 2048},
	}}}
}

func TestFrozenRuntimeCheckRejectsCommandInjection(t *testing.T) {
	policy := runtimeCheckTestPolicy(t.TempDir(), domain.Digest([]byte("tree")), domain.Digest([]byte("go")))
	if _, err := parseFrozenRuntimeCheck(policy, "doctor-unit"); err != nil {
		t.Fatal(err)
	}
	for _, args := range []domain.Object{
		{"check_id": "doctor-unit", "executable": "powershell.exe"},
		{"check_id": "doctor-unit", "argv": []any{"-C", "host"}},
		{"check_id": "missing"},
	} {
		_, err := (&Host{}).executeRuntimeCheck(context.Background(), domain.RuntimeToolRequest{Name: "run_check", Access: AccessReadOnly, Arguments: args, Policy: policy})
		if err == nil {
			t.Fatalf("accepted child command selection: %v", args)
		}
	}
	row := policy["checks"].([]any)[0].(domain.Object)
	row["argv"] = []any{"-C", "${SOURCE}", "test", "-exec", "powershell.exe", "./..."}
	if _, err := parseFrozenRuntimeCheck(policy, "doctor-unit"); err == nil {
		t.Fatal("accepted arbitrary frozen test executable")
	}
	row["argv"] = []any{"-C", "${SOURCE}", "test", "-p=2", "-count=1", "-run", "^TestPass$", "./..."}
	row["source_paths"] = []any{domain.Object{"path": "../host-secret"}}
	if _, err := parseFrozenRuntimeCheck(policy, "doctor-unit"); err == nil {
		t.Fatal("accepted source escape")
	}
}

func TestRuntimeCheckSourceSnapshotCurrentAndFixed(t *testing.T) {
	workspace := t.TempDir()
	root, err := os.OpenRoot(workspace)
	if err != nil {
		t.Fatal(err)
	}
	defer root.Close()
	if err := os.WriteFile(filepath.Join(workspace, "sample.go"), []byte("old"), 0600); err != nil {
		t.Fatal(err)
	}
	path := []runtimeCheckSource{{path: "sample.go"}}
	before, err := runtimeCheckSnapshot(context.Background(), root, path, "")
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(workspace, "sample.go"), []byte("new"), 0600); err != nil {
		t.Fatal(err)
	}
	after, err := runtimeCheckSnapshot(context.Background(), root, path, "")
	if err != nil || domain.Hash(before) == domain.Hash(after) {
		t.Fatalf("current source bytes were not observed: %v", err)
	}
	if _, err := runtimeCheckSnapshot(context.Background(), root, []runtimeCheckSource{{path: "sample.go", expected: domain.Digest([]byte("old"))}}, ""); err == nil {
		t.Fatal("accepted changed fixed source")
	}
	staged := filepath.Join(t.TempDir(), "stage")
	if err := os.Mkdir(staged, 0700); err != nil {
		t.Fatal(err)
	}
	manifest, err := runtimeCheckSnapshot(context.Background(), root, path, staged)
	if err != nil {
		t.Fatal(err)
	}
	if got, err := os.ReadFile(filepath.Join(staged, "sample.go")); err != nil || string(got) != "new" || domain.Hash(manifest) != domain.Hash(after) {
		t.Fatalf("wrong staged source: %q %v", got, err)
	}
}

func TestRuntimeCheckFrozenTreeHashDetectsChangedInput(t *testing.T) {
	goRoot := t.TempDir()
	for _, dir := range []string{"bin", "pkg", "lib", "src"} {
		if err := os.Mkdir(filepath.Join(goRoot, dir), 0700); err != nil {
			t.Fatal(err)
		}
	}
	exe := filepath.Join(goRoot, "bin", "go.exe")
	if err := os.WriteFile(exe, []byte("pinned"), 0600); err != nil {
		t.Fatal(err)
	}
	treeBefore, buildBefore, err := FrozenGoToolchainHash(goRoot)
	if err != nil || buildBefore != domain.Digest([]byte("pinned")) {
		t.Fatalf("incorrect frozen Go hash: %s %v", buildBefore, err)
	}
	if err := os.WriteFile(exe, []byte("changed"), 0600); err != nil {
		t.Fatal(err)
	}
	treeAfter, buildAfter, err := FrozenGoToolchainHash(goRoot)
	if err != nil || treeBefore == treeAfter || buildBefore == buildAfter {
		t.Fatalf("mutable toolchain was accepted: %s %s %v", treeBefore, treeAfter, err)
	}
	vendor := t.TempDir()
	file := filepath.Join(vendor, "modules.txt")
	if err := os.WriteFile(file, []byte("pinned"), 0600); err != nil {
		t.Fatal(err)
	}
	vendorBefore, err := FrozenVendorHash(vendor)
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(file, []byte("changed"), 0600); err != nil {
		t.Fatal(err)
	}
	vendorAfter, err := FrozenVendorHash(vendor)
	if err != nil || vendorBefore == vendorAfter {
		t.Fatalf("mutable vendor was accepted: %s %s %v", vendorBefore, vendorAfter, err)
	}
}

func TestRuntimeCheckDispatcherUsesCheckOnlyPolicy(t *testing.T) {
	host, workspace, binding := runtimeToolFixture(t, AccessReadOnly)
	for name, data := range map[string]string{"go.mod": "module example.test/check\n", "sample_test.go": "package check\n"} {
		if err := os.WriteFile(filepath.Join(workspace, name), []byte(data), 0600); err != nil {
			t.Fatal(err)
		}
	}
	goRoot := t.TempDir()
	for _, dir := range []string{"bin", "pkg", "lib", "src"} {
		if err := os.Mkdir(filepath.Join(goRoot, dir), 0700); err != nil {
			t.Fatal(err)
		}
	}
	exe := filepath.Join(goRoot, "bin", "go.exe")
	if err := os.WriteFile(exe, []byte("pinned"), 0600); err != nil {
		t.Fatal(err)
	}
	tree, build, err := FrozenGoToolchainHash(goRoot)
	if err != nil {
		t.Fatal(err)
	}
	policy := runtimeCheckTestPolicy(goRoot, tree, build)
	delete(policy, "read_paths") // source_paths is the check-only read allowlist.
	if err := os.WriteFile(exe, []byte("changed"), 0600); err != nil {
		t.Fatal(err)
	}
	request := domain.RuntimeToolRequest{WorkspacePath: workspace, Access: AccessReadOnly, Name: "run_check", Arguments: domain.Object{"check_id": "doctor-unit"}, Policy: policy}
	if _, err := host.ExecuteRuntimeTool(context.Background(), request); err == nil || !strings.Contains(err.Error(), "frozen Go toolchain changed") {
		t.Fatalf("check_id-only dispatcher did not reach toolchain pin: %v", err)
	} else {
		var failure *domain.RuntimeToolFailure
		if !errors.As(err, &failure) || failure.Outcome != "NOT_APPLIED" {
			t.Fatalf("frozen check prelaunch failure should be NOT_APPLIED: %v", err)
		}
	}
	if err := host.RevokeWorkspace(binding.Ref); err != nil {
		t.Fatal(err)
	}
	if _, err := host.ExecuteRuntimeTool(context.Background(), request); err == nil {
		t.Fatal("revoked workspace ran check")
	}
}

// This expensive probe uses the already-installed pinned Go toolchain. It
// creates a fresh source workspace and never widens the host toolchain ACL.
func TestRuntimeCheckNativeGo(t *testing.T) {
	toolchain := os.Getenv("W14_GO_TOOLCHAIN")
	if toolchain == "" {
		t.Skip("set W14_GO_TOOLCHAIN for native Go run_check probe")
	}
	host, workspace, _ := runtimeToolFixture(t, AccessReadOnly)
	if err := os.WriteFile(filepath.Join(workspace, "go.mod"), []byte("module example.test/runcheck\n\ngo 1.27\n"), 0600); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(workspace, "sample_test.go"), []byte("package runcheck\nimport \"testing\"\nfunc TestPass(t *testing.T) { if 2+2 != 4 { t.Fatal(\"bad result\") } }\n"), 0600); err != nil {
		t.Fatal(err)
	}
	tree, build, err := FrozenGoToolchainHash(toolchain)
	if err != nil {
		t.Fatal(err)
	}
	policy := runtimeCheckTestPolicy(toolchain, tree, build)
	result, err := host.ExecuteRuntimeTool(context.Background(), domain.RuntimeToolRequest{WorkspacePath: workspace, Access: AccessReadOnly, Name: "run_check", Arguments: domain.Object{"check_id": "doctor-unit"}, Policy: policy})
	if err != nil {
		t.Fatal(err)
	}
	details := result["details"].(domain.Object)
	full := result["host_evidence"].(domain.Object)
	if details["exit_code"] != 0 || details["children_stopped"] != true || details["streams_drained"] != true || details["cleanup_complete"] != true || details["source_count"] != 2 || !strings.Contains(details["stdout_text"].(string), "ok") {
		t.Fatalf("native run_check failed: %v", details)
	}
	if details["job_total_processes"].(uint32) < 2 || full["source_manifest_hash"] != details["source_manifest_hash"] || len(full["source_manifest"].([]any)) != 2 || full["toolchain_hash"] != tree {
		t.Fatalf("native check evidence incomplete: %v", details)
	}
}
