//go:build windows

package domain

import (
	"context"
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
}

func (s *Service) RuntimeDrainSnapshot(ctx context.Context) (RuntimeDrainSnapshot, error) {
	var snap RuntimeDrainSnapshot
	queries := []struct {
		dest  *int
		query string
	}{
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
// worker or unresolved Run/effect restores scanning before returning an error.
func (c *RuntimeCoordinator) QuiesceForRelease(ctx context.Context) (RuntimeDrainSnapshot, error) {
	var snap RuntimeDrainSnapshot
	if !c.scanMu.TryLock() {
		return snap, errors.New("runtime scan busy")
	}
	defer c.scanMu.Unlock()
	if c.quiesced {
		return snap, errors.New("runtime coordinator already quiesced")
	}
	c.quiesced = true
	c.mu.Lock()
	snap.ActiveWorkers = len(c.active)
	c.mu.Unlock()
	observed, e := c.service.RuntimeDrainSnapshot(ctx)
	if e != nil {
		c.quiesced = false
		return snap, e
	}
	observed.ActiveWorkers = snap.ActiveWorkers
	if observed.ActiveRuns != 0 || observed.UnresolvedEffects != 0 || observed.UnresolvedDispatches != 0 || observed.ActiveWorkers != 0 || observed.Reservations != 0 {
		c.quiesced = false
		return observed, errors.New("runtime busy or external effect unresolved")
	}
	return observed, nil
}

func (c *RuntimeCoordinator) ResumeAfterReleaseAbort() {
	c.scanMu.Lock()
	c.quiesced = false
	c.scanMu.Unlock()
}
