//go:build windows

package domain

import (
	"context"
	"database/sql"
	"errors"
)

// RuntimeDrainSnapshot contains only host-observed counters. It is not a
// candidate acceptance receipt and never authorizes promotion.
type RuntimeDrainSnapshot struct {
	ActiveRuns           int `json:"active_runs"`
	UnresolvedEffects    int `json:"unresolved_effects"`
	UnresolvedDispatches int `json:"unresolved_dispatches"`
	ActiveWorkers        int `json:"active_workers"`
	Reservations         int `json:"reservations"`
	CheckpointBusy       int `json:"checkpoint_busy"`
	UnresolvedCommands   int `json:"unresolved_commands"`
}

func (c *RuntimeCoordinator) StartupReady() bool {
	if !c.scanMu.TryLock() {
		return false
	}
	defer c.scanMu.Unlock()
	return c.startupComplete && !c.quiesced
}

func (s *Service) RuntimeDrainSnapshot(ctx context.Context) (RuntimeDrainSnapshot, error) {
	var snap RuntimeDrainSnapshot
	queries := []struct {
		dest  *int
		query string
	}{
		{&snap.UnresolvedCommands, `SELECT (SELECT count(*) FROM client_command_queue WHERE state NOT IN ('CONSUMED','DROPPED'))+(SELECT count(*) FROM client_control_requests WHERE state<>'CONFIRMED')`},
		{&snap.ActiveRuns, `SELECT count(*) FROM domain_objects WHERE kind='Run' AND coalesce(json_extract(body,'$.status'),'UNKNOWN') NOT IN ('SETTLED','FAILED','CANCELLED')`},
		{&snap.UnresolvedEffects, `SELECT count(*) FROM resource_effects x WHERE sequence=(SELECT max(y.sequence) FROM resource_effects y WHERE y.project=x.project AND y.run=x.run AND y.effect_key=x.effect_key) AND json_extract(body,'$.state') IN ('PREPARED','STARTED','UNKNOWN')`},
		{&snap.UnresolvedDispatches, `SELECT count(*) FROM runtime_dispatches WHERE state IN ('PREPARED','STARTED','UNKNOWN')`},
		{&snap.Reservations, `SELECT count(*) FROM domain_objects x WHERE kind='BudgetLedgerEntry' AND json_extract(body,'$.operation') IN ('RESERVE','UNKNOWN') AND rowid=(SELECT max(y.rowid) FROM domain_objects y WHERE y.kind='BudgetLedgerEntry' AND y.project=x.project AND json_extract(y.body,'$.run_id')=json_extract(x.body,'$.run_id') AND json_extract(y.body,'$.provider_request_id')=json_extract(x.body,'$.provider_request_id'))`},
	}
	for _, q := range queries {
		if e := s.DB.QueryRowContext(ctx, q.query).Scan(q.dest); e != nil {
			return snap, e
		}
	}
	return snap, nil
}

