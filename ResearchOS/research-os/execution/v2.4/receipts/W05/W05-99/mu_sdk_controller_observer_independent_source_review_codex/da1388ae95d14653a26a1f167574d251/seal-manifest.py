import hashlib,json
from pathlib import Path
O=Path(__file__).resolve().parent
def pin(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def write(n,v):
 with (O/n).open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode())
check=json.loads((O/"source-exit-integrity.json").read_bytes())
for row in check["entries"]:assert pin(Path(row["source_ref"]["path"]))==row["source_ref"]
members=[pin(p) for p in sorted(O.iterdir()) if p.is_file() and p.name not in ("manifest.json","handoff.json")]
write("manifest.json",{"schema":"researchos.immutable-independent-review-manifest.v1","decision":"REQUEST_CHANGES","members":members,"member_count":len(members),"explicit_exclusions":["manifest.json","handoff.json"],"input_refs":[r["source_ref"] for r in check["entries"]],"source_exit_drift":0})
write("handoff.json",{"schema":"researchos.independent-source-review-handoff.v1","actor_id":"codex:/root/command_queue_impl","state":"STOPPED_REQUEST_CHANGES","namespace":str(O),"decision":"REQUEST_CHANGES","manifest_ref":pin(O/"manifest.json"),"independent_source_review_ref":pin(O/"independent-source-review.json"),"report_ref":pin(O/"review.md"),"findings_ref":pin(O/"findings.json"),"controller_source_sha256":"ddcf54587a9cb32cff4470ebf2fa2d34a57ef061dc64e27c71b5f7b610a39ae8","observer_source_sha256":"b062be8b68d1b31b658ba79a20c890ce895009fc135c80ae8d33ed5b78d01fd0","new_tool_failures":0,"native_product_sql_provider_calls":0,"candidate_module_imports":0,"canonical_Main_writes":0,"input_count":28,"input_drift":0,"independent_case_count":31,"source_findings":6,"execution_grant_issued":False,"formal_acceptance":False,"source_ready":False,"stop_source_writes":True})
assert all(pin(Path(ref["path"]))==ref for ref in members)
print(json.dumps({"handoff_ref":pin(O/"handoff.json"),"manifest_ref":pin(O/"manifest.json"),"review_ref":pin(O/"independent-source-review.json"),"report_ref":pin(O/"review.md"),"member_count":len(members),"source_exit_drift":0,"decision":"REQUEST_CHANGES","status":"STOPPED"},ensure_ascii=False))

