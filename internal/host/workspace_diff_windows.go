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

// gitLocal is used against a repository only for metadata and immutable blobs.
// Worktree comparisons run against copies in a fresh directory outside the
// repository: Git's ordinary diff can execute repository clean/process filters.
func gitLocal(ctx context.Context, dir string, args ...string) ([]byte, error) {
	base := []string{"-c", "core.fsmonitor=false", "-c", "core.hooksPath=NUL", "-c", "diff.external=", "-c", "core.quotePath=false"}
	cmd := exec.CommandContext(ctx, "git", append(base, args...)...)
	cmd.Dir = dir
	cmd.Env = make([]string, 0, len(os.Environ())+6)
	for _, item := range os.Environ() {
		key, _, _ := strings.Cut(item, "=")
		if strings.HasPrefix(strings.ToUpper(key), "GIT_") {
			continue
		}
		cmd.Env = append(cmd.Env, item)
	}
	cmd.Env = append(cmd.Env, "GIT_CONFIG_NOSYSTEM=1", "GIT_CONFIG_GLOBAL=NUL", "GIT_OPTIONAL_LOCKS=0", "GIT_ATTR_NOSYSTEM=1", "GIT_NO_REPLACE_OBJECTS=1", "GIT_LITERAL_PATHSPECS=1")
	var out limitedGitOutput
	cmd.Stdout = &out
	if err := cmd.Run(); err != nil {
		if out.exceeded {
			return nil, errors.New("CONTENT_TOO_LARGE: Git output exceeds 64 MiB")
		}
		return out.Bytes(), fmt.Errorf("HOST_UNAVAILABLE: local Git operation failed: %w", err)
	}
	return out.Bytes(), nil
}

type gitFile struct {
	mode       string
	sha        string
	conflicted bool
}

func gitNulPaths(raw []byte) ([]string, error) {
	if len(raw) == 0 {
		return nil, nil
	}
	if raw[len(raw)-1] != 0 {
		return nil, errors.New("HOST_UNAVAILABLE: malformed Git path list")
	}
	return strings.Split(string(raw[:len(raw)-1]), "\x00"), nil
}

func gitFileList(raw []byte, staged bool) (map[string]gitFile, error) {
	paths, err := gitNulPaths(raw)
	if err != nil {
		return nil, err
	}
	result := make(map[string]gitFile, len(paths))
	for _, record := range paths {
		meta, path, ok := strings.Cut(record, "\t")
		fields := strings.Fields(meta)
		if !ok || path == "" || (staged && len(fields) != 3) || (!staged && (len(fields) != 3 || fields[1] != "blob" && fields[1] != "commit")) {
			return nil, errors.New("HOST_UNAVAILABLE: malformed Git file inventory")
		}
		file := gitFile{mode: fields[0], sha: fields[1]}
		if staged {
			file.sha = fields[1]
			if fields[2] != "0" {
				file.conflicted = true
			}
		} else {
			file.sha = fields[2]
		}
		if previous, exists := result[path]; exists && previous.conflicted {
			continue
		}
		result[path] = file
	}
	return result, nil
}

