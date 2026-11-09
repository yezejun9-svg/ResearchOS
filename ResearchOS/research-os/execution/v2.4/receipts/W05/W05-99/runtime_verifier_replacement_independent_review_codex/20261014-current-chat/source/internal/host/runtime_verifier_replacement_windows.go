//go:build windows

package host

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/url"
	"os"
	"path/filepath"
	"strings"
	"time"
	"unsafe"

	"golang.org/x/sys/windows"
	_ "modernc.org/sqlite"
	rt "researchos.local/research-os/adapters/runtime"
	"researchos.local/research-os/internal/auth"
	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/verifier"
)

const replacementSchema = "researchos.runtime-verifier-replacement.v1"
const replacementJournal = "runtime-verifier-replacements"

type RuntimeVerifierReplacementInput struct {
	Action, DataRoot, Manifest, ExpectRecordSHA256, ExpectManifestSHA256 string
	OperationID, Out, Plan, ExpectPlanSHA256, RecoveryAction, RollbackOf string
}

type RuntimeVerifierReplacementResult struct {
	Schema           string `json:"schema"`
	Action           string `json:"action"`
	OperationID      string `json:"operation_id"`
	State            string `json:"state"`
	Outcome          string `json:"outcome"`
	ErrorCode        string `json:"error_code,omitempty"`
	PlanSHA256       string `json:"plan_sha256"`
	OldRecordSHA256  string `json:"old_record_sha256"`
	NewRecordSHA256  string `json:"new_record_sha256"`
	RegistrationHash string `json:"registration_hash"`
	InstallationHash string `json:"installation_hash"`
	ReadonlyCensus   [4]int `json:"readonly_census"`
}

type replacementFileID struct {
	Volume    uint32
	IndexHigh uint32
	IndexLow  uint32
}
type replacementPlan struct {
	Schema              string                      `json:"schema"`
	OperationID         string                      `json:"operation_id"`
	CreatedAt           string                      `json:"created_at"`
	DataRoot            string                      `json:"data_root"`
	HostPath            string                      `json:"host_path"`
	DBPath              string                      `json:"db_path"`
	FileIDs             [3]replacementFileID        `json:"file_ids"`
	PrincipalRef        string                      `json:"principal_ref"`
	HostID              string                      `json:"host_id"`
	Owner               string                      `json:"owner"`
	Root                string                      `json:"service_root"`
	StateSHA256         string                      `json:"state_sha256"`
	LineageHash         string                      `json:"lineage_hash"`
	SchemaVersion       int                         `json:"schema_version"`
	Census              [4]int                      `json:"readonly_census"`
	OldBytes            []byte                      `json:"old_record_bytes"`
	OldSHA256           string                      `json:"old_record_sha256"`
	OldHash             string                      `json:"old_registration_hash"`
	OldInstallationHash string                      `json:"old_installation_hash"`
	Manifest            string                      `json:"manifest"`
	ManifestSHA256      string                      `json:"manifest_sha256"`
	Installation        RuntimeVerifierInstallation `json:"installation"`
	NewBytes            []byte                      `json:"new_record_bytes"`
	NewSHA256           string                      `json:"new_record_sha256"`
	NewHash             string                      `json:"registration_hash"`
	NewInstallationHash string                      `json:"installation_hash"`
	RollbackOf          string                      `json:"rollback_of,omitempty"`
}

// Seams are package-private and are never wired from argv or environment. Tests
// use them for external rename and real child-process termination boundaries.
var replacementBoundary = func(string) {}
var replacementReplace = callReplaceFile

