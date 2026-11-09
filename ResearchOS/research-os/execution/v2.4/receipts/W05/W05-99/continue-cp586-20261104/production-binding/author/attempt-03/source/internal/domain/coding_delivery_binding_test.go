package domain

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"testing"

	_ "modernc.org/sqlite"
	"researchos.local/research-os/internal/canonical"
)

// All subjects/contexts here are synthetic data in newly created databases.
// These tests demonstrate integrity, never authenticated Host/business acceptance.
func codingDeliveryTestContract(ids ...string) Object {
	checks := []any{}
	for _, id := range ids {
		checks = append(checks, Object{"check_id": id, "kind": "DETERMINISTIC", "required": true, "expected": "fixture integrity only", "command_key": id,
			"rubric_ref": nil, "qualification_id": nil, "not_applicable_reason": nil})
	}
	c := Object{"contract_revision": 1, "checks": checks, "require_independent_verifier": true, "version_policy": "EXACT", "frozen_at": "2026-11-04T00:00:00Z"}
	c["contract_hash"] = contractDigest(c)
	return c
}

func codingDeliveryTestBinding(t *testing.T) codingDeliveryBinding {
	t.Helper()
	b := codingDeliveryBinding{codingDeliveryBindingIdentity: codingDeliveryBindingIdentity{
		BindingSchema: codingDeliveryBindingSchema, SchemaVersion: codingDeliveryBindingVersion, Project: "project-one", GoalID: "goal-one", TaskID: "task-one",
		ApprovalIssuerRef: "original-approval-issuer", ApprovalRef: "approval-one", LineageIssuerRef: "original-lineage-issuer", OwnerPrincipal: "owner-one", OwnerRoot: "root-one", OwnerHost: "host-one",
		TaskContractHash: Str(codingDeliveryTestContract("mu.turn-output-v1", "coding.pure-scalar-delivery-v1"), "contract_hash"),
		GoalContractHash: Str(codingDeliveryTestContract("coding.accepted-task-delivery-v1"), "contract_hash")},
		OriginalProblemAnchor: "original-problem-anchor", RequirementContentHash: Digest([]byte("original requirement bytes")), BusinessInputContentHash: Digest([]byte("original business input bytes")),
		ParentRef: "trusted-parent-ref", ParentConfirmationHash: Hash("parent-confirmation"), CreationMethod: "goal.start", ClientID: "client-one", CommandID: "command-one", RequestHash: Hash("original-envelope"),
		SessionRef: "session-one", WorkspaceRef: "workspace-one", WorkspaceHash: Hash("workspace"), ProfileRef: "profile-one", ProfileHash: Hash("profile"), PolicyRef: "policy-one", PolicyHash: Hash("policy"),
		SuiteRef: "coding.pure-scalar-bundle-v1", SuiteHash: Hash("stable trusted suite"), ApprovedPlanRef: "plan-one", ApprovedPlanHash: Hash("approved plan"),
		RequirementRefsRef: "requirements-one", RequirementRefsHash: Hash([]any{Object{"id": "requirement-one", "revision": 1, "content_hash": Hash("requirement")}}),
		InputRefsRef: "inputs-one", InputRefsHash: Hash([]any{Object{"id": "input-one", "revision": 1, "content_hash": Hash("input")}}),
		OriginProblemID: "problem-one", CandidateID: "candidate-one", NoProgressRef: "no-progress-one", NoProgressInputKey: Hash("original-no-progress-key"),
		CreationWriterEpoch: "9223372036854775807", CreationSessionRevision: "9007199254740993"}
	var err error
	b.BusinessAnchor, err = codingDeliveryBusinessAnchor(b.origin())
	if err != nil {
		t.Fatal(err)
	}
	if err = b.validate(); err != nil {
		t.Fatal(err)
	}
	return b
}

