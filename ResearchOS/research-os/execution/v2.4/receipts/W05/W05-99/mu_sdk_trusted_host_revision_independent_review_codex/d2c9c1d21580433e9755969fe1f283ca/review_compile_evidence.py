from pathlib import Path
import hashlib,json
O=Path(__file__).resolve().parent
B=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/trusted-host-v2-build-147c7ec3b9a7494db8518cce368e7529")
def m(p):
 raw=p.read_bytes();return dict(path=p.as_posix(),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
refs=[]
def cap(p,pin=None,copy=True):
 x=m(p)
 if pin:assert (x["sha256"],x["bytes"])==(pin["sha256"],pin["bytes"]),p
 if copy:
  d=O/"build-evidence"/p.name;d.parent.mkdir(exist_ok=True);d.write_bytes(p.read_bytes());x["snapshot"]=d.relative_to(O).as_posix()
 refs.append(x);return x
closed=json.loads((B/"compile.closed.json").read_bytes())
inv=json.loads((B/"compile.invocation.json").read_bytes())
cap(B/"compile.closed.json",dict(sha256="8cd37b7db0ef092ee17baf8bf2ef7c559b16365c3c07e17e4d97319ba4c68b8f",bytes=1175))
cap(B/"compile.invocation.json",dict(sha256="20c4835daee4b3b5c8b630ff76585a7cbae9bcd4d14835ddb79180ba14c32d52",bytes=4548))
for ref in [closed["before_ref"],inv["stdout_ref"],inv["stderr_ref"]]:cap(Path(ref["path"]),ref)
for name in ["compile.intent.json","build_trusted_host_v2.actual_owned.py"]:cap(B/name)
cap(Path(closed["binary_ref"]["path"]),closed["binary_ref"],False)
assert inv["actual_native_exit"]==0 and inv["result"]["actual_exit"]==0 and not inv["result"]["timed_out"] and inv["exception"] is None
jc=inv["result"]["job_cleanup"]
assert all(jc[k] is True for k in ["unnamed_exclusive_job","kill_on_job_close_configured","assigned_before_resume","job_idle_confirmed","primary_exit_confirmed","handles_closed"])
assert jc["active_processes_last_observed"]==0 and jc["errors"]==[]
assert len(inv["argv"])==9 and inv["argv"][1:4]==["build","-trimpath","-o"]
assert [Path(x).name for x in inv["argv"][-4:]]==["main.go","hostapi.go","prepare.go","execute.go"]
assert all(inv["frozen_inputs_unchanged"].values())
assert inv["target_host_executions"]==inv["provider_requests"]==0
out=dict(status="ROOT_COMPILE_EVIDENCE_VERIFIED_SOURCE_ONLY",files=refs,reported_native_exit=0,recorded_job_cleanup_verified=True,reviewer_compile_runs=0,target_host_executions=0,provider_requests=0,scope="Read and hash Root compiler records, verify stated argv/exit/cleanup fields and current binary identity; did not independently observe the past OS execution or execute binary.")
(O/"compile-evidence-review.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(dict(status=out["status"],refs=len(refs),binary_bytes=closed["binary_ref"]["bytes"])))

