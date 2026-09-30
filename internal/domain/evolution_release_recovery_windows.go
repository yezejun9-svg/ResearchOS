//go:build windows

package domain

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"reflect"
	"sort"

	rt "researchos.local/research-os/adapters/runtime"
	"researchos.local/research-os/ops/supervisor"
)

// The policy is supplied by the existing production cutover guard. Tests may
// supply an explicitly public synthetic storage policy; no native/private
// evaluator is needed to test this recovery-only copy and fencing mechanism.
func restoreEvolutionCutoverContext(ctx context.Context, state supervisor.ReleaseState, lease *rt.DataRootLease, contracts *Contracts, policy *backupPolicy) (supervisor.ReleaseRestoreResult, error) {
	var result supervisor.ReleaseRestoreResult
	a, b := state.AdmissionBundle, state.Cutover
	if a == nil || b == nil || lease == nil || !lease.Held() || lease.Root() != b.Root || state.Data != b.Root || policy == nil || contracts == nil || state.Admission != releasePlainDigest(*a) || a.Operation != state.Operation || a.ExpectedEpoch+1 != state.Epoch {
		return result, errors.New("recovery source lease or admission changed")
	}
	directory, destination, err := supervisor.RestoreContextPaths(state)
	if err != nil {
		return result, err
	}
	if state.RestoreContext != nil {
		if _, err = supervisor.ValidateReleaseRestoreResult(state, *state.RestoreContext); err != nil {
			return result, err
		}
		return *state.RestoreContext, nil
	}
	key, err := os.ReadFile(b.KeyPath)
	if err != nil {
		return result, err
	}
	manifestFile, err := supervisor.ObserveRestorePath(filepath.Join(b.Directory, "manifest.json"), false)
	if err != nil {
		return result, err
	}
	manifestRaw, err := supervisor.ReadRestoreFile(manifestFile)
	if err != nil {
		return result, err
	}
	manifestRawHash := supervisor.ReleaseBytesDigest(manifestRaw)
	manifestUnchanged := func() error {
		hash, err := supervisor.RestoreFileDigest(manifestFile)
		if err != nil || hash != manifestRawHash {
			return errors.New("recovery source manifest bytes or identity changed")
		}
		return nil
	}
	manifest, _, err := readBackupPolicy(b.Directory, key, policy)
	if err != nil {
		return result, err
	}
	var captured BackupManifest
	if json.Unmarshal(manifestRaw, &captured) != nil || Hash(captured) != Hash(manifest) {
		return result, errors.New("recovery captured manifest differs from authenticated manifest")
	}
	if err = manifestUnchanged(); err != nil {
		return result, err
	}
	if releaseArtifactDigest(Digest(Bytes(manifest))) != b.ManifestSHA256 || Hash(manifest.Migrations) != Hash(b.Migrations) || policy.databaseName != "researchos.sqlite" || releasePlainDigest(policy.purpose) != releasePlainDigest(json.RawMessage(b.Purpose)) {
		return result, errors.New("recovery manifest or policy binding changed")
	}
	sourceRoot, err := supervisor.ObserveRestorePath(b.Root, true)
	if err != nil {
		return result, err
	}
	sourceDatabase, err := supervisor.ObserveRestorePath(b.Database, false)
	if err != nil {
		return result, err
	}
	sourceHash, err := supervisor.RestoreFileDigest(sourceDatabase)
	if err != nil {
		return result, err
	}
	if err = supervisor.EnsureRestoreDirectory(directory); err != nil {
		return result, err
	}
	if _, err = supervisor.ObserveRestorePath(directory, true); err != nil {
		return result, err
	}
	// An existing reservation is an uncertain operation, including a crash after
	// restore/context publication but before the host journal acknowledges it.
	// Only a journal-bound context above is reusable; never resnapshot/rerestore.
	if _, err = os.Lstat(destination); !os.IsNotExist(err) {
		return result, errors.New("BLOCKED_RESTORE_OUTCOME_UNKNOWN: destination exists")
	}
	attempt := Object{"format": "R2_RESTORE_ATTEMPT_V1", "operation": state.Operation, "epoch": state.Epoch, "admission_hash": state.Admission, "manifest_hash": b.ManifestSHA256, "source_root": sourceRoot, "source_database": sourceDatabase, "source_database_sha256": sourceHash, "destination": destination}
	if err = backupWrite(filepath.Join(directory, "attempt.json"), Bytes(attempt)); err != nil {
		return result, fmt.Errorf("BLOCKED_RESTORE_OUTCOME_UNKNOWN: reservation unavailable: %w", err)
	}
	guard := releaseRecoveryGuard{state: state, destination: destination}
	bounded := *policy
	priorBefore, priorAfter := policy.beforeRecovery, policy.afterRecovery
	bounded.beforeRecovery = func(db *sql.DB) error {
		if priorBefore != nil {
			if err := priorBefore(db); err != nil {
				return err
			}
		}
		if err := manifestUnchanged(); err != nil {
			return err
		}
		return guard.beforeRecovery(db)
	}
	bounded.afterRecovery = func(db *sql.DB) error {
		if priorAfter != nil {
			if err := priorAfter(db); err != nil {
				return err
			}
		}
		if err := manifestUnchanged(); err != nil {
			return err
		}
		return guard.afterRecovery(db)
	}
	report, err := restoreBackupPolicy(ctx, b.Directory, destination, RestoreOptions{Key: key, Contracts: contracts, SupportedMigrations: b.Migrations}, &bounded)
	if err != nil {
		return result, err
	}
	if err = manifestUnchanged(); err != nil {
		return result, err
	}
	if report.Status != "RESTORED_RECONCILIATION_REQUIRED" || guard.after == nil || Hash(report.Before) != Hash(manifest.Inventory) {
		return result, errors.New("recovery copy is incomplete")
	}
	root, err := supervisor.ObserveRestorePath(destination, true)
	if err != nil {
		return result, err
	}
	database, err := supervisor.ObserveRestorePath(filepath.Join(destination, "researchos.sqlite"), false)
	if err != nil {
		return result, err
	}
	reportFile, err := supervisor.ObserveRestorePath(filepath.Join(destination, "restore-report.json"), false)
	if err != nil {
		return result, err
	}
	databaseHash, err := supervisor.RestoreFileDigest(database)
	if err != nil {
		return result, err
	}
	reportHash, err := supervisor.RestoreFileDigest(reportFile)
	if err != nil {
		return result, err
	}
	// Preserve the report's actual persisted bytes, rather than hashing a newly
	// constructed report and claiming it was what recovery wrote.
	reportRaw, err := os.ReadFile(reportFile.Path)
	if err != nil || supervisor.ReleaseBytesDigest(reportRaw) != reportHash {
		return result, errors.New("recovery report changed during binding")
	}
	var stored RestoreReport
	if json.Unmarshal(reportRaw, &stored) != nil || Hash(stored) != Hash(report) {
		return result, errors.New("recovery report differs from completed restore")
	}
	c := supervisor.ReleaseRestoreContext{
		Format: supervisor.ReleaseRestoreContextFormat, Status: supervisor.RecoveryAuthorizationBlocked,
		Operation: state.Operation, Project: a.Project, Candidate: a.CandidateID, AdmissionSHA256: state.Admission,
		ManifestSHA256: b.ManifestSHA256, PurposeSHA256: supervisor.ReleaseBytesDigest(b.Purpose), SnapshotEpoch: a.ExpectedEpoch, HostEpoch: state.Epoch,
		Manifest: manifestFile, ManifestRawSHA256: manifestRawHash,
		SourceRoot: sourceRoot, SourceDatabase: sourceDatabase, DestinationRoot: root, DestinationDatabase: database,
		SourceDatabaseSHA256: sourceHash, DestinationDatabaseSHA256: databaseHash, Report: reportFile, ReportSHA256: reportHash,
		BeforeInventory: Bytes(stored.Before), AfterInventory: Bytes(stored.After), BeforeRowsSHA256: releasePlainDigest(guard.before), AfterRowsSHA256: releasePlainDigest(guard.after), AllowedDelta: releaseRecoveryDeltaSummary(guard.before, guard.after),
	}
	contextRaw := Bytes(c)
	result = supervisor.ReleaseRestoreResult{Operation: state.Operation, Epoch: state.Epoch, SourceRoot: b.Root, Destination: destination, ContextPath: filepath.Join(directory, "context.json"), ContextSHA256: supervisor.ReleaseBytesDigest(contextRaw), ManifestSHA256: b.ManifestSHA256}
	if err = backupWrite(result.ContextPath, contextRaw); err != nil {
		return result, err
	}
	if _, err = supervisor.ValidateReleaseRestoreResult(state, result); err != nil {
		return result, err
	}
	return result, nil
}

