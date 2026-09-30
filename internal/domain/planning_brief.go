package domain

import (
	"bytes"
	"database/sql"
	"encoding/json"
	"fmt"
	"io"
	"regexp"
	"strings"
)

var planningLogicalID = regexp.MustCompile(`^[a-zA-Z][a-zA-Z0-9_-]{0,63}$`)
var planningCommandKey = regexp.MustCompile(`^[a-z][a-z0-9_.-]{0,127}$`)
var planningJSONInstruction = regexp.MustCompile(`^请(?:(按先后顺序|先后)?生成(一份|两份) ([\s\S]+) JSON 报告|交付 ([\s\S]+))。$`)

// Recognition is intentionally narrow: mentioning a JSON object inside an
// arbitrary sentence (including a prohibition) does not authorize its delivery.
func planningJSONAuthorization(meta Object) (string, int, bool) {
	for _, v := range Arr(meta, "sources") {
		r := v.(map[string]any)
		if r["status"] != "ACCEPTED" || r["basis"] != "USER_STATED" {
			continue
		}
		m := planningJSONInstruction.FindStringSubmatch(Str(r, "text"))
		if m == nil {
			continue
		}
		literal := m[3]
		count := 1
		if m[2] == "两份" {
			count = 2
		}
		if m[4] != "" {
			literal = m[4]
		}
		if !json.Valid([]byte(literal)) {
			continue
		}
		if _, e := Decode([]byte(literal)); e != nil {
			continue
		}
		return literal, count, m[1] != ""
	}
	return "", 0, false
}

// GoalBrief is private GENERATED content, never a public mutation request.
// Every business arrangement remains a proposal even after structural acceptance.
type GoalBrief struct {
	Schema          string             `json:"schema"`
	ProjectID       string             `json:"project_id"`
	RawIntentRef    Object             `json:"raw_intent_ref"`
	RawIntentHash   string             `json:"raw_intent_hash"`
	ContextRef      Object             `json:"context_ref"`
	VersionVector   []any              `json:"version_vector"`
	Revision        int                `json:"revision"`
	SupersedesRef   Object             `json:"supersedes_ref"`
	Status          string             `json:"status"`
	Title           string             `json:"title"`
	Facts           []PlanningFact     `json:"facts"`
	Scope           []string           `json:"scope"`
	Exclusions      []string           `json:"exclusions"`
	Deliverables    []string           `json:"deliverables"`
	Nodes           []PlanningNode     `json:"nodes"`
	BudgetPolicyRef Object             `json:"budget_policy_ref"`
	FailureExits    []string           `json:"failure_exits"`
	OpenQuestions   []PlanningQuestion `json:"open_questions"`
	CapabilityGaps  []PlanningGap      `json:"capability_gaps"`
}
type PlanningFact struct {
	Text       string `json:"text"`
	Basis      string `json:"basis"`
	SourceRefs []any  `json:"source_refs"`
}
type PlanningNode struct {
	ID           string          `json:"logical_id"`
	Title        string          `json:"title"`
	Action       string          `json:"action"`
	Dependencies []string        `json:"depends_on"`
	Inputs       []any           `json:"input_refs"`
	Outputs      []string        `json:"outputs"`
	Checks       []PlanningCheck `json:"checks"`
	WallTime     int             `json:"wall_time_seconds"`
	MaxAttempts  int             `json:"max_attempts"`
}
type PlanningCheck struct {
	ID       string `json:"check_id"`
	Command  string `json:"command_key"`
	Expected string `json:"expected"`
}
type PlanningQuestion struct {
	ID       string   `json:"question_id"`
	Question string   `json:"question"`
	Options  []string `json:"options"`
	Blocking bool     `json:"blocking"`
}
type PlanningGap struct {
	Node       string `json:"logical_id"`
	Capability string `json:"capability"`
	Reason     string `json:"reason"`
}

