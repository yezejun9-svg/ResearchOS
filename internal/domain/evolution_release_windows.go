//go:build windows

package domain

import (
	"context"
	"database/sql"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"researchos.local/research-os/ops/supervisor"
	"strings"
	"time"
)

const releaseFixtureMechanism = "R2_NATIVE_FIXTURE"

func releasePlainDigest(v any) string    { return supervisor.ReleaseDigest(v) }
func releaseArtifactDigest(v any) string { return strings.TrimPrefix(fmt.Sprint(v), "sha256:") }
func validReleaseOperationID(id string) bool {
	if len(id) != 64 || strings.ToLower(id) != id {
		return false
	}
	_, e := hex.DecodeString(id)
	return e == nil
}

func releaseStateRoot(h Object) string { return filepath.Join(Str(h, "root"), "release-state") }
func releaseAdmissionPath(h Object, operation string) string {
	return filepath.Join(releaseStateRoot(h), "admissions", operation+".json")
}
func releaseBackupPath(h Object, operation string) string {
	return filepath.Join(releaseStateRoot(h), "backups", operation)
}
func releaseFixtureData(h Object) string { return filepath.Join(Str(h, "root"), "data") }
func releaseFixtureMarker(h Object) string {
	return filepath.Join(releaseFixtureData(h), "fixture-instance.json")
}
func releaseReceiptPath(h Object, operation string) string {
	return filepath.Join(releaseStateRoot(h), "receipts", operation+".json")
}

func releaseFixtureDriver() supervisor.NativeFixtureDriver {
	return supervisor.NativeFixtureDriver{Args: func(token, data string) []string { return []string{"--release-fixture", token, data} }}
}

// The native fixture can only assert an idle test database, not production
// drain/checkpoint or service ACL isolation. The independent production barrier
// must replace this adapter before any LIVE release is permitted.
type releaseFixtureBarrier struct {
	s      *Service
	h      Object
	driver supervisor.ProcessDriver
}

func (b releaseFixtureBarrier) Ready(_ context.Context, p supervisor.ProcessIdentity, _ string) error {
	alive, e := b.driver.Alive(p)
	if e != nil {
		return e
	}
	if !alive {
		return errors.New("fixture process not alive")
	}
	return nil
}
func (b releaseFixtureBarrier) Drain(ctx context.Context, p supervisor.ProcessIdentity, operation string) (string, error) {
	if e := b.Ready(ctx, p, operation); e != nil {
		return "", e
	}
	raw, e := os.ReadFile(releaseAdmissionPath(b.h, operation))
	if e != nil {
		return "", e
	}
	var sealed supervisor.ReleaseAdmission
	if e = json.Unmarshal(raw, &sealed); e != nil {
		return "", e
	}
	if sealed.Operation != operation {
		return "", errors.New("drain admission changed")
	}
	if e = b.s.releaseAdmissionCurrent(ctx, sealed); e != nil {
		return "", e
	}
	var active, unknown int
	if e := b.s.DB.QueryRowContext(ctx, `SELECT count(*) FROM domain_objects WHERE kind='Run' AND json_extract(body,'$.status') IN ('QUEUED','STARTING','RUNNING','CANCEL_REQUESTED','RECONCILING','LOST')`).Scan(&active); e != nil {
		return "", e
	}
	if e := b.s.DB.QueryRowContext(ctx, `SELECT count(*) FROM resource_effects x WHERE sequence=(SELECT max(y.sequence) FROM resource_effects y WHERE y.project=x.project AND y.run=x.run AND y.effect_key=x.effect_key) AND json_extract(body,'$.state') IN ('PREPARED','STARTED','UNKNOWN')`).Scan(&unknown); e != nil {
		return "", e
	}
	if active != 0 || unknown != 0 {
		return "", errors.New("fixture has active Run or unresolved external effect")
	}
	return releasePlainDigest(Object{"fixture_idle_observation": true, "operation": operation, "pid": p.PID, "created_ns": p.CreatedNS}), nil
}
func (b releaseFixtureBarrier) Compatible(ctx context.Context, state supervisor.ReleaseState) error {
	if state.AdmissionBundle == nil {
		return errors.New("release admission missing")
	}
	a := state.AdmissionBundle
	if e := b.s.verifyReleaseAuthorityBackup(ctx, b.h, a.Project, a.CandidateID, state.Operation, "sha256:"+a.HoldoutProofSHA256, state.Backup); e != nil {
		return e
	}
	if state.AdmissionBundle == nil || !state.AdmissionBundle.SameSchema || !state.AdmissionBundle.NoUnknownEffects {
		return errors.New("same-schema idle rollback proof absent")
	}
	return nil
}

