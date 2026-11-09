import sys
sys.dont_write_bytecode=True
from pathlib import Path
import hashlib,json,copy,difflib
ROOT=Path(r"D:\作品集\ResearchOS\research-os")
OUT=ROOT/r"execution/v2.4/receipts/W05/W05-99/cli43_transport_binding_preparation_codex/2c271a22fbb34123a65d799e854b9d24"
def need(v,m):
 if not v: raise RuntimeError(m)
def pin(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def save(name,v):
 with (OUT/name).open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode())
def write(name,b):
 with (OUT/name).open("xb") as f:f.write(b)
old_dir=ROOT/r"execution/v2.4/receipts/W05/W05-99/cli43_http_bytes_ownership_preparation_codex/310e0bf842a34df6813dad1126e2970a"
test_dir=ROOT/r"execution/v2.4/receipts/W05/W05-99/cli43_fresh_compiler_preparation_revision_codex/bb395255ecb14df6820b2e20631c9c39"
hp=old_dir/"cli43_receipt_instrumentation_test.go.proposed.txt"
pp=old_dir/"instrumentation-plan.proposed.json"
tp=test_dir/"cli_sessions_test.instrumented.go.txt"
schema=ROOT/"internal/api/contracts/domain.schema.json"
orig=ROOT/"apps/cli/cli_sessions_test.go"
inputs=[hp,pp,tp,schema,orig,ROOT/"internal/domain/contracts.go",ROOT/"internal/domain/contracts_persistence_v24.go",ROOT/"internal/domain/client_protocol_schema.go",ROOT/"internal/api/v2.go",ROOT/"go.mod"]
before=[pin(p) for p in inputs];save("inputs.before.json",before)
need(before[0]["sha256"]=="37a3a61abe8fe81718021b17c7243fb3410c066a107cf346ec636b04bae176d9","old helper pin")
need(before[1]["sha256"]=="a6262abc7510fc7974b5bebe71cc46a237d568729268e1686991024e6f8bf253","old plan pin")
need(before[2]["sha256"]=="37220e2a574343f7e291b41745e556d23775711d79f01cc8deb47ee1c0b19966","old test pin")
need(before[3]["sha256"]=="b53d9e6eddfeed89d27ee65c378d8067ae8b0c46de2ba2a098856a7557df1c54","fixed domain schema")
h=hp.read_bytes().decode(); t=tp.read_bytes().decode(); oldh=h;oldt=t
hchanges=[];tchanges=[]
def edit(s,old,new,changes):
 need(s.count(old)==1,"nonunique exact edit: "+old[:80]);changes.append({"old":old,"new":new});return s.replace(old,new,1)
