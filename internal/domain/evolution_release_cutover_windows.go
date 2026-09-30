//go:build windows

package domain

import (
	"context"
	"crypto/rand"
	"database/sql"
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"researchos.local/research-os/adapters/protectedstore"
	rt "researchos.local/research-os/adapters/runtime"
	"researchos.local/research-os/ops/supervisor"
	"strings"
)

func (s *Service) writeReleaseCutover(ctx context.Context, root string, state supervisor.ReleaseState, a supervisor.ReleaseAdmission) (*supervisor.ReleaseCutover, error) {
	if state.Phase != "DRAIN_UNKNOWN" || state.Operation != a.Operation || state.Epoch != a.ExpectedEpoch+1 || state.Admission != releasePlainDigest(a) {
		return nil, errors.New("cutover journal binding invalid")
	}
	o, e := readReleaseOperation(s.DB, a.Project, a.Operation)
	if e != nil || o.Status != "DISPATCHED" {
		return nil, errors.New("cutover authority must contain DISPATCHED intent")
	}
	var seq int
	var alias, database string
	if e = s.DB.QueryRow("PRAGMA database_list").Scan(&seq, &alias, &database); e != nil {
		return nil, e
	}
	if filepath.Clean(database) != filepath.Join(root, "researchos.sqlite") {
		return nil, errors.New("cutover database is not the active authority")
	}
	tx, e := s.DB.BeginTx(ctx, nil)
	if e != nil {
		return nil, e
	}
	h, e := evolutionHost(tx, a.Project)
	_ = tx.Rollback()
	if e != nil {
		return nil, e
	}
	if filepath.Clean(releaseFixtureData(h)) != filepath.Clean(root) {
		return nil, errors.New("cutover host root changed")
	}
	policy, e := s.releaseBackupPolicy(ctx, a.Project, a.CandidateID, a.Operation, "sha256:"+a.HoldoutProofSHA256)
	if e != nil {
		return nil, e
	}
	policy.purpose["kind"] = "R2_FIXTURE_QUIESCED_CUTOVER"
	policy.purpose["root"] = root
	policy.purpose["database"] = database
	policy.purpose["epoch"] = state.Epoch
	policy.purpose["admission_hash"] = state.Admission
	b := &supervisor.ReleaseCutover{Operation: a.Operation, Epoch: state.Epoch, Root: root, Database: database, Directory: filepath.Join(releaseStateRoot(h), "cutovers", a.Operation), KeyPath: filepath.Join(releaseStateRoot(h), "keys", a.Operation+"-cutover.key"), Purpose: Bytes(policy.purpose)}
	if _, e = os.Stat(b.KeyPath); !os.IsNotExist(e) {
		return nil, errors.New("cutover attempt exists; reconcile without resnapshot")
	}
	key := make([]byte, 32)
	if _, e = rand.Read(key); e != nil {
		return nil, e
	}
	if e = os.MkdirAll(filepath.Dir(b.KeyPath), 0700); e != nil {
		return nil, e
	}
	if e = backupWrite(b.KeyPath, key); e != nil {
		return nil, e
	}
	policy.validate = chainCutoverValidation(policy.validate, a, state)
	manifest, e := s.createBackupPolicy(ctx, b.Directory, key, policy)
	if e != nil {
		return nil, e
	}
	b.ManifestSHA256 = strings.TrimPrefix(Digest(Bytes(manifest)), "sha256:")
	b.Migrations = manifest.Migrations
	return b, nil
}

func chainCutoverValidation(prior func(*sql.DB) error, a supervisor.ReleaseAdmission, state supervisor.ReleaseState) func(*sql.DB) error {
	return func(db *sql.DB) error {
		if e := prior(db); e != nil {
			return e
		}
		o, e := readReleaseOperation(db, a.Project, a.Operation)
		if e != nil || o.Status != "DISPATCHED" || o.Admission != state.Admission || o.Epoch+1 != state.Epoch {
			return errors.New("cutover DISPATCHED fence changed")
		}
		return nil
	}
}

// RestoreEvolutionCutover only receives an already held original-root OS lease.
// It publishes a new inactive root, preserving the failed database untouched.
func RestoreEvolutionCutover(ctx context.Context, state supervisor.ReleaseState, lease *rt.DataRootLease, contractsDir, privateRoot string) (string, error) {
	result, err := RestoreEvolutionCutoverContext(ctx, state, lease, contractsDir, privateRoot)
	return result.Destination, err
}

// RestoreEvolutionCutoverContext restores and fences a copy; it does not grant
// permission to start that copy or reconcile historical release operations.
func RestoreEvolutionCutoverContext(ctx context.Context, state supervisor.ReleaseState, lease *rt.DataRootLease, contractsDir, privateRoot string) (supervisor.ReleaseRestoreResult, error) {
	var result supervisor.ReleaseRestoreResult
	b := state.Cutover
	a := state.AdmissionBundle
	if b == nil || a == nil || lease == nil || !lease.Held() || lease.Root() != state.Data || b.Root != state.Data || b.Operation != state.Operation || b.Epoch != state.Epoch || b.Database != filepath.Join(b.Root, "researchos.sqlite") {
		return result, errors.New("offline cutover lease or binding unavailable")
	}
	hostRoot := filepath.Dir(b.Root)
	releaseRoot := filepath.Join(hostRoot, "release-state")
	if b.Directory != filepath.Join(releaseRoot, "cutovers", b.Operation) || b.KeyPath != filepath.Join(releaseRoot, "keys", b.Operation+"-cutover.key") {
		return result, errors.New("cutover storage locator changed")
	}
	c, e := LoadContracts(contractsDir)
	if e != nil {
		return result, e
	}
	p, e := protectedstore.OpenCanary(privateRoot)
	if e != nil {
		return result, e
	}
	defer p.Close()
	var purpose Object
	if e = json.Unmarshal(b.Purpose, &purpose); e != nil {
		return result, e
	}
	if Str(purpose, "kind") != "R2_FIXTURE_QUIESCED_CUTOVER" || Str(purpose, "root") != b.Root || Str(purpose, "database") != b.Database || Str(purpose, "operation") != b.Operation || Str(purpose, "admission_hash") != state.Admission {
		return result, errors.New("cutover purpose binding changed")
	}
	count, e := Num(purpose, "protected_reference_versions")
	if e != nil {
		return result, e
	}
	g := &releaseBackupGuard{ctx: ctx, s: &Service{Contracts: c, Protected: p}, project: a.Project, candidate: a.CandidateID, proof: "sha256:" + a.HoldoutProofSHA256, references: Str(purpose, "protected_reference_digest"), count: int(count)}
	policy := &backupPolicy{format: releaseFixtureBackupFormat, databaseName: "researchos.sqlite", purpose: purpose, validate: chainCutoverValidation(g.refresh, *a, state), allowProtected: g.artifact}
	return restoreEvolutionCutoverContext(ctx, state, lease, c, policy)
}