func releaseFixtureVerifier(s *Service, h Object) supervisor.AdmissionVerifier {
	return func(a supervisor.ReleaseAdmission) error {
		if !validReleaseOperationID(a.Operation) {
			return errors.New("invalid operation identifier")
		}
		b, e := os.ReadFile(releaseAdmissionPath(h, a.Operation))
		if e != nil {
			return e
		}
		var frozen supervisor.ReleaseAdmission
		if e = json.Unmarshal(b, &frozen); e != nil {
			return e
		}
		if releasePlainDigest(frozen) != releasePlainDigest(a) || frozen.Project == "" || frozen.CandidateID == "" {
			return errors.New("supervisor sealed admission differs")
		}
		if e = s.releaseAdmissionCurrent(context.Background(), a); e != nil {
			return e
		}
		if e = s.verifyReleaseAuthorityBackup(context.Background(), h, a.Project, a.CandidateID, a.Operation, "sha256:"+a.HoldoutProofSHA256, a.BackupReceiptSHA256); e != nil {
			return e
		}
		if e = s.releaseAdmissionCurrent(context.Background(), a); e != nil {
			return e
		}
		return nil
	}
}

func evolutionCurrentPrincipal(tx *sql.Tx, id string) (Principal, error) {
	p := Principal{ID: id}
	var roles string
	if e := tx.QueryRow("SELECT roles FROM auth_principals WHERE id=? AND revoked=0", id).Scan(&roles); e != nil {
		return p, Fail(403, "FORBIDDEN", "release evidence principal no longer active")
	}
	if e := json.Unmarshal([]byte(roles), &p.Roles); e != nil {
		return p, e
	}
	rows, e := tx.Query("SELECT project,task,run,restricted FROM auth_grants WHERE principal=?", id)
	if e != nil {
		return p, e
	}
	for rows.Next() {
		var g Grant
		if e = rows.Scan(&g.ProjectID, &g.TaskID, &g.RunID, &g.Restricted); e != nil {
			rows.Close()
			return p, e
		}
		p.Grants = append(p.Grants, g)
	}
	e = rows.Err()
	rows.Close()
	if e != nil {
		return p, e
	}
	if e = constrainRemotePrincipal(tx, &p); e != nil {
		return p, e
	}
	return p, nil
}

func (s *Service) releaseActorsCurrent(tx *sql.Tx, project string, x, h, accepted Object) error {
	verifierID := Str(accepted, "verifier_principal_id")
	verifier, e := evolutionCurrentPrincipal(tx, verifierID)
	if e != nil {
		return e
	}
	if !verifier.HasRole("VERIFIER") || !verifier.Allowed(project, "", "", false) {
		return Fail(403, "FORBIDDEN", "regression verifier current grant required")
	}
	releaseID := Str(h, "release_principal")
	release, e := evolutionCurrentPrincipal(tx, releaseID)
	if e != nil {
		return e
	}
	if !release.HasRole("RELEASE_SERVICE") || !release.Allowed(project, "", "", false) || release.DeviceID != "" {
		return Fail(403, "FORBIDDEN", "registered local release actor current grant required")
	}
	var authorID string
	if e = tx.QueryRow("SELECT creator FROM evolution_candidates WHERE project=? AND candidate=?", project, x["id"]).Scan(&authorID); e != nil {
		return e
	}
	authorRoot, e := authorityRoot(tx, authorID)
	if e != nil {
		return e
	}
	verifierRoot, e := authorityRoot(tx, verifierID)
	if e != nil {
		return e
	}
	releaseRoot, e := authorityRoot(tx, releaseID)
	if e != nil {
		return e
	}
	if authorRoot == verifierRoot || authorRoot == releaseRoot || verifierRoot == releaseRoot {
		return Fail(403, "FORBIDDEN", "release actor, author and regression verifier must be independent")
	}
	return nil
}