func codingDeliveryTestSubjects(b codingDeliveryBinding) (Object, Object) {
	requirements := []any{Object{"id": "requirement-one", "revision": 1, "content_hash": Hash("requirement")}}
	goal := Object{"project_id": b.Project, "id": b.GoalID, "requirement_refs": requirements, "acceptance_contract": codingDeliveryTestContract("coding.accepted-task-delivery-v1")}
	task := Object{"project_id": b.Project, "id": b.TaskID, "goal_id": b.GoalID, "origin_problem_id": b.OriginProblemID, "candidate_id": b.CandidateID,
		"requirement_refs": requirements, "input_refs": []any{Object{"id": "input-one", "revision": 1, "content_hash": Hash("input")}},
		"acceptance_contract": codingDeliveryTestContract("mu.turn-output-v1", "coding.pure-scalar-delivery-v1")}
	return goal, task
}

func codingDeliveryTestOpen(t *testing.T, path string) *sql.DB {
	t.Helper()
	db, err := sql.Open("sqlite", path)
	if err != nil {
		t.Fatal(err)
	}
	db.SetMaxOpenConns(1)
	db.SetMaxIdleConns(1)
	t.Cleanup(func() { db.Close() })
	if _, err = db.Exec("PRAGMA foreign_keys=ON; PRAGMA busy_timeout=3000;"); err != nil {
		t.Fatal(err)
	}
	return db
}

func codingDeliveryTestDB(t *testing.T, install bool) (*sql.DB, string) {
	t.Helper()
	path := filepath.Join(t.TempDir(), "fresh.sqlite")
	db := codingDeliveryTestOpen(t, path)
	// Use the real canonical table source, not an invented fixture_only table.
	ddl, err := os.ReadFile(filepath.Join("..", "..", "migrations", "sqlite", "0002_domain.sql"))
	if err != nil {
		t.Fatal(err)
	}
	if _, err = db.Exec(string(ddl)); err != nil {
		t.Fatal(err)
	}
	if install {
		if _, err = db.Exec(codingDeliveryBindingSQL); err != nil {
			t.Fatal(err)
		}
	}
	return db, path
}

func codingDeliveryTestPutSubjects(t *testing.T, db *sql.DB, b codingDeliveryBinding) {
	t.Helper()
	goal, task := codingDeliveryTestSubjects(b)
	for i, subject := range []Object{goal, task} {
		kind := "Goal"
		if i == 1 {
			kind = "Task"
		}
		if _, err := db.Exec(`INSERT INTO domain_objects(project,kind,id,revision,body) VALUES(?,?,?,1,?)`, b.Project, kind, subject["id"], string(Bytes(subject))); err != nil {
			t.Fatal(err)
		}
	}
}

func codingDeliveryTestInsert(t *testing.T, db *sql.DB, b codingDeliveryBinding) {
	t.Helper()
	tx, err := db.BeginTx(context.Background(), nil)
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback()
	if err = insertCodingDeliveryBindingTx(context.Background(), tx, b, b); err != nil {
		t.Fatal(err)
	}
	if err = tx.Commit(); err != nil {
		t.Fatal(err)
	}
}

func codingDeliveryTestRead(t *testing.T, db *sql.DB, b codingDeliveryBinding) error {
	t.Helper()
	tx, err := db.BeginTx(context.Background(), nil)
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback()
	actual, err := readCodingDeliveryBindingTx(context.Background(), tx, b.Project, b.TaskID, b)
	if err == nil && actual != b {
		t.Fatal("binding changed")
	}
	return err
}

