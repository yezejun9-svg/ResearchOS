//go:build windows

package main

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"golang.org/x/sys/windows"
	"io"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"sync"
	"unicode/utf16"
)

const stageARoot = `C:\Users\yqyyds\Documents\Codex\2026-11-04\task\cp586-continuation\owned-model-resource`
const stageBRoot = `C:\Users\yqyyds\Documents\Codex\2026-11-04\task\cp586-continuation\owned-model-resource-stage-b\revision-04`
const stageASHA = "1ee48d848976e0d1aff869c474516cc6ce90bdc7373fd2735b27b6dc6b61fd24"
const modelSHA = "0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0"
const endpoint = "http://127.0.0.1:43861"
const desiredVersion = "0.30.0-rc31"
const modelName = "qwen3:4b-instruct"
const streamBound = 2 << 20

type asset struct {
	Source      string `json:"source"`
	Destination string `json:"destination"`
	Relative    string `json:"destination_relative"`
	Bytes       int64  `json:"bytes"`
	SourceSHA   string `json:"source_sha256"`
	TargetSHA   string `json:"destination_sha256"`
	Verified    bool   `json:"verified"`
}
type assetManifest struct {
	Status string  `json:"status"`
	Count  int     `json:"verified_asset_file_count"`
	Bytes  int64   `json:"asset_bytes"`
	Assets []asset `json:"assets"`
}

