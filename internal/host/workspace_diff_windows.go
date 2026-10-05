//go:build windows

package host

import (
	"bytes"
	"context"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strings"
	"unicode/utf8"

	"researchos.local/research-os/internal/domain"
)

const workspaceFullDiffLimit = 64 << 20

type limitedGitOutput struct {
	bytes.Buffer
	exceeded bool
}

func (b *limitedGitOutput) Write(p []byte) (int, error) {
	if b.Len()+len(p) > workspaceFullDiffLimit {
		b.exceeded = true
		return 0, errors.New("CONTENT_TOO_LARGE: Git output exceeds 64 MiB")
	}
	return b.Buffer.Write(p)
}

// gitLocal runs local, read-only Git operations with user/system configuration
// disabled. In particular, a repository cannot supply an external diff driver,
// textconv program, fsmonitor, or hook to execute during a workspace read.
func gitLocal(ctx context.Context, dir string, args ...string) ([]byte, error) {
	base := []string{"-c", "core.fsmonitor=false", "-c", "core.hooksPath=NUL", "-c", "diff.external=", "-c", "diff.noprefix=false"}
	cmd := exec.CommandContext(ctx, "git", append(base, args...)...)
	cmd.Dir = dir
	cmd.Env = make([]string, 0, len(os.Environ())+5)
	for _, item := range os.Environ() {
		key, _, _ := strings.Cut(item, "=")
		if strings.HasPrefix(strings.ToUpper(key), "GIT_") {
			continue
		}
		cmd.Env = append(cmd.Env, item)
	}
	cmd.Env = append(cmd.Env, "GIT_CONFIG_NOSYSTEM=1", "GIT_CONFIG_GLOBAL=NUL", "GIT_OPTIONAL_LOCKS=0", "GIT_ATTR_NOSYSTEM=1")
	var out limitedGitOutput
	cmd.Stdout = &out
	err := cmd.Run()
	if err != nil {
		if out.exceeded {
			return nil, errors.New("CONTENT_TOO_LARGE: Git output exceeds 64 MiB")
		}
		return out.Bytes(), fmt.Errorf("HOST_UNAVAILABLE: local Git operation failed: %w", err)
	}
	return out.Bytes(), nil
}

type workspaceChange struct {
	path   string
	status string
}

func parseGitNames(raw []byte) ([]workspaceChange, error) {
	parts := bytes.Split(raw, []byte{0})
	if len(parts) == 0 || len(parts[len(parts)-1]) != 0 {
		return nil, errors.New("HOST_UNAVAILABLE: malformed Git name-status output")
	}
	changes := make([]workspaceChange, 0, len(parts)/2)
	for i := 0; i < len(parts)-1; {
		if i+1 >= len(parts)-1 {
			return nil, errors.New("HOST_UNAVAILABLE: malformed Git name-status pair")
		}
		status := string(parts[i])
		path := string(parts[i+1])
		i += 2
		if strings.HasPrefix(status, "R") || strings.HasPrefix(status, "C") {
			if i >= len(parts)-1 {
				return nil, errors.New("HOST_UNAVAILABLE: malformed Git rename")
			}
			path = string(parts[i])
			i++
		}
		if len(status) == 0 {
			return nil, errors.New("HOST_UNAVAILABLE: empty Git status")
		}
		changes = append(changes, workspaceChange{path: path, status: status[:1]})
	}
	return changes, nil
}

func gitNulPaths(raw []byte) ([]string, error) {
	if len(raw) == 0 {
		return nil, nil
	}
	if raw[len(raw)-1] != 0 {
		return nil, errors.New("HOST_UNAVAILABLE: malformed Git path list")
	}
	items := strings.Split(string(raw[:len(raw)-1]), "\x00")
	return items, nil
}

