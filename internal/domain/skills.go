package domain

import (
	"context"
	"database/sql"
	"researchos.local/research-os/adapters/knowledge"
	skillseval "researchos.local/research-os/evaluation/skills"
	"strings"
)

func init() {
	for _, name := range []string{"createSkillCandidate", "getSkillVersion", "listSkillVersion", "promoteSkill"} {
		implemented[name] = true
	}
}

// Skill payloads are sealed JSON artifacts. The external extraction is data;
// it cannot grant host capabilities or supply a second ProjectState.
func (s *Service) skillDocument(tx *sql.Tx, project string, ref Object) (Object, error) {
	a, e := version(tx, project, ref)
	if e != nil {
		return nil, e
	}
	if a["kind"] != "SKILL" || a["access_class"] != "PROJECT" {
		return nil, Fail(422, "GATE_FAILED", "sealed project skill artifact required")
	}
	v, e := s.artifactJSON(tx, project, ref)
	if e != nil {
		return nil, e
	}
	doc, ok := v.(map[string]any)
	if !ok || doc["format"] != "researchos.skill.v1" || doc["project_state"] != "CURRENT_PROJECTION" {
		return nil, Fail(422, "GATE_FAILED", "versioned skill document and current ProjectState projection required")
	}
	allowed := map[string]bool{"format": true, "project_state": true, "inputs": true, "outputs": true, "applicable_tasks": true, "limitations": true, "side_effects": true, "claims": true, "conflicts": true, "extraction": true, "suite_case_ids": true, "negative_case_ids": true}
	for k := range doc {
		if !allowed[k] {
			return nil, Fail(422, "GATE_FAILED", "unrecognized skill payload field")
		}
	}
	for _, k := range []string{"inputs", "outputs", "applicable_tasks", "limitations", "suite_case_ids", "negative_case_ids"} {
		if len(Arr(doc, k)) == 0 {
			return nil, Fail(422, "GATE_FAILED", "skill declaration missing "+k)
		}
		for _, x := range Arr(doc, k) {
			if v, ok := x.(string); !ok || strings.TrimSpace(v) == "" {
				return nil, Fail(422, "GATE_FAILED", "invalid skill declaration")
			}
		}
	}
	if len(Arr(doc, "side_effects")) != 0 {
		return nil, Fail(422, "GATE_FAILED", "fixture skill cannot request side effects")
	}
	if len(Arr(doc, "claims")) == 0 {
		return nil, Fail(422, "GATE_FAILED", "attributed knowledge claims required")
	}
	return doc, nil
}

