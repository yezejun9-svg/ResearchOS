package recoveryauthority

import (
	"bytes"
	"encoding/json"
	"errors"
	"sync"
	"time"
)

const MigrationPurpose = "RESEARCHOS_PREPARED_SCHEMA23_TO24_V1"
const MigrationPlanID = "schema23-to24-prepared-abandonment-v1"
const MigrationSQLSHA256 = "sha256:1c606771104c3b9abaaedaadb55d8e8c16d5f91f3398fa283ec9886b935f9098"
const MigrationArgument = "--private-prepared-schema23-to24"

type MigrationBinding struct {
	PlanID                string `json:"plan_id"`
	OwnerRoot             string `json:"owner_root"`
	ProjectID             string `json:"project_id"`
	Root                  string `json:"root"`
	RootIdentity          string `json:"root_identity"`
	Database              string `json:"database"`
	DatabaseIdentity      string `json:"database_identity"`
	SourceReleaseSHA256   string `json:"source_release_sha256"`
	TargetReleaseSHA256   string `json:"target_release_sha256"`
	SourceInventorySHA256 string `json:"source_inventory_sha256"`
	TargetInventorySHA256 string `json:"target_inventory_sha256"`
	SourceSchemaSHA256    string `json:"source_schema_sha256"`
	TargetSchemaSHA256    string `json:"target_schema_sha256"`
	SQLSHA256             string `json:"sql_sha256"`
	OriginalRowsSHA256    string `json:"original_rows_sha256"`
	OptionsSHA256         string `json:"options_sha256"`
	Backup                RawPin `json:"backup"`
	Rehearsal             RawPin `json:"rehearsal"`
}
type MigrationGrant struct {
	Schema        string           `json:"schema"`
	Purpose       string           `json:"purpose"`
	Stage         string           `json:"stage"`
	ReleaseSHA256 string           `json:"release_sha256"`
	Nonce         string           `json:"nonce"`
	IssuedUTC     string           `json:"issued_utc"`
	ExpiresUTC    string           `json:"expires_utc"`
	Binding       MigrationBinding `json:"binding"`
	// Every accepted source/target program, complete release inventory, exact
	// SQL, backup/rehearsal bytes and original IO must be retained raw pins.
	Pins    []RawPin        `json:"pins"`
	Options json.RawMessage `json:"options"`
}

func validMigrationBinding(b MigrationBinding) error {
	if b.PlanID != MigrationPlanID || b.OwnerRoot == "" || b.ProjectID == "" || b.Root == "" || b.RootIdentity == "" || b.Database == "" || b.DatabaseIdentity == "" || b.SQLSHA256 != MigrationSQLSHA256 {
		return errors.New("AUTHORITY_MIGRATION_BINDING")
	}
	for _, s := range []string{b.SourceReleaseSHA256, b.TargetReleaseSHA256, b.SourceInventorySHA256, b.TargetInventorySHA256, b.SourceSchemaSHA256, b.TargetSchemaSHA256, b.OriginalRowsSHA256, b.OptionsSHA256, b.Backup.SHA256, b.Rehearsal.SHA256} {
		if !validHash(s) {
			return errors.New("AUTHORITY_MIGRATION_DIGEST")
		}
	}
	if b.Backup.Path == "" || b.Backup.Bytes <= 0 || b.Backup.Role != "encrypted-backup-manifest" || b.Rehearsal.Path == "" || b.Rehearsal.Bytes <= 0 || b.Rehearsal.Role != "isolated-restore-rehearsal" {
		return errors.New("AUTHORITY_MIGRATION_BACKUP_REHEARSAL")
	}
	return nil
}
func verifyMigrationGrant(raw, releaseRaw []byte) (MigrationGrant, error) {
	var g MigrationGrant
	if e := verifyDocument(raw, MigrationPurpose+"/grant", &g); e != nil {
		return g, e
	}
	nonce, e := hexNonce(g.Nonce)
	if e != nil || len(nonce) != 32 || g.Schema != "researchos.recovery-migration-grant.v1" || g.Purpose != MigrationPurpose || g.Stage != "APPLY_ORIGINAL" || g.ReleaseSHA256 != digest(releaseRaw) || !validInterval(g.IssuedUTC, g.ExpiresUTC, time.Now(), 5*time.Minute) {
		return g, errors.New("AUTHORITY_MIGRATION_GRANT")
	}
	if e = validMigrationBinding(g.Binding); e != nil {
		return g, e
	}
	if digest(g.Options) != g.Binding.OptionsSHA256 {
		return g, errors.New("AUTHORITY_MIGRATION_OPTIONS")
	}
	required := map[string]string{"source-program": g.Binding.SourceReleaseSHA256, "target-program": g.Binding.TargetReleaseSHA256, "migration-sql": MigrationSQLSHA256, "encrypted-backup-manifest": g.Binding.Backup.SHA256, "isolated-restore-rehearsal": g.Binding.Rehearsal.SHA256}
	seen := map[string]bool{}
	for _, p := range g.Pins {
		if seen[p.Role] || !validHash(p.SHA256) || p.Bytes < 0 || p.Path == "" {
			return g, errors.New("AUTHORITY_MIGRATION_RAW_PINS")
		}
		seen[p.Role] = true
		if expected, ok := required[p.Role]; ok && expected != p.SHA256 {
			return g, errors.New("AUTHORITY_MIGRATION_PIN_BINDING")
		}
		if p.Role == g.Binding.Backup.Role && !bytes.Equal(encoded(p), encoded(g.Binding.Backup)) {
			return g, errors.New("AUTHORITY_MIGRATION_BACKUP_PIN")
		}
		if p.Role == g.Binding.Rehearsal.Role && !bytes.Equal(encoded(p), encoded(g.Binding.Rehearsal)) {
			return g, errors.New("AUTHORITY_MIGRATION_REHEARSAL_PIN")
		}
	}
	for role := range required {
		if !seen[role] {
			return g, errors.New("AUTHORITY_MIGRATION_MISSING_PIN")
		}
	}
	return g, nil
}

