package domain

import (
	"bytes"
	"encoding/json"
	"fmt"
	"strconv"
	"strings"
	"unicode/utf8"

	"researchos.local/research-os/internal/canonical"
)

const codingDeliveryBindingSchema = "researchos.coding-delivery-binding.v1"
const codingDeliveryBindingVersion = 1
const codingDeliveryBindingMaxBytes = 64 << 10

// These inputs must eventually be read from the original trusted business
// origin. Constructing this value or its hash does not authenticate that origin.
// Permission, project, storage refs, new object IDs and approval are deliberately
// absent: none may create a fresh causal lineage for the same original work.
type codingDeliveryOriginalOrigin struct {
	OriginalProblemAnchor    string `json:"original_problem_anchor"`
	RequirementContentHash   string `json:"requirement_content_hash"`
	BusinessInputContentHash string `json:"business_input_content_hash"`
	SuiteRef                 string `json:"suite_ref"`
	SuiteHash                string `json:"suite_hash"`
}

func codingDeliveryBusinessAnchor(origin codingDeliveryOriginalOrigin) (string, error) {
	if !codingDeliveryText(origin.OriginalProblemAnchor) || !codingDeliveryText(origin.SuiteRef) ||
		!codingDeliveryHash(origin.RequirementContentHash) || !codingDeliveryHash(origin.BusinessInputContentHash) || !codingDeliveryHash(origin.SuiteHash) {
		return "", fmt.Errorf("CODING_DELIVERY_ORIGINAL_ORIGIN_REQUIRED")
	}
	return Hash(Object{"schema": "researchos.coding-delivery-original-origin.v1", "origin": origin}), nil
}

// Permission snapshots are required provenance, never current authority or an
// authentication credential. Qualified approval and lineage have database-wide
// uniqueness; project and principal do not namespace either claim.
type codingDeliveryBindingIdentity struct {
	BindingSchema     string `json:"binding_schema"`
	SchemaVersion     int    `json:"schema_version"`
	Project           string `json:"project"`
	GoalID            string `json:"goal_id"`
	TaskID            string `json:"task_id"`
	ApprovalIssuerRef string `json:"approval_issuer_ref"`
	ApprovalRef       string `json:"approval_ref"`
	LineageIssuerRef  string `json:"lineage_issuer_ref"`
	BusinessAnchor    string `json:"business_anchor"`
	OwnerPrincipal    string `json:"owner_principal"`
	OwnerRoot         string `json:"owner_root"`
	OwnerHost         string `json:"owner_host"`
	TaskContractHash  string `json:"task_contract_hash"`
	GoalContractHash  string `json:"goal_contract_hash"`
}

type codingDeliveryBinding struct {
	codingDeliveryBindingIdentity
	OriginalProblemAnchor    string `json:"original_problem_anchor"`
	RequirementContentHash   string `json:"requirement_content_hash"`
	BusinessInputContentHash string `json:"business_input_content_hash"`
	ParentRef                string `json:"parent_ref"`
	ParentConfirmationHash   string `json:"parent_confirmation_hash"`
	CreationMethod           string `json:"creation_method"`
	ClientID                 string `json:"client_id"`
	CommandID                string `json:"command_id"`
	RequestHash              string `json:"request_hash"`
	SessionRef               string `json:"session_ref"`
	WorkspaceRef             string `json:"workspace_ref"`
	WorkspaceHash            string `json:"workspace_hash"`
	ProfileRef               string `json:"profile_ref"`
	ProfileHash              string `json:"profile_hash"`
	PolicyRef                string `json:"policy_ref"`
	PolicyHash               string `json:"policy_hash"`
	SuiteRef                 string `json:"suite_ref"`
	SuiteHash                string `json:"suite_hash"`
	ApprovedPlanRef          string `json:"approved_plan_ref"`
	ApprovedPlanHash         string `json:"approved_plan_hash"`
	RequirementRefsRef       string `json:"requirement_refs_ref"`
	RequirementRefsHash      string `json:"requirement_refs_hash"`
	InputRefsRef             string `json:"input_refs_ref"`
	InputRefsHash            string `json:"input_refs_hash"`
	OriginProblemID          string `json:"origin_problem_id"`
	CandidateID              string `json:"candidate_id"`
	NoProgressRef            string `json:"no_progress_ref"`
	NoProgressInputKey       string `json:"no_progress_input_key"`
	// Decimal strings retain the entire positive int64 domain through JCS. These
	// are creation snapshots, not a Run or a current lease/epoch authorization.
	CreationWriterEpoch     string `json:"creation_writer_epoch"`
	CreationSessionRevision string `json:"creation_session_revision"`
}

func codingDeliveryText(v string) bool {
	return utf8.ValidString(v) && strings.TrimSpace(v) != "" && !strings.ContainsRune(v, 0)
}

func codingDeliveryHash(v string) bool {
	if len(v) != 71 || !strings.HasPrefix(v, "sha256:") {
		return false
	}
	for _, c := range v[7:] {
		if !(c >= '0' && c <= '9' || c >= 'a' && c <= 'f') {
			return false
		}
	}
	return true
}

func (b codingDeliveryBinding) origin() codingDeliveryOriginalOrigin {
	return codingDeliveryOriginalOrigin{b.OriginalProblemAnchor, b.RequirementContentHash, b.BusinessInputContentHash, b.SuiteRef, b.SuiteHash}
}