func (s *Service) validateSkillSources(tx *sql.Tx, project string, b, doc Object) error {
	expected, refs := Arr(b, "expected_source_ids"), Arr(b, "source_refs")
	if len(expected) == 0 || len(expected) != len(refs) {
		return Fail(422, "GATE_FAILED", "exact source manifest required")
	}
	refByID := map[string]Object{}
	for _, v := range refs {
		r, ok := v.(map[string]any)
		if !ok || r["entity_type"] != "Artifact" || refByID[Str(r, "id")] != nil {
			return Fail(422, "GATE_FAILED", "unique source artifact references required")
		}
		a, e := version(tx, project, r)
		if e != nil {
			return e
		}
		if a["kind"] != "SOURCE_SNAPSHOT" || a["access_class"] != "PROJECT" {
			return Fail(422, "GATE_FAILED", "source snapshot required")
		}
		refByID[Str(r, "id")] = r
	}
	ids, outcomes := []string{}, []knowledge.Outcome{}
	processed, failed := map[string]bool{}, map[string]bool{}
	for _, v := range Arr(b, "processed_source_ids") {
		id, ok := v.(string)
		if !ok || processed[id] {
			return Fail(422, "GATE_FAILED", "duplicate processed source")
		}
		processed[id] = true
	}
	for _, v := range Arr(b, "failed_source_ids") {
		id, ok := v.(string)
		if !ok || failed[id] {
			return Fail(422, "GATE_FAILED", "duplicate failed source")
		}
		failed[id] = true
	}
	entries := map[string]Object{}
	for _, v := range Arr(doc, "extraction") {
		o, ok := v.(map[string]any)
		if !ok || entries[Str(o, "source_id")] != nil {
			return Fail(422, "GATE_FAILED", "duplicate extraction entry")
		}
		entries[Str(o, "source_id")] = o
	}
	for _, v := range expected {
		id, ok := v.(string)
		if !ok || refByID[id] == nil || entries[id] == nil {
			return Fail(422, "GATE_FAILED", "missing source or extraction entry")
		}
		entry := entries[id]
		done, ok := entry["processed"].(bool)
		if !ok || done != processed[id] || !done != failed[id] {
			return Fail(422, "GATE_FAILED", "extraction ledger mismatch")
		}
		failure, _ := entry["failure"].(string)
		outcomes = append(outcomes, knowledge.Outcome{SourceID: id, Processed: done, Failure: failure})
		ids = append(ids, id)
		if done {
			if e := s.effective(tx, project, refByID[id]); e != nil {
				return e
			}
		}
	}
	if len(entries) != len(expected) {
		return Fail(422, "GATE_FAILED", "unexpected extraction entry")
	}
	coverage, e := knowledge.Reconcile(ids, outcomes)
	if e != nil {
		return Fail(422, "GATE_FAILED", e.Error())
	}
	if len(coverage.Processed) != len(processed) || len(coverage.Failed) != len(failed) {
		return Fail(422, "GATE_FAILED", "source lists omit extractor results")
	}
	for _, v := range Arr(doc, "claims") {
		claim, ok := v.(map[string]any)
		if !ok || strings.TrimSpace(Str(claim, "text")) == "" || strings.TrimSpace(Str(claim, "locator")) == "" {
			return Fail(422, "GATE_FAILED", "located source claim required")
		}
		r, ok := claim["source_ref"].(map[string]any)
		if !ok || !processed[Str(r, "id")] || Hash(r) != Hash(refByID[Str(r, "id")]) {
			return Fail(422, "GATE_FAILED", "claim provenance mismatch")
		}
		// ponytail: This lexical check is defense in depth; host capability isolation is the authority boundary.
		lower := strings.ToLower(Str(claim, "text"))
		for _, term := range []string{"ignore previous", "system prompt", "api key", "secret key", "global config", "disable verification", "grant permission"} {
			if strings.Contains(lower, term) {
				return Fail(422, "GATE_FAILED", "untrusted instruction in extracted claim")
			}
		}
	}
	conflicts := map[string]bool{}
	for _, v := range Arr(b, "conflict_ids") {
		id, ok := v.(string)
		if !ok || conflicts[id] {
			return Fail(422, "GATE_FAILED", "duplicate conflict")
		}
		conflicts[id] = true
	}
	if len(conflicts) != len(Arr(doc, "conflicts")) {
		return Fail(422, "GATE_FAILED", "conflict ledger mismatch")
	}
	for _, v := range Arr(doc, "conflicts") {
		entry, ok := v.(map[string]any)
		if !ok || !conflicts[Str(entry, "conflict_id")] {
			return Fail(422, "GATE_FAILED", "unresolved conflict or applicability conditions required")
		}
		c, e := load(tx, project, "Conflict", Str(entry, "conflict_id"))
		if e != nil {
			return e
		}
		if len(Arr(c, "subject_refs")) < 2 {
			return Fail(422, "GATE_FAILED", "source conflict record required")
		}
		switch c["status"] {
		case "OPEN":
			if entry["resolution"] != "UNRESOLVED" {
				return Fail(422, "GATE_FAILED", "open source conflict must remain unresolved")
			}
		case "RESOLVED":
			if entry["resolution"] != "CONDITIONAL" || len(Arr(entry, "conditions")) == 0 {
				return Fail(422, "GATE_FAILED", "resolved contradiction requires explicit applicability conditions")
			}
			if e := s.resolvedSkillSourceConflict(tx, project, c, entry); e != nil {
				return e
			}
		default:
			return Fail(422, "GATE_FAILED", "source conflict has no accepted resolution")
		}
		for _, v := range Arr(c, "subject_refs") {
			r := v.(map[string]any)
			if !processed[Str(r, "id")] || Hash(r) != Hash(refByID[Str(r, "id")]) {
				return Fail(422, "GATE_FAILED", "conflict source mismatch")
			}
		}
	}
	return nil
}