// This callback is used by both PrepareFixture and SwitchFixture. It reads
// current domain state, not merely the historical sealed admission or ledger.
func (s *Service) releaseAdmissionCurrent(ctx context.Context, a supervisor.ReleaseAdmission) error {
	tx, e := s.DB.BeginTx(ctx, nil)
	if e != nil {
		return e
	}
	defer tx.Rollback()
	x, e := load(tx, a.Project, "SystemCandidate", a.CandidateID)
	if e != nil {
		return e
	}
	if x["status"] != "EVALUATING" || x["regression_acceptance_id"] != a.AcceptanceID {
		return errors.New("candidate or regression acceptance changed before release effect")
	}
	h, e := s.evolutionCurrent(tx, a.Project, x)
	if e != nil {
		return e
	}
	if h["release_mechanism"] != releaseFixtureMechanism || h["os_service_qualified"] != false {
		return errors.New("fixture host changed")
	}
	o, e := readReleaseOperationTx(tx, a.Project, a.Operation)
	if e != nil {
		return e
	}
	if o.Candidate != a.CandidateID || o.Action != "START_CANARY" || o.Epoch != a.ExpectedEpoch || o.Admission != releasePlainDigest(a) || (o.Status != "PREPARED" && o.Status != "DISPATCHED") {
		return errors.New("release operation changed before effect")
	}
	record, e := s.evolutionAccepted(tx, a.Project, x, "REGRESSION", a.AcceptanceID)
	if e != nil {
		return e
	}
	request := Object{"regression_acceptance_id": a.AcceptanceID, "observation_deadline": a.ExpiresUTC.Format(time.RFC3339Nano)}
	expected, e := s.releaseAdmissionInputs(tx, a.Project, x, h, request, record, a.ExpectedEpoch, a.BackupReceiptSHA256)
	if e != nil {
		return e
	}
	if releasePlainDigest(expected) != releasePlainDigest(a) {
		return errors.New("current release admission differs")
	}
	return nil
}

func (s *Service) releaseFixtureEngine(h Object, j *supervisor.ReleaseJournal) (*supervisor.ReleaseEngine, error) {
	d := releaseFixtureDriver()
	return supervisor.NewReleaseEngine(j, d, releaseFixtureBarrier{s: s, h: h, driver: d}, releaseFixtureVerifier(s, h))
}

// BootstrapEvolutionReleaseFixture is host-only provisioning. It uses only a
// new OS-temp fixture root registered with os_service_qualified=false.
func (s *Service) BootstrapEvolutionReleaseFixture(ctx context.Context, project string) error {
	tx, e := s.DB.BeginTx(ctx, nil)
	if e != nil {
		return e
	}
	h, e := evolutionHost(tx, project)
	_ = tx.Rollback()
	if e != nil {
		return e
	}
	if h["release_mechanism"] != releaseFixtureMechanism || h["os_service_qualified"] != false {
		return errors.New("R2 native fixture host required")
	}
	j, e := supervisor.OpenReleaseJournal(releaseStateRoot(h))
	if e != nil {
		return e
	}
	defer j.Close()
	engine, e := s.releaseFixtureEngine(h, j)
	if e != nil {
		return e
	}
	if e = os.Mkdir(releaseFixtureData(h), 0700); e != nil {
		return e
	}
	marker := Object{"format": "R2_DISPOSABLE_INSTANCE_V1", "project": project, "stable_sha256": h["stable_ref"].(map[string]any)["content_hash"]}
	if e = os.WriteFile(releaseFixtureMarker(h), Bytes(marker), 0600); e != nil {
		return e
	}
	return engine.BootstrapFixture(ctx, filepath.Join(Str(h, "root"), "stable.exe"), releaseFixtureData(h))
}

func releaseOperationID(project, candidate, acceptance string, epoch uint64) string {
	return releasePlainDigest(Object{"project": project, "candidate": candidate, "action": "START_CANARY", "acceptance": acceptance, "epoch": epoch})
}

