import ast,copy,json,types
from pathlib import Path
O=Path(__file__).resolve().parent
intake=json.loads((O/"intake.json").read_bytes());rows=intake["rows"]
def raw(name):
 r=next(x for x in rows if Path(x["source_ref"]["path"]).name==name)
 return Path(r["snapshot_ref"]["path"]).read_bytes()
results=[]
def add(name,observed,expected=True,**details):
 results.append({"case":name,"observed":observed,"expected":expected,"matches_expected":observed==expected,**details})
# Reuse the exact previous reviewer's in-memory fixture harness before its test list.
prior=raw("canonical-controls.py").decode()
prefix=prior.split("\nresults=[]\n",1)[0]
ce={"__file__":str(O/"regression-controls.py")}
exec(compile(prefix,"<prior-independent-canonical-memory-fixture-prefix>","exec"),ce)
def reset_canonical():ce["reset"]()
def current_doc():return {"run_uuid":"b"*32,"root_registration":{"synthetic":"new-reg"},"data_root":"D:/review-only-isolated"}
def admit():
 try:
  ce["cenv"]["activate_canonical_lease"](current_doc(),{"synthetic":"new-lease"},ce["file_pin"](ce["paths"][0]),ce["file_pin"](ce["paths"][1]),ce["journal_dir"])
  return None
 except RuntimeError as exc:return str(exc)
reset_canonical();ce["fault"]["write_ownership"]=True
close_error=None
try:ce["cenv"]["close_canonical_lease"]({"run_uuid":ce["uuid"]},ce["journal_dir"],ce["good"],None)
except RuntimeError as exc:close_error=str(exc)
cp=json.loads(ce["files"][str(ce["paths"][0])]);ow=json.loads(ce["files"][str(ce["paths"][1])])
assert close_error is not None and cp["work_in_progress"]["mu_sdk_active_run_uuid"] is None
assert ow["card_path_bindings"]["W05-99"]["subtasks"]["mu_sdk_trial"]["state"]=="ACTIVE_ISOLATED_PHASE"
ce["fault"].clear();before=dict(ce["files"]);admission_error=admit()
add("C3_R01_ACTUAL_MEMORY_PARTIAL_CLOSE_THEN_FRESH_ADMISSION_REJECTS",admission_error is not None and ce["files"]==before,error=admission_error,partial_close_error=close_error,checkpoint_active=None,ownership_state="ACTIVE_ISOLATED_PHASE")
for state in ["CLOSED_PENDING_INDEPENDENT_EVIDENCE_REVIEW","FAILED_EXECUTION_CLOSED"]:
 reset_canonical();cp=copy.deepcopy(ce["cp0"]);cp["work_in_progress"].update(mu_sdk_active_run_uuid=None,mu_sdk_last_phase_uuid=ce["uuid"])
 ow=copy.deepcopy(ce["ow0"]);ow["card_path_bindings"]["W05-99"]["subtasks"]["mu_sdk_trial"]["state"]=state
 ce["files"][str(ce["paths"][0])]=ce["json_bytes"](cp);ce["files"][str(ce["paths"][1])]=ce["json_bytes"](ow)
 error=admit();add("CONSISTENT_"+state+"_ADMITS",error is None,error=error)
for case,record,last in [
 ("ACTIVE_OWNERSHIP",{"run_uuid":"a"*32,"state":"ACTIVE_ISOLATED_PHASE"},"a"*32),
 ("CLOSED_UUID_MISMATCH",{"run_uuid":"a"*32,"state":"FAILED_EXECUTION_CLOSED"},"c"*32),
 ("CLOSED_MISSING_RUN_UUID",{"state":"FAILED_EXECUTION_CLOSED"},"a"*32),
 ("MALFORMED_OWNERSHIP_RECORD",[],"a"*32)]:
 reset_canonical();cp=copy.deepcopy(ce["cp0"]);cp["work_in_progress"].update(mu_sdk_active_run_uuid=None,mu_sdk_last_phase_uuid=last)
 ow=copy.deepcopy(ce["ow0"]);ow["card_path_bindings"]["W05-99"]["subtasks"]["mu_sdk_trial"]=record
 ce["files"][str(ce["paths"][0])]=ce["json_bytes"](cp);ce["files"][str(ce["paths"][1])]=ce["json_bytes"](ow);before=dict(ce["files"])
 error=admit();add("REJECT_"+case,error is not None and ce["files"]==before,error=error)
# Reuse independent simulated clock/thread/handle fixture; no actual threading or WinAPI.
prefix=raw("watchdog-controls.py").decode().split("\nresults=[]\n",1)[0]
we={"__file__":str(O/"regression-controls.py")}
exec(compile(prefix,"<prior-independent-watchdog-memory-fixture-prefix>","exec"),we)
def wreset():
 we["clock"]["now"]=10.0;we["calls"].clear();we["thread_mode"].update(fail_start=False,refuse_join=False)
def wobj(**kw):
 o=we["obj"](**kw);o.thread_started=False
 return o
