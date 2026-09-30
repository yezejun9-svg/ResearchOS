//go:build windows

package domain

import (
	"context"
	"crypto/rand"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"researchos.local/research-os/ops/supervisor"
	"strings"
	"time"
)

const releaseFixtureMechanism = "R2_NATIVE_FIXTURE"

func releasePlainDigest(v any) string { return supervisor.ReleaseDigest(v) }
func releaseArtifactDigest(v any) string { return strings.TrimPrefix(fmt.Sprint(v), "sha256:") }

func releaseStateRoot(h Object) string { return filepath.Join(Str(h,"root"),"release-state") }
func releaseAdmissionPath(h Object, operation string) string { return filepath.Join(releaseStateRoot(h),"admissions",operation+".json") }
func releaseBackupPath(h Object, operation string) string { return filepath.Join(releaseStateRoot(h),"backups",operation) }
func releaseKeyPath(h Object, operation string) string { return filepath.Join(releaseStateRoot(h),"backups",operation+".key") }
func releaseReceiptPath(h Object, operation string) string { return filepath.Join(releaseStateRoot(h),"receipts",operation+".json") }

func releaseFixtureDriver() supervisor.NativeFixtureDriver {
	return supervisor.NativeFixtureDriver{Args:func(token,data string) []string {return []string{"--release-fixture",token,data}}}
}

// The native fixture can only assert an idle test database, not production
// drain/checkpoint or service ACL isolation. The independent production barrier
// must replace this adapter before any LIVE release is permitted.
type releaseFixtureBarrier struct { s *Service; h Object; driver supervisor.ProcessDriver }
func (b releaseFixtureBarrier) Ready(_ context.Context,p supervisor.ProcessIdentity,_ string) error {
	alive,e:=b.driver.Alive(p);if e!=nil {return e};if !alive {return errors.New("fixture process not alive")};return nil
}
func (b releaseFixtureBarrier) Drain(ctx context.Context,p supervisor.ProcessIdentity,operation string) (string,error) {
	if e:=b.Ready(ctx,p,operation);e!=nil {return "",e}
	var active,unknown int
	if e:=b.s.DB.QueryRowContext(ctx,`SELECT count(*) FROM domain_objects WHERE kind='Run' AND json_extract(body,'$.status') IN ('QUEUED','STARTING','RUNNING','CANCEL_REQUESTED','RECONCILING','LOST')`).Scan(&active);e!=nil {return "",e}
	if e:=b.s.DB.QueryRowContext(ctx,`SELECT count(*) FROM resource_effects x WHERE sequence=(SELECT max(y.sequence) FROM resource_effects y WHERE y.project=x.project AND y.run=x.run AND y.effect_key=x.effect_key) AND json_extract(body,'$.state') IN ('PREPARED','STARTED','UNKNOWN')`).Scan(&unknown);e!=nil {return "",e}
	if active!=0 || unknown!=0 {return "",errors.New("fixture has active Run or unresolved external effect")}
	return releasePlainDigest(Object{"fixture_idle_observation":true,"operation":operation,"pid":p.PID,"created_ns":p.CreatedNS}),nil
}
func (b releaseFixtureBarrier) Compatible(_ context.Context,state supervisor.ReleaseState) error {
	key,e:=os.ReadFile(releaseKeyPath(b.h,state.Operation));if e!=nil {return e};defer clear(key)
	m,_,e:=readBackup(releaseBackupPath(b.h,state.Operation),key)
	if e!=nil || releasePlainDigest(m)!=state.Backup {return errors.New("sealed fixture backup missing or incompatible")}
	if state.AdmissionBundle==nil || !state.AdmissionBundle.SameSchema || !state.AdmissionBundle.NoUnknownEffects {return errors.New("same-schema idle rollback proof absent")}
	return nil
}

func releaseFixtureVerifier(h Object) supervisor.AdmissionVerifier {
	return func(a supervisor.ReleaseAdmission) error {
		if len(a.Operation)!=64 || !strings.EqualFold(a.Operation,strings.ToLower(a.Operation)) {return errors.New("invalid operation identifier")}
		b,e:=os.ReadFile(releaseAdmissionPath(h,a.Operation));if e!=nil {return e}
		var frozen supervisor.ReleaseAdmission
		if e=json.Unmarshal(b,&frozen);e!=nil {return e}
		if releasePlainDigest(frozen)!=releasePlainDigest(a) || frozen.Project=="" || frozen.CandidateID=="" {return errors.New("supervisor sealed admission differs")}
		return nil
	}
}

