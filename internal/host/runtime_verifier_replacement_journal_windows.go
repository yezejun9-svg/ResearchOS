//go:build windows

package host

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"
	"unsafe"

	"golang.org/x/sys/windows"
	rt "researchos.local/research-os/adapters/runtime"
	"researchos.local/research-os/internal/domain"
)

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
type replacementJournalView struct {
	Events []replacementEvent
	Files  map[string][]byte
}
type replacementHistoryHead struct {
	Sequence                                            uint64
	OperationID, PlanSHA256, TerminalHash, RecordSHA256 string
}

func replacementSameHistory(a, b replacementPlan) bool {
	return a.HistorySequence == b.HistorySequence && a.PredecessorOperation == b.PredecessorOperation && a.PredecessorPlanSHA256 == b.PredecessorPlanSHA256 && a.PredecessorTerminalHash == b.PredecessorTerminalHash
}
func replacementExtendsHead(p replacementPlan, h replacementHistoryHead) bool {
	return p.HistorySequence == h.Sequence+1 && p.PredecessorOperation == h.OperationID && p.PredecessorPlanSHA256 == h.PlanSHA256 && p.PredecessorTerminalHash == h.TerminalHash && (h.Sequence == 0 || p.OldSHA256 == h.RecordSHA256)
}

// Supply the protected descriptor to the native create itself. A process death
// between mkdir and a later SetNamedSecurityInfo must not strand recovery with
// an inherited (rather than protected) operation directory.
func replacementMkdirPrivate(path string) error {
	sid, e := currentSIDString()
	if e != nil {
		return e
	}
	sd, e := windows.SecurityDescriptorFromString("O:" + sid + "D:P(A;OICI;FA;;;" + sid + ")")
	if e != nil {
		return e
	}
	wide, e := windows.UTF16PtrFromString(path)
	if e != nil {
		return e
	}
	sa := windows.SecurityAttributes{Length: uint32(unsafe.Sizeof(windows.SecurityAttributes{})), SecurityDescriptor: sd}
	if e = windows.CreateDirectory(wide, &sa); e != nil {
		return e
	}
	return replacementACL(path, true, true)
}

func replacementCreateDirectory(path string) error {
	if _, e := os.Lstat(path); os.IsNotExist(e) {
		if e = replacementMkdirPrivate(path); e != nil {
			return e
		}
	} else if e != nil {
		return e
	}
	if _, e := replacementIdentity(path, true); e != nil {
		return e
	}
	return replacementACL(path, true, true)
}

// Publish only complete bytes using a non-overwriting write-through rename.
// The temp receives its private ACL before any sensitive content is written.
func replacementWrite(dir, name string, raw []byte) error {
	path := filepath.Join(dir, name)
	if old, e := os.Lstat(path); e == nil {
		if !old.Mode().IsRegular() {
			return errors.New("immutable target not regular")
		}
		got, e := replacementRead(path, 256<<10)
		if e != nil {
			return e
		}
		if !bytes.Equal(got, raw) {
			return errors.New("immutable bytes conflict")
		}
		return nil
	} else if !os.IsNotExist(e) {
		return e
	}
	tmp, e := os.CreateTemp(dir, name+".tmp-")
	if e != nil {
		return e
	}
	defer os.Remove(tmp.Name())
	if e = privateFile(tmp.Name()); e != nil {
		tmp.Close()
		return e
	}
	if e = replacementACL(tmp.Name(), false, true); e != nil {
		tmp.Close()
		return e
	}
	if _, e = tmp.Write(raw); e != nil {
		tmp.Close()
		return e
	}
	if e = tmp.Sync(); e != nil {
		tmp.Close()
		return e
	}
	if e = tmp.Close(); e != nil {
		return e
	}
	from, e := windows.UTF16PtrFromString(tmp.Name())
	if e != nil {
		return e
	}
	to, e := windows.UTF16PtrFromString(path)
	if e != nil {
		return e
	}
	if e = windows.MoveFileEx(from, to, windows.MOVEFILE_WRITE_THROUGH); e != nil {
		return e
	}
	got, e := replacementRead(path, 256<<10)
	if e != nil {
		return e
	}
	if !bytes.Equal(got, raw) {
		return errors.New("published bytes differ")
	}
	return nil
}

