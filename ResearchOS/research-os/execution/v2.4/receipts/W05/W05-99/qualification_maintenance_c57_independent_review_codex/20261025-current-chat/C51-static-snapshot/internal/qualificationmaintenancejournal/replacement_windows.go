//go:build windows

package qualificationmaintenancejournal

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"reflect"
	"sort"
	"strings"
	"time"
)

const replacementPlanSchema = "researchos.runtime-verifier-replacement-plan.v2"
const replacementEventSchema = "researchos.runtime-verifier-replacement.v1"

type replacementFileID struct {
	Volume    uint32
	IndexHigh uint32
	IndexLow  uint32
}
type replacementInstallation struct {
	Schema         string   `json:"schema"`
	ServiceID      string   `json:"service_id"`
	Protocol       string   `json:"protocol"`
	Executable     string   `json:"executable"`
	ExecutableHash string   `json:"executable_hash"`
	SourceCommit   string   `json:"source_commit"`
	Arguments      []string `json:"arguments"`
}
type replacementRegistration struct {
	Schema         string                  `json:"schema"`
	OwnerHost      string                  `json:"owner_host"`
	OwnerPrincipal string                  `json:"owner_principal"`
	ServiceRoot    string                  `json:"service_root"`
	InstallHash    string                  `json:"installation_hash"`
	Installation   replacementInstallation `json:"installation"`
}
type replacementPlan struct {
	Schema                  string                  `json:"schema"`
	HistorySequence         uint64                  `json:"history_sequence"`
	PredecessorOperation    string                  `json:"predecessor_operation,omitempty"`
	PredecessorPlanSHA256   string                  `json:"predecessor_plan_sha256,omitempty"`
	PredecessorTerminalHash string                  `json:"predecessor_terminal_hash,omitempty"`
	OperationID             string                  `json:"operation_id"`
	CreatedAt               string                  `json:"created_at"`
	DataRoot                string                  `json:"data_root"`
	HostPath                string                  `json:"host_path"`
	DBPath                  string                  `json:"db_path"`
	FileIDs                 [3]replacementFileID    `json:"file_ids"`
	PrincipalRef            string                  `json:"principal_ref"`
	HostID                  string                  `json:"host_id"`
	Owner                   string                  `json:"owner"`
	Root                    string                  `json:"service_root"`
	StateSHA256             string                  `json:"state_sha256"`
	LineageHash             string                  `json:"lineage_hash"`
	SchemaVersion           int                     `json:"schema_version"`
	Census                  [4]int                  `json:"readonly_census"`
	OldBytes                []byte                  `json:"old_record_bytes"`
	OldSHA256               string                  `json:"old_record_sha256"`
	OldHash                 string                  `json:"old_registration_hash"`
	OldInstallationHash     string                  `json:"old_installation_hash"`
	Manifest                string                  `json:"manifest"`
	ManifestSHA256          string                  `json:"manifest_sha256"`
	Installation            replacementInstallation `json:"installation"`
	NewBytes                []byte                  `json:"new_record_bytes"`
	NewSHA256               string                  `json:"new_record_sha256"`
	NewHash                 string                  `json:"registration_hash"`
	NewInstallationHash     string                  `json:"installation_hash"`
	RollbackOf              string                  `json:"rollback_of,omitempty"`
}
type replacementEvent struct {
	Schema      string `json:"schema"`
	Sequence    int    `json:"sequence"`
	Previous    string `json:"previous"`
	Hash        string `json:"hash"`
	OperationID string `json:"operation_id"`
	PlanSHA256  string `json:"plan_sha256"`
	OldSHA256   string `json:"old_record_sha256"`
	NewSHA256   string `json:"new_record_sha256"`
	State       string `json:"state"`
	At          string `json:"at"`
}
type replacementView struct {
	plan       replacementPlan
	planDigest string
	files      map[string][]byte
	events     []replacementEvent
}
type replacementHead struct {
	sequence     uint64
	operation    string
	planDigest   string
	terminalHash string
	recordDigest string
}

