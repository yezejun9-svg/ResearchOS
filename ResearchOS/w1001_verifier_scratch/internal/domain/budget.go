package domain

import (
	"database/sql"
	"math/big"
	"strings"
	"time"
)

var resourceOperations = map[string]bool{}

func init() {
	for _, id := range strings.Fields("appendBudgetLedger listBudgetLedgerEntry getBudgetLedgerEntry updateBudgetPolicy updateGlobalBudgetPolicy updateGoalBudgetPolicy updateExperimentBudgetPolicy getExperimentBudgetPolicy updateRunPolicy updateGlobalRunPolicy") {
		resourceOperations[id] = true
		implemented[id] = true
	}
}

func (s *Service) resourcePolicyTarget(tx *sql.Tx, project, id, op string, b Object) (Object, error) {
	kind := "BudgetPolicy"
	if strings.Contains(op, "RunPolicy") {
		kind = "RunPolicy"
	}
	if op == "appendBudgetLedger" {
		return load(tx, project, kind, Str(b, "policy_id"))
	}
	if strings.Contains(op, "Global") {
		return singleton(tx, "", kind)
	}
	parent := "ProjectProfile"
	if strings.Contains(op, "Goal") {
		parent = "Goal"
	}
	if strings.Contains(op, "Experiment") {
		parent = "Experiment"
	}
	var o Object
	var e error
	if parent == "ProjectProfile" {
		o, e = singleton(tx, project, parent)
	} else {
		o, e = load(tx, project, parent, id)
	}
	if e != nil {
		return nil, e
	}
	field := "budget_policy_id"
	if kind == "RunPolicy" {
		field = "run_policy_id"
	}
	return load(tx, project, kind, Str(o, field))
}

func (s *Service) resourceOperation(tx *sql.Tx, p Principal, project, id string, b Object, op string) (Object, string, int, error) {
	if op == "advanceNoProgress" {
		o, e := s.advanceNoProgress(tx, p, project, id, b)
		return o, "NoProgressRecord", 200, e
	}
	if op == "createResourceRequest" {
		o, e := s.createResourceRequest(tx, project, b)
		return o, "ResourceRequest", 201, e
	}
	if op == "resolveResourceRequest" {
		o, e := s.resolveResourceRequest(tx, p, project, id, b)
		return o, "ResourceRequest", 200, e
	}
	if op == "appendBudgetLedger" {
		o, e := s.appendBudget(tx, project, b)
		return o, "BudgetLedgerEntry", 201, e
	}
	kind := "BudgetPolicy"
	if strings.Contains(op, "RunPolicy") {
		kind = "RunPolicy"
	}
	o, e := s.resourcePolicyTarget(tx, project, id, op, b)
	if e != nil {
		return nil, kind, 200, e
	}
	if strings.HasPrefix(op, "update") {
		if kind == "BudgetPolicy" && b["cap"] != nil {
			if _, e = moneyAmount(b["cap"]); e != nil {
				return nil, kind, 200, e
			}
		}
		Merge(o, b)
		if e = bump(o); e == nil {
			e = s.put(tx, kind, o)
		}
		if e == nil {
			e = s.resourcePolicyChanged(tx, p, project)
		}
	}
	return o, kind, 200, e
}

// math/big uses integer numerators and denominators; arbitrary decimal precision
// is preserved without float conversion, rounding, overflow or currency exchange.
func moneyAmount(v any) (*big.Rat, error) {
	m, ok := v.(map[string]any)
	if !ok {
		return nil, Fail(422, "GATE_FAILED", "money required")
	}
	if len(Str(m, "amount")) > 4096 {
		return nil, Fail(422, "GATE_FAILED", "decimal amount too large")
	}
	n, ok := new(big.Rat).SetString(Str(m, "amount"))
	if !ok || n.Sign() < 0 {
		return nil, Fail(422, "GATE_FAILED", "nonnegative decimal amount required")
	}
	return n, nil
}

func budgetChain(tx *sql.Tx, project, id string) ([]Object, error) {
	out := []Object{}
	seen := map[string]bool{}
	for id != "" {
		if seen[id] {
			return nil, Fail(422, "GATE_FAILED", "budget ancestry cycle")
		}
		seen[id] = true
		o, e := load(tx, project, "BudgetPolicy", id)
		if e != nil {
			o, e = load(tx, "", "BudgetPolicy", id)
		}
		if e != nil {
			return nil, e
		}
		effective, e := time.Parse(time.RFC3339Nano, Str(o, "effective_from"))
		if e != nil {
			return nil, e
		}
		if effective.After(time.Now()) {
			rows, e := tx.Query("SELECT body FROM domain_versions WHERE project=? AND kind='BudgetPolicy' AND id=? ORDER BY revision DESC", Str(o, "project_id"), id)
			if e != nil {
				return nil, e
			}
			var active Object
			for rows.Next() {
				var raw string
				if e = rows.Scan(&raw); e != nil {
					rows.Close()
					return nil, e
				}
				v, e := Decode([]byte(raw))
				if e != nil {
					rows.Close()
					return nil, e
				}
				at, e := time.Parse(time.RFC3339Nano, Str(v, "effective_from"))
				if e != nil {
					rows.Close()
					return nil, e
				}
				if !at.After(time.Now()) {
					active = v
					break
				}
			}
			e = rows.Err()
			rows.Close()
			if e != nil {
				return nil, e
			}
			if active == nil {
				return nil, Fail(422, "GATE_FAILED", "no budget policy is effective yet")
			}
			o = active
		}
		out = append(out, o)
		id = Str(o, "parent_policy_id")
	}
	return out, nil
}

