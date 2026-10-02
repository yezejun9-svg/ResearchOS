package localworkspace

// The local inventory is the first thing a new project gets, and it is deliberately limited to
// what is inside the one directory the user chose. 15_NEW_PROJECT_WORKFLOW §2 requires the record
// to distinguish FOUND / NOT_FOUND / NOT_CHECKED / NOT_ACCESSIBLE: "不能把未访问等同于没有".
// So a skipped subtree is written as NOT_CHECKED with the reason, an unreadable directory is
// NOT_ACCESSIBLE, and never does an unreadable root come back as an empty inventory.
//
// Content never leaves this package. What is recorded is a digest of the file that was parsed and
// a fixed reason string, so an inventory cannot become a channel for private source material.

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"io"
	"io/fs"
	"os"
	"path/filepath"
	"runtime"
	"sort"
	"strings"

	"researchos.local/research-os/internal/domain"
)

const (
	// MaxInventoryEntries bounds one inventory. A larger tree is recorded honestly as truncated
	// and NOT_CHECKED rather than silently shortened.
	MaxInventoryEntries = 200
	// MaxScanDepth keeps a pathological deep tree from stalling a first-use bootstrap.
	MaxScanDepth = 8
	// MaxHashedFileBytes is the size cap for content digests.
	MaxHashedFileBytes = 1 << 20
	// EnvironmentLabel names what kind of machine produced the inventory without leaking a path.
	EnvironmentLabel = "local-windows"
	otherEnvLabel    = "local-posix"
)

// Scanner satisfies domain.LocalInventoryScanner for one authorized directory at a time.
type Scanner struct {
	// SkipDirectories are subtree names whose contents are not inventoried (their existence is
	// still reported, as NOT_CHECKED, because "we did not look" is not "there is nothing").
	SkipDirectories []string
}

// NewScanner returns the default first-use scanner.
func NewScanner() *Scanner {
	return &Scanner{SkipDirectories: []string{".git", "node_modules", "vendor", ".venv", "__pycache__", "dist", "build"}}
}

func (s *Scanner) skip(name string) bool {
	for _, d := range s.SkipDirectories {
		if strings.EqualFold(name, d) {
			return true
		}
	}
	return false
}

