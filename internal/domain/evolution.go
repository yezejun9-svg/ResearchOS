//go:build windows

package domain

import (
	"context"
	"database/sql"
	"fmt"
	"os"
	"path/filepath"
	"researchos.local/research-os/evaluation/evolution"
	"time"
)

var evolutionOperations = map[string]bool{"createSystemCandidate": true, "getSystemCandidate": true, "listSystemCandidate": true, "actOnSystemCandidate": true}

func init() {
	for k := range evolutionOperations {
		implemented[k] = true
	}
}

func evolutionPlan(x Object) Object {
	o := Object{}
	for _, k := range []string{"scope", "candidate_artifact_ref", "stable_artifact_ref", "isolated_workspace_id", "baseline_suite_ref", "baseline_policy_hash", "changed_paths_manifest_ref", "experiment_id", "migration_plan_ref", "rollback_plan_ref", "independent_supervisor_id"} {
		o[k] = x[k]
	}
	return o
}
func evolutionHost(tx *sql.Tx, project string) (Object, error) {
	var raw string
	if e := tx.QueryRow("SELECT body FROM evolution_hosts WHERE project=?", project).Scan(&raw); e != nil {
		return nil, Fail(503, "RESOURCE_UNAVAILABLE", "trusted W16 fixture supervisor not registered")
	}
	return Decode([]byte(raw))
}
func (s *Service) evolutionBytes(tx *sql.Tx, project string, ref Object) (Object, []byte, error) {
	if ref["entity_type"] != "Artifact" {
		return nil, nil, Fail(422, "GATE_FAILED", "sealed artifact required")
	}
	if e := s.effective(tx, project, ref); e != nil {
		return nil, nil, e
	}
	a, e := version(tx, project, ref)
	if e != nil {
		return nil, nil, e
	}
	if a["measurement_mode"] != "FIXTURE" || a["access_class"] != "PROJECT" {
		return nil, nil, Fail(403, "FORBIDDEN", "W16 development accepts only public fixture artifacts")
	}
	var raw []byte
	if e = tx.QueryRow("SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1", project, a["storage_key"]).Scan(&raw); e != nil {
		return nil, nil, e
	}
	if Digest(raw) != a["content_hash"] {
		return nil, nil, Fail(422, "CONTENT_HASH_MISMATCH", "frozen artifact bytes changed")
	}
	return a, raw, nil
}

// RegisterEvolutionFixture is trusted local test-host provisioning, not an HTTP
// operation or OS-service qualification. It can only register a fresh temp root.
func (s *Service) RegisterEvolutionFixture(ctx context.Context, project, supervisorID, releasePrincipal, root string, stable, suite, rollback Object) error {
	return s.registerEvolutionFixture(ctx, project, supervisorID, releasePrincipal, root, stable, suite, rollback, false)
}

// RegisterEvolutionReleaseFixture is a host-only same-user mechanism fixture.
// Its host remains os_service_qualified=false and cannot enable LIVE release.
func (s *Service) RegisterEvolutionReleaseFixture(ctx context.Context, project, supervisorID, releasePrincipal, root string, stable, suite, rollback Object) error {
	return s.registerEvolutionFixture(ctx, project, supervisorID, releasePrincipal, root, stable, suite, rollback, true)
}

func (s *Service) registerEvolutionFixture(ctx context.Context, project, supervisorID, releasePrincipal, root string, stable, suite, rollback Object, releaseMechanism bool) error {
	abs, e := filepath.Abs(root)
	if e != nil {
		return e
	}
	real, e := filepath.EvalSymlinks(abs)
	if e != nil || real != abs {
		return fmt.Errorf("plain isolated fixture root required")
	}
	temp, e := filepath.Abs(os.TempDir())
	if e != nil {
		return e
	}
	rel, e := filepath.Rel(temp, abs)
	if e != nil || !filepath.IsLocal(rel) || rel == "." {
		return fmt.Errorf("fixture root must be a new child of OS temp")
	}
	entries, e := os.ReadDir(abs)
	if e != nil || len(entries) != 0 {
		return fmt.Errorf("empty fixture root required")
	}
	tx, e := s.DB.BeginTx(ctx, nil)
	if e != nil {
		return e
	}
	defer tx.Rollback()
	_, stableBytes, e := s.evolutionBytes(tx, project, stable)
	if e != nil {
		return e
	}
	_, b, e := s.evolutionBytes(tx, project, suite)
	if e != nil {
		return e
	}
	if string(b) != string(evolution.Bytes(evolution.Suite())) {
		return fmt.Errorf("suite must equal trusted built-in suite including negative labels")
	}
	if _, _, e = s.evolutionBytes(tx, project, rollback); e != nil {
		return e
	}
	var principalRaw string
	if e = tx.QueryRow("SELECT roles FROM auth_principals WHERE id=? AND revoked=0", releasePrincipal).Scan(&principalRaw); e != nil {
		return e
	}
	h := Object{"supervisor_id": supervisorID, "release_principal": releasePrincipal, "root": abs, "stable_ref": stable, "suite_ref": suite, "rollback_ref": rollback, "policy_hash": Digest(evolution.Bytes(evolution.Policy())), "scope": evolution.Scope, "os_service_qualified": false}
	if releaseMechanism {
		h["release_mechanism"] = "R2_NATIVE_FIXTURE"
		if e = os.WriteFile(filepath.Join(abs, "stable.exe"), stableBytes, 0600); e != nil { return e }
		defer func() { if e != nil { _ = os.Remove(filepath.Join(abs, "stable.exe")) } }()
	}
	if _, e = tx.Exec("INSERT INTO evolution_hosts(project,body) VALUES(?,?)", project, string(Bytes(h))); e != nil {
		return e
	}
	if _, e = tx.Exec("INSERT INTO evolution_slots(project,active_hash,stable_hash,candidate,epoch,state) VALUES(?,?,?,NULL,1,'STABLE')", project, stable["content_hash"], stable["content_hash"]); e != nil {
		return e
	}
	e = tx.Commit()
	return e
}

