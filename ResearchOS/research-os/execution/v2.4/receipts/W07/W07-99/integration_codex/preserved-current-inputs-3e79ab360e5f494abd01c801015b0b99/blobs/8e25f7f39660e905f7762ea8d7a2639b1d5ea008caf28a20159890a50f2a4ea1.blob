//go:build windows

package domain

import (
	"context"
	"database/sql"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"researchos.local/research-os/adapters/protectedstore"
	rt "researchos.local/research-os/adapters/runtime"
	"researchos.local/research-os/evaluation/evolution"
	"researchos.local/research-os/ops/supervisor"
)

const researchOSPermanentID = "aede0678-7308-43dc-b9f2-cfe3d90cfdfb"

type controlCurrentHost struct {
	mu       sync.Mutex
	roots    map[string]bool
	sessions map[string]*currentControlAuthority
}

var controlCurrentHosts sync.Map // *Service -> process-local trusted configuration

// ConfigureCurrentControlHost is a local startup capability. No request or
// public artifact may add a root. Reconfiguration after use is refused.
func (s *Service) ConfigureCurrentControlHost(approvedSourceRoots []string) error {
	if len(approvedSourceRoots) == 0 || len(approvedSourceRoots) > 2 {
		return fmt.Errorf("CONTROL_TRUSTED_SOURCE_ROOTS_REQUIRED")
	}
	h := &controlCurrentHost{roots: map[string]bool{}, sessions: map[string]*currentControlAuthority{}}
	for _, root := range approvedSourceRoots {
		abs, err := filepath.Abs(root)
		if err != nil || abs != filepath.Clean(root) {
			return fmt.Errorf("CONTROL_TRUSTED_SOURCE_CANONICAL")
		}
		real, err := filepath.EvalSymlinks(abs)
		if err != nil || real != abs {
			return fmt.Errorf("CONTROL_TRUSTED_SOURCE_REPARSE")
		}
		identityPath := filepath.Join(abs, "execution", "project_identity.json")
		realIdentity, err := filepath.EvalSymlinks(identityPath)
		if err != nil || realIdentity != identityPath {
			return fmt.Errorf("CONTROL_TRUSTED_SOURCE_IDENTITY_PATH")
		}
		raw, err := os.ReadFile(identityPath)
		if err != nil {
			return err
		}
		identity, err := Decode(raw)
		if err != nil || identity["project_id"] != researchOSPermanentID || identity["name"] != "ResearchOS" || identity["other_project_access"] != "NOT_AUTHORIZED" {
			return fmt.Errorf("CONTROL_TRUSTED_SOURCE_IDENTITY")
		}
		h.roots[strings.ToLower(abs)] = true
	}
	if _, loaded := controlCurrentHosts.LoadOrStore(s, h); loaded {
		return fmt.Errorf("CONTROL_TRUSTED_SOURCE_ALREADY_CONFIGURED")
	}
	return nil
}

type currentControlAuthority struct {
	mu                                                  sync.RWMutex
	s                                                   *Service
	lease                                               *rt.DataRootLease
	store                                               *protectedstore.CanaryStore
	id, project, cycle, ownerID                         string
	owner                                               evolution.ControlAuthorityOwner
	provenance                                          evolution.ControlBuildProvenance
	provenanceRef, stableRef, candidateRef, snapshotRef Object
	stableBytes, candidateBytes                         []byte
	binding                                             evolution.ControlBinding
	b0, g0                                              evolution.ControlPrivateSnapshot
	registered                                          bool
	frozen                                              *controlCurrentNames
	preparationDelta                                    []evolution.ControlGenerationDelta
	evaluating, evaluated                               bool
	observationRef                                      Object
	sealed                                              *evolution.ControlCurrentReply
	expires                                             time.Time
}

func (s *Service) currentControlSession(id string) (*currentControlAuthority, error) {
	v, ok := controlCurrentHosts.Load(s)
	if !ok {
		return nil, fmt.Errorf("CONTROL_CURRENT_HOST_UNCONFIGURED")
	}
	h := v.(*controlCurrentHost)
	h.mu.Lock()
	a := h.sessions[id]
	h.mu.Unlock()
	if a == nil || a.s != s || !a.expires.After(time.Now()) {
		return nil, fmt.Errorf("CONTROL_CURRENT_SESSION_EXPIRED")
	}
	return a, nil
}

