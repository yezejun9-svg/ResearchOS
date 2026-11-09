//go:build windows

package qualificationmaintenancejournal

import (
	"bytes"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"
	"unsafe"

	"golang.org/x/sys/windows"
)

const qualificationPlanSchema = "researchos.qualification-failure-maintenance-plan.v1"
const qualificationEventSchema = "researchos.qualification-failure-maintenance-event.v1"

// JournalPlan is the immutable discoverable subset of the full reviewed plan.
// The payload fields are bound by their canonical hashes and validated again
// by the maintenance transaction before any SQL write.
type JournalPlan struct {
	Schema       string          `json:"schema"`
	OperationID  string          `json:"operation_id"`
	DataRoot     string          `json:"data_root"`
	Database     string          `json:"database"`
	PlanHash     string          `json:"plan_hash"`
	BeforeHash   string          `json:"before_hash"`
	AfterHash    string          `json:"after_hash"`
	SubjectHash  string          `json:"subject_hash"`
	EvidenceHash string          `json:"evidence_hash"`
	FullPlan     json.RawMessage `json:"full_plan"`
}
type QualificationEvent struct {
	Schema      string `json:"schema"`
	Sequence    int    `json:"sequence"`
	Previous    string `json:"previous"`
	Hash        string `json:"hash"`
	OperationID string `json:"operation_id"`
	PlanSHA256  string `json:"plan_sha256"`
	State       string `json:"state"`
	At          string `json:"at"`
	OutcomeHash string `json:"outcome_hash,omitempty"`
}

func qualificationFullPlanMatches(plan JournalPlan) error {
	decoder := json.NewDecoder(bytes.NewReader(plan.FullPlan))
	decoder.UseNumber()
	var f map[string]any
	if err := decoder.Decode(&f); err != nil {
		return err
	}
	var trailing any
	if decoder.Decode(&trailing) != io.EOF {
		return errors.New("qualification full plan trailing data")
	}
	get := func(key string) any { return f[key] }
	if get("schema") != "researchos.qualification-failure-maintenance-full-plan.v1" ||
		get("operation_id") != plan.OperationID || get("data_root") != plan.DataRoot || get("database") != plan.Database {
		return errors.New("qualification full plan identity mismatch")
	}
	outcome, _ := get("outcome_hash").(string)
	if !validDigest(outcome) {
		return errors.New("qualification full outcome invalid")
	}
	core, ok := get("core").(map[string]any)
	if !ok {
		return errors.New("qualification full core absent")
	}
	if value, err := hash(core); err != nil || value != plan.PlanHash {
		return errors.New("qualification full core hash mismatch")
	}
	before := map[string]any{
		"census": get("before_census"), "run": get("before_run"), "state": get("before_state"),
		"dispatch": get("before_dispatch"), "protected": get("before_protected_sha256"),
		"residual": get("before_residual_sha256"),
	}
	if value, err := hash(before); err != nil || value != plan.BeforeHash {
		return errors.New("qualification before hash mismatch")
	}
	proofBytesText, ok := get("proof_bytes").(string)
	if !ok {
		return errors.New("qualification proof bytes absent")
	}
	proofBytes, err := base64.StdEncoding.DecodeString(proofBytesText)
	if err != nil || len(proofBytes) == 0 || len(proofBytes) > 64<<10 {
		return errors.New("qualification proof bytes invalid")
	}
	after := map[string]any{
		"artifact": get("artifact"), "impact_link": get("impact_link"), "run": get("run"),
		"state": get("project_state"), "event": get("event"), "observation": get("observation"),
		"dispatch_sequence": get("dispatch_sequence"), "upload_hash": digest(proofBytes),
		"outcome_hash": get("outcome_hash"),
	}
	if value, err := hash(after); err != nil || value != plan.AfterHash {
		return errors.New("qualification after hash mismatch")
	}
	if value, err := hash(get("subject")); err != nil || value != plan.SubjectHash {
		return errors.New("qualification subject hash mismatch")
	}
	proof, ok := get("proof").(map[string]any)
	if !ok {
		return errors.New("qualification proof absent")
	}
	evidence := map[string]any{"source": get("source"), "native": proof["native"], "model": proof["model_binding"]}
	if value, err := hash(evidence); err != nil || value != plan.EvidenceHash {
		return errors.New("qualification evidence hash mismatch")
	}
	return nil
}