func replacementID(s string) bool {
	b, e := hex.DecodeString(s)
	return e == nil && len(b) == 16 && strings.ToLower(s) == s
}
func replacementDigest(s string) bool {
	b, e := hex.DecodeString(strings.TrimPrefix(s, "sha256:"))
	return strings.HasPrefix(s, "sha256:") && e == nil && len(b) == 32 && strings.ToLower(s) == s
}
func replacementPath(p string) error {
	if !filepath.IsAbs(p) || filepath.Clean(p) != p || len(filepath.VolumeName(p)) != 2 || strings.Contains(p[2:], ":") {
		return errors.New("canonical absolute local path required")
	}
	return nil
}
func replacementACL(path string, dir, private bool) error {
	sid, e := currentSIDString()
	if e != nil {
		return e
	}
	sd, e := windows.GetNamedSecurityInfo(path, windows.SE_FILE_OBJECT, windows.OWNER_SECURITY_INFORMATION|windows.DACL_SECURITY_INFORMATION)
	if e != nil {
		return e
	}
	owner, _, e := sd.Owner()
	if e != nil || owner == nil || owner.String() != sid {
		return errors.New("current SID owner required")
	}
	if !private {
		return nil
	}
	control, _, e := sd.Control()
	if e != nil || control&windows.SE_DACL_PROTECTED == 0 {
		return errors.New("protected private DACL required")
	}
	acl, _, e := sd.DACL()
	if e != nil || acl == nil || acl.AceCount != 1 {
		return errors.New("single private ACE required")
	}
	var ace *windows.ACCESS_ALLOWED_ACE
	if windows.GetAce(acl, 0, &ace) != nil {
		return errors.New("private ACE unavailable")
	}
	flags := byte(0)
	if dir {
		flags = windows.OBJECT_INHERIT_ACE | windows.CONTAINER_INHERIT_ACE
	}
	if ace.Header.AceType != windows.ACCESS_ALLOWED_ACE_TYPE || ace.Header.AceFlags != flags || ace.Mask != 0x001f01ff || (*windows.SID)(unsafe.Pointer(&ace.SidStart)).String() != sid {
		return errors.New("private ACE differs")
	}
	return nil
}
func replacementIdentity(path string, dir bool) (replacementFileID, error) {
	var out replacementFileID
	if e := replacementPath(path); e != nil {
		return out, e
	}
	p, e := windows.UTF16PtrFromString(path)
	if e != nil {
		return out, e
	}
	h, e := windows.CreateFile(p, windows.FILE_READ_ATTRIBUTES, windows.FILE_SHARE_READ|windows.FILE_SHARE_WRITE|windows.FILE_SHARE_DELETE, nil, windows.OPEN_EXISTING, windows.FILE_FLAG_OPEN_REPARSE_POINT|windows.FILE_FLAG_BACKUP_SEMANTICS, 0)
	if e != nil {
		return out, e
	}
	defer windows.CloseHandle(h)
	var i windows.ByHandleFileInformation
	if e = windows.GetFileInformationByHandle(h, &i); e != nil {
		return out, e
	}
	if i.FileAttributes&windows.FILE_ATTRIBUTE_REPARSE_POINT != 0 || (i.FileAttributes&windows.FILE_ATTRIBUTE_DIRECTORY != 0) != dir || (!dir && i.NumberOfLinks != 1) {
		return out, errors.New("reparse, alias or wrong file type")
	}
	return replacementFileID{i.VolumeSerialNumber, i.FileIndexHigh, i.FileIndexLow}, nil
}
func replacementRead(path string, limit int64) ([]byte, error) {
	if _, e := replacementIdentity(path, false); e != nil {
		return nil, e
	}
	guards, e := guardWriteDirectories(filepath.Dir(path))
	if e != nil {
		return nil, e
	}
	defer closeWriteGuards(guards)
	wide, e := windows.UTF16PtrFromString(path)
	if e != nil {
		return nil, e
	}
	h, e := windows.CreateFile(wide, windows.GENERIC_READ, windows.FILE_SHARE_READ, nil, windows.OPEN_EXISTING, windows.FILE_FLAG_OPEN_REPARSE_POINT, 0)
	if e != nil {
		return nil, e
	}
	f := os.NewFile(uintptr(h), path)
	defer f.Close()
	var info windows.ByHandleFileInformation
	if e = windows.GetFileInformationByHandle(h, &info); e != nil {
		return nil, e
	}
	if info.FileAttributes&(windows.FILE_ATTRIBUTE_DIRECTORY|windows.FILE_ATTRIBUTE_REPARSE_POINT) != 0 || info.NumberOfLinks != 1 {
		return nil, errors.New("managed handle redirected or aliased")
	}
	if e = replacementACL(path, false, true); e != nil {
		return nil, e
	}
	stat, e := f.Stat()
	if e != nil {
		return nil, e
	}
	if stat.Size() < 1 || stat.Size() > limit {
		return nil, errors.New("bounded managed file required")
	}
	raw, e := io.ReadAll(io.LimitReader(f, limit+1))
	if e != nil {
		return nil, e
	}
	if int64(len(raw)) > limit {
		return nil, errors.New("managed read exceeded bound")
	}
	return raw, nil
}