func replacementReadJournal(dir string, p replacementPlan, raw []byte) (replacementJournalView, error) {
	v := replacementJournalView{Files: map[string][]byte{}}
	if _, e := replacementIdentity(dir, true); e != nil {
		return v, e
	}
	if e := replacementACL(dir, true, true); e != nil {
		return v, e
	}
	guards, e := guardWriteDirectories(dir)
	if e != nil {
		return v, e
	}
	defer closeWriteGuards(guards)
	entries, e := os.ReadDir(dir)
	if e != nil {
		return v, e
	}
	if len(entries) > 12 {
		return v, errors.New("journal entry bound exceeded")
	}
	for _, entry := range entries {
		name := entry.Name()
		if entry.IsDir() {
			return v, errors.New("journal contains directory")
		}
		data, e := replacementRead(filepath.Join(dir, name), 256<<10)
		if e != nil {
			return v, e
		}
		v.Files[name] = data
		switch name {
		case "plan.json":
			if !bytes.Equal(data, raw) {
				return v, errors.New("same ID with different plan")
			}
		case "old-registration.bin":
			if !bytes.Equal(data, p.OldBytes) {
				return v, errors.New("old snapshot differs")
			}
		case "new-registration.bin", "stage.bin":
			if !bytes.Equal(data, p.NewBytes) {
				return v, errors.New("new snapshot differs")
			}
		case "actual-backup.bin": // Preserve third-party bytes; observation classifies them UNKNOWN.
		default:
			var event replacementEvent
			if decodeRuntimeManaged(data, &event) != nil || name != fmt.Sprintf("%04d-%s.json", len(v.Events)+1, strings.ToLower(event.State)) {
				return v, errors.New("unknown/orphan journal file")
			}
			want := event.Hash
			event.Hash = ""
			if want != domain.Hash(event) || event.Schema != replacementSchema || event.Sequence != len(v.Events)+1 || event.OperationID != p.OperationID || event.PlanSHA256 != domain.Digest(raw) || event.OldSHA256 != p.OldSHA256 || event.NewSHA256 != p.NewSHA256 {
				return v, errors.New("event linkage corrupt")
			}
			previous, state := "", ""
			if len(v.Events) > 0 {
				last := v.Events[len(v.Events)-1]
				previous, state = last.Hash, last.State
				// Audit clocks can change precision or move backwards. Sequence,
				// previous hash and transition are the only ordering authority.
			}
			if event.Previous != previous || !replacementTransition(state, event.State) {
				return v, errors.New("event chain invalid")
			}
			if _, e = time.Parse(time.RFC3339Nano, event.At); e != nil {
				return v, e
			}
			event.Hash = want
			v.Events = append(v.Events, event)
		}
	}
	if len(v.Events) > 0 {
		for _, name := range []string{"plan.json", "old-registration.bin", "new-registration.bin"} {
			if _, ok := v.Files[name]; !ok {
				return v, errors.New("journal snapshot missing")
			}
		}
	}
	return v, nil
}
func replacementTransition(old, new string) bool {
	switch old {
	case "":
		return new == "PREPARED" || new == "ABORTED"
	case "PREPARED":
		return new == "PUBLISHING" || new == "ABORTED"
	case "PUBLISHING":
		return new == "COMMITTED" || new == "ABORTED"
	}
	return false
}
func replacementAppend(dir string, p replacementPlan, raw []byte, state string) error {
	v, e := replacementReadJournal(dir, p, raw)
	if e != nil {
		return e
	}
	prior, last := "", ""
	if len(v.Events) > 0 {
		ev := v.Events[len(v.Events)-1]
		prior, last = ev.Hash, ev.State
	}
	if !replacementTransition(last, state) {
		return errors.New("invalid journal transition")
	}
	event := replacementEvent{Schema: replacementSchema, Sequence: len(v.Events) + 1, Previous: prior, OperationID: p.OperationID, PlanSHA256: domain.Digest(raw), OldSHA256: p.OldSHA256, NewSHA256: p.NewSHA256, State: state, At: time.Now().UTC().Format(time.RFC3339Nano)}
	event.Hash = domain.Hash(event)
	data, e := json.MarshalIndent(event, "", "  ")
	if e != nil {
		return e
	}
	if e = replacementWrite(dir, fmt.Sprintf("%04d-%s.json", event.Sequence, strings.ToLower(state)), data); e != nil {
		return e
	}
	_, e = replacementReadJournal(dir, p, raw)
	return e
}

func replacementApplied(p replacementPlan, dir string) error {
	backup, e := replacementRead(filepath.Join(dir, "actual-backup.bin"), 64<<10)
	if e != nil || !bytes.Equal(backup, p.OldBytes) {
		return errors.New("actual ReplaceFile backup differs: UNKNOWN")
	}
	current, e := replacementRead(filepath.Join(p.HostPath, "runtime-verifier-installation.json"), 64<<10)
	if e != nil || !bytes.Equal(current, p.NewBytes) {
		return errors.New("published registration differs: UNKNOWN")
	}
	if _, e = os.Lstat(filepath.Join(dir, "stage.bin")); !os.IsNotExist(e) {
		return errors.New("stage survived publication: UNKNOWN")
	}
	for _, path := range []string{filepath.Join(p.HostPath, "runtime-verifier-installation.json"), filepath.Join(dir, "actual-backup.bin")} {
		f, e := os.OpenFile(path, os.O_RDWR, 0)
		if e != nil {
			return e
		}
		e = f.Sync()
		ce := f.Close()
		if e != nil {
			return e
		}
		if ce != nil {
			return ce
		}
	}
	return nil
}
func replacementInstallationValid(p replacementPlan) error {
	raw, e := replacementRead(p.Manifest, 64<<10)
	if e != nil {
		return e
	}
	if domain.Digest(raw) != p.ManifestSHA256 {
		return errors.New("manifest changed")
	}
	install, e := LoadRuntimeVerifierInstallation(p.Manifest)
	if e != nil {
		return e
	}
	if domain.Hash(install) != p.NewInstallationHash {
		return errors.New("installation changed")
	}
	_, e = replacementRead(install.Executable, 128<<20)
	return e
}

