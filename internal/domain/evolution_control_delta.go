//go:build windows

package domain

import (
	"database/sql"
	"fmt"
	"researchos.local/research-os/evaluation/evolution"
	"sort"
	"strings"
)

func controlRowSetHash(rows []Object) string {
	v := []string{}
	for _, r := range rows {
		v = append(v, Hash(r))
	}
	sort.Strings(v)
	return Hash(v)
}
func controlSchemaHash(q controlQuery) (string, error) {
	rows, err := q.Query("SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name")
	if err != nil {
		return "", err
	}
	defer rows.Close()
	all := []any{}
	for rows.Next() {
		var typ, name, table string
		var statement sql.NullString
		if err = rows.Scan(&typ, &name, &table, &statement); err != nil {
			return "", err
		}
		all = append(all, []any{typ, name, table, statement.String})
	}
	return Hash(all), rows.Err()
}
func controlRowKeys(q controlQuery, table string) ([]string, error) {
	if table == "sqlite_sequence" {
		return []string{"name"}, nil
	}
	rows, err := q.Query(`PRAGMA table_info("` + strings.ReplaceAll(table, `"`, `""`) + `")`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	keys := map[int]string{}
	for rows.Next() {
		var cid, required, pk int
		var name, typ string
		var d any
		if err = rows.Scan(&cid, &name, &typ, &required, &d, &pk); err != nil {
			return nil, err
		}
		if pk > 0 {
			keys[pk] = name
		}
	}
	if err = rows.Err(); err != nil {
		return nil, err
	}
	out := []string{}
	for i := 1; i <= len(keys); i++ {
		out = append(out, keys[i])
	}
	return out, nil
}
func controlRowKey(r Object, keys []string) string {
	if len(keys) == 0 {
		return Hash(r)
	}
	v := []any{}
	for _, k := range keys {
		v = append(v, r[k])
	}
	return Hash(v)
}
func controlRowIndex(rows []Object, keys []string) (map[string]Object, error) {
	out := map[string]Object{}
	for _, r := range rows {
		k := controlRowKey(r, keys)
		if out[k] != nil {
			return nil, fmt.Errorf("CONTROL_DELTA_DUPLICATE_KEY")
		}
		out[k] = r
	}
	return out, nil
}
func controlRowDifferences(q controlQuery, before, after upgradeData) ([]evolution.ControlGenerationDelta, error) {
	if len(before) != len(after) {
		return nil, fmt.Errorf("CONTROL_DELTA_TABLE_SET")
	}
	out := []evolution.ControlGenerationDelta{}
	for table, rows := range before {
		current, ok := after[table]
		if !ok {
			return nil, fmt.Errorf("CONTROL_DELTA_TABLE_REMOVED")
		}
		keys, err := controlRowKeys(q, table)
		if err != nil {
			return nil, err
		}
		old, err := controlRowIndex(rows, keys)
		if err != nil {
			return nil, err
		}
		next, err := controlRowIndex(current, keys)
		if err != nil {
			return nil, err
		}
		all := map[string]bool{}
		for k := range old {
			all[k] = true
		}
		for k := range next {
			all[k] = true
		}
		for k := range all {
			b, a := old[k], next[k]
			if Hash(b) == Hash(a) {
				continue
			}
			d := evolution.ControlGenerationDelta{Table: table, KeyHash: k}
			if b != nil {
				d.BeforeHash = Hash(b)
			}
			if a != nil {
				d.AfterHash = Hash(a)
			}
			out = append(out, d)
		}
	}
	sort.Slice(out, func(i, j int) bool {
		if out[i].Table != out[j].Table {
			return out[i].Table < out[j].Table
		}
		return out[i].KeyHash < out[j].KeyHash
	})
	return out, nil
}

type controlDeltaIndex struct{ before, after map[string]Object }

func controlIndexChanges(q controlQuery, before, after upgradeData, delta []evolution.ControlGenerationDelta) (map[string]controlDeltaIndex, error) {
	result := map[string]controlDeltaIndex{}
	for _, d := range delta {
		if _, ok := result[d.Table]; ok {
			continue
		}
		keys, err := controlRowKeys(q, d.Table)
		if err != nil {
			return nil, err
		}
		b, err := controlRowIndex(before[d.Table], keys)
		if err != nil {
			return nil, err
		}
		a, err := controlRowIndex(after[d.Table], keys)
		if err != nil {
			return nil, err
		}
		result[d.Table] = controlDeltaIndex{b, a}
	}
	return result, nil
}

func controlBody(r Object) (Object, error) { return Decode([]byte(Str(r, "body"))) }
func controlSameExcept(before, after Object, fields string) bool {
	b, a := copyObject(before), copyObject(after)
	for _, k := range strings.Fields(fields) {
		delete(b, k)
		delete(a, k)
	}
	return Hash(b) == Hash(a)
}
func (n *controlCurrentNames) actor(id string) bool {
	return id == n.Verifier || id == n.Executor || id == n.Author || id == n.Release
}
func (n *controlCurrentNames) named(kind, id string) bool {
	switch kind {
	case "Task":
		return id == n.Task
	case "Run":
		return id == n.Run
	case "Experiment":
		return id == n.Experiment
	case "SystemCandidate":
		return id == n.Candidate
	case "ProjectState":
		return id == n.State
	case "NoProgressRecord":
		return id == n.Retention
	}
	return false
}

// Every original row is preserved unless a named lifecycle field is listed
// here. New rows must have an exact relationship to this single frozen Run.
func (a *currentControlAuthority) validateCurrentRows(tx *sql.Tx) ([]evolution.ControlGenerationDelta, error) {
	n := a.frozen
	if n == nil {
		return nil, fmt.Errorf("CONTROL_CURRENT_G0_REQUIRED")
	}
	if err := a.currentOwner(tx); err != nil {
		return nil, err
	}
	if err := a.independentVerifier(tx, n.Verifier, n); err != nil {
		return nil, err
	}
	return a.validateNamedDelta(tx)
}

// This helper only checks rows; it never establishes host or verifier authority.
// Admission always uses validateCurrentRows above.
func (a *currentControlAuthority) validateNamedDelta(tx *sql.Tx) ([]evolution.ControlGenerationDelta, error) {
	n := a.frozen
	schema, err := controlSchemaHash(tx)
	if err != nil || schema != n.Schema {
		return nil, fmt.Errorf("CONTROL_CURRENT_SCHEMA_CHANGED")
	}
	after, err := controlCurrentRows(tx)
	if err != nil {
		return nil, err
	}
	delta, err := controlRowDifferences(tx, n.Rows, after)
	if err != nil {
		return nil, err
	}
	oldObjects := map[string]Object{}
	objects := map[string]Object{}
	newObjects := map[string]Object{}
	versions := map[string]Object{}
	for _, row := range after["domain_versions"] {
		versions[controlVersionKey(row)] = row
	}
	for _, r := range n.Rows["domain_objects"] {
		oldObjects[Hash([]any{r["project"], r["kind"], r["id"]})] = r
	}
	for _, r := range after["domain_objects"] {
		key := Hash([]any{r["project"], r["kind"], r["id"]})
		objects[key] = r
		if oldObjects[key] == nil {
			newObjects[Str(r, "kind")+":"+Str(r, "id")] = r
		}
	}
	getNew := func(kind, id string) Object { return newObjects[kind+":"+id] }
	artifactRoles := map[string]string{}
	artifactHashes := map[string]string{}
	bindArtifact := func(ref Object, role string) {
		if ref["entity_type"] == "Artifact" {
			id := Str(ref, "id")
			artifactRoles[id] = role
			artifactHashes[id] = Str(ref, "content_hash")
		}
	}
	for _, row := range after["evolution_journal"] {
		if row["project"] == n.Project && row["candidate"] == n.Candidate && row["event"] == "HOLDOUT_EVALUATED" {
			body, e := controlBody(row)
			if e == nil && body["plan_hash"] == n.Plan && body["verifier_id"] == n.Verifier {
				ref, _ := body["proof_ref"].(map[string]any)
				bindArtifact(ref, "PRIVATE_PROOF")
			}
		}
	}
	for _, row := range after["evolution_executions"] {
		if row["project"] == n.Project && row["candidate"] == n.Candidate && row["run"] == n.Run && row["state"] == "RECORDED" {
			body, e := controlBody(row)
			if e == nil && body["receipt_hash"] == Receipt(body) {
				ref, _ := body["artifact_ref"].(map[string]any)
				bindArtifact(ref, "RUN_OBSERVATION")
			}
		}
	}
	for _, row := range newObjects {
		if row["kind"] == "AcceptanceReceipt" {
			b, e := controlBody(row)
			subject, _ := b["subject_ref"].(map[string]any)
			if e == nil && subject["id"] == n.Task && b["run_id"] == n.Run && b["verifier_principal_id"] == n.Verifier && b["receipt_hash"] == Receipt(b) {
				for _, v := range Arr(b, "checks") {
					check, _ := v.(map[string]any)
					for _, ev := range Arr(check, "evidence_refs") {
						ref, _ := ev.(map[string]any)
						bindArtifact(ref, "ACCEPTANCE_REPORT")
					}
				}
			}
		}
	}
	artifactAllowed := func(id string) bool { return getNew("Artifact", id) != nil && artifactRoles[id] != "" }
	validNewObject := func(kind string, b Object) bool {
		if b["project_id"] != n.Project {
			return false
		}
		rev, _ := Num(b, "revision")
		if rev != 1 {
			return false
		}
		switch kind {
		case "Artifact":
			if b["measurement_mode"] != "FIXTURE" || b["validity"] != "CURRENT" || !artifactAllowed(Str(b, "id")) || b["content_hash"] != artifactHashes[Str(b, "id")] {
				return false
			}
			if b["access_class"] == "VERIFIER_ONLY" {
				return artifactRoles[Str(b, "id")] == "PRIVATE_PROOF" && b["kind"] == "REPORT" && b["produced_by"] == n.Verifier && b["run_id"] == nil
			}
			if b["access_class"] != "PROJECT" {
				return false
			}
			return b["kind"] == "REPORT" && (artifactRoles[Str(b, "id")] == "RUN_OBSERVATION" && b["produced_by"] == n.Executor && b["run_id"] == n.Run || artifactRoles[Str(b, "id")] == "ACCEPTANCE_REPORT" && b["produced_by"] == n.Verifier && b["run_id"] == nil)
		case "AcceptanceReceipt":
			subject, _ := b["subject_ref"].(map[string]any)
			return subject["entity_type"] == "Task" && subject["id"] == n.Task && b["run_id"] == n.Run && b["verifier_principal_id"] == n.Verifier && b["receipt_hash"] == Receipt(b) && b["verdict"] == "PASS" && b["measurement_mode"] == "FIXTURE"
		case "ImpactLink":
			target, _ := b["from_ref"].(map[string]any)
			return target["entity_type"] == "Artifact" && artifactAllowed(Str(target, "id")) && b["relation"] == "DERIVED_FROM" && b["status"] == "ACTIVE"
		case "EventEnvelope":
			ref, _ := b["aggregate_ref"].(map[string]any)
			kind, id := Str(ref, "entity_type"), Str(ref, "id")
			return b["receipt_hash"] == Receipt(b) && n.actor(Str(b, "actor_id")) && (n.named(kind, id) || getNew(kind, id) != nil) && kind != "EventEnvelope" && b["causation_id"] == nil && b["event_data_artifact_ref"] == nil
		}
		return false
	}
	validBody := func(kind, id string, b Object) bool {
		key := Hash([]any{n.Project, kind, id})
		old := oldObjects[key]
		if old == nil {
			return validNewObject(kind, b)
		}
		if !n.named(kind, id) {
			return false
		}
		base, e := controlBody(old)
		if e != nil {
			return false
		}
		fields := "revision updated_at"
		switch kind {
		case "Run":
			fields += " status heartbeat_at lease_expires_at execution_report exit_code result_artifact_ids checkpoint_artifact_id runtime_settled_at children_stopped queue_empty ended_at"
			if b["status"] != "RUNNING" && b["status"] != "SETTLED" {
				return false
			}
		case "Task":
			fields += " status output_artifact_ids acceptance_id"
			if b["status"] != base["status"] && b["status"] != "EXECUTION_REPORTED" && b["status"] != "ACCEPTED" {
				return false
			}
		case "Experiment":
			fields += " status results outcome acceptance_id"
			if b["status"] != "RUNNING" && b["status"] != "COMPLETED" {
				return false
			}
		case "SystemCandidate":
			fields += " status regression_acceptance_id freeze_reason"
			if b["status"] != "EVALUATING" && b["status"] != "REJECTED" {
				return false
			}
		case "NoProgressRecord":
			fields += " best_accepted_artifact_ref last_effective_progress_at"
		case "ProjectState":
			fields += " event_sequence"
		default:
			return false
		}
		return controlSameExcept(base, b, fields)
	}
	// Validate the full new entity first; references cannot introduce extra scope.
	for _, r := range newObjects {
		b, e := controlBody(r)
		if e != nil || !validNewObject(Str(r, "kind"), b) {
			return nil, fmt.Errorf("CONTROL_CURRENT_NEW_OBJECT_REJECTED:%s", Str(r, "kind"))
		}
	}
	indexes, err := controlIndexChanges(tx, n.Rows, after, delta)
	if err != nil {
		return nil, err
	}
	for i := range delta {
		d := &delta[i]
		index := indexes[d.Table]
		b, r := index.before[d.KeyHash], index.after[d.KeyHash]
		if r == nil {
			return nil, fmt.Errorf("CONTROL_CURRENT_ROW_DELETED:%s", d.Table)
		}
		allowed := false
		switch d.Table {
		case "domain_objects", "domain_versions":
			body, e := controlBody(r)
			allowed = e == nil && r["project"] == n.Project && body["id"] == r["id"] && Hash(body["revision"]) == Hash(r["revision"]) && validBody(Str(r, "kind"), Str(r, "id"), body)
			if d.Table == "domain_versions" && b != nil {
				allowed = false
			}
			if allowed {
				allowed = a.s.Contracts.Validate(Str(r, "kind"), body) == nil
			}
		case "domain_refs":
			key := Hash([]any{r["project"], r["kind"], r["id"]})
			obj := objects[key]
			allowed = b == nil && r["project"] == n.Project && obj != nil && (n.named(Str(r, "kind"), Str(r, "id")) || getNew(Str(r, "kind"), Str(r, "id")) != nil)
			allowed = allowed && controlReferenceRowBound(r, versions, oldObjects)
			if allowed {
				var count int
				e := tx.QueryRow("SELECT count(*) FROM domain_versions WHERE project=? AND kind=? AND id=? AND revision=?", r["target_project"], r["target_kind"], r["target_id"], r["target_revision"]).Scan(&count)
				allowed = e == nil && count == 1
			}
		case "uploaded_content":
			if b == nil && r["project"] == n.Project && n.actor(Str(r, "principal")) && r["sealed"] == int64(1) {
				for _, ar := range newObjects {
					if ar["kind"] != "Artifact" {
						continue
					}
					ab, _ := controlBody(ar)
					raw, ok := r["bytes"].([]byte)
					if ok && ab["storage_key"] == r["storage_key"] && ab["content_hash"] == Digest(raw) && r["content_hash"] == Digest(raw) && ab["produced_by"] == r["principal"] {
						allowed = true
					}
				}
			}
		case "runtime_uploads", "artifact_uses", "artifact_use_proofs", "runtime_observations":
			allowed = b == nil && r["project"] == n.Project && r["run"] == n.Run && r["epoch"] == n.Epoch
			if d.Table == "artifact_uses" {
				body, e := controlBody(r)
				allowed = allowed && e == nil && body["receipt_hash"] == Receipt(body) && r["principal"] == n.Executor && artifactAllowed(Str(r, "artifact"))
			}
			if d.Table == "artifact_use_proofs" {
				allowed = false
			} // stale canonical reuse is outside this profile
			if d.Table == "runtime_observations" {
				body, e := controlBody(r)
				allowed = allowed && e == nil && r["receipt_hash"] == Hash(body) && body["control_current_session"] == a.id && body["control_g0_hash"] == a.g0.Generation
			}
		case "outbox":
			event := getNew("EventEnvelope", Str(r, "id"))
			allowed = b == nil && r["project"] == n.Project && r["acknowledged"] == int64(0) && event != nil && event["body"] == r["body"]
		case "event_state_snapshots":
			event := getNew("EventEnvelope", Str(r, "event_id"))
			body, e := controlBody(r)
			allowed = b == nil && event != nil && r["project"] == n.Project && e == nil && validBody("ProjectState", n.State, body) && Hash(body["revision"]) == Hash(r["revision"])
		case "evolution_executions":
			body, e := controlBody(r)
			allowed = b == nil && e == nil && r["project"] == n.Project && r["candidate"] == n.Candidate && r["phase"] == "REGRESSION" && r["run"] == n.Run && r["epoch"] == n.Epoch && (r["state"] == "RESERVED" || r["state"] == "RECORDED") && body["plan_hash"] == n.Plan
			if allowed && r["state"] == "RECORDED" {
				allowed = body["receipt_hash"] == Receipt(body) && r["receipt_hash"] == body["receipt_hash"]
			}
		case "evolution_journal":
			body, e := controlBody(r)
			event := Str(r, "event")
			allowed = b == nil && e == nil && r["project"] == n.Project && r["candidate"] == n.Candidate && (r["run"] == "" || r["run"] == n.Run) && (event == "HOLDOUT_EVALUATED" || event == "EXECUTION_FINAL" || event == "REJECTED") && r["receipt_hash"] == Hash(body)
			if event == controlCurrentReserved || event == controlCurrentRecorded {
				count := 0
				for _, journal := range after["evolution_journal"] {
					if journal["project"] == n.Project && journal["candidate"] == n.Candidate && journal["event"] == event {
						count++
					}
				}
				allowed = b == nil && e == nil && count == 1 && r["project"] == n.Project && r["candidate"] == n.Candidate && r["run"] == n.Run && r["receipt_hash"] == Hash(body) && a.reservationJournalBound(body, event)
			}
		case "sqlite_sequence":
			var max int64
			e := tx.QueryRow("SELECT coalesce(max(sequence),0) FROM evolution_journal").Scan(&max)
			allowed = r["name"] == "evolution_journal" && r["seq"] == max && e == nil
		case "idempotency":
			ops := map[string]bool{"heartbeatRun": true, "reportRun": true, "recordAcceptance": true, "recordExperimentResult": true, "actOnSystemCandidate": true}
			allowed = b == nil && r["project"] == n.Project && n.actor(Str(r, "principal")) && ops[Str(r, "operation")]
		}
		if !allowed {
			return nil, fmt.Errorf("CONTROL_CURRENT_DELTA_REJECTED:%s:%s", d.Table, d.KeyHash)
		}
		d.Reason = "NAMED_RUN_AND_INDEPENDENT_ACCEPTANCE_METADATA"
	}
	if err = controlValidateVersionEvents(n, after); err != nil {
		return nil, err
	}
	return delta, nil
}
