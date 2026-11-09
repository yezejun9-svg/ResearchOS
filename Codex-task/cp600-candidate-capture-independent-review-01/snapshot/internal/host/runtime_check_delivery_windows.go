//go:build windows

package host

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"io"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"unsafe"

	"golang.org/x/sys/windows"
	"researchos.local/research-os/internal/deliverygate"
	"researchos.local/research-os/internal/domain"
	sandbox "researchos.local/research-os/ops/experiment_sandbox"
)

const runtimeCandidateCaptureSchema = "researchos.coding-private-candidate-capture.v1"
const runtimeCaptureFixedLimit = 1 << 20

var runtimeCapturePaths = [3]string{"go.mod", "pkg/solution.go", "pkg/solution_test.go"}

type runtimeCaptureEntry struct {
	path, hash, mode string
	size             int64
}

// Owns an exact before-resume candidate snapshot. It does not attest later
// compiler reads, final toolchain/vendor copies, same-user exclusion or business
// correctness. The context is trusted-port provenance, not an auth credential.
type runtimeCandidateCapture struct {
	view         domain.RuntimeCodingCaptureView
	identity     sandbox.Identity
	entries      [3]runtimeCaptureEntry
	source       *deliverygate.ValidatedSource
	manifestHash string
	argv         []string
}

func runtimeCaptureCheck(v domain.RuntimeCodingCaptureView, c frozenRuntimeCheck, policyHash string) error {
	if err := v.ValidateShape(); err != nil {
		return err
	}
	if v.CheckID != c.id || v.PolicyHash != policyHash || v.ToolchainHash != c.toolchainHash ||
		c.vendorRoot != "" || c.vendorHash != "" || len(c.sources) != 3 || len(c.argv) != 8 ||
		c.argv[0] != "-C" || c.argv[1] != "${SOURCE}" || c.argv[2] != "test" ||
		c.argv[3] != "-p=2" || c.argv[4] != "-count=1" || c.argv[5] != "-run" || c.argv[7] != "./pkg" {
		return toolDenied("private capture differs from frozen check")
	}
	for i, p := range runtimeCapturePaths {
		if c.sources[i].path != p {
			return toolDenied("private capture requires exact roster")
		}
	}
	if c.sources[0].expected != v.GoModHash || c.sources[1].expected != "" || c.sources[2].expected != v.TestHash {
		return toolDenied("private capture fixed inputs differ")
	}
	return nil
}
func runtimeCaptureManifest(raw []any, v domain.RuntimeCodingCaptureView) ([3]runtimeCaptureEntry, error) {
	var entries [3]runtimeCaptureEntry
	if len(raw) != 3 {
		return entries, toolDenied("private capture staging manifest invalid")
	}
	for i, item := range raw {
		row, ok := item.(map[string]any)
		if !ok || len(row) != 4 || row["path"] != runtimeCapturePaths[i] {
			return entries, toolDenied("private capture staging manifest invalid")
		}
		size, err := domain.Num(row, "size_bytes")
		hash, ok := row["sha256"].(string)
		mode := "fixed"
		limit := int64(runtimeCaptureFixedLimit)
		if i == 1 {
			mode = "current"
			limit = deliverygate.MaxSourceBytes
		}
		if err != nil || size <= 0 || size > limit || !ok || !runtimeCheckHash(hash) || row["mode"] != mode ||
			i == 0 && hash != v.GoModHash || i == 2 && hash != v.TestHash {
			return entries, toolDenied("private capture staging manifest invalid")
		}
		entries[i] = runtimeCaptureEntry{runtimeCapturePaths[i], hash, mode, size}
	}
	return entries, nil
}
func runtimeCaptureIdentity(id sandbox.Identity) error {
	volume := filepath.VolumeName(id.StagingDirectory)
	if id.PID == 0 || id.Created <= 0 || id.Job == "" || id.SID == "" || id.Profile == "" ||
		!filepath.IsAbs(id.StagingDirectory) || filepath.Clean(id.StagingDirectory) != id.StagingDirectory ||
		len(id.StagingDirectory) > 4096 || len(volume) != 2 || strings.ContainsAny(id.StagingDirectory, "/\x00") {
		return toolDenied("private capture native identity invalid")
	}
	if volume[1] != ':' {
		return toolDenied("private capture local volume required")
	}
	for _, part := range strings.Split(strings.TrimPrefix(id.StagingDirectory, volume+"\\"), "\\") {
		if part == "" || part == "." || part == ".." || strings.TrimRight(part, ". ") != part || strings.Contains(part, ":") {
			return toolDenied("private capture staging spelling invalid")
		}
	}
	return nil
}
func runtimeCaptureHandle(f *os.File, dir bool) error {
	var info windows.ByHandleFileInformation
	if err := windows.GetFileInformationByHandle(windows.Handle(f.Fd()), &info); err != nil {
		return err
	}
	if info.FileAttributes&windows.FILE_ATTRIBUTE_REPARSE_POINT != 0 ||
		(info.FileAttributes&windows.FILE_ATTRIBUTE_DIRECTORY != 0) != dir || !dir && info.NumberOfLinks != 1 {
		return toolDenied("private capture reparse, alias or file type refused")
	}
	stat, err := f.Stat()
	if err != nil {
		return err
	}
	if dir && !stat.IsDir() || !dir && !stat.Mode().IsRegular() {
		return toolDenied("private capture regular handle required")
	}
	return nil
}

