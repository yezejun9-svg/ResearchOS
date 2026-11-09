package domain

import (
 "bytes"
 "context"
 "database/sql"
 "encoding/json"
 "fmt"
 "maps"
 "testing"

 "researchos.local/research-os/internal/canonical"
)

// Independent schema-valid fixtures. They do not call a Host, API or old DB.
func reviewCodingDeliverySchemas(t *testing.T) *Contracts {
 t.Helper()
 result,err:=LoadContracts("../../spec/v2.0/contracts")
 if err!=nil {t.Fatal(err)}
 return result
}

func reviewCodingDeliveryPublicSubjects(t *testing.T) (codingDeliveryBinding,Object,Object,Object) {
 t.Helper()
 b:=codingDeliveryTestBinding(t)
 requirements:=[]any{Object{"entity_type":"Requirement","id":"review-requirement","revision":1,"content_hash":Hash("review requirement")}}
 inputs:=[]any{Object{"entity_type":"Artifact","id":"review-input","revision":1,"content_hash":Hash("review input")}}
 b.RequirementRefsHash=Hash(requirements)
 b.InputRefsHash=Hash(inputs)
 b.NoProgressRef="review-no-progress"
 b.NoProgressInputKey=Hash([]any{b.OriginProblemID,b.CandidateID,b.InputRefsHash})
 binding:=Object{"route":"MU_FORK","upstream_project_id":nil,"upstream_goal_id":nil,"upstream_task_id":nil}
 base:=func(id string)Object{return Object{"id":id,"project_id":b.Project,"revision":1,"created_at":"2026-11-04T00:00:00Z","updated_at":"2026-11-04T00:00:00Z"}}
 goal:=Merge(base(b.GoalID),Object{"title":"Review delivery","original_intent":"Schema-valid integrity fixture","scope":"PROJECT","status":"DRAFT","requirement_refs":requirements,"problem_ids":[]any{b.OriginProblemID},"task_ids":[]any{b.TaskID},"deliverables":[]any{"source bundle"},"acceptance_contract":codingDeliveryTestContract("coding.accepted-task-delivery-v1"),"budget_policy_id":"review-budget","outcome":nil,"acceptance_id":nil,"binding":binding})
 task:=Merge(base(b.TaskID),Object{"goal_id":b.GoalID,"title":"Review task","task_type":"coding","stage":"delivery","status":"DRAFT","dependency_task_ids":[]any{},"requirement_refs":requirements,"input_refs":inputs,"context_bundle_id":nil,"acceptance_contract":codingDeliveryTestContract("mu.turn-output-v1","coding.pure-scalar-delivery-v1"),"assigned_principal_id":nil,"active_run_id":nil,"output_artifact_ids":[]any{},"acceptance_id":nil,"blocking_conflict_ids":[]any{},"no_progress_record_id":b.NoProgressRef,"stop_policy":Object{"wall_time_seconds":60,"max_attempts":1,"max_parallel_runs":1,"stop_conditions":[]any{"fixture only"}},"binding":binding})
 record:=Merge(base(b.NoProgressRef),Object{"origin_problem_id":b.OriginProblemID,"candidate_id":b.CandidateID,"input_hash":b.InputRefsHash,"key_hash":b.NoProgressInputKey,"same_failure_count":2,"no_progress_iterations":1,"best_accepted_artifact_ref":nil,"last_effective_progress_at":nil,"resume_conditions":[]any{"new evidence"},"status":"ACTIVE"})
 schemas:=reviewCodingDeliverySchemas(t)
 for kind,value:=range map[string]Object{"Goal":goal,"Task":task,"NoProgressRecord":record}{
  if err:=schemas.Validate(kind,value);err!=nil {t.Fatalf("independent positive %s is not public-schema-valid: %v",kind,err)}
 }
 if _,ok:=task["origin_problem_id"];ok {t.Fatal("fixture leaked origin into Task")}
 if _,ok:=task["candidate_id"];ok {t.Fatal("fixture leaked candidate into Task")}
 if err:=b.validate();err!=nil {t.Fatal(err)}
 return b,goal,task,record
}