// Scan walks exactly realPath. Every location_ref it returns is relative to that root, so the
// domain can refuse an entry that points outside without trusting this package.
func (s *Scanner) Scan(ctx context.Context, realPath string) (domain.LocalInventoryScan, error) {
	env := EnvironmentLabel
	if runtime.GOOS != "windows" {
		env = otherEnvLabel
	}
	out := domain.LocalInventoryScan{Environment: env, Entries: []domain.LocalInventoryEntry{}, Failures: []domain.LocalInventoryFileFailure{}}
	if realPath == "" {
		return out, nil
	}
	if st, err := os.Stat(realPath); err != nil || !st.IsDir() {
		// An unreadable or vanished root is recorded as the root being inaccessible. It is never
		// reported as an empty directory.
		out.Entries = append(out.Entries, domain.LocalInventoryEntry{Capability: "workspace_root", LocationRef: ".",
			Status: "NOT_ACCESSIBLE", Notes: reasonOf(err)})
		out.Failures = append(out.Failures, domain.LocalInventoryFileFailure{Path: ".", Reason: reasonOf(err)})
		return out, nil
	}
	out.Entries = append(out.Entries, domain.LocalInventoryEntry{Capability: "workspace_root", LocationRef: ".",
		Status: "FOUND", Notes: "authorized directory is readable"})
	// Reserve room for the verdict entries so hitting the entry cap cannot silence the very marker
	// that says the inventory was shortened.
	capacity := MaxInventoryEntries - 8
	// The root is resolved once, then every subtree is asked the same question: does the directory
	// I am about to enter still live under that root? A junction or symlink answers no, and it is
	// recorded as unexamined instead of being walked, because walking it would quietly widen the
	// authorised scope to a directory the user never chose. An OS link flag alone is not enough:
	// an NTFS junction is not reported as a symlink by the directory iterator.
	rootReal, rerr := filepath.EvalSymlinks(realPath)
	if rerr != nil {
		rootReal = realPath
	}
	rootReal = filepath.Clean(rootReal)

	seen := map[string]bool{}
	add := func(e domain.LocalInventoryEntry) {
		key := e.Capability + "|" + e.LocationRef
		if seen[key] || len(out.Entries) >= capacity {
			return
		}
		seen[key] = true
		out.Entries = append(out.Entries, e)
	}
	// addVerdict appends a statement about the scan itself. It ignores the capability cap on
	// purpose: the entries that say "this inventory is incomplete" must survive an incomplete
	// inventory, or the cap would erase the only evidence of it.
	addVerdict := func(e domain.LocalInventoryEntry) {
		key := e.Capability + "|" + e.LocationRef
		if seen[key] {
			return
		}
		seen[key] = true
		out.Entries = append(out.Entries, e)
	}
	markAbsent := func(capability string) {
		if !seen[capability+"|*"] {
			add(domain.LocalInventoryEntry{Capability: capability, LocationRef: "*", Status: "NOT_FOUND",
				Notes: "not present anywhere in the authorized directory"})
		}
	}

	found := map[string]bool{}
	truncated := false
	unexamined := false
	skippedSubtrees := 0
	// Version control lives at the root, and the directory branch below returns before it would
	// ever be inspected, so it is decided once here instead of by an unreachable loop variable.
	// A .git entry is version control whether it is a directory, a worktree pointer file or a
	// submodule stub; treating the file form as absent would be a false NOT_FOUND.
	if st, e := os.Lstat(filepath.Join(realPath, ".git")); e == nil && !st.IsDir() {
		found["version_control"] = true
	} else if e == nil {
		found["version_control"] = true
	}

	walkErr := filepath.WalkDir(realPath, func(path string, d fs.DirEntry, err error) error {
		if ctx.Err() != nil {
			return ctx.Err()
		}
		rel, e := filepath.Rel(realPath, path)
		if e != nil {
			return e
		}
		relSlash := filepath.ToSlash(rel)
		if rel == "." {
			return nil
		}
		if depth := strings.Count(relSlash, "/"); depth > MaxScanDepth {
			if d.IsDir() {
				skippedSubtrees++
				unexamined = true
				add(domain.LocalInventoryEntry{Capability: "subtree_beyond_depth", LocationRef: relSlash,
					Status: "NOT_CHECKED", Notes: "depth cap exceeded"})
				return fs.SkipDir
			}
			return nil
		}
		if err != nil {
			out.Failures = append(out.Failures, domain.LocalInventoryFileFailure{Path: relSlash, Reason: reasonOf(err)})
			add(domain.LocalInventoryEntry{Capability: "unreachable_path", LocationRef: relSlash,
				Status: "NOT_ACCESSIBLE", Notes: reasonOf(err)})
			return nil
		}
		if d.Type()&fs.ModeSymlink != 0 || d.Type() == fs.ModeIrregular || reparsePoint(path) ||
			(d.IsDir() && escapesRoot(rootReal, path)) {
			// A link out of the authorized directory is recorded and not followed.
			skippedSubtrees++
			unexamined = true
			add(domain.LocalInventoryEntry{Capability: "reparse_point", LocationRef: relSlash,
				Status: "NOT_CHECKED", Notes: "link is not followed out of the authorized directory"})
			if d.IsDir() {
				return fs.SkipDir
			}
			return nil
		}
		if d.IsDir() {
			if s.skip(d.Name()) {
				skippedSubtrees++
				unexamined = true
				add(domain.LocalInventoryEntry{Capability: "excluded_subtree", LocationRef: relSlash,
					Status: "NOT_CHECKED", Notes: "contents are not inventoried on first use"})
				return fs.SkipDir
			}
			if strings.EqualFold(d.Name(), ".git") {
				found["version_control"] = true
			}
			return nil
		}
		if len(out.Entries) >= capacity {
			truncated = true
			return filepath.SkipAll
		}
		name := strings.ToLower(d.Name())
		switch name {
		case "go.mod":
			found["go_module"] = true
			add(domain.LocalInventoryEntry{Capability: "go_module", LocationRef: relSlash, Status: "FOUND",
				RevisionOrHash: digestOf(path), Notes: "go module definition"})
		case "package.json":
			found["node_manifest"] = true
			version, e := readJSONVersion(path)
			if e != nil {
				out.Failures = append(out.Failures, domain.LocalInventoryFileFailure{Path: relSlash, Reason: e.Error()})
				add(domain.LocalInventoryEntry{Capability: "node_manifest", LocationRef: relSlash, Status: "NOT_CHECKED",
					RevisionOrHash: digestOf(path), Notes: "manifest could not be parsed: " + e.Error()})
			} else {
				add(domain.LocalInventoryEntry{Capability: "node_manifest", LocationRef: relSlash, Status: "FOUND",
					RevisionOrHash: digestOf(path), Notes: "node manifest version " + version})
			}
		case "pyproject.toml", "requirements.txt":
			found["python_manifest"] = true
			add(domain.LocalInventoryEntry{Capability: "python_manifest", LocationRef: relSlash, Status: "FOUND",
				RevisionOrHash: digestOf(path), Notes: "python dependency declaration"})
		case "readme.md", "readme.rst", "readme":
			found["readme"] = true
			add(domain.LocalInventoryEntry{Capability: "readme", LocationRef: relSlash, Status: "FOUND",
				RevisionOrHash: digestOf(path), Notes: "project description present"})
		case ".researchos-project":
			found["researchos_project_marker"] = true
			add(domain.LocalInventoryEntry{Capability: "researchos_project_marker", LocationRef: relSlash, Status: "FOUND",
				RevisionOrHash: digestOf(path), Notes: "directory already carries a ResearchOS identity file"})
		default:
			if filepath.Ext(name) == ".json" {
				// Any other JSON document is still something the project may depend on. A parse
				// failure is recorded against that file, and the entry says NOT_CHECKED rather
				// than vanishing from the inventory.
				if _, e := readJSONVersion(path); e != nil {
					out.Failures = append(out.Failures, domain.LocalInventoryFileFailure{Path: relSlash, Reason: e.Error()})
					add(domain.LocalInventoryEntry{Capability: "unparsed_json", LocationRef: relSlash, Status: "NOT_CHECKED",
						RevisionOrHash: digestOf(path), Notes: "could not be parsed: " + e.Error()})
				} else {
					add(domain.LocalInventoryEntry{Capability: "json_document", LocationRef: relSlash, Status: "FOUND",
						RevisionOrHash: digestOf(path), Notes: "JSON document readable"})
				}
			}
			if ext := filepath.Ext(name); ext == ".go" || ext == ".py" || ext == ".ts" || ext == ".tsx" || ext == ".sql" {
				if !found["source_tree"] {
					found["source_tree"] = true
					add(domain.LocalInventoryEntry{Capability: "source_tree", LocationRef: firstDirOf(relSlash),
						Status: "FOUND", Notes: "source files present"})
				}
			}
		}
		return nil
	})
	if walkErr != nil && !strings.Contains(walkErr.Error(), "context") {
		out.Failures = append(out.Failures, domain.LocalInventoryFileFailure{Path: ".", Reason: reasonOf(walkErr)})
	}
	// Absence may only be claimed over ground that was actually walked. A skipped subtree, an
	// unfollowed link, a depth cut or an entry cap all mean "we did not look", and
	// 15_NEW_PROJECT_WORKFLOW line 31 forbids reading that as "there is none".
	if unexamined || truncated || skippedSubtrees > 0 {
		addVerdict(domain.LocalInventoryEntry{Capability: "scan_completeness", LocationRef: "*", Status: "NOT_CHECKED",
			Notes: "the walk was shortened by a skip, link, depth cap or entry cap"})
	}
	if found["version_control"] {
		add(domain.LocalInventoryEntry{Capability: "version_control", LocationRef: ".git", Status: "FOUND",
			Notes: "version control directory present at the authorised root"})
	}
	for _, c := range append([]string{"version_control"}, []string{"go_module", "node_manifest", "python_manifest",
		"readme", "source_tree", "researchos_project_marker"}...) {
		if found[c] {
			continue
		}
		if unexamined || truncated || skippedSubtrees > 0 {
			addVerdict(domain.LocalInventoryEntry{Capability: c, LocationRef: "*", Status: "NOT_CHECKED",
				Notes: "not seen in the part that was walked; unexamined subtrees remain"})
			continue
		}
		markAbsent(c)
	}
	if truncated {
		unexamined = true
		addVerdict(domain.LocalInventoryEntry{Capability: "inventory_truncated", LocationRef: "*", Status: "NOT_CHECKED",
			Notes: "entry cap reached; the rest of the tree was not examined"})
	}
	if skippedSubtrees > 0 {
		addVerdict(domain.LocalInventoryEntry{Capability: "unexamined_subtrees", LocationRef: "*", Status: "NOT_CHECKED",
			Notes: "subtrees that were skipped, links or excluded directories"})
	}
	sort.Slice(out.Entries, func(i, j int) bool {
		if out.Entries[i].Capability == out.Entries[j].Capability {
			return out.Entries[i].LocationRef < out.Entries[j].LocationRef
		}
		return out.Entries[i].Capability < out.Entries[j].Capability
	})
	return out, nil
}

