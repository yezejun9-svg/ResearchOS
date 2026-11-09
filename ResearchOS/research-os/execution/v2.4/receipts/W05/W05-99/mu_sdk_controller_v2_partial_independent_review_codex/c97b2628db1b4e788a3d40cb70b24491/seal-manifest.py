import hashlib,json
from pathlib import Path
O=Path(__file__).resolve().parent
def pin(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def write(n,v):
 with (O/n).open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode())
rows=json.loads((O/"source-exit-integrity.json").read_bytes())["rows"]
for row in rows:assert pin(Path(row["source_ref"]["path"]))==row["source_ref"]
members=[pin(p) for p in sorted(O.iterdir()) if p.is_file() and p.name not in ("manifest.json","handoff.json")]
write("manifest.json",{"schema":"researchos.immutable-independent-review-manifest.v1","decision":"REQUEST_CHANGES_WITH_PARTIAL_FIXES","members":members,"member_count":len(members),"explicit_exclusions":["manifest.json","handoff.json"],"input_refs":[r["source_ref"] for r in rows],"input_drift":0})
write("handoff.json",{"schema":"researchos.controller-v2-partial-review-handoff.v1","state":"STOPPED_REQUEST_CHANGES_WITH_PARTIAL_FIXES","actor_id":"codex:/root/command_queue_impl","manifest_ref":pin(O/"manifest.json"),"review_ref":pin(O/"independent-review.json"),"report_ref":pin(O/"review.md"),"controller_sha256":"9dfad55126c68bc02a3a16c45b0d487c3af363182d45914fb409850c63309487","results":{"R01":"SOURCE_PASS_IN_SCOPE","R03":"SOURCE_PASS_IN_SCOPE","R04":"PARTIAL_FIX_COMSPEC_PATHEXT_STILL_UNBOUND"},"inputs":len(rows),"input_drift":0,"independent_controls":19,"new_tool_failures":0,"target_native_SQL_provider_calls":0,"canonical_Main_writes":0,"formal_acceptance":False,"execution_ready":False,"whole_source_review_repeated":False,"stop_source_writes":True})
assert all(pin(Path(r["path"]))==r for r in members)
print(json.dumps({"handoff_ref":pin(O/"handoff.json"),"manifest_ref":pin(O/"manifest.json"),"review_ref":pin(O/"independent-review.json"),"report_ref":pin(O/"review.md"),"members":len(members),"input_drift":0,"new_tool_failures":0,"status":"STOPPED"},ensure_ascii=False))

