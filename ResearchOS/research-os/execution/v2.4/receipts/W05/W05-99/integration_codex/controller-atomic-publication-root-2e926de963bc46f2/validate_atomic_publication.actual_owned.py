import sys
sys.dont_write_bytecode = True
import hashlib, json, types, threading, time, os, uuid
from pathlib import Path
R=Path(r"D:/作品集/ResearchOS/research-os")
B=R/"execution/v2.4/receipts/W05/W05-99"
O=Path(__file__).resolve().parent
def pin(path):
 path=Path(path).resolve(); raw=path.read_bytes()
 return dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,value):
 with (O/name).open("xb") as f:f.write((json.dumps(value,ensure_ascii=True,indent=2)+"\n").encode("utf-8"))
 return pin(O/name)
def module(path):
 path=Path(path).resolve(); name="root_atomic_"+path.stem
 m=types.ModuleType(name);m.__file__=str(path);sys.modules[name]=m
 exec(compile(path.read_bytes(),str(path),"exec"),m.__dict__);return m
meta=json.loads((O/"source-input.reviewed.json").read_bytes())
assert meta["atomic_publication_source_accepted"] is True and meta["native_or_owner_accepted"] is False
cp=Path(meta["controller_ref"]["path"])
assert pin(cp)==meta["controller_ref"]
gp=B/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py"
hp=B/"integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py"
assert pin(gp)["sha256"]=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85"
assert pin(hp)["sha256"]=="6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad"
assert pin(sys.executable)["sha256"]=="cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b"
controller=module(cp);gm=module(gp);original=module(hp)
refs=[pin(p) for p in (cp,gp,hp,Path(__file__),Path(sys.executable),O/"source-input.reviewed.json")]
for ref in meta["review_refs"]:
 assert pin(ref["path"])==ref
 refs.append(ref)
refs += [pin(p) for p in original.runtime_resource_paths()]
refs += [pin(m.__file__) for m in list(sys.modules.values())
         if getattr(m,"__file__",None) and Path(m.__file__).is_file()]
