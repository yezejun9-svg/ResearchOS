//go:build windows

package host

import (
	"bytes"
	"context"
	"crypto/sha256"
	"database/sql"
	"encoding/hex"
	"encoding/json"
	"errors"
	"io"
	"os"
	"path/filepath"
	"strings"
	"unsafe"

	"golang.org/x/sys/windows"
	rt "researchos.local/research-os/adapters/runtime"
	"researchos.local/research-os/internal/canonical"
	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/qualificationmaintenancejournal"
	"researchos.local/research-os/internal/recoveryboundary"
	"researchos.local/research-os/internal/store"
)

type QualificationMaintenanceInput struct {
	Action, DataRoot, Proposal, Out, Plan, PlanSHA256, OperationID string
}

type QualificationMaintenanceResult struct {
	Schema      string `json:"schema"`
	Action      string `json:"action"`
	State       string `json:"state"`
	OperationID string `json:"operation_id"`
	PlanSHA256  string `json:"plan_sha256"`
	OutcomeHash string `json:"outcome_hash,omitempty"`
}

type qualificationProposal struct {
	Schema             string                                `json:"schema"`
	OperationID        string                                `json:"operation_id"`
	BoundaryPlanSHA256 string                                `json:"boundary_plan_sha256"`
	Subject            domain.HistoricalQualificationSubject `json:"subject"`
}

// The post-restart reader runs under a distinct management SID. It reads the
// frozen business host state without asserting that the management token is
// the business Owner. Its no-write/no-delete handle stays open across SQL.
type qualificationBusinessIdentityHold struct {
	file                                                     *os.File
	volume                                                   uint64
	fileID                                                   [16]byte
	final, descriptor, hash, ownerID, ownerRoot, businessSID string
}

func qualificationHostFileID(h windows.Handle) (uint64, [16]byte, error) {
	var raw struct {
		VolumeSerialNumber uint64
		FileID             [16]byte
	}
	e := windows.GetFileInformationByHandleEx(h, windows.FileIdInfo, (*byte)(unsafe.Pointer(&raw)), uint32(unsafe.Sizeof(raw)))
	return raw.VolumeSerialNumber, raw.FileID, e
}

func qualificationHostFinal(h windows.Handle) (string, error) {
	buf := make([]uint16, 32768)
	n, e := windows.GetFinalPathNameByHandle(h, &buf[0], uint32(len(buf)), 0)
	if e != nil || n == 0 || n >= uint32(len(buf)) {
		return "", errors.New("business host state final path unavailable")
	}
	return windows.UTF16ToString(buf[:n]), nil
}

func openQualificationBusinessIdentity(root, businessSID, expectedHash string) (*qualificationBusinessIdentityHold, error) {
	path := filepath.Join(root, "host", stateFile)
	wide, e := windows.UTF16PtrFromString(path)
	if e != nil {
		return nil, e
	}
	h, e := windows.CreateFile(wide, windows.GENERIC_READ|windows.READ_CONTROL, windows.FILE_SHARE_READ, nil,
		windows.OPEN_EXISTING, windows.FILE_FLAG_OPEN_REPARSE_POINT, 0)
	if e != nil {
		return nil, e
	}
	fail := func(e error) (*qualificationBusinessIdentityHold, error) { windows.CloseHandle(h); return nil, e }
	var info windows.ByHandleFileInformation
	if e = windows.GetFileInformationByHandle(h, &info); e != nil {
		return fail(e)
	}
	if info.FileAttributes&(windows.FILE_ATTRIBUTE_DIRECTORY|windows.FILE_ATTRIBUTE_REPARSE_POINT) != 0 || info.NumberOfLinks != 1 {
		return fail(errors.New("business host state alias or kind invalid"))
	}
	volume, id, e := qualificationHostFileID(h)
	if e != nil {
		return fail(e)
	}
	final, e := qualificationHostFinal(h)
	if e != nil {
		return fail(e)
	}
	sd, e := windows.GetSecurityInfo(h, windows.SE_FILE_OBJECT, windows.OWNER_SECURITY_INFORMATION|windows.DACL_SECURITY_INFORMATION)
	if e != nil || sd == nil {
		return fail(errors.New("business host state descriptor unavailable"))
	}
	owner, _, e := sd.Owner()
	if e != nil || owner == nil || owner.String() != businessSID {
		return fail(errors.New("business host state owner SID changed"))
	}
	file := os.NewFile(uintptr(h), path)
	infoFile, e := file.Stat()
	if e != nil || infoFile.Size() < 1 || infoFile.Size() > 64<<10 {
		file.Close()
		return nil, errors.New("business host state size invalid")
	}
	raw, e := io.ReadAll(io.LimitReader(file, 64<<10+1))
	if e != nil || int64(len(raw)) != infoFile.Size() {
		file.Close()
		return nil, errors.New("business host state read changed")
	}
	digest := sha256.Sum256(raw)
	actual := hex.EncodeToString(digest[:])
	if actual != expectedHash {
		file.Close()
		return nil, errors.New("business host state hash differs")
	}
	var state hostState
	if e = decodeRuntimeManaged(raw, &state); e != nil {
		file.Close()
		return nil, e
	}
	if state.Version != 1 || state.PrincipalID == "" || state.PrincipalRef == "" || state.HostInstanceID == "" {
		file.Close()
		return nil, errors.New("business host state incomplete")
	}
	return &qualificationBusinessIdentityHold{file: file, volume: volume, fileID: id, final: final,
		descriptor: sd.String(), hash: actual, ownerID: state.PrincipalID, businessSID: businessSID}, nil
}

