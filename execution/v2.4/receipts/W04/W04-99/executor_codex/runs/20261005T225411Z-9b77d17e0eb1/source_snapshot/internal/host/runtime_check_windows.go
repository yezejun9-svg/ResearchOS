//go:build windows

package host

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"io"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"time"
	"unicode/utf8"

	"researchos.local/research-os/internal/domain"
	sandbox "researchos.local/research-os/ops/experiment_sandbox"
)

// A check is frozen in the admitted profile, not supplied by the model. The
// model may select only check_id. Source paths without sha256 intentionally
// capture current workspace bytes after an edit; fixed dependencies carry a
// sha256. Toolchain and optional vendor trees are always frozen by tree hash.
type frozenRuntimeCheck struct {
	id, buildHash, toolchainRoot, toolchainHash string
	vendorRoot, vendorHash                      string
	argv                                        []string
	sources                                     []runtimeCheckSource
	timeout                                     time.Duration
	processLimit, memoryMiB                     uint32
	textLimit                                   int
}

type runtimeCheckSource struct {
	path, expected string
}

func runtimeCheckHash(s string) bool {
	if !strings.HasPrefix(s, "sha256:") || len(s) != 71 {
		return false
	}
	_, err := hex.DecodeString(strings.TrimPrefix(s, "sha256:"))
	return err == nil
}

func runtimeCheckPath(s string) bool {
	if s == "." || CheckRelativePath(s) != nil || NormalizeRelative(s) != s || strings.ContainsAny(s, "\\:") {
		return false
	}
	for _, segment := range strings.Split(s, "/") {
		if segment == "." || segment == "" {
			return false
		}
	}
	return true
}

func runtimeCheckNumber(o domain.Object, key string, low, high int64) (int64, error) {
	n, err := domain.Num(o, key)
	if err != nil || n < low || n > high {
		return 0, toolDenied("invalid frozen check resource: " + key)
	}
	return n, nil
}

