package domain

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"sort"
	"strings"
	"time"
	"unicode/utf8"
)

type clientGoalBindingResolver interface {
	ResolveGoalBinding(context.Context, *sql.Tx, string, string, string) (string, string, error)
}

type finiteGoalSpec struct {
	Objective, Title, Deliverable, RequirementKey, Rationale string
	ProblemID, CandidateID                                   string
	SourceRefs, InputRefs                                    []any
	Contract                                                 Object
	Draft, ReuseRequirement                                  bool
}

type finiteGoalResult struct {
	Goal, Task Object
	Blocked    error
}

// buildFiniteClientGoal is the existing one-turn business path shared by
// session.send and explicit Goal creation. It never starts a worker in this
// transaction; the one runtime coordinator admits and dispatches the Task.
func (s *ClientService) buildFiniteClientGoal(ctx context.Context, tx *sql.Tx, env *Envelope, owner Principal, sess *clientSessionRow, model string, spec finiteGoalSpec) (finiteGoalResult, error) {
	var out finiteGoalResult
	project := sess.project
	var req Object
	var err error
	if spec.ReuseRequirement {
		req, err = s.goalRequirement(tx, project, spec)
		if err != nil {
			return out, err
		}
	} else {
		req, err = s.Domain.createRequirement(tx, project, Object{"requirement_key": spec.RequirementKey, "text": spec.Objective, "basis": "USER_STATED", "source_refs": spec.SourceRefs, "rationale": spec.Rationale, "supersedes_id": nil, "acceptance_check_ids": Empty()})
		if err != nil {
			return out, err
		}
		req, err = s.Domain.actRequirement(tx, project, Str(req, "id"), Object{"action": "ACCEPT", "source_validation_refs": Empty()})
		if err != nil {
			return out, err
		}
	}
	reqRef := Ref(req, "Requirement")
	refs := append(append(Empty(), spec.InputRefs...), reqRef)
	if !spec.Draft {
		if authority, ok := s.SessionRuntime.(ClientTaskInputAuthority); ok {
			frozen, freezeErr := authority.FreezeClientTaskInputs(ctx, tx, project, model)
			if freezeErr != nil {
				return out, freezeErr
			}
			refs = append(refs, frozen...)
		}
	}
	goal, err := s.Domain.createGoal(tx, project, Object{"title": spec.Title, "original_intent": spec.Objective, "scope": "PROJECT", "requirement_refs": []any{reqRef}, "problem_ids": []any{spec.ProblemID}, "deliverables": []any{spec.Deliverable}, "acceptance_contract": spec.Contract})
	if err != nil {
		return out, err
	}
	out.Goal = goal
	if spec.Draft {
		_, err = tx.ExecContext(ctx, "UPDATE client_sessions SET goal_id=?,task_id=NULL,run_id=NULL WHERE id=? AND project_id=?", goal["id"], sess.sessionID, project)
		sess.runID = ""
		return out, err
	}
	task, err := s.Domain.createTask(tx, project, Object{"goal_id": goal["id"], "title": spec.Title, "task_type": "mu_turn", "stage": "delivery", "dependency_task_ids": Empty(), "requirement_refs": []any{reqRef}, "input_refs": refs, "acceptance_contract": spec.Contract, "origin_problem_id": spec.ProblemID, "candidate_id": spec.CandidateID, "stop_policy": Object{"wall_time_seconds": 900, "max_attempts": 1, "max_parallel_runs": 1, "stop_conditions": []any{"turn complete", "model or tool effect unknown", "lease or authority lost", "Owner cancellation"}}})
	if err != nil {
		return out, err
	}
	goal, err = s.Domain.actGoal(tx, project, Str(goal, "id"), Object{"action": "ACTIVATE", "reason": "Authenticated finite client objective"})
	if err != nil {
		return out, err
	}
	out.Goal = goal
	state, err := singleton(tx, project, "ProjectState")
	if err != nil {
		return out, err
	}
	if _, err = s.Domain.createContext(tx, owner, project, Object{"task_id": task["id"], "expected_project_state_revision": state["revision"]}); err != nil {
		return out, err
	}
	task, err = load(tx, project, "Task", Str(task, "id"))
	if err != nil {
		return out, err
	}
	task, err = s.Domain.orchestrateTask(tx, project, task, Object{"action": "SUBMIT"})
	if err != nil {
		return out, err
	}
	blocked := s.SessionRuntime.AdmitTurn(ctx, tx, project, model, task)
	if blocked != nil {
		var fault *Fault
		if !errors.As(blocked, &fault) {
			return out, blocked
		}
		if task["status"] != "BLOCKED" {
			task["status"] = "BLOCKED"
			if err = bump(task); err != nil {
				return out, err
			}
			if err = s.Domain.put(tx, "Task", task); err != nil {
				return out, err
			}
		}
	}
	if _, err = tx.ExecContext(ctx, "UPDATE client_sessions SET goal_id=?,task_id=?,run_id=NULL WHERE id=? AND project_id=?", goal["id"], task["id"], sess.sessionID, project); err != nil {
		return out, err
	}
	sess.runID = ""
	out.Task, out.Blocked = task, blocked
	return out, nil
}

