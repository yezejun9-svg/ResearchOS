import ast,copy,json,math,types
from pathlib import Path
O=Path(__file__).resolve().parent
intake=json.loads((O/"intake.json").read_bytes())
cr=Path(intake["tuple"]["controller_source_ref"]["path"]).read_bytes();ct=ast.parse(cr)
orr=Path(intake["tuple"]["observer_source_ref"]["path"]).read_bytes();ot=ast.parse(orr)
pr=Path(intake["tuple"]["cleanup_producer_source_ref"]["path"]).read_bytes();pt=ast.parse(pr)
clock={"now":100.0};pid={"value":2222};trace=[];cases=[]
class MemoryLock:
 def __enter__(self):return self
 def __exit__(self,*a):return False
fake_sys=types.SimpleNamespace()
env={"os":types.SimpleNamespace(getpid=lambda:pid["value"]),"threading":types.SimpleNamespace(RLock=MemoryLock),
 "time":types.SimpleNamespace(monotonic=lambda:clock["now"]),"sys":fake_sys}
wanted={"require","cleanup_confirmed","ResidentSourceOwner","get_resident_source_owner","_require_source_owner",
 "_append_cleanup_error","source_retention_status","reconcile_retained_sources","expected_source_provenance","require_non_author","validate_review_actor"}
nodes=[n for n in ct.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in wanted]
nodes += [n for n in ct.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="_RESIDENT_OWNER_ATTR" for t in n.targets)]
exec(compile(ast.Module(body=nodes,type_ignores=[]),"<C6 selected lifecycle and provenance AST>","exec"),env)
p_env={"os":env["os"],"time":env["time"],"uuid":types.SimpleNamespace(uuid4=lambda:types.SimpleNamespace(hex="b"*32))}
pclass=next(n for n in pt.body if isinstance(n,ast.ClassDef) and n.name=="HeldJobCleanupProducer")
exec(compile(ast.Module(body=[pclass],type_ignores=[]),"<C6 producer class AST with fake kernel only>","exec"),p_env)
obsenv={}
for n in ot.body:
 if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in (
  "SOURCE_AUTHOR_POLICY","SOURCE_PROVENANCE_SCHEMA","RUNNER_REF","AUTHOR","ROOT_ACTOR","ACTOR"):
  obsenv[n.targets[0].id]=ast.literal_eval(n.value)
obsnodes=[n for n in ot.body if isinstance(n,ast.FunctionDef) and n.name in ("require","source_author_provenance","validate_source_review")]
exec(compile(ast.Module(body=obsnodes,type_ignores=[]),"<O4 pure provenance gate AST>","exec"),obsenv)
def add(name,observed,expected=True,**details):
 cases.append({"case":name,"observed":observed,"expected":expected,"matches_expected":observed==expected,**details})
def capture_error(fn):
 try:fn();return None
 except Exception as e:return {"type":type(e).__name__,"message":str(e)}
context=copy.deepcopy(intake["source_context"])
prov=env["expected_source_provenance"](context)
add("FIXED_ELEVEN_ROLE_POLICY_MATCHES_C6_O4",prov==obsenv["source_author_provenance"](context) and len(prov["sources"])==11)
review={"schema":"researchos.mu-sdk-controller-observer-independent-source-review.v2","decision":"READY_SOURCE_ONLY",
 "actor_id":"codex:/root/command_queue_impl","formal_acceptance":False,
 "callback_contract":"REAL_ASSIGNED_SUSPENDED_FRAME_BEFORE_FIRST_RESUME","source_provenance":prov,**intake["tuple"]}
for actor,allowed in (("codex:/root/command_queue_impl",True),("codex:/root",False),
 ("codex:/root/live_resource_lookup",False),("codex:/root/w05_merge_review",False),
 ("program:researchos.mu-sdk-job-observer.v1",False)):
 value={**review,"actor_id":actor}
 ce=capture_error(lambda:env["validate_review_actor"](value,context))
 oe=capture_error(lambda:obsenv["validate_source_review"](value,context))
 add("AUTHOR_POLICY_"+actor,ce is None and oe is None,allowed,controller_error=ce,observer_error=oe)
