//go:build windows

package domain

// These events are a view of the existing effect and budget journals. They do
// not dispatch tools, alter an effect outcome, reconcile money, or renew a lease.
import (
	"context"
	"database/sql"
	"encoding/base64"
	"errors"
	"os"
	"path/filepath"
	"strings"
	"unicode/utf8"
)

type runtimeSessionEventView struct {
	id, build                  string
	revision, epoch, watermark int64
	sealed                     bool
}

func runtimeProjectionID(parts ...any) string {
	return "runtime-event-" + strings.TrimPrefix(Hash(parts), "sha256:")
}

func (c *RuntimeCoordinator) effectSessionView(tx *sql.Tx, project string, run Object) (*runtimeSessionEventView, error) {
	task, err := load(tx, project, "Task", Str(run, "task_id"))
	if err != nil || task["task_type"] != "mu_turn" {
		return nil, err
	}
	// A historical RUN_STATE was produced after checking this canonical Task.
	// It remains the association after the session moves to a subsequent turn.
	rows, err := tx.Query(`SELECT DISTINCT s.id,s.core_build_id,s.revision,s.writer_epoch,s.event_watermark,s.sealed_at
		FROM client_sessions s WHERE s.project_id=? AND (s.task_id=? OR EXISTS (
		 SELECT 1 FROM outbox o WHERE o.project=s.project_id AND json_extract(o.body,'$.session_id')=s.id
		 AND json_extract(o.body,'$.run_id')=? AND json_extract(o.body,'$.kind')='RUN_STATE'
		 AND json_extract(o.body,'$.payload.run_id')=?))`, project, task["id"], run["id"], run["id"])
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var found *runtimeSessionEventView
	for rows.Next() {
		var v runtimeSessionEventView
		var sealed sql.NullString
		if err = rows.Scan(&v.id, &v.build, &v.revision, &v.epoch, &v.watermark, &sealed); err != nil {
			return nil, err
		}
		v.sealed = sealed.Valid
		if found != nil {
			return nil, Fail(409, "STATE_CONFLICT", "runtime fact has ambiguous session provenance")
		}
		found = &v
	}
	return found, rows.Err()
}

func (c *RuntimeCoordinator) appendRuntimeProjection(tx *sql.Tx, project string, run Object, view *runtimeSessionEventView, id, kind string, payload Object) error {
	var prior string
	err := tx.QueryRow("SELECT body FROM outbox WHERE project=? AND id=?", project, id).Scan(&prior)
	if err == nil {
		ev, e := DecodeEvent([]byte(prior))
		if e != nil || deref(ev.SessionID) != view.id || deref(ev.RunID) != Str(run, "id") || deref(ev.Kind) != kind {
			return Fail(409, "STATE_CONFLICT", "runtime projection identity changed")
		}
		p, e := Decode(ev.Payload)
		if e != nil || Hash(p) != Hash(payload) {
			return Fail(409, "STATE_CONFLICT", "runtime projection payload changed")
		}
		return nil
	}
	if err != sql.ErrNoRows {
		return err
	}
	if c.config.ClientSchema == nil {
		return Fail(503, "HOST_UNAVAILABLE", "typed runtime event schema unavailable")
	}
	next := view.watermark + 1
	ev := &SessionEvent{EventID: &id, SessionID: &view.id, Sequence: &next, CoreBuildID: &view.build,
		ProtocolVersion: strptr(ProtocolV2), RunID: strptr(Str(run, "id")), Kind: &kind, Payload: Bytes(payload)}
	if err = AppendSessionEvent(context.Background(), tx, c.config.ClientSchema, project, ev, view.epoch, view.revision); err != nil {
		return err
	}
	view.watermark, view.revision = next, view.revision+1
	return nil
}