func controlCurrentReply(a *currentControlAuthority, phase string) evolution.ControlCurrentReply {
	return evolution.ControlCurrentReply{Phase: phase, Purpose: evolution.ControlCurrentPurpose, Profile: evolution.ControlCurrentProfile, SessionID: a.id, B0Hash: a.b0.Generation, G0Hash: a.g0.Generation, OwnerMatches: a.owner.Qualified, OSQualified: false, Remaining: []string{"G2_CUTOVER_GENERATION_UNQUALIFIED", "W18_CURRENT_RESTORE_QUALIFICATION_REQUIRED", "SCM_INDEPENDENT_IDENTITIES_UNQUALIFIED", "POSITIVE_GAIN_NOT_PROVEN", "NORMAL_RELEASE_CLOSED"}}
}

// HandleCurrentControlFixture is reachable only through an inherited private
// host capability. Tokens are used in memory and never added to replies/proofs.
func (s *Service) HandleCurrentControlFixture(ctx context.Context, lease *rt.DataRootLease, req evolution.ControlCurrentRequest) (evolution.ControlCurrentReply, error) {
	var out evolution.ControlCurrentReply
	if lease == nil || !lease.Held() {
		return out, fmt.Errorf("CONTROL_CURRENT_ROOT_LEASE_REQUIRED")
	}
	if req.Phase == "SAMPLE" {
		return s.sampleCurrentControl(ctx, lease, req)
	}
	a, err := s.currentControlSession(req.SessionID)
	if err != nil {
		return out, err
	}
	if a.lease != lease {
		return out, fmt.Errorf("CONTROL_CURRENT_LEASE_INSTANCE_CHANGED")
	}
	switch req.Phase {
	case "REGISTER":
		return s.registerCurrentControl(ctx, a, req)
	case "FREEZE":
		return s.freezeCurrentControl(ctx, a, req)
	case "EVALUATE":
		return s.evaluateCurrentControl(ctx, a, req)
	case "SEAL":
		return s.sealCurrentControl(ctx, a, req)
	default:
		return out, fmt.Errorf("CONTROL_CURRENT_PHASE")
	}
}

func controlDatabasePath(tx *sql.Tx) (string, error) {
	rows, err := tx.Query("PRAGMA database_list")
	if err != nil {
		return "", err
	}
	defer rows.Close()
	path := ""
	for rows.Next() {
		var sequence int
		var name, file string
		if err = rows.Scan(&sequence, &name, &file); err != nil {
			return "", err
		}
		if name == "main" {
			path = filepath.Clean(file)
		} else if name != "temp" {
			return "", fmt.Errorf("CONTROL_ATTACHED_AUTHORITY_UNSUPPORTED")
		}
	}
	if err = rows.Err(); err != nil {
		return "", err
	}
	if !filepath.IsAbs(path) {
		return "", fmt.Errorf("CONTROL_CURRENT_FILE_DATABASE_REQUIRED")
	}
	return path, nil
}

func (a *currentControlAuthority) currentOwner(tx *sql.Tx) error {
	if !a.lease.Held() || a.lease.Root() != a.owner.Root {
		return fmt.Errorf("CONTROL_CURRENT_ROOT_LEASE_CHANGED")
	}
	path, err := controlDatabasePath(tx)
	if err != nil {
		return err
	}
	owner, err := supervisor.ObserveControlAuthorityOwner(a.lease.Root(), path, Str(a.stableRef, "content_hash"))
	if err != nil || Hash(owner) != Hash(a.owner) {
		return fmt.Errorf("CONTROL_CURRENT_OWNER_CHANGED")
	}
	if err = supervisor.VerifyControlBuildProvenance(a.stableBytes, a.provenance.Stable); err != nil {
		return err
	}
	return supervisor.VerifyControlBuildProvenance(a.candidateBytes, a.provenance.Candidate)
}

