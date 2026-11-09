"""Root fixed two-origin late cut for the next independent scope; metadata only."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,hashlib
ROOT=Path(r"D:\作品集\ResearchOS\research-os");OUT=Path(__file__).absolute().parent
SPECS=[
("execution/v2.4/receipts/W09/W09-99/w09_controller_revision_independent_review_codex/bd6b0994244f4676a3c3a2be8ef3661a/coordination-failure-origin.json","21eb69a5dcc61a1f6ea23ca7ef9075a4e9f3b928ea409643671b263ea713161f"),
("execution/v2.4/receipts/W05/W05-99/cli43_successful_execution_independent_review_codex/6f07498ca19a49c7866b9e528d401aa0/failure-origin.61653a.json","35b6490d2158d5bccc5f9d78d807c90a4a66d9cc61ad79b3010877363cf6e6bf")]
def pin(p):
 b=p.read_bytes();return {"path":p.relative_to(ROOT).as_posix(),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def read(p):return json.loads(p.read_bytes())
def save(n,v):
 with (OUT/n).open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+"\n").encode())
assert sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode
cp=read(ROOT/"execution/v2.4/checkpoint.json");ow=read(ROOT/"execution/v2.4/path_ownership.json")
assert [cp["revision"],ow["revision"],len(cp["failure_counters"])]==[331,159,509]
closed=read(OUT/"root-launch.outer-completion.json")
for r in closed["canonical_refs_at_completion"]:
 actual=pin(Path(r["path"]));assert (actual["sha256"],actual["bytes"])==(r["sha256"],r["bytes"])
origins=[]
for rel,sha in SPECS:
 p=ROOT/rel;ref=pin(p);assert ref["sha256"]==sha
 assert not any(old.get("evidence_ref",{}).get("sha256")==sha for old in cp["failure_counters"])
 origins.append({"evidence_ref":ref,"original_payload":read(p),"classification":"LATE_DISTINCT_ORIGINAL_FAILURE_NULL_AND_PROPAGATION_PRESERVED","counter_reset":False,"automatic_same_input_retry":False})
assert len(origins)==len({r["evidence_ref"]["sha256"] for r in origins})==2
cut={"schema":"researchos.root-late-origin-cut.v1","actor":"codex:/root","before":[331,159,509],"after":[332,160,511],"registered_origin_count":509,"captured_late_origin_count":2,"fixed_cut_observed_origin_count":511,"observed_including_later_pending_at_capture":511,"origins":origins,"native_NULL_and_original_payloads_preserved":True,"nested_exit_propagations_counted_once":True,"new_later_origins_not_added_to_this_fixed_cut":True,"canonical_writes":0,"automatic_retry":False,"counter_reset":False,"formal_increment":0}
save("late-origins.capture.for-next-r332.json",cut)
print(json.dumps({"capture_ref":pin(OUT/"late-origins.capture.for-next-r332.json"),"before":cut["before"],"after":cut["after"],"canonical_writes":0,"formal_increment":0},ensure_ascii=False))