func (s *Service) releaseAdmissionInputs(tx *sql.Tx, project string, x, h, b, record Object, epoch uint64, backupHash string) (supervisor.ReleaseAdmission, error) {
	var a supervisor.ReleaseAdmission
	if h["release_mechanism"] != releaseFixtureMechanism || h["os_service_qualified"] != false {
		return a, errors.New("fixture release host required")
	}
	deadline, e := time.Parse(time.RFC3339Nano, Str(b, "observation_deadline"))
	if e != nil {
		return a, e
	}
	acceptanceID := Str(b, "regression_acceptance_id")
	accepted, e := load(tx, project, "AcceptanceReceipt", acceptanceID)
	if e != nil {
		return a, e
	}
	if e = s.releaseActorsCurrent(tx, project, x, h, accepted); e != nil {
		return a, e
	}
	if record["improved"] != true || record["required_passed"] != true || record["holdout_summary"] == nil || record["holdout_proof_hash"] == nil {
		return a, errors.New("private objective benefit and required regression proof required")
	}
	if record["holdout_summary"].(map[string]any)["gain"] != true {
		return a, errors.New("private holdout did not improve")
	}
	a = supervisor.ReleaseAdmission{
		Project: project, CandidateID: Str(x, "id"), AcceptanceID: acceptanceID, ExecutionSHA256: releaseArtifactDigest(record["receipt_hash"]),
		Operation: releaseOperationID(project, Str(x, "id"), acceptanceID, epoch), ExpectedEpoch: epoch,
		StableSHA256:        releaseArtifactDigest(x["stable_artifact_ref"].(map[string]any)["content_hash"]),
		CandidateSHA256:     releaseArtifactDigest(x["candidate_artifact_ref"].(map[string]any)["content_hash"]),
		BackupReceiptSHA256: backupHash, VerifierReceiptSHA256: releaseArtifactDigest(accepted["receipt_hash"]),
		HoldoutProofSHA256: releaseArtifactDigest(record["holdout_proof_hash"]), SameSchema: true, NoUnknownEffects: true, ExpiresUTC: deadline.UTC(),
	}
	return a, nil
}

