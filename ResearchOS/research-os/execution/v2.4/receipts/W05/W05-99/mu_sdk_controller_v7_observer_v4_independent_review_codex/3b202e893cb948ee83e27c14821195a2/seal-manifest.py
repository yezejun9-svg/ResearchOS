import hashlib,json
from pathlib import Path
O=Path(__file__).resolve().parent
def ref(p):
 p=Path(p);b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def put(n,d):
 p=O/n
 with p.open("xb") as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+"\n").encode())
 return ref(p)
a=json.loads((O/"intake.json").read_bytes())
for row in a["rows"]:assert ref(row["source_ref"]["path"])==row["source_ref"],row["source_ref"]["path"]
manifest=put("manifest.json",{"schema":"researchos.c7-o4-independent-review-manifest.v1",
 "actor":"codex:/root/command_queue_impl","decision":"READY_SOURCE_ONLY",
 "scope":"All files in this independent review directory except manifest.json and subsequent handoff.json",
 "members":[ref(p) for p in sorted(O.rglob("*")) if p.is_file()],
 "input_records":38,"input_drift":0,"new_tool_failures":0,"candidate_native_SQL_provider_calls":0,"Main_canonical_writes":0,"formal_acceptance":False})
handoff=put("handoff.json",{"schema":"researchos.c7-o4-independent-review-handoff.v1",
 "actor":"codex:/root/command_queue_impl","decision":"READY_SOURCE_ONLY","review_ref":ref(O/"independent-source-review.json"),
 "manifest_ref":manifest,"findings_ref":ref(O/"findings.json"),"report_ref":ref(O/"review.md"),
 "controls_ref":ref(O/"independent-delta-controls.json"),"original_tool_io_ref":ref(O/"original-tool-io.json"),
 "original_review_seal_io_ref":ref(O/"original-review-seal-io.json"),
 "closed_findings":["C6-O4-R01"],"control_counts":{"new_delta":5,"passed":5,"counterexamples":0},
 "prior_C6_O4_controls_reused_not_rerun":67,"input_records":38,"input_drift":0,"new_tool_failures":0,
 "execution_grant_issued":False,"runtime_qualification":False,"formal_acceptance":False,
 "candidate_entry_or_WinAPI_SQL_provider_calls":0,"real_threads_started":0,"Main_canonical_writes":0,
 "open":["ROOT_PARENT_RESIDENCY","ACTUAL_HELD_JOB_CLEANUP_LIFECYCLE","ROOT_HOST_SIBLING_JOB_STDIN_COMMON_DEADLINE","ACTUAL_QUALIFICATION_AND_TRIAL"],"stopped":True})
print(json.dumps({"handoff_ref":handoff,"manifest_ref":manifest,"review_ref":ref(O/"independent-source-review.json")},ensure_ascii=False,indent=2))

