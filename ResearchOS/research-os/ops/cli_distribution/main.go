// Command cli_distribution produces the W05-03 Windows CLI distribution candidate and verifies it in place: it builds
// apps/cli, installs the binary plus a cmd shim into a target directory, launches the installed program there, and
// grades the answers. The target is deliberately allowed to contain spaces and non-ASCII characters because that is
// the case the card names; a candidate that only works under a clean ASCII path is not a Windows candidate.
//
// It prints one JSON report line in the shape the command dispatcher accepts (status / assertions / assertion_ids /
// failures / not_verified) so the construction check can drive it and a reviewer can read the same numbers.
package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"sort"
	"strings"
)

var (
	ids      []string
	failures []map[string]string
	notVer   []string
	// versionDigest is published in the report so the leg can be cross-checked by a reader who runs the same binary.
	versionDigest = ""
)

func sha256hex(s string) string {
	h := sha256.Sum256([]byte(s))
	return hex.EncodeToString(h[:])
}

func clipDigest(s string) string { return "sha256=" + sha256hex(s)[:16] + " bytes=" + fmt.Sprint(len(s)) }

func ok(label string, cond bool, detail ...any) {
	if cond {
		ids = append(ids, label)
		return
	}
	parts := make([]string, 0, len(detail))
	for _, d := range detail {
		s := fmt.Sprint(d)
		if len(s) > 400 {
			s = s[:400]
		}
		parts = append(parts, s)
	}
	failures = append(failures, map[string]string{"id": label, "detail": strings.Join(parts, " | ")})
}

func skip(label, reason string) { notVer = append(notVer, label+": "+reason) }

func goExe() string {
	if v := os.Getenv("RESEARCHOS_GO"); v != "" {
		return v
	}
	return filepath.Join(".local", "tools", "go1.27.1", "go", "bin", "go.exe")
}

func sha(p string) string {
	b, err := os.ReadFile(p)
	if err != nil {
		return "unreadable:" + err.Error()
	}
	h := sha256.Sum256(b)
	return hex.EncodeToString(h[:])
}

// installed runs the program that now lives in the target directory, with no repository-relative assumption: the
// working directory is the target itself, so a path bug would show up as a failed launch rather than as a silent
// fallback to the build tree.
func installed(exe string, args ...string) (int, string, string, error) {
	c := exec.Command(exe, args...)
	c.Dir = filepath.Dir(exe)
	var so, se bytes.Buffer
	c.Stdout, c.Stderr = &so, &se
	err := c.Run()
	code := 0
	if ee, isExit := err.(*exec.ExitError); isExit {
		code = ee.ExitCode()
	}
	return code, so.String(), se.String(), err
}

