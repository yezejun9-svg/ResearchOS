package domain

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"researchos.local/research-os/internal/store"
	"sort"
	"strconv"
	"strings"
	"testing"
	"time"
)

type independentWorkspace struct {
	expected            WorkspaceBinding
	calls               int
	records             []any
	restored            bool
	root                string
	expectedDestination string
}

func (s *independentWorkspace) SnapshotWorkspace(_ context.Context, b WorkspaceBinding, destination string, _ BackupWorkspaceLimits) (BackupWorkspaceSnapshot, error) {
	if Hash(b) != Hash(s.expected) || filepath.Clean(destination) != filepath.Clean(s.expectedDestination) || b.PrincipalID != s.expected.PrincipalID || b.AuthorizedRef != "tool-workspace" || b.Access != "READ_ONLY" || b.ProjectID == nil || *b.ProjectID != "00172b0dce9cbf45a78a9625552efd10" {
		return BackupWorkspaceSnapshot{}, fmt.Errorf("SYNTHETIC_WORKSPACE_IDENTITY_MISMATCH")
	}
	witness := []byte("workspace-file-observation-7719")
	if s.restored {
		if filepath.Clean(b.RealPath) != filepath.Clean(s.root) {
			return BackupWorkspaceSnapshot{}, fmt.Errorf("restored pin mismatch")
		}
		raw, e := os.ReadFile(filepath.Join(s.root, "evidence.txt"))
		if e != nil || Digest(raw) != Digest(witness) {
			return BackupWorkspaceSnapshot{}, fmt.Errorf("restored witness mismatch")
		}
	}
	s.calls++
	s.records = append(s.records, Object{"binding": b, "principal": b.PrincipalID, "destination": destination, "synthetic": true, "original_filesystem_read": false, "witness_hash": Digest(witness), "witness_bytes": len(witness)})
	return BackupWorkspaceSnapshot{Directories: []string{}, Files: []BackupWorkspaceFile{{Path: "evidence.txt", Data: witness}}}, nil
}
func independentWrite(t *testing.T, path string, v any) {
	t.Helper()
	f, e := os.OpenFile(path, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
	if e != nil {
		t.Fatal(e)
	}
	_, e = f.Write(Bytes(v))
	ce := f.Close()
	if e != nil || ce != nil {
		t.Fatal(e, ce)
	}
}
func independentInventory(t *testing.T, db *sql.DB) Object {
	t.Helper()
	tx, e := db.Begin()
	if e != nil {
		t.Fatal(e)
	}
	v, e := validateProviderInventory(tx, "", "")
	tx.Rollback()
	if e != nil {
		t.Fatal("inventory", e)
	}
	r := Object{}
	for k, v := range v {
		r[k] = v
	}
	return r
}
func independentTable(v Object, name string) Object { return v["tables"].(Object)[name].(Object) }
func independentRows(v Object, name string) []string {
	return independentTable(v, name)["rows"].(Object)["typed_row_multiset"].([]string)
}
func independentSubset(t *testing.T, a, b []string, label string) {
	t.Helper()
	m := map[string]int{}
	for _, r := range b {
		m[r]++
	}
	for _, r := range a {
		m[r]--
		if m[r] < 0 {
			t.Fatal("original immutable row changed", label)
		}
	}
}
func independentCellRows(v Object, name string) []Object {
	tab := independentTable(v, name)["rows"].(Object)
	cols := tab["columns"].([]string)
	out := []Object{}
	for _, r := range tab["typed_row_multiset"].([]string) {
		var cells [][]any
		if json.Unmarshal([]byte(r), &cells) != nil {
			panic("typed row decode")
		}
		o := Object{}
		for i, c := range cells {
			if len(c) > 1 {
				o[cols[i]] = c[1]
			} else {
				o[cols[i]] = nil
			}
		}
		out = append(out, o)
	}
	return out
}
func independentClone(o Object, omit ...string) Object {
	c := Object{}
	for k, v := range o {
		c[k] = v
	}
	for _, k := range omit {
		delete(c, k)
	}
	return c
}
func independentNumber(t *testing.T, o Object, k string) int64 {
	t.Helper()
	var n int64
	var e error
	if s, ok := o[k].(string); ok {
		n, e = strconv.ParseInt(s, 10, 64)
	} else {
		n, e = Num(o, k)
	}
	if e != nil {
		t.Fatal("integer", k, e)
	}
	return n
}
func independentBody(t *testing.T, r Object) Object {
	t.Helper()
	b, e := Decode([]byte(Str(r, "body")))
	if e != nil {
		t.Fatal(e)
	}
	return b
}
func independentTime(t *testing.T, value, start, end string) {
	t.Helper()
	v, e := time.Parse(time.RFC3339Nano, value)
	lo, e1 := time.Parse(time.RFC3339Nano, start)
	hi, e2 := time.Parse(time.RFC3339Nano, end)
	if e != nil || e1 != nil || e2 != nil || v.Before(lo) || v.After(hi) {
		t.Fatal("restore time outside actual invocation", value, start, end)
	}
}
func independentObjectKey(r Object) string {
	return Str(r, "project") + "|" + Str(r, "kind") + "|" + Str(r, "id")
}
func independentNewRows(t *testing.T, before, after Object, name string) []Object {
	t.Helper()
	b := independentRows(before, name)
	a := independentRows(after, name)
	independentSubset(t, b, a, name)
	known := map[string]int{}
	for _, s := range b {
		known[s]++
	}
	objects := independentCellRows(after, name)
	newRows := []Object{}
	for i, s := range a {
		if known[s] > 0 {
			known[s]--
		} else {
			newRows = append(newRows, objects[i])
		}
	}
	return newRows
}
func independentRestoreDelta(t *testing.T, before, after Object, destination, start, end string) Object {
	t.Helper()
	allowed := map[string]bool{"domain_objects": true, "domain_versions": true, "domain_refs": true, "outbox": true, "event_state_snapshots": true, "resource_effects": true, "auth_credentials": true, "backup_restore_barriers": true, "client_command_queue": true, "client_control_receipts": true, "client_queue_fences": true, "client_control_requests": true, "client_sessions": true, "retrieval_roots": true}
	delta := Object{}
	old := before["tables"].(Object)
	cur := after["tables"].(Object)
	for n, b := range old {
		a, ok := cur[n]
		if !ok {
			t.Fatal("restore removed table", n)
		}
		if Hash(b) != Hash(a) {
			if !allowed[n] {
				t.Fatal("unexpected restored table change", n)
			}
			delta[n] = Object{"before": Hash(b), "after": Hash(a)}
		}
	}
	for n := range cur {
		if _, ok := old[n]; !ok && n != "backup_restore_barriers" {
			t.Fatal("unexpected new restore table", n)
		}
	}
	// Full old schema objects survive. Only the named existing restore fence
	// producers may append schema; their actual SQL remains in the full vector.
	bs := before["schema"].(Object)["typed_row_multiset"].([]string)
	as := after["schema"].(Object)["typed_row_multiset"].([]string)
	independentSubset(t, bs, as, "sqlite_schema")
	knownSchema := map[string]bool{}
	for _, v := range bs {
		knownSchema[v] = true
	}
	allowedSchema := map[string]bool{"backup_restore_barriers": true, "sqlite_autoindex_backup_restore_barriers_1": true, "backup_require_fresh_observation": true, "client_session_epoch_no_regression": true, "client_session_require_fresh": true}
	for _, v := range as {
		if knownSchema[v] {
			continue
		}
		var cells [][]any
		if json.Unmarshal([]byte(v), &cells) != nil || len(cells) < 4 || len(cells[1]) < 2 || !allowedSchema[fmt.Sprint(cells[1][1])] {
			t.Fatal("unexpected restore schema append", v)
		}
	}
	oldobj := map[string]Object{}
	newobj := map[string]Object{}
	for _, r := range independentCellRows(before, "domain_objects") {
		oldobj[independentObjectKey(r)] = r
	}
	for _, r := range independentCellRows(after, "domain_objects") {
		newobj[independentObjectKey(r)] = r
	}
	active := map[string]Object{}
	states := map[string]Object{}
	activeStates := map[string]bool{"QUEUED": true, "STARTING": true, "RUNNING": true, "CANCEL_REQUESTED": true, "RECONCILING": true, "LOST": true}
	expectedVersions := map[string]Object{}
	oldWorkspace := Object{}
	for key, r := range oldobj {
		if r["kind"] == "WorkspaceBinding" {
			b := independentBody(t, r)
			if b["authorized_workspace_ref"] == "tool-workspace" {
				oldWorkspace = b
			}
		}
		if r["kind"] == "ProjectState" {
			states[Str(r, "project")] = independentBody(t, r)
		}
		if r["kind"] == "Run" {
			b := independentBody(t, r)
			if activeStates[Str(b, "status")] {
				active[key] = b
			}
		}
	}
	versionKey := func(project, kind, id string, rev int64) string {
		return project + "|" + kind + "|" + id + "|" + fmt.Sprint(rev)
	}
	for key, r := range oldobj {
		a, ok := newobj[key]
		if !ok {
			t.Fatal("missing original object", key)
		}
		b := independentBody(t, r)
		ab := independentBody(t, a)
		kind := Str(r, "kind")
		if orig, yes := active[key]; yes {
			if Hash(independentClone(orig, "status", "lease_token_hash", "lease_expires_at", "revision", "updated_at")) != Hash(independentClone(ab, "status", "lease_token_hash", "lease_expires_at", "revision", "updated_at")) {
				t.Fatal("Run immutable fields changed", key)
			}
			status := "RECONCILING"
			if orig["status"] == "CANCEL_REQUESTED" {
				status = "CANCEL_REQUESTED"
			}
			if ab["status"] != status || ab["lease_expires_at"] != "1970-01-01T00:00:00Z" || independentNumber(t, ab, "revision") != independentNumber(t, orig, "revision")+1 || Str(ab, "lease_token_hash") == "" || ab["lease_token_hash"] == orig["lease_token_hash"] {
				t.Fatal("bad exact Run fence", key)
			}
			independentTime(t, Str(ab, "updated_at"), start, end)
			expectedVersions[versionKey(Str(a, "project"), kind, Str(a, "id"), independentNumber(t, ab, "revision"))] = Object{"body": ab, "content_hash": nil}
		} else if kind == "ProjectState" {
			if Hash(independentClone(b, "event_sequence", "revision", "updated_at")) != Hash(independentClone(ab, "event_sequence", "revision", "updated_at")) {
				t.Fatal("ProjectState unrelated mutation")
			}
		} else if kind == "WorkspaceBinding" && Str(b, "authorized_workspace_ref") == "tool-workspace" && b["status"] == "ACTIVE" {
			expected := independentClone(b)
			expected["real_path"] = BackupWorkspaceDestination(destination, "tool-workspace")
			expected["display_path"] = expected["real_path"]
			expected["revision"] = independentNumber(t, b, "revision") + 2
			expected["status"] = "ACTIVE"
			expected["host_principal_ref"] = "SYNTHETIC_INDEPENDENT_RESTORE"
			if Hash(expected) != Hash(ab) || a["content_hash"] != Digest([]byte(Str(a, "body"))) {
				t.Fatal("workspace exact two-stage remap")
			}
		} else if kind == "Project" && b["authorized_workspace_ref"] == "tool-workspace" && len(oldWorkspace) > 0 {
			if b["id"] != "00172b0dce9cbf45a78a9625552efd10" || b["real_path"] != oldWorkspace["real_path"] {
				t.Fatal("original Project workspace binding")
			}
			expected := independentClone(b)
			expected["real_path"] = BackupWorkspaceDestination(destination, "tool-workspace")
			expected["revision"] = independentNumber(t, b, "revision") + 1
			if Hash(expected) != Hash(ab) || a["content_hash"] != Digest([]byte(Str(a, "body"))) {
				t.Fatal("Project exact opaque remap")
			}
		} else if Hash(r) != Hash(a) {
			t.Fatal("unrelated original object changed", key)
		}
		if Hash(r) != Hash(a) {
			if Hash(independentClone(r, "body", "revision", "content_hash")) != Hash(independentClone(a, "body", "revision", "content_hash")) {
				t.Fatal("SQL identity or immutable flag changed", key)
			}
			if independentNumber(t, a, "revision") != independentNumber(t, ab, "revision") {
				t.Fatal("SQL/body revision mismatch")
			}
			if kind == "Run" || kind == "ProjectState" {
				if a["content_hash"] != nil {
					t.Fatal("mutable typed object unexpected hash")
				}
			}
		}
	}
	events := independentNewRows(t, before, after, "outbox")
	snapshots := independentNewRows(t, before, after, "event_state_snapshots")
	if len(events) != len(active) || len(snapshots) != len(active) {
		t.Fatal("restore event/snapshot/run count", len(events), len(snapshots), len(active))
	}
	sort.Slice(events, func(i, j int) bool {
		if events[i]["project"] != events[j]["project"] {
			return Str(events[i], "project") < Str(events[j], "project")
		}
		return independentNumber(t, events[i], "sequence") < independentNumber(t, events[j], "sequence")
	})
	maxSeq := map[string]int64{}
	for _, r := range independentCellRows(before, "outbox") {
		p := Str(r, "project")
		n := independentNumber(t, r, "sequence")
		if n > maxSeq[p] {
			maxSeq[p] = n
		}
	}
	snapshotByEvent := map[string]Object{}
	for _, s := range snapshots {
		if snapshotByEvent[Str(s, "event_id")] != nil {
			t.Fatal("duplicate snapshot")
		}
		snapshotByEvent[Str(s, "event_id")] = s
	}
	seenRun := map[string]bool{}
	seenEvent := map[string]bool{}
	chain := []any{}
	for _, row := range events {
		ev := independentBody(t, row)
		project := Str(row, "project")
		id := Str(ev, "id")
		aggregate, ok := ev["aggregate_ref"].(map[string]any)
		if !ok {
			t.Fatal("restore aggregate")
		}
		key := project + "|Run|" + Str(aggregate, "id")
		original, ok := active[key]
		if !ok || seenRun[key] {
			t.Fatal("event not bijective to original active run", key)
		}
		seenRun[key] = true
		seenEvent[id] = true
		run := independentBody(t, newobj[key])
		if Hash(aggregate) != Hash(Ref(run, "Run")) {
			t.Fatal("event restored Run reference")
		}
		if ev["event_type"] != "RUN_CHANGED" || ev["actor_id"] != "restore-local-admin" || ev["project_id"] != project || ev["causation_id"] != nil || ev["event_data_artifact_ref"] != nil || Str(ev, "correlation_id") == "" || ev["receipt_hash"] != Receipt(ev) || independentNumber(t, ev, "revision") != 1 || row["id"] != id || independentNumber(t, row, "acknowledged") != 0 {
			t.Fatal("restore event producer mismatch")
		}
		independentTime(t, Str(ev, "created_at"), start, end)
		state, ok := states[project]
		if !ok {
			t.Fatal("original ProjectState missing")
		}
		seq := independentNumber(t, state, "event_sequence")
		if maxSeq[project] > seq {
			seq = maxSeq[project]
		}
		seq++
		if independentNumber(t, ev, "sequence") != seq || independentNumber(t, row, "sequence") != seq {
			t.Fatal("restore event sequence")
		}
		snap := snapshotByEvent[id]
		if snap == nil || snap["project"] != project {
			t.Fatal("unmatched restore snapshot")
		}
		sb := independentBody(t, snap)
		expected := independentClone(state)
		expected["revision"] = independentNumber(t, state, "revision") + 1
		expected["event_sequence"] = seq
		expected["updated_at"] = sb["updated_at"]
		independentTime(t, Str(sb, "updated_at"), start, end)
		if Hash(expected) != Hash(sb) || independentNumber(t, snap, "revision") != independentNumber(t, sb, "revision") {
			t.Fatal("snapshot not exact next ProjectState")
		}
		states[project] = sb
		maxSeq[project] = seq
		erow, ok := newobj[project+"|EventEnvelope|"+id]
		if !ok || Str(erow, "body") != Str(row, "body") || erow["content_hash"] != ev["receipt_hash"] || independentNumber(t, erow, "immutable") != 1 {
			t.Fatal("event original object/outbox/hash")
		}
		expectedVersions[versionKey(project, "ProjectState", Str(sb, "id"), independentNumber(t, sb, "revision"))] = Object{"body": sb, "content_hash": nil}
		expectedVersions[versionKey(project, "EventEnvelope", id, 1)] = Object{"body": ev, "content_hash": ev["receipt_hash"]}
		chain = append(chain, Object{"original_run": original, "restored_run": run, "event": ev, "snapshot": sb})
	}
	for project, state := range states {
		found := false
		for _, r := range newobj {
			if r["project"] == project && r["kind"] == "ProjectState" {
				found = true
				if Hash(independentBody(t, r)) != Hash(state) {
					t.Fatal("final ProjectState mismatch")
				}
			}
		}
		if !found {
			t.Fatal("final state absent")
		}
	}
	for key, r := range newobj {
		if _, exists := oldobj[key]; !exists {
			if r["kind"] != "EventEnvelope" || !seenEvent[Str(r, "id")] {
				t.Fatal("unexpected new domain object", key)
			}
		}
	}
	versions := independentNewRows(t, before, after, "domain_versions")
	if len(versions) != len(expectedVersions) {
		t.Fatal("unexpected historical append count", len(versions), len(expectedVersions))
	}
	for _, r := range versions {
		k := versionKey(Str(r, "project"), Str(r, "kind"), Str(r, "id"), independentNumber(t, r, "revision"))
		expected := expectedVersions[k]
		if expected == nil || Hash(independentBody(t, r)) != Hash(expected["body"]) || Hash(r["content_hash"]) != Hash(expected["content_hash"]) {
			t.Fatal("unexpected historical producer append", k)
		}
	}
	// Original references stay, and each new reference must belong to one of the
	// exact new versions. Targets must resolve to the actual full immutable row.
	// Independent frozen producer reconstruction: never invoke Service.refs/ref/put.
	refs := independentNewRows(t, before, after, "domain_refs")
	relationTargets := map[string]string{
		"budget_policy_id": "BudgetPolicy", "run_policy_id": "RunPolicy", "goal_id": "Goal", "task_id": "Task", "task_ids": "Task", "dependency_task_ids": "Task", "active_run_id": "Run", "run_id": "Run", "run_ids": "Run", "runtime_id": "RuntimeRegistration", "context_bundle_id": "ContextBundle", "no_progress_record_id": "NoProgressRecord", "acceptance_id": "AcceptanceReceipt", "acceptance_ids": "AcceptanceReceipt", "output_artifact_ids": "Artifact", "result_artifact_ids": "Artifact", "checkpoint_artifact_id": "Artifact", "blocking_conflict_ids": "Conflict", "conflict_ids": "Conflict", "active_goal_ids": "Goal", "active_cycle_id": "ResearchCycle", "latest_release_id": "MilestoneRelease", "pending_change_ids": "ChangeProposal", "origin_evidence_id": "Evidence", "verified_by_run_id": "Run", "candidate_evidence_ids": "Evidence", "required_experiment_ids": "Experiment", "decision_ids": "DecisionReceipt", "follow_up_task_ids": "Task", "cycle_id": "ResearchCycle", "qualification_id": "Qualification", "qualification_ids": "Qualification", "impact_link_ids": "ImpactLink", "semantic_review_run_id": "Run", "blocked_task_ids": "Task", "continuable_task_ids": "Task", "parent_release_id": "MilestoneRelease", "open_resource_request_ids": "ResourceRequest", "baseline_skill_id": "SkillVersion", "experiment_id": "Experiment", "rollback_skill_id": "SkillVersion", "regression_acceptance_id": "AcceptanceReceipt", "canary_acceptance_id": "AcceptanceReceipt", "rollback_verified_receipt_id": "AcceptanceReceipt", "last_cycle_id": "ResearchCycle", "policy_id": "BudgetPolicy", "reservation_id": "BudgetLedgerEntry", "release_id": "MilestoneRelease", "resource_request_id": "ResourceRequest", "resolution_proposal_id": "ChangeProposal",
	}
	currentAtPut := map[string]Object{}
	for k, row := range oldobj {
		currentAtPut[k] = row
	}
	historyRows := map[string]Object{}
	for _, row := range independentCellRows(after, "domain_versions") {
		k := versionKey(Str(row, "project"), Str(row, "kind"), Str(row, "id"), independentNumber(t, row, "revision"))
		if historyRows[k] != nil {
			t.Fatal("duplicate immutable target version")
		}
		historyRows[k] = row
	}
	expectedRefCounts := map[string]int{}
	expectedRefTotal := 0
	generatedOwners := map[string]bool{}
	var generateOwner func(string, string, Object)
	generateOwner = func(project, kind string, body Object) {
		id := Str(body, "id")
		revision := independentNumber(t, body, "revision")
		ownerKey := versionKey(project, kind, id, revision)
		expected := expectedVersions[ownerKey]
		if expected == nil || generatedOwners[ownerKey] || Hash(body) != Hash(expected["body"]) {
			t.Fatal("reference producer owner mismatch", ownerKey)
		}
		generatedOwners[ownerKey] = true
		ownerRow := historyRows[ownerKey]
		if ownerRow == nil || Hash(independentBody(t, ownerRow)) != Hash(body) || Hash(ownerRow["content_hash"]) != Hash(expected["content_hash"]) {
			t.Fatal("reference owner immutable witness")
		}
		currentAtPut[project+"|"+kind+"|"+id] = ownerRow
		add := func(field, tp, tk, tid string, tr int64, wantHash any, exact bool) {
			if tp != project && !(tp == "" && (tk == "BudgetPolicy" || tk == "RunPolicy")) {
				t.Fatal("reference foreign target")
			}
			latest := currentAtPut[tp+"|"+tk+"|"+tid]
			if latest == nil {
				t.Fatal("reference producer-time target absent", field)
			}
			latestRev := independentNumber(t, latest, "revision")
			target := latest
			// Newly produced owner kinds are fixed Run/ProjectState/EventEnvelope.
			// EventEnvelope may carry an exact historical VersionRef; other two require current.
			if exact && kind == "EventEnvelope" {
				target = historyRows[versionKey(tp, tk, tid, tr)]
			} else if exact && latestRev != tr {
				t.Fatal("reference exact producer-time revision mismatch")
			}
			if target == nil {
				t.Fatal("reference immutable target absent")
			}
			targetRevision := independentNumber(t, target, "revision")
			if targetRevision != tr {
				t.Fatal("reference requested target revision differs")
			}
			witness := historyRows[versionKey(tp, tk, tid, tr)]
			if witness == nil || Str(witness, "body") != Str(target, "body") || Hash(witness["content_hash"]) != Hash(target["content_hash"]) {
				t.Fatal("reference complete target history witness differs")
			}
			if exact && Hash(wantHash) != Hash(witness["content_hash"]) {
				t.Fatal("reference VersionRef content hash mismatch")
			}
			tuple := Object{"project": project, "kind": kind, "id": id, "revision": fmt.Sprint(revision), "field": field, "target_project": tp, "target_kind": tk, "target_id": tid, "target_revision": fmt.Sprint(tr)}
			expectedRefCounts[Hash(tuple)]++
			expectedRefTotal++
		}
		var walk func(string, any)
		walk = func(path string, value any) {
			switch v := value.(type) {
			case map[string]any:
				if _, ok := v["entity_type"]; ok {
					if len(v) != 4 {
						t.Fatal("VersionRef shape")
					}
					tk, ok1 := v["entity_type"].(string)
					tid, ok2 := v["id"].(string)
					if !ok1 || !ok2 || tk == "" || tid == "" {
						t.Fatal("VersionRef identity")
					}
					if _, ok := v["content_hash"]; !ok {
						t.Fatal("VersionRef missing content hash")
					}
					add(path, project, tk, tid, independentNumber(t, v, "revision"), v["content_hash"], true)
					return
				}
				for field, x := range v {
					if field == "id" || field == "project_id" {
						continue
					}
					target := relationTargets[field]
					if kind == "RuntimeRegistration" && field == "qualification_ids" {
						target = "AcceptanceReceipt"
					}
					if field == "supersedes_id" || field == "parent_policy_id" {
						target = kind
					}
					if target != "" && x != nil {
						values := []any{x}
						if array, ok := x.([]any); ok {
							values = array
						}
						for _, member := range values {
							tid, ok := member.(string)
							if !ok {
								t.Fatal("relation member is not string")
							}
							tp := project
							if field == "parent_policy_id" && currentAtPut[tp+"|"+target+"|"+tid] == nil {
								tp = ""
							}
							row := currentAtPut[tp+"|"+target+"|"+tid]
							if row == nil {
								t.Fatal("relation target missing", field)
							}
							add(path+"/"+field, tp, target, tid, independentNumber(t, row, "revision"), nil, false)
						}
					} else {
						walk(path+"/"+field, x)
					}
				}
			case []any:
				for n, x := range v {
					walk(fmt.Sprintf("%s/%d", path, n), x)
				}
			}
		}
		walk("", body)
	}
	// Each original Run is put, then its ProjectState, then EventEnvelope; use the
	// already independently checked per-project actual event order, not final latest.
	for _, entry := range chain {
		c := entry.(Object)
		run := c["restored_run"].(Object)
		event := c["event"].(Object)
		snapshot := c["snapshot"].(Object)
		project := Str(event, "project_id")
		generateOwner(project, "Run", run)
		generateOwner(project, "ProjectState", snapshot)
		generateOwner(project, "EventEnvelope", event)
	}
	if len(generatedOwners) != len(expectedVersions) || len(refs) != expectedRefTotal {
		t.Fatal("reference complete producer closure count")
	}
	rowids := map[int64]bool{}
	for _, r := range independentCellRows(before, "domain_refs") {
		id := independentNumber(t, r, "rowid")
		if id < 1 || rowids[id] {
			t.Fatal("old reference rowid")
		}
		rowids[id] = true
	}
	actualRefCounts := map[string]int{}
	for _, r := range refs {
		id := independentNumber(t, r, "rowid")
		if id < 1 || rowids[id] {
			t.Fatal("new reference rowid duplicate")
		}
		rowids[id] = true
		if len(r) != 10 {
			t.Fatal("reference row shape")
		}
		actualRefCounts[Hash(independentClone(r, "rowid"))]++
	}
	if Hash(actualRefCounts) != Hash(expectedRefCounts) {
		t.Fatal("complete reference multiset differs", actualRefCounts, expectedRefCounts)
	}
	// Every original effect row remains. Appends equal the original latest state
	// with only the five fields written by backupFence/effectAppend changed.
	latest := map[string]Object{}
	for _, r := range independentCellRows(before, "resource_effects") {
		k := Str(r, "project") + "|" + Str(r, "run") + "|" + Str(r, "effect_key")
		if latest[k] == nil || independentNumber(t, r, "sequence") > independentNumber(t, latest[k], "sequence") {
			latest[k] = r
		}
	}
	need := map[string]Object{}
	for k, r := range latest {
		b := independentBody(t, r)
		if b["state"] == "PREPARED" || b["state"] == "STARTED" || b["state"] == "UNKNOWN" {
			need[k] = r
		}
	}
	appended := independentNewRows(t, before, after, "resource_effects")
	if len(appended) != len(need) {
		t.Fatal("restore effect append count")
	}
	for _, r := range appended {
		k := Str(r, "project") + "|" + Str(r, "run") + "|" + Str(r, "effect_key")
		prior := need[k]
		if prior == nil {
			t.Fatal("unexpected restored effect")
		}
		delete(need, k)
		b := independentBody(t, prior)
		ab := independentBody(t, r)
		n := independentNumber(t, prior, "sequence") + 1
		if independentNumber(t, r, "sequence") != n || independentNumber(t, ab, "sequence") != n || ab["state"] != "UNKNOWN" || ab["restore_reason"] != "SNAPSHOT_MAY_PREDATE_EXTERNAL_DISPATCH" || Hash(independentClone(b, "sequence", "observed_at", "state", "restore_reason")) != Hash(independentClone(ab, "sequence", "observed_at", "state", "restore_reason")) {
			t.Fatal("restore effect original identity/cost changed")
		}
		independentTime(t, Str(ab, "observed_at"), start, end)
	}
	delta["restore_event_chain"] = chain
	delta["original_immutable_rows_retained"] = true
	delta["schema_before"] = Hash(before["schema"])
	delta["schema_after"] = Hash(after["schema"])
	return delta
}

func independentDecodedArchive(t *testing.T, path string, key []byte, out string, wantWorkspace bool) Object {
	t.Helper()
	m, files, e := readBackup(path, key)
	if e != nil {
		t.Fatal(e)
	}
	refs := Object{}
	dir := filepath.Join(out, "decoded")
	if e = os.Mkdir(dir, 0700); e != nil {
		t.Fatal(e)
	}
	for n, b := range files {
		if filepath.Base(n) != n {
			t.Fatal("decoded filename")
		}
		if e = os.WriteFile(filepath.Join(dir, n), b, 0600); e != nil {
			t.Fatal(e)
		}
		refs[n] = Object{"sha256": Digest(b), "bytes": len(b)}
	}
	var idx backupWorkspaceIndex
	if wantWorkspace {
		if e = json.Unmarshal(files["workspace-index.json"], &idx); e != nil || idx.Format != "RESEARCHOS_WORKSPACE_SNAPSHOT_V1" {
			t.Fatal("workspace index", e)
		}
	} else {
		for name := range files {
			if strings.HasPrefix(name, "workspace-") {
				t.Fatal("unexpected workspace decoded resource", name)
			}
		}
		for _, entry := range m.Files {
			if strings.HasPrefix(entry.Name, "workspace-") {
				t.Fatal("unexpected workspace manifest resource", entry.Name)
			}
		}
	}
	if wantWorkspace {
		if len(idx.Roots) != 1 || idx.Roots[0].Ref != "tool-workspace" || len(idx.Roots[0].Files) != 1 || len(idx.Roots[0].Directories) != 0 {
			t.Fatal("workspace root/file bound")
		}
		f := idx.Roots[0].Files[0]
		if f.Path != "evidence.txt" || f.Size != 31 || f.Hash != Digest([]byte("workspace-file-observation-7719")) || Digest(files[f.Blob]) != f.Hash {
			t.Fatal("decoded witness mismatch")
		}
	} else if len(idx.Roots) != 0 {
		t.Fatal("unexpected workspace")
	}
	if _, e = providerSemanticVector(filepath.Join(dir, "state.sqlite"), filepath.Join(out, "decoded-semantic.json.gz")); e != nil {
		t.Fatal(e)
	}
	r := Object{"manifest": m, "files": refs, "workspace_index": idx}
	independentWrite(t, filepath.Join(out, "decoded-chain.json"), r)
	return r
}
func TestIndependentProviderPublicArchiveBoundary(t *testing.T) {
	raw, e := os.ReadFile(os.Getenv("RESEARCHOS_INDEPENDENT_PUBLIC_SPEC"))
	if e != nil {
		t.Fatal(e)
	}
	spec, e := Decode(raw)
	if e != nil {
		t.Fatal(e)
	}
	input, e := os.ReadFile(Str(spec, "input"))
	if e != nil || Digest(input) != spec["input_sha256"] {
		t.Fatal("input hash", e)
	}
	dir := Str(spec, "output")
	if e = os.Mkdir(dir, 0700); e != nil {
		t.Fatal(e)
	}
	path := filepath.Join(dir, "case.sqlite")
	if e = os.WriteFile(path, input, 0600); e != nil {
		t.Fatal(e)
	}
	before, e := providerSemanticVector(path, filepath.Join(dir, "semantic-before.json.gz"))
	if e != nil {
		t.Fatal(e)
	}
	pre, e := os.ReadFile(path)
	if e != nil || Digest(pre) != Digest(input) {
		t.Fatal("before Open copy differs")
	}
	db, e := store.Open(path)
	if e != nil {
		t.Fatal(e)
	}
	result := Object{"label": "INDEPENDENT_ZERO_MODEL_PUBLIC_BOUNDARY", "input_sha256": Digest(input), "pre_open_sha256": Digest(pre), "mode": spec["mode"], "model_calls": 0, "HTTP": 0, "worker_starts": 0, "synthetic_workspace": spec["id"] == "0"}
	t.Cleanup(func() {
		_, ce := db.Exec("PRAGMA wal_checkpoint(TRUNCATE)")
		if ce != nil {
			t.Error(ce)
		}
		if ce = db.Close(); ce != nil {
			t.Error(ce)
		}
		b, ce := os.ReadFile(path)
		if ce != nil {
			t.Error(ce)
		}
		result["closed_sha256"] = Digest(b)
		after, ce := providerSemanticVector(path, filepath.Join(dir, "semantic-after.json.gz"))
		if ce != nil {
			t.Error(ce)
		} else {
			allowed := map[string]bool{}
			if spec["mode"] != "positive" {
				allowed["resource_effects"] = true
				allowed["runtime_dispatches"] = true
			}
			if Hash(before["schema"]) != Hash(after["schema"]) {
				t.Error("original copied schema changed")
			}
			changes := []string{}
			for n, v := range before["tables"].(Object) {
				if Hash(v) != Hash(after["tables"].(Object)[n]) {
					changes = append(changes, n)
					if !allowed[n] {
						t.Error("undeclared source mutation", n)
					}
				}
			}
			result["changed_tables"] = changes
		}
		original, ce := os.ReadFile(Str(spec, "input"))
		if ce != nil || Digest(original) != spec["input_sha256"] {
			t.Error("immutable source drift", ce)
		}
		result["test_failed"] = t.Failed()
		independentWrite(t, filepath.Join(dir, "actual.json"), result)
	})
	contracts, e := LoadContracts("../../spec/v2.0/contracts")
	if e != nil {
		t.Fatal(e)
	}
	svc := &Service{DB: db, Contracts: contracts}
	bindings, e := workspaceBackupBindings(db)
	if e != nil {
		t.Fatal(e)
	}
	hasWorkspace := spec["id"] == "0"
	if !hasWorkspace {
		var allBindings int
		if e = db.QueryRow(`SELECT count(*) FROM domain_objects WHERE kind='WorkspaceBinding'`).Scan(&allBindings); e != nil || allBindings != 0 {
			t.Fatal("original all WorkspaceBinding rows must be zero", allBindings, e)
		}
		result["original_all_workspace_binding_count"] = allBindings
	}
	var ws *independentWorkspace
	if hasWorkspace {
		if len(bindings) != 1 {
			t.Fatal("workspace count")
		}
		b := bindings[0]
		if b.HostPrincipalRef != "fixture-local-user" || b.Revision != 1 || b.Status != "ACTIVE" || b.ClientID != "mu-client" {
			t.Fatal("original fixed workspace metadata")
		}
		ws = &independentWorkspace{expected: b, expectedDestination: filepath.Join(dir, "archive")}
	} else if len(bindings) != 0 {
		t.Fatal("unexpected workspace")
	}
	if spec["mode"] != "positive" {
		rows, er := db.Query("SELECT name,sql FROM sqlite_schema WHERE type='trigger' ORDER BY name")
		if er != nil {
			t.Fatal(er)
		}
		tr := [][2]string{}
		for rows.Next() {
			var n, s string
			if er = rows.Scan(&n, &s); er != nil {
				t.Fatal(er)
			}
			tr = append(tr, [2]string{n, s})
		}
		rows.Close()
		tx, er := db.Begin()
		if er != nil {
			t.Fatal(er)
		}
		defer tx.Rollback()
		for _, x := range tr {
			if _, er = tx.Exec(`DROP TRIGGER "` + strings.ReplaceAll(x[0], `"`, `""`) + `"`); er != nil {
				t.Fatal(er)
			}
		}
		statements := []string{`DELETE FROM runtime_dispatches`, `UPDATE resource_effects SET body=json_remove(body,'$.payload.provider_transport') WHERE json_extract(body,'$.payload.capability')='MODEL'`}
		mutations := []any{}
		for _, s := range statements {
			r, er := tx.Exec(s)
			if er != nil {
				t.Fatal(er)
			}
			n, er := r.RowsAffected()
			if er != nil {
				t.Fatal(er)
			}
			mutations = append(mutations, Object{"sql": s, "rows": n})
		}
		for _, x := range tr {
			if _, er = tx.Exec(x[1]); er != nil {
				t.Fatal(er)
			}
		}
		if er = tx.Commit(); er != nil {
			t.Fatal(er)
		}
		result["mutations"] = mutations
		result["triggers_restored"] = tr
	}
	key := backupTestKey(t)
	archive := filepath.Join(dir, "archive")
	var manifest BackupManifest
	if hasWorkspace {
		manifest, e = svc.CreateBackupWithWorkspaces(context.Background(), archive, key, ws)
	} else {
		manifest, e = svc.CreateBackup(context.Background(), archive, key)
	}
	result["backup_manifest"] = manifest
	if e != nil {
		result["backup_error"] = e.Error()
	}
	if spec["mode"] != "positive" {
		if e == nil {
			t.Fatal("PUBLIC_CREATEBACKUP_UNEXPECTED_ACCEPT")
		}
		if _, er := os.Stat(archive); !os.IsNotExist(er) {
			t.Fatal("refusal published destination", er)
		}
		result["public_refusal_proven"] = true
		return
	}
	if e != nil {
		t.Fatal("public backup prerequisite/refusal", e)
	}
	firstDir := filepath.Join(dir, "archive-proof")
	if e = os.Mkdir(firstDir, 0700); e != nil {
		t.Fatal(e)
	}
	result["archive_chain"] = independentDecodedArchive(t, archive, key, firstDir, hasWorkspace)
	inv := independentInventory(t, db)
	expected, numberErr := Num(spec, "expected_inventory")
	if numberErr != nil || expected < 1 {
		t.Fatal("invalid expected inventory", numberErr)
	}
	if len(inv) != int(expected) {
		t.Fatal("nonempty original inventory")
	}
	for k := range inv {
		if !strings.Contains(k, ":model:") {
			t.Fatal("TOOL classified MODEL")
		}
	}
	result["original_inventory"] = inv
	destination := filepath.Join(dir, "restored")
	opt := backupOpt(t, svc, key)
	pins := []any{}
	opt.WorkspaceTarget = func(_ context.Context, d string, req []WorkspaceRestoreRequest) ([]WorkspaceRestorePin, error) {
		if !hasWorkspace || d != destination || len(req) != 1 {
			return nil, fmt.Errorf("unexpected pin request")
		}
		r := req[0]
		expected := BackupWorkspaceDestination(destination, "tool-workspace")
		if r.AuthorizedRef != "tool-workspace" || r.PrincipalID != "fixture-author" || r.Access != "READ_ONLY" || filepath.Clean(r.RealPath) != filepath.Clean(expected) {
			return nil, fmt.Errorf("pin scope")
		}
		b, er := os.ReadFile(filepath.Join(expected, "evidence.txt"))
		if er != nil || Digest(b) != Digest([]byte("workspace-file-observation-7719")) {
			return nil, fmt.Errorf("pin witness")
		}
		pin := WorkspaceRestorePin{AuthorizedRef: r.AuthorizedRef, RealPath: expected, HostPrincipalRef: "SYNTHETIC_INDEPENDENT_RESTORE"}
		pins = append(pins, Object{"request": r, "returned": pin, "sha256": Digest(b)})
		return []WorkspaceRestorePin{pin}, nil
	}
	restoreStarted := Now()
	report, e := RestoreBackup(context.Background(), archive, destination, opt)
	restoreFinished := Now()
	result["restore_report"] = report
	result["restore_pins"] = pins
	if e != nil {
		result["restore_error"] = e.Error()
		t.Fatal("public restore", e)
	}
	rp := filepath.Join(destination, "state.sqlite")
	restoredBefore, e := providerSemanticVector(rp, filepath.Join(dir, "restored-before-open.json.gz"))
	if e != nil {
		t.Fatal(e)
	}
	result["restore_delta"] = independentRestoreDelta(t, before, restoredBefore, destination, restoreStarted, restoreFinished)
	rdb, e := store.Open(rp)
	if e != nil {
		t.Fatal(e)
	}
	defer rdb.Close()
	if e = validateModelStreamBackup(rdb); e != nil {
		t.Fatal("restored stream validation", e)
	}
	restInv := independentInventory(t, rdb)
	if len(restInv) != len(inv) {
		t.Fatal("inventory membership lost")
	}
	for k := range inv {
		if _, ok := restInv[k]; !ok {
			t.Fatal("original inventory key lost")
		}
	}
	again := filepath.Join(dir, "rebackup")
	rsvc := &Service{DB: rdb, Contracts: contracts}
	var rews *independentWorkspace
	if hasWorkspace {
		bs, er := workspaceBackupBindings(rdb)
		if er != nil || len(bs) != 1 {
			t.Fatal(er)
		}
		rews = &independentWorkspace{expected: bs[0], restored: true, root: BackupWorkspaceDestination(destination, "tool-workspace"), expectedDestination: again}
		_, e = rsvc.CreateBackupWithWorkspaces(context.Background(), again, key, rews)
	} else {
		_, e = rsvc.CreateBackup(context.Background(), again, key)
	}
	if e != nil {
		t.Fatal("public rebackup", e)
	}
	reDir := filepath.Join(dir, "rebackup-proof")
	if e = os.Mkdir(reDir, 0700); e != nil {
		t.Fatal(e)
	}
	result["rebackup_chain"] = independentDecodedArchive(t, again, key, reDir, hasWorkspace)
	if _, e = rdb.Exec("PRAGMA wal_checkpoint(TRUNCATE)"); e != nil {
		t.Fatal(e)
	}
	if e = rdb.Close(); e != nil {
		t.Fatal(e)
	}
	after, e := providerSemanticVector(rp, filepath.Join(dir, "restored-closed.json.gz"))
	if e != nil {
		t.Fatal(e)
	}
	if Hash(after) != Hash(restoredBefore) {
		t.Fatal("rebackup mutated restored DB")
	}
	rb, e := os.ReadFile(rp)
	if e != nil {
		t.Fatal(e)
	}
	result["restored_closed_sha256"] = Digest(rb)
	result["restored_inventory"] = restInv
	if ws != nil {
		result["synthetic_backup_callbacks"] = ws.records
		result["synthetic_rebackup_callbacks"] = rews.records
		if ws.calls != 1 || rews.calls != 1 || len(pins) != 1 {
			t.Fatal("workspace callback count")
		}
	}
	result["public_roundtrip_proven"] = true
}
