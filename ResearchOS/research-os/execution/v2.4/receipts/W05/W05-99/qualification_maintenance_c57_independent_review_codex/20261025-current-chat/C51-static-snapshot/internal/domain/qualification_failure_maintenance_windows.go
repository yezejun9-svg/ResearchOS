//go:build windows

package domain

import (
	"bytes"
	"context"
	"crypto/sha256"
	"database/sql"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"sync"
	"time"
	"unsafe"

	"golang.org/x/sys/windows"
	rt "researchos.local/research-os/adapters/runtime"
	"researchos.local/research-os/internal/canonical"
	"researchos.local/research-os/internal/recoveryboundary"
	"researchos.local/research-os/internal/store"
)

// Historical qualification evidence has no original typed B rejection. Its
// native source hold and private proof kind are deliberately separate from the
// online qualification closure.
type historicalQualificationNative struct {
	journal    rt.BridgeJournal
	frames     [3]rt.BridgeFrame
	bridgeHash string
	stdoutHash string
	stderrHash string
	modelHash  string
	modelRaw   []byte
}

type historicalNativeID struct {
	volume uint64
	file   [16]byte
}

type historicalNativeFile struct {
	path               string
	file               *os.File
	identity           historicalNativeID
	final              string
	owner              string
	securityDescriptor string
	digest             string
	size               int64
}

type historicalQualificationHold struct {
	mu     sync.Mutex
	files  []*historicalNativeFile
	owner  *os.File
	closed bool
}

func historicalNativeIdentity(h windows.Handle) (historicalNativeID, error) {
	var raw struct {
		VolumeSerialNumber uint64
		FileID             [16]byte
	}
	if err := windows.GetFileInformationByHandleEx(h, windows.FileIdInfo, (*byte)(unsafe.Pointer(&raw)), uint32(unsafe.Sizeof(raw))); err != nil {
		return historicalNativeID{}, err
	}
	return historicalNativeID{volume: raw.VolumeSerialNumber, file: raw.FileID}, nil
}

func historicalFinalPath(h windows.Handle) (string, error) {
	buf := make([]uint16, 32768)
	n, err := windows.GetFinalPathNameByHandle(h, &buf[0], uint32(len(buf)), 0)
	if err != nil || n == 0 || n >= uint32(len(buf)) {
		return "", errors.New("historical source final path unavailable")
	}
	return windows.UTF16ToString(buf[:n]), nil
}

func openHistoricalNative(path string, directory, requireOwner bool, sid string) (*historicalNativeFile, error) {
	if !filepath.IsAbs(path) || filepath.Clean(path) != path || strings.Contains(path[len(filepath.VolumeName(path)):], ":") {
		return nil, errors.New("historical source path invalid")
	}
	wide, err := windows.UTF16PtrFromString(path)
	if err != nil {
		return nil, err
	}
	sharing := uint32(windows.FILE_SHARE_READ)
	if directory {
		sharing |= windows.FILE_SHARE_WRITE
	}
	h, err := windows.CreateFile(wide, windows.GENERIC_READ|windows.READ_CONTROL,
		sharing, nil, windows.OPEN_EXISTING,
		windows.FILE_FLAG_OPEN_REPARSE_POINT|windows.FILE_FLAG_BACKUP_SEMANTICS, 0)
	if err != nil {
		return nil, err
	}
	fail := func(err error) (*historicalNativeFile, error) {
		windows.CloseHandle(h)
		return nil, err
	}
	var info windows.ByHandleFileInformation
	if err := windows.GetFileInformationByHandle(h, &info); err != nil {
		return fail(err)
	}
	if info.FileAttributes&windows.FILE_ATTRIBUTE_REPARSE_POINT != 0 ||
		(info.FileAttributes&windows.FILE_ATTRIBUTE_DIRECTORY != 0) != directory ||
		(!directory && info.NumberOfLinks != 1) {
		return fail(errors.New("historical source reparse, kind or hardlink mismatch"))
	}
	id, err := historicalNativeIdentity(h)
	if err != nil {
		return fail(err)
	}
	final, err := historicalFinalPath(h)
	if err != nil {
		return fail(err)
	}
	sd, err := windows.GetSecurityInfo(h, windows.SE_FILE_OBJECT, windows.OWNER_SECURITY_INFORMATION|windows.DACL_SECURITY_INFORMATION)
	if err != nil || sd == nil {
		return fail(errors.New("historical source security descriptor unavailable"))
	}
	owner, _, err := sd.Owner()
	if err != nil || owner == nil || (requireOwner && owner.String() != sid) {
		return fail(errors.New("historical source owner differs"))
	}
	return &historicalNativeFile{path: path, file: os.NewFile(uintptr(h), path), identity: id,
		final: final, owner: owner.String(), securityDescriptor: sd.String()}, nil
}

func (f *historicalNativeFile) check() error {
	if f == nil || f.file == nil {
		return errors.New("historical native file absent")
	}
	h := windows.Handle(f.file.Fd())
	id, err := historicalNativeIdentity(h)
	if err != nil || id != f.identity {
		return errors.New("historical native identity drift")
	}
	final, err := historicalFinalPath(h)
	if err != nil || final != f.final {
		return errors.New("historical final path drift")
	}
	sd, err := windows.GetSecurityInfo(h, windows.SE_FILE_OBJECT, windows.OWNER_SECURITY_INFORMATION|windows.DACL_SECURITY_INFORMATION)
	if err != nil || sd == nil || sd.String() != f.securityDescriptor {
		return errors.New("historical source security descriptor unavailable")
	}
	owner, _, err := sd.Owner()
	if err != nil || owner == nil || owner.String() != f.owner {
		return errors.New("historical source owner drift")
	}
	if f.digest != "" {
		if _, err := f.file.Seek(0, io.SeekStart); err != nil {
			return err
		}
		h := sha256.New()
		n, err := io.Copy(h, io.LimitReader(f.file, f.size+1))
		if err != nil || n != f.size || "sha256:"+hex.EncodeToString(h.Sum(nil)) != f.digest {
			return errors.New("historical source bytes drift")
		}
	}
	return nil
}

func (h *historicalQualificationHold) Check() error {
	if h == nil {
		return errors.New("historical qualification hold required")
	}
	h.mu.Lock()
	defer h.mu.Unlock()
	if h.closed || h.owner == nil {
		return errors.New("historical qualification hold closed")
	}
	for _, f := range h.files {
		if err := f.check(); err != nil {
			return err
		}
	}
	return nil
}

func (h *historicalQualificationHold) Close() error {
	if h == nil {
		return nil
	}
	h.mu.Lock()
	defer h.mu.Unlock()
	if h.closed {
		return nil
	}
	h.closed = true
	var err error
	for i := len(h.files) - 1; i >= 0; i-- {
		err = errors.Join(err, h.files[i].file.Close())
	}
	if h.owner != nil {
		err = errors.Join(err, h.owner.Close())
	}
	return err
}

// The transaction uses a non-canceling lifetime while individual SQL calls
// use the caller's context. This makes a canceled call end in this synchronous
// Rollback, whose driver return precedes release of the native source hold.
func finishHistoricalQualificationTx(tx *sql.Tx, committed bool, hold *historicalQualificationHold) error {
	var err error
	if tx != nil && !committed {
		err = tx.Rollback()
	}
	return errors.Join(err, hold.Close())
}

func (h *historicalQualificationHold) add(path string, directory, requireOwner bool, sid string) (*historicalNativeFile, error) {
	f, err := openHistoricalNative(path, directory, requireOwner, sid)
	if err == nil {
		h.files = append(h.files, f)
	}
	return f, err
}

func historicalNativeRead(f *historicalNativeFile, limit int64, allowEmpty bool) ([]byte, error) {
	if _, err := f.file.Seek(0, io.SeekStart); err != nil {
		return nil, err
	}
	raw, err := io.ReadAll(io.LimitReader(f.file, limit+1))
	if err != nil || (!allowEmpty && len(raw) == 0) || int64(len(raw)) > limit {
		return nil, errors.New("historical source bounded read failed")
	}
	f.size, f.digest = int64(len(raw)), Digest(raw)
	return raw, f.check()
}

func hashHistoricalNative(f *historicalNativeFile, limit int64, expected string) error {
	if f == nil || f.file == nil || expected == "" {
		return errors.New("historical staged input required")
	}
	info, err := f.file.Stat()
	if err != nil || info.Size() <= 0 || info.Size() > limit {
		return errors.New("historical staged input size invalid")
	}
	if _, err := f.file.Seek(0, io.SeekStart); err != nil {
		return err
	}
	h := sha256.New()
	n, err := io.Copy(h, io.LimitReader(f.file, limit+1))
	if err != nil || n != info.Size() {
		return errors.New("historical staged input read changed")
	}
	digest := "sha256:" + hex.EncodeToString(h.Sum(nil))
	if digest != expected {
		return errors.New("historical staged input hash differs")
	}
	f.size, f.digest = n, digest
	return f.check()
}