// RegisterEvolutionBuild retains reviewed host build provenance. Candidates have
// no remote route to register binaries, replace the suite, or approve a manifest.
func (s *Service) RegisterEvolutionBuild(ctx context.Context, project string, artifact, manifest Object, sourceHash string) error {
	if e := s.Contracts.Validate("Digest", sourceHash); e != nil {
		return e
	}
	tx, e := s.DB.BeginTx(ctx, nil)
	if e != nil {
		return e
	}
	defer tx.Rollback()
	a, _, e := s.evolutionBytes(tx, project, artifact)
	if e != nil {
		return e
	}
	if a["kind"] != "CODE" {
		return fmt.Errorf("code build required")
	}
	_, raw, e := s.evolutionBytes(tx, project, manifest)
	if e != nil {
		return e
	}
	m, e := Decode(raw)
	if e != nil {
		return e
	}
	if Hash(m) != Hash(Object{"paths": []any{"ops/canary/fixture/main.go"}}) {
		return Fail(422, "GATE_FAILED", "development build may not modify tests labels supervisor or release permissions")
	}
	body := Object{"artifact_ref": artifact, "manifest_ref": manifest, "source_hash": sourceHash, "build_hash": a["content_hash"], "registered_at": Now(), "scope": evolution.Scope}
	_, e = tx.Exec("INSERT INTO evolution_builds(project,artifact,body) VALUES(?,?,?)", project, a["id"], string(Bytes(body)))
	if e != nil {
		return e
	}
	return tx.Commit()
}
func (s *Service) evolutionCurrent(tx *sql.Tx, project string, x Object) (Object, error) {
	h, e := evolutionHost(tx, project)
	if e != nil {
		return nil, e
	}
	if x["independent_supervisor_id"] != h["supervisor_id"] || x["baseline_policy_hash"] != h["policy_hash"] || h["policy_hash"] != Digest(evolution.Bytes(evolution.Policy())) || Hash(x["stable_artifact_ref"]) != Hash(h["stable_ref"]) || Hash(x["baseline_suite_ref"]) != Hash(h["suite_ref"]) || Hash(x["rollback_plan_ref"]) != Hash(h["rollback_ref"]) || x["migration_plan_ref"] != nil {
		return nil, Fail(422, "GATE_FAILED", "candidate may not select host baseline policy suite rollback or migration")
	}
	for _, k := range []string{"candidate_artifact_ref", "stable_artifact_ref", "baseline_suite_ref", "changed_paths_manifest_ref", "rollback_plan_ref"} {
		if _, _, e = s.evolutionBytes(tx, project, x[k].(map[string]any)); e != nil {
			return nil, e
		}
	}
	var raw string
	if e = tx.QueryRow("SELECT body FROM evolution_builds WHERE project=? AND artifact=?", project, x["candidate_artifact_ref"].(map[string]any)["id"]).Scan(&raw); e != nil {
		return nil, Fail(422, "GATE_FAILED", "unregistered candidate build")
	}
	build, e := Decode([]byte(raw))
	if e != nil {
		return nil, e
	}
	if Hash(build["artifact_ref"]) != Hash(x["candidate_artifact_ref"]) || Hash(build["manifest_ref"]) != Hash(x["changed_paths_manifest_ref"]) {
		return nil, Fail(422, "GATE_FAILED", "candidate differs from host reviewed build")
	}
	experiment, e := load(tx, project, "Experiment", Str(x, "experiment_id"))
	if e != nil {
		return nil, e
	}
	if experiment["scope"] != "SYSTEM" || experiment["measurement_mode"] != "FIXTURE" || experiment["status"] == "DRAFT" || Hash(experiment["candidate_ref"]) != Hash(x["candidate_artifact_ref"]) || Hash(experiment["baseline_refs"]) != Hash([]any{x["stable_artifact_ref"]}) {
		return nil, Fail(422, "GATE_FAILED", "preregistered system experiment must bind both builds")
	}
	if e = s.experimentCurrent(tx, project, experiment); e != nil {
		return nil, e
	}
	var expected string
	e = tx.QueryRow("SELECT plan_hash FROM evolution_candidates WHERE project=? AND candidate=?", project, x["id"]).Scan(&expected)
	if e != nil && e != sql.ErrNoRows {
		return nil, e
	}
	if e == nil && expected != Hash(evolutionPlan(x)) {
		return nil, Fail(422, "GATE_FAILED", "frozen candidate plan changed")
	}
	return h, nil
}
func (s *Service) createSystemCandidate(tx *sql.Tx, p Principal, project string, b Object) (Object, error) {
	x := Merge(Base(project), b)
	Merge(x, Object{"status": "DRAFT", "regression_acceptance_id": nil, "canary_acceptance_id": nil, "rollback_verified_receipt_id": nil, "observation_deadline": nil, "promoted_at": nil, "freeze_reason": nil})
	h, e := s.evolutionCurrent(tx, project, x)
	if e != nil {
		return nil, e
	}
	author, e := authorityRoot(tx, p.ID)
	if e != nil {
		return nil, e
	}
	release, e := authorityRoot(tx, Str(h, "release_principal"))
	if e != nil {
		return nil, e
	}
	if author == release {
		return nil, Fail(403, "FORBIDDEN", "candidate author cannot own release authority")
	}
	if _, e = tx.Exec("INSERT INTO evolution_candidates(project,candidate,creator,plan_hash) VALUES(?,?,?,?)", project, x["id"], p.ID, Hash(evolutionPlan(x))); e != nil {
		return nil, e
	}
	return x, s.put(tx, "SystemCandidate", x)
}
func evolutionTerminal(x Object) bool {
	return x["status"] == "FROZEN" || x["status"] == "REJECTED" || x["status"] == "ROLLED_BACK" || x["status"] == "PROMOTED"
}
func (s *Service) actSystemCandidate(tx *sql.Tx, p Principal, project, id string, b Object) (Object, error) {
	x, e := load(tx, project, "SystemCandidate", id)
	if e != nil {
		return nil, e
	}
	h, e := s.evolutionCurrent(tx, project, x)
	if e != nil {
		return nil, e
	}
	if !p.HasRole("RELEASE_SERVICE") || p.ID != h["release_principal"] {
		return nil, Fail(403, "FORBIDDEN", "registered independent fixture release principal required")
	}
	if evolutionTerminal(x) {
		return nil, Fail(409, "STATE_CONFLICT", "candidate frozen or terminal; new independently reviewed input required")
	}
	if b["action"] == "PROMOTE" {
		return nil, Fail(503, "RESOURCE_UNAVAILABLE", "W16-G01 W14 LIVE and independent OS supervisor/canary qualification unavailable; fixture cannot promote")
	}
	switch b["action"] {
	case "START_EVALUATION":
		if x["status"] != "ISOLATED" {
			return nil, Fail(409, "STATE_CONFLICT", "host must isolate frozen build first")
		}
		x["status"] = "EVALUATING"
	case "START_CANARY":
		if x["status"] != "EVALUATING" {
			return nil, Fail(409, "STATE_CONFLICT", "candidate not awaiting regression gate")
		}
		deadline, err := time.Parse(time.RFC3339Nano, Str(b, "observation_deadline"))
		if err != nil || !deadline.After(time.Now()) || deadline.After(time.Now().Add(2*time.Minute)) {
			return nil, Fail(422, "GATE_FAILED", "bounded future fixture observation deadline required")
		}
		record, e := s.evolutionAccepted(tx, project, x, "REGRESSION", Str(b, "regression_acceptance_id"))
		if e != nil {
			return nil, e
		}
		x["regression_acceptance_id"] = b["regression_acceptance_id"]
		if record["improved"] != true || record["required_passed"] != true {
			x["status"] = "REJECTED"
			x["freeze_reason"] = "frozen required regression or no independently measured gain"
		} else {
			x["status"] = "CANARY"
			x["observation_deadline"] = b["observation_deadline"]
		}
	case "ROLLBACK":
		return nil, Fail(409, "STATE_CONFLICT", "actual host rollback must finish before receipt can be consumed")
	case "FREEZE":
		var state string
		if e = tx.QueryRow("SELECT state FROM evolution_slots WHERE project=?", project).Scan(&state); e != nil {
			return nil, e
		}
		if state != "STABLE" {
			return nil, Fail(409, "STATE_CONFLICT", "host must reconcile active trial before freeze")
		}
		x["status"] = "FROZEN"
		x["freeze_reason"] = b["reason"]
	default:
		return nil, Fail(400, "INVALID_REQUEST", "unknown candidate action")
	}
	if e = bump(x); e != nil {
		return nil, e
	}
	return x, s.put(tx, "SystemCandidate", x)
}
