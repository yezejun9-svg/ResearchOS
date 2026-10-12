//go:build windows

package supervisor

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"flag"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"testing"

	"golang.org/x/sys/windows"
)

var observedElectronPID = flag.Uint("observed-electron-pid", 0, "existing actual Electron PID; observe only, never signal or terminate")
var observedElectronHash = flag.String("observed-electron-sha256", "", "exact locked Electron executable SHA256")
var observedNodeExe = flag.String("observed-node-exe", "", "exact existing Node executable for an EOF-exiting identity child")
var observedReferenceImages = flag.String("observed-reference-images", "", "JSON array of exact existing Node/control/verifier executable paths")

func TestObservedActualElectronIdentity(t *testing.T) {
	if *observedElectronPID == 0 || !validDigest(*observedElectronHash) {
		t.Skip("explicit live Electron PID and pinned image hash required")
	}
	p, err := ObserveProcess(uint32(*observedElectronPID))
	if err != nil {
		t.Fatal("actual Electron identity observation:", err)
	}
	if p.PID != uint32(*observedElectronPID) || p.CreatedNS <= 0 || p.ImageSHA256 != *observedElectronHash {
		t.Fatalf("actual identity mismatch: %+v", p)
	}
	alive, err := (NativeFixtureDriver{}).Alive(p)
	if err != nil || !alive {
		t.Fatalf("exact observed identity was not alive: %v %v", alive, err)
	}
	for _, mutation := range []string{"created", "image"} {
		bad := p
		if mutation == "created" {
			bad.CreatedNS++
		} else {
			bad.ImageSHA256 = strings.Repeat("0", 64)
		}
		if alive, err = (NativeFixtureDriver{}).Alive(bad); err == nil || alive {
			t.Fatalf("mismatched %s identity accepted", mutation)
		}
	}
	t.Logf("OBSERVE_ONLY Electron PID=%d CreatedNS=%d SHA256=%s no_signal=true", p.PID, p.CreatedNS, p.ImageSHA256)
}

func TestObservedCurrentProcessIdentity(t *testing.T) {
	p, err := ObserveProcess(uint32(os.Getpid()))
	if err != nil {
		t.Fatal(err)
	}
	path, err := os.Executable()
	if err != nil {
		t.Fatal(err)
	}
	_, digest, err := exactImage(path)
	if err != nil || digest != p.ImageSHA256 {
		t.Fatal("small executable identity changed", err)
	}
	if alive, err := (NativeFixtureDriver{}).Alive(p); err != nil || !alive {
		t.Fatal("current process identity refused", err)
	}
}

func TestObservedImageBoundsAndReleaseGate(t *testing.T) {
	for _, size := range []int64{128*1024*1024 + 1, observedProcessImageMaxBytes, observedProcessImageMaxBytes + 1} {
		t.Run(strconv.FormatInt(size, 10), func(t *testing.T) {
			path := filepath.Join(t.TempDir(), "bounded.exe")
			f, err := os.Create(path)
			if err != nil {
				t.Fatal(err)
			}
			if err = f.Truncate(size); err != nil {
				f.Close()
				t.Fatal(err)
			}
			f.Close()
			digest, err := observedProcessImageDigest(path)
			if size > observedProcessImageMaxBytes {
				if err == nil || digest != "" {
					t.Fatal("oversized observed image accepted")
				}
			} else {
				if err != nil {
					t.Fatal(err)
				}
				f, err = os.Open(path)
				if err != nil {
					t.Fatal(err)
				}
				expected := sha256.New()
				_, err = io.Copy(expected, f)
				f.Close()
				if err != nil || digest != hex.EncodeToString(expected.Sum(nil)) {
					t.Fatal("bounded streamed digest differs", err)
				}
			}
			if _, _, err = exactImage(path); err == nil {
				t.Fatal("release image128MiB gate widened")
			}
			driver := NativeFixtureDriver{Args: func(string, string) []string { return []string{"never-start"} }}
			if p, err := driver.Start(path, "explicit-fixture-token", filepath.Dir(path)); err == nil || p.PID != 0 {
				t.Fatal("oversized native fixture reached process launch")
			}
		})
	}
}

func TestObservedImageRejectsNoncanonicalPaths(t *testing.T) {
	root := t.TempDir()
	real := filepath.Join(root, "real")
	if err := os.Mkdir(real, 0700); err != nil {
		t.Fatal(err)
	}
	image := filepath.Join(real, "image.exe")
	if err := os.WriteFile(image, []byte("read-only path fixture"), 0600); err != nil {
		t.Fatal(err)
	}
	link := filepath.Join(root, "junction")
	cmd := exec.Command("cmd.exe", "/d", "/c", "mklink", "/J", link, real)
	cmd.SysProcAttr = &windows.SysProcAttr{HideWindow: true}
	if raw, err := cmd.CombinedOutput(); err != nil {
		t.Fatalf("native owned junction: %v %s", err, raw)
	}
	t.Cleanup(func() {
		if err := os.Remove(link); err != nil {
			t.Errorf("remove owned junction: %v", err)
		}
	})
	for _, p := range []string{filepath.Join(link, "image.exe"), "relative.exe", real, filepath.Join(real, "missing.exe")} {
		if _, err := observedProcessImageDigest(p); err == nil {
			t.Fatalf("unsafe observed path accepted: %s", p)
		}
	}
}

func TestObservedReferenceImageDigests(t *testing.T) {
	if *observedReferenceImages == "" {
		t.Skip("explicit Node/control/verifier images required")
	}
	var paths []string
	if err := json.Unmarshal([]byte(*observedReferenceImages), &paths); err != nil || len(paths) != 3 {
		t.Fatal("three reference images required", err)
	}
	for _, path := range paths {
		t.Run(filepath.Base(path), func(t *testing.T) {
			_, old, err := exactImage(path)
			if err != nil {
				t.Fatal(err)
			}
			got, err := observedProcessImageDigest(path)
			if err != nil || got != old {
				t.Fatal("existing small image observation changed", err)
			}
		})
	}
}

func TestObservedNodeProcessIdentity(t *testing.T) {
	if *observedNodeExe == "" {
		t.Skip("explicit Node executable required")
	}
	path, digest, err := exactImage(*observedNodeExe)
	if err != nil {
		t.Fatal(err)
	}
	cmd := exec.Command(path, "-e", `process.stdin.resume(); process.stdin.on("end", () => process.exit(0));`)
	cmd.SysProcAttr = &windows.SysProcAttr{HideWindow: true}
	cmd.Env = []string{"SystemRoot=" + os.Getenv("SystemRoot")}
	in, err := cmd.StdinPipe()
	if err != nil {
		t.Fatal(err)
	}
	if err = cmd.Start(); err != nil {
		in.Close()
		t.Fatal(err)
	}
	defer func() {
		in.Close()
		if err := cmd.Wait(); err != nil {
			t.Errorf("owned Node did not exit normally on EOF: %v", err)
		}
	}()
	p, err := ObserveProcess(uint32(cmd.Process.Pid))
	if err != nil || p.ImageSHA256 != digest {
		t.Fatal("actual Node identity changed", err)
	}
	if alive, err := (NativeFixtureDriver{}).Alive(p); err != nil || !alive {
		t.Fatal("actual Node identity is not alive", err)
	}
	t.Logf("owned Node PID=%d identity matched; cleanup=stdin_EOF only", p.PID)
}