func replacementRecover(in RuntimeVerifierReplacementInput, p replacementPlan, raw []byte) (RuntimeVerifierReplacementResult, error) {
	out := replacementResult(in.Action, p, domain.Digest(raw), "UNKNOWN", "UNKNOWN")
	dir := filepath.Join(p.HostPath, replacementJournal, p.OperationID)
	guards, e := guardWriteDirectories(dir)
	if e != nil {
		return out, e
	}
	defer closeWriteGuards(guards)
	v, e := replacementReadJournal(dir, p, raw)
	if e != nil {
		return out, e
	}
	head, e := replacementReadHistory(p.DataRoot, p.OperationID)
	if e != nil {
		return out, e
	}
	if !replacementExtendsHead(p, head) {
		return out, errors.New("recovery causal predecessor differs")
	}
	state := ""
	if len(v.Events) > 0 {
		state = v.Events[len(v.Events)-1].State
	}
	current, e := replacementRead(filepath.Join(p.HostPath, "runtime-verifier-installation.json"), 64<<10)
	if e != nil {
		return out, e
	}
	backup, published := v.Files["actual-backup.bin"]
	applied := bytes.Equal(current, p.NewBytes) && published && bytes.Equal(backup, p.OldBytes) && v.Files["stage.bin"] == nil
	unapplied := bytes.Equal(current, p.OldBytes) && !published
	if state == "COMMITTED" {
		if !applied {
			return out, errors.New("committed result drift")
		}
		if e = replacementInstallationValid(p); e != nil {
			return out, e
		}
		out.State, out.Outcome = "COMMITTED", "APPLIED"
		return out, nil
	}
	if state == "ABORTED" {
		if !unapplied {
			return out, errors.New("aborted result drift")
		}
		out.State, out.Outcome = "ABORTED", "NOT_APPLIED"
		return out, nil
	}
	if applied && state == "PUBLISHING" {
		if e = replacementInstallationValid(p); e != nil {
			return out, e
		}
		if in.RecoveryAction == "abort" {
			return out, errors.New("published operation cannot abort")
		}
		if in.RecoveryAction == "complete" {
			if e = replacementApplied(p, dir); e != nil {
				return out, e
			}
			if e = replacementAppend(dir, p, raw, "COMMITTED"); e != nil {
				return out, e
			}
			if e = replacementApplied(p, dir); e != nil {
				return out, e
			}
			if e = replacementCheckHistoryCurrent(p.DataRoot); e != nil {
				return out, e
			}
			out.State, out.Outcome = "COMMITTED", "APPLIED"
			return out, nil
		}
		out.State = "PUBLISHING"
		return out, nil
	}
	if !unapplied {
		return out, errors.New("replacement evidence ambiguous; no replay or rollback")
	}
	out.State, out.Outcome = "UNAPPLIED", "NOT_APPLIED"
	if in.RecoveryAction == "complete" {
		return out, errors.New("complete never replays ReplaceFile")
	}
	if in.RecoveryAction == "abort" {
		// Also provides recovery from death immediately after operation mkdir.
		for _, v := range []struct {
			name string
			data []byte
		}{{"plan.json", raw}, {"old-registration.bin", p.OldBytes}, {"new-registration.bin", p.NewBytes}} {
			if e = replacementWrite(dir, v.name, v.data); e != nil {
				return out, e
			}
		}
		if e = replacementAppend(dir, p, raw, "ABORTED"); e != nil {
			return out, e
		}
		if e = replacementCheckHistoryCurrent(p.DataRoot); e != nil {
			return out, e
		}
		out.State = "ABORTED"
	}
	return out, nil
}