var replacementCensusSQL = [4]string{
	`SELECT count(*) FROM domain_objects WHERE kind='Run' AND coalesce(json_extract(body,'$.status'),'UNKNOWN') NOT IN ('SETTLED','FAILED','CANCELLED')`,
	`SELECT count(*) FROM resource_effects x WHERE sequence=(SELECT max(y.sequence) FROM resource_effects y WHERE y.project=x.project AND y.run=x.run AND y.effect_key=x.effect_key) AND json_extract(body,'$.state') IN ('PREPARED','STARTED','UNKNOWN')`,
	`SELECT count(*) FROM runtime_dispatches WHERE state IN ('PREPARED','STARTED','UNKNOWN')`,
	`SELECT count(*) FROM idempotency i LEFT JOIN domain_objects r ON r.project=i.project AND r.kind='Run' AND r.id=json_extract(i.body,'$.run_ref.id') WHERE i.operation='host:managed-runtime-qualification' AND (r.id IS NULL OR coalesce(json_extract(r.body,'$.status'),'UNKNOWN') NOT IN ('SETTLED','FAILED','CANCELLED') OR EXISTS(SELECT 1 FROM runtime_dispatches d WHERE d.project=i.project AND d.run=r.id AND d.state IN ('PREPARED','STARTED','UNKNOWN')) OR EXISTS(SELECT 1 FROM resource_effects x WHERE x.project=i.project AND x.run=r.id AND x.sequence=(SELECT max(y.sequence) FROM resource_effects y WHERE y.project=x.project AND y.run=x.run AND y.effect_key=x.effect_key) AND json_extract(x.body,'$.state') IN ('PREPARED','STARTED','UNKNOWN')))`,
}