h=edit(h,' "researchos.local/research-os/internal/api"',' "github.com/santhosh-tekuri/jsonschema/v6"\n "researchos.local/research-os/internal/domain"\n "researchos.local/research-os/internal/api"',hchanges)
add=r'''type cli43TransportFact struct {
 RequestIndex int `json:"request_index"`
 ResponseIndex int `json:"response_index"`
 Method string `json:"method"`
 RequestURI string `json:"request_uri"`
 Status int `json:"status"`
}
type cli43LocalSchemaOnly struct{}
func (cli43LocalSchemaOnly) Load(uri string)(any,error){return nil,fmt.Errorf("export-only unregistered schema resource: %s",uri)}
func cli43EntityContracts(t *testing.T)*domain.Contracts{
 t.Helper()
 raw,e:=os.ReadFile(filepath.Join("..","..","internal","api","contracts","domain.schema.json"));if e!=nil{t.Fatal(e)}
 if fmt.Sprintf("%x",sha256.Sum256(raw))!="b53d9e6eddfeed89d27ee65c378d8067ae8b0c46de2ba2a098856a7557df1c54"{t.Fatal("export-only domain schema pin")}
 body,e:=domain.Decode(raw);if e!=nil{t.Fatal(e)}
 compiler:=jsonschema.NewCompiler();compiler.UseLoader(cli43LocalSchemaOnly{});compiler.AssertFormat();compiler.DefaultDraft(jsonschema.Draft2020)
 const location="https://researchos.invalid/domain.schema.json"
 if e=compiler.AddResource(location,body);e!=nil{t.Fatal(e)}
 contracts:=&domain.Contracts{Schemas:map[string]*jsonschema.Schema{}}
 for _,kind:=range []string{"Goal","Task"}{
  compiled,e:=compiler.Compile(location+"#/$defs/"+kind);if e!=nil{t.Fatal(e)};contracts.Schemas[kind]=compiled
 }
 return contracts // Fixed fixture THIN_CORE route only; no V24/general route qualification.
}
'''
h=edit(h,'func cli43AssertBinding(',add+'\nfunc cli43AssertBinding(',hchanges)
h=edit(h,'requests []json.RawMessage,responses [][]byte,before,after []byte)','requests []json.RawMessage,responses [][]byte,transport []cli43TransportFact,before,after []byte)',hchanges)
h=edit(h,' if len(requests)!=len(responses){t.Fatal("request/response pairing")}',' if len(requests)!=len(responses)||len(requests)!=len(transport){t.Fatal("request/response/transport pairing")}',hchanges)
h=edit(h,' doc,e:=api.ClientProtocolDocument();if e!=nil{t.Fatal(e)}\n for i,raw:=range requests{',r''' doc,e:=api.ClientProtocolDocument();if e!=nil{t.Fatal(e)}
 entities:=cli43EntityContracts(t)
 sendGoal:="";completedSends:=0;goals:=[]map[string]any{};tasks:=[]map[string]any{}
 for i,raw:=range requests{
  fact:=transport[i]
  if fact.RequestIndex!=i||fact.ResponseIndex!=i||fact.Status!=http.StatusOK{t.Fatal("exact transport index/status mismatch",i,fact)}
  uri,e:=url.ParseRequestURI(fact.RequestURI);if e!=nil{t.Fatal(e)}
  if uri.Scheme!=""||uri.Host!=""||uri.Opaque!=""||uri.RawPath!=""||uri.RawQuery!=""||uri.ForceQuery||uri.Fragment!=""||uri.String()!=fact.RequestURI{t.Fatal("noncanonical fixture request URI",fact.RequestURI)}
  if fact.Method==http.MethodGet{
   if len(raw)!=0||len(responses[i])==0||completedSends!=1{t.Fatal("REST exact empty request/nonempty response/send binding",i)}
   parts:=strings.Split(strings.TrimPrefix(uri.Path,"/"),"/")
   if len(parts)!=5||parts[0]!="v1"||parts[1]!="projects"||parts[2]!=cfg.ProjectID||parts[4]==""{t.Fatal("REST fixture project/path mismatch",fact.RequestURI)}
   kind:="";switch parts[3]{case "goals":kind="Goal";case "tasks":kind="Task";default:t.Fatal("unexpected REST fixture entity",fact.RequestURI)}
   reply,e:=domain.Decode(responses[i]);if e!=nil{t.Fatal(e)}
   binding,ok:=reply["binding"].(map[string]any);if !ok||binding["route"]!="THIN_CORE"{t.Fatal("fixed REST fixture route must be THIN_CORE",kind)}
   if e=entities.Validate(kind,reply);e!=nil{t.Fatal(e)}
   if reply["id"]!=parts[4]||reply["project_id"]!=cfg.ProjectID{t.Fatal("REST entity exact path identity",kind)}
   if kind=="Goal"{
    if reply["id"]!=sendGoal{t.Fatal("REST Goal differs from completed send snapshot")};goals=append(goals,reply)
   }else{
    if reply["goal_id"]!=sendGoal{t.Fatal("REST Task differs from completed send Goal")};tasks=append(tasks,reply)
   }
   continue
  }
  if fact.Method!=http.MethodPost||uri.Path!="/v2/command"||len(raw)==0{t.Fatal("unexpected fixture transport method/path/body",i,fact)}''',hchanges)
h=edit(h,'   if method=="session.attach"&&result["write_owner_acquired"]!=false{t.Fatal("readonly attach acquired writer")}','   if method=="session.attach"&&result["write_owner_acquired"]!=false{t.Fatal("readonly attach acquired writer")}\n   if method=="session.send"{completedSends++;sendGoal,ok=snapshot["goal_id"].(string);if !ok||sendGoal==""||completedSends!=1{t.Fatal("completed send Goal identity missing or repeated")}}',hchanges)
h=edit(h,' cli43SessionBoundary(t,db,dir,"after",cfg)',r''' if completedSends==0{
  if len(goals)!=0||len(tasks)!=0{t.Fatal("readonly fixture unexpectedly read Goal/Task")}
 }else{
  if completedSends!=1||len(goals)!=1||len(tasks)!=1{t.Fatal("completed send exact Goal/Task pairing")}
  ids,ok:=goals[0]["task_ids"].([]any);if !ok{t.Fatal("REST Goal task_ids missing")}
  matches:=0;for _,id:=range ids{if id==tasks[0]["id"]{matches++}};if matches!=1{t.Fatal("REST Goal does not uniquely link actual Task")}
 }
 cli43SessionBoundary(t,db,dir,"after",cfg)''',hchanges)
