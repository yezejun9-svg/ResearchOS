from pathlib import Path
import json,hashlib,ast
O=Path(__file__).resolve().parent
R=Path("D:/作品集/ResearchOS/research-os")
B=R/"execution/v2.4/receipts/W09/W09-99"
N=B/"integration_codex/w09c19v7-consumers-1a11f30"
checks=[];pins={}
def check(name,ok,detail=None):
 row={"check":name,"pass":bool(ok)}
 if detail is not None:row["detail"]=detail
 checks.append(row)
 if not ok:
  (O/"checks.failed.json").write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding="utf-8")
  raise AssertionError(name)
def pin(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def read(ref):
 p=Path(ref["path"]);b=p.read_bytes();check("pin:"+str(p),hashlib.sha256(b).hexdigest()==ref["sha256"] and len(b)==ref["bytes"]);pins[str(p)]={"path":str(p),"sha256":ref["sha256"],"bytes":ref["bytes"]};return b
def obj(ref):return json.loads(read(ref))
def save(n,d):
 p=O/n;check("fresh_output:"+n,not p.exists());p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding="utf-8");return pin(p)
closedref={"path":str(N/"consumers.closed.json"),"sha256":"8dd7f3d0ecd90f4b35b497917db132005e369e1501c9ff2a5fd31a82dab0c53c","bytes":1946};closed=obj(closedref)
request=obj(closed["request_ref"]);scope=obj(request["root_consumer_scope_ref"]);T=Path(scope["candidate_root"])
check("closed_exact_two_routes",closed["status"]=="TWO_C19_COMPONENT_CONSUMERS_CLOSED_PENDING_INDEPENDENT_REVIEW" and closed["error"] is None and closed["routes"]==[["test.research.fixture","W09","","C19"],["test.retrieval","W09","","C19"]])
check("closed_boundaries",all(closed[k] is False for k in ["formal_dispatcher","registry_written","producer_rerun","canonical_written","Main_adopted"]) and closed["formal_case_count"]==1 and closed["formal_cases_accepted"]==closed["formal_case_accepted_delta"]==closed["new_Go_SQL_API_model_calls"]==0 and closed["all_owned_jobs_closed"] and closed["all_acquired_guards_closed"])
for k in ['producer_closed_ref','native_packet_ref','report_ref','tool_run_ref','producer_review_handoff_ref','producer_review_manifest_ref','caller_review_handoff_ref','caller_review_manifest_ref','canonical_vector_ref','modes']:check("scope_request_binding:"+k,scope[k]==request[k])
caller_ref=scope["source_caller_ref"];caller=read(caller_ref).decode();ch=obj(request["caller_review_handoff_ref"]);ph=obj(request["producer_review_handoff_ref"])
check("reviewed_caller_exact",ch["candidate_ref"]==caller_ref and caller_ref["sha256"]=="28cb94dfd8e941afd5d292e26a931047097e93265c3b8c98f37b2e39ec73b9f5" and caller_ref["bytes"]==22088 and ch["actor"]!="codex:/root")
check("producer_qualified",ph["actual_fixture_decision"]=="QUALIFIED" and ph["consumer_readiness"]=="QUALIFIED_PENDING_ROOT_ACTUAL_CONSUMPTION" and ph["formal_acceptance"] is False)
manifest_counts={}
for key in ["producer_review_manifest_ref","caller_review_manifest_ref"]:
 d=obj(request[key]);members=list(d["members"].values()) if isinstance(d["members"],dict) else d["members"]
 for ref in members:read(ref)
 manifest_counts[key]=len(members)