func qualificationTransition(previous, next string) bool {
	switch previous {
	case "":
		return next == "BEGIN"
	case "BEGIN":
		return next == "CLASSIFIED_NOT_APPLIED" || next == "DB_COMMITTED_OBSERVED"
	case "CLASSIFIED_NOT_APPLIED":
		return next == "ABORTED" || next == "DB_COMMITTED_OBSERVED"
	case "DB_COMMITTED_OBSERVED":
		return next == "DURABLE"
	}
	return false
}

func readQualification(root, operation string) (JournalPlan, string, []QualificationEvent, error) {
	var plan JournalPlan
	if !validOperation(operation) {
		return plan, "", nil, errors.New("qualification operation ID invalid")
	}
	dir := filepath.Join(root, "host", QualificationNamespace, operation)
	if err := checkPrivateDirectory(dir); err != nil {
		return plan, "", nil, err
	}
	entries, err := os.ReadDir(dir)
	if err != nil {
		return plan, "", nil, err
	}
	if len(entries) < 2 || len(entries) > 8 {
		return plan, "", nil, errors.New("qualification journal inventory bound")
	}
	var names []string
	for _, entry := range entries {
		if entry.IsDir() {
			return plan, "", nil, errors.New("qualification journal nested directory")
		}
		names = append(names, entry.Name())
	}
	sort.Strings(names)
	raw, err := readPrivateFile(filepath.Join(dir, "plan.json"), 256<<10)
	if err != nil {
		return plan, "", nil, err
	}
	if err := strictJSON(raw, &plan); err != nil {
		return plan, "", nil, err
	}
	if plan.Schema != qualificationPlanSchema || plan.OperationID != operation ||
		plan.DataRoot != root || plan.Database != filepath.Join(root, "researchos.sqlite") ||
		!validDigest(plan.PlanHash) || !validDigest(plan.BeforeHash) ||
		!validDigest(plan.AfterHash) || !validDigest(plan.SubjectHash) ||
		!validDigest(plan.EvidenceHash) || len(plan.FullPlan) == 0 {
		return plan, "", nil, errors.New("qualification journal plan identity invalid")
	}
	if err := qualificationFullPlanMatches(plan); err != nil {
		return plan, "", nil, err
	}
	var full map[string]any
	if err := strictJSON(plan.FullPlan, &full); err != nil {
		return plan, "", nil, err
	}
	outcome, _ := full["outcome_hash"].(string)
	if !validDigest(outcome) {
		return plan, "", nil, errors.New("qualification full outcome invalid")
	}
	planDigest := digest(raw)
	var events []QualificationEvent
	previous, state := "", ""
	for _, name := range names {
		if name == "plan.json" {
			continue
		}
		eventRaw, err := readPrivateFile(filepath.Join(dir, name), 64<<10)
		if err != nil {
			return plan, "", nil, err
		}
		var event QualificationEvent
		if err := strictJSON(eventRaw, &event); err != nil {
			return plan, "", nil, err
		}
		if name != fmt.Sprintf("%04d-%s.json", len(events)+1, event.State) ||
			event.Schema != qualificationEventSchema || event.Sequence != len(events)+1 ||
			event.OperationID != operation || event.PlanSHA256 != planDigest ||
			event.Previous != previous || !qualificationTransition(state, event.State) {
			return plan, "", nil, errors.New("qualification event chain invalid")
		}
		want := event.Hash
		event.Hash = ""
		got, err := hash(event)
		if err != nil || want != got {
			return plan, "", nil, errors.New("qualification event hash invalid")
		}
		if _, err := time.Parse(time.RFC3339Nano, event.At); err != nil {
			return plan, "", nil, err
		}
		if (event.State == "DURABLE" || event.State == "DB_COMMITTED_OBSERVED") != validDigest(event.OutcomeHash) {
			return plan, "", nil, errors.New("qualification outcome digest missing or premature")
		}
		if event.OutcomeHash != "" && event.OutcomeHash != outcome {
			return plan, "", nil, errors.New("qualification event outcome differs")
		}
		event.Hash = want
		events = append(events, event)
		previous, state = want, event.State
	}
	if len(events) == 0 {
		return plan, "", nil, errors.New("qualification BEGIN missing")
	}
	return plan, planDigest, events, nil
}

