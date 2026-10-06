package protectedstore

import (
	"encoding/hex"
	"os"
	"reflect"
	"researchos.local/research-os/adapters/decision"
	holdout "researchos.local/research-os/evaluation/holdout/jev"
	"sync"
	"time"
)

const frozenProjectID = "aede0678-7308-43dc-b9f2-cfe3d90cfdfb"

// FrozenKeyCounts contains only aggregate bounded counters for a fixed language
// key. It is absent during RUNNING, including on repeated status polling.
type FrozenBaselineCounts struct {
	Rule        string `json:"rule"`
	Correct     int64  `json:"correct"`
	FalseAccept int64  `json:"false_accept"`
	FalseReject int64  `json:"false_reject"`
}
type FrozenKeyCounts struct {
	PositiveLabelCount      int64                   `json:"positive_label_count"`
	NegativeLabelCount      int64                   `json:"negative_label_count"`
	NonAbstainedAcceptCount int64                   `json:"nonabstained_accept_count"`
	NonAbstainedRejectCount int64                   `json:"nonabstained_reject_count"`
	Baseline                FrozenBaselineCounts    `json:"baseline"`
	Scope                   decision.Scope          `json:"scope"`
	Development             FrozenDevelopmentCounts `json:"development"`
	DevelopmentCount        int64                   `json:"development_count"`
	Planned                 int64                   `json:"planned"`
	StartedRequests         int64                   `json:"started_requests"`
	RecordedInvocations     int64                   `json:"recorded_invocations"`
	UnknownRequests         int64                   `json:"unknown_requests"`
	HTTP200                 int64                   `json:"http_200"`
	Correct                 int64                   `json:"correct"`
	FalseAccept             int64                   `json:"false_accept"`
	FalseReject             int64                   `json:"false_reject"`
	Abstain                 int64                   `json:"abstain"`
	CriticalFalseAccept     int64                   `json:"critical_false_accept"`
	Errors                  int64                   `json:"errors"`
	LatencyMS               int64                   `json:"latency_ms"`
}

type FrozenRunSummary struct {
	DevelopmentHash    string            `json:"development_aggregate_hash"`
	Dataset            *Blob             `json:"dataset,omitempty"`
	FrozenAt           string            `json:"frozen_at,omitempty"`
	ProjectID          string            `json:"project_id"`
	RunState           string            `json:"run_state"`
	GeneratorRevision  string            `json:"generator_revision"`
	RubricHash         string            `json:"rubric_hash"`
	Threshold          float64           `json:"confidence_threshold"`
	RequestBudget      int64             `json:"request_budget"`
	Qualification      string            `json:"qualification"`
	AutomaticAuthority string            `json:"automatic_authority"`
	CostStatus         string            `json:"cost_status"`
	Keys               []FrozenKeyCounts `json:"keys"`
	BinaryHash         string            `json:"binary_hash"`
}

var binaryHashOnce sync.Once
var binaryHash string

func frozenBinaryHash() string {
	binaryHashOnce.Do(func() {
		path, e := os.Executable()
		if e != nil {
			return
		}
		info, e := os.Stat(path)
		if e != nil || info.Size() > 64<<20 {
			return
		}
		raw, e := os.ReadFile(path)
		if e == nil {
			binaryHash = decision.Digest(raw)
		}
	})
	return binaryHash
}

func newFrozenSummary(state string) SafeSummary {
	status := "BLOCKED"
	if state == "READY" || state == "RUNNING" {
		status = state
	}
	return SafeSummary{Schema: "researchos.protected-summary.v1", Status: status, MaximumMode: "ADVISORY", Frozen: &FrozenRunSummary{
		DevelopmentHash: frozenDevelopmentHash, ProjectID: frozenProjectID, RunState: state, GeneratorRevision: holdout.GeneratorRevision, RubricHash: holdout.RubricHash(), Threshold: holdout.Threshold,
		RequestBudget: holdout.CaseCount, Qualification: "PENDING", AutomaticAuthority: "NONE", CostStatus: "UNKNOWN", Keys: nil, BinaryHash: frozenBinaryHash(),
	}}
}