report=obj(request["report_ref"]);tool=obj(request["tool_run_ref"]);packet=obj(request["native_packet_ref"]);producer=obj(request["producer_closed_ref"]);vector=obj(request["canonical_vector_ref"])
check("same_original_native",packet["original_report_ref"]==request["report_ref"] and packet["original_tool_run_ref"]==request["tool_run_ref"] and report["run_id"]==tool["run_id"]==packet["run_id"]==ph["original_run_id"]=="37dedbd890c44a93975558f2851d8675")
for ref in vector["refs"]:read(ref)
cp=json.loads(Path(vector["refs"][0]["path"]).read_bytes());ow=json.loads(Path(vector["refs"][1]["path"]).read_bytes());check("canonical_366_170",cp["revision"]==vector["checkpoint_revision"]==366 and ow["revision"]==170)
pre=obj(producer["canonical_pre_run_ref"]);check("same_producer_canonical",pre["canonical_input_vector_ref"]==request["canonical_vector_ref"] and pre["refs"]==vector["refs"])
source21=[]
for rel,digest in report["version_manifest"]["source_sha256"].items():
 ref=pin(T/rel);check("source21:"+rel,"sha256:"+ref["sha256"]==digest);source21.append(ref)
check("source21_count",len(source21)==21)
router=T/"ops/ci/w09_formal_router.py";tree=ast.parse(router.read_bytes());maps={}
for node in tree.body:
 if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in {"NATIVE","FORMAL","PRESERVED"} for t in node.targets):maps[node.targets[0].id]=ast.literal_eval(node.value)