func policyWindow(p Object, at time.Time) (time.Time, error) {
	loc, e := time.LoadLocation(Str(p, "timezone"))
	if e != nil {
		return time.Time{}, e
	}
	v := at.In(loc)
	switch p["period"] {
	case "DAILY":
		return time.Date(v.Year(), v.Month(), v.Day(), 0, 0, 0, 0, loc), nil
	case "MONTHLY":
		return time.Date(v.Year(), v.Month(), 1, 0, 0, 0, 0, loc), nil
	}
	return time.Time{}, nil
}

// Exposure is derived from immutable ledger entries, never a second balance.
// ponytail: scans retained ledger rows; add a rebuildable indexed projection if measured ledger size requires it.
// Settled requests replace reservations; UNKNOWN remains an unresolved liability.
func budgetExposure(tx *sql.Tx, p Object, currency string) (*big.Rat, bool, error) {
	rows, e := tx.Query("SELECT body FROM domain_objects WHERE kind='BudgetLedgerEntry' ORDER BY rowid")
	if e != nil {
		return nil, false, e
	}
	entries := []Object{}
	for rows.Next() {
		var raw string
		if e = rows.Scan(&raw); e != nil {
			rows.Close()
			return nil, false, e
		}
		o, err := Decode([]byte(raw))
		if err != nil {
			rows.Close()
			return nil, false, err
		}
		entries = append(entries, o)
	}
	e = rows.Err()
	rows.Close()
	if e != nil {
		return nil, false, e
	}
	window, e := policyWindow(p, time.Now())
	if e != nil {
		return nil, false, e
	}
	groups := map[string][]Object{}
	for _, o := range entries {
		chain, _, e := runBudgetScopes(tx, Str(o, "project_id"), Str(o, "run_id"))
		if e != nil {
			return nil, false, e
		}
		applies := false
		for _, a := range chain {
			if a["id"] == p["id"] {
				applies = true
			}
		}
		if applies {
			k := Hash([]any{o["project_id"], o["run_id"], o["provider_request_id"]})
			groups[k] = append(groups[k], o)
		}
	}
	total := new(big.Rat)
	unknown := false
	for _, group := range groups {
		last := group[len(group)-1]
		first := group[0]
		at, e := time.Parse(time.RFC3339Nano, Str(first, "created_at"))
		if e != nil {
			return nil, false, e
		}
		if at.Before(window) && (last["operation"] == "COMMIT" || last["operation"] == "RECONCILE" || last["operation"] == "RELEASE") {
			continue
		}
		if last["operation"] == "RELEASE" {
			continue
		}
		if last["operation"] == "UNKNOWN" {
			unknown = true
			continue
		}
		money := last["money"].(map[string]any)
		if money["currency"] != currency {
			return nil, false, Fail(422, "GATE_FAILED", "explicit exchange policy unavailable")
		}
		n, e := moneyAmount(money)
		if e != nil {
			return nil, false, e
		}
		total.Add(total, n)
	}
	return total, unknown, nil
}

