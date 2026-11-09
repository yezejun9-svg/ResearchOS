import sys
sys.dont_write_bytecode = True
import hashlib, importlib.util, json, os, types
from pathlib import Path
R = Path("D:/作品集/ResearchOS/research-os")
B = R / "execution/v2.4/receipts/W05/W05-99"
O = Path(__file__).resolve().parent
Q = B / "native_private_stdin_helper_revision_codex/320740c9ef7c4dbaa6cae48633aa8e60"
gp = B / "source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py"
hp = B / "integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py"
python = Path("C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe")
def pin(p):
    p = Path(p); raw = p.read_bytes()
    return dict(path=str(p), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
def verify(ref):
    actual=pin(ref["path"])
    assert actual["sha256"]==ref["sha256"] and actual["bytes"]==ref["bytes"]
    return actual
def save(n, value):
    path=O/n
    with path.open("xb") as f: f.write((json.dumps(value,ensure_ascii=False,indent=2)+"\n").encode("utf-8"))
    return pin(path)
def module(p,raw):
    m=types.ModuleType("root_private_pipe_"+p.stem)
    m.__file__=str(p);exec(compile(raw,str(p),"exec"),m.__dict__)
    return m
for path, expected in ((Q/"HDF.json","5f6ce572df2365f7cae2b851d4a111b9220d6c21ec7cc0394806ac6fbc202770"),
                       (Q/"MF.json","d10203f609a9b6a5dbce6e6d382f8f59a2131448739387b7cc3465e9cb21a4d1"),
                       (gp,"e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85"),
                       (hp,"6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad"),
                       (python,"cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b")):
    assert pin(path)["sha256"]==expected
assert Path(sys.executable).resolve()==python.resolve()
config=json.loads((O/"source-review.accepted.json").read_text(encoding="utf-8"))
assert Path(config["source_namespace"])==Q and config["source_review_accepted"] is True
review_refs=[verify(r) for r in config["review_refs"]]
manifest=json.loads((Q/"MF.json").read_text(encoding="utf-8"))
source_refs=[verify(r) for r in manifest["source_refs"].values()]
assert len(source_refs)==3
refs=[*source_refs,*review_refs,pin(O/"source-review.accepted.json"),pin(Q/"MF.json"),pin(Q/"HDF.json"),pin(gp),pin(hp),pin(python),pin(Path(__file__).resolve())]
refs += [verify(r) for r in manifest["members"].values()]
refs += [verify(r) for r in manifest["base_refs"]]
canonical=[R/"execution/v2.4"/(n+".json") for n in ("checkpoint","path_ownership","step_state","commands")]
before={p:p.read_bytes() for p in canonical}
assert json.loads(before[canonical[0]])["revision"]==354
gm=module(gp,gp.read_bytes())
initial=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=256*1024*1024)
initial.acquire(list({r["path"]:r for r in refs}.values()))
runtime_guard=None;result=None;invocation_ref=None;closed_ref=None
try:
    helper=module(hp,initial.get_buffer(str(hp)))
    private_helper=module(Q/"windows_owned_private_stdin.py",initial.get_buffer(str(Q/"windows_owned_private_stdin.py")))
    resource_paths=private_helper.runtime_resource_paths()
    python_sources=[]
    for m in tuple(sys.modules.values()):
        path=getattr(m,"__file__",None)
        if path and Path(path).is_file(): python_sources.append(str(Path(path).resolve()))
    runtime_refs=list({r["path"]:r for r in [pin(p) for p in [*resource_paths,*python_sources,str(python)]]}.values())
    runtime_inventory_ref=save("runtime-resources.actual.json",dict(loaded_native_resource_paths=resource_paths,loaded_python_module_paths=sorted(set(python_sources)),refs=runtime_refs,
        scope="ACTUAL_LOADED_MODULES_AND_PYTHON_SOURCES_POINT_IN_TIME",complete_future_dynamic_loading_claim=False))
    runtime_guard=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=256*1024*1024)
    runtime_guard.acquire([*runtime_refs,runtime_inventory_ref])
    frozen_ref=save("frozen-source-inputs.json",list({r["path"]:r for r in refs}.values()))
    scratch=R/".local/private-pipe-public-dummy-2312f157a0344c78"
    scratch.mkdir(parents=True,exist_ok=False)
    output=scratch/"actual-six-cases"
    argv=[str(python),"-I","-S","-B","-X","utf8",str(Q/"root_verify_private_pipe.py"),str(output)]
    env={k:os.environ[k] for k in ("SystemRoot","WINDIR") if k in os.environ}
    env["PYTHONUTF8"]="1"
    stdout_path=O/"six-public-cases.stdout.raw";stderr_path=O/"six-public-cases.stderr.raw"
    exception=None
    try:
        with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
            result=helper.run_owned(argv,str(Q),env,stdout,stderr,120,creation_flags=0x08000000)
    except BaseException as exc: exception=repr(exc)
    invocation_ref=save("six-public-cases.invocation.json",dict(argv=argv,cwd=str(Q),public_environment=env,result=result,exception=exception,
        actual_native_exit=result.get("actual_exit") if result else None,stdout_ref=pin(stdout_path),stderr_ref=pin(stderr_path),
        scope="PUBLIC_DUMMY_INPUT_ONLY",provider_requests=0,production_db_writes=0,real_owner_used=False,native_authority_positive=False))
    assert exception is None and result and result["actual_exit"]==0 and not result["timed_out"] and result["error"] is None
    job=result["job_cleanup"]
    assert not job["errors"] and job["active_processes_last_observed"]==0
    assert all(job[k] for k in ("unnamed_exclusive_job","kill_on_job_close_configured","assigned_before_resume","primary_exit_confirmed","job_idle_confirmed","handles_closed"))
    child_closed=json.loads((output/"validation.closed.json").read_text(encoding="utf-8"))
    assert child_closed["status"]=="PUBLIC_PIPE_TESTS_PASSED"
    cases=child_closed["results"]
    assert [c["case"] for c in cases]==["normal","maximum","reject","timeout","empty","oversize"]
    assert len(cases)==6 and all(c["passed"] for c in cases)
    assert all(p.read_bytes()==raw for p,raw in before.items())
    actual_refs=[pin(p) for p in sorted(output.iterdir()) if p.is_file()]
    closed_ref=save("validation.closed.json",dict(status="SIX_PUBLIC_PRIVATE_PIPE_CASES_PASSED_COMPONENT_ONLY",
        actual_invocation_ref=invocation_ref,child_result_ref=pin(output/"validation.closed.json"),actual_case_refs=actual_refs,
        source_review_refs=review_refs,runtime_inventory_ref=runtime_inventory_ref,frozen_source_ref=frozen_ref,
        passed_case_names=[c["case"] for c in cases],all_outer_and_inner_owned_jobs_closed=True,
        private_input_type="PUBLIC_DUMMY_BYTEARRAY",real_owner_used=False,native_authority_positive=False,
        provider_requests=0,production_db_writes=0,main_canonical_unchanged=True,Main_adopted=False,formal_acceptance=False))
    print(json.dumps(dict(status="SIX_PUBLIC_PRIVATE_PIPE_CASES_PASSED_COMPONENT_ONLY",closed_ref=closed_ref)),flush=True)
finally:
    for label,guard in (("runtime",runtime_guard),("source",initial)):
        if guard is not None:
            cleanup=guard.close()
            save(label+"-source-guard.cleanup.actual.json",cleanup)
            assert cleanup["closed"] and not cleanup["errors"] and cleanup["retained_handles_count"]==0