func replacementPlanValid(p replacementPlan, root, operation string) error {
	if p.Schema != replacementPlanSchema || !validOperation(p.OperationID) || p.OperationID != operation ||
		p.RollbackOf == p.OperationID || (p.RollbackOf != "" && !validOperation(p.RollbackOf)) ||
		p.DataRoot != root || p.HostPath != filepath.Join(root, "host") ||
		p.DBPath != filepath.Join(root, "researchos.sqlite") || p.SchemaVersion != 24 || p.Census != [4]int{} {
		return errors.New("replacement plan identity invalid")
	}
	if p.HistorySequence == 0 || (p.HistorySequence == 1 && (p.PredecessorOperation != "" || p.PredecessorPlanSHA256 != "" || p.PredecessorTerminalHash != "")) ||
		(p.HistorySequence > 1 && (!validOperation(p.PredecessorOperation) || !validDigest(p.PredecessorPlanSHA256) || !validDigest(p.PredecessorTerminalHash))) {
		return errors.New("replacement history predecessor invalid")
	}
	if _, err := time.Parse(time.RFC3339Nano, p.CreatedAt); err != nil {
		return err
	}
	if !validDigest(p.OldSHA256) || !validDigest(p.NewSHA256) || digest(p.OldBytes) != p.OldSHA256 ||
		digest(p.NewBytes) != p.NewSHA256 || p.OldSHA256 == p.NewSHA256 ||
		!validDigest(p.ManifestSHA256) || !validDigest(p.StateSHA256) {
		return errors.New("replacement plan digest invalid")
	}
	var old, next replacementRegistration
	if strictJSON(p.OldBytes, &old) != nil || strictJSON(p.NewBytes, &next) != nil {
		return errors.New("replacement registration invalid")
	}
	oldHash, err := hash(old)
	if err != nil || oldHash != p.OldHash {
		return errors.New("replacement old registration hash invalid")
	}
	newHash, err := hash(next)
	if err != nil || newHash != p.NewHash {
		return errors.New("replacement new registration hash invalid")
	}
	oldInstallHash, err := hash(old.Installation)
	if err != nil || oldInstallHash != old.InstallHash || oldInstallHash != p.OldInstallationHash {
		return errors.New("replacement old installation hash invalid")
	}
	newInstallHash, err := hash(next.Installation)
	if err != nil || newInstallHash != next.InstallHash || newInstallHash != p.NewInstallationHash {
		return errors.New("replacement new installation hash invalid")
	}
	if old.Schema != "researchos.runtime-verifier-registration.v1" || next.Schema != old.Schema ||
		old.OwnerHost != p.HostID || old.OwnerPrincipal != p.Owner || old.ServiceRoot != p.Root ||
		next.OwnerHost != old.OwnerHost || next.OwnerPrincipal != old.OwnerPrincipal || next.ServiceRoot != old.ServiceRoot ||
		!reflect.DeepEqual(next.Installation, p.Installation) {
		return errors.New("replacement registration authority changed")
	}
	expected := old
	expected.Installation = p.Installation
	expected.InstallHash = newInstallHash
	expectedBytes, err := json.MarshalIndent(expected, "", "  ")
	if err != nil || !bytes.Equal(expectedBytes, p.NewBytes) {
		return errors.New("replacement candidate bytes invalid")
	}
	oldExecutable := old.Installation
	newExecutable := p.Installation
	newExecutable.Executable, newExecutable.ExecutableHash, newExecutable.SourceCommit =
		oldExecutable.Executable, oldExecutable.ExecutableHash, oldExecutable.SourceCommit
	oldExecutableHash, err := hash(oldExecutable)
	if err != nil {
		return err
	}
	newExecutableHash, err := hash(newExecutable)
	if err != nil || oldExecutableHash != newExecutableHash {
		return errors.New("replacement changed forbidden installation fields")
	}
	return nil
}

func replacementTransition(old, next string) bool {
	switch old {
	case "":
		return next == "PREPARED" || next == "ABORTED"
	case "PREPARED":
		return next == "PUBLISHING" || next == "ABORTED"
	case "PUBLISHING":
		return next == "COMMITTED" || next == "ABORTED"
	}
	return false
}

