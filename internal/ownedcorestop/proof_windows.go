//go:build windows

package ownedcorestop

import (
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"researchos.local/research-os/internal/store"
)

const proofSchema = "researchos.owned-core-stop-independent-evidence.v1"
const planReviewSchema = "researchos.owned-core-stop-independent-plan-review.v1"

var proofKinds = []string{"f01_ready", "retained_window", "native_entry_gates", "worker_native_exit", "verifier_native_exit", "effect_census", "independent_evidence_review"}

// These are observations in independent receipts, not caller-side booleans.
// Every required digest names a separate raw artifact retained by its reviewer.
type historicalEvidence struct {
	Schema                   string                 `json:"schema"`
	Kind                     string                 `json:"kind"`
	OperationID              string                 `json:"operation_id"`
	SourceCommit             string                 `json:"source_commit"`
	CorePID                  uint32                 `json:"core_pid"`
	CoreCreatedNS            int64                  `json:"core_created_ns"`
	CoreImageSHA256          string                 `json:"core_image_sha256"`
	HostID                   string                 `json:"host_id"`
	OwnerID                  string                 `json:"owner_id"`
	OwnerRoot                string                 `json:"owner_root"`
	Subject                  store.OwnedStopSubject `json:"subject"`
	Reviewer                 string                 `json:"reviewer"`
	RawSHA256                map[string]string      `json:"raw_sha256"`
	NativePID                uint32                 `json:"native_pid,omitempty"`
	NativeCreatedNS          int64                  `json:"native_created_ns,omitempty"`
	NativeExitCode           uint32                 `json:"native_exit_code,omitempty"`
	NativeWaitAPI            string                 `json:"native_wait_api,omitempty"`
	NativeWaitResult         uint32                 `json:"native_wait_result,omitempty"`
	NativeExitAPI            string                 `json:"native_exit_api,omitempty"`
	NativeHandleRecordSHA256 string                 `json:"native_handle_record_sha256,omitempty"`
	BaselineSHA256           string                 `json:"baseline_sha256,omitempty"`
}

type operationPlanReview struct {
	Schema                   string `json:"schema"`
	OperationID              string `json:"operation_id"`
	PlanSHA256               string `json:"plan_sha256"`
	EvidenceSHA256           string `json:"evidence_sha256"`
	SourceCommit             string `json:"source_commit"`
	CoreCreatedNS            int64  `json:"core_created_ns"`
	CoreImageSHA256          string `json:"core_image_sha256"`
	Reviewer                 string `json:"reviewer"`
	Verdict                  string `json:"verdict"`
	RootOperationScopeSHA256 string `json:"root_operation_scope_sha256"`
}

func verifierPath(repo, path string) error {
	if !filepath.IsAbs(repo) || !filepath.IsAbs(path) || filepath.Clean(path) != path {
		return errors.New("canonical independent evidence path required")
	}
	root := filepath.Join(repo, "execution", "verifier")
	rel, err := filepath.Rel(root, path)
	if err != nil || rel == "." || strings.HasPrefix(rel, ".."+string(filepath.Separator)) || rel == ".." || filepath.IsAbs(rel) {
		return errors.New("evidence outside independent verifier namespace")
	}
	actual, err := filepath.EvalSymlinks(path)
	if err != nil || !strings.EqualFold(actual, path) {
		return errors.New("evidence reparse or absence")
	}
	return nil
}

func readEvidence(repo string, ref EvidenceRef) (historicalEvidence, error) {
	var out historicalEvidence
	if !validSHA(ref.SHA256) {
		return out, errors.New("evidence hash required")
	}
	if err := verifierPath(repo, ref.Path); err != nil {
		return out, err
	}
	raw, err := os.ReadFile(ref.Path)
	if err != nil {
		return out, err
	}
	if len(raw) == 0 || len(raw) > 128<<10 || digest(raw) != ref.SHA256 {
		return out, errors.New("evidence content/hash mismatch")
	}
	if err = strictJSON(raw, &out); err != nil {
		return out, err
	}
	if out.Schema != proofSchema || out.Kind != ref.Kind || out.Reviewer == "" || strings.Contains(out.Reviewer, "owned_core_stop_builder") {
		return out, errors.New("independent evidence identity invalid")
	}
	return out, nil
}