func parseGoalBrief(raw []byte) (*GoalBrief, error) {
	if len(raw) > 512*1024 {
		return nil, fmt.Errorf("GoalBrief exceeds bounded proposal size")
	}
	var b GoalBrief
	d := json.NewDecoder(bytes.NewReader(raw))
	d.DisallowUnknownFields()
	d.UseNumber()
	if e := d.Decode(&b); e != nil {
		return nil, e
	}
	if e := d.Decode(new(any)); e != io.EOF {
		return nil, fmt.Errorf("exactly one GoalBrief JSON object required")
	}
	if b.Schema != "GoalBrief/v1" || b.Revision != 1 || b.SupersedesRef != nil {
		return nil, fmt.Errorf("v1 requires a first immutable proposal; revisions need explicit W04/new planning lineage")
	}
	if strings.TrimSpace(b.Title) == "" || len(b.Title) > 500 || len(b.Scope) == 0 || len(b.Deliverables) == 0 || len(b.FailureExits) == 0 || b.Exclusions == nil || b.Facts == nil || b.Nodes == nil || b.OpenQuestions == nil || b.CapabilityGaps == nil || b.VersionVector == nil {
		return nil, fmt.Errorf("complete scope, provenance, outputs, failure exits and explicit unknown arrays required")
	}
	if len(b.Nodes) > 32 || len(b.Facts) > 128 || len(b.OpenQuestions) > 32 || len(b.CapabilityGaps) > 64 {
		return nil, fmt.Errorf("proposal exceeds bounded compilation limits")
	}
	for _, items := range [][]string{b.Scope, b.Exclusions, b.Deliverables, b.FailureExits} {
		for _, v := range items {
			if strings.TrimSpace(v) == "" || len(v) > 4000 {
				return nil, fmt.Errorf("empty or excessive proposal statement")
			}
		}
	}
	if b.Status != "READY" && b.Status != "NEEDS_INPUT" {
		return nil, fmt.Errorf("proposal status must explicitly identify unknowns")
	}
	return &b, nil
}

func (s *Service) planningOwner(tx *sql.Tx, project, actor string) (Principal, error) {
	p := Principal{ID: actor}
	var roles string
	if e := tx.QueryRow("SELECT roles FROM auth_principals WHERE id=? AND revoked=0", actor).Scan(&roles); e != nil {
		return p, Fail(403, "FORBIDDEN", "original intent Owner no longer active")
	}
	if e := json.Unmarshal([]byte(roles), &p.Roles); e != nil {
		return p, e
	}
	rows, e := tx.Query("SELECT project,task,run,restricted FROM auth_grants WHERE principal=?", actor)
	if e != nil {
		return p, e
	}
	defer rows.Close()
	for rows.Next() {
		var g Grant
		if e = rows.Scan(&g.ProjectID, &g.TaskID, &g.RunID, &g.Restricted); e != nil {
			return p, e
		}
		p.Grants = append(p.Grants, g)
	}
	if e = rows.Err(); e != nil {
		return p, e
	}
	rows.Close()
	if e = constrainRemotePrincipal(tx, &p); e != nil {
		return p, e
	}
	if !p.HasRole("OWNER") || !p.Allowed(project, "", "", false) {
		return p, Fail(403, "FORBIDDEN", "original intent Owner grant no longer current")
	}
	return p, nil
}

