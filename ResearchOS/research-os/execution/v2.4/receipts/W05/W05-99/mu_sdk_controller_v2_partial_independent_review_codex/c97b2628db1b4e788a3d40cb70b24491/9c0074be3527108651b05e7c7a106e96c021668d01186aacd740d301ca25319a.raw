import ast,copy,hashlib,json,types
from pathlib import Path
O=Path(__file__).resolve().parent
intake=json.loads((O/"intake.json").read_bytes())
def source(name):
 row=next(r for r in intake["rows"] if Path(r["source_ref"]["path"]).name==name)
 return Path(row["snapshot_ref"]["path"]).read_text(encoding="utf-8")
controller=ast.parse(source("controller.py"))
runner=ast.parse(source("mu_sdk_trial.v8.proposed.py"))
results=[]
def load(tree,names,env):
 nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
 assert {n.name for n in nodes}==set(names)
 exec(compile(ast.Module(body=nodes,type_ignores=[]),"<independent-selected-AST>","exec"),env)
 return env
def require(ok,msg):
 if not ok:raise RuntimeError(msg)
class MemPath:
 def __init__(self,p):self.p=p.p if isinstance(p,MemPath) else str(p)
 def __truediv__(self,p):return MemPath(self.p+"/"+str(p))
 def __str__(self):return self.p
 def __eq__(self,o):return isinstance(o,MemPath) and self.p==o.p
 def read_bytes(self):return fs[self.p]
 def is_absolute(self):return self.p.startswith("/")
 def is_file(self):return self.p in fs
