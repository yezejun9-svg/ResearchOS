import ast,copy,hashlib,json,types
from pathlib import Path
O=Path(__file__).resolve().parent
rows=json.loads((O/"intake.json").read_bytes())["rows"]+json.loads((O/"observer-intake.json").read_bytes())["rows"]
def source(name):
 r=next(x for x in rows if Path(x["source_ref"]["path"]).name==name)
 return Path(r["snapshot_ref"]["path"]).read_bytes()
obs=ast.parse(source("mu_sdk_job_observer.proposed.py"));runner=ast.parse(source("mu_sdk_trial.v8.proposed.py"));base=source("windows_owned_process.py").decode()
const={}
for n in obs.body:
 if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name):
  try:const[n.targets[0].id]=ast.literal_eval(n.value)
  except (ValueError,TypeError):pass
def load(names,env):
 n=[x for x in obs.body if isinstance(x,ast.FunctionDef) and x.name in names];assert len(n)==len(names)
 exec(compile(ast.Module(body=n,type_ignores=[]),"<independent-observer-selected-AST>","exec"),env)
 return env
def require(v,s):
 if not v:raise ValueError(s)
derived=base.replace(const["SIGNATURE"],const["SIGNATURE"][:-2]+", before_resume=None):").replace(const["ASSIGNED"],const["ASSIGNED"]+const["HOOK"])
filename=str(Path(const["BASE_REF"]["path"]))+"::root-before-resume"
compiled=compile(derived,filename,"exec",dont_inherit=True)
expected=next(c for c in compiled.co_consts if isinstance(c,types.CodeType) and c.co_name=="run_owned")
callline=next(n.lineno for n in ast.walk(ast.parse(derived)) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="before_resume")
loc={"pi":types.SimpleNamespace(hProcess=7,hThread=8,dwProcessId=41),"job":9,"result":{"creation_time_100ns":123456,"resumed":False},"cleanup":{"assigned_before_resume":True,"kill_on_job_close_configured":True},"stage":"ASSIGN_SUSPENDED_CHILD","assigned":True,"flags":0x08080404,"started":100.0,"timeout":200.0,"env":{"SystemRoot":"C:/Windows"},"argv":["C:/Python/python.exe","-I","-S","C:/reviewed/phase_worker.py","C:/reviewed/input.json"],"cwd":"D:/作品集/ResearchOS/research-os"}
owner=types.SimpleNamespace(f_code=expected,f_lineno=callline,f_locals=loc,f_back=None)
current=types.SimpleNamespace(f_back=owner)
context={"hooks_source":{"synthetic":"opaque-reviewed-ref"},"public_environment":{"SystemRoot":"C:/Windows"}}
state={"started":90.0,"deadline":350.0,"job":{"actual_owned_runner_deadline_monotonic":300.0,"actual_creation_time_100ns":123456}}
env=dict(const,require=require,types=types,inspect=types.SimpleNamespace(currentframe=lambda:current),time=types.SimpleNamespace(monotonic=lambda:200.0),expected_hook_code=lambda _: (expected,callline))
load(["code_identity","observe_callback_frame","validate_observed_facts","validate_source_review","phase_projection","mode_public_pins","validate_limits","strict_json"],env)
results=[]
def case(name,fn,expect_reject):
 try:
  ret=fn();rejected=False;error=None
 except ValueError as exc:
  ret=None;rejected=True;error=str(exc)
 results.append({"case":name,"expected_reject":expect_reject,"observed_reject":rejected,"matches_expected":expect_reject==rejected,"error":error,"returned":ret})
