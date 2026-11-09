"""A04 independent static/pure-data review; no product or full candidate execution."""
import ast,copy,difflib,hashlib,json,re,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path("D:/作品集/ResearchOS/research-os")
SRC=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/a04_formal_profile_source_preparation_codex/a61c549b78aa4f2ea3ccf4857e44838e")
BASE=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/a04_formal_profile_independent_source_review_codex/d8dba4feee094e90b4a8f41c11d8648f")
def physical(ref):
 p=Path(ref["path"]);return p if p.is_absolute() else ROOT/p
def pin(p):
 raw=p.read_bytes();return {"path":str(p).replace("\\","/"),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def verify(ref):
 actual=pin(physical(ref));return {"expected":ref,"actual":actual,"matches":actual["sha256"]==ref["sha256"] and actual["bytes"]==ref["bytes"]}
h=json.loads((SRC/"handoff.json").read_bytes());mf=json.loads((SRC/"manifest.json").read_bytes());iv=json.loads((SRC/"source.inverse.json").read_bytes())
members=[verify(ref) for ref in mf["members"]]
inverse=[]
for entry in iv["entries"]:
 candidate=physical(entry["proposed"]);raw=candidate.read_bytes();tree=ast.parse(raw)
 info={"target":entry["target"],"candidate":verify(entry["proposed"]),"ast_parse":True}
 if entry["before"] is None:
  info.update(before_absence_currently_observed=not (ROOT/entry["target"]).exists(),inverse_not_executed=True)
 else:
  before=physical(entry["before"]);before_raw=before.read_bytes();old_text=before.read_text(encoding="utf-8");new_text=candidate.read_text(encoding="utf-8")
  expected=entry["inverse_unified_diff"];heads=expected.splitlines()
  generated="".join(difflib.unified_diff(new_text.splitlines(keepends=True),old_text.splitlines(keepends=True),fromfile=heads[0][4:],tofile=heads[1][4:]))
  old_lossless=before_raw.decode("utf-8");new_lossless=raw.decode("utf-8")
  delta=list(difflib.ndiff(old_lossless.splitlines(keepends=True),new_lossless.splitlines(keepends=True)))
  oa={n.name:ast.dump(n,include_attributes=False) for n in ast.parse(before_raw).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
  na={n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
  info.update(before=verify(entry["before"]),inverse_text_exact=generated==expected,
   raw_byte_restore_before_exact="".join(difflib.restore(delta,1)).encode("utf-8")==before_raw,
   raw_byte_restore_after_exact="".join(difflib.restore(delta,2)).encode("utf-8")==raw,
   changed_definitions=[n for n in oa if n in na and oa[n]!=na[n]],new_definitions=[n for n in na if n not in oa],
   other_definitions_ast_unchanged=sum(oa[n]==na[n] for n in oa if n in na))
 inverse.append(info)
profile=(SRC/"formal_profile_w05.proposed.py").read_text(encoding="utf-8"); pt=ast.parse(profile)
test=(SRC/"precheck_a04.py").read_text(encoding="utf-8"); tt=ast.parse(test)
# Execute selected pure assertion function with in-memory evidence only.
witness_node=next(n for n in pt.body if isinstance(n,ast.FunctionDef) and n.name=="_witness")
api_node=next(n for n in tt.body if isinstance(n,ast.ClassDef) and n.name=="API")
values={"re":re,"copy":copy}
exec(compile(ast.Module(body=[api_node],type_ignores=[]),"<data-api-stub>","exec"),values)
for n in tt.body:
 if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ("LANES","INV","facts","context","raw_values"):
  exec(compile(ast.Module(body=[n],type_ignores=[]),"<fixture-values>","exec"),values)
space={"EXTRA":{"A04-04":"H08","A04-05":"P01","A04-06":"U02"}}
exec(compile(ast.Module(body=[witness_node],type_ignores=[]),"<selected-pure-witness>","exec"),space)
API=values["API"];facts=values["facts"];context=values["context"];raw_values=values["raw_values"]
proofs={}
for cid,f in facts.items():
 lane=values["LANES"][cid]
 proofs[cid]={"schema":"researchos.w05.a04-raw-observation.v1","assertion_id":cid,"run_id":context["run_id"],"lane":lane,
 "invocation_ref":next(i["invocation_ref"] for i in context["command_invocations"] if i["lane"]==lane),
 "facts":f,"actual":"observed-"+cid,"fact_source_refs":{key:{"path":"raw-"+cid,"sha256":"d"*64,"locator":{"json_pointer":"/facts/"+key}} for key in f}}
def raw(_api,_reader,ref):
 path=ref["path"]
 if path.startswith("obs-"):return proofs[path[4:]]
 if path.startswith("raw-"):return raw_values[path[4:]][ref["locator"]["json_pointer"][7:]]
 if path.startswith("refusal-"):return {"status":"PASS","rejected":False,"foreign_run":"not-this-run"}
 raise ValueError("unmodeled evidence")
space["_raw"]=raw
space["_doc"]=lambda *_:{"selected_runtime":"mu"}
row_node=next(n for n in tt.body if isinstance(n,ast.FunctionDef) and n.name=="row")
exec(compile(ast.Module(body=[row_node],type_ignores=[]),"<data-row-builder>","exec"),values)
witness=space["_witness"]; observations=[]
def observe(name,fn):
 try:value=fn();result={"accepted":True,"returned_type":type(value).__name__,"error":None}
 except (ValueError,KeyError,TypeError,AssertionError) as e:result={"accepted":False,"error":type(e).__name__+":"+str(e)}
 observations.append({"name":name,**result})
for cid in ("A04-01","A04-02","A04-06"):
 observe("assertion "+cid+" with refusal saying PASS/rejected=false/foreign run",
   lambda cid=cid:witness(API,None,values["row"](cid),context,{lane:{} for lane in values["LANES"].values()}))
old=copy.deepcopy(facts["A04-02"]);old_raw=copy.deepcopy(raw_values["A04-02"])
for key in ("owned_tool_processes_after","pending_requests_after","late_launches"):facts["A04-02"][key]=False;raw_values["A04-02"][key]=False
observe("cancellation count fields are bool false rather than actual numeric counts",
 lambda:witness(API,None,values["row"]("A04-02"),context,{lane:{} for lane in values["LANES"].values()}))
facts["A04-02"].clear();facts["A04-02"].update(old);raw_values["A04-02"].clear();raw_values["A04-02"].update(old_raw)
wrong=values["row"]("A04-02");wrong["lane"]="success";proofs["A04-02"]["lane"]="success"
proofs["A04-02"]["invocation_ref"]=context["command_invocations"][0]["invocation_ref"]
observe("cancel assertion bound to success lane instead of pending_queue_cancel",
 lambda:witness(API,None,wrong,context,{lane:{} for lane in values["LANES"].values()}))
# Bundle gate uses no filesystem here: pinned-reference IO is replaced with a closed memory map.
handler=(SRC/"runtime_w05_live.proposed.py").read_text(encoding="utf-8");ht=ast.parse(handler)
nodes=[n for n in ht.body if isinstance(n,ast.FunctionDef) and n.name in ("require","verify_bundle")]
ID=tuple("A04-0"+str(i) for i in range(1,7));SC=("success","tool_failed","request_timeout","pending_queue_cancel","executor_crash");GA=("W05-G01","W05-G02","W05-H08","W05-P01","W05-U02")
def ref(path):return {"path":path,"sha256":"a"*64}
grant_ref=ref("grant");original_ref=ref("original-empty-output")
docs={"grant":{"schema":"researchos.w05.a04-root-grant.v1","run_id":"R","decision":"GRANTED","mode":"LIVE_WINDOWS","accounting_mode":"UNLIMITED_AMOUNT","selected_runtime":"mu","fixed_model":"fixed"}}
bundle={"schema":"researchos.w05.live-dispatch-bundle.v1","task_id":"W05","case_id":"A04","mode":"LIVE_WINDOWS","run_id":"R","producer_actor":"codex:/root","independent_acceptance":"NOT_EVALUATED","selected_runtime":"mu","fixed_model":"fixed",
 "accounting":{"mode":"UNLIMITED_AMOUNT","status":"UNKNOWN","amount_usd":None,"source_refs":[]},"root_grant_ref":grant_ref,"product_original_refs":[original_ref],"invocations":[],"assertions":[],"gate_results":[]}
for lane in (*SC,"H08","P01","U02"):
 invocation={"run_id":"R","lane":lane,"root_grant_ref":grant_ref,"stdout_ref":original_ref,"stderr_ref":original_ref}
 scope={"schema":"researchos.w05.a04-live-scope.v1","run_id":"R","lane":lane,"root_grant_ref":grant_ref}
 docs["inv-"+lane]=invocation;docs["scope-"+lane]=scope
 bundle["invocations"].append({"lane":lane,"invocation_ref":ref("inv-"+lane),"scope_ref":ref("scope-"+lane)})
for cid in ID:
 lane=values["LANES"][cid];docs["empty-"+cid]={"schema":"researchos.w05.a04-raw-observation.v1","assertion_id":cid,"run_id":"R","lane":lane,"actual":"opaque","facts":{},"fact_source_refs":{}}
 bundle["assertions"].append({"id":cid,"status":"PASS","lane":lane,"actual":"opaque","raw_evidence_refs":[ref("empty-"+cid)]})
for gate in GA:bundle["gate_results"].append({"id":gate,"status":"PASS","raw_evidence_refs":[original_ref]})
hs={"IDS":ID,"GATES":GA,"SCENARIOS":SC,"read_ref":lambda r:(docs[r["path"]],r["path"]),"pin_raw":lambda r:(b"",r["path"])}
exec(compile(ast.Module(body=nodes,type_ignores=[]),"<selected-pure-bundle-validator>","exec"),hs)
observe("bundle with no DB/JSONL/Job data, empty facts, missing actual argv/cwd/env/native_exit",
 lambda:hs["verify_bundle"](bundle,"A04"))
observe("same opaque bundle W05-H08 gate",lambda:hs["verify_bundle"](bundle,"W05-H08"))
audit={"schema":"researchos.a04-independent-source-audit.v1","actor_id":"codex:/root/f08_whole_scope_review","manifest_members":members,"member_count":len(members),"all_members_exact":all(x["matches"] for x in members),
 "source_inverse":inverse,"five_sources_ast_parsed":True,"selected_pure_counterexamples":observations,
 "handler_exporter_full_entry_point_executed":False,"real_product_sql_native_sdk_model_calls":0,"canonical_writes":0,"formal_case_accepted_delta":0}
with (BASE/"audit.json").open("xb") as f:f.write((json.dumps(audit,ensure_ascii=False,indent=2)+"\n").encode("utf-8"))
print(json.dumps({"audit_ref":pin(BASE/"audit.json"),"member_count":len(members),"all_members_exact":audit["all_members_exact"],"inverse":[{k:v for k,v in row.items() if k not in ("candidate","before")} for row in inverse],"observations":observations},ensure_ascii=False))