type releaseRecoveryGuard struct {
	state         supervisor.ReleaseState
	destination   string
	before, after upgradeData
}

func (g *releaseRecoveryGuard) beforeRecovery(db *sql.DB) error {
	var activeRuns, unfinishedEffects int
	if err := db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='Run' AND json_extract(body,'$.status') IN ('QUEUED','STARTING','RUNNING','CANCEL_REQUESTED','RECONCILING','LOST')").Scan(&activeRuns); err != nil {
		return err
	}
	if err := db.QueryRow("SELECT count(*) FROM resource_effects x WHERE sequence=(SELECT max(y.sequence) FROM resource_effects y WHERE y.project=x.project AND y.run=x.run AND y.effect_key=x.effect_key) AND json_extract(body,'$.state') IN ('PREPARED','STARTED','UNKNOWN')").Scan(&unfinishedEffects); err != nil {
		return err
	}
	if activeRuns != 0 || unfinishedEffects != 0 {
		return errors.New("BLOCKED_RECOVERY_NON_IDLE: active runs or unfinished effects require separately qualified recovery")
	}
	a := g.state.AdmissionBundle
	o, err := readReleaseOperation(db, a.Project, a.Operation)
	if err != nil || o.ID != a.Operation || o.Project != a.Project || o.Candidate != a.CandidateID || o.Action != "START_CANARY" || o.Status != "DISPATCHED" || o.Epoch != a.ExpectedEpoch || o.Admission != g.state.Admission || o.EffectKey != "r2-fixture-"+a.Operation || o.Receipt.Valid || o.Revision != 0 {
		return errors.New("recovery cutover operation lineage changed")
	}
	tx, err := db.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()
	x, err := load(tx, a.Project, "SystemCandidate", a.CandidateID)
	if err != nil || x["status"] != "EVALUATING" || x["regression_acceptance_id"] != a.AcceptanceID {
		return errors.New("recovery candidate lineage changed")
	}
	candidateRef, candidateOK := x["candidate_artifact_ref"].(map[string]any)
	stableRef, stableOK := x["stable_artifact_ref"].(map[string]any)
	var planHash string
	if !candidateOK || !stableOK || releaseArtifactDigest(candidateRef["content_hash"]) != a.CandidateSHA256 || releaseArtifactDigest(stableRef["content_hash"]) != a.StableSHA256 {
		return errors.New("recovery candidate artifacts changed")
	}
	if err = tx.QueryRow("SELECT plan_hash FROM evolution_candidates WHERE project=? AND candidate=?", a.Project, a.CandidateID).Scan(&planHash); err != nil || planHash != Hash(evolutionPlan(x)) {
		return errors.New("recovery candidate plan changed")
	}
	h, err := evolutionHost(tx, a.Project)
	if err != nil || releaseFixtureData(h) != g.state.Cutover.Root || Hash(h["stable_ref"]) != Hash(stableRef) {
		return errors.New("recovery immutable host root changed")
	}
	var active, stable, phase string
	var candidate sql.NullString
	var epoch uint64
	if err = tx.QueryRow("SELECT active_hash,stable_hash,candidate,epoch,state FROM evolution_slots WHERE project=?", a.Project).Scan(&active, &stable, &candidate, &epoch, &phase); err != nil || phase != "STABLE" || candidate.Valid || epoch != a.ExpectedEpoch || active != "sha256:"+a.StableSHA256 || stable != active {
		return errors.New("recovery source slot changed")
	}
	if err = tx.Rollback(); err != nil {
		return err
	}
	g.before, err = upgradeRows(db)
	return err
}