// Relative NT opens do not re-open an absolute path after a weak Lstat check.
// Held directories deny deletion; files deny writes/deletion during this read.
func runtimeCaptureOpen(parent *os.File, name string, dir bool) (*os.File, error) {
	switch name {
	case "input", "source", "pkg", "go.mod", "solution.go", "solution_test.go":
	default:
		return nil, toolDenied("private capture literal path required")
	}
	nt, err := windows.NewNTUnicodeString(name)
	if err != nil {
		return nil, err
	}
	oa := windows.OBJECT_ATTRIBUTES{RootDirectory: windows.Handle(parent.Fd()), ObjectName: nt, Attributes: windows.OBJ_DONT_REPARSE}
	oa.Length = uint32(unsafe.Sizeof(oa))
	options := uint32(windows.FILE_OPEN_REPARSE_POINT | windows.FILE_SYNCHRONOUS_IO_NONALERT)
	share := uint32(windows.FILE_SHARE_READ)
	if dir {
		options |= windows.FILE_DIRECTORY_FILE
		share |= windows.FILE_SHARE_WRITE
	} else {
		options |= windows.FILE_NON_DIRECTORY_FILE
	}
	var handle windows.Handle
	var status windows.IO_STATUS_BLOCK
	if err = windows.NtCreateFile(&handle, windows.GENERIC_READ|windows.SYNCHRONIZE, &oa, &status, nil, 0, share, windows.FILE_OPEN, options, 0, 0); err != nil {
		return nil, toolDenied("private capture relative open refused")
	}
	f := os.NewFile(uintptr(handle), name)
	if f == nil {
		windows.CloseHandle(handle)
		return nil, toolDenied("private capture handle invalid")
	}
	if err = runtimeCaptureHandle(f, dir); err != nil {
		f.Close()
		return nil, err
	}
	return f, nil
}

