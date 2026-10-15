//go:build windows

package ownedcorestop

import (
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
	"unsafe"

	"golang.org/x/sys/windows"
	"researchos.local/research-os/internal/store"
	"researchos.local/research-os/ops/supervisor"
)

type heldFile struct {
	file      *os.File
	ancestors []windows.Handle
	info      windows.ByHandleFileInformation
}

func (h *heldFile) Close() {
	if h == nil {
		return
	}
	if h.file != nil {
		_ = h.file.Close()
		h.file = nil
	}
	for i := len(h.ancestors) - 1; i >= 0; i-- {
		_ = windows.CloseHandle(h.ancestors[i])
	}
	h.ancestors = nil
}

func nativeFileIdentity(info windows.ByHandleFileInformation, path string) grantFileIdentity {
	return grantFileIdentity{Path: path, Volume: info.VolumeSerialNumber, Index: uint64(info.FileIndexHigh)<<32 | uint64(info.FileIndexLow)}
}

// Every component is opened without FILE_SHARE_DELETE and retained. The final
// file additionally denies write sharing; its bytes are read and decoded from
// this one handle while the handles remain live through the operation.
func openHeldFile(path string, directory bool) (out *heldFile, err error) {
	if err = cleanOwnedLocalPath(path); err != nil {
		return nil, err
	}
	out = &heldFile{}
	defer func() {
		if err != nil {
			out.Close()
			out = nil
		}
	}()
	volume := filepath.VolumeName(path)
	parts := strings.Split(strings.TrimPrefix(path[len(volume):], string(filepath.Separator)), string(filepath.Separator))
	current := volume + string(filepath.Separator)
	paths := []string{current}
	if path != current {
		for _, part := range parts {
			if part == "" || part == "." || part == ".." {
				return nil, errors.New("noncanonical path component")
			}
			current = filepath.Join(current, part)
			paths = append(paths, current)
		}
	}
	for i, p := range paths {
		last := i == len(paths)-1
		wide, e := windows.UTF16PtrFromString(p)
		if e != nil {
			err = e
			return
		}
		access := uint32(windows.FILE_READ_ATTRIBUTES | windows.READ_CONTROL)
		share := uint32(windows.FILE_SHARE_READ | windows.FILE_SHARE_WRITE)
		flags := uint32(windows.FILE_FLAG_OPEN_REPARSE_POINT | windows.FILE_FLAG_BACKUP_SEMANTICS)
		if last && !directory {
			access = windows.GENERIC_READ | windows.READ_CONTROL
			share = windows.FILE_SHARE_READ
		}
		if last && directory {
			share = windows.FILE_SHARE_READ
		}
		h, e := windows.CreateFile(wide, access, share, nil, windows.OPEN_EXISTING, flags, 0)
		if e != nil {
			err = e
			return
		}
		var info windows.ByHandleFileInformation
		if e = windows.GetFileInformationByHandle(h, &info); e != nil {
			_ = windows.CloseHandle(h)
			err = e
			return
		}
		expectDir := !last || directory
		if info.FileAttributes&windows.FILE_ATTRIBUTE_REPARSE_POINT != 0 || (info.FileAttributes&windows.FILE_ATTRIBUTE_DIRECTORY != 0) != expectDir || info.VolumeSerialNumber == 0 || uint64(info.FileIndexHigh)<<32|uint64(info.FileIndexLow) == 0 || (!expectDir && info.NumberOfLinks != 1) {
			_ = windows.CloseHandle(h)
			err = errors.New("reparse, alias, or native identity invalid")
			return
		}
		if last {
			sd, e := windows.GetSecurityInfo(h, windows.SE_FILE_OBJECT, windows.OWNER_SECURITY_INFORMATION)
			if e != nil {
				_ = windows.CloseHandle(h)
				err = e
				return
			}
			owner, _, e := sd.Owner()
			sid, se := currentSID()
			if e != nil || se != nil || owner == nil || owner.String() != sid.String() {
				_ = windows.CloseHandle(h)
				err = errors.New("file owner SID differs")
				return
			}
			out.file = os.NewFile(uintptr(h), p)
			out.info = info
		} else {
			out.ancestors = append(out.ancestors, h)
		}
	}
	return out, nil
}