check("router_exact_expected_maps",len(maps)==3)
invocations=[];outputs=[];summaries=[];decisions=[];reviews=[]
for route,iref,mode in zip(closed["routes"],closed["invocation_refs"],request["modes"]):
 inv=obj(iref);out=json.loads(read(inv["stdout_ref"]));stderr=read(inv["stderr_ref"]);env=inv["public_environment"];result=inv["result"];cleanup=result["job_cleanup"]
 check("route:"+route[0],inv["route"]==route==mode["route"] and tuple(route) in maps["NATIVE"] and tuple(route) not in maps["PRESERVED"])
 check("actual_argv:"+route[0],inv["argv"]==[inv["argv"][0],"-S","-B","-X","utf8",str(router),route[0]] and inv["cwd"]==str(T) and Path(inv["argv"][0]).name.lower()=="python.exe")
 check("consumer_python_zero_no_new_native:"+route[0],inv["actual_consumer_python_exit"]==result["actual_exit"]==0 and inv["actual_new_product_native_exit"] is None and result["error"] is None and inv["exception"] is None and result["timed_out"] is False and result["resumed"] is True and not stderr)
 check("owned_job_closed:"+route[0],all(cleanup[k] is True for k in ["unnamed_exclusive_job","kill_on_job_close_configured","assigned_before_resume","primary_exit_confirmed","job_idle_confirmed","handles_closed"]) and not cleanup["errors"] and cleanup["active_processes_last_observed"]==0 and cleanup["termination_requested"] is False)
 check("u64_identity_preserved:"+route[0],type(result["creation_time_100ns"]) is int and result["creation_time_100ns"]>2**53)
 check("same_report_tool_mode_refs:"+route[0],inv["report_ref"]==request["report_ref"] and inv["tool_run_ref"]==request["tool_run_ref"] and inv["mode_decision_ref"]==mode["decision_ref"])
 check("selectors:"+route[0],[env["RESEARCHOS_TASK_ID"],env["RESEARCHOS_CHECK_ID"],env["RESEARCHOS_CASE_ID"]]==route[1:])
 for field,ref in [("NATIVE_REPORT",request["report_ref"]),("TOOL_RUN",request["tool_run_ref"]),("MODE_DECISION",mode["decision_ref"])]:
  check("env_binding:"+route[0]+":"+field,env["RESEARCHOS_W09_"+field+"_REF"]==Path(ref["path"]).relative_to(T).as_posix() and env["RESEARCHOS_W09_"+field+"_SHA256"]==ref["sha256"])
 check("fixture_temp:"+route[0],env["TEMP"]==env["TMP"]==str(R/".local/w09c19v7-producer-env-1a11f30/temp"))
 check("formal_three_native_five:"+route[0],out["status"]=="PASS" and out["assertion_ids"]==list(maps["FORMAL"][tuple(route)])==["C19-01","C19-02","C19-03"] and out["assertions"]==3 and out["native_assertion_ids"]==list(maps["NATIVE"][tuple(route)])==[f"C19-{i:02d}" for i in range(1,6)])
 check("consumer_no_formal_authority:"+route[0],out["formal_acceptance"]=="PENDING_INDEPENDENT_VERIFIER" and out["mode_evidence"]["formal_authority"] is False and out["task_id"]=="W09" and out["case_id"]=="C19" and out["check_id"] is None and inv["formal_dispatcher"] is False and inv["formal_case_accepted_delta"]==inv["new_Go_SQL_API_model_calls"]==0)
 for ref in out["source_pins"]:read({**ref,"path":str(T/ref["path"])})
 check("consumer_original_refs:"+route[0],out["source_pins"]==[{"path":ref,"sha256":tool[key],"bytes":len((T/ref).read_bytes())} for ref,key in zip(report["raw_evidence_references"],["stdout_sha256","stderr_sha256"])]+[{**request["report_ref"],"path":tool["report_ref"]}] and out["owned_export_member_count"]==486 and out["native_tool_run_ref"]==Path(request["tool_run_ref"]["path"]).relative_to(T).as_posix())
 d=obj(mode["decision_ref"]);review=obj(mode["independent_review_ref"]);decisions.append(d);reviews.append(review)
 check("mode_actual_output:"+route[0],out["mode_evidence"]=={"mode":"FIXTURE","decision_ref":Path(mode["decision_ref"]["path"]).relative_to(T).as_posix(),"decision_sha256":mode["decision_ref"]["sha256"],"formal_authority":False})
 check("mode_nonauthor:"+route[0],d["reviewer_id"]==review["actor_id"]=="codex:/root/native_temp_independent_review" and d["producer_id"]==review["producer_id"]=="codex:/root" and d["producer_id"]!=d["reviewer_id"] and d["reviewer_role"]==review["actor_role"]=="INDEPENDENT_NON_AUTHOR" and d["decision"]==review["decision"]=="QUALIFIED")
 check("mode_source_run:"+route[0],d["route"]==route and d["run_id"]==review["run_id"]==report["run_id"] and d["source_sha256"]==review["source_sha256"]==report["version_manifest"]["source_sha256"] and d["go_executable"]==review["go_executable"]==report["go_executable"] and d["report_sha256"]==review["report_sha256"]==request["report_ref"]["sha256"] and d["stdout_sha256"]==tool["stdout_sha256"])
 check("mode_review_ref:"+route[0],{**d["independent_review_ref"],"path":str(T/d["independent_review_ref"]["path"])}==mode["independent_review_ref"] and not Path(mode["independent_review_ref"]["path"]).is_relative_to(Path(request["report_ref"]["path"]).parent))
 summaries.append({"route":route,"invocation_ref":iref,"stdout_ref":inv["stdout_ref"],"stderr_ref":inv["stderr_ref"],"actual_consumer_python_exit":0,"new_product_native_exit":None,"owned_child_pid":result["owned_child_pid"],"creation_time_100ns":str(result["creation_time_100ns"]),"reported_assertions":3,"native_assertion_ids":out["native_assertion_ids"],"formal_acceptance":out["formal_acceptance"],"mode_decision_ref":mode["decision_ref"]});invocations.append(inv);outputs.append(out)
check("single_case_two_routes",len(invocations)==2 and len({x["owned_child_pid"] for x in summaries})==2 and {x["case_id"] for x in outputs}=={"C19"} and outputs[0]["source_pins"]==outputs[1]["source_pins"] and request["modes"][0]["independent_review_ref"]==request["modes"][1]["independent_review_ref"] and request["modes"][0]["decision_ref"]!=request["modes"][1]["decision_ref"])
inputs_ref=pin(N/"consumer.inputs.exact.json");inputs=obj(inputs_ref);check("finite_inputs_metadata",inputs["source_roster_count"]==21 and inputs["owned_members"]==486 and inputs["same_native_report_ref"]==request["report_ref"] and inputs["same_native_tool_run_ref"]==request["tool_run_ref"] and inputs["read_only"] is True)
check("one_guard",len(closed["guard_cleanups"])==1);guardref=closed["guard_cleanups"][0]["ref"];guard=obj(guardref)
check("guard_success_closed",guard["verification"]=="PASSED" and guard["share_mode"]=="FILE_SHARE_READ_ONLY" and guard["closed"] is True and guard["retained_handles_count"]==0 and not guard["errors"] and not guard["failure"])
held={}
for entry in guard["entries"]:
 ref={k:entry[k] for k in ["path","sha256","bytes"]};read(ref);check("held_closed:"+ref["path"],entry["verified"] and entry["final_path_match"] and entry["closed"] and ref["path"] not in held);held[ref["path"]]=ref
