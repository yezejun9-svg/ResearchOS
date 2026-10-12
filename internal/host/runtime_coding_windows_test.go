//go:build windows

package host

import (
	"context"
	"os"
	"path/filepath"
	"researchos.local/research-os/internal/domain"
	"strings"
	"testing"
)

func codingInventory(t *testing.T) (*os.Root, string, domain.RuntimeCodingCheck) {
	t.Helper()
	workspace := t.TempDir()
	files := map[string]string{"go.mod": "module fixture.local/coding\n\ngo 1.27\n", "pkg/main.go": "package pkg\nfunc Value() int { return 1 }\n", "pkg/main_test.go": "package pkg\nimport \"testing\"\nfunc TestSelected(t *testing.T) { if Value()!=1 { t.Fatal(\"wrong\") } }\n"}
	for p, s := range files {
		target := filepath.Join(workspace, filepath.FromSlash(p))
		if e := os.MkdirAll(filepath.Dir(target), 0700); e != nil {
			t.Fatal(e)
		}
		if e := os.WriteFile(target, []byte(s), 0600); e != nil {
			t.Fatal(e)
		}
	}
	root, e := os.OpenRoot(workspace)
	if e != nil {
		t.Fatal(e)
	}
	t.Cleanup(func() { root.Close() })
	toolchain := t.TempDir()
	if e = os.MkdirAll(filepath.Join(toolchain, "src/testing"), 0700); e != nil {
		t.Fatal(e)
	}
	return root, workspace, domain.RuntimeCodingCheck{ID: "selected", Package: "./pkg", TestPattern: "^TestSelected$", SourcePaths: []string{"go.mod", "pkg/main.go", "pkg/main_test.go"}, ToolchainRoot: toolchain, TimeoutSeconds: 30, ProcessLimit: 8, MemoryMiB: 512, MaxTextBytes: 2048}
}
func TestProductCodingCheckInventory(t *testing.T) {
	for _, name := range []string{"complete", "missing_mod", "missing_sum", "missing_production", "missing_helper", "missing_import", "missing_embed", "zero_tests", "test_main", "test_init", "unanchored", "complete_import", "complete_embed"} {
		t.Run(name, func(t *testing.T) {
			root, workspace, check := codingInventory(t)
			write := func(p, s string) {
				t.Helper()
				full := filepath.Join(workspace, filepath.FromSlash(p))
				if e := os.MkdirAll(filepath.Dir(full), 0700); e != nil {
					t.Fatal(e)
				}
				if e := os.WriteFile(full, []byte(s), 0600); e != nil {
					t.Fatal(e)
				}
			}
			switch name {
			case "missing_mod":
				check.SourcePaths = check.SourcePaths[1:]
			case "missing_sum":
				write("go.sum", "fixture sum")
			case "missing_production":
				write("pkg/other.go", "package pkg\nfunc Other(){}")
			case "missing_helper":
				write("pkg/main_test.go", "package pkg\nimport \"testing\"\nfunc TestSelected(t *testing.T){missingHelper(t)}")
			case "missing_import", "complete_import":
				write("pkg/main.go", "package pkg\nimport \"fixture.local/coding/helper\"\nfunc Value() int{return helper.Value()}")
				write("helper/value.go", "package helper\nfunc Value()int{return 1}")
				if name == "complete_import" {
					check.SourcePaths = append(check.SourcePaths, "helper/value.go")
				}
			case "missing_embed", "complete_embed":
				os.MkdirAll(filepath.Join(check.ToolchainRoot, "src/embed"), 0700)
				write("pkg/main.go", "package pkg\nimport _ \"embed\"\n//go:embed input.txt\nvar input string\nfunc Value()int{return len(input)}")
				write("pkg/input.txt", "x")
				if name == "complete_embed" {
					check.SourcePaths = append(check.SourcePaths, "pkg/input.txt")
				}
			case "zero_tests":
				check.TestPattern = "^TestNotIncluded$"
			case "test_main":
				write("pkg/main_test.go", "package pkg\nfunc TestMain(){}\nfunc TestSelected(){}")
			case "test_init":
				write("pkg/main_test.go", "package pkg\nfunc init(){}\nfunc TestSelected(){}")
			case "unanchored":
				check.TestPattern = "TestSelected"
			}
			e := validateCodingCheckSources(context.Background(), root, workspace, check)
			positive := strings.HasPrefix(name, "complete")
			if (e == nil) != positive {
				t.Fatalf("inventory %s err=%v", name, e)
			}
		})
	}
}
func TestProductCodingPrivateFrames(t *testing.T) {
	_, _, check := codingInventory(t)
	in := domain.RuntimeCodingIntent{ClientID: "client", ExpectedRevision: 1, WriterEpoch: 1, ConfigRevision: 2, WorkspaceRef: "workspace", ReadPaths: check.SourcePaths, WritePaths: []string{"pkg/main.go"}, MaxReadBytes: 4096, MaxWriteBytes: 4096, MaxToolCalls: 16, MaxOutputTokens: 2048, Checks: []domain.RuntimeCodingCheck{check}}
	frame := DesktopManagementFrame{Protocol: DesktopManagementProtocol, MessageID: "message", Operation: "PREPARE_CODING", HostID: "host", ProjectID: "project", SessionID: "session", ModelRef: "model", Coding: &in}
	raw := domain.Bytes(frame)
	if _, e := decodeDesktopManagement(raw); e != nil {
		t.Fatal(e)
	}
	for _, change := range []func(){func() { frame.Operation = "PREPARE" }, func() { frame.Operation = "CONFIRM_CODING" }, func() { frame.Operation = "PREPARE_CODING"; in.WritePaths = []string{"../escape"} }, func() { in.WritePaths = []string{"pkg/main.go"}; in.MaxToolCalls = 33 }} {
		change()
		if _, e := decodeDesktopManagement(domain.Bytes(frame)); e == nil {
			t.Fatal("invalid mixed private scope admitted")
		}
	}
	duplicate := strings.Replace(string(raw), `"max_tool_calls":16`, `"max_tool_calls":16,"max_tool_calls":32`, 1)
	if _, e := decodeDesktopManagement([]byte(duplicate)); e == nil {
		t.Fatal("nested duplicate accepted")
	}
}