func runtimeToolOutcome(intent Object) (string, string) {
	receipt, _ := intent["receipt"].(map[string]any)
	result, _ := receipt["payload"].(map[string]any)
	if intent["state"] == "UNKNOWN" {
		return "UNKNOWN", "Host has no complete tool outcome; original effect requires reconciliation"
	}
	if intent["state"] == "NOT_APPLIED" {
		return "BLOCKED", "Host refused before the side effect: " + Str(result, "reason")
	}
	if intent["state"] != "CONFIRMED" {
		return "", ""
	}
	details, _ := result["details"].(map[string]any)
	if result["isError"] == true || details["timed_out"] == true {
		return "FAILED", "Host returned a complete failed tool result"
	}
	if exit, ok := details["exit_code"]; ok && Hash(exit) != Hash(0) {
		return "FAILED", "Host tool completed with a nonzero exit code"
	}
	return "SUCCEEDED", "Host returned and reconciled the complete tool result"
}

func runtimeEvidenceBytes(value any) ([]byte, error) {
	switch v := value.(type) {
	case []byte:
		return v, nil
	case string:
		return base64.StdEncoding.DecodeString(v)
	default:
		return nil, errors.New("host raw output is not an encoded byte sequence")
	}
}

func (c *RuntimeCoordinator) projectionFact(tx *sql.Tx, project string, intent, fact Object) (Object, Object, error) {
	dispatch, err := runtimeDispatch(tx, project, Str(intent, "run_id"), intent["epoch"])
	if err != nil {
		return nil, nil, err
	}
	if fact == nil || fact["effect_key"] != intent["key"] {
		var locator string
		if err = tx.QueryRow("SELECT journal_locator FROM runtime_dispatches WHERE project=? AND run=? AND epoch=?", project, intent["run_id"], intent["epoch"]).Scan(&locator); err != nil {
			return nil, nil, err
		}
		if filepath.Base(locator) != locator || locator == "." || locator == ".." {
			return nil, nil, errors.New("runtime journal locator is not local")
		}
		path := filepath.Join(c.config.DataRoot, "runtime-dispatches", locator, "effect-"+strings.TrimPrefix(Digest([]byte(Str(intent, "key"))), "sha256:")+".json")
		actual, e := filepath.EvalSymlinks(path)
		if os.IsNotExist(e) {
			return dispatch, nil, nil
		}
		if e != nil || !strings.EqualFold(actual, path) {
			return nil, nil, errors.New("runtime projection fact reparse rejected")
		}
		info, e := os.Stat(path)
		if os.IsNotExist(e) {
			return dispatch, nil, nil
		}
		if e != nil {
			return nil, nil, e
		}
		if !info.Mode().IsRegular() || info.Size() > runtimeFactMaxBytes {
			return nil, nil, errors.New("runtime projection fact exceeds bound")
		}
		raw, e := os.ReadFile(path)
		if e != nil {
			return nil, nil, e
		}
		fact, e = Decode(raw)
		if e != nil {
			return nil, nil, e
		}
	}
	for key, want := range (Object{"project_id": project, "run_id": intent["run_id"], "effect_key": intent["key"], "epoch": intent["epoch"],
		"request_hash": intent["request_hash"], "reservation_id": intent["reservation_id"], "dispatch_key": dispatch["dispatch_key"], "manifest_hash": dispatch["manifest_hash"], "receipt": intent["receipt"]}) {
		if Hash(fact[key]) != Hash(want) {
			return nil, nil, Fail(422, "GATE_FAILED", "projection fact does not match canonical effect")
		}
	}
	if evidence := fact["host_tool_evidence"]; evidence != nil && (len(Bytes(evidence)) > 4*1024*1024 || Hash(evidence) != fact["host_tool_evidence_hash"]) {
		return nil, nil, Fail(422, "GATE_FAILED", "projection host evidence mismatch")
	}
	return dispatch, fact, nil
}

