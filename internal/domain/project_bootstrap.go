package domain

// W04-01 · project.bootstrap (22_CLIENT_INTERFACE_DETAILS §2.3 step 2 and §5, 15_NEW_PROJECT_WORKFLOW §2).
//
// The order the contract pins is: trusted本机 bootstrap -> native.workspace.choose ->
// workspace.register -> project.bootstrap. By the time this runs the directory is already an
// authorized_workspace_ref, so the only identity question left is "does a ResearchOS project
// already own this canonical directory?". A changed alias for the same directory reuses the
// original project; a second directory that happens to share a display name gets its own project
// and never sees the first one's materials.
//
// What this card writes: project identity, the LOCAL_INVENTORY artifact and the stage records.
// What it deliberately does NOT claim: RESEARCH, REUSE_DECISION and IMPLEMENTATION are recorded as
// NOT_STARTED (W08 owns them), and bootstrap_task_id points at the durable LOCAL_INVENTORY stage
// record rather than at a fabricated Goal/Task chain, because creating those here would mean
// pretending an initialisation that has not happened.

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"strings"
)

// LocalInventoryEntry is one capability observation. The four statuses are the contract's: an
// unreadable directory is NOT_ACCESSIBLE, never an empty one, and something never looked at is
// NOT_CHECKED, never "absent".
type LocalInventoryEntry struct {
	Capability     string
	LocationRef    string
	Status         string
	RevisionOrHash *string
	Notes          string
}

// LocalInventoryFileFailure records a partial parse failure per file, which is what lets a later
// reader see exactly what could not be understood instead of a silently shortened inventory.
type LocalInventoryFileFailure struct {
	Path    string
	Reason  string
	Encoded bool
}

// LocalInventoryScan is the adapter's answer for one authorized directory.
type LocalInventoryScan struct {
	Environment string
	Entries     []LocalInventoryEntry
	Failures    []LocalInventoryFileFailure
}

// LocalInventoryScanner walks exactly one authorized directory. The domain passes the canonical
// path it resolved from the binding, never a client-supplied one, and refuses a scan whose result
// claims anything outside that root.
type LocalInventoryScanner interface {
	Scan(ctx context.Context, realPath string) (LocalInventoryScan, error)
}

// BootstrapProjectInput is the published BootstrapPayload plus the envelope identity the host
// needs to make a duplicate delivery return the original answer.
type BootstrapProjectInput struct {
	AuthorizedWorkspaceRef string
	DisplayName            string
	ClientID               string
	CommandID              string
	// MeasurementMode is FIXTURE or LIVE. A qualification run may not stamp its own scan as LIVE
	// evidence about a real user machine, so an unrecognised value falls back to FIXTURE.
	MeasurementMode string
}

const (
	inventoryDefLocal     = "LocalInventoryPayload"
	inventoryDefBootstrap = "BootstrapResult"
	inventoryMediaType    = "application/json"
)

