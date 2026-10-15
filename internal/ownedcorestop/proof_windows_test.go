//go:build windows

package ownedcorestop

import (
	"path/filepath"
	"strings"
	"testing"
)

func TestOwnedCoreStopMissingHistoricalProofNeverEligible(t *testing.T) {
	plan := Plan{OperationID: strings.Repeat("a", 32), Input: Input{SourceRepository: t.TempDir()}}
	_, missing := validateHistoricalEvidence(plan)
	if len(missing) < len(proofKinds) {
		t.Fatalf("missing F01/native/effect proofs were accepted: %v", missing)
	}
	for _, ref := range []EvidenceRef{{Kind: "f01_ready", Path: filepath.Join(t.TempDir(), "forged.json"), SHA256: strings.Repeat("a", 64)}} {
		plan.Input.Evidence = append(plan.Input.Evidence, ref)
	}
	_, missing = validateHistoricalEvidence(plan)
	if len(missing) == 0 {
		t.Fatal("caller-selected evidence outside independent namespace accepted")
	}
}

func TestOwnedCoreStopCallerReviewCannotOmitExactScope(t *testing.T) {
	plan := Plan{Input: Input{SourceRepository: t.TempDir(), PlanReviewPath: filepath.Join(t.TempDir(), "review.json")}}
	if err := validatePlanReview(plan, strings.Repeat("a", 64)); err == nil {
		t.Fatal("non-independent review path accepted")
	}
}