func (h *qualificationBusinessIdentityHold) Check() error {
	if h == nil || h.file == nil {
		return errors.New("business identity hold absent")
	}
	native := windows.Handle(h.file.Fd())
	volume, id, e := qualificationHostFileID(native)
	if e != nil || volume != h.volume || id != h.fileID {
		return errors.New("business identity native ID changed")
	}
	final, e := qualificationHostFinal(native)
	if e != nil || final != h.final {
		return errors.New("business identity final path changed")
	}
	sd, e := windows.GetSecurityInfo(native, windows.SE_FILE_OBJECT, windows.OWNER_SECURITY_INFORMATION|windows.DACL_SECURITY_INFORMATION)
	if e != nil || sd == nil || sd.String() != h.descriptor {
		return errors.New("business identity descriptor changed")
	}
	if _, e = h.file.Seek(0, io.SeekStart); e != nil {
		return e
	}
	raw, e := io.ReadAll(io.LimitReader(h.file, 64<<10+1))
	if e != nil {
		return e
	}
	sum := sha256.Sum256(raw)
	if hex.EncodeToString(sum[:]) != h.hash {
		return errors.New("business host state changed")
	}
	return nil
}

func (h *qualificationBusinessIdentityHold) Close() error {
	if h == nil || h.file == nil {
		return errors.New("business identity hold absent")
	}
	e := h.file.Close()
	h.file = nil
	return e
}

func (h *qualificationBusinessIdentityHold) ValidateOwner(ctx context.Context, db *sql.DB) (string, error) {
	if e := h.Check(); e != nil {
		return "", e
	}
	rows, e := db.QueryContext(ctx, `SELECT id,roles FROM auth_principals WHERE revoked=0 ORDER BY id`)
	if e != nil {
		return "", e
	}
	count := 0
	for rows.Next() {
		var id, rolesRaw string
		if e = rows.Scan(&id, &rolesRaw); e != nil {
			break
		}
		var roles []string
		if e = json.Unmarshal([]byte(rolesRaw), &roles); e != nil {
			break
		}
		for _, role := range roles {
			if role == "OWNER" {
				count++
				if id != h.ownerID {
					e = errors.New("business Owner principal changed")
				}
				break
			}
		}
		if e != nil {
			break
		}
	}
	if e == nil {
		e = rows.Err()
	}
	rows.Close()
	if e != nil {
		return "", e
	}
	if count != 1 {
		return "", errors.New("business Owner census differs")
	}
	var root string
	if e = db.QueryRowContext(ctx, `SELECT root FROM orchestration_identity WHERE principal=?`, h.ownerID).Scan(&root); e != nil || root == "" {
		return "", errors.New("business Owner root unavailable")
	}
	h.ownerRoot = root
	return root, nil
}