h=edit(h,'"all_reply_sid_mirror_request":true','"all_command_reply_sid_mirror_request":true,"transport_entries":len(transport),"REST_goal_count":len(goals),"REST_task_count":len(tasks),"completed_send_goal_id":sendGoal,"REST_send_goal_task_links_validated":completedSends==1',hchanges)
nl="\r\n" if "\r\n" in t else "\n";need(nl in t and ("\r" not in t if nl=="\n" else t.count("\r\n")==t.count("\n")),"preserve measured uniform test newline")
old='\t\t\t\tresponses := [][]byte{}'
t=edit(t,old,old+nl+'\t\t\t\ttransport := []cli43TransportFact{}',tchanges)
old='\t\t\t\t\tmu.Lock()'+nl+'\t\t\t\t\trequests = append(requests, append(json.RawMessage(nil), raw...))'+nl+'\t\t\t\t\trequestBytes = append(requestBytes, append([]byte(nil), raw...))'
new='\t\t\t\t\tmu.Lock()'+nl+'\t\t\t\t\trequestIndex := len(requests)'+nl+'\t\t\t\t\trequests = append(requests, append(json.RawMessage(nil), raw...))'+nl+'\t\t\t\t\trequestBytes = append(requestBytes, append([]byte(nil), raw...))'
t=edit(t,old,new,tchanges)
old='\t\t\t\t\tresponses = append(responses, append([]byte(nil), responseRaw...))'
t=edit(t,old,'\t\t\t\t\ttransport = append(transport, cli43TransportFact{RequestIndex: requestIndex, ResponseIndex: len(responses), Method: r.Method, RequestURI: r.URL.RequestURI(), Status: resp.StatusCode})'+nl+old,tchanges)
old='\t\t\t\trequestEvidence := append([][]byte(nil), requestBytes...)'
t=edit(t,old,old+nl+'\t\t\t\ttransportEvidence := append([]cli43TransportFact(nil), transport...)',tchanges)
old='\t\t\t\tos.WriteFile(filepath.Join(evidence, "requests.exact.json"), rawRequests, 0600)'
t=edit(t,old,old+nl+'\t\t\t\tif err := cli43Save(evidence, "transport.exact.json", transportEvidence); err != nil { t.Fatal(err) }',tchanges)
old='\t\t\t\tcli43AssertBinding(t, db, evidence, name, cfg, copyRequests, responseEvidence, configBefore, configAfter)'
t=edit(t,old,'\t\t\t\tcli43AssertBinding(t, db, evidence, name, cfg, copyRequests, responseEvidence, transportEvidence, configBefore, configAfter)',tchanges)
def inverse(raw,changes):
 for c in reversed(changes):
  need(raw.count(c["new"])==1,"nonunique inverse");raw=raw.replace(c["new"],c["old"],1)
 return raw