func parseFrozenRuntimeCheck(policy domain.Object, checkID string) (frozenRuntimeCheck, error) {
	var check frozenRuntimeCheck
	items, ok := policy["checks"].([]any)
	if !ok || len(items) == 0 || len(items) > 32 {
		return check, toolDenied("frozen checks registry required")
	}
	if checkID == "" || len(checkID) > 128 {
		return check, toolInvalid("check_id required")
	}
	seen := map[string]bool{}
	var record domain.Object
	for _, item := range items {
		row, ok := item.(map[string]any)
		if !ok {
			return check, toolDenied("invalid frozen check record")
		}
		id := domain.Str(row, "id")
		if id == "" || seen[id] {
			return check, toolDenied("duplicate or empty frozen check id")
		}
		seen[id] = true
		if id == checkID {
			record = row
		}
	}
	if record == nil {
		return check, toolDenied("check_id is not in frozen registry")
	}
	if domain.Str(record, "executable") != "go" {
		return check, toolDenied("only frozen native Go checks are supported")
	}
	check.id = checkID
	check.buildHash = domain.Str(record, "build_hash")
	check.toolchainRoot = domain.Str(record, "toolchain_root")
	check.toolchainHash = domain.Str(record, "toolchain_hash")
	check.vendorRoot = domain.Str(record, "vendor_root")
	check.vendorHash = domain.Str(record, "vendor_hash")
	if !runtimeCheckHash(check.buildHash) || !runtimeCheckHash(check.toolchainHash) || !filepath.IsAbs(check.toolchainRoot) {
		return check, toolDenied("frozen Go toolchain root and hashes required")
	}
	if (check.vendorRoot == "") != (check.vendorHash == "") || check.vendorRoot != "" && (!filepath.IsAbs(check.vendorRoot) || !runtimeCheckHash(check.vendorHash)) {
		return check, toolDenied("vendor root and hash must be frozen together")
	}
	argv, ok := record["argv"].([]any)
	if !ok {
		return check, toolDenied("frozen Go test argv required")
	}
	for _, item := range argv {
		s, ok := item.(string)
		if !ok || s == "" || strings.ContainsRune(s, 0) {
			return check, toolDenied("invalid frozen Go argv")
		}
		check.argv = append(check.argv, s)
	}
	// No shell, go run, test -exec, arbitrary build flags or model arguments.
	want := []string{"-C", "${SOURCE}", "test", "-p=2", "-count=1", "-run"}
	if check.vendorRoot != "" {
		want = []string{"-C", "${SOURCE}", "test", "-mod=vendor", "-p=2", "-count=1", "-run"}
	}
	if len(check.argv) != len(want)+2 {
		return check, toolDenied("unsupported frozen Go test argv")
	}
	for i, value := range want {
		if check.argv[i] != value {
			return check, toolDenied("unsupported frozen Go test argv")
		}
	}
	pattern := check.argv[len(want)]
	if len(pattern) > 128 {
		return check, toolDenied("Go test selector too long")
	}
	if _, err := regexp.Compile(pattern); err != nil {
		return check, toolDenied("invalid frozen Go test selector")
	}
	pkg := check.argv[len(want)+1]
	if !strings.HasPrefix(pkg, "./") || !runtimeCheckPath(strings.TrimPrefix(pkg, "./")) {
		return check, toolDenied("Go test package must be a canonical staged relative path")
	}
	paths, ok := record["source_paths"].([]any)
	if !ok || len(paths) == 0 || len(paths) > 512 {
		return check, toolDenied("bounded frozen source_paths required")
	}
	seenPaths := map[string]bool{}
	for _, item := range paths {
		row, ok := item.(map[string]any)
		if !ok || len(row) < 1 || len(row) > 2 {
			return check, toolDenied("invalid frozen source entry")
		}
		p := domain.Str(row, "path")
		if !runtimeCheckPath(p) || strings.EqualFold(p, "vendor") || strings.HasPrefix(strings.ToLower(p), "vendor/") || seenPaths[strings.ToLower(p)] {
			return check, toolDenied("invalid or duplicate frozen source path")
		}
		seenPaths[strings.ToLower(p)] = true
		expected := ""
		if value, present := row["sha256"]; present {
			var ok bool
			expected, ok = value.(string)
			if !ok || !runtimeCheckHash(expected) {
				return check, toolDenied("invalid frozen source hash")
			}
		}
		for key := range row {
			if key != "path" && key != "sha256" {
				return check, toolDenied("unexpected frozen source field")
			}
		}
		check.sources = append(check.sources, runtimeCheckSource{p, expected})
	}
	resources, ok := record["resources"].(map[string]any)
	if !ok {
		return check, toolDenied("frozen check resources required")
	}
	seconds, err := runtimeCheckNumber(resources, "timeout_seconds", 1, 120)
	if err != nil {
		return check, err
	}
	processes, err := runtimeCheckNumber(resources, "process_limit", 2, 32)
	if err != nil {
		return check, err
	}
	memory, err := runtimeCheckNumber(resources, "memory_mib", 256, 1024)
	if err != nil {
		return check, err
	}
	text, err := runtimeCheckNumber(resources, "max_text_bytes", 1, 8192)
	if err != nil {
		return check, err
	}
	check.timeout, check.processLimit, check.memoryMiB, check.textLimit = time.Duration(seconds)*time.Second, uint32(processes), uint32(memory), int(text)
	return check, nil
}

