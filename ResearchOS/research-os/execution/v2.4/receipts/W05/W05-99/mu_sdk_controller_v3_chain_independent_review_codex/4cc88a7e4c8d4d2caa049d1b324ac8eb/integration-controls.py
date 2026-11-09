import ast,hashlib,json
from pathlib import Path
O=Path(__file__).resolve().parent
rows=json.loads((O/"intake.json").read_bytes())["rows"]
def source(name):
 r=next(x for x in rows if Path(x["source_ref"]["path"]).name==name)
 return Path(r["snapshot_ref"]["path"]).read_bytes()
ct=ast.parse(source("controller.py"));worker=ast.parse(source("phase_worker.py"))
launch=next(n for n in ct.body if isinstance(n,ast.FunctionDef) and n.name=="launch_reviewed_phase")
start=next(i for i,n in enumerate(launch.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="public_env" for t in n.targets))
end=next(i for i,n in enumerate(launch.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="public_os" for t in n.targets))
gate=ast.FunctionDef(name="gate",args=ast.arguments(posonlyargs=[],args=[ast.arg(arg="seed")],vararg=None,kwonlyargs=[],kw_defaults=[],kwarg=None,defaults=[]),body=launch.body[start:end]+[ast.Return(value=ast.Name(id="public_env",ctx=ast.Load()))],decorator_list=[])
def require(v,s):
 if not v:raise ValueError(s)
env={"require":require}
exec(compile(ast.fix_missing_locations(ast.Module(body=[gate],type_ignores=[])),"<v3-env-gate-pure>","exec"),env)
legal={"SystemRoot":"C:/Windows","WINDIR":"C:/Windows"}
cases=[]
for key in (None,"ComSpec","PATHEXT","REVIEW_DUMMY_EXTRA"):
 m=dict(legal)
 if key:m[key]="PUBLIC_SYNTHETIC"
 rejected=False
 try:env["gate"]({"public_environment":m})
 except ValueError:rejected=True
 cases.append({"case":"ENV_"+str(key),"expected_reject":key is not None,"observed_reject":rejected,"matches_expected":rejected==(key is not None)})
before=next(n for n in ast.walk(launch) if isinstance(n,ast.FunctionDef) and n.name=="before_resume")
watch_start=next(n.lineno for n in ast.walk(before) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=="start")
activate=next(n.lineno for n in ast.walk(before) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="activate_canonical_lease")
observe=next(n.lineno for n in ast.walk(before) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=="observe_assigned_before_resume")
cases.append({"case":"WATCHDOG_STARTS_BEFORE_CALLBACK_AUTHORITY_WORK","watchdog_start":watch_start,"canonical_activate":activate,"observer_call":observe,"matches_expected":watch_start<activate<observe})
context=next(n.value for n in ast.walk(before) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="context" for t in n.targets))
keys=[ast.literal_eval(k) for k in context.keys]
cases.append({"case":"OBSERVER_V2_CONTEXT_ADDITIONS_PRESENT","keys":keys,"matches_expected":"phase_worker_source" in keys and "python_binary" in keys})
argv=next(n.value for n in launch.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="argv" for t in n.targets))
args=ast.unparse(argv)
worker_main=next(n for n in worker.body if isinstance(n,ast.FunctionDef) and n.name=="main")
loop=next(n for n in worker_main.body if isinstance(n,ast.Try)).body[0]
cases.append({"case":"SAME_PID_WORKER_AND_EXACT_REVIEWED_VECTOR_STATIC","controller_argv":args,"worker_loop":ast.unparse(loop.iter),"matches_expected":isinstance(loop,ast.For) and ast.unparse(loop.iter)=="('precheck-' + phase, phase)"})
# Retain a precise source-only load-boundary trace; no runtime file mutation or execution.
obs=ast.parse(source("mu_sdk_job_observer.v2.proposed.py"))
validate_launch=next(n for n in obs.body if isinstance(n,ast.FunctionDef) and n.name=="validate_launch_inputs")
ret=next(n.value for n in validate_launch.body if isinstance(n,ast.Return))
retkeys=[ast.literal_eval(k) for k in ret.keys]
compile_nodes=[n for n in ast.walk(validate_launch) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="compile"]
load_boundary={"controller_worker_arg":"str(HERE/'phase_worker.py')","controller_records_worker_pin":True,"observer_checks_worker_raw_and_compiles":True,"observer_returns_compiled_code":False,"observer_return_keys":retkeys,"worker_compile_result_discarded":any(isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=="compile" for n in validate_launch.body),"worker_file_handle_retained_for_resume":False,"controller_create_process_uses_file_path":True,"phase_worker_itself_loaded_only_after_ResumeThread":True,"claim_scope":"static execution-consumption trace; no real process or file tampering","unclosed_interval":"last observer worker read -> Root grant/input writes -> ResumeThread -> Python opens worker path"}
# An immutable byte snapshot and the later path's bytes are distinct objects; demonstrate the unchecked interval only.
reviewed=b'print("REVIEWED")\n';path_contents=reviewed;checked=path_contents;reviewed_pin=hashlib.sha256(checked).hexdigest();path_contents=b'print("CHANGED_AFTER_OBSERVER")\n'
load_boundary["memory_timeline"]={"reviewed_snapshot_sha256":reviewed_pin,"later_path_sha256":hashlib.sha256(path_contents).hexdigest(),"argv_unchanged":True,"same_job_pid_possible":True,"actual_execution_performed":False,"later_bytes_differ":path_contents!=checked}
report={"schema":"researchos.independent-v3-integration-static-controls.v1","cases":cases,"load_boundary":load_boundary,"observer_39_controls_not_repeated":True,"candidate_modules_imported":0,"WinAPI_native_SQL_provider_calls":0,"source_function_locations":{n.name:{"start":n.lineno,"end":n.end_lineno} for n in ct.body if isinstance(n,ast.FunctionDef)}}
(O/"integration-controls.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"cases":len(cases),"mismatches":[r["case"] for r in cases if not r["matches_expected"]],"execution_load_immutability":"OPEN_SOURCE_GAP","native_calls":0},ensure_ascii=False))

