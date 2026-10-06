//go:build windows

package domain

import (
	"context"
	"database/sql"
	"strings"
	"time"

	rt "researchos.local/research-os/adapters/runtime"
	"researchos.local/research-os/adapters/sources"
)

func (c *RuntimeCoordinator) researchSourceAvailable(tx *sql.Tx, project string, task Object, route RuntimeCoordinatorRoute, profile Object) bool {
	w, err := loadResearchWork(tx, project, Str(task, "id"))
	if err != nil {
		return false
	}
	for _, provider := range c.config.Providers {
		if provider.ProjectID != project || provider.RuntimeID != route.RuntimeID || provider.Purpose != task["task_type"] || provider.Capability != "SOURCE" || provider.SourceID != w.SourceID {
			continue
		}
		for _, raw := range Arr(profile, "effect_routes") {
			bound := raw.(map[string]any)
			if bound["id"] != provider.ID || bound["capability"] != "SOURCE" || bound["credential_revision"] != provider.CredentialRevision || Hash(bound["upper_bound"]) != Hash(provider.UpperBound) {
				continue
			}
			if _, _, _, err = c.researchSourceGate(tx, project, task, provider, Object{"logical_key": w.Key}); err == nil {
				return true
			}
		}
	}
	return false
}

func (c *RuntimeCoordinator) researchSourceGate(tx *sql.Tx, project string, task Object, provider RuntimeProviderRoute, payload Object) (*researchWork, Object, Object, error) {
	w, err := loadResearchWork(tx, project, Str(task, "id"))
	if err != nil {
		return nil, nil, nil, err
	}
	if w.Stage != "discovery" || provider.SourceID != w.SourceID || Hash(payload) != Hash(Object{"logical_key": w.Key}) {
		return nil, nil, nil, Fail(403, "FORBIDDEN", "SOURCE requires exact host-bound discovery work")
	}
	meta, _, err := c.service.monitorSnapshot(tx, project, Str(task, "goal_id"), true)
	if err != nil {
		return nil, nil, nil, err
	}
	if Hash(w.PlanRef) != Hash(meta["brief_ref"]) || Hash(w.InputRefs) != Hash(task["input_refs"]) {
		return nil, nil, nil, Fail(412, "STALE_INPUT", "source work binding changed")
	}
	p, err := authenticate(tx, provider.SourceToken)
	if err != nil {
		return nil, nil, nil, err
	}
	if !p.HasRole("SOURCE_ADAPTER") || !p.Allowed(project, "", "", false) {
		return nil, nil, nil, Fail(403, "FORBIDDEN", "current host source grant required")
	}
	cycle, err := load(tx, project, "ResearchCycle", w.Cycle)
	if err != nil {
		return nil, nil, nil, err
	}
	if cycle["status"] != "RUNNING" {
		return nil, nil, nil, Fail(409, "STATE_CONFLICT", "source cycle closed")
	}
	cursor, err := load(tx, project, "SourceCursor", Str(w.Parameters, "cursor_id"))
	if err != nil {
		return nil, nil, nil, err
	}
	profile := meta["profile"].(map[string]any)
	for _, raw := range Arr(profile, "source_configs") {
		config := raw.(map[string]any)
		if config["source_id"] != w.SourceID || config["enabled"] != true || Hash(config["query"]) != w.Parameters["query_hash"] {
			continue
		}
		if w.SourceReceipt == nil && Str(cursor, "opaque_cursor") != Str(w.Parameters, "page_cursor_in") {
			return nil, nil, nil, Fail(412, "STALE_INPUT", "source page position changed")
		}
		if retry := Str(cursor, "retry_after"); retry != "" && w.SourceReceipt == nil {
			after, e := time.Parse(time.RFC3339Nano, retry)
			if e != nil || time.Now().Before(after) {
				return nil, nil, nil, Fail(503, "RESOURCE_UNAVAILABLE", "source retry window is not due")
			}
		}
		if config["kind"] == "X" && (provider.BrowserActPath == "" || provider.BrowserID == "") {
			return nil, nil, nil, Fail(503, "RESOURCE_UNAVAILABLE", "authorized host X browser unavailable")
		}
		return w, config, cursor, nil
	}
	return nil, nil, nil, Fail(412, "STALE_INPUT", "current source configuration unavailable")
}