func readHeldBytes(h *heldFile, max int) ([]byte, error) {
	if h == nil || h.file == nil || h.info.FileSizeHigh != 0 || h.info.FileSizeLow == 0 || h.info.FileSizeLow > uint32(max) {
		return nil, errors.New("bounded held file required")
	}
	raw, err := io.ReadAll(io.LimitReader(h.file, int64(max)+1))
	if err != nil || len(raw) != int(h.info.FileSizeLow) {
		return nil, errors.New("held file read changed")
	}
	var after windows.ByHandleFileInformation
	if err = windows.GetFileInformationByHandle(windows.Handle(h.file.Fd()), &after); err != nil || nativeFileIdentity(after, h.file.Name()) != nativeFileIdentity(h.info, h.file.Name()) || after.FileSizeHigh != h.info.FileSizeHigh || after.FileSizeLow != h.info.FileSizeLow || after.LastWriteTime != h.info.LastWriteTime {
		return nil, errors.New("held file identity/content changed")
	}
	return raw, nil
}

type heldDocuments struct{ files []*heldFile }

func (d *heldDocuments) Close() {
	for i := len(d.files) - 1; i >= 0; i-- {
		d.files[i].Close()
	}
	d.files = nil
}
func (d *heldDocuments) read(ref grantDocument, max int) ([]byte, error) {
	if !validGrantDocument(ref) {
		return nil, errors.New("invalid pinned document")
	}
	raw, err := d.readUnpinned(ref.Path, max)
	if err != nil {
		return nil, err
	}
	if digest(raw) != ref.SHA256 {
		return nil, errors.New("pinned document digest differs")
	}
	return raw, nil
}
func (d *heldDocuments) readUnpinned(path string, max int) ([]byte, error) {
	h, err := openHeldFile(path, false)
	if err != nil {
		return nil, err
	}
	d.files = append(d.files, h)
	raw, err := readHeldBytes(h, max)
	if err != nil {
		return nil, err
	}
	return raw, nil
}

type operationLock struct {
	dir  *heldFile
	file *os.File
}

func (l *operationLock) Close() {
	if l == nil {
		return
	}
	if l.file != nil {
		_ = l.file.Close()
	}
	if l.dir != nil {
		l.dir.Close()
	}
}

func acquireOperationLock(g operationGrant, create bool) (*operationLock, error) {
	if err := outsideDataRoot(g.OperationDir.Path, g.DataRoot.Path); err != nil {
		return nil, err
	}
	dir, err := openHeldFile(g.OperationDir.Path, true)
	if err != nil {
		return nil, err
	}
	if nativeFileIdentity(dir.info, g.OperationDir.Path) != g.OperationDir {
		dir.Close()
		return nil, errors.New("pinned operation directory identity differs")
	}
	if err = verifyOwnedPrivate(g.OperationDir.Path, true); err != nil {
		dir.Close()
		return nil, err
	}
	lockPath := filepath.Join(g.OperationDir.Path, ".operation.lock")
	wide, err := windows.UTF16PtrFromString(lockPath)
	if err != nil {
		dir.Close()
		return nil, err
	}
	mode := uint32(windows.OPEN_EXISTING)
	newLock := false
	if create {
		mode = windows.CREATE_NEW
	}
	h, err := windows.CreateFile(wide, windows.GENERIC_READ|windows.GENERIC_WRITE, 0, nil, mode, windows.FILE_FLAG_OPEN_REPARSE_POINT, 0)
	if create && (errors.Is(err, windows.ERROR_FILE_EXISTS) || errors.Is(err, windows.ERROR_ALREADY_EXISTS)) {
		h, err = windows.CreateFile(wide, windows.GENERIC_READ|windows.GENERIC_WRITE, 0, nil, windows.OPEN_EXISTING, windows.FILE_FLAG_OPEN_REPARSE_POINT, 0)
	} else if create && err == nil {
		newLock = true
	}
	if err != nil {
		dir.Close()
		return nil, fmt.Errorf("operation already locked or lock absent: %w", err)
	}
	l := &operationLock{dir: dir, file: os.NewFile(uintptr(h), lockPath)}
	var info windows.ByHandleFileInformation
	if err = windows.GetFileInformationByHandle(h, &info); err != nil || info.FileAttributes&(windows.FILE_ATTRIBUTE_REPARSE_POINT|windows.FILE_ATTRIBUTE_DIRECTORY) != 0 || info.NumberOfLinks != 1 {
		l.Close()
		return nil, errors.New("operation lock reparse/alias rejected")
	}
	if newLock {
		err = privateOwnedPath(lockPath, false)
	}
	if err != nil {
		l.Close()
		return nil, err
	}
	if err = verifyOwnedPrivate(lockPath, false); err != nil {
		l.Close()
		return nil, err
	}
	return l, nil
}

