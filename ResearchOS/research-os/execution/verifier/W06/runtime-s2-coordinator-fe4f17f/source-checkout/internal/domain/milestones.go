package domain

import (
	"database/sql"
	"encoding/json"
)

func workbenchIndependent(tx *sql.Tx, receipt Object) error {
	verifier := Str(receipt, "verifier_principal_id")
	if receipt["verdict"] != "PASS" || receipt["receipt_hash"] != Receipt(receipt) || verifier == "" || len(Arr(receipt, "executor_principal_ids")) == 0 || len(Arr(receipt, "blocking_conflict_ids")) != 0 {
		return Fail(422, "GATE_FAILED", "current independent passing acceptance required")
	}
	root, e := authorityRoot(tx, verifier)
	if e != nil {
		return e
	}
	for _, id := range Arr(receipt, "executor_principal_ids") {
		executorRoot, e := authorityRoot(tx, id.(string))
		if e != nil {
			return e
		}
		if executorRoot == root {
			return Fail(403, "FORBIDDEN", "acceptance shares executor authority")
		}
	}
	return nil
}

func (s *Service) workbenchTaskAcceptance(tx *sql.Tx, project string, task Object) (Object, error) {
	if task["status"] != "ACCEPTED" || len(Arr(task, "blocking_conflict_ids")) != 0 {
		return nil, Fail(422, "GATE_FAILED", "task is not currently accepted")
	}
	if e := s.acceptedTaskBinding(tx, project, task); e != nil {
		return nil, e
	}
	if e := s.taskContext(tx, project, task); e != nil {
		return nil, e
	}
	r, e := load(tx, project, "AcceptanceReceipt", Str(task, "acceptance_id"))
	if e != nil {
		return nil, e
	}
	ref, ok := r["subject_ref"].(map[string]any)
	if !ok || ref["entity_type"] != "Task" || ref["id"] != task["id"] || r["verifier_principal_id"] == task["assigned_principal_id"] {
		return nil, Fail(422, "GATE_FAILED", "acceptance subject or verifier changed")
	}
	return r, workbenchIndependent(tx, r)
}

// Milestones bind the current acceptance graph, not merely an existing receipt.
// Goal acceptance is checked through its current independently accepted tasks.
func (s *Service) milestoneAcceptance(tx *sql.Tx, project, id string) (Object, error) {
	r, e := load(tx, project, "AcceptanceReceipt", id)
	if e != nil {
		return nil, e
	}
	if e = workbenchIndependent(tx, r); e != nil {
		return nil, e
	}
	ref := r["subject_ref"].(map[string]any)
	subject, e := load(tx, project, Str(ref, "entity_type"), Str(ref, "id"))
	if e != nil {
		return nil, e
	}
	if subject["acceptance_id"] != r["id"] {
		return nil, Fail(422, "GATE_FAILED", "acceptance is not current for its subject")
	}
	switch ref["entity_type"] {
	case "Task":
		return s.workbenchTaskAcceptance(tx, project, subject)
	case "Goal":
		if subject["status"] != "ACCEPTED" || len(Arr(subject, "task_ids")) == 0 || len(Arr(subject, "blocking_conflict_ids")) != 0 {
			return nil, Fail(422, "GATE_FAILED", "goal is not currently accepted")
		}
		inputs := append(Empty(), Arr(subject, "requirement_refs")...)
		refs := Empty()
		for _, v := range Arr(subject, "task_ids") {
			t, e := load(tx, project, "Task", v.(string))
			if e != nil {
				return nil, e
			}
			a, e := s.workbenchTaskAcceptance(tx, project, t)
			if e != nil {
				return nil, e
			}
			inputs = append(inputs, Ref(t, "Task"))
			refs = append(refs, Arr(a, "artifact_refs")...)
		}
		contract := subject["acceptance_contract"].(map[string]any)
		if Hash(inputs) != Hash(r["input_refs"]) || Hash(refs) != Hash(r["artifact_refs"]) || r["contract_hash"] != contract["contract_hash"] || contract["contract_hash"] != contractDigest(contract) {
			return nil, Fail(422, "GATE_FAILED", "goal acceptance inputs or deliverables changed")
		}
		for _, v := range Arr(subject, "requirement_refs") {
			if e = s.effective(tx, project, v.(map[string]any)); e != nil {
				return nil, e
			}
		}
	case "ChangeProposal":
		if subject["status"] != "APPLIED" || r["contract_hash"] != changeHash(subject) {
			return nil, Fail(422, "GATE_FAILED", "change has not been independently accepted and applied")
		}
		for _, v := range Arr(r, "artifact_refs") {
			a, err := version(tx, project, v.(map[string]any))
			if err != nil {
				return nil, err
			}
			if e = s.requireCurrentArtifactBody(tx, project, a); e != nil {
				return nil, e
			}
		}
		for _, v := range Arr(subject, "edits") {
			edit := v.(map[string]any)
			target := edit["target_ref"].(map[string]any)
			current, err := load(tx, project, Str(target, "entity_type"), Str(target, "id"))
			if err != nil {
				return nil, err
			}
			value, err := s.artifactJSON(tx, project, edit["proposed_value_artifact_ref"].(map[string]any))
			if err != nil {
				return nil, err
			}
			if Hash(current[Str(edit, "field")]) != Hash(value) {
				return nil, Fail(412, "STALE_INPUT", "accepted change no longer matches current state")
			}
		}
	default:
		return nil, Fail(503, "RESOURCE_UNAVAILABLE", "milestone acceptance subject requires its owning stage")
	}
	return r, nil
}