func (s *Service) skillConflictLedgerCurrent(tx *sql.Tx, project string, o Object) error {
	manifest := map[string]bool{}
	for _, v := range Arr(o, "source_refs") {
		r := v.(map[string]any)
		manifest[Str(r, "entity_type")+":"+Str(r, "id")] = true
	}
	disclosed := map[string]bool{}
	for _, v := range Arr(o, "conflict_ids") {
		disclosed[v.(string)] = true
	}
	rows, e := tx.Query("SELECT body FROM domain_objects WHERE project=? AND kind='Conflict' AND json_extract(body,'$.status') IN ('OPEN','RESOLVED')", project)
	if e != nil {
		return e
	}
	defer rows.Close()
	for rows.Next() {
		var raw string
		if e = rows.Scan(&raw); e != nil {
			return e
		}
		c, e := Decode([]byte(raw))
		if e != nil {
			return e
		}
		if !sourceEvidenceConflict(c) {
			continue
		}
		for _, v := range Arr(c, "subject_refs") {
			r := v.(map[string]any)
			if manifest[Str(r, "entity_type")+":"+Str(r, "id")] && !disclosed[Str(c, "id")] {
				return Fail(422, "GATE_FAILED", "relevant source conflict omitted from skill ledger")
			}
		}
	}
	return rows.Err()
}

func (s *Service) resolvedSkillSourceConflict(tx *sql.Tx, project string, c, entry Object) error {
	if !sourceEvidenceConflict(c) || Str(c, "resolution_proposal_id") == "" {
		return Fail(422, "GATE_FAILED", "formal source conflict resolution required")
	}
	state, e := singleton(tx, project, "ProjectState")
	if e != nil {
		return e
	}
	for _, v := range Arr(state, "current_decision_refs") {
		ref := v.(map[string]any)
		d, e := version(tx, project, ref)
		if e != nil {
			return e
		}
		oldRef, ok := d["subject_ref"].(map[string]any)
		if !ok || oldRef["entity_type"] != "Conflict" || oldRef["id"] != c["id"] {
			continue
		}
		resolved, e := s.resolvedSourceDecision(tx, project, d, oldRef)
		if e != nil {
			return e
		}
		if !resolved {
			continue
		}
		for _, condition := range Arr(entry, "conditions") {
			if condition == d["rationale"] {
				return nil
			}
		}
	}
	return Fail(422, "GATE_FAILED", "skill conditions lack current accepted source decision")
}

