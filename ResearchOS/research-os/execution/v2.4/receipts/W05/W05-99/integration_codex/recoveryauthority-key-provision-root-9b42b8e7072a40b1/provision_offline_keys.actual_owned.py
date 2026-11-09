import sys
sys.dont_write_bytecode=True
import json,hashlib,re,types
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99";O=Path(__file__).resolve().parent
V=B/"integration_codex/native-authority-unprovisioned-component-root-cb0935d7bf444f4f"
P=R/".local/resources/recoveryauthority-enrollment-52d176f3e0684166"
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(n,v):
 p=O/n
 with p.open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(p)
def mod(p,raw):
 m=types.ModuleType("root_provision_"+p.stem);m.__file__=str(p);exec(compile(raw,str(p),"exec"),m.__dict__);return m
closed=json.loads((V/"validation.closed.json").read_bytes())
assert closed["status"]=="UNPROVISIONED_AUTHORITY_LEAF_TESTS_AND_ENROLLMENT_BUILD_PASSED_SOURCE_ONLY"
binary=closed["binary_ref"];assert pin(binary["path"])==binary
assert closed["test_actions"] and all(v=="pass" for v in closed["test_actions"].values())
g=B/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py";h=B/"integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py"
assert pin(g)["sha256"]=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85" and pin(h)["sha256"]=="6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad"
canonical=[R/"execution/v2.4"/(n+".json") for n in ("checkpoint","path_ownership","step_state","commands")];before={p:p.read_bytes() for p in canonical};assert json.loads(before[canonical[0]])["revision"]==352
refs=[pin(g),pin(h),binary,pin(V/"validation.closed.json"),pin(V/"original-tool-io.json"),pin(Path(__file__).resolve())]
gm=mod(g,g.read_bytes());guard=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=512*1024*1024);guard.acquire(refs)
helper=mod(h,guard.get_buffer(str(h)));P.mkdir(parents=True,exist_ok=False)
scratch=O/"scratch";scratch.mkdir();(scratch/"temp").mkdir()
env={"SystemRoot":"C:/Windows","WINDIR":"C:/Windows","ComSpec":"C:/Windows/System32/cmd.exe","PATH":"C:/Windows/System32","PATHEXT":".COM;.EXE;.BAT;.CMD","TEMP":str(scratch/"temp"),"TMP":str(scratch/"temp")}
keys={};invocations=[]
try:
 for role in ("issuer","root-adoption"):
  dest=P/(role+".private.dpapi");assert not dest.exists()
  out=O/(role+".stdout.public.raw");err=O/(role+".stderr.raw");result=None;exception=None;argv=[binary["path"],"provision",role,str(dest)]
  try:
   with out.open("xb") as stdout,err.open("xb") as stderr:result=helper.run_owned(argv,str(R),env,stdout,stderr,30,creation_flags=0x08000000)
  except BaseException as e:exception=repr(e)
  receipt=save(role+".invocation.json",dict(argv=argv,cwd=str(R),public_environment=env,result=result,exception=exception,actual_native_exit=result.get("actual_exit") if result else None,stdout_public_ref=pin(out),stderr_ref=pin(err),provider_requests=0,production_db_writes=0))
  invocations.append(receipt)
  assert exception is None and result and result["actual_exit"]==0 and not result["timed_out"] and result["error"] is None
  c=result["job_cleanup"];assert not c["errors"] and c["active_processes_last_observed"]==0 and all(c[k] for k in ("unnamed_exclusive_job","kill_on_job_close_configured","assigned_before_resume","primary_exit_confirmed","job_idle_confirmed","handles_closed"))
  pub=out.read_text(encoding="utf-8").strip();assert re.fullmatch("[0-9a-f]{64}",pub) and dest.is_file()
  keys[role]=dict(public_key_hex=pub,private_resource_ref=pin(dest),private_format="Windows DPAPI current-user scope, role-bound entropy, private DACL, CREATE_NEW",private_plaintext_logged=False)
  print(json.dumps(dict(role=role,public_key_hex=pub,actual_native_exit=0,job_closed=True)),flush=True)
 assert all(p.read_bytes()==raw for p,raw in before.items())
 ref=save("key-provision.closed.json",dict(status="OFFLINE_KEYS_CREATED_PUBLIC_ONLY_NOT_AN_ACCEPTED_AUTHORITY",keys=keys,invocation_refs=invocations,accepted_binary_ref=binary,current_source_anchor_empty=True,Main_canonical_unchanged=True,provider_requests=0,production_db_writes=0,formal_acceptance=False))
 print(json.dumps(dict(closed_ref=ref,provider_requests=0)),flush=True)
finally:
 c=guard.close();save("source-guard.cleanup.actual.json",c);assert c["closed"] and not c["errors"] and c["retained_handles_count"]==0
