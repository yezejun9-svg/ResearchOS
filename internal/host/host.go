// Package host is the trusted local host boundary (W17-01). It owns three things the plain
// command protocol must never own: the one-time OWNER bootstrap bound to the OS user, the
// short-lived session credential that can be renewed without the user ever copying a token,
// and the protected storage for provider credentials and workspace-root bindings.
//
// Business truth stays in the existing domain layer: this package calls domain.ProvisionPrincipal
// and domain.IssueCredential instead of writing auth_* tables itself, and its own local state
// (credential vault, root registry, single-use selection references) lives in a private
// current-user directory as files, never as a second set of business tables.
package host

import (
	"crypto/sha256"
	"database/sql"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"time"

	"researchos.local/research-os/internal/auth"
	"researchos.local/research-os/internal/domain"
)

const (
	// MaxSessionTTL mirrors the existing host credential ceiling (22: short sessions only).
	MaxSessionTTL = 15 * time.Minute
	// DefaultSessionTTL is what the host issues unless configured lower.
	DefaultSessionTTL = MaxSessionTTL
	// SelectionTTL is the published single-use window for a workspace selection reference.
	SelectionTTL = 5 * time.Minute
	// MaxSelectionRecords bounds the local reference table so a hostile loop cannot grow it.
	MaxSelectionRecords = 256
)

var (
	ErrNoOwner            = errors.New("OWNER_NOT_INITIALIZED")
	ErrMultipleOwners     = errors.New("MULTIPLE_OWNER_STATE")
	ErrOwnerTaken         = errors.New("OWNER_ALREADY_INITIALIZED")
	ErrPrincipalRevoked   = errors.New("PRINCIPAL_REVOKED")
	ErrHostIdentity       = errors.New("OS_IDENTITY_MISMATCH")
	ErrUntrustedTransport = errors.New("UNTRUSTED_TRANSPORT")
	// ErrUntrustedPathChoice refuses a directory a client named by itself when no user chooser
	// confirmed it: binding a caller-typed path is how a "user-chosen workspace" becomes a
	// drive-by path.
	ErrUntrustedPathChoice = errors.New("FORBIDDEN")
	ErrBadState            = errors.New("HOST_STATE_INVALID")
)

// Config wires the host onto an already-migrated database. ContractsDir and MigrationFile are
// the existing host inputs (same values apps/control uses) so domain validation stays one
// implementation rather than a second one tuned for tests.
type Config struct {
	DB            *sql.DB
	Dir           string
	ContractsDir  string
	MigrationFile string
	SessionTTL    time.Duration
	// SchemaDir holds the pinned client.protocol.schema.json plus domain.schema.json the bridge
	// grades its frames against. Without it the host refuses to start rather than accepting
	// frames nobody has graded.
	SchemaDir string
	Now       func() time.Time
	// AllowNonWindows is only used to keep the package buildable; the bootstrap path refuses
	// to run anywhere the OS identity cannot be verified as the local principal.
	AllowNonWindows bool
	// PeerIdentityResolver decides who is on the other end of a native connection. The default
	// is the real OS lookup (auth.ProcessIdentity). Qualification may substitute it to prove the
	// serve path refuses a peer whose resolved principal is not the host owner: the seam only
	// replaces the OS answer, it cannot replace the comparison, so a host that stopped comparing
	// would accept a peer the resolver called foreign.
	PeerIdentityResolver func(pid uint32) (auth.Identity, error)
	// ProtocolVersion is the version this host stamps into bridge replies. It defaults to the
	// pinned researchos-client/2; a host built for any other version has its replies refused by
	// contract grading, which is what keeps the bridge from growing a private dialect.
	ProtocolVersion string
}

// Host is one trusted local host instance.
type Host struct {
	db       *sql.DB
	domain   *domain.Service
	dir      string
	ttl      time.Duration
	identity auth.Identity
	now      func() time.Time

	doc schemaDocument

	peerLookup      func(pid uint32) (auth.Identity, error)
	protocolVersion string

	vault      *Vault
	roots      *RootRegistry
	selections *SelectionStore
	state      *hostState
}

