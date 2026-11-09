package domain

import (
 "bytes"
 "context"
 "encoding/json"
 "database/sql"
 "os"
 "path/filepath"
 "strings"
 "testing"
 "time"

 "researchos.local/research-os/internal/store"
)

// These are public local fixtures, not evidence of a historical release binary,
// OS owner authentication, production migration, or the complete 20-to24 route.
func history20Fixture(t *testing.T) (LocalUpgradeOptions, upgradeData) {
 t.Helper()
 source, target := upgradeTestRelease(t, 20), upgradeTestRelease(t, 20)
 raw, err := os.ReadFile("../../migrations/sqlite/0021_research_pending_windows.sql")
 if err != nil { t.Fatal(err) }
 if err = os.WriteFile(filepath.Join(target, "migrations/sqlite/0021_research_pending_windows.sql"), raw, 0600); err != nil { t.Fatal(err) }
 _, sqls, err := upgradeHistory20Release(source, 20)
 if err != nil { t.Fatal(err) }
 base := t.TempDir()
 opt := LocalUpgradeOptions{Source: filepath.Join(base,"source.sqlite"), Snapshot: filepath.Join(base,"backup"), Destination: filepath.Join(base,"candidate"), KeyFile: filepath.Join(base,"recovery.key"), SourceRoot:source, TargetRoot:target, SourceProgram:filepath.Join(base,"source.program"), TargetProgram:filepath.Join(base,"target.program"), Plan:History20SchemaUpgradePlan}
 for path, data := range map[string][]byte{opt.KeyFile:bytes.Repeat([]byte{7},32), opt.SourceProgram:[]byte("PUBLIC_FIXTURE_SOURCE_PROGRAM_BYTES"), opt.TargetProgram:[]byte("PUBLIC_FIXTURE_TARGET_PROGRAM_BYTES")} {
  if err = os.WriteFile(path,data,0600); err != nil { t.Fatal(err) }
 }
 db, err := store.Open(opt.Source)
 if err != nil { t.Fatal(err) }
 defer db.Close()
 // Deliberately do not call New: it would install current additive schema.
 for i, raw := range sqls {
  if _, err = db.Exec(string(raw)); err != nil { t.Fatal(err) }
  if _, err = db.Exec("INSERT INTO schema_migrations(version) VALUES(?)", i+1); err != nil { t.Fatal(err) }
 }
 contracts, err := LoadContracts(filepath.Join(source,"spec/v2.0/contracts"))
 if err != nil { t.Fatal(err) }
 svc := &Service{DB:db, Contracts:contracts}
 owner := Principal{ID:ID(),Roles:[]string{"OWNER"},CanCreateProject:true}
 if err = svc.ProvisionPrincipal(context.Background(),owner); err != nil { t.Fatal(err) }
 if _, err = svc.IssueCredential(context.Background(),owner.ID,time.Minute); err != nil { t.Fatal(err) }
 before, err := upgradeRows(db)
 if err != nil { t.Fatal(err) }
 return opt,before
}

func history20Rows(t *testing.T, path string) upgradeData {
 t.Helper()
 db, err := store.Open(path)
 if err != nil { t.Fatal(err) }
 defer db.Close()
 rows, err := upgradeRows(db)
 if err != nil { t.Fatal(err) }
 return rows
}

func TestHistory20PublicUpgradePreservesSourceAndRevokesRestoredCredentials(t *testing.T) {
 opt,before := history20Fixture(t)
 report,err := UpgradeLocal(context.Background(),opt)
 if err != nil { t.Fatal(err) }
 if report.Status != "RESTORED_RECONCILIATION_REQUIRED" { t.Fatalf("unexpected status %s", report.Status) }
 if Hash(history20Rows(t,opt.Source)) != Hash(before) { t.Fatal("source rows changed") }
 after := history20Rows(t,filepath.Join(opt.Destination,"researchos.sqlite"))
 if err = upgradeHistory20RecoveryInvariant(before,after,opt.Destination,true); err != nil { t.Fatal(err) }
 if len(after["research_pending_windows"]) != 0 || len(after["schema_migrations"]) != 21 { t.Fatal("wrong migration result") }
 if _,ok := after["client_sessions"]; ok { t.Fatal("unreviewed additive sessions installed") }
 if Hash(before["auth_principals"]) != Hash(after["auth_principals"]) { t.Fatal("Owner row changed") }
 for _, row := range after["auth_credentials"] { revoked,err := Num(row,"revoked"); if err != nil || revoked != 1 { t.Fatal("restored credential still active") } }
 key,err := os.ReadFile(opt.KeyFile)
 if err != nil { t.Fatal(err) }
 defer clear(key)
 raw,err := os.ReadFile(filepath.Join(opt.Snapshot,"manifest.json"))
 if err != nil { t.Fatal(err) }
 var manifest BackupManifest
 if err = json.Unmarshal(raw,&manifest); err != nil { t.Fatal(err) }
 plan,ok := manifest.Purpose["plan"].(map[string]any)
 if !ok || plan["id"] != History20SchemaUpgradePlan || manifest.Format != localUpgradeFormat { t.Fatal("wrong snapshot plan or format") }
 policy := &backupPolicy{format:localUpgradeFormat,databaseName:"researchos.sqlite",purpose:manifest.Purpose}
 verified,files,err := readBackupPolicy(opt.Snapshot,key,policy)
 if err != nil { t.Fatalf("correct key rejected under matching upgrade policy: %v",err) }
 if len(files["state.sqlite"]) == 0 || Hash(verified.Migrations) != Hash(upgradeVersions(20)) { t.Fatal("authenticated snapshot missing historical20 database or migrations") }
 if _,ok := files["portable.json"]; ok { t.Fatal("upgrade snapshot contains a portable export") }
 wrong := append([]byte(nil),key...); defer clear(wrong); wrong[0] ^= 1
 _,wrongFiles,err := readBackupPolicy(opt.Snapshot,wrong,policy)
 if err == nil || err.Error() != "BACKUP_MANIFEST_INVALID" || wrongFiles != nil { t.Fatalf("wrong key did not fail snapshot authentication: %v",err) }
}

