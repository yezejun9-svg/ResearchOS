package domain

// W04-01 · authorized workspace bindings (22_CLIENT_INTERFACE_DETAILS §2.2, §4 field lifecycle).
//
// The lifecycle the contract pins is: a trusted local chooser produces a single-use
// selection_ref, the ordinary command workspace.register consumes that reference and mints the
// durable authorized_workspace_ref, and only then may project.bootstrap bind a project identity.
// The host is the only component that can see real paths, links and permissions, so path
// canonicalisation, reparse detection and access scope are asked of the WorkspaceAuthority port
// rather than trusted from a client-supplied string. Conversely, an authorized_workspace_ref is
// never a path: a caller that presents "C:\somewhere" or "/srv/x" as a reference is refused,
// because references are only ever minted here.
//
// Two deliberate omissions belong to later cards, and both are recorded rather than faked:
// internal/domain/client_protocol.go (out of this card's write scope) still answers
// NOT_IMPLEMENTED for these two methods over /v2/command, so the production entry point is the
// exported functions below plus an injected authority; and the Goal/Task chain that the
// bootstrap_task_id will eventually point at is created by W04-02/W08, not here.

import (
	"context"
	"database/sql"
	"errors"
	"path/filepath"
	"strings"
)

const (
	// KindWorkspaceBinding is the durable record behind an authorized_workspace_ref. It is
	// intentionally not a VersionRef entity_type: the published contract treats the workspace
	// reference as an opaque string (BootstrapPayload.authorized_workspace_ref and
	// WorkspaceBinding.authorized_workspace_ref are plain strings), so nothing may point a
	// VersionRef at it, and the record itself is graded against the pinned WorkspaceBinding
	// definition of the client protocol before it leaves the domain.
	KindWorkspaceBinding = "WorkspaceBinding"
	// KindBootstrapStage is the LOCAL_INVENTORY stage record produced by project.bootstrap.
	KindBootstrapStage = "BootstrapStage"

	WorkspaceActive  = "ACTIVE"
	WorkspaceRevoked = "REVOKED"

	bootstrapDefWorkspaceBinding = "WorkspaceBinding"
)

// WorkspaceSelection is the resolved answer of one trusted directory choice.
type WorkspaceSelection struct {
	RealPath    string
	DisplayPath string
	Access      string
	// HostPrincipalRef is the OS-principal reference the host recorded for the choice. The host
	// compares it against its own verified local user, so the domain can keep it as evidence
	// without ever treating it as a domain principal.
	HostPrincipalRef string
	ClientID         string
}

// WorkspaceAuthority is the host-side port that a composition root injects into these calls.
// internal/host already owns the selection store and the pinned root registry; the domain must
// not import it (host imports domain), so the port is declared here and satisfied by an adapter.
type WorkspaceAuthority interface {
	// ConsumeSelection redeems a single-use selection reference exactly once, by the same
	// principal and client, before it expires. Reuse must return an error whose text carries
	// SELECTION_ALREADY_USED and expiry must return SELECTION_EXPIRED.
	ConsumeSelection(ctx context.Context, selectionRef, clientID, principalID string) (WorkspaceSelection, error)
	// ConfirmPath re-asks the OS whether the directory is still the same authorized, non-reparse
	// object it was when the reference was minted. Registration-time correctness grants no later
	// immunity, so bootstrap calls this before touching a directory.
	ConfirmPath(ctx context.Context, realPath, wantAccess string) error
}

// DefGrader grades a value against one published definition of the pinned client protocol.
// *SchemaDoc from the protocol qualification satisfies it, so the bridge, the protocol check and
// this card decide shape from the same document instead of three hand-written validators.
type DefGrader interface {
	ValidateDef(name string, value any) error
}

