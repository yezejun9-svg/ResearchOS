import sys
sys.dont_write_bytecode=True
import json,hashlib,types
from pathlib import Path
from datetime import datetime,timezone
R=Path("D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99";O=Path(__file__).resolve().parent
def pin(p):
 p=Path(p).resolve();raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def verify(v):
 q=pin(v["path"]);assert (q["sha256"],q["bytes"])==(v["sha256"].removeprefix("sha256:"),v["bytes"]);return q
def save(n,v):
 with (O/n).open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(O/n)
def module(p,raw):
 p=Path(p).resolve();m=types.ModuleType("cp363_"+p.stem);m.__file__=str(p);sys.modules[m.__name__]=m;exec(compile(raw,str(p),"exec"),m.__dict__);return m
assert len(sys.argv)==3, "usage: writer FACTS_SHA256 FACTS_BYTES"
fr=verify(dict(path=str(O/"checkpoint.execution.facts.json"),sha256=sys.argv[1],bytes=int(sys.argv[2])));facts=json.loads(Path(fr["path"]).read_bytes())
assert facts["schema"]=="researchos.root-cp365-c12-failed-archive-and-h20-component-facts.v1" and facts["formal_acceptance"] is False
cp=R/"execution/v2.4/checkpoint.json";ow=R/"execution/v2.4/path_ownership.json";pair=[pin(cp),pin(ow)];old=[cp.read_bytes(),ow.read_bytes()]
assert (pair[0]["sha256"],pair[0]["bytes"])==("6ed349c5b8380ad6b099ae2237c33513f4e2717afc7789398968366a8cddf6dd",4237636)
assert (pair[1]["sha256"],pair[1]["bytes"])==("48c5641956b5f22bb48f7775e46d90494bd95944027f55070e430e207a506452",192861)
before=json.loads(old[0]);assert before["revision"]==364 and len(before["failure_counters"])==900
assert before["head"]=="adc460c2138528f163f7fdab5e8d81dde157b7fb" and before["project_id"]=="aede0678-7308-43dc-b9f2-cfe3d90cfdfb"
identity=R/"execution/project_identity.json";assert (pin(identity)["sha256"],pin(identity)["bytes"])==("03f06a2b72ae85b3445d724058b10c8b13bcdb98f31feaf195e10b2e88fb26ec",420)
others=[R/"execution/v2.4"/(n+".json") for n in ("step_state","commands")];other_bytes=[p.read_bytes() for p in others]
assert [pin(p) for p in (cp,ow,*others)]==facts["canonical_refs"]
assert facts["registered_before"]==900 and facts["registered_after"]==922 and facts["highest_observed_ordinal"]==924 and facts["next_failure_ordinal"]==925
gp=B/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py";tp=B/"mu_sdk_controller_revision_v5_codex/e5953a6723c44426a05b5bb540186cdc/canonical_transactions.py"
assert pin(gp)["sha256"]=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85" and pin(tp)["sha256"]=="094e1a97fb00d01412b4e71e2d740b800accfce00e607c6853cb634280b12ba9"
gm=module(gp,gp.read_bytes());tm=module(tp,tp.read_bytes())
refs=[fr,pin(__file__),pin(sys.executable),pin(identity),pin(gp),pin(tp)]+[pin(p) for p in others]
for e in facts["reviews"]:
 refs.extend([verify(e["handoff_ref"]),verify(e["manifest_ref"])])
 members=json.loads(Path(e["manifest_ref"]["path"]).read_bytes())["members"]
 members=members.values() if isinstance(members,dict) else members
 refs.extend(verify(v) for v in members)
pending=facts["diagnostics"];assert [v["ordinal"] for v in pending]==list(range(903,925))
refs += [verify(v["origin_ref"]) for v in pending]+[verify(v) for v in facts["actual_refs"]]+[verify(v) for v in facts["qualification_refs"]]
for mod in list(sys.modules.values()):
 for field in ("__file__","__cached__"):
  p=getattr(mod,field,None)
  if p and Path(p).is_file():refs.append(pin(p))
pairs={p["path"].casefold() for p in pair};unique={}
for ref in refs:
 if ref["path"].casefold() in pairs:continue
 key=ref["path"].casefold();assert key not in unique or unique[key]==ref;unique[key]=ref
refs=list(unique.values());guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);guard.acquire(refs)
def transform(c,o):
 assert c["revision"]==364 and o["revision"]==168 and c["failure_counters"]==before["failure_counters"]
 keys={v.get("origin_key") for v in c["failure_counters"]}
 for v in pending:
  ref=verify(v["origin_ref"]);n=v["ordinal"];key=hashlib.sha256((ref["sha256"]+"#"+str(n)).encode()).hexdigest();assert key not in keys;keys.add(key)
  c["failure_counters"].append(dict(origin_key=key,evidence_ref=ref,original_payload=dict(observed_ordinal=n,immutable_origin_ref=ref,actual_outer_exit=v["actual_outer_exit"],actual_python_exit=v["actual_python_exit"],actual_native_exit=v["actual_native_exit"],diagnostic=v["description"],origin_selector=v["origin_selector"],exit_qualification=v["exit_qualification"]),counted_once=True,counter_reset=False,automatic_retry=False))
 assert len(c["failure_counters"])==922 and c["failure_counters"][:900]==before["failure_counters"]
 c.update(expected_previous_revision=364,revision=365,updated_at=datetime.now(timezone.utc).isoformat(),updated_by="codex:/root")
 c["work_in_progress"].update(facts["work_in_progress"])
 c["work_in_progress"].update(r365_registered_failure_count=922,r365_highest_observed_diagnostic_ordinal_at_cutoff=924,r365_next_failure_ordinal_at_cutoff=925,mu_sdk_r365_facts_ref=fr,later_diagnostics_observed_after_cutoff=[],root_next_failure_ordinal_live=925)
 c["note"]=facts["checkpoint_note"];return c,o