func replacementValidateReverse(p replacementPlan) error {
	if !replacementID(p.RollbackOf) || p.RollbackOf == p.OperationID {
		return errors.New("invalid rollback reference")
	}
	dir := filepath.Join(p.HostPath, replacementJournal, p.RollbackOf)
	raw, e := replacementRead(filepath.Join(dir, "plan.json"), 256<<10)
	if e != nil {
		return e
	}
	var prior replacementPlan
	if decodeRuntimeManaged(raw, &prior) != nil || replacementPlanValid(prior) != nil {
		return errors.New("invalid reverse source plan")
	}
	v, e := replacementReadJournal(dir, prior, raw)
	if e != nil {
		return e
	}
	if len(v.Events) == 0 || v.Events[len(v.Events)-1].State != "COMMITTED" || p.OldSHA256 != prior.NewSHA256 || p.NewHash != prior.OldHash {
		return errors.New("rollback must reverse the committed current installation")
	}
	return nil
}

// RuntimeVerifierReplacementStartupGate is read-only and must run while the
// caller holds its existing lease, before store.Open or any migration.
func RuntimeVerifierReplacementStartupGate(lease *rt.DataRootLease) error {
	if lease == nil || !lease.Held() {
		return errors.New("replacement startup gate requires data-root lease")
	}
	return replacementCheckHistoryCurrent(lease.Root())
}
func replacementCheckHistoryCurrent(dataRoot string) error {
	head, e := replacementReadHistory(dataRoot, "")
	if e != nil {
		return e
	}
	if head.Sequence == 0 {
		return nil
	}
	raw, e := replacementRead(filepath.Join(dataRoot, "host", "runtime-verifier-installation.json"), 64<<10)
	if e != nil {
		return e
	}
	if domain.Digest(raw) != head.RecordSHA256 {
		return errors.New("latest replacement registration drift")
	}
	return nil
}

// Every new plan binds the previous immutable terminal, including ABORTED
// operations. No wall clock, directory enumeration order, or byte-hash cycle is
// used to infer causality. Unbound older draft plans remain intact and fail
// closed; this maintenance command does not silently rewrite/migrate history.
func replacementReadHistory(dataRoot, excludeOperation string) (head replacementHistoryHead, err error) {
	root := filepath.Join(dataRoot, "host", replacementJournal)
	if _, e := os.Lstat(root); os.IsNotExist(e) {
		return head, nil
	} else if e != nil {
		return head, e
	}
	if _, e := replacementIdentity(root, true); e != nil {
		return head, e
	}
	if e := replacementACL(root, true, true); e != nil {
		return head, e
	}
	guards, e := guardWriteDirectories(root)
	if e != nil {
		return head, e
	}
	defer closeWriteGuards(guards)
	entries, e := os.ReadDir(root)
	if e != nil {
		return head, e
	}
	type terminal struct {
		P          replacementPlan
		E          replacementEvent
		PlanSHA256 string
	}
	var all []terminal
	for _, entry := range entries {
		if !entry.IsDir() || !replacementID(entry.Name()) {
			return head, errors.New("replacement journal malformed; explicit recover required")
		}
		if entry.Name() == excludeOperation {
			continue
		}
		dir := filepath.Join(root, entry.Name())
		raw, e := replacementRead(filepath.Join(dir, "plan.json"), 256<<10)
		if e != nil {
			return head, fmt.Errorf("replacement unfinished; explicit recover required: %w", e)
		}
		var p replacementPlan
		if decodeRuntimeManaged(raw, &p) != nil || replacementPlanValid(p) != nil || p.OperationID != entry.Name() || p.DataRoot != dataRoot {
			return head, errors.New("replacement plan invalid; explicit recover required")
		}
		v, e := replacementReadJournal(dir, p, raw)
		if e != nil {
			return head, e
		}
		if len(v.Events) == 0 {
			return head, errors.New("replacement unfinished; explicit recover required")
		}
		last := v.Events[len(v.Events)-1]
		switch last.State {
		case "COMMITTED":
			if !bytes.Equal(v.Files["actual-backup.bin"], p.OldBytes) || v.Files["stage.bin"] != nil {
				return head, errors.New("committed backup/stage invalid")
			}
		case "ABORTED":
			if v.Files["actual-backup.bin"] != nil {
				return head, errors.New("aborted journal has publication evidence")
			}
		default:
			return head, errors.New("replacement unfinished; use --runtime-verifier-replacement recover")
		}
		all = append(all, terminal{p, last, domain.Digest(raw)})
	}
	if len(all) == 0 {
		return head, nil
	}
	sort.Slice(all, func(i, j int) bool { return all[i].P.HistorySequence < all[j].P.HistorySequence })
	for _, t := range all {
		if !replacementExtendsHead(t.P, head) {
			return head, errors.New("causal history fork, cycle, missing predecessor or digest drift")
		}
		record := t.P.OldSHA256
		if t.E.State == "COMMITTED" {
			record = t.P.NewSHA256
		}
		head = replacementHistoryHead{Sequence: t.P.HistorySequence, OperationID: t.P.OperationID, PlanSHA256: t.PlanSHA256, TerminalHash: t.E.Hash, RecordSHA256: record}
	}
	return head, nil
}