for mode in ("erase_author","swap_source","remove_role"):
 value=copy.deepcopy(review)
 if mode=="erase_author":value["source_provenance"]["sources"]["controller"]["authors"]=[]
 if mode=="swap_source":value["source_provenance"]["sources"]["cleanup_producer"]["source_ref"]["sha256"]="f"*64
 if mode=="remove_role":del value["source_provenance"]["sources"]["base_owned"]
 ce=capture_error(lambda:env["validate_review_actor"](value,context))
 oe=capture_error(lambda:obsenv["validate_source_review"](value,context))
 add("PROVENANCE_MUTATION_REJECT_"+mode,ce is not None and oe is not None)
# Evaluate the exact dict expression built by the real before_resume callback.
inner=next(n for n in ct.body if isinstance(n,ast.FunctionDef) and n.name=="_launch_reviewed_phase_with_guard")
outer=next(n for n in ct.body if isinstance(n,ast.FunctionDef) and n.name=="launch_reviewed_phase")
callback=next(n for n in inner.body if isinstance(n,ast.FunctionDef) and n.name=="before_resume")
context_assignment=next(n for n in callback.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="context" for t in n.targets))
C=Path(intake["tuple"]["controller_source_ref"]["path"]).parent
byname={Path(v["path"]).name:v for v in context.values()}
caller_env={"doc":{"outer_job_contract":{"synthetic":True}},"controller_ref":context["controller_source"],
 "pin":lambda p:copy.deepcopy(byname[Path(p).name]),"HERE":C,"phase_dir":Path("D:/synthetic-not-created"),
 "public_env":{},"CLEANUP_PRODUCER_REF":context["cleanup_producer_source"],
 "seed":{"observer_source":context["observer_source"],"controller_source_review":{"synthetic":True},"python_binary":context["python_binary"]}}
actual_context=eval(compile(ast.Expression(context_assignment.value),"<exact C6 callback context dict>","eval"),caller_env)
callback_error=capture_error(lambda:obsenv["validate_source_review"](review,actual_context))
missing=sorted(set(context)-{"runner_source"}-set(actual_context))
add("ACTUAL_C6_CALLBACK_CONTEXT_MUST_SATISFY_O4",callback_error is None,True,
 error=callback_error,missing_required_source_keys=missing,controller_line=context_assignment.lineno,
 scope="Exact Source dict expression and exact O4 gate; synthetic values only for unrelated runtime fields.")
# Supplying the four missing reviewed pins is a diagnostic only, never a Source patch or READY claim.
diagnostic_context={**actual_context,**{k:context[k] for k in missing}}
add("DIAGNOSTIC_COMPLETE_CONTEXT_PASSES_O4",capture_error(lambda:obsenv["validate_source_review"](review,diagnostic_context)) is None)
class Guard:
 def __init__(self,fail=False):
  self.fail=fail;self.close_calls=0;self._entries=[{"handle":41,"closed":False}]
 def close(self):
  self.close_calls+=1;trace.append("guard.close")
  if self.fail:return {"closed":False,"retained_handles_count":1,"errors":["fake close failure"]}
  for row in self._entries:row.update(handle=None,closed=True)
  return {"closed":True,"retained_handles_count":0,"errors":[]}
class Watchdog:
 def __init__(self,fail=False):
  self.fail=fail;self.close_calls=0;self.observation={"errors":[]}
 def stop_and_close(self):
  self.close_calls+=1;trace.append("watchdog.stop_and_close")
  return {"duplicate_handle_closed":not self.fail,"errors":["fake close failure"] if self.fail else []}
