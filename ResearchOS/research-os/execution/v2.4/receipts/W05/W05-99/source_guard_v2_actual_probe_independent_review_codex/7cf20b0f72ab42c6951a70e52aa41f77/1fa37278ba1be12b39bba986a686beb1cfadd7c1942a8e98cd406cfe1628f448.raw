import sys
sys.dont_write_bytecode=True
import hashlib,json
from pathlib import Path
O=Path(__file__).resolve().parent
R=Path("D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99"
P=B/"sdk_five_go_root_adoption_preparation_codex/04a454a98b164aa2983f16245f273e9d"
def pin(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def save(n,obj):
 p=O/n
 with p.open("xb") as f:f.write((json.dumps(obj,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(p)
closed=O/"probe.closed.json";invocation=O/"probe.invocation.json";proof=O/"guard.windows.actual.json"
assert pin(closed)["sha256"]=="b473f1c5b3950dba2142b23a59ffd933746fffd2e0d9d33124cf20e796bb18f7"
assert pin(invocation)["sha256"]=="1a728c51a8459140f9ef7fc761828a408a6fc47656ae31f095a81803f3a6a221"
c=json.loads(closed.read_bytes());i=json.loads(invocation.read_bytes());p=json.loads(proof.read_bytes())
assert i["actual_native_exit"]==0 and p["actual_pid"]==i["result"]["owned_child_pid"]
manifest=save("manifest.json",{"schema":"researchos.root-windows-source-guard-component-probe-manifest.v1","actor":"codex:/root",
 "members":[pin(f) for f in sorted(O.iterdir()) if f.is_file()],"excludes":["manifest.json","handoff.json"]})
hdf=save("handoff.json",{"schema":"researchos.root-windows-source-guard-component-probe-handoff.v1","actor":"codex:/root",
 "decision":"ACTUAL_PRIVATE_WINDOWS_COMPONENT_PROBE_EXECUTED_PENDING_NONAUTHOR_REVIEW",
 "manifest_ref":manifest,"closed_ref":pin(closed),"invocation_ref":pin(invocation),"proof_ref":pin(proof),
 "guard_cleanup_ref":pin(O/"guard.cleanup.actual.json"),"raw_control_journal_ref":pin(O/"control-events.actual.jsonl"),
 "original_root_tool_io_ref":pin(O/"root-execution.original-tool-io.json"),
 "failed_probe_696_ref":pin(P/"failure-origin.696.original-tool-io.json"),
 "failed_probe_698_ref":pin(P/"failure-origin.698.original-tool-io.json"),
 "guard_source_independent_review_ref":p["review_ref"],"guard_source_ref":p["source_ref"],
 "checks":["actual PID bound to owned helper child PID","anyJob evidence used only with real suspended assignment/owned Job cleanup","read permitted while three handles held","raw CreateFileW write and DeleteFileW rejected with actual32","same-path MoveFileEx succeeds before/after guard but rejected with actual5 while held","all protected source bytes unchanged while held","three verified handles closed retained0 errors0","all owned Job cleanup assertions confirmed","Main5 and canonical4 unchanged"],
 "actual_any_job_member_does_not_alone_prove_exact_parent_job":True,
 "source_guard_temporary_target_component_only":True,"whole_controller_ready":False,"runtime_qualification":False,
 "formal_acceptance":False,"provider_requests":0,"target_host_executions":0,
 "open":["Non-author review of these exact actual records","C4 unconfirmed-cleanup guard lifecycle finding; C5 proposed fix","Actual separate trusted Host whole-trial lifecycle and root SDK qualification scope"]})
print(json.dumps({"handoff_ref":hdf,"manifest_ref":manifest,"original_io_ref":pin(O/"root-execution.original-tool-io.json"),"decision":"ACTUAL_PRIVATE_WINDOWS_COMPONENT_ONLY"}),flush=True)

