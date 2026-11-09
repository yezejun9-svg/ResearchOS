import sys,json,hashlib,types
from pathlib import Path
R=Path(r"D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99";O=Path(__file__).resolve().parent
D=B/"integration_codex/native-broker4-controller-config-root-1791513411000/controller-runtime"
GP=B/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py"
def pin(p):
 p=Path(p).resolve();raw=p.read_bytes();return dict(path=str(p),sha256="sha256:"+hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def verify(v):
 q=pin(v["path"]);assert(q["sha256"],q["bytes"])==(v["sha256"],v["bytes"]);return q
rr=pin(D/"sign-release.receipt.json");assert(rr["sha256"],rr["bytes"])==("sha256:684ce833422235ef1eeae19c601b9c192f53fcb2364c2f81d1c888a0ee1623e5",188460)
rec=json.loads(Path(rr["path"]).read_bytes());a=json.loads((O/"release.sign.approval.json").read_bytes())
assert rec["success"] is True and rec["phase"]==rec["sign_kind"]=="release" and rec["payload_ref"]==a["Payload"]
result=rec["result"];j=result["job_cleanup"];assert result["actual_exit"]==0 and result["error"] is None and not result["timed_out"]
assert all(j[k] for k in ("unnamed_exclusive_job","kill_on_job_close_configured","assigned_before_resume","primary_exit_confirmed","job_idle_confirmed","handles_closed")) and j["active_processes_last_observed"]==0 and not j["errors"]
assert rec["source_guard_cleanup"]["closed"] and not rec["source_guard_cleanup"]["errors"] and rec["source_guard_cleanup"]["retained_handles_count"]==0
sd=verify(rec["signed_ref"]);assert(sd["sha256"],sd["bytes"])==("sha256:2382bbca3fee118b79f2e35fa339d61df1587b58faf22f8c423be991c9e16b0a",182116)
signed=Path(sd["path"]).read_bytes();payload_ref=verify(a["Payload"]);payload=Path(payload_ref["path"]).read_bytes()
text=signed.decode("utf-8");prefix='{"payload":';assert text.startswith(prefix)
value,end=json.JSONDecoder().raw_decode(text,len(prefix));wrapper=json.loads(text)
assert text[len(prefix):end].encode("utf-8")==payload and set(wrapper)=={"payload","signature"} and isinstance(wrapper["signature"],str) and wrapper["signature"]
assert value==json.loads(payload) and sd["path"]==a["SignedDestination"] and rec["config_ref"]["sha256"]==a["ConfigSHA256"]
assert pin(GP)["sha256"]=="sha256:e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85"
gm=types.ModuleType("root_release_publish_guard");gm.__file__=str(GP);exec(compile(GP.read_bytes(),str(GP),"exec"),gm.__dict__)
refs=[rr,sd,payload_ref,verify(a["Snapshot"]),pin(O/"release.sign.approval.json"),pin(GP),pin(__file__)]
g=gm.SourceReadGuard();g.acquire([dict(path=v["path"],sha256=v["sha256"].removeprefix("sha256:"),bytes=v["bytes"]) for v in refs])
try:
 a["Action"]="PUBLISH_REVIEWED_SIGNED_DOCUMENT";a["SignedDocument"]=sd;a["SigningReceipt"]=rr
 p=O/"release.publish.approval.json"
 with p.open("xb") as f:f.write((json.dumps(a,ensure_ascii=True,indent=2)+"\n").encode())
 print(json.dumps(dict(approval_ref=pin(p),signed_payload_bytes_exact=True,signer_pid=result["owned_child_pid"],signer_creation_FILETIME_decimal=str(result["creation_time_100ns"]),signer_exit=0,signer_job_closed=True)),flush=True)
finally:
 cleanup=g.close()
 with (O/"release-publish-approval.guard-closure.json").open("xb") as f:f.write((json.dumps(cleanup,ensure_ascii=True,indent=2)+"\n").encode())
 assert cleanup["closed"] and not cleanup["errors"] and cleanup["retained_handles_count"]==0