func holdHistoricalQualificationNative(directory, manifestHash, modelKey, sid string,
	source HistoricalQualificationSource) (facts historicalQualificationNative, hold *historicalQualificationHold, err error) {
	if !filepath.IsAbs(directory) || filepath.Clean(directory) != directory || sid == "" {
		return facts, nil, errors.New("historical source identity required")
	}
	ownerPath := filepath.Join(directory, "owner.lock")
	ownerInfo, statErr := os.Lstat(ownerPath)
	if statErr != nil || !ownerInfo.Mode().IsRegular() {
		return facts, nil, errors.New("historical owner lock must already exist")
	}
	// ReadBridgeTerminal performs the existing native terminal and process check
	// before the durable owner lock is retained. The bytes are then reopened and
	// compared under that lock so a race cannot authorize a different source.
	terminal, err := rt.ReadBridgeTerminal(directory, manifestHash)
	if err != nil {
		return facts, nil, err
	}
	if modelKey == "" {
		// Discovery does not authorize anything. The selected fact is reopened,
		// held and checked against the complete three-frame census below.
		stdout, readErr := os.ReadFile(filepath.Join(directory, "stdout.raw"))
		if readErr != nil || len(stdout) == 0 || len(stdout) > 16<<20 {
			return facts, nil, errors.New("historical model key discovery unavailable")
		}
		for _, line := range bytes.Split(stdout, []byte{'\n'}) {
			var candidate rt.BridgeFrame
			if json.Unmarshal(line, &candidate) == nil && candidate.Sequence == 2 && candidate.Type == "effect.request" && candidate.Capability == "MODEL" {
				if modelKey != "" {
					return facts, nil, errors.New("historical duplicate MODEL frame")
				}
				modelKey = candidate.Key
			}
		}
		if modelKey == "" {
			return facts, nil, errors.New("historical MODEL frame missing")
		}
	}
	wide, err := windows.UTF16PtrFromString(ownerPath)
	if err != nil {
		return facts, nil, err
	}
	ownerHandle, err := windows.CreateFile(wide, windows.GENERIC_READ|windows.GENERIC_WRITE, 0, nil, windows.OPEN_EXISTING, windows.FILE_ATTRIBUTE_NORMAL, 0)
	if err != nil {
		return facts, nil, errors.New("historical dispatch owner lock unavailable")
	}
	hold = &historicalQualificationHold{owner: os.NewFile(uintptr(ownerHandle), ownerPath)}
	defer func() {
		if err != nil {
			_ = hold.Close()
			hold = nil
		}
	}()
	var ancestors []string
	for p := directory; ; p = filepath.Dir(p) {
		ancestors = append(ancestors, p)
		if filepath.Dir(p) == p {
			break
		}
	}
	for i := len(ancestors) - 1; i >= 0; i-- {
		if _, err = hold.add(ancestors[i], true, i == 0, sid); err != nil {
			return facts, hold, err
		}
	}
	modelName := "effect-" + strings.TrimPrefix(Digest([]byte(modelKey)), "sha256:") + ".json"
	names := []string{"bridge.json", "stdout.raw", "stderr.raw", modelName}
	var raw [4][]byte
	for i, name := range names {
		f, openErr := hold.add(filepath.Join(directory, name), false, true, sid)
		if openErr != nil {
			err = openErr
			return facts, hold, err
		}
		limit := int64(4 << 20)
		if i == 1 || i == 2 {
			limit = 16 << 20
		}
		raw[i], err = historicalNativeRead(f, limit, i == 2)
		if err != nil {
			return facts, hold, err
		}
	}
	if err = json.Unmarshal(raw[0], &facts.journal); err != nil {
		return facts, hold, err
	}
	if Hash(facts.journal) != Hash(terminal) {
		err = errors.New("historical terminal journal raced")
		return facts, hold, err
	}
	facts.bridgeHash, facts.stdoutHash, facts.stderrHash, facts.modelHash = Digest(raw[0]), Digest(raw[1]), Digest(raw[2]), Digest(raw[3])
	facts.modelRaw = append([]byte(nil), raw[3]...)
	if facts.bridgeHash != source.BridgeSHA256 ||
		(source.StdoutSHA256 != "" && facts.stdoutHash != source.StdoutSHA256) ||
		(source.StderrSHA256 != "" && facts.stderrHash != source.StderrSHA256) ||
		manifestHash != source.ManifestHash {
		err = errors.New("historical frozen raw hash differs")
		return facts, hold, err
	}
	if _, err = hold.add(filepath.Join(directory, "input"), true, true, sid); err != nil {
		return facts, hold, err
	}
	for _, input := range []struct {
		name, expected string
		size           int64
	}{
		{"worker.exe", source.WorkerSHA256, 128 << 20},
		{"mu-worker.mjs", source.BundleSHA256, 32 << 20},
		{"worker.json", source.WorkerConfigSHA256, 64 << 10},
		{"request.json", source.RequestSHA256, 64 << 10},
	} {
		f, openErr := hold.add(filepath.Join(directory, "input", input.name), false, true, sid)
		if openErr != nil {
			err = openErr
			return facts, hold, err
		}
		if err = hashHistoricalNative(f, input.size, input.expected); err != nil {
			return facts, hold, err
		}
	}
	if facts.stdoutHash != terminal.StdoutHash || facts.stderrHash != terminal.StderrHash || terminal.Frames != 3 || terminal.Acknowledged != 2 || terminal.QueueRequired || terminal.QueueInitSequence != 0 || len(terminal.CommandReceipts) != 0 || terminal.Checkpoint != nil || terminal.CheckpointSequence != 0 || terminal.Paused || terminal.ProtocolComplete || !terminal.Receipt.Stopped || !terminal.Receipt.StreamsDrained || !terminal.Receipt.CleanupComplete || !terminal.Receipt.OutputCopied || len(terminal.Artifacts) != 0 {
		err = errors.New("historical raw terminal classification differs")
		return facts, hold, err
	}
	var lines [][]byte
	for _, line := range bytes.Split(raw[1], []byte{'\n'}) {
		if len(line) == 0 {
			continue
		}
		if len(line) > 64<<10 {
			err = errors.New("historical frame too large")
			return facts, hold, err
		}
		canonicalLine, canonErr := canonical.JSON(line)
		if canonErr != nil {
			err = canonErr
			return facts, hold, err
		}
		var shape map[string]json.RawMessage
		if json.Unmarshal(canonicalLine, &shape) != nil || shape["version"] != nil {
			err = errors.New("historical auxiliary or invalid stdout frame")
			return facts, hold, err
		}
		lines = append(lines, line)
	}
	if len(lines) != 3 {
		err = fmt.Errorf("historical frame count %d", len(lines))
		return facts, hold, err
	}
	for i, line := range lines {
		if err = json.Unmarshal(line, &facts.frames[i]); err != nil || facts.frames[i].Sequence != int64(i+1) {
			return facts, hold, errors.New("historical frame order invalid")
		}
	}
	if facts.frames[0].Type != "context.ready" || facts.frames[1].Type != "effect.request" || facts.frames[1].Capability != "MODEL" || facts.frames[2].Type != "effect.request" || facts.frames[2].Capability != "TOOL" || facts.frames[1].Key == "" || facts.frames[2].Key == "" || facts.frames[1].Key == facts.frames[2].Key || facts.frames[1].Route != facts.frames[2].Route {
		err = errors.New("historical first-gate frame grammar invalid")
		return facts, hold, err
	}
	if facts.frames[1].Key != modelKey {
		err = errors.New("historical model fact key differs")
		return facts, hold, err
	}
	if err = hold.Check(); err != nil {
		return facts, hold, err
	}
	return facts, hold, nil
}

// A source-derived historical closure has its own marker namespace and holds
// all original bytes through the caller's actual Commit or Rollback return.
type historicalQualificationClosure struct {
	proof Object
	hold  *historicalQualificationHold
}

func (c historicalQualificationClosure) Check() error {
	if c.hold == nil || c.proof == nil {
		return errors.New("historical qualification closure absent")
	}
	return c.hold.Check()
}

func (c historicalQualificationClosure) Close() error { return c.hold.Close() }

const historicalMaintenanceProofKind = "HISTORICAL_HOST_BROKER_DENIAL_RECONSTRUCTION_V1"
const historicalMaintenanceNativeClass = "HISTORICAL_NATIVE_JOB_ACCOUNTING_CLOSURE_V1"
const historicalMaintenanceRule = "EXACT_QUALIFICATION_MODEL_ONLY_FIRST_GATE_V1"

type HistoricalQualificationSubject struct {
	ProjectID   string `json:"project_id"`
	TaskID      string `json:"task_id"`
	RunID       string `json:"run_id"`
	RuntimeID   string `json:"runtime_id"`
	DispatchKey string `json:"dispatch_key"`
	Epoch       int64  `json:"epoch"`
}

type HistoricalQualificationSource struct {
	BridgeSHA256          string `json:"bridge_sha256"`
	StdoutSHA256          string `json:"stdout_sha256"`
	StderrSHA256          string `json:"stderr_sha256"`
	ManifestHash          string `json:"manifest_hash"`
	SourceCommit          string `json:"source_commit"`
	CoreSHA256            string `json:"core_sha256"`
	WorkerSHA256          string `json:"worker_sha256"`
	BundleSHA256          string `json:"bundle_sha256"`
	WorkerConfigSHA256    string `json:"worker_config_sha256"`
	RequestSHA256         string `json:"request_sha256"`
	FirstGateSourceSHA256 string `json:"first_gate_source_sha256"`
	BuildSHA256           string `json:"build_sha256"`
	PID                   uint32 `json:"pid"`
	Created               int64  `json:"created"`
	Job                   string `json:"job"`
}