// RegisterWorkspaceInput is the published RegisterWorkspacePayload plus the command identity the
// host needs to make a replay return the original binding.
type RegisterWorkspaceInput struct {
	SelectionRef    string
	DisplayName     string
	RequestedAccess string
	CommandID       string
	// ClientID is the envelope's client identity. The selection is bound to the principal AND the
	// client that made the choice, so redemption has to carry both or a second client of the same
	// user could spend a reference it never earned.
	ClientID string
}

// WorkspaceBinding is the durable binding view. Reply() narrows it to the seven published fields.
type WorkspaceBinding struct {
	AuthorizedRef    string  `json:"authorized_workspace_ref"`
	DisplayName      string  `json:"display_name"`
	DisplayPath      string  `json:"display_path"`
	RealPath         string  `json:"real_path"`
	Access           string  `json:"access"`
	ProjectID        *string `json:"project_id"`
	Revision         int64   `json:"revision"`
	Status           string  `json:"status"`
	PrincipalID      string  `json:"principal_id"`
	HostPrincipalRef string  `json:"host_principal_ref"`
	ClientID         string  `json:"client_id"`
	SelectionRef     string  `json:"selection_ref"`
	CommandID        string  `json:"command_id"`
	CreatedAt        string  `json:"created_at"`
}

// Reply is the object the protocol allows to leave the domain: exactly the published fields.
func (b *WorkspaceBinding) Reply() Object {
	var project any
	if b.ProjectID != nil {
		project = *b.ProjectID
	}
	return Object{
		"authorized_workspace_ref": b.AuthorizedRef,
		"display_name":             b.DisplayName,
		"display_path":             b.DisplayPath,
		"access":                   b.Access,
		"project_id":               project,
		"revision":                 b.Revision,
		"status":                   b.Status,
	}
}

// ProjectFor binds a project identity into the record. The domain owns this association; the host
// keeps the canonical path, the access class and the revocation state.
func (b *WorkspaceBinding) bindProject(projectID string) Object {
	o := b.record()
	o["project_id"] = projectID
	o["revision"] = b.Revision + 1
	return o
}

// nextRevision reads the revision a domain-owned record currently has, so a refresh advances by
// exactly one instead of replaying the old number and tripping the append-only guard.
func (s *Service) nextRevision(ctx context.Context, tx *sql.Tx, project, kind, id string) (int64, error) {
	var rev int64
	err := tx.QueryRowContext(ctx, `SELECT revision FROM domain_objects WHERE project=? AND kind=? AND id=?`, project, kind, id).Scan(&rev)
	if errors.Is(err, sql.ErrNoRows) {
		return 1, nil
	}
	if err != nil {
		return 0, err
	}
	if rev >= 1<<62 {
		return 0, Fail(409, "STATE_CONFLICT", "record revision exhausted")
	}
	return rev + 1, nil
}

func (b *WorkspaceBinding) record() Object {
	return Object{
		"authorized_workspace_ref": b.AuthorizedRef,
		"display_name":             b.DisplayName,
		"display_path":             b.DisplayPath,
		"real_path":                b.RealPath,
		"access":                   b.Access,
		"project_id":               b.ProjectID,
		"revision":                 b.Revision,
		"status":                   b.Status,
		"principal_id":             b.PrincipalID,
		"host_principal_ref":       b.HostPrincipalRef,
		"client_id":                b.ClientID,
		"selection_ref":            b.SelectionRef,
		"command_id":               b.CommandID,
		"created_at":               b.CreatedAt,
	}
}

// RegisterWorkspace consumes a trusted selection and mints the durable authorized reference.
// Every refusal is typed so the caller can distinguish "the choice was already spent" from
// "that reference was never minted here".
func (s *Service) RegisterWorkspace(ctx context.Context, p Principal, a WorkspaceAuthority, g DefGrader, in RegisterWorkspaceInput) (Object, error) {
	tx, err := s.DB.BeginTx(ctx, nil)
	if err != nil {
		return nil, err
	}
	defer tx.Rollback()
	result, err := s.registerWorkspaceTx(ctx, tx, p, a, g, in)
	if err != nil {
		return nil, err
	}
	if err = tx.Commit(); err != nil {
		return nil, err
	}
	return result, nil
}

