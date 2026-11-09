from pathlib import Path
import json,hashlib
from datetime import datetime,timezone
O=Path(__file__).resolve().parent
R=Path("D:/作品集/ResearchOS/research-os")
def pin(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def read(ref):
 p=Path(ref["path"]);b=p.read_bytes();assert hashlib.sha256(b).hexdigest()==ref["sha256"] and len(b)==ref["bytes"];return b
def save(n,d):
 p=O/n;assert not p.exists();p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding="utf-8");return pin(p)
A=R/"execution/v2.4/receipts/W09/W09-99/integration_codex/w09c19v7-producer-1a11f30"
rootref={"path":str(A/"postseal-root-producer.original-tool-results.json"),"sha256":"f9a1602799f7487e80650bdd0758ccd601bb2834079de75182bcd356cf9e899f","bytes":5362}
raw=read(rootref);root=json.loads(raw);assert root["result_only"] is True and len(root["records"])==4
results={x["result"]["chunk_id"]:x for x in root["records"]};assert set(results)=={"7b5b34","6444d0","bc4ba4","868a4b"}
assert results["7b5b34"]["result"]["session_id"]==81639 and results["bc4ba4"]["result"]["session_id"]==14737
for final in ["6444d0","868a4b"]:assert results[final]["result"]["exit_code"]==0 and "ROOT_PYTHON_EXIT=0" in results[final]["result"]["output"]
refs=[]
for row in root["records"]:
 for line in row["result"]["output"].splitlines():
  if not line.startswith("{"):continue
  d=json.loads(line)
  for key in ["receipt_ref","ready_ref","closed_ref"]:
   if key in d:read(d[key]);refs.append(d[key])
assert len(refs)==10
(O/"root-original-tool-results.input.json").write_bytes(raw)
save("root-original-tool-results.verification.json",{"decision":"PASS","source_ref":rootref,"result_only":True,"original_args_not_archived_here":True,"no_reconstructed_args_claimed_original":True,"chunks":list(results),"sessions":[81639,14737],"final_outer_exits":[0,0],"explicit_Root_Python_exits":[0,0],"public_result_refs_verified":refs,"native_exit_basis":"Original report plus native-tool-run and original 8 owned invocation receipts; not inferred from Root Python exit."})
checks=json.loads((O/"checks.json").read_bytes());p=json.loads((O/"native-packet.public-index.json.input.json").read_bytes());r=json.loads(read(p["original_report_ref"]));t=json.loads(read(p["original_tool_run_ref"]));T=Path(p["consumer_source_root"])
copies=json.loads((O/"candidate-copy-provenance.json").read_bytes())["copies"]
for x in copies:assert read(x["original_ref"])==read(x["candidate_copy_ref"])
sourcepins=[]
for rel,digest in r["version_manifest"]["source_sha256"].items():
 ref=pin(T/rel);assert "sha256:"+ref["sha256"]==digest;sourcepins.append(ref)
inputs=json.loads((O/"producer-inputs.read.json").read_bytes());canonical=next(x["document"] for x in inputs if x["key"]=="canonical-pre")
for ref in canonical["refs"]:read(ref)
mode=json.loads(read(copies[0]["original_ref"]));decisions=[json.loads(read(x["original_ref"])) for x in copies[1:]]
assert [d["route"] for d in decisions]==[["test.research.fixture","W09","","C19"],["test.retrieval","W09","","C19"]]
for d in decisions:
 assert d["decision"]==mode["decision"]=="QUALIFIED" and d["run_id"]==mode["run_id"]==r["run_id"]
 assert d["source_sha256"]==mode["source_sha256"]==r["version_manifest"]["source_sha256"] and d["go_executable"]==mode["go_executable"]==r["go_executable"]
 assert d["report_ref"]==t["report_ref"] and d["report_sha256"]==p["original_report_ref"]["sha256"]==mode["report_sha256"] and d["stdout_sha256"]==t["stdout_sha256"]
 assert d["tool_run_sha256"]==p["original_tool_run_ref"]["sha256"] and d["producer_id"]!=d["reviewer_id"]==mode["actor_id"]
 reviewref={**d["independent_review_ref"],"path":str(T/d["independent_review_ref"]["path"])};assert read(reviewref)==read(copies[0]["original_ref"])
 assert not Path(reviewref["path"]).is_relative_to(Path(p["original_report_ref"]["path"]).parent)
