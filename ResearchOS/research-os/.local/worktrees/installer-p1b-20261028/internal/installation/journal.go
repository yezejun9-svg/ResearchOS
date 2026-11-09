package installation

import "fmt"

type JournalState string

const (
	Prepared JournalState = "PREPARED"
	OldProgramSaved JournalState = "OLD_PROGRAM_SAVED"
	NewProgramPlaced JournalState = "NEW_PROGRAM_PLACED"
	DataPlaced JournalState = "DATA_PLACED"
	IntegrationApplied JournalState = "INTEGRATION_APPLIED"
	Verifying JournalState = "VERIFYING"
	Committed JournalState = "COMMITTED"
	RollingBack JournalState = "ROLLING_BACK"
	RolledBack JournalState = "ROLLED_BACK"
	NeedsRecovery JournalState = "NEEDS_RECOVERY"
)

type JournalRecord struct {
	Sequence uint64
	State JournalState
	Step string
	Phase string // INTENT, COMPLETE, or RECOVERY
	ObservedFactsSHA256 string
}

type Journal struct { Records []JournalRecord }

var forward = []JournalState{Prepared, OldProgramSaved, NewProgramPlaced, DataPlaced, IntegrationApplied, Verifying, Committed}

// Append never edits a prior record. Each side effect must have an intent and a
// completed record; the caller must persist each append before proceeding.
func (j Journal) Append(next JournalRecord) (Journal, error) {
	if next.Step == "" || next.ObservedFactsSHA256 == "" { return j, fmt.Errorf("step and observed facts required") }
	if next.Phase != "INTENT" && next.Phase != "COMPLETE" && next.Phase != "RECOVERY" { return j, fmt.Errorf("invalid phase") }
	previous := JournalRecord{}
	if len(j.Records) > 0 { previous = j.Records[len(j.Records)-1] }
	if previous.State == Committed || previous.State == RolledBack { return j, fmt.Errorf("terminal journal") }
	if next.State == Committed && next.Phase != "COMPLETE" { return j, fmt.Errorf("commit requires completion") }
	if next.State == Committed && previous.State == Verifying && previous.Phase == "COMPLETE" {
		// The verified commit marker itself is a single durable completion record.
		next.Sequence = previous.Sequence + 1
		out := Journal{Records: make([]JournalRecord, len(j.Records)+1)}
		copy(out.Records, j.Records)
		out.Records[len(j.Records)] = next
		return out, nil
	}
	if next.State == RollingBack || next.State == NeedsRecovery || next.State == RolledBack {
		if next.Phase != "RECOVERY" { return j, fmt.Errorf("recovery phase required") }
		if next.State == RolledBack && previous.State != RollingBack { return j, fmt.Errorf("rollback not started") }
	} else if previous.State == RollingBack || previous.State == NeedsRecovery {
		return j, fmt.Errorf("forward progress blocked by recovery")
	} else if !validForward(previous, next) { return j, fmt.Errorf("invalid forward transition") }
	next.Sequence = previous.Sequence + 1
	out := Journal{Records: make([]JournalRecord, len(j.Records)+1)}
	copy(out.Records, j.Records)
	out.Records[len(j.Records)] = next
	return out, nil
}

func validForward(previous, next JournalRecord) bool {
	index := func(s JournalState) int { for i, v := range forward { if s == v { return i } }; return -1 }
	p, n := index(previous.State), index(next.State)
	if n < 0 { return false }
	if p < 0 { return n == 0 && next.Phase == "INTENT" }
	if n == p { return previous.Phase == "INTENT" && next.Phase == "COMPLETE" && previous.Step == next.Step }
	return n == p+1 && previous.Phase == "COMPLETE" && next.Phase == "INTENT"
}

type RecoveryFacts struct {
	ObservedFactsSHA256 string
	OldProgramMatches bool
	NewProgramMatches bool
	DataMatches bool
	CandidateStopped bool
	OwnershipMatches bool
}

// RecoveryDecision is conservative: any unproved identity requires manual
// recovery. A committed transaction must never be restored from an old copy.
func RecoveryDecision(j Journal, facts RecoveryFacts) JournalState {
	if len(j.Records) == 0 { return NeedsRecovery }
	last := j.Records[len(j.Records)-1]
	if last.State == Committed { return Committed }
	if last.State == RolledBack { return RolledBack }
	if facts.ObservedFactsSHA256 == "" || !facts.OwnershipMatches || !facts.CandidateStopped || !facts.DataMatches { return NeedsRecovery }
	if !facts.OldProgramMatches && !facts.NewProgramMatches { return NeedsRecovery }
	if facts.OldProgramMatches { return RollingBack }
	return NeedsRecovery
}

// MaintenanceSequence defines ordering for a future OS adapter. The use lease
// is drained before exclusive maintenance admission to avoid deadlock.
var MaintenanceSequence = [...]string{"SERIALIZE_INSTALLERS", "PERSIST_MAINTENANCE_REQUESTED", "BLOCK_NEW_USE", "SAFE_EXIT_AND_DRAIN_EXISTING_USE", "VERIFY_CAPTURED_PROCESS_IDENTITIES", "ACQUIRE_EXCLUSIVE_MAINTENANCE", "ACQUIRE_DATA_COORDINATOR", "TRANSACT_AND_VERIFY", "COMMIT_OR_RECOVER"}