// A repeated explicit Goal with unchanged objective and contract inputs must
// retain its accepted Requirement identity, and must not obtain a new budget or
// progress key through a new command id. Its original Goal is resumed through
// the session controls rather than recreated here.
func (s *ClientService) goalRequirement(tx *sql.Tx, project string, spec finiteGoalSpec) (Object, error) {
	rows, err := tx.Query(`SELECT body FROM domain_objects WHERE project=? AND kind='Requirement' AND json_extract(body,'$.requirement_key')=?`, project, spec.RequirementKey)
	if err != nil {
		return nil, err
	}
	var existing []Object
	for rows.Next() {
		var raw string
		if err = rows.Scan(&raw); err != nil {
			rows.Close()
			return nil, err
		}
		o, decodeErr := Decode([]byte(raw))
		if decodeErr != nil {
			rows.Close()
			return nil, decodeErr
		}
		existing = append(existing, o)
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return nil, err
	}
	if len(existing) > 1 {
		return nil, Fail(409, "STATE_CONFLICT", "goal intent has conflicting Requirement identities")
	}
	if len(existing) == 1 {
		req := existing[0]
		if req["status"] != "ACCEPTED" || req["basis"] != "USER_STATED" || req["text"] != spec.Objective || Hash(req["source_refs"]) != Hash(spec.SourceRefs) {
			return nil, Fail(409, "STATE_CONFLICT", "goal intent Requirement changed")
		}
		var count int
		if err = tx.QueryRow(`SELECT count(*) FROM domain_objects WHERE project=? AND kind='Goal' AND json_extract(body,'$.original_intent')=? AND EXISTS
			(SELECT 1 FROM json_each(domain_objects.body,'$.requirement_refs') r WHERE json_extract(r.value,'$.id')=?)`, project, spec.Objective, req["id"]).Scan(&count); err != nil {
			return nil, err
		}
		if count != 0 {
			return nil, Fail(409, "STATE_CONFLICT", "same Goal already exists; continue its original Task")
		}
		return req, nil
	}
	req, err := s.Domain.createRequirement(tx, project, Object{"requirement_key": spec.RequirementKey, "text": spec.Objective, "basis": "USER_STATED", "source_refs": spec.SourceRefs, "rationale": spec.Rationale, "supersedes_id": nil, "acceptance_check_ids": Empty()})
	if err != nil {
		return nil, err
	}
	return s.Domain.actRequirement(tx, project, Str(req, "id"), Object{"action": "ACCEPT", "source_validation_refs": Empty()})
}

