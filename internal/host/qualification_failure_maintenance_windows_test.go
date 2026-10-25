//go:build windows

package host

import (
	"context"
	"crypto/sha256"
	"database/sql"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
	"unsafe"

	"golang.org/x/sys/windows"
	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/qualificationmaintenancejournal"
)

func TestQualificationJournalFullPlanDispatchRowRoundTrip(t *testing.T) {
	root := t.TempDir()
	user, err := windows.GetCurrentProcessToken().GetTokenUser()
	if err != nil {
		t.Fatal(err)
	}
	sid := user.User.Sid.String()
	sd, err := windows.SecurityDescriptorFromString("O:" + sid + "D:P(A;OICI;FA;;;" + sid + ")")
	if err != nil {
		t.Fatal(err)
	}
	hostPath, err := windows.UTF16PtrFromString(filepath.Join(root, "host"))
	if err != nil {
		t.Fatal(err)
	}
	sa := windows.SecurityAttributes{Length: uint32(unsafe.Sizeof(windows.SecurityAttributes{})), SecurityDescriptor: sd}
	if err = windows.CreateDirectory(hostPath, &sa); err != nil {
		t.Fatal(err)
	}
	plan := domain.HistoricalQualificationPlan{
		Schema:      "researchos.qualification-failure-maintenance-full-plan.v1",
		OperationID: "00112233445566778899aabbccddeeff", DataRoot: root,
		Database: filepath.Join(root, "researchos.sqlite"),
		Core:     domain.Object{"schema": "fixture"}, Proof: domain.Object{
			"native": domain.Object{"kind": "fixture"}, "model_binding": domain.Object{"kind": "fixture"}},
		ProofBytes: []byte("fixture"), OutcomeHash: domain.Digest([]byte("outcome")),
		Subject:   domain.HistoricalQualificationSubject{ProjectID: "project", RunID: "run", Epoch: 1, DispatchKey: "dispatch"},
		BeforeRun: domain.Object{}, BeforeState: domain.Object{}, BeforeDispatch: domain.Object{"state": "STARTED"},
		BeforeProtectedSHA256: domain.Digest([]byte("protected")), BeforeResidualSHA256: domain.Digest([]byte("residual")),
		Artifact: domain.Object{}, ImpactLink: domain.Object{}, Run: domain.Object{}, ProjectState: domain.Object{},
		Event: domain.Object{}, Observation: domain.Object{}, DispatchSequence: 1,
	}
	// Populate the private typed dispatch row through its public JSON contract,
	// as the Host does when reading a reviewed plan from disk.
	initial, err := json.Marshal(plan)
	if err != nil {
		t.Fatal(err)
	}
	var tree map[string]any
	if err = json.Unmarshal(initial, &tree); err != nil {
		t.Fatal(err)
	}
	row := tree["before_dispatch_row"].(map[string]any)
	row["project"], row["run"], row["epoch"], row["dispatch_key"] = "project", "run", float64(1), "dispatch"
	row["worker"] = "fixture-worker"
	cells := row["cells"].([]any)
	cells[7] = map[string]any{"type": "text", "data": base64.StdEncoding.EncodeToString([]byte("fixture-worker"))}
	serialized, err := json.Marshal(tree)
	if err != nil {
		t.Fatal(err)
	}
	if err = json.Unmarshal(serialized, &plan); err != nil {
		t.Fatal(err)
	}
	fullPlanRaw, err := json.Marshal(plan)
	if err != nil {
		t.Fatal(err)
	}
	var reviewed domain.HistoricalQualificationPlan
	if err = json.Unmarshal(fullPlanRaw, &reviewed); err != nil {
		t.Fatal(err)
	}
	journalRaw, err := qualificationJournalRaw(reviewed, fullPlanRaw)
	if err != nil {
		t.Fatal(err)
	}
	digest, err := qualificationmaintenancejournal.StartQualification(root, journalRaw)
	if err != nil {
		t.Fatal(err)
	}
	_, status, err := qualificationmaintenancejournal.OpenOwnInspection(root,
		qualificationmaintenancejournal.QualificationNamespace, plan.OperationID, digest)
	if err != nil || status.State != "BEGIN" {
		t.Fatalf("typed full plan journal readback: %#v %v", status, err)
	}
}

