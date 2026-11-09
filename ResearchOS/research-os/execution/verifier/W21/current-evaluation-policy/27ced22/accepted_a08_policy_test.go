package domain

import (
 "encoding/json"
 "fmt"
 "os"
 "testing"
 "researchos.local/research-os/adapters/decision"
 "researchos.local/research-os/adapters/protectedstore"
)

// Public accepted responses only. No service query, private dataset, or provider invocation.
func TestIndependentW21AcceptedA08PolicyReferences(t *testing.T) {
 root:=`D:/作品集/ResearchOS/research-os/execution/verifier/W11/product-live-591d16e/`
 read:=func(name string) Object {t.Helper();b,e:=os.ReadFile(root+name);if e!=nil {t.Fatal(e)};o,e:=Decode(b);if e!=nil {t.Fatal(e)};return o}
 clone:=func(o Object)Object{x,e:=Decode(Bytes(o));if e!=nil {t.Fatal(e)};return x}
 assert:=func(id string,ok bool){t.Helper();status:="PASS";if !ok {status="FAIL"};fmt.Println("R03_ASSERTION "+string(Bytes(Object{"assertion_id":id,"status":status,"scope":"PUBLIC_ACCEPTED_AGGREGATE_PURE_BINDING_ONLY"})));if !ok {t.Fatal(id)}}
 for _,language:=range []string{"zh","zh-en"} {t.Run(language,func(t *testing.T){
   q:=read(language+"-qualification-before.response.json")
   receipt:=read(language+"-acceptance-persisted.response.json")
   result:=read(language+"-qualification-persisted.response.json")
   artifact:=read(language+"-public-summary-artifact.response.json")
   aggregate:=read(language+"-public-summary-content.response.json")
   var summary protectedstore.SafeSummary
   if e:=json.Unmarshal(Bytes(aggregate),&summary);e!=nil {t.Fatal(e)}
   assert(language+"-SAFE-SUMMARY",summary.Validate()==nil)
   assert(language+"-FAILED-ADVISORY-NONE",summary.Frozen!=nil&&summary.Frozen.Qualification=="FAILED"&&summary.MaximumMode=="ADVISORY"&&summary.Frozen.AutomaticAuthority=="NONE"&&summary.Frozen.RunState=="COMPLETED")
   assert(language+"-ORIGINAL-AGGREGATE",summary.Total==30&&summary.Correct==13&&summary.Abstain==17&&summary.FalseAccept==0&&summary.FalseReject==0)
   assert(language+"-PUBLIC-SUMMARY-BYTES",Digest(decision.Encode(summary))==artifact["content_hash"]&&Hash(receipt["artifact_refs"])==Hash([]any{Ref(artifact,"Artifact")})&&artifact["access_class"]=="PROJECT")
   assert(language+"-DRAFT-TO-FAILED",q["status"]=="DRAFT"&&result["status"]=="FAILED"&&result["maximum_mode"]=="ADVISORY"&&result["jev_called"]==true&&result["acceptance_id"]==receipt["id"]&&qualificationContract(q)==qualificationContract(result))
   authors:=Arr(receipt,"executor_principal_ids");verifier:=Str(receipt,"verifier_principal_id");policy:=receipt["policy_revision"];refs:=receipt["artifact_refs"]
   assert(language+"-CURRENT-RECEIPT-BINDING",qualificationReceiptBinding(q,receipt,authors,verifier,policy,refs)==nil)
   assert(language+"-FROZEN-THRESHOLDS",q["thresholds_hash"]==QualificationThresholdsHash()&&q["thresholds_frozen_at"]==summary.Frozen.FrozenAt)
   found:=false
   for _,key:=range summary.Frozen.Keys {if key.Scope.Language!=language {continue};found=true
     assert(language+"-EXACT-FIVE-DIMENSION-KEY",Hash(q["scope"])==Hash(key.Scope)&&key.Scope.TaskType=="evidence-validity"&&key.Scope.Provider=="typesafe"&&key.Scope.ModelRevision=="jev-1.13.0"&&key.Scope.RubricRevision=="objective-source-records-v1")
     assert(language+"-INSUFFICIENT-PER-KEY",key.DevelopmentCount==30&&key.Planned==15&&Hash(q["total_case_count"])==Hash(45)&&Hash(q["holdout_case_count"])==Hash(15))
     assert(language+"-RESULT-RATES",Hash(result["critical_false_accept_count"])==Hash(key.CriticalFalseAccept)&&Hash(result["false_accept_rate"])==Hash(float64(key.FalseAccept)/float64(key.Planned))&&Hash(result["false_reject_rate"])==Hash(float64(key.FalseReject)/float64(key.PositiveLabelCount))&&Hash(result["abstain_rate"])==Hash(float64(key.Abstain)/float64(key.Planned))&&Hash(result["test_receipt_refs"])==Hash(refs))
   };assert(language+"-KEY-PRESENT",found)
   for _,field:=range []string{"task_type","language","provider","model_revision","rubric_revision"} {
     altered:=clone(q);scope:=altered["scope"].(map[string]any);scope[field]=Str(scope,field)+"-different"
     assert(language+"-NO-INHERIT-"+field,qualificationContract(altered)!=qualificationContract(q)&&qualificationReceiptBinding(altered,receipt,authors,verifier,policy,refs)!=nil)
   }
   mutations:=map[string]func(Object){
    "INPUT-REF":func(r Object){r["input_refs"]=[]any{}},
    "POLICY":func(r Object){r["policy_revision"]=999},
    "VERIFIER":func(r Object){r["verifier_principal_id"]="different-verifier"},
    "AUTHOR":func(r Object){r["executor_principal_ids"]=[]any{verifier}},
    "MEASUREMENT":func(r Object){r["measurement_mode"]="FIXTURE"},
    "MISSING-CHECK":func(r Object){r["checks"]=Arr(r,"checks")[:2]},
    "FAILED-CHECK":func(r Object){Arr(r,"checks")[0].(map[string]any)["status"]="FAIL"},
    "CHECK-EVIDENCE":func(r Object){Arr(r,"checks")[0].(map[string]any)["evidence_refs"]=[]any{}},
   }
   for name,mutate:=range mutations {r:=clone(receipt);mutate(r);r["receipt_hash"]=Receipt(r);assert(language+"-REJECT-REHASHED-"+name,qualificationReceiptBinding(q,r,authors,verifier,policy,refs)!=nil)}
 })}
}
