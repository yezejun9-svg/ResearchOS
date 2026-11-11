package host

import (
	"crypto/rand"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"
)

// Vault is the protected provider-credential store (22 §credential intake): plaintext material
// enters here only, through the native bridge, and the rest of the system ever sees a
// reference plus an availability state. There is deliberately no exported method that returns
// plaintext to a caller outside this package, and no listing method that reveals values.
const (
	MaxCredentialBytes = 4096
	MaxWrappedBytes    = 16384
)

// Status is what an ordinary response may report.
const (
	StatusAvailable = "AVAILABLE"
	StatusMissing   = "MISSING"
	StatusRevoked   = "REVOKED"
)

var (
	ErrCredentialTooLarge    = errors.New("CREDENTIAL_TOO_LARGE")
	ErrCredentialUnprintable = errors.New("CREDENTIAL_MUST_BE_PRINTABLE")
	ErrCredentialProtected   = errors.New("CREDENTIAL_PROTECTION_UNAVAILABLE")
	ErrUnknownCredential     = errors.New("CREDENTIAL_UNKNOWN")
)

type vaultRecord struct {
	Ref      string `json:"ref"`
	Provider string `json:"provider"`
	Kind     string `json:"kind"`
	Wrapped  []byte `json:"wrapped"`
	StoredAt string `json:"stored_at"`
	Revoked  bool   `json:"revoked"`
	// MaterialDigest lets qualification prove the vault round-trips the same bytes without
	// any caller having to read them back out.
	MaterialDigest string `json:"material_digest"`
}

type vaultIndex struct {
	Version int      `json:"version"`
	Records []string `json:"refs"`
	Revoked []string `json:"revoked"`
}

// Vault stores each credential as its own current-user-only file plus a ref-only index, so a
// directory listing or a log line can never carry material.
type Vault struct {
	dir  string
	path string
	readOnly bool
	allowedRef string
	allowedProvider string
}

// openVaultReadOnly references one existing sealed record without copying,
// importing, revoking or changing the original vault directory.
func openVaultReadOnly(hostDir, ref, provider string) (*Vault, error) {
	if !filepath.IsAbs(hostDir) || ref == "" || provider == "" {
		return nil, ErrUnknownCredential
	}
	resolved, err := filepath.EvalSymlinks(hostDir)
	if err != nil || !strings.EqualFold(resolved, filepath.Clean(hostDir)) {
		return nil, ErrUnknownCredential
	}
	d := filepath.Join(resolved, "credentials")
	info, err := os.Lstat(d)
	if err != nil || !info.IsDir() || info.Mode()&os.ModeSymlink != 0 {
		return nil, ErrUnknownCredential
	}
	canonicalCredentials, err := filepath.EvalSymlinks(d)
	if err != nil || !strings.EqualFold(canonicalCredentials, filepath.Clean(d)) {
		return nil, ErrUnknownCredential
	}
	for _, name := range []string{"index.json", ref + ".dpapi"} {
		path := filepath.Join(d, name)
		entry, err := os.Lstat(path)
		if err != nil || !entry.Mode().IsRegular() || entry.Mode()&os.ModeSymlink != 0 {
			return nil, ErrUnknownCredential
		}
	}
	v := &Vault{dir: d, path: filepath.Join(d, "index.json"), readOnly: true,
		allowedRef: ref, allowedProvider: provider}
	idx, err := v.load()
	if err != nil {
		return nil, err
	}
	found := false
	for _, known := range idx.Records {
		if known == ref { found = true }
	}
	if !found { return nil, ErrUnknownCredential }
	record, err := v.record(ref)
	if err != nil || record.Revoked || record.Provider != provider {
		return nil, ErrUnknownCredential
	}
	return v, nil
}