type verifiedHistoricalQualification struct {
	subject      HistoricalQualificationSubject
	author       Principal
	ownerRoot    string
	profileRef   Object
	run          Object
	task         Object
	state        Object
	dispatch     Object
	observation  Object
	modelBinding Object
	native       historicalQualificationNative
	source       HistoricalQualificationSource
}

type HistoricalQualificationPlan struct {
	Schema                string                         `json:"schema"`
	OperationID           string                         `json:"operation_id"`
	DataRoot              string                         `json:"data_root"`
	Database              string                         `json:"database"`
	Subject               HistoricalQualificationSubject `json:"subject"`
	Source                HistoricalQualificationSource  `json:"source"`
	BoundaryPlanSHA256    string                         `json:"boundary_plan_sha256"`
	AuthorID              string                         `json:"author_id"`
	OwnerRoot             string                         `json:"owner_root"`
	DispatchDirectory     string                         `json:"dispatch_directory"`
	SID                   string                         `json:"sid"`
	BeforeCensus          store.OwnedStopCensus          `json:"before_census"`
	BeforeProtectedSHA256 string                         `json:"before_protected_sha256"`
	BeforeResidualSHA256  string                         `json:"before_residual_sha256"`
	Core                  Object                         `json:"core"`
	Proof                 Object                         `json:"proof"`
	ProofBytes            []byte                         `json:"proof_bytes"`
	Artifact              Object                         `json:"artifact"`
	ImpactLink            Object                         `json:"impact_link"`
	Run                   Object                         `json:"run"`
	ProjectState          Object                         `json:"project_state"`
	Event                 Object                         `json:"event"`
	Observation           Object                         `json:"observation"`
	BeforeRun             Object                         `json:"before_run"`
	BeforeState           Object                         `json:"before_state"`
	BeforeDispatch        Object                         `json:"before_dispatch"`
	UploadKey             string                         `json:"upload_key"`
	ExpiresAt             string                         `json:"expires_at"`
	ObservedAt            string                         `json:"observed_at"`
	EventSequence         int64                          `json:"event_sequence"`
	DispatchSequence      int64                          `json:"dispatch_sequence"`
	OutcomeHash           string                         `json:"outcome_hash"`
}

func (p HistoricalQualificationPlan) coreHash() string { return Hash(p.Core) }

func (p HistoricalQualificationPlan) beforeHash() string {
	return Hash(Object{"census": p.BeforeCensus, "run": p.BeforeRun,
		"state": p.BeforeState, "dispatch": p.BeforeDispatch,
		"protected": p.BeforeProtectedSHA256, "residual": p.BeforeResidualSHA256})
}

func (p HistoricalQualificationPlan) residualSelectors() (store.QualificationResidualSelectors, error) {
	runRev, e := Num(p.Run, "revision")
	if e != nil {
		return store.QualificationResidualSelectors{}, e
	}
	stateRev, e := Num(p.ProjectState, "revision")
	if e != nil {
		return store.QualificationResidualSelectors{}, e
	}
	return store.QualificationResidualSelectors{
		Project: p.Subject.ProjectID, Run: p.Subject.RunID, Operation: p.OperationID,
		Principal: p.AuthorID, UploadKey: p.UploadKey, EventID: Str(p.Event, "id"),
		Epoch: p.Subject.Epoch, EventSequence: p.EventSequence, ArtifactID: Str(p.Artifact, "id"),
		ImpactLinkID: Str(p.ImpactLink, "id"), StateID: Str(p.ProjectState, "id"),
		RunRevision: runRev, StateRevision: stateRev, ObservationHash: Hash(p.Observation),
	}, nil
}

func (p HistoricalQualificationPlan) afterHash() string {
	return Hash(Object{"artifact": p.Artifact, "impact_link": p.ImpactLink,
		"run": p.Run, "state": p.ProjectState, "event": p.Event,
		"observation": p.Observation, "dispatch_sequence": p.DispatchSequence,
		"upload_hash": Digest(p.ProofBytes), "outcome_hash": p.OutcomeHash})
}

// JournalHashes allow a lower-dependency journal to bind every immutable
// planned payload without importing domain or exposing SQL authority.
func (p HistoricalQualificationPlan) JournalHashes() (plan, before, after, subject, evidence string) {
	return p.coreHash(), p.beforeHash(), p.afterHash(), Hash(p.Subject),
		Hash(Object{"source": p.Source, "native": p.Proof["native"], "model": p.Proof["model_binding"]})
}

