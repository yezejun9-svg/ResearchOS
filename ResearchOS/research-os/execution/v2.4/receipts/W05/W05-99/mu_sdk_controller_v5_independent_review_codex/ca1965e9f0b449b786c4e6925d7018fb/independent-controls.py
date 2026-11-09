import ast,copy,json,math,types
from pathlib import Path
O=Path(__file__).resolve().parent
intake=json.loads((O/"intake.json").read_bytes())
source=Path(intake["source_ref"]["path"]).read_bytes();tree=ast.parse(source)
clock={"now":100.0};pid={"value":2222};trace=[]
class MemoryLock:
 def __enter__(self):return self
 def __exit__(self,*args):return False
fake_sys=types.SimpleNamespace()
env={"os":types.SimpleNamespace(getpid=lambda:pid["value"]),"threading":types.SimpleNamespace(RLock=MemoryLock),"time":types.SimpleNamespace(monotonic=lambda:clock["now"]),"sys":fake_sys}
names={"require","cleanup_confirmed","ResidentSourceOwner","get_resident_source_owner","_require_source_owner","_append_cleanup_error","source_retention_status","reconcile_retained_sources"}
selected=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names]
selected+=[n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="_RESIDENT_OWNER_ATTR" for t in n.targets)]
exec(compile(ast.Module(body=selected,type_ignores=[]),"<C5 selected lifecycle AST, fake PID/clock/lock/sys only>","exec"),env)
class Guard:
 def __init__(self,fail_close=False):
  self.close_calls=0;self.fail_close=fail_close
  self._entries=[{"handle":n,"closed":False} for n in range(1,4)]
 def close(self):
  self.close_calls+=1;trace.append("guard.close")
  if self.fail_close:return {"closed":False,"retained_handles_count":3,"errors":["independent fake close failure"]}
  for e in self._entries:e.update(handle=None,closed=True)
  return {"closed":True,"retained_handles_count":0,"errors":[]}
class Watchdog:
 def __init__(self,fail_close=False):
  self.close_calls=0;self.fail_close=fail_close;self.observation={"errors":[]}
 def stop_and_close(self):
  self.close_calls+=1;trace.append("watchdog.stop_and_close")
  return {"duplicate_handle_closed":not self.fail_close,"errors":["fake duplicate close failure"] if self.fail_close else []}
run_uuid="a"*32
def reset():
 fake_sys.__dict__.clear();pid["value"]=2222;clock["now"]=100.0;trace.clear()
 return env["get_resident_source_owner"]()
def setup(native=True,retained=False,guard_fail=False,watchdog_fail=False):
 owner=reset();guard=Guard(guard_fail);watchdog=Watchdog(watchdog_fail)
 owner.reserve(run_uuid,guard)
 if native:owner.invoked(run_uuid);owner.attach_watchdog(run_uuid,watchdog)
 if retained:owner.retain(run_uuid,"independent retained setup")
 return owner,guard,watchdog
good={"actual_exit":0,"timed_out":False,"error":None,"job_cleanup":{"errors":[],"active_processes_last_observed":0,"primary_exit_confirmed":True,"job_idle_confirmed":True,"handles_closed":True}}
cases=[]
def add(name,observed,expected=True,**detail):
 cases.append({"case":name,"observed":observed,"expected":expected,"matches_expected":observed==expected,**detail})
inner=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="_launch_reviewed_phase_with_guard")
outer=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="launch_reviewed_phase")
fin=next(n.finalbody for n in inner.body if isinstance(n,ast.Try) and n.finalbody)
stop_index=next(i for i,n in enumerate(fin) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Attribute) and isinstance(n.value.func.value,ast.Name) and n.value.func.value.id=="stop_heartbeat")
cleanup_ast=fin[:stop_index]
outer_final=next(n.finalbody for n in outer.body if isinstance(n,ast.Try) and n.finalbody)
def finalize(name,result,native=True,activated=False,guard_fail=False,watchdog_fail=False,expect_retained=True):
 owner,guard,watchdog=setup(native=native,guard_fail=guard_fail,watchdog_fail=watchdog_fail)
 def fake_module(ref,name):
  trace.append("transaction.module.while_guarded")
  assert any(e["handle"] is not None for e in guard._entries)
  return types.SimpleNamespace()
 e=dict(env,source_owner=owner,source_guard=guard,guard=guard,doc={"run_uuid":run_uuid},run_uuid=run_uuid,result=copy.deepcopy(result),error=None,watchdog=watchdog if native else None,activated=activated,module=fake_module,CANONICAL_TRANSACTION_REF={"synthetic":"already independently byte verified"})
 exec(compile(ast.Module(body=cleanup_ast,type_ignores=[]),"<C5 inner cleanup AST only>","exec"),e)
 exec(compile(ast.Module(body=outer_final,type_ignores=[]),"<C5 outer finalization AST only>","exec"),e)
 record=owner.record(run_uuid);retained=record is not None
 add(name,retained,expect_retained,guard_close_calls=guard.close_calls,watchdog_close_calls=watchdog.close_calls,state=record["state"] if record else "RELEASED",source_observation=e.get("source_guard_observation"),trace=list(trace))
 return owner,guard,watchdog,e