refs=list({p["path"].casefold():p for p in refs}.values())
guard=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=768*1024*1024)
guard.acquire(refs)
canon=[R/"execution/v2.4"/(n+".json") for n in ("checkpoint","path_ownership","step_state","commands")]
before=[pin(p) for p in canon]
scratch=R/".local"/("atomic-publication-"+("inner-" if "--child" in sys.argv else "outer-")+uuid.uuid4().hex)
scratch.mkdir()
env={"SystemRoot":"C:/Windows","WINDIR":"C:/Windows","PATH":"C:/Windows/System32","TEMP":str(scratch),"TMP":str(scratch)}
try:
 if "--child" not in sys.argv:
  out=O/"atomic-cases.stdout.raw";err=O/"atomic-cases.stderr.raw"
  with out.open("xb") as stdout,err.open("xb") as stderr:
   result=original.run_owned([str(Path(sys.executable).resolve()),"-I","-S","-B","-X","utf8",str(Path(__file__).resolve()),"--child"],str(R),env,stdout,stderr,45,creation_flags=0x08000000)
  receipt=save("atomic-cases.invocation.json",dict(result=result,stdout_ref=pin(out),stderr_ref=pin(err),actual_native_exit=result["actual_exit"]))
  j=result["job_cleanup"]
  closed=not j["errors"] and j["active_processes_last_observed"]==0 and all(j[k] for k in ("unnamed_exclusive_job","kill_on_job_close_configured","assigned_before_resume","primary_exit_confirmed","job_idle_confirmed","handles_closed"))
  assert result["actual_exit"]==0 and result["error"] is None and not result["timed_out"] and closed
  inner=json.loads((O/"inner.closed.json").read_bytes())
  assert inner["cases_passed"]==["complete-publication","duplicate-no-clobber","rename-failure-cleanup","partial-ready-deferral"]
  assert [pin(p) for p in canon]==before
  final=save("validation.closed.json",dict(status="FOUR_ATOMIC_PUBLICATION_CASES_PASSED_OWNED_JOB_CLOSED_COMPONENT_ONLY",outer_invocation_ref=receipt,inner_ref=pin(O/"inner.closed.json"),runtime_refs=refs,canonical_unchanged_refs=before,owned_job_closed=closed,native_migration_cases_executed=0,owner_authority_used=False,private_key_reads=0,signatures=0,provider_requests=0,formal_acceptance=False))
  print(json.dumps({"closed_ref":final}),flush=True)
 else:
  cases=[]; final=scratch/"publication.json";value={"content":"public-"*300000}
  entered=threading.Event();release=threading.Event();done=threading.Event()
  original_fsync=controller.os.fsync
  errors=[];observations=[];writer_result=[]
  def gated_fsync(fd):
   result=original_fsync(fd)
   if threading.current_thread().name=="root-atomic-public-writer":
    entered.set()
    if not release.wait(8):raise RuntimeError("public writer gate timeout")
   return result
  def writer():
   try:writer_result.append(controller.write_new(final,value))
   except BaseException as exc:errors.append(type(exc).__name__)
   finally:done.set()
  controller.os.fsync=gated_fsync
  thread=threading.Thread(target=writer,name="root-atomic-public-writer")
  thread.start()
  try:
   assert entered.wait(8)
   for _ in range(20):
    observations.append("MISSING" if not final.exists() else "VISIBLE")
    assert not final.exists()
    time.sleep(.002)
   release.set()
   while not done.wait(.001):
    if final.exists():
     assert json.loads(final.read_bytes())==value
     observations.append("COMPLETE")
   thread.join(8)
   assert not thread.is_alive() and not errors and len(writer_result)==1
   assert json.loads(final.read_bytes())==value
  finally:
   release.set();thread.join(8);controller.os.fsync=original_fsync
  cases.append({"name":"complete-publication","final_ref":pin(final),"prepublish_missing_observations":observations.count("MISSING"),"partial_observations":0,"writer_result":writer_result})
  baseline=final.read_bytes()
  try:controller.write_new(final,{"replacement":"forbidden"})
  except FileExistsError:pass
  else:raise AssertionError("existing public final overwritten")
  assert final.read_bytes()==baseline
  assert not list(scratch.glob("*.pending")) and not list(scratch.glob("*.pending.*"))
  raced=scratch/"race.json"; winner=b'{"winner":"other-public-writer"}'
  original_rename=controller.os.rename
  def late_winner_rename(src,dst):
   if Path(dst)==raced:
    assert not raced.exists()
    raced.write_bytes(winner)
   return original_rename(src,dst)
  controller.os.rename=late_winner_rename
  try:
   try:controller.write_new(raced,{"loser":"must-not-overwrite"})
   except FileExistsError:pass
   else:raise AssertionError("rename-time destination race overwritten")
  finally:controller.os.rename=original_rename
  assert raced.read_bytes()==winner and not list(scratch.glob("*.pending"))
  cases.append({"name":"duplicate-no-clobber","final_unchanged_ref":pin(final),"rename_time_winner_unchanged_ref":pin(raced)})
  rejected=scratch/"rejected.json"; original_rename=controller.os.rename
  def refused_rename(src,dst):
   if Path(dst)==rejected:raise OSError("synthetic publication refusal")
   return original_rename(src,dst)
  controller.os.rename=refused_rename
  try:
   try:controller.write_new(rejected,{"public":True})
   except OSError as exc:assert "synthetic publication refusal" in str(exc)
   else:raise AssertionError("synthetic rename refusal not preserved")
  finally:controller.os.rename=original_rename
  assert not rejected.exists()
  remaining=[p.name for p in scratch.iterdir() if p not in (final,raced)]
  assert not remaining,remaining
  cases.append({"name":"rename-failure-cleanup","final_exists":False,"remaining_temp_files":[]})
  output=scratch/"go-ready";output.mkdir()
  ready=output/controller.PHASES["release"][1]
  ready.write_bytes(b'{"public":')
  assert controller._phase({"output":output})=="running"
  ready.write_bytes(b'{"public":true}')
  assert controller._phase({"output":output})=="release"
  cases.append({"name":"partial-ready-deferral","incomplete_phase":"running","complete_phase":"release","ready_ref":pin(ready)})
  final=save("inner.closed.json",dict(cases_passed=[c["name"] for c in cases],case_evidence=cases,native_or_owner_execution=False))
  print(json.dumps({"inner_ref":final}),flush=True)
finally:
 cleanup=guard.close();save(("inner" if "--child" in sys.argv else "outer")+"-source-guard.cleanup.actual.json",cleanup)
 assert cleanup["closed"] and not cleanup["errors"] and cleanup["retained_handles_count"]==0