func (s *Service) buildHistoricalQualificationPlan(ctx context.Context, tx *sql.Tx, verified verifiedHistoricalQualification,
	operationID, boundaryPlanSHA256, dataRoot, database, directory, sid string, before store.OwnedStopCensus,
	frozen *HistoricalQualificationPlan) (HistoricalQualificationPlan, error) {
	var plan HistoricalQualificationPlan
	if len(operationID) != 32 || before.Tables < 87 || before.SHA256 == "" ||
		dataRoot == "" || boundaryPlanSHA256 == "" || database != filepath.Join(dataRoot, "researchos.sqlite") {
		return plan, qualificationDenialUnavailable("historical plan inputs invalid")
	}
	currentRun, err := cloneQualificationObject(verified.run)
	if err != nil {
		return plan, err
	}
	currentState, err := cloneQualificationObject(verified.state)
	if err != nil {
		return plan, err
	}
	observation, err := cloneQualificationObject(verified.observation)
	if err != nil {
		return plan, err
	}
	seq, err := Num(verified.state, "event_sequence")
	if err != nil || seq == 1<<63-1 {
		return plan, qualificationDenialUnavailable("event sequence exhausted")
	}
	var maxOutbox int64
	if err = tx.QueryRow(`SELECT coalesce(max(sequence),0) FROM outbox WHERE project=?`, verified.subject.ProjectID).Scan(&maxOutbox); err != nil {
		return plan, err
	}
	if maxOutbox > seq {
		seq = maxOutbox
	}
	if seq == 1<<63-1 {
		return plan, qualificationDenialUnavailable("event sequence exhausted")
	}
	seq++
	dispatchSeq, err := Num(verified.dispatch, "observation_sequence")
	if err != nil {
		return plan, err
	}
	if verified.native.journal.Sequence > dispatchSeq {
		dispatchSeq = verified.native.journal.Sequence
	}
	if dispatchSeq == 1<<63-1 {
		return plan, qualificationDenialUnavailable("dispatch sequence exhausted")
	}
	dispatchSeq++
	observedAt := Now()
	expiresAt := time.Now().UTC().Add(time.Hour).Format(time.RFC3339Nano)
	uploadKey, artifactID, linkID, eventID := ID(), ID(), ID(), ID()
	if frozen != nil {
		observedAt, expiresAt = frozen.ObservedAt, frozen.ExpiresAt
		uploadKey, artifactID, linkID, eventID = frozen.UploadKey,
			Str(frozen.Core, "artifact_id"), Str(frozen.Core, "impact_link_id"), Str(frozen.Core, "event_id")
		if len(uploadKey) != 32 || len(artifactID) != 32 || len(linkID) != 32 || len(eventID) != 32 ||
			observedAt == "" || expiresAt == "" {
			return plan, qualificationDenialUnavailable("frozen historical identifiers invalid")
		}
	}
	qf := observation["qualification_failure"].(map[string]any)
	qf["closure_observed_at"] = observedAt
	core := Object{"schema": "researchos.qualification-failure-maintenance-core.v1",
		"operation_id": operationID, "boundary_plan_sha256": boundaryPlanSHA256,
		"subject": verified.subject, "source": verified.source,
		"data_root": dataRoot, "database": database, "author": verified.author.ID,
		"owner_root": verified.ownerRoot, "business_sid": sid,
		"before_census": before, "before_run_hash": Hash(verified.run),
		"before_state_hash": Hash(verified.state), "before_dispatch_hash": Hash(verified.dispatch),
		"profile_ref": verified.profileRef, "upload_key": uploadKey,
		"artifact_id": artifactID, "impact_link_id": linkID, "event_id": eventID,
		"observed_at": observedAt, "expires_at": expiresAt,
		"event_sequence": seq, "dispatch_observation_sequence": dispatchSeq,
		"observation_hash": Hash(observation)}
	proof := Object{"schema": "researchos.qualification-failure-maintenance-proof.v1",
		"kind":         historicalMaintenanceProofKind,
		"claim":        "HOST_TOOL_EFFECT_NOT_DISPATCHED",
		"rule":         historicalMaintenanceRule,
		"native_class": historicalMaintenanceNativeClass,
		"plan_hash":    Hash(core), "plan_core": core, "subject": verified.subject,
		"author": verified.author.ID, "owner_root": verified.ownerRoot,
		"observed_at": observedAt,
		"native": Object{"bridge_sha256": verified.native.bridgeHash,
			"stdout_sha256": verified.native.stdoutHash, "stderr_sha256": verified.native.stderrHash,
			"model_fact_sha256": verified.native.modelHash,
			"pid":               verified.native.journal.Identity.PID,
			"created":           verified.native.journal.Identity.Created,
			"job":               verified.native.journal.Identity.Job,
			"frames":            int64(3), "acknowledged": int64(2), "raw_queue_empty": false,
			"stopped":             verified.native.journal.Receipt.Stopped,
			"streams_drained":     verified.native.journal.Receipt.StreamsDrained,
			"job_total_processes": verified.native.journal.Receipt.JobProcesses,
			"exit_code":           verified.native.journal.Receipt.ExitCode,
			"raw_wait_result":     nil},
		"source_binding": verified.source, "model_binding": verified.modelBinding,
		"derived_observation": observation,
		"limits":              "Host first-gate TOOL only; no universal OS NO_EFFECT, raw WAIT or broker join"}
	proofBytes := Bytes(proof)
	if len(proofBytes) == 0 || len(proofBytes) > 64<<10 {
		return plan, qualificationDenialUnavailable("historical proof bound exceeded")
	}
	artifact := Object{"id": artifactID, "project_id": verified.subject.ProjectID,
		"revision": 1, "created_at": observedAt, "updated_at": observedAt,
		"run_id": nil, "kind": "MANIFEST", "evidence_kind": "GENERATED",
		"measurement_mode": "LIVE", "media_type": "application/json",
		"content_hash": Digest(proofBytes), "storage_key": uploadKey, "byte_size": len(proofBytes),
		"input_refs": []any{verified.profileRef}, "source_refs": Empty(),
		"produced_by": verified.author.ID, "access_class": "PROJECT",
		"validity": "CURRENT", "sealed_at": observedAt}
	link := Object{"id": linkID, "project_id": verified.subject.ProjectID,
		"revision": 1, "created_at": observedAt, "updated_at": observedAt,
		"from_ref": Ref(artifact, "Artifact"), "to_ref": verified.profileRef,
		"relation": "DERIVED_FROM", "basis": "DETERMINISTIC",
		"evidence_refs": Empty(), "status": "ACTIVE"}
	runRev, err := Num(currentRun, "revision")
	if err != nil || runRev == 1<<63-1 {
		return plan, qualificationDenialUnavailable("Run revision unavailable")
	}
	currentRun["revision"] = runRev + 1
	currentRun["updated_at"] = observedAt
	currentRun["status"] = "FAILED"
	currentRun["execution_report"] = "Historical Host first-gate TOOL classification; operation " + operationID +
		"; proof " + Digest(proofBytes) + "; native ended " + verified.native.journal.Ended
	currentRun["exit_code"] = verified.native.journal.Receipt.ExitCode
	currentRun["runtime_settled_at"] = observedAt
	currentRun["children_stopped"] = true
	currentRun["queue_empty"] = true
	currentRun["ended_at"] = observedAt
	stateRev, err := Num(currentState, "revision")
	if err != nil || stateRev == 1<<63-1 {
		return plan, qualificationDenialUnavailable("ProjectState revision unavailable")
	}
	currentState["revision"] = stateRev + 1
	currentState["updated_at"] = observedAt
	currentState["event_sequence"] = seq
	event := Object{"id": eventID, "project_id": verified.subject.ProjectID,
		"revision": 1, "created_at": observedAt, "sequence": seq,
		"event_type": "RUN_CHANGED", "aggregate_ref": Ref(currentRun, "Run"),
		"actor_id": verified.author.ID, "correlation_id": operationID,
		"causation_id": nil, "event_data_artifact_ref": nil}
	event["receipt_hash"] = Receipt(event)
	outcomeHash := Hash(Object{"artifact": artifact, "impact_link": link, "run": currentRun,
		"state": currentState, "event": event, "observation": observation,
		"dispatch_sequence": dispatchSeq, "before_census": before})
	plan = HistoricalQualificationPlan{Schema: "researchos.qualification-failure-maintenance-full-plan.v1",
		OperationID: operationID, BoundaryPlanSHA256: boundaryPlanSHA256,
		DataRoot: dataRoot, Database: database, Subject: verified.subject,
		Source: verified.source, AuthorID: verified.author.ID, OwnerRoot: verified.ownerRoot,
		DispatchDirectory: directory,
		SID:               sid, BeforeCensus: before, Core: core, Proof: proof,
		ProofBytes: proofBytes, Artifact: artifact, ImpactLink: link, Run: currentRun,
		ProjectState: currentState, Event: event, Observation: observation,
		BeforeRun: verified.run, BeforeState: verified.state, BeforeDispatch: verified.dispatch,
		UploadKey: uploadKey, ExpiresAt: expiresAt, ObservedAt: observedAt,
		EventSequence: seq, DispatchSequence: dispatchSeq, OutcomeHash: outcomeHash}
	plan.BeforeProtectedSHA256, err = store.QualificationMaintenanceProtectedCensus(ctx, tx)
	if err != nil {
		return HistoricalQualificationPlan{}, err
	}
	selectors, err := plan.residualSelectors()
	if err != nil {
		return HistoricalQualificationPlan{}, err
	}
	plan.BeforeResidualSHA256, err = store.QualificationMaintenanceResidualCensus(ctx, tx, selectors)
	if err != nil {
		return HistoricalQualificationPlan{}, err
	}
	return plan, nil
}

// PlanHistoricalQualification performs only reads of the existing database.
// The returned plan is informational until a separate boot-bound opaque
// current-quiescence witness, native root lock and journal BEGIN are present.
func PlanHistoricalQualification(ctx context.Context, db *sql.DB, contractsDir string,
	subject HistoricalQualificationSubject, source HistoricalQualificationSource,
	authorID, dataRoot, operationID, boundaryPlanSHA256, sid string) (plan HistoricalQualificationPlan, retErr error) {
	if db == nil || !filepath.IsAbs(dataRoot) || filepath.Clean(dataRoot) != dataRoot ||
		!filepath.IsAbs(contractsDir) || sid == "" {
		return plan, qualificationDenialUnavailable("historical preflight input invalid")
	}
	if err := ctx.Err(); err != nil {
		return plan, err
	}
	contracts, err := LoadContracts(contractsDir)
	if err != nil {
		return plan, err
	}
	s := &Service{DB: db, Contracts: contracts}
	// SQL statements still use ctx, but the transaction itself must be rolled
	// back synchronously before the native evidence hold is released. A Tx
	// bound to ctx can auto-rollback in a background goroutine after cancellation.
	tx, err := db.BeginTx(context.WithoutCancel(ctx), &sql.TxOptions{ReadOnly: true})
	if err != nil {
		return plan, err
	}
	var hold *historicalQualificationHold
	defer func() {
		retErr = errors.Join(retErr, finishHistoricalQualificationTx(tx, false, hold))
	}()
	var manifestHash string
	if err := tx.QueryRowContext(ctx, `SELECT manifest_hash FROM runtime_dispatches WHERE project=? AND run=? AND epoch=? AND dispatch_key=?`,
		subject.ProjectID, subject.RunID, subject.Epoch, subject.DispatchKey).Scan(&manifestHash); err != nil || manifestHash == "" {
		return plan, qualificationDenialUnavailable("exact historical dispatch unavailable")
	}
	directory := filepath.Join(dataRoot, "runtime-dispatches", subject.DispatchKey)
	native, nativeHold, err := holdHistoricalQualificationNative(directory, manifestHash, "", sid, source)
	if err != nil {
		return plan, err
	}
	hold = nativeHold
	verified, err := s.verifyHistoricalQualificationTx(ctx, tx, subject, source, authorID, directory, sid, native)
	if err != nil {
		return plan, err
	}
	before, err := store.QualificationMaintenanceCensus(ctx, tx)
	if err != nil {
		return plan, err
	}
	plan, err = s.buildHistoricalQualificationPlan(ctx, tx, verified, operationID, boundaryPlanSHA256, dataRoot,
		filepath.Join(dataRoot, "researchos.sqlite"), directory, sid, before, nil)
	if err != nil {
		return plan, err
	}
	if err = hold.Check(); err != nil {
		return plan, err
	}
	if err = ctx.Err(); err != nil {
		return plan, err
	}
	return plan, nil
}

func historicalMaintenanceMarker(plan HistoricalQualificationPlan, planFileSHA256 string) Object {
	return Object{"schema": "researchos.qualification-failure-maintenance-marker.v1",
		"kind": historicalMaintenanceProofKind, "operation_id": plan.OperationID,
		"plan_hash": plan.coreHash(), "plan_file_sha256": planFileSHA256,
		"subject": plan.Subject, "author": plan.AuthorID, "owner_root": plan.OwnerRoot,
		"proof_ref":        Ref(plan.Artifact, "Artifact"),
		"observation_hash": Hash(plan.Observation),
		"terminal_run_ref": Ref(plan.Run, "Run"), "outcome_hash": plan.OutcomeHash}
}

