//go:build windows

package host

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"errors"
	"io"
	"os"
	"path"
	"strings"
	"sync"
	"unicode/utf8"

	"researchos.local/research-os/internal/domain"
)

const runtimeToolFileLimit = 2 << 20
const runtimeToolByteLimit = 64 << 10

// The broker adds sequence/key/state around this payload before sending its
// 64 KiB bridge frame. Keep room for that envelope and measure encoded bytes,
// since JSON escaping can expand a requested byte slice substantially.
const runtimeToolReplyLimit = 56 << 10

// Serialize host writes, including the read/compare/replace interval. External
// writers are not serialized by this mutex; callers still need a frozen,
// host-authorized workspace and an expected content hash for every replacement.
var runtimeToolWriteMu sync.Mutex

func toolDenied(message string) error  { return domain.Fail(403, "FORBIDDEN", message) }
func toolInvalid(message string) error { return domain.Fail(400, "INVALID_REQUEST", message) }

func (h *Host) ExecuteRuntimeTool(ctx context.Context, request domain.RuntimeToolRequest) (result domain.Object, err error) {
	// Validation and reads cannot mutate the workspace. Each mutating tool
	// takes responsibility for classifying errors after this boundary.
	beforeMutation := true
	defer func() {
		if err != nil && beforeMutation {
			err = &domain.RuntimeToolFailure{Err: err, Outcome: "NOT_APPLIED"}
		}
	}()
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	if h == nil || h.roots == nil {
		return nil, toolDenied("workspace host unavailable")
	}
	if request.Name != "read" && request.Name != "write" && request.Name != "edit" && request.Name != "run_check" {
		return nil, toolDenied("tool is not permitted")
	}
	args := request.Arguments
	if args == nil {
		return nil, toolInvalid("tool arguments required")
	}
	if request.Name == "run_check" {
		if request.Access != AccessReadOnly && request.Access != AccessReadWrite {
			return nil, toolDenied("session workspace access does not permit check")
		}
		if len(args) != 1 {
			return nil, toolInvalid("run_check accepts only check_id")
		}
		checkID, ok := args["check_id"].(string)
		if !ok {
			return nil, toolInvalid("check_id must be text")
		}
		check, err := parseFrozenRuntimeCheck(request.Policy, checkID)
		if err != nil {
			return nil, err
		}
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
		var binding *RootBinding
		for _, candidate := range h.roots.List() {
			if candidate.RealPath != request.WorkspacePath {
				continue
			}
			if candidate.Revoked {
				return nil, ErrRootRevoked
			}
			if binding != nil {
				return nil, toolDenied("workspace path has ambiguous root bindings")
			}
			binding = candidate
		}
		if binding == nil {
			return nil, ErrRootUnknown
		}
		if binding.Access != request.Access {
			return nil, toolDenied("workspace access differs from current root binding")
		}
		for _, source := range check.sources {
			if _, err := h.ResolveWorkspace(binding.Ref, source.path, AccessReadOnly); err != nil {
				return nil, err
			}
		}
		beforeMutation = false
		return h.executeRuntimeCheck(ctx, request)
	}
	rel := domain.Str(args, "path")
	if err := CheckRelativePath(rel); err != nil {
		return nil, err
	}
	if rel != NormalizeRelative(rel) {
		return nil, toolDenied("path must use one canonical relative spelling")
	}
	readPaths, err := runtimeToolPaths(request.Policy, "read_paths")
	if err != nil {
		return nil, err
	}
	writePaths, err := runtimeToolPaths(request.Policy, "write_paths")
	if err != nil {
		return nil, err
	}
	readMax, err := runtimeToolLimit(request.Policy, "max_read_bytes")
	if err != nil {
		return nil, err
	}
	writeMax, err := runtimeToolLimit(request.Policy, "max_write_bytes")
	if err != nil {
		return nil, err
	}
	wantAccess := AccessReadOnly
	if request.Name == "read" {
		if !readPaths[rel] {
			return nil, toolDenied("path is not in frozen read permission")
		}
	} else {
		if !writePaths[rel] {
			return nil, toolDenied("path is not in frozen write permission")
		}
		wantAccess = AccessReadWrite
	}
	if request.Access != wantAccess && !(wantAccess == AccessReadOnly && request.Access == AccessReadWrite) {
		return nil, toolDenied("session workspace access does not permit tool")
	}
	var binding *RootBinding
	for _, candidate := range h.roots.List() {
		if candidate.RealPath == request.WorkspacePath {
			if candidate.Revoked {
				return nil, ErrRootRevoked
			}
			if binding != nil {
				return nil, toolDenied("workspace path has ambiguous root bindings")
			}
			binding = candidate
		}
	}
	if binding == nil {
		return nil, ErrRootUnknown
	}
	if binding.Access != request.Access {
		return nil, toolDenied("workspace access differs from current root binding")
	}
	if _, err := h.ResolveWorkspace(binding.Ref, rel, wantAccess); err != nil {
		return nil, err
	}
	root, err := os.OpenRoot(binding.RealPath)
	if err != nil {
		return nil, err
	}
	defer root.Close()
	if err := runtimeToolPlainPath(root, rel, request.Name != "read" && args["expected_hash"] == nil); err != nil {
		return nil, err
	}
	switch request.Name {
	case "read":
		return runtimeToolRead(ctx, root, rel, args, readMax)
	case "write", "edit":
		runtimeToolWriteMu.Lock()
		defer runtimeToolWriteMu.Unlock()
		// Recheck current revocation, root pin and reparse state while serialized.
		if _, err := h.ResolveWorkspace(binding.Ref, rel, AccessReadWrite); err != nil {
			return nil, err
		}
		if err := runtimeToolPlainPath(root, rel, request.Name == "write" && args["expected_hash"] == nil); err != nil {
			return nil, err
		}
		beforeMutation = false
		return runtimeToolWrite(ctx, root, rel, request.Name, args, writeMax)
	}
	panic("unreachable")
}