// New verifies the OS identity first: a host that cannot name the local principal is not
// allowed to bootstrap, renew, or accept native calls at all.
func New(cfg Config) (*Host, error) {
	if cfg.DB == nil || cfg.Dir == "" || cfg.ContractsDir == "" || cfg.MigrationFile == "" || cfg.SchemaDir == "" {
		return nil, fmt.Errorf("%w: db, dir, contracts, migration and schema are required", ErrBadState)
	}
	ttl := cfg.SessionTTL
	if ttl <= 0 || ttl > MaxSessionTTL {
		ttl = DefaultSessionTTL
	}
	now := cfg.Now
	if now == nil {
		now = func() time.Time { return time.Now().UTC() }
	}
	id, err := auth.Current()
	if err != nil {
		return nil, err
	}
	if !verifiableKind(id.Kind) {
		return nil, fmt.Errorf("%w: host identity kind %s is not a verifiable local principal", ErrHostIdentity, id.Kind)
	}
	if err := os.MkdirAll(cfg.Dir, 0o700); err != nil {
		return nil, err
	}
	if err := privateDir(cfg.Dir); err != nil {
		return nil, fmt.Errorf("private host directory refused: %w", err)
	}
	doc, err := loadSchema(cfg.SchemaDir)
	if err != nil {
		return nil, err
	}
	svc, err := domain.New(cfg.DB, cfg.ContractsDir, cfg.MigrationFile)
	if err != nil {
		return nil, err
	}
	h := &Host{db: cfg.DB, domain: svc, dir: cfg.Dir, ttl: ttl, identity: id, now: now, doc: doc}
	h.peerLookup = cfg.PeerIdentityResolver
	if h.peerLookup == nil {
		h.peerLookup = auth.ProcessIdentity
	}
	h.protocolVersion = cfg.ProtocolVersion
	if h.protocolVersion == "" {
		h.protocolVersion = nativeProtocolVersion
	}
	if h.vault, err = openVault(cfg.Dir); err != nil {
		return nil, err
	}
	if h.roots, err = openRootRegistry(cfg.Dir); err != nil {
		return nil, err
	}
	if h.selections, err = openSelectionStore(cfg.Dir); err != nil {
		return nil, err
	}
	if h.state, err = loadHostState(cfg.Dir); err != nil {
		return nil, err
	}
	return h, nil
}

// verifiableKind accepts WINDOWS_SID today; the POSIX path must be re-qualified before it is
// trusted as a local principal, so anything else fails closed.
func verifiableKind(kind string) bool { return kind == "WINDOWS_SID" }

// Identity exposes the verified OS principal reference (never the raw SID).
func (h *Host) Identity() auth.Identity { return h.identity }

// InstanceID is a stable local host identifier for handshake responses; it is derived from
// the private directory path plus the principal reference, so it changes if either does.
func (h *Host) InstanceID() string {
	sum := sha256.Sum256([]byte(h.dir + "|" + h.identity.Ref))
	return "host-" + hex.EncodeToString(sum[:6])
}

// writePrivate stores a file with 0600 plus the current-user-only DACL and a durable rename,
// so a crash cannot leave a half-written credential or root registry.
func writePrivate(dir, name string, payload any) error {
	raw, err := json.MarshalIndent(payload, "", "  ")
	if err != nil {
		return err
	}
	tmp, err := os.CreateTemp(dir, name+".tmp-")
	if err != nil {
		return err
	}
	defer os.Remove(tmp.Name())
	if err := tmp.Chmod(0o600); err != nil {
		tmp.Close()
		return err
	}
	if _, err := tmp.Write(raw); err != nil {
		tmp.Close()
		return err
	}
	if err := tmp.Sync(); err != nil {
		tmp.Close()
		return err
	}
	if err := tmp.Close(); err != nil {
		return err
	}
	if err := privateFile(tmp.Name()); err != nil {
		return err
	}
	return os.Rename(tmp.Name(), filepath.Join(dir, name))
}

func readPrivate(dir, name string, into any) error {
	raw, err := os.ReadFile(filepath.Join(dir, name))
	if err != nil {
		if errors.Is(err, os.ErrNotExist) {
			return nil
		}
		return err
	}
	return json.Unmarshal(raw, into)
}
