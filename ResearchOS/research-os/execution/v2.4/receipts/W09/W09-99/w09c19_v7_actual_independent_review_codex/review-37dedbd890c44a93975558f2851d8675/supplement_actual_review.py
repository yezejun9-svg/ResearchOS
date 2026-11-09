from pathlib import Path
import ast,json,hashlib
O=Path(__file__).resolve().parent
R=O.parents[6]
def pin(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def save(n,d): (O/n).write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding="utf-8")
def read(ref):
 p=Path(ref["path"]);assert pin(p)==ref;return p.read_bytes()
packet=json.loads((O/"native-packet.public-index.json.input.json").read_bytes());T=Path(packet["consumer_source_root"])
report=json.loads(read(packet["original_report_ref"]));tool=json.loads(read(packet["original_tool_run_ref"]))
source=T/"ops/ci/w09_evidence_closure.py";sr=pin(source);assert sr["sha256"]=="1cc37f4fec48d2e2bae39db3c1f8d1da9fdfe6bd788a44396ea0a8b877be6777" and sr["bytes"]==42716
nodes=[x for x in ast.parse(source.read_bytes()).body if isinstance(x,ast.FunctionDef) and x.name in {"require","_go_assertions"}];assert len(nodes)==2
unit=ast.Module(body=nodes,type_ignores=[]);ns={"json":json};exec(compile(unit,str(source),"exec"),ns)
stdout=T/tool["stdout_ref"];events=[json.loads(line) for line in stdout.read_text(encoding="utf-8").splitlines()]
actual=ns["_go_assertions"](events,report["selected_tests"],tool["stdout_ref"]);assert actual==report["assertion_results"] and len(actual)==5 and all(x["run_id"]==report["run_id"] and x["status"]=="PASS" for x in actual)
streams={};trace=[]
for index,event in enumerate(events):
 owner=(event.get("Package"),event.get("Test"));output=event.get("Output","")
 if not output:continue
 entry=streams.setdefault(owner,{"buffer":"","indices":[],"chunks":[]});entry["buffer"]+=output;entry["indices"].append(index);entry["chunks"].append(output)
 while "\n" in entry["buffer"]:
  line,tail=entry["buffer"].split("\n",1)
  if line.startswith("W09_ASSERTION "):
   raw=json.loads(line[len("W09_ASSERTION "):]);assert raw["test_name"]==owner[1]
   trace.append({"assertion_id":raw["assertion_id"],"Package":owner[0],"Test":owner[1],"event_indices_zero_based":list(entry["indices"]),"Output_chunks":list(entry["chunks"]),"complete_line":line+"\n","payload":raw})
  entry["buffer"]=tail;entry["indices"]=[] if not tail else [index];entry["chunks"]=[] if not tail else [tail]
assert all(not v["buffer"] for v in streams.values()) and len(trace)==5
reconstructed=[dict(x["payload"],raw_evidence_reference=tool["stdout_ref"]) for x in trace];assert reconstructed==actual
fragments=[x for x in trace if len(x["event_indices_zero_based"])>1];assert fragments
save("actual-v7-fragment-replay.json",{"decision":"PASS","scope":"PURE_AST_PARSER_ON_ACTUAL_STDOUT_ONLY","consumer_executed":False,"source_ref":sr,"extracted_functions":[{"name":x.name,"line":x.lineno,"end_line":x.end_lineno} for x in nodes],"stdout_ref":pin(stdout),"report_ref":packet["original_report_ref"],"run_id":report["run_id"],"actual_record_count":len(actual),"all_exactly_equal_report":True,"dangling_streams":0,"fragmented_assertion_ids":[x["assertion_id"] for x in fragments],"records":trace})
closures=json.loads((O/"closure-and-root-io.read.json").read_bytes());guardrefs={};groups=[]
for row in closures:
 d=json.loads(read(row["ref"]))
 if "entries" not in d:continue
 for entry in d["entries"]:
  ref={k:entry[k] for k in ("path","sha256","bytes")};read(ref)
  if ref["path"] in guardrefs: assert ref==guardrefs[ref["path"]]
  guardrefs[ref["path"]]=ref
 groups.append({"ref":row["ref"],"entries":len(d["entries"]),"closed":d["closed"],"live_pins_verified":True})
inputs=json.loads((O/"producer-inputs.read.json").read_bytes());overlay=next(x["document"] for x in inputs if x["key"]=="source-overlay");members=next(x["document"] for x in inputs if x["key"]=="exact-source-members")
expected=[]
for rel,ref in overlay["sources"].items():
 p=T/rel;assert read(ref)==p.read_bytes();expected.append(pin(p))
assert members==expected and len(expected)==6
for ref in overlay["independent_source_reviews"]:read(ref)
assert len(report["version_manifest"]["source_sha256"])==21
save("runtime-guard-and-overlay.live-verification.json",{"decision":"PASS","guard_groups":groups,"unique_refs":list(guardrefs.values()),"unique_ref_count":len(guardrefs),"guard_entry_count":sum(x["entries"] for x in groups),"exact_six_source_members":members,"review_refs":overlay["independent_source_reviews"],"all_current_refs_match_held_refs":True,"reviewer_runtime_execution":False,"fresh_guard_contention_test":False})
print(json.dumps({"parser":"PASS","actual_assertions":len(actual),"fragmented_ids":[x["assertion_id"] for x in fragments],"guards":len(groups),"guard_entries":sum(x["entries"] for x in groups),"unique_guard_live_pins":len(guardrefs),"consumer_readiness":"QUALIFIED_PENDING_ROOT_ACTUAL_CONSUMPTION"}))