wreset();we["thread_mode"]["fail_start"]=True;o=wobj();start_error=close_error=None
try:o.start()
except RuntimeError as exc:start_error=str(exc)
try:observation=o.stop_and_close()
except RuntimeError as exc:close_error=str(exc)
add("C3_R02_THREAD_START_FAILURE_CLOSES_DUPLICATE_WITHOUT_JOIN",start_error is not None and close_error is None and o.handle is None and o.observation["duplicate_handle_closed"] and bool(o.observation["errors"]),start_error=start_error,close_error=close_error,observation=copy.deepcopy(o.observation),calls=list(we["calls"]))
wreset();o=wobj();o.start();o.thread.run_to_completion();observation=o.stop_and_close()
add("WATCHDOG_SUCCESS_TIMER_AND_CLOSE",observation["termination_succeeded"] is True and observation["duplicate_handle_closed"],observation=copy.deepcopy(observation))
wreset();o=wobj(close_ok=False);o.start();observation=o.stop_and_close()
add("WATCHDOG_CLOSE_FAILURE_RETAINS_AND_RECORDS",o.handle is not None and bool(observation["errors"]),observation=copy.deepcopy(observation))
controller=ast.parse(raw("controller.py"));inner=next(n for n in controller.body if isinstance(n,ast.FunctionDef) and n.name=="_launch_reviewed_phase_with_guard");outer=next(n for n in controller.body if isinstance(n,ast.FunctionDef) and n.name=="launch_reviewed_phase")
fin=next(n.finalbody for n in inner.body if isinstance(n,ast.Try) and n.finalbody)
watchdog_cleanup=fin[0]
# The exact watchdog cleanup block now catches cleanup exceptions instead of preventing later receipt sealing.
def raising_cleanup():raise RuntimeError("independent stop_and_close exception")
env={"watchdog":types.SimpleNamespace(stop_and_close=raising_cleanup),"error":None,"result":{"job_cleanup":{"errors":[],"active_processes_last_observed":0,"primary_exit_confirmed":True,"job_idle_confirmed":True,"handles_closed":True}}}
exec(compile(ast.Module(body=[watchdog_cleanup],type_ignores=[]),"<C4 exact watchdog finally block>","exec"),env)
add("C3_R02_CLEANUP_EXCEPTION_RECORDED_NO_ESCAPE",bool(env["result"]["job_cleanup"]["errors"]) and env["watchdog_observation"]["duplicate_handle_closed"] is False,observation=env["watchdog_observation"],error=env["error"])
# Exact two source-guard finalization blocks with no OS, Job, module import, real filesystem or process.
source_index=next(i for i,n in enumerate(fin) if isinstance(n,ast.Try) and any(isinstance(c,ast.Call) and isinstance(c.func,ast.Attribute) and isinstance(c.func.value,ast.Name) and c.func.value.id=="source_guard" and c.func.attr=="close" for c in ast.walk(n)))
source_block=fin[source_index:source_index+2]
outer_fin=next(n.finalbody for n in outer.body if isinstance(n,ast.Try))
class Guard:
 def __init__(self):self.held=True;self.close_calls=0
 def close(self):
  self.close_calls+=1;self.held=False
  return {"closed":True,"errors":[],"retained_handles_count":0}
def guard_lifecycle(case,result,should_hold):
 guard=Guard();env={"source_guard":guard,"guard":guard,"result":copy.deepcopy(result),"error":None}
 exec(compile(ast.Module(body=source_block,type_ignores=[]),"<C4 source-close finally AST>","exec"),env)
 after_inner={"held":guard.held,"close_calls":guard.close_calls}
 exec(compile(ast.Module(body=outer_fin,type_ignores=[]),"<C4 outer unconditional finally AST>","exec"),env)
 add(case,guard.held,should_hold,after_inner=after_inner,after_outer={"held":guard.held,"close_calls":guard.close_calls},native_result=result,scope="Pure finalization AST; no real Job or source-file mutation performed.")
good={"job_cleanup":{"errors":[],"active_processes_last_observed":0,"primary_exit_confirmed":True,"job_idle_confirmed":True,"handles_closed":True}}
guard_lifecycle("CONFIRMED_JOB_CLEANUP_RELEASES_SOURCE_GUARD",good,False)
live=copy.deepcopy(good);live["job_cleanup"].update(active_processes_last_observed=1,job_idle_confirmed=False,handles_closed=False)
guard_lifecycle("LIVE_CHILD_UNCONFIRMED_JOB_MUST_KEEP_SOURCE_GUARD",live,True)
guard_lifecycle("MISSING_NATIVE_RESULT_MUST_NOT_RELEASE_POSSIBLY_LIVE_SOURCE_CONSUMERS",None,True)
# Guard-close failures must mark the result unfit for canonical lease release.
class BadGuard:
 def close(self):return {"closed":False,"errors":[{"stage":"CloseHandle"}],"retained_handles_count":1}
env={"source_guard":BadGuard(),"result":copy.deepcopy(good),"error":None}
exec(compile(ast.Module(body=source_block,type_ignores=[]),"<C4 source-close failure AST>","exec"),env)
add("SOURCE_GUARD_CLOSE_FAILURE_BLOCKS_CANONICAL_RELEASE",bool(env["result"]["job_cleanup"]["errors"]) and not ce["cenv"]["cleanup_confirmed"](env["result"]),result=env["result"],error=env["error"])
report={"schema":"researchos.c4-independent-pure-regression-controls.v1","cases":results,"summary":{"total":len(results),"matched":sum(r["matches_expected"] for r in results),"mismatches":[r["case"] for r in results if not r["matches_expected"]]},"prior_independent_fixture_prefixes_reused":["canonical-controls.py before results=[]","watchdog-controls.py before results=[]"],"candidate_code_boundary":"Selected AST functions, class methods and exact finally blocks only; all OS/thread/time/path/process/transaction operations use independent deterministic memory substitutes.","actual_WinAPI_calls":0,"actual_threads_started":0,"candidate_module_imports":0,"candidate_actual_entry_calls":0,"real_canonical_access":False,"provider_requests":0}
(O/"regression-controls.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(report["summary"],ensure_ascii=False,indent=2))

