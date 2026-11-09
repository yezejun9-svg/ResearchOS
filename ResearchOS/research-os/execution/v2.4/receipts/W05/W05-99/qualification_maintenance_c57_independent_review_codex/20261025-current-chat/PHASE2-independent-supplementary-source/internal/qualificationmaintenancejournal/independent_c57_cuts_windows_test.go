//go:build windows
package qualificationmaintenancejournal
import("os";"path/filepath";"testing";"encoding/json";"crypto/sha256";"fmt";"sort")
func independentC57JournalBytes(t *testing.T,dir string) string{
 t.Helper();entries,e:=os.ReadDir(dir);if e!=nil{t.Fatal(e)};parts:=[]string{}
 for _,entry:=range entries{if entry.IsDir(){parts=append(parts,entry.Name()+"/");continue};raw,e:=os.ReadFile(filepath.Join(dir,entry.Name()));if e!=nil{t.Fatal(e)};parts=append(parts,fmt.Sprintf("%s:%x",entry.Name(),sha256.Sum256(raw)))}
 sort.Strings(parts);raw,_:=json.Marshal(parts);return string(raw)
}
func TestIndependentC57JournalCrashPrefixes(t *testing.T){
 cases:=[]string{"empty_operation","plan_only","partial_plan","partial_begin","wrong_sequence","wrong_event_hash","not_applied","committed_observed","durable"}
 for _,name:=range cases{t.Run(name,func(t *testing.T){
  root,plan,raw:=qualificationJournalFixture(t)
  digest,e:=StartQualification(root,raw);if e!=nil{t.Fatal(e)}
  dir:=filepath.Join(root,"host",QualificationNamespace,plan.OperationID)
  events,e:=filepath.Glob(filepath.Join(dir,"0001-*.json"));if e!=nil||len(events)!=1{t.Fatalf("event fixture %v %v",events,e)}
  switch name{
  case "empty_operation":if e=os.Remove(events[0]);e!=nil{t.Fatal(e)};if e=os.Remove(filepath.Join(dir,"plan.json"));e!=nil{t.Fatal(e)}
  case "plan_only":if e=os.Remove(events[0]);e!=nil{t.Fatal(e)}
  case "partial_plan":if e=os.WriteFile(filepath.Join(dir,"plan.json"),raw[:len(raw)/2],0600);e!=nil{t.Fatal(e)}
  case "partial_begin":b,e:=os.ReadFile(events[0]);if e!=nil{t.Fatal(e)};if e=os.WriteFile(events[0],b[:len(b)/2],0600);e!=nil{t.Fatal(e)}
  case "wrong_sequence":if e=os.Rename(events[0],filepath.Join(dir,"0002-BEGIN.json"));e!=nil{t.Fatal(e)}
  case "wrong_event_hash":b,e:=os.ReadFile(events[0]);if e!=nil{t.Fatal(e)};var obj map[string]any;if e=json.Unmarshal(b,&obj);e!=nil{t.Fatal(e)};obj["previous"]="tamper";b,_=json.Marshal(obj);if e=os.WriteFile(events[0],b,0600);e!=nil{t.Fatal(e)}
  case "not_applied":if e=AppendQualification(root,plan.OperationID,digest,"CLASSIFIED_NOT_APPLIED","");e!=nil{t.Fatal(e)}
  case "committed_observed","durable":var full map[string]any;if e=json.Unmarshal(plan.FullPlan,&full);e!=nil{t.Fatal(e)};outcome:=full["outcome_hash"].(string);if e=AppendQualification(root,plan.OperationID,digest,"DB_COMMITTED_OBSERVED",outcome);e!=nil{t.Fatal(e)};if name=="durable"{if e=AppendQualification(root,plan.OperationID,digest,"DURABLE",outcome);e!=nil{t.Fatal(e)}}
  }
  before:=independentC57JournalBytes(t,dir)
  ordinaryErr:=CheckOrdinary(root)
  if name=="durable"{if ordinaryErr!=nil{t.Fatal(ordinaryErr)}}else if ordinaryErr==nil{t.Fatalf("%s ordinary startup admitted",name)}
  _,status,ownErr:=OpenOwnInspection(root,QualificationNamespace,plan.OperationID,digest)
  coherent:=name=="not_applied"||name=="committed_observed"||name=="durable"
  if coherent&&ownErr!=nil{t.Fatal(ownErr)};if !coherent&&ownErr==nil{t.Fatalf("%s own inspection admitted corrupted prefix",name)}
  after:=independentC57JournalBytes(t,dir);if before!=after{t.Fatal("inspection altered append-only evidence")}
  if _,e=os.Stat(plan.Database);!os.IsNotExist(e){t.Fatalf("journal inspection created database: %v",e)}
  t.Logf("JOURNAL_PREFIX case=%s ordinary_blocked=%t own_inspection=%t state=%s evidence_unchanged=true DB_absent=true inventory=%s",name,ordinaryErr!=nil,ownErr==nil,status.State,before)
 })}
}
