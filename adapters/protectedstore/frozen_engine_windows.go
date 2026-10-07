//go:build windows

package protectedstore

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"sync"
	"time"

	"researchos.local/research-os/adapters/decision"
	holdout "researchos.local/research-os/evaluation/holdout/jev"
)

const runMarkerFile = "frozen-run.started.json"
const batchFile = "frozen-run.batch.json"
const batchCommitFile = "frozen-run.batch-commit.json"
const terminalFile = "frozen-run.terminal.json"

type frozenCase struct {
	ID       string
	Scope    decision.Scope
	Request  decision.Request
	Expected string
	Critical bool
}
type frozenBatch struct {
	Raw   []byte
	Cases []frozenCase
}
type frozenGenerator struct {
	Generate func() (frozenBatch, error)
	Restore  func([]byte) (frozenBatch, error)
}
type frozenCall func(context.Context, decision.Binding, decision.Request) (decision.Envelope, error)
type runMarker struct {
	Schema    string `json:"schema"`
	PlanHash  string `json:"plan_hash"`
	StartedAt string `json:"started_at"`
}
type batchCommit struct {
	Hash string `json:"hash"`
}
type callIntent struct {
	Index       int    `json:"index"`
	ID          string `json:"id"`
	Language    string `json:"language"`
	RequestHash string `json:"request_hash"`
}

type frozenEngine struct {
	mu        sync.Mutex
	store     *CanaryStore
	generator frozenGenerator
	newCall   func() (frozenCall, error)
	ctx       context.Context
	summary   SafeSummary
	done      chan struct{}
}

func frozenPlanHash() string {
	return decision.Digest(decision.Encode(map[string]any{
		"generator": holdout.GeneratorRevision, "rubric_hash": holdout.RubricHash(), "model": holdout.ModelRevision,
		"threshold": holdout.Threshold, "request_budget": holdout.CaseCount, "zh": 15, "zh-en": 15,
		"binary_hash":  frozenBinaryHash(),
		"maximum_mode": "ADVISORY", "automatic_authority": "NONE", "rerun": false,
	}))
}
func privateExists(s *CanaryStore, name string) bool {
	_, e := os.Stat(filepath.Join(s.root, name))
	return e == nil
}

func newFrozenEngine(ctx context.Context, store *CanaryStore, generator frozenGenerator, newCall func() (frozenCall, error)) *frozenEngine {
	e := &frozenEngine{store: store, generator: generator, newCall: newCall, ctx: ctx, summary: newFrozenSummary("NOT_CONFIGURED")}
	if privateExists(store, terminalFile) {
		raw, err := store.readFile(terminalFile, 4096)
		if err == nil {
			e.summary, err = ParseSafeSummary(raw)
		}
		if err != nil || e.summary.Frozen == nil || e.summary.Frozen.Qualification != "FAILED" || e.summary.Frozen.BinaryHash != frozenBinaryHash() {
			e.summary = e.emptyTerminal("CORRUPT")
		}
		return e
	}
	if privateExists(store, runMarkerFile) {
		// Never resume network IO after a crash or an ambiguous request. Rebuild
		// only a FAILED/INTERRUPTED aggregate from private durable envelopes.
		summary := e.recoverTerminal()
		if store.createFile(terminalFile, decision.Encode(summary)) == nil {
			e.summary = summary
		} else {
			e.summary = newFrozenSummary("BLOCKED_STORAGE")
		}
		return e
	}
	if _, err := newCall(); err == nil {
		e.summary = newFrozenSummary("READY")
	}
	return e
}

func (e *frozenEngine) snapshot() SafeSummary {
	e.mu.Lock()
	defer e.mu.Unlock()
	// Copy by value through the strict serializer, so callers cannot mutate the
	// service's stored slice or turn one polling response into a progress oracle.
	copy, err := ParseSafeSummary(decision.Encode(e.summary))
	if err != nil {
		return newFrozenSummary("NOT_CONFIGURED")
	}
	return copy
}
func (e *frozenEngine) start() SafeSummary {
	e.mu.Lock()
	if e.ctx.Err() != nil {
		e.mu.Unlock()
		return newFrozenSummary("NOT_CONFIGURED")
	}
	if e.summary.Frozen.RunState != "READY" {
		e.mu.Unlock()
		return e.snapshot()
	}
	call, err := e.newCall()
	if err != nil {
		e.summary = newFrozenSummary("NOT_CONFIGURED")
		e.mu.Unlock()
		return e.snapshot()
	}
	marker := runMarker{Schema: "researchos.frozen-run.v1", PlanHash: frozenPlanHash(), StartedAt: time.Now().UTC().Format(time.RFC3339Nano)}
	if err = e.store.createFile(runMarkerFile, decision.Encode(marker)); err != nil {
		e.summary = e.emptyTerminal("CORRUPT")
		e.mu.Unlock()
		return e.snapshot()
	}
	e.summary = newFrozenSummary("RUNNING")
	e.done = make(chan struct{})
	e.mu.Unlock()
	go func() { defer close(e.done); e.run(call) }()
	return e.snapshot()
}
func (e *frozenEngine) wait() {
	e.mu.Lock()
	done := e.done
	e.mu.Unlock()
	if done != nil {
		<-done
	}
}