func firstDirOf(rel string) string {
	if i := strings.LastIndex(rel, "/"); i > 0 {
		return rel[:i]
	}
	return "."
}

func reasonOf(err error) string {
	if err == nil {
		return "unreadable"
	}
	// The message is classified, never forwarded: an OS error can carry a full path.
	switch {
	case os.IsPermission(err):
		return "permission denied"
	case os.IsNotExist(err):
		return "path no longer exists"
	default:
		return "unreadable"
	}
}

func digestOf(path string) *string {
	f, err := os.Open(path)
	if err != nil {
		return nil
	}
	defer f.Close()
	h := sha256.New()
	n, err := io.Copy(h, io.LimitReader(f, MaxHashedFileBytes))
	if err != nil || n == 0 {
		return nil
	}
	sum := "sha256:" + hex.EncodeToString(h.Sum(nil))
	return &sum
}

// readJSONVersion extracts only the version field, so a manifest's other content stays local.
func readJSONVersion(path string) (string, error) {
	f, err := os.Open(path)
	if err != nil {
		return "", err
	}
	defer f.Close()
	var doc struct {
		Version string `json:"version"`
	}
	body, err := io.ReadAll(io.LimitReader(f, MaxHashedFileBytes))
	if err != nil {
		return "", err
	}
	if err := json.Unmarshal(body, &doc); err != nil {
		return "", errJSONParse
	}
	if doc.Version == "" {
		return "unspecified", nil
	}
	return doc.Version, nil
}

var errJSONParse = &parseError{"manifest is not valid JSON"}

type parseError struct{ msg string }

func (p *parseError) Error() string { return p.msg }

// escapesRoot reports whether a directory resolves, after every link, to something outside the
// authorised root. Comparison is case-insensitive on Windows because that is what the filesystem
// is.
func escapesRoot(rootReal, path string) bool {
	tgt, err := filepath.EvalSymlinks(path)
	if err != nil {
		return false // unreadable links are handled by the walk error branch
	}
	tgt = filepath.Clean(tgt)
	if runtime.GOOS == "windows" {
		return !strings.EqualFold(tgt, rootReal) &&
			!strings.HasPrefix(strings.ToLower(tgt+string(filepath.Separator)), strings.ToLower(rootReal+string(filepath.Separator)))
	}
	return tgt != rootReal && !strings.HasPrefix(tgt+string(filepath.Separator), rootReal+string(filepath.Separator))
}

var _ domain.LocalInventoryScanner = (*Scanner)(nil)
