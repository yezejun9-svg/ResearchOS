package domain

import (
	"context"
	"database/sql"
	"encoding/hex"
	"strings"
	"time"
)

const preparedAbandonmentOutcome = "FAILED_NOT_DISPATCHED_ACCOUNTING_UNKNOWN"

// PreparedRunAbandonmentEvidence is a signed Root-witness input for a local-only
// operation. A caller's fields are never sufficient authority: Service has no
// verifier by default and no public constructor or HTTP route grants one.
type PreparedRunAbandonmentEvidence struct {
	Schema                string  `json:"schema"`
	Outcome               string  `json:"outcome"`
	ProjectID             string  `json:"project_id"`
	TaskID                string  `json:"task_id"`
	RunID                 string  `json:"run_id"`
	RuntimeID             string  `json:"runtime_id"`
	OwnerRoot             string  `json:"owner_root"`
	Epoch                 int64   `json:"epoch"`
	RunRevision           int64   `json:"run_revision"`
	TaskRevision          int64   `json:"task_revision"`
	DispatchKey           string  `json:"dispatch_key"`
	ManifestHash          string  `json:"manifest_hash"`
	RootStartedUTC        string  `json:"root_started_utc"`
	RootClockExpiredUTC   string  `json:"root_clock_expired_utc"`
	ParentJobID           string  `json:"parent_job_id"`
	ParentJobClosedUTC    string  `json:"parent_job_closed_utc"`
	ParentJobTerminal     bool    `json:"parent_job_terminal"`
	HostJobContractSHA256 string  `json:"host_job_contract_sha256"`
	HostJobProbeSHA256    string  `json:"host_job_probe_sha256"`
	GOAuthoritySHA256     string  `json:"go_authority_sha256"`
	RootWitnessSHA256     string  `json:"root_witness_sha256"`
	RootWitnessSignature  string  `json:"root_witness_signature"`
	ProviderRequests      *int64  `json:"provider_requests"`
	ActualCost            *string `json:"actual_cost"`
	FinancialClosed       bool    `json:"financial_closed"`
}

// Only a trusted local Root-witness integration within package domain may
// install this private capability. Production's default nil rejects every call.
// The verifier must authenticate the Root witness signature, exact source pins,
// parent Job terminal fact, and exclusive data-root ownership independently.
type preparedRunAbandonmentAuthority interface {
	verifyPreparedRunAbandonment(context.Context, PreparedRunAbandonmentEvidence) error
}

func preparedAbandonmentDigest(s string) bool {
	if len(s) != 71 || !strings.HasPrefix(s, "sha256:") {
		return false
	}
	b, err := hex.DecodeString(s[7:])
	return err == nil && len(b) == 32
}

func validatePreparedAbandonmentEvidence(e PreparedRunAbandonmentEvidence) error {
	if e.Schema != "researchos.prepared-run-abandonment.v1" || e.Outcome != preparedAbandonmentOutcome || e.ProjectID == "" || e.TaskID == "" || e.RunID == "" || e.RuntimeID == "" || e.OwnerRoot == "" || e.DispatchKey == "" || e.ParentJobID == "" || e.Epoch < 1 || e.RunRevision < 1 || e.TaskRevision < 1 || !e.ParentJobTerminal {
		return Fail(422, "GATE_FAILED", "exact pre-dispatch abandonment identity and terminal parent Job required")
	}
	if e.FinancialClosed || e.ProviderRequests != nil || e.ActualCost != nil {
		return Fail(422, "GATE_FAILED", "unknown provider accounting must remain open and null")
	}
	for _, digest := range []string{e.ManifestHash, e.HostJobContractSHA256, e.HostJobProbeSHA256, e.GOAuthoritySHA256, e.RootWitnessSHA256} {
		if !preparedAbandonmentDigest(digest) {
			return Fail(422, "GATE_FAILED", "pinned Root witness or dispatch digest required")
		}
	}
	if len(e.RootWitnessSignature) == 0 {
		return Fail(422, "GATE_FAILED", "signed Root witness required")
	}
	started, err := time.Parse(time.RFC3339Nano, e.RootStartedUTC)
	if err != nil {
		return Fail(422, "GATE_FAILED", "Root start time invalid")
	}
	expired, err := time.Parse(time.RFC3339Nano, e.RootClockExpiredUTC)
	if err != nil || !expired.Equal(started.Add(300*time.Second)) || time.Now().Before(expired) {
		return Fail(422, "GATE_FAILED", "original Root clock must be expired")
	}
	closed, err := time.Parse(time.RFC3339Nano, e.ParentJobClosedUTC)
	if err != nil || time.Now().Before(closed) {
		return Fail(422, "GATE_FAILED", "terminal parent Job time invalid")
	}
	return nil
}