func writeNew(path string, v any) error {
	b, e := json.MarshalIndent(v, "", "  ")
	if e != nil {
		return e
	}
	f, e := os.OpenFile(path, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if e != nil {
		return e
	}
	defer f.Close()
	if _, e = f.Write(append(b, '\n')); e != nil {
		return e
	}
	return f.Sync()
}
func hashFile(path string) (string, error) {
	f, e := os.Open(path)
	if e != nil {
		return "", e
	}
	defer f.Close()
	h := sha256.New()
	if _, e = io.Copy(h, f); e != nil {
		return "", e
	}
	return hex.EncodeToString(h.Sum(nil)), nil
}
func utf(s string) *uint16 {
	p, e := windows.UTF16PtrFromString(s)
	if e != nil {
		panic(e)
	}
	return p
}
func plain(path string) error {
	for p := filepath.Clean(path); p != ""; p = filepath.Dir(p) {
		a, e := windows.GetFileAttributes(utf(p))
		if e != nil {
			return e
		}
		if a&windows.FILE_ATTRIBUTE_REPARSE_POINT != 0 {
			return fmt.Errorf("reparse refused: %s", p)
		}
		if filepath.Dir(p) == p {
			break
		}
	}
	return nil
}
func under(root, path string) bool {
	r, e := filepath.Rel(root, path)
	return e == nil && r != "." && r != ".." && !strings.HasPrefix(r, ".."+string(filepath.Separator)) && !filepath.IsAbs(r)
}
func verifyAssets() (assetManifest, error) {
	var m assetManifest
	p := filepath.Join(stageARoot, "MANIFEST.json")
	h, e := hashFile(p)
	if e != nil || h != stageASHA {
		return m, fmt.Errorf("Stage A manifest pin differs: %w", e)
	}
	b, e := os.ReadFile(p)
	if e != nil {
		return m, e
	}
	if e = json.Unmarshal(b, &m); e != nil {
		return m, e
	}
	if m.Status != "ASSETS_STAGED_NOT_STARTED" || m.Count != 981 || len(m.Assets) != 981 || m.Bytes != 5686303776 {
		return m, errors.New("Stage A count/status differs")
	}
	seen := map[string]bool{}
	var total int64
	for _, a := range m.Assets {
		if !under(stageARoot, a.Destination) || a.SourceSHA != a.TargetSHA || !a.Verified {
			return m, errors.New("asset identity differs")
		}
		k := strings.ToLower(filepath.Clean(a.Destination))
		if seen[k] {
			return m, errors.New("duplicate asset")
		}
		seen[k] = true
		if e = plain(a.Destination); e != nil {
			return m, e
		}
		info, e := os.Stat(a.Destination)
		if e != nil || !info.Mode().IsRegular() || info.Size() != a.Bytes {
			return m, fmt.Errorf("asset size/type differs: %s", a.Relative)
		}
		h, e := hashFile(a.Destination)
		if e != nil || h != a.TargetSHA {
			return m, fmt.Errorf("asset SHA differs: %s", a.Relative)
		}
		total += a.Bytes
	}
	actual := 0
	for _, dir := range []string{"runtime", "models"} {
		e = filepath.WalkDir(filepath.Join(stageARoot, dir), func(p string, d os.DirEntry, e error) error {
			if e != nil {
				return e
			}
			if d.Type()&os.ModeSymlink != 0 {
				return errors.New("asset link refused")
			}
			if !d.IsDir() {
				actual++
				if !seen[strings.ToLower(filepath.Clean(p))] {
					return errors.New("undeclared asset")
				}
			}
			return nil
		})
		if e != nil {
			return m, e
		}
	}
	if actual != 981 || total != m.Bytes {
		return m, errors.New("asset roster differs")
	}
	for _, p := range []string{"profile/.ollama", "profile/AppData/Local", "profile/AppData/Roaming", "tmp"} {
		entries, e := os.ReadDir(filepath.Join(stageARoot, p))
		if e != nil || len(entries) != 0 {
			return m, errors.New("Stage A empty profile changed")
		}
	}
	return m, nil
}
func childEnvironment(run string) ([]uint16, []string, error) {
	system := os.Getenv("SystemRoot")
	if !filepath.IsAbs(system) {
		return nil, nil, errors.New("absolute SystemRoot required")
	}
	profile := filepath.Join(run, "profile")
	local := filepath.Join(profile, "AppData", "Local")
	roam := filepath.Join(profile, "AppData", "Roaming")
	tmp := filepath.Join(run, "tmp")
	for _, d := range []string{filepath.Join(profile, ".ollama"), local, roam, tmp} {
		if e := os.MkdirAll(d, 0700); e != nil {
			return nil, nil, e
		}
		if e := plain(d); e != nil {
			return nil, nil, e
		}
	}
	env := map[string]string{"SystemRoot": system, "WINDIR": system, "USERPROFILE": profile, "LOCALAPPDATA": local, "APPDATA": roam, "TEMP": tmp, "TMP": tmp, "PATH": strings.Join([]string{filepath.Join(stageARoot, "runtime"), filepath.Join(stageARoot, "runtime", "lib", "ollama"), filepath.Join(system, "System32")}, ";"), "OLLAMA_HOST": "127.0.0.1:43861", "OLLAMA_MODELS": filepath.Join(stageARoot, "models"), "OLLAMA_NO_CLOUD": "1", "OLLAMA_NOPRUNE": "1", "OLLAMA_DEBUG": "0", "OLLAMA_NOHISTORY": "1"}
	keys := make([]string, 0, len(env))
	for k := range env {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	pairs := []string{}
	for _, k := range keys {
		pairs = append(pairs, k+"="+env[k])
	}
	return utf16.Encode([]rune(strings.Join(pairs, "\x00") + "\x00\x00")), keys, nil
}

type boundedLog struct {
	mu       sync.Mutex
	f        *os.File
	count    int64
	overflow bool
	tail     []byte
	done     chan error
}

func (b *boundedLog) Write(p []byte) (int, error) {
	b.mu.Lock()
	defer b.mu.Unlock()
	n := len(p)
	b.count += int64(n)
	if b.count <= streamBound {
		if _, e := b.f.Write(p); e != nil {
			return 0, e
		}
	} else {
		b.overflow = true
	}
	b.tail = append(b.tail, p...)
	if len(b.tail) > 65536 {
		b.tail = b.tail[len(b.tail)-65536:]
	}
	return n, nil
}
func (b *boundedLog) has(s string) bool {
	b.mu.Lock()
	defer b.mu.Unlock()
	return strings.Contains(string(b.tail), s)
}
func (b *boundedLog) exceeded() bool { b.mu.Lock(); defer b.mu.Unlock(); return b.overflow }
func startLog(read *os.File, path string) (*boundedLog, error) {
	f, e := os.OpenFile(path, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if e != nil {
		return nil, e
	}
	b := &boundedLog{f: f, done: make(chan error, 1)}
	go func() { _, e := io.Copy(b, read); e = errors.Join(e, f.Sync(), f.Close(), read.Close()); b.done <- e }()
	return b, nil
}