func (b codingDeliveryBinding) validate() error {
	bad := func() error { return fmt.Errorf("CODING_DELIVERY_CLOSED_BINDING_REQUIRED") }
	if b.BindingSchema != codingDeliveryBindingSchema || b.SchemaVersion != codingDeliveryBindingVersion || b.CreationMethod != "goal.start" {
		return bad()
	}
	// Check original typed strings before json.Marshal, which substitutes invalid
	// UTF-8. Persisting substituted provenance would not be an exact binding.
	for _, value := range []string{
		b.BindingSchema, b.Project, b.GoalID, b.TaskID, b.ApprovalIssuerRef, b.ApprovalRef, b.LineageIssuerRef, b.BusinessAnchor,
		b.OwnerPrincipal, b.OwnerRoot, b.OwnerHost, b.TaskContractHash, b.GoalContractHash,
		b.OriginalProblemAnchor, b.RequirementContentHash, b.BusinessInputContentHash, b.ParentRef, b.ParentConfirmationHash,
		b.CreationMethod, b.ClientID, b.CommandID, b.RequestHash, b.SessionRef, b.WorkspaceRef, b.WorkspaceHash,
		b.ProfileRef, b.ProfileHash, b.PolicyRef, b.PolicyHash, b.SuiteRef, b.SuiteHash, b.ApprovedPlanRef, b.ApprovedPlanHash,
		b.RequirementRefsRef, b.RequirementRefsHash, b.InputRefsRef, b.InputRefsHash, b.OriginProblemID, b.CandidateID,
		b.NoProgressRef, b.NoProgressInputKey, b.CreationWriterEpoch, b.CreationSessionRevision,
	} {
		if !codingDeliveryText(value) {
			return bad()
		}
	}
	for _, v := range []string{b.BusinessAnchor, b.TaskContractHash, b.GoalContractHash, b.RequirementContentHash, b.BusinessInputContentHash,
		b.ParentConfirmationHash, b.RequestHash, b.WorkspaceHash, b.ProfileHash, b.PolicyHash, b.SuiteHash, b.ApprovedPlanHash,
		b.RequirementRefsHash, b.InputRefsHash, b.NoProgressInputKey} {
		if !codingDeliveryHash(v) {
			return bad()
		}
	}
	if b.TaskContractHash == b.GoalContractHash {
		return bad()
	}
	for _, value := range []string{b.CreationWriterEpoch, b.CreationSessionRevision} {
		n, err := strconv.ParseInt(value, 10, 64)
		if err != nil || n < 1 || strconv.FormatInt(n, 10) != value {
			return bad()
		}
	}
	anchor, err := codingDeliveryBusinessAnchor(b.origin())
	if err != nil || anchor != b.BusinessAnchor {
		return bad()
	}
	raw, err := json.Marshal(b)
	if err != nil || len(raw) > codingDeliveryBindingMaxBytes {
		return bad()
	}
	return nil
}

func codingDeliveryBindingBytes(b codingDeliveryBinding) ([]byte, string, error) {
	if err := b.validate(); err != nil {
		return nil, "", err
	}
	raw, err := canonical.JSON(Bytes(b))
	if err != nil {
		return nil, "", err
	}
	// This is the existing domain Hash chain: Marshal -> canonical.JSON -> Digest.
	return raw, Hash(b), nil
}

func decodeCodingDeliveryBinding(raw []byte) (codingDeliveryBinding, error) {
	var b codingDeliveryBinding
	if len(raw) == 0 || len(raw) > codingDeliveryBindingMaxBytes {
		return b, fmt.Errorf("CODING_DELIVERY_BINDING_BYTES")
	}
	strict, err := canonical.JSON(raw)
	if err != nil || !bytes.Equal(raw, strict) {
		return b, fmt.Errorf("CODING_DELIVERY_CANONICAL_BINDING_REQUIRED")
	}
	var fields, names map[string]json.RawMessage
	if json.Unmarshal(raw, &fields) != nil || fields == nil || json.Unmarshal(Bytes(b), &names) != nil || len(fields) != len(names) {
		return b, fmt.Errorf("CODING_DELIVERY_CLOSED_BINDING_REQUIRED")
	}
	// Check exact names before struct decoding, which otherwise accepts case
	// aliases. canonical.JSON has already rejected duplicate names/invalid UTF-8.
	for name := range fields {
		if _, ok := names[name]; !ok {
			return b, fmt.Errorf("CODING_DELIVERY_UNKNOWN_BINDING_FIELD")
		}
	}
	if err = json.Unmarshal(raw, &b); err != nil {
		return b, err
	}
	if err = b.validate(); err != nil {
		return b, err
	}
	return b, nil
}

// All expected provenance must be supplied explicitly by a future trusted Host
// integration. Equality here proves integrity only, not the provenance's truth,
// current Owner/root/Host authority, approval consumption or business acceptance.
func codingDeliveryBindingContext(b, expected codingDeliveryBinding) error {
	if err := expected.validate(); err != nil {
		return err
	}
	if err := b.validate(); err != nil {
		return err
	}
	if b != expected {
		return fmt.Errorf("CODING_DELIVERY_EXPECTED_CONTEXT_MISMATCH")
	}
	return nil
}