func (s *Service) planningSnapshot(tx *sql.Tx, project string, task Object) (Object, error) {
	var requirement, actor, rawHash string
	var revision int64
	e := tx.QueryRow("SELECT requirement,actor,raw_hash,accepted_revision FROM intent_plan_bindings WHERE project=? AND planning_task=? AND planning_goal=?", project, task["id"], task["goal_id"]).Scan(&requirement, &actor, &rawHash, &revision)
	if e == sql.ErrNoRows {
		return nil, nil
	}
	if e != nil {
		return nil, e
	}
	if task["task_type"] != "intent_planning" {
		return nil, Fail(422, "GATE_FAILED", "intent planning task type mismatch")
	}
	req, e := load(tx, project, "Requirement", requirement)
	if e != nil {
		return nil, e
	}
	rev, _ := Num(req, "revision")
	if req["status"] != "ACCEPTED" || req["basis"] != "USER_STATED" || rev != revision || rawHash != Digest([]byte(Str(req, "text"))) {
		return nil, Fail(412, "STALE_INPUT", "accepted intent no longer exact")
	}
	if e = s.effective(tx, project, Ref(req, "Requirement")); e != nil {
		return nil, e
	}
	owner, e := s.planningOwner(tx, project, actor)
	if e != nil {
		return nil, e
	}
	ctx, e := load(tx, project, "ContextBundle", Str(task, "context_bundle_id"))
	if e != nil {
		return nil, e
	}
	budget := Object(nil)
	sources := Empty()
	for _, v := range Arr(ctx, "version_vector") {
		ref, ok := v.(map[string]any)
		if !ok {
			return nil, Fail(422, "GATE_FAILED", "invalid planning context reference")
		}
		if e = s.effective(tx, project, ref); e != nil {
			return nil, e
		}
		if ref["entity_type"] == "BudgetPolicy" {
			budget = ref
		}
		if ref["entity_type"] == "Requirement" {
			r, e := version(tx, project, ref)
			if e != nil {
				return nil, e
			}
			sources = append(sources, r)
		}
	}
	if budget == nil {
		return nil, Fail(422, "GATE_FAILED", "planning needs the current budget policy")
	}
	return Object{"requirement": req, "context": ctx, "budget_ref": budget, "sources": sources, "owner": owner.ID, "owner_roles": owner.Roles, "owner_grants": owner.Grants}, nil
}

func planningRaw(snap Object) (*GoalBrief, Object, error) {
	meta, _ := snap["planning"].(map[string]any)
	if meta == nil {
		return nil, nil, fmt.Errorf("planning checks require a private Owner-bound intent")
	}
	artifacts := Arr(snap, "artifacts")
	if len(artifacts) != 1 {
		return nil, nil, fmt.Errorf("one sealed GoalBrief output required")
	}
	entry := artifacts[0].(map[string]any)
	artifact := entry["artifact"].(map[string]any)
	if artifact["evidence_kind"] != "GENERATED" || artifact["media_type"] != "application/json" {
		return nil, nil, fmt.Errorf("GoalBrief must remain GENERATED JSON")
	}
	brief, e := parseGoalBrief(entry["bytes"].([]byte))
	return brief, meta, e
}

func verifyPlanningProvenance(b *GoalBrief, meta Object) error {
	req := meta["requirement"].(map[string]any)
	ctx := meta["context"].(map[string]any)
	if b.ProjectID != Str(req, "project_id") || Hash(b.RawIntentRef) != Hash(Ref(req, "Requirement")) || b.RawIntentHash != Digest([]byte(Str(req, "text"))) || Hash(b.ContextRef) != Hash(Ref(ctx, "ContextBundle")) || Hash(b.VersionVector) != Hash(ctx["version_vector"]) || Hash(b.BudgetPolicyRef) != Hash(meta["budget_ref"]) {
		return fmt.Errorf("proposal provenance or policy differs from exact frozen context")
	}
	allowed := map[string]bool{}
	for _, r := range b.VersionVector {
		allowed[Hash(r)] = true
	}
	rawFact := false
	for _, fact := range b.Facts {
		if strings.TrimSpace(fact.Text) == "" || fact.SourceRefs == nil {
			return fmt.Errorf("fact requires text and explicit source refs")
		}
		for _, r := range fact.SourceRefs {
			if !allowed[Hash(r)] {
				return fmt.Errorf("fact cites an unavailable or stale source")
			}
		}
		switch fact.Basis {
		case "USER_STATED", "OBSERVED":
			found := false
			for _, v := range Arr(meta, "sources") {
				r := v.(map[string]any)
				if r["status"] == "ACCEPTED" && r["basis"] == fact.Basis && Str(r, "text") == fact.Text && len(fact.SourceRefs) == 1 && Hash(fact.SourceRefs[0]) == Hash(Ref(r, "Requirement")) {
					found = true
					if r["id"] == req["id"] {
						rawFact = true
					}
				}
			}
			if !found {
				return fmt.Errorf("authoritative fact must quote an exact accepted source with its original basis")
			}
		case "PROPOSED", "ASSUMED":
		default:
			return fmt.Errorf("unknown fact basis; system recommendations must stay PROPOSED")
		}
	}
	if !rawFact {
		return fmt.Errorf("proposal must include unchanged original USER_STATED intent")
	}
	return nil
}

