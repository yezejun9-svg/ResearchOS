//go:build windows

package domain

import (
	"bytes"
	"context"
	"database/sql"
	"errors"
	"io"
	"net"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"strings"
	"time"

	rt "researchos.local/research-os/adapters/runtime"
)

// RuntimeProviderRoute is host-owned and never included in a task input.
// A child requests only an ID, capability, stable logical key and JSON payload.
type RuntimeProviderRoute struct {
	ID                 string `json:"id"`
	ProjectID          string `json:"project_id"`
	RuntimeID          string `json:"runtime_id"`
	Purpose            string `json:"purpose"`
	Capability         string `json:"capability"`
	CredentialRevision string `json:"credential_revision"`
	Endpoint           string `json:"endpoint"`
	BearerToken        string `json:"bearer_token"`
	UpperBound         Object `json:"upper_bound"`
	MeasurementMode    string `json:"measurement_mode"`
}

func (c *RuntimeCoordinator) providerRoute(tx *sql.Tx, route RuntimeCoordinatorRoute, run, dispatch Object, frame rt.BridgeFrame) (RuntimeProviderRoute, error) {
	manifest := dispatch["manifest"].(map[string]any)
	admission := manifest["admission"].(map[string]any)
	profile := admission["profile"].(map[string]any)
	if admission["qualification_bootstrap"] == true {
		return RuntimeProviderRoute{}, Fail(403, "FORBIDDEN", "qualification bootstrap grants no provider authority")
	}
	if c.service.Contracts.Validate("Idempotency-Key", frame.Key) != nil {
		return RuntimeProviderRoute{}, Fail(400, "INVALID_REQUEST", "stable effect key required")
	}
	task, e := load(tx, route.ProjectID, "Task", Str(run, "task_id"))
	if e != nil {
		return RuntimeProviderRoute{}, e
	}
	for _, provider := range c.config.Providers {
		if provider.ID != frame.Route || provider.ProjectID != route.ProjectID || provider.RuntimeID != route.RuntimeID || provider.Purpose != task["task_type"] || provider.Capability != frame.Capability || provider.MeasurementMode != admission["mode"] {
			continue
		}
		bound := false
		for _, v := range Arr(profile, "effect_routes") {
			p, ok := v.(map[string]any)
			if ok && p["id"] == provider.ID && p["capability"] == provider.Capability && p["credential_revision"] == provider.CredentialRevision && Hash(p["upper_bound"]) == Hash(provider.UpperBound) {
				bound = true
			}
		}
		if !bound {
			return RuntimeProviderRoute{}, Fail(403, "FORBIDDEN", "provider differs from frozen route permission")
		}
		u, e := url.Parse(provider.Endpoint)
		if e != nil || u.User != nil || u.Fragment != "" || u.Hostname() == "" || (u.Scheme != "https" && !(u.Scheme == "http" && net.ParseIP(u.Hostname()) != nil && net.ParseIP(u.Hostname()).IsLoopback() && provider.MeasurementMode == "FIXTURE")) {
			return RuntimeProviderRoute{}, Fail(403, "FORBIDDEN", "provider endpoint requires bound TLS or local fixture")
		}
		return provider, nil
	}
	return RuntimeProviderRoute{}, Fail(403, "FORBIDDEN", "effect route not permitted for this purpose")
}

