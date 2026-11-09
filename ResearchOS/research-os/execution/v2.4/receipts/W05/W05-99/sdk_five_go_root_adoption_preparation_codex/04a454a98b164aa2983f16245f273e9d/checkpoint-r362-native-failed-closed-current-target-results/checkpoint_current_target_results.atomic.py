import sys
sys.dont_write_bytecode=True
import json,hashlib,types,copy
from pathlib import Path
from datetime import datetime,timezone
R=Path(r"D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99";O=Path(__file__).resolve().parent
def pin(p):
 p=Path(p).resolve();raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def verify(v):
 q=pin(v["path"]);assert (q["sha256"],q["bytes"])==(v["sha256"].removeprefix("sha256:"),v["bytes"]);return q
def save(n,v):
 with (O/n).open("xb") as f:f.write((json.dumps(v,ensure_ascii=True,indent=2)+"\n").encode())
 return pin(O/n)
def module(p,raw):
 p=Path(p).resolve();m=types.ModuleType("root_cp362_"+p.stem);m.__file__=str(p);sys.modules[m.__name__]=m;exec(compile(raw,str(p),"exec"),m.__dict__);return m
fr=verify(dict(path=str(O/"checkpoint.execution.facts.current.json"),sha256=sys.argv[1],bytes=int(sys.argv[2])))
facts=json.loads(Path(fr["path"]).read_bytes());assert facts["schema"]=="researchos.root-cp362-failed-closed-current-target-facts.v1" and facts["formal_acceptance"] is False
cp=R/"execution/v2.4/checkpoint.json";ow=R/"execution/v2.4/path_ownership.json";pair=[pin(cp),pin(ow)];old=[cp.read_bytes(),ow.read_bytes()]
assert (pair[0]["sha256"],pair[0]["bytes"])==("27b6680899a8ba49b0f76fa6c7c917a80edecd0bcf68059de4dfc8da91088845",4147646)
assert (pair[1]["sha256"],pair[1]["bytes"])==("48c5641956b5f22bb48f7775e46d90494bd95944027f55070e430e207a506452",192861)
before=json.loads(old[0]);assert before["revision"]==361 and len(before["failure_counters"])==845
assert before["head"]=="adc460c2138528f163f7fdab5e8d81dde157b7fb" and before["project_id"]=="aede0678-7308-43dc-b9f2-cfe3d90cfdfb"
identity=R/"execution/project_identity.json";assert (pin(identity)["sha256"],pin(identity)["bytes"])==("03f06a2b72ae85b3445d724058b10c8b13bcdb98f31feaf195e10b2e88fb26ec",420)
others=[R/"execution/v2.4"/(n+".json") for n in ("step_state","commands")];other_bytes=[p.read_bytes() for p in others]
refs=[fr,pin(__file__),pin(sys.executable),pin(identity)]+[pin(p) for p in others]
for entry in facts["reviews"]:
 refs += [verify(entry["handoff_ref"]),verify(entry["manifest_ref"])]
 members=json.loads(Path(entry["manifest_ref"]["path"]).read_bytes())["members"];members=members.values() if isinstance(members,dict) else members
 refs += [verify(v) for v in members]
pending=facts["diagnostics"];assert [v["ordinal"] for v in pending]==list(range(848,876))
refs += [verify(v["origin_ref"]) for v in pending]+[verify(v) for v in facts["actual_refs"]]+[verify(facts["trace_bundle_ref"])]
gp=B/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py";tp=B/"mu_sdk_controller_revision_v5_codex/e5953a6723c44426a05b5bb540186cdc/canonical_transactions.py"
assert pin(gp)["sha256"]=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85"
assert pin(tp)["sha256"]=="094e1a97fb00d01412b4e71e2d740b800accfce00e607c6853cb634280b12ba9"
refs += [pin(gp),pin(tp)];refs=list({v["path"].casefold():v for v in refs if v["path"].casefold() not in {p["path"].casefold() for p in pair}}.values())
gm=module(gp,gp.read_bytes());guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);guard.acquire(refs);tm=module(tp,guard.get_buffer(str(tp.resolve())))
def transform(c,o):
 assert c["revision"]==361 and o["revision"]==168 and c["failure_counters"]==before["failure_counters"]
 keys={v.get("origin_key") for v in c["failure_counters"]}
 for v in pending:
  ref=verify(v["origin_ref"]);n=v["ordinal"];key=hashlib.sha256((ref["sha256"]+"#"+str(n)).encode()).hexdigest();assert key not in keys;keys.add(key)
  c["failure_counters"].append(dict(origin_key=key,evidence_ref=ref,original_payload=dict(observed_ordinal=n,immutable_origin_ref=ref,actual_outer_exit=v["actual_outer_exit"],actual_python_exit=v["actual_python_exit"],actual_native_exit=v["actual_native_exit"],diagnostic=v["description"]),counted_once=True,counter_reset=False,automatic_retry=False))
 assert len(c["failure_counters"])==873 and c["failure_counters"][:845]==before["failure_counters"]
 c.update(expected_previous_revision=361,revision=362,updated_at=datetime.now(timezone.utc).isoformat(),updated_by="codex:/root")
 c["work_in_progress"].update(facts["work_in_progress"])
 c["work_in_progress"].update(r362_registered_failure_count=873,r362_highest_observed_diagnostic_ordinal=875,r362_next_failure_ordinal_at_cutoff=876,mu_sdk_r362_facts_ref=fr)
 c["note"]=facts["checkpoint_note"];return c,o