func TestCodingDeliveryBindingCanonicalOriginAndInt64(t *testing.T) {
	b := codingDeliveryTestBinding(t)
	raw, digest, err := codingDeliveryBindingBytes(b)
	if err != nil {
		t.Fatal(err)
	}
	decoded, err := decodeCodingDeliveryBinding(raw)
	if err != nil || decoded != b || digest != Hash(b) || digest != Digest(raw) {
		t.Fatalf("canonical round trip: %v", err)
	}
	var generic Object
	if err = json.Unmarshal(raw, &generic); err != nil || Hash(generic) != digest {
		t.Fatalf("existing Hash interoperability: %v", err)
	}
	if !bytes.Contains(raw, []byte(`"creation_session_revision":"9007199254740993"`)) || !bytes.Contains(raw, []byte(`"creation_writer_epoch":"9223372036854775807"`)) {
		t.Fatal("int64 creation snapshot lost precision")
	}
	renamed := b
	renamed.Project = "other-project"
	renamed.OwnerPrincipal = "other-owner"
	renamed.OwnerRoot = "other-root"
	renamed.GoalID = "new-goal"
	renamed.TaskID = "new-task"
	renamed.ApprovalRef = "new-approval"
	renamed.CommandID = "new-command"
	renamed.InputRefsHash = Hash("reupload IDs")
	if err = renamed.validate(); err != nil || renamed.BusinessAnchor != b.BusinessAnchor {
		t.Fatalf("permission/storage rename changed causal anchor: %v", err)
	}
	changed := b.origin()
	changed.BusinessInputContentHash = Hash("different original input")
	anchor, err := codingDeliveryBusinessAnchor(changed)
	if err != nil || anchor == b.BusinessAnchor {
		t.Fatal("original content change must change anchor")
	}
	missing := b.origin()
	missing.OriginalProblemAnchor = ""
	if _, err = codingDeliveryBusinessAnchor(missing); err == nil {
		t.Fatal("missing original origin accepted")
	}
}

func TestCodingDeliveryBindingStrictDTO(t *testing.T) {
	b := codingDeliveryTestBinding(t)
	raw, _, _ := codingDeliveryBindingBytes(b)
	canon := func(v Object) []byte {
		out, err := canonical.JSON(Bytes(v))
		if err != nil {
			t.Fatal(err)
		}
		return out
	}
	for _, kind := range []string{"missing", "unknown", "case-alias", "duplicate", "null-field", "unknown-version", "array", "null", "unicode", "noncanonical", "number-epoch", "overflow", "leading-zero", "anchor-mismatch", "oversized"} {
		t.Run(kind, func(t *testing.T) {
			var object Object
			if err := json.Unmarshal(raw, &object); err != nil {
				t.Fatal(err)
			}
			bad := append([]byte{}, raw...)
			switch kind {
			case "missing":
				delete(object, "owner_root")
				bad = canon(object)
			case "unknown":
				object["unknown"] = "x"
				bad = canon(object)
			case "case-alias":
				delete(object, "owner_root")
				object["Owner_Root"] = "root-one"
				bad = canon(object)
			case "duplicate":
				bad = append(append([]byte{}, raw[:len(raw)-1]...), []byte(`,"project":"project-one"}`)...)
			case "null-field":
				object["owner_root"] = nil
				bad = canon(object)
			case "unknown-version":
				object["schema_version"] = 2
				bad = canon(object)
			case "array":
				bad = []byte(`[]`)
			case "null":
				bad = []byte(`null`)
			case "unicode":
				bad = bytes.Replace(raw, []byte(`"root-one"`), []byte(`"\ud800"`), 1)
			case "noncanonical":
				bad = append([]byte(" "), raw...)
			case "number-epoch":
				object["creation_writer_epoch"] = json.Number("9223372036854775807")
				bad = Bytes(object)
			case "overflow":
				object["creation_writer_epoch"] = "9223372036854775808"
				bad = canon(object)
			case "leading-zero":
				object["creation_writer_epoch"] = "01"
				bad = canon(object)
			case "anchor-mismatch":
				object["business_input_content_hash"] = Hash("changed origin")
				bad = canon(object)
			case "oversized":
				object["parent_ref"] = strings.Repeat("x", codingDeliveryBindingMaxBytes)
				bad = canon(object)
			}
			if _, err := decodeCodingDeliveryBinding(bad); err == nil {
				t.Fatal("invalid closed DTO accepted")
			}
		})
	}
	for _, value := range []string{"0", "-1", "+1", "1.0", "1e0", " 1", "9223372036854775808"} {
		changed := b
		changed.CreationWriterEpoch = value
		if err := changed.validate(); err == nil {
			t.Fatalf("invalid decimal %q accepted", value)
		}
	}
}

