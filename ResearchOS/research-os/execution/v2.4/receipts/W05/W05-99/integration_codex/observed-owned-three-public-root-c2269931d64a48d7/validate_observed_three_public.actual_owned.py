import sys
sys.dont_write_bytecode=True
import hashlib,json,types,time,uuid
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99";O=Path(__file__).resolve().parent
S=B/"native_migration_root_controller_source_codex/949c31b5ce9172756b85a2aa388"
def pin(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(n,v):
 p=O/n
 with p.open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode("utf-8"))
 return pin(p)
def module(p):
 m=types.ModuleType("root_observed_dummy_"+p.stem);m.__file__=str(p);exec(compile(p.read_bytes(),str(p),"exec"),m.__dict__);return m
gp=B/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py"
hp=B/"integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py"
np=S/"windows_owned_observed.py";python=Path(sys.executable);probe=O/"public_probe.py"
assert pin(gp)["sha256"]=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85"
assert pin(hp)["sha256"]=="6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad"
assert pin(np)["sha256"]=="fe102f02de5aa966945ef88218e412f1988509168705d03a8660dab8b282d4e3"
assert pin(python)["sha256"]=="cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b"
accepted=json.loads((O/"source-review.accepted.json").read_bytes());assert accepted["allows_three_public_observed_owned_cases"] is True and accepted["real_owner_authority_accepted"] is False
refs=[pin(p) for p in (gp,hp,np,python,probe,Path(__file__).resolve(),O/"source-review.accepted.json")]
for r in accepted["review_refs"]:
 a=pin(r["path"]);assert a["sha256"]==r["sha256"] and a["bytes"]==r["bytes"];refs.append(a)
gm=module(gp);original=module(hp);observed=module(np)
refs += [pin(p) for p in original.runtime_resource_paths()]
refs += [pin(Path(m.__file__).resolve()) for m in list(sys.modules.values()) if getattr(m,"__file__",None) and Path(m.__file__).is_file()]
refs=list({r["path"]:r for r in refs}.values());guard=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=768*1024*1024);guard.acquire(refs)
canonical=[R/"execution/v2.4"/(n+".json") for n in ("checkpoint","path_ownership","step_state","commands")];before={p:p.read_bytes() for p in canonical};assert json.loads(before[canonical[0]])["revision"]==356
scratch=R/".local"/("observed-owned-public-"+("inner" if "--child" in sys.argv else "outer")+"-"+uuid.uuid4().hex);scratch.mkdir()
env={"SystemRoot":"C:/Windows","WINDIR":"C:/Windows","PATH":"C:/Windows/System32","TEMP":str(scratch),"TMP":str(scratch)}
def good(c):
 return not c["errors"] and c["active_processes_last_observed"]==0 and all(c[k] for k in ("unnamed_exclusive_job","kill_on_job_close_configured","assigned_before_resume","primary_exit_confirmed","job_idle_confirmed","handles_closed"))
try:
 if "--child" not in sys.argv:
  out=O/"three-public-cases.stdout.raw";err=O/"three-public-cases.stderr.raw"
  with out.open("xb") as stdout,err.open("xb") as stderr:
   result=original.run_owned([str(python),"-I","-S","-B","-X","utf8",str(Path(__file__).resolve()),"--child"],str(R),env,stdout,stderr,70,creation_flags=0x08000000)
  receipt=save("three-public-cases.invocation.json",dict(result=result,stdout_ref=pin(out),stderr_ref=pin(err),actual_native_exit=result["actual_exit"],provider_requests=0,production_db_writes=0))
  assert result["actual_exit"]==0 and not result["timed_out"] and result["error"] is None and good(result["job_cleanup"])
  inner=json.loads((O/"inner.closed.json").read_bytes());assert inner["cases_passed"]==["normal","cancel","timeout"] and inner["all_three_jobs_closed"]
  assert all(p.read_bytes()==b for p,b in before.items())
  ref=save("validation.closed.json",dict(status="THREE_PUBLIC_OBSERVE_CANCEL_TIMEOUT_CASES_PASSED_FOUR_JOBS_CLOSED_COMPONENT_ONLY",outer_invocation_ref=receipt,inner_ref=pin(O/"inner.closed.json"),frozen_runtime_refs=refs,all_four_jobs_closed=True,main_canonical_unchanged=True,Owner_private_input_used=False,native_migration_executed=False,provider_requests=0,production_db_writes=0,formal_acceptance=False))
  print(json.dumps(dict(closed_ref=ref,status="THREE_PUBLIC_CASES_PASSED")),flush=True)
 else:
  cases=[]
  for mode in ("normal","cancel","timeout"):
   events=[];ready=scratch/(mode+".ready.json");seen_two=[False]
   def callback(event,snapshot):
    events.append(dict(event=event,observation=snapshot))
    if (snapshot["job_cleanup"].get("active_processes_last_observed") or 0)>=2 and ready.exists():seen_two[0]=True
   def cancellation():return mode=="cancel" and seen_two[0]
   out=O/(mode+".stdout.raw");err=O/(mode+".stderr.raw")
   with out.open("xb") as stdout,err.open("xb") as stderr:
    result=observed.run_owned_observed([str(python),"-I","-S","-B","-X","utf8",str(probe),mode,str(ready)],str(R),env,stdout,stderr,2.0 if mode=="timeout" else 12,creation_flags=0x08000000,on_observation=callback,cancel_requested=cancellation)
   assert good(result["job_cleanup"]) and result["resumed"] and result["owned_child_pid"] is not None and events and events[0]["event"]=="assigned-before-resume" and not events[0]["observation"]["resumed"]
   if mode=="normal":assert result["actual_exit"]==0 and not result["timed_out"] and result["error"] is None
   elif mode=="cancel":assert seen_two[0] and result["actual_exit"] is not None and result["actual_exit"]!=0 and not result["timed_out"] and "Root requested owned case cancellation" in result["error"]
   else:assert seen_two[0] and result["actual_exit"] is not None and result["actual_exit"]!=0 and result["timed_out"]
   receipt=save(mode+".actual.json",dict(result=result,events=events,public_ready_ref=pin(ready),descendant_observed=seen_two[0],stdout_ref=pin(out),stderr_ref=pin(err),component_only=True,actual_held_job_observation=True));cases.append(receipt)
  ref=save("inner.closed.json",dict(cases_passed=["normal","cancel","timeout"],case_refs=cases,all_three_jobs_closed=True,Main_or_native_authority_claim=False))
  print(json.dumps(dict(inner_closed_ref=ref)),flush=True)
finally:
 c=guard.close();save(("inner" if "--child" in sys.argv else "outer")+"-source-guard.cleanup.actual.json",c);assert c["closed"] and not c["errors"] and c["retained_handles_count"]==0
