package domain

import (
	"database/sql"
	"encoding/json"
	"errors"
	"time"
)

var researchOperations = map[string]bool{
	"createResearchCycle": true, "checkpointResearchCycle": true, "closeResearchCycle": true,
}

func init() {
	for name := range researchOperations {
		implemented[name] = true
	}
	implemented["getResearchCycle"] = true
	implemented["listResearchCycle"] = true
}

func (s *Service) researchOperation(tx *sql.Tx, p Principal, project, id string, b Object, op string) (Object, string, int, error) {
	switch op {
	case "createResearchCycle":
		state, err := singleton(tx, project, "ProjectState")
		if err != nil {
			return nil, "", 0, err
		}
		if active := Str(state, "active_cycle_id"); active != "" {
			o, err := load(tx, project, "ResearchCycle", active)
			return o, "", 200, err
		}
		o, err := s.createResearchCycle(tx, p, project, b)
		return o, "ResearchCycle", 201, err
	case "checkpointResearchCycle":
		o, err := s.checkpointResearchCycle(tx, project, id, b)
		return o, "ResearchCycle", 200, err
	case "closeResearchCycle":
		o, err := s.closeResearchCycle(tx, project, id, b)
		return o, "ResearchCycle", 200, err
	}
	return nil, "", 0, Fail(503, "RESOURCE_UNAVAILABLE", "research operation unavailable")
}

func parseCycleWindow(from, to string) (time.Time, time.Time, error) {
	a, e1 := time.Parse(time.RFC3339Nano, from)
	b, e2 := time.Parse(time.RFC3339Nano, to)
	if e1 != nil || e2 != nil || !a.Before(b) || b.After(time.Now().Add(time.Minute)) {
		return a, b, Fail(400, "INVALID_REQUEST", "bounded past research window required")
	}
	return a, b, nil
}

func (s *Service) createResearchCycle(tx *sql.Tx, p Principal, project string, b Object) (Object, error) {
	state, err := singleton(tx, project, "ProjectState")
	if err != nil {
		return nil, err
	}
	if active := Str(state, "active_cycle_id"); active != "" {
		// Coalesced triggers never create another active cycle.
		return load(tx, project, "ResearchCycle", active)
	}
	profile, err := singleton(tx, project, "ProjectProfile")
	if err != nil {
		return nil, err
	}
	if profile["revision"] != b["profile_revision"] {
		return nil, Fail(412, "STALE_REVISION", "project profile changed")
	}
	from, to, err := parseCycleWindow(Str(b, "window_from"), Str(b, "window_to"))
	if err != nil {
		return nil, err
	}
	policy, err := load(tx, project, "RunPolicy", Str(profile, "run_policy_id"))
	if err != nil {
		return nil, err
	}
	period, _ := Num(policy, "monitor_period_seconds")
	lookback, _ := Num(policy, "first_lookback_seconds")
	if b["trigger"] == "SCHEDULE" {
		var previous string
		err = tx.QueryRow("SELECT body FROM domain_objects WHERE project=? AND kind='ResearchCycle' ORDER BY created_at DESC LIMIT 1", project).Scan(&previous)
		if err == nil {
			last, e := Decode([]byte(previous))
			if e != nil {
				return nil, e
			}
			end, e := time.Parse(time.RFC3339Nano, Str(last, "window_to"))
			if e != nil {
				return nil, e
			}
			if to.Before(end.Add(time.Duration(period) * time.Second)) {
				return nil, Fail(409, "STATE_CONFLICT", "next scheduled cycle is not due")
			}
			from = end // All missed ticks are one window, never many cycles.
		} else if errors.Is(err, sql.ErrNoRows) {
			from = to.Add(-time.Duration(lookback) * time.Second)
		} else {
			return nil, err
		}
	}
	if !from.Before(to) {
		return nil, Fail(409, "STATE_CONFLICT", "research window did not advance")
	}
	coverage, err := s.researchCoverage(tx, project, profile, from, to)
	if err != nil {
		return nil, err
	}
	o := Merge(Base(project), Object{"profile_ref": Ref(profile, "ProjectProfile"), "status": "RUNNING", "trigger": b["trigger"],
		"window_from": from.UTC().Format(time.RFC3339Nano), "window_to": to.UTC().Format(time.RFC3339Nano),
		"source_coverage": coverage, "candidate_evidence_ids": Empty(), "required_experiment_ids": Empty(), "decision_ids": Empty(),
		"follow_up_task_ids": Empty(), "checkpoint_artifact_id": nil, "outcome_summary": nil, "started_at": Now(), "closed_at": nil})
	if err = s.put(tx, "ResearchCycle", o); err != nil {
		return nil, err
	}
	if err = bump(state); err != nil {
		return nil, err
	}
	state["active_cycle_id"] = o["id"]
	if err = s.put(tx, "ProjectState", state); err != nil {
		return nil, err
	}
	for _, raw := range coverage {
		c := raw.(map[string]any)
		if c["required"] != true || c["status"] != "NOT_CONFIGURED" {
			continue
		}
		request := Object{"category": "CREDENTIAL", "account_ref": nil, "reason_code": "RESEARCH_SOURCE_NOT_CONFIGURED:" + Str(c, "source_id"),
			"summary": "Required research source is not configured", "blocked_task_ids": Empty(), "continuable_task_ids": Empty(),
			"completed_artifact_refs": Empty(), "requested_capability": "Configure source " + Str(c, "source_id"),
			"estimated_cost": nil, "cost_known": false, "resume_checkpoint_ref": nil}
		resource, requestErr := s.createResourceRequest(tx, project, request)
		if requestErr != nil {
			return nil, requestErr
		}
		if err = s.event(tx, project, "ResourceRequest", resource, p.ID, ID(), "RESOURCE_REQUESTED"); err != nil {
			return nil, err
		}
	}
	return o, nil
}

