import hashlib,json,pathlib,difflib
OUT=pathlib.Path(__file__).resolve().parent
B=pathlib.Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99")
A=B/"integration_codex/trusted-host-v5-lossless-build-root-17f16d9253094e14bedfb51b"
S=B/"mu_sdk_trusted_qualification_host_source_v5_codex/17e94063a8244fdfa69aefdbdf895cf6"
def read(p):return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
def ref(p):
 p=pathlib.Path(p);raw=p.read_bytes();return dict(path=p.as_posix(),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
verified={}
def verify(v):
 p=pathlib.Path(v["path"]);r=ref(p);assert r["sha256"]==v["sha256"] and r["bytes"]==v["bytes"],str(p);verified[r["path"]]=r
 return p
closedref=dict(path=str(A/"reader-validation.closed.json"),sha256="077ffe84064e0227d8df22b63b1a93456090c202abe06921545c6f41274888ae",bytes=4599)
closed=read(verify(closedref))
assert closed["status"]=="ACTUAL_GO_READER_TESTS_AND_COMPILE_PASSED_SOURCE_ONLY"
for k in ("formal_acceptance","runtime_qualification"):assert closed[k] is False
for k in ("target_host_executions","provider_requests"):assert closed[k]==0
verify(closed["binary_ref"])
members=read(verify(closed["source_members_ref"]))
assert len(members)==9
for v in members:verify(v)
source=pathlib.Path(closed["source_namespace"])
formatted=pathlib.Path(closed["formatted_namespace"])
mf=read(S/"MF.json")
for name,v in mf["members"].items():verify(dict(path=str(source/name),**{k:v[k] for k in ("sha256","bytes")}))
assert (formatted/"execute.go").read_text(encoding="utf-8")==(source/"execute.go").read_text(encoding="utf-8").replace("}\n// readPinnedOwnedJobObject","}\n\n// readPinnedOwnedJobObject",1)
for name in mf["members"]:
 if name!="execute.go":assert (formatted/name).read_bytes()==(source/name).read_bytes()
test_source=A/"go-source/reader_contract_test.go"
test_fmt=formatted/test_source.name
test_diff="".join(difflib.unified_diff(test_source.read_text(encoding="utf-8").splitlines(True),test_fmt.read_text(encoding="utf-8").splitlines(True),fromfile="original test",tofile="gofmt test"))
jobs=[]
for r in closed["invocation_refs"]:
 p=verify(r);v=read(p);result=v["result"];clean=result["job_cleanup"]
 assert v["actual_native_exit"]==0 and result["actual_exit"]==0 and result["timed_out"] is False and result["error"] is None and v["exception"] is None
 assert result["resumed"] is True and type(result["owned_child_pid"]) is int and result["owned_child_pid"]>0 and type(result["creation_time_100ns"]) is int and result["creation_time_100ns"]>0
 assert clean["errors"]==[] and clean["active_processes_last_observed"]==0
 for k in ("unnamed_exclusive_job","kill_on_job_close_configured","assigned_before_resume","primary_exit_confirmed","job_idle_confirmed","handles_closed"):assert clean[k] is True
 assert v["target_host_executions"]==0 and v["provider_requests"]==0
 for k in ("stdout_ref","stderr_ref"):verify(v[k])
 assert pathlib.Path(v["cwd"])==B.parents[4]
 labels=p.name.split(".")[0]
 args=v["argv"]
 gofiles=[str(formatted/n) for n in ("main.go","hostapi.go","prepare.go","execute.go","prepare_runtime.go")]
 # Compare only path components with Windows path semantics.
 if labels=="reader-test":assert args[1:4]==["test","-count=1","-json"] and [pathlib.Path(x) for x in args[4:]]==[pathlib.Path(x) for x in gofiles+[str(test_fmt)]]
 elif labels=="compile":assert args[1:4]==["build","-trimpath","-o"] and pathlib.Path(args[4])==pathlib.Path(closed["binary_ref"]["path"]) and [pathlib.Path(x) for x in args[5:]]==[pathlib.Path(x) for x in gofiles]
 elif labels=="format":assert args[1]=="-w" and [pathlib.Path(x) for x in args[2:]]==[pathlib.Path(x) for x in gofiles+[str(test_fmt)]]
 else:raise AssertionError(labels)
 jobs.append(dict(label=labels,pid=result["owned_child_pid"],creation_time_100ns=result["creation_time_100ns"],actual_exit=0,closed=True))
events=[json.loads(l) for l in (A/"reader-test.stdout.raw").read_text(encoding="utf-8").splitlines() if l]
assert not any(e["Action"] in ("fail","skip") for e in events)
passes=sorted(e["Test"] for e in events if e["Action"]=="pass" and "Test" in e)
assert len(passes)==27 and passes==closed["go_test_pass_names"]
assert any(e["Action"]=="pass" and "Test" not in e for e in events)
guards=[]
for name,count in (("input-source-guard.cleanup.actual.json",36),("formatted-source-guard.cleanup.actual.json",10)):
 g=read(A/name);assert g["verification"]=="PASSED" and g["closed"] is True and g["retained_handles_count"]==0 and not g["errors"] and not g["failure"] and len(g["entries"])==count
 for e in g["entries"]:
  assert all(e[k] is True for k in ("verified","final_path_match","closed"));verify(e)
 guards.append(dict(name=name,count=count,closed=True))
for name in ("HDF.json","MF.json","source-diff.patch","static-test-evidence.json"):verified[ref(S/name)["path"]]=ref(S/name)
for name in ("reader-validation.closed.json","input-source-guard.cleanup.actual.json","formatted-source-guard.cleanup.actual.json"):verified[ref(A/name)["path"]]=ref(A/name)
result=dict(status="PASS_READONLY_ACTUAL_GO_COMPONENT_INTAKE",verified_refs=list(verified.values()),owned_jobs=jobs,test_node_pass_count=27,leaf_case_count=25,guard_summaries=guards,formatted_execute_change="one blank line only",test_format_diff=test_diff,reviewer_native_executions=0,reviewer_provider_requests=0,reviewer_sql_operations=0)
(OUT/"actual-component-intake.json").write_text(json.dumps(result,indent=2,ensure_ascii=True)+"\n",encoding="utf-8")
print(json.dumps(dict(status=result["status"],verified_ref_count=len(verified),owned_jobs=jobs,test_node_pass_count=27,guards=guards,output_ref=ref(OUT/"actual-component-intake.json")),ensure_ascii=True))