func validateFrozenBatch(batch frozenBatch) error {
	if len(batch.Cases) != holdout.CaseCount || len(batch.Raw) == 0 || len(batch.Raw) > MaxBlobBytes {
		return ErrIntegrity
	}
	languages := map[string]int{}
	ids := map[string]bool{}
	for _, c := range batch.Cases {
		if c.ID == "" || ids[c.ID] || (c.Scope.Language != "zh" && c.Scope.Language != "zh-en") || c.Scope != holdout.ScopeFor(c.Scope.Language) || c.Request.Model != holdout.ModelRevision || decision.Digest(decision.Encode(c.Request.Questions)) != decision.Digest(decision.Encode(holdout.Questions())) || c.Request.Validate() != nil || (c.Expected != "ACCEPT" && c.Expected != "REJECT") || (c.Critical && c.Expected != "REJECT") {
			return ErrIntegrity
		}
		ids[c.ID] = true
		languages[c.Scope.Language]++
	}
	if languages["zh"] != 15 || languages["zh-en"] != 15 {
		return ErrIntegrity
	}
	return nil
}
func frozenBinding(c frozenCase) decision.Binding {
	return decision.Binding{ProjectID: frozenProjectID, InputHash: decision.Digest(decision.Encode(c.Request.State)), RubricHash: holdout.RubricHash(), Scope: c.Scope}
}
func intentName(i int) string   { return fmt.Sprintf("frozen-call-%02d.started.json", i) }
func envelopeName(i int) string { return fmt.Sprintf("frozen-call-%02d.envelope.json", i) }
func resultName(i int) string   { return fmt.Sprintf("frozen-call-%02d.result.json", i) }

func (e *frozenEngine) emptyTerminal(state string) SafeSummary {
	summary := newFrozenSummary("NOT_CONFIGURED")
	summary.Status = "EXECUTION_REPORTED"
	summary.Frozen.RunState = state
	summary.Frozen.Qualification = "FAILED"
	for _, language := range []string{"zh", "zh-en"} {
		dev, _ := frozenDevelopment(language)
		summary.Frozen.Keys = append(summary.Frozen.Keys, FrozenKeyCounts{Scope: holdout.ScopeFor(language), Planned: 15, Baseline: FrozenBaselineCounts{Rule: "ALWAYS_REJECT"}, DevelopmentCount: dev.Count, Development: dev})
	}
	return summary
}
func countResult(summary *SafeSummary, c frozenCase, env *decision.Envelope) {
	i := 0
	if c.Scope.Language == "zh-en" {
		i = 1
	}
	k := &summary.Frozen.Keys[i]
	k.StartedRequests++
	if c.Expected == "ACCEPT" {
		k.PositiveLabelCount++
		k.Baseline.FalseReject++
	} else {
		k.NegativeLabelCount++
		k.Baseline.Correct++
	}
	summary.Total++
	if env == nil {
		k.UnknownRequests++
		k.Abstain++
		k.Errors++
		summary.Abstain++
		return
	}
	k.RecordedInvocations++
	if env.HTTPStatus == 200 {
		k.HTTP200++
	}
	if env.LatencyMS >= 0 {
		k.LatencyMS += env.LatencyMS
	}
	result := decision.Evaluate(*env, holdout.Threshold)
	if result.Abstained || env.Binding != frozenBinding(c) || decision.Digest(decision.Encode(env.Request)) != decision.Digest(decision.Encode(c.Request)) {
		k.Abstain++
		summary.Abstain++
		if env.TransportError != "" || env.HTTPStatus != 200 || result.ModelRevision != holdout.ModelRevision || result.Usage == nil || env.Binding != frozenBinding(c) || decision.Digest(decision.Encode(env.Request)) != decision.Digest(decision.Encode(c.Request)) {
			k.Errors++
		}
		return
	}
	if result.Selected == "ACCEPT" {
		k.NonAbstainedAcceptCount++
	} else if result.Selected == "REJECT" {
		k.NonAbstainedRejectCount++
	}
	if result.Selected == c.Expected {
		k.Correct++
		summary.Correct++
	} else if result.Selected == "ACCEPT" {
		k.FalseAccept++
		summary.FalseAccept++
		if c.Critical {
			k.CriticalFalseAccept++
			summary.CriticalFalseAccept++
		}
	} else if result.Selected == "REJECT" {
		k.FalseReject++
		summary.FalseReject++
	} else {
		k.Abstain++
		k.Errors++
		summary.Abstain++
	}
}

