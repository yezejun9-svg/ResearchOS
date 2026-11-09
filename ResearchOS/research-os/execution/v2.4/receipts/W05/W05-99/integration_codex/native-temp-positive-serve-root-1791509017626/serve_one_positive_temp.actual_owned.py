import sys
sys.dont_write_bytecode=True
import json,hashlib,types,sqlite3,struct,collections,uuid,subprocess,queue,threading,datetime,ctypes
from pathlib import Path
R=Path(r"D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99";O=Path(__file__).resolve().parent
C=Path(r"D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/native-temp-controller-config-root-1791508950616/controller.public.config.json")
def pin_raw(path,raw):
 return dict(path=str(Path(path).resolve()),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def pin(path):
 path=Path(path).resolve();return pin_raw(path,path.read_bytes())
def plain(ref):
 assert set(ref)=={"path","sha256","bytes"}
 return dict(path=ref["path"],sha256=ref["sha256"].removeprefix("sha256:"),bytes=ref["bytes"])
def checked(ref,raw):
 assert pin_raw(ref["path"],raw)==plain(ref),"fixed source reference mismatch before execution"
 return raw
def save(name,value):
 with (O/name).open("xb") as f:f.write((json.dumps(value,ensure_ascii=True,indent=2)+"\n").encode("utf-8"))
 return pin(O/name)
def module_raw(ref,raw):
 raw=checked(ref,raw);path=Path(ref["path"]).resolve()
 m=types.ModuleType("root_serve_"+path.stem);m.__file__=str(path);sys.modules[m.__name__]=m
 exec(compile(raw,str(path),"exec"),m.__dict__);return m
def unique(refs):
 out={}
 for p in refs:
  key=str(Path(p["path"]).resolve()).casefold()
  assert key not in out or out[key]==p,"conflicting exact source pins"
  out[key]=p
 return list(out.values())
def runtime_pins():
 refs=[]
 for m in list(sys.modules.values()):
  for field in ("__file__","__cached__"):
   path=getattr(m,field,None)
   if path and Path(path).is_file():refs.append(pin(path))
 return refs
config_raw=C.read_bytes()
config_plain=pin_raw(C,config_raw)
assert config_plain["sha256"]=="19c92dc0af96281b0d00b1cb767ef3715e9f97102669722550e07888213808af" and config_plain["bytes"]==1163646
cfg=json.loads(config_raw)
config_ref={**config_plain,"sha256":"sha256:"+config_plain["sha256"]}
assert cfg["Schema"]=="researchos.root-native-migration-controller.v1"
fixed_python=pin(Path(sys.executable))
assert fixed_python["sha256"]=="cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b" and fixed_python["bytes"]==106328
guard_ref=cfg["SourceReadGuard"]
gm=module_raw(guard_ref,checked(guard_ref,Path(guard_ref["path"]).read_bytes()))
refs=unique([plain(p) for p in cfg["FrozenInputs"]]+[config_plain,pin(__file__),fixed_python]+runtime_pins())
guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
guard.acquire(refs)
runtime_guard=None
is_child="--child" in sys.argv
try:
 assert guard.get_buffer(str(C))==config_raw
 assert guard.get_buffer(guard_ref["path"])==checked(guard_ref,guard.get_buffer(guard_ref["path"]))
 controller=module_raw(cfg["ControllerSource"],guard.get_buffer(cfg["ControllerSource"]["path"]))
 helper=module_raw(cfg["OriginalOwnedHelper"],guard.get_buffer(cfg["OriginalOwnedHelper"]["path"]))
 c=controller.context(config_ref);assert c["hc"]["Case"]=="positive-replay"
 additional=unique([pin(p) for p in helper.runtime_resource_paths()]+runtime_pins())
 existing={p["path"].casefold():p for p in refs}
 for p in additional:
  if p["path"].casefold() in existing:assert existing[p["path"].casefold()]==p
 additional=[p for p in additional if p["path"].casefold() not in existing]
 if additional:
  runtime_guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
  runtime_guard.acquire(additional)
 if is_child:
  closed=controller.serve(config_ref)
  save("serve-child.result.json",dict(controller_closed_ref=closed,Root_only_serve=True,no_automatic_approval=True))
  data=controller.decode(controller.read_ref(closed))
  print(json.dumps({"controller_closed_ref":closed}),flush=True)
  sys.exit(0 if data["job_and_guards_closed"] and data["harness_test_exit_zero"] else 1)
 before=[pin(R/"execution/v2.4"/(n+".json")) for n in ("checkpoint","path_ownership","step_state","commands")]
 env=dict(cfg["Environment"]);env["PATH"]="C:/Windows/System32"
 argv=[str(Path(sys.executable).resolve()),"-I","-S","-B","-X","utf8",str(Path(__file__).resolve()),"--child"]
 result=None
 with (O/"serve.stdout.raw").open("xb") as stdout,(O/"serve.stderr.raw").open("xb") as stderr:
  result=helper.run_owned(argv,str(R),env,stdout,stderr,1440,creation_flags=0x08000000)
 receipt=save("serve-outer.invocation.json",dict(argv=argv,cwd=str(R),public_environment=env,result=result,actual_native_exit=result["actual_exit"],stdout_ref=pin(O/"serve.stdout.raw"),stderr_ref=pin(O/"serve.stderr.raw"),config_ref=config_ref,no_automatic_approval=True))
 j=result["job_cleanup"]
 closed=not j["errors"] and j["active_processes_last_observed"]==0 and all(j[k] for k in ("unnamed_exclusive_job","kill_on_job_close_configured","assigned_before_resume","primary_exit_confirmed","job_idle_confirmed","handles_closed"))
 assert before==[pin(p["path"]) for p in before]
 final=save("serve-outer.closed.json",dict(status="EXECUTION_REPORTED_PENDING_INDEPENDENT_REVIEW",invocation_ref=receipt,
 owned_outer_job_closed=closed,controller_closed_ref=pin(Path(cfg["ControllerDirectory"])/"controller.closed.json"),
 canonical_unchanged_refs=before,frozen_source_refs=refs,additional_runtime_refs=additional,formal_acceptance=False))
 print(json.dumps({"outer_closed_ref":final}),flush=True)
 if result["actual_exit"]!=0 or result["error"] is not None or result["timed_out"] or not closed:sys.exit(1)
finally:
 cleanups=[]
 if runtime_guard is not None:cleanups.append(runtime_guard.close())
 cleanups.append(guard.close())
 save("serve-child-source-guard.cleanup.actual.json" if is_child else "serve-outer-source-guard.cleanup.actual.json",{"guards":cleanups})
 assert all(p["closed"] and not p["errors"] and p["retained_handles_count"]==0 for p in cleanups)
