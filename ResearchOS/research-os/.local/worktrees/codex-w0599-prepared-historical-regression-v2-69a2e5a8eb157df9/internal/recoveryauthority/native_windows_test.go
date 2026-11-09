//go:build windows

package recoveryauthority

import (
	"bytes"
	"context"
	"crypto/rand"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"golang.org/x/sys/windows"
)

func TestAuthorityTransportPurposeMACAndFrameLimit(t *testing.T) {
	key := make([]byte, 32)
	if _, err := rand.Read(key); err != nil {
		t.Fatal(err)
	}
	var buffer bytes.Buffer
	if err := writeFrame(&buffer, key, Purpose, map[string]string{"hello": "world"}); err != nil {
		t.Fatal(err)
	}
	raw := append([]byte(nil), buffer.Bytes()...)
	var result map[string]string
	if err := readFrame(bytes.NewReader(raw), key, Purpose, &result); err != nil || result["hello"] != "world" {
		t.Fatal("valid transport failed", err)
	}
	if readFrame(bytes.NewReader(raw), key, MigrationPurpose, &result) == nil {
		t.Fatal("cross-purpose replay accepted")
	}
	key[0] ^= 1
	if readFrame(bytes.NewReader(raw), key, Purpose, &result) == nil {
		t.Fatal("wrong inherited key accepted")
	}
	if readFrame(bytes.NewReader([]byte{255, 255, 255, 255}), key, Purpose, &result) == nil {
		t.Fatal("unbounded frame accepted")
	}
}
func TestAuthorityRawPinHandleDeniesOverwrite(t *testing.T) {
	path := filepath.Join(t.TempDir(), "evidence.json")
	raw := []byte(`{"original":true}`)
	if err := os.WriteFile(path, raw, 0600); err != nil {
		t.Fatal(err)
	}
	f, got, err := pinHeld(RawPin{Path: path, SHA256: digest(raw), Bytes: int64(len(raw))})
	if err != nil {
		t.Fatal(err)
	}
	defer f.file.Close()
	if !bytes.Equal(raw, got) {
		t.Fatal("wrong raw bytes")
	}
	if err = os.WriteFile(path, []byte("changed"), 0600); err == nil {
		t.Fatal("read guard allowed write")
	}
	if err = f.check(); err != nil {
		t.Fatal(err)
	}
	if _, _, err = pinHeld(RawPin{Path: path, SHA256: digest([]byte("wrong")), Bytes: int64(len(raw))}); err == nil {
		t.Fatal("hash mismatch accepted")
	}
}
func TestAuthorityObserveNativeBirthAndRejectCallerImage(t *testing.T) {
	observed, err := process(windows.CurrentProcess())
	if err != nil {
		t.Fatal(err)
	}
	if observed.PID != uint32(os.Getpid()) || observed.Birth100ns == "" || observed.SID == "" {
		t.Fatal("native identity missing")
	}
	pin := observed.Image
	pin.SHA256 = digest([]byte("caller hash"))
	if acceptedImage(observed, pin, observed.SID, "researchos.local/research-os/apps/control") == nil {
		t.Fatal("caller hash accepted")
	}
}
func TestAuthorityPublicModeWithoutPrivateInheritanceRejects(t *testing.T) {
	t.Setenv(bootstrapEnv, "")
	if _, _, err := ReceiveInherited(context.Background()); err == nil {
		t.Fatal("public invocation minted token")
	}
	if _, _, err := ReceiveMigrationInherited(context.Background()); err == nil {
		t.Fatal("public invocation minted migration token")
	}
}
func TestAuthorityProvisionReturnsOnlyDPAPIAndDistinctPurpose(t *testing.T) {
	path := filepath.Join(t.TempDir(), "root.dpapi")
	pub, err := ProvisionEnrollmentKey(path, "root-adoption")
	if err != nil {
		t.Fatal(err)
	}
	if len(pub) != 64 {
		t.Fatal("invalid public key")
	}
	if _, err = readPurposeKey(path, "issuer"); err == nil {
		t.Fatal("root signer decrypted as issuer")
	}
	key, err := readPurposeKey(path, "root-adoption")
	if err != nil {
		t.Fatal(err)
	}
	defer wipe(key)
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	if bytes.Contains(raw, key) || json.Valid(raw) {
		t.Fatal("private key stored as plaintext")
	}
	if _, err = ProvisionEnrollmentKey(path, "root-adoption"); err == nil {
		t.Fatal("existing private resource overwritten")
	}
}