func (s *Service) createSkillCandidate(tx *sql.Tx, p Principal, project string, b Object) (Object, error) {
	if len(Arr(b, "allowed_capabilities")) != 0 {
		return nil, Fail(403, "FORBIDDEN", "external skill cannot grant host capabilities")
	}
	ref := b["content_artifact_ref"].(map[string]any)
	doc, e := s.skillDocument(tx, project, ref)
	if e != nil {
		return nil, e
	}
	a, e := version(tx, project, ref)
	if e != nil {
		return nil, e
	}
	if Hash(a["input_refs"]) != Hash(b["source_refs"]) {
		return nil, Fail(422, "GATE_FAILED", "candidate sources differ from sealed generator input manifest")
	}
	if a["produced_by"] != p.ID {
		return nil, Fail(403, "FORBIDDEN", "candidate author must own sealed skill artifact")
	}
	if e = s.validateSkillSources(tx, project, b, doc); e != nil {
		return nil, e
	}
	var activeID sql.NullString
	e = tx.QueryRow("SELECT id FROM domain_objects WHERE project=? AND kind='SkillVersion' AND json_extract(body,'$.skill_name')=? AND json_extract(body,'$.status')='ACTIVE' LIMIT 1", project, b["skill_name"]).Scan(&activeID)
	if e != nil && e != sql.ErrNoRows {
		return nil, e
	}
	if activeID.Valid && activeID.String != b["baseline_skill_id"] {
		return nil, Fail(409, "STATE_CONFLICT", "active skill must be the declared baseline")
	}
	if b["baseline_skill_id"] != nil {
		old, e := load(tx, project, "SkillVersion", Str(b, "baseline_skill_id"))
		if e != nil {
			return nil, e
		}
		if old["skill_name"] != b["skill_name"] || old["status"] != "ACTIVE" {
			return nil, Fail(422, "GATE_FAILED", "current same-name baseline required")
		}
	}
	if b["experiment_id"] != nil {
		if _, e = load(tx, project, "Experiment", Str(b, "experiment_id")); e != nil {
			return nil, e
		}
	}
	var existing int
	if e = tx.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='SkillVersion' AND json_extract(body,'$.skill_name')=? AND json_extract(body,'$.version')=?", project, b["skill_name"], b["version"]).Scan(&existing); e != nil {
		return nil, e
	}
	if existing != 0 {
		return nil, Fail(409, "STATE_CONFLICT", "skill version already exists")
	}
	o := Merge(Base(project), b)
	Merge(o, Object{"status": "CANDIDATE", "acceptance_id": nil, "rollback_skill_id": nil})
	return o, s.put(tx, "SkillVersion", o)
}

func (s *Service) skillCurrent(tx *sql.Tx, project string, o Object) error {
	if len(Arr(o, "failed_source_ids")) != 0 {
		return Fail(422, "GATE_FAILED", "partial extraction cannot activate")
	}
	if o["license_expression"] == nil {
		return Fail(422, "GATE_FAILED", "source rights unresolved")
	}
	if len(Arr(o, "allowed_capabilities")) != 0 {
		return Fail(403, "FORBIDDEN", "skill host capabilities denied")
	}
	if e := s.effective(tx, project, o["content_artifact_ref"].(map[string]any)); e != nil {
		return e
	}
	for _, v := range Arr(o, "source_refs") {
		if e := s.effective(tx, project, v.(map[string]any)); e != nil {
			return e
		}
	}
	if e := skillOpenSourceConflict(tx, project, Arr(o, "source_refs")); e != nil {
		return e
	}
	for _, v := range Arr(o, "conflict_ids") {
		c, e := load(tx, project, "Conflict", v.(string))
		if e != nil {
			return e
		}
		if c["status"] == "OPEN" {
			return Fail(409, "STATE_CONFLICT", "source conflict unresolved")
		}
	}
	return nil
}

// A candidate's conflict_ids are only a disclosure ledger. Current conflicts
// concerning its source manifest are server state, including conflicts opened
// after its Experiment or acceptance.
func skillOpenSourceConflict(tx *sql.Tx, project string, sources []any) error {
	ids := map[string]bool{}
	for _, v := range sources {
		r := v.(map[string]any)
		ids[Str(r, "entity_type")+":"+Str(r, "id")] = true
	}
	rows, e := tx.Query("SELECT body FROM domain_objects WHERE project=? AND kind='Conflict' AND json_extract(body,'$.status')='OPEN'", project)
	if e != nil {
		return e
	}
	defer rows.Close()
	for rows.Next() {
		var raw string
		if e = rows.Scan(&raw); e != nil {
			return e
		}
		c, e := Decode([]byte(raw))
		if e != nil {
			return e
		}
		for _, field := range []string{"subject_refs", "blocks_refs"} {
			for _, v := range Arr(c, field) {
				r, ok := v.(map[string]any)
				if ok && ids[Str(r, "entity_type")+":"+Str(r, "id")] {
					return Fail(409, "STATE_CONFLICT", "source conflict unresolved")
				}
			}
		}
	}
	return rows.Err()
}