func replacementSnapshot(ctx context.Context, root string) (replacementPlan, error) {
	p := replacementPlan{Schema: replacementSchema, DataRoot: root, HostPath: filepath.Join(root, "host"), DBPath: filepath.Join(root, "researchos.sqlite")}
	for n, path := range []string{p.DataRoot, p.HostPath, p.DBPath} {
		id, e := replacementIdentity(path, n < 2)
		if e != nil {
			return p, e
		}
		p.FileIDs[n] = id
		if e = replacementACL(path, n < 2, n == 1); e != nil {
			return p, e
		}
	}
	raw, e := replacementRead(filepath.Join(p.HostPath, stateFile), 64<<10)
	if e != nil {
		return p, e
	}
	var state hostState
	if e = decodeRuntimeManaged(raw, &state); e != nil {
		return p, e
	}
	p.StateSHA256 = domain.Digest(raw)
	identity, e := auth.Current()
	if e != nil {
		return p, e
	}
	h := &Host{dir: p.HostPath, identity: identity, state: &state}
	if state.Version != 1 || state.PrincipalID == "" {
		return p, ErrBadState
	}
	if _, e = h.ConfigurationMetadata(ctx, state.PrincipalID, "", nil); e != nil {
		return p, e
	}
	p.PrincipalRef, p.HostID, p.Owner = identity.Ref, h.InstanceID(), state.PrincipalID
	p.Root = "local-verifier-root-" + strings.TrimPrefix(domain.Hash([]any{p.HostID, verifier.ServiceID}), "sha256:")[:24]
	u := url.URL{Scheme: "file", Opaque: filepath.ToSlash(p.DBPath)}
	q := u.Query()
	q.Set("mode", "ro")
	u.RawQuery = q.Encode()
	db, e := sql.Open("sqlite", u.String())
	if e != nil {
		return p, e
	}
	defer db.Close()
	db.SetMaxOpenConns(1)
	db.SetMaxIdleConns(1)
	if _, e = db.ExecContext(ctx, "PRAGMA query_only=ON"); e != nil {
		return p, e
	}
	if _, e = db.ExecContext(ctx, "PRAGMA busy_timeout=2000"); e != nil {
		return p, e
	}
	var ro int
	if e = db.QueryRowContext(ctx, "PRAGMA query_only").Scan(&ro); e != nil || ro != 1 {
		return p, errors.New("readonly connection unavailable")
	}
	tx, e := db.BeginTx(ctx, &sql.TxOptions{ReadOnly: true})
	if e != nil {
		return p, e
	}
	defer tx.Rollback()
	var count, minVersion int
	if e = tx.QueryRowContext(ctx, "SELECT max(version),count(DISTINCT version),min(version) FROM schema_migrations").Scan(&p.SchemaVersion, &count, &minVersion); e != nil || p.SchemaVersion != 24 || count != 24 || minVersion != 1 {
		return p, errors.New("supported schema 24 required")
	}
	rows, e := tx.QueryContext(ctx, "SELECT id,roles,revoked,can_create_project FROM auth_principals ORDER BY id")
	if e != nil {
		return p, e
	}
	type principal struct {
		ID, Roles       string
		Revoked, Create int
	}
	var principals []principal
	owners := 0
	for rows.Next() {
		var v principal
		if e = rows.Scan(&v.ID, &v.Roles, &v.Revoked, &v.Create); e != nil {
			rows.Close()
			return p, e
		}
		var roles []string
		if decodeRuntimeManaged([]byte(v.Roles), &roles) != nil {
			rows.Close()
			return p, errors.New("invalid principal roles")
		}
		for _, r := range roles {
			if r == "OWNER" && v.Revoked == 0 {
				owners++
				if v.ID != p.Owner {
					rows.Close()
					return p, ErrHostIdentity
				}
			}
		}
		principals = append(principals, v)
	}
	e = rows.Err()
	rows.Close()
	if e != nil {
		return p, e
	}
	if owners != 1 {
		return p, ErrMultipleOwners
	}
	var ownerRoot string
	if e = tx.QueryRowContext(ctx, "SELECT root FROM orchestration_identity WHERE principal=?", p.Owner).Scan(&ownerRoot); e != nil || ownerRoot == "" || ownerRoot == p.Root {
		return p, errors.New("Owner lineage invalid")
	}
	// Include both root/parent links and every derived verifier ID. A detached or
	// reparented service child cannot disappear from the validation census.
	rows, e = tx.QueryContext(ctx, "SELECT principal,root,parent FROM orchestration_identity ORDER BY principal")
	if e != nil {
		return p, e
	}
	type lineage struct {
		ID, Root string
		Parent   sql.NullString
	}
	lines := map[string]lineage{}
	for rows.Next() {
		var l lineage
		if e = rows.Scan(&l.ID, &l.Root, &l.Parent); e != nil {
			rows.Close()
			return p, e
		}
		lines[l.ID] = l
	}
	e = rows.Err()
	rows.Close()
	if e != nil {
		return p, e
	}
	type grant struct {
		Project, Task, Run string
		Restricted         bool
	}
	type member struct {
		Principal principal
		Lineage   lineage
		Grants    []grant
	}
	members := []member{}
	foundRoot := false
	for _, v := range principals {
		l := lines[v.ID]
		belongs := v.ID == p.Root || l.Root == p.Root || (l.Parent.Valid && l.Parent.String == p.Root)
		grows, e := tx.QueryContext(ctx, "SELECT project,task,run,restricted FROM auth_grants WHERE principal=? ORDER BY project,task,run,restricted", v.ID)
		if e != nil {
			return p, e
		}
		gs := []grant{}
		for grows.Next() {
			var g grant
			if e = grows.Scan(&g.Project, &g.Task, &g.Run, &g.Restricted); e != nil {
				grows.Close()
				return p, e
			}
			gs = append(gs, g)
			derived := "local-verifier-" + strings.TrimPrefix(domain.Hash([]any{p.Root, g.Project}), "sha256:")[:32]
			if v.ID == derived {
				belongs = true
			}
		}
		e = grows.Err()
		grows.Close()
		if e != nil {
			return p, e
		}
		if !belongs {
			continue
		}
		if v.Revoked != 0 || v.Create != 0 || v.Roles != `["VERIFIER"]` || l.Root != p.Root {
			return p, errors.New("service principal or lineage drift")
		}
		if v.ID == p.Root {
			foundRoot = true
			if l.Parent.Valid || len(gs) != 0 {
				return p, errors.New("service root drift")
			}
		} else {
			if !l.Parent.Valid || l.Parent.String != p.Root || len(gs) != 1 {
				return p, errors.New("service child lineage/grants drift")
			}
			g := gs[0]
			derived := "local-verifier-" + strings.TrimPrefix(domain.Hash([]any{p.Root, g.Project}), "sha256:")[:32]
			if g.Project == "" || g.Task != "" || g.Run != "" || g.Restricted || derived != v.ID {
				return p, errors.New("service child grant drift")
			}
		}
		members = append(members, member{v, l, gs})
		delete(lines, v.ID)
	}
	if !foundRoot {
		return p, errors.New("service root missing")
	}
	for _, l := range lines {
		if l.Root == p.Root || (l.Parent.Valid && l.Parent.String == p.Root) {
			return p, errors.New("orphan service lineage")
		}
	}
	p.LineageHash = domain.Hash([]any{ownerRoot, members})
	for i, query := range replacementCensusSQL {
		if e = tx.QueryRowContext(ctx, query).Scan(&p.Census[i]); e != nil {
			return p, e
		}
	}
	for i, n := range p.Census {
		if n != 0 {
			return p, fmt.Errorf("unresolved census %d", i+1)
		}
	}
	return p, nil
}