// v1 deliberately supports a narrow existing execution/check pair. A JSON
// expectation is authorized only when the Owner actually supplied that literal.
// Arbitrary business evaluation needs a declared capability gap, not a fake check.
func planningNodeSupported(n PlanningNode, meta Object) bool {
	if n.Action != "json_report" || len(n.Checks) != 1 || n.Checks[0].Command != "orchestration.json-equals" {
		return false
	}
	expected := n.Checks[0].Expected
	if _, e := Decode([]byte(expected)); e != nil {
		return false
	}
	literal, count, _ := planningJSONAuthorization(meta)
	return count > 0 && literal == expected && len(n.Outputs) == 1 && n.Outputs[0] == "result.json"
}

func planningOrder(b *GoalBrief, meta Object) ([]PlanningNode, error) {
	nodes := map[string]PlanningNode{}
	checks := map[string]bool{}
	allowed := map[string]bool{}
	for _, r := range b.VersionVector {
		allowed[Hash(r)] = true
	}
	for _, n := range b.Nodes {
		if !planningLogicalID.MatchString(n.ID) || !planningCommandKey.MatchString(n.Action) {
			return nil, fmt.Errorf("typed action/logical identifiers required; shell or path strings are not commands")
		}
		if n.ID == "" || len(n.ID) > 80 || strings.TrimSpace(n.Title) == "" || n.Action == "" || n.Dependencies == nil || n.Inputs == nil || len(n.Outputs) == 0 || len(n.Checks) == 0 || n.WallTime < 1 || n.WallTime > 300 || n.MaxAttempts < 1 || n.MaxAttempts > 2 {
			return nil, fmt.Errorf("each node needs bounded execution, concrete outputs and required checks")
		}
		if _, exists := nodes[n.ID]; exists {
			return nil, fmt.Errorf("duplicate logical node")
		}
		nodes[n.ID] = n
		for _, ref := range n.Inputs {
			if !allowed[Hash(ref)] {
				return nil, fmt.Errorf("node input is not in the exact context")
			}
		}
		for _, output := range n.Outputs {
			if strings.TrimSpace(output) == "" {
				return nil, fmt.Errorf("empty output")
			}
		}
		for _, check := range n.Checks {
			if !planningLogicalID.MatchString(check.ID) || !planningCommandKey.MatchString(check.Command) {
				return nil, fmt.Errorf("typed check identifiers required; arbitrary shell is not a verifier")
			}
			if check.ID == "" || checks[check.ID] || check.Command == "" || check.Expected == "" {
				return nil, fmt.Errorf("check IDs must be unique and checks complete")
			}
			checks[check.ID] = true
		}
		if !planningNodeSupported(n, meta) {
			gap := false
			for _, g := range b.CapabilityGaps {
				if g.Node == n.ID && g.Reason != "" && g.Capability != "" {
					gap = true
				}
			}
			if !gap {
				return nil, fmt.Errorf("unsupported action or ungrounded business check needs an explicit capability gap")
			}
		}
	}
	ordered := []PlanningNode{}
	visiting := map[string]bool{}
	done := map[string]bool{}
	var visit func(string) error
	visit = func(id string) error {
		n, ok := nodes[id]
		if !ok {
			return fmt.Errorf("missing dependency; cross-Goal model IDs are not authority")
		}
		if visiting[id] {
			return fmt.Errorf("DAG contains a cycle")
		}
		if done[id] {
			return nil
		}
		visiting[id] = true
		seen := map[string]bool{}
		for _, dep := range n.Dependencies {
			if seen[dep] {
				return fmt.Errorf("duplicate dependency")
			}
			seen[dep] = true
			if e := visit(dep); e != nil {
				return e
			}
		}
		delete(visiting, id)
		done[id] = true
		ordered = append(ordered, n)
		return nil
	}
	for _, n := range b.Nodes {
		if e := visit(n.ID); e != nil {
			return nil, e
		}
	}
	if b.Status == "READY" {
		_, count, sequential := planningJSONAuthorization(meta)
		if count != len(ordered) {
			return nil, fmt.Errorf("business DAG cardinality requires an exact supported Owner instruction")
		}
		if sequential && len(ordered) == 2 && (len(ordered[0].Dependencies) != 0 || len(ordered[1].Dependencies) != 1 || ordered[1].Dependencies[0] != ordered[0].ID) {
			return nil, fmt.Errorf("Owner requested sequential report delivery")
		}
	}
	return ordered, nil
}

