import sys
sys.dont_write_bytecode=True
import json,hashlib,types,uuid
from pathlib import Path
R=Path(r"D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99";O=Path(__file__).resolve().parent
A=B/"integration_codex/native-harness43-compile-unit-root-c16a0730cf914bc5"
W=B/"integration_codex/w04-frozen-resource-verification-root-4e17c2a0972847f5"
I=B/"w04_frozen_resource_independent_review_codex/05c0c29c21ff4365a2190d2bc18e4aca"
def pin(path):
 path=Path(path).resolve();raw=path.read_bytes()
 return dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,value):
 with (O/name).open("xb") as f:f.write((json.dumps(value,ensure_ascii=True,indent=2)+"\n").encode("utf-8"))
 return pin(O/name)
def module(path):
 path=Path(path).resolve();m=types.ModuleType("root_w04_actual_"+path.stem);m.__file__=str(path);sys.modules[m.__name__]=m
 exec(compile(path.read_bytes(),str(path),"exec"),m.__dict__);return m
gp=B/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py"
hp=B/"integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py"
assert pin(gp)["sha256"]=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85"
assert pin(hp)["sha256"]=="6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad"
assert pin(sys.executable)["sha256"]=="cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b"
assert pin(I/"HDF.json")["sha256"]=="9675641fceb04ef601823ecbcca7e0d51b9aa037e9355942474c166b32a9f12f"
assert pin(I/"MF.json")["sha256"]=="304d068552632c229c014ce3260b45c4b3f6c62c7c3a2c6c827d14b8ad0c3b5f"
assert json.loads((I/"HDF.json").read_bytes())["decision"]=="W04_FROZEN_RESOURCE_COMPONENT_ACCEPTED_STOP"
actual=json.loads((A/"validation.closed.json").read_bytes())
test=actual["binary_refs"]["tagged-test-harness"];assert pin(test["path"])==test
inventory_ref=actual["compiler_input_inventory_ref"];assert pin(inventory_ref["path"])==inventory_ref
inventory=json.loads(Path(inventory_ref["path"]).read_bytes())
build=json.loads((A/"tagged-test-binary-compile.invocation.json").read_bytes())
T=Path(actual["current_source_root"]).resolve()
resource=json.loads((W/"resource-closure.actual.json").read_bytes())
gm=module(gp);helper=module(hp)
refs=inventory["build_inputs"]+inventory["product_inventory"]+inventory["compiler_tool_refs"]+resource["source_refs"]
refs += [pin(p) for p in (gp,hp,Path(__file__),Path(sys.executable),A/"validation.closed.json",
        Path(inventory_ref["path"]),A/"tagged-test-binary-compile.invocation.json",
        W/"resource-closure.actual.json",I/"HDF.json",I/"MF.json",Path(test["path"]))]
refs += [pin(p) for p in (T/"spec/v2.0").rglob("*") if p.is_file()]
refs += [pin(p) for p in helper.runtime_resource_paths()]
refs += [pin(m.__file__) for m in list(sys.modules.values()) if getattr(m,"__file__",None) and Path(m.__file__).is_file()]
refs=list({str(Path(p["path"]).resolve()).casefold():dict(path=str(Path(p["path"]).resolve()),sha256=p["sha256"].removeprefix("sha256:"),bytes=p["bytes"]) for p in refs}.values())
guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
guard.acquire(refs)
before=[pin(R/"execution/v2.4"/(n+".json")) for n in ("checkpoint","path_ownership","step_state","commands")]
scratch=R/".local"/("w04-two-resource-env-"+uuid.uuid4().hex)
(scratch/"temp").mkdir(parents=True);(scratch/"profile").mkdir()
env=dict(build["public_environment"])
env["PATH"]=str(Path(sys.executable).resolve().parent)+";"+env["PATH"]
env.update(PYTHONUTF8="1",PYTHONDONTWRITEBYTECODE="1",RESEARCHOS_W04_PACKAGE_INPUT=resource["package_input"])
for k in ("TEMP","TMP"):env[k]=str((scratch/"temp").resolve())
for k in ("USERPROFILE","LOCALAPPDATA","APPDATA"):env[k]=str((scratch/"profile").resolve())
go=Path(build["argv"][0]);assert pin(go)["sha256"]=="d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490"
env["RESEARCHOS_GO"]=str(go)
argv=[str(go),"tool","test2json","-t","-p","researchos.local/research-os/internal/domain",test["path"],
      "-test.v=test2json","-test.run=^(TestW04A01|TestW04CurrentA01)$","-test.count=1","-test.timeout=3m"]
result=None;error=None;cleanup=None
out=O/"two-cases.stdout.jsonl";err=O/"two-cases.stderr.raw"
try:
 with out.open("xb") as stdout,err.open("xb") as stderr:
  result=helper.run_owned(argv,str(T/"internal/domain"),env,stdout,stderr,240,creation_flags=0x08000000)
finally:
 cleanup=guard.close();save("input-source-guard.cleanup.actual.json",cleanup)
receipt=save("two-cases.invocation.json",dict(argv=argv,cwd=str(T/"internal/domain"),public_environment=env,result=result,actual_native_exit=result["actual_exit"] if result else None,stdout_ref=pin(out),stderr_ref=pin(err),native_migration_cases_executed=0,original_trial_DB_writes=0,external_provider_requests=0))
assert cleanup["closed"] and not cleanup["errors"] and cleanup["retained_handles_count"]==0
j=result["job_cleanup"]
closed=not j["errors"] and j["active_processes_last_observed"]==0 and all(j[k] for k in ("unnamed_exclusive_job","kill_on_job_close_configured","assigned_before_resume","primary_exit_confirmed","job_idle_confirmed","handles_closed"))
events=[json.loads(line) for line in out.read_text(encoding="utf-8").splitlines() if line]
runs=[e["Test"] for e in events if e["Action"]=="run" and e.get("Test")]
term={}
for e in events:
 if e["Action"] in ("pass","fail","skip") and e.get("Test"):
  assert e["Test"] not in term
  term[e["Test"]]=e["Action"]
assert set(runs)==set(term)
counts={a:list(term.values()).count(a) for a in ("pass","fail","skip")}
passed=result["actual_exit"]==0 and result["error"] is None and not result["timed_out"] and closed and counts["fail"]==counts["skip"]==0 and all(term.get(n)=="pass" for n in ("TestW04A01","TestW04CurrentA01"))
assert before==[pin(p["path"]) for p in before]
final=save("validation.closed.json",dict(status="W04_TWO_RESOURCE_REPAIRED_CASES_PASSED_COMPONENT_ONLY" if passed else "W04_TWO_CASES_FAILED_CLOSED_COMPONENT_ONLY",
 invocation_ref=receipt,terminal_actions=term,counts=counts,owned_job_closed=closed,source_guard_closed=True,
 canonical_unchanged_refs=before,compiler_input_ref=inventory_ref,test_binary_ref=test,frozen_source_refs=refs,
 exact_resource_ref=pin(W/"resource-closure.actual.json"),resource_independent_ref=pin(I/"HDF.json"),
 native_migration_cases_executed=0,private_key_reads=0,issuer_signatures=0,original_trial_DB_writes=0,external_provider_requests=0,formal_acceptance=False))
print(json.dumps({"closed_ref":final,"counts":counts,"owned_job_closed":closed}),flush=True)
if not passed:sys.exit(1)