func (s *Service) researchCoverage(tx *sql.Tx, project string, profile Object, from, to time.Time) ([]any, error) {
	out := Empty()
	kinds := map[string]bool{}
	for _, raw := range Arr(profile, "source_configs") {
		config := raw.(map[string]any)
		kind, sourceID := Str(config, "kind"), Str(config, "source_id")
		kinds[kind] = true
		c := Object{"source_id": sourceID, "required": config["required"], "status": "PARTIAL",
			"requested_from": from.UTC().Format(time.RFC3339Nano), "requested_to": to.UTC().Format(time.RFC3339Nano),
			"observed_from": nil, "observed_to": nil, "record_count": 0, "gap_reason": "source window has no verified complete page", "cursor_id": nil}
		if config["enabled"] != true {
			c["status"], c["gap_reason"] = "NOT_CONFIGURED", "source disabled"
			out = append(out, c)
			continue
		}
		var rawCursor string
		err := tx.QueryRow("SELECT body FROM domain_objects WHERE project=? AND kind='SourceCursor' AND json_extract(body,'$.source_id')=?", project, sourceID).Scan(&rawCursor)
		if err != nil {
			return nil, err
		}
		cursor, err := Decode([]byte(rawCursor))
		if err != nil {
			return nil, err
		}
		c["cursor_id"] = cursor["id"]
		if cursor["query_hash"] != Hash(config["query"]) {
			c["status"], c["gap_reason"] = "PARTIAL", "source query changed"
			out = append(out, c)
			continue
		}
		if retry := Str(cursor, "retry_after"); retry != "" {
			wait, err := time.Parse(time.RFC3339Nano, retry)
			if err != nil {
				return nil, err
			}
			if time.Now().Before(wait) {
				c["status"], c["gap_reason"] = "RATE_LIMITED", "retry after "+retry
				out = append(out, c)
				continue
			}
		}
		// Only W07's durable raw page chain can prove a covered window.
		var refs string
		err = tx.QueryRow("SELECT item_refs_json FROM source_pages WHERE project=? AND cursor_id=? AND query_hash=? AND window_from<=? AND window_to>=? AND complete=1 ORDER BY window_from DESC LIMIT 1", project, cursor["id"], cursor["query_hash"], c["requested_from"], c["requested_to"]).Scan(&refs)
		if err != nil && !errors.Is(err, sql.ErrNoRows) {
			return nil, err
		}
		end, _ := time.Parse(time.RFC3339Nano, Str(cursor, "covered_until"))
		if err == nil && !end.Before(to) && cursor["last_success_at"] != nil {
			var ids []string
			if e := json.Unmarshal([]byte(refs), &ids); e != nil {
				return nil, e
			}
			c["status"], c["observed_from"], c["observed_to"], c["record_count"], c["gap_reason"] = "COMPLETE", c["requested_from"], c["requested_to"], len(ids), nil
		} else if kind == "X" {
			c["gap_reason"] = "X visible observations do not prove a complete bounded window"
		}
		out = append(out, c)
	}
	for _, kind := range []string{"GITHUB", "X", "PAPER"} {
		if kinds[kind] {
			continue
		}
		out = append(out, Object{"source_id": "missing:" + kind, "required": true, "status": "NOT_CONFIGURED", "requested_from": from.UTC().Format(time.RFC3339Nano),
			"requested_to": to.UTC().Format(time.RFC3339Nano), "observed_from": nil, "observed_to": nil, "record_count": 0,
			"gap_reason": "required source absent from project profile", "cursor_id": nil})
	}
	return out, nil
}