func (s *Service) sampleCurrentControl(ctx context.Context, lease *rt.DataRootLease, req evolution.ControlCurrentRequest) (evolution.ControlCurrentReply, error) {
	var out evolution.ControlCurrentReply
	configured, ok := controlCurrentHosts.Load(s)
	if !ok {
		return out, fmt.Errorf("CONTROL_CURRENT_HOST_UNCONFIGURED")
	}
	config := configured.(*controlCurrentHost)
	store, ok := s.Protected.(*protectedstore.CanaryStore)
	if !ok || s.protectedReady(ctx, "FIXTURE") != nil {
		return out, fmt.Errorf("CONTROL_CURRENT_PRIVATE_STORE_REQUIRED")
	}
	tx, err := s.DB.BeginTx(ctx, nil)
	if err != nil {
		return out, err
	}
	defer tx.Rollback()
	owner, err := authenticate(tx, req.OwnerToken)
	if err != nil || owner.DeviceID != "" || !owner.HasRole("OWNER") || !owner.Allowed(req.ProjectID, "", "", false) {
		return out, Fail(403, "FORBIDDEN", "current local owner required")
	}
	var count int
	if err = tx.QueryRow("SELECT count(*) FROM evolution_hosts WHERE project=?", req.ProjectID).Scan(&count); err != nil || count != 0 {
		return out, fmt.Errorf("CONTROL_CURRENT_REQUIRES_NEW_HOST")
	}
	sa, stable, err := s.evolutionBytes(tx, req.ProjectID, req.StableRef)
	if err != nil {
		return out, err
	}
	ca, candidate, err := s.evolutionBytes(tx, req.ProjectID, req.CandidateRef)
	if err != nil {
		return out, err
	}
	pa, raw, err := s.evolutionBytes(tx, req.ProjectID, req.ProvenanceRef)
	if err != nil {
		return out, err
	}
	if sa["kind"] != "CODE" || ca["kind"] != "CODE" || pa["kind"] != "REPORT" {
		return out, fmt.Errorf("CONTROL_CURRENT_BUILD_ARTIFACT_KIND")
	}
	var provenance evolution.ControlBuildProvenance
	if err = evolution.StrictControlJSON(raw, &provenance); err != nil || provenance.Schema != evolution.ControlCurrentProfile {
		return out, fmt.Errorf("CONTROL_CURRENT_PROVENANCE_SCHEMA")
	}
	// Verify root permission before inventory traversal. The report is evidence,
	// never the authority that grants filesystem access.
	for _, source := range []evolution.ControlSourceProvenance{provenance.Stable, provenance.Candidate} {
		if !config.roots[strings.ToLower(source.Root)] {
			return out, fmt.Errorf("CONTROL_CURRENT_SOURCE_ROOT_NOT_APPROVED")
		}
	}
	if err = supervisor.VerifyControlBuildProvenance(stable, provenance.Stable); err != nil {
		return out, err
	}
	if err = supervisor.VerifyControlBuildProvenance(candidate, provenance.Candidate); err != nil {
		return out, err
	}
	if err = currentControlSourceDifference(provenance); err != nil {
		return out, err
	}
	if err = supervisor.RebuildControlSource(ctx, provenance.Stable, stable); err != nil {
		return out, err
	}
	if Hash(provenance.Stable) != Hash(provenance.Candidate) || Digest(stable) != Digest(candidate) {
		if err = supervisor.RebuildControlSource(ctx, provenance.Candidate, candidate); err != nil {
			return out, err
		}
	}
	database, err := controlDatabasePath(tx)
	if err != nil {
		return out, err
	}
	identity, err := supervisor.ObserveControlAuthorityOwner(lease.Root(), database, Digest(stable))
	if err != nil {
		return out, err
	}
	if err = tx.Rollback(); err != nil {
		return out, err
	}
	config.mu.Lock()
	defer config.mu.Unlock()
	for _, existing := range config.sessions {
		if existing.project == req.ProjectID {
			return out, fmt.Errorf("CONTROL_CURRENT_SESSION_ALREADY_EXISTS")
		}
	}
	a := &currentControlAuthority{s: s, lease: lease, store: store, id: ID(), project: req.ProjectID, cycle: req.CycleID, ownerID: owner.ID, owner: identity, provenance: provenance, provenanceRef: copyObject(req.ProvenanceRef), stableRef: copyObject(req.StableRef), candidateRef: copyObject(req.CandidateRef), stableBytes: stable, candidateBytes: candidate, expires: time.Now().Add(15 * time.Minute)}
	snapshot, err := controlCurrentSnapshot(ctx, s.DB)
	if err != nil {
		return out, err
	}
	a.b0, err = controlSavePrivateSnapshot(ctx, store, a.project, a.id, "B0", snapshot)
	if err != nil {
		return out, err
	}
	bundle, err := prepareEvolutionControlBundle(ctx, snapshot, provenance.Stable.Root, a.project, a.cycle, true)
	if err != nil {
		return out, err
	}
	a.binding = bundle.Binding
	if a.binding.AuthorityGeneration != a.b0.Generation || a.binding.SourceSnapshotHash != a.b0.Hash {
		return out, fmt.Errorf("CONTROL_CURRENT_SAMPLE_BINDING")
	}
	tx, err = s.DB.BeginTx(ctx, nil)
	if err != nil {
		return out, err
	}
	defer tx.Rollback()
	if err = a.currentOwner(tx); err != nil {
		return out, err
	}
	currentOwner, err := authenticate(tx, req.OwnerToken)
	if err != nil || currentOwner.ID != owner.ID || currentOwner.DeviceID != "" || !currentOwner.HasRole("OWNER") || !currentOwner.Allowed(a.project, "", "", false) {
		return out, Fail(403, "FORBIDDEN", "current owner changed")
	}
	generation, err := evolution.ControlDatabaseHash(tx)
	if err != nil || generation != a.b0.Generation {
		return out, fmt.Errorf("CONTROL_CURRENT_SAMPLE_MOVED")
	}
	artifact, err := s.controlSealPublic(tx, currentOwner, a.project, "DATASET", evolution.Bytes(bundle))
	if err != nil {
		return out, err
	}
	a.snapshotRef = Ref(artifact, "Artifact")
	if err = tx.Commit(); err != nil {
		return out, err
	}
	config.sessions[a.id] = a
	out = controlCurrentReply(a, "SAMPLE")
	out.SnapshotRef, out.Binding = a.snapshotRef, &a.binding
	return out, nil
}

