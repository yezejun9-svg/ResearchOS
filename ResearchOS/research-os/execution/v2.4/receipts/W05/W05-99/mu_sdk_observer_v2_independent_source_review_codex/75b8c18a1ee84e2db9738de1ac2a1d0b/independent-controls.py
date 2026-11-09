import ast,copy,hashlib,json,types
from pathlib import Path
O=Path(__file__).resolve().parent
rows=json.loads((O/"intake.json").read_bytes())["rows"]
def row(name):return next(r for r in rows if Path(r["source_ref"]["path"]).name==name)
def raw(name):return Path(row(name)["snapshot_ref"]["path"]).read_bytes()
observer=ast.parse(raw("mu_sdk_job_observer.v2.proposed.py"))
prior=ast.parse(raw("independent_observer_controls.py"))
constants={}
for n in observer.body:
 if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name):
  try:constants[n.targets[0].id]=ast.literal_eval(n.value)
  except (ValueError,TypeError):pass
env=dict(constants,ast=ast,json=json,hashlib=hashlib,Path=Path,types=types,time=types.SimpleNamespace(monotonic=lambda:200.0))
wanted={"require","strict_json","pin_bytes","json_bytes","validate_public_environment","phase_projection","validate_source_review","validate_launch_inputs","validate_callback_launch","code_identity","observe_callback_frame"}
nodes=[n for n in observer.body if isinstance(n,ast.FunctionDef) and n.name in wanted];assert len(nodes)==len(wanted)
exec(compile(ast.Module(body=nodes,type_ignores=[]),"<observer-v2-pure-selected-AST>","exec"),env)
worker_ref=copy.deepcopy(row("phase_worker.py")["source_ref"])
python_ref=copy.deepcopy(next(r["source_ref"] for r in rows if Path(r["source_ref"]["path"]).suffix.lower()==".exe"))
buffers={worker_ref["path"]:raw("phase_worker.py"),python_ref["path"]:Path(next(r["snapshot_ref"]["path"] for r in rows if r["source_ref"]==python_ref)).read_bytes()}
original_buffers=dict(buffers);reads={}
class CheckedBuffer:
 def __init__(self,name):self.name=name
 def read_bytes(self):
  reads[self.name]=reads.get(self.name,0)+1
  return buffers[self.name]
env["checked_path"]=lambda name:CheckedBuffer(name)
env["os"]=types.SimpleNamespace(path=types.SimpleNamespace(lexists=lambda _:False))
legal_env={"SystemRoot":"C:/Windows","WINDIR":"C:/Windows"}
context={"input_doc":{"discovery_file":"C:/isolated/discovery.json","cli_config_file":"C:/isolated/config.json"},"phase_worker_source":worker_ref,"python_binary":python_ref,"public_environment":dict(legal_env),"phase_dir":"D:/review-only/bootstrap","hooks_source":{"synthetic":"opaque-reviewed-ref"}}
basis={"child_environment":dict(legal_env,RESEARCHOS_CLI_DISCOVERY=context["input_doc"]["discovery_file"],RESEARCHOS_CLI_CONFIG=context["input_doc"]["cli_config_file"])}
compile_calls=[]
real_compile=compile
def compile_spy(buf,filename,*args,**kwargs):
 compile_calls.append({"object_identity":id(buf),"sha256":hashlib.sha256(buf).hexdigest(),"filename":filename})
 return real_compile(buf,filename,*args,**kwargs)