type ownedBeginRecord struct{ Schema, OperationID, PlanSHA256, GrantSHA256 string }
type preflightManifest struct {
	Schema               string            `json:"schema"`
	OperationID          string            `json:"operation_id"`
	GrantSHA256          string            `json:"grant_sha256"`
	ExecutableSHA256     string            `json:"executable_sha256"`
	InputSHA256          string            `json:"input_sha256"`
	PlanSHA256           string            `json:"plan_sha256"`
	BackupSHA256         string            `json:"backup_sha256"`
	BackupManifestSHA256 string            `json:"backup_manifest_sha256"`
	PlanFile             grantFileIdentity `json:"plan_file"`
	BackupFile           grantFileIdentity `json:"backup_file"`
}
type preflightComplete struct {
	Schema           string `json:"schema"`
	OperationID      string `json:"operation_id"`
	GrantSHA256      string `json:"grant_sha256"`
	ExecutableSHA256 string `json:"executable_sha256"`
	PlanSHA256       string `json:"plan_sha256"`
	ManifestSHA256   string `json:"manifest_sha256"`
}
type stopAttemptRecord struct {
	Schema      string `json:"schema"`
	OperationID string `json:"operation_id"`
	GrantSHA256 string `json:"grant_sha256"`
	PlanSHA256  string `json:"plan_sha256"`
}
type ownedIntentRecord struct {
	Schema, OperationID, PlanSHA256, GrantSHA256 string
	Native                                       supervisor.OwnedCoreNativeIdentity `json:"native"`
}
type ownedExitRecord struct {
	Schema, OperationID, PlanSHA256, GrantSHA256 string
	Native                                       supervisor.OwnedCoreNativeExit `json:"native"`
}

func readOwnedExit(out, operationID, planSHA string, grantSHA ...string) (supervisor.OwnedCoreNativeExit, error) {
	raw, err := readOwnedJournal(out, "NATIVE_EXIT.json", 64<<10)
	if err != nil {
		return supervisor.OwnedCoreNativeExit{}, err
	}
	var record ownedExitRecord
	if err = strictJSON(raw, &record); err != nil {
		return supervisor.OwnedCoreNativeExit{}, err
	}
	if record.Schema != "researchos.owned-core-stop-native-exit.v1" || record.OperationID != operationID || record.PlanSHA256 != planSHA || !record.Native.ExitObserved || (record.Native.TerminateCalls != 1 && !record.Native.BeforeSignal) {
		return supervisor.OwnedCoreNativeExit{}, errors.New("native exit journal binding/observation missing")
	}
	if len(grantSHA) > 0 && record.GrantSHA256 != grantSHA[0] {
		return supervisor.OwnedCoreNativeExit{}, errors.New("native exit grant differs")
	}
	return record.Native, nil
}

func currentExecutableSHA256() (string, error) {
	path, err := os.Executable()
	if err != nil {
		return "", err
	}
	h, err := openHeldFile(path, false)
	if err != nil {
		return "", err
	}
	defer h.Close()
	if h.info.FileSizeHigh != 0 || h.info.FileSizeLow == 0 || h.info.FileSizeLow > 256<<20 {
		return "", errors.New("bounded executable required")
	}
	stream := sha256.New()
	n, err := io.Copy(stream, io.LimitReader(h.file, 256<<20+1))
	if err != nil || n != int64(h.info.FileSizeLow) {
		return "", errors.New("executable read differs")
	}
	return hex.EncodeToString(stream.Sum(nil)), nil
}

