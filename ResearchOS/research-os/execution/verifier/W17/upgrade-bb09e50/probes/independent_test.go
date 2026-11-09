package domain

import (
 "context"
 "database/sql"
 "fmt"
 "os"
 "os/exec"
 "path/filepath"
 "strings"
 "testing"
 "researchos.local/research-os/internal/store"
 "researchos.local/research-os/adapters/protectedstore"
)

func TestIndependentUpgradeReceiptSubject(t *testing.T) {
 opt, f, fake := upgradeFixture(t, true)
 qs,e := backupObjects(f.db,"SELECT body FROM domain_objects WHERE kind='Qualification' ORDER BY id")
 if e!=nil {t.Fatal(e)}
 q:=copyObject(qs[0])
 var raw string
 if e=f.db.QueryRow("SELECT body FROM domain_objects WHERE kind='AcceptanceReceipt' AND id=?",q["acceptance_id"]).Scan(&raw);e!=nil {t.Fatal(e)}
 receipt,e:=Decode([]byte(raw));if e!=nil {t.Fatal(e)}
 oldReceiptID:=receipt["id"]
 oldQRevision:=q["revision"]
 receipt["id"]=ID()
 // An internally consistent receipt hash does not prove the right subject.
 receipt["subject_ref"]=Ref(qs[1],"Qualification")
 receipt["receipt_hash"]=Receipt(receipt)
 if e=bump(q);e!=nil {t.Fatal(e)}
 q["acceptance_id"]=receipt["id"]
 sourceTx(t,f.db,func(tx *sql.Tx)error{
  for _,entry:=range []struct{kind string;obj Object}{{"AcceptanceReceipt",receipt},{"Qualification",q}} {
   o:=entry.obj
   if e:=f.s.Contracts.Validate(entry.kind,o);e!=nil{return e}
   var contentHash any;immutable:=0;priorID,priorRevision:=q["id"],oldQRevision
   if entry.kind=="AcceptanceReceipt"{contentHash=o["receipt_hash"];immutable=1;priorID=oldReceiptID;priorRevision=1}
   if _,e:=tx.Exec("INSERT INTO domain_versions(project,kind,id,revision,body,content_hash) VALUES(?,?,?,?,?,?)",f.project,entry.kind,o["id"],o["revision"],string(Bytes(o)),contentHash);e!=nil{return e}
   if _,e:=tx.Exec("INSERT INTO domain_objects(project,kind,id,revision,body,content_hash,immutable) VALUES(?,?,?,?,?,?,?) ON CONFLICT(project,kind,id) DO UPDATE SET revision=excluded.revision,body=excluded.body",f.project,entry.kind,o["id"],o["revision"],string(Bytes(o)),contentHash,immutable);e!=nil{return e}
   if _,e:=tx.Exec("INSERT INTO domain_refs SELECT project,kind,?,?,field,target_project,target_kind,target_id,target_revision FROM domain_refs WHERE project=? AND kind=? AND id=? AND revision=?",o["id"],o["revision"],f.project,entry.kind,priorID,priorRevision);e!=nil{return e}
   if entry.kind=="AcceptanceReceipt"{if _,e:=tx.Exec("UPDATE domain_refs SET target_id=?,target_revision=? WHERE project=? AND kind='AcceptanceReceipt' AND id=? AND field='subject_ref'",qs[1]["id"],qs[1]["revision"],f.project,o["id"]);e!=nil{return e}}
  }
  return nil
 })
 evidence:=Object{"attack":"receipt subject references different qualification","qualification":q,"receipt":receipt,"expected":"reject before publication"}
 if e=os.WriteFile(filepath.Join(os.Getenv("W17_INDEPENDENT_EVIDENCE"),"receipt-subject-input.json"),Bytes(evidence),0600);e!=nil{t.Fatal(e)}
 f.db.Close()
 report,e:=upgradeLocal(context.Background(),opt,fake.verifier())
 t.Logf("wrong receipt subject upgrade status=%s error=%v reads=%d",report.Status,e,fake.reads)
 if e==nil {t.Fatal("INDEPENDENT_FINDING: unrelated qualification receipt subject accepted and target published")}
}