func (s *Service) registerWorkspaceTx(ctx context.Context, tx *sql.Tx, p Principal, a WorkspaceAuthority, g DefGrader, in RegisterWorkspaceInput) (Object, error) {
	if a == nil || g == nil {
		return nil, Fail(503, "RESOURCE_UNAVAILABLE", "workspace authority and contract grader are required")
	}
	if strings.TrimSpace(in.SelectionRef) == "" || strings.TrimSpace(in.DisplayName) == "" || strings.TrimSpace(in.CommandID) == "" {
		return nil, Fail(400, "INVALID_REQUEST", "selection_ref, display_name and command_id are required")
	}
	if in.RequestedAccess != "READ_ONLY" && in.RequestedAccess != "READ_WRITE" {
		return nil, Fail(400, "INVALID_REQUEST", "requested_access must be READ_ONLY or READ_WRITE")
	}
	if !p.HasRole("OWNER") && !p.CanCreateProject {
		return nil, Fail(403, "FORBIDDEN", "project creation is not granted")
	}

	// The project-creation right is checked FIRST (a caller with no right must not learn that a
	// command id exists), and only then the command-id namespace, so a caller that does have a
	// right but collides is refused with COMMAND_ID_CONFLICT instead of a generic FORBIDDEN.
	// project.bootstrap uses the opposite ordering on purpose: there the namespace collision is
	// about the replay record, and the reference scoping confines what it can reach.
	if clash, e := s.bindingCommandOwner(ctx, tx, in.CommandID); e == nil && clash != "" && clash != p.ID {
		return nil, Fail(409, "COMMAND_ID_CONFLICT", "this command id was already used by another principal")
	} else if e != nil && !errors.Is(e, errNoBinding) {
		return nil, e
	}
	// A replay of the same command returns the original binding and must not redeem a second
	// selection: the reference is already spent, so asking the authority again would fail with
	// SELECTION_ALREADY_USED for what is really a duplicate delivery.
	if existing, e := s.bindingByCommand(ctx, tx, p.ID, in.CommandID); e == nil && existing != nil {
		return existing.Reply(), nil
	} else if e != nil && !errors.Is(e, errNoBinding) {
		return nil, e
	}

	if strings.TrimSpace(in.ClientID) == "" {
		return nil, Fail(400, "INVALID_REQUEST", "client_id is required to redeem a directory choice")
	}
	sel, err := a.ConsumeSelection(ctx, in.SelectionRef, in.ClientID, p.ID)
	if err != nil {
		return nil, typedFromAuthority(err)
	}
	// Requested permission may never exceed what the directory choice authorised.
	if in.RequestedAccess == "READ_WRITE" && sel.Access != "READ_WRITE" {
		return nil, Fail(403, "POLICY_DENIED", "requested access exceeds the chosen directory authorisation")
	}
	realPath, err := canonicalLocalPath(sel.RealPath)
	if err != nil {
		return nil, err
	}
	if err := a.ConfirmPath(ctx, realPath, sel.Access); err != nil {
		return nil, typedFromAuthority(err)
	}
	// A directory that already carries another principal's project is refused rather than given a
	// second permanent identity: 重复创建永久身份 must fail, and two writable identities over one
	// canonical path is exactly that. The refusal says nothing about who owns the other binding.
	if taken, e := s.directoryHeldByOther(ctx, tx, realPath, p.ID); e != nil {
		return nil, e
	} else if taken {
		return nil, Fail(403, "POLICY_DENIED", "this directory is already bound to another principal")
	}

	ref := "wsref-" + ID()[:16]
	b := &WorkspaceBinding{AuthorizedRef: ref, DisplayName: in.DisplayName, DisplayPath: firstNonEmpty(sel.DisplayPath, realPath),
		RealPath: realPath, Access: in.RequestedAccess, Revision: 1, Status: WorkspaceActive,
		PrincipalID: p.ID, HostPrincipalRef: sel.HostPrincipalRef, ClientID: sel.ClientID,
		SelectionRef: in.SelectionRef, CommandID: in.CommandID, CreatedAt: Now()}
	reply := b.Reply()
	if err := g.ValidateDef(bootstrapDefWorkspaceBinding, reply); err != nil {
		return nil, Fail(422, "CONTENT_HASH_MISMATCH", "workspace binding violates the published definition: "+err.Error())
	}
	if err := s.putOpaque(ctx, tx, "", KindWorkspaceBinding, ref, b.record()); err != nil {
		return nil, err
	}
	return reply, nil
}

