//go:build windows

package ownedcorestop

import (
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"unsafe"

	"golang.org/x/sys/windows"
	"researchos.local/research-os/ops/supervisor"
)

type ownedBeginRecord struct{ Schema, OperationID, PlanSHA256 string }
type ownedIntentRecord struct {
	Schema, OperationID, PlanSHA256 string
	Native                          supervisor.OwnedCoreNativeIdentity `json:"native"`
}
type ownedExitRecord struct {
	Schema, OperationID, PlanSHA256 string
	Native                          supervisor.OwnedCoreNativeExit `json:"native"`
}

func readOwnedExit(out, operationID, planSHA string) (supervisor.OwnedCoreNativeExit, error) {
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
	return record.Native, nil
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
	plan, planSHA, err := readPlan(planPath)
	if err != nil {
		return Result{}, err
	}
	out := Result{Schema: ResultSchema, OperationID: plan.OperationID, PlanSHA256: planSHA, State: "UNKNOWN", Reason: "incomplete journal; no automatic retry"}
	if _, e := os.Lstat(filepath.Join(plan.OutputDir, "POSTFLIGHT.json")); e == nil {
		raw, e := readOwnedJournal(plan.OutputDir, "POSTFLIGHT.json", 64<<10)
		if e != nil {
			return out, e
		}
		var terminal Result
		if err = strictJSON(raw, &terminal); err != nil {
			return out, err
		}
		if terminal.Schema != ResultSchema || terminal.OperationID != plan.OperationID || terminal.PlanSHA256 != planSHA {
			return out, errors.New("terminal receipt binding differs")
		}
		if terminal.State == "STOPPED_LEASE_VERIFIED" || terminal.State == "STOP_OBSERVED_MAINTENANCE_BLOCKED" || terminal.State == "OBSERVED_BEFORE_SIGNAL" {
			native, e := readOwnedExit(plan.OutputDir, plan.OperationID, planSHA)
			if e != nil || terminal.Native == nil || *terminal.Native != native {
				return out, errors.New("terminal native exit proof absent or differs")
			}
		}
		return terminal, nil
	}
	if _, e := os.Lstat(filepath.Join(plan.OutputDir, "NATIVE_EXIT.json")); e == nil {
		if _, e = readOwnedExit(plan.OutputDir, plan.OperationID, planSHA); e != nil {
			return out, e
		}
		out.State = "STOP_OBSERVED_MAINTENANCE_BLOCKED"
		out.Reason = "native exit recorded; postflight absent"
		return out, nil
	}
	if _, e := os.Lstat(filepath.Join(plan.OutputDir, "TERMINATE_INTENT.json")); e == nil {
		raw, e := readOwnedJournal(plan.OutputDir, "TERMINATE_INTENT.json", 64<<10)
		if e != nil {
			return out, e
		}
		var intent ownedIntentRecord
		if e = strictJSON(raw, &intent); e != nil {
			return out, e
		}
		if intent.Schema != "researchos.owned-core-stop-terminate-intent.v1" || intent.OperationID != plan.OperationID || intent.PlanSHA256 != planSHA || intent.Native != plan.Native {
			return out, errors.New("termination intent journal binding differs")
		}
		out.Reason = "termination intent exists without retained native wait receipt"
		return out, nil
	}
	return out, nil
}
