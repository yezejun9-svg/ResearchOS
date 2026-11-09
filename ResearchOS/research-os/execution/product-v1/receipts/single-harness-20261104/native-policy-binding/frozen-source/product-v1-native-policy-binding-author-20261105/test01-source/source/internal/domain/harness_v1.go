package domain

import (
	"context"
	"database/sql"
	"fmt"
	"strconv"
	"strings"
	"time"
	"unicode/utf8"
)

// HarnessAPI is an authenticated Host port. Credentials are validated by the
// implementation; caller-provided identity/authority booleans are not inputs.
type HarnessAPI interface {
	Capabilities(context.Context, string) (Object, error)
	Submit(context.Context, string, HarnessSubmit) (Object, error)
	List(context.Context, string, HarnessList) (Object, error)
	Get(context.Context, string, string, string) (Object, error)
	Events(context.Context, string, HarnessEvents) (Object, error)
	Cancel(context.Context, string, string, string, HarnessCancel) (Object, error)
}
type HarnessSubmit struct {
	RequestID    string `json:"request_id"`
	ProjectID    string `json:"project_id"`
	WorkspaceRef string `json:"workspace_ref"`
	HarnessID    string `json:"harness_id"`
	Scope        string `json:"scope"`
	Prompt       string `json:"prompt"`
}
type HarnessCancel struct {
	RequestID            string  `json:"request_id"`
	ExpectedTaskRevision string  `json:"expected_task_revision"`
	ExpectedRunID        *string `json:"expected_run_id"`
	ExpectedEpoch        *string `json:"expected_epoch"`
}
type HarnessList struct {
	ProjectID, Cursor, RequestID string
	Limit                        int
}
type HarnessEvents struct {
	ProjectID, TaskID, Cursor string
	Limit                     int
}
type HarnessError struct {
	Status        int
	Code, Message string
	TaskRef       Object
	Revision      *string
	Run           Object
}