func reviewCodingDeliveryPutPublic(t *testing.T,db *sql.DB,b codingDeliveryBinding,goal,task,record Object) {
 t.Helper()
 for kind,value:=range map[string]Object{"Goal":goal,"Task":task,"NoProgressRecord":record}{
  if value==nil {continue}
  if _,err:=db.Exec(`INSERT INTO domain_objects(project,kind,id,revision,body) VALUES(?,?,?,1,?)`,b.Project,kind,value["id"],string(Bytes(value)));err!=nil {t.Fatal(err)}
 }
}

func TestReviewCodingDeliveryBindingPublicTaskNoProgressPositive(t *testing.T) {
 b,goal,task,record:=reviewCodingDeliveryPublicSubjects(t)
 db,_:=codingDeliveryTestDB(t,true)
 reviewCodingDeliveryPutPublic(t,db,b,goal,task,record)
 tx,err:=db.BeginTx(context.Background(),nil);if err!=nil {t.Fatal(err)}
 defer tx.Rollback()
 if err=insertCodingDeliveryBindingTx(context.Background(),tx,reviewCodingDeliverySchemas(t),b,b);err!=nil {t.Fatalf("a schema-valid public Task follows its NoProgressRecord, not nonexistent Task origin/candidate fields: %v",err)}
 if err=tx.Commit();err!=nil {t.Fatal(err)}
 if err=codingDeliveryTestRead(t,db,b);err!=nil {t.Fatal(err)}
 var actualRecord string
 if err=db.QueryRow(`SELECT body FROM domain_objects WHERE project=? AND kind='NoProgressRecord' AND id=?`,b.Project,b.NoProgressRef).Scan(&actualRecord);err!=nil || actualRecord!=string(Bytes(record)) {t.Fatalf("binding insert/read rewrote existing failure/progress history: %v",err)}
}

func TestReviewCodingDeliveryBindingNoProgressRelationNegatives(t *testing.T) {
 for _,kind:=range []string{"missing-record","foreign-record-id","foreign-project","origin","candidate","input-hash","self-consistent-foreign-key","goal-problem","goal-task","fake-task-extra-fields"}{
  t.Run(kind,func(t *testing.T){
   b,goal,task,record:=reviewCodingDeliveryPublicSubjects(t)
   db,_:=codingDeliveryTestDB(t,true)
   switch kind {
   case "missing-record":record=nil
   case "foreign-record-id":task["no_progress_record_id"]="foreign-record"
   case "foreign-project":record["project_id"]="foreign-project"
   case "origin":record["origin_problem_id"]="foreign-origin"
   case "candidate":record["candidate_id"]="foreign-candidate"
   case "input-hash":record["input_hash"]=Hash("foreign inputs")
   case "self-consistent-foreign-key":record["key_hash"]=Hash([]any{b.OriginProblemID,b.CandidateID,Hash("foreign inputs")});b.NoProgressInputKey=Str(record,"key_hash")
   case "goal-problem":goal["problem_ids"]=[]any{"other-problem"}
   case "goal-task":goal["task_ids"]=[]any{"other-task"}
   case "fake-task-extra-fields":task["origin_problem_id"]=b.OriginProblemID;task["candidate_id"]=b.CandidateID;record=nil
   }
   reviewCodingDeliveryPutPublic(t,db,b,goal,task,record)
   tx,err:=db.BeginTx(context.Background(),nil);if err!=nil {t.Fatal(err)}
   defer tx.Rollback()
   if err=insertCodingDeliveryBindingTx(context.Background(),tx,reviewCodingDeliverySchemas(t),b,b);err==nil {t.Fatalf("invalid %s relation accepted",kind)}
  })
 }
}