// ValidateTrialVaultIsolation runs before any trial data-root lease, database open,
// migration or host mkdir. Both roots must exist as ordinary directories. EvalSymlinks
// rejects path aliases/reparse ancestors; SameFile catches Windows spelling aliases.
// The new data root must be disjoint from the entire old protected resource root,
// not merely from its host/credentials child.
func ValidateTrialVaultIsolation(dataRoot, oldHostDir string) error {
    if !filepath.IsAbs(dataRoot) || !filepath.IsAbs(oldHostDir) {
        return ErrUnknownCredential
    }
    clean := func(path string) (string, error) {
        path = filepath.Clean(path)
        for current := path; ; current = filepath.Dir(current) {
            info, err := os.Lstat(current)
            if err != nil || !info.IsDir() || info.Mode()&os.ModeSymlink != 0 {
                return "", ErrUnknownCredential
            }
            resolved, err := filepath.EvalSymlinks(current)
            if err != nil || !strings.EqualFold(resolved, current) {
                return "", ErrUnknownCredential
            }
            if filepath.Dir(current) == current { break }
        }
        return path, nil
    }
    data, err := clean(dataRoot)
    if err != nil { return err }
    hostDir, err := clean(oldHostDir)
    if err != nil { return err }
    protected, err := clean(filepath.Dir(hostDir))
    if err != nil { return err }
    sameAncestor := func(target, descendant string) bool {
        wanted, err := os.Stat(target)
        if err != nil { return true }
        for current := descendant; ; current = filepath.Dir(current) {
            actual, err := os.Stat(current)
            if err != nil || os.SameFile(wanted, actual) { return true }
            if filepath.Dir(current) == current { break }
        }
        return false
    }
    if sameAncestor(data, protected) || sameAncestor(protected, data) {
        return ErrUnknownCredential
    }
    return nil
}

// ValidateTrialStorageLayout checks the actual child paths before lease, DB
// creation or Host.New privateDir work. A missing host/DB leaf is allowed only
// below an already verified ordinary data-root directory.
func ValidateTrialStorageLayout(dataRoot, newHostDir, oldHostDir string) error {
    if err := ValidateTrialVaultIsolation(dataRoot, oldHostDir); err != nil {
        return err
    }
    expectedHost := filepath.Join(filepath.Clean(dataRoot), "host")
    if !filepath.IsAbs(newHostDir) || !strings.EqualFold(filepath.Clean(newHostDir), expectedHost) {
        return ErrUnknownCredential
    }
    checkLeaf := func(path string, wantDir bool) error {
        info, err := os.Lstat(path)
        if os.IsNotExist(err) { return nil }
        if err != nil || info.Mode()&(os.ModeSymlink|os.ModeIrregular) != 0 {
            return ErrUnknownCredential
        }
        if wantDir != info.IsDir() {
            return ErrUnknownCredential
        }
        resolved, err := filepath.EvalSymlinks(path)
        if err != nil || !strings.EqualFold(resolved, filepath.Clean(path)) {
            return ErrUnknownCredential
        }
        old, err := os.Stat(oldHostDir)
        if err != nil { return ErrUnknownCredential }
        actual, err := os.Stat(path)
        if err != nil || os.SameFile(actual, old) { return ErrUnknownCredential }
        oldDB := filepath.Join(filepath.Dir(oldHostDir), "researchos.sqlite")
        original, err := os.Stat(oldDB)
        if err != nil && !os.IsNotExist(err) { return ErrUnknownCredential }
        if err == nil && os.SameFile(actual, original) {
            return ErrUnknownCredential
        }
        return nil
    }
    if err := checkLeaf(newHostDir, true); err != nil { return err }
    return checkLeaf(filepath.Join(filepath.Clean(dataRoot), "researchos.sqlite"), false)
}

func openVault(dir string) (*Vault, error) {
	d := filepath.Join(dir, "credentials")
	if err := os.MkdirAll(d, 0o700); err != nil {
		return nil, err
	}
	if err := privateDir(d); err != nil {
		return nil, err
	}
	return &Vault{dir: d, path: filepath.Join(d, "index.json")}, nil
}

// credentialRef is unique per store operation: a repeated clock or identical material must not
// make two credentials collide on one reference, because that would let a revoke destroy the
// wrong record. The random suffix is a label, not secret material.
func credentialRef(provider, kind string, storedAt time.Time, digest string, nonce []byte) string {
	return fmt.Sprintf("cred-%s-%s-%d-%s-%x", sanitize(provider), sanitize(kind), storedAt.UTC().UnixNano(),
		strings.TrimPrefix(digest, "sha256:")[:8], nonce)
}

func sanitize(s string) string {
	var b strings.Builder
	for _, r := range strings.ToLower(s) {
		if (r >= 'a' && r <= 'z') || (r >= '0' && r <= '9') {
			b.WriteByte(byte(r))
			continue
		}
		b.WriteByte('_')
	}
	out := b.String()
	if len(out) > 24 {
		out = out[:24]
	}
	return out
}

