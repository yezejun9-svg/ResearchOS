//go:build windows

package supervisor

import (
	"context"
	"errors"
	"fmt"
	"path/filepath"
	"sync"
	"time"
)

// ReleaseAdmission is a frozen input supplied by an independent verifier.
// This package only exercises a same-schema fixture; it never manufactures
// verifier authority from candidate-writable domain state.
type ReleaseAdmission struct {
	Project               string    `json:"project"`
	CandidateID           string    `json:"candidate_id"`
	AcceptanceID          string    `json:"acceptance_id"`
	ExecutionSHA256       string    `json:"execution_sha256"`
	Operation             string    `json:"operation"`
	ExpectedEpoch         uint64    `json:"expected_epoch"`
	StableSHA256          string    `json:"stable_sha256"`
	CandidateSHA256       string    `json:"candidate_sha256"`
	BackupReceiptSHA256   string    `json:"backup_receipt_sha256"`
	VerifierReceiptSHA256 string    `json:"verifier_receipt_sha256"`
	HoldoutProofSHA256    string    `json:"holdout_proof_sha256"`
	SameSchema            bool      `json:"same_schema"`
	NoUnknownEffects      bool      `json:"no_unknown_effects"`
	ExpiresUTC            time.Time `json:"expires_utc"`
}

type AdmissionVerifier func(ReleaseAdmission) error

type ReleaseBarrier interface {
	Drain(context.Context, ProcessIdentity, string) (string, error)
	Ready(context.Context, ProcessIdentity, string) error
	Compatible(context.Context, ReleaseState) error
}

type ReleaseEngine struct {
	mu      sync.Mutex
	journal *ReleaseJournal
	driver  ProcessDriver
	barrier ReleaseBarrier
	verify  AdmissionVerifier
}

func NewReleaseEngine(j *ReleaseJournal, d ProcessDriver, b ReleaseBarrier, v AdmissionVerifier) (*ReleaseEngine, error) {
	if j == nil || d == nil || b == nil || v == nil {
		return nil, errors.New("independent release dependencies required")
	}
	return &ReleaseEngine{journal: j, driver: d, barrier: b, verify: v}, nil
}

func processIn(s ReleaseState) ProcessIdentity {
	return ProcessIdentity{PID: s.PID, CreatedNS: s.CreatedNS, ImageSHA256: s.ImageSHA256}
}

func setProcess(s *ReleaseState, p ProcessIdentity) {
	s.PID, s.CreatedNS, s.ImageSHA256 = p.PID, p.CreatedNS, p.ImageSHA256
}

func clearProcess(s *ReleaseState) { s.PID, s.CreatedNS, s.ImageSHA256 = 0, 0, "" }

// BootstrapFixture starts one disposable stable binary in an empty state root.
// STARTING is durable before launch; a crash before the PID is recorded cannot
// be retried automatically because the launch may already have succeeded.
func (e *ReleaseEngine) BootstrapFixture(ctx context.Context, stablePath, data string) error {
	e.mu.Lock()
	defer e.mu.Unlock()
	if e.journal.Sequence() != 0 {
		return errors.New("release state already initialized")
	}
	if !filepath.IsAbs(data) {
		return errors.New("absolute fixture data root required")
	}
	_, digest, err := exactImage(stablePath)
	if err != nil {
		return err
	}
	s := ReleaseState{Epoch: 1, Phase: "STARTING", Operation: "bootstrap", Active: digest, ActivePath: stablePath, LastGood: digest, LastGoodPath: stablePath, Data: data}
	if err = e.journal.Append(s); err != nil {
		return err
	}
	p, err := e.driver.Start(stablePath, "bootstrap-1", data)
	if err != nil {
		s.Phase = "RECOVERING"
		_ = e.journal.Append(s)
		return err
	}
	setProcess(&s, p)
	s.Phase = "STABLE"
	if err = e.barrier.Ready(ctx, p, "bootstrap-1"); err != nil {
		_ = e.driver.Stop(p)
		s.Phase = "RECOVERING"
		_ = e.journal.Append(s)
		return err
	}
	return e.journal.Append(s)
}