// QuiesceForRelease takes the same scan mutex as every Task claim. A busy
// worker or unresolved Run/effect restores only the release-owned fence;
// managed qualification and prior admission closure remain in force.
func (c *RuntimeCoordinator) QuiesceForRelease(ctx context.Context) (RuntimeDrainSnapshot, error) {
	return c.quiesceRuntime(ctx, false)
}
func (c *RuntimeCoordinator) quiesceRuntime(ctx context.Context, desktopExit bool) (RuntimeDrainSnapshot, error) {
	var snap RuntimeDrainSnapshot
	if !c.scanMu.TryLock() {
		return snap, errors.New("runtime scan busy")
	}
	defer c.scanMu.Unlock()
	if !c.startupComplete {
		return snap, errors.New("runtime startup recovery not complete")
	}
	if c.quiesced {
		return snap, errors.New("runtime coordinator already quiesced")
	}
	c.releaseIntakeClosed = c.intakeClosed.Load()
	c.intakeClosed.Store(true)
	c.quiesced = true
	c.mu.Lock()
	snap.ActiveWorkers = len(c.active)
	c.mu.Unlock()
	observed, e := c.service.RuntimeDrainSnapshot(ctx)
	if e != nil {
		c.quiesced = false
		// A failed observation cannot establish that admission is safe.
		c.intakeClosed.Store(true)
		return snap, e
	}
	observed.ActiveWorkers = snap.ActiveWorkers
	effectiveDispatches := observed.UnresolvedDispatches
	var preparationErr error
	if desktopExit && effectiveDispatches != 0 && observed.ActiveRuns == 0 &&
		observed.UnresolvedEffects == 0 && observed.ActiveWorkers == 0 && observed.UnresolvedCommands == 0 {
		var settled int
		settled, preparationErr = c.service.stoppedHarnessPreparationsForDesktopExit(ctx, c.config.DataRoot, observed)
		if preparationErr == nil {
			effectiveDispatches -= settled
		}
	}
	accountingBlocked := observed.Reservations != 0
	var accountingErr error
	if desktopExit && preparationErr == nil && accountingBlocked && observed.ActiveRuns == 0 && observed.UnresolvedEffects == 0 && effectiveDispatches == 0 && observed.ActiveWorkers == 0 && observed.UnresolvedCommands == 0 {
		accountingErr = c.service.completedLocalUnknownCosts(ctx)
		accountingBlocked = accountingErr != nil
	}
	if desktopExit && (c.qualificationActive || c.config.ManagedStartupHold) {
		accountingBlocked = true
	}
	if observed.ActiveRuns != 0 || observed.UnresolvedEffects != 0 || effectiveDispatches != 0 || observed.ActiveWorkers != 0 || accountingBlocked || observed.UnresolvedCommands != 0 || preparationErr != nil {
		c.quiesced = false
		c.restoreIntakeAfterRelease(ctx, c.releaseIntakeClosed)
		if preparationErr != nil {
			return observed, preparationErr
		}
		if accountingErr != nil {
			return observed, accountingErr
		}
		return observed, errors.New("runtime busy or external effect unresolved")
	}
	return observed, nil
}

// Only the Desktop admission/scan fence calls this. The count is read again in
// the same read transaction as every C5 proof so a changed snapshot cannot be
// used to subtract an unrelated unresolved dispatch.
func (s *Service) stoppedHarnessPreparationsForDesktopExit(ctx context.Context, dataRoot string, observed RuntimeDrainSnapshot) (int, error) {
	tx, err := s.DB.BeginTx(ctx, &sql.TxOptions{ReadOnly: true})
	if err != nil {
		return 0, err
	}
	defer tx.Rollback()
	var total int
	if err = tx.QueryRowContext(ctx, `SELECT count(*) FROM runtime_dispatches WHERE state IN ('PREPARED','STARTED','UNKNOWN')`).Scan(&total); err != nil {
		return 0, err
	}
	if total != observed.UnresolvedDispatches {
		return 0, errors.New("desktop exit dispatch snapshot changed")
	}
	// The original snapshot is returned to callers unchanged. The decision uses
	// one transaction for all durable counters that could change its meaning.
	checks := []struct {
		query    string
		expected int
	}{
		{`SELECT count(*) FROM domain_objects WHERE kind='Run' AND coalesce(json_extract(body,'$.status'),'UNKNOWN') NOT IN ('SETTLED','FAILED','CANCELLED')`, observed.ActiveRuns},
		{`SELECT count(*) FROM resource_effects x WHERE sequence=(SELECT max(y.sequence) FROM resource_effects y WHERE y.project=x.project AND y.run=x.run AND y.effect_key=x.effect_key) AND json_extract(body,'$.state') IN ('PREPARED','STARTED','UNKNOWN')`, observed.UnresolvedEffects},
		{`SELECT (SELECT count(*) FROM client_command_queue WHERE state NOT IN ('CONSUMED','DROPPED'))+(SELECT count(*) FROM client_control_requests WHERE state<>'CONFIRMED')`, observed.UnresolvedCommands},
		{`SELECT count(*) FROM domain_objects x WHERE kind='BudgetLedgerEntry' AND json_extract(body,'$.operation') IN ('RESERVE','UNKNOWN') AND rowid=(SELECT max(y.rowid) FROM domain_objects y WHERE y.kind='BudgetLedgerEntry' AND y.project=x.project AND json_extract(y.body,'$.run_id')=json_extract(x.body,'$.run_id') AND json_extract(y.body,'$.provider_request_id')=json_extract(x.body,'$.provider_request_id'))`, observed.Reservations},
	}
	for _, check := range checks {
		var actual int
		if err = tx.QueryRowContext(ctx, check.query).Scan(&actual); err != nil {
			return 0, err
		}
		if actual != check.expected {
			return 0, errors.New("desktop exit durable drain snapshot changed")
		}
	}
	rows, err := tx.QueryContext(ctx, `SELECT project,run,epoch FROM runtime_dispatches WHERE state='STARTED' AND reason LIKE 'native preparation failed before model launch: %'`)
	if err != nil {
		return 0, err
	}
	type key struct {
		project, run string
		epoch        int64
	}
	keys := []key{}
	for rows.Next() {
		var k key
		if err = rows.Scan(&k.project, &k.run, &k.epoch); err != nil {
			rows.Close()
			return 0, err
		}
		keys = append(keys, k)
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return 0, err
	}
	for _, k := range keys {
		if err = s.stoppedHarnessPreparationInTx(tx, k.project, k.run, k.epoch, dataRoot); err != nil {
			return 0, err
		}
	}
	return len(keys), nil
}