func checkQualificationOrdinary(root string) error {
	namespace := filepath.Join(root, "host", QualificationNamespace)
	if _, err := os.Lstat(namespace); os.IsNotExist(err) {
		return nil
	} else if err != nil {
		return err
	}
	if err := checkPrivateDirectory(namespace); err != nil {
		return err
	}
	entries, err := os.ReadDir(namespace)
	if err != nil {
		return err
	}
	if len(entries) > 256 {
		return errors.New("qualification history bound")
	}
	for _, entry := range entries {
		if !entry.IsDir() || !validOperation(entry.Name()) {
			return errors.New("qualification unknown operation")
		}
		_, _, events, err := readQualification(root, entry.Name())
		if err != nil {
			return err
		}
		state := events[len(events)-1].State
		if state != "ABORTED" && state != "DURABLE" {
			return errors.New("qualification pending operation")
		}
	}
	return nil
}

func inspectQualification(root, operation, planDigest string) (HistoryStatus, error) {
	var status HistoryStatus
	_, actualDigest, events, err := readQualification(root, operation)
	if err != nil {
		return status, err
	}
	if actualDigest != planDigest {
		return status, errors.New("qualification own plan digest mismatch")
	}
	namespace := filepath.Join(root, "host", QualificationNamespace)
	entries, err := os.ReadDir(namespace)
	if err != nil {
		return status, err
	}
	for _, entry := range entries {
		if entry.Name() == operation {
			continue
		}
		if !entry.IsDir() || !validOperation(entry.Name()) {
			return status, errors.New("qualification other operation invalid")
		}
		_, _, other, err := readQualification(root, entry.Name())
		if err != nil {
			return status, err
		}
		last := other[len(other)-1].State
		if last != "ABORTED" && last != "DURABLE" {
			return status, errors.New("qualification other pending operation")
		}
	}
	state := events[len(events)-1].State
	return HistoryStatus{Namespace: QualificationNamespace, Operation: operation, PlanDigest: planDigest,
		State: state, Terminal: state == "ABORTED" || state == "DURABLE",
		Applied: state == "DB_COMMITTED_OBSERVED" || state == "DURABLE"}, nil
}

func currentSID() (string, error) {
	user, err := windows.GetCurrentProcessToken().GetTokenUser()
	if err != nil || user == nil || user.User.Sid == nil {
		return "", errors.New("maintenance SID unavailable")
	}
	return user.User.Sid.String(), nil
}

