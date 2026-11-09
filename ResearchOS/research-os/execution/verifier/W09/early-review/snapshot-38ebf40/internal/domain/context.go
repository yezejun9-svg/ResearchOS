package domain

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"sort"
	"strings"
)

var contextOperations = map[string]bool{}

func init() {
	for _, name := range strings.Fields("createContextBundle getContextBundle listContextBundle createChangeProposal getChangeProposal listChangeProposal applyChangeProposal createImpactLink getImpactLink listImpactLink createConflict getConflict listConflict resolveConflict sendAgentMessage getAgentMessage listAgentMessage recordDecision getDecisionReceipt listDecisionReceipt recordAcceptance getAcceptanceReceipt listAcceptanceReceipt") {
		implemented[name] = true
		contextOperations[name] = true
	}
}

func version(tx *sql.Tx, project string, r Object) (Object, error) {
	n, e := Num(r, "revision")
	if e != nil {
		return nil, e
	}
	var raw string
	var hash sql.NullString
	e = tx.QueryRow("SELECT body,content_hash FROM domain_versions WHERE project=? AND kind=? AND id=? AND revision=?", project, r["entity_type"], r["id"], n).Scan(&raw, &hash)
	if e != nil {
		return nil, Fail(422, "GATE_FAILED", "referenced version unavailable")
	}
	if hash.Valid && r["content_hash"] != hash.String || !hash.Valid && r["content_hash"] != nil {
		return nil, Fail(422, "CONTENT_HASH_MISMATCH", "reference hash mismatch")
	}
	return Decode([]byte(raw))
}
func (s *Service) effective(tx *sql.Tx, project string, r Object) error {
	return s.effectiveGraph(tx, project, r, map[string]bool{})
}
func (s *Service) effectiveGraph(tx *sql.Tx, project string, r Object, seen map[string]bool) error {
	key := Hash(r)
	if seen[key] {
		return nil
	}
	seen[key] = true
	old, e := version(tx, project, r)
	if e != nil {
		return e
	}
	current, e := load(tx, project, Str(r, "entity_type"), Str(r, "id"))
	if e != nil {
		return e
	}
	if current["revision"] != old["revision"] {
		return Fail(412, "STALE_INPUT", "input version changed")
	}
	if current["validity"] == "STALE" || current["validity"] == "REVOKED" {
		return Fail(409, "STATE_CONFLICT", "input is no longer effective")
	}
	if r["entity_type"] == "DecisionReceipt" {
		state, e := singleton(tx, project, "ProjectState")
		if e != nil {
			return e
		}
		found := false
		for _, v := range Arr(state, "current_decision_refs") {
			if v.(map[string]any)["id"] == r["id"] {
				found = true
			}
		}
		if !found {
			return Fail(409, "STATE_CONFLICT", "decision is not current")
		}
	}
	return s.effectiveInputs(tx, project, Str(r, "entity_type"), current, seen)
}

// Semantic references exclude identity-only and historical links such as supersedes_id.
// The same set drives current-input checks and deterministic impact links.
func semanticReferences(kind string, o Object) []Object {
	fields := []string{"input_refs", "source_refs", "source_document_refs", "facts"}
	if kind == "DecisionReceipt" {
		fields = append(fields, "subject_ref", "rubric_ref", "evidence_refs", "deterministic_results")
	}
	refs := []Object{}
	seen := map[string]bool{}
	var inspect func(any)
	inspect = func(v any) {
		switch x := v.(type) {
		case map[string]any:
			if Str(x, "entity_type") != "" {
				key := Hash(x)
				if !seen[key] {
					refs = append(refs, x)
					seen[key] = true
				}
				return
			}
			for _, v := range x {
				inspect(v)
			}
		case []any:
			for _, v := range x {
				inspect(v)
			}
		}
	}
	for _, field := range fields {
		inspect(o[field])
	}
	sort.Slice(refs, func(i, j int) bool { return Hash(refs[i]) < Hash(refs[j]) })
	return refs
}
func (s *Service) effectiveInputs(tx *sql.Tx, project, kind string, o Object, seen map[string]bool) error {
	for _, ref := range semanticReferences(kind, o) {
		if e := s.effectiveGraph(tx, project, ref, seen); e != nil {
			return e
		}
	}
	return nil
}