func (c *RuntimeCoordinator) brokerResearchSource(ctx context.Context, route RuntimeCoordinatorRoute, provider RuntimeProviderRoute, runID, lease string, epoch int64, frame rt.BridgeFrame, payload, intent Object) (Object, error) {
	tx, run, dispatch, err := c.dispatchGate(ctx, route, runID, lease, epoch)
	if err != nil {
		return nil, err
	}
	if _, err = c.providerRoute(tx, route, run, dispatch, frame); err != nil {
		tx.Rollback()
		return nil, err
	}
	task, err := load(tx, route.ProjectID, "Task", Str(run, "task_id"))
	if err != nil {
		tx.Rollback()
		return nil, err
	}
	w, config, cursor, err := c.researchSourceGate(tx, route.ProjectID, task, provider, payload)
	tx.Rollback()
	if err != nil {
		return nil, err
	}
	allowed := []string{}
	for _, raw := range Arr(config, "allowed_origins") {
		allowed = append(allowed, raw.(string))
	}
	var adapter sources.Adapter
	switch config["kind"] {
	case "GITHUB":
		if strings.HasPrefix(Str(config, "query"), "readme:") {
			adapter = sources.GitHubReadme{AllowedOrigins: allowed}
		} else if strings.HasPrefix(Str(config, "query"), "pr:") {
			adapter = sources.GitHubPR{AllowedOrigins: allowed}
		} else {
			adapter = sources.GitHubReleases{AllowedOrigins: allowed}
		}
	case "PAPER":
		adapter = &sources.Arxiv{AllowedOrigins: allowed}
	case "X":
		adapter = sources.XBrowser{Runner: sources.BrowserActCLI{Executable: provider.BrowserActPath}, BrowserID: provider.BrowserID}
	default:
		return nil, Fail(400, "INVALID_REQUEST", "unsupported source kind")
	}
	if c.sourceFixtureAdapter != nil {
		if provider.MeasurementMode != "FIXTURE" {
			return nil, Fail(403, "FORBIDDEN", "offline source seam is forbidden for LIVE")
		}
		adapter = c.sourceFixtureAdapter(config)
		if adapter == nil {
			return nil, Fail(503, "RESOURCE_UNAVAILABLE", "offline source fixture unavailable")
		}
	}
	return c.captureResearchSource(ctx, route, provider, runID, epoch, frame, intent, w, config, cursor, adapter)
}