func (s *Service) skillExperiment(tx *sql.Tx, project string, o, doc Object) (Object, Object, error) {
	if o["experiment_id"] == nil {
		return nil, nil, Fail(422, "GATE_FAILED", "frozen experiment required")
	}
	x, e := load(tx, project, "Experiment", Str(o, "experiment_id"))
	if e != nil {
		return nil, nil, e
	}
	if x["status"] != "COMPLETED" || x["outcome"] != "IMPROVED" || x["measurement_mode"] != "FIXTURE" || Hash(x["candidate_ref"]) != Hash(o["content_artifact_ref"]) {
		return nil, nil, Fail(422, "GATE_FAILED", "completed paired candidate experiment required")
	}
	previousCases, previousNegative := []string{}, []string{}
	if o["baseline_skill_id"] != nil {
		old, e := load(tx, project, "SkillVersion", Str(o, "baseline_skill_id"))
		if e != nil {
			return nil, nil, e
		}
		if Hash(x["baseline_refs"]) != Hash([]any{old["content_artifact_ref"]}) {
			return nil, nil, Fail(422, "GATE_FAILED", "old skill baseline mismatch")
		}
		oldDoc, e := s.skillDocument(tx, project, old["content_artifact_ref"].(map[string]any))
		if e != nil {
			return nil, nil, e
		}
		for _, v := range Arr(oldDoc, "suite_case_ids") {
			previousCases = append(previousCases, v.(string))
		}
		for _, v := range Arr(oldDoc, "negative_case_ids") {
			previousNegative = append(previousNegative, v.(string))
		}
	}
	receipt, e := s.experimentAcceptance(tx, project, x, Str(x, "acceptance_id"))
	if e != nil {
		return nil, nil, e
	}
	if Hash(doc["suite_case_ids"]) != Hash(mustExperimentCaseIDs(x)) {
		return nil, nil, Fail(422, "GATE_FAILED", "skill suite differs from frozen experiment")
	}
	var observations Object
	for _, v := range Arr(receipt, "artifact_refs") {
		ref := v.(map[string]any)
		a, e := version(tx, project, ref)
		if e != nil {
			return nil, nil, e
		}
		if a["kind"] != "REPORT" || a["media_type"] != "application/json" {
			continue
		}
		raw, e := s.artifactJSON(tx, project, ref)
		if e != nil {
			return nil, nil, e
		}
		item, ok := raw.(map[string]any)
		if ok && item["experiment_id"] == x["id"] {
			if observations != nil {
				return nil, nil, Fail(422, "GATE_FAILED", "ambiguous skill observation")
			}
			observations = item
		}
	}
	if observations == nil {
		return nil, nil, Fail(422, "GATE_FAILED", "sealed skill observation missing")
	}
	var pair Object
	for _, v := range Arr(observations, "observations") {
		r := v.(map[string]any)
		if r["metric_id"] == "skill_success" {
			pair = r
		}
	}
	if pair == nil || Hash(pair["case_ids"]) != Hash(doc["suite_case_ids"]) {
		return nil, nil, Fail(422, "GATE_FAILED", "skill metric and cases required")
	}
	ids, before, after := []string{}, []string{}, []string{}
	for _, v := range Arr(doc, "suite_case_ids") {
		ids = append(ids, v.(string))
	}
	for _, v := range Arr(pair, "baseline") {
		text, ok := v.(string)
		if !ok {
			return nil, nil, Fail(422, "GATE_FAILED", "paired boolean required")
		}
		before = append(before, text)
	}
	for _, v := range Arr(pair, "candidate") {
		text, ok := v.(string)
		if !ok {
			return nil, nil, Fail(422, "GATE_FAILED", "paired boolean required")
		}
		after = append(after, text)
	}
	declaredNegative := []string{}
	for _, v := range Arr(doc, "negative_case_ids") {
		declaredNegative = append(declaredNegative, v.(string))
	}
	negative, e := skillseval.TrustedSuite(ids, declaredNegative, previousCases, previousNegative)
	if e != nil {
		return nil, nil, Fail(422, "GATE_FAILED", e.Error())
	}
	if e = skillseval.Compare(ids, before, after, negative); e != nil {
		return nil, nil, Fail(422, "GATE_FAILED", e.Error())
	}
	return x, receipt, nil
}