func (e *HarnessError) Error() string { return e.Code + ": " + e.Message }
func harnessFail(status int, code, message string) error {
	return &HarnessError{Status: status, Code: code, Message: message}
}
func harnessLabel(s string, max int) bool {
	return len(s) > 0 && len(s) <= max && utf8.ValidString(s) && strings.TrimSpace(s) != "" && !strings.ContainsAny(s, "\x00\r\n")
}
func harnessRequestID(s string) bool {
	if !harnessLabel(s, 128) {
		return false
	}
	for i, c := range s {
		if !(c >= 'a' && c <= 'z' || c >= 'A' && c <= 'Z' || c >= '0' && c <= '9' || i > 0 && strings.ContainsRune("._:-", c)) {
			return false
		}
	}
	return true
}
func HarnessDecimal(s string, positive bool) (int64, error) {
	n, err := strconv.ParseInt(s, 10, 64)
	if err != nil || n < 0 || positive && n == 0 || strconv.FormatInt(n, 10) != s {
		return 0, harnessFail(400, "INVALID_REQUEST", "canonical decimal string required")
	}
	return n, nil
}
func (r HarnessSubmit) Validate() error {
	if !harnessRequestID(r.RequestID) || !harnessLabel(r.ProjectID, 128) || !harnessLabel(r.WorkspaceRef, 256) ||
		!utf8.ValidString(r.Prompt) || strings.TrimSpace(r.Prompt) == "" || len(r.Prompt) > 65536 || strings.ContainsRune(r.Prompt, 0) {
		return harnessFail(400, "INVALID_REQUEST", "bounded prompt and registered workspace reference required")
	}
	if r.HarnessID != "codex" || r.Scope != "workspace-read" {
		return harnessFail(422, "UNSUPPORTED_CAPABILITY", "only Codex workspace-read is supported")
	}
	return nil
}
func (r HarnessCancel) Validate() error {
	if !harnessRequestID(r.RequestID) {
		return harnessFail(400, "INVALID_REQUEST", "request_id required")
	}
	if _, err := HarnessDecimal(r.ExpectedTaskRevision, true); err != nil {
		return err
	}
	if (r.ExpectedRunID == nil) != (r.ExpectedEpoch == nil) {
		return harnessFail(400, "INVALID_REQUEST", "run and epoch must both be null or present")
	}
	if r.ExpectedRunID != nil {
		if !harnessLabel(*r.ExpectedRunID, 128) {
			return harnessFail(400, "INVALID_REQUEST", "run required")
		}
		if _, err := HarnessDecimal(*r.ExpectedEpoch, true); err != nil {
			return err
		}
	}
	return nil
}
func harnessRef(project, task string) Object { return Object{"project_id": project, "task_id": task} }
func harnessRunRef(run Object) any {
	if run == nil {
		return nil
	}
	epoch, _ := Num(run, "lease_epoch")
	return Object{"run_id": Str(run, "id"), "epoch": strconv.FormatInt(epoch, 10)}
}
func harnessErrorValue(err error) Object {
	if err == nil {
		return nil
	}
	e, ok := err.(*HarnessError)
	if !ok {
		e = &HarnessError{Status: 500, Code: "INTERNAL_ERROR", Message: "Host operation failed"}
	}
	return Object{"code": e.Code, "message": e.Message, "retryable": false, "task_ref": e.TaskRef, "current_task_revision": e.Revision, "current_run": e.Run}
}
func harnessEnvelope(data any) Object { return Object{"api_version": "harness.v1", "data": data} }
func harnessExecutionContract() Object {
	c := Object{"contract_revision": 1, "checks": []any{Object{"check_id": "codex-execution", "kind": "DETERMINISTIC", "required": true, "expected": "Host-observed bounded Codex execution; business acceptance is separate", "command_key": "harness.codex-execution-v1", "rubric_ref": nil, "qualification_id": nil, "not_applicable_reason": nil}}, "require_independent_verifier": true, "version_policy": "EXACT", "frozen_at": Now()}
	c["contract_hash"] = contractDigest(c)
	return c
}
func harnessScopeError(err error) error {
	if err == nil {
		return nil
	}
	return harnessFail(403, "WORKSPACE_REVOKED", fmt.Sprint("current registered workspace authority required"))
}

// HarnessAuthority is an actual Host-owned current-principal port, never a
// request Boolean. Implementations must reverify their local binding.
type HarnessAuthority interface {
	HarnessPrincipal(context.Context) (string, error)
}

