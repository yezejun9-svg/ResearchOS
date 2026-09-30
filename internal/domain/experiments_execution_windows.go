//go:build windows

package domain

import (
	"context"
	"database/sql"
	"fmt"
	"os"
	"path/filepath"
	"researchos.local/research-os/adapters/evaluation"
	sandbox "researchos.local/research-os/ops/experiment_sandbox"
	"time"
)

// ExecuteExperimentPair is a worker-side, credential/lease-bound invocation. It
// runs only the frozen native executable and artifacts; it cannot import caller
// supplied observations. Reservation and immutable receipts prevent replay.
func (s *Service) ExecuteExperimentPair(ctx context.Context, token, project, id, runID string, lease Object) (Object, error) {
	tx, e := s.DB.BeginTx(ctx, nil)
	if e != nil {
		return nil, e
	}
	defer tx.Rollback()
	p, e := authenticate(tx, token)
	if e != nil {
		return nil, e
	}
	r, e := currentRun(tx, p, project, runID)
	if e != nil {
		return nil, e
	}
	if e = runtimeLease(tx, p, project, r, lease); e != nil {
		return nil, e
	}
	if r["status"] != "RUNNING" {
		return nil, Fail(409, "STATE_CONFLICT", "heartbeat current run before native execution")
	}
	x, e := load(tx, project, "Experiment", id)
	if e != nil {
		return nil, e
	}
	if x["status"] != "RUNNING" {
		return nil, Fail(409, "STATE_CONFLICT", "experiment must begin first")
	}
	if e = s.experimentCurrent(tx, project, x); e != nil {
		return nil, e
	}
	var started string
	if e = tx.QueryRow("SELECT started_at FROM experiment_runs WHERE project=? AND experiment=? AND run=? AND preregistration_hash=?", project, id, runID, x["preregistration_hash"]).Scan(&started); e != nil {
		return nil, Fail(422, "GATE_FAILED", "run not bound to frozen experiment")
	}
	if !nativeExperiment(x) {
		return nil, Fail(422, "GATE_FAILED", "native invocation must be frozen in acceptance contract")
	}
	if x["measurement_mode"] != "FIXTURE" {
		return nil, Fail(503, "RESOURCE_UNAVAILABLE", "W05 live runtime qualification is unavailable")
	}
	if len(Arr(x, "baseline_refs")) != 1 {
		return nil, Fail(422, "GATE_FAILED", "native paired runner needs exactly one baseline")
	}
	loadBytes := func(ref Object) (Object, []byte, error) {
		if ref["entity_type"] != "Artifact" {
			return nil, nil, Fail(422, "GATE_FAILED", "sealed input artifact required")
		}
		a, e := version(tx, project, ref)
		if e != nil {
			return nil, nil, e
		}
		if a["access_class"] != "PROJECT" {
			return nil, nil, Fail(403, "FORBIDDEN", "holdout unavailable")
		}
		var raw []byte
		e = tx.QueryRow("SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1", project, a["storage_key"]).Scan(&raw)
		if e != nil {
			return nil, nil, e
		}
		if Digest(raw) != a["content_hash"] {
			return nil, nil, Fail(422, "CONTENT_HASH_MISMATCH", "input bytes changed")
		}
		return a, raw, nil
	}
	candidate, candidateBytes, e := loadBytes(x["candidate_ref"].(map[string]any))
	if e != nil {
		return nil, e
	}
	baseline, baselineBytes, e := loadBytes(Arr(x, "baseline_refs")[0].(map[string]any))
	if e != nil {
		return nil, e
	}
	var dataset, executable Object
	var datasetBytes, executableBytes []byte
	for _, v := range Arr(x, "input_refs") {
		a, raw, e := loadBytes(v.(map[string]any))
		if e != nil {
			return nil, e
		}
		switch a["kind"] {
		case "DATASET":
			if dataset != nil {
				return nil, Fail(422, "GATE_FAILED", "one dataset required")
			}
			dataset, datasetBytes = a, raw
		case "CODE":
			if executable != nil {
				return nil, Fail(422, "GATE_FAILED", "one worker binary required")
			}
			executable, executableBytes = a, raw
		default:
			return nil, Fail(422, "GATE_FAILED", "native input must be DATASET or CODE")
		}
	}
	if dataset == nil || executable == nil {
		return nil, Fail(422, "GATE_FAILED", "frozen dataset and executable required")
	}
	var registeredTool int
	if e = tx.QueryRow("SELECT count(*) FROM evaluation_native_tools WHERE project=? AND content_hash=?", project, executable["content_hash"]).Scan(&registeredTool); e != nil || registeredTool != 1 {
		return nil, Fail(503, "RESOURCE_UNAVAILABLE", "native binary is not administratively registered")
	}
	ids, e := experimentCaseIDs(x)
	if e != nil {
		return nil, e
	}
	expected := []string{}
	for _, v := range ids {
		expected = append(expected, v.(string))
	}
	startedAt, e := time.Parse(time.RFC3339Nano, started)
	if e != nil {
		return nil, e
	}
	wall, _ := Num(x["stop_policy"].(map[string]any), "wall_time_seconds")
	deadline := startedAt.Add(time.Duration(wall) * time.Second)
	if !time.Now().Before(deadline) {
		return nil, Fail(422, "GATE_FAILED", "experiment wall time exhausted")
	}
	snapshot := Object{"experiment_id": id, "project_id": project, "run_id": runID, "lease_epoch": r["lease_epoch"], "preregistration_hash": x["preregistration_hash"], "candidate_ref": x["candidate_ref"], "baseline_refs": x["baseline_refs"], "input_refs": x["input_refs"], "reserved_at": Now(), "scope": "DEVELOPMENT_ONLY_NATIVE_WINDOWS"}
	if _, e = tx.Exec("INSERT INTO experiment_executions(project,experiment,run,epoch,state,body) VALUES(?,?,?,?,'RESERVED',?)", project, id, runID, r["lease_epoch"], string(Bytes(snapshot))); e != nil {
		return nil, Fail(409, "STATE_CONFLICT", "experiment invocation already reserved; reconcile instead of repeating")
	}
	if e = tx.Commit(); e != nil {
		return nil, e
	}
	// Every exit after reservation writes FAILED or a complete immutable receipt.
	record := Merge(snapshot, Object{"state": "FAILED", "reports": Empty(), "sandbox_receipts": Empty(), "raw_exports": Empty(), "raw_hashes": Empty(), "artifact_ids": Empty(), "error": nil, "observation": nil})
	work, e := os.MkdirTemp("", "researchos-native-pair-")
	if e != nil {
		return nil, s.finishExperimentExecution(ctx, token, project, id, runID, r, record, e)
	}
	defer os.RemoveAll(work)
	input := filepath.Join(work, "input")
	if e = os.Mkdir(input, 0700); e != nil {
		return nil, s.finishExperimentExecution(ctx, token, project, id, runID, r, record, e)
	}
	exe := filepath.Join(input, "native.exe")
	if e = os.WriteFile(exe, executableBytes, 0700); e != nil {
		return nil, s.finishExperimentExecution(ctx, token, project, id, runID, r, record, e)
	}
	dataPath := filepath.Join(input, "dataset.json")
	if e = os.WriteFile(dataPath, datasetBytes, 0600); e != nil {
		return nil, s.finishExperimentExecution(ctx, token, project, id, runID, r, record, e)
	}
	runCtx, cancel := context.WithDeadline(ctx, deadline)
	defer cancel()
	watchDone := make(chan struct{})
	defer close(watchDone)
	go func() {
		ticker := time.NewTicker(25 * time.Millisecond)
		defer ticker.Stop()
		for {
			select {
			case <-watchDone:
				return
			case <-runCtx.Done():
				return
			case <-ticker.C:
				var status, expires string
				var epoch int64
				e := s.DB.QueryRow("SELECT json_extract(body,'$.status'),json_extract(body,'$.lease_epoch'),json_extract(body,'$.lease_expires_at') FROM domain_objects WHERE project=? AND kind='Run' AND id=?", project, runID).Scan(&status, &epoch, &expires)
				want, _ := Num(r, "lease_epoch")
				leaseEnd, te := time.Parse(time.RFC3339Nano, expires)
				if e != nil || te != nil || !time.Now().Before(leaseEnd) || epoch != want || status != "RUNNING" {
					cancel()
					return
				}
			}
		}
	}()
	scores := [][]any{}
	m := evaluation.Manifest{ProjectID: project, ExperimentID: id, RunID: runID, Engine: Object{"name": "NATIVE", "version": "1", "config_hash": Hash(x["acceptance_contract"])}, DatasetHash: Str(dataset, "content_hash"), CandidateHash: Str(candidate, "content_hash"), BaselineHash: Str(baseline, "content_hash"), RubricHash: Hash(x["acceptance_contract"]), Expected: expected}
	for i, program := range [][]byte{baselineBytes, candidateBytes} {
		programPath := filepath.Join(input, "program.json")
		if e = os.WriteFile(programPath, program, 0600); e != nil {
			return nil, s.finishExperimentExecution(ctx, token, project, id, runID, r, record, e)
		}
		output := filepath.Join(work, fmt.Sprintf("output-%d", i))
		if e = os.Mkdir(output, 0700); e != nil {
			return nil, s.finishExperimentExecution(ctx, token, project, id, runID, r, record, e)
		}
		remaining := time.Until(deadline)
		if remaining > 5*time.Minute {
			remaining = 5 * time.Minute
		}
		receipt, err := sandbox.Run(runCtx, sandbox.Command{Executable: exe, Args: []string{dataPath, programPath}, InputDirectory: input, OutputDirectory: output, Timeout: remaining})
		record["sandbox_receipts"] = append(Arr(record, "sandbox_receipts"), receipt)
		record["raw_exports"] = append(Arr(record, "raw_exports"), string(receipt.Stdout))
		record["raw_hashes"] = append(Arr(record, "raw_hashes"), Digest(receipt.Stdout))
		if err != nil || receipt.ExitCode != 0 || !receipt.Stopped || receipt.TimedOut {
			if err == nil {
				err = fmt.Errorf("native runtime exit=%d stopped=%v timeout=%v", receipt.ExitCode, receipt.Stopped, receipt.TimedOut)
			}
			return nil, s.finishExperimentExecution(ctx, token, project, id, runID, r, record, err)
		}
		durationStart, _ := time.Parse(time.RFC3339Nano, receipt.Started)
		durationEnd, _ := time.Parse(time.RFC3339Nano, receipt.Finished)
		report, err := evaluation.Normalize(m, m, receipt.Stdout, Digest(receipt.Stdout), &receipt.ExitCode, durationEnd.Sub(durationStart).Milliseconds())
		if err == nil {
			err = evaluation.Validate(m, report, receipt.Stdout, Digest(receipt.Stdout))
		}
		if err != nil {
			return nil, s.finishExperimentExecution(ctx, token, project, id, runID, r, record, err)
		}
		record["reports"] = append(Arr(record, "reports"), report)
		values := Empty()
		for _, row := range report["results"].([]evaluation.Result) {
			var value any
			switch row.Verdict {
			case "PASS":
				value = "1"
			case "FAIL":
				value = "0"
			}
			values = append(values, value)
		}
		scores = append(scores, values)
	}
	observations := Empty()
	for _, v := range Arr(x, "metrics") {
		metric := v.(map[string]any)
		if metric["metric_id"] != "accuracy" {
			return nil, s.finishExperimentExecution(ctx, token, project, id, runID, r, record, fmt.Errorf("native runner supports only accuracy metric"))
		}
		observations = append(observations, Object{"metric_id": metric["metric_id"], "case_ids": ids, "baseline": scores[0], "candidate": scores[1]})
	}
	observation := Object{"experiment_id": id, "preregistration_hash": x["preregistration_hash"], "observations": observations}
	results, outcome, e := recomputeExperiment(x, observation)
	if e != nil {
		return nil, s.finishExperimentExecution(ctx, token, project, id, runID, r, record, e)
	}
	observation["results"], observation["outcome"] = results, outcome
	record["manifest"] = m
	record["observation"] = observation
	record["state"] = "RECORDED"
	if e = s.finishExperimentExecution(ctx, token, project, id, runID, r, record, nil); e != nil {
		return nil, e
	}
	return record, nil
}
func (s *Service) finishExperimentExecution(ctx context.Context, token, project, id, run string, r, record Object, cause error) error {
	// Persist failure even when the execution context has been cancelled.
	tx, e := s.DB.BeginTx(context.WithoutCancel(ctx), nil)
	if e != nil {
		return e
	}
	defer tx.Rollback()
	record["finished_at"] = Now()
	if cause != nil {
		record["state"] = "FAILED"
		record["error"] = cause.Error()
	}
	current, e := load(tx, project, "Run", run)
	if e != nil {
		return e
	}
	if current["status"] != "RUNNING" || Hash(current["lease_epoch"]) != Hash(r["lease_epoch"]) {
		record["state"] = "FAILED"
		record["error"] = "current run state or epoch changed"
		cause = Fail(409, "STATE_CONFLICT", "native result no longer belongs to current run")
	}

	if record["state"] == "RECORDED" {
		principal, authError := authenticate(tx, token)
		if authError == nil {
			authError = validExecutorRun(tx, principal, project, current)
		}
		if authError == nil {
			_, authError = tx.Exec("SAVEPOINT evaluation_artifacts")
		}
		if authError == nil {
			authError = s.sealExperimentOutputs(tx, principal, project, current, record)
			if authError != nil {
				tx.Exec("ROLLBACK TO evaluation_artifacts")
			}
			tx.Exec("RELEASE evaluation_artifacts")
		}
		if authError != nil {
			record["state"] = "FAILED"
			record["error"] = authError.Error()
			record["artifact_ids"] = Empty()
			cause = authError
		}
	}
	record["receipt_hash"] = Receipt(record)
	if _, e = tx.Exec("UPDATE experiment_executions SET state=?,body=?,receipt_hash=? WHERE project=? AND experiment=? AND run=? AND epoch=? AND state='RESERVED'", record["state"], string(Bytes(record)), record["receipt_hash"], project, id, run, r["lease_epoch"]); e != nil {
		return e
	}
	if e = tx.Commit(); e != nil {
		return e
	}
	return cause
}