func (s *Service) releaseFixtureEngine(h Object,j *supervisor.ReleaseJournal) (*supervisor.ReleaseEngine,error) {
	d:=releaseFixtureDriver()
	return supervisor.NewReleaseEngine(j,d,releaseFixtureBarrier{s:s,h:h,driver:d},releaseFixtureVerifier(h))
}

// BootstrapEvolutionReleaseFixture is host-only provisioning. It uses only a
// new OS-temp fixture root registered with os_service_qualified=false.
func (s *Service) BootstrapEvolutionReleaseFixture(ctx context.Context,project string) error {
	tx,e:=s.DB.BeginTx(ctx,nil);if e!=nil {return e}
	h,e:=evolutionHost(tx,project);_ = tx.Rollback();if e!=nil {return e}
	if h["release_mechanism"]!=releaseFixtureMechanism || h["os_service_qualified"]!=false {return errors.New("R2 native fixture host required")}
	j,e:=supervisor.OpenReleaseJournal(releaseStateRoot(h));if e!=nil {return e};defer j.Close()
	engine,e:=s.releaseFixtureEngine(h,j);if e!=nil {return e}
	return engine.BootstrapFixture(ctx,filepath.Join(Str(h,"root"),"stable.exe"),Str(h,"root"))
}

func releaseOperationID(project,candidate,acceptance string,epoch uint64) string {
	return releasePlainDigest(Object{"project":project,"candidate":candidate,"action":"START_CANARY","acceptance":acceptance,"epoch":epoch})
}

func (s *Service) releaseAdmissionInputs(tx *sql.Tx,project string,x,h,b,record Object,epoch uint64,backupHash string) (supervisor.ReleaseAdmission,error) {
	var a supervisor.ReleaseAdmission
	if h["release_mechanism"]!=releaseFixtureMechanism || h["os_service_qualified"]!=false {return a,errors.New("fixture release host required")}
	deadline,e:=time.Parse(time.RFC3339Nano,Str(b,"observation_deadline"));if e!=nil {return a,e}
	acceptanceID:=Str(b,"regression_acceptance_id")
	accepted,e:=load(tx,project,"AcceptanceReceipt",acceptanceID);if e!=nil {return a,e}
	if record["improved"]!=true || record["required_passed"]!=true || record["holdout_summary"]==nil || record["holdout_proof_hash"]==nil {return a,errors.New("private objective benefit and required regression proof required")}
	if record["holdout_summary"].(map[string]any)["gain"]!=true {return a,errors.New("private holdout did not improve")}
	a=supervisor.ReleaseAdmission{
		Project:project,CandidateID:Str(x,"id"),AcceptanceID:acceptanceID,ExecutionSHA256:releaseArtifactDigest(record["receipt_hash"]),
		Operation:releaseOperationID(project,Str(x,"id"),acceptanceID,epoch),ExpectedEpoch:epoch,
		StableSHA256:releaseArtifactDigest(x["stable_artifact_ref"].(map[string]any)["content_hash"]),
		CandidateSHA256:releaseArtifactDigest(x["candidate_artifact_ref"].(map[string]any)["content_hash"]),
		BackupReceiptSHA256:backupHash,VerifierReceiptSHA256:releaseArtifactDigest(accepted["receipt_hash"]),
		HoldoutProofSHA256:releaseArtifactDigest(record["holdout_proof_hash"]),SameSchema:true,NoUnknownEffects:true,ExpiresUTC:deadline.UTC(),
	}
	return a,nil
}