func TestIndependentUpgradeLateReleaseAndPackage(t *testing.T) {
 opt,f,fake:=upgradeFixture(t,true)
 before,e:=upgradeRows(f.db);if e!=nil{t.Fatal(e)}
 f.db.Close()
 v:=fake.verifier()
 original:=v.summary
 calls:=0
 v.summary=func(ctx context.Context)(protectedstore.SafeSummary,error){
  calls++
  if calls==3 {if e:=os.WriteFile(filepath.Join(opt.TargetRoot,"migrations/sqlite/0015_injected.sql"),[]byte("SELECT 1;"),0600);e!=nil{return protectedstore.SafeSummary{},e}}
  return original(ctx)
 }
 _,e=upgradeLocal(context.Background(),opt,v)
 if e==nil||!strings.Contains(e.Error(),"UPGRADE_RELEASE_CHANGED"){t.Fatalf("late release mutation: %v",e)}
 if _,e=os.Stat(opt.Destination);!os.IsNotExist(e){t.Fatal("published failed target")}
 raw,e:=os.ReadFile(filepath.Join(opt.Snapshot,"manifest.json"));if e!=nil{t.Fatal(e)}
 key,e:=os.ReadFile(opt.KeyFile);if e!=nil{t.Fatal(e)}
 manifest,e:=Decode(raw);if e!=nil{t.Fatal(e)}
 m,files,e:=readBackupPolicy(opt.Snapshot,key,&backupPolicy{format:localUpgradeFormat,purpose:manifest["purpose"].(map[string]any)})
 if e!=nil||len(files["state.sqlite"])==0{t.Fatalf("stable package unusable: %v",e)}
 db,e:=store.Open(opt.Source);if e!=nil{t.Fatal(e)};defer db.Close()
 after,e:=upgradeRows(db);if e!=nil||Hash(before)!=Hash(after){t.Fatalf("source mutated: %v",e)}
 t.Logf("late release rejected; source hash stable; encrypted package MAC/decryption verified; backup=%s; Read=%d",m.ID,fake.reads)
}

func TestIndependentUpgradeLockChild(t *testing.T) {
 path:=os.Getenv("W17_INDEPENDENT_LOCK_DB");if path==""{return}
 db,e:=store.Open(path)
 if db!=nil{db.Close()}
 if e==nil{t.Fatal("child acquired exclusive source")}
 fmt.Println("INDEPENDENT_CHILD_SOURCE_EXCLUDED",e)
}

func TestIndependentUpgradeLockAcrossStages(t *testing.T) {
 opt,f,fake:=upgradeFixture(t,true);f.db.Close()
 v:=fake.verifier();original:=v.summary;calls:=0
 v.summary=func(ctx context.Context)(protectedstore.SafeSummary,error){
  calls++
  child:=exec.Command(os.Args[0],"-test.run=^TestIndependentUpgradeLockChild$","-test.v")
  child.Env=append(os.Environ(),"W17_INDEPENDENT_LOCK_DB="+opt.Source)
  output,e:=child.CombinedOutput()
  if e!=nil||!strings.Contains(string(output),"INDEPENDENT_CHILD_SOURCE_EXCLUDED"){return protectedstore.SafeSummary{},fmt.Errorf("child stage %d lock failed: %v %s",calls,e,output)}
  t.Logf("source excluded real child process during validation stage %d: %s",calls,strings.TrimSpace(string(output)))
  return original(ctx)
 }
 _,e:=upgradeLocal(context.Background(),opt,v);if e!=nil{t.Fatal(e)}
 if calls<4{t.Fatalf("missing snapshot/restore/final checks: %d",calls)}
 db,e:=store.Open(opt.Source);if e!=nil{t.Fatal(e)};db.Close()
 t.Logf("source released only after publication; stages=%d Read=%d",calls,fake.reads)
}