func (c *RuntimeCoordinator) ResumeAfterReleaseAbort() {
	c.scanMu.Lock()
	defer c.scanMu.Unlock()
	wasClosed := c.intakeClosed.Load()
	if c.quiesced {
		wasClosed = c.releaseIntakeClosed
	}
	c.quiesced = false
	c.restoreIntakeAfterRelease(context.Background(), wasClosed)
}

// Caller holds scanMu, never an admission transaction. Admission reads only
// the atomic guard, so checking durable state cannot deadlock that transaction.
func (c *RuntimeCoordinator) restoreIntakeAfterRelease(ctx context.Context, wasClosed bool) {
	c.intakeClosed.Store(true)
	if wasClosed || c.qualificationActive || c.config.ManagedStartupHold {
		return
	}
	if fenced, err := c.managedQualificationUnsettled(ctx); err == nil && !fenced {
		c.intakeClosed.Store(false)
	}
}

// Called inside the admission transaction; drain closes intake before reading DB.
func (c *RuntimeCoordinator) ClientIntakeOpen() bool { return !c.intakeClosed.Load() }

// QuiesceForDesktopExit preserves UNKNOWN money. Only the private Desktop
// shutdown caller may classify a fully completed credential-free loopback
// MODEL response as safe to leave on disk; release promotion remains strict.
func (c *RuntimeCoordinator) QuiesceForDesktopExit(ctx context.Context) (RuntimeDrainSnapshot, error) {
	return c.quiesceRuntime(ctx, true)
}

