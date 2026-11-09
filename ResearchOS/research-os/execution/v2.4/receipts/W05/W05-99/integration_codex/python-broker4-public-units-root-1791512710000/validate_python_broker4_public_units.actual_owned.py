import sys
sys.dont_write_bytecode=True
import argparse,hashlib,importlib.util,os,json,types,tempfile,traceback,unittest
from unittest import mock
import subprocess,threading,queue,ctypes,re,shutil
from pathlib import Path
R=Path(r"D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99";O=Path(__file__).resolve().parent
S=B/"native_python_broker_temp_env_revision_codex/7bc2467624af477a8d55e0595ec4a7c2";V=B/"native_python_broker_temp_env_independent_review_codex/9e4f389d093d4ea58eb5ec06e102876d"
GP=B/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py";HP=B/"integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py"
def pin(p):
 p=Path(p).resolve();raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def verify(v):
 q=pin(v["path"]);assert (q["sha256"],q["bytes"])==(v["sha256"].removeprefix("sha256:"),v["bytes"]);return q
def check(p,h,n):
 q=pin(p);assert(q["sha256"],q["bytes"])==(h,n);return q
def save(n,v):
 with (O/n).open("xb") as f:f.write((json.dumps(v,ensure_ascii=True,indent=2)+"\n").encode())
 return pin(O/n)
def module(p,raw):
 p=Path(p).resolve();m=types.ModuleType("root_broker4_"+p.stem);m.__file__=str(p);sys.modules[m.__name__]=m;exec(compile(raw,str(p),"exec"),m.__dict__);return m
bp=S/"root_only_native_broker.py";up=S/"broker_temp_environment_boundary_test.py"
br=check(bp,"70b8eba1de168849d041488ac9268da60fd2ae8a059cc9518e9dc93d0cd4b87c",8562)
ur=check(up,"0b5f78f27a5a52c74f438b954d40d561c1149b85a13bd8650964b635cf264963",7677)
refs=[br,ur,pin(__file__),check(sys.executable,"cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b",106328),
check(GP,"e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85",11404),
check(HP,"6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad",18901)]
for d,hh,hn,mh,mn in [(S,"ed0f388870aef974f9577e6d5146637d5a1a77ce6b22c57e989227654de05824",6761,"deab5d3bb0fc512c37808a4dcd9b66d370dcd0c1ae14b84e1949fcfdb915ebdc",9803),(V,"7c0ad0872da573a5a6948b2c6e7d55a438e57e3cc2ba65b70329e9cea6dd2518",4535,"8edd94cc087bf2f042fcec9a892f04687eb0898dc67c683e2fe710f85cbf58bb",5044)]:
 refs += [check(d/"HDF.json",hh,hn),check(d/"MF.json",mh,mn)]
 members=json.loads((d/"MF.json").read_bytes())["members"];members=members.values() if isinstance(members,dict) else members;refs += [verify(v) for v in members]
canonical=[R/"execution/v2.4"/(n+".json") for n in ("checkpoint","path_ownership","step_state","commands")];before=[pin(p) for p in canonical]
gm=module(GP,GP.read_bytes());helper=module(HP,HP.read_bytes())
inputguard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
inputguard.acquire(list({v["path"].casefold():v for v in refs}.values()))
runtimeguard=None;result=None
try:
 units=module(up,inputguard.get_buffer(str(up.resolve())))
 broker=module(bp,inputguard.get_buffer(str(bp.resolve())))
 methods=sorted(n for n in units.PublicEnvironmentBoundaryTests.__dict__ if n.startswith("test_"));assert len(methods)==17
 runtime=[pin(p) for p in helper.runtime_resource_paths()]
 for mod in list(sys.modules.values()):
  for field in ("__file__","__cached__"):
   p=getattr(mod,field,None)
   if p and Path(p).is_file():runtime.append(pin(p))
 runtime=list({v["path"].casefold():v for v in runtime}.values())
 runtime_ref=save("python-public-unit-runtime-inventory.json",dict(resources=runtime,public_modules_loaded_before_freeze=True,scope="Actual preloaded unit/broker imports and loaded Windows/Python module inventory",native_helper_or_private_calls=0))
 runtimeguard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);runtimeguard.acquire(runtime)
 scratch=R/".local/python-broker4-public-units-env-1791512710000";scratch.mkdir(exist_ok=False)
 env={k:os.environ[k] for k in ("SystemRoot","WINDIR")};env.update(TEMP=str(scratch.resolve()),TMP=str(scratch.resolve()))
 argv=[str(Path(sys.executable).resolve()),"-I","-S","-B","-X","utf8",str(up.resolve()),"--broker-source",str(bp.resolve()),"--broker-sha256",br["sha256"],"--verbosity","2"]
 result=helper.run_owned(argv,str(R),env,str(O/"units.stdout.raw"),str(O/"units.stderr.raw"),60,creation_flags=0x08000000)
 invocation=save("units.invocation.json",dict(argv=argv,cwd=str(R),public_environment=env,owned_process=result,actor="Python public boundary test",broker_source_ref=br,unit_source_ref=ur,runtime_inventory_ref=runtime_ref,private_inputs=0,provider_calls_from_this_public_unit=0,formal_acceptance=False))
 assert result["actual_exit"]==0 and result["job_cleanup"]["job_idle_confirmed"] and result["job_cleanup"]["handles_closed"] and not result["job_cleanup"]["errors"]
 stderr=(O/"units.stderr.raw").read_text(encoding="utf-8");stdout=(O/"units.stdout.raw").read_text(encoding="utf-8")
 terminals=re.findall(r"^test_[^\r\n]+ \.\.\. (ok|FAIL|ERROR|skipped[^\r\n]*)$",stderr,re.M)
 assert terminals==["ok"]*17 and "Ran 17 tests" in stderr and "ROOT_PYTHON_EXIT=0" in stdout,(len(terminals),stderr[-500:])
 assert not any(scratch.iterdir());scratch.rmdir()
 assert [pin(p) for p in canonical]==before
 summary=save("units.results.json",dict(test_method_names=methods,pass_count=17,fail_count=0,skip_count=0,actual_python_child_exit=0,owned_job_closed=True,alias_scope="MOCK_ONLY_NO_ACTUAL_JUNCTION",canonical_path_scope="PATH_NORMALIZED_PHYSICAL_CANONICAL",system_descendant_dedicated_test=False,no_broker_main_or_private_helper_call=True,invocation_ref=invocation,stdout_ref=pin(O/"units.stdout.raw"),stderr_ref=pin(O/"units.stderr.raw"),formal_acceptance=False))
finally:
 if runtimeguard:
  cleanup=runtimeguard.close();save("runtime-source-guard.cleanup.actual.json",cleanup);assert cleanup["closed"] and not cleanup["errors"] and cleanup["retained_handles_count"]==0
 cleanup=inputguard.close();save("input-source-guard.cleanup.actual.json",cleanup);assert cleanup["closed"] and not cleanup["errors"] and cleanup["retained_handles_count"]==0
closed=save("validation.closed.json",dict(status="BROKER4_PUBLIC_BOUNDARIES_17_PASS_COMPONENT_ONLY_NATIVE_PENDING",results_ref=summary,source_input_ref_count=len(refs),runtime_ref_count=len(runtime),actual_outer_driver_exit=0,python_unit_owned_actual_exit=result["actual_exit"],job_cleanup=result["job_cleanup"],canonical_unchanged=True,formal_acceptance=False))
print(json.dumps(dict(closed_ref=closed,pass_count=17,fail_count=0,skip_count=0)),flush=True)