func TestCodingDeliveryBindingOriginalTypedUTF8(t *testing.T) {
	b := codingDeliveryTestBinding(t)
	b.OwnerRoot = string([]byte{0xff})
	if err := b.validate(); err == nil {
		t.Fatal("invalid original typed provenance accepted before Marshal substitution")
	}
	if _, _, err := codingDeliveryBindingBytes(b); err == nil {
		t.Fatal("invalid typed provenance persisted")
	}
}
func TestCodingDeliveryBindingExpectedContext(t *testing.T) {
	b := codingDeliveryTestBinding(t)
	for _, kind := range []string{"owner", "root", "host", "approval", "lineage", "project", "goal", "task", "request", "profile", "plan", "no-progress", "creation-revision", "dual-contract"} {
		t.Run(kind, func(t *testing.T) {
			other := b
			switch kind {
			case "owner":
				other.OwnerPrincipal = "foreign-owner"
			case "root":
				other.OwnerRoot = "foreign-root"
			case "host":
				other.OwnerHost = "foreign-host"
			case "approval":
				other.ApprovalRef = "other-approval"
			case "lineage":
				other.LineageIssuerRef = "other-issuer"
			case "project":
				other.Project = "foreign-project"
			case "goal":
				other.GoalID = "foreign-goal"
			case "task":
				other.TaskID = "foreign-task"
			case "request":
				other.RequestHash = Hash("foreign-request")
			case "profile":
				other.ProfileHash = Hash("foreign-profile")
			case "plan":
				other.ApprovedPlanHash = Hash("foreign-plan")
			case "no-progress":
				other.NoProgressInputKey = Hash("zeroed failure history")
			case "creation-revision":
				other.CreationSessionRevision = "1"
			case "dual-contract":
				other.TaskContractHash, other.GoalContractHash = other.GoalContractHash, other.TaskContractHash
			}
			if err := codingDeliveryBindingContext(b, other); err == nil {
				t.Fatal("foreign provenance accepted")
			}
		})
	}
	if err := codingDeliveryBindingContext(b, codingDeliveryBinding{}); err == nil {
		t.Fatal("implicit expected context accepted")
	}
}

func TestCodingDeliveryBindingFreshInsertRead(t *testing.T) {
	db, _ := codingDeliveryTestDB(t, true)
	b := codingDeliveryTestBinding(t)
	codingDeliveryTestPutSubjects(t, db, b)
	codingDeliveryTestInsert(t, db, b)
	if err := codingDeliveryTestRead(t, db, b); err != nil {
		t.Fatal(err)
	}
	tx, err := db.BeginTx(context.Background(), nil)
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback()
	if err = codingDeliveryBindingInventoryTx(context.Background(), tx, map[codingDeliveryBindingKey]codingDeliveryBinding{{b.Project, b.TaskID}: b}); err != nil {
		t.Fatal(err)
	}
	if err = codingDeliveryBindingInventoryTx(context.Background(), tx, map[codingDeliveryBindingKey]codingDeliveryBinding{}); err == nil {
		t.Fatal("partial inventory accepted")
	}
}

func TestCodingDeliveryBindingMissingCapabilityAndRow(t *testing.T) {
	for _, installed := range []bool{false, true} {
		t.Run(map[bool]string{false: "missing-schema", true: "missing-row"}[installed], func(t *testing.T) {
			db, _ := codingDeliveryTestDB(t, installed)
			b := codingDeliveryTestBinding(t)
			codingDeliveryTestPutSubjects(t, db, b)
			if err := codingDeliveryTestRead(t, db, b); err == nil {
				t.Fatal("missing binding capability/row accepted")
			}
		})
	}
}

