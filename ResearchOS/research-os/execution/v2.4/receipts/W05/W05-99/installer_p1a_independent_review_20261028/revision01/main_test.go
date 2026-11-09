package main

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strings"
	"testing"
)

func fixture(t *testing.T, root string) ([]byte, *payload) {
	t.Helper()
	if err := os.Mkdir(root, 0700); err != nil {
		t.Fatal(err)
	}
	p := &payload{Schema: "researchos.static-payload/1", CandidateMarkerSHA256: candidateSHA256,
		Metadata: map[string]any{"schema": "researchos.product-layout/1",
			"mode": "OWNED_PRODUCT_LAYOUT_NOT_INSTALLER", "source_commit": sourceCommit,
			"source_digest": strings.Repeat("a", 64), "product_version": "2.4.0",
			"client_protocol": "researchos-client/2", "schema_version": float64(24),
			"tool_hashes": map[string]any{}, "go_compiled_input_sha256": strings.Repeat("b", 64),
			"mu_compiled_input_sha256": strings.Repeat("c", 64),
			"mu_vendor_5083_sha256":    strings.Repeat("d", 64),
			"client_wire_input_digest": strings.Repeat("e", 64)},
		Binaries: map[string]binary{}, Files: []row{},
		VerifierTemplate: map[string]any{"schema": "researchos.runtime-verifier-installation.v1",
			"service_id": "researchos.runtime-qualification-verifier.v1",
			"protocol":   "researchos.runtime-verifier/1", "source_commit": sourceCommit,
			"arguments": []any{}},
	}
	for i := 0; i < 100; i++ {
		name := fmt.Sprintf("payload/file-%03d.bin", i)
		if i == 0 {
			name = "apps/desktop/resources/control/runtime-verifier.exe"
		}
		full := filepath.Join(root, filepath.FromSlash(name))
		if err := os.MkdirAll(filepath.Dir(full), 0700); err != nil {
			t.Fatal(err)
		}
		data := []byte(fmt.Sprintf("%03d", i))
		if err := os.WriteFile(full, data, 0600); err != nil {
			t.Fatal(err)
		}
		p.Files = append(p.Files, row{Path: name, SHA256: shaBytes(data), Bytes: int64(len(data))})
		if i < 5 {
			p.Binaries[roles[i]] = binary{Path: name, SHA256: shaBytes(data)}
		}
	}
	sort.Slice(p.Files, func(i, j int) bool { return p.Files[i].Path < p.Files[j].Path })
	raw, err := jsonLine(p)
	if err != nil {
		t.Fatal(err)
	}
	return raw, p
}

func TestFreshRootsHaveSharedPayloadAndDistinctInstallationIdentity(t *testing.T) {
	base := t.TempDir()
	var ids []string
	var digests []string
	for _, name := range []string{"中文 空格 A", "中文 空格 B"} {
		root := filepath.Join(base, name)
		raw, p := fixture(t, root)
		bound := shaBytes(raw)
		decoded, err := parseManifest(raw, bound)
		if err != nil {
			t.Fatal(err)
		}
		if len(decoded.Files) != len(p.Files) {
			t.Fatal("lost files")
		}
		manifest := filepath.Join(base, name+".json")
		if err = os.WriteFile(manifest, raw, 0600); err != nil {
			t.Fatal(err)
		}
		id, err := finalize(root, manifest, bound)
		if err != nil {
			t.Fatal(err)
		}
		markerRaw, err := os.ReadFile(filepath.Join(root, markerPath))
		if err != nil {
			t.Fatal(err)
		}
		var marker map[string]any
		if err = json.Unmarshal(markerRaw, &marker); err != nil {
			t.Fatal(err)
		}
		if marker["installation_id"] != id || marker["install_root"] != root {
			t.Fatal("wrong marker identity")
		}
		rows := append(append([]row{}, p.Files...), row{})
		rows[len(rows)-1], err = fileRow(root, verifierPath)
		if err != nil {
			t.Fatal(err)
		}
		sort.Slice(rows, func(i, j int) bool { return rows[i].Path < rows[j].Path })
		if marker["inventory_digest"] != inventoryDigest(rows) || id != installationID(root, p, inventoryDigest(rows)) {
			t.Fatal("inventory or installation identity differs from marker")
		}
		ids = append(ids, id)
		digests = append(digests, bound)
		if _, err = finalize(root, manifest, bound); err == nil {
			t.Fatal("existing marker accepted")
		}
	}
	if ids[0] == ids[1] || digests[0] != digests[1] {
		t.Fatal("payload/location identity contract broken")
	}
}

func TestRejectUnboundChangedAndUnsafeManifest(t *testing.T) {
	root := filepath.Join(t.TempDir(), "fresh")
	raw, p := fixture(t, root)
	if _, err := parseManifest(raw, ""); err == nil {
		t.Fatal("unbound manifest accepted")
	}
	if _, err := parseManifest(append(append([]byte{}, raw...), byte(' ')), shaBytes(raw)); err == nil {
		t.Fatal("changed manifest accepted")
	}
	p.Files[1].Path = "payload/../escape"
	changed, _ := jsonLine(p)
	if _, err := parseManifest(changed, shaBytes(changed)); err == nil {
		t.Fatal("unsafe row accepted")
	}
	p.Files[1].Path = "payload/File-000.bin"
	changed, _ = jsonLine(p)
	if _, err := parseManifest(changed, shaBytes(changed)); err == nil {
		t.Fatal("case alias accepted")
	}
}

