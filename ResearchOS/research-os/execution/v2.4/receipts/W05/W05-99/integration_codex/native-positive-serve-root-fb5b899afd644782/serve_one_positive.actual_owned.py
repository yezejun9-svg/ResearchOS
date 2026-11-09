import sys
sys.dont_write_bytecode=True
import json,hashlib,types
from pathlib import Path
R=Path(r"D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99";O=Path(__file__).resolve().parent
C=B/"integration_codex/native-positive-controller-config-v2-root-0da7b5a0b3f84a13/controller.public.config.json"
def pin(path):
 path=Path(path).resolve();raw=path.read_bytes()
 return dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def pref(path):
 v=pin(path);v["sha256"]="sha256:"+v["sha256"];return v
def save(name,value):
 with (O/name).open("xb") as f:f.write((json.dumps(value,ensure_ascii=True,indent=2)+"\n").encode("utf-8"))
 return pin(O/name)
def module(path):
 path=Path(path).resolve();m=types.ModuleType("root_serve_"+path.stem);m.__file__=str(path);sys.modules[m.__name__]=m
 exec(compile(path.read_bytes(),str(path),"exec"),m.__dict__);return m
assert pin(C)["sha256"]=="9d561a6be761ebb2e61bb72a7bee22b07e188cee3877105827f4ca48ba6928fc"
cfg=json.loads(C.read_bytes());config_ref=pref(C)
assert cfg["Schema"]=="researchos.root-native-migration-controller.v1"
controller=module(cfg["ControllerSource"]["path"])
c=controller.context(config_ref);assert c["hc"]["Case"]=="positive-replay"
gp=Path(cfg["SourceReadGuard"]["path"]);hp=Path(cfg["OriginalOwnedHelper"]["path"])
gm=module(gp);helper=module(hp)
assert pin(sys.executable)["sha256"]=="cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b"
if "--child" in sys.argv:
 closed=controller.serve(config_ref)
 save("serve-child.result.json",dict(controller_closed_ref=closed,Root_only_serve=True,no_automatic_approval=True))
 data=controller.decode(controller.read_ref(closed))
 print(json.dumps({"controller_closed_ref":closed}),flush=True)
 sys.exit(0 if data["job_and_guards_closed"] and data["harness_test_exit_zero"] else 1)
refs=[dict(path=p["path"],sha256=p["sha256"].removeprefix("sha256:"),bytes=p["bytes"]) for p in cfg["FrozenInputs"]]
refs += [pin(p) for p in (C,Path(__file__),Path(sys.executable))]
refs += [pin(p) for p in helper.runtime_resource_paths()]
for m in list(sys.modules.values()):
 for field in ("__file__","__cached__"):
  path=getattr(m,field,None)
  if path and Path(path).is_file():refs.append(pin(path))
refs=list({p["path"].casefold():p for p in refs}.values())
guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);guard.acquire(refs)
before=[pin(R/"execution/v2.4"/(n+".json")) for n in ("checkpoint","path_ownership","step_state","commands")]
env=dict(cfg["Environment"]);env["PATH"]="C:/Windows/System32"
argv=[str(Path(sys.executable).resolve()),"-I","-S","-B","-X","utf8",str(Path(__file__).resolve()),"--child"]
result=None
try:
 with (O/"serve.stdout.raw").open("xb") as stdout,(O/"serve.stderr.raw").open("xb") as stderr:
  result=helper.run_owned(argv,str(R),env,stdout,stderr,1440,creation_flags=0x08000000)
 receipt=save("serve-outer.invocation.json",dict(argv=argv,cwd=str(R),public_environment=env,result=result,actual_native_exit=result["actual_exit"],stdout_ref=pin(O/"serve.stdout.raw"),stderr_ref=pin(O/"serve.stderr.raw"),config_ref=config_ref,no_automatic_approval=True))
 j=result["job_cleanup"]
 closed=not j["errors"] and j["active_processes_last_observed"]==0 and all(j[k] for k in ("unnamed_exclusive_job","kill_on_job_close_configured","assigned_before_resume","primary_exit_confirmed","job_idle_confirmed","handles_closed"))
 assert before==[pin(p["path"]) for p in before]
 final=save("serve-outer.closed.json",dict(status="EXECUTION_REPORTED_PENDING_INDEPENDENT_REVIEW",invocation_ref=receipt,
 owned_outer_job_closed=closed,controller_closed_ref=pin(Path(cfg["ControllerDirectory"])/"controller.closed.json"),
 canonical_unchanged_refs=before,frozen_source_refs=refs,formal_acceptance=False))
 print(json.dumps({"outer_closed_ref":final}),flush=True)
 if result["actual_exit"]!=0 or result["error"] is not None or result["timed_out"] or not closed:sys.exit(1)
finally:
 cleanup=guard.close();save("serve-outer-source-guard.cleanup.actual.json",cleanup)
 assert cleanup["closed"] and not cleanup["errors"] and cleanup["retained_handles_count"]==0