func TestCodingDeliveryBindingImmutableConflictForms(t *testing.T) {
	for _, recursive := range []string{"OFF", "ON"} {
		t.Run(recursive, func(t *testing.T) {
			db, _ := codingDeliveryTestDB(t, true)
			if _, err := db.Exec("PRAGMA recursive_triggers=" + recursive); err != nil {
				t.Fatal(err)
			}
			b := codingDeliveryTestBinding(t)
			codingDeliveryTestPutSubjects(t, db, b)
			codingDeliveryTestInsert(t, db, b)
			raw, digest, _ := codingDeliveryBindingBytes(b)
			args := codingDeliveryBindingArguments(b, raw, digest)
			for _, statement := range []string{
				`UPDATE coding_delivery_bindings SET binding_hash=binding_hash`, `UPDATE coding_delivery_bindings SET owner_root='changed'`, `DELETE FROM coding_delivery_bindings`,
				strings.Replace(codingDeliveryBindingInsert, "INSERT INTO", "INSERT OR REPLACE INTO", 1), strings.Replace(codingDeliveryBindingInsert, "INSERT INTO", "INSERT OR IGNORE INTO", 1),
				codingDeliveryBindingInsert + ` ON CONFLICT DO NOTHING`, codingDeliveryBindingInsert + ` ON CONFLICT(project,task_id) DO UPDATE SET owner_root=excluded.owner_root`,
			} {
				var err error
				if strings.HasPrefix(statement, "INSERT") {
					_, err = db.Exec(statement, args...)
				} else {
					_, err = db.Exec(statement)
				}
				if err == nil {
					t.Fatalf("conflict/no-op silently succeeded: %s", statement)
				}
				var gotRaw, gotHash string
				if err = db.QueryRow(`SELECT binding_body,binding_hash FROM coding_delivery_bindings`).Scan(&gotRaw, &gotHash); err != nil || gotRaw != string(raw) || gotHash != digest {
					t.Fatalf("original row changed: %v", err)
				}
			}
		})
	}
}

func codingDeliveryTestOther(b codingDeliveryBinding) codingDeliveryBinding {
	other := b
	other.Project = "project-two"
	other.GoalID = "goal-two"
	other.TaskID = "task-two"
	other.OwnerPrincipal = "owner-two"
	other.OwnerRoot = "root-two"
	other.OwnerHost = "host-two"
	other.ApprovalRef = "approval-two"
	other.OriginalProblemAnchor = "other-original-problem"
	other.BusinessAnchor, _ = codingDeliveryBusinessAnchor(other.origin())
	return other
}

func TestCodingDeliveryBindingDatabaseWideUniqueness(t *testing.T) {
	for _, collision := range []string{"task", "goal", "approval", "lineage"} {
		t.Run(collision, func(t *testing.T) {
			db, _ := codingDeliveryTestDB(t, true)
			b := codingDeliveryTestBinding(t)
			codingDeliveryTestPutSubjects(t, db, b)
			codingDeliveryTestInsert(t, db, b)
			other := codingDeliveryTestOther(b)
			switch collision {
			case "task":
				other.Project = b.Project
				other.TaskID = b.TaskID
			case "goal":
				other.Project = b.Project
				other.GoalID = b.GoalID
			case "approval":
				other.ApprovalRef = b.ApprovalRef
			case "lineage":
				other.OriginalProblemAnchor = b.OriginalProblemAnchor
				other.BusinessAnchor = b.BusinessAnchor
			}
			// Existing colliding subjects remain; fresh distinct subjects are inserted.
			goal, task := codingDeliveryTestSubjects(other)
			for i, subject := range []Object{goal, task} {
				kind := "Goal"
				if i == 1 {
					kind = "Task"
				}
				var count int
				if err := db.QueryRow(`SELECT count(*) FROM domain_objects WHERE project=? AND kind=? AND id=?`, other.Project, kind, subject["id"]).Scan(&count); err != nil {
					t.Fatal(err)
				}
				if count == 0 {
					if _, err := db.Exec(`INSERT INTO domain_objects(project,kind,id,revision,body) VALUES(?,?,?,1,?)`, other.Project, kind, subject["id"], string(Bytes(subject))); err != nil {
						t.Fatal(err)
					}
				}
			}
			raw, digest, err := codingDeliveryBindingBytes(other)
			if err != nil {
				t.Fatal(err)
			}
			if _, err = db.Exec(codingDeliveryBindingInsert, codingDeliveryBindingArguments(other, raw, digest)...); err == nil {
				t.Fatal("cross-principal/project identity claim accepted")
			}
			var count int
			if err = db.QueryRow(`SELECT count(*) FROM coding_delivery_bindings`).Scan(&count); err != nil || count != 1 {
				t.Fatalf("original claim changed: %d %v", count, err)
			}
		})
	}
}