func preparedRunAbandonmentExists(tx *sql.Tx, project, run string, epoch int64) (bool, error) {
	var count int
	err := tx.QueryRow("SELECT count(*) FROM runtime_prepared_abandonments WHERE project=? AND run=? AND epoch=?", project, run, epoch).Scan(&count)
	return count != 0, err
}

// Only the exact sealed pre-admission profile upload may be excluded from the
// executor-wide upload footprint. Every binding is checked under the caller's
// resourceWriteLock transaction; none of these checks grants launch authority.
func (s *Service) preparedRunAbandonmentProfileUpload(tx *sql.Tx, e PreparedRunAbandonmentEvidence, run, task, manifest Object) (string, error) {
	reject := func() (string, error) {
		return "", Fail(409, "STATE_CONFLICT", "preparation profile immutable binding differs")
	}
	plan, planHash, planRoot, err := qualificationPlan(tx, e.ProjectID, e.TaskID, e.RuntimeID)
	if err != nil {
		return "", err
	}
	if planRoot != e.OwnerRoot || plan["runtime_id"] != e.RuntimeID || plan["task_hash"] != qualificationTaskHash(task) {
		return reject()
	}
	profileRef, ok := plan["profile_ref"].(map[string]any)
	if !ok || profileRef["entity_type"] != "Artifact" {
		return reject()
	}
	var markerPlan, markerProfile, markerContract, markerInputs, markerContext string
	if err = tx.QueryRow("SELECT plan_hash,profile_hash,contract_hash,input_hash,context_bundle FROM runtime_qualification_runs WHERE project=? AND task=? AND run=? AND runtime=? AND epoch=? AND owner_root=?", e.ProjectID, e.TaskID, e.RunID, e.RuntimeID, e.Epoch, e.OwnerRoot).Scan(&markerPlan, &markerProfile, &markerContract, &markerInputs, &markerContext); err != nil {
		return "", Fail(409, "STATE_CONFLICT", "preparation profile qualification marker differs")
	}
	contract, ok := task["acceptance_contract"].(map[string]any)
	if !ok || markerPlan != planHash || markerProfile != Hash(profileRef) || markerContract != Str(contract, "contract_hash") || markerContract != manifest["contract_hash"] || markerInputs != Hash(task["input_refs"]) || markerInputs != Hash(run["input_refs"]) || markerInputs != Hash(manifest["input_refs"]) || markerContext != task["context_bundle_id"] || markerContext != run["context_bundle_id"] || markerContext != manifest["context_bundle_id"] {
		return reject()
	}
	found := 0
	for _, input := range Arr(task, "input_refs") {
		if Hash(input) == Hash(profileRef) {
			found++
		}
	}
	if found != 1 {
		return reject()
	}
	admission, ok := manifest["admission"].(map[string]any)
	if !ok {
		return reject()
	}
	permission, ok := admission["permission"].(map[string]any)
	if !ok || admission["qualification_bootstrap"] != true || Hash(admission["profile_ref"]) != Hash(profileRef) || admission["profile_hash"] != Hash(profileRef) || permission["plan_hash"] != planHash || permission["author_root"] != e.OwnerRoot {
		return reject()
	}
	runtime, err := load(tx, e.ProjectID, "RuntimeRegistration", e.RuntimeID)
	if err != nil {
		return "", err
	}
	boundRef, artifact, err := s.currentRuntimeBinding(tx, e.ProjectID, runtime)
	if err != nil {
		return "", err
	}
	if Hash(boundRef) != Hash(profileRef) || Hash(Ref(artifact, "Artifact")) != Hash(profileRef) || artifact["validity"] != "CURRENT" || artifact["run_id"] != nil || artifact["produced_by"] != run["executor_principal_id"] || Str(artifact, "storage_key") == "" || artifact["content_hash"] != profileRef["content_hash"] {
		return reject()
	}
	sealedAt, sealedErr := time.Parse(time.RFC3339Nano, Str(artifact, "sealed_at"))
	runCreated, createdErr := time.Parse(time.RFC3339Nano, Str(run, "created_at"))
	size, sizeErr := Num(artifact, "byte_size")
	if sealedErr != nil || createdErr != nil || sealedAt.After(runCreated) || sizeErr != nil || size <= 0 {
		return reject()
	}
	var raw []byte
	var digest, principal string
	var sealed int
	storageKey := Str(artifact, "storage_key")
	if err = tx.QueryRow("SELECT bytes,content_hash,principal,sealed FROM uploaded_content WHERE project=? AND storage_key=?", e.ProjectID, storageKey).Scan(&raw, &digest, &principal, &sealed); err != nil {
		return "", Fail(409, "STATE_CONFLICT", "preparation profile upload missing")
	}
	if sealed != 1 || principal != run["executor_principal_id"] || digest != artifact["content_hash"] || Digest(raw) != digest || int64(len(raw)) != size {
		return "", Fail(409, "STATE_CONFLICT", "preparation profile upload integrity differs")
	}
	profile, err := Decode(raw)
	if err != nil || Hash(profile) != Hash(admission["profile"]) || profile["runtime_id"] != e.RuntimeID || profile["technical_hash"] != admission["technical_hash"] {
		return reject()
	}
	return storageKey, nil
}