// MigrationToken cannot be converted to Token. Its scope contains no Run
// mutation, abandonment evidence, runtime dispatch or financial authority.
type MigrationToken struct{ state *migrationState }
type migrationState struct {
	mu     sync.Mutex
	native *nativeSession
	grant  MigrationGrant
	phase  string
}

func (t MigrationToken) Binding() (MigrationBinding, error) {
	if t.state == nil {
		return MigrationBinding{}, errors.New("AUTHORITY_ZERO_MIGRATION_TOKEN")
	}
	t.state.mu.Lock()
	defer t.state.mu.Unlock()
	return t.state.grant.Binding, nil
}
func (t MigrationToken) Options() ([]byte, error) {
	if t.state == nil {
		return nil, errors.New("AUTHORITY_ZERO_MIGRATION_TOKEN")
	}
	t.state.mu.Lock()
	defer t.state.mu.Unlock()
	return append([]byte(nil), t.state.grant.Options...), nil
}

// RequirePin proves this exact raw member is already covered by the issuer's
// grant and retained by native deny-write handles. It cannot append authority.
func (t MigrationToken) RequirePin(pin RawPin) error {
	if t.state == nil {
		return errors.New("AUTHORITY_ZERO_MIGRATION_TOKEN")
	}
	s := t.state
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.phase == "CLOSED" || s.native == nil {
		return errors.New("AUTHORITY_MIGRATION_CLOSED")
	}
	for _, approved := range s.grant.Pins {
		if bytes.Equal(encoded(pin), encoded(approved)) {
			return nil
		}
	}
	return errors.New("AUTHORITY_MIGRATION_REQUIRED_RAW_PIN_ABSENT")
}
func (t MigrationToken) Check(binding MigrationBinding) error {
	if t.state == nil {
		return errors.New("AUTHORITY_ZERO_MIGRATION_TOKEN")
	}
	s := t.state
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.phase == "CLOSED" || s.native == nil || !bytes.Equal(encoded(binding), encoded(s.grant.Binding)) || !validInterval(s.grant.IssuedUTC, s.grant.ExpiresUTC, time.Now(), 5*time.Minute) {
		return errors.New("AUTHORITY_MIGRATION_TOKEN_BINDING")
	}
	return s.native.check()
}
func (t MigrationToken) Begin(binding MigrationBinding) error {
	if t.state == nil {
		return errors.New("AUTHORITY_ZERO_MIGRATION_TOKEN")
	}
	s := t.state
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.phase != "READY" || !bytes.Equal(encoded(binding), encoded(s.grant.Binding)) {
		return errors.New("AUTHORITY_MIGRATION_ONE_USE")
	}
	if e := s.native.check(); e != nil {
		return e
	}
	s.phase = "INFLIGHT"
	return nil
}
func (t MigrationToken) Finish(committed bool) {
	if t.state == nil {
		return
	}
	s := t.state
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.phase == "INFLIGHT" {
		if committed {
			s.phase = "COMMITTED"
		} else {
			s.phase = "READY"
		}
	}
}
func (t MigrationToken) Close() error {
	if t.state == nil {
		return nil
	}
	s := t.state
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.phase == "INFLIGHT" {
		return errors.New("AUTHORITY_MIGRATION_INFLIGHT")
	}
	if s.phase == "CLOSED" {
		return nil
	}
	s.phase = "CLOSED"
	return s.native.close()
}