// This fixture includes the actual project_rules_v24.go and both of its actual
// embedded files from the integration source tree. The fixture is only for the
// source guard, not an accepted build or a production authority constructor.
func sourceInventoryFixture(t *testing.T, extra map[string][]byte) Release {
	t.Helper()
	root := t.TempDir()
	for _, dir := range []string{"apps/control", "internal/domain/contracts", "adapters", "evaluation", "ops", "migrations/sqlite", "spec/v2.0/contracts", "execution/toolchains"} {
		if err := os.MkdirAll(filepath.Join(root, filepath.FromSlash(dir)), 0700); err != nil {
			t.Fatal(err)
		}
	}
	cwd, err := os.Getwd()
	if err != nil {
		t.Fatal(err)
	}
	sourceRoot := filepath.Clean(filepath.Join(cwd, "..", ".."))
	files := map[string][]byte{"go.mod": []byte("module fixture\n"), "go.sum": nil, "execution/toolchains/locked.json": []byte("{}")}
	for _, rel := range []string{"internal/domain/project_rules_v24.go", "internal/domain/contracts/new-project-rules-v24.md", "internal/domain/contracts/new-project-rules-v24.json"} {
		raw, e := os.ReadFile(filepath.Join(sourceRoot, filepath.FromSlash(rel)))
		if e != nil {
			t.Fatal("actual embed input unavailable", rel, e)
		}
		files[rel] = raw
	}
	if !bytes.Contains(files["internal/domain/project_rules_v24.go"], []byte("//go:embed contracts/new-project-rules-v24.md")) {
		t.Fatal("actual markdown is no longer the tested go:embed input")
	}
	for rel, raw := range extra {
		files[rel] = raw
	}
	release := Release{SourceRoot: root}
	for rel, raw := range files {
		path := filepath.Join(root, filepath.FromSlash(rel))
		if err = os.MkdirAll(filepath.Dir(path), 0700); err != nil {
			t.Fatal(err)
		}
		if err = os.WriteFile(path, raw, 0600); err != nil {
			t.Fatal(err)
		}
		release.SourceFiles = append(release.SourceFiles, RawPin{Role: "source:" + rel, Path: path, SHA256: digest(raw), Bytes: int64(len(raw))})
	}
	return release
}
func requireSourceInventoryOmission(t *testing.T, release Release, rel string) {
	t.Helper()
	expectedPath := filepath.Join(release.SourceRoot, filepath.FromSlash(rel))
	filtered := []RawPin{}
	found := false
	for _, p := range release.SourceFiles {
		if p.Path == expectedPath {
			found = true
		} else {
			filtered = append(filtered, p)
		}
	}
	if !found {
		t.Fatal("test did not remove a real declared member")
	}
	release.SourceFiles = filtered
	guards, err := sourceGuards(release)
	for _, g := range guards {
		_ = g.file.Close()
	}
	if err == nil || err.Error() != "AUTHORITY_SOURCE_OMITTED:"+rel {
		t.Fatalf("omitting %s: got %v", rel, err)
	}
	// A failed inventory must release earlier handles, including the remaining
	// actual embedded JSON file, so rejection cannot leak a permanent read lock.
	for _, p := range release.SourceFiles {
		if strings.HasSuffix(p.Path, "new-project-rules-v24.json") {
			if err = os.WriteFile(p.Path, []byte("released after reject"), 0600); err != nil {
				t.Fatal(err)
			}
			break
		}
	}
}
func TestAuthoritySourceInventoryRequiresActualEmbeddedMarkdown(t *testing.T) {
	release := sourceInventoryFixture(t, nil)
	guards, err := sourceGuards(release)
	if err != nil {
		t.Fatal("complete actual embed fixture rejected", err)
	}
	markdown := filepath.Join(release.SourceRoot, "internal", "domain", "contracts", "new-project-rules-v24.md")
	if err = os.WriteFile(markdown, []byte("tampered"), 0600); err == nil {
		t.Fatal("complete inventory failed to retain markdown read guard")
	}
	for _, g := range guards {
		if err = g.file.Close(); err != nil {
			t.Fatal(err)
		}
	}
	requireSourceInventoryOmission(t, release, "internal/domain/contracts/new-project-rules-v24.md")
}
func TestAuthoritySourceInventoryConservativelyRequiresAllEmbedCandidates(t *testing.T) {
	// Go permits directory/glob and all: patterns. Full-tree enumeration does
	// not interpret their syntax and therefore cannot omit a future suffix or
	// an all:-eligible dot/underscore member by filtering extensions.
	extra := map[string][]byte{
		"internal/example/embed.go":                       []byte("package example\nimport \"embed\"\n//go:embed all:assets\nvar data embed.FS\n"),
		"internal/example/assets/extensionless":           []byte("asset"),
		"internal/example/assets/future.custom":           []byte("custom"),
		"internal/example/assets/.hidden":                 []byte("hidden"),
		"internal/example/assets/_hidden":                 []byte("underscore"),
		"internal/example/assets/matches_test.go":         []byte("package assets\n"),
		"vendor/example.test/mod/assets/embedded.payload": []byte("vendored embed"),
	}
	for _, rel := range []string{"internal/example/assets/extensionless", "internal/example/assets/future.custom", "internal/example/assets/.hidden", "internal/example/assets/_hidden", "internal/example/assets/matches_test.go", "vendor/example.test/mod/assets/embedded.payload"} {
		t.Run(rel, func(t *testing.T) { requireSourceInventoryOmission(t, sourceInventoryFixture(t, extra), rel) })
	}
}