func (c *RuntimeCoordinator) toolProjectionArtifacts(tx *sql.Tx, project string, intent, fact Object) (any, any, []any, string, error) {
	refs := Empty()
	if intent["state"] != "CONFIRMED" && intent["state"] != "NOT_APPLIED" {
		return nil, nil, refs, "without-full-receipt", nil
	}
	dispatch, fact, err := c.projectionFact(tx, project, intent, fact)
	if err != nil {
		return nil, nil, nil, "", err
	}
	// The actual complete receipt is available even when raw process evidence is
	// absent. A missing raw stream is not represented as a fabricated empty log.
	a, err := c.recoverArtifact(tx, project, dispatch, Bytes(intent["receipt"]), "REPORT")
	if err != nil {
		return nil, nil, nil, "", err
	}
	refs = append(refs, Ref(a, "Artifact"))
	if fact == nil {
		return nil, nil, refs, "without-raw-evidence", nil
	}
	evidence, _ := fact["host_tool_evidence"].(map[string]any)
	if evidence == nil {
		return nil, nil, refs, "receipt-only", nil
	}
	a, err = c.recoverArtifact(tx, project, dispatch, Bytes(evidence), "REPORT")
	if err != nil {
		return nil, nil, nil, "", err
	}
	refs = append(refs, Ref(a, "Artifact"))
	sandbox, _ := evidence["sandbox_receipt"].(map[string]any)
	var stdout, stderr any
	for _, name := range []string{"stdout", "stderr"} {
		value, exists := sandbox[name+"_raw"]
		if !exists {
			continue
		}
		raw, e := runtimeEvidenceBytes(value)
		if e != nil || len(raw) > 4*1024*1024 || Digest(raw) != sandbox[name+"_hash"] || Hash(len(raw)) != Hash(sandbox[name+"_raw_bytes"]) {
			return nil, nil, nil, "", Fail(422, "CONTENT_HASH_MISMATCH", "host raw tool output does not match its witness")
		}
		a, e = c.recoverArtifact(tx, project, dispatch, raw, "LOG")
		if e != nil {
			return nil, nil, nil, "", e
		}
		if name == "stdout" {
			stdout = Ref(a, "Artifact")
		} else {
			stderr = Ref(a, "Artifact")
		}
	}
	return stdout, stderr, refs, Str(fact, "host_tool_evidence_hash"), nil
}

func (c *RuntimeCoordinator) projectSessionEffects(tx *sql.Tx, project string, run, fact Object) error {
	view, err := c.effectSessionView(tx, project, run)
	if err != nil || view == nil || view.sealed {
		return err
	}
	var dispatched int
	if err = tx.QueryRow("SELECT count(*) FROM runtime_dispatches WHERE project=? AND run=?", project, run["id"]).Scan(&dispatched); err != nil {
		return err
	}
	// This producer describes host runtime journals, not an unrelated run that
	// happens to have acquired a client mapping after executing elsewhere.
	if dispatched == 0 {
		return nil
	}
	rows, err := tx.Query("SELECT body FROM resource_effects WHERE project=? AND run=? ORDER BY rowid", project, run["id"])
	if err != nil {
		return err
	}
	intents := []Object{}
	for rows.Next() {
		var raw string
		if err = rows.Scan(&raw); err != nil {
			break
		}
		var intent Object
		intent, err = Decode([]byte(raw))
		if err != nil {
			break
		}
		intents = append(intents, intent)
	}
	if err == nil {
		err = rows.Err()
	}
	rows.Close()
	if err != nil {
		return err
	}
	for _, intent := range intents {
		request, _ := intent["payload"].(map[string]any)
		if request["capability"] != "TOOL" {
			continue
		}
		if intent["project_id"] != project || intent["run_id"] != run["id"] || intent["task_id"] != run["task_id"] {
			return Fail(422, "GATE_FAILED", "tool event source identity mismatch")
		}
		payload, _ := request["payload"].(map[string]any)
		callID := runtimeProjectionID("host-tool-call-v1", project, run["id"], intent["epoch"], intent["key"])
		if intent["state"] == "STARTED" {
			dispatch, e := runtimeDispatch(tx, project, Str(run, "id"), intent["epoch"])
			if e != nil {
				return e
			}
			input, e := c.recoverArtifact(tx, project, dispatch, Bytes(payload), "REPORT")
			if e != nil {
				return e
			}
			summary := Str(payload, "name") + " logical tool call admitted; physical execution may await permission"
			started := Object{"tool_call_id": callID, "parent_tool_call_id": nil, "tool_name": payload["name"], "input_summary": summary, "input_artifact_ref": Ref(input, "Artifact")}
			id := runtimeProjectionID("tool-started-v1", view.id, run["id"], intent["key"], intent["epoch"])
			if err = c.appendRuntimeProjection(tx, project, run, view, id, "TOOL_STARTED", started); err != nil {
				return err
			}
		}
		outcome, summary := runtimeToolOutcome(intent)
		if outcome == "" {
			continue
		}
		stdout, stderr, refs, evidenceKey, e := c.toolProjectionArtifacts(tx, project, intent, fact)
		if e != nil {
			return e
		}
		result := Object{"tool_call_id": callID, "outcome": outcome, "summary": summary, "stdout_artifact_ref": stdout, "stderr_artifact_ref": stderr, "result_artifact_refs": refs}
		if !utf8.ValidString(summary) {
			return errors.New("tool summary is not UTF-8")
		}
		id := runtimeProjectionID("tool-result-v1", view.id, run["id"], intent["key"], intent["sequence"], Hash(intent["receipt"]), evidenceKey)
		if err = c.appendRuntimeProjection(tx, project, run, view, id, "TOOL_RESULT", result); err != nil {
			return err
		}
	}
	rows, err = tx.Query("SELECT body FROM domain_objects WHERE project=? AND kind='BudgetLedgerEntry' AND json_extract(body,'$.run_id')=? ORDER BY rowid", project, run["id"])
	if err != nil {
		return err
	}
	entries := []Object{}
	for rows.Next() {
		var raw string
		if err = rows.Scan(&raw); err != nil {
			break
		}
		var entry Object
		entry, err = Decode([]byte(raw))
		if err != nil {
			break
		}
		entries = append(entries, entry)
	}
	if err == nil {
		err = rows.Err()
	}
	rows.Close()
	if err != nil {
		return err
	}
	for _, entry := range entries {
		known := entry["cost_basis"] == "ACTUAL" && (entry["operation"] == "COMMIT" || entry["operation"] == "RECONCILE") && entry["money"] != nil
		var money any
		if known {
			money = entry["money"]
		}
		usage := Object{"ledger_entry_id": entry["id"], "provider_usage_id": nil, "input_tokens": nil, "output_tokens": nil, "money": money, "cost_known": known}
		id := runtimeProjectionID("usage-v1", view.id, run["id"], entry["id"])
		if err = c.appendRuntimeProjection(tx, project, run, view, id, "USAGE", usage); err != nil {
			return err
		}
	}
	return nil
}

