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
write("manifest.json",{"schema":"researchos.immutable-independent-review-manifest.v1","decision":"REQUEST_CHANGES","members":members,"member_count":len(members),"excluded":["manifest.json","handoff.json"],"input_refs":[r["source_ref"] for r in rows],"input_drift":0})
write("handoff.json",{"schema":"researchos.mu-sdk-controller-v3-independent-review-handoff.v1","state":"STOPPED_REQUEST_CHANGES","actor_id":"codex:/root/command_queue_impl","manifest_ref":pin(O/"manifest.json"),"review_ref":pin(O/"independent-source-review.json"),"report_ref":pin(O/"review.md"),"findings_ref":pin(O/"findings.json"),"controller_source_sha256":"273523f540f3ad1d3cb6adab1791d6887af2f8682f8fece9d840d6e0979c9c4f","observer_source_sha256":"7077b2b70098f64f6b0a4aa5d993c59fb6cb3ffa4f08e66eb73cdb00cecc7dc0","independent_new_cases":21,"prior_observer_39_reused":True,"distinct_findings":3,"input_count":len(rows),"input_drift":0,"new_tool_failures":0,"candidate_entry_WinAPI_SQL_provider_calls":0,"canonical_Main_writes":0,"formal_acceptance":False,"execution_ready":False,"python_binary_selection":"NOT_PROVIDED_BY_CURRENT_PHASE_SEED","stop_source_writes":True})
assert all(pin(Path(r["path"]))==r for r in members)
print(json.dumps({"handoff_ref":pin(O/"handoff.json"),"manifest_ref":pin(O/"manifest.json"),"review_ref":pin(O/"independent-source-review.json"),"report_ref":pin(O/"review.md"),"members":len(members),"status":"STOPPED"},ensure_ascii=False))

