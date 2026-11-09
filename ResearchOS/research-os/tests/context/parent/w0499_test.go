package parent_test

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"testing"
	"time"

	localworkspace "researchos.local/research-os/adapters/local_workspace"
	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/host"
	"researchos.local/research-os/internal/store"
)

const w04RuleDigest = "sha256:b81a28161c9115f3290a9e61e0460d22a516e168071965efd9692a0d45dc2497"

type w04LocalHarness struct {
	t         *testing.T
	db        *sql.DB
	svc       *domain.Service
	host      *host.Host
	principal domain.Principal
	authority *localworkspace.Authority
	scanner   *localworkspace.Scanner
	grader    domain.DefGrader
	root      string
}

func w04Harness(t *testing.T) *w04LocalHarness {
	t.Helper()
	ctx := context.Background()
	repo, err := filepath.Abs("../../..")
	if err != nil {
		t.Fatal(err)
	}
	root := t.TempDir()
	db, err := store.Open(filepath.Join(root, "current.sqlite"))
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { db.Close() })
	if err = store.Bootstrap(ctx, db, filepath.Join(repo, "migrations/sqlite/0001_bootstrap.sql")); err != nil {
		t.Fatal(err)
	}
	contracts := filepath.Join(repo, "spec/v2.0/contracts")
	migration := filepath.Join(repo, "migrations/sqlite/0002_domain.sql")
	svc, err := domain.NewCurrentMu(db, contracts, migration)
	if err != nil {
		t.Fatal(err)
	}
	schemas := filepath.Join(repo, "tests/contracts/fixtures")
	h, err := host.New(host.Config{DB: db, Dir: filepath.Join(root, "host"), ContractsDir: contracts,
		MigrationFile: migration, SchemaDir: schemas, SessionTTL: 10 * time.Minute})
	if err != nil {
		t.Fatal(err)
	}
	proto, err := os.ReadFile(filepath.Join(schemas, "client.protocol.schema.json"))
	if err != nil {
		t.Fatal(err)
	}
	external, err := os.ReadFile(filepath.Join(schemas, "domain.schema.json"))
	if err != nil {
		t.Fatal(err)
	}
	grader, err := domain.LoadSchemaWithExternals(proto, map[string][]byte{"domain.schema.json": external})
	if err != nil {
		t.Fatal(err)
	}
	owner, err := h.BootstrapOwner(ctx)
	if err != nil {
		t.Fatal(err)
	}
	principal, err := domain.AuthenticateToken(ctx, db, owner.Session.Token)
	if err != nil {
		t.Fatal(err)
	}
	return &w04LocalHarness{t: t, db: db, svc: svc, host: h, principal: principal,
		authority: localworkspace.NewAuthority(h), scanner: localworkspace.NewScanner(), grader: grader, root: root}
}

func (h *w04LocalHarness) register(dir, name string) domain.Object {
	h.t.Helper()
	frame, err := json.Marshal(domain.Object{"kind": host.KindWorkspaceChooseRequest, "client_id": "w04-current-fixture",
		"payload": domain.Object{"requested_path": nil, "requested_access": "READ_WRITE"}})
	if err != nil {
		h.t.Fatal(err)
	}
	reply, err := h.host.HandleNative(frame, true, func(string) (string, error) { return dir, nil })
	if err != nil {
		h.t.Fatal(err)
	}
	var value struct {
		Payload struct {
			SelectionRef string `json:"selection_ref"`
		} `json:"payload"`
	}
	if err = json.Unmarshal(reply, &value); err != nil || value.Payload.SelectionRef == "" {
		h.t.Fatalf("native selection failed: %v", err)
	}
	registered, err := h.svc.RegisterWorkspace(context.Background(), h.principal, h.authority, h.grader,
		domain.RegisterWorkspaceInput{SelectionRef: value.Payload.SelectionRef, DisplayName: name, RequestedAccess: "READ_WRITE", CommandID: domain.ID(), ClientID: "w04-current-fixture"})
	if err != nil {
		h.t.Fatal(err)
	}
	return registered
}

func (h *w04LocalHarness) bootstrap(ref, command string, grader domain.DefGrader) (domain.Object, error) {
	return h.svc.BootstrapProject(context.Background(), h.principal, h.authority, grader, h.scanner,
		domain.BootstrapProjectInput{AuthorizedWorkspaceRef: ref, DisplayName: "same display name", CommandID: command,
			ClientID: "w04-current-fixture", MeasurementMode: "FIXTURE"})
}

