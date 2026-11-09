import sys
sys.dont_write_bytecode=True
import json,hashlib,types
from pathlib import Path
from datetime import datetime,timezone
R=Path(r"D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99";O=Path(__file__).resolve().parent
def pin(path):
 path=Path(path).resolve();raw=path.read_bytes();return dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def verify(ref):
 value=pin(ref["path"]);assert value["sha256"]==ref["sha256"].removeprefix("sha256:") and value["bytes"]==ref["bytes"];return value
def save(name,value):
 with (O/name).open("xb") as f:f.write((json.dumps(value,ensure_ascii=True,indent=2)+"\n").encode("utf-8"))
 return pin(O/name)
def module(path,raw):
 path=Path(path).resolve();m=types.ModuleType("root_cp360_"+path.stem);m.__file__=str(path);sys.modules[m.__name__]=m
 exec(compile(raw,str(path),"exec"),m.__dict__);return m
facts_path=O/"checkpoint.execution.facts.json";facts_ref={"path":str(facts_path),"sha256":sys.argv[1],"bytes":int(sys.argv[2])}
verify(facts_ref);facts=json.loads(facts_path.read_bytes())
assert facts["schema"]=="researchos.root-cp360-evidence-facts.v1" and facts["formal_acceptance"] is False
cp=R/"execution/v2.4/checkpoint.json";ow=R/"execution/v2.4/path_ownership.json"
pair=[pin(cp),pin(ow)];old=[cp.read_bytes(),ow.read_bytes()]
assert pair[0]["sha256"]=="f52e1416c81fefedde08725c3a7c9250a8e478b22e38b1e6ec1f7e42be236ecc"
assert pair[1]["sha256"]=="48c5641956b5f22bb48f7775e46d90494bd95944027f55070e430e207a506452"
before=json.loads(old[0]);assert before["revision"]==359 and len(before["failure_counters"])==829
assert before["project_id"]=="aede0678-7308-43dc-b9f2-cfe3d90cfdfb" and before["head"]=="adc460c2138528f163f7fdab5e8d81dde157b7fb"
others=[R/"execution/v2.4"/(name+".json") for name in ("step_state","commands")];others_before=[p.read_bytes() for p in others]
refs=[verify(facts_ref),pin(__file__),pin(sys.executable)]
for entry in facts["reviews"]:
 for ref in (entry["handoff_ref"],entry["manifest_ref"]):refs.append(verify(ref))
 mf=json.loads(Path(entry["manifest_ref"]["path"]).read_bytes())
 members=mf["members"];members=members.values() if isinstance(members,dict) else members
 refs.extend(verify(ref) for ref in members)
pending=facts["diagnostics"];assert [item["ordinal"] for item in pending]==list(range(832,839))
refs.extend(verify(item["origin_ref"]) for item in pending)
refs.extend(verify(ref) for ref in facts["actual_refs"])
gp=B/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py"
tp=B/"mu_sdk_controller_revision_v5_codex/e5953a6723c44426a05b5bb540186cdc/canonical_transactions.py"
gp_raw=gp.read_bytes();assert hashlib.sha256(gp_raw).hexdigest()=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85"
assert pin(tp)["sha256"]=="094e1a97fb00d01412b4e71e2d740b800accfce00e607c6853cb634280b12ba9"
refs += [pin(gp),pin(tp)];refs=list({ref["path"].casefold():ref for ref in refs}.values())
gm=module(gp,gp_raw);guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);guard.acquire(refs)
tm=module(tp,guard.get_buffer(str(tp)))
def transform(c,o):
 assert c["revision"]==359 and o["revision"]==168
 keys={entry.get("origin_key") for entry in c["failure_counters"]}
 for item in pending:
  ref=verify(item["origin_ref"]);ordinal=item["ordinal"]
  key=hashlib.sha256((ref["sha256"]+"#"+str(ordinal)).encode()).hexdigest()
  assert key not in keys;keys.add(key)
  c["failure_counters"].append(dict(origin_key=key,evidence_ref=ref,original_payload=dict(observed_ordinal=ordinal,immutable_origin_ref=ref,actual_outer_exit=item["actual_outer_exit"],actual_python_exit=item["actual_python_exit"],actual_native_exit=item["actual_native_exit"],diagnostic=item["description"],inferred_exits_are_not_directly_observed=False),counted_once=True,counter_reset=False,automatic_retry=False))
 assert c["failure_counters"][:829]==before["failure_counters"] and len(c["failure_counters"])==836
 c.update(expected_previous_revision=359,revision=360,updated_at=datetime.now(timezone.utc).isoformat(),updated_by="codex:/root")
 c["work_in_progress"].update(facts["work_in_progress"])
 c["work_in_progress"].update(r360_registered_failure_count=836,r360_highest_observed_diagnostic_ordinal=838,mu_sdk_r360_facts_ref=verify(facts_ref))
 c["note"]=facts["checkpoint_note"]
 return c,o
try:
 transaction=tm.update_pair(pair,transform,O,"activate")
 assert ow.read_bytes()==old[1] and [p.read_bytes() for p in others]==others_before
 assert json.loads(cp.read_bytes())["revision"]==360
finally:
 cleanup=guard.close();save("source_guard.cleanup.actual.json",cleanup)
 assert cleanup["closed"] and not cleanup["errors"] and cleanup["retained_handles_count"]==0
proof=save("canonical_pair.actual.json",dict(transaction=transaction,checkpoint_ref=pin(cp),ownership_ref=pin(ow),old829prefix_preserved=True,registered_failures=836,highest_observed_diagnostic_ordinal=838,formal_acceptance=False))
resume=save("RESUME.r360.original.json",dict(schema="researchos.root-resume-native-temp-failed-closed-attach-timestamp-open.v1",repository_root=str(R),checkpoint_ref=pin(cp),checkpoint_revision=360,ownership_revision=168,head=before["head"],project_id=before["project_id"],current_card="W05-99",historical_accepted_parents=6,current_formal_accepted=0,formal_required=42,registered_failures=836,highest_observed_diagnostic_ordinal=838,native_T7_positive_failed_and_closed=True,signatures_created=0,native9_accepted=False,typed_Q3_epoch_actual_state="49SOURCE_25PARENTS_61PASS6FAIL0SKIP_ALL_FOUR_JOBS_CLOSED_RUNTIME8_ATTACH_ACK_FAILURE",original_trial_business_open=True,original_trial_provider_requests=None,financial_closed=False,once_consumed=True,original_clock_expired=True,counter_reset=False,completion_asserted=False,proof_ref=proof,next_action=facts["next_action"]))
manifest=save("manifest.json",dict(members=[pin(path) for path in O.iterdir() if path.is_file()]))
handoff=save("handoff.json",dict(status="CHECKPOINT_SAVED_T7_NATIVE_TEMP_FAILURE_CLOSED_ATTACH_RESTORE_TIMESTAMP_SOURCE_REJECTED_LEGACY_ROLLBACK_SOURCE_REVISION",checkpoint_ref=pin(cp),resume_ref=resume,manifest_ref=manifest,formal_acceptance=False))
print(json.dumps(dict(checkpoint_ref=pin(cp),resume_ref=resume,handoff_ref=handoff,registered_failures=836,highest_observed_diagnostic_ordinal=838)),flush=True)