// WorkspaceBindingFor resolves one authorized reference for the authenticated principal. A
// reference this host never minted is NOT_FOUND: the lookup is by minted identifier only, so a
// caller cannot self-authorise a directory by naming its path.
func (s *Service) WorkspaceBindingFor(ctx context.Context, p Principal, a WorkspaceAuthority, ref string) (*WorkspaceBinding, error) {
	if strings.TrimSpace(ref) == "" {
		return nil, Fail(400, "INVALID_REQUEST", "authorized_workspace_ref is required")
	}
	if looksLikePath(ref) {
		return nil, Fail(403, "FORBIDDEN", "an authorized workspace reference is not a filesystem path")
	}
	tx, err := s.DB.BeginTx(ctx, nil)
	if err != nil {
		return nil, err
	}
	defer tx.Rollback()
	b, err := s.binding(ctx, tx, ref)
	if err != nil {
		return nil, err
	}
	// The reference belongs to the principal who made the choice. An OWNER role is not a pass:
	// authorisation here came from that user's own OS-scoped directory choice, and treating a role
	// as a universal key would let any OWNER bind another user's workspace and inherit its project.
	if b.PrincipalID != p.ID {
		return nil, Fail(403, "FORBIDDEN", "workspace was authorised for a different principal")
	}
	if b.Status != WorkspaceActive {
		return nil, Fail(410, "WORKSPACE_REVOKED", "authorized workspace is revoked")
	}
	if a != nil {
		if err := a.ConfirmPath(ctx, b.RealPath, b.Access); err != nil {
			return nil, typedFromAuthority(err)
		}
	}
	return b, nil
}

// RevokeWorkspaceBinding withdraws an authorized reference. History is kept: the record stays
// readable as REVOKED rather than disappearing, and later access is refused rather than reported
// as an empty directory.
func (s *Service) RevokeWorkspaceBinding(ctx context.Context, p Principal, ref string) error {
	tx, err := s.DB.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	b, err := s.binding(ctx, tx, ref)
	if err != nil {
		return err
	}
	if b.PrincipalID != p.ID {
		return Fail(403, "FORBIDDEN", "only the principal that authorised this workspace may revoke it")
	}
	if b.Status == WorkspaceRevoked {
		return nil
	}
	o := b.record()
	o["status"] = WorkspaceRevoked
	rev, _ := Num(o, "revision")
	o["revision"] = rev + 1
	if err := s.putOpaque(ctx, tx, "", KindWorkspaceBinding, ref, o); err != nil {
		return err
	}
	return tx.Commit()
}

// ListWorkspaceBindings returns only the bindings this principal authorised, never another
// project's or another user's directories.
func (s *Service) ListWorkspaceBindings(ctx context.Context, p Principal) ([]*WorkspaceBinding, error) {
	rows, err := s.DB.QueryContext(ctx, `SELECT body FROM domain_objects WHERE kind=? ORDER BY id`, KindWorkspaceBinding)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	out := []*WorkspaceBinding{}
	for rows.Next() {
		var raw string
		if err := rows.Scan(&raw); err != nil {
			return nil, err
		}
		b, err := decodeBinding(raw)
		if err != nil {
			return nil, err
		}
		if b.PrincipalID == p.ID {
			out = append(out, b)
		}
	}
	return out, rows.Err()
}