func readPinnedPlan(d *heldDocuments, g operationGrant) (Plan, string, error) {
	var p Plan
	path := filepath.Join(g.OperationDir.Path, "plan.json")
	raw, err := d.read(grantDocument{Path: path, SHA256: g.PlanSHA256}, 256<<10)
	if err != nil {
		return p, "", err
	}
	if err = decodeCanonicalAuthority(raw, &p); err != nil {
		return p, "", err
	}
	canonical, err := canonicalJSON(p)
	if err != nil || string(canonical) != string(raw) {
		return p, "", errors.New("plan serialization differs")
	}
	if err = validatePlan(p); err != nil {
		return p, "", err
	}
	if p.OutputDir != g.OperationDir.Path || p.OperationID != g.OperationID || p.Native != mustObservedNative(g) || p.Host != g.Host || p.Input.Subject != g.Subject || p.Input.DataRoot != g.DataRoot.Path {
		return p, "", errors.New("pinned plan subject/authority differs")
	}
	return p, digest(raw), nil
}

func mustObservedNative(g operationGrant) supervisor.OwnedCoreNativeIdentity {
	n, _ := g.Native.observed()
	return n
}

func readPreflightComplete(d *heldDocuments, g operationGrant) (preflightComplete, preflightManifest, error) {
	var c preflightComplete
	var m preflightManifest
	raw, err := d.readUnpinned(filepath.Join(g.OperationDir.Path, "PREFLIGHT_COMPLETE.json"), 64<<10)
	if err != nil {
		return c, m, err
	}
	if err = decodeCanonicalAuthority(raw, &c); err != nil {
		return c, m, err
	}
	if c.Schema != "researchos.owned-core-stop-preflight-complete.v1" || c.OperationID != g.OperationID || !validSHA(c.GrantSHA256) || !validSHA(c.ExecutableSHA256) || !validSHA(c.PlanSHA256) || !validSHA(c.ManifestSHA256) {
		return c, m, errors.New("preflight complete binding")
	}
	if g.GrantKind == "STOP_ONCE" && (c.GrantSHA256 != g.PreflightGrantSHA256 || c.ExecutableSHA256 != g.PreflightExecutableSHA256 || c.PlanSHA256 != g.PlanSHA256 || c.ManifestSHA256 != g.PreflightManifestSHA256) {
		return c, m, errors.New("predecessor grant/manifest differs")
	}
	if g.GrantKind == "PREFLIGHT_ONLY" && c.GrantSHA256 != g.digest {
		return c, m, errors.New("preflight grant digest differs")
	}
	manifestRaw, err := d.read(grantDocument{Path: filepath.Join(g.OperationDir.Path, "preflight-manifest.json"), SHA256: c.ManifestSHA256}, 128<<10)
	if err != nil {
		return c, m, err
	}
	if err = decodeCanonicalAuthority(manifestRaw, &m); err != nil {
		return c, m, err
	}
	if m.Schema != "researchos.owned-core-stop-preflight-manifest.v1" || m.OperationID != g.OperationID || m.GrantSHA256 != c.GrantSHA256 || m.ExecutableSHA256 != c.ExecutableSHA256 || m.PlanSHA256 != c.PlanSHA256 || !validSHA(m.BackupSHA256) || !validSHA(m.BackupManifestSHA256) {
		return c, m, errors.New("preflight manifest binding")
	}
	return c, m, nil
}

func validatePreflightOutputs(d *heldDocuments, g operationGrant, c preflightComplete, m preflightManifest, p Plan) error {
	if p.GrantSHA256 != c.GrantSHA256 || p.PreflightExecutableSHA256 != c.ExecutableSHA256 || p.InputSHA256 != m.InputSHA256 || p.BackupSHA256 != m.BackupSHA256 || p.BackupPath != m.BackupFile.Path || filepath.Join(g.OperationDir.Path, "plan.json") != m.PlanFile.Path {
		return errors.New("preflight plan/manifest links differ")
	}
	for _, item := range []grantFileIdentity{m.PlanFile, m.BackupFile} {
		h, err := openHeldFile(item.Path, false)
		if err != nil {
			return err
		}
		d.files = append(d.files, h)
		if nativeFileIdentity(h.info, item.Path) != item {
			return errors.New("preflight output native identity differs")
		}
	}
	raw, err := d.read(grantDocument{Path: filepath.Join(g.OperationDir.Path, "backup-manifest.json"), SHA256: m.BackupManifestSHA256}, 128<<10)
	if err != nil {
		return err
	}
	var backup struct {
		Schema, OperationID, BackupSHA256 string
		Census                            store.OwnedStopCensus `json:"census"`
	}
	if err = decodeCanonicalAuthority(raw, &backup); err != nil {
		return err
	}
	if backup.Schema != "researchos.owned-core-stop-backup.v1" || backup.OperationID != g.OperationID || backup.BackupSHA256 != p.BackupSHA256 || backup.Census != p.Baseline {
		return errors.New("backup manifest differs")
	}
	return nil
}