func mustExperimentCaseIDs(x Object) []any { ids, _ := experimentCaseIDs(x); return ids }

func skillContractHash(o, x Object) string {
	return Hash([]any{"W15-skill-v1", Ref(o, "SkillVersion"), x["preregistration_hash"], x["acceptance_id"]})
}

func (s *Service) acceptSkill(tx *sql.Tx, p Principal, project string, b Object) (Object, error) {
	if !p.HasRole("VERIFIER") || !p.Allowed(project, "", "", false) {
		return nil, Fail(403, "FORBIDDEN", "independent verifier required")
	}
	r := b["subject_ref"].(map[string]any)
	o, e := load(tx, project, "SkillVersion", Str(r, "id"))
	if e != nil {
		return nil, e
	}
	if o["status"] != "CANDIDATE" || Hash(r) != Hash(Ref(o, "SkillVersion")) {
		return nil, Fail(412, "STALE_INPUT", "current candidate required")
	}
	if e = s.skillCurrent(tx, project, o); e != nil {
		return nil, e
	}
	doc, e := s.skillDocument(tx, project, o["content_artifact_ref"].(map[string]any))
	if e != nil {
		return nil, e
	}
	if e = s.validateSkillSources(tx, project, o, doc); e != nil {
		return nil, e
	}
	if e = s.skillConflictLedgerCurrent(tx, project, o); e != nil {
		return nil, e
	}
	x, experimentReceipt, e := s.skillExperiment(tx, project, o, doc)
	if e != nil {
		return nil, e
	}
	if b["contract_hash"] != skillContractHash(o, x) {
		return nil, Fail(422, "GATE_FAILED", "skill contract changed")
	}
	a, e := version(tx, project, o["content_artifact_ref"].(map[string]any))
	if e != nil {
		return nil, e
	}
	ownerRoot, e := authorityRoot(tx, Str(a, "produced_by"))
	if e != nil {
		return nil, e
	}
	verifierRoot, e := authorityRoot(tx, p.ID)
	if e != nil {
		return nil, e
	}
	if ownerRoot == verifierRoot || p.ID == experimentReceipt["verifier_principal_id"] && p.ID == a["produced_by"] {
		return nil, Fail(403, "FORBIDDEN", "candidate author cannot accept own skill")
	}
	state, e := singleton(tx, project, "ProjectState")
	if e != nil {
		return nil, e
	}
	if Hash(b["policy_revision"]) != Hash(state["policy_revision"]) {
		return nil, Fail(412, "STALE_INPUT", "policy changed")
	}
	proof, e := s.serverArtifact(tx, project, p.ID, "REPORT", Bytes(Object{"skill_ref": r, "experiment_ref": Ref(x, "Experiment"), "source_refs": o["source_refs"], "project_state_ref": Ref(state, "ProjectState"), "checks": []any{"source-coverage", "provenance-conflicts", "host-permission", "frozen-paired-suite", "independence"}}), []any{r, Ref(x, "Experiment")})
	if e != nil {
		return nil, e
	}
	checks := Empty()
	for _, id := range []string{"source-coverage", "provenance-conflicts", "host-permission", "frozen-paired-suite", "independence"} {
		checks = append(checks, Object{"check_id": id, "status": "PASS", "evidence_refs": []any{Ref(proof, "Artifact")}, "command_key": "test.skills", "actual": "server recomputed from sealed current evidence", "exit_code": 0, "started_at": Now(), "finished_at": Now()})
	}
	receipt := Object{"id": ID(), "project_id": project, "revision": 1, "created_at": Now(), "subject_ref": r, "run_id": nil, "contract_hash": skillContractHash(o, x), "input_refs": []any{r, Ref(x, "Experiment")}, "artifact_refs": []any{Ref(proof, "Artifact")}, "checks": checks, "verdict": "PASS", "verifier_principal_id": p.ID, "executor_principal_ids": []any{a["produced_by"]}, "independence_basis": "DETERMINISTIC_SERVICE", "blocking_conflict_ids": Empty(), "qualification_ids": Empty(), "policy_revision": state["policy_revision"], "measurement_mode": "FIXTURE", "reason": "Independent fixture skill validation; no live qualification."}
	receipt["receipt_hash"] = Receipt(receipt)
	return receipt, s.put(tx, "AcceptanceReceipt", receipt)
}