expected={ref["path"]:ref for ref in inputs["refs"]+[inputs_ref]};check("guard_exact_input_set",held==expected and len(inputs["refs"])==len(expected)-1)
required=[closed["request_ref"],scope["source_caller_ref"],request["root_consumer_scope_ref"],request["report_ref"],request["tool_run_ref"],request["canonical_vector_ref"],*vector["refs"],*source21]
for mode in request["modes"]:required.extend([mode["decision_ref"],mode["independent_review_ref"]])
for ref in required:check("required_held:"+ref["path"],held.get(ref["path"])==ref)
for pair in packet["raw_copy_mapping"]:
 check("original_archive_held:"+pair["original_ref"]["path"],all(held.get(ref["path"])==ref for ref in [pair["original_ref"],pair["archive_ref"]]))
rootref={"path":str(B/"integration_codex/w09c19v7-root-scope-20261009/component-consumers.original-tool-io.root.json"),"sha256":"995036d2ebd4dc3ebe2b8a89e055b68262714a1151ea9695d4ba31e3ecf9ff52","bytes":5152};rootio=obj(rootref);records=rootio["records"]
check("root_complete_io",len(records)==4 and all(set(x)>={"arguments","result","tool"} for x in records) and [x["result"]["chunk_id"] for x in records]==["1e05c5","ae87be","e86663","cff377"])
check("root_primary_session",records[1]["result"]["session_id"]==records[2]["arguments"]["session_id"]==records[2]["result"]["session_id"]==records[3]["arguments"]["session_id"]==57281)
check("root_final_exits",all(records[i]["result"]["exit_code"]==0 and "ROOT_PYTHON_EXIT=0" in records[i]["result"]["output"] for i in [0,3]))
cmd=records[1]["arguments"]["cmd"];check("root_actual_source_request_argv",Path(caller_ref["path"]).as_posix() in cmd and Path(closed["request_ref"]["path"]).as_posix() in cmd and closed["request_ref"]["sha256"] in cmd and "'6212'" in cmd and "dispatch.py" not in cmd)
root_output_refs=[]
for record in records:
 for line in record["result"]["output"].splitlines():
  if not line.startswith("{"):continue
  value=json.loads(line)
  for key,item in value.items():
   if isinstance(item,dict) and set(item)=={"path","sha256","bytes"}:read(item);root_output_refs.append(item)
check("root_six_output_refs",len(root_output_refs)==6)
main=[]
overlay=obj(producer["source_overlay_ref"])
for rel in overlay["sources"]:
 path=R/rel;candidate=pin(T/rel);state="MISSING" if not path.is_file() else "SAME" if path.read_bytes()==(T/rel).read_bytes() else "DRIFT"
 main.append({"relative_path":rel,"Main_state":state,"Main_ref":pin(path) if path.is_file() else None,"candidate_ref":candidate})
