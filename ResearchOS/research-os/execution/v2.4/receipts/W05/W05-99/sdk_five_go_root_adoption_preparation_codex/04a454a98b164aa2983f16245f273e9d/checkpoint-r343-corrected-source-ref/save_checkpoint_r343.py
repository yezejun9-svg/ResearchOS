import sys
sys.dont_write_bytecode=True
import hashlib,json,os,uuid
from pathlib import Path
from datetime import datetime,timezone
R=Path("D:/作品集/ResearchOS/research-os");O=Path(__file__).resolve().parent;P=O.parent
BASE=R/"execution/v2.4/receipts/W05/W05-99"
def pin(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def save(n,v):
 p=O/n
 with p.open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(p)
cp=R/"execution/v2.4/checkpoint.json";old=cp.read_bytes()
assert hashlib.sha256(old).hexdigest()=="21cfd200ebf23283909b44d8033175a59448330f1f152168aaa13e9ba57e4e44"
c=json.loads(old);assert c["revision"]==342 and len(c["failure_counters"])==681 and c["head"]=="adc460c2138528f163f7fdab5e8d81dde157b7fb"
other=[R/"execution/v2.4"/(x+".json") for x in ("path_ownership","step_state","commands")];other_bytes=[x.read_bytes() for x in other]
orig682=BASE/"mu_sdk_observer_v2_independent_source_review_codex/75b8c18a1ee84e2db9738de1ac2a1d0b/failure-origin.read-report-name.json"
assert pin(orig682)["sha256"]=="78f1d48968d2d4ffd4bf0f300d8b8611a44bbc3fd04da7c40d359960a9ade658"
locator=BASE/"mu_sdk_trusted_host_independent_source_review_codex/a23894ca628e4e2c85ead05c283d73aa/failure-origin.readonly-locator.json"
assert pin(locator)["sha256"]=="1f43c637912983cc2add1c460cce1affe31ca428d86e60218123ec147d276eb2"
records=json.loads(locator.read_bytes())["failures"];bychunk={}
for entry in records:
 result=entry["result"]
 if "value" in result:result=result["value"]
 bychunk[result["chunk_id"]]=(entry,result)
assert set(bychunk)=={"5eb308","421888","4c30ee","99365b"}
pending=[{"ordinal":682,"ref":pin(orig682),"original_chunk":None,"outer_exit":1,"python_exit":None,"target_native_exit":None,"diagnostic":"readonly missing source report path"}]
for n,chunk in [(683,"5eb308"),(684,"421888"),(685,"4c30ee"),(686,"99365b")]:
 entry,result=bychunk[chunk]
 assert result["exit_code"]==(1 if n==683 else 0)
 pending.append({"ordinal":n,"ref":pin(locator),"original_chunk":chunk,"outer_exit":result["exit_code"],"python_exit":None,"target_native_exit":None,"embedded_rg_exit":None,"embedded_rg_exit_not_separately_observed":n!=683,"diagnostic":"readonly rg missing literal path or Windows wildcard path; exact original stderr retained"})
pending += [{"ordinal":687,"ref":pin(BASE/"integration_codex/trusted-host-build-7c2f6e6f4b884f00930fa07e1b4e508d/failure-origin.687.original-tool-io.json"),"original_chunk":"f17665","outer_exit":1,"python_exit":1,"go_native_exit":1,"target_host_exit":None,"one_causal_chain":True,"diagnostic":"Go package build rejected by existing execution/go.mod boundary; named-files build subsequently passed"},
 {"ordinal":688,"ref":pin(P/"failure-origin.688.original-tool-io.json"),"original_chunk":"2c8e41","outer_exit":1,"python_exit":None,"target_native_exit":None,"diagnostic":"readonly guessed controller filename missing; exact directory then controller.py read succeeded"}]
pending.append({"ordinal":689,"ref":pin(P/"failure-origin.689.original-tool-io.json"),"original_chunk":"16bcaa","outer_exit":1,"python_exit":1,"target_native_exit":None,"one_causal_chain":True,"diagnostic":"checkpoint preparation read a guessed observer review filename; canonical write not reached, current342 preserved; corrected fresh preparation uses enumerated independent-review.json"})
keys={e.get("origin_key") for e in c["failure_counters"]}
for event in pending:
 key=hashlib.sha256((event["ref"]["sha256"]+"#"+str(event["ordinal"])+":"+(event["original_chunk"] or "origin682")).encode()).hexdigest()
 assert key not in keys;keys.add(key)
 c["failure_counters"].append({"origin_key":key,"evidence_ref":event["ref"],"original_payload":{"observed_ordinal":event["ordinal"],"immutable_origin_ref":event["ref"],"full_original_tool_io_embedded":True,"source_locator":event},"counter_reset":False,"counted_once":True,"automatic_retry":False})
assert len(c["failure_counters"])==689 and c["failure_counters"][:681]==json.loads(old)["failure_counters"]
with (O/"checkpoint.before.json").open("xb") as f:f.write(old)
c["expected_previous_revision"]=342;c["revision"]=343;c["updated_at"]=datetime.now(timezone.utc).isoformat();c["updated_by"]="codex:/root"
w=c["work_in_progress"]
w.update({"mu_sdk_live_trial_state":"SOURCE_CORRECTIONS_NO_MODEL_GRANT",
"mu_sdk_runner_v9_handoff_ref":pin(BASE/"mu_model_sdk_real_trial_v9_source_codex/8c135404809b41a5a795574699bd0249/handoff.json"),
"mu_sdk_controller_v3_handoff_ref":pin(BASE/"mu_sdk_controller_revision_v3_codex/41ee2ad00c864829b5f6926c5fac919f/handoff.json"),
"mu_sdk_controller_review_state":"V3_INDEPENDENT_REQUEST_CHANGES_THREE_REMAINING_GAPS",
"mu_sdk_controller_open":["partial canonical close must reject fresh admission while either canonical retains the old active lease","watchdog thread start failure must close duplicate handle and preserve terminal invocation","immutable Windows FILE_SHARE_READ Source ownership must span observation Resume and all path consumers","actual no-provider same-PID owned Job/observer/watchdog/Source guard probes","trusted Host separately owned whole-trial lifecycle with stdin READY/GO/EOF"],
"mu_sdk_observer_v2_review_ref":pin(BASE/"mu_sdk_observer_v2_independent_source_review_codex/75b8c18a1ee84e2db9738de1ac2a1d0b/independent-review.json"),
"mu_sdk_trusted_host_v2_manifest_ref":pin(BASE/"mu_sdk_trusted_qualification_host_source_revision_codex/797a5659dec64d55a16915d1aea6e46c/manifest.json"),
"mu_sdk_trusted_host_v2_actual_compile_ref":pin(BASE/"integration_codex/trusted-host-v2-build-147c7ec3b9a7494db8518cce368e7529/compile.closed.json"),
"mu_sdk_trusted_host_v1_actual_compile_ref":pin(BASE/"integration_codex/trusted-host-named-file-build-1d640c13b19a49c5aeb1607aeae2c170/compile.closed.json"),
"mu_sdk_source_authors_active":["codex:/root: controller v4 corrections","codex:/root/live_resource_lookup: Windows SourceReadGuard module"],
"mu_sdk_source_readonly_reviewers_active":["codex:/root/command_queue_impl: controller v3 then runner v9 review","codex:/root/w05_merge_review: corrected trusted Host v2 and actual compiler receipts"],
"mu_sdk_active_run_uuid":None,"mu_sdk_live_execution_grant_issued":False,"mu_sdk_runtime_qualification":False,
"mu_sdk_actual_external_provider_requests_current_trial":0,"r343_registered_failure_count":689,"r343_observed_failure_count":689,
"mu_sdk_next_action":"Seal controller v4 with independent SourceReadGuard import and partial-pair admission gate, complete Source reviews, then Root actual no-provider OS probes before fresh model scope."})
c["note"]="Source corrections continue on W05-99: five-Go Main commit adc460c2 and22 local top-level PASS remain unchanged. Old and revised trusted Host both actual named-file compile PASS/owned Job cleanup, no target Host/provider execution. Host v2 and runner v9 Source await nonauthor review. True independent C3 Source review finds3 remaining gaps; C4 and SourceReadGuard under construction. Late actual failures682-689 appended exactly once with complete original IO, including four locator chunks in one immutable file and one causal Go failure687. Current formal0/42, accepted parents6/22; no grant."
new=(json.dumps(c,ensure_ascii=False,indent=2)+"\n").encode()
with (O/"checkpoint.after.proposed.json").open("xb") as f:f.write(new)
save("prepared.json",{"before_ref":pin(O/"checkpoint.before.json"),"after_ref":pin(O/"checkpoint.after.proposed.json"),"unchanged_other_refs":[pin(x) for x in other],"new_actual_failure_events":pending,"original_tool_io_ref":pin(O/"root-builds-and-runner.original-tool-io.json"),"execution_grant_issued":False})
assert cp.read_bytes()==old and [x.read_bytes() for x in other]==other_bytes
tmp=cp.with_name(cp.name+"."+uuid.uuid4().hex)
with tmp.open("xb") as f:f.write(new);f.flush();os.fsync(f.fileno())
assert cp.read_bytes()==old
os.replace(tmp,cp)
assert cp.read_bytes()==new and [x.read_bytes() for x in other]==other_bytes
closed=save("checkpoint.closed.json",{"checkpoint_ref":pin(cp),"revision":343,"ownership_revision":168,"registered_failures":689,"observed_failures":689,"old681_unchanged":True,"other_canonical_unchanged":True,"formal_acceptance":False,"real_provider_calls":0})
print(json.dumps({"closed_ref":closed,"checkpoint_ref":pin(cp),"state":"PROGRESS_PRESERVED_NO_LIVE_GRANT"}),flush=True)