func readReplacement(root, operation string, externalPlan []byte) (replacementView, error) {
	v := replacementView{files: map[string][]byte{}}
	if !validOperation(operation) {
		return v, errors.New("replacement operation ID invalid")
	}
	dir := filepath.Join(root, "host", ReplacementNamespace, operation)
	if err := checkPrivateDirectory(dir); err != nil {
		return v, err
	}
	entries, err := os.ReadDir(dir)
	if err != nil {
		return v, err
	}
	if len(entries) > 12 || (externalPlan == nil && len(entries) == 0) {
		return v, errors.New("replacement journal inventory bound")
	}
	for _, entry := range entries {
		if entry.IsDir() {
			return v, errors.New("replacement journal has directory")
		}
		name := entry.Name()
		raw, err := readPrivateFile(filepath.Join(dir, name), 256<<10)
		if err != nil {
			return v, err
		}
		v.files[name] = raw
	}
	raw, ok := v.files["plan.json"]
	if externalPlan != nil {
		if ok && !bytes.Equal(raw, externalPlan) {
			return v, errors.New("own replacement plan bytes changed")
		}
		raw = externalPlan
	} else if !ok {
		return v, errors.New("replacement plan missing")
	}
	if err := strictJSON(raw, &v.plan); err != nil {
		return v, err
	}
	if err := replacementPlanValid(v.plan, root, operation); err != nil {
		return v, err
	}
	v.planDigest = digest(raw)
	if old, exists := v.files["old-registration.bin"]; exists && !bytes.Equal(old, v.plan.OldBytes) {
		return v, errors.New("replacement old snapshot invalid")
	}
	if next, exists := v.files["new-registration.bin"]; exists && !bytes.Equal(next, v.plan.NewBytes) {
		return v, errors.New("replacement new snapshot invalid")
	}
	if externalPlan == nil && (!bytes.Equal(v.files["old-registration.bin"], v.plan.OldBytes) ||
		!bytes.Equal(v.files["new-registration.bin"], v.plan.NewBytes)) {
		return v, errors.New("replacement immutable snapshots invalid")
	}
	if stage, present := v.files["stage.bin"]; present && !bytes.Equal(stage, v.plan.NewBytes) {
		return v, errors.New("replacement stage invalid")
	}
	var eventNames []string
	for name := range v.files {
		switch name {
		case "plan.json", "old-registration.bin", "new-registration.bin", "stage.bin", "actual-backup.bin":
		default:
			eventNames = append(eventNames, name)
		}
	}
	sort.Strings(eventNames)
	previous, state := "", ""
	for _, name := range eventNames {
		raw := v.files[name]
		var event replacementEvent
		if err := strictJSON(raw, &event); err != nil {
			return v, err
		}
		if name != fmt.Sprintf("%04d-%s.json", len(v.events)+1, strings.ToLower(event.State)) ||
			event.Schema != replacementEventSchema || event.Sequence != len(v.events)+1 ||
			event.OperationID != operation || event.PlanSHA256 != v.planDigest ||
			event.OldSHA256 != v.plan.OldSHA256 || event.NewSHA256 != v.plan.NewSHA256 ||
			event.Previous != previous || !replacementTransition(state, event.State) {
			return v, errors.New("replacement event chain invalid")
		}
		if _, err := time.Parse(time.RFC3339Nano, event.At); err != nil {
			return v, err
		}
		want := event.Hash
		event.Hash = ""
		got, err := hash(event)
		if err != nil || want != got {
			return v, errors.New("replacement event hash invalid")
		}
		event.Hash = want
		v.events = append(v.events, event)
		previous, state = event.Hash, event.State
	}
	if len(v.events) > 0 && (!bytes.Equal(v.files["old-registration.bin"], v.plan.OldBytes) ||
		!bytes.Equal(v.files["new-registration.bin"], v.plan.NewBytes) || !ok) {
		return v, errors.New("replacement event lacks immutable plan/snapshots")
	}
	if externalPlan == nil && len(v.events) == 0 {
		return v, errors.New("replacement event missing")
	}
	return v, nil
}

func replacementExtends(p replacementPlan, h replacementHead) bool {
	return p.HistorySequence == h.sequence+1 &&
		p.PredecessorOperation == h.operation &&
		p.PredecessorPlanSHA256 == h.planDigest &&
		p.PredecessorTerminalHash == h.terminalHash &&
		(h.sequence == 0 || p.OldSHA256 == h.recordDigest)
}