for name,result in [
 ("C4_MISSING_RESULT_NOW_RETAINS",None),
 ("C4_LIVE_CHILD_NOW_RETAINS",{"job_cleanup":{**good["job_cleanup"],"active_processes_last_observed":1,"job_idle_confirmed":False,"handles_closed":False}}),
 ("NATIVE_CLEANUP_ERROR_RETAINS",{"job_cleanup":{**good["job_cleanup"],"errors":["unconfirmed close"]}}),
 ("BOOL_FALSE_ACTIVE_COUNT_REJECTS",{"job_cleanup":{**good["job_cleanup"],"active_processes_last_observed":False}}),
 ("FLOAT_ZERO_ACTIVE_COUNT_REJECTS",{"job_cleanup":{**good["job_cleanup"],"active_processes_last_observed":0.0}})]:
 owner,guard,watchdog,e=finalize(name,result)
 assert guard.close_calls==0 and watchdog.close_calls==0 and owner.record(run_uuid)["guard"] is guard
 assert env["get_resident_source_owner"]() is owner
finalize("CONFIRMED_NATIVE_CLEANUP_RELEASES",good,activated=True,expect_retained=False)
assert trace.index("transaction.module.while_guarded")<trace.index("guard.close")
finalize("PRE_NATIVE_FAILURE_RELEASES",None,native=False,expect_retained=False)
finalize("NATIVE_GUARD_CLOSE_FAILURE_RETAINS",good,guard_fail=True)
finalize("NATIVE_WATCHDOG_CLOSE_FAILURE_RETAINS",good,watchdog_fail=True)
# Interrupted inner finalization is handled by the outer boundary, without close.
owner,guard,watchdog=setup(native=True)
e=dict(env,source_owner=owner,guard=guard,run_uuid=run_uuid)
exec(compile(ast.Module(body=outer_final,type_ignores=[]),"<C5 outer interrupted-finalization AST>","exec"),e)
add("INTERRUPTED_NATIVE_FINALIZATION_RETAINS",owner.record(run_uuid)["state"]=="RETAINED_UNCONFIRMED" and guard.close_calls==0 and watchdog.close_calls==0)
owner,guard,watchdog=setup(native=False,guard_fail=True)
e=dict(env,source_owner=owner,guard=guard,run_uuid=run_uuid)
exec(compile(ast.Module(body=outer_final,type_ignores=[]),"<C5 outer pre-native-close failure AST>","exec"),e)
add("PRE_NATIVE_OUTER_CLOSE_FAILURE_RETAINS",owner.record(run_uuid)["state"]=="RETAINED_UNCONFIRMED" and guard.close_calls==1)
def proof(owner,when=100.0):
 return {"run_uuid":run_uuid,"owner_pid":owner.owner_pid,"observed_monotonic":when,"native_result":copy.deepcopy(good)}
def reconcile_case(name,make_proof=None,expected_release=False,owner_pid=2222,native=True,callback=True):
 owner,guard,watchdog=setup(native=native,retained=True)
 p=proof(owner) if make_proof is None else make_proof(owner)
 supplied=(lambda **kwargs:copy.deepcopy(p)) if callback else None
 before=dict(owner.record(run_uuid));error=None;result=None
 try:result=env["reconcile_retained_sources"](run_uuid,owner_pid,owner,supplied)
 except RuntimeError as exc:error=str(exc)
 released=owner.record(run_uuid) is None
 add(name,released,expected_release,error=error,result=result,proof=p,guard_close_calls=guard.close_calls,watchdog_close_calls=watchdog.close_calls,clock_now=clock["now"],retained_monotonic=before["retained_monotonic"])