func (s *Service) promoteSkill(tx *sql.Tx, project, id string, b Object) (Object, error) {
	o, e := load(tx, project, "SkillVersion", id)
	if e != nil {
		return nil, e
	}
	if o["status"] != "CANDIDATE" {
		return nil, Fail(409, "STATE_CONFLICT", "candidate required")
	}
	if e = s.skillCurrent(tx, project, o); e != nil {
		return nil, e
	}
	receipt, e := load(tx, project, "AcceptanceReceipt", Str(b, "acceptance_id"))
	if e != nil {
		return nil, e
	}
	if receipt["verdict"] != "PASS" || receipt["receipt_hash"] != Receipt(receipt) || Hash(receipt["subject_ref"]) != Hash(Ref(o, "SkillVersion")) || receipt["measurement_mode"] != "FIXTURE" {
		return nil, Fail(422, "GATE_FAILED", "current independent skill acceptance required")
	}
	doc, e := s.skillDocument(tx, project, o["content_artifact_ref"].(map[string]any))
	if e != nil {
		return nil, e
	}
	if e = s.validateSkillSources(tx, project, o, doc); e != nil {
		return nil, e
	}
	if e = s.skillConflictLedgerCurrent(tx, project, o); e != nil {
		return nil, e
	}
	x, _, e := s.skillExperiment(tx, project, o, doc)
	if e != nil {
		return nil, e
	}
	if receipt["contract_hash"] != skillContractHash(o, x) || b["rollback_skill_id"] != o["baseline_skill_id"] {
		return nil, Fail(422, "GATE_FAILED", "frozen comparison or rollback mismatch")
	}
	state, e := singleton(tx, project, "ProjectState")
	if e != nil {
		return nil, e
	}
	if Hash(receipt["policy_revision"]) != Hash(state["policy_revision"]) {
		return nil, Fail(412, "STALE_INPUT", "skill acceptance policy changed")
	}
	var verifier int
	if e = tx.QueryRow("SELECT count(*) FROM auth_principals p WHERE p.id=? AND p.revoked=0 AND EXISTS (SELECT 1 FROM json_each(p.roles) WHERE value='VERIFIER') AND EXISTS (SELECT 1 FROM auth_grants g WHERE g.principal=p.id AND g.project=? AND g.task='' AND g.run='')", receipt["verifier_principal_id"], project).Scan(&verifier); e != nil {
		return nil, e
	}
	if verifier != 1 {
		return nil, Fail(403, "FORBIDDEN", "independent verifier grant withdrawn")
	}
	var activeID sql.NullString
	e = tx.QueryRow("SELECT id FROM domain_objects WHERE project=? AND kind='SkillVersion' AND json_extract(body,'$.skill_name')=? AND json_extract(body,'$.status')='ACTIVE' LIMIT 1", project, o["skill_name"]).Scan(&activeID)
	if e != nil && e != sql.ErrNoRows {
		return nil, e
	}
	if activeID.Valid && activeID.String != o["baseline_skill_id"] {
		return nil, Fail(409, "STATE_CONFLICT", "active skill changed since comparison")
	}
	var old Object
	if o["baseline_skill_id"] != nil {
		old, e = load(tx, project, "SkillVersion", Str(o, "baseline_skill_id"))
		if e != nil {
			return nil, e
		}
		if old["status"] != "ACTIVE" || old["skill_name"] != o["skill_name"] {
			return nil, Fail(409, "STATE_CONFLICT", "baseline is no longer active")
		}
	}
	if e = bump(o); e != nil {
		return nil, e
	}
	o["status"] = "EVALUATING"
	if e = s.put(tx, "SkillVersion", o); e != nil {
		return nil, e
	}
	if e = bump(o); e != nil {
		return nil, e
	}
	o["status"] = "QUALIFIED"
	o["acceptance_id"] = receipt["id"]
	if e = s.put(tx, "SkillVersion", o); e != nil {
		return nil, e
	}
	if e = bump(o); e != nil {
		return nil, e
	}
	o["status"] = "ACTIVE"
	o["rollback_skill_id"] = b["rollback_skill_id"]
	if e = s.put(tx, "SkillVersion", o); e != nil {
		return nil, e
	}
	if old != nil {
		if e = bump(old); e != nil {
			return nil, e
		}
		old["status"] = "RETIRED"
		if e = s.put(tx, "SkillVersion", old); e != nil {
			return nil, e
		}
	}
	return o, nil
}

