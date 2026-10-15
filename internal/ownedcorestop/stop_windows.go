//go:build windows

package ownedcorestop

import (
	"context"
	"errors"
	"fmt"
	"path/filepath"
	"time"

	rt "researchos.local/research-os/adapters/runtime"
	"researchos.local/research-os/internal/host"
	"researchos.local/research-os/internal/store"
	"researchos.local/research-os/ops/supervisor"
)

// Preflight only observes the named existing process and new owned fixture or
// future reviewed data. This source card does not call it on current product.
func Preflight(ctx context.Context, inputPath, operationID, outDir string) (Plan, string, error) {
	var p Plan
	in, inputSHA, err := readInput(inputPath)
	if err != nil {
		return p, "", err
	}
	if in.OperationID != operationID {
		return p, "", errors.New("operation ID differs from strict input")
	}
	if err = createPrivateOutput(outDir, in.DataRoot); err != nil {
		return p, "", err
	}
	p = Plan{Schema: PlanSchema, OperationID: in.OperationID, SourceBaseCommit: SourceBaseCommit, OutputDir: outDir, InputSHA256: inputSHA, Input: in, BackupPath: filepath.Join(outDir, "backup.sqlite"), Eligibility: "STOP_UNAVAILABLE"}
	p.Native, err = supervisor.ObserveOwnedCoreReadOnly(in.CorePID)
	if err != nil {
		return p, "", err
	}
	p.Host, err = host.ReadOwnedCoreStopPublicIdentity(ctx, in.DataRoot)
	if err != nil {
		return p, "", err
	}
	if p.Native.SID != p.Host.SID || p.Native.ParentSID != p.Host.SID {
		return p, "", errors.New("Core/parent/current SID mismatch")
	}
	p.Baseline, p.BackupSHA256, err = store.OnlineOwnedStopBackup(ctx, p.Host.Database, p.BackupPath)
	if err != nil {
		return p, "", err
	}
	p.PreflightSafety, err = store.ReadOwnedStopSafetyPreflight(ctx, p.Host.Database, in.Subject)
	if err != nil {
		p.Missing = append(p.Missing, "preflight safety catalog: "+err.Error())
	} else if !p.PreflightSafety.ExactOldSubjectSafe() {
		p.Missing = append(p.Missing, "additional unresolved work or exact old subject differs")
	}
	proofSHA, missing := validateHistoricalEvidence(p)
	p.EvidenceSHA256 = proofSHA
	p.Missing = append(p.Missing, missing...)
	if len(p.Missing) == 0 {
		p.Eligibility = "ELIGIBLE_FOR_INDEPENDENT_REVIEW"
	}
	if err = validatePlan(p); err != nil {
		return p, "", err
	}
	if _, err = writeOwnedJournal(outDir, "backup-manifest.json", struct {
		Schema, OperationID, BackupSHA256 string
		Census                            store.OwnedStopCensus `json:"census"`
	}{"researchos.owned-core-stop-backup.v1", p.OperationID, p.BackupSHA256, p.Baseline}); err != nil {
		return p, "", err
	}
	planSHA, err := writeOwnedJournal(outDir, "plan.json", p)
	return p, planSHA, err
}

func stopResult(plan Plan, sha, state, reason string) Result {
	return Result{Schema: ResultSchema, OperationID: plan.OperationID, PlanSHA256: sha, State: state, Reason: reason}
}

func persistStopResult(plan Plan, result Result) (Result, error) {
	_, err := writeOwnedJournal(plan.OutputDir, "POSTFLIGHT.json", result)
	return result, err
}