func runtimeToolPaths(policy domain.Object, key string) (map[string]bool, error) {
	items, ok := policy[key].([]any)
	if !ok {
		return nil, toolDenied("frozen path permissions required")
	}
	out := map[string]bool{}
	for _, item := range items {
		p, ok := item.(string)
		if !ok || CheckRelativePath(p) != nil || p != NormalizeRelative(p) || out[p] {
			return nil, toolDenied("invalid frozen path permission")
		}
		out[p] = true
	}
	return out, nil
}

func runtimeToolLimit(policy domain.Object, key string) (int64, error) {
	n, err := domain.Num(policy, key)
	if err != nil || n < 1 || n > runtimeToolByteLimit {
		return 0, toolDenied("bounded frozen tool byte limit required")
	}
	return n, nil
}

func runtimeToolPlainPath(root *os.Root, rel string, allowMissingFinal bool) error {
	parts := strings.Split(rel, "/")
	for i := range parts {
		prefix := strings.Join(parts[:i+1], "/")
		info, err := root.Lstat(prefix)
		if errors.Is(err, os.ErrNotExist) && i == len(parts)-1 && allowMissingFinal {
			return nil
		}
		if err != nil {
			return err
		}
		if info.Mode()&os.ModeSymlink != 0 || !info.IsDir() && !info.Mode().IsRegular() {
			return ErrPathReparsePoint
		}
		if i < len(parts)-1 && !info.IsDir() {
			return toolDenied("parent must be a plain directory")
		}
		if i == len(parts)-1 && !info.Mode().IsRegular() {
			return toolDenied("target must be a regular file")
		}
	}
	return nil
}

func runtimeToolBytes(root *os.Root, rel string) ([]byte, error) {
	f, err := root.Open(rel)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	info, err := f.Stat()
	if err != nil {
		return nil, err
	}
	if !info.Mode().IsRegular() || info.Size() > runtimeToolFileLimit {
		return nil, toolDenied("tool file must be regular and at most 2 MiB")
	}
	data, err := io.ReadAll(io.LimitReader(f, runtimeToolFileLimit+1))
	if err != nil {
		return nil, err
	}
	if len(data) > runtimeToolFileLimit {
		return nil, toolDenied("tool file exceeded 2 MiB")
	}
	return data, nil
}