func verifyPlanningQuestions(b *GoalBrief) error {
	blocking := false
	ids := map[string]bool{}
	for _, q := range b.OpenQuestions {
		if q.ID == "" || q.Question == "" || q.Options == nil || ids[q.ID] {
			return fmt.Errorf("questions require stable unique identity, wording and explicit options")
		}
		ids[q.ID] = true
		blocking = blocking || q.Blocking
	}
	nodes := map[string]bool{}
	for _, n := range b.Nodes {
		nodes[n.ID] = true
	}
	for _, g := range b.CapabilityGaps {
		if !nodes[g.Node] || g.Capability == "" || g.Reason == "" {
			return fmt.Errorf("capability gap must identify an actual node and missing capability")
		}
	}
	if b.Status == "READY" && (blocking || len(b.CapabilityGaps) > 0 || len(b.Nodes) == 0) {
		return fmt.Errorf("unresolved business choices, capability gaps or empty work cannot be READY")
	}
	if b.Status == "NEEDS_INPUT" && !blocking && len(b.CapabilityGaps) == 0 {
		return fmt.Errorf("NEEDS_INPUT requires a concrete unresolved question or capability")
	}
	return nil
}

func verifyPlanning(snap Object, key string) (string, string) {
	b, meta, e := planningRaw(snap)
	if e == nil {
		switch key {
		case "planning.provenance-v1":
			e = verifyPlanningProvenance(b, meta)
		case "planning.dag-capabilities-v1":
			_, e = planningOrder(b, meta)
		case "planning.open-questions-v1":
			e = verifyPlanningQuestions(b)
		default:
			e = fmt.Errorf("unknown planning verifier")
		}
	}
	if e != nil {
		return "FAIL", e.Error()
	}
	return "PASS", "Current exact provenance and bounded proposal constraints verified; this is not business success or semantic fidelity certification."
}

func planningPrompt(req Object) string {
	return "\nPlanning contract: output exactly one GENERATED application/json GoalBrief/v1. Preserve this exact USER_STATED intent: " + string(Bytes(req)) + ". Never promote suggestions to facts. All scope/deliverable/DAG choices are PROPOSED. Required fields: schema, project_id, raw_intent_ref, raw_intent_hash (sha256 of raw text), context_ref, version_vector, revision=1, supersedes_ref=null, status=READY|NEEDS_INPUT, title, facts [{text,basis,source_refs}], scope [], exclusions [], deliverables [], nodes [{logical_id,title,action,depends_on:[],input_refs:[],outputs:[],checks:[{check_id,command_key,expected}],wall_time_seconds:1..300,max_attempts:1..2}], budget_policy_ref, failure_exits [], open_questions [{question_id,question,options:[],blocking}], capability_gaps [{logical_id,capability,reason}]. Use the request's exact ContextBundle reference/version_vector and its BudgetPolicy reference. Authoritative facts must exactly quote accepted Requirements. Only implemented action json_report with orchestration.json-equals is compilable in v1, and its expected JSON literal must be the exact positive Owner instruction: 请生成一份 <JSON object> JSON 报告。 or 请先后生成两份 <JSON object> JSON 报告。 (请按先后顺序生成两份 is also supported), or 请交付 <JSON object>。 Mentioning JSON elsewhere does not authorize delivery. Nodes/output count and ordering must match that instruction; output name is result.json. Other actions/checks require capability_gaps and NEEDS_INPUT; missing business facts require explicit blocking questions. Do not invent success thresholds, source facts, shell commands, permissions or user answers. A NEEDS_INPUT proposal may have nodes=[] when the business choice must precede any safe task."
}