check("Main_not_adopted",sum(x["Main_state"]=="MISSING" for x in main)==3 and sum(x["Main_state"]=="DRIFT" for x in main)==3)
registryref=next(x for x in vector["refs"] if Path(x["path"]).name=="commands.json");registry=obj(registryref);entries={k:registry["commands"][k] for k in ["test.research.fixture","test.retrieval"]}
check("formal_registry_not_C19",entries["test.research.fixture"]["argv"]==["run","./tests/research/check"] and entries["test.research.fixture"]["selectors"]["task_id"]==["W08"] and entries["test.retrieval"]["argv"]==["-X","utf8","tests/evidence/check/main.py"] and entries["test.retrieval"]["selectors"]["check_id"]==["W09-01"] and all("case_id" not in x["selectors"] for x in entries.values()))
indexpath=R/"execution/v2.4/formal_case_index.py";indexref=pin(indexpath);read(indexref);ilines=indexpath.read_text().splitlines();index_rows=[{"line":i+1,"text":x} for i,x in enumerate(ilines) if 'require(task_id in {"W04", "W07"}' in x or 'require(task_id == "W04"' in x];check("W09_profile_unimplemented",len(index_rows)==3)
ssref=next(x for x in vector["refs"] if Path(x["path"]).name=="step_state.json");ss=obj(ssref);w09=[{"id":x["id"],"status":x["status"]} for x in ss["steps"] if x["id"].startswith("W09")];check("W09_parent_not_accepted",all(x["id"]!="W09-99" for x in w09))
dispatcherref=pin(R/"execution/command_dispatcher/dispatch.py");read(dispatcherref)
save("formal-gaps.actual-readonly.json",{"scope":"READ_ONLY_CURRENT_SOURCE_AND_REGISTRY_BOUNDARY","Main_six_source_members":main,"registry_ref":registryref,"current_command_bindings":entries,"formal_dispatcher_ref":dispatcherref,"formal_dispatcher_executed_in_this_run":False,"basis":"Both actual owned argv use candidate w09_formal_router.py; reviewed caller only launches those two commands; selected C19 routes are not PRESERVED subprocess branches; original Root tool args contain no dispatcher invocation.","formal_index_ref":indexref,"unsupported_W09_profile_source_lines":index_rows,"W09_canonical_child_states":w09,"W09_parent_row_present":False,"remaining":["Adopt six reviewed source members into Main with independent integration review","Register exact C19 formal command selector bindings while preserving existing routes","Implement and independently verify W09 formal evidence profile and canonical registration flow","A06 plus W09-G01 and W09-G02 are not covered by this C19 component run; W09 parent cannot be accepted from this packet"],"formal_case_accepted_delta":0,"CURRENT_formal_acceptance_created":False})
summary={"decision":"ACTUAL_TWO_C19_COMPONENT_CONSUMERS_VERIFIED_PASS","source_scope":"CANDIDATE_COMPONENT_ONLY","run_id":report["run_id"],"routes":closed["routes"],"single_case_id":"C19","formal_case_count":1,"consumer_python_exits":[0,0],"new_product_native_exit":None,"new_Go_SQL_API_model_calls":0,"assertions_per_consumer":3,"native_assertions_from_same_original_report":5,"owned_members":486,"held_guard_entries":len(held),"finite_input_refs":len(inputs["refs"]),"all_held_inputs_unchanged":True,"all_owned_jobs_closed":True,"all_guards_closed":True,"canonical_revisions":[366,170],"manifest_member_counts":manifest_counts,"formal_dispatcher":False,"registry_written":False,"Main_adopted":False,"formal_acceptance":False,"formal_case_accepted_delta":0,"W09_parent_accepted":False,"checks":len(checks),"failed_checks":0,"reviewer_is_source_author":False,"reviewer_is_consumer_executor":False,"reviewer_is_prior_mode_packet_author":True}
save("checks.json",{"summary":summary,"checks":checks});save("verified-input-pins.json",list(pins.values()));save("actual-consumer-summary.json",{"summary":summary,"consumers":summaries,"closed_ref":closedref,"request_ref":closed["request_ref"],"scope_ref":request["root_consumer_scope_ref"],"caller_ref":caller_ref,"guard_ref":guardref,"inputs_ref":inputs_ref,"root_original_tool_io_ref":rootref,"producer_review_handoff_ref":request["producer_review_handoff_ref"],"caller_review_handoff_ref":request["caller_review_handoff_ref"],"canonical_refs":vector["refs"]})
print(json.dumps(summary,ensure_ascii=False))
