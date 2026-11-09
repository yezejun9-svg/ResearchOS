"""Seal this independent SOURCE review only; no product or candidate execution."""
import hashlib,json
from pathlib import Path
ROOT=Path("D:/作品集/ResearchOS/research-os")
BASE=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/a04_formal_profile_independent_source_review_codex/d8dba4feee094e90b4a8f41c11d8648f")
def pin(p):
 raw=p.read_bytes()
 return {"path":str(p).replace("\\","/"),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def actual(ref):
 p=Path(ref["path"])
 if not p.is_absolute():p=ROOT/p
 got=pin(p)
 if got["sha256"]!=ref["sha256"] or got["bytes"]!=ref["bytes"]:raise ValueError("Immutable pin drift: "+ref["path"])
 return got
def put(name,doc):
 with (BASE/name).open("xb") as f:f.write((json.dumps(doc,ensure_ascii=False,indent=2)+"\n").encode("utf-8"))
 return pin(BASE/name)
review=json.loads((BASE/"review.json").read_bytes())
audit=json.loads((BASE/"audit.json").read_bytes())
for key in ("source_handoff_ref","source_manifest_ref","source_report_ref","source_inverse_ref"):actual(review[key])
for ref in review["selected_source_refs"].values():actual(ref)
actual(review["audit_ref"])
if review["decision"]!="REQUEST_CHANGES" or len(review["requested_changes"])!=3:raise ValueError("Review seal identity mismatch")
if audit["member_count"]!=11 or not audit["all_members_exact"]:raise ValueError("Incomplete source member audit")
if len(audit["selected_pure_counterexamples"])!=7 or not all(x["accepted"] for x in audit["selected_pure_counterexamples"]):raise ValueError("Counterexample facts differ")
names=("metadata_audit.py","audit.json","tool-observations.original.json","review.json","report.md","seal_review.py")
members=[pin(BASE/name) for name in names]
mf=put("manifest.json",{"schema":"researchos.a04-independent-source-review-manifest.v1","actor_id":"codex:/root/f08_whole_scope_review","status":"SEALED_SOURCE_ONLY","decision":"REQUEST_CHANGES","member_count":len(members),"members":members,"self_included":False,"handoff_external":True,"postseal_tool_observations_external":True})
hdf=put("handoff.json",{"schema":"researchos.a04-independent-source-review-handoff.v1","actor_id":"codex:/root/f08_whole_scope_review","status":"STOPPED","decision":"REQUEST_CHANGES","review_ref":pin(BASE/"review.json"),"report_ref":pin(BASE/"report.md"),"audit_ref":pin(BASE/"audit.json"),"manifest_ref":mf,"original_tool_observations_ref":pin(BASE/"tool-observations.original.json"),"source_handoff_ref":review["source_handoff_ref"],"source_manifest_ref":review["source_manifest_ref"],"requested_change_ids":[x["id"] for x in review["requested_changes"]],"source_candidate_entry_points_executed":False,"build_verified":False,"product_native_sdk_model_calls":0,"canonical_writes":0,"formal_case_accepted_delta":0,"new_tool_failure_origin_refs":[],"new_tool_failure_count":0,"prior_original_tool_io_unavailable":"Continuation-only earlier read/patch history explicitly unavailable; not reconstructed or counted again.","next_action":"Root may assign a new immutable Source revision; non-author review and actual Root finite LIVE gate remain required.","sealing_original_tool_io_annex":"Separate immutable postseal-tool-observations.original.json; outside this manifest to avoid a hash cycle."})
print(json.dumps({"review_ref":pin(BASE/"review.json"),"report_ref":pin(BASE/"report.md"),"audit_ref":pin(BASE/"audit.json"),"manifest_ref":mf,"handoff_ref":hdf,"new_tool_failures":0,"decision":"REQUEST_CHANGES"},ensure_ascii=False))

