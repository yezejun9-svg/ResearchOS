import ast,copy,json,types
from pathlib import Path
O=Path(__file__).resolve().parent
rows=json.loads((O/"intake.json").read_bytes())["rows"]
def raw(n):
 r=next(x for x in rows if Path(x["source_ref"]["path"]).name==n)
 return Path(r["snapshot_ref"]["path"]).read_bytes()
tree=ast.parse(raw("job_deadline_watchdog.py"))
klass=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=="JobDeadlineWatchdog")
methods=[n for n in klass.body if isinstance(n,ast.FunctionDef) and n.name in ("start","stop_and_close")]
only=ast.ClassDef(name="ReviewedWatchdogMethods",bases=[],keywords=[],body=methods,decorator_list=[])
clock={"now":10.0};calls=[]
class Event:
 def __init__(self):self.flag=False
 def is_set(self):return self.flag
 def set(self):self.flag=True
 def wait(self,delay):clock["now"]+=delay;return self.flag
class Thread:
 def __init__(self,target,daemon):self.target=target;self.daemon=daemon;self.started=False;self.alive=False;self.fail_start=False;self.refuse_join=False
 def start(self):
  if self.fail_start:raise RuntimeError("simulated thread start failure")
  self.started=True;self.alive=True
 def run_to_completion(self):self.target();self.alive=False
 def join(self,timeout):
  if not self.started:raise RuntimeError("cannot join thread before it is started")
  if not self.refuse_join:self.alive=False
 def is_alive(self):return self.alive
thread_mode={"fail_start":False,"refuse_join":False}
def make_thread(target,daemon):
 t=Thread(target,daemon);t.fail_start=thread_mode["fail_start"];t.refuse_join=thread_mode["refuse_join"];return t
env={"threading":types.SimpleNamespace(Thread=make_thread),"time":types.SimpleNamespace(monotonic=lambda:clock["now"]),"ctypes":types.SimpleNamespace(get_last_error=lambda:5)}
exec(compile(ast.fix_missing_locations(ast.Module(body=[only],type_ignores=[])),"<selected-watchdog-methods>","exec"),env)
K=env["ReviewedWatchdogMethods"]
def obj(terminate_ok=True,close_ok=True):
 o=K();o.deadline=10.05;o.stop=Event();o.thread=None;o.handle="duplicated-job-handle"
 o.observation={"deadline_monotonic":o.deadline,"termination_requested":False,"termination_succeeded":None,"duplicate_handle_closed":False,"errors":[]}
 def terminate(handle,code):calls.append(("terminate",handle,code));return terminate_ok
 def close(handle):calls.append(("close",handle));return close_ok
 o.terminate=terminate;o.close=close;return o
results=[]
def reset():
 clock["now"]=10.0;calls.clear();thread_mode.update(fail_start=False,refuse_join=False)
reset();o=obj();o.start();o.stop_and_close()
results.append({"case":"CANCEL_BEFORE_DEADLINE_CLOSES_DUPLICATE","calls":list(calls),"observation":copy.deepcopy(o.observation),"matches_expected":not o.observation["termination_requested"] and o.observation["duplicate_handle_closed"]})
reset();o=obj();o.start();o.thread.run_to_completion();o.stop_and_close()
results.append({"case":"SYNC_CALLBACK_STALL_TIMER_MODEL_TERMINATES_AT_DEADLINE","calls":list(calls),"observation":copy.deepcopy(o.observation),"matches_expected":o.observation["termination_requested"] and o.observation["termination_succeeded"] and o.observation["termination_monotonic"]>=o.deadline and o.observation["duplicate_handle_closed"]})
reset();o=obj(terminate_ok=False);o.start();o.thread.run_to_completion();o.stop_and_close()
results.append({"case":"TERMINATE_FAILURE_PRESERVED","calls":list(calls),"observation":copy.deepcopy(o.observation),"matches_expected":o.observation["termination_succeeded"] is False and bool(o.observation["errors"])})
reset();o=obj(close_ok=False);o.start();o.stop_and_close()
results.append({"case":"DUPLICATE_CLOSE_FAILURE_PRESERVED","calls":list(calls),"observation":copy.deepcopy(o.observation),"matches_expected":not o.observation["duplicate_handle_closed"] and bool(o.observation["errors"])})
reset();thread_mode["refuse_join"]=True;o=obj();o.start();observation=o.stop_and_close()
results.append({"case":"LIVE_WATCHER_RETAINS_DUPLICATE","calls":list(calls),"observation":copy.deepcopy(observation),"matches_expected":not observation["duplicate_handle_closed"] and bool(observation["errors"]) and not calls})
reset();thread_mode["fail_start"]=True;o=obj();start_error=close_error=None
try:o.start()
except RuntimeError as exc:start_error=str(exc)
try:o.stop_and_close()
except RuntimeError as exc:close_error=str(exc)
results.append({"case":"THREAD_START_FAILURE_SHOULD_STILL_CLOSE_DUPLICATE","start_error":start_error,"close_error":close_error,"calls":list(calls),"observation":copy.deepcopy(o.observation),"matches_expected":o.observation["duplicate_handle_closed"],"duplicate_retained_without_observation_error":o.handle is not None and not o.observation["errors"]})
controller=ast.parse(raw("controller.py"))
cleanup=next(n for n in controller.body if isinstance(n,ast.FunctionDef) and n.name=="cleanup_confirmed")
ce={};exec(compile(ast.Module(body=[cleanup],type_ignores=[]),"<unchanged-R01-helper>","exec"),ce)
launch=next(n for n in controller.body if isinstance(n,ast.FunctionDef) and n.name=="launch_reviewed_phase")
fin=next(n.finalbody for n in launch.body if isinstance(n,ast.Try))
integration=fin[0]
assert isinstance(integration,ast.If)
case_env={"watchdog":types.SimpleNamespace(stop_and_close=lambda:{"errors":["cleanup unconfirmed"],"duplicate_handle_closed":False}),"error":None,"result":{"job_cleanup":{"errors":[],"active_processes_last_observed":0,"primary_exit_confirmed":True,"job_idle_confirmed":True,"handles_closed":True}}}
exec(compile(ast.Module(body=[integration],type_ignores=[]),"<watchdog-finally-integration-only>","exec"),case_env)
results.append({"case":"WATCHDOG_UNCONFIRMED_MARKS_NATIVE_RESULT_UNSAFE_FOR_RELEASE","result":case_env["result"],"error":case_env["error"],"matches_expected":not ce["cleanup_confirmed"](case_env["result"])})
report={"schema":"researchos.independent-v3-watchdog-source-controls.v1","cases":results,"real_threads_started":0,"WinAPI_calls":0,"real_timing_measurement":False,"scope":"Selected start/stop AST methods with deterministic Python-only thread/event/clock and handle substitutes; __init__ not executed","new_tool_failures":0}
(O/"watchdog-controls.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"cases":len(results),"mismatches":[r["case"] for r in results if not r["matches_expected"]],"WinAPI_calls":0,"real_threads":0},ensure_ascii=False))

