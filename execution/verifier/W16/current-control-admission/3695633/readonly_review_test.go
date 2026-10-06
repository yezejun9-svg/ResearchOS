//go:build windows

package domain

import (
 "context"
 "database/sql"
 "encoding/json"
 "os"
 "sort"
 "strings"
 "testing"
 "time"
 "researchos.local/research-os/adapters/protectedstore"
 "researchos.local/research-os/evaluation/evolution"
 "researchos.local/research-os/ops/supervisor"
)

// An overlay-only reviewer. No producer, service startup, store write, or original DB write.
func TestIndependentCurrentPersistedReview(t *testing.T) {
 ctx:=context.Background()
 must:=func(e error){t.Helper();if e!=nil {t.Fatal(e)}}
 check:=func(b bool,label string){t.Helper();if !b {t.Fatal(label)}}
 source:=`D:/作品集/ResearchOS/research-os/.local/worktrees/control-business-proof`
 output:=`D:/作品集/ResearchOS/research-os/execution/verifier/W16/current-control-admission/3695633/readonly-result.json`
 readJSON:=func(p string) Object {b,e:=os.ReadFile(p);must(e);o,e:=Decode(b);must(e);return o}
 receipt:=readJSON(source+`/execution/receipts/W16/current-control-admission/attempt-10-first-evaluation/current-control-native.json`)
 loc:=readJSON(source+`/execution/receipts/W16/current-control-admission/attempt-10-first-evaluation/private-locators.json`)
 project:=Str(receipt["candidate"].(map[string]any),"project_id")
 store,e:=protectedstore.OpenCanary(Str(loc,"canary_store"));must(e);defer store.Close()
 desc,e:=store.Describe(ctx,project,"ps1:8e776706c93226d15055839353649c5a");must(e)
 raw,e:=store.Read(ctx,desc);must(e)
 check(Digest(raw)=="sha256:52e11691cd7d336868d285bcf403afc5ae26e88d8e8008d4959cfbd209491a9c","proof bytes")
 proof,e:=Decode(raw);must(e)
 check(proof["project_id"]==project && proof["normal_release_authorized"]==false && proof["positive_gain"]==false,"proof scope")
 result:=Object{"scope":"SYNTHETIC_FIXTURE_PERSISTED_RECOMPUTATION_ONLY","proof_hash":Digest(raw),"native_event_authenticity_now":"UNVERIFIED","current_owner_now":"UNVERIFIED_STOPPED","store_mutation":false,"native_execution":false}
 databases:=map[string]*sql.DB{}; data:=map[string]upgradeData{}; snapshots:=map[string]evolution.ControlPrivateSnapshot{}
 summary:=[]any{}
 for _,stage:=range []string{"b0","g0","g1"} {
   var snapshot evolution.ControlPrivateSnapshot;must(json.Unmarshal(Bytes(proof[stage]),&snapshot))
   check(snapshot.Stage==strings.ToUpper(stage)&&snapshot.SessionID==proof["session_id"],"snapshot session/stage")
   _,db,e:=controlReadPrivateSnapshot(ctx,store,project,snapshot);must(e);defer db.Close()
   databases[stage]=db;snapshots[stage]=snapshot
   data[stage],e=controlCurrentRows(db);must(e)
   summary=append(summary,Object{"stage":snapshot.Stage,"size":snapshot.Size,"parts":len(snapshot.Parts),"hash":snapshot.Hash,"generation":snapshot.Generation,"recomputed":true})
 }
 result["snapshots"]=summary
 original,e:=os.ReadFile(Str(loc,"database"));must(e);originalHash:=Digest(original)
 wal,e:=os.Stat(Str(loc,"database")+"-wal");must(e);check(wal.Size()==0,"nonempty original WAL")
 db,e:=controlSnapshotMemoryDB(ctx,original);must(e);defer db.Close()
 generation,e:=evolution.ControlDatabaseHash(db);must(e);check(generation==snapshots["g1"].Generation,"original generation != G1")
 result["original_database_hash"]=originalHash;result["original_matches_g1_generation"]=true
 tx0,e:=databases["g0"].BeginTx(ctx,nil);must(e);defer tx0.Rollback()
 tx1,e:=databases["g1"].BeginTx(ctx,nil);must(e);defer tx1.Rollback()
 candidate:=Str(receipt["candidate"].(map[string]any),"id")
 x,e:=load(tx0,project,"SystemCandidate",candidate);must(e)
 runID:=Str(receipt["acceptance"].(map[string]any),"run_id")
 run,e:=load(tx0,project,"Run",runID);must(e);task,e:=load(tx0,project,"Task",Str(run,"task_id"));must(e)
 contracts,e:=LoadContracts(source+"/spec/v2.0/contracts");must(e)
 s:=&Service{DB:databases["g1"],Contracts:contracts}
 h,e:=s.evolutionCurrent(tx0,project,x);must(e)
 state,e:=singleton(tx0,project,"ProjectState");must(e)
 frozen,present,e:=evolutionHoldoutEntry(tx0,project,candidate,"HOLDOUT_FROZEN");must(e);check(present,"holdout frozen")
 n:=&controlCurrentNames{Project:project,Candidate:candidate,Task:Str(task,"id"),Run:runID,Experiment:Str(x,"experiment_id"),Goal:Str(task,"goal_id"),Retention:Str(task,"no_progress_record_id"),State:Str(state,"id"),Verifier:Str(frozen,"verifier_id"),Executor:Str(run,"executor_principal_id"),Release:Str(h,"release_principal"),Rows:data["g0"],Holdout:Hash(frozen),Plan:Hash(evolutionPlan(x)),Contract:Hash(task["acceptance_contract"])}
 n.Epoch,e=Num(run,"lease_epoch");must(e);n.Schema,e=controlSchemaHash(tx0);must(e)
 must(tx0.QueryRow("SELECT creator FROM evolution_candidates WHERE project=? AND candidate=?",project,candidate).Scan(&n.Author))
 a:=&currentControlAuthority{s:s,store:store,id:Str(proof,"session_id"),project:project,ownerID:"current-control-owner",frozen:n,b0:snapshots["b0"],g0:snapshots["g0"]}
 must(json.Unmarshal(Bytes(proof["owner"]),&a.owner));must(json.Unmarshal(Bytes(proof["source_provenance"]),&a.provenance))
 a.stableRef=x["stable_artifact_ref"].(map[string]any);a.candidateRef=x["candidate_artifact_ref"].(map[string]any)
 must(a.independentVerifier(tx0,n.Verifier,n))
 prep,e:=a.validatePreparation(tx0,data["b0"],n);must(e)
 check(Hash(prep)==Hash(proof["preparation_delta"]),"preparation delta mismatch")
 delta,e:=a.validateNamedDelta(tx1);must(e)
 check(Hash(delta)==Hash(proof["evaluation_delta"]),"evaluation delta mismatch")
 result["preparation_delta"]=Object{"count":len(prep),"hash":Hash(prep),"whitelist_recomputed":true}
 result["evaluation_delta"]=Object{"count":len(delta),"hash":Hash(delta),"whitelist_recomputed":true}
 // Independently assert every authority table except the exact one-run grant is preserved.
 authNames:=[]string{};for name:=range data["b0"] {if strings.HasPrefix(name,"auth_")||strings.HasPrefix(name,"remote_")||name=="orchestration_identity" {authNames=append(authNames,name)}};sort.Strings(authNames)
 authChanges:=0
 for _,d:=range prep {if strings.HasPrefix(d.Table,"auth_")||strings.HasPrefix(d.Table,"remote_")||d.Table=="orchestration_identity" {authChanges++;check(d.Table=="auth_grants"&&d.BeforeHash=="","unexpected preparation authority delta")}}
 for _,name:=range authNames {check(controlRowSetHash(data["g0"][name])==controlRowSetHash(data["g1"][name]),"G0/G1 authority drift")}
 result["authority_tables"]=len(authNames);result["preparation_authority_additions"]=authChanges
 result["historical_verifier_role_root_separation"]=true
 build:=readJSON(source+`/execution/receipts/W16/current-control-admission/attempt-10-first-evaluation/actual-build.json`)
 image,e:=os.ReadFile(Str(build,"image_path"));must(e)
 _,code,e:=s.evolutionBytes(tx1,project,a.candidateRef);must(e)
 check(Digest(image)==Digest(code)&&Digest(image)==a.owner.ImageHash&&Digest(image)==build["binary_hash"],"image/CODE/protected owner bytes")
 result["image_code_owner_hash"]=Digest(image)
 acceptance,e:=load(tx1,project,"AcceptanceReceipt",Str(receipt["acceptance"].(map[string]any),"id"));must(e)
 check(Receipt(acceptance)==acceptance["receipt_hash"]&&acceptance["verdict"]=="PASS","acceptance receipt")
 finalCandidate,e:=load(tx1,project,"SystemCandidate",candidate);must(e);check(finalCandidate["status"]=="REJECTED","no-gain gate")
 finalExperiment,e:=load(tx1,project,"Experiment",n.Experiment);must(e);check(finalExperiment["outcome"]=="NO_IMPROVEMENT","no improvement")
 check(Hash(acceptance)==Hash(receipt["acceptance"])&&Hash(finalCandidate)==Hash(receipt["candidate"])&&Hash(finalExperiment)==Hash(receipt["experiment"]),"persisted normal result != public receipt")
 result["acceptance_hash_recomputed"]=true;result["normal_gate"]="REJECTED";result["experiment_outcome"]="NO_IMPROVEMENT"
 var recordRaw string;must(tx1.QueryRow("SELECT body FROM evolution_executions WHERE project=? AND candidate=? AND phase='REGRESSION'",project,candidate).Scan(&recordRaw))
 record,e:=Decode([]byte(recordRaw));must(e);check(Receipt(record)==record["receipt_hash"]&&record["receipt_hash"]==proof["execution_hash"],"execution receipt hash")
 recomputed,outcome,e:=recomputeExperiment(finalExperiment,record["observation"].(map[string]any));must(e)
 check(Hash(recomputed)==Hash(finalExperiment["results"])&&outcome==finalExperiment["outcome"],"experiment recomputation")
 result["experiment_recomputed"]=true
 _,suite,e:=s.controlHostInputs(tx1,project,h);must(e)
 stableSource,candidateSource,e:=s.controlBuildSources(tx1,project,x,h);must(e)
 var publicProof supervisor.ControlProof;must(evolution.StrictControlJSON(Bytes(record["control_proof"]),&publicProof))
 publicVerdict,e:=supervisor.CheckControl(publicProof,suite.Inputs,suite.Labels,n.Plan,Str(record,"baseline_hash"),Str(record,"candidate_hash"),stableSource,candidateSource,evolutionSuiteHash(h));must(e)
 privateEntry,present,e:=evolutionHoldoutEntry(tx1,project,candidate,"HOLDOUT_EVALUATED");must(e);check(present,"private evaluated entry")
 privateBytes:=func(ref map[string]any) []byte {
   artifact,e:=load(tx1,project,"Artifact",Str(ref,"id"));must(e)
   descriptor,e:=store.Describe(ctx,project,Str(artifact,"storage_key"));must(e)
   check(descriptor.Hash==ref["content_hash"]&&descriptor.Hash==artifact["content_hash"],"private descriptor binding")
   b,e:=store.Read(ctx,descriptor);must(e);return b
 }
 inputsRaw:=privateBytes(frozen["input_ref"].(map[string]any));labelsRaw:=privateBytes(frozen["labels_ref"].(map[string]any));privateRaw:=privateBytes(privateEntry["proof_ref"].(map[string]any))
 check(Digest(inputsRaw)==frozen["inputs_hash"]&&Digest(labelsRaw)==frozen["labels_hash"]&&Digest(privateRaw)==privateEntry["proof_hash"],"private raw binding")
 var inputs evolution.ControlInputs;var labels evolution.ControlLabels;var privateProof supervisor.ControlProof
 must(evolution.StrictControlJSON(inputsRaw,&inputs));must(evolution.StrictControlJSON(labelsRaw,&labels));must(evolution.StrictControlJSON(privateRaw,&privateProof))
 must(evolution.ValidateControlDataset(inputs,labels))
 privateVerdict,e:=supervisor.CheckControl(privateProof,inputs,labels,n.Plan,Str(record,"baseline_hash"),Str(record,"candidate_hash"),stableSource,candidateSource,evolutionSuiteHash(h));must(e)
 privateSummary:=controlHoldoutSummary(privateVerdict)
 check(Hash(privateSummary)==privateEntry["summary_hash"]&&Hash(privateSummary)==Hash(record["holdout_summary"])&&Digest(privateRaw)==record["holdout_proof_hash"],"private summary binding")
 check(!publicVerdict.Gain&&!privateVerdict.Gain&&publicVerdict.RequiredPassed&&record["improved"]==false&&record["required_passed"]==true,"derived regression verdict")
 rows:=Arr(record["observation"].(map[string]any),"observations");check(len(rows)==1,"observation count")
 metric:=rows[0].(map[string]any);check(Hash(metric["baseline"])==Hash(publicVerdict.BaselineValues)&&Hash(metric["candidate"])==Hash(publicVerdict.CandidateValues),"raw public values")
 result["public_proof_recomputed"]=Object{"pairs":len(publicProof.Pairs),"required_passed":publicVerdict.RequiredPassed,"gain":publicVerdict.Gain}
 result["private_proof_recomputed"]=Object{"pairs":len(privateProof.Pairs),"required_passed":privateVerdict.RequiredPassed,"gain":privateVerdict.Gain,"summary_hash":Hash(privateSummary)}
 ended,e:=controlNativeEnd(publicProof,privateProof);must(e)
 var observationRaw string;must(tx1.QueryRow("SELECT body FROM runtime_observations WHERE project=? AND run=? AND epoch=?",project,runID,n.Epoch).Scan(&observationRaw))
 observation,e:=Decode([]byte(observationRaw));must(e)
 check(observation["ended"]==ended&&observation["control_execution_hash"]==record["receipt_hash"]&&observation["control_current_session"]==a.id&&observation["control_g0_hash"]==a.g0.Generation,"runtime observation evidence binding")
 endTime,e:=time.Parse(time.RFC3339Nano,ended);must(e);recordedTime,e:=time.Parse(time.RFC3339Nano,Str(observation,"recorded_at"));must(e);check(!recordedTime.Before(endTime),"runtime recorded before end")
 result["runtime_finished_recomputed"]=Object{"native_receipt_count":2*(len(publicProof.Pairs)+len(privateProof.Pairs)),"ended":ended,"recorded_at":observation["recorded_at"],"stored_finished_matches_native_max":true}
 counts:=Object{};for _,kind:=range []string{"CURRENT_CONTROL_EVALUATE_RESERVED","CURRENT_CONTROL_EVALUATE_RECORDED"} {var count int;must(tx1.QueryRow("SELECT count(*) FROM evolution_journal WHERE project=? AND candidate=? AND event=?",project,candidate,kind).Scan(&count));check(count==1,"durable evaluation count");counts[kind]=count};result["evaluation_counts"]=counts
 must(a.currentEvaluationJournal(tx1,controlCurrentReserved));must(a.currentEvaluationJournal(tx1,controlCurrentRecorded))
 result["reservation_and_completion_full_binding"]=true
 after,e:=os.ReadFile(Str(loc,"database"));must(e);check(Digest(after)==originalHash,"original changed during review")
 result["original_database_unchanged"]=true
 must(os.WriteFile(output,Bytes(result),0600));t.Log("safe persisted recomputation written; no private payload emitted")
}
