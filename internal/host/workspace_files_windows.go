//go:build windows

package host

// User-visible workspace reads. The caller has already checked the durable
// WorkspaceBinding; this layer independently checks the native pinned root and
// uses os.Root for every traversal. No path supplied by the renderer is opened
// as an absolute filesystem path.

import (
	"context"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"
	"unicode/utf8"

	"researchos.local/research-os/internal/domain"
)

const workspaceReadLimit int64 = 1 << 20
const workspaceContentLimit int64 = 64 << 20

type workspaceCursor struct {
	Root string `json:"root"`
	Dir  string `json:"dir"`
	Hash string `json:"hash"`
	Last string `json:"last"`
}

func workspaceRelativePath(rel string, allowRoot bool) (string, error) {
	if allowRoot && rel == "." {
		return ".", nil
	}
	if rel == "." || len(rel) > 4096 || CheckRelativePath(rel) != nil {
		return "", ErrPathEscape
	}
	canonicalSeparators := strings.ReplaceAll(rel, `\`, "/")
	for _, segment := range strings.Split(canonicalSeparators, "/") {
		if segment == "" || segment == "." || strings.TrimRight(segment, " .") != segment ||
			strings.ContainsAny(segment, `:<>"|?*`) {
			return "", ErrPathEscape
		}
		for _, char := range segment {
			if char < 32 {
				return "", ErrPathEscape
			}
		}
		stem := strings.ToUpper(strings.SplitN(segment, ".", 2)[0])
		if stem == "CON" || stem == "PRN" || stem == "AUX" || stem == "NUL" ||
			(len(stem) == 4 && (strings.HasPrefix(stem, "COM") || strings.HasPrefix(stem, "LPT")) && stem[3] >= '1' && stem[3] <= '9') {
			return "", ErrPathEscape
		}
	}
	return NormalizeRelative(rel), nil
}

func (h *Host) workspaceRoot(workspacePath, access string) (*RootBinding, *os.Root, error) {
	if h == nil || h.roots == nil || (access != AccessReadOnly && access != AccessReadWrite) || workspacePath == "" {
		return nil, nil, ErrRootDenied
	}
	var match *RootBinding
	for _, candidate := range h.roots.List() {
		if strings.EqualFold(filepath.Clean(candidate.RealPath), filepath.Clean(workspacePath)) {
			if candidate.Revoked {
				return nil, nil, ErrRootRevoked
			}
			if match != nil || candidate.Access != access {
				return nil, nil, ErrRootDenied
			}
			match = candidate
		}
	}
	if match == nil {
		return nil, nil, ErrRootUnknown
	}
	if _, err := h.ResolveWorkspace(match.Ref, ".", AccessReadOnly); err != nil {
		return nil, nil, err
	}
	root, err := os.OpenRoot(match.RealPath)
	if err != nil {
		return nil, nil, err
	}
	vol, id, _, err := fileIdentity(match.RealPath)
	if err != nil || vol != match.VolumeID || id != match.FileID {
		root.Close()
		return nil, nil, ErrPathReparsePoint
	}
	return match, root, nil
}

func (h *Host) workspacePlain(root *os.Root, binding *RootBinding, rel string, directory bool) error {
	if _, err := h.ResolveWorkspace(binding.Ref, rel, AccessReadOnly); err != nil {
		return err
	}
	if rel == "." {
		if directory {
			return nil
		}
		return ErrPathEscape
	}
	parts := strings.Split(rel, "/")
	for i := range parts {
		prefix := strings.Join(parts[:i+1], "/")
		info, err := root.Lstat(prefix)
		if err != nil {
			return err
		}
		if info.Mode()&os.ModeSymlink != 0 || info.Mode()&os.ModeIrregular != 0 {
			return ErrPathReparsePoint
		}
		if i < len(parts)-1 || directory {
			if !info.IsDir() {
				return ErrPathEscape
			}
		} else if !info.Mode().IsRegular() {
			return ErrPathEscape
		}
	}
	return nil
}

func workspaceNumber(payload domain.Object, name string, maximum int64) (int64, error) {
	n, err := domain.Num(payload, name)
	if err != nil || n < 1 || n > maximum {
		return 0, fmt.Errorf("INVALID_REQUEST: %s must be 1..%d", name, maximum)
	}
	return n, nil
}