class Kernel:
 def __init__(self):
  self.pid=3333;self.creation=778899;self.active=0;self.signaled=True;self.member=True
  self.duplicate_calls=[];self.closed=[];self.close_fail=set();self.query_fail=False;self.duplicate_fail_call=None
 def duplicate(self,handle):
  self.duplicate_calls.append(handle)
  if self.duplicate_fail_call==len(self.duplicate_calls):raise OSError("synthetic DuplicateHandle failure")
  return handle+10000
 def process_id(self,h):return self.pid
 def creation_time_100ns(self,h):return self.creation
 def in_job(self,p,j):return self.member
 def active_processes(self,j):
  if self.query_fail:raise OSError("synthetic QueryInformationJobObject failure")
  return self.active
 def primary_exit(self,p):return self.signaled,259 if self.signaled else None
 def close(self,h):
  trace.append("producer.close."+str(h))
  if h in self.close_fail:raise OSError("synthetic CloseHandle failure")
  self.closed.append(h)
run="a"*32
def reset():
 fake_sys.__dict__.clear();pid["value"]=2222;clock["now"]=100.0;trace.clear()
 return env["get_resident_source_owner"]()
def new_producer(kernel=None):
 kernel=kernel or Kernel()
 producer=p_env["HeldJobCleanupProducer"](run,2222,lambda:kernel)
 actual={"assigned_before_resume":True,"kill_on_job_close_configured":True,"resumed":False,
 "runner_pid":3333,"creation_time_100ns":778899,"job_handle":51,"process_handle":52}
 return producer,actual,kernel
def setup(native=True,retained=False,guard_fail=False,watchdog_fail=False,captured=True):
 owner=reset();guard=Guard(guard_fail);watchdog=Watchdog(watchdog_fail);producer=None;kernel=None
 owner.reserve(run,guard)
 if native:
  owner.invoked(run);producer,actual,kernel=new_producer();owner.attach_producer(run,producer)
  if captured:owner.bind_job_identity(run,producer.capture_before_resume(actual))
  owner.attach_watchdog(run,watchdog)
 if retained:owner.retain(run,"synthetic unconfirmed cleanup")
 return owner,guard,watchdog,producer,kernel
producer,actual,kernel=new_producer();identity=producer.capture_before_resume(actual)
add("CAPTURE_BINDS_DUPLICATED_EXACT_JOB_PRIMARY",kernel.duplicate_calls==[51,52] and identity["runner_pid"]==3333 and identity["creation_time_100ns"]==778899 and identity["captured_before_resume"])
add("CAPTURE_ONE_SHOT",capture_error(lambda:producer.capture_before_resume(actual)) is not None)
for field,value in (("resumed",True),("assigned_before_resume",False),("kill_on_job_close_configured",False),("runner_pid",True),("process_handle",0)):
 p,a,k=new_producer();a[field]=value;e=capture_error(lambda:p.capture_before_resume(a))
 add("INVALID_CAPTURE_"+field,e is not None and k.duplicate_calls==[],error=e)
for field,value in (("pid",3334),("creation",778900),("member",False)):
 p,a,k=new_producer();setattr(k,field,value);e=capture_error(lambda:p.capture_before_resume(a))
 add("MISMATCH_CAPTURE_RETAINS_DUPLICATES_"+field,e is not None and p.job_handle==10051 and p.primary_handle==10052 and not p._captured)
 p.close()
p,a,k=new_producer();k.duplicate_fail_call=2
e=capture_error(lambda:p.capture_before_resume(a))
add("PARTIAL_CAPTURE_RETAINS_FIRST_DUPLICATE",e is not None and p.job_handle==10051 and p.primary_handle is None)
add("PARTIAL_CAPTURE_CLOSE_CAN_RECOVER",p.close()["closed"] and k.closed==[10051])
def reconcile_case(name,mutate=None,expected=False):
 owner,guard,watchdog,p,k=setup(native=True,retained=True)
 if mutate:mutate(owner,guard,watchdog,p,k)
 result=None;error=None
 try:result=env["reconcile_retained_sources"](run,2222,owner)
 except Exception as ex:error={"type":type(ex).__name__,"message":str(ex)}
 released=owner.record(run) is None
 add(name,released,expected,error=error,result=result,guard_close_calls=guard.close_calls,
  watchdog_close_calls=watchdog.close_calls,producer_handles=[p.job_handle,p.primary_handle],trace=list(trace))
 return owner,guard,watchdog,p,k,result