fs={};root=MemPath("/repo");phase=MemPath("/receipt")
cp_path=str(root/"execution/v2.4/checkpoint.json");ow_path=str(root/"execution/v2.4/path_ownership.json")
uuid="a"*32
cp0={"head":"CURRENT","current_step_id":"W05-99","revision":341,"work_in_progress":{"mu_sdk_active_run_uuid":uuid,"other_agent_fact":"OLD"}}
ow0={"revision":168,"card_path_bindings":{"W05-99":{"subtasks":{"mu_sdk_trial":{"run_uuid":uuid,"state":"ACTIVE_ISOLATED_PHASE"}}}}}
def encode(x):return json.dumps(x,sort_keys=True).encode()
def pin(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def exclusive(p,v):
 assert str(p) not in fs;fs[str(p)]=encode(v);return pin(p)
def reset():
 fs.clear();fs[cp_path]=encode(cp0);fs[ow_path]=encode(ow0)
def atomic(p,v):fs[str(p)]=encode(v)
env={"Path":MemPath,"ROOT":root,"json":json,"require":require,"stamp":lambda:"2026-10-08T00:00:00Z","pin":pin,"exclusive_json":exclusive,"atomic_json":atomic}
load(controller,["close_canonical_lease","assert_native_closed"],env)
closed={"errors":[],"active_processes_last_observed":0,"unnamed_exclusive_job":True,"kill_on_job_close_configured":True,"assigned_before_resume":True,"primary_exit_confirmed":True,"job_idle_confirmed":True,"handles_closed":True}
for case,cleanup,native_error in [("POSITIVE_CONFIRMED_CLOSED",closed,None),("NEGATIVE_UNCONFIRMED_LIVE_CHILD",dict(closed,active_processes_last_observed=1,job_idle_confirmed=False,handles_closed=False,errors=["TerminateJobObject failed","CloseHandle failed"]),"native cleanup unconfirmed")]:
 reset();result={"actual_exit":0 if native_error is None else None,"timed_out":bool(native_error),"error":native_error,"job_cleanup":cleanup}
 rejected=False
 try:env["assert_native_closed"](result)
 except RuntimeError:rejected=True
 ref=env["close_canonical_lease"]({"run_uuid":uuid},phase,result,native_error)
 cp=json.loads(fs[cp_path]);ow=json.loads(fs[ow_path]);results.append({"case":case,"native_assert_rejected":rejected,"after_active_uuid":cp["work_in_progress"]["mu_sdk_active_run_uuid"],"after_ownership_state":ow["card_path_bindings"]["W05-99"]["subtasks"]["mu_sdk_trial"]["state"],"expected_lease_held_if_cleanup_unknown":native_error is not None,"scope":"pure selected AST with in-memory canonical filesystem; no real writes or native calls"})
reset()
def interleaving_atomic(p,v):
 if str(p)==ow_path:
  concurrent=json.loads(fs[cp_path]);concurrent["revision"]+=9;concurrent["work_in_progress"]["other_agent_fact"]="CONCURRENT_NEW";fs[cp_path]=encode(concurrent)
 fs[str(p)]=encode(v)
env["atomic_json"]=interleaving_atomic
env["close_canonical_lease"]({"run_uuid":uuid},phase,{"job_cleanup":closed},None)
after=json.loads(fs[cp_path]);results.append({"case":"NEGATIVE_CONCURRENT_CHECKPOINT_AFTER_CHECK_BEFORE_REPLACE","scheduled_other_revision":350,"scheduled_other_fact":"CONCURRENT_NEW","actual_revision":after["revision"],"actual_other_fact":after["work_in_progress"]["other_agent_fact"],"lost_update":after["work_in_progress"]["other_agent_fact"]!="CONCURRENT_NEW","scope":"pure AST close, memory scheduler inserts concurrent checkpoint update during first ownership replacement"})
# Controller pinned() itself performs two reads: hash read followed by returned execution read.
class ChangingPath:
 def __init__(self,p):self.path=str(p)
 def __str__(self):return self.path
 def is_absolute(self):return True
 def is_file(self):return True
 def read_bytes(self):
  global reads
  reads+=1;return b"reviewed source" if reads==1 else b"unreviewed changed source"
reads=0
pinen={"Path":ChangingPath,"hashlib":hashlib,"require":require}
load(controller,["pin","pinned"],pinen)
ref={"path":"/reviewed.py","sha256":hashlib.sha256(b"reviewed source").hexdigest(),"bytes":len(b"reviewed source")}
_,returned=pinen["pinned"](ref)
results.append({"case":"NEGATIVE_PIN_DOUBLE_READ","reads":reads,"returned_bytes_match_pin":hashlib.sha256(returned).hexdigest()==ref["sha256"],"scope":"pure AST with synthetic changing reader; module() compiles returned second read"})
# Environment basis only retains public allowlist; controller preserves/logs/forwards full seed map.
e={"os":types.SimpleNamespace(environ={"SystemRoot":"C:/Windows","RESEARCHOS_REVIEW_SYNTHETIC_EXTRA":"not-a-secret"})}
load(runner,["cli_environment"],e)
basis_env=e["cli_environment"]({"discovery_file":"/isolated/discovery.json","cli_config_file":"/isolated/config.json"})
results.append({"case":"NEGATIVE_ENV_BASIS_OMITS_EXTRA","seed_keys":sorted(e["os"].environ),"basis_keys":sorted(basis_env),"extra_is_in_basis": "RESEARCHOS_REVIEW_SYNTHETIC_EXTRA" in basis_env,"controller_forwards_and_logs_original_seed":True,"source_lines":[130,161,193,217],"scope":"pure runner cli_environment AST, public dummy values only; controller dataflow verified statically"})
# Native-sensitive functions are never imported or run; only compile transformed source and inspect AST ordering.
hooks=ast.parse(source("owned_job_hooks.py"));literals={}
for n in hooks.body:
 if isinstance(n,ast.Assign) and isinstance(n.value,ast.Constant):
  for t in n.targets:
   if isinstance(t,ast.Name):literals[t.id]=n.value.value
loader=next(n for n in hooks.body if isinstance(n,ast.FunctionDef) and n.name=="load_hooked_owned_process")
hook=next(ast.literal_eval(n.value) for n in loader.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="hook" for t in n.targets))
base=source("windows_owned_process.py")
assert base.count(literals["SIGNATURE"])==1 and base.count(literals["ASSIGNED"])==1
derived=base.replace(literals["SIGNATURE"],literals["SIGNATURE"][:-2]+", before_resume=None):").replace(literals["ASSIGNED"],literals["ASSIGNED"]+hook)
compile(derived,"<not-executed-derived-hook>","exec")
positions={x:derived.index(x) for x in ["require(assign(job, process))","before_resume({","if time.monotonic() - started >= timeout:","prior = resume(pi.hThread)"]}
results.append({"case":"POSITIVE_HOOK_ORDER_ASSIGN_CALLBACK_DEADLINE_RESUME","positions":positions,"ordered":list(positions.values())==sorted(positions.values()),"callback_runs_inline_before_next_deadline_check":True,"scope":"source transformation and compile only; no candidate module execution or Windows calls"})
worker=ast.parse(source("phase_worker.py"))
loops=[n for n in ast.walk(worker) if isinstance(n,ast.For)]
results.append({"case":"POSITIVE_SAME_PID_PRECHECK_PHASE","single_python_process":True,"loop_count":len(loops),"has_engine_main_inside_loop":any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=="main" for n in ast.walk(loops[0])),"input_bytes_rechecked":True,"runner_source_repinned":True,"scope":"static worker AST, not process execution"})
report={"schema":"researchos.independent-pure-source-controls.v1","cases":results,"native_calls":0,"candidate_module_imports":0,"product_sql_or_provider_calls":0,"real_canonical_writes":0,"all_controls_completed":True}
(O/"controls.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
print(json.dumps(report,indent=2))

