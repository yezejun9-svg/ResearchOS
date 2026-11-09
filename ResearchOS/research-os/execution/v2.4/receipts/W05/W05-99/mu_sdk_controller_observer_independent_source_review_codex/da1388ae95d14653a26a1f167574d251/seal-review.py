import hashlib,json
from pathlib import Path
O=Path(__file__).resolve().parent
rows=json.loads((O/"intake.json").read_bytes())["rows"]+json.loads((O/"observer-intake.json").read_bytes())["rows"]
def pin(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def write(n,v):
 with (O/n).open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode())
def named(n):return next(r["source_ref"] for r in rows if Path(r["source_ref"]["path"]).name==n)
for r in rows:
 assert pin(Path(r["source_ref"]["path"]))==r["source_ref"]
 assert pin(Path(r["snapshot_ref"]["path"]))==r["snapshot_ref"]
review={"schema":"researchos.mu-sdk-controller-observer-independent-source-review.v1","decision":"REQUEST_CHANGES","actor_id":"codex:/root/command_queue_impl","controller_source_ref":named("controller.py"),"observer_source_ref":named("mu_sdk_job_observer.proposed.py"),"hooks_source_ref":named("owned_job_hooks.py"),"runner_source_ref":named("mu_sdk_trial.v8.proposed.py"),"additional_execution_dependencies":[named("phase_worker.py"),named("job_probe_worker.py"),named("windows_owned_process.py")],"callback_contract":"REAL_ASSIGNED_SUSPENDED_FRAME_BEFORE_FIRST_RESUME","formal_acceptance":False,"execution_grant_issued":False,"findings_ref":pin(O/"findings.json"),"report_ref":pin(O/"review.md"),"independent_controls_refs":[pin(O/"controls.json"),pin(O/"observer-controls.json")],"source_read_entries":len(rows),"source_exit_drift":0,"positive_scope":"Source ordering, pin inventory and independent in-memory guard counterexamples only; no live lifecycle approval","open":["six_source_findings","actual_callback_OS_probe","trusted_qualification_host_dispatch","full_trial_process_tree_cleanup","current_live_authority"],"native_calls":0,"candidate_module_imports":0,"product_SQL_or_provider_calls":0,"canonical_or_Main_writes":0,"new_tool_failures":0}
write("independent-source-review.json",review)
write("source-exit-integrity.json",{"entries":rows,"input_count":len(rows),"drift_count":0,"review_ref":pin(O/"independent-source-review.json")})
print(json.dumps({"decision":"REQUEST_CHANGES","review_ref":pin(O/"independent-source-review.json"),"report_ref":pin(O/"review.md"),"findings_ref":pin(O/"findings.json"),"inputs":len(rows),"drift":0,"controls":31,"source_findings":6,"new_tool_failures":0},ensure_ascii=False))

