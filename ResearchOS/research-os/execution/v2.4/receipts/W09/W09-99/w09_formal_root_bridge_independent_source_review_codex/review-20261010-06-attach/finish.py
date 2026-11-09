from pathlib import Path
import hashlib,json,types
R=Path(r"D:\作品集\ResearchOS\research-os");O=Path(__file__).parent
S=R/"execution/v2.4/receipts/W09/W09-99/w09_formal_root_bridge_source_codex/bridge-20261010-06"
A=Path(r"C:\Users\yqyyds\.codex\sessions\2026\10\09\rollout-2026-10-09T08-25-26-01a11e0c-eef6-7363-a5b1-da61d6ae7f4c.jsonl")
G=R/"execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py"
def sha(b):return hashlib.sha256(b).hexdigest()
def pin(p):
    p=Path(p);b=p.read_bytes();return dict(path=str(p),sha256=sha(b),bytes=len(b))
def save(n,v,raw=False):
    p=O/n
    with p.open("xb") as f:f.write(v if raw else (json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode())
    return pin(p)
def verify(ref):
    b=Path(ref["path"]).read_bytes()
    assert sha(b)==ref["sha256"] and len(b)==ref["bytes"]
    return b
# Capture the known failed tool result by exact chunk and its matching call, not a guessed input string.
rows=[]
with A.open("rb") as f:
    while True:
        off=f.tell();line=f.readline()
        if not line:break
        rows.append((off,line,json.loads(line)))
results=[]
for item in rows:
    doc=item[2];p=doc.get("payload",{})
    if doc.get("type")!="response_item" or p.get("type") not in ("custom_tool_call_output","function_call_output"):continue
    for block in p.get("output",[]):
        if type(block) is not dict:continue
        try:value=json.loads(block.get("text",""))
        except ValueError:continue
        if type(value) is dict and value.get("chunk_id")=="c50cd4":results.append((item,value))
assert len(results)==1
result,tool=results[0]
assert tool["exit_code"]==1 and "ROOT_PYTHON_EXIT=1" in tool["output"] and "AssertionError: source_build_actual_0" in tool["output"]
call_id=result[2]["payload"]["call_id"]
calls=[x for x in rows if x[2].get("type")=="response_item" and x[2].get("payload",{}).get("type") in ("custom_tool_call","function_call") and x[2]["payload"].get("call_id")==call_id]
assert len(calls)==1
call=calls[0]
hosts=[x for x in rows if call[2]["ordinal"]<x[2]["ordinal"]<result[2]["ordinal"] and x[2].get("type")=="event_msg" and x[2].get("payload",{}).get("item",{}).get("type")=="CommandExecution"]
assert len(hosts)==1 and hosts[0][2]["payload"]["item"]["exit_code"]==1
host=hosts[0];triple=[rows[0],call,result]
raw_ref=save("original-1191.raw.jsonl",b"".join(x[1] for x in triple),True)
host_ref=save("original-1191.host-event.jsonl",host[1],True)
diag=save("original-1191.binding.json",dict(schema="researchos.w09-resource-readonly-host-binding.v1",
    actor_id="/root/attach_restore_independent_review",actor_thread_id=rows[0][2]["payload"]["id"],
    source_audit_path=str(A),source_prefix_size_observed=A.stat().st_size,
    source_line_offsets=[x[0] for x in triple],original_line_sha256=[sha(x[1]) for x in triple],
    original_line_bytes=[len(x[1]) for x in triple],original_raw_ref=raw_ref,
    actual_call_id=call_id,actual_chunk_id="c50cd4",host_event_ref=host_ref,
    host_event_offset=host[0],host_event_ordinal=host[2]["ordinal"],original_ordinal=1191,
    actual_outer_exit=1,actual_python_exit=1,actual_native_exit=None,actual_go_exit=None,
    actual_sql_exit=None,actual_dispatcher_exit=None,actual_model_exit=None,actual_TP_exit=None,
    product_calls=0,execution_grant=False,formal_acceptance=False,
    classification="REVIEWER_CASE_SENSITIVE_MARKER_ASSERTION_ERROR",
    actual_Source_marker="Python_exit=0",mistaken_reviewer_marker="PYTHON_EXIT=0",
    Source_build_failed=False,successful_checks_rerun=False))
prefix=json.loads((O/"independent-checks.json").read_bytes())
assert prefix["passed"]==24 and prefix["count"]==25 and prefix["failure"]["message"]=="source_build_actual_0"
assert all(x["passed"] for x in prefix["checks"][:24]) and prefix["checks"][24]["passed"] is False
prior_closed=json.loads((O/"source-guard.closed.json").read_bytes())
assert prior_closed["closed"] and prior_closed["retained_handles_count"]==0 and prior_closed["errors"]==[]
h=json.loads((S/"HDF.json").read_bytes())
assert pin(S/"HDF.json")["sha256"]=="0fda15ff927c164aca24e27a1ef92691f5a81e20838ac263a25fbcb0c9be265d"
refs=[pin(S/"HDF.json"),pin(S/"MF.json"),h["root_calling_contract_ref"],h["source_ref"],
    h["consumer_launcher_ref"],h["actual_source_build_host"]["raw_ref"],h["actual_source_build_host"]["binding_ref"]]
graw=G.read_bytes();assert sha(graw)=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85"
gm=types.ModuleType("br6_tail_guard");exec(compile(graw,str(G),"exec"),gm.__dict__);guard=gm.SourceReadGuard()
tail=[]
try:
    guard.acquire(refs)
    lines=guard.get_buffer(h["actual_source_build_host"]["raw_ref"]["path"]).splitlines()
    binding=json.loads(guard.get_buffer(h["actual_source_build_host"]["binding_ref"]["path"]))
    output=json.loads(lines[-1])["payload"]["output"]
    actual=[]
    for block in output:
        try:v=json.loads(block.get("text",""))
        except ValueError:continue
        if type(v) is dict and v.get("chunk_id")=="dcc9e2":actual.append(v)
    assert len(actual)==1
    actual=actual[0]
    assert actual["exit_code"]==binding["actual_outer_exit"]==binding["actual_python_exit"]==0
    assert "Python_exit=0" in actual["output"].splitlines()
    tail.append(dict(name="actual_Source_exit_from_observed_host_and_literal_marker",passed=True,
        actual_chunk_id="dcc9e2",actual_outer_exit=0,actual_python_exit=0,
        observed_marker="Python_exit=0",corrects_failed_check_index=24,original_failure_ref=diag))
    c=json.loads(guard.get_buffer(h["root_calling_contract_ref"]["path"]))
    assert c["source_ref"]==h["source_ref"] and c["consumer_launcher_ref"]==h["consumer_launcher_ref"]
    assert c["source_author_backend"]=="/root/full_w09_source_review" and c["verifier_backend"]=="/root/backup_regression_resources"
    tail.append(dict(name="calling_contract_exact_source_and_actor",passed=True))
finally:
    closed=guard.close();save("tail-source-guard.closed.json",closed)
assert closed["closed"] and closed["retained_handles_count"]==0 and not closed["errors"]
tail_ref=save("tail-checks.json",dict(schema="researchos.w09-br6-review-tail-checks.v1",
    checks=tail,passed=len(tail),count=len(tail),original_prefix_checks_ref=pin(O/"independent-checks.json"),
    successful_prefix_reused=24,successful_prefix_rerun=False,original_failed_check_retained=True,
    source_guard_ref=pin(O/"tail-source-guard.closed.json"),actual_Root_stages=0,live_Canon_readlocks=0))
report=save("review-report.json",dict(schema="researchos.w09-br6-independent-source-review.v1",
    reviewer_id="/root/attach_restore_independent_review",reviewed_author="/root/full_w09_source_review",
    review_scope="BR5 history boundary plus BR6 alias remediation; historical Attach BR3 contribution disclosed, not newly self-certified.",
    decision="ACCEPTED_SOURCE_ONLY",closed_findings=["BR5-HISTORICAL-CANON-ALIAS-001"],findings=[],
    source_hdf_ref=pin(S/"HDF.json"),source_mf_ref=pin(S/"MF.json"),source_ref=h["source_ref"],
    independent_checks_ref=pin(O/"independent-checks.json"),tail_checks_ref=tail_ref,
    validation="24 successful initial checks reused; failed case-sensitive marker assertion retained; 2 tail checks pass using observed Source marker and exact contract.",
    source_guard_refs=[pin(O/"source-guard.closed.json"),pin(O/"tail-source-guard.closed.json")],
    new_original_diagnostic_ref=diag,original1190_preserved=h["original1190_io"],
    original1185_preserved=h["original1185_io_preserved"],original1186_1187_1188_preserved=True,
    source_controls_reused=22,BR5_controls_reused=36,old_controls_rerun=False,
    Source_build_actual_outer_exit=0,Source_build_actual_python_exit=0,
    actual_Root_stages=0,actual_Main_Native_Go_SQL_TP_model_calls=0,
    Main_Canon_Scope_written=False,live_Canon_readlocks=0,formal_acceptance=False,execution_grant=False,STOP=True))
decision=save("review-decision.json",dict(schema="researchos.w09-bridge-independent-source-review.v1",
    reviewer_id="/root/attach_restore_independent_review",actor_role="INDEPENDENT_NON_AUTHOR_OF_REVIEWED_DELTA",
    source_ref=h["source_ref"],consumer_launcher_ref=h["consumer_launcher_ref"],
    source_hdf_ref=pin(S/"HDF.json"),source_mf_ref=pin(S/"MF.json"),
    decision="ACCEPTED_SOURCE_ONLY",formal_acceptance=False,execution_grant=False,
    closed_findings=["BR5-HISTORICAL-CANON-ALIAS-001"],findings=[],report_ref=report))
members=[pin(p) for p in sorted(O.iterdir()) if p.is_file() and p.name not in ("HDF.json","MF.json","postseal-tool-io.json")]
mf=save("MF.json",dict(schema="researchos.w09-independent-source-review-manifest.v1",members=members,exclusions=["HDF.json","MF.json","postseal-tool-io.json"]))
hf=save("HDF.json",dict(schema="researchos.w09-independent-source-review-handoff.v1",
    reviewer_id="/root/attach_restore_independent_review",reviewed_author="/root/full_w09_source_review",
    decision="ACCEPTED_SOURCE_ONLY",source_hdf_ref=pin(S/"HDF.json"),source_mf_ref=pin(S/"MF.json"),
    source_ref=h["source_ref"],consumer_launcher_ref=h["consumer_launcher_ref"],
    decision_ref=decision,report_ref=report,manifest_ref=mf,
    independent_checks_ref=pin(O/"independent-checks.json"),tail_checks_ref=tail_ref,
    independent_successful_initial_checks=24,independent_successful_tail_checks=2,
    original_failed_check_preserved=True,new_original_diagnostics=[1191],original_diagnostic_ref=diag,
    source_guard_refs=[pin(O/"source-guard.closed.json"),pin(O/"tail-source-guard.closed.json")],
    guards_closed_zero=True,retained_handles_count=0,live_Canon_readlocks=0,
    closed_findings=["BR5-HISTORICAL-CANON-ALIAS-001"],author_controls_reused=22,BR5_controls_reused=36,
    successful_controls_rerun=False,actual_Root_stages=0,actual_Main_Native_Go_SQL_TP_model_calls=0,
    Main_Canon_Scope_written=False,formal_acceptance=False,parent_acceptance=False,execution_grant=False,
    actual_product_exits={k:None for k in ("Native","Go","SQL","dispatcher","model","TP")},STOP=True))
for ref in members:verify(ref)
print(json.dumps(dict(HDF=hf,MF=mf,decision=decision,report=report,
    verdict="ACCEPTED_SOURCE_ONLY",guard_closed=True,retained_handles_count=0,original1191=diag),ensure_ascii=False))