func checkPrivateACL(path string, directory bool) error {
	sid, err := currentSID()
	if err != nil {
		return err
	}
	sd, err := windows.GetNamedSecurityInfo(path, windows.SE_FILE_OBJECT,
		windows.OWNER_SECURITY_INFORMATION|windows.DACL_SECURITY_INFORMATION)
	if err != nil {
		return err
	}
	owner, _, err := sd.Owner()
	if err != nil || owner == nil || owner.String() != sid {
		return errors.New("maintenance journal owner mismatch")
	}
	control, _, err := sd.Control()
	if err != nil || control&windows.SE_DACL_PROTECTED == 0 {
		return errors.New("maintenance journal unprotected DACL")
	}
	acl, _, err := sd.DACL()
	if err != nil || acl == nil || acl.AceCount != 1 {
		return errors.New("maintenance journal ACE count")
	}
	var ace *windows.ACCESS_ALLOWED_ACE
	if err := windows.GetAce(acl, 0, &ace); err != nil {
		return err
	}
	flags := byte(0)
	if directory {
		flags = windows.OBJECT_INHERIT_ACE | windows.CONTAINER_INHERIT_ACE
	}
	if ace.Header.AceType != windows.ACCESS_ALLOWED_ACE_TYPE || ace.Header.AceFlags != flags ||
		ace.Mask != 0x001f01ff || (*windows.SID)(unsafe.Pointer(&ace.SidStart)).String() != sid {
		return errors.New("maintenance journal ACL differs")
	}
	return nil
}

func openNativePath(path string, directory bool) (windows.Handle, error) {
	if !filepath.IsAbs(path) || filepath.Clean(path) != path || strings.Contains(path[len(filepath.VolumeName(path)):], ":") {
		return 0, errors.New("maintenance path noncanonical")
	}
	wide, err := windows.UTF16PtrFromString(path)
	if err != nil {
		return 0, err
	}
	h, err := windows.CreateFile(wide, windows.GENERIC_READ, windows.FILE_SHARE_READ,
		nil, windows.OPEN_EXISTING, windows.FILE_FLAG_OPEN_REPARSE_POINT|windows.FILE_FLAG_BACKUP_SEMANTICS, 0)
	if err != nil {
		return 0, err
	}
	var info windows.ByHandleFileInformation
	if err := windows.GetFileInformationByHandle(h, &info); err != nil {
		windows.CloseHandle(h)
		return 0, err
	}
	if info.FileAttributes&windows.FILE_ATTRIBUTE_REPARSE_POINT != 0 ||
		(info.FileAttributes&windows.FILE_ATTRIBUTE_DIRECTORY != 0) != directory ||
		(!directory && info.NumberOfLinks != 1) {
		windows.CloseHandle(h)
		return 0, errors.New("maintenance path reparse, alias or kind mismatch")
	}
	return h, nil
}

func checkPrivateDirectory(path string) error {
	h, err := openNativePath(path, true)
	if err != nil {
		return err
	}
	defer windows.CloseHandle(h)
	return checkPrivateACL(path, true)
}

func createPrivateDirectory(path string) error {
	sid, err := currentSID()
	if err != nil {
		return err
	}
	sd, err := windows.SecurityDescriptorFromString("O:" + sid + "D:P(A;OICI;FA;;;" + sid + ")")
	if err != nil {
		return err
	}
	wide, err := windows.UTF16PtrFromString(path)
	if err != nil {
		return err
	}
	sa := windows.SecurityAttributes{Length: uint32(unsafe.Sizeof(windows.SecurityAttributes{})), SecurityDescriptor: sd}
	if err := windows.CreateDirectory(wide, &sa); err != nil {
		return err
	}
	return checkPrivateDirectory(path)
}

func createPrivateFile(path string, raw []byte) error {
	if len(raw) == 0 || len(raw) > 256<<10 {
		return errors.New("qualification journal file bound")
	}
	sid, err := currentSID()
	if err != nil {
		return err
	}
	sd, err := windows.SecurityDescriptorFromString("O:" + sid + "D:P(A;;FA;;;" + sid + ")")
	if err != nil {
		return err
	}
	wide, err := windows.UTF16PtrFromString(path)
	if err != nil {
		return err
	}
	sa := windows.SecurityAttributes{Length: uint32(unsafe.Sizeof(windows.SecurityAttributes{})), SecurityDescriptor: sd}
	h, err := windows.CreateFile(wide, windows.GENERIC_WRITE|windows.READ_CONTROL, windows.FILE_SHARE_READ,
		&sa, windows.CREATE_NEW, windows.FILE_ATTRIBUTE_NORMAL|windows.FILE_FLAG_WRITE_THROUGH, 0)
	if err != nil {
		return err
	}
	f := os.NewFile(uintptr(h), path)
	if err := checkPrivateACL(path, false); err != nil {
		_ = f.Close()
		return err
	}
	n, writeErr := f.Write(raw)
	if writeErr == nil && n != len(raw) {
		writeErr = io.ErrShortWrite
	}
	return errors.Join(writeErr, f.Sync(), f.Close())
}