reconcile_case("RECONCILE_VALID_INTERFACE_SHAPE_SYNTHETIC_POSITIVE",expected_release=True)
reconcile_case("RECONCILE_REQUIRES_CALLBACK",callback=False)
reconcile_case("RECONCILE_WRONG_CALLER_PID",owner_pid=2223)
reconcile_case("RECONCILE_WRONG_PROOF_RUN",lambda o:{**proof(o),"run_uuid":"b"*32})
reconcile_case("RECONCILE_WRONG_PROOF_OWNER",lambda o:{**proof(o),"owner_pid":2223})
reconcile_case("RECONCILE_OBSERVATION_BEFORE_RETENTION",lambda o:proof(o,99.0))
reconcile_case("RECONCILE_ACTIVE_CHILD_PROOF_REJECTS",lambda o:{**proof(o),"native_result":{"job_cleanup":{**good["job_cleanup"],"active_processes_last_observed":1}}})
reconcile_case("RECONCILE_FUTURE_OBSERVATION_MUST_REJECT",lambda o:proof(o,1000000.0))
# JSON does not encode Infinity portably, so retain finite evidence in the formal controls.
reconcile_case("RECONCILE_UNBOUND_CALLBACK_SOURCE_MUST_NOT_RELEASE",lambda o:{**proof(o),"probe_source_ref":{"path":"D:/foreign/unreviewed.py","sha256":"f"*64,"bytes":1},"owned_job_identity":{"pid":98765,"creation_time_100ns":1}})
owner,guard,watchdog=setup(native=False,retained=True)
result=env["reconcile_retained_sources"](run_uuid,2222,owner,None)
add("PRE_NATIVE_RECONCILE_DOES_NOT_REQUIRE_JOB_PROOF",owner.record(run_uuid) is None and result["state"]=="RELEASED_AFTER_CONFIRMED_CLEANUP")
owner,guard,watchdog=setup(native=True,retained=True);pid["value"]=2223;error=None
try:env["source_retention_status"](run_uuid,owner)
except RuntimeError as exc:error=str(exc)
add("RESIDENT_OWNER_REJECTS_OTHER_PID",error is not None and guard.close_calls==0,error=error)
pid["value"]=2222
# New author provenance regression: exercise exact C5 gate and unchanged O3 validator.
gate=next(n for n in outer.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and len(n.value.args)>1 and isinstance(n.value.args[1],ast.Constant) and n.value.args[1].value=="independent exact Source review required before import")
gate_code=compile(ast.Expression(body=gate.value.args[0]),"<C5 exact independent-review guard>","eval")
obtree=ast.parse(Path(intake["tuple"]["observer_source_ref"]["path"]).read_bytes())
obsenv={}
for n in obtree.body:
 if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ("ROOT_ACTOR","AUTHOR","ACTOR","RUNNER_REF"):
  obsenv[n.targets[0].id]=ast.literal_eval(n.value)
obsenv["require"]=env["require"]
obsfn=next(n for n in obtree.body if isinstance(n,ast.FunctionDef) and n.name=="validate_source_review")
exec(compile(ast.Module(body=[obsfn],type_ignores=[]),"<unchanged O3 exact reviewer-identity gate only>","exec"),obsenv)
t=intake["tuple"]
review={"schema":"researchos.mu-sdk-controller-observer-independent-source-review.v2","decision":"READY_SOURCE_ONLY","actor_id":intake["source_author"],"formal_acceptance":False,"callback_contract":"REAL_ASSIGNED_SUSPENDED_FRAME_BEFORE_FIRST_RESUME",**copy.deepcopy(t)}
context={"controller_source":t["controller_source_ref"],"observer_source":t["observer_source_ref"],"hooks_source":t["hooks_source_ref"],"phase_worker_source":t["phase_worker_source_ref"],"python_binary":t["python_binary_ref"]}
for actor,expected in [(intake["source_author"],False),("codex:/root/command_queue_impl",True),("codex:/root",False),("codex:/root/w05_merge_review",False)]:
 review["actor_id"]=actor
 root_gate=eval(gate_code,{"__builtins__":{}},{"review":review})
 observer_gate=True
 try:obsenv["validate_source_review"](review,context)
 except RuntimeError:observer_gate=False
 add("CURRENT_AUTHOR_PROVENANCE_"+actor,root_gate and observer_gate,expected,controller_accepted=root_gate,observer_accepted=observer_gate,source_author=intake["source_author"])
report={"schema":"researchos.c5-independent-lifecycle-and-provenance-controls.v1","cases":cases,"summary":{"total":len(cases),"matched":sum(c["matches_expected"] for c in cases),"counterexamples":[c["case"] for c in cases if not c["matches_expected"]]},"proof_boundary":"Selected lifecycle/class methods, finalization blocks and review predicates only. Fake sys namespace/PID/clock/RLock/guard/watchdog/transaction replace all OS and process operations. Reconcile synthetic positive means interface shape only, not real cleanup.","candidate_module_imports":0,"real_threads_or_WinAPI_calls":0,"actual_candidate_entry_calls":0,"native_SQL_provider_calls":0,"Main_canonical_writes":0,"author_controls_executed":0}
(O/"independent-controls.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(report["summary"],ensure_ascii=False,indent=2))

