"""Forward-only seal of the existing partial note plus its original native failure."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,hashlib
ROOT=Path(r"D:\作品集\ResearchOS\research-os");OUT=Path(__file__).absolute().parent
def pin(p):
 p=Path(p).absolute();b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def read(p):return json.loads(Path(p).read_bytes())
def save(n,v):
 with (OUT/n).open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+"\n").encode())
assert sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode
partial=OUT/"RESUME.qualified-held2.note.json";note=read(partial);assert note["independent_actual_decision"]=="CURRENT43_FRESH_HELD2_BOUNDED_QUALIFICATION_EVIDENCE_CLOSED" and note["source_or_formal_increment"]==0
origin=OUT/"failure-origin.4e8b35.json";failure=read(origin);assert failure["outer_exit_code"]==failure["actual_native_exit"]==1 and failure["canonical_writes"]==0
for r in note["independent_qualification_refs"].values():assert pin(r["path"])==r
closed=read(OUT/"root-launch.outer-completion.json")
for r in closed["canonical_refs_at_completion"]:assert pin(r["path"])==r
cp=read(ROOT/"execution/v2.4/checkpoint.json");ow=read(ROOT/"execution/v2.4/path_ownership.json");assert [cp["revision"],ow["revision"],len(cp["failure_counters"])]==[331,159,509]
record={"schema":"researchos.qualified-held2-forward-seal.v1","actor":"codex:/root","current_tuple":[331,159,509],"known_observed_origins_at_seal":512,"unregistered_distinct_origins":3,"partial_original_note_ref":pin(partial),"original_failed_note_writer_ref":pin(OUT/"save-resume.qualified-held2-note.py"),"original_metadata_failure_ref":pin(origin),"partial_original_note_bytes_changed":False,"qualified_actual_CLI_evidence_unchanged":True,"independent_qualification_refs":note["independent_qualification_refs"],"Desktop15_scope_preparation_allowed":True,"Desktop_execution_source_formal_acceptance":False,"current_formal_acceptance":"0/42","all22parents_effective_acceptance_incomplete":True,"next_fixed_two_origin_cut_ref":pin(OUT/"late-origins.capture.for-next-r332.json"),"origin4e8b35_outside_this_fixed_cut":True,"counter_reset":False,"automatic_same_input_retry":False,"canonical_writes":0,"Go_SQL_HTTP_SDK_MODEL_calls":0}
save("RESUME.qualified-held2.forward-note.json",record)
save("RESUME.qualified-held2.forward-note.manifest.json",{"self_excluded":True,"entries":[pin(OUT/"RESUME.qualified-held2.forward-note.json"),pin(partial),pin(origin),pin(OUT/"save-resume.qualified-held2-note.py"),pin(__file__)]})
print(json.dumps({"forward_note_ref":pin(OUT/"RESUME.qualified-held2.forward-note.json"),"manifest_ref":pin(OUT/"RESUME.qualified-held2.forward-note.manifest.json"),"registered":509,"known_observed":512,"formal_increment":0},ensure_ascii=False))
