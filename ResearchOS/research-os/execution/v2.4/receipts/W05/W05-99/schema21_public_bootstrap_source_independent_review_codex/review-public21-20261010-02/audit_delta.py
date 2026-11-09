import ast,copy,hashlib,json,os,sys,types
from pathlib import Path
B=Path(r"D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99")
N=Path(__file__).resolve().parent
Q=B/"genuine_schema21_public_bootstrap_runner_source_codex/s21public-20261010-02"
OLD=B/"genuine_schema21_public_bootstrap_runner_source_codex/s21public-20261010-01"
REVIEW=B/"schema21_public_bootstrap_source_independent_review_codex/review-public21-20261010-01"
def sha(raw):return hashlib.sha256(raw).hexdigest()
def pin(p):
 p=Path(p);raw=p.read_bytes();return {"path":str(p),"sha256":sha(raw),"bytes":len(raw)}
def require(ok,code):
 if not ok:raise ValueError(code)
def exact(ref):
 p=Path(ref["path"]);require(pin(p)==ref,"PIN_CHANGED:"+str(p));return p.read_bytes()
def write(name,value,raw=False):
 p=N/name;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("xb") as out:
  out.write(value if raw else (json.dumps(value,ensure_ascii=False,indent=2)+"\n").encode());out.flush();os.fsync(out.fileno())
 return pin(p)
refs=[
 {"path":str(Q/"HDF.json"),"sha256":"67370cddc352f299c5c8569ae69e0b90dec64a8f281746d4510a55dac1d02c0d","bytes":6131},
 {"path":str(Q/"MF.json"),"sha256":"045363095aa0b1efaa3359cdead8d246153ba1f695cd98095a20dc016dcb791f","bytes":19678}]
hdf,mf=[json.loads(exact(r)) for r in refs]
require(len(mf["members"])==mf["member_count"]==55,"NEW_SOURCE_MANIFEST_COUNT")
refs.extend(mf["members"])
sourceinputs=json.loads(exact(hdf["source_inputs_ref"]))
refs.extend(sourceinputs["references"])
olddecision={"path":str(REVIEW/"source-decision.json"),"sha256":"cc22aba4e7cc9d9c4d6978bbca4996541bcfcd51b5b5bb2286f78fa428314b47","bytes":4740}
refs.append(olddecision)
seen={}
for ref in refs:
 path=str(Path(ref["path"]))
 require(path not in seen or seen[path]["sha256"]==ref["sha256"],"CONFLICTING_INPUT_PIN")
 seen[path]=dict(ref,path=path)
