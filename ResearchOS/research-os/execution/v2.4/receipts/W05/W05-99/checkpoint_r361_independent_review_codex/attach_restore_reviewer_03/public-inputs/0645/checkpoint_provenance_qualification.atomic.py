import sys
sys.dont_write_bytecode=True
import json,hashlib,types,copy
from pathlib import Path
from datetime import datetime,timezone
R=Path(r"D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99";O=Path(__file__).resolve().parent
def pin(path):
 path=Path(path).resolve();raw=path.read_bytes();return dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def verify(ref):
 v=pin(ref["path"]);assert v["sha256"]==ref["sha256"].removeprefix("sha256:") and v["bytes"]==ref["bytes"];return v
def save(name,v):
 with (O/name).open("xb") as f:f.write((json.dumps(v,ensure_ascii=True,indent=2)+"\n").encode("utf-8"))
 return pin(O/name)
def module(path,raw):
 path=Path(path).resolve();m=types.ModuleType("root_cp361_"+path.stem);m.__file__=str(path);sys.modules[m.__name__]=m
 exec(compile(raw,str(path),"exec"),m.__dict__);return m
fp=O/"checkpoint.execution.facts.json";fr=dict(path=str(fp),sha256=sys.argv[1],bytes=int(sys.argv[2]));verify(fr);facts=json.loads(fp.read_bytes())
assert facts["schema"]=="researchos.root-cp361-evidence-facts.v1" and facts["formal_acceptance"] is False
qr=verify(facts["qualification_ref"]);q=json.loads(Path(qr["path"]).read_bytes())
cp=R/"execution/v2.4/checkpoint.json";ow=R/"execution/v2.4/path_ownership.json";pair=[pin(cp),pin(ow)];old=[cp.read_bytes(),ow.read_bytes()]
assert pair[0]["sha256"]=="685545935a0da0bf576eb28ada59f453beb9d26628af4f656faf18f94d336d56" and pair[0]["bytes"]==4126105
assert pair[1]["sha256"]=="48c5641956b5f22bb48f7775e46d90494bd95944027f55070e430e207a506452"
before=json.loads(old[0]);assert before["revision"]==360 and len(before["failure_counters"])==836
assert before["head"]=="adc460c2138528f163f7fdab5e8d81dde157b7fb" and before["project_id"]=="aede0678-7308-43dc-b9f2-cfe3d90cfdfb"
others=[R/"execution/v2.4"/(n+".json") for n in ("step_state","commands")];other_bytes=[p.read_bytes() for p in others]
refs=[verify(fr),qr,pin(__file__),pin(sys.executable)]
for entry in facts["reviews"]:
 refs += [verify(entry["handoff_ref"]),verify(entry["manifest_ref"])]
 mf=json.loads(Path(entry["manifest_ref"]["path"]).read_bytes());members=mf["members"];members=members.values() if isinstance(members,dict) else members
 refs += [verify(ref) for ref in members]
pending=facts["diagnostics"];assert [v["ordinal"] for v in pending]==list(range(839,847))
refs += [verify(v["origin_ref"]) for v in pending]+[verify(ref) for ref in facts["actual_refs"]]
gp=B/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py"
tp=B/"mu_sdk_controller_revision_v5_codex/e5953a6723c44426a05b5bb540186cdc/canonical_transactions.py"
assert pin(gp)["sha256"]=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85" and pin(tp)["sha256"]=="094e1a97fb00d01412b4e71e2d740b800accfce00e607c6853cb634280b12ba9"
refs += [pin(gp),pin(tp)];refs=list({r["path"].casefold():r for r in refs}.values())
gm=module(gp,gp.read_bytes());guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);guard.acquire(refs);tm=module(tp,guard.get_buffer(str(tp)))
def transform(c,o):
 assert c["revision"]==360 and o["revision"]==168
 corrected=[]
 for v in q["qualified_original_records"]:
  ordinal=v["ordinal"];indices=[i for i,x in enumerate(c["failure_counters"]) if x.get("original_payload",{}).get("observed_ordinal")==ordinal];assert len(indices)==1
  i=indices[0];entry=c["failure_counters"][i];assert entry==v["original_canonical_record"]
  p=entry["original_payload"]
  if ordinal==833:
   assert p["actual_python_exit"]==1
   p["source_reported_previous_actual_python_exit"]=1;p["actual_python_exit"]=None
   p["inferred_python_exit"]=1;p["inferred_exits_are_not_directly_observed"]=True
   p["previous_diagnostic_reported_by_CP360"]=p["diagnostic"]
   p["diagnostic"]="Original seal has actual outer1 and traceback, no independent Python exit marker; effective actualPythonNULL, source-reported/inferred1 retained separately. See immutable evidence qualification."
  else:
   assert ordinal==835 and p["actual_native_exit"]==1
   p["effective_native_rehearsal_creation_time_100ns_decimal"]=q["ordinal835"]["actual_rehearsal_FILETIME_decimal"]
   p["effective_native_harness_creation_time_100ns_decimal"]=q["ordinal835"]["actual_harness_FILETIME_decimal"]
   p["original_origin_FILETIME_fields_source_reported_inexact"]=True
  p["evidence_accuracy_qualification_ref"]=qr;corrected.append(i)
 assert len(corrected)==2
 for i,x in enumerate(c["failure_counters"]):
  original=before["failure_counters"][i]
  assert x["origin_key"]==original["origin_key"] and x["evidence_ref"]==original["evidence_ref"] and x["counted_once"]==original["counted_once"]
  if i not in corrected:assert x==original
 keys={x.get("origin_key") for x in c["failure_counters"]}
 for v in pending:
  ref=verify(v["origin_ref"]);ordinal=v["ordinal"];key=hashlib.sha256((ref["sha256"]+"#"+str(ordinal)).encode()).hexdigest()
  assert key not in keys;keys.add(key)
  c["failure_counters"].append(dict(origin_key=key,evidence_ref=ref,original_payload=dict(observed_ordinal=ordinal,immutable_origin_ref=ref,actual_outer_exit=v["actual_outer_exit"],actual_python_exit=v["actual_python_exit"],actual_native_exit=v["actual_native_exit"],diagnostic=v["description"],inferred_exits_are_not_directly_observed=ordinal in (841,842)),counted_once=True,counter_reset=False,automatic_retry=False))
 assert len(c["failure_counters"])==844
 c.update(expected_previous_revision=360,revision=361,updated_at=datetime.now(timezone.utc).isoformat(),updated_by="codex:/root")
 c["work_in_progress"].update(facts["work_in_progress"]);c["work_in_progress"].update(r361_registered_failure_count=844,r361_highest_observed_diagnostic_ordinal=846,mu_sdk_r361_facts_ref=verify(fr))
 c["note"]=facts["checkpoint_note"];return c,o