func TestReviewCodingDeliveryBindingRequiredCommandIdentity(t *testing.T) {
 mandatory:=[]string{"mu.turn-output-v1","coding.pure-scalar-delivery-v1"}
 valid:=codingDeliveryTestContract(mandatory...)
 if err:=codingDeliveryContractIntegrity(reviewCodingDeliverySchemas(t),valid,Str(valid,"contract_hash"),mandatory...);err!=nil {t.Fatalf("valid control failed: %v",err)}
 for _,index:=range []int{0,1}{
  t.Run(fmt.Sprint("wrong-command-",index),func(t *testing.T){
   c:=codingDeliveryTestContract(mandatory...)
   c["checks"].([]any)[index].(map[string]any)["command_key"]="orchestration.json-equals"
   c["contract_hash"]=contractDigest(c)
   if err:=reviewCodingDeliverySchemas(t).Validate("AcceptanceContract",c);err!=nil {t.Fatalf("attack must remain public-schema-valid: %v",err)}
   if err:=codingDeliveryContractIntegrity(reviewCodingDeliverySchemas(t),c,Str(c,"contract_hash"),mandatory...);err==nil {t.Fatal("display check_id hid replacement of mandatory execution command_key")}
  })
 }
 c:=codingDeliveryTestContract(mandatory...)
 c["checks"].([]any)[0].(map[string]any)["check_id"]="mu-turn-output"
 c["checks"].([]any)[1].(map[string]any)["check_id"]="pure-delivery-output"
 c["contract_hash"]=contractDigest(c)
 if err:=codingDeliveryContractIntegrity(reviewCodingDeliverySchemas(t),c,Str(c,"contract_hash"),mandatory...);err!=nil {t.Fatalf("valid checker command identity should not depend on arbitrary display check_id: %v",err)}
 for _,required:=range []bool{false,true}{
  t.Run(fmt.Sprint("duplicate-command-required-",required),func(t *testing.T){
   c:=codingDeliveryTestContract(mandatory...)
   first:=c["checks"].([]any)[0].(map[string]any)
   duplicate:=Object{};for key,value:=range first {duplicate[key]=value};duplicate["check_id"]="different-label-same-command";duplicate["required"]=required
   c["checks"]=append(c["checks"].([]any),duplicate);c["contract_hash"]=contractDigest(c)
   if err:=reviewCodingDeliverySchemas(t).Validate("AcceptanceContract",c);err!=nil {t.Fatalf("duplicate attack must remain schema-valid: %v",err)}
   if err:=codingDeliveryContractIntegrity(reviewCodingDeliverySchemas(t),c,Str(c,"contract_hash"),mandatory...);err==nil {t.Fatal("ambiguous duplicate mandatory command accepted")}
  })
 }
}

func TestReviewCodingDeliveryBindingClosedDTOExactFieldNames(t *testing.T) {
 b:=codingDeliveryTestBinding(t)
 raw,_,err:=codingDeliveryBindingBytes(b);if err!=nil {t.Fatal(err)}
 if _,err=decodeCodingDeliveryBinding(raw);err!=nil {t.Fatalf("valid canonical control rejected: %v",err)}
 var fields map[string]json.RawMessage
 if err=json.Unmarshal(raw,&fields);err!=nil {t.Fatal(err)}
 originalCount:=len(fields)
 fields["Owner_Host"]=fields["owner_host"];delete(fields,"owner_host")
 if len(fields)!=originalCount {t.Fatal("attack must preserve arity")}
 unknown,err:=canonical.JSON(Bytes(fields));if err!=nil {t.Fatal(err)}
 if _,err=decodeCodingDeliveryBinding(unknown);err==nil {t.Fatal("same-length unknown/case alias passed closed DTO")}
 escaped:=bytes.Replace(raw,[]byte(`"owner_root":`),[]byte(`"owner_root":"forged","\u006fwner_root":`),1)
 if bytes.Equal(escaped,raw) {t.Fatal("escaped-duplicate attack did not change bytes")}
 if _,err=decodeCodingDeliveryBinding(escaped);err==nil {t.Fatal("escaped duplicate identity accepted")}
}