func currentControlSourceDifference(p evolution.ControlBuildProvenance) error {
	if p.Stable.Toolchain != p.Candidate.Toolchain || p.Stable.ModuleHash != p.Candidate.ModuleHash || len(p.Stable.Files) != len(p.Candidate.Files) {
		return fmt.Errorf("CONTROL_CURRENT_BUILD_ENVIRONMENT_CHANGED")
	}
	allowed := map[string]bool{"internal/domain/research.go": true, "internal/domain/research_close.go": true, "internal/domain/research_acceptance.go": true}
	for path, before := range p.Stable.Files {
		after, present := p.Candidate.Files[path]
		if !present || before != after && !allowed[path] {
			return fmt.Errorf("CONTROL_CURRENT_CANDIDATE_SOURCE_SCOPE")
		}
	}
	return nil
}

func (s *Service) controlSealPublic(tx *sql.Tx, p Principal, project, kind string, raw []byte) (Object, error) {
	u, err := s.upload(tx, p, project, raw)
	if err != nil {
		return nil, err
	}
	b := Object{"run_id": nil, "kind": kind, "evidence_kind": "GENERATED", "measurement_mode": "FIXTURE", "content_hash": u["content_hash"], "storage_key": u["storage_key"], "media_type": "application/json", "byte_size": len(raw), "input_refs": Empty(), "source_refs": Empty(), "produced_by": p.ID, "access_class": "PROJECT"}
	if err = s.Contracts.Validate("CreateArtifactRequest", b); err != nil {
		return nil, err
	}
	a, err := s.seal(tx, p, project, b)
	if err != nil {
		return nil, err
	}
	return a, s.event(tx, project, "Artifact", a, p.ID, ID(), "PROJECT_UPDATED")
}

func (s *Service) registerCurrentControl(ctx context.Context, a *currentControlAuthority, req evolution.ControlCurrentRequest) (evolution.ControlCurrentReply, error) {
	a.mu.Lock()
	defer a.mu.Unlock()
	var out evolution.ControlCurrentReply
	if a.registered || a.frozen != nil {
		return out, fmt.Errorf("CONTROL_CURRENT_REGISTRATION_SINGLE_USE")
	}
	tx, err := s.DB.BeginTx(ctx, nil)
	if err != nil {
		return out, err
	}
	if err = a.currentOwner(tx); err == nil {
		var release Principal
		release, err = evolutionCurrentPrincipal(tx, req.ReleasePrincipal)
		if err == nil && (release.DeviceID != "" || !release.HasRole("RELEASE_SERVICE") || !release.HasRole("SCHEDULER") || !release.Allowed(a.project, "", "", false)) {
			err = Fail(403, "FORBIDDEN", "current local release principal required")
		}
	}
	tx.Rollback()
	if err != nil {
		return out, err
	}
	registration := &controlHostRegistration{SnapshotRef: a.snapshotRef, StableSourceHash: a.provenance.Stable.InventoryHash, Current: Object{"purpose": evolution.ControlCurrentPurpose, "profile": evolution.ControlCurrentProfile, "session_id": a.id, "b0_hash": a.b0.Generation, "owner_hash": Hash(a.owner), "provenance_ref": a.provenanceRef}}
	if err = s.registerEvolutionFixtureProfile(ctx, a.project, req.SupervisorID, req.ReleasePrincipal, req.HostRoot, a.stableRef, req.SuiteRef, req.RollbackRef, false, registration); err != nil {
		return out, err
	}
	if err = s.RegisterEvolutionBuild(ctx, a.project, a.candidateRef, req.ManifestRef, a.provenance.Candidate.InventoryHash); err != nil {
		return out, err
	}
	a.registered = true
	return controlCurrentReply(a, "REGISTER"), nil
}