func (c *RuntimeCoordinator) captureResearchSource(ctx context.Context, route RuntimeCoordinatorRoute, provider RuntimeProviderRoute, runID string, epoch int64, frame rt.BridgeFrame, intent Object, w *researchWork, config, cursor Object, adapter sources.Adapter) (Object, error) {
	from, err := time.Parse(time.RFC3339Nano, Str(w.Parameters, "window_from"))
	if err != nil {
		return nil, err
	}
	to, err := time.Parse(time.RFC3339Nano, Str(w.Parameters, "window_to"))
	if err != nil {
		return nil, err
	}
	limitValue, err := Num(w.Parameters, "limit")
	if err != nil {
		return nil, err
	}
	limit := int(limitValue)
	var receipt Object
	_, err = c.service.captureSourcePageBound(ctx, provider.SourceToken, route.ProjectID, cursor, config, from, to, limit, adapter, func(tx *sql.Tx, captured SourceCapture) error {
		// A completed old-epoch read may settle only its original durable intent.
		original, e := latestEffect(tx, route.ProjectID, runID, frame.Key)
		if e != nil {
			return e
		}
		if original["request_hash"] != intent["request_hash"] || original["reservation_id"] != intent["reservation_id"] || Hash(original["epoch"]) != Hash(epoch) || (original["state"] != "STARTED" && original["state"] != "UNKNOWN") {
			return Fail(409, "STATE_CONFLICT", "source effect binding changed")
		}
		after := cursor
		if captured.Page.Complete || captured.Page.NextCursor != "" {
			b := Object{"opaque_cursor": nullableText(captured.Page.NextCursor), "covered_until": cursor["covered_until"], "last_success_at": Now(), "retry_after": nil, "pending_window_from": from.UTC().Format(time.RFC3339Nano), "pending_window_to": to.UTC().Format(time.RFC3339Nano), "last_cycle_id": w.Cycle}
			if captured.Page.Complete {
				b["covered_until"], b["pending_window_from"], b["pending_window_to"] = to.UTC().Format(time.RFC3339Nano), nil, nil
			}
			after, e = c.service.advanceSourceCursor(tx, route.ProjectID, Str(cursor, "id"), b)
			if e != nil {
				return e
			}
		}
		// Public source adapters provide no audited billing receipt. A reservation
		// remains UNKNOWN; neither a free-looking API nor its upper bound is actual.
		sealed := Object{"project_id": route.ProjectID, "task_id": w.Task, "run_id": runID, "epoch": epoch, "effect_key": frame.Key, "request_hash": intent["request_hash"], "reservation_id": intent["reservation_id"], "manifest_ref": Ref(captured.Manifest, "Artifact"), "cursor_before_ref": Ref(cursor, "SourceCursor"), "cursor_after_ref": Ref(after, "SourceCursor"), "actual_cost": nil, "cost_basis": "UNKNOWN"}
		sealed["capture_environment"] = provider.MeasurementMode
		updated, e := tx.Exec("UPDATE research_cycle_work SET source_receipt=? WHERE project=? AND cycle=? AND logical_key=? AND source_receipt IS NULL", string(Bytes(sealed)), route.ProjectID, w.Cycle, w.Key)
		if e != nil {
			return e
		}
		if n, e := updated.RowsAffected(); e != nil || n != 1 {
			return Fail(409, "STATE_CONFLICT", "source work already has a sealed receipt")
		}
		ledger, e := load(tx, route.ProjectID, "BudgetLedgerEntry", Str(intent, "reservation_id"))
		if e != nil {
			return e
		}
		cost := Object{"policy_id": ledger["policy_id"], "run_id": runID, "operation": "UNKNOWN", "money": nil, "provider_request_id": frame.Key, "provider_event_id": "source/" + Str(captured.Manifest, "id"), "reservation_id": intent["reservation_id"], "cost_basis": "UNKNOWN", "occurred_at": Now()}
		if _, e = c.service.appendBudget(tx, route.ProjectID, cost); e != nil {
			return e
		}
		w.SourceReceipt = sealed
		cycle, e := load(tx, route.ProjectID, "ResearchCycle", w.Cycle)
		if e != nil {
			return e
		}
		candidates := Arr(cycle, "candidate_evidence_ids")
		for _, evidence := range captured.Evidence {
			candidates = mergeUnique(candidates, []any{evidence["id"]})
		}
		if Hash(candidates) != Hash(cycle["candidate_evidence_ids"]) {
			if _, e = c.service.checkpointResearchCycle(tx, route.ProjectID, w.Cycle, Object{"candidate_evidence_ids": candidates, "required_experiment_ids": cycle["required_experiment_ids"], "decision_ids": cycle["decision_ids"], "follow_up_task_ids": cycle["follow_up_task_ids"], "checkpoint_artifact_id": cycle["checkpoint_artifact_id"]}); e != nil {
				return e
			}
		}
		facts, e := c.service.researchSourceFacts(tx, route.ProjectID, w)
		if e != nil {
			return e
		}
		receipt = Object{"key": frame.Key, "epoch": epoch, "run_id": runID, "receipt_id": Str(captured.Manifest, "id"), "state": "CONFIRMED", "actual_cost": nil, "cost_basis": "UNKNOWN", "payload": facts}
		original["state"], original["receipt"] = "CONFIRMED", receipt
		return effectAppend(tx, route.ProjectID, runID, frame.Key, original)
	})
	if err != nil || receipt == nil {
		c.service.ObserveEffect(context.Background(), route.ProjectID, runID, frame.Key, "UNKNOWN", Object{"reason": "source read did not commit a complete bound receipt"})
		if err != nil {
			return nil, err
		}
		return nil, Fail(503, "RESOURCE_UNAVAILABLE", "source read unavailable; original effect remains unresolved")
	}
	c.boundary("effect_receipt_durable", intent)
	return Object{"sequence": frame.Sequence, "key": frame.Key, "state": "CONFIRMED", "payload": receipt["payload"]}, nil
}