func (s *Service) taskContext(tx *sql.Tx, project string, task Object) error {
	if task["status"] == "NEEDS_REVALIDATION" || task["status"] == "CANCELLED" {
		return Fail(409, "STATE_CONFLICT", "task needs new validated inputs")
	}
	id := Str(task, "context_bundle_id")
	if id == "" {
		return Fail(422, "GATE_FAILED", "task context required")
	}
	bundle, e := load(tx, project, "ContextBundle", id)
	if e != nil {
		return e
	}
	for _, v := range Arr(bundle, "version_vector") {
		if e = s.effective(tx, project, v.(map[string]any)); e != nil {
			return e
		}
	}
	state, e := singleton(tx, project, "ProjectState")
	if e != nil {
		return e
	}
	if Hash(bundle["policy_revision"]) != Hash(state["policy_revision"]) {
		return Fail(412, "STALE_INPUT", "context policy changed")
	}
	return nil
}
func (s *Service) createContext(tx *sql.Tx, p Principal, project string, b Object) (Object, error) {
	state, e := singleton(tx, project, "ProjectState")
	if e != nil {
		return nil, e
	}
	if Hash(state["revision"]) != Hash(b["expected_project_state_revision"]) {
		return nil, Fail(412, "STALE_REVISION", "state changed")
	}
	task, e := load(tx, project, "Task", Str(b, "task_id"))
	if e != nil {
		return nil, e
	}
	if task["status"] == "CANCELLED" || task["status"] == "NEEDS_REVALIDATION" {
		return nil, Fail(409, "STATE_CONFLICT", "task inputs require revalidation")
	}
	profile, e := singleton(tx, project, "ProjectProfile")
	if e != nil {
		return nil, e
	}
	refs := []any{Ref(profile, "ProjectProfile")}
	snapshotIDs, e := s.currentAuthorizedSnapshots(tx, p, project)
	if e != nil { return nil, e }
	for _, rawID := range snapshotIDs {
		a, loadErr := s.readObject(tx, p, project, "Artifact", rawID.(string))
		if loadErr != nil { return nil, loadErr }
		refs = append(refs, Ref(a, "Artifact"))
	}
	seen := map[string]bool{}
	for _, field := range []string{"requirement_refs", "input_refs"} {
		for _, v := range Arr(task, field) {
			r := v.(map[string]any)
			if e = s.effective(tx, project, r); e != nil {
				return nil, e
			}
			key := Hash(r)
			if !seen[key] {
				refs = append(refs, r)
				seen[key] = true
			}
		}
	}
	for _, kind := range []string{"BudgetPolicy", "RunPolicy"} {
		field := "budget_policy_id"
		if kind == "RunPolicy" {
			field = "run_policy_id"
		}
		policy, e := load(tx, project, kind, Str(profile, field))
		if e != nil {
			return nil, e
		}
		refs = append(refs, Ref(policy, kind))
	}
	unresolved := Empty()
	for _, v := range Arr(state, "blocking_conflict_ids") {
		unresolved = append(unresolved, "Open conflict: "+v.(string))
	}
	commitments := Empty()
	for _, v := range Arr(task, "dependency_task_ids") {
		dep, e := load(tx, project, "Task", v.(string))
		if e != nil {
			return nil, e
		}
		if dep["status"] != "ACCEPTED" {
			commitments = append(commitments, "Dependency "+v.(string)+" remains "+Str(dep, "status"))
		} else {
			if e = s.acceptedTaskBinding(tx, project, dep); e != nil {
				return nil, e
			}
			receipt, e := load(tx, project, "AcceptanceReceipt", Str(dep, "acceptance_id"))
			if e != nil {
				return nil, e
			}
			for _, ref := range append([]any{Ref(dep, "Task"), Ref(receipt, "AcceptanceReceipt")}, Arr(receipt, "artifact_refs")...) {
				if !seen[Hash(ref)] {
					refs = append(refs, ref)
					seen[Hash(ref)] = true
				}
			}
		}
	}
	summary := Str(profile, "intent") + "\nTask: " + Str(task, "title") + "\nNext: follow the frozen acceptance contract; execution is not acceptance."
	decisions := Empty()
	for _, v := range refs {
		r := v.(map[string]any)
		if r["entity_type"] == "DecisionReceipt" {
			decisions = append(decisions, r)
		}
	}
	manifestHash := Hash(profile["source_document_refs"])
	var importedHash string
	if err := tx.QueryRow("SELECT manifest_hash FROM context_imports WHERE project=?", project).Scan(&importedHash); err == nil {
		manifestHash = importedHash
	} else if err != sql.ErrNoRows {
		return nil, err
	}
	if len(snapshotIDs) > 0 { manifestHash = Hash([]any{manifestHash, snapshotIDs}) }
	bundle := Object{"id": ID(), "project_id": project, "revision": 1, "created_at": Now(), "task_id": task["id"], "project_state_revision": state["revision"], "version_vector": refs, "facts": profile["facts"], "unresolved_items": unresolved, "latest_decision_refs": decisions, "unfinished_commitments": commitments, "summary": summary, "summary_hash": Digest([]byte(summary)), "source_manifest_hash": manifestHash, "authorized_snapshot_ids": snapshotIDs, "policy_revision": state["policy_revision"]}
	bundle["receipt_hash"] = Receipt(bundle)
	if e = s.put(tx, "ContextBundle", bundle); e != nil {
		return nil, e
	}
	task["context_bundle_id"] = bundle["id"]
	if e = bump(task); e != nil {
		return nil, e
	}
	if e = s.put(tx, "Task", task); e != nil {
		return nil, e
	}
	if e = s.retireTaskDependencies(tx, project, Str(task, "id")); e != nil {
		return nil, e
	}
	for _, r := range refs {
		if _, e = s.impactLink(tx, project, Object{"from_ref": Ref(task, "Task"), "to_ref": r, "relation": "DEPENDS_ON", "basis": "DETERMINISTIC", "evidence_refs": []any{Ref(bundle, "ContextBundle")}}); e != nil {
			return nil, e
		}
	}
	if e = s.event(tx, project, "Task", task, p.ID, Str(bundle, "id"), "TASK_CHANGED"); e != nil {
		return nil, e
	}
	return bundle, nil
}
func (s *Service) sendMessage(tx *sql.Tx, p Principal, project string, b Object) (Object, error) {
	if b["run_id"] != nil {
		return nil, Fail(503, "RESOURCE_UNAVAILABLE", "Run messaging awaits runtime qualification")
	}
	if b["task_id"] != nil {
		task, e := s.readObject(tx, p, project, "Task", Str(b, "task_id"))
		if e != nil {
			return nil, e
		}
		if e = s.taskContext(tx, project, task); e != nil {
			return nil, e
		}
	}
	var found int
	if e := tx.QueryRow("SELECT count(*) FROM auth_principals WHERE id=? AND revoked=0", b["recipient_id"]).Scan(&found); e != nil {
		return nil, e
	}
	if found != 1 {
		return nil, Fail(422, "GATE_FAILED", "recipient unavailable")
	}
	var recipientRoles string
	if e := tx.QueryRow("SELECT roles FROM auth_principals WHERE id=? AND revoked=0", b["recipient_id"]).Scan(&recipientRoles); e != nil {
		return nil, e
	}
	recipient := Principal{ID: Str(b, "recipient_id")}
	if e := json.Unmarshal([]byte(recipientRoles), &recipient.Roles); e != nil {
		return nil, e
	}
	rows, e := tx.Query("SELECT project,task,run,restricted FROM auth_grants WHERE principal=?", recipient.ID)
	if e != nil {
		return nil, e
	}
	for rows.Next() {
		var g Grant
		if e = rows.Scan(&g.ProjectID, &g.TaskID, &g.RunID, &g.Restricted); e != nil {
			rows.Close()
			return nil, e
		}
		recipient.Grants = append(recipient.Grants, g)
	}
	e = rows.Err()
	rows.Close()
	if e != nil {
		return nil, e
	}
	if !recipient.Allowed(project, Str(b, "task_id"), Str(b, "run_id"), false) || !s.visible(tx, recipient, project, b) {
		return nil, Fail(403, "FORBIDDEN", "recipient cannot read this message scope")
	}
	o := Merge(Object{"id": ID(), "project_id": project, "revision": 1, "created_at": Now()}, b)
	o["sender_id"] = p.ID
	o["dedup_key"] = Hash([]any{p.ID, project, b})
	o["receipt_hash"] = Receipt(o)
	return o, s.put(tx, "AgentMessage", o)
}
func (s *Service) impactLink(tx *sql.Tx, project string, b Object) (Object, error) {
	for _, k := range []string{"from_ref", "to_ref"} {
		if _, e := version(tx, project, b[k].(map[string]any)); e != nil {
			return nil, e
		}
	}
	o := Merge(Base(project), b)
	o["status"] = "ACTIVE"
	return o, s.put(tx, "ImpactLink", o)
}
func (s *Service) closure(tx *sql.Tx, project string, roots []Object) ([]any, []any, error) {
	rows, e := tx.Query("SELECT body FROM domain_objects WHERE project=? AND kind='ImpactLink' AND json_extract(body,'$.status')='ACTIVE'", project)
	if e != nil {
		return nil, nil, e
	}
	links := []Object{}
	for rows.Next() {
		var raw string
		if e = rows.Scan(&raw); e != nil {
			rows.Close()
			return nil, nil, e
		}
		o, e := Decode([]byte(raw))
		if e != nil {
			rows.Close()
			return nil, nil, e
		}
		links = append(links, o)
	}
	e = rows.Err()
	rows.Close()
	if e != nil {
		return nil, nil, e
	}
	seen := map[string]bool{}
	queue := append([]Object{}, roots...)
	for _, r := range roots {
		seen[Str(r, "entity_type")+":"+Str(r, "id")] = true
	}
	affected := []Object{}
	used := map[string]bool{}
	for len(queue) > 0 {
		r := queue[0]
		queue = queue[1:]
		for _, link := range links {
			from := link["from_ref"].(map[string]any)
			to := link["to_ref"].(map[string]any)
			relation := Str(link, "relation")
			if (relation == "DEPENDS_ON" || relation == "DERIVED_FROM" || relation == "IMPLEMENTS" || relation == "VERIFIES") && to["entity_type"] == r["entity_type"] && to["id"] == r["id"] {
				used[Str(link, "id")] = true
				key := Str(from, "entity_type") + ":" + Str(from, "id")
				if !seen[key] {
					current, e := load(tx, project, Str(from, "entity_type"), Str(from, "id"))
					if e != nil {
						return nil, nil, e
					}
					ref := Ref(current, Str(from, "entity_type"))
					affected = append(affected, ref)
					queue = append(queue, ref)
					seen[key] = true
				}
			}
		}
	}
	sort.Slice(affected, func(i, j int) bool { return Hash(affected[i]) < Hash(affected[j]) })
	out := Empty()
	for _, r := range affected {
		out = append(out, r)
	}
	ids := []string{}
	for id := range used {
		ids = append(ids, id)
	}
	sort.Strings(ids)
	linkIDs := Empty()
	for _, id := range ids {
		linkIDs = append(linkIDs, id)
	}
	return out, linkIDs, nil
}
func (s *Service) ConsumeEvent(ctx context.Context, consumer, project, eventID string) (Object, error) {
	tx, e := s.DB.BeginTx(ctx, nil)
	if e != nil {
		return nil, e
	}
	defer tx.Rollback()
	var raw string
	var seq int64
	if e = tx.QueryRow("SELECT sequence,body FROM outbox WHERE project=? AND id=?", project, eventID).Scan(&seq, &raw); e != nil {
		return nil, Fail(404, "NOT_FOUND", "event unavailable")
	}
	if _, e = tx.Exec("INSERT OR IGNORE INTO consumer_positions(consumer,project) VALUES(?,?)", consumer, project); e != nil {
		return nil, e
	}
	res, e := tx.Exec("INSERT OR IGNORE INTO consumer_inbox(consumer,project,event_id,sequence) VALUES(?,?,?,?)", consumer, project, eventID, seq)
	if e != nil {
		return nil, e
	}
	added, _ := res.RowsAffected()
	var position int64
	if e = tx.QueryRow("SELECT sequence FROM consumer_positions WHERE consumer=? AND project=?", consumer, project).Scan(&position); e != nil {
		return nil, e
	}
	applied := 0
	for {
		var id string
		e = tx.QueryRow("SELECT event_id FROM consumer_inbox WHERE consumer=? AND project=? AND sequence=? AND applied=0", consumer, project, position+1).Scan(&id)
		if e == sql.ErrNoRows {
			break
		}
		if e != nil {
			return nil, e
		}
		if e = tx.QueryRow("SELECT body FROM outbox WHERE id=?", id).Scan(&raw); e != nil {
			return nil, e
		}
		ev, e := Decode([]byte(raw))
		if e != nil {
			return nil, e
		}
		r := ev["aggregate_ref"].(map[string]any)
		obj, e := version(tx, project, r)
		if e != nil {
			return nil, e
		}
		revision, e := Num(r, "revision")
		if e != nil {
			return nil, e
		}
		_, e = tx.Exec("INSERT INTO context_projection(consumer,project,kind,id,revision,body) VALUES(?,?,?,?,?,?) ON CONFLICT(consumer,project,kind,id) DO UPDATE SET revision=excluded.revision,body=excluded.body WHERE excluded.revision>context_projection.revision", consumer, project, r["entity_type"], r["id"], revision, string(Bytes(obj)))
		if e != nil {
			return nil, e
		}
		var stateRaw string
		var stateRevision int64
		if e = tx.QueryRow("SELECT revision,body FROM event_state_snapshots WHERE project=? AND event_id=?", project, id).Scan(&stateRevision, &stateRaw); e != nil {
			return nil, e
		}
		state, e := Decode([]byte(stateRaw))
		if e != nil {
			return nil, e
		}
		if _, e = tx.Exec("INSERT INTO context_projection(consumer,project,kind,id,revision,body) VALUES(?,?,?,?,?,?) ON CONFLICT(consumer,project,kind,id) DO UPDATE SET revision=excluded.revision,body=excluded.body WHERE excluded.revision>context_projection.revision", consumer, project, "ProjectState", state["id"], stateRevision, stateRaw); e != nil {
			return nil, e
		}
		if _, e = tx.Exec("UPDATE consumer_inbox SET applied=1 WHERE consumer=? AND event_id=?", consumer, id); e != nil {
			return nil, e
		}
		position++
		applied++
	}
	if _, e = tx.Exec("UPDATE consumer_positions SET sequence=? WHERE consumer=? AND project=?", position, consumer, project); e != nil {
		return nil, e
	}
	if e = tx.Commit(); e != nil {
		return nil, e
	}
	status := "APPLIED"
	if added == 0 {
		status = "DUPLICATE"
	} else if seq > position {
		status = "WAITING_FOR_PREDECESSOR"
	}
	return Object{"status": status, "sequence": position, "applied_count": applied}, nil
}
func (s *Service) contextOperation(tx *sql.Tx, p Principal, project, id string, b Object, op string) (Object, string, int, error) {
	var o Object
	var e error
	kind := ""
	status := 201
	switch op {
	case "createContextBundle":
		o, e = s.createContext(tx, p, project, b)
		kind = "ContextBundle"
	case "createImpactLink":
		o, e = s.impactLink(tx, project, b)
		kind = "ImpactLink"
	case "sendAgentMessage":
		o, e = s.sendMessage(tx, p, project, b)
		kind = "AgentMessage"
	case "recordDecision":
		o, e = s.recordDecision(tx, p, project, b)
		kind = "DecisionReceipt"
	case "createChangeProposal":
		o, e = s.createChange(tx, p, project, b)
		kind = "ChangeProposal"
	case "applyChangeProposal":
		o, e = s.applyChange(tx, p, project, id, b)
		kind = "ChangeProposal"
		status = 200
	case "recordAcceptance":
		o, e = s.acceptChange(tx, p, project, b)
		kind = "AcceptanceReceipt"
	case "createConflict":
		o, e = s.createConflict(tx, project, b)
		kind = "Conflict"
	case "resolveConflict":
		o, e = s.resolveConflict(tx, project, id, b)
		kind = "Conflict"
		status = 200
	default:
		e = Fail(503, "RESOURCE_UNAVAILABLE", fmt.Sprintf("operation %s unavailable", op))
	}
	return o, kind, status, e
}

