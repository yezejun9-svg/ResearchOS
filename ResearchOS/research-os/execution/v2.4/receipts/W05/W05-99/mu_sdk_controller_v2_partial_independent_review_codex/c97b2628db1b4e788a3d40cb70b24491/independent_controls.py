import ast,copy,hashlib,json,types
from pathlib import Path
O=Path(__file__).resolve().parent
intake=json.loads((O/"intake.json").read_bytes())
def source(name,old=False):
 choices=[r for r in intake["rows"] if Path(r["source_ref"]["path"]).name==name]
 r=next((r for r in choices if ("mu_sdk_controller_source_codex" in r["source_ref"]["path"])==old),choices[0])
 return Path(r["snapshot_ref"]["path"]).read_bytes()
new=ast.parse(source("controller.py"));prior=ast.parse(source("independent_controls.py"))
# Reuse exactly the previous independent review's own memory filesystem and inputs.
names={"require","MemPath","encode","pin","exclusive","reset"}
variables={"fs","root","phase","cp_path","ow_path","uuid","cp0","ow0","closed"}
selected=[]
for n in prior.body:
 if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names:selected.append(n)
 if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in variables for t in n.targets):selected.append(n)
env={"json":json,"hashlib":hashlib};exec(compile(ast.Module(body=selected,type_ignores=[]),"<prior-own-fixtures>","exec"),env)
Memory=env["MemPath"];env.update(Path=Memory,ROOT=env["root"],stamp=lambda:"2026-10-08T00:00:00Z",exclusive_json=env["exclusive"],atomic_json=lambda p,v:env["fs"].__setitem__(str(p),env["encode"](v)))
functions={"cleanup_confirmed","close_canonical_lease","assert_native_closed"}
exec(compile(ast.Module(body=[n for n in new.body if isinstance(n,ast.FunctionDef) and n.name in functions],type_ignores=[]),"<v2-narrow-cleanup-AST>","exec"),env)
original_loop=next(n for n in prior.body if isinstance(n,ast.For) and isinstance(n.target,ast.Tuple) and [e.id for e in n.target.elts]==["case","cleanup","native_error"])
old_cases=eval(compile(ast.Expression(original_loop.iter),"<prior-own-case-inputs>","eval"),env)
results=[]
def close_case(name,result,error,should_retain):
 env["reset"]();before={k:v for k,v in env["fs"].items()};ret=env["close_canonical_lease"]({"run_uuid":env["uuid"]},env["phase"],result,error)
 cp=json.loads(env["fs"][env["cp_path"]]);ow=json.loads(env["fs"][env["ow_path"]]);retained=cp["work_in_progress"]["mu_sdk_active_run_uuid"]==env["uuid"]
 results.append({"case":name,"expected_retained":should_retain,"observed_retained":retained,"matches_expected":retained==should_retain,"canonical_bytes_unchanged":all(env["fs"][k]==v for k,v in before.items()) if retained else None,"receipt":json.loads(env["fs"][ret["path"]]),"input_result":result})
for name,c,error in old_cases:
 result={"actual_exit":0 if error is None else None,"timed_out":bool(error),"error":error,"job_cleanup":c}
 close_case("REUSED_"+name,result,error,error is not None)
close_case("NONE_RESULT_RETAINS",None,"no native result",True)
close_case("EMPTY_RESULT_RETAINS",{},"missing native result",True)
for key,value in [("primary_exit_confirmed",False),("job_idle_confirmed",False),("handles_closed",False),("errors",["failure"]),("active_processes_last_observed",1)]:
 c=dict(env["closed"]);c[key]=value
 close_case("UNCONFIRMED_"+key,{"actual_exit":None,"timed_out":True,"error":"cleanup unconfirmed","job_cleanup":c},"cleanup unconfirmed",True)
