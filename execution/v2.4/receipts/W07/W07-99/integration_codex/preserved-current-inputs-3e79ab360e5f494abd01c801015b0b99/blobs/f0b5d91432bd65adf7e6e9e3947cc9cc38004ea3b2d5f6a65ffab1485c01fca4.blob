//go:build windows

package supervisor

import (
	"bytes"
	"context"
	"debug/buildinfo"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"syscall"

	"golang.org/x/sys/windows"
	"researchos.local/research-os/evaluation/evolution"
)

func controlAuthorityFileID(path string, directory bool) (string, error) {
	abs, err := filepath.Abs(path)
	if err != nil || abs != filepath.Clean(path) || strings.HasPrefix(path, `\\`) {
		return "", fmt.Errorf("CONTROL_AUTHORITY_PLAIN_PATH")
	}
	real, err := filepath.EvalSymlinks(path)
	if err != nil || !strings.EqualFold(real, path) {
		return "", fmt.Errorf("CONTROL_AUTHORITY_REPARSE")
	}
	p, err := windows.UTF16PtrFromString(path)
	if err != nil {
		return "", err
	}
	h, err := windows.CreateFile(p, windows.FILE_READ_ATTRIBUTES, windows.FILE_SHARE_READ|windows.FILE_SHARE_WRITE|windows.FILE_SHARE_DELETE, nil, windows.OPEN_EXISTING, windows.FILE_FLAG_BACKUP_SEMANTICS|windows.FILE_FLAG_OPEN_REPARSE_POINT, 0)
	if err != nil {
		return "", err
	}
	defer windows.CloseHandle(h)
	var info windows.ByHandleFileInformation
	if err = windows.GetFileInformationByHandle(h, &info); err != nil || info.FileAttributes&windows.FILE_ATTRIBUTE_REPARSE_POINT != 0 || (info.FileAttributes&windows.FILE_ATTRIBUTE_DIRECTORY != 0) != directory {
		return "", fmt.Errorf("CONTROL_AUTHORITY_FILE_ID")
	}
	return evolution.Digest(evolution.Bytes([]uint32{info.VolumeSerialNumber, info.FileIndexHigh, info.FileIndexLow})), nil
}

// ObserveControlAuthorityOwner never accepts a caller assertion about the PID.
// The caller must additionally hold its existing DataRootLease for this root.
func ObserveControlAuthorityOwner(root, database, stableHash string) (evolution.ControlAuthorityOwner, error) {
	o := evolution.ControlAuthorityOwner{Root: root, Database: database, PID: uint32(os.Getpid()), StableHash: stableHash}
	if !strings.EqualFold(filepath.Dir(database), root) {
		return o, fmt.Errorf("CONTROL_AUTHORITY_DATABASE_ROOT")
	}
	var err error
	if o.RootIdentity, err = controlAuthorityFileID(root, true); err != nil {
		return o, err
	}
	if o.DatabaseID, err = controlAuthorityFileID(database, false); err != nil {
		return o, err
	}
	h := windows.CurrentProcess()
	var created, exited, kernel, user windows.Filetime
	if err = windows.GetProcessTimes(h, &created, &exited, &kernel, &user); err != nil {
		return o, err
	}
	o.CreatedNS = created.Nanoseconds()
	buf := make([]uint16, 32768)
	size := uint32(len(buf))
	if err = windows.QueryFullProcessImageName(h, 0, &buf[0], &size); err != nil {
		return o, err
	}
	o.Image = windows.UTF16ToString(buf[:size])
	if _, err = controlAuthorityFileID(o.Image, false); err != nil {
		return o, err
	}
	raw, err := os.ReadFile(o.Image)
	if err != nil {
		return o, err
	}
	o.ImageHash = evolution.Digest(raw)
	info, err := buildinfo.Read(bytes.NewReader(raw))
	if err != nil || info.Path != "researchos.local/research-os/apps/control" || o.ImageHash != stableHash || o.CreatedNS <= 0 {
		return o, fmt.Errorf("CONTROL_AUTHORITY_OWNER_IS_NOT_ACCEPTED_CONTROL")
	}
	settings := map[string]string{}
	for _, v := range info.Settings {
		settings[v.Key] = v.Value
	}
	if settings["GOOS"] != "windows" || settings["GOARCH"] != "amd64" {
		return o, fmt.Errorf("CONTROL_AUTHORITY_PLATFORM")
	}
	o.Qualified = true
	return o, nil
}