func TestQualificationMaintenanceFrozenSubjectAndExternalPlan(t *testing.T) {
	s := domain.HistoricalQualificationSubject{
		ProjectID: "a7ebcf2a322c6abcf87e043f601ee804",
		TaskID:    "0469d97b91b04fd7fdeed77770ea1bed",
		RunID:     "f3dcb996b2e43cf52cba874be7abfc70",
		RuntimeID: "db26746ff0420ca156d315f0de00fb53",
		Epoch:     1, DispatchKey: "705b11ec99044fef19e85f57e2d2b712",
	}
	if !qualificationExactSubject(s) {
		t.Fatal("frozen subject rejected")
	}
	s.DispatchKey = "other"
	if qualificationExactSubject(s) {
		t.Fatal("changed dispatch admitted")
	}
	root := t.TempDir()
	outside := t.TempDir()
	if err := qualificationExternalPath(root, filepath.Join(outside, "plan.json")); err != nil {
		t.Fatal(err)
	}
	if err := qualificationExternalPath(root, filepath.Join(root, "plan.json")); err == nil {
		t.Fatal("plan in data root admitted")
	}
	alias := filepath.Join(outside, "alias")
	if err := os.Symlink(root, alias); err == nil {
		if err := qualificationExternalPath(root, filepath.Join(alias, "plan.json")); err == nil {
			t.Fatal("parent alias into data root admitted")
		}
	}
	if _, err := RunQualificationFailureMaintenance(context.Background(), QualificationMaintenanceInput{
		Action: "preflight", DataRoot: filepath.Join(root, "missing")}); err == nil {
		t.Fatal("empty proposal admitted")
	}
}

func TestQualificationBusinessIdentityHeldWithoutProcessOwnerImpersonation(t *testing.T) {
	root := t.TempDir()
	if e := os.Mkdir(filepath.Join(root, "host"), 0700); e != nil {
		t.Fatal(e)
	}
	state := hostState{Version: 1, PrincipalID: "business-owner", PrincipalRef: "principal-ref", HostInstanceID: "host-id"}
	raw, e := json.Marshal(state)
	if e != nil {
		t.Fatal(e)
	}
	path := filepath.Join(root, "host", stateFile)
	if e = os.WriteFile(path, raw, 0600); e != nil {
		t.Fatal(e)
	}
	user, e := windows.GetCurrentProcessToken().GetTokenUser()
	if e != nil || user == nil || user.User.Sid == nil {
		t.Fatalf("current SID: %v", e)
	}
	digest := sha256.Sum256(raw)
	hold, e := openQualificationBusinessIdentity(root, user.User.Sid.String(), hex.EncodeToString(digest[:]))
	if e != nil {
		t.Fatal(e)
	}
	db, e := sql.Open("sqlite", filepath.Join(root, "identity.sqlite"))
	if e != nil {
		t.Fatal(e)
	}
	defer db.Close()
	if _, e = db.Exec(`CREATE TABLE auth_principals(id TEXT PRIMARY KEY,roles TEXT NOT NULL,revoked INTEGER NOT NULL);
		CREATE TABLE orchestration_identity(principal TEXT PRIMARY KEY,root TEXT NOT NULL);
		INSERT INTO auth_principals VALUES('business-owner','["OWNER"]',0);
		INSERT INTO orchestration_identity VALUES('business-owner','owner-root');`); e != nil {
		t.Fatal(e)
	}
	ownerRoot, e := hold.ValidateOwner(context.Background(), db)
	if e != nil || ownerRoot != "owner-root" {
		t.Fatalf("business Owner read: %s %v", ownerRoot, e)
	}
	if e = os.Rename(path, path+".moved"); e == nil {
		t.Fatal("business identity file renamed while held")
	}
	if e = hold.Check(); e != nil {
		t.Fatal(e)
	}
	if e = hold.Close(); e != nil {
		t.Fatal(e)
	}
	if e = os.Rename(path, path+".moved"); e != nil {
		t.Fatalf("business identity handle remained open: %v", e)
	}
	if e = hold.Check(); e == nil {
		t.Fatal("closed business identity hold accepted")
	}
}