close_case("CONFIRMED_FAILED_PROCESS_MAY_RELEASE",{"actual_exit":17,"timed_out":False,"error":"child failed","job_cleanup":dict(env["closed"])},"child failed",False)
# Reuse original changing reader class and original reviewed byte literal.
changing=next(n for n in prior.body if isinstance(n,ast.ClassDef) and n.name=="ChangingPath")
pinenv={"hashlib":hashlib,"require":env["require"],"reads":0}
exec(compile(ast.Module(body=[changing],type_ignores=[]),"<prior-own-changing-reader>","exec"),pinenv)
pinenv["Path"]=pinenv["ChangingPath"]
exec(compile(ast.Module(body=[n for n in new.body if isinstance(n,ast.FunctionDef) and n.name=="pinned"],type_ignores=[]),"<v2-single-pin-read>","exec"),pinenv)
ref={"path":"/reviewed.py","sha256":hashlib.sha256(b"reviewed source").hexdigest(),"bytes":len(b"reviewed source")}
_,raw=pinenv["pinned"](ref)
results.append({"case":"REUSED_R03_CHANGING_READER_NOW_ONE_VERIFIED_READ","reads":pinenv["reads"],"returned_matches_pin":hashlib.sha256(raw).hexdigest()==ref["sha256"],"matches_expected":pinenv["reads"]==1 and raw==b"reviewed source"})
pinenv["reads"]=0;bad=dict(ref,sha256="0"*64);rejected=False
try:pinenv["pinned"](bad)
except RuntimeError:rejected=True
results.append({"case":"R03_BAD_PIN_REJECTS","matches_expected":rejected,"rejected":rejected})
# Extract only the environment validation statements; never execute launch_reviewed_phase.
launch=next(n for n in new.body if isinstance(n,ast.FunctionDef) and n.name=="launch_reviewed_phase")
start=next(i for i,n in enumerate(launch.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="public_env" for t in n.targets))
end=next(i for i,n in enumerate(launch.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="public_os" for t in n.targets))
fn=ast.FunctionDef(name="environment_gate",args=ast.arguments(posonlyargs=[],args=[ast.arg(arg="seed")],vararg=None,kwonlyargs=[],kw_defaults=[],kwarg=None,defaults=[]),body=launch.body[start:end]+[ast.Return(value=ast.Name(id="public_env",ctx=ast.Load()))],decorator_list=[])
gateenv={"require":env["require"]};exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),"<v2-env-gate-only>","exec"),gateenv)
runner=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v8_source_codex/8251b1ed21754f7cbd6c2f8e7ff574eb/mu_sdk_trial.v8.proposed.py")
rr=runner.read_bytes();assert hashlib.sha256(rr).hexdigest()=="5b112a0824ab3bbbabb228416a9c2d0aa0be70ac2a45f29720138de350507fde" and len(rr)==90096
renv={};exec(compile(ast.Module(body=[n for n in ast.parse(rr).body if isinstance(n,ast.FunctionDef) and n.name=="cli_environment"],type_ignores=[]),"<v8-env-projection-only>","exec"),renv)
def projection(d):
 renv["os"]=types.SimpleNamespace(environ=d)
 return renv["cli_environment"]({"discovery_file":"/isolated/discovery.json","cli_config_file":"/isolated/config.json"})
legal={"SystemRoot":"C:/Windows","WINDIR":"C:/Windows"}
for name,d,expect_reject in [("LEGAL_CLOSED_ENV",legal,False),("REUSED_R04_EXTRA_KEY",dict(legal,RESEARCHOS_REVIEW_SYNTHETIC_EXTRA="not-a-secret"),True),("NUL_VALUE",dict(legal,TEMP="bad\0value"),True),("WRONG_SYSTEM_ROOT",dict(legal,SystemRoot="D:/Windows"),True),("PERMITTED_COMSPEC",dict(legal,ComSpec="C:/review-only/one.exe"),True),("PERMITTED_PATHEXT",dict(legal,PATHEXT=".SYNTHETIC"),True)]:
 try:got=gateenv["environment_gate"]({"public_environment":d});reject=False;err=None
 except RuntimeError as exc:got=None;reject=True;err=str(exc)
 results.append({"case":name,"expected_reject":expect_reject,"observed_reject":reject,"matches_expected":reject==expect_reject,"same_runner_basis_projection_as_legal":projection(d)==projection(legal),"input_environment":d,"error":err})
# Gate is placed before every environment-bearing receipt and child-launch use.
intent_line=next(n.lineno for n in ast.walk(launch) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="exclusive_json" and any(isinstance(x,ast.Constant) and x.value=="phase-launch.intent.json" for x in ast.walk(n)))
results.append({"case":"ENV_GATE_PRECEDES_INTENT","gate_last_line":launch.body[end-1].end_lineno,"intent_line":intent_line,"matches_expected":launch.body[end-1].end_lineno<intent_line})
(O/"runner-env-read.json").write_text(json.dumps({"path":str(runner),"sha256":hashlib.sha256(rr).hexdigest(),"bytes":len(rr),"exit_unchanged":runner.read_bytes()==rr},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
report={"schema":"researchos.v2-partial-independent-controls.v1","cases":results,"prior_inputs_reused_from":next(r["source_ref"] for r in intake["rows"] if Path(r["source_ref"]["path"]).name=="independent_controls.py"),"scope":["R01","R03","R04"],"candidate_module_imports":0,"native_or_sql_or_provider_calls":0,"real_canonical_writes":0,"author_controls_executed":False}
(O/"controls.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"cases":len(results),"mismatches":[r["case"] for r in results if not r["matches_expected"]],"native_or_sql_or_provider_calls":0,"scope":"R01 R03 R04 only"},ensure_ascii=False))

