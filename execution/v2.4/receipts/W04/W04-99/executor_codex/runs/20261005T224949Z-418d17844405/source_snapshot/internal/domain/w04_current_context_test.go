package domain

import (
	"bytes"
	"context"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func w04CurrentFixture(t *testing.T) *fixture {
	t.Helper()
	f := contextFixtureFrom(setupWithConstructor(t, NewCurrentMu))
	w03AssertStoredRoute(t, f, "ProjectState", f.state(), "MU_FORK")
	w04Rules(t, f)
	return f
}

func w04Rules(t *testing.T, f *fixture) Object {
	t.Helper()
	profile := f.expect(200, "GET", f.path("/profile"), "", "", nil)
	var found Object
	count := 0
	for _, value := range Arr(profile, "source_document_refs") {
		ref := value.(map[string]any)
		if ref["content_hash"] == projectRulesHash {
			count++
			found = f.read("artifacts", Str(ref, "id"))
			if found["project_id"] != f.project || found["kind"] != "SOURCE_SNAPSHOT" || found["access_class"] != "PROJECT" || found["measurement_mode"] != "FIXTURE" || Str(found, "sealed_at") == "" {
				t.Fatal("invalid fixed rule artifact", found)
			}
			var raw []byte
			if err := f.db.QueryRow("SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1", f.project, found["storage_key"]).Scan(&raw); err != nil {
				t.Fatal(err)
			}
			if !bytes.Equal(raw, projectRulesBytes) || len(raw) != 12952 {
				t.Fatal("fixed rules original bytes differ")
			}
		}
	}
	if count != 1 {
		t.Fatalf("fixed rule references=%d", count)
	}
	return found
}

func TestW04CurrentC03(t *testing.T)     { runW04C03(t, w04CurrentFixture(t)) }
func TestW04CurrentC04(t *testing.T)     { runW04C04(t, w04CurrentFixture(t)) }
func TestW04CurrentNumbers(t *testing.T) { runW04CanonicalNumbers(t, w04CurrentFixture(t)) }
func TestW04CurrentRecovery(t *testing.T) {
	runW04ContextRecovery(t, w04CurrentFixture(t), NewCurrentMu)
}
func TestW04CurrentRestricted(t *testing.T) { runW04RestrictedContext(t, w04CurrentFixture(t)) }

func TestW04CurrentRules(t *testing.T) {
	f := w04CurrentFixture(t)
	rules := w04Rules(t, f)
	before := databaseCounts(t, f)
	body := projectBody()
	body["source_document_refs"] = []any{Ref(rules, "Artifact")}
	f.expect(503, "POST", "/v1/projects", ID(), "", body)
	if Hash(before) != Hash(databaseCounts(t, f)) {
		t.Fatal("caller source-ref injection wrote state")
	}
	original := append([]byte(nil), projectRulesBytes...)
	projectRulesBytes = append(append([]byte(nil), original...), byte('x'))
	t.Cleanup(func() { projectRulesBytes = original })
	_, err := NewCurrentMu(f.db, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql")
	if err == nil {
		t.Fatal("constructor accepted altered fixed source")
	}
	status, response, _ := f.request("POST", "/v1/projects", ID(), "", projectBody())
	projectRulesBytes = original
	assertion(t, "W04-RULES-ATOMIC", []any{422, before, true}, []any{status, databaseCounts(t, f), err != nil}, Object{"late_create_refusal": response, "constructor_refusal": fmt.Sprint(err), "rules": rules})
}

func TestW04CurrentEmptyWorkers(t *testing.T) {
	f := w04CurrentFixture(t)
	req := f.requirement()
	task := f.task(req, Empty(), "read-frozen-rules-then-continue")
	goal := f.read("goals", Str(task, "goal_id"))
	w03AssertStoredRoute(t, f, "Goal", goal, "MU_FORK")
	w03AssertStoredRoute(t, f, "Task", task, "MU_FORK")
	bundle := f.bundle(task)
	rules := w04Rules(t, f)
	manifests := Empty()
	for i := 0; i < 2; i++ {
		dest := filepath.Join(t.TempDir(), "empty-worker")
		fresh, err := NewCurrentMu(f.db, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql")
		if err != nil {
			t.Fatal(err)
		}
		manifest, err := fresh.MaterializeTaskContext(context.Background(), f.token, f.project, Str(task, "id"), dest)
		if err != nil {
			t.Fatal(err)
		}
		content := filepath.Join(dest, "inputs", Str(rules, "id")+".content")
		raw, err := os.ReadFile(content)
		if err != nil {
			t.Fatal(err)
		}
		info, err := os.Stat(content)
		if err != nil {
			t.Fatal(err)
		}
		bundleRaw, err := os.ReadFile(filepath.Join(dest, "bundle.json"))
		if err != nil {
			t.Fatal(err)
		}
		readBundle, err := Decode(bundleRaw)
		if err != nil {
			t.Fatal(err)
		}
		_, continuation, ok := strings.Cut(Str(readBundle, "summary"), "\nContinuation: ")
		if !ok {
			t.Fatal("frozen continuation absent")
		}
		taskObject, err := Decode([]byte(continuation))
		if err != nil {
			t.Fatal(err)
		}
		if !bytes.Equal(raw, projectRulesBytes) || info.Mode().Perm()&0200 != 0 || readBundle["receipt_hash"] != bundle["receipt_hash"] || taskObject["acceptance_contract"] == nil {
			t.Fatal("fresh worker lacks frozen rules/contract", manifest, readBundle)
		}
		if err = os.WriteFile(filepath.Join(dest, "candidates", "next.txt"), []byte("read fixed rules and task acceptance contract"), 0600); err != nil {
			t.Fatal(err)
		}
		manifests = append(manifests, Object{"manifest": manifest, "rule_sha256": Digest(raw), "rule_size": len(raw), "readonly": info.Mode().Perm()&0200 == 0, "bundle_hash": readBundle["receipt_hash"], "task_acceptance_contract": taskObject["acceptance_contract"]})
		filepath.WalkDir(dest, func(path string, d os.DirEntry, e error) error {
			if e == nil && !d.IsDir() {
				os.Chmod(path, 0600)
			}
			return e
		})
	}
	next := f.task(req, Empty(), "next-task-after-rule-read")
	f.bundle(next)
	assertion(t, "W04-G03-EMPTY-WORKERS", []any{2, true, true}, []any{len(manifests), next["id"] != task["id"], Str(next["binding"].(map[string]any), "route") == "MU_FORK"}, Object{"workers": manifests, "next_task": next, "rules": Ref(rules, "Artifact")})
}

func TestW04CurrentRequiredRefusals(t *testing.T) {
	for _, failure := range []string{"required-contract", "rules-original", "authorization"} {
		t.Run(failure, func(t *testing.T) {
			f := w04CurrentFixture(t)
			task := f.task(f.requirement(), Empty(), "required-input-"+failure)
			bundle := f.bundle(task)
			rules := w04Rules(t, f)
			wantStatus, wantCode := 0, ""
			switch failure {
			case "required-contract":
				profile := f.expect(200, "GET", f.path("/profile"), "", "", nil)
				for _, table := range []string{"domain_objects", "domain_versions"} {
					if _, err := f.db.Exec("DELETE FROM "+table+" WHERE project=? AND kind='RunPolicy' AND id=?", f.project, profile["run_policy_id"]); err != nil {
						t.Fatal(err)
					}
				}
				wantStatus, wantCode = 422, "GATE_FAILED"
			case "rules-original":
				if _, err := f.db.Exec("UPDATE uploaded_content SET bytes=? WHERE project=? AND storage_key=?", []byte("changed original"), f.project, rules["storage_key"]); err != nil {
					t.Fatal(err)
				}
				wantStatus, wantCode = 422, "CONTENT_HASH_MISMATCH"
			case "authorization":
				if err := f.s.RevokePrincipal(context.Background(), f.owner); err != nil {
					t.Fatal(err)
				}
				wantStatus, wantCode = 401, "UNAUTHENTICATED"
			}
			before := databaseCounts(t, f)
			dest := filepath.Join(t.TempDir(), "must-not-exist")
			_, err := f.s.MaterializeTaskContext(context.Background(), f.token, f.project, Str(task, "id"), dest)
			fault, ok := err.(*Fault)
			if !ok {
				t.Fatalf("required input did not produce typed refusal: %v", err)
			}
			_, statErr := os.Stat(dest)
			assertion(t, "W04-H01-"+failure, []any{wantStatus, wantCode, true, before}, []any{fault.Status, fault.Code, os.IsNotExist(statErr), databaseCounts(t, f)}, Object{"bundle": Ref(bundle, "ContextBundle"), "refusal": Object{"status": fault.Status, "code": fault.Code, "message": fault.Error()}, "destination_absent": os.IsNotExist(statErr), "before": before, "after": databaseCounts(t, f)})
		})
	}
}

func TestW04CurrentOptionalRecall(t *testing.T) {
	f := w04CurrentFixture(t)
	task := f.task(f.requirement(), Empty(), "required-context-independent-of-recall")
	f.bundle(task)
	rootPath := t.TempDir()
	file := filepath.Join(rootPath, "optional.txt")
	const marker = "W04_OPTIONAL_RECALL_ORIGINAL"
	if err := os.WriteFile(file, []byte(marker), 0600); err != nil {
		t.Fatal(err)
	}
	rootID, err := f.s.RegisterLocalRoot(context.Background(), f.token, f.project, rootPath)
	if err != nil {
		t.Fatal(err)
	}
	artifact, _ := w09LocalEvidence(t, f, rootID, "optional.txt", "optional recall")
	before := w0902Search(f, marker, Str(artifact, "id"), 10)
	if len(Arr(before, "hits")) != 1 {
		t.Fatal("optional recall positive control failed", before)
	}
	if err = os.Remove(file); err != nil {
		t.Fatal(err)
	}
	if _, err = f.s.RefreshLocalSnapshots(context.Background(), f.token, f.project); err != nil {
		t.Fatal(err)
	}
	after := w0902Search(f, marker, Str(artifact, "id"), 10)
	dest := filepath.Join(t.TempDir(), "worker")
	manifest, err := f.s.MaterializeTaskContext(context.Background(), f.token, f.project, Str(task, "id"), dest)
	if err != nil {
		t.Fatal(err)
	}
	assertion(t, "W04-H01-OPTIONAL-RECALL", []any{0, true, true}, []any{len(Arr(after, "hits")), len(Arr(after, "warnings")) > 0, manifest["task_id"] == task["id"]}, Object{"before": before, "after": after, "worker_manifest": manifest})
	filepath.WalkDir(dest, func(path string, d os.DirEntry, e error) error {
		if e == nil && !d.IsDir() {
			os.Chmod(path, 0600)
		}
		return e
	})
}

func TestW04CurrentA01(t *testing.T) {
	f := setupWithConstructor(t, NewCurrentMu)
	source := filepath.Join(t.TempDir(), "package")
	input := os.Getenv("RESEARCHOS_W04_PACKAGE_INPUT")
	if input == "" {
		t.Fatal("explicit frozen test package input required")
	}
	if err := os.CopyFS(source, os.DirFS(input)); err != nil {
		t.Fatal(err)
	}
	manifestPath := filepath.Join(source, "PACKAGE_MANIFEST.json")
	raw, err := os.ReadFile(manifestPath)
	if err != nil {
		t.Fatal(err)
	}
	if Digest(raw) != "sha256:4666920727e189ed91dc84dae919f7ab9e52a2f9c45efd697ecdd790107d3964" {
		t.Fatal("not the frozen v2.4 package")
	}
	report, err := f.s.ImportSpecification(context.Background(), f.token, source, Digest(raw), Object{"assumptions": []any{"Synthetic fixture assumption: local development."}})
	if err != nil {
		t.Fatal(err)
	}
	f.project = Str(report, "project_id")
	profile := report["profile"].(map[string]any)
	goal := report["goal"].(map[string]any)
	w03AssertStoredRoute(t, f, "ProjectState", f.state(), "MU_FORK")
	w03AssertStoredRoute(t, f, "Goal", goal, "MU_FORK")
	rules := w04Rules(t, f)
	basis := map[string]bool{}
	for _, value := range Arr(profile, "facts") {
		basis[Str(value.(map[string]any), "basis")] = true
	}
	var foreign, ruleBodies int
	f.db.QueryRow("SELECT count(*) FROM auth_grants WHERE project<>?", f.project).Scan(&foreign)
	f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='Artifact' AND json_extract(body,'$.content_hash')=?", f.project, projectRulesHash).Scan(&ruleBodies)
	manifest, err := Decode(raw)
	if err != nil {
		t.Fatal(err)
	}
	assertion(t, "A01-01", []any{4, 0, "DRAFT", 1, len(Arr(manifest, "files")) + 1, "SPECIFICATION_IMPORT_ONLY"}, []any{len(basis), foreign, goal["status"], ruleBodies, len(Arr(report, "inventory")), report["scope"]}, Object{"import": report, "fixed_rule": rules, "manifest_hash": Digest(raw)})
	before := databaseCounts(t, f)
	refusals := Object{}
	reject := func(name string, pin string, options Object) {
		t.Helper()
		_, e := f.s.ImportSpecification(context.Background(), f.token, source, pin, options)
		if e == nil {
			t.Fatal("accepted negative import", name)
		}
		refusals[name] = fmt.Sprint(e)
		if Hash(before) != Hash(databaseCounts(t, f)) {
			t.Fatal("negative import wrote state", name)
		}
	}
	prd := filepath.Join(source, "01_PRD.md")
	original, err := os.ReadFile(prd)
	if err != nil {
		t.Fatal(err)
	}
	if err = os.WriteFile(prd, append(append([]byte(nil), original...), []byte("tampered")...), 0600); err != nil {
		t.Fatal(err)
	}
	reject("tampered-file", Digest(raw), Object{})
	if err = os.WriteFile(prd, original, 0600); err != nil {
		t.Fatal(err)
	}
	attack, _ := Decode(raw)
	Arr(attack, "files")[0].(map[string]any)["path"] = "../outside.txt"
	if err = os.WriteFile(manifestPath, Bytes(attack), 0600); err != nil {
		t.Fatal(err)
	}
	reject("traversal", Digest(Bytes(attack)), Object{})
	attack, _ = Decode(raw)
	attack["forged_authority"] = true
	if err = os.WriteFile(manifestPath, Bytes(attack), 0600); err != nil {
		t.Fatal(err)
	}
	reject("unknown-manifest-field", Digest(Bytes(attack)), Object{})
	if err = os.WriteFile(manifestPath, raw, 0600); err != nil {
		t.Fatal(err)
	}
	reject("historical-authority", Digest(raw), Object{"historical_authorization": Object{"project": "QuillClub", "read": true}})
	injected := filepath.Join(source, "unlisted.txt")
	if err = os.WriteFile(injected, []byte("unlisted"), 0600); err != nil {
		t.Fatal(err)
	}
	reject("unlisted-file", Digest(raw), Object{})
	if err = os.Remove(injected); err != nil {
		t.Fatal(err)
	}
	reject("wrong-manifest-pin", Digest([]byte("wrong")), Object{})
	assertion(t, "A01-02", []any{6, before}, []any{len(refusals), databaseCounts(t, f)}, Object{"refusals": refusals, "before": before, "after": databaseCounts(t, f)})
}

// Caller-pinned historical imports remain evidence; they cannot replace the
// installed current policy, even when they carry a different file named 15.
func TestW04CurrentImportRuleVariants(t *testing.T) {
	for _, mode := range []string{"absent", "different"} {
		t.Run(mode, func(t *testing.T) {
			f := setupWithConstructor(t, NewCurrentMu)
			source := filepath.Join(t.TempDir(), "historical-package")
			if err := os.CopyFS(source, os.DirFS("../../spec/v2.0")); err != nil {
				t.Fatal(err)
			}
			path := filepath.Join(source, "PACKAGE_MANIFEST.json")
			raw, err := os.ReadFile(path)
			if err != nil {
				t.Fatal(err)
			}
			manifest, err := Decode(raw)
			if err != nil {
				t.Fatal(err)
			}
			different := []byte("Caller pinned historical project instructions; retained as source only.\n")
			if mode == "different" {
				if err = os.WriteFile(filepath.Join(source, projectRulesPath), different, 0600); err != nil {
					t.Fatal(err)
				}
				manifest["files"] = append(Arr(manifest, "files"), Object{"path": projectRulesPath, "size_bytes": len(different), "sha256": strings.TrimPrefix(Digest(different), "sha256:")})
				raw = Bytes(manifest)
				if err = os.WriteFile(path, raw, 0600); err != nil {
					t.Fatal(err)
				}
			}
			imported, err := f.s.ImportSpecification(context.Background(), f.token, source, Digest(raw), Object{})
			if err != nil {
				t.Fatal(err)
			}
			f.project = Str(imported, "project_id")
			rules := w04Rules(t, f)
			if mode == "different" {
				found := false
				for _, v := range Arr(imported["profile"].(map[string]any), "source_document_refs") {
					found = found || v.(map[string]any)["content_hash"] == Digest(different)
				}
				if !found {
					t.Fatal("historical rule source was discarded")
				}
			}
			assertion(t, "W04-IMPORT-RULES-"+mode, true, rules["content_hash"] == projectRulesHash, Object{"profile": imported["profile"], "inventory": imported["inventory"], "installed_rules": Ref(rules, "Artifact")})
		})
	}
}