// Enumerate actual names, including otherwise missed empty dirs and case/8.3
// aliases. Source/pkɡ have a complete roster; input's other namespaces are not
// compiler-input attestation and are only bounded while locating literal source.
func runtimeCaptureNames(ctx context.Context, f *os.File, exact bool, names ...string) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	limit := len(names)
	if !exact {
		limit = 8
	}
	entries, err := f.ReadDir(limit + 1)
	if err != nil && !errors.Is(err, io.EOF) {
		return err
	}
	if len(entries) > limit || exact && len(entries) != len(names) {
		return toolDenied("private capture exact inventory required")
	}
	seen := map[string]bool{}
	for _, entry := range entries {
		if err := ctx.Err(); err != nil {
			return err
		}
		found := false
		for _, name := range names {
			if strings.EqualFold(entry.Name(), name) {
				if entry.Name() != name || seen[name] {
					return toolDenied("private capture exact spelling required")
				}
				seen[name] = true
				found = true
			}
		}
		if exact && !found {
			return toolDenied("private capture extra entry refused")
		}
	}
	if len(seen) != len(names) {
		return toolDenied("private capture missing entry")
	}
	return nil
}
func runtimeCaptureRead(ctx context.Context, f *os.File, limit int64, keep bool) ([]byte, string, int64, error) {
	stat, err := f.Stat()
	if err != nil {
		return nil, "", 0, err
	}
	if stat.Size() <= 0 || stat.Size() > limit {
		return nil, "", 0, toolDenied("private capture byte limit")
	}
	hash := sha256.New()
	var owned []byte
	if keep {
		owned = make([]byte, 0, int(stat.Size()))
	}
	buffer := make([]byte, 4096)
	var size int64
	for {
		if err := ctx.Err(); err != nil {
			return nil, "", 0, err
		}
		n, readErr := f.Read(buffer)
		if n > 0 {
			size += int64(n)
			if size > limit {
				return nil, "", 0, toolDenied("private capture byte limit")
			}
			hash.Write(buffer[:n])
			if keep {
				owned = append(owned, buffer[:n]...)
			}
		}
		if errors.Is(readErr, io.EOF) {
			break
		}
		if readErr != nil {
			return nil, "", 0, toolDenied("private capture read failed")
		}
		if n == 0 {
			return nil, "", 0, io.ErrNoProgress
		}
	}
	if err := ctx.Err(); err != nil {
		return nil, "", 0, err
	}
	if size != stat.Size() {
		return nil, "", 0, toolDenied("private capture file changed")
	}
	return owned, "sha256:" + hex.EncodeToString(hash.Sum(nil)), size, nil
}
func captureRuntimeCandidate(ctx context.Context, v domain.RuntimeCodingCaptureView, check frozenRuntimeCheck, policyHash string, manifest []any, id sandbox.Identity) (*runtimeCandidateCapture, error) {
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	if err := runtimeCaptureCheck(v, check, policyHash); err != nil {
		return nil, err
	}
	entries, err := runtimeCaptureManifest(manifest, v)
	if err != nil {
		return nil, err
	}
	if err = runtimeCaptureIdentity(id); err != nil {
		return nil, err
	}
	// Unlike chainHasReparsePoint, this helper fails on every open error and
	// retains no-delete handles throughout the read.
	guards, err := guardWriteDirectories(id.StagingDirectory)
	if err != nil {
		return nil, toolDenied("private capture ancestry refused")
	}
	defer closeWriteGuards(guards)
	if reparse, err := isReparsePoint(filepath.VolumeName(id.StagingDirectory) + "\\"); err != nil || reparse {
		return nil, toolDenied("private capture volume refused")
	}
	wide, err := windows.UTF16PtrFromString(id.StagingDirectory)
	if err != nil {
		return nil, err
	}
	h, err := windows.CreateFile(wide, windows.GENERIC_READ, windows.FILE_SHARE_READ|windows.FILE_SHARE_WRITE, nil, windows.OPEN_EXISTING, windows.FILE_FLAG_BACKUP_SEMANTICS|windows.FILE_FLAG_OPEN_REPARSE_POINT, 0)
	if err != nil {
		return nil, toolDenied("private capture staging open refused")
	}
	stage := os.NewFile(uintptr(h), id.StagingDirectory)
	defer stage.Close()
	if err = runtimeCaptureHandle(stage, true); err != nil {
		return nil, err
	}
	if err = runtimeCaptureNames(ctx, stage, false, "input"); err != nil {
		return nil, err
	}
	input, err := runtimeCaptureOpen(stage, "input", true)
	if err != nil {
		return nil, err
	}
	defer input.Close()
	if err = runtimeCaptureNames(ctx, input, false, "source"); err != nil {
		return nil, err
	}
	source, err := runtimeCaptureOpen(input, "source", true)
	if err != nil {
		return nil, err
	}
	defer source.Close()
	if err = runtimeCaptureNames(ctx, source, true, "go.mod", "pkg"); err != nil {
		return nil, err
	}
	pkg, err := runtimeCaptureOpen(source, "pkg", true)
	if err != nil {
		return nil, err
	}
	defer pkg.Close()
	if err = runtimeCaptureNames(ctx, pkg, true, "solution.go", "solution_test.go"); err != nil {
		return nil, err
	}
	c := &runtimeCandidateCapture{view: v, identity: id, entries: entries, manifestHash: domain.Hash(manifest), argv: append([]string(nil), check.argv...)}
	for i, entry := range entries {
		parent, name := pkg, "solution.go"
		if i == 0 {
			parent, name = source, "go.mod"
		} else if i == 2 {
			name = "solution_test.go"
		}
		f, err := runtimeCaptureOpen(parent, name, false)
		if err != nil {
			return nil, err
		}
		limit := int64(runtimeCaptureFixedLimit)
		if i == 1 {
			limit = deliverygate.MaxSourceBytes
		}
		raw, hash, size, readErr := runtimeCaptureRead(ctx, f, limit, i == 1)
		closeErr := f.Close()
		if readErr != nil || closeErr != nil {
			return nil, errors.Join(readErr, closeErr)
		}
		if hash != entry.hash || size != entry.size {
			return nil, toolDenied("private capture final copy differs from current staging")
		}
		if i == 1 {
			c.source, err = deliverygate.Validate(raw)
			if err != nil {
				return nil, toolDenied("private capture candidate outside structural language")
			}
		}
	}
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	return c, nil
}
func (c *runtimeCandidateCapture) evidence(r sandbox.Receipt) (domain.Object, error) {
	if c == nil || c.source == nil {
		return nil, toolDenied("private capture missing")
	}
	id := c.identity
	if r.PID != id.PID || r.Created != id.Created || r.Job != id.Job || r.SID != id.SID || r.Profile != id.Profile ||
		len(r.Capabilities) != 0 || !r.Stopped || !r.StreamsDrained || !r.CleanupComplete || !r.OutputCopied ||
		r.Directory != filepath.Join(id.StagingDirectory, "output") || r.Executable != filepath.Join(id.StagingDirectory, "input", "go", "bin", "go.exe") {
		return nil, toolDenied("private capture complete receipt identity mismatch")
	}
	argv := append([]string(nil), c.argv...)
	argv[1] = filepath.Join(id.StagingDirectory, "input", "source")
	if len(r.Args) != len(argv) {
		return nil, toolDenied("private capture argv mismatch")
	}
	for i, s := range argv {
		if r.Args[i] != s {
			return nil, toolDenied("private capture argv mismatch")
		}
	}
	inventory := make([]any, 0, 3)
	for _, e := range c.entries {
		inventory = append(inventory, domain.Object{"path": e.path, "sha256": e.hash, "size_bytes": e.size, "mode": e.mode})
	}
	raw := c.source.Bytes()
	if err := c.source.Verify(raw); err != nil {
		return nil, err
	}
	return domain.Object{"schema": runtimeCandidateCaptureSchema, "phase": "BEFORE_RESUME", "context": c.view, "context_hash": domain.Hash(c.view),
		"source_manifest_hash": c.manifestHash, "inventory": inventory,
		"candidate":          domain.Object{"path": "pkg/solution.go", "sha256": domain.Digest(raw), "size_bytes": len(raw), "bytes": raw},
		"structural_witness": domain.Object{"validator": "pure-scalar-v1", "source_sha256": "sha256:" + c.source.SHA256(), "semantic_acceptance": false},
		"native_identity":    domain.Object{"pid": id.PID, "process_created_ns": strconv.FormatInt(id.Created, 10), "job": id.Job, "appcontainer_sid": id.SID, "profile": id.Profile},
		"execution_outcome":  domain.Object{"exit_code": r.ExitCode, "timed_out": r.TimedOut}}, nil
}
