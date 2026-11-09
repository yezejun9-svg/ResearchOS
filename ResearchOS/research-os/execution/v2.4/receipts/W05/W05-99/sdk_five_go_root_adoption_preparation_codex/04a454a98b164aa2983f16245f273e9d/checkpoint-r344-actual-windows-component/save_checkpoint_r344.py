import sys
sys.dont_write_bytecode=True
import hashlib,json,os,uuid
from datetime import datetime,timezone
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");O=Path(__file__).resolve().parent;P=O.parent;B=R/"execution/v2.4/receipts/W05/W05-99"
def pin(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def save(n,obj):
 p=O/n
 with p.open("xb") as f:f.write((json.dumps(obj,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(p)
cp=R/"execution/v2.4/checkpoint.json";old=cp.read_bytes()
assert hashlib.sha256(old).hexdigest()=="dff04bc12f9b54484877b98a7345dc6a878512f550575f8633790331215fd745"
c=json.loads(old);assert c["revision"]==343 and len(c["failure_counters"])==689
assert c["head"]=="adc460c2138528f163f7fdab5e8d81dde157b7fb" and c["current_step_id"]=="W05-99"
other=[R/"execution/v2.4"/(n+".json") for n in ("path_ownership","step_state","commands")];other_bytes=[p.read_bytes() for p in other]
NARROW=B/"mu_sdk_runner_v9_narrow_independent_review_codex/81a6e62dc2af4579aef73a0a477b891b"
CHAIN=B/"mu_sdk_controller_v4_observer_v3_independent_review_codex/4987830389c544cdbcc3f5895a987bd4"
GREV=B/"source_read_guard_v2_independent_review_codex/9697417e746d47d9abea9289d56db2f1"
ORIG=B/"mu_sdk_c5_control_failure_io_origins_codex/19ac9560253f41dcb055c26114a2955a"
pending=[
(690,NARROW/"failure-origin.690.json",1,None,None,"readonly missing directory",True),
(691,NARROW/"failure-origin.691.json",None,None,None,"functions.exec JS parse error before evaluation",True),
(692,P/"failure-origin.692.original-tool-io.json",1,1,None,"Source preparation exact pin path string normalization mismatch; no candidate generated",True),
(693,GREV/"failure-origin.693.json",None,None,None,"collaboration route missing target path, no shell/native",True),
(694,CHAIN/"failure-origin.694.json",1,None,None,"readonly path accidentally contained space",True),
(695,CHAIN/"failure-origin.695.json",1,1,None,"readonly metadata intake assumed old HDF source_ref key",True),
(696,P/"failure-origin.696.original-tool-io.json",1,1,1,"one causal actual private probe producer failed extracting winerror from stdio PermissionError; original preserved",True),
(697,CHAIN/"failure-origin.guard-manifest-key.json",1,1,None,"readonly metadata assumed other author manifest members key",True),
(698,P/"failure-origin.698.original-tool-io.json",1,1,1,"one causal private probe producer raw replacement predicate failed; original success and error values both unpersisted/unknown",True),
]
digests={699:"e8903e09559ce2e3f5a899ed4143b8ac1a8051339a6d4cb31d0b9955bc600ac3",700:"a2540183a99831d441b39fee90698d7e89b512b835ee7c9de87fb0ccce087bf2",701:"c6c14b22de8c4c3a2bf72986b4367b0d4173bc60529474086d5646de553ac5ec",702:"b90f6f53f9eb2b0511341b13e250c78eed3f5b35e89684d80bc32a90aa455eb7"}
for n,why in [(699,"author AST control missing constant NameError"),(700,"author pre-native fake object close setup assertion"),(701,"author conditional-close static assertion"),(702,"readonly stored IO console GBK encoding UnicodeEncodeError")]:
 p=ORIG/(str(n)+".original-commandExecution.item_json")
 assert pin(p)["sha256"]==digests[n]
 stored=json.loads(p.read_bytes())
 pending.append((n,p,1,1,None,why,False if n in (699,700,701) else True))
assert len(pending)==13 and [n for n,*rest in pending]==list(range(690,703))
keys={e.get("origin_key") for e in c["failure_counters"]};events=[]
for n,p,outer,py,native,why,complete in pending:
 ref=pin(p);key=hashlib.sha256((ref["sha256"]+"#"+str(n)).encode()).hexdigest();assert key not in keys;keys.add(key)
 event={"ordinal":n,"origin_ref":ref,"actual_outer_exit":outer,"actual_python_exit":py,"actual_private_probe_child_exit":native,"target_product_host_exit":None,"provider_requests":0,"diagnostic":why,"stored_tool_record_complete":True,"predecode_console_byte_fidelity":complete}
 if n==698:event["clarification_ref"]=pin(O/"failure-698-unknown-values.clarification.json")
 if n in (699,700,701):event["capture_gap"]="Stored aggregatedOutput already has U+FFFD; original pre-decoding stdout bytes unavailable, not reconstructed."
 c["failure_counters"].append({"origin_key":key,"evidence_ref":ref,"original_payload":{"observed_ordinal":n,"immutable_origin_ref":ref,"original_event":event,"full_original_tool_io_embedded":complete},"counter_reset":False,"counted_once":True,"automatic_retry":False})
 events.append(event)
assert len(c["failure_counters"])==702 and c["failure_counters"][:689]==json.loads(old)["failure_counters"]
with (O/"checkpoint.before.json").open("xb") as f:f.write(old)
c["expected_previous_revision"]=343;c["revision"]=344;c["updated_at"]=datetime.now(timezone.utc).isoformat();c["updated_by"]="codex:/root"
w=c["work_in_progress"]
w.update({"mu_sdk_live_trial_state":"C5_SOURCE_PROPOSED_AND_ACTUAL_WINDOWS_GUARD_COMPONENT_REVIEWED_NO_MODEL_GRANT",
"mu_sdk_runner_v9_independent_review_ref":pin(NARROW/"review.json"),
"mu_sdk_observer_v3_handoff_ref":pin(B/"mu_sdk_job_observer_revision_v3_codex/7a43feff8ec24250b87d04d0e346a52e/handoff.json"),
"mu_sdk_guard_v2_independent_source_review_ref":pin(GREV/"review.json"),
"mu_sdk_guard_v2_actual_component_handoff_ref":pin(B/"integration_codex/source-guard-v2-windows-probe-v3-2c915e750ee94356ae32b713bd3d1242/handoff.json"),
"mu_sdk_guard_v2_actual_component_independent_handoff_ref":pin(B/"source_guard_v2_actual_probe_independent_review_codex/7cf20b0f72ab42c6951a70e52aa41f77/handoff.json"),
"mu_sdk_controller_v4_independent_review_ref":pin(CHAIN/"independent-source-review.json"),
"mu_sdk_controller_v5_handoff_ref":pin(B/"mu_sdk_controller_revision_v5_codex/e5953a6723c44426a05b5bb540186cdc/handoff.json"),
"mu_sdk_controller_review_state":"C4_REQUEST_SOURCE_LIFETIME_RETENTION_C5_PENDING_TRUE_INDEPENDENT_REVIEW",
"mu_sdk_controller_open":["C5 full Source tuple independent review; guard/watchdog retention must stay in real resident parent PID","fresh owned Job cleanup probe tied to actual run/owner/Job; Source or arbitrary callback is insufficient","actual canonical exclusive pair and synchronous-callback deadline/samePID observer probes","actual resident Root caller and separately owned trusted Host whole300s lifecycle; READY/GO/EOF and aggregate three model requests"],
"mu_sdk_source_authors_active":[],
"mu_sdk_source_readonly_reviewers_active":["codex:/root/command_queue_impl: C5 Source lifecycle and full tuple review"],
"mu_sdk_active_run_uuid":None,"mu_sdk_live_execution_grant_issued":False,"mu_sdk_runtime_qualification":False,
"mu_sdk_actual_external_provider_requests_current_trial":0,
"r344_registered_failure_count":702,"r344_observed_failure_count":702,
"mu_sdk_guard_component_actual_status":"NONAUTHOR_PASS_ACTUAL_PRIVATE_WINDOWS_COMPONENT_IN_SCOPE",
"mu_sdk_next_action":"Complete C5 actual Source review and fix exact findings, implement resident Root caller/fresh Job query, then actual no-provider full lifecycle probes before Root SDK model scope."})
c["note"]="Root continues W05-99, Main adc460c2/5Go unchanged,22 local top-level tests remain; current accepted parents6/22 formal0/42. Trusted Host revised4Go actual compiler0 reviewed in Source-only scope. Runnerv9 Source READY and O3 rebound. Real Windows guard component private-target probe c4a7ea native0/parent0:write/delete32,replace5 with same-path positive before/after,3handles and Job allclean; nonauthor exact-record review passed. C4 singleP1 lifecycle finding persists, C5 proposed resident retention under independent review, no grant/model requests. Late actual diagnostics690-702 appended once, failed696698 kept;698 old boolean/error both unknown,699-701 stored console decoding gap disclosed. No reset/wholequalification/formal increment."
new=(json.dumps(c,ensure_ascii=False,indent=2)+"\n").encode()
with (O/"checkpoint.after.proposed.json").open("xb") as f:f.write(new)
save("prepared.json",{"before_ref":pin(O/"checkpoint.before.json"),"after_ref":pin(O/"checkpoint.after.proposed.json"),"other_canonical_refs":[pin(p) for p in other],"new_actual_failure_events":events,"execution_grant_issued":False,"formal_acceptance":False})
assert cp.read_bytes()==old and [p.read_bytes() for p in other]==other_bytes
temp=cp.with_name(cp.name+"."+uuid.uuid4().hex)
with temp.open("xb") as f:f.write(new);f.flush();os.fsync(f.fileno())
assert cp.read_bytes()==old
os.replace(temp,cp)
assert cp.read_bytes()==new and [p.read_bytes() for p in other]==other_bytes
closed=save("checkpoint.closed.json",{"checkpoint_ref":pin(cp),"revision":344,"ownership_revision":168,"registered_failures":702,"observed_failures":702,"old689_unchanged":True,"other_canonical_unchanged":True,"formal_acceptance":False,"real_provider_calls":0})
print(json.dumps({"closed_ref":closed,"checkpoint_ref":pin(cp),"state":"ACTUAL_GUARD_COMPONENT_REVIEWED_NO_LIVE_GRANT"}),flush=True)