func (c *RuntimeCoordinator) brokerEffect(ctx context.Context, route RuntimeCoordinatorRoute, runID, lease string, epoch int64, bridge *rt.Bridge, frame rt.BridgeFrame) (Object, error) {
	payload, e := Decode(frame.Payload)
	if e != nil {
		return nil, Fail(400, "INVALID_REQUEST", "effect JSON object required")
	}
	tx, run, dispatch, e := c.dispatchGate(ctx, route, runID, lease, epoch)
	if e != nil {
		return nil, e
	}
	provider, e := c.providerRoute(tx, route, run, dispatch, frame)
	if e != nil {
		tx.Rollback()
		return nil, e
	}
	task, e := load(tx, route.ProjectID, "Task", Str(run, "task_id"))
	if e != nil {
		tx.Rollback()
		return nil, e
	}
	goal, e := load(tx, route.ProjectID, "Goal", Str(task, "goal_id"))
	if e != nil {
		tx.Rollback()
		return nil, e
	}
	request := Object{"route": provider.ID, "capability": provider.Capability, "credential_revision": provider.CredentialRevision, "payload": payload}
	operation, basis := "RESERVE", "UPPER_BOUND"
	var money any = provider.UpperBound
	if provider.UpperBound == nil {
		operation, basis, money = "UNKNOWN", "UNKNOWN", nil
	}
	cost := Object{"policy_id": goal["budget_policy_id"], "run_id": runID, "operation": operation, "money": money, "provider_request_id": frame.Key, "provider_event_id": "prepare/" + frame.Key, "reservation_id": nil, "cost_basis": basis, "occurred_at": run["created_at"]}
	intent, e := c.service.prepareEffectTx(tx, c.config.SchedulerToken, route.ProjectID, runID, frame.Key, request, cost)
	if e != nil {
		tx.Rollback()
		return nil, e
	}
	if e = tx.Commit(); e != nil {
		return nil, e
	}
	if intent["state"] == "CONFIRMED" || intent["state"] == "NOT_APPLIED" {
		receipt, _ := intent["receipt"].(map[string]any)
		return Object{"sequence": frame.Sequence, "key": frame.Key, "state": intent["state"], "payload": receipt["payload"]}, nil
	}
	if intent["state"] != "PREPARED" {
		return nil, Fail(409, "STATE_CONFLICT", "effect outcome unknown; retry prohibited")
	}
	tx, run, dispatch, e = c.dispatchGate(ctx, route, runID, lease, epoch)
	if e != nil {
		return nil, e
	}
	if _, e = c.providerRoute(tx, route, run, dispatch, frame); e != nil {
		tx.Rollback()
		return nil, e
	}
	intent, e = c.service.beginEffectTx(tx, c.config.SchedulerToken, route.ProjectID, runID, frame.Key)
	if e != nil {
		tx.Rollback()
		return nil, e
	}
	if e = tx.Commit(); e != nil {
		return nil, e
	}
	body := Object{"key": frame.Key, "epoch": epoch, "run_id": runID, "capability": provider.Capability, "payload": payload}
	req, e := http.NewRequestWithContext(ctx, "POST", provider.Endpoint, bytes.NewReader(Bytes(body)))
	if e != nil {
		return nil, e
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Idempotency-Key", frame.Key)
	if provider.BearerToken != "" {
		req.Header.Set("Authorization", "Bearer "+provider.BearerToken)
	}
	// No shared proxy credentials, redirects or automatic semantic retry.
	client := &http.Client{Timeout: 10 * time.Second, Transport: &http.Transport{Proxy: nil, DisableKeepAlives: true}, CheckRedirect: func(*http.Request, []*http.Request) error { return errors.New("provider redirect denied") }}
	defer client.CloseIdleConnections()
	response, e := client.Do(req)
	unknown := func(reason string) (Object, error) {
		c.service.ObserveEffect(context.Background(), route.ProjectID, runID, frame.Key, "UNKNOWN", Object{"dispatch_key": dispatch["dispatch_key"], "epoch": epoch, "reason": reason})
		return nil, Fail(409, "STATE_CONFLICT", "provider outcome UNKNOWN; query provider before recovery")
	}
	if e != nil {
		return unknown("provider transport ended without receipt")
	}
	raw, e := io.ReadAll(io.LimitReader(response.Body, 64*1024+1))
	response.Body.Close()
	if e != nil || len(raw) > 64*1024 || response.StatusCode < 200 || response.StatusCode >= 300 {
		return unknown("provider returned no bounded successful receipt")
	}
	for _, secret := range []string{provider.BearerToken, c.config.SchedulerToken, route.ExecutorToken} {
		if secret != "" && bytes.Contains(raw, []byte(secret)) {
			return unknown("provider response contained a host credential")
		}
	}
	receipt, e := Decode(raw)
	if e != nil || receipt["key"] != frame.Key || Hash(receipt["epoch"]) != Hash(epoch) || receipt["run_id"] != runID || Str(receipt, "receipt_id") == "" || (receipt["state"] != "CONFIRMED" && receipt["state"] != "NOT_APPLIED") {
		return unknown("provider receipt binding invalid")
	}
	actual, ok := receipt["actual_cost"].(map[string]any)
	if !ok || c.service.Contracts.Validate("Money", actual) != nil {
		return unknown("provider actual cost missing")
	}
	fact := Object{"version": 1, "project_id": route.ProjectID, "run_id": runID, "epoch": epoch, "dispatch_key": dispatch["dispatch_key"], "manifest_hash": dispatch["manifest_hash"], "effect_key": frame.Key, "request_hash": intent["request_hash"], "reservation_id": intent["reservation_id"], "provider_response_hash": Digest(raw), "receipt": receipt}
	if e = writeRuntimeFact(filepath.Join(bridge.Directory(), "effect-"+strings.TrimPrefix(Digest([]byte(frame.Key)), "sha256:")+".json"), Bytes(fact)); e != nil {
		return unknown("provider receipt persistence failed")
	}
	if e = c.ingestEffectFact(context.Background(), fact); e != nil {
		return nil, e
	}
	return Object{"sequence": frame.Sequence, "key": frame.Key, "state": receipt["state"], "payload": receipt["payload"]}, nil
}

func writeRuntimeFact(path string, raw []byte) error {
	temp := path + ".pending"
	f, e := os.OpenFile(temp, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if e != nil {
		return e
	}
	_, e = f.Write(raw)
	e = errors.Join(e, f.Sync(), f.Close())
	if e != nil {
		return e
	}
	if _, e = os.Stat(path); e == nil {
		old, e := os.ReadFile(path)
		if e == nil && bytes.Equal(old, raw) {
			os.Remove(temp)
			return nil
		}
		return errors.New("immutable host fact already exists")
	}
	return os.Rename(temp, path)
}

// A late receipt settles the original reservation and recorded epoch, without
// acquiring execution authority or extending any lease.
func (c *RuntimeCoordinator) ingestEffectFact(ctx context.Context, fact Object) error {
	project, run, key := Str(fact, "project_id"), Str(fact, "run_id"), Str(fact, "effect_key")
	tx, e := c.service.DB.BeginTx(ctx, nil)
	if e != nil {
		return e
	}
	defer tx.Rollback()
	if e = resourceWriteLock(tx); e != nil {
		return e
	}
	dispatch, e := runtimeDispatch(tx, project, run, fact["epoch"])
	if e != nil {
		return e
	}
	if fact["dispatch_key"] != dispatch["dispatch_key"] || fact["manifest_hash"] != dispatch["manifest_hash"] {
		return Fail(422, "GATE_FAILED", "effect receipt dispatch mismatch")
	}
	intent, e := latestEffect(tx, project, run, key)
	if e != nil {
		return e
	}
	if intent["request_hash"] != fact["request_hash"] || intent["reservation_id"] != fact["reservation_id"] || Hash(intent["epoch"]) != Hash(fact["epoch"]) {
		return Fail(422, "GATE_FAILED", "effect receipt epoch or intent mismatch")
	}
	receipt, ok := fact["receipt"].(map[string]any)
	if !ok {
		return errors.New("trusted effect receipt required")
	}
	if intent["state"] == receipt["state"] && Hash(intent["receipt"]) == Hash(receipt) {
		return nil
	}
	if intent["state"] != "STARTED" && intent["state"] != "UNKNOWN" {
		return Fail(409, "STATE_CONFLICT", "effect outcome cannot be rewritten")
	}
	ledger, e := load(tx, project, "BudgetLedgerEntry", Str(intent, "reservation_id"))
	if e != nil {
		return e
	}
	cost := Object{"policy_id": ledger["policy_id"], "run_id": run, "operation": "RECONCILE", "money": receipt["actual_cost"], "provider_request_id": key, "provider_event_id": "receipt/" + Str(receipt, "receipt_id"), "reservation_id": intent["reservation_id"], "cost_basis": "ACTUAL", "occurred_at": Now()}
	if e = c.service.Contracts.Validate("CostEntryRequest", cost); e != nil {
		return e
	}
	if _, e = c.service.appendBudget(tx, project, cost); e != nil {
		return e
	}
	intent["state"], intent["receipt"] = receipt["state"], receipt
	if e = effectAppend(tx, project, run, key, intent); e != nil {
		return e
	}
	return tx.Commit()
}