func (s *Service) applyHistoricalQualificationTx(ctx context.Context, tx *sql.Tx,
	plan HistoricalQualificationPlan, planFileSHA256 string) error {
	if plan.Schema != "researchos.qualification-failure-maintenance-full-plan.v1" ||
		plan.Proof["kind"] != historicalMaintenanceProofKind ||
		plan.Proof["claim"] != "HOST_TOOL_EFFECT_NOT_DISPATCHED" ||
		plan.Proof["rule"] != historicalMaintenanceRule ||
		plan.Proof["native_class"] != historicalMaintenanceNativeClass ||
		plan.Proof["plan_hash"] != plan.coreHash() ||
		!bytes.Equal(plan.ProofBytes, Bytes(plan.Proof)) ||
		plan.Artifact["run_id"] != nil || len(Arr(plan.Artifact, "input_refs")) != 1 ||
		len(Arr(plan.Artifact, "source_refs")) != 0 ||
		plan.Artifact["content_hash"] != Digest(plan.ProofBytes) ||
		plan.Artifact["produced_by"] != plan.AuthorID ||
		plan.ImpactLink["relation"] != "DERIVED_FROM" ||
		plan.Event["event_type"] != "RUN_CHANGED" ||
		plan.Event["correlation_id"] != plan.OperationID ||
		plan.OutcomeHash == "" || len(plan.ProofBytes) > 64<<10 {
		return qualificationDenialUnavailable("historical planned write set invalid")
	}
	expiresAt, err := time.Parse(time.RFC3339Nano, plan.ExpiresAt)
	if err != nil || !expiresAt.After(time.Now()) {
		return qualificationDenialUnavailable("historical planned upload expired")
	}
	var used int
	if err := tx.QueryRowContext(ctx, `SELECT count(*) FROM domain_objects WHERE project=? AND kind='Artifact' AND json_extract(body,'$.kind')='MANIFEST' AND json_extract(body,'$.content_hash')=?`,
		plan.Subject.ProjectID, plan.Artifact["content_hash"]).Scan(&used); err != nil || used != 0 {
		return qualificationDenialUnavailable("historical proof content reused")
	}
	if _, err := tx.ExecContext(ctx, `INSERT INTO uploaded_content(storage_key,project,principal,bytes,content_hash,expires_at,sealed) VALUES(?,?,?,?,?,?,0)`,
		plan.UploadKey, plan.Subject.ProjectID, plan.AuthorID, plan.ProofBytes, Digest(plan.ProofBytes), plan.ExpiresAt); err != nil {
		return err
	}
	if err := s.put(tx, "Artifact", plan.Artifact); err != nil {
		return err
	}
	result, err := tx.ExecContext(ctx, `UPDATE uploaded_content SET sealed=1 WHERE storage_key=? AND project=? AND principal=? AND sealed=0`,
		plan.UploadKey, plan.Subject.ProjectID, plan.AuthorID)
	if err != nil {
		return err
	}
	if n, err := result.RowsAffected(); err != nil || n != 1 {
		return qualificationDenialUnavailable("historical upload seal CAS failed")
	}
	if err := s.put(tx, "ImpactLink", plan.ImpactLink); err != nil {
		return err
	}
	if _, err := tx.ExecContext(ctx, `INSERT INTO runtime_observations(project,run,epoch,receipt_hash,body,observed_at) VALUES(?,?,?,?,?,?)`,
		plan.Subject.ProjectID, plan.Subject.RunID, plan.Subject.Epoch,
		Hash(plan.Observation), string(Bytes(plan.Observation)), plan.ObservedAt); err != nil {
		return err
	}
	result, err = tx.ExecContext(ctx, `UPDATE runtime_dispatches SET state='OBSERVED',observation_sequence=?,observation_hash=?,reason=?,updated_at=? WHERE project=? AND run=? AND epoch=? AND state=? AND observation_sequence=? AND dispatch_key=? AND manifest_hash=?`,
		plan.DispatchSequence, Hash(plan.Observation), "historical qualification first-gate TOOL reconstruction "+plan.OperationID,
		plan.ObservedAt, plan.Subject.ProjectID, plan.Subject.RunID, plan.Subject.Epoch,
		plan.BeforeDispatch["state"], plan.BeforeDispatch["observation_sequence"],
		plan.BeforeDispatch["dispatch_key"], plan.BeforeDispatch["manifest_hash"])
	if err != nil {
		return err
	}
	if n, err := result.RowsAffected(); err != nil || n != 1 {
		return qualificationDenialUnavailable("historical dispatch CAS failed")
	}
	if err := s.put(tx, "Run", plan.Run); err != nil {
		return err
	}
	if err := s.put(tx, "ProjectState", plan.ProjectState); err != nil {
		return err
	}
	if err := s.put(tx, "EventEnvelope", plan.Event); err != nil {
		return err
	}
	if _, err := tx.ExecContext(ctx, `INSERT INTO outbox(project,sequence,id,body) VALUES(?,?,?,?)`,
		plan.Subject.ProjectID, plan.EventSequence, plan.Event["id"], string(Bytes(plan.Event))); err != nil {
		return err
	}
	if _, err := tx.ExecContext(ctx, `INSERT INTO event_state_snapshots(project,event_id,revision,body) VALUES(?,?,?,?)`,
		plan.Subject.ProjectID, plan.Event["id"], plan.ProjectState["revision"], string(Bytes(plan.ProjectState))); err != nil {
		return err
	}
	marker := historicalMaintenanceMarker(plan, planFileSHA256)
	if _, err := tx.ExecContext(ctx, `INSERT INTO idempotency(principal,project,operation,key,request_hash,status,body,headers,created_at) VALUES(?,?,'host:qualification-failure-maintenance',?,?,200,?,'{}',?)`,
		plan.AuthorID, plan.Subject.ProjectID, plan.OperationID, planFileSHA256,
		string(Bytes(marker)), plan.ObservedAt); err != nil {
		return err
	}
	return nil
}

func (s *Service) validatedHistoricalQualificationFailureTx(tx *sql.Tx,
	plan HistoricalQualificationPlan, verified verifiedHistoricalQualification,
	hold *historicalQualificationHold) (historicalQualificationClosure, error) {
	var zero historicalQualificationClosure
	if tx == nil || hold == nil || verified.subject != plan.Subject ||
		verified.author.ID != plan.AuthorID || verified.ownerRoot != plan.OwnerRoot ||
		Hash(verified.run) != Hash(plan.BeforeRun) || Hash(verified.state) != Hash(plan.BeforeState) ||
		Hash(verified.dispatch) != Hash(plan.BeforeDispatch) ||
		verified.native.bridgeHash != plan.Source.BridgeSHA256 ||
		plan.Proof["kind"] != historicalMaintenanceProofKind ||
		plan.Proof["claim"] != "HOST_TOOL_EFFECT_NOT_DISPATCHED" ||
		plan.Proof["native_class"] != historicalMaintenanceNativeClass ||
		plan.Proof["plan_hash"] != plan.coreHash() ||
		plan.Proof["owner_root"] != plan.OwnerRoot ||
		plan.Proof["author"] != plan.AuthorID ||
		plan.Proof["model_binding"] == nil ||
		Hash(plan.Proof["model_binding"]) != Hash(verified.modelBinding) {
		return zero, qualificationDenialUnavailable("historical private consumer mismatch")
	}
	closure := historicalQualificationClosure{proof: plan.Proof, hold: hold}
	if err := closure.Check(); err != nil {
		return zero, err
	}
	return closure, nil
}

// ApplyHistoricalQualification consumes only a validated full plan and its
// exact external file digest. Native evidence stays held through the actual
// Commit/Rollback return, including a failed Commit and every early error.
func ApplyHistoricalQualification(ctx context.Context, db *sql.DB, contractsDir string,
	plan HistoricalQualificationPlan, planFileSHA256 string,
	boundary *recoveryboundary.CurrentQuiescence, lease *rt.DataRootLease) (marker Object, retErr error) {
	if db == nil || !filepath.IsAbs(contractsDir) || planFileSHA256 == "" ||
		plan.Schema != "researchos.qualification-failure-maintenance-full-plan.v1" ||
		plan.Database != filepath.Join(plan.DataRoot, "researchos.sqlite") ||
		boundary == nil || lease == nil {
		return nil, qualificationDenialUnavailable("historical commit input invalid")
	}
	if err := boundary.Check(ctx, lease, plan.DataRoot, plan.Database, plan.OperationID, plan.BoundaryPlanSHA256); err != nil {
		return nil, err
	}
	contracts, err := LoadContracts(contractsDir)
	if err != nil {
		return nil, err
	}
	s := &Service{DB: db, Contracts: contracts}
	native, hold, err := holdHistoricalQualificationNative(plan.DispatchDirectory,
		Str(plan.BeforeDispatch, "manifest_hash"), "", plan.SID, plan.Source)
	if err != nil {
		return nil, err
	}
	// Keep cancellation from starting database/sql's asynchronous Tx rollback;
	// the deferred synchronous Rollback must return before Close releases the
	// original native evidence. All statements and the final gate use ctx.
	tx, err := db.BeginTx(context.WithoutCancel(ctx), nil)
	if err != nil {
		return nil, errors.Join(err, hold.Close())
	}
	txFinished := false
	var closure historicalQualificationClosure
	defer func() {
		retErr = errors.Join(retErr, finishHistoricalQualificationTx(tx, txFinished, hold))
	}()
	if err := resourceWriteLock(tx); err != nil {
		return nil, err
	}
	before, err := store.QualificationMaintenanceCensus(ctx, tx)
	if err != nil {
		return nil, err
	}
	if Hash(before) != Hash(plan.BeforeCensus) {
		return nil, qualificationDenialUnavailable("historical before census drift")
	}
	verified, err := s.verifyHistoricalQualificationTx(ctx, tx, plan.Subject, plan.Source,
		plan.AuthorID, plan.DispatchDirectory, plan.SID, native)
	if err != nil {
		return nil, err
	}
	rebuilt, err := s.buildHistoricalQualificationPlan(ctx, tx, verified, plan.OperationID, plan.BoundaryPlanSHA256,
		plan.DataRoot, plan.Database, plan.DispatchDirectory, plan.SID, before, &plan)
	if err != nil || Hash(rebuilt) != Hash(plan) {
		return nil, qualificationDenialUnavailable("historical full plan drift")
	}
	closure, err = s.validatedHistoricalQualificationFailureTx(tx, plan, verified, hold)
	if err != nil {
		return nil, err
	}
	if err := s.applyHistoricalQualificationTx(ctx, tx, plan, planFileSHA256); err != nil {
		return nil, err
	}
	if err := closure.Check(); err != nil {
		return nil, err
	}
	if err := boundary.Check(ctx, lease, plan.DataRoot, plan.Database, plan.OperationID, plan.BoundaryPlanSHA256); err != nil {
		return nil, err
	}
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	if err := tx.Commit(); err != nil {
		return nil, err
	}
	txFinished = true
	return historicalMaintenanceMarker(plan, planFileSHA256), nil
}