// At most 128 historical runs with unprojected immutable ledger entries are
// repaired per scan. Fully projected and sealed sessions do not starve others.
func (c *RuntimeCoordinator) projectHistoricalSessionUsage(tx *sql.Tx) error {
	rows, err := tx.Query(`SELECT DISTINCT r.project,r.body FROM domain_objects b
	 JOIN domain_objects r ON r.project=b.project AND r.kind='Run' AND r.id=json_extract(b.body,'$.run_id')
	 JOIN outbox binding ON binding.project=r.project AND json_extract(binding.body,'$.run_id')=r.id AND json_extract(binding.body,'$.kind')='RUN_STATE'
	 JOIN client_sessions s ON s.project_id=binding.project AND s.id=json_extract(binding.body,'$.session_id') AND s.sealed_at IS NULL
	 WHERE b.kind='BudgetLedgerEntry' AND NOT EXISTS (SELECT 1 FROM outbox o WHERE o.project=b.project
	 AND json_extract(o.body,'$.session_id')=s.id AND json_extract(o.body,'$.kind')='USAGE' AND json_extract(o.body,'$.payload.ledger_entry_id')=b.id)
	 ORDER BY r.rowid LIMIT 128`)
	if err != nil {
		return err
	}
	type source struct {
		project string
		run     Object
	}
	sources := []source{}
	for rows.Next() {
		var project, raw string
		if err = rows.Scan(&project, &raw); err != nil {
			break
		}
		run, e := Decode([]byte(raw))
		if e != nil {
			err = e
			break
		}
		sources = append(sources, source{project, run})
	}
	if err == nil {
		err = rows.Err()
	}
	rows.Close()
	if err != nil {
		return err
	}
	for _, src := range sources {
		if err = c.projectSessionEffects(tx, src.project, src.run, nil); err != nil {
			return err
		}
	}
	return nil
}