var errNoBinding = errors.New("no such workspace binding")

func (s *Service) binding(ctx context.Context, tx *sql.Tx, ref string) (*WorkspaceBinding, error) {
	var raw string
	e := tx.QueryRowContext(ctx, `SELECT body FROM domain_objects WHERE project='' AND kind=? AND id=?`, KindWorkspaceBinding, ref).Scan(&raw)
	if errors.Is(e, sql.ErrNoRows) {
		return nil, Fail(404, "NOT_FOUND", "authorized workspace reference was never minted here")
	}
	if e != nil {
		return nil, e
	}
	return decodeBinding(raw)
}

// bindingCommandOwner reports which principal, if any, already used this command id in a
// workspace registration.
func (s *Service) bindingCommandOwner(ctx context.Context, tx *sql.Tx, commandID string) (string, error) {
	var principal string
	e := tx.QueryRowContext(ctx, `SELECT json_extract(body,'$.principal_id') FROM domain_objects WHERE project='' AND kind=? AND json_extract(body,'$.command_id')=?`,
		KindWorkspaceBinding, commandID).Scan(&principal)
	if errors.Is(e, sql.ErrNoRows) {
		return "", errNoBinding
	}
	if e != nil {
		return "", e
	}
	return principal, nil
}

// bindingByCommand returns the binding minted for this command id, or nil when there is none.
func (s *Service) bindingByCommand(ctx context.Context, tx *sql.Tx, principal, commandID string) (*WorkspaceBinding, error) {
	var raw string
	e := tx.QueryRowContext(ctx, `SELECT body FROM domain_objects WHERE project='' AND kind=? AND json_extract(body,'$.command_id')=? AND json_extract(body,'$.principal_id')=?`,
		KindWorkspaceBinding, commandID, principal).Scan(&raw)
	if errors.Is(e, sql.ErrNoRows) {
		return nil, errNoBinding
	}
	if e != nil {
		return nil, e
	}
	return decodeBinding(raw)
}

// directoryHeldByOther reports whether some other principal already bound this canonical
// directory to a project. It never returns the other principal or reference to the caller.
func (s *Service) directoryHeldByOther(ctx context.Context, tx *sql.Tx, realPath, principal string) (bool, error) {
	rows, e := tx.QueryContext(ctx, `SELECT body FROM domain_objects WHERE project='' AND kind=? AND json_extract(body,'$.real_path')=?`,
		KindWorkspaceBinding, realPath)
	if e != nil {
		return false, e
	}
	defer rows.Close()
	for rows.Next() {
		var raw string
		if e = rows.Scan(&raw); e != nil {
			return false, e
		}
		b, e := decodeBinding(raw)
		if e != nil {
			return false, e
		}
		if b.PrincipalID != principal && b.Status == WorkspaceActive && b.ProjectID != nil {
			return true, nil
		}
	}
	return false, rows.Err()
}

// bindingByRealPath finds the live binding for the same canonical directory, which is how a
// changed alias for one permanent project reuses the original identity instead of creating a
// second one.
func (s *Service) bindingByRealPath(ctx context.Context, tx *sql.Tx, principal, realPath string) (*WorkspaceBinding, error) {
	rows, e := tx.QueryContext(ctx, `SELECT body FROM domain_objects WHERE project='' AND kind=? AND json_extract(body,'$.real_path')=? ORDER BY id`, KindWorkspaceBinding, realPath)
	if e != nil {
		return nil, e
	}
	defer rows.Close()
	var found *WorkspaceBinding
	for rows.Next() {
		var raw string
		if e := rows.Scan(&raw); e != nil {
			return nil, e
		}
		b, e := decodeBinding(raw)
		if e != nil {
			return nil, e
		}
		if b.PrincipalID != principal || b.Status != WorkspaceActive {
			continue
		}
		// Continuation prefers the binding that already owns a project: a reference minted
		// seconds ago for the same directory is in this set too, and choosing it would create a
		// second permanent identity for one workspace.
		if found == nil {
			found = b
		} else if found.ProjectID == nil && b.ProjectID != nil {
			found = b
		}
	}
	if e = rows.Err(); e != nil {
		return nil, e
	}
	return found, nil
}