func replacementCandidate(ctx context.Context, in RuntimeVerifierReplacementInput) (replacementPlan, error) {
	p, e := replacementSnapshot(ctx, in.DataRoot)
	if e != nil {
		return p, e
	}
	p.OperationID, p.CreatedAt, p.Manifest, p.RollbackOf = in.OperationID, time.Now().UTC().Format(time.RFC3339Nano), in.Manifest, in.RollbackOf
	p.OldBytes, e = replacementRead(filepath.Join(p.HostPath, "runtime-verifier-installation.json"), 64<<10)
	if e != nil {
		return p, e
	}
	p.OldSHA256 = domain.Digest(p.OldBytes)
	if p.OldSHA256 != in.ExpectRecordSHA256 {
		return p, errors.New("old registration raw digest changed")
	}
	var old runtimeVerifierRegistration
	if e = decodeRuntimeManaged(p.OldBytes, &old); e != nil {
		return p, e
	}
	if old.Schema != "researchos.runtime-verifier-registration.v1" || old.OwnerHost != p.HostID || old.OwnerPrincipal != p.Owner || old.ServiceRoot != p.Root || old.InstallHash != domain.Hash(old.Installation) {
		return p, errors.New("registered identity/hash mismatch")
	}
	p.OldHash, p.OldInstallationHash = domain.Hash(old), old.InstallHash
	raw, e := replacementRead(p.Manifest, 64<<10)
	if e != nil {
		return p, e
	}
	p.ManifestSHA256 = domain.Digest(raw)
	if p.ManifestSHA256 != in.ExpectManifestSHA256 {
		return p, errors.New("manifest raw digest changed")
	}
	p.Installation, e = LoadRuntimeVerifierInstallation(p.Manifest)
	if e != nil {
		return p, e
	}
	var decoded RuntimeVerifierInstallation
	if decodeRuntimeManaged(raw, &decoded) != nil || domain.Hash(decoded) != domain.Hash(p.Installation) {
		return p, errors.New("manifest raced validation")
	}
	image, e := replacementRead(p.Installation.Executable, 128<<20)
	if e != nil || domain.Digest(image) != p.Installation.ExecutableHash {
		return p, errors.New("executable raced validation")
	}
	if e != nil {
		return p, e
	}
	ni, oi := p.Installation, old.Installation
	ni.Executable, ni.ExecutableHash, ni.SourceCommit = oi.Executable, oi.ExecutableHash, oi.SourceCommit
	if domain.Hash(ni) != domain.Hash(oi) || domain.Hash(p.Installation) == old.InstallHash {
		return p, errors.New("only a changed executable/hash/commit installation is allowed")
	}
	old.Installation = p.Installation
	old.InstallHash = domain.Hash(p.Installation)
	p.NewBytes, e = json.MarshalIndent(old, "", "  ")
	if e != nil {
		return p, e
	}
	p.NewSHA256, p.NewHash, p.NewInstallationHash = domain.Digest(p.NewBytes), domain.Hash(old), old.InstallHash
	if p.RollbackOf != "" {
		if e = replacementValidateReverse(p); e != nil {
			return p, e
		}
	}
	return p, nil
}