try:
 transaction=tm.update_pair(pair,transform,O,"activate")
 assert ow.read_bytes()==old[1] and [p.read_bytes() for p in others]==other_bytes and json.loads(cp.read_bytes())["revision"]==361
finally:
 cleanup=guard.close();save("source_guard.cleanup.actual.json",cleanup)
 assert cleanup["closed"] and not cleanup["errors"] and cleanup["retained_handles_count"]==0
proof=save("canonical_pair.actual.json",dict(transaction=transaction,checkpoint_ref=pin(cp),ownership_ref=pin(ow),old836_failure_count_and_origin_keys_preserved=True,old834_unqualified_entries_unchanged=True,qualified_old_ordinals=[833,835],qualification_ref=qr,new_original_ordinals=list(range(839,847)),registered_failures=844,highest_observed_diagnostic_ordinal=846,formal_acceptance=False))
resume=save("RESUME.r361.original.json",dict(schema="researchos.root-resume-evidence-qualified-sources-ready.v1",repository_root=str(R),checkpoint_ref=pin(cp),checkpoint_revision=361,ownership_revision=168,head=before["head"],project_id=before["project_id"],current_card="W05-99",historical_accepted_parents=6,current_formal_accepted=0,required_parents=22,required_formal=42,registered_failures=844,highest_observed_diagnostic_ordinal=846,next_failure_ordinal=847,qualification_ref=qr,Source_ATT3_and_Legacy2_and_Env_approved_scope_only=True,CTL3_Source_pending=True,Q5_Source_pending=True,Root_T8_detached_resource_ready=True,Root_new_compile_or_native_actual_done=False,native_T7_failed_closed=True,original_trial_once_consumed=True,original_trial_clock_expired=True,original_trial_provider_requests=None,financial_closed=False,original_trial_business_open=True,counter_reset=False,completion_asserted=False,proof_ref=proof,next_action=facts["next_action"]))
manifest=save("manifest.json",dict(members=[pin(p) for p in O.iterdir() if p.is_file()]))
hd=save("handoff.json",dict(status="CHECKPOINT_SAVED_EXIT833_AND_NATIVE835_IDENTITIES_QUALIFIED_SOURCE_FIXES_APPROVED_ACTUAL_PENDING",checkpoint_ref=pin(cp),resume_ref=resume,manifest_ref=manifest,formal_acceptance=False))
print(json.dumps(dict(checkpoint_ref=pin(cp),resume_ref=resume,handoff_ref=hd,registered_failures=844,highest_observed_diagnostic_ordinal=846)),flush=True)