func (s *ClientService) goalContracts(tx *sql.Tx, owner Principal, project string, ids []string) (Object, []any, error) {
	base := clientTurnContract()
	checks := append(Empty(), Arr(base, "checks")...)
	byID := map[string]Object{}
	for _, raw := range checks {
		check := Object(raw.(map[string]any))
		byID[Str(check, "check_id")] = check
	}
	refs := Empty()
	seen := map[string]bool{}
	maxRevision := int64(1)
	for _, id := range ids {
		if id == "" || seen[id] {
			return nil, nil, Fail(422, "INVALID_REQUEST", "goal contract artifact ids must be unique and nonempty")
		}
		seen[id] = true
		a, err := s.Domain.readObject(tx, owner, project, "Artifact", id)
		if err != nil {
			return nil, nil, err
		}
		if a["access_class"] != "PROJECT" || Str(a, "sealed_at") == "" {
			return nil, nil, Fail(403, "FORBIDDEN", "goal contract needs a visible sealed project Artifact")
		}
		ref := Ref(a, "Artifact")
		if err = s.Domain.effective(tx, project, ref); err != nil {
			return nil, nil, err
		}
		var raw []byte
		if err = tx.QueryRow(`SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1`, project, a["storage_key"]).Scan(&raw); err != nil {
			return nil, nil, Fail(422, "GATE_FAILED", "goal contract has no sealed bytes")
		}
		size, err := Num(a, "byte_size")
		if err != nil || len(raw) > 4<<20 || int64(len(raw)) != size || Digest(raw) != a["content_hash"] {
			return nil, nil, Fail(422, "CONTENT_HASH_MISMATCH", "goal contract sealed bytes differ")
		}
		body, err := Decode(raw)
		if err != nil || s.Domain.Contracts.Validate("AcceptanceContract", body) != nil || body["contract_hash"] != contractDigest(body) {
			return nil, nil, Fail(422, "GATE_FAILED", "goal contract Artifact is not a valid exact AcceptanceContract")
		}
		revision, err := Num(body, "contract_revision")
		if err != nil {
			return nil, nil, err
		}
		if revision > maxRevision {
			maxRevision = revision
		}
		required := 0
		for _, value := range Arr(body, "checks") {
			check := Object(value.(map[string]any))
			key := Str(check, "check_id")
			if check["required"] == true {
				required++
			}
			if prior, ok := byID[key]; ok {
				if Hash(prior) != Hash(check) {
					return nil, nil, Fail(422, "GATE_FAILED", "goal contracts disagree on a check id")
				}
				continue
			}
			byID[key] = check
			checks = append(checks, check)
		}
		if required == 0 {
			return nil, nil, Fail(422, "GATE_FAILED", "goal contract Artifact has no mandatory check")
		}
		refs = append(refs, ref)
	}
	base["contract_revision"] = maxRevision
	base["checks"] = checks
	base["frozen_at"] = Now()
	base["contract_hash"] = contractDigest(base)
	if err := s.Domain.Contracts.Validate("AcceptanceContract", base); err != nil {
		return nil, nil, Fail(422, "GATE_FAILED", "merged goal contract is invalid")
	}
	return base, refs, nil
}