// PrepareFixture persists one immutable operation before any process action.
// Duplicate operation IDs return the existing state; stale epochs and frozen
// digests cannot be used to rename or replay a failed candidate.
func (e *ReleaseEngine) PrepareFixture(a ReleaseAdmission, candidatePath string) (ReleaseState, error) {
	e.mu.Lock()
	defer e.mu.Unlock()
	s := e.journal.State()
	if s.Operation == a.Operation && s.Admission == releaseHash(a) {
		return s, nil
	}
	if s.Phase != "STABLE" && s.Phase != "ROLLED_BACK" {
		return s, errors.New("release operation already in progress")
	}
	if a.Project == "" || a.CandidateID == "" || a.AcceptanceID == "" || a.Operation == "" || !validDigest(a.ExecutionSHA256) || a.ExpectedEpoch != s.Epoch || a.StableSHA256 != s.Active || !validDigest(a.BackupReceiptSHA256) || !validDigest(a.VerifierReceiptSHA256) || !validDigest(a.HoldoutProofSHA256) || !a.SameSchema || !a.NoUnknownEffects || !a.ExpiresUTC.After(time.Now().UTC()) {
		return s, errors.New("release admission incomplete or stale")
	}
	for _, frozen := range s.Frozen {
		if frozen == a.CandidateSHA256 {
			return s, errors.New("failed candidate digest frozen")
		}
	}
	_, digest, err := exactImage(candidatePath)
	if err != nil || digest != a.CandidateSHA256 {
		return s, errors.New("candidate image differs from admission")
	}
	if err = e.verify(a); err != nil {
		return s, fmt.Errorf("independent verifier rejected admission: %w", err)
	}
	if s.PID == 0 {
		return s, errors.New("stable process identity absent")
	}
	alive, err := e.driver.Alive(processIn(s))
	if err != nil || !alive {
		return s, errors.New("stable process not observed")
	}
	s.Epoch++
	s.Operation = a.Operation
	s.Candidate = a.CandidateSHA256
	s.CandidatePath = candidatePath
	s.Backup = a.BackupReceiptSHA256
	s.Admission = releaseHash(a)
	s.AdmissionBundle = &a
	s.Phase = "PREPARED"
	if err = e.journal.Append(s); err != nil {
		return e.journal.State(), err
	}
	return s, nil
}

// SwitchFixture performs an actual serial process switch. Drain and ready are
// observed outside candidate state. An uncertain launch window remains sealed
// as SWITCHED; restart recovery never sends Start a second time.
func (e *ReleaseEngine) SwitchFixture(ctx context.Context, operation string) (ReleaseState, error) {
	e.mu.Lock()
	defer e.mu.Unlock()
	s := e.journal.State()
	if s.Operation != operation || s.Phase != "PREPARED" {
		return s, errors.New("operation not prepared")
	}
	if s.AdmissionBundle == nil || releaseHash(*s.AdmissionBundle) != s.Admission || s.AdmissionBundle.ExpectedEpoch+1 != s.Epoch || !s.AdmissionBundle.ExpiresUTC.After(time.Now().UTC()) {
		return s, errors.New("sealed admission missing, changed or expired")
	}
	if err := e.verify(*s.AdmissionBundle); err != nil {
		return s, fmt.Errorf("independent verifier revoked admission: %w", err)
	}
	_, digest, err := exactImage(s.CandidatePath)
	if err != nil || digest != s.Candidate {
		return s, errors.New("candidate image changed")
	}
	proof, err := e.barrier.Drain(ctx, processIn(s), operation)
	if err != nil || !validDigest(proof) {
		return e.journal.State(), errors.New("stable drain receipt absent")
	}
	s.DrainNonce = e.journal.State().DrainNonce
	s.DrainReceipt = proof
	s.Phase = "DRAINED"
	if err = e.journal.Append(s); err != nil {
		return s, err
	}
	if err = e.driver.Stop(processIn(s)); err != nil {
		return e.journal.State(), err
	}
	alive, err := e.driver.Alive(processIn(s))
	if err != nil || alive {
		return s, fmt.Errorf("stable process stop not observed: alive=%v error=%v", alive, err)
	}
	clearProcess(&s)
	s.Active = s.Candidate
	s.ActivePath = s.CandidatePath
	s.Phase = "SWITCHED"
	if err = e.journal.Append(s); err != nil {
		return s, err
	}
	p, err := e.driver.Start(s.ActivePath, operation, s.Data)
	if err != nil {
		return s, err
	}
	setProcess(&s, p)
	s.Phase = "CANARY"
	if err = e.journal.Append(s); err != nil {
		return s, err
	}
	if err = e.barrier.Ready(ctx, p, operation); err != nil {
		return s, err
	}
	return s, nil
}