func runtimeToolReply(details domain.Object) (domain.Object, error) {
	text, err := json.Marshal(details)
	if err != nil {
		return nil, err
	}
	return domain.Object{"content": []any{domain.Object{"type": "text", "text": string(text)}}, "details": details}, nil
}

func runtimeToolReadReply(rel, hash string, data []byte, offset, end int64) (domain.Object, error) {
	metadata := domain.Object{"path": rel, "content_hash": hash, "next_offset": end, "truncated": end < int64(len(data)), "size_bytes": len(data)}
	visible := domain.Object{"path": rel, "content_hash": hash, "text": string(data[offset:end]), "next_offset": end, "truncated": end < int64(len(data)), "size_bytes": len(data)}
	encoded, err := json.Marshal(visible)
	if err != nil {
		return nil, err
	}
	// The model sees the text and pagination metadata in content. The SDK's
	// details copy carries only metadata, so the text is encoded just once.
	return domain.Object{"content": []any{domain.Object{"type": "text", "text": string(encoded)}}, "details": metadata}, nil
}

func runtimeToolRead(ctx context.Context, root *os.Root, rel string, args domain.Object, max int64) (domain.Object, error) {
	for key := range args {
		if key != "path" && key != "offset" && key != "limit" {
			return nil, toolInvalid("unexpected read argument")
		}
	}
	data, err := runtimeToolBytes(root, rel)
	if err != nil {
		return nil, err
	}
	if !utf8.Valid(data) {
		return nil, toolDenied("read requires UTF-8 text")
	}
	offset := int64(0)
	if _, ok := args["offset"]; ok {
		offset, err = domain.Num(args, "offset")
		if err != nil || offset < 0 || offset > int64(len(data)) {
			return nil, toolInvalid("offset must be an in-file byte position")
		}
	}
	limit := max
	if _, ok := args["limit"]; ok {
		limit, err = domain.Num(args, "limit")
		if err != nil || limit < 1 || limit > max {
			return nil, toolInvalid("limit exceeds frozen byte bound")
		}
	}
	if offset < int64(len(data)) && !utf8.RuneStart(data[offset]) {
		return nil, toolInvalid("offset must be a UTF-8 boundary")
	}
	wantEnd := offset + limit
	if wantEnd > int64(len(data)) {
		wantEnd = int64(len(data))
	}
	for wantEnd < int64(len(data)) && !utf8.RuneStart(data[wantEnd]) {
		wantEnd--
	}
	if wantEnd == offset && offset < int64(len(data)) {
		return nil, toolInvalid("limit cannot fit the next UTF-8 rune")
	}
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	hash := domain.Digest(data)
	ends := []int64{offset}
	for end := offset; end < wantEnd; {
		_, size := utf8.DecodeRune(data[end:])
		end += int64(size)
		ends = append(ends, end)
	}
	build := func(index int) (domain.Object, bool, error) {
		reply, err := runtimeToolReadReply(rel, hash, data, offset, ends[index])
		if err != nil {
			return nil, false, err
		}
		return reply, len(domain.Bytes(reply)) <= runtimeToolReplyLimit, nil
	}
	if reply, fits, err := build(len(ends) - 1); err != nil || fits {
		return reply, err
	}
	lo, hi := 0, len(ends)-1
	for lo < hi {
		mid := lo + (hi-lo+1)/2
		if _, fits, err := build(mid); err != nil {
			return nil, err
		} else if fits {
			lo = mid
		} else {
			hi = mid - 1
		}
	}
	if lo == 0 && offset < int64(len(data)) {
		return nil, toolDenied("read result cannot fit bridge frame")
	}
	reply, fits, err := build(lo)
	if err != nil {
		return nil, err
	}
	if !fits {
		return nil, toolDenied("read result cannot fit bridge frame")
	}
	return reply, nil
}

