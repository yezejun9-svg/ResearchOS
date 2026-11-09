package domain

import (
	"context"
	"database/sql"
)

// BudgetUsage is a projection of the authoritative immutable ledger. Columns
// are not additive: in_flight is the unresolved issued subset of reservations.
// Unknown liabilities have no invented amount and are never included as zero.
func (s *Service) BudgetUsage(ctx context.Context, token, project, runID string) (Object, error) {
	tx, e := s.DB.BeginTx(ctx, nil)
	if e != nil {
		return nil, e
	}
	defer tx.Rollback()
	p, e := authenticate(tx, token)
	if e != nil {
		return nil, e
	}
	if !p.Allowed(project, "", runID, false) {
		return nil, Fail(403, "FORBIDDEN", "budget scope unavailable")
	}
	rows, e := tx.Query("SELECT body FROM domain_objects WHERE project=? AND kind='BudgetLedgerEntry' AND (?='' OR json_extract(body,'$.run_id')=?) ORDER BY rowid", project, runID, runID)
	if e != nil {
		return nil, e
	}
	latest := map[string]Object{}
	for rows.Next() {
		var raw string
		if e = rows.Scan(&raw); e != nil {
			rows.Close()
			return nil, e
		}
		o, e := Decode([]byte(raw))
		if e != nil {
			rows.Close()
			return nil, e
		}
		latest[Hash([]any{o["run_id"], o["provider_request_id"]})] = o
	}
	e = rows.Err()
	rows.Close()
	if e != nil {
		return nil, e
	}
	result := Object{"incurred": Empty(), "estimated": Empty(), "unknown": Empty(), "reserved": Empty(), "in_flight": Empty(), "in_flight_is_subset": true}
	for _, o := range latest {
		op := Str(o, "operation")
		switch op {
		case "RELEASE":
			continue
		case "COMMIT", "RECONCILE":
			result["incurred"] = append(Arr(result, "incurred"), o)
			continue
		case "UNKNOWN":
			result["unknown"] = append(Arr(result, "unknown"), o)
		case "RESERVE":
			result["reserved"] = append(Arr(result, "reserved"), o)
			if o["cost_basis"] == "ESTIMATE" {
				result["estimated"] = append(Arr(result, "estimated"), o)
			}
		}
		run, e := load(tx, project, "Run", Str(o, "run_id"))
		if e != nil {
			return nil, e
		}
		effect, e := latestEffect(tx, project, Str(o, "run_id"), Str(o, "provider_request_id"))
		if e != nil && e != sql.ErrNoRows {
			return nil, e
		}
		issued := e == nil && (effect["state"] == "STARTED" || effect["state"] == "UNKNOWN" || effect["state"] == "CONFIRMED") || e == sql.ErrNoRows && run["started_at"] != nil
		if issued {
			result["in_flight"] = append(Arr(result, "in_flight"), o)
		}
	}
	return result, nil
}
