import copy,hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent;R=Path("D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99";C=B/"checkpoint_r365_source_preparation_codex/cp365-1a11f08"
S=R/"execution/v2.4/receipts/W09/W09-99/integration_codex/w09c19-root-scope-1791524400000"
inputs={};checks=[]
def pin(p):
 p=Path(p).resolve();raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def ck(k,v):checks.append(dict(label=k,passed=bool(v)))
def verify(ref):
 e=dict(path=str(Path(ref["path"]).resolve()),sha256=ref["sha256"].removeprefix("sha256:"),bytes=ref["bytes"]);ck("pin:"+e["path"],pin(e["path"])==e);inputs[e["path"]]=e;return e
def add(p):return verify(pin(p))
def read(p):return json.loads(Path(p).read_bytes())
def save(name,obj):
 with (N/name).open("x",encoding="utf-8",newline="\n") as f:f.write(json.dumps(obj,ensure_ascii=False,indent=2)+"\n")
io=read(add(C/"postseal-root-canonical-actual-original-tool-io.json")["path"])
actual=io["writer_actual"];ck("Rootactual-shell-Python0",actual["chunk_id"]=="116748" and actual["exit_code"]==0 and "ROOT_PYTHON_EXIT=0" in actual["output"])
emitted=json.loads(actual["output"].splitlines()[0]);verify(emitted["handoff_ref"]);h=read(C/"handoff.json");verify(h["manifest_ref"])
members={Path(x["path"]).name:x for x in read(h["manifest_ref"]["path"])["members"]}
# Only actual artifacts and previously reviewed transform facts are revisited.
for name in ("canonical_pair.actual.json","source_guard.cleanup.actual.json","RESUME.r365.original.json","checkpoint.execution.facts.json"):verify(members[name])
pair=read(C/"canonical_pair.actual.json");facts=read(C/"checkpoint.execution.facts.json")
J=Path(pair["transaction"]["transaction_journal"])
intent=read(add(J/"intent.json")["path"]);commit=read(add(J/"committed.json")["path"])
ck("committed-both-exclusive",commit["written_indices"]==[0,1] and commit["both_verified_while_exclusively_held"] is True and intent["mandatory_share_mode"]==0 and intent["automatic_inverse"] is False)
ck("journal-no-failed-partial",not (J/"failed.partial.json").exists())
for ref in intent["before_refs"]+intent["after_refs"]+commit["after_refs"]:verify(ref)
before=[Path(x["path"]).read_bytes() for x in intent["before_refs"]];after=[Path(x["path"]).read_bytes() for x in intent["after_refs"]]
ck("journal-before-CP364OW168",[(x["sha256"],x["bytes"]) for x in intent["before_refs"]]==[(x["sha256"],x["bytes"]) for x in facts["canonical_refs"][:2]])
ck("live-after-byte-equality",after==[Path(x["path"]).read_bytes() for x in commit["after_refs"]])
ck("pair-committed-ref-equality",commit["after_refs"]==[pair["checkpoint_ref"],pair["ownership_ref"]]==[pair["transaction"]["checkpoint_ref"],pair["transaction"]["ownership_ref"]])
c0,o0=map(json.loads,before);c,o=map(json.loads,after)
ck("revision365169",c0["revision"]==364 and o0["revision"]==168 and c["revision"]==365 and o["revision"]==169)
ck("old900-semantic",len(c0["failure_counters"])==900 and c["failure_counters"][:900]==c0["failure_counters"])
def arr(raw):
 s=raw.decode();start=s.index("[",s.index('"failure_counters":'));_,end=json.JSONDecoder().raw_decode(s[start:]);return s[start:start+end]
ck("old900-rawprefix",arr(after[0]).startswith(arr(before[0]).rstrip()[:-1].rstrip()+","))
expected=copy.deepcopy(c0)
for d in facts["diagnostics"]:
 ref=dict(path=str(Path(d["origin_ref"]["path"]).resolve()),sha256=d["origin_ref"]["sha256"].removeprefix("sha256:"),bytes=d["origin_ref"]["bytes"])
 payload=dict(observed_ordinal=d["ordinal"],immutable_origin_ref=ref,actual_outer_exit=d["actual_outer_exit"],actual_python_exit=d["actual_python_exit"],actual_native_exit=d["actual_native_exit"],diagnostic=d["description"],origin_selector=d["origin_selector"],exit_qualification=d["exit_qualification"])
 expected["failure_counters"].append(dict(origin_key=hashlib.sha256((ref["sha256"]+"#"+str(d["ordinal"])).encode()).hexdigest(),evidence_ref=ref,original_payload=payload,counted_once=True,counter_reset=False,automatic_retry=False))
expected.update(expected_previous_revision=364,revision=365,updated_at=c["updated_at"],updated_by="codex:/root")
expected["work_in_progress"].update(copy.deepcopy(facts["work_in_progress"]))
expected["work_in_progress"].update(r365_registered_failure_count=923,r365_highest_observed_diagnostic_ordinal_at_cutoff=925,r365_next_failure_ordinal_at_cutoff=926,mu_sdk_r365_facts_ref=pin(C/"checkpoint.execution.facts.json"),later_diagnostics_observed_after_cutoff=[],root_next_failure_ordinal_live=926)
expected["work_in_progress"]["construction_active_parents"]=["W05","W09"]
expected["workers"].append(copy.deepcopy(facts["w09_scope_registration"]["worker"]));expected["note"]=facts["checkpoint_note"]
encode=lambda x:(json.dumps(x,ensure_ascii=False,indent=2)+"\n").encode()
ck("independent-entire-CP-after-reconstruction",encode(expected)==after[0])
expected_o=copy.deepcopy(o0);expected_o["card_path_bindings"]["W09-99"]["subtasks"]["c19_fixture_producer"]=copy.deepcopy(facts["w09_scope_registration"]["owner_subtask"])
expected_o.update(revision=169,updated_at=c["updated_at"],updated_by="codex:/root")
ck("independent-entire-OW-after-reconstruction",encode(expected_o)==after[1])
ck("counts-cutoff923high925next926",len(c["failure_counters"])==923 and [x["original_payload"]["observed_ordinal"] for x in c["failure_counters"][900:]]==list(range(903,926)) and c["work_in_progress"]["root_next_failure_ordinal_live"]==926)
ck("unique-C19-Rootworker",len([x for x in c["workers"] if x.get("step_id")=="W09-99" and x.get("slice_id")=="C19_FIXTURE_PRODUCER"])==1 and c["workers"][-1]["owner"]=="codex:/root")
for ref in facts["canonical_refs"][2:]:verify(ref)
scope=verify(facts["w09_scope_registration"]["scope_ref"])
ck("scope-child-exact",o["card_path_bindings"]["W09-99"]["subtasks"]["c19_fixture_producer"]["scope_ref"]==scope)
guards=[]
for label,p in (("writer",C/"source_guard.cleanup.actual.json"),("vector",S/"vector-source-guard.cleanup.actual.json")):
 add(p);g=read(p)
 ck(label+"-guard-closed",g["attempted"] and g["verification"]=="PASSED" and g["closed"] and not g["errors"] and g["failure"] is None and g["retained_handles_count"]==0)
 for i,e in enumerate(g["entries"]):ck(label+"-entry:"+str(i),e["verified"] and e["final_path_match"] and e["closed"])
 guards.append(dict(label=label,ref=pin(p),entries=len(g["entries"]),closed=True,retained=0))
vref=verify(dict(path=str(S/"canonical-input-vector.json"),sha256="05c7b62168defe85694b3895988362ade9a53bcd2ef0b95178f68cbb641cf77b",bytes=983));v=read(vref["path"])
ck("vector-exact-four-current",v["schema"]=="researchos.w09-c19-canonical-input-vector.v1" and v["checkpoint_revision"]==365 and v["refs"]==commit["after_refs"]+facts["canonical_refs"][2:])
for ref in v["refs"]:verify(ref)
vg=read(S/"vector-source-guard.cleanup.actual.json")
ck("vector-held-canonical-set",[dict(path=e["path"],sha256=e["sha256"],bytes=e["bytes"]) for e in vg["entries"][:4]]==v["refs"])
resume=read(h["resume_ref"]["path"]);ck("resume-actual-pins-counts",resume["checkpoint_ref"]==pair["checkpoint_ref"] and resume["checkpoint_revision"]==365 and resume["ownership_revision"]==169 and resume["registered_failures"]==923 and resume["current_formal_accepted"]==0 and resume["financial_closed"] is False)
ck("no-formal-elevation",h["formal_acceptance"] is False and pair["formal_acceptance"] is False and c["work_in_progress"]["mu_sdk_r365"]["W09_C19"]["formal_increment"]==0)
prior=B/"checkpoint_r365_independent_source_review_codex/cp365r-20261009-source-review/HDF.json"
verify(io["source_independent_review_ref"]);ck("Source-gate-reused",read(prior)["status"]=="CP365_OW169_SOURCE_GATE_ACCEPTED_PENDING_ROOT_ACTUAL")
for ref in inputs.values():ck("postpin:"+ref["path"],pin(ref["path"])==ref)
save("input-pins.json",list(inputs.values()));save("checks.json",dict(count=len(checks),all_passed=all(x["passed"] for x in checks),checks=checks));save("guard-summary.json",guards)
save("result.json",dict(status="CP365_OW169_ACTUAL_CONSISTENCY_ACCEPTED_ADMIN_ONLY",checks=len(checks),inputs=len(inputs),checkpoint_ref=pair["checkpoint_ref"],ownership_ref=pair["ownership_ref"],vector_ref=vref,guards=guards,new_failures=[],formal_acceptance=False,reviewer_actual_execution=False))
assert all(x["passed"] for x in checks),[x for x in checks if not x["passed"]]
print(json.dumps(dict(status="CP365_OW169_ACTUAL_CONSISTENCY_ACCEPTED_ADMIN_ONLY",checks=len(checks),inputs=len(inputs),guards=guards),ensure_ascii=False))

