"""Root fixed capture of six distinct late origins; pure metadata IO, no canonical mutation."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import hashlib,json
ROOT=Path(r"D:\作品集\ResearchOS\research-os")
BASE=ROOT/"execution/v2.4/receipts/W05/W05-99"
OUT=Path(__file__).absolute().parent
SPECS=[
ROOT/"execution/v2.4/receipts/W05/W05-99/integration_codex/cli43-fresh-held2-r329-246c20b781664b0e80fae7fd29b9b2b4/failure-origin.task-packet-path-guess.json",
OUT/"failure-origin.c873de.json",
OUT/"failure-origin.collaboration-thread-limit.json",
ROOT/"execution/v2.4/receipts/W09/W09-99/f08_controller_independent_review_codex/d16a4b150b4e4fa9836f852c4a2bc505/failure-origins.json",
BASE/"cli43_fresh_compiler_executor_codex/b802270f725f47dc86f9ec829a60931a/failure.origin.json",
OUT/"failure-origin.abe282.json"]
def need(v,m):
 if not v:raise RuntimeError(m)
def pin(p):
 raw=p.read_bytes();return {"path":p.relative_to(ROOT).as_posix(),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def doc(p):return json.loads(p.read_bytes())
def save(p,v):
 with p.open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+"\n").encode())
need(sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode,"isolated metadata")
cp=doc(ROOT/"execution/v2.4/checkpoint.json");ow=doc(ROOT/"execution/v2.4/path_ownership.json")
need([cp["revision"],ow["revision"],len(cp["failure_counters"])]==[330,158,502],"actual before tuple")
closed=doc(OUT/"root-launch.outer-completion.json")
for row in closed["canonical_refs_at_completion"]:
 actual=pin(Path(row["path"]));need(actual["sha256"]==row["sha256"] and actual["bytes"]==row["bytes"],"canonical actual closure guard")
origins=[]
for p in SPECS:
 ref=pin(p);payload=doc(p)
 need(all(old.get("evidence_ref",{}).get("sha256")!=ref["sha256"] for old in cp["failure_counters"]),"already registered")
 origins.append({"evidence_ref":ref,"original_payload":payload,"classification":"LATE_DISTINCT_ORIGINAL_FAILURE_NULL_AND_PROPAGATION_PRESERVED","counter_reset":False,"automatic_same_input_retry":False})
need(len(origins)==6 and len({r["evidence_ref"]["sha256"] for r in origins})==6,"exact distinct cut")
need(origins[3]["original_payload"]["new_failed_tool_invocations"]==1 and len(origins[3]["original_payload"]["origin_records"])==1 and origins[3]["original_payload"]["origin_records"][0]["actual_native_exit"] is None,"W09 one pre-create failure only, native NULL")
need(origins[4]["original_payload"]["stage"]=="case-01" and origins[4]["original_payload"]["native_exit"] is None,"one r330 case underlying, stage native NULL")
need(origins[5]["original_payload"]["outer_exit_code"]==1 and origins[5]["original_payload"]["actual_native_exit"] is None,"read path original native NULL")
peer=BASE/"cli43_failed_execution_independent_review_codex/b33d80b428a247539130e8585e85f3c7/review.json"
need(pin(peer)["sha256"]=="526b392eca9f7e5b84d67537aac9d7d132e074b7e02868213bf73e6a4b01bf75","actual failed independent closure")
need(doc(peer)["decision"]=="ACTUAL_FAILED_EXECUTION_EVIDENCE_CLOSED_QUALIFICATION_WITHHELD","failed no acceptance")
cut={"schema":"researchos.root-late-origin-cut.v1","actor":"codex:/root","before":[330,158,502],"after":[331,159,508],"registered_origin_count":502,"captured_late_origin_count":6,"fixed_cut_observed_origin_count":508,"observed_including_later_pending_at_capture":508,"origins":origins,"prior_root_closed_manifest_ref":pin(OUT/"root-launch.closed.manifest.json"),"prior_actual_failed_independent_review_ref":pin(peer),"native_NULL_and_original_payloads_preserved":True,"nested_exit_propagations_counted_once":True,"nonterminating_outer_zero_diagnostics_preserved":True,"canonical_writes":0,"automatic_retry":False,"counter_reset":False,"formal_increment":0}
save(OUT/"late-origins.capture.for-r331.json",cut)
print(json.dumps({"capture_ref":pin(OUT/"late-origins.capture.for-r331.json"),"before":cut["before"],"after":cut["after"],"captured_late_origins":6,"canonical_unchanged":True},ensure_ascii=False))