func readExistingStopOutcome(d *heldDocuments, g operationGrant, p Plan, planSHA string) (Result, error) {
	unknown := Result{Schema: ResultSchema, OperationID: g.OperationID, PlanSHA256: planSHA, StopGrantSHA256: g.digest, State: "UNKNOWN", Reason: "consumed attempt without immutable outcome; no retry"}
	raw, err := d.readUnpinned(filepath.Join(g.OperationDir.Path, "STOP_ATTEMPT.json"), 64<<10)
	if err != nil {
		return unknown, err
	}
	var attempt stopAttemptRecord
	if err = decodeCanonicalAuthority(raw, &attempt); err != nil {
		return unknown, err
	}
	if attempt.Schema != "researchos.owned-core-stop-attempt.v1" || attempt.OperationID != g.OperationID || attempt.GrantSHA256 != g.digest || attempt.PlanSHA256 != planSHA {
		return unknown, errors.New("STOP attempt grant conflict")
	}
	terminalPath := filepath.Join(g.OperationDir.Path, "POSTFLIGHT.json")
	if _, err = os.Stat(terminalPath); errors.Is(err, os.ErrNotExist) {
		return unknown, nil
	} else if err != nil {
		return unknown, err
	}
	raw, err = d.readUnpinned(terminalPath, 64<<10)
	if err != nil {
		return unknown, err
	}
	var terminal Result
	if err = decodeCanonicalAuthority(raw, &terminal); err != nil {
		return unknown, err
	}
	if terminal.Schema != ResultSchema || terminal.OperationID != g.OperationID || terminal.PlanSHA256 != planSHA || terminal.StopGrantSHA256 != g.digest {
		return unknown, errors.New("terminal outcome grant binding differs")
	}
	if terminal.State == "STOPPED_LEASE_VERIFIED" || terminal.State == "STOP_OBSERVED_MAINTENANCE_BLOCKED" || terminal.State == "OBSERVED_BEFORE_SIGNAL" {
		beginRaw, e := d.readUnpinned(filepath.Join(g.OperationDir.Path, "BEGIN.json"), 64<<10)
		if e != nil {
			return unknown, e
		}
		var begin ownedBeginRecord
		if e = strictJSON(beginRaw, &begin); e != nil {
			return unknown, e
		}
		if begin.Schema != "researchos.owned-core-stop-begin.v1" || begin.OperationID != g.OperationID || begin.PlanSHA256 != planSHA || begin.GrantSHA256 != g.digest {
			return unknown, errors.New("BEGIN journal binding differs")
		}
		intentRaw, e := d.readUnpinned(filepath.Join(g.OperationDir.Path, "TERMINATE_INTENT.json"), 64<<10)
		if e != nil {
			return unknown, e
		}
		var intent ownedIntentRecord
		if e = strictJSON(intentRaw, &intent); e != nil {
			return unknown, e
		}
		if intent.Schema != "researchos.owned-core-stop-terminate-intent.v1" || intent.OperationID != g.OperationID || intent.PlanSHA256 != planSHA || intent.GrantSHA256 != g.digest || intent.Native != p.Native {
			return unknown, errors.New("intent journal binding differs")
		}
		exitRaw, e := d.readUnpinned(filepath.Join(g.OperationDir.Path, "NATIVE_EXIT.json"), 64<<10)
		if e != nil {
			return unknown, e
		}
		var native ownedExitRecord
		if e = decodeCanonicalAuthority(exitRaw, &native); e != nil {
			return unknown, e
		}
		if native.Schema != "researchos.owned-core-stop-native-exit.v1" || native.OperationID != g.OperationID || native.PlanSHA256 != planSHA || native.GrantSHA256 != g.digest || !native.Native.ExitObserved || terminal.Native == nil || *terminal.Native != native.Native {
			return unknown, errors.New("native closure outcome differs")
		}
		if terminal.State == "STOPPED_LEASE_VERIFIED" && (terminal.Postflight == nil || *terminal.Postflight != p.Baseline || native.Native.TerminateCalls != 1 || native.Native.BeforeSignal) {
			return unknown, errors.New("verified terminal lacks exact postflight/one call")
		}
	}
	return terminal, nil
}