// Source inventory is independently enumerated, so omitted files cannot pass.
// Test helpers are not compiled into the control image. Frozen SQL/contracts
// and module files are included in addition to all product Go source roots.
func ControlSourceInventory(root string) (map[string]string, error) {
	if _, err := controlAuthorityFileID(root, true); err != nil {
		return nil, err
	}
	files := map[string]string{}
	read := func(relative string) error {
		path := filepath.Join(root, filepath.FromSlash(relative))
		if _, err := controlAuthorityFileID(path, false); err != nil {
			return err
		}
		raw, err := os.ReadFile(path)
		if err != nil {
			return err
		}
		files[relative] = evolution.Digest(raw)
		return nil
	}
	for _, dir := range []string{"apps/control", "internal", "adapters", "evaluation", "ops"} {
		err := filepath.WalkDir(filepath.Join(root, filepath.FromSlash(dir)), func(path string, entry os.DirEntry, err error) error {
			if err != nil {
				return err
			}
			if entry.Type()&os.ModeSymlink != 0 {
				return fmt.Errorf("CONTROL_SOURCE_REPARSE")
			}
			compiled := strings.HasSuffix(path, ".go") || strings.HasSuffix(path, ".s") || strings.HasSuffix(path, ".h") || strings.HasSuffix(path, ".c") || strings.HasSuffix(path, ".syso")
			if entry.IsDir() || !compiled || strings.HasSuffix(path, "_test.go") {
				return nil
			}
			rel, err := filepath.Rel(root, path)
			if err != nil || !filepath.IsLocal(rel) {
				return fmt.Errorf("CONTROL_SOURCE_SCOPE")
			}
			return read(filepath.ToSlash(rel))
		})
		if err != nil {
			return nil, err
		}
	}
	for _, file := range []string{"go.mod", "go.sum", "execution/toolchains/locked.json", "adapters/protectedstore/frozen_development.json"} {
		if err := read(file); err != nil {
			return nil, err
		}
	}
	for file, expected := range evolution.ControlReleaseHashes() {
		if err := read(file); err != nil {
			return nil, err
		}
		if files[file] != expected {
			return nil, fmt.Errorf("CONTROL_SOURCE_RELEASE_BYTES")
		}
	}
	return files, nil
}

func ControlBuildProvenance(raw []byte, root string) (evolution.ControlSourceProvenance, error) {
	p := evolution.ControlSourceProvenance{Root: root}
	info, err := buildinfo.Read(bytes.NewReader(raw))
	if err != nil || info.Path != "researchos.local/research-os/apps/control" || info.Main.Path != "researchos.local/research-os" {
		return p, fmt.Errorf("CONTROL_BUILD_PROVENANCE_APPLICATION")
	}
	settings := map[string]string{}
	for _, v := range info.Settings {
		settings[v.Key] = v.Value
	}
	if settings["GOOS"] != "windows" || settings["GOARCH"] != "amd64" || settings["-trimpath"] != "true" || settings["CGO_ENABLED"] != "0" || settings["vcs.revision"] != "" {
		return p, fmt.Errorf("CONTROL_BUILD_PROVENANCE_SETTINGS")
	}
	p.Commit, p.Modified, p.Toolchain = settings["vcs.revision"], settings["vcs.modified"] == "true", info.GoVersion
	p.ModuleHash = evolution.Digest(evolution.Bytes(info.Deps))
	p.Files, err = ControlSourceInventory(root)
	if err != nil {
		return p, err
	}
	p.InventoryHash = evolution.Digest(evolution.Bytes(p.Files))
	return p, nil
}

