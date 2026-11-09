//go:build windows

package domain

import (
	"database/sql"
	"fmt"
	"researchos.local/research-os/evaluation/evolution"
	"researchos.local/research-os/ops/supervisor"
	"time"
)

const controlCurrentReserved = "CURRENT_CONTROL_EVALUATE_RESERVED"
const controlCurrentRecorded = "CURRENT_CONTROL_EVALUATE_RECORDED"

func (a *currentControlAuthority) reservationBody() Object {
	n := a.frozen
	return Object{"purpose": evolution.ControlCurrentPurpose, "profile": evolution.ControlCurrentProfile, "session_id": a.id, "g0_hash": a.g0.Generation, "task_id": n.Task, "lease_epoch": n.Epoch, "owner_hash": Hash(a.owner), "plan_hash": n.Plan}
}

func (a *currentControlAuthority) reservationCurrent(tx *sql.Tx) error {
	return a.currentEvaluationJournal(tx, controlCurrentReserved)
}

func (a *currentControlAuthority) currentEvaluationJournal(tx *sql.Tx, event string) error {
	n := a.frozen
	var count int
	if err := tx.QueryRow("SELECT count(*) FROM evolution_journal WHERE project=? AND candidate=? AND event=?", n.Project, n.Candidate, event).Scan(&count); err != nil {
		return err
	}
	if count != 1 {
		return fmt.Errorf("CONTROL_CURRENT_DURABLE_RESERVATION_REQUIRED")
	}
	var raw, receipt string
	if err := tx.QueryRow("SELECT body,receipt_hash FROM evolution_journal WHERE project=? AND candidate=? AND run=? AND event=?", n.Project, n.Candidate, n.Run, event).Scan(&raw, &receipt); err != nil {
		return err
	}
	body, err := Decode([]byte(raw))
	if err != nil || receipt != Hash(body) || !a.reservationJournalBound(body, event) {
		return fmt.Errorf("CONTROL_CURRENT_RESERVATION_BINDING")
	}
	return nil
}

func (a *currentControlAuthority) reserveCurrentEvaluation(tx *sql.Tx) error {
	n := a.frozen
	var count int
	if err := tx.QueryRow("SELECT count(*) FROM evolution_journal WHERE project=? AND candidate=? AND event IN (?,?)", n.Project, n.Candidate, controlCurrentReserved, controlCurrentRecorded).Scan(&count); err != nil {
		return err
	}
	if count != 0 {
		return fmt.Errorf("CONTROL_CURRENT_EVALUATION_UNKNOWN_INSPECTION_REQUIRED")
	}
	return evolutionJournal(tx, n.Project, n.Candidate, n.Run, controlCurrentReserved, a.reservationBody())
}

func (a *currentControlAuthority) reservationJournalBound(body Object, event string) bool {
	n := a.frozen
	expected := Merge(Object{"project_id": n.Project, "candidate_id": n.Candidate, "run_id": n.Run, "event": event, "scope": evolution.Scope}, a.reservationBody())
	return controlSameExcept(body, expected, "at")
}

func controlNativeEnd(proofs ...supervisor.ControlProof) (string, error) {
	var last time.Time
	count := 0
	for _, proof := range proofs {
		for _, pair := range proof.Pairs {
			for _, inv := range []supervisor.ControlInvocation{pair.Baseline, pair.Candidate} {
				r := inv.Receipt
				start, e := time.Parse(time.RFC3339Nano, r.Started)
				if e != nil {
					return "", fmt.Errorf("CONTROL_NATIVE_START_TIME")
				}
				end, e := time.Parse(time.RFC3339Nano, r.Finished)
				if e != nil || end.Before(start) || !r.Stopped || !r.StreamsDrained || !r.CleanupComplete || r.ExitCode != 0 || r.TimedOut {
					return "", fmt.Errorf("CONTROL_NATIVE_TERMINAL_TIME")
				}
				if end.After(last) {
					last = end
				}
				count++
			}
		}
	}
	if count == 0 {
		return "", fmt.Errorf("CONTROL_NATIVE_TERMINAL_EMPTY")
	}
	return last.UTC().Format(time.RFC3339Nano), nil
}