refs=list(seen.values())
for ref in refs:exact(ref)
guardref=next(r for r in refs if Path(r["path"]).name=="source_read_guard.py")
module=types.ModuleType("public21_delta_guard");module.__file__=guardref["path"]
sys.modules[module.__name__]=module
exec(compile(exact(guardref),guardref["path"],"exec"),module.__dict__)
guard=module.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
facts={};controls=[];copies=[]
try:
 guard.acquire(refs)
 def held(path):return guard.get_buffer(str(path))
 def doc(path):return json.loads(held(path))
 for index,ref in enumerate(refs):
  copies.append({"original_ref":ref,"copy_ref":write("inputs/"+str(index)+"-"+Path(ref["path"]).name,held(ref["path"]),True)})
 old,new=held(OLD/"public21_runner.py"),held(Q/"public21_runner.py")
 oldspan=b"invocation.update(observation=observed,actual_exit=observed.get('actual_exit'),ended_at_unix_ns=time.time_ns(),stdout_ref=observed_ref(stdout),stderr_ref=observed_ref(stderr))"
 newspan=b"invocation.update(observation=observed,actual_exit=observed.get('actual_exit'),ended_at_unix_ns=time.time_ns())\n        invocation['stdout_ref']=observed_ref(stdout)\n        invocation['stderr_ref']=observed_ref(stderr)"
 require(old.count(oldspan)==new.count(newspan)==1,"UNIQUE_EDIT_SPANS")
 restored=new.replace(newspan,oldspan)
 require(restored==old,"EXACT_INVERSE_NOT_OLD_BYTES")
 before,after=doc(OLD/"contract.json"),doc(Q/"contract.json")
 changed=sorted(k for k in set(before)|set(after) if before.get(k)!=after.get(k))
 require(changed==["runner_ref","source_revision_basis","status"],"CONTRACT_DELTA")
 require(after["runner_ref"]==pin(Q/"public21_runner.py"),"CONTRACT_RUNNER_PIN")
 require(after["source_revision_basis"]["finding"]=="PUBLIC21-OBSERVATION-001"
         and after["source_revision_basis"]["accepted_by_author"] is False,"SOURCE_REVISION_BASIS")
 facts["inverse"]={"offset":old.index(oldspan),"old_span_bytes":len(oldspan),"new_span_bytes":len(newspan),
                    "restored_sha256":sha(restored),"original_sha256":sha(old),"all_other_runner_bytes_identical":True,
                    "contract_changed_topkeys":changed}
 tree=ast.parse(new,filename=str(Q/"public21_runner.py"))
 candidates=[]
 for node in ast.walk(tree):
  if isinstance(node,ast.Try):
   for i,item in enumerate(node.body):
    if isinstance(item,ast.Expr) and isinstance(item.value,ast.Call) and isinstance(item.value.func,ast.Attribute):
     target=item.value.func
     if isinstance(target.value,ast.Name) and target.value.id=="invocation" and target.attr=="update":
      keywords={k.arg for k in item.value.keywords}
      if keywords=={"observation","actual_exit","ended_at_unix_ns"}:candidates.append((node,i))
 require(len(candidates)==1,"UNIQUE_LOCAL_OBSERVATION_STATEMENTS")
 tr,start=candidates[0];body=tr.body[start:start+5]
 require(len(body)==5 and len(tr.handlers)==1,"LOCAL_STATEMENT_OR_HANDLER_SHAPE")
 local=ast.Module(body=[ast.Try(body=copy.deepcopy(body),handlers=copy.deepcopy(tr.handlers),orelse=[],finalbody=[])],type_ignores=[])
 ast.fix_missing_locations(local);compiled=compile(local,"public21_v2_observation_delta_ast_only","exec")
 class FakeTime:
  @staticmethod
  def time_ns():return 1234567890123456789
 class FakePath:
  def __init__(self,*parts):self.parts=parts
  def __truediv__(self,other):return FakePath(*self.parts,other)
 for exit_value in (0,1,None):
  for fault in ("stdout","stderr","result","closed"):
   cleanup={"job_idle_confirmed":exit_value is not None,"handles_closed":True,
            "active_processes_last_observed":0 if exit_value is not None else None,
            "errors":[] if exit_value is not None else ["UNCONFIRMED"]}
   observed={"actual_exit":exit_value,"job_cleanup":copy.deepcopy(cleanup),"timed_out":exit_value is None}
   invocation={"actual_exit":None,"observation":None}
   state={"phase":"bootstrap21","status":"STARTED","calls":[invocation],"first_failure":None}
   events=[]
   def observed_ref(path):
    events.append(str(path))
    if path==fault:raise OSError("injected_"+fault)
    return {"path":str(path),"sha256":"0"*64,"bytes":4}
   def save_new(path,value):
    events.append("result")
    if fault=="result":raise OSError("injected_result")
    return {"path":"synthetic-result","sha256":"1"*64,"bytes":7}
   class Helpers:
    @staticmethod
    def closed_job(observation):
     events.append("closed")
     if fault=="closed":raise RuntimeError("injected_closed")
   env={"invocation":invocation,"observed":observed,"time":FakeTime,"observed_ref":observed_ref,
        "stdout":"stdout","stderr":"stderr","save_new":save_new,"Path":FakePath,
        "paths":{"raw":"synthetic-only"},"helpers":Helpers,"state":state}
   exec(compiled,env)
   require(invocation["observation"] is observed and invocation["observation"]["job_cleanup"]==cleanup,"OBSERVED_CLEANUP_LOST")
   require(invocation["actual_exit"] is exit_value and invocation["ended_at_unix_ns"]==FakeTime.time_ns(),"EXIT_OR_END_LOST")
   require(state["status"]=="STOPPED_AT_FIRST_FAILURE" and state["first_failure"]["last_child_exit"] is exit_value,
           "FAILURE_STATE_DROPPED_EXIT")
   require(state["first_failure"]["Root_assignment_required"] is True
           and state["first_failure"]["original_ordinal"] is None,"NO_FABRICATED_ORDINAL")
   expected_fields={"stdout":set(),"stderr":{"stdout_ref"},"result":{"stdout_ref","stderr_ref"},
                    "closed":{"stdout_ref","stderr_ref","result_ref"}}[fault]
   require({k for k in invocation if k.endswith("_ref")}==expected_fields,"PARTIAL_OUTPUT_STATE")
   controls.append({"id":"exit_"+str(exit_value)+"_fault_"+fault,"passed":True,
        "actual_exit_retained":exit_value,"cleanup_retained":True,"ended_at_retained":True,
        "exception_status":"STOPPED_AT_FIRST_FAILURE","output_refs_retained":sorted(expected_fields),
        "pure_AST_only":True,"synthetic_not_product_evidence":True})
 facts["controls"]={"count":len(controls),"controls":controls,"old_author56_not_rerun":True,
                     "old_review_counterexample_not_rerun":True,"whole_leaf_not_executed":True}
 bindings=doc(Q/"Source-final-actual-host.index.json")["completed_tool_pairs"]
 actual=[]
 for row in bindings:
  binding=json.loads(held(row["binding_ref"]["path"]))
  raw=held(row["raw_ref"]["path"]);lines=raw.splitlines(keepends=True)
  require(len(lines)==3 and all(l.endswith(b"\n") for l in lines),"AUTHOR_THREE_RECORDS")
  records=[json.loads(l) for l in lines]
  require(records[0]["payload"]["id"]=="01a11cee-bf59-7a01-be0e-9f799f9b1084"
          and records[0]["payload"]["agent_path"]=="/root/backup_regression_resources","ACTUAL_SOURCE_AUTHOR")
  require(records[1]["payload"]["call_id"]==records[2]["payload"]["call_id"]==row["call_id"],"ACTUAL_CALL_OUTPUT_PAIR")
  require(binding["Root_issuer"] is False and binding["execution_grant"] is False
          and binding["formal_acceptance"] is False,"AUTHOR_NO_ROOT_AUTHORITY")
  with Path(binding["source_audit_path"]).open("rb") as stream:
   for line,offset,size,digest in zip(lines,binding["source_line_offsets"],binding["source_line_bytes"],binding["source_line_sha256"]):
    require(len(line)==size and sha(line)==digest and offset+size<=binding["source_prefix_bytes"],"ORIGINAL_LINE_PIN")
    stream.seek(offset);require(stream.read(size)==line,"ORIGINAL_AUTHOR_RANGE")
  actual.append({"call_id":row["call_id"],"original_ranges_match":True,"binding_ref":row["binding_ref"]})
 require(len(actual)==12,"AUTHOR_NEW_COMPLETED_PAIR_COUNT")
 facts["new_author_actual_pairs"]=actual
 for name in ("Source-revision.guard.closed.json","Source-full-closure.guard.closed.json"):
  value=doc(Q/name)
  require(value["closed"] is True and value["retained_handles_count"]==0 and value["errors"]==[],"AUTHOR_GUARD_NOT_CLOSED")
 facts["author_guards_closed"]=True
 for ordinal,outer,python in ((1119,1,None),(1120,1,1)):
  origin=doc(Q/("failure-origin."+str(ordinal)+".json"))
  require(origin["original_ordinal"]==ordinal and origin["actual_outer_exit"]==outer
          and origin["actual_python_exit"]==python and origin["counter_reset"] is False,"FAILED_PREFIX_EXIT_PRESERVATION")
 facts["preserved_failure_ordinals"]=[1119,1120]
 require(hdf["execution_grant"] is False and hdf["formal_acceptance"] is False
         and hdf["future_Root_scope_ref"] is None and hdf["future_runtime_qualification_ref"] is None,"NO_EXECUTION_GRANT")
 facts["prior_review_ref"]=olddecision
 facts["new_source_refs"]={k:hdf[k] for k in ("runner_ref","contract_ref")}
 facts["review_method"]="Delta-only: exact runner inverse and contract limited-key delta inherit prior approved static conditions; no old146/old56 rerun."
 write("delta-review.json",facts)
 write("source-inputs.json",{"references":refs,"copies":copies,"new_manifest_members":55,"prior146_not_reexecuted":True})