try:
 transaction=tm.update_pair(pair,transform,O,"activate")
 assert ow.read_bytes()==old[1] and [p.read_bytes() for p in others]==other_bytes and json.loads(cp.read_bytes())["revision"]==365
finally:
 cleanup=guard.close();save("source_guard.cleanup.actual.json",cleanup);assert cleanup["closed"] and not cleanup["errors"] and cleanup["retained_handles_count"]==0
def raw_failure_array(raw):
 text=raw.decode("utf-8");start=text.index("[",text.index('"failure_counters":'));value,end=json.JSONDecoder().raw_decode(text[start:]);return text[start:start+end]
old_array=raw_failure_array(old[0]);new_array=raw_failure_array(cp.read_bytes());prefix=old_array.rstrip()[:-1].rstrip()
prefix_equal=new_array.startswith(prefix+",")
assert prefix_equal
proof=save("canonical_pair.actual.json",dict(transaction=transaction,checkpoint_ref=pin(cp),ownership_ref=pin(ow),old900_failure_records_semantic_equal=True,old900_raw_array_prefix_preserved=prefix_equal,new_original_ordinals=list(range(903,925)),registered_failures=922,highest_observed_diagnostic_ordinal_at_cutoff=924,later_diagnostics_pending=[],live_next_failure_ordinal=925,formal_acceptance=False))
resume=save("RESUME.r365.original.json",dict(schema="researchos.root-resume-c12-failed-archive-and-h20-component.v1",repository_root=str(R),checkpoint_ref=pin(cp),checkpoint_revision=365,ownership_revision=168,head=before["head"],project_id=before["project_id"],current_card="W05-99",historical_accepted_parents=6,current_formal_accepted=0,required_parents=22,required_formal=42,registered_failures=922,highest_registered_ordinal=924,next_failure_ordinal_at_cutoff=925,later_diagnostics_pending=[],live_next_failure_ordinal=925,native_T10_exit1_closed=True,native_T10_wholeSQL_after_observed=False,native_T10_specific_release=False,native_T10_fixture_lost=True,broker4_pure17_actual_passed=True,T11_actual_tests="FIVE_TERMINAL_PASS_COMPONENT_ONLY",N12_actual_tests="35_TERMINAL_PASS_COMPONENT_ONLY",C12_actual="FAILED_ORIGINAL_SERVE_EXIT1_GRANT_UNPUBLISHED",C12_wholeSQL="SCHEMA1_TO23_UNCHANGED",C12_explicit_fixture_release=False,C12_fixture_retained_window_expired=True,C12_native_acceptance=False,H20R2_actual="9_TERMINAL_PASS_COMPONENT_A20_TO_PLAIN21_ONLY",public_archive="61_FULL_TEMP_PIN_CLOSURE_COMPONENT_ACCEPTED",W09r2_Source="PENDING_INDEPENDENT_SOURCE_REVIEW_NO_ACTUAL_SCOPE",T11_failed_fullcheckout_preserved=True,T11_sparse_source="ACTUAL_INDEPENDENTLY_ACCEPTED_COMPONENT_ONLY",original_trial_once_consumed=True,original_trial_clock_expired=True,original_trial_provider_requests=None,financial_closed=False,original_trial_business_open=True,counter_reset=False,completion_asserted=False,proof_ref=proof,next_action=facts["next_action"]))
manifest=save("manifest.json",dict(members=[pin(p) for p in O.iterdir() if p.is_file()]))
hd=save("handoff.json",dict(status="CHECKPOINT_SAVED_C12_FAILED_CLOSED_PUBLIC61_ARCHIVE_H20R2_COMPONENT_ACCEPTED",checkpoint_ref=pin(cp),resume_ref=resume,manifest_ref=manifest,formal_acceptance=False))
print(json.dumps(dict(checkpoint_ref=pin(cp),resume_ref=resume,handoff_ref=hd,registered_failures=922,highest_registered_ordinal=924)),flush=True)