func (s *Service) checkpointResearchCycle(tx *sql.Tx, project, id string, b Object) (Object, error) {
	o, err := load(tx, project, "ResearchCycle", id)
	if err != nil {
		return nil, err
	}
	if o["status"] != "RUNNING" {
		return nil, Fail(409, "STATE_CONFLICT", "cycle is not running")
	}
	profile, err := version(tx, project, o["profile_ref"].(map[string]any))
	if err != nil {
		return nil, err
	}
	current, err := singleton(tx, project, "ProjectProfile")
	if err != nil {
		return nil, err
	}
	if current["revision"] != profile["revision"] {
		return nil, Fail(412, "STALE_INPUT", "project profile changed")
	}
	from, to, err := parseCycleWindow(Str(o, "window_from"), Str(o, "window_to"))
	if err != nil {
		return nil, err
	}
	coverage, err := s.researchCoverage(tx, project, profile, from, to)
	if err != nil {
		return nil, err
	}
	if err = s.validateCycleCheckpoint(tx, project, id, b); err != nil {
		return nil, err
	}
	if err = bump(o); err != nil {
		return nil, err
	}
	for _, key := range []string{"candidate_evidence_ids", "required_experiment_ids", "decision_ids", "follow_up_task_ids", "checkpoint_artifact_id"} {
		o[key] = b[key]
	}
	o["source_coverage"] = coverage // Caller claims never replace W07 page evidence.
	return o, s.put(tx, "ResearchCycle", o)
}

func (s *Service) validateCycleCheckpoint(tx *sql.Tx, project, id string, b Object) error {
	seen := map[string]bool{}
	for _, spec := range []struct{ field, kind string }{{"candidate_evidence_ids", "Evidence"}, {"required_experiment_ids", "Experiment"}, {"decision_ids", "DecisionReceipt"}, {"follow_up_task_ids", "Task"}} {
		for _, raw := range Arr(b, spec.field) {
			key := spec.kind + ":" + raw.(string)
			if seen[key] {
				return Fail(422, "GATE_FAILED", "duplicate cycle reference")
			}
			seen[key] = true
			obj, err := load(tx, project, spec.kind, raw.(string))
			if err != nil {
				return err
			}
			if spec.kind == "Experiment" && obj["cycle_id"] != id {
				return Fail(422, "GATE_FAILED", "experiment belongs to another cycle")
			}
			if spec.kind == "Evidence" && obj["validity"] != "CURRENT" {
				return Fail(422, "GATE_FAILED", "candidate evidence is no longer current")
			}
		}
	}
	if raw := Str(b, "checkpoint_artifact_id"); raw != "" {
		artifact, err := load(tx, project, "Artifact", raw)
		if err != nil {
			return err
		}
		if artifact["validity"] != "CURRENT" {
			return Fail(422, "GATE_FAILED", "checkpoint artifact unavailable")
		}
	}
	return nil
}