finally:
 close=guard.close();write("source-guard.closed.json",close)
 require(close["closed"] is True and close["retained_handles_count"]==0 and close["errors"]==[],"REVIEW_GUARD_NOT_CLOSED")
for ref in refs:require(pin(ref["path"])==ref,"SOURCE_DRIFT_AFTER_GUARD")
decision={
 "schema":"researchos.schema21-public-bootstrap-independent-source-decision.v1",
 "decision":"ACCEPTED_SOURCE_ONLY","reviewer_id":"codex:/root/attach_restore_independent_review",
 "source_author":"codex:/root/backup_regression_resources","source_hdf_ref":pin(Q/"HDF.json"),
 "source_mf_ref":pin(Q/"MF.json"),"runner_ref":pin(Q/"public21_runner.py"),"contract_ref":pin(Q/"contract.json"),
 "prior_review_ref":olddecision,"resolved_findings":["PUBLIC21-OBSERVATION-001"],"findings":[],
 "delta_review_ref":pin(N/"delta-review.json"),"guard_ref":pin(N/"source-guard.closed.json"),
 "exact_runner_inverse":True,"contract_delta_keys":["runner_ref","source_revision_basis","status"],
 "new_pure_AST_fault_controls":12,"retained_actual_exits":[0,1,None],"retained_cleanup_and_partial_output_state":True,
 "Native_Go_SQL_model_TP_calls":0,"Leaf_RootScope_calls":0,"old146_inputs_not_retested":True,
 "old56_controls_not_rerun":True,"old_counterexample_not_rerun":True,"execution_grant":False,
 "formal_acceptance":False,"parent_acceptance":False,
 "limit":"Candidate Source only. Root separately supplies genuine PUBLIC21_BOOTSTRAP_ONLY scope and runtime qualification; this review executes nothing."}
write("source-decision.json",decision)
print(json.dumps({"decision":decision["decision"],"inputs":len(refs),"controls":len(controls),
                  "new_author_pairs":len(actual),"decision_ref":pin(N/"source-decision.json")},ensure_ascii=False))