func historicalQualificationRefs(tx *sql.Tx, project, kind, id string, revision int64) ([]any, error) {
	rows, err := tx.Query(`SELECT field,target_project,target_kind,target_id,target_revision FROM domain_refs
		WHERE project=? AND kind=? AND id=? AND revision=?
		ORDER BY field,target_project,target_kind,target_id,target_revision`, project, kind, id, revision)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []any
	for rows.Next() {
		var field, targetProject, targetKind, targetID string
		var targetRevision int64
		if err = rows.Scan(&field, &targetProject, &targetKind, &targetID, &targetRevision); err != nil {
			return nil, err
		}
		out = append(out, []any{field, targetProject, targetKind, targetID, targetRevision})
	}
	return out, rows.Err()
}

func historicalRefValue(object Object, path string) any {
	var current any = object
	for _, component := range strings.Split(strings.TrimPrefix(path, "/"), "/") {
		switch x := current.(type) {
		case map[string]any:
			current = x[component]
		case []any:
			i, e := strconv.Atoi(component)
			if e != nil || i < 0 || i >= len(x) {
				return nil
			}
			current = x[i]
		default:
			return nil
		}
	}
	return current
}

func historicalQualificationRefRevisionMatches(tx *sql.Tx, project, kind string, object Object, oldRows, newRows []any) (bool, error) {
	if len(oldRows) != len(newRows) {
		return false, nil
	}
	for i, entry := range newRows {
		current, ok := entry.([]any)
		if !ok || len(current) != 5 {
			return false, nil
		}
		prior, ok := oldRows[i].([]any)
		if !ok || len(prior) != 5 {
			return false, nil
		}
		for j := 0; j < 4; j++ {
			if current[j] != prior[j] {
				return false, nil
			}
		}
		field, ok := current[0].(string)
		if !ok || !strings.HasPrefix(field, "/") {
			return false, nil
		}
		targetKind, _ := current[2].(string)
		targetID, _ := current[3].(string)
		targetRevision, ok := current[4].(int64)
		if !ok {
			return false, nil
		}
		value := historicalRefValue(object, field)
		if ref, ok := value.(map[string]any); ok {
			rev, e := Num(Object(ref), "revision")
			if e != nil || ref["entity_type"] != targetKind || ref["id"] != targetID || rev != targetRevision {
				return false, nil
			}
			continue
		}
		parts := strings.Split(strings.TrimPrefix(field, "/"), "/")
		if len(parts) == 0 || relationKind(kind, parts[0]) != targetKind {
			return false, nil
		}
		textValue, _ := value.(string)
		contained := textValue == targetID
		if list, ok := value.([]any); ok {
			contained = false
			for _, v := range list {
				if v == targetID {
					contained = true
					break
				}
			}
		}
		if !contained {
			return false, nil
		}
		var currentRevision int64
		if e := tx.QueryRow(`SELECT revision FROM domain_objects WHERE project=? AND kind=? AND id=?`,
			project, targetKind, targetID).Scan(&currentRevision); e != nil {
			return false, e
		}
		if currentRevision != targetRevision {
			return false, nil
		}
	}
	return true, nil
}

func historicalQualificationExactRows(ctx context.Context, tx *sql.Tx, plan HistoricalQualificationPlan, planFileSHA256 string) (bool, error) {
	for _, entry := range []struct {
		kind   string
		object Object
	}{
		{"Artifact", plan.Artifact}, {"ImpactLink", plan.ImpactLink}, {"Run", plan.Run},
		{"ProjectState", plan.ProjectState}, {"EventEnvelope", plan.Event},
	} {
		id := Str(entry.object, "id")
		rev, err := Num(entry.object, "revision")
		if err != nil {
			return false, err
		}
		for _, table := range []string{"domain_versions", "domain_objects"} {
			var body string
			var actualRevision int64
			var contentHash sql.NullString
			var immutable int
			selection := "revision,body,content_hash"
			if table == "domain_objects" {
				selection += ",immutable"
			}
			row := tx.QueryRowContext(ctx, `SELECT `+selection+` FROM "`+table+`" WHERE project=? AND kind=? AND id=?`+
				func() string {
					if table == "domain_versions" {
						return " AND revision=?"
					}
					return ""
				}(),
				func() []any {
					args := []any{plan.Subject.ProjectID, entry.kind, id}
					if table == "domain_versions" {
						args = append(args, rev)
					}
					return args
				}()...,
			)
			var e error
			if table == "domain_objects" {
				e = row.Scan(&actualRevision, &body, &contentHash, &immutable)
			} else {
				e = row.Scan(&actualRevision, &body, &contentHash)
			}
			if e == sql.ErrNoRows {
				return false, nil
			}
			if e != nil {
				return false, e
			}
			if actualRevision != rev || body != string(Bytes(entry.object)) {
				return false, nil
			}
			wantHash := ""
			if entry.kind == "Artifact" {
				wantHash = Str(entry.object, "content_hash")
			}
			if entry.kind == "EventEnvelope" {
				wantHash = Str(entry.object, "receipt_hash")
			}
			if contentHash.Valid != (wantHash != "") || contentHash.Valid && contentHash.String != wantHash ||
				table == "domain_objects" && (immutable == 1) != (entry.kind == "EventEnvelope") {
				return false, nil
			}
		}
	}
	// New revisions of the two mutable objects must carry the same reference
	// edges as their immediately preceding versions.
	for _, entry := range []struct {
		kind   string
		object Object
	}{
		{"Run", plan.Run}, {"ProjectState", plan.ProjectState},
	} {
		rev, err := Num(entry.object, "revision")
		if err != nil {
			return false, err
		}
		newRows, err := historicalQualificationRefs(tx, plan.Subject.ProjectID, entry.kind, Str(entry.object, "id"), rev)
		if err != nil {
			return false, err
		}
		oldRows, err := historicalQualificationRefs(tx, plan.Subject.ProjectID, entry.kind, Str(entry.object, "id"), rev-1)
		if err != nil {
			return false, err
		}
		if matched, err := historicalQualificationRefRevisionMatches(tx, plan.Subject.ProjectID, entry.kind, entry.object, oldRows, newRows); err != nil {
			return false, err
		} else if !matched {
			return false, nil
		}
	}
	profile, ok := plan.Core["profile_ref"].(map[string]any)
	if !ok {
		return false, nil
	}
	profileRevision, err := Num(Object(profile), "revision")
	if err != nil {
		return false, err
	}
	refExpected := []struct {
		kind, id string
		rows     []any
	}{
		{"Artifact", Str(plan.Artifact, "id"), []any{[]any{"/input_refs/0", plan.Subject.ProjectID, Str(Object(profile), "entity_type"), Str(Object(profile), "id"), profileRevision}}},
		{"ImpactLink", Str(plan.ImpactLink, "id"), []any{
			[]any{"/from_ref", plan.Subject.ProjectID, "Artifact", Str(plan.Artifact, "id"), int64(1)},
			[]any{"/to_ref", plan.Subject.ProjectID, Str(Object(profile), "entity_type"), Str(Object(profile), "id"), profileRevision},
		}},
	}
	runRevision, err := Num(plan.Run, "revision")
	if err != nil {
		return false, err
	}
	refExpected = append(refExpected, struct {
		kind, id string
		rows     []any
	}{
		"EventEnvelope", Str(plan.Event, "id"), []any{[]any{"/aggregate_ref", plan.Subject.ProjectID, "Run", plan.Subject.RunID, runRevision}},
	})
	for _, entry := range refExpected {
		rows, err := historicalQualificationRefs(tx, plan.Subject.ProjectID, entry.kind, entry.id, 1)
		if err != nil {
			return false, err
		}
		if Hash(rows) != Hash(entry.rows) {
			return false, nil
		}
	}
	var uploaded []byte
	var contentHash string
	var sealed int
	var expiresAt string
	err = tx.QueryRowContext(ctx, `SELECT bytes,content_hash,sealed,expires_at FROM uploaded_content WHERE storage_key=? AND project=? AND principal=?`,
		plan.UploadKey, plan.Subject.ProjectID, plan.AuthorID).Scan(&uploaded, &contentHash, &sealed, &expiresAt)
	if err == sql.ErrNoRows {
		return false, nil
	}
	if err != nil {
		return false, err
	}
	if !bytes.Equal(uploaded, plan.ProofBytes) || contentHash != Digest(plan.ProofBytes) || sealed != 1 || expiresAt != plan.ExpiresAt {
		return false, nil
	}
	var observed, observedAt string
	err = tx.QueryRowContext(ctx, `SELECT body,observed_at FROM runtime_observations WHERE project=? AND run=? AND epoch=? AND receipt_hash=?`,
		plan.Subject.ProjectID, plan.Subject.RunID, plan.Subject.Epoch, Hash(plan.Observation)).Scan(&observed, &observedAt)
	if err == sql.ErrNoRows {
		return false, nil
	}
	if err != nil {
		return false, err
	}
	if observed != string(Bytes(plan.Observation)) || observedAt != plan.ObservedAt {
		return false, nil
	}
	var dispatchState, dispatchHash, dispatchKey, manifestHash, dispatchUpdated, dispatchReason string
	var dispatchSequence int64
	err = tx.QueryRowContext(ctx, `SELECT state,observation_sequence,observation_hash,dispatch_key,manifest_hash,updated_at,reason
		FROM runtime_dispatches WHERE project=? AND run=? AND epoch=?`, plan.Subject.ProjectID, plan.Subject.RunID, plan.Subject.Epoch).
		Scan(&dispatchState, &dispatchSequence, &dispatchHash, &dispatchKey, &manifestHash, &dispatchUpdated, &dispatchReason)
	if err == sql.ErrNoRows {
		return false, nil
	}
	if err != nil {
		return false, err
	}
	if dispatchState != "OBSERVED" || dispatchSequence != plan.DispatchSequence || dispatchHash != Hash(plan.Observation) ||
		dispatchKey != plan.Subject.DispatchKey || manifestHash != Str(plan.BeforeDispatch, "manifest_hash") ||
		dispatchUpdated != plan.ObservedAt || dispatchReason != "historical qualification first-gate TOOL reconstruction "+plan.OperationID {
		return false, nil
	}
	var outbox string
	var acknowledged int
	err = tx.QueryRowContext(ctx, `SELECT body,acknowledged FROM outbox WHERE project=? AND sequence=? AND id=?`,
		plan.Subject.ProjectID, plan.EventSequence, Str(plan.Event, "id")).Scan(&outbox, &acknowledged)
	if err == sql.ErrNoRows {
		return false, nil
	}
	if err != nil {
		return false, err
	}
	if outbox != string(Bytes(plan.Event)) || acknowledged != 0 {
		return false, nil
	}
	var snapshot string
	var snapshotRev int64
	err = tx.QueryRowContext(ctx, `SELECT body,revision FROM event_state_snapshots WHERE project=? AND event_id=?`,
		plan.Subject.ProjectID, Str(plan.Event, "id")).Scan(&snapshot, &snapshotRev)
	if err == sql.ErrNoRows {
		return false, nil
	}
	if err != nil {
		return false, err
	}
	stateRevision, stateErr := Num(plan.ProjectState, "revision")
	if stateErr != nil {
		return false, stateErr
	}
	if snapshot != string(Bytes(plan.ProjectState)) || snapshotRev != stateRevision {
		return false, nil
	}
	var markerRaw []byte
	var status int
	var headers, createdAt string
	err = tx.QueryRowContext(ctx, `SELECT body,status,headers,created_at FROM idempotency WHERE principal=? AND project=? AND operation='host:qualification-failure-maintenance' AND key=? AND request_hash=?`,
		plan.AuthorID, plan.Subject.ProjectID, plan.OperationID, planFileSHA256).Scan(&markerRaw, &status, &headers, &createdAt)
	if err == sql.ErrNoRows {
		return false, nil
	}
	if err != nil {
		return false, err
	}
	if status != 200 || headers != "{}" || createdAt != plan.ObservedAt ||
		!bytes.Equal(markerRaw, Bytes(historicalMaintenanceMarker(plan, planFileSHA256))) {
		return false, nil
	}
	return true, nil
}