// SealEvolutionReleaseFixture is an explicitly local, host-side test action.
// It seals the independently accepted exact candidate before public HTTP
// START_CANARY records its intent. Production needs a distinct OS verifier.
func (s *Service) SealEvolutionReleaseFixture(ctx context.Context, project, candidate string, request Object) (supervisor.ReleaseAdmission, error) {
	var zero supervisor.ReleaseAdmission
	tx, e := s.DB.BeginTx(ctx, nil)
	if e != nil {
		return zero, e
	}
	defer tx.Rollback()
	x, e := load(tx, project, "SystemCandidate", candidate)
	if e != nil {
		return zero, e
	}
	h, e := s.evolutionCurrent(tx, project, x)
	if e != nil {
		return zero, e
	}
	if x["status"] != "EVALUATING" || request["action"] != "START_CANARY" {
		return zero, errors.New("fixture candidate not awaiting canary intent")
	}
	record, e := s.evolutionAccepted(tx, project, x, "REGRESSION", Str(request, "regression_acceptance_id"))
	if e != nil {
		return zero, e
	}
	var epoch uint64
	if e = tx.QueryRow("SELECT epoch FROM evolution_slots WHERE project=? AND state='STABLE'", project).Scan(&epoch); e != nil {
		return zero, e
	}
	if e = tx.Rollback(); e != nil && !errors.Is(e, sql.ErrTxDone) {
		return zero, e
	}
	j, e := supervisor.OpenReleaseJournal(releaseStateRoot(h))
	if e != nil {
		return zero, e
	}
	state := j.State()
	_ = j.Close()
	if state.Epoch != epoch || state.Active != releaseArtifactDigest(x["stable_artifact_ref"].(map[string]any)["content_hash"]) || state.Phase != "STABLE" {
		return zero, errors.New("fixture supervisor slot differs from frozen stable")
	}
	operation := releaseOperationID(project, candidate, Str(request, "regression_acceptance_id"), epoch)
	backupHash, e := s.writeReleaseAuthorityBackup(ctx, h, project, candidate, operation, Str(record, "holdout_proof_hash"))
	if e != nil {
		return zero, e
	}
	// Recheck current acceptance after the encrypted authority snapshot and
	// isolated restore; the external fixture provider remains a dependency.
	tx, e = s.DB.BeginTx(ctx, nil)
	if e != nil {
		return zero, e
	}
	defer tx.Rollback()
	x, e = load(tx, project, "SystemCandidate", candidate)
	if e != nil {
		return zero, e
	}
	record, e = s.evolutionAccepted(tx, project, x, "REGRESSION", Str(request, "regression_acceptance_id"))
	if e != nil {
		return zero, e
	}
	a, e := s.releaseAdmissionInputs(tx, project, x, h, request, record, epoch, backupHash)
	if e != nil {
		return zero, e
	}
	path := releaseAdmissionPath(h, a.Operation)
	if frozen, readErr := os.ReadFile(path); readErr == nil {
		var previous supervisor.ReleaseAdmission
		if json.Unmarshal(frozen, &previous) != nil || releasePlainDigest(previous) != releasePlainDigest(a) {
			return zero, errors.New("existing fixture admission differs")
		}
		return previous, nil
	} else if !os.IsNotExist(readErr) {
		return zero, readErr
	}
	if e = os.MkdirAll(filepath.Dir(path), 0700); e != nil {
		return zero, e
	}
	encoded, e := json.Marshal(a)
	if e != nil {
		return zero, e
	}
	f, e := os.OpenFile(path, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if e != nil {
		return zero, e
	}
	if _, e = f.Write(encoded); e == nil {
		e = f.Sync()
	}
	if c := f.Close(); e == nil {
		e = c
	}
	return a, e
}

// evolutionReleaseIntent is called only from the frozen public action path,
// inside the same transaction that bumps SystemCandidate revision.
func (s *Service) evolutionReleaseIntent(tx *sql.Tx, project string, x, h, b, record Object) error {
	var epoch uint64
	if e := tx.QueryRow("SELECT epoch FROM evolution_slots WHERE project=? AND state='STABLE'", project).Scan(&epoch); e != nil {
		return e
	}
	op := releaseOperationID(project, Str(x, "id"), Str(b, "regression_acceptance_id"), epoch)
	raw, e := os.ReadFile(releaseAdmissionPath(h, op))
	if e != nil {
		return Fail(422, "GATE_FAILED", "supervisor sealed admission unavailable")
	}
	var sealed supervisor.ReleaseAdmission
	if e = json.Unmarshal(raw, &sealed); e != nil {
		return e
	}
	expected, e := s.releaseAdmissionInputs(tx, project, x, h, b, record, epoch, sealed.BackupReceiptSHA256)
	if e != nil {
		return e
	}
	if releasePlainDigest(sealed) != releasePlainDigest(expected) || !sealed.ExpiresUTC.After(time.Now().UTC()) {
		return Fail(422, "GATE_FAILED", "supervisor admission changed or expired")
	}
	var count int
	if e = tx.QueryRow("SELECT count(*) FROM evolution_release_operations WHERE project=? AND candidate=? AND action='START_CANARY'", project, x["id"]).Scan(&count); e != nil {
		return e
	}
	if count != 0 {
		return Fail(409, "STATE_CONFLICT", "release operation already registered")
	}
	_, e = tx.Exec("INSERT INTO evolution_release_operations(project,candidate,action,operation_id,expected_epoch,admission_hash,effect_key,status) VALUES(?,?,'START_CANARY',?,?,? ,?,'PREPARED')", project, x["id"], sealed.Operation, epoch, releasePlainDigest(sealed), "r2-fixture-"+sealed.Operation)
	if e != nil {
		return e
	}
	x["observation_deadline"] = b["observation_deadline"]
	return nil
}

type releaseOperation struct {
	Project, Candidate, Action, ID string
	Epoch                          uint64
	Admission, EffectKey, Status   string
	Receipt                        sql.NullString
	Revision                       int64
}

func readReleaseOperation(db *sql.DB, project, operation string) (releaseOperation, error) {
	var o releaseOperation
	e := db.QueryRow(`SELECT project,candidate,action,operation_id,expected_epoch,admission_hash,effect_key,status,receipt_digest,projection_revision FROM evolution_release_operations WHERE project=? AND operation_id=?`, project, operation).Scan(&o.Project, &o.Candidate, &o.Action, &o.ID, &o.Epoch, &o.Admission, &o.EffectKey, &o.Status, &o.Receipt, &o.Revision)
	return o, e
}

func readReleaseOperationTx(tx *sql.Tx, project, operation string) (releaseOperation, error) {
	var o releaseOperation
	e := tx.QueryRow(`SELECT project,candidate,action,operation_id,expected_epoch,admission_hash,effect_key,status,receipt_digest,projection_revision FROM evolution_release_operations WHERE project=? AND operation_id=?`, project, operation).Scan(&o.Project, &o.Candidate, &o.Action, &o.ID, &o.Epoch, &o.Admission, &o.EffectKey, &o.Status, &o.Receipt, &o.Revision)
	return o, e
}

func releaseOperationCAS(db *sql.DB, operation, from, to, receipt string) error {
	var res sql.Result
	var e error
	if receipt == "" {
		res, e = db.Exec(`UPDATE evolution_release_operations SET status=? WHERE operation_id=? AND status=?`, to, operation, from)
	} else {
		res, e = db.Exec(`UPDATE evolution_release_operations SET status=?,receipt_digest=? WHERE operation_id=? AND status=?`, to, receipt, operation, from)
	}
	if e != nil {
		return e
	}
	n, e := res.RowsAffected()
	if e != nil || n != 1 {
		return errors.New("release operation transition lost")
	}
	return nil
}

// RunEvolutionReleaseFixtureOnce is called by the separate fixture supervisor
// process after public HTTP has committed PREPARED. It never trusts the DB row
// as authorization: it reloads its own sealed bundle and current acceptance.
// After DISPATCHED, any uncertain host phase is left untouched for reconcile.
func (s *Service) RunEvolutionReleaseFixtureOnce(ctx context.Context, project, operation string) (Object, error) {
	if !validReleaseOperationID(operation) {
		return nil, errors.New("invalid release operation identifier")
	}
	o, e := readReleaseOperation(s.DB, project, operation)
	if e != nil {
		return nil, e
	}
	if o.Action != "START_CANARY" || o.Status == "FAILED" {
		return nil, errors.New("fixture release operation not dispatchable")
	}
	if o.Status == "PROJECTED" {
		return Object{"operation_id": operation, "status": "PROJECTED", "receipt_digest": o.Receipt.String, "projection_revision": o.Revision, "scope": "R2_NATIVE_FIXTURE"}, nil
	}
	tx, e := s.DB.BeginTx(ctx, nil)
	if e != nil {
		return nil, e
	}
	x, e := load(tx, project, "SystemCandidate", o.Candidate)
	if e != nil {
		_ = tx.Rollback()
		return nil, e
	}
	h, e := s.evolutionCurrent(tx, project, x)
	if e != nil {
		_ = tx.Rollback()
		return nil, e
	}
	if h["release_mechanism"] != releaseFixtureMechanism || h["os_service_qualified"] != false || x["status"] != "EVALUATING" {
		_ = tx.Rollback()
		return nil, errors.New("fixture host or candidate changed")
	}
	sealedBytes, e := os.ReadFile(releaseAdmissionPath(h, operation))
	if e != nil {
		_ = tx.Rollback()
		return nil, e
	}
	var sealed supervisor.ReleaseAdmission
	if e = json.Unmarshal(sealedBytes, &sealed); e != nil {
		_ = tx.Rollback()
		return nil, e
	}
	if sealed.Operation != operation || sealed.Project != project || sealed.CandidateID != o.Candidate || sealed.ExpectedEpoch != o.Epoch || releasePlainDigest(sealed) != o.Admission {
		_ = tx.Rollback()
		return nil, errors.New("operation differs from supervisor sealed admission")
	}
	record, e := s.evolutionAccepted(tx, project, x, "REGRESSION", sealed.AcceptanceID)
	if e != nil {
		_ = tx.Rollback()
		return nil, e
	}
	request := Object{"action": "START_CANARY", "regression_acceptance_id": sealed.AcceptanceID, "observation_deadline": sealed.ExpiresUTC.Format(time.RFC3339Nano)}
	expected, e := s.releaseAdmissionInputs(tx, project, x, h, request, record, o.Epoch, sealed.BackupReceiptSHA256)
	if e != nil || releasePlainDigest(expected) != o.Admission {
		_ = tx.Rollback()
		return nil, errors.New("current independent evidence differs from sealed admission")
	}
	_ = tx.Rollback()
	j, e := supervisor.OpenReleaseJournal(releaseStateRoot(h))
	if e != nil {
		return nil, e
	}
	defer j.Close()
	engine, e := s.releaseFixtureEngine(h, j)
	if e != nil {
		return nil, e
	}
	driver := releaseFixtureDriver()
	state := j.State()
	if o.Status == "PREPARED" {
		if state.Phase == "STABLE" {
			state, e = engine.PrepareFixture(sealed, filepath.Join(Str(h, "root"), o.Candidate, "candidate.exe"))
			if e != nil {
				return nil, e
			}
		} else if state.Phase != "PREPARED" || state.Operation != operation || state.Admission != o.Admission {
			return nil, errors.New("supervisor preparation uncertain")
		}
		if e = releaseOperationCAS(s.DB, operation, "PREPARED", "DISPATCHED", ""); e != nil {
			return nil, e
		}
		o.Status = "DISPATCHED"
	}
	if o.Status == "DISPATCHED" {
		state = j.State()
		if state.Phase == "PREPARED" && state.Operation == operation {
			state, e = engine.SwitchFixture(ctx, operation)
			if e != nil {
				return nil, e
			}
		} else if state.Phase != "CANARY" || state.Operation != operation {
			return nil, errors.New("dispatch effect uncertain; inspect supervisor journal")
		}
		_, receipt, e := supervisor.WriteFixtureReceipt(releaseStateRoot(h), j, driver)
		if e != nil {
			return nil, e
		}
		if e = releaseOperationCAS(s.DB, operation, "DISPATCHED", "OBSERVED", receipt); e != nil {
			return nil, e
		}
		o.Status = "OBSERVED"
		o.Receipt = sql.NullString{String: receipt, Valid: true}
	}
	if o.Status != "OBSERVED" {
		return nil, errors.New("raw process receipt unavailable")
	}
	_, receipt, e := supervisor.ReadFixtureReceipt(releaseStateRoot(h), j, driver, operation)
	if e != nil || receipt != o.Receipt.String {
		return nil, errors.New("raw release receipt changed before projection")
	}
	tx, e = s.DB.BeginTx(ctx, nil)
	if e != nil {
		return nil, e
	}
	defer tx.Rollback()
	x, e = load(tx, project, "SystemCandidate", o.Candidate)
	if e != nil {
		return nil, e
	}
	if x["status"] != "EVALUATING" || x["regression_acceptance_id"] != sealed.AcceptanceID {
		return nil, errors.New("candidate changed before release projection")
	}
	res, e := tx.Exec(`UPDATE evolution_slots SET active_hash=?,candidate=?,epoch=?,state='CANARY' WHERE project=? AND state='STABLE' AND epoch=? AND active_hash=?`, "sha256:"+sealed.CandidateSHA256, o.Candidate, j.State().Epoch, project, sealed.ExpectedEpoch, "sha256:"+sealed.StableSHA256)
	if e != nil {
		return nil, e
	}
	n, e := res.RowsAffected()
	if e != nil || n != 1 {
		return nil, errors.New("fixture slot projection fence changed")
	}
	x["status"] = "CANARY"
	if e = bump(x); e != nil {
		return nil, e
	}
	if e = s.put(tx, "SystemCandidate", x); e != nil {
		return nil, e
	}
	res, e = tx.Exec(`UPDATE evolution_release_operations SET status='PROJECTED',projection_revision=? WHERE operation_id=? AND status='OBSERVED' AND receipt_digest=?`, x["revision"], operation, receipt)
	if e != nil {
		return nil, e
	}
	n, e = res.RowsAffected()
	if e != nil || n != 1 {
		return nil, errors.New("release projection revision fence changed")
	}
	if e = s.event(tx, project, "SystemCandidate", x, Str(h, "release_principal"), ID(), "PROJECT_UPDATED"); e != nil {
		return nil, e
	}
	if e = tx.Commit(); e != nil {
		return nil, e
	}
	return Object{"operation_id": operation, "status": "PROJECTED", "receipt_digest": receipt, "projection_revision": x["revision"], "candidate_status": x["status"], "scope": "R2_NATIVE_FIXTURE"}, nil
}