func (s *Service) appendBudget(tx *sql.Tx, project string, b Object) (Object, error) {
	if e := s.Contracts.Validate("CostEntryRequest", b); e != nil {
		return nil, Fail(400, "INVALID_REQUEST", "invalid ledger request")
	}
	var prior string
	e := tx.QueryRow("SELECT body FROM domain_objects WHERE project=? AND kind='BudgetLedgerEntry' AND json_extract(body,'$.provider_event_id')=?", project, b["provider_event_id"]).Scan(&prior)
	if e == nil {
		o, e := Decode([]byte(prior))
		if e != nil {
			return nil, e
		}
		payload := Object{}
		for k := range b {
			payload[k] = o[k]
		}
		if Hash(payload) != Hash(b) {
			return nil, Fail(409, "IDEMPOTENCY_CONFLICT", "provider event payload changed")
		}
		return o, nil
	}
	if e != sql.ErrNoRows {
		return nil, e
	}
	run, e := load(tx, project, "Run", Str(b, "run_id"))
	if e != nil {
		return nil, e
	}
	chain, leaves, e := runBudgetScopes(tx, project, Str(run, "id"))
	if e != nil {
		return nil, e
	}
	leaf := Str(b, "policy_id")
	if !leaves[leaf] {
		return nil, Fail(422, "GATE_FAILED", "ledger requires a run-bound budget scope")
	}
	op := Str(b, "operation")
	basis := Str(b, "cost_basis")
	if op == "UNKNOWN" {
		if b["money"] != nil || basis != "UNKNOWN" {
			return nil, Fail(422, "GATE_FAILED", "unknown must remain null")
		}
	} else {
		if _, e = moneyAmount(b["money"]); e != nil {
			return nil, e
		}
	}
	var count int
	if e = tx.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='BudgetLedgerEntry' AND json_extract(body,'$.run_id')=? AND json_extract(body,'$.provider_request_id')=?", project, run["id"], b["provider_request_id"]).Scan(&count); e != nil {
		return nil, e
	}
	if op == "RESERVE" || op == "UNKNOWN" && count == 0 {
		task, e := load(tx, project, "Task", Str(run, "task_id"))
		if e != nil {
			return nil, e
		}
		goal, e := load(tx, project, "Goal", Str(task, "goal_id"))
		if e != nil {
			return nil, e
		}
		if goal["status"] != "ACTIVE" || task["active_run_id"] != run["id"] {
			return nil, Fail(409, "STATE_CONFLICT", "paused or superseded run cannot create liabilities")
		}
		if runTerminal(run) || run["status"] == "CANCEL_REQUESTED" {
			return nil, Fail(409, "STATE_CONFLICT", "new liability forbidden after stop")
		}
		if count != 0 || b["reservation_id"] != nil {
			return nil, Fail(409, "STATE_CONFLICT", "request already admitted")
		}
		if op == "RESERVE" && basis != "UPPER_BOUND" && basis != "ESTIMATE" {
			return nil, Fail(422, "GATE_FAILED", "reservation requires cost bound or estimate")
		}
		for _, p := range chain {
			effective, e := time.Parse(time.RFC3339Nano, Str(p, "effective_from"))
			if e != nil {
				return nil, e
			}
			if effective.After(time.Now()) {
				return nil, Fail(422, "GATE_FAILED", "future policy requires prior effective revision")
			}
			if p["mode"] != "CAPPED" {
				continue
			}
			if op == "UNKNOWN" {
				if p["enforcement"] == "STRICT" || p["unknown_cost_action"] == "BLOCK" {
					return nil, Fail(422, "GATE_FAILED", "bounded cost cannot be established")
				}
				continue
			}
			if p["enforcement"] == "STRICT" && basis != "UPPER_BOUND" {
				return nil, Fail(422, "GATE_FAILED", "bounded cost cannot be established")
			}
			cap := p["cap"].(map[string]any)
			money := b["money"].(map[string]any)
			if cap["currency"] != money["currency"] {
				return nil, Fail(422, "GATE_FAILED", "currency conversion is not authorized")
			}
			used, unknown, e := budgetExposure(tx, p, Str(cap, "currency"))
			if e != nil {
				return nil, e
			}
			if unknown && (p["enforcement"] == "STRICT" || p["unknown_cost_action"] == "BLOCK") {
				return nil, Fail(422, "GATE_FAILED", "unresolved cost prevents bounded admission")
			}
			n, _ := moneyAmount(money)
			limit, _ := moneyAmount(cap)
			if used.Add(used, n).Cmp(limit) > 0 {
				return nil, Fail(422, "GATE_FAILED", "budget exhausted")
			}
		}
	} else {
		reservation, e := load(tx, project, "BudgetLedgerEntry", Str(b, "reservation_id"))
		if e != nil {
			return nil, e
		}
		if reservation["reservation_id"] != nil || reservation["run_id"] != run["id"] || reservation["provider_request_id"] != b["provider_request_id"] || reservation["policy_id"] != leaf || (reservation["operation"] != "RESERVE" && reservation["operation"] != "UNKNOWN") {
			return nil, Fail(422, "GATE_FAILED", "settlement must bind original reservation and run")
		}
		var terminal int
		if e = tx.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='BudgetLedgerEntry' AND json_extract(body,'$.run_id')=? AND json_extract(body,'$.provider_request_id')=? AND json_extract(body,'$.operation') IN ('COMMIT','RECONCILE','RELEASE')", project, run["id"], b["provider_request_id"]).Scan(&terminal); e != nil {
			return nil, e
		}
		if terminal != 0 && op != "RECONCILE" {
			return nil, Fail(409, "STATE_CONFLICT", "request already settled")
		}
		if op != "UNKNOWN" && basis != "ACTUAL" {
			return nil, Fail(422, "GATE_FAILED", "settlement requires actual cost")
		}
		if reservation["money"] != nil && b["money"] != nil && reservation["money"].(map[string]any)["currency"] != b["money"].(map[string]any)["currency"] {
			return nil, Fail(422, "GATE_FAILED", "settlement currency differs")
		}
	}
	o := Merge(Base(project), b)
	delete(o, "updated_at")
	o["receipt_hash"] = Receipt(o)
	return o, s.put(tx, "BudgetLedgerEntry", o)
}