// ClassifyHistoricalQualification is a read-only crash classifier. An exact
// pre-BEGIN image is NOT_APPLIED; a committed image requires the nine planned
// table rows plus unchanged residual rows in all 87 application tables.
func ClassifyHistoricalQualification(ctx context.Context, db *sql.DB, plan HistoricalQualificationPlan, planFileSHA256 string) (_ string, retErr error) {
	if db == nil || plan.Schema != "researchos.qualification-failure-maintenance-full-plan.v1" || planFileSHA256 == "" {
		return "", errors.New("qualification classifier plan invalid")
	}
	tx, err := db.BeginTx(ctx, &sql.TxOptions{ReadOnly: true})
	if err != nil {
		return "", err
	}
	defer func() { retErr = errors.Join(retErr, tx.Rollback()) }()
	full, err := store.QualificationMaintenanceCensus(ctx, tx)
	if err != nil {
		return "", err
	}
	var count int
	err = tx.QueryRowContext(ctx, `SELECT count(*) FROM idempotency WHERE principal=? AND project=? AND operation='host:qualification-failure-maintenance' AND key=?`,
		plan.AuthorID, plan.Subject.ProjectID, plan.OperationID).Scan(&count)
	if err != nil {
		return "", err
	}
	if Hash(full) == Hash(plan.BeforeCensus) && count == 0 {
		return "NOT_APPLIED", nil
	}
	if count != 1 || full.SchemaSHA256 != plan.BeforeCensus.SchemaSHA256 {
		return "UNKNOWN", nil
	}
	protected, err := store.QualificationMaintenanceProtectedCensus(ctx, tx)
	if err != nil {
		return "", err
	}
	selectors, err := plan.residualSelectors()
	if err != nil {
		return "", err
	}
	residual, err := store.QualificationMaintenanceResidualCensus(ctx, tx, selectors)
	if err != nil {
		return "", err
	}
	if protected != plan.BeforeProtectedSHA256 || residual != plan.BeforeResidualSHA256 {
		return "UNKNOWN", nil
	}
	exact, err := historicalQualificationExactRows(ctx, tx, plan, planFileSHA256)
	if err != nil {
		return "", err
	}
	if !exact {
		return "UNKNOWN", nil
	}
	return "APPLIED", nil
}

