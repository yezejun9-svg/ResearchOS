package host

// Workspace root binding (22 §workspace binding, 04 §鉴权). A root is registered once from a
// user-chosen directory, pinned by volume serial plus file index so a later junction or symlink
// swap of the same path is detectable, and revoked rather than "appearing empty" when access is
// withdrawn - an inaccessible directory must never be presented as an empty one.

import (
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"sync"
	"time"
)

const (
	AccessReadOnly  = "READ_ONLY"
	AccessReadWrite = "READ_WRITE"
)

type RootBinding struct {
	Ref          string `json:"ref"`
	DisplayPath  string `json:"display_path"`
	RealPath     string `json:"real_path"`
	Access       string `json:"access"`
	VolumeID     string `json:"volume_id"`
	FileID       uint64 `json:"file_id"`
	FinalPath    string `json:"final_path"`
	RegisteredAt string `json:"registered_at"`
	Revoked      bool   `json:"revoked"`
}

type rootIndex struct {
	Version int            `json:"version"`
	Roots   []*RootBinding `json:"roots"`
}

type RootRegistry struct {
	dir   string
	mu    sync.RWMutex
	roots map[string]*RootBinding
}

func openRootRegistry(dir string) (*RootRegistry, error) {
	d := filepath.Join(dir, "workspaces")
	if err := os.MkdirAll(d, 0o700); err != nil {
		return nil, err
	}
	if err := privateDir(d); err != nil {
		return nil, err
	}
	r := &RootRegistry{dir: d, roots: map[string]*RootBinding{}}
	var idx rootIndex
	if err := readPrivate(d, "roots.json", &idx); err != nil {
		return nil, err
	}
	for _, b := range idx.Roots {
		if b != nil && b.Ref != "" {
			r.roots[b.Ref] = b
		}
	}
	return r, nil
}

func (r *RootRegistry) save() error {
	idx := rootIndex{Version: 1}
	for _, ref := range sortedRefs(r.roots) {
		idx.Roots = append(idx.Roots, r.roots[ref])
	}
	if idx.Roots == nil {
		idx.Roots = []*RootBinding{}
	}
	return writePrivate(r.dir, "roots.json", &idx)
}

func sortedRefs(m map[string]*RootBinding) []string {
	out := make([]string, 0, len(m))
	for k := range m {
		out = append(out, k)
	}
	sort.Strings(out)
	return out
}

// Register pins the chosen directory. A path that is itself a reparse point, or whose parent
// chain contains one, is refused: the binding must describe the real directory the user picked.
func (r *RootRegistry) Register(ref, displayPath, access string, now time.Time) (*RootBinding, error) {
	if ref == "" || displayPath == "" {
		return nil, fmt.Errorf("%w: root ref and path are required", ErrBadState)
	}
	if access != AccessReadOnly && access != AccessReadWrite {
		return nil, fmt.Errorf("%w: unknown workspace access", ErrRootDenied)
	}
	abs, err := filepath.Abs(displayPath)
	if err != nil {
		return nil, err
	}
	real, err := filepath.EvalSymlinks(abs)
	if err != nil {
		return nil, err
	}
	if cleanReal := filepath.Clean(real); cleanReal != filepath.Clean(abs) {
		return nil, fmt.Errorf("%w: chosen path resolves through a link", ErrPathReparsePoint)
	}
	if reparse, err := chainHasReparsePoint(clean(real)); err != nil {
		return nil, err
	} else if reparse {
		return nil, ErrPathReparsePoint
	}
	vol, id, final, err := fileIdentity(clean(real))
	if err != nil {
		return nil, err
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	if existing, ok := r.roots[ref]; ok && !existing.Revoked {
		return nil, fmt.Errorf("%w: root ref already registered", ErrBadState)
	}
	b := &RootBinding{Ref: ref, DisplayPath: displayPath, RealPath: clean(real), Access: access,
		VolumeID: vol, FileID: id, FinalPath: final, RegisteredAt: now.UTC().Format(time.RFC3339Nano)}
	r.roots[ref] = b
	if err := r.save(); err != nil {
		delete(r.roots, ref)
		return nil, err
	}
	return b, nil
}

// Resolve validates one published relative path against a bound root and returns the absolute
// path to use. Every check is re-done per access: registration time correctness does not grant
// later immunity, because links and permissions can change underneath.
func (r *RootRegistry) Resolve(ref, rel, wantAccess string) (string, error) {
	r.mu.RLock()
	b, ok := r.roots[ref]
	r.mu.RUnlock()
	if !ok || b == nil {
		return "", ErrRootUnknown
	}
	if b.Revoked {
		return "", ErrRootRevoked
	}
	if wantAccess == AccessReadWrite && b.Access == AccessReadOnly {
		return "", ErrRootDenied
	}
	if err := CheckRelativePath(rel); err != nil {
		return "", err
	}
	if err := r.verifyStillPinned(b); err != nil {
		return "", err
	}
	vol, id, _, err := fileIdentity(b.RealPath)
	if err != nil {
		return "", ErrRootRevoked
	}
	if vol != b.VolumeID || id != b.FileID {
		// Same path, different object: the authorised root was replaced under us.
		return "", ErrPathReparsePoint
	}
	abs := filepath.Join(b.RealPath, filepath.FromSlash(NormalizeRelative(rel)))
	inside, err := filepath.Rel(b.RealPath, abs)
	if err != nil || inside == ".." || strings.HasPrefix(inside, ".."+string(filepath.Separator)) {
		return "", ErrPathEscape
	}
	if reparse, err := chainHasReparsePoint(abs); err != nil {
		return "", err
	} else if reparse {
		return "", ErrPathReparsePoint
	}
	return abs, nil
}

// List returns the live bindings for the host's own diagnostics. A revoked root is reported as
// revoked (never silently as "no files"), which is what the contract demands.
// nextRef derives an unambiguous binding reference from the current count plus nanoseconds, so a
// revoked root's reference can never be silently reused.
func (r *RootRegistry) nextRef() (string, error) {
	r.mu.RLock()
	n := len(r.roots)
	r.mu.RUnlock()
	return hostRef("ws", n), nil
}

func (r *RootRegistry) List() []*RootBinding {
	r.mu.RLock()
	defer r.mu.RUnlock()
	out := make([]*RootBinding, 0, len(r.roots))
	for _, ref := range sortedRefs(r.roots) {
		b := *r.roots[ref]
		out = append(out, &b)
	}
	return out
}

func (r *RootRegistry) Status(ref string) string {
	r.mu.RLock()
	defer r.mu.RUnlock()
	b, ok := r.roots[ref]
	if !ok || b == nil {
		return StatusMissing
	}
	if b.Revoked {
		return StatusRevoked
	}
	return StatusAvailable
}

func (r *RootRegistry) Revoke(ref string) error {
	r.mu.Lock()
	defer r.mu.Unlock()
	b, ok := r.roots[ref]
	if !ok || b == nil {
		return ErrRootUnknown
	}
	b.Revoked = true
	return r.save()
}

var errPinnedRootLost = errors.New("pinned workspace root is unavailable")

func (r *RootRegistry) verifyStillPinned(b *RootBinding) error {
	if _, err := os.Stat(b.RealPath); err != nil {
		return errPinnedRootLost
	}
	return nil
}

func clean(p string) string { return filepath.Clean(p) }