func currentSID() (*windows.SID, error) {
	u, err := windows.GetCurrentProcessToken().GetTokenUser()
	if err != nil {
		return nil, err
	}
	if u.User.Sid == nil || !u.User.Sid.IsValid() {
		return nil, errors.New("current SID unavailable")
	}
	return u.User.Sid, nil
}

func privateOwnedPath(path string, dir bool) error {
	sid, err := currentSID()
	if err != nil {
		return err
	}
	ace := "(A;;FA;;;" + sid.String() + ")"
	if dir {
		ace = "(A;OICI;FA;;;" + sid.String() + ")"
	}
	sd, err := windows.SecurityDescriptorFromString("O:" + sid.String() + "D:P" + ace)
	if err != nil {
		return err
	}
	acl, _, err := sd.DACL()
	if err != nil {
		return err
	}
	return windows.SetNamedSecurityInfo(path, windows.SE_FILE_OBJECT, windows.DACL_SECURITY_INFORMATION|windows.PROTECTED_DACL_SECURITY_INFORMATION, nil, nil, acl, nil)
}

func verifyOwnedPrivate(path string, dir bool) error {
	sid, err := currentSID()
	if err != nil {
		return err
	}
	sd, err := windows.GetNamedSecurityInfo(path, windows.SE_FILE_OBJECT, windows.OWNER_SECURITY_INFORMATION|windows.DACL_SECURITY_INFORMATION)
	if err != nil {
		return err
	}
	owner, _, err := sd.Owner()
	if err != nil || owner == nil || owner.String() != sid.String() {
		return errors.New("private path owner SID differs")
	}
	control, _, err := sd.Control()
	if err != nil || control&windows.SE_DACL_PROTECTED == 0 {
		return errors.New("protected private DACL missing")
	}
	acl, _, err := sd.DACL()
	if err != nil || acl == nil || acl.AceCount != 1 {
		return errors.New("single private ACE required")
	}
	var ace *windows.ACCESS_ALLOWED_ACE
	if err = windows.GetAce(acl, 0, &ace); err != nil {
		return err
	}
	flags := byte(0)
	if dir {
		flags = windows.OBJECT_INHERIT_ACE | windows.CONTAINER_INHERIT_ACE
	}
	if ace.Header.AceType != windows.ACCESS_ALLOWED_ACE_TYPE || ace.Header.AceFlags != flags || ace.Mask != 0x001f01ff || (*windows.SID)(unsafe.Pointer(&ace.SidStart)).String() != sid.String() {
		return errors.New("private ACE differs")
	}
	return nil
}

func cleanOwnedLocalPath(path string) error {
	if !filepath.IsAbs(path) || filepath.Clean(path) != path || len(filepath.VolumeName(path)) != 2 || strings.Contains(path[2:], ":") {
		return errors.New("canonical local path required")
	}
	return nil
}

func outsideDataRoot(out, dataRoot string) error {
	if err := cleanOwnedLocalPath(out); err != nil {
		return err
	}
	if err := cleanOwnedLocalPath(dataRoot); err != nil {
		return err
	}
	rel, err := filepath.Rel(dataRoot, out)
	if err != nil || rel == "." || (!strings.HasPrefix(rel, ".."+string(filepath.Separator)) && rel != "..") {
		return errors.New("output must be outside product data root")
	}
	return nil
}

func createPrivateOutput(out, dataRoot string) error {
	if err := outsideDataRoot(out, dataRoot); err != nil {
		return err
	}
	parent := filepath.Dir(out)
	actual, err := filepath.EvalSymlinks(parent)
	if err != nil || !strings.EqualFold(actual, parent) {
		return errors.New("output parent reparse or absence")
	}
	if err = os.Mkdir(out, 0700); err != nil {
		return err
	}
	if err = privateOwnedPath(out, true); err != nil {
		return err
	}
	return verifyOwnedPrivate(out, true)
}