try:
 transaction=tm.update_pair(pair,transform,O,"activate")
 assert ow.read_bytes()==old[1] and [p.read_bytes() for p in others]==other_bytes and json.loads(cp.read_bytes())["revision"]==362
finally:
 cleanup=guard.close();save("source_guard.cleanup.actual.json",cleanup);assert cleanup["closed"] and not cleanup["errors"] and cleanup["retained_handles_count"]==0
proof=save("canonical_pair.actual.json",dict(transaction=transaction,checkpoint_ref=pin(cp),ownership_ref=pin(ow),old845_failure_records_byte_equal=True,new_original_ordinals=list(range(848,876)),registered_failures=873,highest_observed_diagnostic_ordinal=875,formal_acceptance=False))
resume=save("RESUME.r362.original.json",dict(schema="researchos.root-resume-native-failed-closed-current-target.v1",repository_root=str(R),checkpoint_ref=pin(cp),checkpoint_revision=362,ownership_revision=168,head=before["head"],project_id=before["project_id"],current_card="W05-99",historical_accepted_parents=6,current_formal_accepted=0,required_parents=22,required_formal=42,registered_failures=873,highest_observed_diagnostic_ordinal=875,next_failure_ordinal_at_cutoff=876,later_source_diagnostics_pending=True,T8_native_failed_inspected_released_closed=True,T9_target_counts=dict(pass_terminals=152,fail_terminals=5,skip_terminals=0),T9_actual_limited_review_accepted=True,T9_child_native_pid_exit=None,broker4_source_accepted=True,broker4_pure17_actual_done=False,original_trial_once_consumed=True,original_trial_clock_expired=True,original_trial_provider_requests=None,financial_closed=False,original_trial_business_open=True,counter_reset=False,completion_asserted=False,proof_ref=proof,next_action=facts["next_action"]))
manifest=save("manifest.json",dict(members=[pin(p) for p in O.iterdir() if p.is_file()]))
hd=save("handoff.json",dict(status="CHECKPOINT_SAVED_NATIVE_FAILURE_CLOSED_CURRENT_TARGET_LIMITED_REVIEW_ACCEPTED_BROKER4_SOURCE_READY",checkpoint_ref=pin(cp),resume_ref=resume,manifest_ref=manifest,formal_acceptance=False))
print(json.dumps(dict(checkpoint_ref=pin(cp),resume_ref=resume,handoff_ref=hd,registered_failures=873,highest_observed_diagnostic_ordinal=875)),flush=True)