func decodeBinding(raw string) (*WorkspaceBinding, error) {
	o, e := Decode([]byte(raw))
	if e != nil {
		return nil, e
	}
	rev, e := Num(o, "revision")
	if e != nil {
		return nil, e
	}
	var project *string
	if v, ok := o["project_id"].(string); ok && v != "" {
		project = &v
	}
	return &WorkspaceBinding{AuthorizedRef: Str(o, "authorized_workspace_ref"), DisplayName: Str(o, "display_name"),
		DisplayPath: Str(o, "display_path"), RealPath: Str(o, "real_path"), Access: Str(o, "access"),
		ProjectID: project, Revision: rev, Status: Str(o, "status"), PrincipalID: Str(o, "principal_id"),
		ClientID: Str(o, "client_id"), HostPrincipalRef: Str(o, "host_principal_ref"),
		SelectionRef: Str(o, "selection_ref"), CommandID: Str(o, "command_id"),
		CreatedAt: Str(o, "created_at")}, nil
}

// putOpaque stores a domain-owned record that no VersionRef may ever target.
//
// It writes ONLY domain_objects, on purpose. The accepted restore path (internal/domain/backup.go)
// validates every domain_versions row against the frozen domain schema by kind, and WorkspaceBinding,
// BootstrapStage, BootstrapReplay and Project are not schema entities - versioning them here made
// release recovery fail with RESTORE_CONTRACT_INCOMPATIBLE for any backup taken after the first
// bootstrap. The append-only history of the business entities these records point at (ProjectProfile,
// ProjectState, Artifact) is still written by put(). These rows are current-state association records,
// and the revision compare-and-set below keeps them monotonic so a stale writer cannot overwrite one.
func (s *Service) putOpaque(ctx context.Context, tx *sql.Tx, project, kind, id string, o Object) error {
	rev, e := Num(o, "revision")
	if e != nil {
		return e
	}
	var existing string
	q := `SELECT body, revision FROM domain_objects WHERE project=? AND kind=? AND id=?`
	var oldRev int64
	err := tx.QueryRowContext(ctx, q, project, kind, id).Scan(&existing, &oldRev)
	if err == nil {
		if rev != oldRev+1 {
			return Fail(409, "STATE_CONFLICT", "revision must advance once")
		}
	} else if !errors.Is(err, sql.ErrNoRows) {
		return err
	}
	body := string(Bytes(o))
	if _, e := tx.ExecContext(ctx, `INSERT INTO domain_objects(project,kind,id,revision,body,content_hash,immutable) VALUES(?,?,?,?,?,?,0)
		ON CONFLICT(project,kind,id) DO UPDATE SET revision=excluded.revision, body=excluded.body, content_hash=excluded.content_hash`,
		project, kind, id, rev, body, Digest([]byte(body))); e != nil {
		return e
	}
	return nil
}

// canonicalLocalPath refuses anything that is not a single absolute local path. Alternate data
// streams, UNC prefixes and embedded NULs would all let a "directory" mean something else.
func canonicalLocalPath(p string) (string, error) {
	if strings.TrimSpace(p) == "" || strings.ContainsRune(p, 0) {
		return "", Fail(400, "INVALID_REQUEST", "resolved directory path is unusable")
	}
	if strings.HasPrefix(p, `\\`) {
		return "", Fail(403, "PATH_OUT_OF_SCOPE", "network paths cannot be authorised")
	}
	if !filepath.IsAbs(p) {
		return "", Fail(403, "PATH_OUT_OF_SCOPE", "directory path must already be absolute and canonical")
	}
	// A stream separator is a colon that appears AFTER the volume name: "D:\dir\file.txt:$DATA".
	// Testing the first colon would look at the drive letter instead, so the volume name is stripped
	// before the search.
	if stream := strings.Index(strings.TrimPrefix(p, filepath.VolumeName(p)), ":"); stream >= 0 {
		return "", Fail(400, "INVALID_REQUEST", "path carries an alternate data stream")
	}
	return filepath.Clean(p), nil
}