env["compile"]=compile_spy
launch=env["validate_launch_inputs"](context,basis)
results=[{"case":"LEGAL_LAUNCH_INPUTS","matches_expected":True,"reads":dict(reads),"compiled_same_worker_buffer":compile_calls[-1]["object_identity"]==id(buffers[worker_ref["path"]]),"launch":launch}]
assert reads=={worker_ref["path"]:1,python_ref["path"]:1} and compile_calls[-1]["object_identity"]==id(buffers[worker_ref["path"]])
# Reuse the prior review's literal frame and state fixtures, with only newly required legal fields.
fixture_env={"types":types}
fixture_nodes=[n for n in prior.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in {"loc","state"} for t in n.targets)]
exec(compile(ast.Module(body=fixture_nodes,type_ignores=[]),"<prior-own-frame-inputs>","exec"),fixture_env)
loc=fixture_env["loc"];state=fixture_env["state"];state["launch"]=launch
loc["argv"]=list(launch["argv"]);loc["cwd"]=launch["cwd"];loc["env"]=dict(legal_env)
base=raw("windows_owned_process.py").decode()
derived=base.replace(constants["SIGNATURE"],constants["SIGNATURE"][:-2]+", before_resume=None):").replace(constants["ASSIGNED"],constants["ASSIGNED"]+constants["HOOK"])
filename=str(Path(constants["BASE_REF"]["path"]))+"::root-before-resume"
compiled=compile(derived,filename,"exec",dont_inherit=True)
expected=next(c for c in compiled.co_consts if isinstance(c,types.CodeType) and c.co_name=="run_owned")
call_line=next(n.lineno for n in ast.walk(ast.parse(derived)) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="before_resume")
owner=types.SimpleNamespace(f_code=expected,f_lineno=call_line,f_locals=loc,f_back=None)
current=types.SimpleNamespace(f_back=owner)
env["inspect"]=types.SimpleNamespace(currentframe=lambda:current)
env["expected_hook_code"]=lambda _: (expected,call_line)
def case(name,fn,reject):
 try:value=fn();got=False;error=None
 except (ValueError,SyntaxError,KeyError) as exc:value=None;got=True;error=type(exc).__name__+":"+str(exc)
 results.append({"case":name,"expected_reject":reject,"observed_reject":got,"matches_expected":got==reject,"error":error})
call=lambda:env["observe_callback_frame"](context,7,8,9,41,123456,state)
case("LEGAL_FULL_CALLBACK_FRAME",call,False)
foreign_argv=next(ast.literal_eval(n.value) for n in prior.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Subscript) and isinstance(n.value,ast.List) and "foreign-program" in ast.unparse(n.value))
foreign_cwd=next(ast.literal_eval(n.value) for n in prior.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Subscript) and isinstance(n.value,ast.Constant) and n.value.value=="C:/unreviewed/workspace")
loc["argv"]=foreign_argv
case("REUSED_FOREIGN_ARGV_NOW_REJECTS",call,True)
loc["argv"]=list(launch["argv"]);loc["cwd"]=foreign_cwd
case("REUSED_FOREIGN_CWD_NOW_REJECTS",call,True)
loc["cwd"]=launch["cwd"]
context["public_environment"]["REVIEW_DUMMY_EXTRA"]="public-not-a-secret";loc["env"]=dict(context["public_environment"])
case("REUSED_UNBOUND_EXTRA_ENV_NOW_REJECTS",call,True)
context["public_environment"]=dict(legal_env);loc["env"]=dict(legal_env)
for key in ("ComSpec","PATHEXT"):
 loc["env"]=dict(legal_env,**{key:"REVIEW_ONLY"})
 case("FRAME_FORBIDDEN_"+key,call,True)