func TestRejectPhysicalDriftBeforeWriting(t *testing.T) {
	tests := []struct {
		name   string
		mutate func(string) error
	}{
		{"missing", func(root string) error { return os.Remove(filepath.Join(root, "payload", "file-001.bin")) }},
		{"extra", func(root string) error {
			return os.WriteFile(filepath.Join(root, "payload", "extra.bin"), []byte("x"), 0600)
		}},
		{"tamper", func(root string) error {
			return os.WriteFile(filepath.Join(root, "payload", "file-001.bin"), []byte("bad"), 0600)
		}},
		{"alias-root", func(root string) error { return nil }},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			root := filepath.Join(t.TempDir(), "fresh")
			raw, _ := fixture(t, root)
			manifest := filepath.Join(filepath.Dir(root), "manifest.json")
			if err := os.WriteFile(manifest, raw, 0600); err != nil {
				t.Fatal(err)
			}
			if err := tt.mutate(root); err != nil {
				t.Fatal(err)
			}
			input := root
			if tt.name == "alias-root" {
				input = strings.ToUpper(root[:1]) + root[1:]
				if input == root {
					input = strings.ToLower(root[:1]) + root[1:]
				}
			}
			if _, err := finalize(input, manifest, shaBytes(raw)); err == nil {
				t.Fatal("drift accepted")
			}
			if _, err := os.Stat(filepath.Join(root, markerPath)); !os.IsNotExist(err) {
				t.Fatal("marker written after refusal")
			}
		})
	}
}

func TestRejectHardlinkAndReparseFile(t *testing.T) {
	for _, kind := range []string{"hardlink", "symlink"} {
		t.Run(kind, func(t *testing.T) {
			root := filepath.Join(t.TempDir(), "fresh")
			_, p := fixture(t, root)
			source := filepath.Join(root, "payload", "file-001.bin")
			outside := filepath.Join(filepath.Dir(root), "outside.bin")
			content, err := os.ReadFile(source)
			if err != nil {
				t.Fatal(err)
			}
			if err = os.WriteFile(outside, content, 0600); err != nil {
				t.Fatal(err)
			}
			if err = os.Remove(source); err != nil {
				t.Fatal(err)
			}
			if kind == "hardlink" {
				err = os.Link(outside, source)
			} else {
				err = os.Symlink(outside, source)
			}
			if err != nil {
				if kind == "symlink" {
					t.Skipf("Windows symlink privilege unavailable: %v", err)
				}
				t.Fatal(err)
			}
			if err = verifyTree(root, p.Files); err == nil {
				t.Fatal("linked file accepted")
			}
		})
	}
}

func TestRejectJunctionDirectory(t *testing.T) {
	root := filepath.Join(t.TempDir(), "fresh")
	_, p := fixture(t, root)
	original := filepath.Join(root, "payload")
	outside := filepath.Join(filepath.Dir(root), "outside-payload")
	if err := os.Rename(original, outside); err != nil {
		t.Fatal(err)
	}
	output, err := exec.Command("cmd.exe", "/c", "mklink", "/J", original, outside).CombinedOutput()
	if err != nil {
		t.Fatalf("junction setup failed: %v: %s", err, output)
	}
	if err = verifyTree(root, p.Files); err == nil {
		t.Fatal("junction directory accepted")
	}
}

func TestPublishMarkerNoReplace(t *testing.T) {
	for _, scenario := range []string{"success", "preexisting", "appears-before-commit"} {
		t.Run(scenario, func(t *testing.T) {
			root := t.TempDir()
			temp := filepath.Join(root, ".installed-product.json.tmp")
			target := filepath.Join(root, markerPath)
			if err := writeNew(temp, []byte("new marker")); err != nil {
				t.Fatal(err)
			}
			var hook func() error
			if scenario == "preexisting" {
				if err := writeNew(target, []byte("owned sentinel")); err != nil {
					t.Fatal(err)
				}
			}
			if scenario == "appears-before-commit" {
				hook = func() error { return writeNew(target, []byte("racing sentinel")) }
			}
			err := publishMarkerNoReplace(temp, target, hook)
			actual, readErr := os.ReadFile(target)
			if readErr != nil {
				t.Fatal(readErr)
			}
			if scenario == "success" {
				if err != nil || string(actual) != "new marker" {
					t.Fatalf("publication failed: %v, %q", err, actual)
				}
				if _, statErr := os.Stat(temp); !os.IsNotExist(statErr) {
					t.Fatal("temp marker not consumed")
				}
				return
			}
			want := "owned sentinel"
			if scenario == "appears-before-commit" {
				want = "racing sentinel"
			}
			if err == nil || string(actual) != want {
				t.Fatalf("target clobbered: %v, %q", err, actual)
			}
		})
	}
}