func (s *Service) closeResearchCycle(tx *sql.Tx, project, id string, b Object) (Object, error) {
	o, err := load(tx, project, "ResearchCycle", id)
	if err != nil {
		return nil, err
	}
	if o["status"] != "RUNNING" {
		return nil, Fail(409, "STATE_CONFLICT", "cycle already closed")
	}
	state, err := singleton(tx, project, "ProjectState")
	if err != nil {
		return nil, err
	}
	if state["active_cycle_id"] != id {
		return nil, Fail(409, "STATE_CONFLICT", "cycle is not active")
	}
	profile, err := version(tx, project, o["profile_ref"].(map[string]any))
	if err != nil {
		return nil, err
	}
	current, err := singleton(tx, project, "ProjectProfile")
	if err != nil {
		return nil, err
	}
	if current["revision"] != profile["revision"] {
		return nil, Fail(412, "STALE_INPUT", "project profile changed")
	}
	from, to, err := parseCycleWindow(Str(o, "window_from"), Str(o, "window_to"))
	if err != nil {
		return nil, err
	}
	coverage, err := s.researchCoverage(tx, project, profile, from, to)
	if err != nil {
		return nil, err
	}
	complete, progress := true, false
	for _, raw := range coverage {
		c := raw.(map[string]any)
		if c["status"] == "COMPLETE" {
			progress = true
		}
		if c["required"] == true && c["status"] != "COMPLETE" {
			complete = false
		}
	}
	for _, raw := range Arr(o, "required_experiment_ids") {
		x, err := load(tx, project, "Experiment", raw.(string))
		if err != nil {
			return nil, err
		}
		if x["cycle_id"] != id || (x["status"] != "COMPLETED" && x["status"] != "INCONCLUSIVE") || x["acceptance_id"] == nil {
			complete = false
		} else {
			progress = true
		}
	}
	for _, raw := range Arr(o, "candidate_evidence_ids") {
		var count int
		if err := tx.QueryRow("SELECT count(*) FROM research_candidate_reviews WHERE project=? AND cycle_id=? AND evidence_id=?", project, id, raw).Scan(&count); err != nil {
			return nil, err
		}
		if count != 1 {
			complete = false
		} else {
			progress = true
		}
	}
	if len(Arr(o, "decision_ids")) > 0 || o["checkpoint_artifact_id"] != nil {
		progress = true
	}
	actual := "COMPLETE"
	if !complete {
		actual = "PARTIAL"
		if !progress {
			actual = "BLOCKED"
		}
	}
	if b["requested_status"] == "CANCELLED" {
		actual = "CANCELLED"
	}
	if b["requested_status"] != actual {
		return nil, Fail(422, "GATE_FAILED", "requested cycle status differs from verified coverage and experiments: "+actual)
	}
	if err = bump(o); err != nil {
		return nil, err
	}
	o["source_coverage"], o["status"], o["outcome_summary"], o["closed_at"] = coverage, actual, b["outcome_summary"], Now()
	if err = s.put(tx, "ResearchCycle", o); err != nil {
		return nil, err
	}
	if err = bump(state); err != nil {
		return nil, err
	}
	state["active_cycle_id"] = nil
	if err = s.put(tx, "ProjectState", state); err != nil {
		return nil, err
	}
	return o, nil
}