// RollbackFixture freezes the failed digest and returns to the exact last good
// executable only after a separate compatibility barrier. It never overwrites
// data or reissues external effects.
func (e *ReleaseEngine) RollbackFixture(ctx context.Context, operation string) (ReleaseState, error) {
	e.mu.Lock()
	defer e.mu.Unlock()
	s := e.journal.State()
	if s.Operation != operation || (s.Phase != "CANARY" && s.Phase != "ROLLBACK_PREPARED") {
		return s, errors.New("operation not in rollback-capable phase")
	}
	if s.Phase != "ROLLBACK_PREPARED" {
		s.Phase = "ROLLBACK_PREPARED"
		if err := e.journal.Append(s); err != nil {
			return s, err
		}
	}
	if s.PID != 0 {
		if err := e.driver.Stop(processIn(s)); err != nil {
			return s, err
		}
		alive, err := e.driver.Alive(processIn(s))
		if err != nil || alive {
			return s, errors.New("candidate stop not observed")
		}
		clearProcess(&s)
	}
	if err := e.barrier.Compatible(ctx, s); err != nil {
		s.Phase = "RECOVERING"
		_ = e.journal.Append(s)
		return s, err
	}
	_, digest, err := exactImage(s.LastGoodPath)
	if err != nil || digest != s.LastGood {
		s.Phase = "RECOVERING"
		_ = e.journal.Append(s)
		return s, errors.New("last known good image changed")
	}
	s.Frozen = append(s.Frozen, s.Candidate)
	s.Active = s.LastGood
	s.ActivePath = s.LastGoodPath
	s.Phase = "SWITCHED"
	if err = e.journal.Append(s); err != nil {
		return s, err
	}
	p, err := e.driver.Start(s.ActivePath, operation+"-rollback", s.Data)
	if err != nil {
		return s, err
	}
	setProcess(&s, p)
	s.Phase = "ROLLED_BACK"
	if err = e.journal.Append(s); err != nil {
		return s, err
	}
	if err = e.barrier.Ready(ctx, p, operation+"-rollback"); err != nil {
		return s, err
	}
	return s, nil
}

// Reconcile inspects OS state and never replays an uncertain start, stop or
// external effect after supervisor restart. A caller can resume a live canary
// only with a matching PID, creation time and executable digest.
func (e *ReleaseEngine) Reconcile() (ReleaseState, error) {
	e.mu.Lock()
	defer e.mu.Unlock()
	s := e.journal.State()
	if e.journal.Sequence() == 0 {
		return s, nil
	}
	if s.Phase == "STARTING" || s.Phase == "SWITCHED" || s.Phase == "DRAIN_UNKNOWN" || s.Phase == "EXIT_UNKNOWN" || s.Phase == "DRAINED" || s.Phase == "ROLLBACK_PREPARED" || s.Phase == "RECOVERING" {
		return s, errors.New("uncertain release side effect; manual reconciliation required")
	}
	if s.PID == 0 {
		return s, errors.New("active process identity absent")
	}
	if s.Phase == "CANARY" && (s.AdmissionBundle == nil || releaseHash(*s.AdmissionBundle) != s.Admission) {
		return s, errors.New("sealed admission changed")
	}
	alive, err := e.driver.Alive(processIn(s))
	if err != nil || !alive {
		return s, errors.New("active process missing or identity changed")
	}
	return s, nil
}