// StartQualification creates the immutable plan and BEGIN before a caller may
// open a write transaction. A crash at any intermediate point leaves a
// blocking inventory; this function never repairs an existing operation.
func StartQualification(root string, planRaw []byte) (string, error) {
	var plan JournalPlan
	if err := strictJSON(planRaw, &plan); err != nil {
		return "", err
	}
	if plan.Schema != qualificationPlanSchema || !validOperation(plan.OperationID) ||
		plan.DataRoot != root || plan.Database != filepath.Join(root, "researchos.sqlite") ||
		!validDigest(plan.PlanHash) || !validDigest(plan.BeforeHash) || !validDigest(plan.AfterHash) ||
		!validDigest(plan.SubjectHash) || !validDigest(plan.EvidenceHash) || len(plan.FullPlan) == 0 {
		return "", errors.New("qualification journal plan invalid")
	}
	if err := qualificationFullPlanMatches(plan); err != nil {
		return "", err
	}
	if err := checkPrivateDirectory(filepath.Join(root, "host")); err != nil {
		return "", err
	}
	namespace := filepath.Join(root, "host", QualificationNamespace)
	if _, err := os.Lstat(namespace); os.IsNotExist(err) {
		if err := createPrivateDirectory(namespace); err != nil {
			return "", err
		}
	} else if err != nil {
		return "", err
	}
	if err := checkPrivateDirectory(namespace); err != nil {
		return "", err
	}
	dir := filepath.Join(namespace, plan.OperationID)
	if err := createPrivateDirectory(dir); err != nil {
		return "", err
	}
	if err := createPrivateFile(filepath.Join(dir, "plan.json"), planRaw); err != nil {
		return "", err
	}
	planDigest := digest(planRaw)
	event := QualificationEvent{Schema: qualificationEventSchema, Sequence: 1, OperationID: plan.OperationID,
		PlanSHA256: planDigest, State: "BEGIN", At: time.Now().UTC().Format(time.RFC3339Nano)}
	var err error
	event.Hash, err = hash(event)
	if err != nil {
		return "", err
	}
	raw, err := json.Marshal(event)
	if err != nil {
		return "", err
	}
	if err := createPrivateFile(filepath.Join(dir, "0001-BEGIN.json"), raw); err != nil {
		return "", err
	}
	return planDigest, nil
}

// AppendQualification records an observation after the caller has independently
// classified the exact SQLite state. It cannot infer that state from a flag.
func AppendQualification(root, operation, planDigest, state, outcomeDigest string) error {
	plan, actual, events, err := readQualification(root, operation)
	if err != nil || actual != planDigest {
		return errors.New("qualification journal changed before append")
	}
	previous := events[len(events)-1]
	if !qualificationTransition(previous.State, state) ||
		((state == "DB_COMMITTED_OBSERVED" || state == "DURABLE") != validDigest(outcomeDigest)) {
		return errors.New("qualification journal transition invalid")
	}
	if outcomeDigest != "" {
		var full map[string]any
		if err := strictJSON(plan.FullPlan, &full); err != nil {
			return err
		}
		if outcomeDigest != full["outcome_hash"] {
			return errors.New("qualification outcome differs from immutable plan")
		}
	}
	event := QualificationEvent{Schema: qualificationEventSchema, Sequence: len(events) + 1,
		Previous: previous.Hash, OperationID: operation, PlanSHA256: planDigest,
		State: state, At: time.Now().UTC().Format(time.RFC3339Nano), OutcomeHash: outcomeDigest}
	event.Hash, err = hash(event)
	if err != nil {
		return err
	}
	raw, err := json.Marshal(event)
	if err != nil {
		return err
	}
	dir := filepath.Join(root, "host", QualificationNamespace, operation)
	return createPrivateFile(filepath.Join(dir, fmt.Sprintf("%04d-%s.json", event.Sequence, state)), raw)
}