// readReplacementHistory validates every terminal predecessor. An exact pending
// operation is checked against the predecessor separately by inspectReplacement.
func readReplacementHistory(root, own string) (replacementHead, error) {
	var head replacementHead
	namespace := filepath.Join(root, "host", ReplacementNamespace)
	if _, err := os.Lstat(namespace); os.IsNotExist(err) {
		return head, nil
	} else if err != nil {
		return head, err
	}
	if err := checkPrivateDirectory(namespace); err != nil {
		return head, err
	}
	entries, err := os.ReadDir(namespace)
	if err != nil {
		return head, err
	}
	if len(entries) > 256 {
		return head, errors.New("replacement history bound")
	}
	var views []replacementView
	for _, entry := range entries {
		if !entry.IsDir() || !validOperation(entry.Name()) {
			return head, errors.New("replacement unknown operation")
		}
		if entry.Name() == own {
			continue
		}
		v, err := readReplacement(root, entry.Name(), nil)
		if err != nil {
			return head, err
		}
		state := v.events[len(v.events)-1].State
		switch state {
		case "COMMITTED":
			if !bytes.Equal(v.files["actual-backup.bin"], v.plan.OldBytes) || v.files["stage.bin"] != nil {
				return head, errors.New("replacement committed inventory invalid")
			}
		case "ABORTED":
			if v.files["actual-backup.bin"] != nil {
				return head, errors.New("replacement aborted publication evidence")
			}
		default:
			return head, errors.New("replacement pending operation")
		}
		views = append(views, v)
	}
	sort.Slice(views, func(i, j int) bool { return views[i].plan.HistorySequence < views[j].plan.HistorySequence })
	for _, v := range views {
		if !replacementExtends(v.plan, head) {
			return head, errors.New("replacement causal history invalid")
		}
		last := v.events[len(v.events)-1]
		record := v.plan.OldSHA256
		if last.State == "COMMITTED" {
			record = v.plan.NewSHA256
		}
		head = replacementHead{v.plan.HistorySequence, v.plan.OperationID, v.planDigest, last.Hash, record}
	}
	return head, nil
}

func checkReplacementOrdinary(root string) error {
	head, err := readReplacementHistory(root, "")
	if err != nil {
		return err
	}
	if head.sequence == 0 {
		return nil
	}
	raw, err := readPrivateFile(filepath.Join(root, "host", "runtime-verifier-installation.json"), 64<<10)
	if err != nil {
		return err
	}
	if digest(raw) != head.recordDigest {
		return errors.New("latest replacement target drift")
	}
	return nil
}

func inspectReplacement(root, operation, planDigest string, externalPlan []byte) (HistoryStatus, error) {
	var status HistoryStatus
	v, err := readReplacement(root, operation, externalPlan)
	if err != nil {
		return status, err
	}
	if planDigest != v.planDigest {
		return status, errors.New("own replacement plan digest mismatch")
	}
	head, err := readReplacementHistory(root, operation)
	if err != nil {
		return status, err
	}
	if !replacementExtends(v.plan, head) {
		return status, errors.New("own replacement predecessor invalid")
	}
	current, err := readPrivateFile(filepath.Join(root, "host", "runtime-verifier-installation.json"), 64<<10)
	if err != nil {
		return status, err
	}
	_, published := v.files["actual-backup.bin"]
	_, stage := v.files["stage.bin"]
	applied := bytes.Equal(current, v.plan.NewBytes) && published &&
		bytes.Equal(v.files["actual-backup.bin"], v.plan.OldBytes) && !stage
	unapplied := bytes.Equal(current, v.plan.OldBytes) && !published
	state := ""
	if len(v.events) > 0 {
		state = v.events[len(v.events)-1].State
	}
	if !applied && !unapplied {
		return status, errors.New("own replacement ambiguous inventory")
	}
	if state == "COMMITTED" && !applied || state == "ABORTED" && !unapplied ||
		state == "PREPARED" && applied {
		return status, errors.New("own replacement state/target mismatch")
	}
	status = HistoryStatus{Namespace: ReplacementNamespace, Operation: operation,
		PlanDigest: planDigest, State: state, Terminal: state == "COMMITTED" || state == "ABORTED", Applied: applied}
	return status, nil
}
