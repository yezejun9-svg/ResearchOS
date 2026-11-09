import sys
sys.dont_write_bytecode=True
import hashlib,json,os,uuid
from pathlib import Path
from datetime import datetime,timezone
R=Path("D:/作品集/ResearchOS/research-os");P=Path(__file__).resolve().parent;O=P/"checkpoint-r342-controller-open";O.mkdir(exist_ok=False)
def pin(p):
 p=Path(p);b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def save(n,v):
 p=O/n
 with p.open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(p)
cp=R/"execution/v2.4/checkpoint.json";old=cp.read_bytes();assert hashlib.sha256(old).hexdigest()=="7f63366f8bbe9cd5cf4cee781e8a81b5fd9cc69e20b865cac47db0fff5babd0a"
c=json.loads(old);assert c["revision"]==341 and len(c["failure_counters"])==679 and c["head"]=="adc460c2138528f163f7fdab5e8d81dde157b7fb"
other=[R/"execution/v2.4"/(x+".json") for x in ("path_ownership","step_state","commands")];raw_other=[x.read_bytes() for x in other]
pending=[(680,P/"failure-origin.680.readonly-coordinator-path.json"),(681,R/"execution/v2.4/receipts/W05/W05-99/mu_sdk_controller_source_codex/2e716ffb2df44199b7d3d28cdbdddbed/failure-origin.681.patch-hunk-order.json")]
refs=[{"ordinal":n,"evidence_ref":pin(p),"full_original_tool_io_embedded":False,"original_io_location":"Current Codex conversation original tool input/result; root owned origin document explicitly discloses embedding gap."} for n,p in pending]
known={x.get("origin_key") for x in c["failure_counters"]}
for x in refs:
 assert x["evidence_ref"]["sha256"] not in known
 c["failure_counters"].append({"origin_key":x["evidence_ref"]["sha256"],"evidence_ref":x["evidence_ref"],"original_payload":{"observed_ordinal":x["ordinal"],"immutable_origin_ref":x["evidence_ref"],"full_original_tool_io_embedded":False},"counter_reset":False,"counted_once":True,"automatic_retry":False})
(O/"checkpoint.before.json").write_bytes(old)
c["expected_previous_revision"]=341;c["revision"]=342;c["updated_at"]=datetime.now(timezone.utc).isoformat();c["updated_by"]="codex:/root"
w=c["work_in_progress"];w.update({"mu_sdk_live_trial_state":"SOURCE_PREPARATION_CONTROLLER_REQUEST_CHANGES_AND_HOST_TOOL_IMPLEMENTATION",
"mu_sdk_runner_v8_handoff_ref":pin(R/"execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v8_source_codex/8251b1ed21754f7cbd6c2f8e7ff574eb/handoff.json"),
"mu_sdk_runner_v8_independent_review_ref":pin(R/"execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v8_independent_source_review_codex/430f8fc4d15847d48d6d185f51f839a7/review.json"),
"mu_sdk_controller_v1_source_handoff_ref":pin(R/"execution/v2.4/receipts/W05/W05-99/mu_sdk_controller_source_codex/2e716ffb2df44199b7d3d28cdbdddbed/handoff.json"),
"mu_sdk_observer_v1_source_handoff_ref":pin(R/"execution/v2.4/receipts/W05/W05-99/mu_sdk_job_observer_source_codex/8cf71287160941f3b841945dc02be134/handoff.json"),
"mu_sdk_controller_review_state":"INDEPENDENT_REQUEST_CHANGES_PROVISIONAL_SIX_FINDINGS_NO_EXECUTION",
"mu_sdk_controller_open":["Unconfirmed cleanup must retain active lease","Mandatory serialized canonical transaction under OS ownership; partial writes must retain intent","Pin consumers must use exact one verified read","Closed public environment and no pre-review secret intent writes","Absolute Job watchdog while synchronous callback runs","Observer must bind actual argv/cwd/Python/phase-worker source and approved full source tuple","Actual Host qualification admission/dispatch/ordinary Serve lifecycle coverage"],
"mu_sdk_source_authors_active":["codex:/root/live_resource_lookup: trusted Go qualification Host proposed Source"],
"mu_sdk_source_readonly_reviewers_active":["codex:/root/command_queue_impl: controller/observer review"],
"mu_sdk_active_run_uuid":None,"mu_sdk_live_execution_grant_issued":False,"mu_sdk_runtime_qualification":False,
"mu_sdk_actual_external_provider_requests_current_trial":0,
"r342_registered_failure_count":681,"r342_observed_failure_count":681,
"r342_pending_original_tool_io_embedding_refs":refs,
"mu_sdk_next_action":"Finish independent controller/observer REQUEST_CHANGES receipt; create immutable corrected controller+observer revisions, complete proposed trusted Host Source and Root locked-tool compile, then actual no-provider PID/Job probe before any LIVE model grant."})
c["note"]="Main five-Go commit adc460c2 remains unchanged with22 independently reviewed local top-level PASS. SDKv8 Source commit/cancel binding reviewed only. True independent controller review found six gaps; its v1 and observer preserved unexecuted, no model grant or live requests. Trusted Go Host entry Source being implemented. Root two late actual tool failures680-681 appended once; complete original tool IO still in conversation and embedding gap explicitly retained. W05-99 and0/42 current formal remain; old13dirty preserved."
new=(json.dumps(c,ensure_ascii=False,indent=2)+"\n").encode();(O/"checkpoint.after.proposed.json").write_bytes(new)
save("prepared.json",{"before_ref":pin(O/"checkpoint.before.json"),"after_ref":pin(O/"checkpoint.after.proposed.json"),"unchanged_other_refs":[pin(x) for x in other],"new_actual_failure_refs":refs,"execution_grant_issued":False})
assert cp.read_bytes()==old and [x.read_bytes() for x in other]==raw_other
tmp=cp.with_name(cp.name+"."+uuid.uuid4().hex);tmp.write_bytes(new);os.replace(tmp,cp)
assert cp.read_bytes()==new and [x.read_bytes() for x in other]==raw_other
closed=save("checkpoint.closed.json",{"checkpoint_ref":pin(cp),"revision":342,"ownership_revision":168,"registered_failures":681,"observed_failures":681,"old679_unchanged":True,"formal_acceptance":False,"real_provider_calls":0})
print(json.dumps({"closed_ref":closed,"checkpoint_ref":pin(cp),"state":"PROGRESS_PRESERVED_NO_LIVE_GRANT"}),flush=True)