func readPrivateFile(path string, limit int64) ([]byte, error) {
	h, err := openNativePath(path, false)
	if err != nil {
		return nil, err
	}
	f := os.NewFile(uintptr(h), path)
	defer f.Close()
	if err := checkPrivateACL(path, false); err != nil {
		return nil, err
	}
	info, err := f.Stat()
	if err != nil || info.Size() < 1 || info.Size() > limit {
		return nil, errors.New("maintenance file bound")
	}
	raw, err := io.ReadAll(io.LimitReader(f, limit+1))
	if err != nil || int64(len(raw)) != info.Size() {
		return nil, errors.New("maintenance file raced or truncated")
	}
	return raw, nil
}

// CheckOrdinary is a pure read under the caller's native coordinator lock.
// Both namespaces must be complete and current before any startup side effect.
func CheckOrdinary(root string) error {
	if err := checkQualificationOrdinary(root); err != nil {
		return err
	}
	return checkReplacementOrdinary(root)
}

// OpenOwnInspection makes only the exact matching pending transition visible.
// Callers must still establish all separate owner, evidence and write authority.
func OpenOwnInspection(root, namespace, operation, planDigest string) (InspectionPermit, HistoryStatus, error) {
	var zero InspectionPermit
	var status HistoryStatus
	if !validOperation(operation) || !validDigest(planDigest) {
		return zero, status, errors.New("own operation identity invalid")
	}
	switch namespace {
	case ReplacementNamespace:
		if err := checkQualificationOrdinary(root); err != nil {
			return zero, status, err
		}
		var err error
		status, err = inspectReplacement(root, operation, planDigest, nil)
		if err != nil {
			return zero, status, err
		}
	case QualificationNamespace:
		if err := checkReplacementOrdinary(root); err != nil {
			return zero, status, err
		}
		var err error
		status, err = inspectQualification(root, operation, planDigest)
		if err != nil {
			return zero, status, err
		}
	default:
		return zero, status, errors.New("own namespace invalid")
	}
	return InspectionPermit{root: root, namespace: namespace, operation: operation, planDigest: planDigest}, status, nil
}

func OpenOwnReplacementInspection(root, operation, planDigest string, planBytes []byte) (InspectionPermit, HistoryStatus, error) {
	var zero InspectionPermit
	var status HistoryStatus
	if !validOperation(operation) || !validDigest(planDigest) || digest(planBytes) != planDigest {
		return zero, status, errors.New("own replacement plan identity invalid")
	}
	if err := checkQualificationOrdinary(root); err != nil {
		return zero, status, err
	}
	var err error
	status, err = inspectReplacement(root, operation, planDigest, planBytes)
	if err != nil {
		return zero, status, err
	}
	return InspectionPermit{root: root, namespace: ReplacementNamespace, operation: operation,
		planDigest: planDigest, replacementPlan: append([]byte(nil), planBytes...)}, status, nil
}

func (p InspectionPermit) Check(root string) (HistoryStatus, error) {
	if p.root == "" || p.root != root {
		return HistoryStatus{}, errors.New("own inspection root mismatch")
	}
	if p.namespace == ReplacementNamespace && p.replacementPlan != nil {
		if err := checkQualificationOrdinary(root); err != nil {
			return HistoryStatus{}, err
		}
		return inspectReplacement(root, p.operation, p.planDigest, p.replacementPlan)
	}
	_, status, err := OpenOwnInspection(root, p.namespace, p.operation, p.planDigest)
	return status, err
}