func TestCodingDeliveryBindingSQLClosedBody(t *testing.T) {
	for _, kind := range []string{"missing", "null", "unknown", "duplicate", "column-mismatch", "integer-overflow", "version", "nul-requirement-hash", "nul-input-hash"} {
		t.Run(kind, func(t *testing.T) {
			db, _ := codingDeliveryTestDB(t, true)
			b := codingDeliveryTestBinding(t)
			codingDeliveryTestPutSubjects(t, db, b)
			raw, digest, _ := codingDeliveryBindingBytes(b)
			var body Object
			if err := json.Unmarshal(raw, &body); err != nil {
				t.Fatal(err)
			}
			switch kind {
			case "missing":
				delete(body, "parent_ref")
			case "null":
				body["parent_ref"] = nil
			case "unknown":
				body["unknown"] = "x"
			case "column-mismatch":
				body["owner_root"] = "other-root"
			case "integer-overflow":
				body["schema_version"] = json.Number("9223372036854775808")
			case "nul-requirement-hash":
				body["requirement_content_hash"] = b.RequirementContentHash + "\x00suffix"
			case "nul-input-hash":
				body["business_input_content_hash"] = b.BusinessInputContentHash + "\x00suffix"
			case "version":
				body["schema_version"] = 2
			}
			bad := Bytes(body)
			if kind == "duplicate" {
				bad = append(append([]byte{}, raw[:len(raw)-1]...), []byte(`,"project":"project-one"}`)...)
			}
			if _, err := db.Exec(codingDeliveryBindingInsert, codingDeliveryBindingArguments(b, bad, digest)...); err == nil {
				t.Fatal("SQL admitted invalid closed identity/body")
			}
		})
	}
}

func TestCodingDeliveryBindingDigestAndCanonicalReadback(t *testing.T) {
	for _, kind := range []string{"hash", "noncanonical", "origin-anchor"} {
		t.Run(kind, func(t *testing.T) {
			db, _ := codingDeliveryTestDB(t, true)
			b := codingDeliveryTestBinding(t)
			codingDeliveryTestPutSubjects(t, db, b)
			raw, digest, _ := codingDeliveryBindingBytes(b)
			switch kind {
			case "hash":
				digest = Hash("wrong digest")
			case "noncanonical":
				raw = append([]byte(" "), raw...)
			case "origin-anchor":
				var object Object
				_ = json.Unmarshal(raw, &object)
				object["business_input_content_hash"] = Hash("tampered original input")
				raw = Bytes(object)
			}
			// SQL cannot authenticate bytes or compute the domain hash. The Go consumer
			// must independently reject otherwise well-shaped rows.
			if _, err := db.Exec(codingDeliveryBindingInsert, codingDeliveryBindingArguments(b, raw, digest)...); err != nil {
				t.Fatal(err)
			}
			if err := codingDeliveryTestRead(t, db, b); err == nil {
				t.Fatal("invalid canonical hash/origin readback accepted")
			}
		})
	}
}

