package evolution

// This profile proves current authority for the bounded same-user fixture. It
// does not grant SCM/LIVE release authority or change the business gain policy.
const ControlCurrentProfile = "control-current-authority-fixture-v1"
const ControlCurrentPurpose = "CURRENT_CONTROL_EVALUATION"

type ControlCurrentRequest struct {
	Phase            string         `json:"phase"`
	ProjectID        string         `json:"project_id,omitempty"`
	CycleID          string         `json:"cycle_id,omitempty"`
	SessionID        string         `json:"session_id,omitempty"`
	OwnerToken       string         `json:"owner_token,omitempty"`
	VerifierToken    string         `json:"verifier_token,omitempty"`
	WorkerToken      string         `json:"worker_token,omitempty"`
	ReleaseToken     string         `json:"release_token,omitempty"`
	Lease            map[string]any `json:"lease,omitempty"`
	StableRef        map[string]any `json:"stable_ref,omitempty"`
	CandidateRef     map[string]any `json:"candidate_ref,omitempty"`
	ProvenanceRef    map[string]any `json:"provenance_ref,omitempty"`
	SupervisorID     string         `json:"supervisor_id,omitempty"`
	ReleasePrincipal string         `json:"release_principal,omitempty"`
	HostRoot         string         `json:"host_root,omitempty"`
	SuiteRef         map[string]any `json:"suite_ref,omitempty"`
	RollbackRef      map[string]any `json:"rollback_ref,omitempty"`
	ManifestRef      map[string]any `json:"manifest_ref,omitempty"`
	CandidateID      string         `json:"candidate_id,omitempty"`
	TaskID           string         `json:"task_id,omitempty"`
	RunID            string         `json:"run_id,omitempty"`
	AcceptanceID     string         `json:"acceptance_id,omitempty"`
}

type ControlSourceProvenance struct {
	Root          string            `json:"root"`
	Commit        string            `json:"commit"`
	Modified      bool              `json:"modified"`
	Toolchain     string            `json:"toolchain"`
	ModuleHash    string            `json:"module_hash"`
	InventoryHash string            `json:"inventory_hash"`
	Files         map[string]string `json:"files"`
}

type ControlBuildProvenance struct {
	Schema    string                  `json:"schema"`
	Stable    ControlSourceProvenance `json:"stable"`
	Candidate ControlSourceProvenance `json:"candidate"`
}

type ControlAuthorityOwner struct {
	Root         string `json:"root"`
	RootIdentity string `json:"root_identity"`
	Database     string `json:"database"`
	DatabaseID   string `json:"database_identity"`
	PID          uint32 `json:"pid"`
	CreatedNS    int64  `json:"created_ns"`
	Image        string `json:"image"`
	ImageHash    string `json:"image_hash"`
	StableHash   string `json:"stable_hash"`
	Qualified    bool   `json:"qualified_owner_binding"`
}

// Snapshot pieces are private-store descriptors, never uploaded_content or
// ordinary temporary files. The whole original byte hash binds their order.
type ControlPrivatePart struct {
	Ticket string `json:"ticket"`
	Hash   string `json:"hash"`
	Size   int64  `json:"size"`
}
type ControlPrivateSnapshot struct {
	Purpose    string               `json:"purpose"`
	Stage      string               `json:"stage"`
	SessionID  string               `json:"session_id"`
	Hash       string               `json:"hash"`
	Size       int64                `json:"size"`
	Generation string               `json:"generation"`
	Parts      []ControlPrivatePart `json:"parts"`
}

type ControlGenerationDelta struct {
	Table      string `json:"table"`
	KeyHash    string `json:"key_hash"`
	BeforeHash string `json:"before_hash"`
	AfterHash  string `json:"after_hash"`
	Reason     string `json:"reason"`
}

type ControlCurrentReply struct {
	Phase          string          `json:"phase"`
	Purpose        string          `json:"purpose"`
	Profile        string          `json:"profile"`
	SessionID      string          `json:"session_id"`
	SnapshotRef    map[string]any  `json:"snapshot_ref,omitempty"`
	Binding        *ControlBinding `json:"binding,omitempty"`
	B0Hash         string          `json:"b0_hash,omitempty"`
	G0Hash         string          `json:"g0_hash,omitempty"`
	G1Hash         string          `json:"g1_hash,omitempty"`
	DeltaHash      string          `json:"delta_hash,omitempty"`
	ProofHash      string          `json:"proof_hash,omitempty"`
	ProofRef       map[string]any  `json:"proof_ref,omitempty"`
	ObservationRef map[string]any  `json:"observation_ref,omitempty"`
	Current        bool            `json:"current"`
	OwnerMatches   bool            `json:"owner_matches"`
	OSQualified    bool            `json:"os_service_qualified"`
	Summary        map[string]any  `json:"summary,omitempty"`
	Remaining      []string        `json:"remaining"`
}