func (s *Service) createMilestone(tx *sql.Tx, p Principal, project string, b Object, cid string) (Object, error) {
	state, e := singleton(tx, project, "ProjectState")
	if e != nil {
		return nil, e
	}
	if Hash(b["policy_revision"]) != Hash(state["policy_revision"]) {
		return nil, Fail(422, "GATE_FAILED", "milestone policy changed")
	}
	acceptedArtifacts := map[string]bool{}
	for _, id := range Arr(b, "acceptance_ids") {
		r, e := s.milestoneAcceptance(tx, project, id.(string))
		if e != nil {
			return nil, e
		}
		if Hash(r["policy_revision"]) != Hash(state["policy_revision"]) {
			return nil, Fail(412, "STALE_INPUT", "acceptance policy changed")
		}
		for _, v := range Arr(r, "artifact_refs") {
			acceptedArtifacts[Hash(v)] = true
		}
	}
	for _, ref := range Arr(b, "artifact_refs") {
		if !acceptedArtifacts[Hash(ref)] {
			return nil, Fail(422, "GATE_FAILED", "milestone artifact lacks exact accepted binding")
		}
	}
	for _, id := range Arr(b, "decision_ids") {
		d, e := load(tx, project, "DecisionReceipt", id.(string))
		if e != nil {
			return nil, e
		}
		if e = s.effective(tx, project, Ref(d, "DecisionReceipt")); e != nil {
			return nil, e
		}
	}
	var sequence int64
	if e = tx.QueryRow("SELECT coalesce(max(json_extract(body,'$.sequence')),0)+1 FROM domain_objects WHERE project=? AND kind='MilestoneRelease'", project).Scan(&sequence); e != nil {
		return nil, e
	}
	o := Merge(Object{"id": ID(), "project_id": project, "revision": 1, "created_at": Now(), "sequence": sequence, "parent_release_id": state["latest_release_id"]}, b)
	o["receipt_hash"] = Receipt(o)
	if e = s.put(tx, "MilestoneRelease", o); e != nil {
		return nil, e
	}
	state["latest_release_id"] = o["id"]
	if e = bump(state); e != nil {
		return nil, e
	}
	if e = s.put(tx, "ProjectState", state); e != nil {
		return nil, e
	}
	if e = s.event(tx, project, "MilestoneRelease", o, p.ID, cid, "RELEASE_CREATED"); e != nil {
		return nil, e
	}
	// Notify only active human-facing OWNER/READER principals with project-wide
	// grants and visibility of this release. No external delivery is authorized.
	rows, e := tx.Query("SELECT p.id,p.roles,max(g.restricted) FROM auth_principals p JOIN auth_grants g ON g.principal=p.id WHERE p.revoked=0 AND g.project=? AND g.task='' AND g.run='' GROUP BY p.id,p.roles ORDER BY p.id", project)
	if e != nil {
		return nil, e
	}
	recipients := []Principal{}
	for rows.Next() {
		var recipient Principal
		var roles string
		var restricted bool
		if e = rows.Scan(&recipient.ID, &roles, &restricted); e != nil {
			rows.Close()
			return nil, e
		}
		if e = json.Unmarshal([]byte(roles), &recipient.Roles); e != nil {
			rows.Close()
			return nil, e
		}
		recipient.Grants = []Grant{{ProjectID: project, Restricted: restricted}}
		if recipient.HasRole("OWNER") || recipient.HasRole("READER") {
			recipients = append(recipients, recipient)
		}
	}
	e = rows.Err()
	rows.Close()
	if e != nil {
		return nil, e
	}
	for _, recipient := range recipients {
		if !s.visible(tx, recipient, project, o) {
			continue
		}
		if e = s.milestoneNotification(tx, project, o, recipient.ID, p.ID, cid); e != nil {
			return nil, e
		}
	}
	return o, nil
}

func (s *Service) milestoneNotification(tx *sql.Tx, project string, release Object, recipient, actor, cid string) error {
	var exists int
	if e := tx.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='Notification' AND json_extract(body,'$.release_id')=? AND json_extract(body,'$.recipient_id')=? AND json_extract(body,'$.channel')='IN_APP'", project, release["id"], recipient).Scan(&exists); e != nil {
		return e
	}
	if exists != 0 {
		return nil
	}
	n := Merge(Base(project), Object{"release_id": release["id"], "resource_request_id": nil, "recipient_id": recipient, "channel": "IN_APP", "dedup_key": Hash([]any{release["id"], recipient, "IN_APP"}), "status": "UNREAD", "summary": release["summary"], "read_at": nil})
	if e := s.put(tx, "Notification", n); e != nil {
		return e
	}
	return s.event(tx, project, "Notification", n, actor, cid, "NOTIFICATION_CHANGED")
}

func (s *Service) readNotification(tx *sql.Tx, p Principal, project, id, cid string) (Object, error) {
	n, e := s.readObject(tx, p, project, "Notification", id)
	if e != nil {
		return nil, e
	}
	if n["recipient_id"] != p.ID {
		return nil, Fail(404, "NOT_FOUND", "notification unavailable")
	}
	if n["status"] == "READ" {
		return n, nil
	}
	n["status"], n["read_at"] = "READ", Now()
	if e = bump(n); e != nil {
		return nil, e
	}
	if e = s.put(tx, "Notification", n); e != nil {
		return nil, e
	}
	return n, s.event(tx, project, "Notification", n, p.ID, cid, "NOTIFICATION_CHANGED")
}