func (g *releaseRecoveryGuard) afterRecovery(db *sql.DB) error {
	beforeFence, err := upgradeRows(db)
	if err != nil {
		return err
	}
	if err = releaseRecoveryAllowedDelta(g.before, beforeFence, g.destination); err != nil {
		return err
	}
	a := g.state.AdmissionBundle
	tx, err := db.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()
	res, err := tx.Exec("UPDATE evolution_slots SET state='RECOVERING' WHERE project=? AND state='STABLE' AND epoch=? AND candidate IS NULL AND active_hash=? AND stable_hash=?", a.Project, a.ExpectedEpoch, "sha256:"+a.StableSHA256, "sha256:"+a.StableSHA256)
	if err != nil {
		return err
	}
	if n, err := res.RowsAffected(); err != nil || n != 1 {
		return errors.New("recovery slot fence compare-and-swap failed")
	}
	if err = tx.Commit(); err != nil {
		return err
	}
	g.after, err = upgradeRows(db)
	if err != nil {
		return err
	}
	// No state writer is running. Check even the fence's exact table delta;
	// DISPATCHED, candidate EVALUATING, epoch/hash and authorization stay intact.
	expected := make([]Object, len(beforeFence["evolution_slots"]))
	for i, row := range beforeFence["evolution_slots"] {
		expected[i] = copyObject(row)
		if row["project"] == a.Project {
			expected[i]["state"] = "RECOVERING"
		}
	}
	if extra, e := upgradeExtra(expected, g.after["evolution_slots"]); e != nil || len(extra) != 0 {
		return errors.New("recovery slot fence changed unrelated fields")
	}
	for table, rows := range beforeFence {
		if table != "evolution_slots" && Hash(rows) != Hash(g.after[table]) {
			return fmt.Errorf("recovery fence changed table: %s", table)
		}
	}
	return nil
}

