import hashlib,json
from pathlib import Path
O=Path(__file__).resolve().parent
def pin(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def write(n,v):
 with (O/n).open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode())
rows=json.loads((O/"source-exit-integrity.json").read_bytes())["rows"]
for r in rows:assert pin(Path(r["source_ref"]["path"]))==r["source_ref"]
members=[pin(p) for p in sorted(O.iterdir()) if p.is_file() and p.name not in ("manifest.json","handoff.json")]
write("manifest.json",{"schema":"researchos.immutable-independent-review-manifest.v1","decision":"SOURCE_PASS_IN_SCOPE_WITH_OPEN","members":members,"member_count":len(members),"excluded":["manifest.json","handoff.json"],"input_refs":[r["source_ref"] for r in rows],"input_drift":0})
write("handoff.json",{"schema":"researchos.mu-sdk-observer-v2-independent-review-handoff.v1","state":"STOPPED_SOURCE_PASS_IN_SCOPE_WITH_OPEN","actor_id":"codex:/root/command_queue_impl","manifest_ref":pin(O/"manifest.json"),"review_ref":pin(O/"independent-review.json"),"report_ref":pin(O/"review.md"),"failure_origin_ref":pin(O/"failure-origin.read-report-name.json"),"source_sha256":"7077b2b70098f64f6b0a4aa5d993c59fb6cb3ffa4f08e66eb73cdb00cecc7dc0","independent_controls":39,"guard_mismatches":0,"input_count":len(rows),"input_drift":0,"new_tool_failures":1,"root_failure_sequence":682,"whole_chain_ready":False,"execution_ready":False,"formal_acceptance":False,"target_native_SQL_provider_calls":0,"canonical_Main_writes":0,"controller_v3_reviewed":False,"stop_source_writes":True})
assert all(pin(Path(r["path"]))==r for r in members)
print(json.dumps({"handoff_ref":pin(O/"handoff.json"),"manifest_ref":pin(O/"manifest.json"),"review_ref":pin(O/"independent-review.json"),"report_ref":pin(O/"review.md"),"failure_origin_ref":pin(O/"failure-origin.read-report-name.json"),"members":len(members),"status":"STOPPED"},ensure_ascii=False))