// SealEvolutionReleaseFixture is an explicitly local, host-side test action.
// It seals the independently accepted exact candidate before public HTTP
// START_CANARY records its intent. Production needs a distinct OS verifier.
func (s *Service) SealEvolutionReleaseFixture(ctx context.Context,project,candidate string,request Object) (supervisor.ReleaseAdmission,error) {
	var zero supervisor.ReleaseAdmission
	tx,e:=s.DB.BeginTx(ctx,nil);if e!=nil {return zero,e};defer tx.Rollback()
	x,e:=load(tx,project,"SystemCandidate",candidate);if e!=nil {return zero,e}
	h,e:=s.evolutionCurrent(tx,project,x);if e!=nil {return zero,e}
	if x["status"]!="EVALUATING" || request["action"]!="START_CANARY" {return zero,errors.New("fixture candidate not awaiting canary intent")}
	record,e:=s.evolutionAccepted(tx,project,x,"REGRESSION",Str(request,"regression_acceptance_id"));if e!=nil {return zero,e}
	var epoch uint64
	if e=tx.QueryRow("SELECT epoch FROM evolution_slots WHERE project=? AND state='STABLE'",project).Scan(&epoch);e!=nil {return zero,e}
	if e=tx.Rollback();e!=nil && !errors.Is(e,sql.ErrTxDone) {return zero,e}
	j,e:=supervisor.OpenReleaseJournal(releaseStateRoot(h));if e!=nil {return zero,e}
	state:=j.State();_ = j.Close()
	if state.Epoch!=epoch || state.Active!=releaseArtifactDigest(x["stable_artifact_ref"].(map[string]any)["content_hash"]) || state.Phase!="STABLE" {return zero,errors.New("fixture supervisor slot differs from frozen stable")}
	operation:=releaseOperationID(project,candidate,Str(request,"regression_acceptance_id"),epoch)
	backupParent:=filepath.Join(releaseStateRoot(h),"backups")
	if e=os.MkdirAll(backupParent,0700);e!=nil {return zero,e}
	key:=make([]byte,32);if _,e=rand.Read(key);e!=nil {return zero,e};defer clear(key)
	if e=os.WriteFile(releaseKeyPath(h,operation),key,0600);e!=nil {return zero,e}
	manifest,e:=s.CreateBackup(ctx,releaseBackupPath(h,operation),key);if e!=nil {return zero,e}
	// A fresh read rechecks current acceptance after the actual backup; no
	// trusted result is inferred from the operation row itself.
	tx,e=s.DB.BeginTx(ctx,nil);if e!=nil {return zero,e};defer tx.Rollback()
	x,e=load(tx,project,"SystemCandidate",candidate);if e!=nil {return zero,e}
	record,e=s.evolutionAccepted(tx,project,x,"REGRESSION",Str(request,"regression_acceptance_id"));if e!=nil {return zero,e}
	a,e:=s.releaseAdmissionInputs(tx,project,x,h,request,record,epoch,releasePlainDigest(manifest));if e!=nil {return zero,e}
	path:=releaseAdmissionPath(h,a.Operation)
	if e=os.MkdirAll(filepath.Dir(path),0700);e!=nil {return zero,e}
	encoded,e:=json.Marshal(a);if e!=nil {return zero,e}
	f,e:=os.OpenFile(path,os.O_CREATE|os.O_EXCL|os.O_WRONLY,0600);if e!=nil {return zero,e}
	if _,e=f.Write(encoded);e==nil {e=f.Sync()};if c:=f.Close();e==nil {e=c}
	return a,e
}

// evolutionReleaseIntent is called only from the frozen public action path,
// inside the same transaction that bumps SystemCandidate revision.
func (s *Service) evolutionReleaseIntent(tx *sql.Tx,project string,x,h,b,record Object) error {
	var epoch uint64
	if e:=tx.QueryRow("SELECT epoch FROM evolution_slots WHERE project=? AND state='STABLE'",project).Scan(&epoch);e!=nil {return e}
	op:=releaseOperationID(project,Str(x,"id"),Str(b,"regression_acceptance_id"),epoch)
	raw,e:=os.ReadFile(releaseAdmissionPath(h,op));if e!=nil {return Fail(422,"GATE_FAILED","supervisor sealed admission unavailable")}
	var sealed supervisor.ReleaseAdmission
	if e=json.Unmarshal(raw,&sealed);e!=nil {return e}
	expected,e:=s.releaseAdmissionInputs(tx,project,x,h,b,record,epoch,sealed.BackupReceiptSHA256);if e!=nil {return e}
	if releasePlainDigest(sealed)!=releasePlainDigest(expected) || !sealed.ExpiresUTC.After(time.Now().UTC()) {return Fail(422,"GATE_FAILED","supervisor admission changed or expired")}
	var count int
	if e=tx.QueryRow("SELECT count(*) FROM evolution_release_operations WHERE project=? AND candidate=? AND action='START_CANARY'",project,x["id"]).Scan(&count);e!=nil {return e}
	if count!=0 {return Fail(409,"STATE_CONFLICT","release operation already registered")}
	_,e=tx.Exec("INSERT INTO evolution_release_operations(project,candidate,action,operation_id,expected_epoch,admission_hash,effect_key,status) VALUES(?,?,'START_CANARY',?,?,? ,?,'PREPARED')",project,x["id"],sealed.Operation,epoch,releasePlainDigest(sealed),"r2-fixture-"+sealed.Operation)
	if e!=nil {return e}
	x["observation_deadline"]=b["observation_deadline"]
	return nil
}
