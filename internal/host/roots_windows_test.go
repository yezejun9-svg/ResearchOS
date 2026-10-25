//go:build windows

package host

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
	"unicode/utf16"
	"unicode/utf8"
)

func source43FixtureRoot(t *testing.T) string {
	t.Helper()
	base := os.Getenv("RESEARCHOS_SOURCE43_ASCII_FIXTURE_ROOT")
	if base == "" {
		base = os.TempDir()
	}
	base, err := filepath.Abs(base)
	if err != nil {
		t.Fatal(err)
	}
	if err := os.MkdirAll(base, 0o700); err != nil {
		t.Fatal(err)
	}
	root, err := os.MkdirTemp(base, "roots-windows-")
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() {
		resolvedBase, baseErr := filepath.EvalSymlinks(base)
		resolvedRoot, rootErr := filepath.EvalSymlinks(root)
		if baseErr != nil || rootErr != nil {
			t.Errorf("resolve fixture cleanup path: base=%v root=%v", baseErr, rootErr)
			return
		}
		rel, relErr := filepath.Rel(resolvedBase, resolvedRoot)
		if relErr != nil || rel == "." || rel == ".." || strings.HasPrefix(rel, ".."+string(filepath.Separator)) {
			t.Errorf("fixture cleanup escaped explicit root: %q, %v", rel, relErr)
			return
		}
		if err := os.RemoveAll(root); err != nil {
			t.Errorf("remove fixture: %v", err)
		}
	})
	return root
}

func TestBoundedFinalPathUTF16(t *testing.T) {
	want := `\\?\C:\作品集\工作区😀`
	units := utf16.Encode([]rune(want))
	buf := make([]uint16, len(units)+2)
	copy(buf, units)
	buf[len(units)] = 'X'
	got, err := boundedFinalPathUTF16(buf, uint32(len(units)))
	if err != nil || got != want {
		t.Fatalf("bounded conversion = %q, %v; want %q", got, err, want)
	}
	for _, n := range []uint32{0, uint32(len(buf)), uint32(len(buf) + 1)} {
		if got, err := boundedFinalPathUTF16(buf, n); err == nil || got != "" {
			t.Fatalf("invalid length %d accepted: %q, %v", n, got, err)
		}
	}
}

func TestFileIdentityUnicodeFinalPath(t *testing.T) {
	root := source43FixtureRoot(t)
	if os.Getenv("RESEARCHOS_SOURCE43_ASCII_FIXTURE_ROOT") != "" {
		for _, r := range root {
			if r > 127 {
				t.Fatalf("ASCII control fixture root is not ASCII: %q", root)
			}
		}
	}
	paths := map[string]string{
		"ascii-control":             filepath.Join(root, "ascii-control"),
		"CJK-ancestor-and-basename": filepath.Join(root, "父目录", "工作区"),
		"non-BMP":                   filepath.Join(root, "emoji-😀"),
		"common-prefix-one":         filepath.Join(root, "共同前缀", "collision-000001"),
		"common-prefix-two":         filepath.Join(root, "共同前缀", "collision-000002"),
	}
	type identity struct {
		volume string
		id     uint64
		final  string
	}
	seen := map[string]identity{}
	for label, path := range paths {
		if err := os.MkdirAll(path, 0o700); err != nil {
			t.Fatal(err)
		}
		volume, id, final, err := fileIdentity(path)
		if err != nil {
			t.Fatalf("%s: %v", label, err)
		}
		if !utf8.ValidString(final) || final != filepath.Clean(path) || volume == "" || id == 0 {
			t.Fatalf("%s: final=%q want=%q utf8=%v volume=%q id=%d", label, final, filepath.Clean(path), utf8.ValidString(final), volume, id)
		}
		seen[label] = identity{volume, id, final}
	}
	one, two := seen["common-prefix-one"], seen["common-prefix-two"]
	if one.final == two.final || (one.volume == two.volume && one.id == two.id) {
		t.Fatalf("distinct suffixes collapsed: one=%+v two=%+v", one, two)
	}
}

func TestRootRegistryUnicodeFinalPathRoundTrip(t *testing.T) {
	root := source43FixtureRoot(t)
	path := filepath.Join(root, "父目录", "工作区😀")
	if err := os.MkdirAll(path, 0o700); err != nil {
		t.Fatal(err)
	}
	_, _, expectedFinal, err := fileIdentity(path)
	if err != nil {
		t.Fatal(err)
	}
	registryDir := filepath.Join(root, "registry")
	registry, err := openRootRegistry(registryDir)
	if err != nil {
		t.Fatal(err)
	}
	const ref = "source43-unicode-root"
	binding, err := registry.Register(ref, path, AccessReadOnly, time.Date(2026, 10, 15, 0, 0, 0, 0, time.UTC))
	if err != nil {
		t.Fatal(err)
	}
	if binding.FinalPath != expectedFinal || binding.RealPath != filepath.Clean(path) || binding.VolumeID == "" || binding.FileID == 0 {
		t.Fatalf("registered root lost native path or identity: %+v", binding)
	}
	reopened, err := openRootRegistry(registryDir)
	if err != nil {
		t.Fatal(err)
	}
	got := reopened.roots[ref]
	if got == nil || got.FinalPath != expectedFinal || got.RealPath != filepath.Clean(path) || got.VolumeID != binding.VolumeID || got.FileID != binding.FileID || !utf8.ValidString(got.FinalPath) {
		t.Fatalf("reopened root lost full Unicode paths or identity: %+v", got)
	}
}