need(inverse(h,hchanges)==oldh,"helper whole byte inverse")
need(inverse(t,tchanges)==oldt,"instrumented test whole byte inverse")
need('func cli43Bytes(b []byte) map[string]any{b=bytes.Clone(b);' in h,"owned byte clone preserved")
oldplan=json.loads(pp.read_bytes());plan=copy.deepcopy(oldplan)
need((json.dumps(oldplan,ensure_ascii=False,indent=2)+"\n").encode()==pp.read_bytes(),"exact old plan formatting")
plan["changes"].extend(tchanges)
plan["exact_scoped_inline_edits"].extend([[c["old"],c["new"]] for c in tchanges])
write("cli43_receipt_instrumentation_test.go.proposed.txt",h.encode())
write("cli_sessions_test.instrumented.go.proposed.txt",t.encode())
plan["additional_file_ref"]=pin(OUT/"cli43_receipt_instrumentation_test.go.proposed.txt")
plan["instrumented_sha256"]=hashlib.sha256(t.encode()).hexdigest()
restore=copy.deepcopy(plan);restore["changes"]=restore["changes"][:-len(tchanges)];restore["exact_scoped_inline_edits"]=restore["exact_scoped_inline_edits"][:-len(tchanges)]
restore["additional_file_ref"]=oldplan["additional_file_ref"];restore["instrumented_sha256"]=oldplan["instrumented_sha256"]
need((json.dumps(restore,ensure_ascii=False,indent=2)+"\n").encode()==pp.read_bytes(),"plan exact inverse")
reverse=inverse(t,plan["changes"]);need(reverse.encode()==orig.read_bytes(),"complete original Main test byte inverse")
save("instrumentation-plan.proposed.json",plan)
save("helper.exact-edits.json",hchanges);save("test.exact-edits.json",tchanges)
write("helper.diff","".join(difflib.unified_diff(oldh.splitlines(True),h.splitlines(True),fromfile="old-helper",tofile="new-helper")).encode())
write("test.diff","".join(difflib.unified_diff(oldt.splitlines(True),t.splitlines(True),fromfile="old-export-test",tofile="new-export-test")).encode())
after=[pin(p) for p in inputs];save("inputs.after.json",after);need(before==after,"source input drift")
save("static-checks.json",{"helper_byte_inverse":True,"instrumented_test_byte_inverse":True,"complete_Main_test_byte_inverse":True,"plan_byte_inverse":True,"original_POST_identity_and_snapshot_assertions_preserved":True,"actual_transport_index_is_recorded_under_original_mutex":True,"method_URI_status_not_reconstructed_from_HTTP_log_sequences":True,"GET_empty_body_not_generic_skip":True,"fixed_schema_route":"THIN_CORE","Goal_Task_Link":"completed session.send snapshot.goal_id -> GET Goal path/id/project -> Goal.task_ids -> GET Task id/project/goal_id","immediate_bytes_Clone_preserved":True,"input_drift":0,"Go_gofmt_SQL_HTTP_SDK_MODEL_calls":0,"source_acceptance":False,"formal_increment":0})
save("handoff.json",{"schema":"researchos.cli43.transport-binding-preparation.v1","actor":"codex:/root","status":"SOURCE_PREPARATION_ONLY","helper_ref":pin(OUT/"cli43_receipt_instrumentation_test.go.proposed.txt"),"instrumented_source_ref":pin(OUT/"cli_sessions_test.instrumented.go.proposed.txt"),"instrumentation_plan_ref":pin(OUT/"instrumentation-plan.proposed.json"),"old_helper_ref":pin(hp),"old_test_ref":pin(tp),"old_plan_ref":pin(pp),"schema_ref":pin(schema),"changed_functions":["cli43AssertBinding","new export-only cli43EntityContracts","new transport fact struct and local-only schema loader"],"test_additions":len(tchanges),"whole_byte_inverses":True,"business_assertions_changed":False,"HTTP_budget_or_timeout_changed":False,"strict_Python_validator_changed":False,"Go_SQL_SDK_MODEL_HTTP_executed":0,"source_acceptance":False,"formal_increment":0,"requires":["non-author source review","new Root scope/CAS/grant","fresh compile and one execution","independent full qualification"],"original_diagnostic_failures_preserved":["execution/v2.4/receipts/W05/W05-99/cli43_transport_binding_preparation_codex/b69ddf4c7d564a33b017dff4b1a48f2e/diagnostic.origin.null-property.json","execution/v2.4/receipts/W05/W05-99/cli43_transport_binding_preparation_codex/b69ddf4c7d564a33b017dff4b1a48f2e/diagnostic.origin.absent-client-protocol.json","execution/v2.4/receipts/W05/W05-99/cli43_transport_binding_preparation_codex/b69ddf4c7d564a33b017dff4b1a48f2e/failure.origin.newline-assumption.json"],"counter_reset":False})
members=[pin(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!="manifest.json"]
save("manifest.json",{"schema":"researchos.receipt.manifest.v1","self_excluded":True,"members":members})
print(json.dumps({"status":"SOURCE_PREPARATION_ONLY","helper":pin(OUT/"cli43_receipt_instrumentation_test.go.proposed.txt"),"test":pin(OUT/"cli_sessions_test.instrumented.go.proposed.txt"),"plan":pin(OUT/"instrumentation-plan.proposed.json"),"handoff":pin(OUT/"handoff.json"),"manifest":pin(OUT/"manifest.json"),"Go_SQL_HTTP_SDK_MODEL_calls":0},ensure_ascii=False))