// BootstrapProject creates or continues the project identity behind an authorized workspace and
// records the local inventory before any external query happens.
func (s *Service) BootstrapProject(ctx context.Context, p Principal, a WorkspaceAuthority, g DefGrader, scan LocalInventoryScanner, in BootstrapProjectInput) (Object, error) {
	if a == nil || g == nil || scan == nil {
		return nil, Fail(503, "RESOURCE_UNAVAILABLE", "workspace authority, contract grader and inventory scanner are required")
	}
	if strings.TrimSpace(in.AuthorizedWorkspaceRef) == "" || strings.TrimSpace(in.CommandID) == "" {
		return nil, Fail(400, "INVALID_REQUEST", "authorized_workspace_ref and command_id are required")
	}
	if looksLikePath(in.AuthorizedWorkspaceRef) {
		return nil, Fail(403, "FORBIDDEN", "an authorized workspace reference is not a filesystem path")
	}
	mode := strings.ToUpper(strings.TrimSpace(in.MeasurementMode))
	if mode != "LIVE" {
		mode = "FIXTURE"
	}

	tx, err := s.DB.BeginTx(ctx, nil)
	if err != nil {
		return nil, err
	}
	defer tx.Rollback()

	// A command id belongs to the principal that first used it. Proving that before any workspace
	// right is consulted means a colliding replay is refused as a collision, not as a generic
	// authorisation failure that would hide it.
	if owner, e := s.replayOwner(ctx, tx, in.CommandID); e == nil && owner != "" && owner != p.ID {
		return nil, Fail(409, "COMMAND_ID_CONFLICT", "this command id was already used by another principal")
	} else if e != nil && !errors.Is(e, sql.ErrNoRows) {
		return nil, e
	}

	binding, err := s.authorisedBinding(ctx, tx, p, in.AuthorizedWorkspaceRef)
	if err != nil {
		return nil, err
	}
	if err := a.ConfirmPath(ctx, binding.RealPath, "READ_ONLY"); err != nil {
		return nil, typedFromAuthority(err)
	}

	// A redelivery of the same command answers from the durable records instead of scanning again:
	// no second project, no second artifact, no second revision.
	if replay, e := s.bootstrapReplay(ctx, tx, p.ID, in.CommandID, binding); e == nil && replay != nil {
		if err := tx.Commit(); err != nil {
			return nil, err
		}
		return replay, nil
	} else if e != nil && !errors.Is(e, sql.ErrNoRows) {
		return nil, e
	}

	// Continuation: the same canonical directory already owns a project, whether it was reached
	// through this reference or an alias registered later.
	project := ""
	if binding.ProjectID != nil {
		project = *binding.ProjectID
	} else if twin, e := s.bindingByRealPath(ctx, tx, p.ID, binding.RealPath); e == nil && twin != nil && twin.ProjectID != nil {
		project = *twin.ProjectID
		binding = twin
	}
	if project != "" {
		var alive int
		if e := tx.QueryRowContext(ctx, `SELECT count(*) FROM domain_objects WHERE project=? AND kind='ProjectProfile' AND id=?`, project, project).Scan(&alive); e != nil {
			return nil, e
		}
		if alive != 1 {
			return nil, Fail(410, "NOT_FOUND", "the recorded project identity no longer exists")
		}
	}

	profile := Object{}
	if project == "" {
		body := Object{"name": displayNameOr(in.DisplayName, binding), "intent": "continue the local research project held in the authorized workspace " + binding.AuthorizedRef,
			"facts": Empty(), "accepted_scope": []any{binding.AuthorizedRef}, "constraints": []any{"local inventory precedes any external query"},
			"source_configs": Empty(), "source_document_refs": Empty(), "read_snapshot_ids": Empty()}
		created, e := s.createProject(tx, p, body)
		if e != nil {
			return nil, e
		}
		project = Str(created, "id")
		profile = created
		// client_sessions mapping (W03-01) requires a Project row for the id; createProject's own
		// kinds are ProjectProfile and ProjectState, so the identity row is written here with the
		// same append-only bookkeeping.
		if e = s.putOpaque(ctx, tx, project, "Project", project, Object{"id": project, "project_id": project,
			"revision": int64(1), "created_at": Now(), "updated_at": Now(), "name": Str(created, "name"),
			"authorized_workspace_ref": binding.AuthorizedRef, "real_path": binding.RealPath}); e != nil {
			return nil, e
		}
	} else {
		loaded, e := load(tx, project, "ProjectProfile", project)
		if e != nil {
			return nil, e
		}
		profile = loaded
		if _, e = tx.ExecContext(ctx, `INSERT OR IGNORE INTO auth_grants(principal,project) VALUES(?,?)`, p.ID, project); e != nil {
			return nil, e
		}
	}

	entries, payload, failures, err := s.collectInventory(ctx, scan, project, binding, mode)
	if err != nil {
		return nil, err
	}
	if err := g.ValidateDef(inventoryDefLocal, payload); err != nil {
		return nil, Fail(422, "CONTENT_HASH_MISMATCH", "local inventory violates the published definition: "+err.Error())
	}

	raw := Bytes(payload)
	upload, err := s.upload(tx, p, project, raw)
	if err != nil {
		return nil, err
	}
	artifact, err := s.seal(tx, p, project, Object{"run_id": nil, "kind": "MANIFEST", "evidence_kind": "OBSERVED",
		"measurement_mode": mode, "content_hash": upload["content_hash"], "storage_key": upload["storage_key"],
		"media_type": inventoryMediaType, "byte_size": len(raw), "input_refs": Empty(), "source_refs": Empty(),
		"produced_by": p.ID, "access_class": "PROJECT"})
	if err != nil {
		return nil, err
	}

	status := StageCompleted
	if len(failures) > 0 && len(entries) > 0 {
		status = StagePartial
	} else if len(entries) == 0 {
		status = StageFailed
	}
	stageID := "stage-" + project + "-local-inventory"
	stageRev, e := s.nextRevision(ctx, tx, project, KindBootstrapStage, stageID)
	if e != nil {
		return nil, e
	}
	stage := &BootstrapStage{ID: stageID, ProjectID: project, Stage: StageLocalInventory, Status: status,
		InventoryRef: refID(artifact), Failures: failuresList(failures), ObservedAt: Str(payload, "observed_at"), Revision: stageRev}
	if e := s.putOpaque(ctx, tx, project, KindBootstrapStage, stageID, stage.StageRecord()); e != nil {
		return nil, e
	}
	// The stages this card must not finish are written explicitly, so an absent row can never be
	// read as "nothing left to research". They are created once and never silently promoted.
	for _, later := range []string{StageResearch, StageReuseDecision, StageImplementation} {
		id := "stage-" + project + "-" + strings.ToLower(later)
		if e := s.ensureStage(ctx, tx, project, id, later, Str(payload, "observed_at")); e != nil {
			return nil, e
		}
	}

	// Every observation is a new sealed artifact: the payload carries observed_at, so re-scanning
	// the same tree is by definition a different content hash and the seal path cannot dedupe it.
	// The earlier artifact stays as history rather than being rewritten (see the stage record, which
	// IS a single refreshed row).
	// The first bootstrap binds the identity to the reference; a later one on the same reference
	// must not churn the binding revision, so continuation is recognised before it is written.
	if binding.ProjectID == nil {
		projectID := project
		if e := s.putOpaque(ctx, tx, "", KindWorkspaceBinding, binding.AuthorizedRef, binding.bindProject(projectID)); e != nil {
			return nil, e
		}
	}
	record := Object{"project_id": project, "command_id": in.CommandID, "principal_id": p.ID,
		"stage_id": stageID, "artifact_id": Str(artifact, "id"), "revision": int64(1)}
	if e := s.putOpaque(ctx, tx, project, "BootstrapReplay", "replay-"+in.CommandID, record); e != nil {
		return nil, e
	}

	reply := Object{"project_id": project, "workspace": binding.Reply(),
		"project_profile_ref": Ref(profile, "ProjectProfile"), "inventory_artifact_ref": Ref(artifact, "Artifact"),
		"bootstrap_task_id": stageID, "bootstrap_run_id": nil}
	if err := g.ValidateDef(inventoryDefBootstrap, reply); err != nil {
		return nil, Fail(422, "CONTENT_HASH_MISMATCH", "bootstrap result violates the published definition: "+err.Error())
	}
	if err := tx.Commit(); err != nil {
		return nil, err
	}
	return reply, nil
}