// RegisterNativeEvaluationTool is a trusted local installation hook, like runtime
// fixture registration. It is not available to candidate HTTP credentials.
func (s *Service) RegisterNativeEvaluationTool(ctx context.Context, project, contentHash string) error {
	if e := s.Contracts.Validate("Digest", contentHash); e != nil {
		return e
	}
	_, e := s.DB.ExecContext(ctx, "INSERT INTO evaluation_native_tools(project,content_hash,registered_at) VALUES(?,?,?)", project, contentHash, Now())
	return e
}
func (s *Service) sealExperimentOutputs(tx *sql.Tx, p Principal, project string, r, record Object) error {
	ids, refs, manifest := Empty(), Empty(), Empty()
	seen := map[string]bool{}
	seal := func(name, kind string, raw []byte) (Object, error) {
		u, e := s.runtimeUpload(tx, p, project, raw)
		if e != nil {
			return nil, e
		}
		a, e := s.runtimeSeal(tx, p, project, Object{"run_id": r["id"], "kind": kind, "evidence_kind": "GENERATED", "measurement_mode": "FIXTURE", "content_hash": u["content_hash"], "storage_key": u["storage_key"], "media_type": "application/json", "byte_size": len(raw), "input_refs": r["input_refs"], "source_refs": Empty(), "produced_by": p.ID, "access_class": "PROJECT"})
		if e != nil {
			return nil, e
		}
		if !seen[Str(a, "id")] {
			ids = append(ids, a["id"])
			refs = append(refs, Ref(a, "Artifact"))
			manifest = append(manifest, Object{"path": name, "content_hash": a["content_hash"], "byte_size": a["byte_size"]})
			seen[Str(a, "id")] = true
		}
		if e = s.event(tx, project, "Artifact", a, p.ID, ID(), "PROJECT_UPDATED"); e != nil {
			return nil, e
		}
		return a, nil
	}
	for i, v := range Arr(record, "reports") {
		prefix := []string{"baseline", "candidate"}[i]
		raw, e := seal(prefix+".raw.json", "LOG", []byte(Arr(record, "raw_exports")[i].(string)))
		if e != nil {
			return e
		}
		report := v.(map[string]any)
		report["raw_artifact_refs"] = []any{Ref(raw, "Artifact")}
		if e = s.Contracts.Validate("EvaluationReport", report); e != nil {
			return fmt.Errorf("evaluation report schema: %w", e)
		}
		a, e := seal(prefix+".evaluation.json", "REPORT", Bytes(report))
		if e != nil {
			return e
		}
		summary := evaluation.Summary(report, Ref(a, "Artifact"))
		if e = s.Contracts.Validate("EvaluationSummary", summary); e != nil {
			return e
		}
		if _, e = seal(prefix+".summary.json", "REPORT", Bytes(summary)); e != nil {
			return e
		}
	}
	if _, e := seal("native-runtime.json", "LOG", Bytes(Object{"sandbox_receipts": record["sandbox_receipts"], "run_id": r["id"], "lease_epoch": r["lease_epoch"]})); e != nil {
		return e
	}
	if _, e := seal("paired-observations.json", "REPORT", Bytes(record["observation"])); e != nil {
		return e
	}
	record["artifact_ids"] = ids
	record["artifact_refs"] = refs
	record["runtime_artifacts"] = manifest
	return nil
}