// Commit has no force flag. An exact independent evidence review and a later
// exact root operation plan review must already exist in the verifier namespace.
// This card does not produce either review and grants no current-Core action.
func Commit(ctx context.Context, planPath, expectPlanSHA string) (Result, error) {
	p, planSHA, err := readPlan(planPath)
	if err != nil {
		return Result{}, err
	}
	if !validSHA(expectPlanSHA) || planSHA != expectPlanSHA {
		return stopResult(p, planSHA, "STALE_PLAN", "reviewed plan hash differs"), nil
	}
	if p.Eligibility != "ELIGIBLE_FOR_INDEPENDENT_REVIEW" || len(p.Missing) != 0 {
		return stopResult(p, planSHA, "STOP_UNAVAILABLE", "historical proof missing"), nil
	}
	if err = validatePlanReview(p, planSHA); err != nil {
		return stopResult(p, planSHA, "STOP_UNAVAILABLE", err.Error()), nil
	}
	proofSHA, missing := validateHistoricalEvidence(p)
	if len(missing) != 0 || proofSHA != p.EvidenceSHA256 {
		return stopResult(p, planSHA, "STOP_UNAVAILABLE", "independent evidence drift"), nil
	}
	backup, backupSHA, err := store.ReadOwnedStopBackup(ctx, p.BackupPath)
	if err != nil || backupSHA != p.BackupSHA256 || backup != p.Baseline {
		return stopResult(p, planSHA, "STALE_PLAN", "reviewed backup/hash/census differs"), nil
	}
	// PROCESS_TERMINATE is requested only after all external evidence and exact
	// operation-plan review checks have passed. The native handle stays retained.
	h, err := supervisor.OpenOwnedCoreRetained(p.Native)
	if err != nil {
		return stopResult(p, planSHA, "STOP_UNAVAILABLE", err.Error()), nil
	}
	defer h.Close()
	if _, err = writeOwnedJournal(p.OutputDir, "BEGIN.json", struct{ Schema, OperationID, PlanSHA256 string }{"researchos.owned-core-stop-begin.v1", p.OperationID, planSHA}); err != nil {
		return Result{}, err
	}
	barrier, err := store.AcquireOwnedStopBarrier(ctx, p.Host.Database)
	if err != nil {
		return persistStopResult(p, stopResult(p, planSHA, "STOP_UNAVAILABLE", "writer reservation unavailable: "+err.Error()))
	}
	defer barrier.Close()
	current, err := barrier.Census(ctx)
	if err != nil || current != p.Baseline {
		return persistStopResult(p, stopResult(p, planSHA, "STALE_PLAN", "full logical baseline changed"))
	}
	safety, err := barrier.SafetySnapshot(ctx, p.Input.Subject)
	if err != nil || !safety.ExactOldSubjectSafe() {
		return persistStopResult(p, stopResult(p, planSHA, "STOP_UNAVAILABLE", "current unresolved subject/effect census differs"))
	}
	authority, err := host.ReadOwnedCoreStopPublicIdentity(ctx, p.Input.DataRoot)
	if err != nil || authority != p.Host {
		return persistStopResult(p, stopResult(p, planSHA, "STOP_UNAVAILABLE", "current Host/Owner/database identity differs"))
	}
	if _, err = writeOwnedJournal(p.OutputDir, "TERMINATE_INTENT.json", struct {
		Schema, OperationID, PlanSHA256 string
		Native                          supervisor.OwnedCoreNativeIdentity `json:"native"`
	}{"researchos.owned-core-stop-terminate-intent.v1", p.OperationID, planSHA, p.Native}); err != nil {
		return Result{}, err
	}
	exit, nativeErr := h.TerminateOnceAndWait(15 * time.Second)
	if nativeErr != nil {
		result := stopResult(p, planSHA, "UNKNOWN", fmt.Sprintf("single native attempt or wait unknown: %v", nativeErr))
		result.Native = &exit
		return persistStopResult(p, result)
	}
	if _, err = writeOwnedJournal(p.OutputDir, "NATIVE_EXIT.json", struct {
		Schema, OperationID, PlanSHA256 string
		Native                          supervisor.OwnedCoreNativeExit `json:"native"`
	}{"researchos.owned-core-stop-native-exit.v1", p.OperationID, planSHA, exit}); err != nil {
		return Result{}, err
	}
	if err = barrier.Close(); err != nil {
		result := stopResult(p, planSHA, "STOP_OBSERVED_MAINTENANCE_BLOCKED", "writer reservation release failed")
		result.Native = &exit
		return persistStopResult(p, result)
	}
	return finishAfterNativeExit(ctx, p, planSHA, exit)
}

// Called only after an observed native exit and release of the reserved writer.
// A real DataRootLease plus fresh database and authority reads determine state.
func finishAfterNativeExit(ctx context.Context, p Plan, planSHA string, exit supervisor.OwnedCoreNativeExit) (Result, error) {
	if !exit.ExitObserved {
		return persistStopResult(p, stopResult(p, planSHA, "UNKNOWN", "native exit not observed"))
	}
	lease, err := rt.AcquireDataRootLease(p.Input.DataRoot)
	if err != nil {
		result := stopResult(p, planSHA, "STOP_OBSERVED_MAINTENANCE_BLOCKED", "real DataRootLease unavailable")
		result.Native = &exit
		return persistStopResult(p, result)
	}
	defer lease.Close()
	if !lease.Held() {
		result := stopResult(p, planSHA, "STOP_OBSERVED_MAINTENANCE_BLOCKED", "real DataRootLease not held")
		result.Native = &exit
		return persistStopResult(p, result)
	}
	post, postErr := store.ReadOwnedStopCensus(ctx, p.Host.Database)
	postAuthority, authorityErr := host.ReadOwnedCoreStopPublicIdentity(ctx, p.Input.DataRoot)
	result := stopResult(p, planSHA, "STOPPED_LEASE_VERIFIED", "")
	result.Native = &exit
	result.Postflight = &post
	if exit.BeforeSignal {
		result.State = "OBSERVED_BEFORE_SIGNAL"
	}
	if postErr != nil || authorityErr != nil || post != p.Baseline || postAuthority != p.Host {
		result.State = "STOP_OBSERVED_MAINTENANCE_BLOCKED"
		result.Reason = "poststop logical/schema/authority/integrity drift"
	}
	return persistStopResult(p, result)
}