// revalidateTask refreshes admitted versions only; readiness and execution remain W06.
func (s *Service) revalidateTask(tx *sql.Tx, project string, task Object) (Object, error) {
	if task["status"] != "NEEDS_REVALIDATION" {
		return nil, Fail(409, "STATE_CONFLICT", "task is not awaiting revalidation")
	}
	state, e := singleton(tx, project, "ProjectState")
	if e != nil {
		return nil, e
	}
	for _, field := range []string{"requirement_refs", "input_refs"} {
		updated := Empty()
		for _, v := range Arr(task, field) {
			r := v.(map[string]any)
			kind := Str(r, "entity_type")
			current, e := load(tx, project, kind, Str(r, "id"))
			if e != nil {
				return nil, e
			}
			if kind == "DecisionReceipt" {
				var root string
				if e = tx.QueryRow("SELECT root_id FROM decision_lineage WHERE project=? AND receipt_id=?", project, r["id"]).Scan(&root); e != nil {
					return nil, e
				}
				found := false
				for _, v := range Arr(state, "current_decision_refs") {
					candidate := v.(map[string]any)
					var candidateRoot string
					if e = tx.QueryRow("SELECT root_id FROM decision_lineage WHERE project=? AND receipt_id=?", project, candidate["id"]).Scan(&candidateRoot); e != nil {
						return nil, e
					}
					if candidateRoot == root {
						current, e = version(tx, project, candidate)
						if e != nil {
							return nil, e
						}
						found = true
						break
					}
				}
				if !found {
					return nil, Fail(422, "GATE_FAILED", "no accepted successor decision")
				}
			}
			ref := Ref(current, kind)
			if e = s.effective(tx, project, ref); e != nil {
				return nil, e
			}
			if field == "requirement_refs" && current["status"] != "ACCEPTED" {
				return nil, Fail(422, "GATE_FAILED", "requirement no longer accepted")
			}
			updated = append(updated, ref)
		}
		task[field] = updated
	}
	task["status"] = "DRAFT"
	task["context_bundle_id"] = nil
	task["acceptance_id"] = nil
	if e = bump(task); e != nil {
		return nil, e
	}
	return task, s.put(tx, "Task", task)
}
func (s *Service) retireTaskDependencies(tx *sql.Tx, project, taskID string) error {
	rows, e := tx.Query("SELECT body FROM domain_objects WHERE project=? AND kind='ImpactLink' AND json_extract(body,'$.status')='ACTIVE' AND json_extract(body,'$.from_ref.entity_type')='Task' AND json_extract(body,'$.from_ref.id')=? AND json_extract(body,'$.relation')='DEPENDS_ON'", project, taskID)
	if e != nil {
		return e
	}
	links := []Object{}
	for rows.Next() {
		var raw string
		if e = rows.Scan(&raw); e != nil {
			rows.Close()
			return e
		}
		o, e := Decode([]byte(raw))
		if e != nil {
			rows.Close()
			return e
		}
		links = append(links, o)
	}
	e = rows.Err()
	rows.Close()
	if e != nil {
		return e
	}
	for _, link := range links {
		link["status"] = "SUPERSEDED"
		if e = bump(link); e != nil {
			return e
		}
		if e = s.put(tx, "ImpactLink", link); e != nil {
			return e
		}
	}
	return nil
}