func (e *frozenEngine) run(call frozenCall) {
	batch, err := e.generator.Generate()
	if err != nil || validateFrozenBatch(batch) != nil {
		e.finish(e.emptyTerminal("CORRUPT"))
		return
	}
	if e.store.createFile(batchFile, batch.Raw) != nil || e.store.createFile(batchCommitFile, decision.Encode(batchCommit{Hash: decision.Digest(batch.Raw)})) != nil {
		e.finish(e.emptyTerminal("CORRUPT"))
		return
	}
	summary := e.emptyTerminal("INTERRUPTED")
	if e.attachDataset(&summary, batch.Raw) != nil {
		e.finish(e.emptyTerminal("CORRUPT"))
		return
	}
	complete := true
	for i, c := range batch.Cases {
		if e.ctx.Err() != nil {
			complete = false
			break
		}
		intent := callIntent{Index: i, ID: c.ID, Language: c.Scope.Language, RequestHash: decision.Digest(decision.Encode(c.Request))}
		// createFile is CREATE_NEW plus fsync; no request is made until its one
		// budget slot is durable. A crash after this point consumes the slot.
		if e.store.createFile(intentName(i), decision.Encode(intent)) != nil {
			complete = false
			break
		}
		env, err := call(e.ctx, frozenBinding(c), c.Request)
		if err != nil {
			env = decision.Envelope{Version: 1, Binding: frozenBinding(c), Request: c.Request, RequestHash: intent.RequestHash, Response: []byte{}, ResponseHash: decision.Digest(nil), TransportError: "CALL_REJECTED", MeasurementMode: "LIVE"}
		}
		if e.store.createFile(envelopeName(i), decision.Encode(env)) != nil {
			complete = false
			countResult(&summary, c, nil)
			break
		}
		countResult(&summary, c, &env)
		// Detailed Evaluate reasons and any source echo remain private.
		if e.store.createFile(resultName(i), decision.Encode(decision.Evaluate(env, holdout.Threshold))) != nil {
			complete = false
			break
		}
	}
	if complete && summary.Total == holdout.CaseCount && e.ctx.Err() == nil && summary.Frozen.Keys[0].UnknownRequests+summary.Frozen.Keys[1].UnknownRequests == 0 {
		summary.Frozen.RunState = "COMPLETED"
	}
	e.finish(summary)
}
func (e *frozenEngine) attachDataset(summary *SafeSummary, raw []byte) error {
	markerRaw, err := e.store.readFile(runMarkerFile, 4096)
	var marker runMarker
	if err != nil || decision.Strict(markerRaw, &marker) != nil || marker.Schema != "researchos.frozen-run.v1" || marker.PlanHash != frozenPlanHash() {
		return ErrIntegrity
	}
	if _, err = time.Parse(time.RFC3339Nano, marker.StartedAt); err != nil {
		return ErrIntegrity
	}
	hash := decision.Digest(raw)
	summary.Frozen.Dataset = &Blob{Ticket: "ps1:" + hash[7:39], Project: frozenProjectID, Hash: hash, Size: int64(len(raw)), MediaType: "application/json", MeasurementMode: "LIVE"}
	summary.Frozen.FrozenAt = marker.StartedAt
	return nil
}

func (e *frozenEngine) finish(summary SafeSummary) {
	if summary.Validate() != nil || e.store.createFile(terminalFile, decision.Encode(summary)) != nil {
		e.mu.Lock()
		e.summary = newFrozenSummary("BLOCKED_STORAGE")
		e.mu.Unlock()
		return
	}
	e.mu.Lock()
	e.summary = summary
	e.mu.Unlock()
}
func (e *frozenEngine) recoverTerminal() SafeSummary {
	corrupt := e.emptyTerminal("CORRUPT")
	raw, err := e.store.readFile(runMarkerFile, 4096)
	var marker runMarker
	if err != nil || decision.Strict(raw, &marker) != nil || marker.Schema != "researchos.frozen-run.v1" || marker.PlanHash != frozenPlanHash() {
		return corrupt
	}
	raw, err = e.store.readFile(batchCommitFile, 4096)
	var commit batchCommit
	if err != nil || decision.Strict(raw, &commit) != nil {
		return corrupt
	}
	raw, err = e.store.readFile(batchFile, MaxBlobBytes)
	if err != nil || decision.Digest(raw) != commit.Hash {
		return corrupt
	}
	batch, err := e.generator.Restore(raw)
	if err != nil || validateFrozenBatch(batch) != nil {
		return corrupt
	}
	summary := e.emptyTerminal("INTERRUPTED")
	if e.attachDataset(&summary, batch.Raw) != nil {
		return corrupt
	}
	for i, c := range batch.Cases {
		if !privateExists(e.store, intentName(i)) {
			continue
		}
		raw, err = e.store.readFile(intentName(i), 4096)
		var intent callIntent
		if err != nil || decision.Strict(raw, &intent) != nil || intent != (callIntent{Index: i, ID: c.ID, Language: c.Scope.Language, RequestHash: decision.Digest(decision.Encode(c.Request))}) {
			return corrupt
		}
		if !privateExists(e.store, envelopeName(i)) {
			countResult(&summary, c, nil)
			continue
		}
		raw, err = e.store.readFile(envelopeName(i), MaxBlobBytes)
		var env decision.Envelope
		if err != nil || decision.Strict(raw, &env) != nil {
			return corrupt
		}
		countResult(&summary, c, &env)
	}
	return summary
}
