//go:build windows

package ownedcorestop

import (
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"researchos.local/research-os/internal/host"
	"researchos.local/research-os/internal/store"
)

const proofSchema = "researchos.owned-core-stop-independent-evidence.v1"
const planReviewSchema = "researchos.owned-core-stop-independent-plan-review.v1"
const grantAuthoritySchema = "researchos.owned-core-stop-authority-document.v1"
const historicalManifestSchema = "researchos.owned-core-stop-historical-manifest.v1"

var proofKinds = []string{"f01_ready", "retained_window", "native_entry_gates", "worker_native_exit", "verifier_native_exit", "effect_census", "independent_evidence_review"}

type grantAuthorityDocument struct {
	Schema                    string                           `json:"schema"`
	Role                      string                           `json:"role"`
	OperationID               string                           `json:"operation_id"`
	Action                    string                           `json:"action"`
	Subject                   store.OwnedStopSubject           `json:"subject"`
	Native                    grantNativeIdentity              `json:"native"`
	Host                      host.OwnedCoreStopPublicIdentity `json:"host"`
	OperationDir              grantFileIdentity                `json:"operation_dir"`
	HistoricalManifestSHA256  string                           `json:"historical_manifest_sha256"`
	PlanSHA256                string                           `json:"plan_sha256,omitempty"`
	PreflightManifestSHA256   string                           `json:"preflight_manifest_sha256,omitempty"`
	PreflightGrantSHA256      string                           `json:"preflight_grant_sha256,omitempty"`
	PreflightExecutableSHA256 string                           `json:"preflight_executable_sha256,omitempty"`
	Reviewer                  string                           `json:"reviewer"`
	Verdict                   string                           `json:"verdict"`
}

type historicalManifest struct {
	Schema      string        `json:"schema"`
	OperationID string        `json:"operation_id"`
	Evidence    []EvidenceRef `json:"evidence"`
}

func decodeCanonicalAuthority(raw []byte, v any) error {
	return strictJSON(raw, v)
}

func validateAuthorityDocument(d grantAuthorityDocument, g operationGrant, role, action string) error {
	if d.Schema != grantAuthoritySchema || d.Role != role || d.OperationID != g.OperationID || d.Action != action || d.Subject != g.Subject || d.Native != g.Native || d.Host != g.Host || d.OperationDir != g.OperationDir || d.HistoricalManifestSHA256 != g.HistoricalManifest.SHA256 || d.Reviewer == "" || strings.Contains(d.Reviewer, "owned_core_stop_builder") || d.Verdict != "ACCEPTED" {
		return errors.New("authority document semantics differ")
	}
	if action == "preflight" {
		if d.PlanSHA256 != "" || d.PreflightManifestSHA256 != "" || d.PreflightGrantSHA256 != "" || d.PreflightExecutableSHA256 != "" {
			return errors.New("preflight authority refers to future output")
		}
	} else if d.PlanSHA256 != g.PlanSHA256 || d.PreflightManifestSHA256 != g.PreflightManifestSHA256 || d.PreflightGrantSHA256 != g.PreflightGrantSHA256 || d.PreflightExecutableSHA256 != g.PreflightExecutableSHA256 {
		return errors.New("stop authority predecessor differs")
	}
	return nil
}

func validateHistoricalManifest(g operationGrant, d *heldDocuments, evidence []EvidenceRef) error {
	raw, err := d.read(g.HistoricalManifest, 128<<10)
	if err != nil {
		return err
	}
	var m historicalManifest
	if err = decodeCanonicalAuthority(raw, &m); err != nil {
		return err
	}
	if m.Schema != historicalManifestSchema || m.OperationID != g.OperationID || len(m.Evidence) != len(proofKinds) || len(evidence) != len(proofKinds) {
		return errors.New("historical manifest identity/count")
	}
	for i, k := range proofKinds {
		if m.Evidence[i] != evidence[i] || evidence[i].Kind != k || !validSHA(evidence[i].SHA256) {
			return errors.New("historical manifest class/order/binding")
		}
	}
	return nil
}

func validatePreflightAuthority(g operationGrant, d *heldDocuments, in Input) error {
	if err := validateHistoricalManifest(g, d, in.Evidence); err != nil {
		return err
	}
	for _, item := range []struct {
		ref  grantDocument
		role string
	}{{g.PreflightScope, "root_preflight_scope"}, {g.PreflightReview, "independent_preflight_review"}} {
		if err := verifierPath(in.SourceRepository, item.ref.Path); err != nil {
			return err
		}
		raw, err := d.read(item.ref, 128<<10)
		if err != nil {
			return err
		}
		var doc grantAuthorityDocument
		if err = decodeCanonicalAuthority(raw, &doc); err != nil {
			return err
		}
		if err = validateAuthorityDocument(doc, g, item.role, "preflight"); err != nil {
			return err
		}
	}
	return nil
}

func validateStopAuthority(g operationGrant, d *heldDocuments, p Plan, planSHA string) error {
	if err := validateHistoricalManifest(g, d, p.Input.Evidence); err != nil {
		return err
	}
	for _, item := range []struct {
		ref  grantDocument
		role string
	}{{g.StopReview, "independent_stop_review"}, {g.RootOperationScope, "root_operation_scope"}} {
		if err := verifierPath(p.Input.SourceRepository, item.ref.Path); err != nil {
			return err
		}
		raw, err := d.read(item.ref, 128<<10)
		if err != nil {
			return err
		}
		var doc grantAuthorityDocument
		if err = decodeCanonicalAuthority(raw, &doc); err != nil {
			return err
		}
		if err = validateAuthorityDocument(doc, g, item.role, "commit"); err != nil {
			return err
		}
	}
	if p.Input.PlanReviewPath != g.StopReview.Path || planSHA != g.PlanSHA256 {
		return errors.New("plan review path/hash differs")
	}
	return nil
}

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

func validateHistoricalEvidence(plan Plan, held ...*heldDocuments) (string, []string) {
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
		var receipt historicalEvidence
		var err error
		if len(held) > 0 && held[0] != nil {
			if err = verifierPath(plan.Input.SourceRepository, ref.Path); err == nil {
				var raw []byte
				raw, err = held[0].read(grantDocument{Path: ref.Path, SHA256: ref.SHA256}, 128<<10)
				if err == nil {
					err = decodeCanonicalAuthority(raw, &receipt)
				}
				if err == nil && (receipt.Schema != proofSchema || receipt.Kind != ref.Kind || receipt.Reviewer == "" || strings.Contains(receipt.Reviewer, "owned_core_stop_builder")) {
					err = errors.New("independent evidence identity invalid")
				}
			}
		} else {
			receipt, err = readEvidence(plan.Input.SourceRepository, ref)
		}
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