reconcile_case("FRESH_EXACT_OS_PROOF_RELEASES",expected=True)
for field,value in (("active",1),("active",False),("active",0.0),("signaled",False),("pid",3334),("creation",778900),("query_fail",True)):
 reconcile_case("RECONCILE_REJECTS_"+field+"_"+str(value),lambda o,g,w,p,k,f=field,v=value:setattr(k,f,v))
def altered_proof(field,value):
 def mutate(o,g,w,p,k):
  original=p.observe_current
  def observe():
   proof=original();proof[field]=value;return proof
  p.observe_current=observe
 return mutate
for field,value in (("run_uuid","c"*32),("owner_pid",2223),("runner_pid",3334),("creation_time_100ns",778900),("job_binding_id","d"*32),
 ("observed_monotonic",99.0),("observed_monotonic",101.0),("observed_monotonic",float("nan")),
 ("observed_monotonic",float("inf")),("observed_monotonic",float("-inf")),("observed_monotonic",True)):
 reconcile_case("RECONCILE_REJECTS_PROOF_"+field+"_"+str(value),altered_proof(field,value))
def slow(o,g,w,p,k):
 original=p.observe_current
 def observe():
  result=original();clock["now"]=103.0;result["observed_monotonic"]=103.0;return result
 p.observe_current=observe
