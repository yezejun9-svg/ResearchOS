package verifier

import (
	"bytes"
	"context"
	"errors"
	"io"
	"net"
	"net/http"
	"net/url"
	"strings"
	"time"

	"researchos.local/research-os/internal/domain"
)

type apiClient struct {
	base, token, principal, project string
	http                            *http.Client
}

func newClient(job Job) (*apiClient, error) {
	u, e := url.Parse(job.APIURL)
	if e != nil || u.Scheme != "http" || u.User != nil || u.Path != "" || u.RawQuery != "" || u.Fragment != "" || net.ParseIP(u.Hostname()) == nil || !net.ParseIP(u.Hostname()).IsLoopback() {
		return nil, errors.New("fixed loopback control API required")
	}
	if job.Protocol != Protocol || job.Token == "" || job.PrincipalID == "" || job.ServiceRoot == "" || job.PrincipalID == job.ExecutorID || job.ProjectID == "" || job.RuntimeID == "" || job.Epoch < 1 || job.PlanHash == "" {
		return nil, errors.New("fixed verification job binding required")
	}
	for _, id := range []string{job.ProjectID, job.RuntimeID, domain.Str(job.TaskRef, "id"), domain.Str(job.RunRef, "id"), domain.Str(job.ProfileRef, "id"), domain.Str(job.ObservationRef, "id")} {
		if id == "" || strings.ContainsAny(id, "/\\?#% ") {
			return nil, errors.New("verification object identifier invalid")
		}
	}
	t := http.DefaultTransport.(*http.Transport).Clone()
	t.Proxy = nil
	return &apiClient{base: job.APIURL, token: job.Token, principal: job.PrincipalID, project: job.ProjectID, http: &http.Client{Timeout: 15 * time.Second, Transport: t, CheckRedirect: func(*http.Request, []*http.Request) error { return errors.New("control redirect refused") }}}, nil
}
func (c *apiClient) call(ctx context.Context, method, path, key, tag string, body any) (domain.Object, string, error) {
	var payload []byte
	if body != nil {
		payload = domain.Bytes(body)
	}
	r, e := http.NewRequestWithContext(ctx, method, c.base+"/v1/projects/"+c.project+path, bytes.NewReader(payload))
	if e != nil {
		return nil, "", errors.New("verification request invalid")
	}
	r.Header.Set("Authorization", "Bearer "+c.token)
	if body != nil {
		r.Header.Set("Content-Type", "application/json")
	}
	if key != "" {
		r.Header.Set("Idempotency-Key", key)
	}
	if tag != "" {
		r.Header.Set("If-Match", tag)
	}
	response, e := c.http.Do(r)
	if e != nil {
		return nil, "", errors.New("verification control request failed; no retry")
	}
	defer response.Body.Close()
	raw, e := io.ReadAll(io.LimitReader(response.Body, 4<<20+1))
	if e != nil || len(raw) > 4<<20 {
		return nil, "", errors.New("verification response invalid")
	}
	if response.StatusCode < 200 || response.StatusCode >= 300 || response.Header.Get("X-ResearchOS-Principal-ID") != c.principal {
		return nil, "", errors.New("verification operation rejected by control")
	}
	object, e := domain.Decode(raw)
	if e != nil {
		return nil, "", errors.New("verification object invalid")
	}
	return object, response.Header.Get("ETag"), nil
}
func (c *apiClient) artifact(ctx context.Context, ref domain.Object) (domain.Object, domain.Object, error) {
	if ref["entity_type"] != "Artifact" {
		return nil, nil, errors.New("sealed Artifact reference required")
	}
	id := domain.Str(ref, "id")
	a, _, e := c.call(ctx, "GET", "/artifacts/"+id, "", "", nil)
	if e != nil {
		return nil, nil, e
	}
	if domain.Hash(domain.Ref(a, "Artifact")) != domain.Hash(ref) || a["validity"] != "CURRENT" || a["measurement_mode"] != "LIVE" || a["sealed_at"] == nil {
		return nil, nil, errors.New("verification artifact seal changed")
	}
	r, e := http.NewRequestWithContext(ctx, "GET", c.base+"/v1/projects/"+c.project+"/artifacts/"+id+"/content", nil)
	if e != nil {
		return nil, nil, e
	}
	r.Header.Set("Authorization", "Bearer "+c.token)
	response, e := c.http.Do(r)
	if e != nil {
		return nil, nil, errors.New("artifact read failed; no retry")
	}
	defer response.Body.Close()
	raw, e := io.ReadAll(io.LimitReader(response.Body, 4<<20+1))
	size, _ := domain.Num(a, "byte_size")
	if e != nil || len(raw) > 4<<20 || response.StatusCode != 200 || response.Header.Get("X-ResearchOS-Principal-ID") != c.principal || domain.Digest(raw) != a["content_hash"] || int64(len(raw)) != size {
		return nil, nil, errors.New("artifact bytes differ from sealed metadata")
	}
	content, e := domain.Decode(raw)
	if e != nil {
		return nil, nil, errors.New("expected deterministic JSON evidence")
	}
	return a, content, nil
}