loc["env"]=dict(legal_env)
loc["argv"][0]="C:/foreign/python.exe";case("FRAME_FOREIGN_PYTHON_PATH",call,True);loc["argv"]=list(launch["argv"])
loc["argv"][5]="C:/foreign/phase_worker.py";case("FRAME_FOREIGN_WORKER_PATH",call,True);loc["argv"]=list(launch["argv"])
loc["argv"][-1]="C:/foreign/input.json";case("FRAME_FOREIGN_INPUT_PATH",call,True);loc["argv"]=list(launch["argv"])
loc["argv"]=tuple(launch["argv"]);case("FRAME_TUPLE_ARGV_REJECTED",call,True);loc["argv"]=list(launch["argv"])
loc["env"]["PATH"]="CHANGED";case("FRAME_ENV_DIFFERS_BASIS",call,True);loc["env"]=dict(legal_env)
# Byte/hash/size controls use actual pinned worker and metadata interpreter byte snapshots, with memory-only tampering.
for kind in ("phase_worker_source","python_binary"):
 ref=context[kind];p=ref["path"]
 original=buffers[p];buffers[p]=bytes([original[0]^1])+original[1:]
 case(kind+"_WRONG_ACTUAL_BYTES",lambda:env["validate_launch_inputs"](context,basis),True)
 buffers[p]=original
 for field,value in [("sha256","0"*64),("bytes",ref["bytes"]+1)]:
  altered=copy.deepcopy(context);altered[kind][field]=value
  case(kind+"_WRONG_"+field,lambda c=altered:env["validate_launch_inputs"](c,basis),True)
for key in ("ComSpec","PATHEXT"):
 altered=copy.deepcopy(context);altered["public_environment"][key]="REVIEW_ONLY"
 case("INPUT_FORBIDDEN_"+key,lambda c=altered:env["validate_launch_inputs"](c,basis),True)
badbasis=copy.deepcopy(basis);badbasis["child_environment"]["EXTRA"]="REVIEW_ONLY"
case("BASIS_EXTRA_KEY_REJECTS",lambda:env["validate_launch_inputs"](context,badbasis),True)
badbasis=copy.deepcopy(basis);badbasis["child_environment"]["RESEARCHOS_CLI_CONFIG"]="C:/foreign/config"
case("BASIS_FOREIGN_CLI_PATH_REJECTS",lambda:env["validate_launch_inputs"](context,badbasis),True)
# Simulate a second read changing bytes: the implementation must read/compile only the first validated buffer.
class ChangingBuffer:
 def __init__(self,name):self.name=name
 def read_bytes(self):
  reads[self.name]=reads.get(self.name,0)+1
  return original_buffers[self.name] if reads[self.name]==1 else b"changed-unverified-second-read"
reads.clear();compile_calls.clear();env["checked_path"]=lambda name:ChangingBuffer(name)
checked=env["validate_launch_inputs"](context,basis)
results.append({"case":"SINGLE_RAW_READ_AND_COMPILE_SAME_CHECKED_WORKER_BUFFER","matches_expected":reads=={worker_ref["path"]:1,python_ref["path"]:1} and compile_calls[-1]["object_identity"]==id(original_buffers[worker_ref["path"]]),"reads":dict(reads),"compiled_worker_sha":compile_calls[-1]["sha256"]})
env["checked_path"]=lambda name:CheckedBuffer(name)
# v2 review schema requires exact worker and Python references in addition to old four-source tuple.
ctx=dict(context,controller_source={"path":"/controller","sha256":"1"*64,"bytes":1},observer_source={"path":"/observer","sha256":"2"*64,"bytes":2},hooks_source={"path":"/hooks","sha256":"3"*64,"bytes":3})
review={"schema":"researchos.mu-sdk-controller-observer-independent-source-review.v2","decision":"READY_SOURCE_ONLY","actor_id":"codex:/root/independent-reviewer","controller_source_ref":ctx["controller_source"],"observer_source_ref":ctx["observer_source"],"hooks_source_ref":ctx["hooks_source"],"runner_source_ref":constants["RUNNER_REF"],"phase_worker_source_ref":worker_ref,"python_binary_ref":python_ref,"callback_contract":"REAL_ASSIGNED_SUSPENDED_FRAME_BEFORE_FIRST_RESUME","formal_acceptance":False}
case("LEGAL_V2_REVIEW_TUPLE",lambda:env["validate_source_review"](review,ctx),False)
old=copy.deepcopy(review);old["schema"]="researchos.mu-sdk-controller-observer-independent-source-review.v1";old.pop("phase_worker_source_ref");old.pop("python_binary_ref")
case("OLD_V1_FOUR_SOURCE_READY_REJECTS",lambda:env["validate_source_review"](old,ctx),True)
for key in ("phase_worker_source_ref","python_binary_ref"):
 for field,value in [("sha256","f"*64),("bytes",review[key]["bytes"]+1),("path","C:/foreign/file")]:
  changed=copy.deepcopy(review);changed[key][field]=value
  case("REVIEW_"+key+"_WRONG_"+field,lambda r=changed:env["validate_source_review"](r,ctx),True)
 changed=copy.deepcopy(review);changed.pop(key)
 case("REVIEW_MISSING_"+key,lambda r=changed:env["validate_source_review"](r,ctx),True)