func (h *Host) WorkspaceDiff(ctx context.Context, workspacePath, access string, payload domain.Object) (domain.Object, []byte, error) {
	base := domain.Str(payload, "base")
	if base != "HEAD" && base != "INDEX" {
		return nil, nil, errors.New("INVALID_REQUEST: base must be HEAD or INDEX")
	}
	maxBytes, err := workspaceNumber(payload, "max_bytes", workspaceReadLimit)
	if err != nil {
		return nil, nil, err
	}
	filter := ""
	if value := payload["relative_path"]; value != nil {
		var ok bool
		filter, ok = value.(string)
		if !ok {
			return nil, nil, errors.New("INVALID_REQUEST: relative_path must be string or null")
		}
		filter, err = workspaceRelativePath(filter, true)
		if err != nil {
			return nil, nil, err
		}
	}
	binding, root, err := h.workspaceRoot(workspacePath, access)
	if err != nil {
		return nil, nil, err
	}
	defer root.Close()
	if filter != "" && filter != "." {
		// A deleted path need not exist, so check only its present ancestors.
		parts := strings.Split(filter, "/")
		for i := 1; i < len(parts); i++ {
			if err = h.workspacePlain(root, binding, strings.Join(parts[:i], "/"), true); err != nil {
				return nil, nil, err
			}
		}
	}
	top, err := gitLocal(ctx, workspacePath, "rev-parse", "--show-toplevel")
	if err != nil || !strings.EqualFold(filepath.Clean(strings.TrimSpace(string(top))), filepath.Clean(workspacePath)) {
		return nil, nil, errors.New("NOT_A_REPOSITORY: workspace root must be the repository top level")
	}
	var revision string
	var diffArgs []string
	if base == "HEAD" {
		sha, shaErr := gitLocal(ctx, workspacePath, "rev-parse", "--verify", "HEAD")
		if shaErr != nil {
			return nil, nil, errors.New("NOT_FOUND: HEAD revision is not available")
		}
		revision = strings.TrimSpace(string(sha))
		diffArgs = []string{"diff", "--no-ext-diff", "--no-textconv", "--no-renames", "--name-status", "-z", "HEAD", "--"}
	} else {
		stage, stageErr := gitLocal(ctx, workspacePath, "ls-files", "--stage", "-z")
		if stageErr != nil {
			return nil, nil, stageErr
		}
		revision = domain.Digest(stage)
		diffArgs = []string{"diff", "--no-ext-diff", "--no-textconv", "--no-renames", "--name-status", "-z", "--"}
	}
	raw, err := gitLocal(ctx, workspacePath, diffArgs...)
	if err != nil {
		return nil, nil, err
	}
	changes, err := parseGitNames(raw)
	if err != nil {
		return nil, nil, err
	}
	untracked, err := gitLocal(ctx, workspacePath, "ls-files", "--others", "--exclude-standard", "-z", "--")
	if err != nil {
		return nil, nil, err
	}
	paths, err := gitNulPaths(untracked)
	if err != nil {
		return nil, nil, err
	}
	for _, path := range paths {
		changes = append(changes, workspaceChange{path: path, status: "?"})
	}
	selected := make([]workspaceChange, 0, len(changes))
	for _, change := range changes {
		rel, pathErr := workspaceRelativePath(filepath.ToSlash(change.path), false)
		if pathErr != nil {
			return nil, nil, errors.New("PATH_OUT_OF_SCOPE: unsafe Git path")
		}
		if filter != "" && filter != "." && rel != filter && !strings.HasPrefix(rel, filter+"/") {
			continue
		}
		change.path = rel
		selected = append(selected, change)
	}
	sort.Slice(selected, func(i, j int) bool { return selected[i].path < selected[j].path })
	files := make([]any, 0, min(len(selected), 500))
	full := make([]byte, 0)
	previewUsed := int64(0)
	truncated := len(selected) > 500
	for i, change := range selected {
		if err = ctx.Err(); err != nil {
			return nil, nil, err
		}
		status := map[string]string{"A": "ADDED", "M": "MODIFIED", "T": "MODIFIED", "D": "DELETED", "?": "UNTRACKED", "U": "CONFLICTED"}[change.status]
		if status == "" {
			return nil, nil, errors.New("HOST_UNAVAILABLE: unsupported Git status")
		}
		var before, after any
		if status != "UNTRACKED" && status != "ADDED" {
			blob := ":" + change.path
			if base == "HEAD" {
				blob = "HEAD:" + change.path
			}
			content, blobErr := gitLocal(ctx, workspacePath, "cat-file", "blob", blob)
			if blobErr == nil {
				before = domain.Digest(content)
			} else if status != "CONFLICTED" {
				return nil, nil, blobErr
			}
		}
		if status != "DELETED" {
			content, readErr := h.WorkspaceContent(ctx, workspacePath, access, change.path, workspaceContentLimit)
			if readErr != nil {
				return nil, nil, readErr
			}
			after = domain.Digest(content)
		}
		var patch []byte
		if status == "UNTRACKED" {
			patch, err = gitLocal(ctx, workspacePath, "diff", "--no-index", "--binary", "--no-ext-diff", "--no-textconv", "--", "NUL", filepath.FromSlash(change.path))
			// git diff --no-index returns 1 for an ordinary difference.
			if err != nil && !strings.Contains(err.Error(), "exit status 1") {
				return nil, nil, err
			}
		} else {
			args := []string{"diff", "--binary", "--no-ext-diff", "--no-textconv", "--no-renames"}
			if base == "HEAD" {
				args = append(args, "HEAD")
			}
			args = append(args, "--", filepath.FromSlash(change.path))
			patch, err = gitLocal(ctx, workspacePath, args...)
			if err != nil {
				return nil, nil, err
			}
		}
		if len(full)+len(patch) > workspaceFullDiffLimit {
			return nil, nil, errors.New("CONTENT_TOO_LARGE: full diff exceeds 64 MiB")
		}
		full = append(full, patch...)
		binary := bytes.Contains(patch, []byte("GIT binary patch")) || bytes.Contains(patch, []byte("Binary files")) || !utf8.Valid(patch)
		var preview any
		if !binary && previewUsed+int64(len(patch)) <= maxBytes {
			preview = string(patch)
			previewUsed += int64(len(patch))
		} else if len(patch) > 0 {
			truncated = true
		}
		if i < 500 {
			files = append(files, domain.Object{"relative_path": change.path, "previous_path": nil,
				"status": status, "before_hash": before, "after_hash": after, "binary": binary, "patch": preview})
		}
	}
	if err = h.workspacePlain(root, binding, ".", true); err != nil {
		return nil, nil, err
	}
	if base == "HEAD" {
		latest, revErr := gitLocal(ctx, workspacePath, "rev-parse", "--verify", "HEAD")
		if revErr != nil || strings.TrimSpace(string(latest)) != revision {
			return nil, nil, errors.New("CONTENT_CONFLICT: HEAD changed during diff")
		}
	} else {
		latest, revErr := gitLocal(ctx, workspacePath, "ls-files", "--stage", "-z")
		if revErr != nil || domain.Digest(latest) != revision {
			return nil, nil, errors.New("CONTENT_CONFLICT: index changed during diff")
		}
	}
	return domain.Object{"workspace_ref": payload["workspace_ref"], "base": base, "base_revision": revision,
		"files": files, "total_files": len(selected), "truncated": truncated, "full_diff_artifact_ref": nil}, full, nil
}