func replacementLoadPlan(path, digest string) (replacementPlan, []byte, error) {
	var p replacementPlan
	raw, e := replacementRead(path, 256<<10)
	if e != nil {
		return p, nil, e
	}
	if !replacementDigest(digest) || domain.Digest(raw) != digest {
		return p, nil, errors.New("plan raw digest differs")
	}
	if e = decodeRuntimeManaged(raw, &p); e != nil {
		return p, nil, e
	}
	if e = replacementPlanValid(p); e != nil {
		return p, nil, e
	}
	return p, raw, nil
}
func replacementPlanValid(p replacementPlan) error {
	if p.Schema != replacementSchema || !replacementID(p.OperationID) || (p.RollbackOf != "" && (!replacementID(p.RollbackOf) || p.RollbackOf == p.OperationID)) || p.SchemaVersion != 24 || p.Census != [4]int{} || replacementPath(p.DataRoot) != nil || p.HostPath != filepath.Join(p.DataRoot, "host") || p.DBPath != filepath.Join(p.DataRoot, "researchos.sqlite") {
		return errors.New("invalid replacement plan")
	}
	if _, e := time.Parse(time.RFC3339Nano, p.CreatedAt); e != nil {
		return e
	}
	var old, new runtimeVerifierRegistration
	if decodeRuntimeManaged(p.OldBytes, &old) != nil || decodeRuntimeManaged(p.NewBytes, &new) != nil || domain.Digest(p.OldBytes) != p.OldSHA256 || domain.Digest(p.NewBytes) != p.NewSHA256 || domain.Hash(old) != p.OldHash || domain.Hash(new) != p.NewHash || old.InstallHash != p.OldInstallationHash || new.InstallHash != p.NewInstallationHash || domain.Hash(p.Installation) != p.NewInstallationHash || domain.Hash(old.Installation) != old.InstallHash || domain.Hash(new.Installation) != new.InstallHash {
		return errors.New("plan record linkage invalid")
	}
	if old.OwnerHost != p.HostID || old.OwnerPrincipal != p.Owner || old.ServiceRoot != p.Root || old.Schema != "researchos.runtime-verifier-registration.v1" || p.OldSHA256 == p.NewSHA256 {
		return errors.New("plan authority invalid")
	}
	expected := old
	expected.Installation = p.Installation
	expected.InstallHash = domain.Hash(p.Installation)
	raw, e := json.MarshalIndent(expected, "", "  ")
	if e != nil || !bytes.Equal(raw, p.NewBytes) {
		return errors.New("candidate bytes invalid")
	}
	ni, oi := p.Installation, old.Installation
	ni.Executable, ni.ExecutableHash, ni.SourceCommit = oi.Executable, oi.ExecutableHash, oi.SourceCommit
	if domain.Hash(ni) != domain.Hash(oi) {
		return errors.New("forbidden installation mutation")
	}
	return nil
}
func replacementSameSnapshot(a, b replacementPlan) bool {
	return a.DataRoot == b.DataRoot && a.HostPath == b.HostPath && a.DBPath == b.DBPath && a.FileIDs == b.FileIDs && a.PrincipalRef == b.PrincipalRef && a.HostID == b.HostID && a.Owner == b.Owner && a.Root == b.Root && a.StateSHA256 == b.StateSHA256 && a.LineageHash == b.LineageHash && a.SchemaVersion == b.SchemaVersion && a.Census == b.Census
}