for actor in [constants["ROOT_ACTOR"],constants["AUTHOR"],constants["ACTOR"]]:
 changed=copy.deepcopy(review);changed["actor_id"]=actor
 case("REVIEW_SELF_ACTOR_"+actor,lambda r=changed:env["validate_source_review"](r,ctx),True)
changed=copy.deepcopy(review);changed["decision"]="SOURCE_PASS_IN_SCOPE_WITH_OPEN"
case("PARTIAL_REVIEW_NOT_WHOLE_READY",lambda:env["validate_source_review"](changed,ctx),True)
# Both modes preserve the exact v8 child projection under the eight-key public map.
runner_raw=raw("mu_sdk_trial.v8.proposed.py");rt=ast.parse(runner_raw)
keys=next(ast.literal_eval(n.value) for n in rt.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="PHASE_BASIS_KEYS" for t in n.targets))
doc={key:None for key in keys};doc.update(phase="bootstrap",run_uuid="a"*32,cli_binary={"path":"C:/reviewed/cli.exe"},workspace="C:/isolated/workspace",goal_objective="Review only",discovery_file="C:/isolated/discovery.json",cli_config_file="C:/isolated/config.json",repository_root="D:/作品集/ResearchOS/research-os",config_revision=0,prompt="read evidence.txt",project_id="synthetic-project")
renv={"Path":Path,"os":types.SimpleNamespace(environ=legal_env),"__file__":constants["RUNNER_REF"]["path"],"pin_path":lambda _:constants["RUNNER_REF"],"require":env["require"]}
for n in rt.body:
 if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ("PHASE_BASIS_KEYS","PROVIDER","MODEL","BASE","CREDENTIAL_REF"):renv[n.targets[0].id]=ast.literal_eval(n.value)
exec(compile(ast.Module(body=[n for n in rt.body if isinstance(n,ast.FunctionDef) and n.name in ("cli_environment","phase_basis")],type_ignores=[]),"<v8-pure-projection>","exec"),renv)
for mode in ("bootstrap","execute"):
 doc["phase"]=mode
 observed=env["phase_projection"](doc,runner_raw,legal_env);wanted=renv["phase_basis"](doc,mode)
 results.append({"case":"V8_EXACT_PROJECTION_"+mode,"matches_expected":observed==wanted})
report={"schema":"researchos.observer-v2-independent-pure-controls.v1","cases":results,"prior_fixture_source_ref":row("independent_observer_controls.py")["source_ref"],"prior_negative_values_reused":{"argv":foreign_argv,"cwd":foreign_cwd,"extra":{"REVIEW_DUMMY_EXTRA":"public-not-a-secret"}},"positive_fixture_upgrade_only":"Added required WINDIR and v2 launch state with -X utf8 plus pinned worker/Python; old negative payloads unchanged","candidate_modules_imported":0,"native_WinAPI_or_product_SQL_or_provider_calls":0,"actual_frame_observed":False,"actual_process_started":False,"author_controls_executed":False,"byte_fixtures":"Pinned actual worker/interpreter snapshots; tampering occurred in memory only"}
(O/"independent-controls.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"cases":len(results),"mismatches":[r["case"] for r in results if not r["matches_expected"]],"native_calls":0,"single_read_control":next(r for r in results if r["case"]=="SINGLE_RAW_READ_AND_COMPILE_SAME_CHECKED_WORKER_BUFFER")},ensure_ascii=False))