func (s *Service) completedLocalUnknownCosts(ctx context.Context) error {
	tx, e := s.DB.BeginTx(ctx, nil)
	if e != nil {
		return e
	}
	defer tx.Rollback()
	rows, e := tx.QueryContext(ctx, `SELECT project,body FROM domain_objects x WHERE kind='BudgetLedgerEntry' AND json_extract(body,'$.operation') IN ('RESERVE','UNKNOWN') AND rowid=(SELECT max(y.rowid) FROM domain_objects y WHERE y.kind='BudgetLedgerEntry' AND y.project=x.project AND json_extract(y.body,'$.run_id')=json_extract(x.body,'$.run_id') AND json_extract(y.body,'$.provider_request_id')=json_extract(x.body,'$.provider_request_id'))`)
	if e != nil {
		return e
	}
	type item struct {
		project string
		ledger  Object
	}
	items := []item{}
	for rows.Next() {
		var project, raw string
		if e = rows.Scan(&project, &raw); e != nil {
			rows.Close()
			return e
		}
		ledger, err := Decode([]byte(raw))
		if err != nil {
			rows.Close()
			return err
		}
		items = append(items, item{project, ledger})
	}
	e = rows.Err()
	rows.Close()
	if e != nil {
		return e
	}
	for _, item := range items {
		if e = s.completedLocalUnknownCost(tx, item.project, item.ledger); e != nil {
			return e
		}
	}
	return nil
}
func (s *Service) completedLocalUnknownCost(tx *sql.Tx, project string, ledger Object) error {
	bad := func(reason string) error {
		return errors.New("desktop exit requires complete original local MODEL evidence: " + reason + "; cost remains unknown")
	}
	if ledger["operation"] != "UNKNOWN" || ledger["money"] != nil || ledger["cost_basis"] != "UNKNOWN" || ledger["reservation_id"] != nil {
		return bad("unknown ledger " + Str(ledger, "operation") + "/" + Str(ledger, "provider_request_id"))
	}
	run, e := load(tx, project, "Run", Str(ledger, "run_id"))
	if e != nil {
		return e
	}
	if !runTerminal(run) || run["children_stopped"] != true || run["queue_empty"] != true || Str(run, "ended_at") == "" {
		return bad("terminal run")
	}
	task, e := load(tx, project, "Task", Str(run, "task_id"))
	if e != nil {
		return e
	}
	observation, e := runtimeObservation(tx, project, run)
	if e != nil {
		return e
	}
	dispatch, e := nativeDispatchProof(tx, project, run, observation)
	if e != nil {
		return e
	}
	identity, _ := dispatch["identity"].(map[string]any)
	if observation["state"] != run["status"] || observation["children_stopped"] != true || observation["queue_empty"] != true || Str(observation, "ended") == "" || Str(dispatch, "worker") == "" || Str(dispatch, "journal_locator") != Str(dispatch, "dispatch_key") || len(identity) == 0 {
		return bad("native observation")
	}
	manifest, _ := dispatch["manifest"].(map[string]any)
	admission, _ := manifest["admission"].(map[string]any)
	profile, _ := admission["profile"].(map[string]any)
	ref, _ := admission["profile_ref"].(map[string]any)
	spec, _ := observation["spec"].(map[string]any)
	if profile == nil || ref == nil || profile["backend"] != runtimeMuBackend || validateRuntimeDispatchProfile(profile) != nil || manifest["task_id"] != task["id"] || manifest["runtime_id"] != run["runtime_id"] || manifest["executor_principal_id"] != run["executor_principal_id"] || manifest["context_bundle_id"] != run["context_bundle_id"] || Hash(manifest["input_refs"]) != Hash(run["input_refs"]) || admission["profile_hash"] != Hash(ref) || spec["profile_hash"] != Hash(ref) || spec["run_id"] != run["id"] || spec["task_id"] != task["id"] || Hash(spec["epoch"]) != Hash(run["lease_epoch"]) {
		return bad("frozen profile binding")
	}
	artifact, e := version(tx, project, ref)
	if e != nil {
		return e
	}
	frozen, e := runtimeProfileBody(tx, project, artifact)
	if e != nil {
		return e
	}
	if Hash(frozen) != Hash(profile) {
		return bad("profile bytes")
	}
	effect, e := latestEffect(tx, project, Str(run, "id"), Str(ledger, "provider_request_id"))
	if e != nil {
		return e
	}
	request, _ := effect["payload"].(map[string]any)
	receipt, _ := effect["receipt"].(map[string]any)
	config, _ := profile["model_config"].(map[string]any)
	payload, _ := request["payload"].(map[string]any)
	if effect["state"] != "CONFIRMED" || effect["project_id"] != project || effect["task_id"] != task["id"] || effect["run_id"] != run["id"] || effect["context_bundle_id"] != run["context_bundle_id"] || Hash(effect["epoch"]) != Hash(run["lease_epoch"]) || request["route"] != config["route"] || receipt["state"] != "CONFIRMED" || receipt["key"] != effect["key"] || receipt["run_id"] != run["id"] || Hash(receipt["epoch"]) != Hash(run["lease_epoch"]) || receipt["model_transport"] != true || receipt["actual_cost"] != nil {
		return bad("confirmed effect binding")
	}
	if _, e = validateRuntimeModelRequest(config, payload); e != nil {
		return e
	}
	bound := 0
	for _, v := range Arr(profile, "effect_routes") {
		route, _ := v.(map[string]any)
		if route["id"] == request["route"] && route["capability"] == "MODEL" && route["credential_revision"] == "none" && route["upper_bound"] == nil {
			bound++
		}
	}
	if bound != 1 {
		return bad("local MODEL route")
	}
	response, _ := receipt["payload"].(map[string]any)
	raw := []byte(Str(response, "body"))
	if Hash(response["status"]) != Hash(200) || response["content_type"] != "text/event-stream" || len(raw) > runtimeModelMaxSSEBytes || !completeRuntimeModelSSE(raw) || receipt["receipt_id"] != Digest(raw) {
		return bad("complete response")
	}
	// All append-only stages must bind the same exact request and liability.
	rows, e := tx.Query(`SELECT body FROM resource_effects WHERE project=? AND run=? AND effect_key=? ORDER BY sequence`, project, run["id"], effect["key"])
	if e != nil {
		return e
	}
	history := []Object{}
	for rows.Next() {
		var raw string
		if e = rows.Scan(&raw); e != nil {
			rows.Close()
			return e
		}
		o, err := Decode([]byte(raw))
		if err != nil {
			rows.Close()
			return err
		}
		history = append(history, o)
	}
	e = rows.Err()
	rows.Close()
	if e != nil {
		return e
	}
	if len(history) < 3 || history[0]["state"] != "PREPARED" || history[1]["state"] != "STARTED" {
		return bad("effect history stages")
	}
	for i, h := range history {
		n, err := Num(h, "sequence")
		if err != nil || n != int64(i+1) || h["request_hash"] != effect["request_hash"] || h["reservation_id"] != effect["reservation_id"] || Hash(h["payload"]) != Hash(request) || Hash(h["epoch"]) != Hash(effect["epoch"]) {
			return bad("effect history binding")
		}
	}
	goal, e := load(tx, project, "Goal", Str(task, "goal_id"))
	if e != nil {
		return e
	}
	policies, leaves, e := runBudgetScopes(tx, project, Str(run, "id"))
	if e != nil {
		return e
	}
	values := Empty()
	for _, p := range policies {
		values = append(values, p)
	}
	rows, e = tx.Query(`SELECT body FROM domain_objects WHERE project=? AND kind='BudgetLedgerEntry' AND json_extract(body,'$.run_id')=?`, project, run["id"])
	if e != nil {
		return e
	}
	ledgers := Empty()
	for rows.Next() {
		var raw string
		if e = rows.Scan(&raw); e != nil {
			rows.Close()
			return e
		}
		o, err := Decode([]byte(raw))
		if err != nil {
			rows.Close()
			return err
		}
		ledgers = append(ledgers, o)
	}
	e = rows.Err()
	rows.Close()
	if e != nil {
		return e
	}
	mu := Object{"profile": profile, "ledger": ledgers, "unknown_budget": Object{"goal": goal, "policies": values, "leaves": leaves}}
	if reason := verifyMuUnknownBudget(mu, task, run, request, effect, ledger); reason != "" {
		return errors.New(reason)
	}
	return nil
}