func VerifyControlBuildProvenance(raw []byte, expected evolution.ControlSourceProvenance) error {
	got, err := ControlBuildProvenance(raw, expected.Root)
	if err != nil {
		return err
	}
	if !bytes.Equal(evolution.Bytes(got), evolution.Bytes(expected)) {
		return fmt.Errorf("CONTROL_BUILD_SOURCE_CHANGED")
	}
	return nil
}

// RebuildControlSource establishes a byte binding to approved local source;
// build-info or a caller-authored report alone never qualifies the binary.
func RebuildControlSource(ctx context.Context, expected evolution.ControlSourceProvenance, binary []byte) error {
	if err := VerifyControlBuildProvenance(binary, expected); err != nil {
		return err
	}
	lockPath := filepath.Join(expected.Root, "execution", "toolchains", "locked.json")
	raw, err := os.ReadFile(lockPath)
	if err != nil {
		return err
	}
	var lock struct {
		Tools map[string]struct {
			Path    string `json:"path"`
			Hash    string `json:"sha256"`
			Version string `json:"version_output"`
		} `json:"tools"`
	}
	if err = json.Unmarshal(raw, &lock); err != nil {
		return err
	}
	goTool, ok := lock.Tools["go"]
	if !ok {
		return fmt.Errorf("CONTROL_REBUILD_PINNED_GO_REQUIRED")
	}
	if _, err = controlAuthorityFileID(goTool.Path, false); err != nil {
		return err
	}
	toolBytes, err := os.ReadFile(goTool.Path)
	if err != nil || evolution.Digest(toolBytes) != "sha256:"+goTool.Hash {
		return fmt.Errorf("CONTROL_REBUILD_TOOL_HASH")
	}
	temp, err := os.CreateTemp("", "researchos-current-build-*.exe")
	if err != nil {
		return err
	}
	output := temp.Name()
	if err = temp.Close(); err != nil {
		return err
	}
	defer os.Remove(output)
	env := []string{}
	fixed := map[string]string{"GOENV": "off", "GOTOOLCHAIN": "local", "GOWORK": "off", "GOFLAGS": "-mod=readonly", "CGO_ENABLED": "0", "GOOS": "windows", "GOARCH": "amd64", "GOAMD64": "v1", "GOPROXY": "off", "GOSUMDB": "off", "GOEXPERIMENT": ""}
	for _, v := range os.Environ() {
		key, _, _ := strings.Cut(v, "=")
		upper := strings.ToUpper(key)
		if _, set := fixed[upper]; !set && upper != "GOROOT" {
			env = append(env, v)
		}
	}
	for key, value := range fixed {
		env = append(env, key+"="+value)
	}
	version := exec.CommandContext(ctx, goTool.Path, "version")
	version.Env = env
	version.Dir = expected.Root
	version.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
	got, err := version.Output()
	if err != nil || strings.TrimSpace(string(got)) != goTool.Version {
		return fmt.Errorf("CONTROL_REBUILD_TOOL_VERSION")
	}
	cmd := exec.CommandContext(ctx, goTool.Path, "build", "-trimpath", "-buildvcs=false", "-ldflags=-buildid=", "-o", output, "./apps/control")
	cmd.Dir = expected.Root
	cmd.Env = env
	cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
	if err = cmd.Run(); err != nil {
		return fmt.Errorf("CONTROL_REBUILD_FAILED")
	}
	rebuilt, err := os.ReadFile(output)
	if err != nil {
		return err
	}
	if !bytes.Equal(rebuilt, binary) {
		return fmt.Errorf("CONTROL_REBUILD_IMAGE_MISMATCH")
	}
	return VerifyControlBuildProvenance(binary, expected)
}
