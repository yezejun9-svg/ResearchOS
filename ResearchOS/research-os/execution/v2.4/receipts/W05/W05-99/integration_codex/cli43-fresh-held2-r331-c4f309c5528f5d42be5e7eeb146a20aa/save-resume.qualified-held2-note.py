"""Additive note after independent actual qualification; grants preparation only."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,hashlib
ROOT=Path(r"D:\作品集\ResearchOS\research-os");OUT=Path(__file__).absolute().parent
BASE=ROOT/"execution/v2.4/receipts/W05/W05-99";PEER=BASE/"cli43_successful_execution_independent_review_codex/6f07498ca19a49c7866b9e528d401aa0"
def pin(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def read(p):return json.loads(p.read_bytes())
def save(n,v):
 with (OUT/n).open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+"\n").encode())
expected={"review.json":"2d50355615924976b526aae4b3932c9f3b9d491b9da277ef833c36151a4b482a","qualification.json":"b4756653eaa85825f7ec0f787ae3970c9462694439dca6440ee791fb3dc93efe","manifest.json":"f54787dfafdb645d8e88a866f43e020dfc6f62d8475d84cd71002ba6c7238b90","handoff.json":"bb3a32c797620f3260fb28807534059c18e46d6f419cbedd55bf62cb97423327"}
refs={n:pin(PEER/n) for n in expected}
assert all(refs[n]["sha256"]==sha for n,sha in expected.items())
review=read(PEER/"review.json");assert review["decision"]=="CURRENT43_FRESH_HELD2_BOUNDED_QUALIFICATION_EVIDENCE_CLOSED"
closed=read(OUT/"root-launch.outer-completion.json")
for r in closed["canonical_refs_at_completion"]:assert pin(Path(r["path"]))==r
cp=read(ROOT/"execution/v2.4/checkpoint.json");ow=read(ROOT/"execution/v2.4/path_ownership.json");assert [cp["revision"],ow["revision"],len(cp["failure_counters"])]==[331,159,509]
save("RESUME.qualified-held2.note.json",{"schema":"researchos.independent-held2-resume-note.v1","actor":"codex:/root","current_tuple":[331,159,509],"known_observed_origins":511,"known_unregistered_distinct_origins":2,"prior_resume_snapshot_ref":pin(OUT/"RESUME.actual-execution.v2.snapshot.json"),"independent_qualification_refs":refs,"independent_actual_decision":review["decision"],"exact_two_cases_qualified":True,"Desktop15_new_Root_scope_preparation_allowed":True,"Desktop_execution_authorized":False,"complete_current43_source_acceptance":False,"current_formal_acceptance":"0/42","all22parents_effective_acceptance_incomplete":True,"source_or_formal_increment":0,"next":"Review Desktop15 new machine gate proposals; stage new independent Root scope with exact15 and future58/169/GUI checks. Preserve original43 sourceimport proof. F08 Root producer source review remains pending.","next_fixed_origin_cut_ref":pin(OUT/"late-origins.capture.for-next-r332.json"),"F08_SQL24_I17_actual_qualification":"OPEN","counter_reset":False,"original_receipts_or_previous_snapshots_modified":False})
save("RESUME.qualified-held2.note.manifest.json",{"self_excluded":True,"entries":[pin(OUT/"RESUME.qualified-held2.note.json"),pin(__file__)]})
print(json.dumps({"note_ref":pin(OUT/"RESUME.qualified-held2.note.json"),"manifest_ref":pin(OUT/"RESUME.qualified-held2.note.manifest.json"),"formal_increment":0},ensure_ascii=False))
