//go:build windows

package domain

import (
	"context"
	"fmt"
	"researchos.local/research-os/evaluation/evolution"
)

func (s *Service) completedCurrentEvaluation(ctx context.Context, a *currentControlAuthority, req evolution.ControlCurrentRequest) (evolution.ControlCurrentReply, error) {
	var out evolution.ControlCurrentReply
	tx, err := s.DB.BeginTx(ctx, nil)
	if err != nil {
		return out, err
	}
	defer tx.Rollback()
	p, err := authenticate(tx, req.VerifierToken)
	if err != nil || p.ID != a.frozen.Verifier {
		return out, fmt.Errorf("CONTROL_CURRENT_VERIFIER_CHANGED")
	}
	if err = a.currentEvaluationJournal(tx, controlCurrentRecorded); err != nil {
		return out, err
	}
	if _, err = a.validateCurrentRows(tx); err != nil {
		return out, err
	}
	var raw, receipt string
	if err = tx.QueryRow("SELECT body,receipt_hash FROM evolution_executions WHERE project=? AND candidate=? AND run=? AND epoch=? AND phase='REGRESSION' AND state='RECORDED'", a.project, a.frozen.Candidate, a.frozen.Run, a.frozen.Epoch).Scan(&raw, &receipt); err != nil {
		return out, err
	}
	record, err := Decode([]byte(raw))
	if err != nil || record["receipt_hash"] != receipt || receipt != Receipt(record) {
		return out, fmt.Errorf("CONTROL_CURRENT_COMPLETED_EXECUTION_HASH")
	}
	ref, ok := record["artifact_ref"].(map[string]any)
	if !ok {
		return out, fmt.Errorf("CONTROL_CURRENT_COMPLETED_REFERENCE")
	}
	out = controlCurrentReply(a, "EVALUATE")
	out.ObservationRef = ref
	out.Summary = Object{"status": "SEALED_EXISTING_RESULT", "reexecuted": false}
	return out, nil
}