const qualificationProposalSchema = "researchos.qualification-failure-maintenance-proposal.v1"
const qualificationResultSchema = "researchos.qualification-failure-maintenance-result.v1"

func qualificationPinnedSource() domain.HistoricalQualificationSource {
	return domain.HistoricalQualificationSource{
		BridgeSHA256:          "sha256:10b1a3bfa74132fbed965df31fd90125b90b1470556001e254af360c35451bce",
		StdoutSHA256:          "sha256:b83971315132cc02e5f980339c25e9df7cbc0b6c92bb6f74febbe342f093e7f5",
		ManifestHash:          "sha256:adfc970e700a5804a96765219d2a85fb6439bf481afb6a8972048d921f032715",
		SourceCommit:          "4f4023c956f84d65743f39ce77d6c8899a21ada1",
		CoreSHA256:            "sha256:c4a3b498fc15120828427b237b8176710acfd7a9333cd24e9911fded9cd63e24",
		WorkerSHA256:          "sha256:5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6",
		BundleSHA256:          "sha256:2a8e70132a914affc6122c1f1db29cfa315b655c93d4200145852ebbc853d441",
		WorkerConfigSHA256:    "sha256:6a6b5130bc17ef442a9ef3d7fe915e533ebcc93c0442187ac9d38da2df9bbcfd",
		RequestSHA256:         "sha256:d7ec1d721aad5164fa0d663d0b5348418c04e32c66c237aea447024115e1d60b",
		FirstGateSourceSHA256: "sha256:12d143c24e359b473938d77ee58662fe43941edb5f08f03c31adf4f9cef2fc20",
		BuildSHA256:           "sha256:5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6",
		PID:                   69860, Created: 1792057406096619100, Job: `Local\ResearchOS.W10.1792057404322293200`,
	}
}

func qualificationExactSubject(s domain.HistoricalQualificationSubject) bool {
	return s.ProjectID == "a7ebcf2a322c6abcf87e043f601ee804" &&
		s.TaskID == "0469d97b91b04fd7fdeed77770ea1bed" &&
		s.RunID == "f3dcb996b2e43cf52cba874be7abfc70" &&
		s.RuntimeID == "db26746ff0420ca156d315f0de00fb53" &&
		s.Epoch == 1 && s.DispatchKey == "705b11ec99044fef19e85f57e2d2b712"
}

func qualificationReadStrict(path string, limit int64, out any) ([]byte, error) {
	info, e := os.Lstat(path)
	if e != nil || !info.Mode().IsRegular() || info.Size() < 1 || info.Size() > limit {
		return nil, errors.New("qualification input absent or invalid")
	}
	raw, e := os.ReadFile(path)
	if e != nil || int64(len(raw)) != info.Size() {
		return nil, errors.New("qualification input changed")
	}
	if _, e = canonical.JSON(raw); e != nil {
		return nil, e
	}
	d := json.NewDecoder(bytes.NewReader(raw))
	d.DisallowUnknownFields()
	if e = d.Decode(out); e != nil {
		return nil, e
	}
	var tail any
	if d.Decode(&tail) != io.EOF {
		return nil, errors.New("qualification input trailing JSON")
	}
	return raw, nil
}

func qualificationExternalPath(root, path string) error {
	if !filepath.IsAbs(path) || filepath.Clean(path) != path || strings.Contains(path[len(filepath.VolumeName(path)):], ":") {
		return errors.New("qualification external path invalid")
	}
	rel, e := filepath.Rel(root, path)
	if e != nil || rel != ".." && !strings.HasPrefix(rel, ".."+string(filepath.Separator)) {
		return errors.New("qualification external path within data root")
	}
	realRoot, e := filepath.EvalSymlinks(root)
	if e != nil {
		return e
	}
	realParent, e := filepath.EvalSymlinks(filepath.Dir(path))
	if e != nil {
		return e
	}
	realRel, e := filepath.Rel(realRoot, realParent)
	if e != nil || realRel != ".." && !strings.HasPrefix(realRel, ".."+string(filepath.Separator)) {
		return errors.New("qualification external parent aliases data root")
	}
	return nil
}