// checkTree copies a selected tree to caller-owned staging and hashes exactly
// the bytes copied. An empty target computes the hash for registry preparation.
// It never grants the AppContainer access to the original host directory.
func checkTree(ctx context.Context, source, target string, curatedGo bool) (string, string, []any, error) {
	if !filepath.IsAbs(source) {
		return "", "", nil, toolDenied("absolute frozen input root required")
	}
	actual, err := filepath.EvalSymlinks(source)
	if err != nil || !strings.EqualFold(filepath.Clean(actual), filepath.Clean(source)) {
		return "", "", nil, toolDenied("frozen input root is a reparse path")
	}
	manifest := []any{}
	var total int64
	var executableHash string
	err = filepath.WalkDir(source, func(path string, entry os.DirEntry, walkErr error) error {
		if walkErr != nil {
			return walkErr
		}
		if err := ctx.Err(); err != nil {
			return err
		}
		rel, err := filepath.Rel(source, path)
		if err != nil {
			return err
		}
		if rel == "." {
			return nil
		}
		rel = filepath.ToSlash(rel)
		if curatedGo {
			parts := strings.Split(rel, "/")
			if len(parts) == 1 && entry.IsDir() && parts[0] != "bin" && parts[0] != "pkg" && parts[0] != "lib" && parts[0] != "src" {
				return filepath.SkipDir
			}
			if rel == "src/cmd" || rel == "src/testdata" {
				return filepath.SkipDir
			}
			if len(parts) == 1 && !entry.IsDir() && rel != "VERSION" && rel != "go.env" {
				return nil
			}
			if len(parts) == 2 && parts[0] == "src" && !entry.IsDir() && rel != "src/go.mod" && rel != "src/go.sum" {
				return nil
			}
		}
		if entry.Type()&os.ModeSymlink != 0 {
			return toolDenied("reparse point in frozen input tree")
		}
		info, err := entry.Info()
		if err != nil {
			return err
		}
		if entry.IsDir() {
			if target != "" {
				return os.MkdirAll(filepath.Join(target, filepath.FromSlash(rel)), 0700)
			}
			return nil
		}
		if !info.Mode().IsRegular() {
			return toolDenied("frozen input tree requires regular files")
		}
		if info.Size() > (768<<20)-total || len(manifest) >= 25000 {
			return toolDenied("frozen input tree exceeds staging budget")
		}
		input, err := os.Open(path)
		if err != nil {
			return err
		}
		hash := sha256.New()
		writer := io.Writer(hash)
		var output *os.File
		if target != "" {
			output, err = os.OpenFile(filepath.Join(target, filepath.FromSlash(rel)), os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
			if err != nil {
				input.Close()
				return err
			}
			writer = io.MultiWriter(output, hash)
		}
		copied, copyErr := io.Copy(writer, io.LimitReader(input, (768<<20)-total+1))
		err = copyErr
		err = errors.Join(err, input.Close())
		if output != nil {
			err = errors.Join(err, output.Close())
		}
		if err != nil {
			return err
		}
		if copied != info.Size() || copied > (768<<20)-total {
			return domain.Fail(409, "STATE_CONFLICT", "frozen input changed while staging")
		}
		total += copied
		digest := "sha256:" + hex.EncodeToString(hash.Sum(nil))
		manifest = append(manifest, domain.Object{"path": rel, "sha256": digest, "size_bytes": copied})
		if curatedGo && rel == "bin/go.exe" {
			executableHash = digest
		}
		return nil
	})
	if err != nil {
		return "", "", nil, err
	}
	if curatedGo && executableHash == "" {
		return "", "", nil, toolDenied("frozen native Go executable missing")
	}
	return domain.Hash(manifest), executableHash, manifest, nil
}

// FrozenGoToolchainHash is used when freezing the host-side check registry.
// Its selection is identical to the staged tree used during execution.
func FrozenGoToolchainHash(root string) (string, string, error) {
	tree, exe, _, err := checkTree(context.Background(), root, "", true)
	return tree, exe, err
}

// FrozenVendorHash prepares the fixed offline dependency tree registration.
func FrozenVendorHash(root string) (string, error) {
	tree, _, _, err := checkTree(context.Background(), root, "", false)
	return tree, err
}

func runtimeCheckSnapshot(ctx context.Context, root *os.Root, sources []runtimeCheckSource, target string) ([]any, error) {
	manifest := make([]any, 0, len(sources))
	var total int64
	for _, source := range sources {
		if err := ctx.Err(); err != nil {
			return nil, err
		}
		if err := runtimeToolPlainPath(root, source.path, false); err != nil {
			return nil, err
		}
		data, err := runtimeToolBytes(root, source.path)
		if err != nil {
			return nil, err
		}
		total += int64(len(data))
		if total > 32<<20 {
			return nil, toolDenied("source snapshot exceeds 32 MiB")
		}
		digest := domain.Digest(data)
		if source.expected != "" && digest != source.expected {
			return nil, domain.Fail(409, "STATE_CONFLICT", "fixed source hash changed")
		}
		if target != "" {
			path := filepath.Join(target, filepath.FromSlash(source.path))
			if err := os.MkdirAll(filepath.Dir(path), 0700); err != nil {
				return nil, err
			}
			if err := os.WriteFile(path, data, 0600); err != nil {
				return nil, err
			}
		}
		manifest = append(manifest, domain.Object{"path": source.path, "sha256": digest, "size_bytes": len(data), "mode": map[bool]string{true: "fixed", false: "current"}[source.expected != ""]})
	}
	return manifest, nil
}

func runtimeCheckText(raw []byte, max int) (string, int) {
	end := min(len(raw), max)
	for end > 0 && end < len(raw) && !utf8.RuneStart(raw[end]) {
		end--
	}
	return strings.ToValidUTF8(string(raw[:end]), "?"), end
}

// The model-visible result is bounded independently of the raw receipt. It
// carries the test exit code and explicit omission counts; the full raw stream
// bytes remain in host_evidence, subject to its separate 4 MiB total bound.
func runtimeCheckReply(metadata domain.Object, stdout, stderr []byte, textLimit int) (domain.Object, error) {
	outCap, errCap := min(len(stdout), textLimit), min(len(stderr), textLimit)
	build := func() (domain.Object, error) {
		outText, outBytes := runtimeCheckText(stdout, outCap)
		errText, errBytes := runtimeCheckText(stderr, errCap)
		details := make(domain.Object, len(metadata)+8)
		for key, value := range metadata {
			details[key] = value
		}
		details["stdout_truncated"] = outBytes < len(stdout)
		details["stderr_truncated"] = errBytes < len(stderr)
		details["stdout_omitted_bytes"] = len(stdout) - outBytes
		details["stderr_omitted_bytes"] = len(stderr) - errBytes
		details["stdout_raw_bytes"] = len(stdout)
		details["stderr_raw_bytes"] = len(stderr)
		details["stdout_utf8_replaced"] = !utf8.Valid(stdout[:outBytes])
		details["stderr_utf8_replaced"] = !utf8.Valid(stderr[:errBytes])
		visible := make(domain.Object, len(details)+2)
		for key, value := range details {
			visible[key] = value
		}
		visible["stdout_text"] = outText
		visible["stderr_text"] = errText
		encoded, err := json.Marshal(visible)
		if err != nil {
			return nil, err
		}
		return domain.Object{"content": []any{domain.Object{"type": "text", "text": string(encoded)}}, "details": details}, nil
	}
	for {
		reply, err := build()
		if err != nil {
			return nil, err
		}
		if len(domain.Bytes(reply)) <= runtimeToolReplyLimit {
			return reply, nil
		}
		if outCap == 0 && errCap == 0 {
			return nil, toolDenied("run_check result cannot fit bridge frame")
		}
		// Shrink the larger encoded stream. Halving converges even when every
		// byte needs multiple JSON escapes and never silently drops a suffix.
		outText, _ := runtimeCheckText(stdout, outCap)
		errText, _ := runtimeCheckText(stderr, errCap)
		outJSON, _ := json.Marshal(outText)
		errJSON, _ := json.Marshal(errText)
		if outCap > 0 && (errCap == 0 || len(outJSON) >= len(errJSON)) {
			outCap /= 2
		} else {
			errCap /= 2
		}
	}
}

func runtimeCheckEvidenceBound(full domain.Object) error {
	if len(domain.Bytes(full)) > 4<<20 {
		return toolDenied("run_check raw logs and manifests exceed 4 MiB evidence bound")
	}
	return nil
}

func runtimeCheckManifestBytes(manifest []any) int64 {
	var total int64
	for _, item := range manifest {
		row := item.(domain.Object)
		n, _ := domain.Num(row, "size_bytes")
		total += n
	}
	return total
}

// executeRuntimeCheck is called only after ExecuteRuntimeTool has revalidated
// the current workspace binding and read access. Keep that authority check in
// the shared dispatcher; this method enforces the independent check registry.
func (h *Host) executeRuntimeCheck(ctx context.Context, request domain.RuntimeToolRequest) (result domain.Object, err error) {
	beforeLaunch := true
	defer func() {
		if err != nil && beforeLaunch {
			err = &domain.RuntimeToolFailure{Err: err, Outcome: "NOT_APPLIED"}
		}
	}()
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	if request.Name != "run_check" || request.Access != AccessReadOnly && request.Access != AccessReadWrite {
		return nil, toolDenied("run_check requires a bound readable workspace")
	}
	if len(request.Arguments) != 1 {
		return nil, toolInvalid("run_check accepts only check_id")
	}
	checkID, ok := request.Arguments["check_id"].(string)
	if !ok {
		return nil, toolInvalid("check_id must be text")
	}
	check, err := parseFrozenRuntimeCheck(request.Policy, checkID)
	if err != nil {
		return nil, err
	}
	// source_paths is the check-specific frozen read permission. If the same
	// policy also grants ordinary read, never let the check exceed that list.
	if _, present := request.Policy["read_paths"]; present {
		readPaths, err := runtimeToolPaths(request.Policy, "read_paths")
		if err != nil {
			return nil, err
		}
		for _, source := range check.sources {
			if !readPaths[source.path] {
				return nil, toolDenied("check source is outside frozen read permission")
			}
		}
	}
	root, err := os.OpenRoot(request.WorkspacePath)
	if err != nil {
		return nil, err
	}
	defer root.Close()
	staging, err := os.MkdirTemp("", "researchos-run-check-")
	if err != nil {
		return nil, err
	}
	defer func() {
		if cleanupErr := os.RemoveAll(staging); cleanupErr != nil {
			result = nil
			err = errors.Join(err, cleanupErr)
		}
	}()
	input := filepath.Join(staging, "input")
	output := filepath.Join(staging, "output")
	sourceDir := filepath.Join(input, "source")
	goDir := filepath.Join(input, "go")
	for _, dir := range []string{input, output, sourceDir, goDir} {
		if err := os.MkdirAll(dir, 0700); err != nil {
			return nil, err
		}
	}
	sourceManifest, err := runtimeCheckSnapshot(ctx, root, check.sources, sourceDir)
	if err != nil {
		return nil, err
	}
	toolchainHash, buildHash, toolchainManifest, err := checkTree(ctx, check.toolchainRoot, goDir, true)
	if err != nil {
		return nil, err
	}
	if toolchainHash != check.toolchainHash || buildHash != check.buildHash {
		return nil, domain.Fail(409, "STATE_CONFLICT", "frozen Go toolchain changed")
	}
	var vendorManifest []any
	if check.vendorRoot != "" {
		vendorDir := filepath.Join(sourceDir, "vendor")
		if err := os.MkdirAll(vendorDir, 0700); err != nil {
			return nil, err
		}
		var vendorHash string
		vendorHash, _, vendorManifest, err = checkTree(ctx, check.vendorRoot, vendorDir, false)
		if err != nil {
			return nil, err
		}
		if vendorHash != check.vendorHash {
			return nil, domain.Fail(409, "STATE_CONFLICT", "frozen vendor tree changed")
		}
	}
	if runtimeCheckManifestBytes(sourceManifest)+runtimeCheckManifestBytes(toolchainManifest)+runtimeCheckManifestBytes(vendorManifest) > 1024<<20 {
		return nil, toolDenied("combined check input exceeds 1 GiB staging budget")
	}
	inputs := domain.Object{"source_manifest": sourceManifest, "toolchain_manifest": toolchainManifest, "vendor_manifest": vendorManifest}
	if len(domain.Bytes(inputs)) > 3<<20 {
		return nil, toolDenied("run_check input evidence exceeds 3 MiB")
	}
	// Re-read current source bytes immediately before launching the isolated
	// snapshot. A concurrent edit is explicit conflict, never a silent race.
	current, err := runtimeCheckSnapshot(ctx, root, check.sources, "")
	if err != nil {
		return nil, err
	}
	if domain.Hash(current) != domain.Hash(sourceManifest) {
		return nil, domain.Fail(409, "STATE_CONFLICT", "workspace source changed while staging")
	}
	argv := append([]string(nil), check.argv...)
	argv[1] = sourceDir
	// A failed launch may still have started a process. Keep it UNKNOWN unless
	// the sandbox returns a complete receipt.
	beforeLaunch = false
	receipt, err := sandbox.Run(ctx, sandbox.Command{Executable: filepath.Join(goDir, "bin", "go.exe"), Args: argv, InputDirectory: input, OutputDirectory: output, Timeout: check.timeout, ProcessLimit: check.processLimit, MemoryMiB: check.memoryMiB,
		Env: map[string]string{"GOROOT": goDir, "GOPATH": filepath.Join(output, "gopath"), "GOCACHE": filepath.Join(output, "gocache"), "GOTMPDIR": output, "GOTOOLCHAIN": "local", "GOPROXY": "off", "GOSUMDB": "off", "GOENV": "off", "GOWORK": "off", "CGO_ENABLED": "0"}})
	if err != nil {
		return nil, err
	}
	if !receipt.Stopped || !receipt.StreamsDrained || !receipt.CleanupComplete || !receipt.OutputCopied {
		return nil, toolDenied("run_check did not complete sandbox cleanup")
	}
	details := domain.Object{"check_id": check.id, "exit_code": receipt.ExitCode, "timed_out": receipt.TimedOut, "stdout_hash": domain.Digest(receipt.Stdout), "stderr_hash": domain.Digest(receipt.Stderr), "source_manifest_hash": domain.Hash(sourceManifest), "source_count": len(sourceManifest), "frozen_policy_hash": domain.Hash(request.Policy), "toolchain_hash": toolchainHash, "vendor_hash": check.vendorHash, "job_total_processes": receipt.JobProcesses, "children_stopped": receipt.Stopped, "streams_drained": receipt.StreamsDrained, "cleanup_complete": receipt.CleanupComplete}
	full := domain.Object{"check_id": check.id, "workspace_path": request.WorkspacePath, "frozen_policy_hash": domain.Hash(request.Policy), "argv_template": check.argv, "source_manifest": sourceManifest, "source_manifest_hash": domain.Hash(sourceManifest), "toolchain_manifest": toolchainManifest, "toolchain_hash": toolchainHash, "build_hash": buildHash, "vendor_manifest": vendorManifest, "vendor_hash": check.vendorHash,
		"sandbox_receipt": domain.Object{"pid": receipt.PID, "process_created_ns": receipt.Created, "job": receipt.Job, "profile": receipt.Profile, "appcontainer_sid": receipt.SID, "capabilities": receipt.Capabilities, "exit_code": receipt.ExitCode, "timed_out": receipt.TimedOut, "job_total_processes": receipt.JobProcesses, "children_stopped": receipt.Stopped, "streams_drained": receipt.StreamsDrained, "cleanup_complete": receipt.CleanupComplete, "output_copied": receipt.OutputCopied, "stdout_hash": domain.Digest(receipt.Stdout), "stderr_hash": domain.Digest(receipt.Stderr), "stdout_raw_bytes": len(receipt.Stdout), "stderr_raw_bytes": len(receipt.Stderr), "stdout_raw": receipt.Stdout, "stderr_raw": receipt.Stderr}}
	if err := runtimeCheckEvidenceBound(full); err != nil {
		return nil, err
	}
	result, err = runtimeCheckReply(details, receipt.Stdout, receipt.Stderr, check.textLimit)
	if err != nil {
		return nil, err
	}
	result["host_evidence"] = full
	return result, nil
}