func TestCodingDeliveryBindingContractPublishedShape(t *testing.T) {
	for _, kind := range []string{"same-length-unknown", "missing", "command-type", "rubric-type", "required-type", "empty-expected", "qualification-type", "time-offset", "check-id", "top-level-unknown", "duplicate-id"} {
		t.Run(kind, func(t *testing.T) {
			c := codingDeliveryTestContract("mu.turn-output-v1", "coding.pure-scalar-delivery-v1")
			checks := c["checks"].([]any)
			check := checks[0].(map[string]any)
			switch kind {
			case "same-length-unknown":
				delete(check, "expected")
				check["foreign"] = "unknown same-length field"
			case "missing":
				delete(check, "command_key")
			case "command-type":
				check["command_key"] = 123
			case "rubric-type":
				check["rubric_ref"] = Object{"unknown": "foreign-ref"}
			case "required-type":
				check["required"] = "true"
			case "empty-expected":
				check["expected"] = ""
			case "qualification-type":
				check["qualification_id"] = 123
			case "time-offset":
				c["frozen_at"] = "2026-11-04T00:00:00+00:00"
			case "check-id":
				check["check_id"] = "invalid check id"
			case "top-level-unknown":
				c["unknown"] = "x"
			case "duplicate-id":
				c["checks"] = append(checks, check)
			}
			c["contract_hash"] = contractDigest(c)
			if err := codingDeliveryContractIntegrity(c, Str(c, "contract_hash"), "mu.turn-output-v1", "coding.pure-scalar-delivery-v1"); err == nil {
				t.Fatal("malformed published contract accepted with self-consistent digest")
			}
		})
	}
}
func TestCodingDeliveryBindingCanonicalSubjectIntegrity(t *testing.T) {
	for _, kind := range []string{"task-goal", "foreign-project", "task-contract", "goal-contract", "missing-required", "requirements", "inputs", "origin", "candidate"} {
		t.Run(kind, func(t *testing.T) {
			b := codingDeliveryTestBinding(t)
			goal, task := codingDeliveryTestSubjects(b)
			switch kind {
			case "task-goal":
				task["goal_id"] = "foreign-goal"
			case "foreign-project":
				goal["project_id"] = "foreign-project"
			case "task-contract":
				task["acceptance_contract"] = goal["acceptance_contract"]
			case "goal-contract":
				goal["acceptance_contract"] = task["acceptance_contract"]
			case "missing-required":
				c := codingDeliveryTestContract("mu.turn-output-v1")
				task["acceptance_contract"] = c
				b.TaskContractHash = Str(c, "contract_hash")
			case "requirements":
				goal["requirement_refs"] = []any{}
			case "inputs":
				task["input_refs"] = []any{}
			case "origin":
				task["origin_problem_id"] = "new-origin"
			case "candidate":
				task["candidate_id"] = "new-candidate"
			}
			if err := codingDeliverySubjectIntegrity(b, goal, task); err == nil {
				t.Fatal("foreign canonical subject accepted")
			}
		})
	}
	db, _ := codingDeliveryTestDB(t, true)
	b := codingDeliveryTestBinding(t)
	codingDeliveryTestPutSubjects(t, db, b)
	codingDeliveryTestInsert(t, db, b)
	var raw string
	if err := db.QueryRow(`SELECT body FROM domain_objects WHERE kind='Task'`).Scan(&raw); err != nil {
		t.Fatal(err)
	}
	task, err := Decode([]byte(raw))
	if err != nil {
		t.Fatal(err)
	}
	task["input_refs"] = []any{}
	if _, err = db.Exec(`UPDATE domain_objects SET body=? WHERE kind='Task'`, string(Bytes(task))); err != nil {
		t.Fatal(err)
	}
	if err = codingDeliveryTestRead(t, db, b); err == nil {
		t.Fatal("canonical Task drift accepted")
	}
}

func TestCodingDeliveryBindingRollbackIsSQLOnly(t *testing.T) {
	db, _ := codingDeliveryTestDB(t, true)
	b := codingDeliveryTestBinding(t)
	codingDeliveryTestPutSubjects(t, db, b)
	tx, err := db.BeginTx(context.Background(), nil)
	if err != nil {
		t.Fatal(err)
	}
	if err = insertCodingDeliveryBindingTx(context.Background(), tx, b, b); err != nil {
		t.Fatal(err)
	}
	if err = tx.Rollback(); err != nil {
		t.Fatal(err)
	}
	var count int
	if err = db.QueryRow(`SELECT count(*) FROM coding_delivery_bindings`).Scan(&count); err != nil || count != 0 {
		t.Fatalf("partial row after rollback: %d %v", count, err)
	}
	if err = codingDeliveryTestRead(t, db, b); err == nil {
		t.Fatal("missing row treated as usable binding")
	}
	// No external/native approval is exercised or refunded by this fixture.
}