func (s *Service) verifyHistoricalQualificationTx(ctx context.Context, tx *sql.Tx,
	subject HistoricalQualificationSubject, source HistoricalQualificationSource,
	authorID, directory, sid string, native historicalQualificationNative) (verifiedHistoricalQualification, error) {
	var out verifiedHistoricalQualification
	deny := func(reason string) (verifiedHistoricalQualification, error) {
		return out, qualificationDenialUnavailable("historical " + reason)
	}
	if tx == nil || subject.ProjectID == "" || subject.TaskID == "" || subject.RunID == "" ||
		subject.RuntimeID == "" || subject.DispatchKey == "" || subject.Epoch != 1 ||
		source.BridgeSHA256 == "" || source.SourceCommit == "" || source.CoreSHA256 == "" ||
		source.WorkerSHA256 == "" || source.BuildSHA256 == "" || source.PID == 0 ||
		source.Created <= 0 || source.Job == "" || authorID == "" || sid == "" {
		return deny("exact subject/source binding missing")
	}
	j := native.journal
	f1, f2, f3 := native.frames[0], native.frames[1], native.frames[2]
	if native.bridgeHash != source.BridgeSHA256 || native.stdoutHash != j.StdoutHash || native.stderrHash != j.StderrHash ||
		j.DispatchKey != subject.DispatchKey || j.Identity.PID != source.PID || j.Identity.Created != source.Created ||
		j.Identity.Job != source.Job || j.Receipt.PID != source.PID || j.Receipt.Created != source.Created ||
		j.Receipt.Job != source.Job || j.Receipt.SID != j.Identity.SID || j.Receipt.Profile != j.Identity.Profile ||
		j.Identity.SID == "" || !j.Receipt.Stopped || !j.Receipt.StreamsDrained || !j.Receipt.CleanupComplete ||
		!j.Receipt.OutputCopied || j.Receipt.ExitCode != 124 || !j.Receipt.TimedOut ||
		j.Receipt.JobProcesses != 2 || j.Frames != 3 || j.Acknowledged != 2 ||
		j.QueueRequired || j.QueueInitSequence != 0 || len(j.CommandReceipts) != 0 ||
		j.Checkpoint != nil || j.CheckpointSequence != 0 || j.Paused || j.ProtocolComplete ||
		(j.State != "FAILED" && j.State != "UNKNOWN") || j.Reason != "qualification first dispatch gate denied TOOL" ||
		f1.Sequence != 1 || f1.Type != "context.ready" || f2.Sequence != 2 || f2.Capability != "MODEL" ||
		f3.Sequence != 3 || f3.Capability != "TOOL" || f2.Key == "" || f3.Key == "" ||
		f2.Key == f3.Key || f2.Route == "" || f3.Route != f2.Route {
		return deny("raw native Job accounting/three-frame source differs")
	}
	if filepath.Clean(directory) != directory || filepath.Base(directory) != subject.DispatchKey ||
		filepath.Base(filepath.Dir(directory)) != "runtime-dispatches" {
		return deny("dispatch directory identity differs")
	}
	run, err := load(tx, subject.ProjectID, "Run", subject.RunID)
	if err != nil {
		return out, err
	}
	task, err := load(tx, subject.ProjectID, "Task", subject.TaskID)
	if err != nil {
		return out, err
	}
	state, err := singleton(tx, subject.ProjectID, "ProjectState")
	if err != nil {
		return out, err
	}
	dispatch, err := runtimeDispatch(tx, subject.ProjectID, subject.RunID, subject.Epoch)
	if err != nil {
		return out, err
	}
	manifest, manifestOK := dispatch["manifest"].(map[string]any)
	admission, admissionOK := manifest["admission"].(map[string]any)
	profile, profileOK := admission["profile"].(map[string]any)
	modelConfig, configOK := profile["model_config"].(map[string]any)
	if !manifestOK || !admissionOK || !profileOK || !configOK || run["status"] != "RUNNING" ||
		run["task_id"] != subject.TaskID || run["runtime_id"] != subject.RuntimeID ||
		Hash(run["lease_epoch"]) != Hash(subject.Epoch) || run["checkpoint_artifact_id"] != nil ||
		task["task_type"] != "runtime_qualification" || task["active_run_id"] != subject.RunID ||
		dispatch["state"] != "STARTED" && dispatch["state"] != "UNKNOWN" ||
		dispatch["dispatch_key"] != subject.DispatchKey || dispatch["journal_locator"] != subject.DispatchKey ||
		dispatch["manifest_hash"] != j.ManifestHash || dispatch["worker"] != j.Worker ||
		Hash(dispatch["identity"]) != Hash(runtimeNativeIdentity(j.Identity)) ||
		admission["qualification_bootstrap"] != true || admission["mode"] != "LIVE" ||
		profile["build_hash"] != source.WorkerSHA256 || profile["bundle_hash"] != source.BundleSHA256 ||
		Hash(admission["profile_ref"]) != admission["profile_hash"] ||
		f2.Route != Str(modelConfig, "route") || len(Arr(run, "result_artifact_ids")) != 0 || len(j.Artifacts) != 0 {
		return deny("current Run/Task/dispatch/profile differs")
	}
	plan, planHash, ownerRoot, err := qualificationPlan(tx, subject.ProjectID, subject.TaskID, subject.RuntimeID)
	if err != nil || plan["task_hash"] != qualificationTaskHash(task) ||
		Hash(plan["profile_ref"]) != admission["profile_hash"] ||
		Hash(plan["model_qualification"]) != Hash(profile["model_qualification"]) ||
		runtimeTechnicalHashMust(tx, subject.ProjectID, subject.RuntimeID) != admission["technical_hash"] {
		return deny("original qualification plan differs")
	}
	var markerCount int
	if err := tx.QueryRowContext(ctx, `SELECT count(*) FROM runtime_qualification_runs WHERE project=? AND task=? AND run=? AND runtime=? AND epoch=? AND plan_hash=? AND profile_hash=? AND owner_root=?`,
		subject.ProjectID, subject.TaskID, subject.RunID, subject.RuntimeID, subject.Epoch, planHash, admission["profile_hash"], ownerRoot).Scan(&markerCount); err != nil || markerCount != 1 {
		return deny("original qualification marker differs")
	}
	author, err := clientAuthenticatedPrincipal(ctx, tx, authorID)
	if err != nil || !author.HasRole("OWNER") || !author.Allowed(subject.ProjectID, "", "", false) ||
		author.ID != ownerRoot {
		return deny("current Owner authority differs")
	}
	currentRoot, err := currentAuthorityRoot(tx, author.ID)
	if err != nil || currentRoot != ownerRoot {
		return deny("current Owner root differs")
	}
	profileRef, refOK := admission["profile_ref"].(map[string]any)
	if !refOK {
		return deny("profile reference missing")
	}
	ref, err := version(tx, subject.ProjectID, Object(profileRef))
	if err != nil || ref["access_class"] != "PROJECT" || ref["validity"] != "CURRENT" ||
		ref["sealed_at"] == nil || s.effective(tx, subject.ProjectID, Object(profileRef)) != nil {
		return deny("profile not effective")
	}
	var effects, rejected, unknown int
	if err := tx.QueryRowContext(ctx, `SELECT count(DISTINCT effect_key),coalesce(sum(CASE WHEN effect_key=? THEN 1 ELSE 0 END),0),coalesce(sum(CASE WHEN json_extract(body,'$.state') IN ('UNKNOWN','NOT_APPLIED') THEN 1 ELSE 0 END),0) FROM resource_effects WHERE project=? AND run=?`,
		f3.Key, subject.ProjectID, subject.RunID).Scan(&effects, &rejected, &unknown); err != nil || effects != 1 || rejected != 0 || unknown != 0 {
		return deny("effect census differs from sole MODEL")
	}
	effect, err := latestEffect(tx, subject.ProjectID, subject.RunID, f2.Key)
	if err != nil {
		return out, err
	}
	request, _ := effect["payload"].(map[string]any)
	modelPayload, payloadErr := Decode(f2.Payload)
	if payloadErr != nil || effect["state"] != "CONFIRMED" || request["capability"] != "MODEL" ||
		request["route"] != f2.Route || Hash(request["payload"]) != Hash(modelPayload) ||
		effect["receipt"] == nil || effect["key"] != f2.Key ||
		(effect["epoch"] != nil && Hash(effect["epoch"]) != Hash(subject.Epoch)) {
		return deny("MODEL request/receipt differs")
	}
	modelBinding, err := qualificationModelBindingTx(tx, subject.ProjectID, subject.RunID, subject.Epoch,
		dispatch, directory, f2.Key, f2.Route, Hash(modelPayload))
	if err != nil || modelBinding["fact_hash"] != native.modelHash {
		return deny("MODEL fact source differs")
	}
	var ledgerRows int
	var ledgerRaw string
	if err := tx.QueryRowContext(ctx, `SELECT count(*),coalesce(max(body),'') FROM domain_objects WHERE project=? AND kind='BudgetLedgerEntry' AND json_extract(body,'$.run_id')=?`,
		subject.ProjectID, subject.RunID).Scan(&ledgerRows, &ledgerRaw); err != nil || ledgerRows != 1 {
		return deny("monetary ledger census differs")
	}
	ledger, err := Decode([]byte(ledgerRaw))
	if err != nil || ledger["provider_request_id"] != f2.Key || ledger["id"] != modelBinding["reservation_id"] ||
		ledger["operation"] != "UNKNOWN" || ledger["money"] != nil || ledger["cost_basis"] != "UNKNOWN" {
		return deny("UNKNOWN money must remain UNKNOWN")
	}
	var queueFenceCount int
	if err := tx.QueryRowContext(ctx, `SELECT count(*) FROM client_queue_fences WHERE project=? AND run_id=?`,
		subject.ProjectID, subject.RunID).Scan(&queueFenceCount); err != nil || queueFenceCount != 0 {
		return deny("client queue fence remains")
	}
	for _, query := range []string{
		`SELECT count(*) FROM client_command_queue WHERE state NOT IN ('CONSUMED','DROPPED')`,
		`SELECT count(*) FROM client_control_requests WHERE state!='CONFIRMED'`,
	} {
		var n int
		if err := tx.QueryRowContext(ctx, query).Scan(&n); err != nil || n != 0 {
			return deny("client queue/control state remains")
		}
	}
	rawObservation, err := j.Observation()
	if err != nil || rawObservation["queue_empty"] != false {
		return deny("raw queue observation changed")
	}
	observation := Object(rawObservation)
	observation["state"] = "FAILED"
	observation["queue_empty"] = true
	observation["protocol"] = Object{"settled": false, "frames": int64(3), "acknowledged": int64(2), "classified_rejected": int64(1)}
	observation["qualification_failure"] = Object{
		"kind": historicalMaintenanceProofKind, "claim": "HOST_TOOL_EFFECT_NOT_DISPATCHED",
		"rule": historicalMaintenanceRule, "native_class": historicalMaintenanceNativeClass,
		"raw_bridge_hash": native.bridgeHash, "raw_stdout_hash": native.stdoutHash,
		"raw_stderr_hash": native.stderrHash, "raw_model_hash": native.modelHash,
		"frame_hashes": []any{Hash(f1), Hash(f2), Hash(f3)}, "model_effect_key": f2.Key,
		"rejected_effect_key": f3.Key, "raw_frames": int64(3), "raw_acknowledged": int64(2),
		"raw_queue_empty": false, "raw_cancelled": j.Cancelled, "raw_timed_out": j.Receipt.TimedOut,
		"raw_exit_code": j.Receipt.ExitCode, "native_ended": j.Ended,
		"historical_broker_joined": nil, "historical_raw_wait": nil,
	}
	source.StdoutSHA256, source.StderrSHA256 = native.stdoutHash, native.stderrHash
	return verifiedHistoricalQualification{subject: subject, author: author, ownerRoot: ownerRoot,
		profileRef: Object(profileRef), run: run, task: task, state: state, dispatch: dispatch,
		observation: observation, modelBinding: modelBinding, native: native, source: source}, nil
}