func preparedRunAbandonmentFootprint(tx *sql.Tx, e PreparedRunAbandonmentEvidence, executor, preparationStorageKey string) error {
	checks := []struct {
		query string
		args  []any
	}{
		{"SELECT count(*) FROM runtime_observations WHERE project=? AND run=?", []any{e.ProjectID, e.RunID}},
		{"SELECT count(*) FROM runtime_uploads WHERE project=? AND run=?", []any{e.ProjectID, e.RunID}},
		{"SELECT count(*) FROM artifact_uses WHERE project=? AND run=?", []any{e.ProjectID, e.RunID}},
		{"SELECT count(*) FROM artifact_use_proofs WHERE project=? AND run=?", []any{e.ProjectID, e.RunID}},
		{"SELECT count(*) FROM resource_effects WHERE project=? AND run=?", []any{e.ProjectID, e.RunID}},
		{"SELECT count(*) FROM domain_objects WHERE project=? AND kind='BudgetLedgerEntry' AND (json_extract(body,'$.run_id')=? OR json_extract(body,'$.provider_request_id')=?)", []any{e.ProjectID, e.RunID, "qualification-dispatch/" + e.RunID}},
		{"SELECT count(*) FROM domain_objects WHERE project=? AND kind='Artifact' AND json_extract(body,'$.run_id')=?", []any{e.ProjectID, e.RunID}},
		{"SELECT count(*) FROM uploaded_content WHERE project=? AND principal=? AND storage_key<>?", []any{e.ProjectID, executor, preparationStorageKey}},
		{"SELECT count(*) FROM client_queue_fences WHERE project=? AND (task_id=? OR run_id=?)", []any{e.ProjectID, e.TaskID, e.RunID}},
		{"SELECT count(*) FROM client_command_queue WHERE project=? AND task_id=?", []any{e.ProjectID, e.TaskID}},
		{"SELECT count(*) FROM client_control_requests WHERE project=? AND EXISTS (SELECT 1 FROM json_each(task_ids) WHERE value=?)", []any{e.ProjectID, e.TaskID}},
		{"SELECT count(*) FROM runtime_qualification_approvals WHERE project=? AND run=?", []any{e.ProjectID, e.RunID}},
	}
	for _, check := range checks {
		var count int
		if err := tx.QueryRow(check.query, check.args...).Scan(&count); err != nil {
			return err
		}
		if count != 0 {
			return Fail(409, "STATE_CONFLICT", "pre-dispatch abandonment refuses any recorded worker, upload, queue, effect, or billing footprint")
		}
	}
	return nil
}