func TestCodingDeliveryBindingSchemaTamper(t *testing.T) {
	for _, statement := range []string{`DROP TRIGGER coding_delivery_no_update`, `DROP TRIGGER coding_delivery_no_delete`, `DROP TRIGGER coding_delivery_insert_conflict`,
		`DROP INDEX coding_delivery_lineage_unique`, `DROP INDEX coding_delivery_approval_unique`, `CREATE TRIGGER extra_binding_trigger AFTER INSERT ON coding_delivery_bindings BEGIN SELECT 1; END;`,
		`ALTER TABLE coding_delivery_bindings ADD COLUMN surprise TEXT`, `PRAGMA foreign_keys=OFF`} {
		t.Run(statement, func(t *testing.T) {
			db, _ := codingDeliveryTestDB(t, true)
			if _, err := db.Exec(statement); err != nil {
				t.Fatal(err)
			}
			if err := codingDeliveryBindingSchemaIntegrity(context.Background(), db); err == nil {
				t.Fatal("tampered capability accepted")
			}
		})
	}
}

func TestCodingDeliveryBindingFreshSnapshotInventory(t *testing.T) {
	db, _ := codingDeliveryTestDB(t, true)
	b := codingDeliveryTestBinding(t)
	codingDeliveryTestPutSubjects(t, db, b)
	codingDeliveryTestInsert(t, db, b)
	snapshot := filepath.Join(t.TempDir(), "fresh-snapshot.sqlite")
	if _, err := db.Exec(`VACUUM INTO ?`, snapshot); err != nil {
		t.Fatal(err)
	}
	restored := codingDeliveryTestOpen(t, snapshot)
	if err := codingDeliveryTestRead(t, restored, b); err != nil {
		t.Fatal(err)
	}
	tx, err := restored.BeginTx(context.Background(), nil)
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback()
	inventory := map[codingDeliveryBindingKey]codingDeliveryBinding{{b.Project, b.TaskID}: b}
	if err = codingDeliveryBindingInventoryTx(context.Background(), tx, inventory); err != nil {
		t.Fatal(err)
	}
	foreign := b
	foreign.OwnerHost = "copied-to-other-host"
	inventory[codingDeliveryBindingKey{b.Project, b.TaskID}] = foreign
	if err = codingDeliveryBindingInventoryTx(context.Background(), tx, inventory); err == nil {
		t.Fatal("cross-Host snapshot context accepted")
	}
}

func TestCodingDeliveryBindingConcurrentQualifiedClaims(t *testing.T) {
	for _, kind := range []string{"approval", "lineage"} {
		t.Run(kind, func(t *testing.T) {
			db, path := codingDeliveryTestDB(t, true)
			second := codingDeliveryTestOpen(t, path)
			b := codingDeliveryTestBinding(t)
			other := codingDeliveryTestOther(b)
			if kind == "approval" {
				other.ApprovalRef = b.ApprovalRef
			} else {
				other.OriginalProblemAnchor = b.OriginalProblemAnchor
				other.BusinessAnchor = b.BusinessAnchor
			}
			codingDeliveryTestPutSubjects(t, db, b)
			codingDeliveryTestPutSubjects(t, db, other)
			start := make(chan struct{})
			results := make(chan error, 2)
			var ready sync.WaitGroup
			ready.Add(2)
			for i, database := range []*sql.DB{db, second} {
				binding := []codingDeliveryBinding{b, other}[i]
				go func(database *sql.DB, binding codingDeliveryBinding) {
					ready.Done()
					<-start
					tx, err := database.BeginTx(context.Background(), nil)
					if err == nil {
						defer tx.Rollback()
						err = insertCodingDeliveryBindingTx(context.Background(), tx, binding, binding)
						if err == nil {
							err = tx.Commit()
						}
					}
					results <- err
				}(database, binding)
			}
			ready.Wait()
			close(start)
			successes := 0
			for range 2 {
				if err := <-results; err == nil {
					successes++
				}
			}
			var count int
			if err := db.QueryRow(`SELECT count(*) FROM coding_delivery_bindings`).Scan(&count); err != nil {
				t.Fatal(err)
			}
			if successes != 1 || count != 1 {
				t.Fatalf("qualified claim results: successes=%d rows=%d", successes, count)
			}
		})
	}
}
