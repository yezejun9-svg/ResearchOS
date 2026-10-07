//go:build windows

package domain

import (
 "context"
 "database/sql"
 "encoding/json"
 "fmt"
 "os"
 "path/filepath"
 "strings"
 "testing"
 "researchos.local/research-os/internal/store"
)

// This receipt-owned diagnostic never constructs a coordinator, Host,
// credential resolver, worker, SDK session or HTTP client/server.
func TestIndependentP12Offline(t *testing.T) {
 raw, err := os.ReadFile(os.Getenv("P12_CASE_FILE")); if err != nil { t.Fatal(err) }
 var c struct { Database string; Output string; Mode string; ExpectedSHA string }
 if err = json.Unmarshal(raw, &c); err != nil { t.Fatal(err) }
 original, err := os.ReadFile(c.Database); if err != nil { t.Fatal(err) }
 if strings.TrimPrefix(Digest(original), "sha256:") != c.ExpectedSHA { t.Fatal("copied fixture does not match frozen input") }
 db, err := store.Open(c.Database); if err != nil { t.Fatal(err) }
 result := Object{"case": c.Mode, "copied_input_sha256": Digest(original), "model_calls": 0, "worker_starts": 0, "http_calls": 0}
 defer func() {
  _, checkpointErr := db.Exec("PRAGMA wal_checkpoint(TRUNCATE)")
  closeErr := db.Close()
  result["checkpoint_error"], result["close_error"] = p12Error(checkpointErr), p12Error(closeErr)
  after, e := os.ReadFile(c.Database); if e == nil { result["copied_output_sha256"] = Digest(after) }
  if e = os.WriteFile(filepath.Join(c.Output,"actual.json"), Bytes(result),0600); e != nil { t.Error(e) }
 }()
 result["before"] = p12State(t, db)
 if c.Mode != "baseline" && c.Mode != "public_positive" {
  tx, e := db.Begin(); if e != nil { t.Fatal(e) }
  rows, e := tx.Query("SELECT name,sql FROM sqlite_master WHERE type='trigger' AND tbl_name IN ('runtime_dispatches','resource_effects') ORDER BY name")
  if e != nil { tx.Rollback(); t.Fatal(e) }
  type trigger struct { name, sql string }; var triggers []trigger
  for rows.Next() { var tr trigger; if e=rows.Scan(&tr.name,&tr.sql);e!=nil {rows.Close();tx.Rollback();t.Fatal(e)};triggers=append(triggers,tr) }
  if e=rows.Err();e!=nil {rows.Close();tx.Rollback();t.Fatal(e)};rows.Close()
  mutations:=[]any{}
  for _,tr:=range triggers { q:=`DROP TRIGGER "`+strings.ReplaceAll(tr.name,`"`,`""`)+`"`;if _,e=tx.Exec(q);e!=nil {tx.Rollback();t.Fatal(e)};mutations=append(mutations,q) }
  queries:=[]string{`UPDATE resource_effects SET body=json_remove(body,'$.payload.provider_transport') WHERE json_extract(body,'$.payload.capability')='MODEL'`}
  switch c.Mode {
  case "missing_dispatch_and_transport": queries=append(queries,`DELETE FROM runtime_dispatches`)
  case "removed_profile_policy_and_transport": queries=append(queries,`UPDATE runtime_dispatches SET manifest=json_remove(manifest,'$.admission.profile_ref','$.admission.profile.model_config.provider_policy')`)
  default:tx.Rollback();t.Fatal("unregistered case",c.Mode)
  }
  for _,q:=range queries { r,e:=tx.Exec(q);if e!=nil {tx.Rollback();t.Fatal(e)};n,_:=r.RowsAffected();mutations=append(mutations,Object{"sql":q,"affected_rows":n}) }
  for _,tr:=range triggers {if _,e=tx.Exec(tr.sql);e!=nil {tx.Rollback();t.Fatal(e)};mutations=append(mutations,Object{"restored_trigger_sql":tr.sql})}
  if e=tx.Commit();e!=nil {t.Fatal(e)}
  result["mutations"]=mutations
 }
 result["after_mutation"] = p12State(t,db)
 if c.Mode == "public_positive" {
  contracts,e:=LoadContracts(filepath.Join("..","..","spec","v2.0","contracts"));if e!=nil {t.Fatal(e)}
  s:=&Service{DB:db,Contracts:contracts};key:=backupTestKey(t);archive:=filepath.Join(c.Output,"archive")
  manifest,e:=s.CreateBackup(context.Background(),archive,key);result["public_create_error"]=p12Error(e);if e!=nil {t.Fatal("public create prerequisite",e)}
  result["manifest"]=manifest;target:=filepath.Join(c.Output,"restored")
  report,e:=RestoreBackup(context.Background(),archive,target,backupOpt(t,s,key));result["public_restore_error"]=p12Error(e);result["restore_report"]=report
  if e!=nil {t.Fatal("public restore",e)}
  restored,e:=store.Open(filepath.Join(target,"state.sqlite"));if e!=nil {t.Fatal(e)};defer restored.Close()
  _,e=(&Service{DB:restored,Contracts:contracts}).CreateBackup(context.Background(),filepath.Join(c.Output,"rebackup"),key)
  result["public_rebackup_error"]=p12Error(e);if e!=nil {t.Fatal(e)}
  return
 }
 tx,err:=db.Begin();if err!=nil {t.Fatal(err)}
 transports, inventoryErr:=validateProviderInventory(tx,"","");tx.Rollback()
 streamErr:=validateModelStreamBackup(db)
 result["inventory_error"],result["stream_backup_error"]=p12Error(inventoryErr),p12Error(streamErr)
 result["inventory_count"]=len(transports);result["transports"]=transports
 fmt.Println("P12_ACTUAL "+string(Bytes(result)))
 if c.Mode=="baseline" {
  if inventoryErr!=nil || streamErr!=nil || len(transports)==0 {t.Fatal("unaltered prerequisite not valid",inventoryErr,streamErr,len(transports))}
 } else if inventoryErr==nil || streamErr==nil {
  t.Fatalf("UNEXPECTED_ACCEPT: inventory=%v stream_backup=%v inventory_count=%d",inventoryErr,streamErr,len(transports))
 }
}

func p12Error(e error) any { if e==nil{return nil};return e.Error() }
func p12State(t *testing.T,db *sql.DB) Object {
 t.Helper();out:=Object{}
 for name,q:=range map[string]string{
  "effects":"SELECT count(*) FROM resource_effects",
  "model_effect_rows":"SELECT count(*) FROM resource_effects WHERE json_extract(body,'$.payload.capability')='MODEL'",
  "dispatches":"SELECT count(*) FROM runtime_dispatches",
  "model_observations":"SELECT count(*) FROM client_control_receipts WHERE kind='MODEL_STREAM_OBSERVATION_V1'",
 } {var n int;if e:=db.QueryRow(q).Scan(&n);e!=nil {t.Fatal(name,e)};out[name]=n}
 return out
}