func TestIndependentUpgradeHostileInputs(t *testing.T) {
 for _,attack:=range []string{"current-history-divergence","historical-protected-fixture","late-program-replacement","late-target-created","source-root-old-sql-tamper"}{t.Run(attack,func(t *testing.T){
  opt,f,fake:=upgradeFixture(t,true)
  expected:=""
  switch attack {
  case "current-history-divergence":
   expected="UPGRADE_CURRENT_HISTORY_BINDING"
   if _,e:=f.db.Exec("UPDATE domain_objects SET body=json_set(body,'$.expires_at','2099-01-01T00:00:00Z') WHERE kind='Qualification'");e!=nil{t.Fatal(e)}
  case "historical-protected-fixture":
   expected="UPGRADE_PROTECTED_REFERENCE_INVALID"
   arts,e:=backupObjects(f.db,"SELECT body FROM domain_objects WHERE kind='Artifact' AND json_extract(body,'$.access_class')='VERIFIER_ONLY'");if e!=nil{t.Fatal(e)}
   a:=copyObject(arts[0]);a["id"]=ID();a["revision"]=1;a["measurement_mode"]="FIXTURE"
   if _,e=f.db.Exec("INSERT INTO domain_versions(project,kind,id,revision,body,content_hash) VALUES(?,'Artifact',?,1,?,?)",f.project,a["id"],string(Bytes(a)),a["content_hash"]);e!=nil{t.Fatal(e)}
  case "source-root-old-sql-tamper":
   expected="UPGRADE_RELEASE_HASH"
   path:=filepath.Join(opt.SourceRoot,"migrations/sqlite/0007_retrieval.sql")
   raw,e:=os.ReadFile(path);if e!=nil{t.Fatal(e)}
   if e=os.WriteFile(path,append(raw,[]byte("\n-- changed old migration\n")...),0600);e!=nil{t.Fatal(e)}
  case "late-program-replacement":
   expected="UPGRADE_PROGRAM_CHANGED"
   opt.TargetProgram=filepath.Join(t.TempDir(),"reviewed-program.fixture")
   if e:=os.WriteFile(opt.TargetProgram,[]byte("reviewed"),0600);e!=nil{t.Fatal(e)}
  case "late-target-created":expected="DESTINATION_EXISTS"
  }
  before,e:=upgradeRows(f.db);if e!=nil{t.Fatal(e)};f.db.Close()
  v:=fake.verifier();original:=v.summary;calls:=0
  v.summary=func(ctx context.Context)(protectedstore.SafeSummary,error){calls++
   if calls==2 {
    if attack=="late-program-replacement"{if e:=os.WriteFile(opt.TargetProgram,[]byte("unreviewed"),0600);e!=nil{return protectedstore.SafeSummary{},e}}
    if attack=="late-target-created"{if e:=os.Mkdir(opt.Destination,0700);e!=nil{return protectedstore.SafeSummary{},e}}
   };return original(ctx)
  }
  _,e=upgradeLocal(context.Background(),opt,v)
  if e==nil||!strings.Contains(e.Error(),expected){t.Fatalf("%s: expected %s got %v",attack,expected,e)}
  if _,e=os.Stat(filepath.Join(opt.Destination,"researchos.sqlite"));!os.IsNotExist(e){t.Fatal("failed target published")}
  db,e:=store.Open(opt.Source);if e!=nil{t.Fatal(e)};after,e:=upgradeRows(db);db.Close()
  if e!=nil||Hash(before)!=Hash(after){t.Fatalf("source changed: %v",e)}
  if strings.HasPrefix(attack,"late-"){if _,e=os.Stat(filepath.Join(opt.Snapshot,"manifest.json"));e!=nil{t.Fatal("stable encrypted package lost",e)}}
  if fake.reads!=0{t.Fatal("private Read attempted")}
  t.Logf("%s rejected with %s; source unchanged; target unpublished; Read=0",attack,expected)
 })}
}

func TestIndependentUpgradeJunctionAlias(t *testing.T) {
 opt,f,fake:=upgradeFixture(t,true);f.db.Close()
 alias:=filepath.Join(t.TempDir(),"source-junction")
 command:=exec.Command("cmd.exe","/c","mklink","/J",alias,filepath.Dir(opt.Source))
 output,e:=command.CombinedOutput();if e!=nil{t.Fatalf("junction fixture setup: %v %s",e,output)}
 opt.Snapshot=filepath.Join(alias,"snapshot-child")
 resolved,e:=upgradePath(opt.Snapshot,false);if e!=nil{t.Fatal(e)}
 target,e:=os.Readlink(alias)
 t.Logf("junction output=%s source=%s alias=%s Readlink=%s error=%v resolvedSnapshot=%s",output,opt.Source,alias,target,e,resolved)
 _,e=upgradeLocal(context.Background(),opt,fake.verifier())
 if e==nil {
  info,err:=os.Stat(filepath.Join(filepath.Dir(opt.Source),"snapshot-child","manifest.json"))
  t.Logf("actual snapshot created inside source directory: exists=%v error=%v",info!=nil,err)
  if err==nil{raw,_:=os.ReadFile(filepath.Join(filepath.Dir(opt.Source),"snapshot-child","manifest.json"));os.WriteFile(filepath.Join(os.Getenv("W17_INDEPENDENT_EVIDENCE"),"junction-alias-manifest.json"),raw,0600)}
 }
 if e==nil||!strings.Contains(e.Error(),"UPGRADE_PATH_OVERLAP"){t.Fatalf("native junction overlap escaped: %v",e)}
 if _,e=os.Stat(opt.Snapshot);!os.IsNotExist(e){t.Fatal("aliased snapshot created")}
 if fake.refreshes!=0||fake.reads!=0{t.Fatal("provider called before path rejection")}
 t.Log("native NTFS junction existing ancestor resolved; source snapshot overlap rejected before metadata/provider calls")
}

func TestIndependentUpgradeSourceRename(t *testing.T) {
 opt,f,fake:=upgradeFixture(t,true);f.db.Close()
 v:=fake.verifier();original:=v.summary;calls:=0;renameSucceeded:=false
 v.summary=func(ctx context.Context)(protectedstore.SafeSummary,error){calls++
  if calls==2 {
   e:=os.Rename(opt.Source,opt.Source+".moved")
   renameSucceeded=e==nil
   t.Logf("attempted native source rename while locked: succeeded=%v error=%v",renameSucceeded,e)
  };return original(ctx)
 }
 _,e:=upgradeLocal(context.Background(),opt,v)
 if renameSucceeded&&e==nil{t.Fatal("INDEPENDENT_FINDING: target published after source path identity replaced")}
 if !renameSucceeded&&e!=nil{t.Fatal(e)}
 t.Logf("source identity protected during native lock: renameSucceeded=%v upgradeError=%v",renameSucceeded,e)
}