func workspacePatch(ctx context.Context, temp, relative string, before, after []byte, hasBefore, hasAfter bool) ([]byte, error) {
	oldName, newName := "before", "after"
	for _, name := range []string{oldName, newName} {
		if err := os.Remove(filepath.Join(temp, name)); err != nil && !errors.Is(err, os.ErrNotExist) {
			return nil, err
		}
	}
	if hasBefore {
		if err := os.WriteFile(filepath.Join(temp, oldName), before, 0600); err != nil {
			return nil, err
		}
	} else {
		oldName = "NUL"
	}
	if hasAfter {
		if err := os.WriteFile(filepath.Join(temp, newName), after, 0600); err != nil {
			return nil, err
		}
	} else {
		newName = "NUL"
	}
	patch, err := gitLocal(ctx, temp, "diff", "--no-index", "--binary", "--no-ext-diff", "--no-textconv", "--", oldName, newName)
	if err != nil {
		var exit *exec.ExitError
		if !errors.As(err, &exit) || exit.ExitCode() != 1 {
			return nil, err
		}
	}
	// Only rewrite Git's headers, never hunk or binary-patch data. Control
	// characters and quotes are excluded by workspaceRelativePath.
	var output bytes.Buffer
	for _, line := range bytes.SplitAfter(patch, []byte{'\n'}) {
		switch {
		case bytes.HasPrefix(line, []byte("diff --git ")):
			line = []byte("diff --git a/" + relative + " b/" + relative + "\n")
		case bytes.HasPrefix(line, []byte("--- ")) && !bytes.HasPrefix(line, []byte("--- /dev/null")):
			line = []byte("--- a/" + relative + "\n")
		case bytes.HasPrefix(line, []byte("+++ ")) && !bytes.HasPrefix(line, []byte("+++ /dev/null")):
			line = []byte("+++ b/" + relative + "\n")
		case bytes.HasPrefix(line, []byte("Binary files ")):
			line = []byte("Binary files a/" + relative + " and b/" + relative + " differ\n")
		}
		output.Write(line)
	}
	return output.Bytes(), nil
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
	stageRaw, err := gitLocal(ctx, workspacePath, "ls-files", "--stage", "-z")
	if err != nil {
		return nil, nil, err
	}
	indexFiles, err := gitFileList(stageRaw, true)
	if err != nil {
		return nil, nil, err
	}
	revision := domain.Digest(stageRaw)
	baseFiles := indexFiles
	if base == "HEAD" {
		sha, shaErr := gitLocal(ctx, workspacePath, "rev-parse", "--verify", "HEAD")
		if shaErr != nil {
			return nil, nil, errors.New("NOT_FOUND: HEAD revision is not available")
		}
		revision = strings.TrimSpace(string(sha))
		headRaw, headErr := gitLocal(ctx, workspacePath, "ls-tree", "-r", "-z", "--full-tree", "HEAD")
		if headErr != nil {
			return nil, nil, headErr
		}
		baseFiles, err = gitFileList(headRaw, false)
		if err != nil {
			return nil, nil, err
		}
	}
	untrackedRaw, err := gitLocal(ctx, workspacePath, "ls-files", "--others", "--exclude-standard", "-z")
	if err != nil {
		return nil, nil, err
	}
	untracked, err := gitNulPaths(untrackedRaw)
	if err != nil {
		return nil, nil, err
	}
	all := map[string]bool{}
	for name := range baseFiles {
		all[name] = true
	}
	for name := range indexFiles {
		all[name] = true
	}
	for _, name := range untracked {
		all[name] = true
	}
	selected := make([]string, 0, len(all))
	for name := range all {
		rel, pathErr := workspaceRelativePath(filepath.ToSlash(name), false)
		if pathErr != nil || rel != name {
			return nil, nil, errors.New("PATH_OUT_OF_SCOPE: unsafe Git path")
		}
		if filter == "" || filter == "." || rel == filter || strings.HasPrefix(rel, filter+"/") {
			selected = append(selected, rel)
		}
	}
	sort.Strings(selected)
	temp, err := os.MkdirTemp("", "researchos-diff-")
	if err != nil {
		return nil, nil, err
	}
	defer func() {
		_ = os.Remove(filepath.Join(temp, "before"))
		_ = os.Remove(filepath.Join(temp, "after"))
		_ = os.Remove(temp)
	}()
	absTemp, err := filepath.Abs(temp)
	if err != nil {
		return nil, nil, err
	}
	if relative, relErr := filepath.Rel(workspacePath, absTemp); relErr == nil && relative != ".." && !strings.HasPrefix(relative, ".."+string(filepath.Separator)) {
		return nil, nil, errors.New("HOST_UNAVAILABLE: temporary diff directory lies within workspace")
	}
	files := make([]any, 0, min(len(selected), 500))
	full := make([]byte, 0)
	previewUsed := int64(0)
	truncated := false
	total := 0
	for _, name := range selected {
		if err = ctx.Err(); err != nil {
			return nil, nil, err
		}
		prior, hasBefore := baseFiles[name]
		if hasBefore && prior.mode != "100644" && prior.mode != "100755" {
			return nil, nil, errors.New("PATH_OUT_OF_SCOPE: unsupported tracked file type")
		}
		var before, after []byte
		if hasBefore && !prior.conflicted {
			before, err = gitLocal(ctx, workspacePath, "cat-file", "blob", prior.sha)
			if err != nil {
				return nil, nil, err
			}
		}
		after, err = h.WorkspaceContent(ctx, workspacePath, access, name, workspaceContentLimit)
		hasAfter := err == nil
		if err != nil && !errors.Is(err, os.ErrNotExist) {
			return nil, nil, err
		}
		if !hasBefore && !hasAfter || hasBefore && hasAfter && bytes.Equal(before, after) && !prior.conflicted {
			continue
		}
		status := "MODIFIED"
		if prior.conflicted {
			status = "CONFLICTED"
		} else if !hasBefore {
			status = "UNTRACKED"
			if _, tracked := indexFiles[name]; tracked {
				status = "ADDED"
			}
		} else if !hasAfter {
			status = "DELETED"
		}
		patch, patchErr := workspacePatch(ctx, temp, name, before, after, hasBefore && !prior.conflicted, hasAfter)
		if patchErr != nil {
			return nil, nil, patchErr
		}
		if len(full)+len(patch) > workspaceFullDiffLimit {
			return nil, nil, errors.New("CONTENT_TOO_LARGE: full diff exceeds 64 MiB")
		}
		full = append(full, patch...)
		binary := bytes.IndexByte(before, 0) >= 0 || bytes.IndexByte(after, 0) >= 0 || !utf8.Valid(before) || !utf8.Valid(after) || bytes.Contains(patch, []byte("GIT binary patch"))
		var preview any
		if !binary && previewUsed+int64(len(patch)) <= maxBytes {
			preview = string(patch)
			previewUsed += int64(len(patch))
		} else if len(patch) > 0 {
			truncated = true
		}
		if len(files) < 500 {
			var beforeHash, afterHash any
			if hasBefore && !prior.conflicted {
				beforeHash = domain.Digest(before)
			}
			if hasAfter {
				afterHash = domain.Digest(after)
			}
			files = append(files, domain.Object{"relative_path": name, "previous_path": nil,
				"status": status, "before_hash": beforeHash, "after_hash": afterHash, "binary": binary, "patch": preview})
		} else {
			truncated = true
		}
		total++
		// Catch edits during patch generation. The advertised hash and patch always
		// describe the same bytes even if a later independent edit follows.
		latest, checkErr := h.WorkspaceContent(ctx, workspacePath, access, name, workspaceContentLimit)
		if hasAfter && (checkErr != nil || !bytes.Equal(latest, after)) || !hasAfter && checkErr == nil {
			return nil, nil, errors.New("CONTENT_CONFLICT: worktree changed during diff")
		}
		if !hasAfter && checkErr != nil && !errors.Is(checkErr, os.ErrNotExist) {
			return nil, nil, checkErr
		}
	}
	if err = h.workspacePlain(root, binding, ".", true); err != nil {
		return nil, nil, err
	}
	latestStage, err := gitLocal(ctx, workspacePath, "ls-files", "--stage", "-z")
	if err != nil || !bytes.Equal(latestStage, stageRaw) {
		return nil, nil, errors.New("CONTENT_CONFLICT: index changed during diff")
	}
	if base == "HEAD" {
		latest, revErr := gitLocal(ctx, workspacePath, "rev-parse", "--verify", "HEAD")
		if revErr != nil || strings.TrimSpace(string(latest)) != revision {
			return nil, nil, errors.New("CONTENT_CONFLICT: HEAD changed during diff")
		}
	}
	return domain.Object{"workspace_ref": payload["workspace_ref"], "base": base, "base_revision": revision,
		"files": files, "total_files": total, "truncated": truncated, "full_diff_artifact_ref": nil}, full, nil
}