func (h *w04LocalHarness) object(project, kind, id string) domain.Object {
	h.t.Helper()
	var raw string
	query := "SELECT body FROM domain_objects WHERE project=? AND kind=?"
	args := []any{project, kind}
	if id != "" {
		query += " AND id=?"
		args = append(args, id)
	}
	if err := h.db.QueryRow(query, args...).Scan(&raw); err != nil {
		h.t.Fatal(err)
	}
	value, err := domain.Decode([]byte(raw))
	if err != nil {
		h.t.Fatal(err)
	}
	return value
}

func (h *w04LocalHarness) sealed(project string, artifact domain.Object) []byte {
	h.t.Helper()
	var raw []byte
	if err := h.db.QueryRow("SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1", project, artifact["storage_key"]).Scan(&raw); err != nil {
		h.t.Fatal(err)
	}
	if domain.Digest(raw) != artifact["content_hash"] {
		h.t.Fatal("sealed content digest changed")
	}
	return raw
}

func (h *w04LocalHarness) count(query string, args ...any) int64 {
	h.t.Helper()
	var n int64
	if err := h.db.QueryRow(query, args...).Scan(&n); err != nil {
		h.t.Fatal(err)
	}
	return n
}

func (h *w04LocalHarness) snapshot() domain.Object {
	h.t.Helper()
	out := domain.Object{}
	for _, table := range []string{"domain_objects", "domain_versions", "domain_refs", "uploaded_content", "auth_grants", "outbox", "idempotency"} {
		out[table] = h.count("SELECT count(*) FROM " + table)
	}
	var raw string
	if err := h.db.QueryRow("SELECT coalesce(json_group_array(body),'[]') FROM (SELECT body FROM domain_objects ORDER BY project,kind,id)").Scan(&raw); err != nil {
		h.t.Fatal(err)
	}
	out["object_body_digest"] = domain.Digest([]byte(raw))
	return out
}

type w04RejectInventory struct{ original domain.DefGrader }

func (g w04RejectInventory) ValidateDef(name string, value any) error {
	if name == "LocalInventoryPayload" {
		return errors.New("intentional required inventory contract fault after actual local scan")
	}
	return g.original.ValidateDef(name, value)
}

func w04Require(t *testing.T, label string, condition bool) {
	t.Helper()
	if !condition {
		t.Fatal(label)
	}
}