// AbandonPreparedQualification is deliberately absent from runtimeOperations and
// every HTTP/client protocol route. Only an explicitly Root-bound Service with
// a trusted witness verifier may record failure before native dispatch.
func (s *Service) AbandonPreparedQualification(ctx context.Context, ownerToken string, evidence PreparedRunAbandonmentEvidence) (Object, error) {
	if s.preparedAbandonmentAuthority == nil {
		return nil, Fail(503, "RESOURCE_UNAVAILABLE", "trusted Root abandonment witness not installed")
	}
	if err := validatePreparedAbandonmentEvidence(evidence); err != nil {
		return nil, err
	}
	tx, err := s.DB.BeginTx(ctx, nil)
	if err != nil {
		return nil, err
	}
	defer tx.Rollback()
	if err = resourceWriteLock(tx); err != nil {
		return nil, err
	}
	owner, err := authenticate(tx, ownerToken)
	if err != nil {
		return nil, err
	}
	if !owner.HasRole("OWNER") || !owner.Allowed(evidence.ProjectID, "", "", false) {
		return nil, Fail(403, "FORBIDDEN", "current project Owner required")
	}
	root, err := authorityRoot(tx, owner.ID)
	if err != nil || root != owner.ID || root != evidence.OwnerRoot {
		return nil, Fail(403, "FORBIDDEN", "direct local Root Owner required")
	}
	if err = s.preparedAbandonmentAuthority.verifyPreparedRunAbandonment(ctx, evidence); err != nil {
		return nil, err
	}
	proofHash := Digest(Bytes(evidence))
	var priorHash, priorTask, priorKey, priorManifest string
	err = tx.QueryRow("SELECT proof_hash,task,dispatch_key,manifest_hash FROM runtime_prepared_abandonments WHERE project=? AND run=? AND epoch=?", evidence.ProjectID, evidence.RunID, evidence.Epoch).Scan(&priorHash, &priorTask, &priorKey, &priorManifest)
	if err != nil && err != sql.ErrNoRows {
		return nil, err
	}
	if err == nil {
		if priorHash != proofHash || priorTask != evidence.TaskID || priorKey != evidence.DispatchKey || priorManifest != evidence.ManifestHash {
			return nil, Fail(409, "STATE_CONFLICT", "different abandonment proof already sealed")
		}
		priorRun, loadErr := load(tx, evidence.ProjectID, "Run", evidence.RunID)
		if loadErr != nil || priorRun["status"] != "FAILED" {
			return nil, Fail(409, "STATE_CONFLICT", "abandonment proof lacks terminal Run")
		}
		priorTaskObject, loadErr := load(tx, evidence.ProjectID, "Task", evidence.TaskID)
		if loadErr != nil || priorTaskObject["status"] != "FAILED" || priorTaskObject["active_run_id"] != evidence.RunID {
			return nil, Fail(409, "STATE_CONFLICT", "abandonment proof lacks terminal Task")
		}
		return priorRun, nil
	}
	run, err := load(tx, evidence.ProjectID, "Run", evidence.RunID)
	if err != nil {
		return nil, err
	}
	task, err := load(tx, evidence.ProjectID, "Task", evidence.TaskID)
	if err != nil {
		return nil, err
	}
	runRevision, runErr := Num(run, "revision")
	taskRevision, taskErr := Num(task, "revision")
	epoch, epochErr := Num(run, "lease_epoch")
	expiry, timeErr := time.Parse(time.RFC3339Nano, Str(run, "lease_expires_at"))
	if runErr != nil || taskErr != nil || epochErr != nil || timeErr != nil || runRevision != evidence.RunRevision || taskRevision != evidence.TaskRevision || epoch != evidence.Epoch || !time.Now().After(expiry) || run["status"] != "QUEUED" || task["status"] != "RUNNING" || task["task_type"] != "runtime_qualification" || task["active_run_id"] != evidence.RunID || run["task_id"] != evidence.TaskID || run["runtime_id"] != evidence.RuntimeID || task["assigned_principal_id"] != run["executor_principal_id"] || run["started_at"] != nil || run["heartbeat_at"] != nil || run["external_run_id"] != nil || run["checkpoint_artifact_id"] != nil || len(Arr(run, "result_artifact_ids")) != 0 || run["runtime_settled_at"] != nil || run["cancel_requested_at"] != nil {
		return nil, Fail(409, "STATE_CONFLICT", "current pre-dispatch Run, Task, revision or expired lease differs")
	}
	var markerRun, markerRuntime, markerRoot string
	var markerEpoch int64
	if err = tx.QueryRow("SELECT run,runtime,epoch,owner_root FROM runtime_qualification_runs WHERE project=? AND task=?", evidence.ProjectID, evidence.TaskID).Scan(&markerRun, &markerRuntime, &markerEpoch, &markerRoot); err != nil || markerRun != evidence.RunID || markerRuntime != evidence.RuntimeID || markerEpoch != evidence.Epoch || markerRoot != root {
		return nil, Fail(409, "STATE_CONFLICT", "immutable qualification marker differs")
	}
	dispatch, err := runtimeDispatch(tx, evidence.ProjectID, evidence.RunID, evidence.Epoch)
	if err != nil {
		return nil, err
	}
	manifest := dispatch["manifest"].(map[string]any)
	sequence, sequenceErr := Num(dispatch, "observation_sequence")
	if sequenceErr != nil || dispatch["state"] != "PREPARED" || dispatch["worker"] != "" || dispatch["journal_locator"] != "" || len(dispatch["identity"].(map[string]any)) != 0 || sequence != 0 || dispatch["observation_hash"] != "" || dispatch["reason"] != "" || dispatch["dispatch_key"] != evidence.DispatchKey || dispatch["manifest_hash"] != evidence.ManifestHash || manifest["task_id"] != evidence.TaskID || manifest["runtime_id"] != evidence.RuntimeID || manifest["executor_principal_id"] != run["executor_principal_id"] {
		return nil, Fail(409, "STATE_CONFLICT", "native dispatch launch fence or immutable manifest differs")
	}
	preparationStorageKey, err := s.preparedRunAbandonmentProfileUpload(tx, evidence, run, task, manifest)
	if err != nil {
		return nil, err
	}
	if err = preparedRunAbandonmentFootprint(tx, evidence, Str(run, "executor_principal_id"), preparationStorageKey); err != nil {
		return nil, err
	}
	if err = bump(run); err != nil {
		return nil, err
	}
	run["status"] = "FAILED"
	run["execution_report"] = "Trusted pre-dispatch abandonment; provider accounting remains unknown and open."
	run["ended_at"] = Now()
	if err = s.put(tx, "Run", run); err != nil {
		return nil, err
	}
	if err = s.event(tx, evidence.ProjectID, "Run", run, owner.ID, ID(), "RUN_CHANGED"); err != nil {
		return nil, err
	}
	if err = bump(task); err != nil {
		return nil, err
	}
	task["status"] = "FAILED"
	if err = s.put(tx, "Task", task); err != nil {
		return nil, err
	}
	if err = s.event(tx, evidence.ProjectID, "Task", task, owner.ID, ID(), "TASK_CHANGED"); err != nil {
		return nil, err
	}
	if _, err = tx.Exec("INSERT INTO runtime_prepared_abandonments(project,task,run,runtime,epoch,dispatch_key,manifest_hash,owner_root,proof_hash,proof_json,outcome,financial_closed,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,0,?)", evidence.ProjectID, evidence.TaskID, evidence.RunID, evidence.RuntimeID, evidence.Epoch, evidence.DispatchKey, evidence.ManifestHash, root, proofHash, string(Bytes(evidence)), preparedAbandonmentOutcome, Now()); err != nil {
		return nil, err
	}
	return run, tx.Commit()
}