// ResolveActiveSkill is the use boundary. Each call rechecks source validity;
// metadata from a past successful promotion never grants stale content access.
func (s *Service) ResolveActiveSkill(tx *sql.Tx, project, id string) (Object, error) {
	o, e := load(tx, project, "SkillVersion", id)
	if e != nil {
		return nil, e
	}
	if o["status"] != "ACTIVE" {
		return nil, Fail(409, "STATE_CONFLICT", "skill inactive")
	}
	if e = s.skillCurrent(tx, project, o); e != nil {
		return nil, e
	}
	return o, nil
}

func (s *Service) GetActiveSkillContext(ctx context.Context, token, project, id string) (Object, error) {
	tx, e := s.DB.BeginTx(ctx, nil)
	if e != nil {
		return nil, e
	}
	defer tx.Rollback()
	p, e := authenticate(tx, token)
	if e != nil {
		return nil, e
	}
	if !p.Allowed(project, "", "", false) {
		return nil, Fail(404, "NOT_FOUND", "skill unavailable")
	}
	o, e := s.ResolveActiveSkill(tx, project, id)
	if e != nil {
		return nil, e
	}
	if !s.visible(tx, p, project, o) {
		return nil, Fail(404, "NOT_FOUND", "skill unavailable")
	}
	doc, e := s.skillDocument(tx, project, o["content_artifact_ref"].(map[string]any))
	if e != nil {
		return nil, e
	}
	state, e := singleton(tx, project, "ProjectState")
	if e != nil {
		return nil, e
	}
	return Object{"skill_ref": Ref(o, "SkillVersion"), "project_state": state, "document": doc}, nil
}

func (s *Service) freezeSkillsForSource(tx *sql.Tx, project, sourceID string) error {
	rows, e := tx.Query("SELECT body FROM domain_objects WHERE project=? AND kind='SkillVersion' AND json_extract(body,'$.status')='ACTIVE'", project)
	if e != nil {
		return e
	}
	selected := []Object{}
	for rows.Next() {
		var raw string
		if e = rows.Scan(&raw); e != nil {
			break
		}
		o, err := Decode([]byte(raw))
		if err != nil {
			e = err
			break
		}
		for _, v := range Arr(o, "source_refs") {
			if Str(v.(map[string]any), "id") == sourceID {
				selected = append(selected, o)
				break
			}
		}
	}
	if e == nil {
		e = rows.Err()
	}
	rows.Close()
	if e != nil {
		return e
	}
	for _, o := range selected {
		if e = bump(o); e != nil {
			return e
		}
		o["status"] = "FROZEN"
		if e = s.put(tx, "SkillVersion", o); e != nil {
			return e
		}
	}
	return nil
}