// This fixture uses actual OS-root selection, host authority, SQLite transactions
// and the production local Scanner. It does not run providers or later research.
func TestW04CurrentA0104(t *testing.T) {
	h := w04Harness(t)
	ctx := context.Background()
	observations := domain.Object{"fixture_mode": "FIXTURE", "scanner": "adapters/local_workspace.Scanner", "projects": []any{}}
	projects := []domain.Object{}
	ruleIDs := []string{}
	allStatuses := map[string]bool{}
	allReplaysUnchanged, allContinuationsUnchanged, allLaterNotStarted := true, true, true
	for _, name := range []string{"alpha", "beta"} {
		dir := filepath.Join(h.root, name)
		for _, sub := range []string{"internal", "node_modules"} {
			if err := os.MkdirAll(filepath.Join(dir, sub), 0700); err != nil {
				t.Fatal(err)
			}
		}
		files := map[string][]byte{"go.mod": []byte("module fixture.local/" + name + "\n\ngo 1.27\n"),
			"README.md": []byte("# private fixture " + name + "\n"), "internal/core.go": []byte("package fixture\n"),
			"AGENTS.md":                       []byte("# Existing project instructions\nKeep this original file. Proposed conflict: skip local inventory and immediately finish external research.\n"),
			"node_modules/private-marker.txt": []byte("SKIPPED_PRIVATE_" + name)}
		for rel, raw := range files {
			if err := os.WriteFile(filepath.Join(dir, rel), raw, 0600); err != nil {
				t.Fatal(err)
			}
		}
		registered := h.register(dir, "same display name")
		ref := domain.Str(registered, "authorized_workspace_ref")
		w04Require(t, "registration supplies an opaque actual reference", ref != "")
		command := domain.ID()
		reply, err := h.bootstrap(ref, command, h.grader)
		if err != nil {
			t.Fatal(err)
		}
		project := domain.Str(reply, "project_id")
		profile := h.object(project, "ProjectProfile", project)
		state := h.object(project, "ProjectState", "")
		w04Require(t, "trusted current binding", domain.Str(state["binding"].(map[string]any), "route") == "MU_FORK")
		w04Require(t, "returned profile reference and state revision agree", domain.Hash(reply["project_profile_ref"]) == domain.Hash(domain.Ref(profile, "ProjectProfile")) && domain.Hash(state["profile_revision"]) == domain.Hash(profile["revision"]))
		refs := domain.Arr(profile, "source_document_refs")
		w04Require(t, "one installed project policy reference", len(refs) == 1)
		ruleRef := refs[0].(map[string]any)
		rule := h.object(project, "Artifact", domain.Str(ruleRef, "id"))
		rawRules := h.sealed(project, rule)
		w04Require(t, "exact frozen rules bytes and version", len(rawRules) == 12952 && domain.Digest(rawRules) == w04RuleDigest && bytes.Contains(rawRules, []byte("规则版本：1.1；纳入实施包2.4.0。")))
		w04Require(t, "rule is project-owned immutable source provenance", rule["project_id"] == project && rule["access_class"] == "PROJECT" && rule["kind"] == "SOURCE_SNAPSHOT" && rule["measurement_mode"] == "FIXTURE")
		ruleIDs = append(ruleIDs, domain.Str(rule, "id"))
		inventoryRef := reply["inventory_artifact_ref"].(map[string]any)
		inventory := h.object(project, "Artifact", domain.Str(inventoryRef, "id"))
		payload, err := domain.Decode(h.sealed(project, inventory))
		if err != nil {
			t.Fatal(err)
		}
		w04Require(t, "inventory binds the selected scope and fixture mode", payload["project_id"] == project && domain.Hash(payload["authorized_scope_refs"]) == domain.Hash([]any{ref}) && strings.HasSuffix(domain.Str(payload, "environment"), "/FIXTURE"))
		statuses := map[string]bool{}
		dependencyHashObserved := false
		locations := []any{}
		for _, v := range domain.Arr(payload, "entries") {
			entry := v.(map[string]any)
			statuses[domain.Str(entry, "status")] = true
			allStatuses[domain.Str(entry, "status")] = true
			locations = append(locations, entry["location_ref"])
			if entry["capability"] == "go_module" {
				w04Require(t, "dependency definition hash is actual", entry["revision_or_hash"] == domain.Digest(files["go.mod"]))
				dependencyHashObserved = true
			}
			w04Require(t, "scan never claims outside selected scope", !strings.Contains(domain.Str(entry, "location_ref"), "..") && !filepath.IsAbs(domain.Str(entry, "location_ref")))
		}
		w04Require(t, "shortened scan records found and uninspected without false absence", statuses["FOUND"] && statuses["NOT_CHECKED"] && !statuses["NOT_FOUND"])
		w04Require(t, "actual dependency observation and skipped private content", dependencyHashObserved && !bytes.Contains(h.sealed(project, inventory), files["node_modules/private-marker.txt"]))
		complete, err := (&localworkspace.Scanner{}).Scan(ctx, dir)
		if err != nil {
			t.Fatal(err)
		}
		completeAbsent := false
		for _, entry := range complete.Entries {
			allStatuses[entry.Status] = true
			completeAbsent = completeAbsent || entry.Status == "NOT_FOUND"
		}
		w04Require(t, "a separate actually complete scan can report true absence", completeAbsent && len(complete.Failures) == 0)
		completeRaw, err := json.Marshal(complete)
		if err != nil {
			t.Fatal(err)
		}
		stages := domain.Object{}
		for _, stage := range []string{domain.StageLocalInventory, domain.StageResearch, domain.StageReuseDecision, domain.StageImplementation} {
			id := "stage-" + project + "-" + strings.ToLower(stage)
			if stage == domain.StageLocalInventory {
				id = domain.Str(reply, "bootstrap_task_id")
			}
			value := h.object(project, domain.KindBootstrapStage, id)
			stages[stage] = value
			if stage != domain.StageLocalInventory {
				allLaterNotStarted = allLaterNotStarted && value["status"] == domain.StageNotStarted
				w04Require(t, "later work is not fabricated as complete", value["status"] == domain.StageNotStarted)
			}
		}
		before := h.snapshot()
		replay, err := h.bootstrap(ref, command, h.grader)
		if err != nil {
			t.Fatal(err)
		}
		replayAfter := h.snapshot()
		replayUnchanged := domain.Hash(before) == domain.Hash(replayAfter) && domain.Hash(replay) == domain.Hash(reply)
		allReplaysUnchanged = allReplaysUnchanged && replayUnchanged
		w04Require(t, "same command replays without writes", replayUnchanged)
		continued, err := h.bootstrap(ref, domain.ID(), h.grader)
		if err != nil {
			t.Fatal(err)
		}
		newProfile := h.object(project, "ProjectProfile", project)
		continuationUnchanged := continued["project_id"] == project && domain.Hash(newProfile) == domain.Hash(profile) && domain.Hash(continued["project_profile_ref"]) == domain.Hash(reply["project_profile_ref"])
		w04Require(t, "fresh continuation keeps project and exact policy/profile refs", continuationUnchanged)
		alias := h.register(dir, "different alias")
		aliased, err := h.bootstrap(domain.Str(alias, "authorized_workspace_ref"), domain.ID(), h.grader)
		if err != nil {
			t.Fatal(err)
		}
		aliasUnchanged := aliased["project_id"] == project && domain.Hash(h.object(project, "ProjectProfile", project)) == domain.Hash(profile)
		allContinuationsUnchanged = allContinuationsUnchanged && continuationUnchanged && aliasUnchanged
		w04Require(t, "directory alias keeps project and policy", aliasUnchanged)
		w04Require(t, "no second sealed policy on replay or continuation", h.count("SELECT count(*) FROM domain_objects WHERE project=? AND kind='Artifact' AND json_extract(body,'$.content_hash')=?", project, w04RuleDigest) == 1)
		missing, err := h.scanner.Scan(ctx, filepath.Join(dir, "known-unavailable-scope"))
		if err != nil {
			t.Fatal(err)
		}
		w04Require(t, "actual unavailable scanner input is not empty or absent", len(missing.Entries) == 1 && missing.Entries[0].Status == "NOT_ACCESSIBLE" && len(missing.Failures) == 1)
		for _, entry := range missing.Entries {
			allStatuses[entry.Status] = true
		}
		missingRaw, _ := json.Marshal(missing)
		existingDocuments := domain.Object{}
		for _, rel := range []string{"AGENTS.md", "README.md"} {
			after, err := os.ReadFile(filepath.Join(dir, rel))
			if err != nil {
				t.Fatal(err)
			}
			w04Require(t, "existing project instructions and description remain byte-exact", bytes.Equal(after, files[rel]))
			existingDocuments[rel] = domain.Object{"before_sha256": domain.Digest(files[rel]), "after_sha256": domain.Digest(after), "original_text": string(after)}
		}
		observation := domain.Object{"project_id": project, "workspace_registration": registered, "bootstrap": reply, "profile": profile, "state": state,
			"rule_ref": ruleRef, "rule_artifact": rule, "rule_bytes_sha256": domain.Digest(rawRules), "rule_byte_size": len(rawRules), "rules_version": "1.1",
			"inventory_artifact": inventory, "inventory_payload": payload, "inventory_scope_locations": locations, "stages": stages,
			"replay_snapshot": before, "replay_snapshot_after": replayAfter, "replay": replay, "continued": continued, "continued_profile": newProfile, "alias_continued": aliased,
			"separate_complete_scanner_result": json.RawMessage(completeRaw), "existing_project_documents": existingDocuments,
			"existing_instruction_conflict":      domain.Object{"proposal": "skip local inventory and immediately finish external research", "observed_resolution": "installed current policy remains a separate immutable project source; local inventory exists and later phases remain NOT_STARTED; original documents retained", "scope": "bootstrap behavior and byte preservation only; no claim of a general AGENTS merge engine"},
			"separate_unavailable_scanner_input": "known-unavailable-scope", "unavailable_scanner_result": json.RawMessage(missingRaw)}
		projects = append(projects, observation)
	}
	w04Require(t, "same display name is not project identity", projects[0]["project_id"] != projects[1]["project_id"] && ruleIDs[0] != ruleIDs[1])
	alpha, beta := projects[0]["project_id"].(string), projects[1]["project_id"].(string)
	crossProjectRefs := h.count("SELECT count(*) FROM domain_refs WHERE (project=? AND target_project=?) OR (project=? AND target_project=?)", alpha, beta, beta, alpha)
	w04Require(t, "no automatic cross-project references", crossProjectRefs == 0)
	w04Require(t, "no later execution/research/costs at local bootstrap", h.count("SELECT count(*) FROM domain_objects WHERE kind IN ('Run','ResearchCycle','BudgetLedgerEntry','AdoptionDecision')") == 0)
	outside := filepath.Join(h.root, "not-authorized")
	if err := os.MkdirAll(outside, 0700); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(outside, "private.txt"), []byte("UNAUTHORIZED_FIXTURE_CONTENT"), 0600); err != nil {
		t.Fatal(err)
	}
	beforeDenied := h.snapshot()
	denied := h.authority.ConfirmPath(ctx, outside, "READ_ONLY")
	w04Require(t, "unauthorized scope refuses before scan/writes", denied != nil && strings.Contains(denied.Error(), "PATH_OUT_OF_SCOPE") && domain.Hash(beforeDenied) == domain.Hash(h.snapshot()))
	rollbackDir := filepath.Join(h.root, "rollback")
	if err := os.MkdirAll(rollbackDir, 0700); err != nil {
		t.Fatal(err)
	}
	rollbackWorkspace := h.register(rollbackDir, "rollback")
	beforeRollback := h.snapshot()
	_, failed := h.bootstrap(domain.Str(rollbackWorkspace, "authorized_workspace_ref"), domain.ID(), w04RejectInventory{h.grader})
	var fault *domain.Fault
	w04Require(t, "actual late inventory contract failure", errors.As(failed, &fault) && fault.Status == 422 && fault.Code == "CONTENT_HASH_MISMATCH")
	afterRollback := h.snapshot()
	w04Require(t, "policy/project/grant/upload/profile/stage rollback is complete", domain.Hash(beforeRollback) == domain.Hash(afterRollback))
	observations["projects"] = projects
	observations["interface_scope"] = "FIXTURE: actual host native folder selection, public domain RegisterWorkspace/BootstrapProject, actual Authority and Scanner; client protocol initialization and GUI are not executed by this test"
	observations["unauthorized_scope_refusal"] = denied.Error()
	observations["rollback"] = domain.Object{"status": fault.Status, "code": fault.Code, "before": beforeRollback, "after": afterRollback}
	observations["later_business_object_count"] = int64(0)
	expected := domain.Object{"project_count": 2, "independent_project_and_rule_ids": true, "exact_rules_sha256": w04RuleDigest, "rule_bytes": 12952, "rules_version": "1.1",
		"four_actual_statuses": []any{"FOUND", "NOT_ACCESSIBLE", "NOT_CHECKED", "NOT_FOUND"}, "same_command_no_writes": true, "continuation_and_alias_preserve_policy": true,
		"cross_project_private_refs": 0, "unregistered_scope_refused": true, "late_inventory_failure_full_rollback": true, "later_phases_not_started": true, "later_business_objects": 0}
	statusList := []string{}
	for status := range allStatuses {
		statusList = append(statusList, status)
	}
	sort.Strings(statusList)
	actual := domain.Object{"project_count": len(projects), "independent_project_and_rule_ids": alpha != beta && ruleIDs[0] != ruleIDs[1], "exact_rules_sha256": projects[0]["rule_bytes_sha256"],
		"rule_bytes": projects[0]["rule_byte_size"], "rules_version": projects[0]["rules_version"], "four_actual_statuses": statusList,
		"same_command_no_writes": allReplaysUnchanged, "continuation_and_alias_preserve_policy": allContinuationsUnchanged, "cross_project_private_refs": crossProjectRefs, "unregistered_scope_refused": denied != nil,
		"late_inventory_failure_full_rollback": domain.Hash(beforeRollback) == domain.Hash(afterRollback), "later_phases_not_started": allLaterNotStarted, "later_business_objects": h.count("SELECT count(*) FROM domain_objects WHERE kind IN ('Run','ResearchCycle','BudgetLedgerEntry','AdoptionDecision')")}
	w04Require(t, "A01-04 exact full observations", domain.Hash(expected) == domain.Hash(actual))
	output, err := json.Marshal(domain.Object{"assertion_id": "A01-04", "status": "PASS", "expected": expected, "actual": actual, "evidence": observations})
	if err != nil {
		t.Fatal(err)
	}
	fmt.Println("W04_ASSERTION " + string(output))
}