func releaseRecoveryDeltaSummary(before, after upgradeData) []supervisor.RestoreTableDelta {
	names := []string{}
	for table := range after {
		names = append(names, table)
	}
	sort.Strings(names)
	result := []supervisor.RestoreTableDelta{}
	for _, table := range names {
		if Hash(before[table]) != Hash(after[table]) {
			result = append(result, supervisor.RestoreTableDelta{Table: table, BeforeSHA256: releasePlainDigest(before[table]), AfterSHA256: releasePlainDigest(after[table]), BeforeRows: len(before[table]), AfterRows: len(after[table])})
		}
	}
	return result
}

// This first slice accepts only an idle cutover. It permits no Run, audit,
// effect, migration, authorization-history or other business-table changes.
func releaseRecoveryAllowedDelta(before, after upgradeData, destination string) error {
	if before == nil {
		return errors.New("recovery source inventory missing")
	}
	for table, old := range before {
		current, exists := after[table]
		if !exists {
			return fmt.Errorf("recovery table lost: %s", table)
		}
		switch table {
		case "auth_credentials":
			expected := []Object{}
			for _, row := range old {
				expected = append(expected, Merge(copyObject(row), Object{"revoked": int64(1)}))
			}
			if extra, err := upgradeExtra(expected, current); err != nil || len(extra) != 0 {
				return errors.New("recovery credentials not revoked exactly")
			}
		case "retrieval_roots":
			strip := func(rows []Object) []Object {
				result := []Object{}
				for _, row := range rows {
					result = append(result, upgradeWithout(row, "path", "root_identity"))
				}
				return result
			}
			if extra, err := upgradeExtra(strip(old), strip(current)); err != nil || len(extra) != 0 {
				return errors.New("recovery retrieval root metadata changed")
			}
			for _, row := range current {
				if !upgradeInside(destination, Str(row, "path")) || Str(row, "root_identity") == "" {
					return errors.New("recovery source root not isolated")
				}
			}
		default:
			if !reflect.DeepEqual(old, current) {
				return fmt.Errorf("recovery unexpected table change: %s", table)
			}
		}
	}
	for table, rows := range after {
		if _, existed := before[table]; !existed && (table != "backup_restore_barriers" || len(rows) != 0) {
			return fmt.Errorf("recovery unexpected new table: %s", table)
		}
	}
	return nil
}