func main() {
	repo := flag.String("repo", ".", "repository root to build from")
	target := flag.String("target", "", "install directory; may contain spaces and non-ASCII characters")
	flag.Parse()
	defer func() {
		if r := recover(); r != nil {
			failures = append(failures, map[string]string{"id": "PANIC", "detail": fmt.Sprint(r)})
		}
		if len(ids) == 0 && len(failures) == 0 {
			failures = append(failures, map[string]string{"id": "NO-ASSERTIONS-RECORDED",
				"detail": "a candidate that measured nothing is not a candidate"})
		}
		status := "PASS"
		if len(failures) > 0 {
			status = "FAIL"
		}
		if len(ids) == 0 {
			status = "FAIL"
		}
		sort.Strings(ids)
		f := failures
		if f == nil {
			f = []map[string]string{}
		}
		nv := notVer
		if nv == nil {
			nv = []string{}
		}
		out, _ := json.Marshal(map[string]any{"status": status, "assertions": len(ids), "assertion_ids": ids,
			"failures": f, "not_verified": nv, "target": *target, "os": runtime.GOOS,
			"installed_version_sha256": versionDigest,
			"scope": "DISTRIBUTION_CANDIDATE_NOT_FINAL_RELEASE", "owner_card": "W05-03",
			"final_release_reverification": "owned by W20"})
		fmt.Println(string(out))
		if len(failures) > 0 || len(ids) == 0 {
			os.Exit(1)
		}
	}()

	if *target == "" {
		ok("DIST-TARGET-GIVEN", false, "-target is required")
		return
	}
	absTarget, err := filepath.Abs(*target)
	if err != nil {
		ok("DIST-TARGET-RESOLVES", false, err)
		return
	}
	ok("DIST-TARGET-RESOLVES", true, absTarget)
	if err := os.MkdirAll(absTarget, 0o700); err != nil {
		ok("DIST-TARGET-CREATABLE", false, err)
		return
	}
	ok("DIST-TARGET-CREATABLE", true)
	// The card's named condition, asserted on the path that is actually used rather than claimed about it.
	ok("DIST-TARGET-HAS-SPACE-AND-NON-ASCII", strings.Contains(filepath.Base(absTarget), " ") &&
		!isASCII(absTarget), absTarget)

	exeName := "researchos.exe"
	if runtime.GOOS != "windows" {
		exeName = "researchos"
		skip("DIST-BUILDS", "this candidate targets Windows; host is "+runtime.GOOS)
		return
	}
	exe := filepath.Join(absTarget, exeName)
	build := exec.Command(goExe(), "build", "-o", exe, "./apps/cli")
	build.Dir = *repo
	build.Env = append(os.Environ(), "GOTOOLCHAIN=local", "GOENV=off")
	if out, err := build.CombinedOutput(); err != nil {
		ok("DIST-BUILDS", false, err, string(out))
		return
	}
	info, err := os.Stat(exe)
	ok("DIST-BUILDS", err == nil && info.Size() > 100000, err, info)

	// The shim is the thing a user actually types. It must point at this install's own binary and quote the path,
	// because an unquoted path containing a space silently launches a different program.
	shim := filepath.Join(absTarget, "researchos.cmd")
	shimText := "@echo off\r\n\"%~dp0" + exeName + "\" %*\r\n"
	if err := os.WriteFile(shim, []byte(shimText), 0o600); err != nil {
		ok("DIST-SHIM-WRITTEN", false, err)
		return
	}
	ok("DIST-SHIM-WRITTEN", true, shim)
	shimRaw, _ := os.ReadFile(shim)
	ok("DIST-SHIM-QUOTES-OWN-BINARY", strings.Contains(string(shimRaw), `"%~dp0`+exeName) &&
		!strings.Contains(strings.ToLower(string(shimRaw)), "claude") &&
		!strings.Contains(strings.ToLower(string(shimRaw)), "codex"), string(shimRaw))

	// Launch from the install directory: the contract must hold there, not only in the build tree. The observed bytes
	// are published as a digest so a reader can tell whether this leg really ran the installed process or recited an
	// answer, and the construction check compares that digest against its own launch of the same file.
	code, stdout, stderr, err := installed(exe, "version")
	ok("DIST-INSTALLED-VERSION-BYTES-PUBLISHED", len(strings.TrimSpace(stdout)) > 0, clipDigest(stdout))
	versionDigest = sha256hex(stdout)
	var vrec map[string]any
	_ = json.Unmarshal([]byte(strings.TrimSpace(firstLine(stdout))), &vrec)
	ok("DIST-INSTALLED-LAUNCHES", err == nil && code == 0 && fmt.Sprint(vrec["status"]) == "COMPLETED",
		code, strings.TrimSpace(stdout), stderr, err)
	ok("DIST-INSTALLED-STDOUT-JSONL-ONLY", len(nonEmptyLines(stdout)) == 1 &&
		strings.HasPrefix(strings.TrimSpace(firstLine(stdout)), "{"), lines(stdout))

	code, stdout, stderr, _ = installed(exe, "commands")
	var crec map[string]any
	_ = json.Unmarshal([]byte(strings.TrimSpace(firstLine(stdout))), &crec)
	list, _ := crec["commands"].([]any)
	missingH := fmt.Sprint(crec["missing_handler"])
	missingC := fmt.Sprint(crec["missing_check"])
	ok("DIST-INSTALLED-COMMAND-SURFACE-INTACT", code == 0 && len(list) >= 15 && missingH == "[]" && missingC == "[]",
		code, len(list), missingH, missingC, strings.TrimSpace(stdout), stderr)

	// A refused verb must still refuse from the install, so packaging cannot quietly turn NOT_IMPLEMENTED into success.
	code, stdout, _, _ = installed(exe, "chat")
	ok("DIST-INSTALLED-REFUSAL-STILL-REFUSES", code == 3 && strings.Contains(stdout, "NOT_IMPLEMENTED"), code, stdout)

	// The install must be a real, self-contained artefact: the report names its digest, and nothing is left pointing
	// at the build tree.
	digest := sha(exe)
	ok("DIST-INSTALLED-BINARY-DIGEST-RECORDED", len(digest) == 64, digest)
	fmt.Fprintf(os.Stderr, "cli_distribution: installed %s sha256=%s\n", exe, digest)
}

func firstLine(s string) string {
	for _, l := range strings.Split(strings.ReplaceAll(s, "\r\n", "\n"), "\n") {
		if strings.TrimSpace(l) != "" {
			return l
		}
	}
	return ""
}

func nonEmptyLines(s string) []string {
	out := []string{}
	for _, l := range strings.Split(strings.ReplaceAll(s, "\r\n", "\n"), "\n") {
		if strings.TrimSpace(l) != "" {
			out = append(out, l)
		}
	}
	return out
}

func lines(s string) string { return fmt.Sprint(len(nonEmptyLines(s))) }

func isASCII(s string) bool {
	for _, r := range s {
		if r > 127 {
			return false
		}
	}
	return true
}