call=lambda:env["observe_callback_frame"](context,7,8,9,41,123456,state)
case("FRAME_POSITIVE_EXPECTED_LAUNCH",call,False)
loc["argv"]=["C:/unreviewed/foreign-program.exe","--unrelated"]
case("FRAME_FOREIGN_ARGV_EXPECT_REJECT",call,True)
loc["argv"]=["C:/Python/python.exe","-I","-S","C:/reviewed/phase_worker.py","C:/reviewed/input.json"]
loc["cwd"]="C:/unreviewed/workspace"
case("FRAME_FOREIGN_CWD_EXPECT_REJECT",call,True)
loc["cwd"]="D:/作品集/ResearchOS/research-os"
loc["result"]["resumed"]=True
case("FRAME_ALREADY_RESUMED_REJECTS",call,True)
loc["result"]["resumed"]=False
loc["assigned"]=False
case("FRAME_NOT_ASSIGNED_REJECTS",call,True)
loc["assigned"]=True
loc["env"]={"SystemRoot":"OTHER"}
case("FRAME_FOREIGN_ENV_REJECTS",call,True)
loc["env"]=dict(context["public_environment"])
loc["result"]["creation_time_100ns"]=234567
case("FRAME_CREATION_ID_REJECTS",call,True)
loc["result"]["creation_time_100ns"]=123456
owner.f_lineno+=1
case("FRAME_WRONG_CALLBACK_LINE_REJECTS",call,True)
owner.f_lineno-=1
context["public_environment"]["REVIEW_DUMMY_EXTRA"]="public-not-a-secret";loc["env"]=dict(context["public_environment"])
case("FRAME_UNBOUND_EXTRA_ENV_EXPECT_REJECT",call,True)
# Independent minimal phase input constructed from the actual runner's literal key vector.
keys=next(ast.literal_eval(n.value) for n in runner.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="PHASE_BASIS_KEYS" for t in n.targets))
doc={k:None for k in keys};doc.update(phase="bootstrap",cli_binary={"path":"C:/reviewed/cli.exe"},workspace="C:/isolated/workspace",goal_objective="Review only",run_uuid="a"*32,discovery_file="C:/isolated/discovery.json",cli_config_file="C:/isolated/config.json",repository_root="D:/作品集/ResearchOS/research-os")
env.update(ast=ast,Path=Path,json=json,math=__import__("math"))
p0=env["phase_projection"](doc,source("mu_sdk_trial.v8.proposed.py"),{"SystemRoot":"C:/Windows"})
p1=env["phase_projection"](doc,source("mu_sdk_trial.v8.proposed.py"),{"SystemRoot":"C:/Windows","REVIEW_DUMMY_EXTRA":"public-not-a-secret"})
results.append({"case":"OBSERVER_PROJECTION_IGNORES_EXTRA_ENV","same_basis_with_extra_env":p0==p1,"extra_key_in_basis": "REVIEW_DUMMY_EXTRA" in p1["child_environment"]})
facts={"process_id":41,"thread_process_id":41,"thread_id":42,"creation_filetime":123456,"member_of_expected_job":True,"exit_code":259,"wait_result":258,"assigned_count":1,"returned_count":1,"active_pids":[41],"job_limit_flags":0x2000}
case("OS_FACT_POSITIVE",lambda:env["validate_observed_facts"](facts,41,123456),False)
for name,key,value in [("OS_WRONG_PID","process_id",43),("OS_FOREIGN_JOB","member_of_expected_job",False),("OS_MORE_CHILDREN","active_pids",[41,43]),("OS_BREAKAWAY","job_limit_flags",0x2800),("OS_EXITED","wait_result",0)]:
 f=dict(facts);f[key]=value
 case(name,lambda f=f:env["validate_observed_facts"](f,41,123456),True)
ctx={k:{"path":"/"+k,"sha256":"0"*64,"bytes":1} for k in ["controller_source","observer_source","hooks_source"]}
rev={"schema":"researchos.mu-sdk-controller-observer-independent-source-review.v1","decision":"READY_SOURCE_ONLY","actor_id":"codex:/root/independent-reviewer","controller_source_ref":ctx["controller_source"],"observer_source_ref":ctx["observer_source"],"hooks_source_ref":ctx["hooks_source"],"runner_source_ref":const["RUNNER_REF"],"callback_contract":"REAL_ASSIGNED_SUSPENDED_FRAME_BEFORE_FIRST_RESUME","formal_acceptance":False}
case("REVIEW_VALID_MINIMAL_SOURCE_TUPLE",lambda:env["validate_source_review"](rev,ctx),False)
for name,key,value in [("REVIEW_ROOT_SELF","actor_id",const["ROOT_ACTOR"]),("REVIEW_AUTHOR_SELF","actor_id",const["AUTHOR"]),("REVIEW_NOT_READY","decision","REQUEST_CHANGES"),("REVIEW_FORMAL_TRUE","formal_acceptance",True),("REVIEW_FOREIGN_RUNNER","runner_source_ref",{})]:
 r=dict(rev);r[key]=value;case(name,lambda r=r:env["validate_source_review"](r,ctx),True)
case("STRICT_DUPLICATE_REJECT",lambda:env["strict_json"](b'{"a":1,"a":2}'),True)
case("STRICT_NAN_REJECT",lambda:env["strict_json"](b'{"a":NaN}'),True)
report={"schema":"researchos.independent-observer-pure-controls.v1","source_sha":"b062be8b68d1b31b658ba79a20c890ce895009fc135c80ae8d33ed5b78d01fd0","cases":results,"native_observer_calls":0,"full_candidate_imports":0,"real_live_frame_inspected":False,"frame_semantics":"Synthetic in-memory frame/locals and compiled reviewed code object; source comparison and branch behavior only, not actual Windows or live callback proof","real_receipts_written_by_candidate":0,"author_controls_executed":False}
(O/"observer-controls.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"case_count":len(results),"rejection_cases":sum(x.get("expected_reject",False) for x in results),"mismatches":[x["case"] for x in results if x.get("matches_expected") is False],"native_calls":0,"raw_report":str(O/"observer-controls.json")},ensure_ascii=False))

