import sys
sys.dont_write_bytecode=True
import hashlib,json,types,uuid
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");O=Path(__file__).resolve().parent
def pin(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def save(n,obj):
 p=O/n
 with p.open("xb") as f:f.write((json.dumps(obj,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(p)
BASE=R/"execution/v2.4/receipts/W05/W05-99"
guard_path=BASE/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py"
review_path=BASE/"source_read_guard_v2_independent_review_codex/9697417e746d47d9abea9289d56db2f1/review.json"
assert pin(guard_path)["sha256"]=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85"
assert pin(review_path)["sha256"]=="e93fe5a0e2e2d3b6c18732c7259d75a6d922ab7d31e48ee75e4c2b41f84c7831"
python=Path("C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe")
assert pin(python)["sha256"]=="cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b"
helper_path=BASE/"integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py"
raw=helper_path.read_bytes()
assert len(raw)==18901 and hashlib.sha256(raw).hexdigest()=="6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad"
helper=types.ModuleType("root_probe_owned_process");helper.__file__=str(helper_path)
exec(compile(raw,str(helper_path),"exec"),helper.__dict__)
temp=R/".local"/("source-guard-windows-probe-"+uuid.uuid4().hex)
temp.mkdir();(temp/"profile").mkdir();(temp/"temp").mkdir();(temp/"fixtures").mkdir()
frozen_paths=[R/"execution/v2.4"/(n+".json") for n in ("checkpoint","path_ownership","step_state","commands")]
frozen_paths+=[R/p for p in ("internal/host/vault.go","internal/host/host.go","apps/control/main.go","internal/domain/runtime_qualification.go","apps/cli/cli_stream.go")]
frozen={p:p.read_bytes() for p in frozen_paths}
env={"SystemRoot":"C:/Windows","WINDIR":"C:/Windows","PATH":str(python.parent)+";C:/Windows/System32",
 "USERPROFILE":str(temp/"profile"),"LOCALAPPDATA":str(temp/"profile"),"APPDATA":str(temp/"profile"),"TEMP":str(temp/"temp"),"TMP":str(temp/"temp")}
input_ref=save("probe.input.json",{"guard_ref":pin(guard_path),"review_ref":pin(review_path),"python_ref":pin(python),"fixture_directory":str(temp/"fixtures")})
argv=[str(python),"-I","-S","-X","utf8",str(O/"guard_windows_probe.py"),input_ref["path"]]
save("probe.intent.json",{"argv":argv,"cwd":str(R),"public_environment":env,"wall_seconds":30,
 "child_source_ref":pin(O/"guard_windows_probe.py"),"helper_ref":pin(helper_path),"guard_ref":pin(guard_path),"review_ref":pin(review_path),"frozen_main_and_canonical_refs":[pin(p) for p in frozen_paths],"provider_requests":0,"formal_acceptance":False})
stdout,stderr=O/"probe.stdout.raw",O/"probe.stderr.raw";result=None;error=None
try:
 with stdout.open("xb") as out,stderr.open("xb") as err:result=helper.run_owned(argv,str(R),env,out,err,30)
except BaseException as exc:error=repr(exc)
finally:
 unchanged={str(p):p.read_bytes()==b for p,b in frozen.items()}
 invocation=save("probe.invocation.json",{"result":result,"exception":error,"actual_native_exit":result["actual_exit"] if result else None,"stdout_ref":pin(stdout),"stderr_ref":pin(stderr),"frozen_inputs_unchanged":unchanged,"provider_requests":0,"formal_acceptance":False})
 print(json.dumps({"invocation_ref":invocation,"actual_native_exit":result["actual_exit"] if result else None}),flush=True)
assert result is not None and result["actual_exit"]==0 and result["error"] is None and not result["timed_out"] and error is None
cleanup=result["job_cleanup"]
assert cleanup["errors"]==[] and cleanup["active_processes_last_observed"]==0
assert all(cleanup[k] is True for k in ("unnamed_exclusive_job","kill_on_job_close_configured","assigned_before_resume","primary_exit_confirmed","job_idle_confirmed","handles_closed"))
proof=json.loads((O/"guard.windows.actual.json").read_bytes())
assert proof["actual_pid"]==result["owned_child_pid"] and all(e["pass"] for e in proof["events"])
assert all(unchanged.values())
closed=save("probe.closed.json",{"status":"ACTUAL_WINDOWS_COMPONENT_PROBE_PASS","invocation_ref":invocation,"proof_ref":pin(O/"guard.windows.actual.json"),"guard_cleanup_ref":pin(O/"guard.cleanup.actual.json"),"owned_job_cleanup_confirmed":True,"main_and_canonical_unchanged":True,"provider_requests":0,"target_host_executions":0,"runtime_qualification":False,"whole_controller_ready":False,"formal_acceptance":False})
print(json.dumps({"closed_ref":closed,"status":"ACTUAL_WINDOWS_COMPONENT_PROBE_PASS"}),flush=True)