// collectInventory asks the adapter about exactly the bound directory and refuses a result that
// reports anything outside it, so a scanner bug cannot turn into a wider authorisation.
func (s *Service) collectInventory(ctx context.Context, scan LocalInventoryScanner, project string, b *WorkspaceBinding, mode string) ([]LocalInventoryEntry, Object, []LocalInventoryFileFailure, error) {
	res, err := scan.Scan(ctx, b.RealPath)
	if err != nil {
		return nil, nil, nil, typedFromAuthority(err)
	}
	entries := []LocalInventoryEntry{}
	list := []any{}
	for _, e := range res.Entries {
		if e.Status != "FOUND" && e.Status != "NOT_FOUND" && e.Status != "NOT_CHECKED" && e.Status != "NOT_ACCESSIBLE" {
			return nil, nil, nil, Fail(422, "GATE_FAILED", "inventory entry carries an unknown status")
		}
		if strings.Contains(e.LocationRef, "..") || strings.HasPrefix(e.LocationRef, "/") || filepathLike(e.LocationRef) {
			return nil, nil, nil, Fail(403, "PATH_OUT_OF_SCOPE", "inventory entry points outside the authorised directory")
		}
		entries = append(entries, e)
		list = append(list, Object{"capability": e.Capability, "location_ref": e.LocationRef, "status": e.Status,
			"revision_or_hash": e.RevisionOrHash, "notes": e.Notes})
	}
	failures := []LocalInventoryFileFailure{}
	for _, f := range res.Failures {
		if filepathLike(f.Path) || strings.Contains(f.Path, "..") {
			return nil, nil, nil, Fail(403, "PATH_OUT_OF_SCOPE", "file failure record leaks an absolute path")
		}
		failures = append(failures, f)
	}
	// A directory the scanner could read but found nothing in is a legitimate empty project; a
	// scanner that returns no entry at all hid the difference between those two, which is exactly
	// the failure this card must not allow. Unreadable roots must come back as one
	// NOT_ACCESSIBLE entry instead.
	if len(list) == 0 {
		return entries, Object{}, failures, Fail(422, "GATE_FAILED", "inventory scanner reported neither findings nor an inaccessible root")
	}
	env := res.Environment
	if env == "" {
		env = "local-workspace"
	}
	payload := Object{"project_id": project, "authorized_scope_refs": []any{b.AuthorizedRef},
		"environment": fmt.Sprintf("%s/%s", env, mode), "observed_at": Now(), "entries": list}
	return entries, payload, failures, nil
}