reconcile_case("RECONCILE_REJECTS_SLOW_OS_PROOF",slow)
o,g,w,p,k,result=reconcile_case("RECONCILE_WATCHDOG_CLOSE_FAILURE_RETAINS",lambda o,g,w,p,k:setattr(w,"fail",True))
add("WATCHDOG_CLOSE_FAILURE_PRESERVES_GUARD_PRODUCER",g.close_calls==0 and p.job_handle==10051 and p.primary_handle==10052)
o,g,w,p,k,result=reconcile_case("RECONCILE_GUARD_CLOSE_FAILURE_RETAINS",lambda o,g,w,p,k:setattr(g,"fail",True))
add("GUARD_CLOSE_FAILURE_PRESERVES_PRODUCER",p.job_handle==10051 and p.primary_handle==10052)
o,g,w,p,k,result=reconcile_case("RECONCILE_PRODUCER_PARTIAL_CLOSE_RETAINS",lambda o,g,w,p,k:k.close_fail.add(10051))
add("FAILED_CLOSE_RETAINS_ONLY_FAILED_HANDLE",p.job_handle==10051 and p.primary_handle is None and o.record(run)["guard_released"])
k.close_fail.clear();result=env["reconcile_retained_sources"](run,2222,o)
add("FAILED_CLOSE_RETRY_RELEASES_NO_DOUBLE_CLOSE",o.record(run) is None and k.closed.count(10052)==1 and k.closed.count(10051)==1 and g.close_calls==1,result=result)
o,g,w,p,k=setup(native=False,retained=True);result=env["reconcile_retained_sources"](run,2222,o)
add("PRE_NATIVE_RECONCILE_RELEASES_WITHOUT_PRODUCER",o.record(run) is None and result["current_cleanup_proof"]["native_invoked"] is False)
o,g,w,p,k=setup(native=True,retained=True,captured=False)
e=capture_error(lambda:env["reconcile_retained_sources"](run,2222,o))
add("MISSING_CAPTURE_STAYS_RETAINED",e is not None and g.close_calls==0 and w.close_calls==0)
e=capture_error(lambda:env["reconcile_retained_sources"](run,2222,o,lambda:{"forged":True}))
add("CALLER_CALLBACK_REMOVED_FROM_INTERFACE",e is not None and e["type"]=="TypeError")
# Execute only original finalization AST; no candidate entrypoint, filesystem or OS operations.
fin=next(n.finalbody for n in inner.body if isinstance(n,ast.Try) and n.finalbody)
stop=next(i for i,n in enumerate(fin) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Attribute) and isinstance(n.value.func.value,ast.Name) and n.value.func.value.id=="stop_heartbeat")
cleanup_ast=fin[:stop]
outer_fin=next(n.finalbody for n in outer.body if isinstance(n,ast.Try) and n.finalbody)
good={"actual_exit":0,"timed_out":False,"error":None,"job_cleanup":{"errors":[],"active_processes_last_observed":0,"primary_exit_confirmed":True,"job_idle_confirmed":True,"handles_closed":True}}
def finalize(name,result,native=True,expected_retained=False,watchdog_fail=False,guard_fail=False,producer_close_fail=False):
 owner,guard,watchdog,p,k=setup(native=native,guard_fail=guard_fail,watchdog_fail=watchdog_fail)
 if producer_close_fail:k.close_fail.add(10051)
 def fake_module(*args):
  trace.append("transaction.module.while_guarded");assert not owner.record(run)["guard_released"];return types.SimpleNamespace()
 e=dict(env,source_owner=owner,source_guard=guard,guard=guard,doc={"run_uuid":run},run_uuid=run,
  result=copy.deepcopy(result),error=None,watchdog=watchdog if native else None,activated=True,
  producer=p,producer_observation=None,module=fake_module,CANONICAL_TRANSACTION_REF={})
 exec(compile(ast.Module(body=cleanup_ast,type_ignores=[]),"<exact C6 finally AST to heartbeat stop>","exec"),e)
 exec(compile(ast.Module(body=outer_fin,type_ignores=[]),"<exact C6 outer finally AST>","exec"),e)
 retained=owner.record(run) is not None
 add(name,retained,expected_retained,guard_close_calls=guard.close_calls,watchdog_close_calls=watchdog.close_calls,
  producer_closed=[] if k is None else k.closed,state=owner.record(run)["state"] if retained else "RELEASED",trace=list(trace))
 return owner,guard,watchdog,p,k
finalize("NORMAL_FINALLY_RELEASES_ALL_DUPLICATES",good)
add("NORMAL_CLOSE_ORDER_PRESERVES_TRANSACTION_SOURCE",trace.index("transaction.module.while_guarded")<trace.index("guard.close")<trace.index("producer.close.10052"))
for label,result in (("NONE",None),("LIVE_CHILD",{"job_cleanup":{**good["job_cleanup"],"active_processes_last_observed":1,"job_idle_confirmed":False}})):
 o,g,w,p,k=finalize("FINALLY_"+label+"_RETAINS_ALL",result,expected_retained=True)
 add("FINALLY_"+label+"_NO_EARLY_CLOSE",g.close_calls==0 and w.close_calls==0 and k.closed==[] and o.record(run)["producer"] is p)
finalize("PRE_NATIVE_FINALLY_CLOSES_GUARD",None,native=False)
finalize("WATCHDOG_FINAL_CLOSE_FAILURE_RETAINS",good,watchdog_fail=True,expected_retained=True)
finalize("GUARD_FINAL_CLOSE_FAILURE_RETAINS",good,guard_fail=True,expected_retained=True)
finalize("PRODUCER_FINAL_CLOSE_FAILURE_RETAINS",good,producer_close_fail=True,expected_retained=True)
o,g,w,p,k=setup(native=True)
exec(compile(ast.Module(body=outer_fin,type_ignores=[]),"<C6 outer interrupted cleanup AST>","exec"),dict(env,source_owner=o,guard=g,run_uuid=run))
add("INTERRUPTED_FINALIZATION_RETAINS_STRONG_REFERENCES",o.record(run)["state"]=="RETAINED_UNCONFIRMED" and o.record(run)["producer"] is p and g.close_calls==0)
# Changed ownership now retains a second Job handle: confirm unchanged watchdog uses explicit termination.
watchdog_path=Path(context["job_watchdog_source"]["path"]);wt=ast.parse(watchdog_path.read_bytes())
wc=next(n for n in wt.body if isinstance(n,ast.ClassDef) and n.name=="JobDeadlineWatchdog")
class Event:
 def __init__(self):self.flag=False
 def is_set(self):return self.flag
 def set(self):self.flag=True
 def wait(self,t):clock["now"]+=t
