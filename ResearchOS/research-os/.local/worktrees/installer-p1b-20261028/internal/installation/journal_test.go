package installation

import "testing"

func TestJournalIntentCompletionAndTerminal(t *testing.T) {
	j := Journal{}
	var err error
	for _, state := range forward {
		j, err = j.Append(JournalRecord{State:state, Step:string(state), Phase:"INTENT", ObservedFactsSHA256:"facts"})
		if state == Committed { // commit can only be recorded as completed
			if err == nil { t.Fatal("intent commit accepted") }; break
		}
		if err != nil { t.Fatal(err) }
		j, err = j.Append(JournalRecord{State:state, Step:string(state), Phase:"COMPLETE", ObservedFactsSHA256:"facts"})
		if err != nil { t.Fatal(err) }
	}
	// The final transition records its intent under VERIFYING; COMMITTED is atomic.
	j, err = j.Append(JournalRecord{State:Committed, Step:"COMMIT", Phase:"COMPLETE", ObservedFactsSHA256:"facts"})
	if err != nil { t.Fatal(err) }
	if len(j.Records) != 13 { t.Fatalf("record count %d", len(j.Records)) }
	if _, err := j.Append(JournalRecord{State:RollingBack, Step:"UNDO", Phase:"RECOVERY", ObservedFactsSHA256:"facts"}); err == nil { t.Fatal("rollback after commit") }
	if got := RecoveryDecision(j, RecoveryFacts{}); got != Committed { t.Fatal(got) }
}

func TestRecoveryRequiresObservedOwnershipAndStoppedCandidate(t *testing.T) {
	j, _ := (Journal{}).Append(JournalRecord{State:Prepared, Step:"prepare", Phase:"INTENT", ObservedFactsSHA256:"before"})
	if got := RecoveryDecision(j, RecoveryFacts{}); got != NeedsRecovery { t.Fatal(got) }
	f := RecoveryFacts{ObservedFactsSHA256:"now", OldProgramMatches:true, DataMatches:true, OwnershipMatches:true, CandidateStopped:true}
	if got := RecoveryDecision(j, f); got != RollingBack { t.Fatal(got) }
	f.CandidateStopped = false
	if got := RecoveryDecision(j, f); got != NeedsRecovery { t.Fatal(got) }
	if MaintenanceSequence[4] != "VERIFY_CAPTURED_PROCESS_IDENTITIES" || MaintenanceSequence[5] != "ACQUIRE_EXCLUSIVE_MAINTENANCE" { t.Fatal("maintenance ordering") }
}
