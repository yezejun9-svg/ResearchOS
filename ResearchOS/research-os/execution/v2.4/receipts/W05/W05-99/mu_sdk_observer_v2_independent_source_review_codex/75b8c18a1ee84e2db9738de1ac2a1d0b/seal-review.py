import hashlib,json
from pathlib import Path
O=Path(__file__).resolve().parent
def pin(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def write(n,v):
 with (O/n).open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode())
intake=json.loads((O/"intake.json").read_bytes());rows=intake["rows"]
for r in rows:
 assert pin(Path(r["source_ref"]["path"]))==r["source_ref"]
 assert pin(Path(r["snapshot_ref"]["path"]))==r["snapshot_ref"]
source=next(r["source_ref"] for r in rows if Path(r["source_ref"]["path"]).name=="mu_sdk_job_observer.v2.proposed.py")
old=next(r["source_ref"] for r in rows if Path(r["source_ref"]["path"]).name=="mu_sdk_job_observer.proposed.py")
controls=json.loads((O/"independent-controls.json").read_bytes());assert len(controls["cases"])==39 and all(r["matches_expected"] for r in controls["cases"])
review={"schema":"researchos.mu-sdk-observer-partial-independent-source-review.v2","decision":"SOURCE_PASS_IN_SCOPE_WITH_OPEN","actor_id":"codex:/root/command_queue_impl","source_ref":source,"previous_source_ref":old,"scope":["CTRL-R06 observer argv/cwd/Python/worker binding","CTRL-R04 observer closed environment"],"report_ref":pin(O/"review.md"),"controls_ref":pin(O/"independent-controls.json"),"forward_inverse_byte_exact":True,"changed_functions":intake["changed_functions"],"new_functions":intake["new_functions"],"independent_cases":39,"guard_mismatches":0,"actual_native_observation":False,"whole_chain_ready":False,"formal_acceptance":False,"execution_ready":False,"execution_grant_issued":False,"input_count":len(rows),"input_drift":0,"target_native_SQL_provider_calls":0,"full_candidate_imports":0,"canonical_Main_writes":0,"new_tool_failures":1,"failure_origin_ref":pin(O/"failure-origin.read-report-name.json"),"root_failure_sequence":682,"open":["CTRL-R02 canonical OS transaction","CTRL-R05 independent watchdog","controller new context/source pins integration","execution-load immutability","actual callback/OS probe","qualification Host full lifecycle"],"later_controller_v3_reviewed":False}
write("independent-review.json",review)
write("source-exit-integrity.json",{"rows":rows,"input_count":len(rows),"drift_count":0})
print(json.dumps({"decision":review["decision"],"review_ref":pin(O/"independent-review.json"),"report_ref":pin(O/"review.md"),"failure_origin_ref":pin(O/"failure-origin.read-report-name.json"),"inputs":len(rows),"drift":0,"controls":39,"new_tool_failures":1},ensure_ascii=False))