func (s *ClientService) startClientGoal(ctx context.Context, tx *sql.Tx, env *Envelope, principal string, sess *clientSessionRow) (*Response, error) {
	project := deref(env.ProjectID)
	owner, err := clientPrincipal(ctx, tx, principal, project, true)
	if err != nil {
		return clientFault(env, err)
	}
	var payload struct {
		Objective string   `json:"objective"`
		Contracts []string `json:"contract_artifact_ids"`
		Draft     bool     `json:"start_as_draft"`
	}
	if err = json.Unmarshal(env.Payload, &payload); err != nil {
		return nil, err
	}
	if strings.TrimSpace(payload.Objective) == "" || utf8.RuneCountInString(payload.Objective) > 16384 {
		return NewTypedRejection(env, "CONTENT_TOO_LARGE", "goal objective must contain 1 to 16384 characters"), nil
	}
	contract, artifactRefs, err := s.goalContracts(tx, owner, project, payload.Contracts)
	if err != nil {
		return clientFault(env, err)
	}
	model := ""
	createdSession := sess == nil
	if createdSession {
		if env.ExpectedRevision != nil || env.WriterEpoch != nil {
			return NewTypedRejection(env, "INVALID_REQUEST", "project goal must not claim a session writer"), nil
		}
		resolver, ok := s.SessionRuntime.(clientGoalBindingResolver)
		if !ok {
			return NewTypedRejection(env, "RESOURCE_BLOCKED", "host cannot resolve a unique Goal workspace and model"), nil
		}
		workspace := ""
		workspace, model, err = resolver.ResolveGoalBinding(ctx, tx, principal, project, deref(env.ClientID))
		if err != nil {
			return clientFault(env, err)
		}
		title := string([]rune(payload.Objective)[:min(60, utf8.RuneCountInString(payload.Objective))])
		sid, makeErr := s.createBoundClientSession(ctx, tx, env, principal, workspace, model, title)
		if makeErr != nil {
			return clientFault(env, makeErr)
		}
		sess, err = loadClientSession(ctx, tx, sid, project)
		if err != nil {
			return nil, err
		}
	} else {
		var workspace, previous string
		var lease sql.NullString
		if err = tx.QueryRowContext(ctx, `SELECT workspace_ref,model_config_ref,lease_expires_at,coalesce(task_id,'') FROM client_sessions WHERE id=? AND project_id=?`, sess.sessionID, project).Scan(&workspace, &model, &lease, &previous); err != nil {
			return nil, err
		}
		expires, parseErr := time.Parse(time.RFC3339Nano, lease.String)
		if parseErr != nil || !expires.After(time.Now()) {
			return NewTypedRejection(env, "LEASE_EXPIRED", "writer lease expired; acquire a current writer lease"), nil
		}
		if err = s.checkClientBinding(ctx, tx, principal, project, workspace, model); err != nil {
			return clientFault(env, err)
		}
		if previous != "" {
			task, loadErr := load(tx, project, "Task", previous)
			if loadErr != nil {
				return nil, loadErr
			}
			if !clientTurnSettled(tx, project, sess.sessionID, task) {
				return NewTypedRejection(env, "SESSION_BUSY", "previous Task requires settlement or explicit cancellation"), nil
			}
		}
	}
	// A stable requirement reference and the exact current runtime profile ref
	// keep NoProgressRecord's input key stable for unchanged explicit Goals.
	keyRefs := append(Empty(), artifactRefs...)
	sort.Slice(keyRefs, func(i, j int) bool { return Hash(keyRefs[i]) < Hash(keyRefs[j]) })
	identity := Digest(Bytes(Object{"project": project, "principal": principal, "objective": payload.Objective, "contracts": keyRefs}))
	spec := finiteGoalSpec{
		Objective: payload.Objective, Title: payload.Objective, Deliverable: "One bounded Mu response to the exact Owner objective; independent acceptance remains separate",
		RequirementKey: "GOAL-" + identity[:32], Rationale: "Authenticated Owner explicit goal.start objective",
		ProblemID: "goal-problem-" + identity[:32], CandidateID: "goal-candidate-" + identity[:32],
		SourceRefs: keyRefs, InputRefs: keyRefs, Contract: contract, Draft: payload.Draft, ReuseRequirement: true,
	}
	created, err := s.buildFiniteClientGoal(ctx, tx, env, owner, sess, model, spec)
	if err != nil {
		return clientFault(env, err)
	}
	goal := created.Goal
	if err = s.journal(ctx, tx, env, sess, "GOAL_STATE", Object{"goal_id": goal["id"], "status": goal["status"], "revision": goal["revision"], "accepted_artifact_refs": Empty()}); err != nil {
		return nil, err
	}
	sess.revision++
	sess.watermark++
	if created.Task != nil {
		if err = s.Domain.event(tx, project, "Task", created.Task, principal, deref(env.CommandID), "TASK_CHANGED"); err != nil {
			return nil, err
		}
		if created.Blocked != nil || created.Task["status"] == "BLOCKED" {
			if err = s.journal(ctx, tx, env, sess, "ERROR", Object{"code": "RESOURCE_BLOCKED", "message": "Goal saved; its finite Task is BLOCKED until runtime qualification and permission are current", "retryable": false, "recovery": "RESOLVE_RESOURCE", "current_revision": sess.revision, "current_writer_epoch": sess.epoch, "resource_request_id": nil, "retry_after_ms": nil, "correlation_id": deref(env.CommandID)}); err != nil {
				return nil, err
			}
			sess.revision++
			sess.watermark++
		}
	}
	snap, err := BuildSessionSnapshot(ctx, tx, s.Doc, project, sess.sessionID)
	if err != nil {
		return nil, err
	}
	// A null top-level SessionID identifies this as the session's original
	// project-level creation receipt. The real session is in the typed snapshot.
	var responseSession *string
	if !createdSession {
		responseSession = env.SessionID
	}
	return &Response{ProtocolVersion: strptr(ProtocolV2), CommandID: env.CommandID, Method: env.Method, Status: strptr("COMPLETED"), SessionID: responseSession, Revision: revPtr(sess.revision), Result: Object{"goal_id": goal["id"], "goal_revision": goal["revision"], "goal_status": goal["status"], "snapshot": snap}}, nil
}
