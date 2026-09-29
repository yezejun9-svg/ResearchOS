package retrieval

import (
	"os"
	"os/exec"
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
		if output, err := exec.Command("cmd.exe", "/c", "mklink", "/J", link, b).CombinedOutput(); err != nil {
			t.Fatalf("junction fixture unavailable: %v: %s", err, output)
		}
	} else if err := os.Symlink(b, link); err != nil {
		t.Fatal(err)
	}
	if got, err := ReadFile(a, filepath.Join("outside", "same.txt")); err == nil {
		t.Fatalf("outside link returned %q", got)
	}
}

func TestW09RootIdentityRejectsReplacement(t *testing.T) {
	base := t.TempDir()
	a, b := filepath.Join(base, "A"), filepath.Join(base, "B")
	for _, path := range []string{a, b} {
		if err := os.Mkdir(path, 0700); err != nil {
			t.Fatal(err)
		}
	}
	if err := os.WriteFile(filepath.Join(a, "same.txt"), []byte("authorized"), 0600); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(b, "same.txt"), []byte("SECRET-B-UNAUTHORIZED"), 0600); err != nil {
		t.Fatal(err)
	}
	identity, err := Identity(a)
	if err != nil {
		t.Fatal(err)
	}
	if data, readErr := ReadFileBound(a, "", "same.txt"); readErr == nil {
		t.Fatalf("unidentified legacy root disclosed %q", data)
	}
	if err = os.Rename(a, filepath.Join(base, "A-original")); err != nil {
		t.Fatal(err)
	}
	if runtime.GOOS == "windows" {
		if output, createErr := exec.Command("cmd.exe", "/c", "mklink", "/J", a, b).CombinedOutput(); createErr != nil {
			t.Fatalf("junction fixture unavailable: %v: %s", createErr, output)
		}
	} else if err = os.Symlink(b, a); err != nil {
		t.Fatal(err)
	}
	if data, readErr := ReadFileBound(a, identity, "same.txt"); readErr == nil {
		t.Fatalf("replaced root disclosed %q", data)
	}
}
