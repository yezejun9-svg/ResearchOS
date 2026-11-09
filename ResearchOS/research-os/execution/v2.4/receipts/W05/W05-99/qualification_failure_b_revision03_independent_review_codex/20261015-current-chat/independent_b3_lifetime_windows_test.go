//go:build windows

package domain

import (
 "context"
 "database/sql"
 "errors"
 "os"
 "path/filepath"
 "reflect"
 "testing"
)

func TestIndependentB3PrivateHoldLifetimeAndRefusalRelease(t *testing.T) {
 c, route, r, calls := qualificationFailureLoopbackFixture(t)
 if err := c.RunAdmitted(context.Background(), route, r.run, r.lease); err == nil || calls.Load()!=1 {t.Fatalf("fixture closure: %v calls=%d",err,calls.Load())}
 epoch, err := Num(r.run,"lease_epoch"); if err != nil {t.Fatal(err)}
 var locator string
 if err:=r.f.db.QueryRow("SELECT journal_locator FROM runtime_dispatches WHERE project=? AND run=?",r.f.project,r.run["id"]).Scan(&locator);err!=nil {t.Fatal(err)}
 dir:=filepath.Join(c.config.DataRoot,"runtime-dispatches",locator)
 names:=[]string{"bridge.json","stdout.raw","stderr.raw","qualification-rejection-00000000000000000003.json"}
 hosts,err:=filepath.Glob(filepath.Join(dir,"effect-*.json"));if err!=nil||len(hosts)!=1 {t.Fatalf("host facts %v %v",hosts,err)}
 names=append(names,filepath.Base(hosts[0]))
 originals:=map[string][]byte{}
 for _,name:=range names {b,e:=os.ReadFile(filepath.Join(dir,name));if e!=nil {t.Fatal(e)};originals[name]=b}
 before:=independentB2Census(t,r.f.db)
 validate:=func(tx *sql.Tx)(qualificationFailureClosure,error){return r.f.s.validatedQualificationFailureTx(tx,r.f.project,Str(r.task,"id"),Str(r.run,"id"),epoch)}
 assertLocked:=func(t *testing.T) {
  t.Helper()
  for _,name:=range names {
   p:=filepath.Join(dir,name)
   if e:=os.WriteFile(p,originals[name],0600);e==nil {t.Fatalf("competing write accepted %s",name)}
   if e:=os.Rename(p,p+".moved");e==nil {t.Fatalf("competing rename accepted %s",name)}
   if e:=os.Remove(p);e==nil {t.Fatalf("competing delete accepted %s",name)}
  }
  for _,p:=range []string{dir,filepath.Dir(dir)} {if e:=os.Rename(p,p+"-moved");e==nil {t.Fatalf("namespace rename accepted %s",p)}}
 }
 assertReleased:=func(t *testing.T) {
  t.Helper()
  for _,name:=range names {
   p:=filepath.Join(dir,name)
   if e:=os.WriteFile(p,originals[name],0600);e!=nil {t.Fatalf("leaked write lock %s: %v",name,e)}
   if e:=os.Rename(p,p+".probe");e!=nil {t.Fatalf("leaked rename lock %s: %v",name,e)}
   if e:=os.Rename(p+".probe",p);e!=nil {t.Fatal(e)}
  }
 }
 for _,mode:=range []string{"commit","rollback"} {t.Run(mode,func(t *testing.T){
  tx,e:=r.f.db.Begin();if e!=nil {t.Fatal(e)}
  closure,e:=validate(tx);if e!=nil {tx.Rollback();t.Fatal(e)}
  defer closure.Close();defer tx.Rollback()
  if e:=closure.Check();e!=nil {t.Fatal(e)}
  assertLocked(t)
  if mode=="commit" {e=tx.Commit()}else{e=tx.Rollback()};if e!=nil {t.Fatal(e)}
  if e:=closure.Check();e!=nil {t.Fatal(e)}
  assertLocked(t)
  if e:=closure.Close();e!=nil {t.Fatal(e)}
  if e:=closure.Check();e==nil {t.Fatal("closed closure retained authority")}
  if e:=closure.Close();e!=nil {t.Fatal("repeat Close",e)}
  assertReleased(t)
  t.Log("all five original files and selected directory plus ancestor pinned before/after transaction; explicit Close released all")
 })}
 check:=func()error {
  tx,e:=r.f.db.Begin();if e!=nil{return e}
  cl,e:=validate(tx);if e==nil{e=cl.Check()}
  return errors.Join(e,tx.Rollback(),cl.Close())
 }
 for _,name:=range names {t.Run("missing_"+name,func(t *testing.T){
  p:=filepath.Join(dir,name)
  if e:=os.Rename(p,p+".missing");e!=nil{t.Fatal(e)}
  e:=check()
  restore:=os.Rename(p+".missing",p)
  if e==nil{t.Error("missing native file accepted")}
  if restore!=nil{t.Fatal("missing-file refusal leaked namespace lock",restore)}
  assertReleased(t)
  if e:=check();e!=nil {t.Fatal("restored baseline",e)}
 })}
 t.Run("canonical_rejection_whitespace",func(t *testing.T){
  name:="qualification-rejection-00000000000000000003.json";p:=filepath.Join(dir,name)
  if e:=os.WriteFile(p,append([]byte{' '},originals[name]...),0600);e!=nil{t.Fatal(e)}
  e:=check();if e==nil{t.Error("whitespace recoding accepted")}
  assertReleased(t)
  if e:=check();e!=nil{t.Fatal("restored baseline",e)}
 })
 t.Run("host_fact_bytes",func(t *testing.T){
  name:=names[4];p:=filepath.Join(dir,name)
  if e:=os.WriteFile(p,append(append([]byte(nil),originals[name]...),byte('x')),0600);e!=nil{t.Fatal(e)}
  if e:=check();e==nil{t.Error("changed MODEL Host fact accepted")}
  assertReleased(t)
  if e:=check();e!=nil{t.Fatal("restored baseline",e)}
 })
 for _,cut:=range []string{"project","task","run","epoch"} {t.Run("subject_"+cut,func(t *testing.T){
  tx,e:=r.f.db.Begin();if e!=nil{t.Fatal(e)}
  p,task,run,ep:=r.f.project,Str(r.task,"id"),Str(r.run,"id"),epoch
  switch cut {case "project":p+="-wrong";case "task":task+="-wrong";case "run":run+="-wrong";case "epoch":ep++}
  cl,e:=r.f.s.validatedQualificationFailureTx(tx,p,task,run,ep)
  tx.Rollback();cl.Close()
  if e==nil {t.Fatal("wrong subject accepted")}
  assertReleased(t)
 })}
 if !reflect.DeepEqual(before,independentB2Census(t,r.f.db))||calls.Load()!=1 {t.Fatal("cuts changed database or repeated MODEL")}
 t.Logf("full %d-table census unchanged; MODEL count one, rejected TOOL remains without effect",len(before))
}