class FakeThread:
 def __init__(self,target,daemon=True):self.target=target;self.alive=False
 def start(self):self.target()
 def join(self,t):pass
 def is_alive(self):return self.alive
wen={"time":env["time"],"threading":types.SimpleNamespace(Thread=FakeThread),"ctypes":types.SimpleNamespace(get_last_error=lambda:123)}
exec(compile(ast.Module(body=[wc],type_ignores=[]),"<watchdog AST with fake thread/kernel>","exec"),wen)
def watchdog_instance():
 w=wen["JobDeadlineWatchdog"].__new__(wen["JobDeadlineWatchdog"])
 w.deadline=100.;w.stop=Event();w.thread=None;w.thread_started=False;w.handle=900
 w.observation={"errors":[],"termination_requested":False,"termination_succeeded":None,"duplicate_handle_closed":False}
 w.terminate=lambda handle,code:trace.append("TerminateJobObject."+str(handle)) or True
 w.close=lambda handle:trace.append("CloseHandle."+str(handle)) or True
 return w
clock["now"]=100.;trace.clear();w=watchdog_instance();w.start()
add("WATCHDOG_TERMINATES_WITH_PRODUCER_DUPLICATE_STILL_HELD",w.observation["termination_requested"] is True and w.observation["termination_succeeded"] is True and trace==["TerminateJobObject.900"])
class FailingStart(FakeThread):
 def start(self):raise RuntimeError("synthetic thread start failure")
wen["threading"]=types.SimpleNamespace(Thread=FailingStart);trace.clear();w=watchdog_instance()
err=capture_error(w.start);closed=w.stop_and_close()
add("WATCHDOG_THREAD_START_FAILURE_CLOSE_IS_SAFE",err is not None and closed["duplicate_handle_closed"] is True and w.thread_started is False and trace==["CloseHandle.900"])
class StillAlive(FakeThread):
 def start(self):self.alive=True
wen["threading"]=types.SimpleNamespace(Thread=StillAlive);trace.clear();w=watchdog_instance();w.start();closed=w.stop_and_close()
add("WATCHDOG_JOIN_TIMEOUT_RETAINS_DUPLICATE",closed["duplicate_handle_closed"] is False and w.handle==900 and trace==[])
summary={"total":len(cases),"matched":sum(x["matches_expected"] for x in cases),
 "counterexamples":[x["case"] for x in cases if not x["matches_expected"]]}
report={"schema":"researchos.c6-o4-independent-pure-controls.v1","cases":cases,"summary":summary,
 "source_provenance":prov,"proof_boundary":"Exact selected Source AST, fake PID/clock/sys/RLock/kernel/thread/guard/IO only. No candidate module imports, entrypoints, real WinAPI, SQL, provider calls or threads. The complete callback context diagnostic does not amend Source.",
 "candidate_module_imports":0,"actual_candidate_entry_calls":0,"real_threads_started":0,"real_WinAPI_SQL_provider_calls":0,
 "Main_canonical_writes":0,"author_controls_executed":0}
(O/"independent-controls.json").write_bytes((json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+"\n").encode())
print(json.dumps(summary,ensure_ascii=False,indent=2))