func writeOwnedJournal(out, name string, body any) (string, error) {
	if filepath.Base(name) != name || strings.ContainsAny(name, "/\\:") {
		return "", errors.New("fixed journal filename required")
	}
	if err := verifyOwnedPrivate(out, true); err != nil {
		return "", err
	}
	raw, err := canonicalJSON(body)
	if err != nil {
		return "", err
	}
	path := filepath.Join(out, name)
	f, err := os.OpenFile(path, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if err != nil {
		return "", err
	}
	defer f.Close()
	if err = privateOwnedPath(path, false); err != nil {
		return "", err
	}
	if err = verifyOwnedPrivate(path, false); err != nil {
		return "", err
	}
	if _, err = f.Write(raw); err != nil {
		return "", err
	}
	if err = f.Sync(); err != nil {
		return "", err
	}
	return digest(raw), nil
}

func readOwnedJournal(out, name string, max int) ([]byte, error) {
	if err := verifyOwnedPrivate(out, true); err != nil {
		return nil, err
	}
	path := filepath.Join(out, name)
	actual, err := filepath.EvalSymlinks(path)
	if err != nil || !strings.EqualFold(actual, path) {
		return nil, errors.New("journal reparse or absence")
	}
	if err := verifyOwnedPrivate(path, false); err != nil {
		return nil, err
	}
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	if len(raw) == 0 || len(raw) > max {
		return nil, fmt.Errorf("bounded %s required", name)
	}
	return raw, nil
}

func readPlan(path string) (Plan, string, error) {
	var plan Plan
	if filepath.Base(path) != "plan.json" {
		return plan, "", errors.New("canonical plan.json required")
	}
	raw, err := readOwnedJournal(filepath.Dir(path), "plan.json", 256<<10)
	if err != nil {
		return plan, "", err
	}
	if err = strictJSON(raw, &plan); err != nil {
		return plan, "", err
	}
	if err = validatePlan(plan); err != nil {
		return plan, "", err
	}
	if plan.OutputDir != filepath.Dir(path) {
		return plan, "", errors.New("plan directory changed")
	}
	canonical, err := canonicalJSON(plan)
	if err != nil || string(canonical) != string(raw) {
		return plan, "", errors.New("plan serialization differs")
	}
	return plan, digest(raw), nil
}

// Inspect is observation-only. It never opens a termination handle or repairs
// a missing native wait. Completed POSTFLIGHT is returned unchanged.
func Inspect(planPath string) (Result, error) {
	g, err := loadCompiledOperationGrant()
	if err != nil {
		return Result{}, err
	}
	if _, err = g.checkAction("inspect", false); err != nil {
		return Result{}, err
	}
	if planPath != filepath.Join(g.OperationDir.Path, "plan.json") {
		return Result{}, errors.New("inspect plan differs from compiled grant")
	}
	lock, err := acquireOperationLock(g, false)
	if err != nil {
		return Result{Schema: ResultSchema, OperationID: g.OperationID, State: "IN_PROGRESS", Reason: "operation writer active or immutable lock absent"}, nil
	}
	defer lock.Close()
	docs := &heldDocuments{}
	defer docs.Close()
	c, m, err := readPreflightComplete(docs, g)
	if err != nil {
		return Result{Schema: ResultSchema, OperationID: g.OperationID, State: "STOP_UNAVAILABLE", Reason: "immutable preflight completion absent"}, nil
	}
	planGrant := g
	planGrant.PlanSHA256 = c.PlanSHA256
	p, sha, err := readPinnedPlan(docs, planGrant)
	if err != nil {
		return Result{}, err
	}
	if err = validatePreflightOutputs(docs, g, c, m, p); err != nil {
		return Result{}, err
	}
	if g.GrantKind == "PREFLIGHT_ONLY" {
		return Result{Schema: ResultSchema, OperationID: g.OperationID, PlanSHA256: sha, State: "PREFLIGHT_COMPLETE"}, nil
	}
	if _, err = os.Stat(filepath.Join(g.OperationDir.Path, "STOP_ATTEMPT.json")); errors.Is(err, os.ErrNotExist) {
		return Result{Schema: ResultSchema, OperationID: g.OperationID, PlanSHA256: sha, State: "STOP_UNAVAILABLE", Reason: "no STOP attempt"}, nil
	} else if err != nil {
		return Result{}, err
	}
	return readExistingStopOutcome(docs, g, p, sha)
}