// Store protects the plaintext with the OS user's DPAPI master key, writes it 0600 under a
// protected DACL, and returns only the reference. The caller's buffer is zeroed here on every
// exit path, including errors.
func (v *Vault) Store(provider, kind string, material []byte, now time.Time) (ref string, err error) {
	defer func() {
		for i := range material {
			material[i] = 0
		}
	}()
	if v.readOnly { return "", ErrCredentialProtected }
	if len(material) == 0 || len(material) > MaxCredentialBytes {
		return "", ErrCredentialTooLarge
	}
	for _, b := range material {
		if b < 33 || b > 126 {
			return "", ErrCredentialUnprintable
		}
	}
	wrapped, err := protect(material)
	if err != nil {
		return "", fmt.Errorf("%w: %v", ErrCredentialProtected, err)
	}
	if len(wrapped) == 0 || len(wrapped) > MaxWrappedBytes {
		return "", ErrCredentialProtected
	}
	materialDigest := digestBytes(material)
	rec := vaultRecord{Provider: provider, Kind: kind, Wrapped: wrapped,
		StoredAt: now.UTC().Format(time.RFC3339Nano), MaterialDigest: materialDigest}
	// the reference itself is derived from the wrapped material's digest, not from the material
	nonce := make([]byte, 4)
	if _, err := rand.Read(nonce); err != nil {
		return "", err
	}
	rec.Ref = credentialRef(provider, kind, now, digestBytes(wrapped), nonce)
	ref = rec.Ref
	if err := writePrivate(v.dir, ref+".dpapi", rec); err != nil {
		return "", err
	}
	idx, err := v.load()
	if err != nil {
		return "", err
	}
	idx.Version = 1
	idx.Records = append(idx.Records, ref)
	return ref, v.save(idx)
}

// Open is intentionally package-private: only code inside the host can decrypt, and it is used
// by the provider-adapter path, never by a protocol response, event or log.
func (v *Vault) open(ref string) ([]byte, error) {
	rec, err := v.record(ref)
	if err != nil {
		return nil, err
	}
	if rec.Revoked {
		return nil, ErrUnknownCredential
	}
	return unprotect(rec.Wrapped)
}

func (v *Vault) record(ref string) (*vaultRecord, error) {
	if v.readOnly && ref != v.allowedRef { return nil, ErrUnknownCredential }
	var rec vaultRecord
	if err := readPrivate(v.dir, ref+".dpapi", &rec); err != nil {
		return nil, err
	}
	if rec.Ref == "" || rec.Ref != ref || v.readOnly && rec.Provider != v.allowedProvider {
		return nil, fmt.Errorf("%w: %s", ErrUnknownCredential, ref)
	}
	return &rec, nil
}

// Status is the only public view of a credential: reference plus availability, never material.
func (v *Vault) Status(ref string) string {
	rec, err := v.record(ref)
	if err != nil || rec == nil {
		return StatusMissing
	}
	if rec.Revoked {
		return StatusRevoked
	}
	return StatusAvailable
}

// Revoke marks a record revoked and destroys its wrapped bytes, so a later reference lookup
// reports REVOKED and no path can recover the material.
func (v *Vault) Revoke(ref string) error {
	if v.readOnly { return ErrCredentialProtected }
	rec, err := v.record(ref)
	if err != nil {
		return err
	}
	for i := range rec.Wrapped {
		rec.Wrapped[i] = 0
	}
	rec.Revoked = true
	rec.MaterialDigest = ""
	if err := writePrivate(v.dir, ref+".dpapi", rec); err != nil {
		return err
	}
	idx, err := v.load()
	if err != nil {
		return err
	}
	idx.Revoked = append(idx.Revoked, ref)
	return v.save(idx)
}

// Refs lists references (never values or providers' secrets) for host diagnostics.
func (v *Vault) Refs() ([]string, error) {
	idx, err := v.load()
	if err != nil {
		return nil, err
	}
	return append([]string(nil), idx.Records...), nil
}

func (v *Vault) load() (*vaultIndex, error) {
	var idx vaultIndex
	if err := readPrivate(v.dir, "index.json", &idx); err != nil {
		return nil, err
	}
	if idx.Records == nil {
		idx.Records = []string{}
	}
	if idx.Revoked == nil {
		idx.Revoked = []string{}
	}
	return &idx, nil
}

func (v *Vault) save(idx *vaultIndex) error { return writePrivate(v.dir, "index.json", idx) }