func TestHistory20RejectsReleaseAndSourceDrift(t *testing.T) {
 for _, tc := range []string{"migration-hash","extra-numbered-migration","foreign-table","session-addon"} {
  t.Run(tc,func(t *testing.T){
   opt,before := history20Fixture(t)
   switch tc {
   case "migration-hash":
    p:=filepath.Join(opt.TargetRoot,"migrations/sqlite/0021_research_pending_windows.sql")
    if err:=os.WriteFile(p,[]byte("SELECT 1;"),0600); err!=nil {t.Fatal(err)}
   case "extra-numbered-migration":
    if err:=os.WriteFile(filepath.Join(opt.SourceRoot,"migrations/sqlite/0021_unapproved.sql"),[]byte("SELECT 1;"),0600);err!=nil {t.Fatal(err)}
   default:
    db,err:=store.Open(opt.Source);if err!=nil {t.Fatal(err)}
    raw:=[]byte("CREATE TABLE foreign_authority(id TEXT)")
    if tc=="session-addon" {raw,err=os.ReadFile("../../migrations/sqlite/next_v24_sessions.sql");if err!=nil {db.Close();t.Fatal(err)}}
    _,err=db.Exec(string(raw));db.Close();if err!=nil {t.Fatal(err)}
    before=history20Rows(t,opt.Source)
   }
   _,err:=UpgradeLocal(context.Background(),opt)
   if err==nil {t.Fatal("source/release drift accepted")}
   for _,p:=range []string{opt.Destination,opt.Snapshot} {if _,err:=os.Stat(p);!os.IsNotExist(err){t.Fatalf("early rejection published %s: %v",p,err)}}
   if Hash(history20Rows(t,opt.Source))!=Hash(before){t.Fatal("rejection mutated source")}
  })
 }
}

func TestHistory20MigrationRollsBackDDLWhenLedgerInsertFails(t *testing.T) {
 opt,_:=history20Fixture(t)
 db,err:=store.Open(opt.Source);if err!=nil {t.Fatal(err)};defer db.Close()
 if _,err=db.Exec("CREATE TRIGGER fixture_reject_21 BEFORE INSERT ON schema_migrations WHEN NEW.version=21 BEGIN SELECT RAISE(ABORT,'fixture ledger failure'); END");err!=nil {t.Fatal(err)}
 before,err:=backupSchema(db);if err!=nil {t.Fatal(err)}
 rows,err:=upgradeRows(db);if err!=nil {t.Fatal(err)}
 raw,err:=os.ReadFile(filepath.Join(opt.TargetRoot,"migrations/sqlite/0021_research_pending_windows.sql"));if err!=nil {t.Fatal(err)}
 if err=upgradeHistory20Migration(context.Background(),db,raw);err==nil || !strings.Contains(err.Error(),"fixture ledger failure"){t.Fatalf("expected actual transaction failure: %v",err)}
 after,err:=backupSchema(db);if err!=nil {t.Fatal(err)}
 now,err:=upgradeRows(db);if err!=nil {t.Fatal(err)}
 if before!=after || Hash(rows)!=Hash(now){t.Fatal("failed DDL transaction survived rollback")}
}

func TestHistory20RestoreFailureRetainsEncryptedBackupAndSource(t *testing.T) {
 opt,before:=history20Fixture(t)
 key,err:=os.ReadFile(opt.KeyFile);if err!=nil {t.Fatal(err)}
 db,err:=store.Open(opt.Source);if err!=nil {t.Fatal(err)};defer db.Close()
 contracts,err:=LoadContracts(filepath.Join(opt.SourceRoot,"spec/v2.0/contracts"));if err!=nil {t.Fatal(err)}
 svc:=&Service{DB:db,Contracts:contracts}
 if _,err=svc.CreateBackup(context.Background(),opt.Snapshot,key);err!=nil {t.Fatal(err)}
 _,err=RestoreBackup(context.Background(),opt.Snapshot,opt.Destination,RestoreOptions{Key:key,SupportedMigrations:upgradeVersions(20),Contracts:contracts,Migration:func(ctx context.Context,target *sql.DB) error {
  if _,err:=target.ExecContext(ctx,"CREATE TABLE fixture_unpublished(value TEXT)");err!=nil{return err}
  return context.Canceled
 }})
 if err==nil {t.Fatal("injected migration failure accepted")}
 if _,err=os.Stat(opt.Destination);!os.IsNotExist(err){t.Fatalf("failed destination published: %v",err)}
 if _,err=os.Stat(opt.Snapshot);err!=nil {t.Fatal("backup lost",err)}
 now,err:=upgradeRows(db);if err!=nil {t.Fatal(err)}
 if Hash(now)!=Hash(before){t.Fatal("source changed after isolated failure")}
}

func TestHistory20ImplicitStartupStillRejectsPopulatedSource(t *testing.T) {
 opt,_:=history20Fixture(t)
 db,err:=store.Open(opt.Source);if err!=nil {t.Fatal(err)};defer db.Close()
 files,err:=filepath.Glob(filepath.Join(opt.TargetRoot,"migrations/sqlite/0*.sql"));if err!=nil {t.Fatal(err)}
 if err=CheckMigrationSafety(db,files);err==nil || !strings.Contains(err.Error(),"MIGRATION_PREBACKUP_REQUIRED"){t.Fatalf("implicit upgrade not blocked: %v",err)}
}
