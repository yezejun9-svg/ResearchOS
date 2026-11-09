from pathlib import Path
import ast,hashlib,json,datetime
R=Path(r"D:\作品集\ResearchOS\research-os")
O=Path(__file__).parent
S=R/"execution/v2.4/receipts/W09/W09-99/w09_formal_root_bridge_source_codex/bridge-20261010-05"
A=Path(r"C:\Users\yqyyds\.codex\sessions\2026\10\09\rollout-2026-10-09T08-25-26-01a11e0c-eef6-7363-a5b1-da61d6ae7f4c.jsonl")
def sha(b):return hashlib.sha256(b).hexdigest()
def pin(p):
    b=Path(p).read_bytes();return dict(path=str(p),sha256=sha(b),bytes=len(b))
def write(n,v,raw=False):
    p=O/n;b=v if raw else (json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode()
    with p.open("xb") as f:f.write(b)
    return pin(p)
entries=[]
with A.open("rb") as f:
    while True:
        at=f.tell();raw=f.readline()
        if not raw:break
        entries.append((at,raw,json.loads(raw)))
header=entries[0]
def exact_diag(ordinal,call_id,host_ordinal,exit_code,python_exit,marker):
    calls=[x for x in entries if x[2].get("type")=="response_item" and x[2].get("payload",{}).get("call_id")==call_id and x[2]["payload"].get("type") in ("function_call","custom_tool_call")]
    outputs=[x for x in entries if x[2].get("type")=="response_item" and x[2].get("payload",{}).get("call_id")==call_id and x[2]["payload"].get("type") in ("function_call_output","custom_tool_call_output")]
    hosts=[x for x in entries if x[2].get("ordinal")==host_ordinal]
    assert len(calls)==len(outputs)==len(hosts)==1
    call,result,host=calls[0],outputs[0],hosts[0]
    assert call[2]["ordinal"]<host_ordinal<result[2]["ordinal"]
    assert marker in str(result[2]["payload"]["output"])
    assert host[2]["payload"]["item"]["type"]=="CommandExecution" and host[2]["payload"]["item"]["exit_code"]==exit_code
    triple=[header,call,result];raw=b"".join(x[1] for x in triple)
    rr=write("original-"+str(ordinal)+".raw.jsonl",raw,True)
    hr=write("original-"+str(ordinal)+".host-event.jsonl",host[1],True)
    binding=dict(schema="researchos.w09-resource-readonly-host-binding.v1",
        actor_id="/root/attach_restore_independent_review",actor_thread_id=header[2]["payload"]["id"],
        source_audit_path=str(A),source_prefix_size_observed=A.stat().st_size,
        source_line_offsets=[x[0] for x in triple],original_line_sha256=[sha(x[1]) for x in triple],
        original_line_bytes=[len(x[1]) for x in triple],original_raw_ref=rr,
        actual_call_id=call_id,host_event_ref=hr,host_event_offset=host[0],host_event_ordinal=host_ordinal,
        original_ordinal=ordinal,actual_outer_exit=exit_code,actual_python_exit=python_exit,
        actual_native_exit=None,actual_go_exit=None,actual_sql_exit=None,actual_dispatcher_exit=None,
        actual_model_exit=None,actual_TP_exit=None,product_calls=0,execution_grant=False,formal_acceptance=False)
    for offset,line in [(x[0],x[1]) for x in triple]+[(host[0],host[1])]:
        with A.open("rb") as f:f.seek(offset);assert f.readline()==line
    return write("original-"+str(ordinal)+".binding.json",binding)
diagnostics=[
exact_diag(1186,"call_e652542ae43245b68229cccdd323b2fb",4070,0,None,"Cannot find path"),
exact_diag(1187,"call_44c8414ebcaa4bc8bc96af0baebea078",4099,0,None,"os error 123"),
exact_diag(1188,"call_eb5a7dafc4294c5582d5d2ffe4252b66",4128,1,1,"ROOT_PYTHON_EXIT=1")]
h=json.loads((S/"HDF.json").read_bytes())
closed=json.loads((O/"source-guard.closed.json").read_bytes())
assert closed["closed"] and closed["retained_handles_count"]==0 and not closed["errors"]
src=(S/"w09_root_bridge.source.py").read_bytes()
assert pin(S/"HDF.json")["sha256"]=="7cac259f230b60c691418b33495f4ae556efc310389e981018163825bce42147"
assert sha(src)==h["source_ref"]["sha256"]=="e9e6aebaa88eb749576be8b68ebdd4fdeb202213111546437153d1d0739836b3"
nodes={n.name:n for n in ast.parse(src).body if isinstance(n,ast.FunctionDef)}
alias=r"D:\作品集\ResearchOS\research-os\execution\v2.4\..\v2.4\checkpoint.json"
finding=dict(id="BR5-HISTORICAL-CANON-ALIAS-001",priority="P2",decision="REQUEST_CHANGES",
    title="Unnormalized paths bypass historical Canon rejection before later physical normalization",
    source_ref=h["source_ref"],
    functions={k:nodes[k].lineno for k in ("canonical_identity","validate_persistent_snapshot","historical_dependency_refs","request_dependency_refs","main")},
    input_reference=dict(path=alias,sha256="f"*64,bytes=10),
    current_reference=dict(path=str(R/"execution/v2.4/checkpoint.json"),sha256="0"*64,bytes=10),
    expected="Reject alias as undeclared historical Canon or reject noncanonical lexical path before any TP skip.",
    actual_observed={"publication_ref":"accepted alias reference","role_registry_input_ref":"accepted alias reference",
      "dependency_snapshot.files":"accepted aliased Canon key","request_dependency_refs":"accepted conflicting alias"},
    evidence_method="These four values satisfied explicit runtime assertions in review.py before its later diagnostic-capture failure at line144; per-case values were not separately serialized before that failure. The exact script, tool call/result and host event are preserved. Successful pure controls were not rerun.",
    actual_control_script_ref=pin(O/"review.py"),actual_control_host_binding_ref=diagnostics[2],
    normalized_target=str(R/"execution/v2.4/checkpoint.json"),
    impact="canonical_identity retains .., while physical resolves .. . An undeclared historical CP/OW alias in a publication reaches the existing activate/publish-registration CP/OW skip without archive proof or pin check. Snapshot exclusion also misses alias keys. Fresh req.current4, SourceReadGuard and TP CAS remain required; this finding does not assert arbitrary current authority bypass.",
    proposed_fix="Reject or normalize equivalent accepted path spellings consistently before Canon classification, snapshot exclusion/refusal, request conflict checks and historical walker checks. Preserve fresh current4 physical checking, exact proposal binding, archive pins, SS/CM equality, lease checks and TP CAS.",
    actual_Root_stages=0,live_Canon_reads=0,live_Canon_readlocks=0)
fr=write("findings.json",[finding])
report=dict(schema="researchos.w09-br5-independent-source-review.v1",reviewer_id="/root/attach_restore_independent_review",
    reviewed_delta_author="/root/full_w09_source_review",
    review_scope="BR5 history/snapshot delta; inherited Attach BR3 contribution disclosed, not newly self-certified.",
    source_hdf_ref=pin(S/"HDF.json"),source_mf_ref=pin(S/"MF.json"),
    source_ref=h["source_ref"],consumer_launcher_ref=h["consumer_launcher_ref"],
    calling_contract_ref=h["root_calling_contract_ref"],
    decision="REQUEST_CHANGES",findings_ref=fr,
    independent_checks_completed_before_packaging_failure=[
      "supplied five source pins and manifest SourceReadGuard",
      "full 12-block inverse to exact BR4 bytes",
      "changed existing functions exactly snapshot/propose/registration/registered/publish_registration/main",
      "unchanged consumer launcher",
      "reuse author 36 controls, no replay",
      "author build/seal guards closed zero",
      "exact-path Canon is refused",
      "four alias edge paths accepted, demonstrating finding",
      "downstream physical resolution before TP Canon skip",
      "233c90 actual original3LF ranges/call id",
      "1185 actual original3LF ranges/call id and outer1 childNULL",
      "independent SourceReadGuard closed zero"],
    evidence_limit="Pre-failure checks were in-process assertions; successful completion is established by reaching diagnostic capture at line144, not by a completed first-run report.",
    source_controls_reused=36,source_controls_rerun=False,successful_independent_controls_rerun=False,
    original1185_raw_ref=h["original1185_io"]["raw_ref"],
    original1185_binding_ref=h["original1185_io"]["binding_ref"],
    new_original_diagnostic_refs=diagnostics,
    source_guard_ref=pin(O/"source-guard.closed.json"),
    actual_Root_stages=0,actual_Main_calls=0,actual_Native_Go_SQL_TP_model_calls=0,live_Canon_readlocks=0,
    Main_Canon_Scope_written=False,execution_grant=False,formal_acceptance=False,STOP=True)
rr=write("review-report.json",report)
decision=write("review-decision.json",dict(schema="researchos.w09-bridge-independent-source-review.v1",
    reviewer_id="/root/attach_restore_independent_review",
    source_ref=h["source_ref"],consumer_launcher_ref=h["consumer_launcher_ref"],
    source_hdf_ref=pin(S/"HDF.json"),source_mf_ref=pin(S/"MF.json"),
    decision="REQUEST_CHANGES",formal_acceptance=False,execution_grant=False,findings_ref=fr,report_ref=rr))
members=[pin(p) for p in sorted(O.iterdir()) if p.is_file() and p.name not in ("HDF.json","MF.json","postseal-tool-io.json")]
manifest=write("MF.json",dict(schema="researchos.w09-independent-source-review-manifest.v1",members=members,exclusions=["HDF.json","MF.json","postseal-tool-io.json"]))
handoff=write("HDF.json",dict(schema="researchos.w09-independent-source-review-handoff.v1",
    reviewer_id="/root/attach_restore_independent_review",reviewed_author="/root/full_w09_source_review",
    source_hdf_ref=pin(S/"HDF.json"),source_mf_ref=pin(S/"MF.json"),source_ref=h["source_ref"],
    decision="REQUEST_CHANGES",priority="P2",decision_ref=decision,report_ref=rr,findings_ref=fr,
    manifest_ref=manifest,source_guard_ref=pin(O/"source-guard.closed.json"),
    source_build_original1185_preserved=True,new_original_diagnostics=[1186,1187,1188],
    guards_closed_zero=True,retained_handles_count=0,live_Canon_readlocks=0,
    successful_controls_rerun=False,execution_grant=False,formal_acceptance=False,parent_acceptance=False,
    actual_Root_stages=0,actual_Main_Native_Go_SQL_TP_model_calls=0,Main_Canon_Scope_written=False,
    actual_product_exits={k:None for k in ("Native","Go","SQL","dispatcher","model","TP")},
    STOP=True))
for ref in members:
    assert pin(Path(ref["path"]))==ref
print(json.dumps(dict(HDF=handoff,MF=manifest,decision=decision,report=rr,findings=fr,
    retained_handles_count=0,live_Canon_readlocks=0,decision_text="REQUEST_CHANGES"),ensure_ascii=False))