review={"schema":"researchos.w09-c19-independent-actual-review.v2","reviewed_at":datetime.now(timezone.utc).isoformat(),"actor_id":"codex:/root/native_temp_independent_review","actor_role":"INDEPENDENT_NON_AUTHOR","decision":"ACTUAL_NATIVE_FIXTURE_QUALIFIED_CURRENT_V7_REPLAY_PASS","actual_fixture_decision":"QUALIFIED","consumer_readiness":"QUALIFIED_PENDING_ROOT_ACTUAL_CONSUMPTION","run_id":r["run_id"],"report_ref":p["original_report_ref"],"native_tool_run_ref":p["original_tool_run_ref"],"actual_evidence":checks["summary"],"checks_ref":pin(O/"checks.json"),"v7_actual_parser_ref":pin(O/"actual-v7-fragment-replay.json"),"runtime_current_ref":pin(O/"runtime-guard-and-overlay.live-verification.json"),"root_original_results_ref":rootref,"root_original_results_verification_ref":pin(O/"root-original-tool-results.verification.json"),"root_original_results_limitation":"result_only archive preserves original returned output strings; original tool arguments remain in the original conversation transcript. Invocation argv and sources were independently checked from original owned receipts and pinned source records; reconstructed argv is not labelled original tool arguments.","source21_current_refs":sourcepins,"canonical_refs_unchanged":canonical["refs"],"mode_review_ref":copies[0]["original_ref"],"mode_decision_refs":[x["original_ref"] for x in copies[1:]],"candidate_copy_provenance_ref":pin(O/"candidate-copy-provenance.json"),"parser_execution_scope":"Only require and _go_assertions AST function definitions executed with actual immutable stdout input. No consumer entrypoint or verification route invoked.","native_exit_evidence":"Original native Go report exit_code=0 and native-tool-run native_exit_code=0; 6 original Git preparation jobs plus compiler list and producer owned primary results=0; Root outer exits are separate evidence.","runtime_verification_scope":"Reviewed original closed guard records and verified finite listed current bytes. No fresh guard contention test or production model call was performed by reviewer.","http_delivery":"132 original IN_PROCESS_HTTptest_RECORDER exchanges bound to owned request/response bytes; no HTTP client or external provider call made by reviewer.","old_v6_qualification_reused":False,"old_v6_packet_and_failure_927_modified":False,"new_original_failures":[],"root_reported_live_next_at_close":942,"pending_external_diagnostics":[937,938,939,940,941],"consumer_executed":False,"new_execution_grant":False,"formal_acceptance":False,"formal_case_accepted_delta":0,"Main_adopted":False,"financial_control_status":"NOT_PROVEN","findings":[],"next":"Root may bind these exact fresh mode packets under existing authorization, perform both actual consumers, and obtain independent consumer review. This review adds no authority."}
save("review.json",review)
save("original-failures.json",{"new_original_failures":[],"original_failures_from_prior_tasks_preserved":True,"failure_927_old_source_not_relabelled":True,"root_reported_pending_diagnostics":[937,938,939,940,941],"root_reported_live_next":942,"new_native_execution":False})
anchors=[x["ref"] for x in inputs]+[x["ref"] for x in json.loads((O/"closure-and-root-io.read.json").read_bytes())]+[rootref,p["original_report_ref"],p["original_tool_run_ref"],*canonical["refs"]]
for ref in anchors:read(ref)
members=[pin(x) for x in sorted(O.iterdir()) if x.is_file() and x.name not in {"MF.json","HDF.json"}]
save("MF.json",{"schema":"researchos.w09-c19-independent-actual-manifest.v1","member_count":len(members),"members":members,"input_anchor_refs":anchors,"verified_deep_input_pins_ref":pin(O/"verified-input-pins.json"),"runtime_live_pins_ref":pin(O/"runtime-guard-and-overlay.live-verification.json"),"candidate_copies":copies,"input_drift":0,"excludes_self_and_handoff":True})
hdf={"schema":"researchos.w09-c19-independent-actual-handoff.v1","actor_id":review["actor_id"],"decision":review["decision"],"actual_fixture_decision":"QUALIFIED","consumer_readiness":review["consumer_readiness"],"review_ref":pin(O/"review.json"),"manifest_ref":pin(O/"MF.json"),"lossless_reconstruction_ref":pin(O/"actual-v7-fragment-replay.json"),"mode_review_ref":copies[0]["original_ref"],"route_specific_decision_refs":[x["original_ref"] for x in copies[1:]],"candidate_copy_refs":[x["candidate_copy_ref"] for x in copies],"candidate_relative_decision_refs":[{**x["original_ref"],"path":x["candidate_relative_path"]} for x in copies[1:]],"original_run_id":r["run_id"],"original_report_ref":p["original_report_ref"],"native_tool_run_ref":p["original_tool_run_ref"],"root_original_result_only_ref":rootref,"original_argv_provenance":"Original arguments remain in Root transcript; source and owned invocation argv independently reviewed; result-only archive is not full IO.","new_failures":[],"root_reported_live_next":942,"formal_acceptance":False,"formal_case_accepted_delta":0,"Main_adopted":False,"execution_grant":False,"consumer_executed":False,"stopped":True}
save("HDF.json",hdf)
for ref in members:read(ref)
for ref in anchors:read(ref)
print(json.dumps({"HDF":pin(O/"HDF.json"),"MF":pin(O/"MF.json"),"review":pin(O/"review.json"),"members":len(members),"anchors":len(anchors),"decisions":hdf["route_specific_decision_refs"],"mode_review":hdf["mode_review_ref"],"new_failures":[]},ensure_ascii=False))