func TestReviewCodingDeliveryBindingOriginIndependentDimensions(t *testing.T) {
 b,_,_,_:=reviewCodingDeliveryPublicSubjects(t)
 for _,kind:=range []string{"problem","requirements","business-input","suite-version","suite-hash"}{
  origin:=b.origin()
  switch kind {case "problem":origin.OriginalProblemAnchor="other-original-problem";case "requirements":origin.RequirementContentHash=Hash("other requirements");case "business-input":origin.BusinessInputContentHash=Hash("other original inputs");case "suite-version":origin.SuiteRef="coding.pure-scalar-bundle-v2";case "suite-hash":origin.SuiteHash=Hash("other suite")}
  hash,err:=codingDeliveryBusinessAnchor(origin)
  if err!=nil || hash==b.BusinessAnchor {t.Fatalf("original causal dimension %s not bound: %v",kind,err)}
 }
 other:=b;other.Project="another-project";other.OwnerPrincipal="another-owner";other.OwnerRoot="another-root";other.GoalID="another-goal";other.TaskID="another-task";other.ApprovalRef="another-approval";other.CommandID="another-command";other.RequirementRefsHash=Hash("reuploaded refs");other.InputRefsHash=Hash("different storage refs")
 hash,err:=codingDeliveryBusinessAnchor(other.origin());if err!=nil || hash!=b.BusinessAnchor {t.Fatalf("storage/permission/new-object rename laundered original anchor: %v",err)}
}

func TestReviewCodingDeliveryBindingContextCancellationAndRollback(t *testing.T) {
 b,goal,task,record:=reviewCodingDeliveryPublicSubjects(t)
 db,_:=codingDeliveryTestDB(t,true)
 reviewCodingDeliveryPutPublic(t,db,b,goal,task,record)
 tx,err:=db.BeginTx(context.Background(),nil);if err!=nil {t.Fatal(err)}
 canceled,cancel:=context.WithCancel(context.Background());cancel()
 if err=insertCodingDeliveryBindingTx(canceled,tx,reviewCodingDeliverySchemas(t),b,b);err==nil {t.Fatal("canceled insert accepted")}
 if err=tx.Rollback();err!=nil {t.Fatal(err)}
 if err=insertCodingDeliveryBindingTx(context.Background(),tx,reviewCodingDeliverySchemas(t),b,b);err==nil {t.Fatal("rolled-back transaction accepted")}
 var count int
 if err=db.QueryRow(`SELECT count(*) FROM coding_delivery_bindings`).Scan(&count);err!=nil || count!=0 {t.Fatalf("canceled/rolled-back helper left claims: %d %v",count,err)}
}

func TestReviewCodingDeliveryBindingRealCatalogDependency(t *testing.T) {
 _,goal,task,record:=reviewCodingDeliveryPublicSubjects(t)
 real:=reviewCodingDeliverySchemas(t)
 for kind,value:=range map[string]Object{"Goal":goal,"Task":task,"NoProgressRecord":record}{
  if err:=codingDeliveryPublishedIntegrity(real,kind,value);err!=nil {t.Fatalf("real loaded catalog valid %s control failed: %v",kind,err)}
  if err:=codingDeliveryPublishedIntegrity(nil,kind,value);err==nil {t.Fatalf("nil catalog accepted %s",kind)}
  if err:=codingDeliveryPublishedIntegrity(&Contracts{},kind,value);err==nil {t.Fatalf("empty catalog accepted %s",kind)}
  catalogCopy:=*real;catalogCopy.Schemas=maps.Clone(real.Schemas);delete(catalogCopy.Schemas,kind)
  if err:=codingDeliveryPublishedIntegrity(&catalogCopy,kind,value);err==nil {t.Fatalf("missing primary schema accepted %s",kind)}
 }
 for kind,value:=range map[string]Object{"Goal":goal,"Task":task}{
  catalogCopy:=*real;catalogCopy.Schemas=maps.Clone(real.Schemas);delete(catalogCopy.Schemas,kind+"V24")
  if err:=codingDeliveryPublishedIntegrity(&catalogCopy,kind,value);err==nil {t.Fatalf("missing true MU_FORK selected schema silently fell back for %s",kind)}
 }
}
