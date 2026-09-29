package retrieval

import (
	"os"
	"path/filepath"
	"runtime"
	"testing"
)

func TestW09RootReadRejectsEscape(t *testing.T) {
	base := t.TempDir()
	a, b := filepath.Join(base, "A"), filepath.Join(base, "B")
	for _, path := range []string{a, b} {
		if err := os.Mkdir(path, 0700); err != nil {
			t.Fatal(err)
		}
	}
	if err := os.WriteFile(filepath.Join(a, "same.txt"), []byte("allowed"), 0600); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(b, "same.txt"), []byte("secret-marker"), 0600); err != nil {
		t.Fatal(err)
	}
	got, err := ReadFile(a, "same.txt")
	if err != nil || string(got) != "allowed" {
		t.Fatalf("root read %q %v", got, err)
	}
	for _, path := range []string{"../B/same.txt", filepath.Join(b, "same.txt"), "../../same.txt"} {
		if got, err := ReadFile(a, path); err == nil {
			t.Fatalf("escape %s returned %q", path, got)
		}
	}
	link := filepath.Join(a, "outside")
	if runtime.GOOS == "windows" {
		if err := os.Symlink(b, link); err != nil {
			t.Skipf("link privilege unavailable: %v", err)
		}
	} else if err := os.Symlink(b, link); err != nil {
		t.Fatal(err)
	}
	if got, err := ReadFile(a, filepath.Join("outside", "same.txt")); err == nil {
		t.Fatalf("outside link returned %q", got)
	}
}