func (s SafeSummary) validateFrozen() error {
	f := s.Frozen
	if f == nil {
		return nil
	}
	if f.DevelopmentHash != frozenDevelopmentHash || f.ProjectID != frozenProjectID || f.GeneratorRevision != holdout.GeneratorRevision || f.RubricHash != holdout.RubricHash() || f.Threshold != holdout.Threshold || f.RequestBudget != holdout.CaseCount || f.AutomaticAuthority != "NONE" || f.CostStatus != "UNKNOWN" || f.BinaryHash == "" {
		return ErrIntegrity
	}
	// A consumer may run a different control-plane executable; the native IPC
	// client additionally binds this hash to the immutable installed service.
	if len(f.BinaryHash) != 71 || f.BinaryHash[:7] != "sha256:" {
		return ErrIntegrity
	}
	if _, err := hex.DecodeString(f.BinaryHash[7:]); err != nil {
		return ErrIntegrity
	}
	terminal := f.RunState == "COMPLETED" || f.RunState == "INTERRUPTED" || f.RunState == "CORRUPT"
	if !terminal {
		if f.RunState != "NOT_CONFIGURED" && f.RunState != "READY" && f.RunState != "RUNNING" && f.RunState != "BLOCKED_STORAGE" {
			return ErrIntegrity
		}
		status := "BLOCKED"
		if f.RunState == "READY" || f.RunState == "RUNNING" {
			status = f.RunState
		}
		if f.Dataset != nil || f.FrozenAt != "" || s.Status != status || f.Qualification != "PENDING" || len(f.Keys) != 0 || s.Total != 0 || s.Correct != 0 || s.FalseAccept != 0 || s.FalseReject != 0 || s.Abstain != 0 || s.CriticalFalseAccept != 0 {
			return ErrIntegrity
		}
		return nil
	}
	if s.Status != "EXECUTION_REPORTED" || f.Qualification != "FAILED" || len(f.Keys) != 2 {
		return ErrIntegrity
	}
	if f.Dataset != nil {
		d := f.Dataset
		if !d.Valid() || d.Project != frozenProjectID || d.MeasurementMode != "LIVE" || d.MediaType != "application/json" || d.Ticket != "ps1:"+d.Hash[7:39] {
			return ErrIntegrity
		}
		if _, err := time.Parse(time.RFC3339Nano, f.FrozenAt); err != nil {
			return ErrIntegrity
		}
	} else if f.FrozenAt != "" || f.RunState == "COMPLETED" {
		return ErrIntegrity
	}
	var total, correct, fa, fr, abstain, critical int64
	for i, language := range []string{"zh", "zh-en"} {
		k := f.Keys[i]
		dev, err := frozenDevelopment(language)
		if err != nil || !reflect.DeepEqual(k.Development, dev) {
			return ErrIntegrity
		}
		// The independently verified public development aggregate is hash frozen;
		// no measurements from another rubric/key can be inherited.
		if k.Scope != holdout.ScopeFor(language) || k.DevelopmentCount != 30 || k.Planned != 15 {
			return ErrIntegrity
		}
		for _, n := range []int64{k.StartedRequests, k.RecordedInvocations, k.UnknownRequests, k.HTTP200, k.Correct, k.FalseAccept, k.FalseReject, k.Abstain, k.CriticalFalseAccept, k.Errors} {
			if n < 0 || n > 15 {
				return ErrIntegrity
			}
		}
		if k.PositiveLabelCount < 0 || k.NegativeLabelCount < 0 || k.PositiveLabelCount+k.NegativeLabelCount != k.StartedRequests || k.NonAbstainedAcceptCount < 0 || k.NonAbstainedRejectCount < 0 || k.NonAbstainedAcceptCount+k.NonAbstainedRejectCount+k.Abstain != k.StartedRequests || k.Baseline != (FrozenBaselineCounts{Rule: "ALWAYS_REJECT", Correct: k.NegativeLabelCount, FalseReject: k.PositiveLabelCount}) {
			return ErrIntegrity
		}
		if k.RecordedInvocations+k.UnknownRequests != k.StartedRequests || k.Correct+k.FalseAccept+k.FalseReject+k.Abstain != k.StartedRequests || k.CriticalFalseAccept > k.FalseAccept || k.Errors > k.Abstain || k.UnknownRequests > k.Errors || k.HTTP200 > k.RecordedInvocations || k.LatencyMS < 0 || k.LatencyMS > 15*61000 {
			return ErrIntegrity
		}
		if f.RunState == "COMPLETED" && (k.StartedRequests != 15 || k.RecordedInvocations != 15 || k.UnknownRequests != 0) {
			return ErrIntegrity
		}
		total += k.StartedRequests
		correct += k.Correct
		fa += k.FalseAccept
		fr += k.FalseReject
		abstain += k.Abstain
		critical += k.CriticalFalseAccept
	}
	if s.Total != total || s.Correct != correct || s.FalseAccept != fa || s.FalseReject != fr || s.Abstain != abstain || s.CriticalFalseAccept != critical {
		return ErrIntegrity
	}
	return nil
}