func runtimeToolWrite(ctx context.Context, root *os.Root, rel, name string, args domain.Object, max int64) (result domain.Object, err error) {
	beforeMutation := true
	defer func() {
		if err != nil && beforeMutation {
			err = &domain.RuntimeToolFailure{Err: err, Outcome: "NOT_APPLIED"}
		}
	}()
	allowed := map[string]bool{"path": true, "expected_hash": true}
	if name == "write" {
		allowed["content"] = true
	} else {
		allowed["old_text"], allowed["new_text"] = true, true
	}
	for key := range args {
		if !allowed[key] {
			return nil, toolInvalid("unexpected write argument")
		}
	}
	expected, present := args["expected_hash"]
	if !present {
		return nil, toolInvalid("expected_hash is required")
	}
	create := expected == nil
	if name == "edit" && create {
		return nil, toolInvalid("edit requires an existing content hash")
	}
	var old []byte
	if create {
		if _, err := root.Lstat(rel); err == nil {
			return nil, toolDenied("create target already exists")
		} else if !errors.Is(err, os.ErrNotExist) {
			return nil, err
		}
	} else {
		oldHash, ok := expected.(string)
		if !ok || len(oldHash) != len(domain.Digest(nil)) || !strings.HasPrefix(oldHash, "sha256:") {
			return nil, toolInvalid("expected_hash must be sha256 digest")
		}
		var err error
		old, err = runtimeToolBytes(root, rel)
		if err != nil {
			return nil, err
		}
		if domain.Digest(old) != oldHash {
			return nil, domain.Fail(409, "STATE_CONFLICT", "stale expected_hash")
		}
	}
	var next string
	if name == "write" {
		var ok bool
		next, ok = args["content"].(string)
		if !ok {
			return nil, toolInvalid("content must be text")
		}
	} else {
		needle, okOld := args["old_text"].(string)
		replacement, okNew := args["new_text"].(string)
		if !okOld || !okNew || needle == "" || !utf8.Valid(old) || strings.Count(string(old), needle) != 1 {
			return nil, toolInvalid("old_text must occur exactly once in UTF-8 file")
		}
		next = strings.Replace(string(old), needle, replacement, 1)
	}
	if !utf8.ValidString(next) || int64(len(next)) > max || len(next) > runtimeToolFileLimit {
		return nil, toolDenied("write exceeds frozen UTF-8 byte bound")
	}
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	// A replacement can create a temporary file, publish via Link, or rename.
	// Once entered, an error does not prove that the effect was absent.
	beforeMutation = false
	if err := runtimeToolReplace(root, rel, []byte(next), create, expected); err != nil {
		return nil, err
	}
	return runtimeToolReply(domain.Object{"path": rel, "content_hash": domain.Digest([]byte(next)), "size_bytes": len(next), "operation": name})
}

func runtimeToolReplace(root *os.Root, rel string, next []byte, create bool, expected any) error {
	var nonce [16]byte
	if _, err := rand.Read(nonce[:]); err != nil {
		return err
	}
	tmp := path.Join(path.Dir(rel), ".researchos-"+hex.EncodeToString(nonce[:])+".tmp")
	f, err := root.OpenFile(tmp, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
	if err != nil {
		return err
	}
	defer root.Remove(tmp)
	_, writeErr := f.Write(next)
	if writeErr == nil {
		writeErr = f.Sync()
	}
	closeErr := f.Close()
	if writeErr != nil {
		return writeErr
	}
	if closeErr != nil {
		return closeErr
	}
	if create {
		// Link publishes complete bytes only if the name is still absent.
		if err := root.Link(tmp, rel); err != nil {
			return err
		}
		return nil
	}
	// The second check catches ordinary external edits before replacement. No
	// cross-process mutex can make this an atomic compare-and-swap against a
	// separately authorized external writer on Windows.
	current, err := runtimeToolBytes(root, rel)
	if err != nil {
		return err
	}
	if domain.Digest(current) != expected {
		return domain.Fail(409, "STATE_CONFLICT", "file changed before replacement")
	}
	return root.Rename(tmp, rel)
}