func (h *Host) WorkspaceContent(ctx context.Context, workspacePath, access, relativePath string, maxBytes int64) ([]byte, error) {
	if maxBytes < 1 || maxBytes > workspaceContentLimit {
		return nil, errors.New("INVALID_REQUEST: content limit must be 1..67108864")
	}
	rel, err := workspaceRelativePath(relativePath, false)
	if err != nil {
		return nil, err
	}
	binding, root, err := h.workspaceRoot(workspacePath, access)
	if err != nil {
		return nil, err
	}
	defer root.Close()
	if err = h.workspacePlain(root, binding, rel, false); err != nil {
		return nil, err
	}
	file, err := root.Open(rel)
	if err != nil {
		return nil, err
	}
	defer file.Close()
	info, err := file.Stat()
	if err != nil {
		return nil, err
	}
	if !info.Mode().IsRegular() {
		return nil, ErrPathReparsePoint
	}
	if info.Size() > maxBytes {
		return nil, errors.New("CONTENT_TOO_LARGE: file exceeds bounded read")
	}
	data, err := io.ReadAll(io.LimitReader(file, maxBytes+1))
	if err != nil {
		return nil, err
	}
	if int64(len(data)) > maxBytes {
		return nil, errors.New("CONTENT_TOO_LARGE: file grew during bounded read")
	}
	after, err := file.Stat()
	if err != nil {
		return nil, err
	}
	if after.Size() != int64(len(data)) || !after.ModTime().Equal(info.ModTime()) {
		return nil, errors.New("CONTENT_CONFLICT: file changed during read")
	}
	if err = ctx.Err(); err != nil {
		return nil, err
	}
	if err = h.workspacePlain(root, binding, rel, false); err != nil {
		return nil, err
	}
	return data, nil
}

func (h *Host) WorkspaceRead(ctx context.Context, workspacePath, access string, payload domain.Object) (domain.Object, error) {
	rel, err := workspaceRelativePath(domain.Str(payload, "relative_path"), false)
	if err != nil {
		return nil, err
	}
	limit, err := workspaceNumber(payload, "max_bytes", workspaceReadLimit)
	if err != nil {
		return nil, err
	}
	data, err := h.WorkspaceContent(ctx, workspacePath, access, rel, limit)
	if err != nil {
		return nil, err
	}
	if !utf8.Valid(data) {
		return nil, errors.New("UNSUPPORTED_CONTENT: file is not UTF-8")
	}
	// Read metadata from the same pinned root again. A concurrent replacement is
	// refused instead of pairing old bytes with a new modified_at timestamp.
	binding, root, err := h.workspaceRoot(workspacePath, access)
	if err != nil {
		return nil, err
	}
	defer root.Close()
	if err = h.workspacePlain(root, binding, rel, false); err != nil {
		return nil, err
	}
	info, err := root.Stat(rel)
	if err != nil {
		return nil, err
	}
	if info.Size() != int64(len(data)) {
		return nil, errors.New("CONTENT_CONFLICT: file changed after read")
	}
	return domain.Object{"workspace_ref": payload["workspace_ref"], "relative_path": rel,
		"content_hash": domain.Digest(data), "byte_size": len(data), "encoding": "UTF-8",
		"text": string(data), "modified_at": info.ModTime().UTC().Format(time.RFC3339Nano),
		"editable": access == AccessReadWrite}, nil
}