func proofNeeds(kind string) []string {
	switch kind {
	case "f01_ready":
		return []string{"main4f_build", "store_open_ready", "wal_full_live_core", "startup_native_identity"}
	case "retained_window":
		return []string{"consumed_original_request", "begin_window_marker", "end_unresolved_return", "scan_durable_fence"}
	case "native_entry_gates":
		return []string{"all_entry_map", "durable_prepare_before_effect", "dispatch_before_worker", "serial_desktop_serve", "no_alternate_bypass"}
	case "worker_native_exit":
		return []string{"original_os_wait_capture", "numeric_exit_capture", "job_drained", "owner_lock_released"}
	case "verifier_native_exit":
		return []string{"original_os_wait_capture", "numeric_exit_capture", "original_verifier_registration"}
	case "effect_census":
		return []string{"complete_current_census", "original_model_receipt", "original_request_hash", "original_dispatch_hash"}
	case "independent_evidence_review":
		return proofKinds[:6]
	default:
		return nil
	}
}

func validateHistoricalEvidence(plan Plan) (string, []string) {
	missing := []string{}
	refs := map[string]EvidenceRef{}
	for _, r := range plan.Input.Evidence {
		if _, exists := refs[r.Kind]; exists {
			missing = append(missing, "duplicate "+r.Kind)
		}
		refs[r.Kind] = r
	}
	if len(refs) != len(proofKinds) {
		missing = append(missing, "exact seven independent receipts required")
	}
	observed := map[string]string{}
	for _, kind := range proofKinds {
		ref, ok := refs[kind]
		if !ok {
			missing = append(missing, kind+": missing")
			continue
		}
		receipt, err := readEvidence(plan.Input.SourceRepository, ref)
		if err != nil {
			missing = append(missing, kind+": "+err.Error())
			continue
		}
		if receipt.OperationID != plan.OperationID || receipt.SourceCommit != SourceBaseCommit || receipt.CorePID != plan.Native.PID || receipt.CoreCreatedNS != plan.Native.CreatedNS || receipt.CoreImageSHA256 != plan.Native.ImageSHA256 || receipt.HostID != plan.Host.HostID || receipt.OwnerID != plan.Host.OwnerID || receipt.OwnerRoot != plan.Host.OwnerRoot || receipt.Subject != plan.Input.Subject {
			missing = append(missing, kind+": subject/authority/core binding differs")
			continue
		}
		if kind == "worker_native_exit" || kind == "verifier_native_exit" {
			// An ignored cmd.Wait error, a PID-list absence, or an assumed exit 0
			// cannot satisfy this typed original OS wait and numeric-exit receipt.
			if receipt.NativePID == 0 || receipt.NativePID == plan.Native.PID || receipt.NativeCreatedNS == 0 || receipt.NativeWaitAPI != "WaitForSingleObject" || receipt.NativeWaitResult != 0 || receipt.NativeExitAPI != "GetExitCodeProcess" || !validSHA(receipt.NativeHandleRecordSHA256) {
				missing = append(missing, kind+": captured exact OS wait/exit/handle identity absent")
			}
		}
		if kind == "effect_census" && receipt.BaselineSHA256 != plan.Baseline.SHA256 {
			missing = append(missing, kind+": full baseline differs")
		}
		for _, name := range proofNeeds(kind) {
			hash := receipt.RawSHA256[name]
			if !validSHA(hash) {
				missing = append(missing, fmt.Sprintf("%s: %s raw receipt missing", kind, name))
			}
			if kind == "independent_evidence_review" && hash != observed[name] {
				missing = append(missing, kind+": evidence hash differs for "+name)
			}
		}
		observed[kind] = ref.SHA256
	}
	// Bind the seven references and their order into a single reviewable digest.
	raw, _ := canonicalJSON(plan.Input.Evidence)
	return digest(raw), missing
}

func validatePlanReview(plan Plan, planSHA string) error {
	if plan.Input.PlanReviewPath == "" {
		return errors.New("independent operation plan review missing")
	}
	if err := verifierPath(plan.Input.SourceRepository, plan.Input.PlanReviewPath); err != nil {
		return err
	}
	raw, err := os.ReadFile(plan.Input.PlanReviewPath)
	if err != nil {
		return err
	}
	if len(raw) == 0 || len(raw) > 64<<10 {
		return errors.New("bounded plan review required")
	}
	var r operationPlanReview
	if err = strictJSON(raw, &r); err != nil {
		return err
	}
	if r.Schema != planReviewSchema || r.OperationID != plan.OperationID || r.PlanSHA256 != planSHA || r.EvidenceSHA256 != plan.EvidenceSHA256 || r.SourceCommit != SourceBaseCommit || r.CoreCreatedNS != plan.Native.CreatedNS || r.CoreImageSHA256 != plan.Native.ImageSHA256 || r.Reviewer == "" || strings.Contains(r.Reviewer, "owned_core_stop_builder") || r.Verdict != "ACCEPTED" || !validSHA(r.RootOperationScopeSHA256) {
		return errors.New("independent exact plan/root-scope review unavailable")
	}
	return nil
}
