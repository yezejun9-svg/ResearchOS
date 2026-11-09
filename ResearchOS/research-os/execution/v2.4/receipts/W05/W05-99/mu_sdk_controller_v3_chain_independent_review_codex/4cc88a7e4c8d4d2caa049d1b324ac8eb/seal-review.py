import ast,hashlib,json
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
def source(n,contains=None):
 return next(r["source_ref"] for r in rows if Path(r["source_ref"]["path"]).name==n and (contains is None or contains in r["source_ref"]["path"]))
ctrl=source("controller.py","revision_v3");obs=source("mu_sdk_job_observer.v2.proposed.py")
review={"schema":"researchos.mu-sdk-controller-observer-independent-source-review.v2","decision":"REQUEST_CHANGES","actor_id":"codex:/root/command_queue_impl","controller_source_ref":ctrl,"observer_source_ref":obs,"hooks_source_ref":source("owned_job_hooks.py"),"runner_source_ref":source("mu_sdk_trial.v8.proposed.py"),"phase_worker_source_ref":source("phase_worker.py"),"python_binary_ref":None,"python_selection_status":"No current Root phase seed selected binary supplied for this whole-chain review; no inferred execution authority","callback_contract":"REAL_ASSIGNED_SUSPENDED_FRAME_BEFORE_FIRST_RESUME","formal_acceptance":False,"execution_ready":False,"additional_dependencies":[source("canonical_transactions.py"),source("job_deadline_watchdog.py"),source("windows_owned_process.py")],"prior_observer_review_ref":source("independent-review.json","observer_v2_independent"),"prior_observer_39_controls_reused_not_rerun":True,"findings_ref":pin(O/"findings.json"),"report_ref":pin(O/"review.md"),"controls_refs":[pin(O/n) for n in ("watchdog-controls.json","canonical-controls.json","integration-controls.json")],"new_independent_cases":21,"guard_or_cleanup_counterexamples":3,"distinct_findings":3,"static_execution_load_gap":True,"old_issue_status":{"CTRL-R01":"SOURCE_GUARD_PRESERVED","CTRL-R02":"EXCLUSIVE_LOCK_GAP_FIXED_PARTIAL_CLOSE_ADMISSION_OPEN","CTRL-R03":"SINGLE_VERIFIED_BUFFER_PRESERVED","CTRL-R04":"CLOSED_EIGHT_KEY_ENVIRONMENT_FIXED","CTRL-R05":"DEADLINE_TIMER_ADDED_THREAD_START_CLEANUP_OPEN","CTRL-R06":"ARGV_CWD_REFS_FIXED_EXECUTION_LOAD_IMMUTABILITY_OPEN"},"input_count":len(rows),"input_drift":0,"new_tool_failures":0,"candidate_entry_or_WinAPI_SQL_provider_calls":0,"real_threads_started":0,"canonical_Main_writes":0,"open":["three_source_findings","actual_OS_sharing_watchdog_callback_probes","Host_and_qualification_full_lifecycle","current_phase_seed_runtime_choice"],"later_sdk_v9_reviewed":False}
write("independent-source-review.json",review)
write("source-exit-integrity.json",{"rows":rows,"input_count":len(rows),"input_drift":0})
print(json.dumps({"decision":"REQUEST_CHANGES","review_ref":pin(O/"independent-source-review.json"),"report_ref":pin(O/"review.md"),"findings_ref":pin(O/"findings.json"),"inputs":len(rows),"input_drift":0,"new_tool_failures":0},ensure_ascii=False))