func (h *Host) WorkspaceTree(ctx context.Context, workspacePath, access string, payload domain.Object) (domain.Object, error) {
	rel, err := workspaceRelativePath(domain.Str(payload, "relative_path"), true)
	if err != nil {
		return nil, err
	}
	limit, err := workspaceNumber(payload, "limit", 500)
	if err != nil {
		return nil, err
	}
	binding, root, err := h.workspaceRoot(workspacePath, access)
	if err != nil {
		return nil, err
	}
	defer root.Close()
	if err = h.workspacePlain(root, binding, rel, true); err != nil {
		return nil, err
	}
	dir, err := root.Open(rel)
	if err != nil {
		return nil, err
	}
	defer dir.Close()
	children, err := dir.ReadDir(-1)
	if err != nil {
		return nil, err
	}
	sort.Slice(children, func(i, j int) bool { return children[i].Name() < children[j].Name() })
	fingerprint := make([]any, 0, len(children))
	for _, child := range children {
		info, statErr := child.Info()
		if statErr != nil {
			fingerprint = append(fingerprint, []any{child.Name(), "unavailable"})
			continue
		}
		fingerprint = append(fingerprint, []any{child.Name(), info.Mode().String(), info.Size(), info.ModTime().UTC().Format(time.RFC3339Nano)})
	}
	digest := domain.Hash(fingerprint)
	start := 0
	if token, ok := payload["cursor"].(string); ok && token != "" {
		if len(token) > 2048 {
			return nil, errors.New("CURSOR_INVALID: cursor too long")
		}
		decoded, decodeErr := base64.RawURLEncoding.DecodeString(token)
		var cursor workspaceCursor
		if decodeErr != nil || json.Unmarshal(decoded, &cursor) != nil || cursor.Root != binding.Ref || cursor.Dir != rel || cursor.Hash != digest || cursor.Last == "" {
			return nil, errors.New("CURSOR_INVALID: workspace directory changed or cursor mismatch")
		}
		start = sort.Search(len(children), func(i int) bool { return children[i].Name() > cursor.Last })
		if start == 0 || children[start-1].Name() != cursor.Last {
			return nil, errors.New("CURSOR_INVALID: prior entry no longer exists")
		}
	} else if payload["cursor"] != nil {
		return nil, errors.New("INVALID_REQUEST: cursor must be string or null")
	}
	end := start + int(limit)
	if end > len(children) {
		end = len(children)
	}
	entries := make([]any, 0, end-start)
	for _, child := range children[start:end] {
		if err = ctx.Err(); err != nil {
			return nil, err
		}
		name := child.Name()
		childRel := name
		if rel != "." {
			childRel = rel + "/" + name
		}
		entry := domain.Object{"relative_path": childRel, "name": name, "kind": "UNSUPPORTED",
			"byte_size": nil, "content_hash": nil, "modified_at": nil,
			"readable": false, "reason_code": "UNSUPPORTED_CONTENT"}
		if _, pathErr := workspaceRelativePath(childRel, false); pathErr != nil {
			entry["reason_code"] = "PATH_OUT_OF_SCOPE"
			entries = append(entries, entry)
			continue
		}
		info, statErr := root.Lstat(childRel)
		if statErr != nil {
			entry["reason_code"] = "FORBIDDEN"
			entries = append(entries, entry)
			continue
		}
		entry["modified_at"] = info.ModTime().UTC().Format(time.RFC3339Nano)
		if info.Mode()&os.ModeSymlink != 0 || info.Mode()&os.ModeIrregular != 0 {
			entry["kind"], entry["reason_code"] = "SYMLINK", "PATH_OUT_OF_SCOPE"
		} else if reparse, reparseErr := isReparsePoint(filepath.Join(binding.RealPath, filepath.FromSlash(childRel))); reparseErr != nil {
			entry["reason_code"] = "FORBIDDEN"
		} else if reparse {
			entry["kind"], entry["reason_code"] = "SYMLINK", "PATH_OUT_OF_SCOPE"
		} else if info.IsDir() {
			entry["kind"], entry["readable"], entry["reason_code"] = "DIRECTORY", true, nil
		} else if info.Mode().IsRegular() {
			entry["kind"], entry["byte_size"] = "FILE", info.Size()
			if info.Size() > workspaceReadLimit {
				entry["reason_code"] = "CONTENT_TOO_LARGE"
			} else if data, readErr := h.WorkspaceContent(ctx, workspacePath, access, childRel, workspaceReadLimit); readErr == nil {
				if utf8.Valid(data) {
					entry["readable"], entry["reason_code"], entry["content_hash"] = true, nil, domain.Digest(data)
				}
			} else {
				entry["reason_code"] = "FORBIDDEN"
			}
		}
		entries = append(entries, entry)
	}
	var next any
	if end < len(children) {
		cursor := workspaceCursor{Root: binding.Ref, Dir: rel, Hash: digest, Last: children[end-1].Name()}
		encoded, _ := json.Marshal(cursor)
		next = base64.RawURLEncoding.EncodeToString(encoded)
	}
	if err = h.workspacePlain(root, binding, rel, true); err != nil {
		return nil, err
	}
	return domain.Object{"workspace_ref": payload["workspace_ref"], "root_revision": 1,
		"entries": entries, "next_cursor": next}, nil
}