// Verify re-reads the exact settled evidence using only the service credential,
// then asks the existing server to recompute every frozen check. No result from
// the controller is accepted as a PASS claim. There is no retry of any write.
func Verify(ctx context.Context, job Job) (Result, error) {
	result := Result{Protocol: Protocol, Nonce: job.Nonce, Status: "REJECTED", ErrorCode: "VERIFICATION_FAILED"}
	c, e := newClient(job)
	if e != nil {
		return result, e
	}
	defer c.http.CloseIdleConnections()
	result.ErrorCode = "TASK_RUN_BINDING"
	task, tag, e := c.call(ctx, "GET", "/tasks/"+domain.Str(job.TaskRef, "id"), "", "", nil)
	if e != nil {
		return result, e
	}
	run, _, e := c.call(ctx, "GET", "/runs/"+domain.Str(job.RunRef, "id"), "", "", nil)
	if e != nil {
		return result, e
	}
	epoch, _ := domain.Num(run, "lease_epoch")
	if domain.Hash(domain.Ref(task, "Task")) != domain.Hash(job.TaskRef) || domain.Hash(domain.Ref(run, "Run")) != domain.Hash(job.RunRef) || task["task_type"] != "runtime_qualification" || task["status"] != "EXECUTION_REPORTED" || task["active_run_id"] != run["id"] || run["task_id"] != task["id"] || run["runtime_id"] != job.RuntimeID || run["executor_principal_id"] != job.ExecutorID || epoch != job.Epoch || run["status"] != "SETTLED" || run["children_stopped"] != true || run["queue_empty"] != true || run["context_bundle_id"] != task["context_bundle_id"] || domain.Hash(run["input_refs"]) != domain.Hash(task["input_refs"]) || domain.Hash(run["result_artifact_ids"]) != domain.Hash(task["output_artifact_ids"]) {
		return result, errors.New("current settled task/run binding differs")
	}
	result.ErrorCode = "PROFILE_EVIDENCE"
	_, profile, e := c.artifact(ctx, job.ProfileRef)
	if e != nil {
		return result, e
	}
	config, _ := profile["model_config"].(map[string]any)
	count, _ := domain.Num(config, "max_calls")
	qualification, _ := profile["model_qualification"].(map[string]any)
	qualificationCalls, _ := domain.Num(qualification, "max_calls")
	bounded := count == 1 && len(domain.Arr(config, "tools")) == 0 && profile["coding_authorization"] == nil
	if authorization, ok := profile["coding_authorization"].(map[string]any); ok {
		seen := map[string]bool{}
		for _, value := range domain.Arr(config, "tools") {
			tool, _ := value.(map[string]any)
			fn, _ := tool["function"].(map[string]any)
			name := domain.Str(fn, "name")
			if tool["type"] != "function" || seen[name] || (name != "read" && name != "write" && name != "edit" && name != "run_check") {
				return result, errors.New("coding tools differ from fixed host capabilities")
			}
			seen[name] = true
		}
		bounded = count == 8 && len(seen) == 4 && authorization["schema"] == "researchos.explicit-workspace-coding.v1" && authorization["model_config_ref"] == config["ref"] && domain.Hash(authorization["tool_policy"]) == domain.Hash(profile["tool_policy"])
	}
	if profile["runtime_id"] != job.RuntimeID || profile["backend"] != "mu-sdk-broker-v1" || profile["credential_revision"] != "none" || !bounded || qualificationCalls != 1 || qualification["route"] != config["route"] || qualification["model_config_hash"] != domain.Hash(config) {
		return result, errors.New("bounded credential-free Mu profile required")
	}
	result.ErrorCode = "NATIVE_OBSERVATION"
	log, observation, e := c.artifact(ctx, job.ObservationRef)
	if e != nil {
		return result, e
	}
	spec, _ := observation["spec"].(map[string]any)
	if log["run_id"] != run["id"] || log["kind"] != "LOG" || observation["state"] != "SETTLED" || observation["children_stopped"] != true || observation["queue_empty"] != true || spec["profile_hash"] != domain.Hash(job.ProfileRef) {
		return result, errors.New("original native observation differs")
	}
	result.ErrorCode = "OUTPUT_EVIDENCE"
	outputs := domain.Empty()
	for _, value := range domain.Arr(task, "output_artifact_ids") {
		id, ok := value.(string)
		if !ok || strings.ContainsAny(id, "/\\?#% ") {
			return result, errors.New("output identifier invalid")
		}
		a, _, err := c.call(ctx, "GET", "/artifacts/"+id, "", "", nil)
		if err != nil {
			return result, err
		}
		if a["run_id"] != run["id"] {
			return result, errors.New("output belongs to another run")
		}
		ref := domain.Ref(a, "Artifact")
		if _, _, err = c.artifact(ctx, ref); err != nil {
			return result, err
		}
		outputs = append(outputs, ref)
	}
	if len(outputs) != 1 {
		return result, errors.New("one bounded Mu output required")
	}
	result.ErrorCode = "FROZEN_CHECKS"
	contract, _ := task["acceptance_contract"].(map[string]any)
	checks := domain.Empty()
	for _, value := range domain.Arr(contract, "checks") {
		check, ok := value.(map[string]any)
		if !ok || check["kind"] != "DETERMINISTIC" || check["command_key"] != "mu.turn-output-v1" || check["rubric_ref"] != nil || check["qualification_id"] != nil {
			return result, errors.New("unsupported frozen deterministic check")
		}
		checks = append(checks, domain.Object{"check_id": check["check_id"], "status": "NOT_RUN", "actual": "Request independent server recomputation of frozen native Mu evidence", "command_key": check["command_key"], "exit_code": nil, "evidence_refs": domain.Empty(), "started_at": nil, "finished_at": nil})
	}
	if len(checks) == 0 || contract["require_independent_verifier"] != true {
		return result, errors.New("frozen independent checks missing")
	}
	result.ErrorCode = "DETERMINISTIC_CHECK"
	snapshot := job.VerificationSnapshot
	mu, _ := snapshot["mu_turn"].(map[string]any)
	if snapshot == nil || domain.Hash(snapshot) != job.VerificationSnapshotHash || domain.Hash(snapshot["task"]) != domain.Hash(task) || domain.Hash(snapshot["run"]) != domain.Hash(run) || domain.Hash(mu["profile"]) != domain.Hash(profile) {
		return result, errors.New("private verification snapshot differs from current public evidence")
	}
	snapshotOutputs := domain.Empty()
	for _, value := range domain.Arr(snapshot, "artifacts") {
		entry, _ := value.(map[string]any)
		artifact, _ := entry["artifact"].(map[string]any)
		snapshotOutputs = append(snapshotOutputs, domain.Ref(artifact, "Artifact"))
	}
	if domain.Hash(snapshotOutputs) != domain.Hash(outputs) {
		return result, errors.New("snapshot output seals differ from independently read artifacts")
	}
	status, _ := domain.CheckLocalRuntimeQualification(snapshot)
	if status != "PASS" {
		return result, errors.New("separate deterministic check did not pass")
	}
	result.ErrorCode = "SERVER_ACCEPTANCE"
	state, _, e := c.call(ctx, "GET", "/state", "", "", nil)
	if e != nil {
		return result, e
	}
	body := domain.Object{"subject_ref": job.TaskRef, "run_id": run["id"], "contract_hash": contract["contract_hash"], "input_refs": task["input_refs"], "artifact_refs": outputs, "checks": checks, "verdict": "PASS", "executor_principal_ids": []any{job.ExecutorID}, "independence_basis": "DETERMINISTIC_SERVICE", "blocking_conflict_ids": domain.Empty(), "qualification_ids": domain.Empty(), "policy_revision": state["policy_revision"], "measurement_mode": "LIVE", "reason": "Separate installed local deterministic service requested frozen check recomputation; application separation only."}
	receipt, _, e := c.call(ctx, "POST", "/acceptances", job.Nonce+"-accept", tag, body)
	if e != nil {
		return result, e
	}
	if receipt["verdict"] != "PASS" || receipt["verifier_principal_id"] != job.PrincipalID || receipt["run_id"] != run["id"] || domain.Hash(receipt["subject_ref"]) != domain.Hash(job.TaskRef) || receipt["receipt_hash"] != domain.Receipt(receipt) {
		return result, errors.New("server did not produce the exact independent PASS")
	}
	result.ErrorCode = "SERVER_QUALIFICATION"
	runtime, runtimeTag, e := c.call(ctx, "GET", "/runtimes/"+job.RuntimeID, "", "", nil)
	if e != nil {
		return result, e
	}
	if runtime["status"] != "REGISTERED" {
		return result, errors.New("runtime is not awaiting first qualification")
	}
	qualified, _, e := c.call(ctx, "POST", "/runtimes/"+job.RuntimeID+"/qualify", job.Nonce+"-qualify", runtimeTag, domain.Object{"qualification_ids": []any{receipt["id"]}, "supports_resume": false, "resume_evidence_ref": nil, "receipt_artifact_ref": job.ObservationRef})
	if e != nil {
		return result, e
	}
	if qualified["status"] != "AVAILABLE" || qualified["supports_resume"] != false || domain.Hash(qualified["qualification_ids"]) != domain.Hash([]any{receipt["id"]}) {
		return result, errors.New("server qualification response differs")
	}
	return Result{Protocol: Protocol, Nonce: job.Nonce, Status: "QUALIFIED", RuntimeRef: domain.Ref(qualified, "RuntimeRegistration"), AcceptanceRef: domain.Ref(receipt, "AcceptanceReceipt"), ObservationRef: job.ObservationRef}, nil
}