// ensureStage writes a NOT_STARTED marker only when the stage has no record yet. Re-running
// bootstrap therefore cannot rewrite history, and cannot promote a stage this card has not done.
func (s *Service) ensureStage(ctx context.Context, tx *sql.Tx, project, id, stage, observedAt string) error {
	var existing string
	err := tx.QueryRowContext(ctx, `SELECT body FROM domain_objects WHERE project=? AND kind=? AND id=?`, project, KindBootstrapStage, id).Scan(&existing)
	if err == nil {
		return nil
	}
	if !errors.Is(err, sql.ErrNoRows) {
		return err
	}
	return s.putOpaque(ctx, tx, project, KindBootstrapStage, id, Object{"id": id, "project_id": project,
		"stage": stage, "status": StageNotStarted, "inventory_artifact_ref": nil, "file_failures": Empty(),
		"observed_at": observedAt, "revision": int64(1)})
}

func (s *Service) authorisedBinding(ctx context.Context, tx *sql.Tx, p Principal, ref string) (*WorkspaceBinding, error) {
	b, err := s.binding(ctx, tx, ref)
	if err != nil {
		return nil, err
	}
	// A role is not a universal key: the authorisation behind this reference is one principal's own
	// OS-scoped directory choice, so only that principal may bind a project through it.
	if b.PrincipalID != p.ID {
		return nil, Fail(403, "FORBIDDEN", "workspace was authorised for a different principal")
	}
	if b.Status != WorkspaceActive {
		return nil, Fail(410, "WORKSPACE_REVOKED", "authorized workspace is revoked")
	}
	return b, nil
}

// replayOwner reports which principal, if any, already ran a bootstrap under this command id.
func (s *Service) replayOwner(ctx context.Context, tx *sql.Tx, commandID string) (string, error) {
	var principal string
	e := tx.QueryRowContext(ctx, `SELECT json_extract(body,'$.principal_id') FROM domain_objects WHERE kind='BootstrapReplay' AND id=?`,
		"replay-"+commandID).Scan(&principal)
	if errors.Is(e, sql.ErrNoRows) {
		return "", nil
	}
	if e != nil {
		return "", e
	}
	return principal, nil
}

// bootstrapReplay rebuilds the original answer from the durable records a previous delivery wrote.
func (s *Service) bootstrapReplay(ctx context.Context, tx *sql.Tx, principal, commandID string, b *WorkspaceBinding) (Object, error) {
	var raw string
	e := tx.QueryRowContext(ctx, `SELECT body FROM domain_objects WHERE kind=? AND id=?`, "BootstrapReplay", "replay-"+commandID).Scan(&raw)
	if errors.Is(e, sql.ErrNoRows) {
		return nil, nil
	}
	if e != nil {
		return nil, e
	}
	o, e := Decode([]byte(raw))
	if e != nil {
		return nil, e
	}
	if Str(o, "principal_id") != principal {
		return nil, Fail(403, "COMMAND_ID_CONFLICT", "this command id belongs to another principal")
	}
	project := Str(o, "project_id")
	profile, e := load(tx, project, "ProjectProfile", project)
	if e != nil {
		return nil, e
	}
	artifact, e := load(tx, project, "Artifact", Str(o, "artifact_id"))
	if e != nil {
		return nil, e
	}
	withProject := *b
	withProject.ProjectID = &project
	return Object{"project_id": project, "workspace": withProject.Reply(), "project_profile_ref": Ref(profile, "ProjectProfile"),
		"inventory_artifact_ref": Ref(artifact, "Artifact"), "bootstrap_task_id": Str(o, "stage_id"), "bootstrap_run_id": nil}, nil
}

func displayNameOr(name string, b *WorkspaceBinding) string {
	if strings.TrimSpace(name) != "" {
		return name
	}
	return b.DisplayName
}

func refID(o Object) *string {
	v := Str(o, "id")
	if v == "" {
		return nil
	}
	return &v
}

func failuresList(failures []LocalInventoryFileFailure) []any {
	out := []any{}
	for _, f := range failures {
		out = append(out, Object{"path": f.Path, "reason": f.Reason, "content_disclosed": f.Encoded})
	}
	return out
}

func filepathLike(p string) bool {
	return strings.ContainsRune(p, '\\') || strings.HasPrefix(p, "/") || strings.Contains(p, ":\\") ||
		len(p) > 1 && p[1] == ':'
}
