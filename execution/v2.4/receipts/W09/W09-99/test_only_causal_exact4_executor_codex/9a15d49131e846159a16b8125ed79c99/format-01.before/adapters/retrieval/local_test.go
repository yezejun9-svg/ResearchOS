package retrieval

import (
	"errors"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
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

// Causal controls added under W09 r320. OS link capability is a prerequisite,
// never a reason to substitute another classifier or report a skipped PASS.
func w09CausalRootFixture(t *testing.T) (string, string, string) {
	t.Helper()
	base := t.TempDir()
	a, b := filepath.Join(base, "A"), filepath.Join(base, "B")
	for _, p := range []string{a, b} {
		if err := os.Mkdir(p, 0700); err != nil { t.Fatal(err) }
		if err := os.WriteFile(filepath.Join(p, "same.txt"), []byte("owned-public-marker"), 0600); err != nil { t.Fatal(err) }
	}
	id, err := Identity(a)
	if err != nil || id == "" { t.Fatalf("root identity: %q %v", id, err) }
	got, err := ReadFileBound(a, id, "same.txt")
	if err != nil || string(got) != "owned-public-marker" { t.Fatalf("positive bound read: %q %v", got, err) }
	return a, b, id
}

func w09CausalRootRefusal(t *testing.T, body []byte, err error, exact string) {
	t.Helper()
	if len(body) != 0 || err == nil || err.Error() != exact { t.Fatalf("exact refusal: body=%q err=%v want=%q", body, err, exact) }
	t.Logf("W09_CAUSAL_FIXTURE reason=%q body_bytes=%d", err.Error(), len(body))
}

func TestW09CausalRootBoundReadPositive(t *testing.T) { w09CausalRootFixture(t) }

func TestW09CausalRootMissingIdentity(t *testing.T) {
	a, _, _ := w09CausalRootFixture(t)
	b, err := ReadFileBound(a, "", "same.txt")
	w09CausalRootRefusal(t, b, err, "registered root identity missing")
}

func TestW09CausalRootChangedIdentity(t *testing.T) {
	_, b, idA := w09CausalRootFixture(t)
	idB, err := Identity(b)
	if err != nil || idB == "" || idB == idA { t.Fatalf("distinct actual roots: %q %q %v", idA, idB, err) }
	good, err := ReadFileBound(b, idB, "same.txt")
	if err != nil || string(good) != "owned-public-marker" { t.Fatal("B positive", err) }
	got, err := ReadFileBound(b, idA, "same.txt")
	w09CausalRootRefusal(t, got, err, "registered root identity changed")
}

func TestW09CausalRootLexicalPrecheck(t *testing.T) {
	for _, name := range []string{"Absolute", "Traversal", "Empty", "Dot"} {
		t.Run(name, func(t *testing.T) {
			a, b, id := w09CausalRootFixture(t)
			missing := filepath.Join(filepath.Dir(a), "never-created")
			_, original := ReadFileBound(missing, id, "same.txt")
			var pathError *os.PathError
			if original == nil || !errors.As(original, &pathError) || original.Error() == "path is not root-relative" { t.Fatal("missing-root control", original) }
			rel := map[string]string{"Absolute":filepath.Join(b,"same.txt"),"Traversal":"../B/same.txt","Empty":"","Dot":"."}[name]
			got, err := ReadFileBound(missing, id, rel)
			w09CausalRootRefusal(t, got, err, "path is not root-relative")
		})
	}
}

func w09CausalRootAbsence(t *testing.T, rel, prefix string) {
	t.Helper()
	a, _, id := w09CausalRootFixture(t)
	got, err := ReadFileBound(a, id, rel)
	var original *os.PathError
	if len(got) != 0 || err == nil || !strings.HasPrefix(err.Error(), prefix+": ") || !errors.As(err, &original) { t.Fatalf("classifier mismatch: %q %v", got, err) }
	t.Logf("W09_CAUSAL_FIXTURE classifier=%q original_type=%T", err.Error(), original)
}

func TestW09CausalRootClassifierFinalAbsence(t *testing.T) {
	w09CausalRootAbsence(t, "missing.txt", "path is not present inside the registered root")
}

func TestW09CausalRootClassifierIntermediateAbsence(t *testing.T) {
	w09CausalRootAbsence(t, "missing/leaf.txt", `path component "missing" could not be inspected inside the registered root`)
}

func TestW09CausalRootClassifierFallback(t *testing.T) {
	a, _, _ := w09CausalRootFixture(t)
	root, err := os.OpenRoot(a)
	if err != nil { t.Fatal(err) }
	defer root.Close()
	original := errors.New("W09_SYNTHETIC_OPEN_FAILURE")
	err = classifyOpen(root, "same.txt", original)
	if err == nil || err.Error() != "registered root refused the path: W09_SYNTHETIC_OPEN_FAILURE" || !errors.Is(err, original) { t.Fatal("fallback lost original cause", err) }
	t.Log("PURE_CLASSIFIER_WITH_OS_LSTAT: injected openErr, not an actual OS open refusal")
}

func TestW09CausalRootClassifierSymlink(t *testing.T) {
	a, b, id := w09CausalRootFixture(t)
	link := filepath.Join(a, "outside")
	if err := os.Symlink(b, link); err != nil { t.Fatalf("RESOURCE_PRECONDITION_UNAVAILABLE: actual symlink: %v", err) }
	info, err := os.Lstat(link)
	if err != nil || info.Mode()&os.ModeSymlink == 0 { t.Fatalf("wrong actual symlink mode: %v %v", info, err) }
	got, err := ReadFileBound(a, id, "outside/same.txt")
	w09CausalRootRefusal(t, got, err, fmt.Sprintf("path component %q is a symbolic link to %q; snapshots must be a regular file inside the registered root", "outside", b))
}

func TestW09CausalRootClassifierJunction(t *testing.T) {
	// Future authorized controller creates exactly this public fixture under its
	// owned Job. This test starts no unowned cmd.exe and never creates a link in
	// an existing user directory. Resource absence is a failed prerequisite/HOLD.
	base := os.Getenv("RESEARCHOS_W09_CAUSAL_LINK_RESOURCE")
	if runtime.GOOS != "windows" || !filepath.IsAbs(base) { t.Fatal("RESOURCE_PRECONDITION_UNAVAILABLE: owned Windows junction fixture") }
	a := filepath.Join(base, "A")
	info, err := os.Lstat(filepath.Join(a, "outside"))
	if err != nil || info.Mode()&os.ModeSymlink != 0 || info.Mode().IsRegular() || info.Mode().IsDir() { t.Fatalf("RESOURCE_PRECONDITION_UNAVAILABLE: actual irregular reparse mode: %v %v", info, err) }
	id, err := Identity(a)
	if err != nil { t.Fatal(err) }
	good, err := ReadFileBound(a, id, "same.txt")
	if err != nil || string(good) != "owned-public-marker" { t.Fatal("junction regular control", err) }
	got, err := ReadFileBound(a, id, "outside/same.txt")
	w09CausalRootRefusal(t, got, err, fmt.Sprintf("path component %q is a link or reparse point with irregular mode %s; snapshots must be a regular file inside the registered root", "outside", info.Mode()))
}