// RuntimeVerifierReplacement owns the same native lease as normal control. It
// never constructs Host/NewCurrentMu, migrates, decrypts, or starts a process.
func RuntimeVerifierReplacement(ctx context.Context, in RuntimeVerifierReplacementInput) (out RuntimeVerifierReplacementResult, err error) {
	out = RuntimeVerifierReplacementResult{Schema: replacementSchema, Action: in.Action, OperationID: in.OperationID, State: "REJECTED", Outcome: "NOT_APPLIED"}
	if in.Action == "recover" {
		out.Outcome = "UNKNOWN"
	}
	defer func() {
		if err != nil && out.ErrorCode == "" {
			out.ErrorCode = "REPLACEMENT_REJECTED"
		}
		if err != nil && out.Outcome == "UNKNOWN" {
			out.ErrorCode = "REPLACEMENT_RECOVERY_REQUIRED"
		}
	}()
	if replacementPath(in.DataRoot) != nil {
		return out, errors.New("canonical data root required")
	}
	for i, p := range []string{in.DataRoot, filepath.Join(in.DataRoot, "host"), filepath.Join(in.DataRoot, "researchos.sqlite"), filepath.Join(in.DataRoot, "host", stateFile), filepath.Join(in.DataRoot, "host", "runtime-verifier-installation.json")} {
		if _, e := replacementIdentity(p, i < 2); e != nil {
			return out, e
		}
	}
	guards, e := guardWriteDirectories(filepath.Join(in.DataRoot, "host"))
	if e != nil {
		return out, e
	}
	defer closeWriteGuards(guards)
	dbPath, e := windows.UTF16PtrFromString(filepath.Join(in.DataRoot, "researchos.sqlite"))
	if e != nil {
		return out, e
	}
	dbGuard, e := windows.CreateFile(dbPath, windows.FILE_READ_ATTRIBUTES, windows.FILE_SHARE_READ|windows.FILE_SHARE_WRITE, nil, windows.OPEN_EXISTING, windows.FILE_FLAG_OPEN_REPARSE_POINT, 0)
	if e != nil {
		return out, e
	}
	defer windows.CloseHandle(dbGuard)
	lease, e := rt.AcquireDataRootLease(in.DataRoot)
	if e != nil {
		return out, e
	}
	defer lease.Close()
	if in.Action == "preflight" {
		if !replacementID(in.OperationID) || !replacementDigest(in.ExpectRecordSHA256) || !replacementDigest(in.ExpectManifestSHA256) || replacementPath(in.Out) != nil {
			return out, errors.New("invalid preflight arguments")
		}
		if _, e = os.Lstat(in.Out); !os.IsNotExist(e) {
			return out, errors.New("plan output must not exist")
		}
		// Never create a preflight artifact inside the product root.
		rel, e := filepath.Rel(in.DataRoot, in.Out)
		if e != nil || (rel != ".." && !strings.HasPrefix(rel, ".."+string(filepath.Separator))) {
			return out, errors.New("plan output must be outside product data")
		}
		if e = RuntimeVerifierReplacementStartupGate(lease); e != nil {
			return out, e
		}
		if _, e = os.Lstat(filepath.Join(in.DataRoot, "host", replacementJournal, in.OperationID)); !os.IsNotExist(e) {
			return out, errors.New("operation ID already exists")
		}
		p, e := replacementCandidate(ctx, in)
		out.ReadonlyCensus = p.Census
		if e != nil {
			return out, e
		}
		raw, e := json.MarshalIndent(p, "", "  ")
		if e != nil {
			return out, e
		}
		og, e := guardWriteDirectories(filepath.Dir(in.Out))
		if e != nil {
			return out, e
		}
		defer closeWriteGuards(og)
		if e = replacementWrite(filepath.Dir(in.Out), filepath.Base(in.Out), raw); e != nil {
			return out, e
		}
		return replacementResult(in.Action, p, domain.Digest(raw), "PREFLIGHT", "NOT_APPLIED"), nil
	}
	if in.Action != "commit" && in.Action != "recover" {
		return out, errors.New("unknown replacement action")
	}
	p, raw, e := replacementLoadPlan(in.Plan, in.ExpectPlanSHA256)
	if e != nil {
		return out, e
	}
	if p.DataRoot != in.DataRoot {
		return out, errors.New("plan root differs")
	}
	out = replacementResult(in.Action, p, in.ExpectPlanSHA256, "REJECTED", "NOT_APPLIED")
	if _, existing := os.Lstat(filepath.Join(p.HostPath, replacementJournal, p.OperationID)); in.Action == "recover" || existing == nil {
		out.Outcome = "UNKNOWN"
	}
	if in.Action == "recover" && (in.OperationID != p.OperationID || (in.RecoveryAction != "inspect" && in.RecoveryAction != "complete" && in.RecoveryAction != "abort")) {
		return out, errors.New("invalid recovery arguments")
	}
	snapshot, e := replacementSnapshot(ctx, in.DataRoot)
	out.ReadonlyCensus = snapshot.Census
	if e != nil {
		return out, e
	}
	if !replacementSameSnapshot(p, snapshot) {
		return out, errors.New("identity or readonly snapshot drift")
	}
	if in.Action == "recover" {
		out.Outcome = "UNKNOWN"
		return replacementRecover(in, p, raw)
	}
	dir := filepath.Join(p.HostPath, replacementJournal, p.OperationID)
	if _, e = os.Lstat(dir); e == nil {
		in.RecoveryAction = "inspect"
		result, err := replacementRecover(in, p, raw)
		if err == nil && result.State != "COMMITTED" {
			return result, errors.New("existing operation requires explicit recover")
		}
		return result, err
	} else if !os.IsNotExist(e) {
		return out, e
	}
	if e = RuntimeVerifierReplacementStartupGate(lease); e != nil {
		return out, e
	}
	fresh, e := replacementCandidate(ctx, RuntimeVerifierReplacementInput{DataRoot: p.DataRoot, OperationID: p.OperationID, Manifest: p.Manifest, ExpectRecordSHA256: p.OldSHA256, ExpectManifestSHA256: p.ManifestSHA256, RollbackOf: p.RollbackOf})
	if e != nil {
		return out, e
	}
	if !replacementSameSnapshot(p, fresh) || !bytes.Equal(fresh.NewBytes, p.NewBytes) || fresh.OldSHA256 != p.OldSHA256 {
		return out, errors.New("stale plan")
	}
	out.Outcome = "UNKNOWN"
	if e = replacementCreateDirectory(filepath.Join(p.HostPath, replacementJournal)); e != nil {
		return out, e
	}
	if e = replacementMkdirPrivate(dir); e != nil {
		return out, e
	}
	if e = replacementACL(dir, true, true); e != nil {
		return out, e
	}
	journalGuards, e := guardWriteDirectories(dir)
	if e != nil {
		return out, e
	}
	defer closeWriteGuards(journalGuards)
	replacementBoundary("directory")
	for _, v := range []struct {
		name string
		data []byte
	}{{"plan.json", raw}, {"old-registration.bin", p.OldBytes}, {"new-registration.bin", p.NewBytes}} {
		if e = replacementWrite(dir, v.name, v.data); e != nil {
			return out, e
		}
	}
	replacementBoundary("snapshots")
	if e = replacementAppend(dir, p, raw, "PREPARED"); e != nil {
		return out, e
	}
	replacementBoundary("prepared")
	if e = replacementWrite(dir, "stage.bin", p.NewBytes); e != nil {
		return out, e
	}
	replacementBoundary("stage")
	fresh, e = replacementCandidate(ctx, RuntimeVerifierReplacementInput{DataRoot: p.DataRoot, OperationID: p.OperationID, Manifest: p.Manifest, ExpectRecordSHA256: p.OldSHA256, ExpectManifestSHA256: p.ManifestSHA256, RollbackOf: p.RollbackOf})
	if e != nil || !replacementSameSnapshot(p, fresh) {
		return out, errors.New("final preconditions changed")
	}
	target := filepath.Join(p.HostPath, "runtime-verifier-installation.json")
	handle, e := openWriteTarget(target)
	if e != nil {
		return out, e
	}
	defer handle.Close()
	current, e := readGuardedBytes(handle)
	if e != nil || !bytes.Equal(current, p.OldBytes) {
		return out, errors.New("final raw CAS failed")
	}
	if e = replacementAppend(dir, p, raw, "PUBLISHING"); e != nil {
		return out, e
	}
	replacementBoundary("publishing")
	if e = replacementReplace(target, filepath.Join(dir, "stage.bin"), filepath.Join(dir, "actual-backup.bin")); e != nil {
		return out, e
	}
	if e = handle.Close(); e != nil {
		return out, e
	}
	replacementBoundary("replaced")
	if e = replacementApplied(p, dir); e != nil {
		return out, e
	}
	replacementBoundary("before-committed")
	if e = replacementAppend(dir, p, raw, "COMMITTED"); e != nil {
		return out, e
	}
	replacementBoundary("committed")
	if e = replacementApplied(p, dir); e != nil {
		return out, e
	}
	return replacementResult(in.Action, p, in.ExpectPlanSHA256, "COMMITTED", "APPLIED"), nil
}

func replacementResult(action string, p replacementPlan, digest, state, outcome string) RuntimeVerifierReplacementResult {
	return RuntimeVerifierReplacementResult{Schema: replacementSchema, Action: action, OperationID: p.OperationID, State: state, Outcome: outcome, PlanSHA256: digest, OldRecordSHA256: p.OldSHA256, NewRecordSHA256: p.NewSHA256, RegistrationHash: p.NewHash, InstallationHash: p.NewInstallationHash, ReadonlyCensus: p.Census}
}