func looksLikePath(s string) bool {
	return strings.ContainsRune(s, filepath.Separator) || strings.Contains(s, "/") ||
		filepath.VolumeName(s) != "" || strings.HasPrefix(s, `\\`)
}

func firstNonEmpty(a, b string) string {
	if a != "" {
		return a
	}
	return b
}

// typedFromAuthority maps the host's refusal vocabulary onto protocol error codes without ever
// echoing a path or a credential back to the caller: the message is fixed per class.
func typedFromAuthority(err error) error {
	switch {
	case err == nil:
		return nil
	case strings.Contains(err.Error(), "SELECTION_ALREADY_USED"):
		return Fail(409, "SELECTION_ALREADY_USED", "this directory choice was already consumed")
	case strings.Contains(err.Error(), "SELECTION_EXPIRED"):
		return Fail(410, "SELECTION_EXPIRED", "this directory choice expired")
	case strings.Contains(err.Error(), "PATH_OUT_OF_SCOPE"):
		return Fail(403, "PATH_OUT_OF_SCOPE", "the chosen directory is outside the authorised scope")
	case strings.Contains(err.Error(), "WORKSPACE_REVOKED"):
		return Fail(410, "WORKSPACE_REVOKED", "the authorized workspace is revoked")
	case strings.Contains(err.Error(), "pinned workspace root is unavailable"),
		strings.Contains(err.Error(), "PATH_OUT_OF_SCOPE"),
		strings.Contains(err.Error(), "WORKSPACE_ROOT_UNAVAILABLE"):
		return Fail(403, "PATH_OUT_OF_SCOPE", "the authorized directory is no longer the directory that was chosen")
	case strings.Contains(err.Error(), "UNAUTHENTICATED"), strings.Contains(err.Error(), "FORBIDDEN"):
		return Fail(403, "FORBIDDEN", "the directory choice does not belong to this caller")
	default:
		return Fail(403, "POLICY_DENIED", "the host refused this directory: "+err.Error())
	}
}

// BootstrapStage is the durable LOCAL_INVENTORY record. Stages that this card must not claim are
// written as NOT_STARTED so a reader can tell "not done yet" from "nothing to do".
type BootstrapStage struct {
	ID           string  `json:"id"`
	ProjectID    string  `json:"project_id"`
	Stage        string  `json:"stage"`
	Status       string  `json:"status"`
	InventoryRef *string `json:"inventory_artifact_ref"`
	Failures     []any   `json:"file_failures"`
	ObservedAt   string  `json:"observed_at"`
	Revision     int64   `json:"revision"`
}

const (
	StageLocalInventory = "LOCAL_INVENTORY"
	StageResearch       = "RESEARCH"
	StageReuseDecision  = "REUSE_DECISION"
	StageImplementation = "IMPLEMENTATION"

	StageCompleted  = "COMPLETED"
	StagePartial    = "PARTIAL"
	StageFailed     = "FAILED"
	StageNotStarted = "NOT_STARTED"
)

// StageRecord returns the row shape kept under KindBootstrapStage.
func (b *BootstrapStage) StageRecord() Object {
	return Object{"id": b.ID, "project_id": b.ProjectID, "stage": b.Stage, "status": b.Status,
		"inventory_artifact_ref": b.InventoryRef, "file_failures": b.Failures,
		"observed_at": b.ObservedAt, "revision": b.Revision}
}