// Harness task ownership is proven by the original Host operation and its
// sealed input; merely naming a generic task harness_turn grants no launch.
func harnessTaskInput(tx *sql.Tx, project string, task Object) (Object, error) {
	var principal, requestID, requestHash string
	if err := tx.QueryRow("SELECT principal,key,request_hash FROM idempotency WHERE project=? AND operation='harness:v1:submit' AND json_extract(body,'$.data.task_ref.task_id')=?", project, task["id"]).Scan(&principal, &requestID, &requestHash); err != nil {
		return nil, Fail(403, "FORBIDDEN", "original Host Harness submission missing")
	}
	for _, value := range Arr(task, "input_refs") {
		ref, ok := value.(map[string]any)
		if !ok || ref["entity_type"] != "Artifact" {
			continue
		}
		artifact, err := version(tx, project, ref)
		if err != nil {
			return nil, err
		}
		var raw []byte
		if err = tx.QueryRow("SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1", project, artifact["storage_key"]).Scan(&raw); err != nil {
			return nil, err
		}
		if Digest(raw) != artifact["content_hash"] {
			return nil, Fail(422, "CONTENT_HASH_MISMATCH", "native input seal changed")
		}
		data, err := Decode(raw)
		if err != nil || data["schema"] != "researchos.harness-submit.v1" {
			continue
		}
		request, ok := data["request"].(map[string]any)
		if !ok || data["principal_id"] != principal || request["request_id"] != requestID || request["project_id"] != project || Hash(request) != requestHash {
			return nil, Fail(403, "FORBIDDEN", "native submission identity changed")
		}
		return data, nil
	}
	return nil, Fail(403, "FORBIDDEN", "native input missing")
}
func (s *Service) nativeHarnessAdmission(tx *sql.Tx, project string, task, runtime Object, requested []any, operation string) (Object, error) {
	if task == nil || task["task_type"] != "harness_turn" || runtime["adapter"] != "codex-cli-harness-v1" || runtime["status"] != "AVAILABLE" || operation == "resume" || len(requested) != 1 || requested[0] != "start" {
		return nil, Fail(403, "FORBIDDEN", "native readonly Harness scope required")
	}
	ref, artifact, err := s.currentRuntimeBinding(tx, project, runtime)
	if err != nil {
		return nil, err
	}
	profile, err := runtimeProfileBody(tx, project, artifact)
	if err != nil {
		return nil, err
	}
	if profile["backend"] != "codex-cli-readonly-v1" || profile["sandbox"] != "codex-mxc-permissions-workspace-read-v2" || profile["command_id"] != "codex-mxc-readonly-v2" || profile["native_policy_revision"] != "researchos-codex-mxc-readonly-v1" || profile["windows_sandbox"] != "mxc" || profile["permission_profile"] != "researchos-readonly" || Str(profile, "requested_config_sha256") == "" || profile["credential_revision"] != "CLI_OWNED" {
		return nil, Fail(422, "GATE_FAILED", "native Harness profile required")
	}
	record, err := harnessTaskInput(tx, project, task)
	if err != nil {
		return nil, err
	}
	if record["runtime_id"] != runtime["id"] || Hash(record["profile_ref"]) != Hash(ref) || record["principal_id"] != profile["harness_owner"] {
		return nil, Fail(403, "FORBIDDEN", "native Task/profile mismatch")
	}
	principal := Str(record, "principal_id")
	owner, err := clientAuthenticatedPrincipal(context.Background(), tx, principal)
	if err != nil || owner.DeviceID != "" || !owner.HasRole("OWNER") || !owner.Allowed(project, "", "", false) {
		return nil, Fail(403, "FORBIDDEN", "native Owner authority revoked")
	}
	root, err := currentAuthorityRoot(tx, principal)
	if err != nil || root != profile["owner_root"] {
		return nil, Fail(403, "FORBIDDEN", "native Owner lineage changed")
	}
	request := record["request"].(map[string]any)
	binding, err := s.binding(context.Background(), tx, Str(request, "workspace_ref"))
	if err != nil || binding.PrincipalID != principal || binding.ProjectID == nil || *binding.ProjectID != project || binding.Status != WorkspaceActive {
		return nil, Fail(403, "FORBIDDEN", "native workspace revoked")
	}
	expires, err := time.Parse(time.RFC3339Nano, Str(profile, "consent_expires_at"))
	if err != nil || !expires.After(time.Now()) {
		return nil, Fail(403, "FORBIDDEN", "native Host consent expired")
	}
	return Object{"admission_kind": "HOST_HARNESS_V1", "mode": runtime["measurement_mode"], "runtime_id": runtime["id"], "runtime_ref": Ref(runtime, "RuntimeRegistration"), "profile_ref": ref, "profile_hash": Hash(ref), "profile": profile, "technical_hash": runtimeTechnicalHash(runtime), "qualification_ids": Empty(), "qualification_evidence": Empty(), "permission": Object{"kind": "OWNER_AUTHORIZED_HARNESS_TURN", "principal": principal, "workspace_ref": request["workspace_ref"], "scope": "workspace-read"}, "credential_revision": "CLI_OWNED", "expires_at": profile["consent_expires_at"], "requested_capabilities": requested}, nil
}