func qualificationJournalRaw(plan domain.HistoricalQualificationPlan, raw []byte) ([]byte, error) {
	core, before, after, subject, evidence := plan.JournalHashes()
	return json.Marshal(qualificationmaintenancejournal.JournalPlan{
		Schema: "researchos.qualification-failure-maintenance-plan.v1", OperationID: plan.OperationID,
		DataRoot: plan.DataRoot, Database: plan.Database, PlanHash: core, BeforeHash: before, AfterHash: after,
		SubjectHash: subject, EvidenceHash: evidence, FullPlan: append(json.RawMessage(nil), raw...)})
}

func qualificationResult(action, state, operation, digest string, outcome ...string) QualificationMaintenanceResult {
	result := QualificationMaintenanceResult{Schema: qualificationResultSchema, Action: action, State: state, OperationID: operation, PlanSHA256: digest}
	if len(outcome) > 0 {
		result.OutcomeHash = outcome[0]
	}
	return result
}

func RunQualificationFailureMaintenance(ctx context.Context, input QualificationMaintenanceInput) (out QualificationMaintenanceResult, retErr error) {
	root := input.DataRoot
	if ctx.Err() != nil {
		return out, ctx.Err()
	}
	if !filepath.IsAbs(root) || filepath.Clean(root) != root || strings.Contains(root[len(filepath.VolumeName(root)):], ":") {
		return out, errors.New("qualification data root invalid")
	}
	database := filepath.Join(root, "researchos.sqlite")
	var plan domain.HistoricalQualificationPlan
	var proposal qualificationProposal
	var raw []byte
	var e error
	if input.Action == "preflight" {
		if e = qualificationExternalPath(root, input.Proposal); e != nil {
			return out, e
		}
		if e = qualificationExternalPath(root, input.Out); e != nil {
			return out, e
		}
		if _, e = qualificationReadStrict(input.Proposal, 64<<10, &proposal); e != nil {
			return out, e
		}
		if proposal.Schema != qualificationProposalSchema || !qualificationExactSubject(proposal.Subject) {
			return out, errors.New("qualification proposal invalid")
		}
		if _, e = os.Lstat(input.Out); !os.IsNotExist(e) {
			return out, errors.New("qualification output already exists or unavailable")
		}
	} else if input.Action == "commit" || input.Action == "recover" || input.Action == "abort" {
		if e = qualificationExternalPath(root, input.Plan); e != nil {
			return out, e
		}
		if raw, e = qualificationReadStrict(input.Plan, 256<<10, &plan); e != nil {
			return out, e
		}
		if domain.Digest(raw) != input.PlanSHA256 || input.OperationID != plan.OperationID || plan.DataRoot != root || plan.Database != database ||
			!qualificationExactSubject(plan.Subject) || plan.Schema != "researchos.qualification-failure-maintenance-full-plan.v1" {
			return out, errors.New("qualification reviewed plan differs")
		}
		pinned := qualificationPinnedSource()
		pinned.StderrSHA256 = plan.Source.StderrSHA256
		if pinned != plan.Source {
			return out, errors.New("qualification source pins differ")
		}
	} else {
		return out, errors.New("qualification action invalid")
	}
	operation, boundaryHash := plan.OperationID, plan.BoundaryPlanSHA256
	if input.Action == "preflight" {
		operation, boundaryHash = proposal.OperationID, proposal.BoundaryPlanSHA256
	}
	boundary, boundaryState, e := recoveryboundary.ReadBoundaryPlan(root, operation, boundaryHash)
	if e != nil {
		return out, e
	}
	if boundary.DataRoot.Path != root || boundary.Database.Path != database || boundary.BusinessSID == "" ||
		boundaryState != "BOOT_OBSERVED" && !((input.Action == "recover" || input.Action == "commit") && boundaryState == "C_DURABLE") {
		return out, errors.New("qualification boundary not boot observed")
	}
	subject := plan.Subject
	if input.Action == "preflight" {
		subject = proposal.Subject
	}
	if boundary.SubjectSHA256 != strings.TrimPrefix(domain.Hash(subject), "sha256:") {
		return out, errors.New("qualification boundary subject differs")
	}
	var journalRaw []byte
	if input.Action != "preflight" {
		journalRaw, e = qualificationJournalRaw(plan, raw)
		if e != nil {
			return out, e
		}
	}
	journalDigest := domain.Digest(journalRaw)
	journalPath := filepath.Join(root, "host", qualificationmaintenancejournal.QualificationNamespace, operation)
	_, journalErr := os.Lstat(journalPath)
	journalExists := journalErr == nil
	if journalErr != nil && !os.IsNotExist(journalErr) {
		return out, journalErr
	}
	if input.Action == "preflight" && journalExists {
		return out, errors.New("qualification operation already exists")
	}
	var lease *rt.DataRootLease
	if input.Action == "recover" || input.Action == "abort" || input.Action == "commit" && journalExists {
		lease, e = rt.AcquireDataRootLeaseForQualificationRecovery(root, operation, journalDigest)
	} else {
		lease, e = rt.AcquireDataRootLease(root)
	}
	if e != nil {
		return out, e
	}
	defer func() { retErr = errors.Join(retErr, lease.Close()) }()
	if boundaryState == "C_DURABLE" {
		_, status, e := qualificationmaintenancejournal.OpenOwnInspection(root, qualificationmaintenancejournal.QualificationNamespace, operation, journalDigest)
		if e != nil || status.State != "DURABLE" {
			return out, errors.New("qualification durable journal unavailable")
		}
		db, e := store.OpenQualificationMaintenance(ctx, database)
		if e != nil {
			return out, e
		}
		defer func() { retErr = errors.Join(retErr, db.Close()) }()
		business, e := openQualificationBusinessIdentity(root, boundary.BusinessSID, boundary.HostIdentitySHA256)
		if e != nil {
			return out, e
		}
		defer func() { retErr = errors.Join(retErr, business.Close()) }()
		ownerRoot, e := business.ValidateOwner(ctx, db)
		if e != nil {
			return out, e
		}
		if plan.AuthorID != business.ownerID || plan.OwnerRoot != ownerRoot || plan.SID != boundary.BusinessSID {
			return out, errors.New("qualification replay business Owner differs")
		}
		classified, e := domain.ClassifyHistoricalQualification(ctx, db, plan, input.PlanSHA256)
		if e != nil || classified != "APPLIED" {
			return out, errors.New("qualification durable replay SQL image differs")
		}
		return qualificationResult(input.Action, "DURABLE", operation, input.PlanSHA256, plan.OutcomeHash), nil
	}
	q, e := recoveryboundary.OpenCurrentQuiescence(ctx, lease, root, database, operation, boundaryHash)
	if e != nil {
		return out, e
	}
	defer func() { retErr = errors.Join(retErr, q.Close()) }()
	if e = q.Check(ctx, lease, root, database, operation, boundaryHash); e != nil {
		return out, e
	}
	db, e := store.OpenQualificationMaintenance(ctx, database)
	if e != nil {
		return out, e
	}
	defer func() { retErr = errors.Join(retErr, db.Close()) }()
	business, e := openQualificationBusinessIdentity(root, boundary.BusinessSID, boundary.HostIdentitySHA256)
	if e != nil {
		return out, e
	}
	defer func() { retErr = errors.Join(retErr, business.Close()) }()
	ownerRoot, e := business.ValidateOwner(ctx, db)
	if e != nil {
		return out, e
	}
	if input.Action != "preflight" && (plan.AuthorID != business.ownerID || plan.OwnerRoot != ownerRoot || plan.SID != boundary.BusinessSID) {
		return out, errors.New("qualification planned business Owner differs")
	}
	contracts, e := filepath.Abs(filepath.Join("spec", "v2.0", "contracts"))
	if e != nil {
		return out, e
	}
	if input.Action == "preflight" {
		plan, e = domain.PlanHistoricalQualification(ctx, db, contracts, proposal.Subject, qualificationPinnedSource(), business.ownerID, root, operation, boundaryHash, boundary.BusinessSID)
		if e != nil {
			return out, e
		}
		raw, e = json.MarshalIndent(plan, "", "  ")
		if e != nil {
			return out, e
		}
		f, e := os.OpenFile(input.Out, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
		if e != nil {
			return out, e
		}
		_, writeErr := f.Write(raw)
		closeErr := f.Close()
		if e = errors.Join(writeErr, closeErr); e != nil {
			return out, e
		}
		return qualificationResult(input.Action, "PREFLIGHT", operation, domain.Digest(raw)), nil
	}
	if input.Action == "commit" {
		if journalExists {
			_, existing, e := qualificationmaintenancejournal.OpenOwnInspection(root, qualificationmaintenancejournal.QualificationNamespace, operation, journalDigest)
			if e != nil {
				return out, e
			}
			if existing.State != "DURABLE" && existing.State != "DB_COMMITTED_OBSERVED" {
				return out, errors.New("qualification pending or aborted operation requires explicit recover")
			}
		} else {
			if e = business.Check(); e != nil {
				return out, e
			}
			if e = q.Check(ctx, lease, root, database, operation, boundaryHash); e != nil {
				return out, e
			}
			actual, startErr := qualificationmaintenancejournal.StartQualification(root, journalRaw)
			if startErr != nil || actual != journalDigest {
				return out, errors.New("qualification BEGIN unavailable")
			}
			if _, e = domain.ApplyHistoricalQualification(ctx, db, contracts, plan, input.PlanSHA256, q, lease); e != nil {
				return out, e
			}
			if e = business.Check(); e != nil {
				return out, e
			}
		}
	}
	_, status, e := qualificationmaintenancejournal.OpenOwnInspection(root, qualificationmaintenancejournal.QualificationNamespace, operation, journalDigest)
	if e != nil {
		return out, e
	}
	classification, e := domain.ClassifyHistoricalQualification(ctx, db, plan, input.PlanSHA256)
	if e != nil {
		return out, e
	}
	if classification == "NOT_APPLIED" {
		if e = business.Check(); e != nil {
			return out, e
		}
		if status.State == "BEGIN" {
			if e = qualificationmaintenancejournal.AppendQualification(root, operation, journalDigest, "CLASSIFIED_NOT_APPLIED", ""); e != nil {
				return out, e
			}
			status.State = "CLASSIFIED_NOT_APPLIED"
		}
		if input.Action == "abort" && status.State == "CLASSIFIED_NOT_APPLIED" {
			if e = qualificationmaintenancejournal.AppendQualification(root, operation, journalDigest, "ABORTED", ""); e != nil {
				return out, e
			}
			return qualificationResult(input.Action, "ABORTED", operation, input.PlanSHA256), nil
		}
		return qualificationResult(input.Action, status.State, operation, input.PlanSHA256), nil
	}
	if input.Action == "abort" || classification != "APPLIED" {
		return out, errors.New("qualification SQL state unresolved or applied abort denied")
	}
	if status.State == "BEGIN" || status.State == "CLASSIFIED_NOT_APPLIED" {
		if e = qualificationmaintenancejournal.AppendQualification(root, operation, journalDigest, "DB_COMMITTED_OBSERVED", plan.OutcomeHash); e != nil {
			return out, e
		}
		status.State = "DB_COMMITTED_OBSERVED"
	}
	if status.State == "DB_COMMITTED_OBSERVED" {
		if e = qualificationmaintenancejournal.AppendQualification(root, operation, journalDigest, "DURABLE", plan.OutcomeHash); e != nil {
			return out, e
		}
		status.State = "DURABLE"
	}
	if status.State != "DURABLE" {
		return out, errors.New("qualification terminal journal mismatch")
	}
	if e = business.Check(); e != nil {
		return out, e
	}
	if e = recoveryboundary.MarkCDurable(ctx, q, lease, root, database, operation, boundaryHash, journalDigest); e != nil {
		return out, e
	}
	return qualificationResult(input.Action, "DURABLE", operation, input.PlanSHA256, plan.OutcomeHash), nil
}
