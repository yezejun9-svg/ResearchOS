import hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent
C=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/restored21_session_profile_source_codex/r21s-1a11f5e")
def pin(p):
 p=Path(p).resolve();b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(n,v):
 with (N/n).open("x",encoding="utf-8",newline="\n") as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+"\n")
refs=json.loads((N/"input-pins.json").read_bytes());result=json.loads((N/"result.json").read_bytes())
assert all(pin(v["path"])==v for v in refs)
for name in ("source-guard.cleanup.actual.json","source-guard.cleanup.fixed.actual.json"):
 c=json.loads((N/name).read_bytes());assert c["closed"] is True and not c["errors"] and c["retained_handles_count"]==0
assert result["independent_checks"]==85 and result["finite_input_count"]==59
save("MF.json",dict(schema="researchos.restored21-independent-source-review-manifest.v1",members=[pin(p) for p in sorted(N.iterdir()) if p.is_file()]))
save("HDF.json",dict(schema="researchos.restored21-independent-source-review-handoff.v1",status=result["status"],actor="codex:/root/attach_fixture_source_review",source_handoff_ref=pin(C/"HDF.json"),source_manifest_ref=pin(C/"MF.json"),manifest_ref=pin(N/"MF.json"),report_ref=pin(N/"REPORT.md"),result_ref=pin(N/"result.json"),findings_ref=pin(N/"findings.json"),P1_findings=0,P2_findings=1,source_gate="PASS_WITH_NONBLOCKING_RECEIPT_GAP",runtime_qualification="OPEN",public_late_failure_no_publication="OPEN",genuine21_22_program_provenance="OPEN",B_branch="OPEN",overall20to24="OPEN",independent_static_controls=85,finite_exact_input_pins=59,actual_SourceReadGuard=True,all_acquired_guards_closed=True,retained_handles=0,actual_test_count=0,expected_parent_count=9,expected_leaf_count=4,formal_acceptance=False,formal_case_accepted_delta=0,execution_grant=False,Main_or_SQL_or_candidate_or_canonical_written=False,current_canonical_read_locked=False,current_checkpoint_revision=None,current_ownership_revision=None,Go_parser_compiler_formatter_SQL_native_Git_API_model_executed=False,new_original_failures=[dict(ordinal=939,origin_ref=pin(N/"r21_run.original-tool-io.json"),outer_exit=1,python_exit=1,native_exit=None,model_exit=None)],failure_disposition_ref=pin(N/"failure-disposition.json"),guard_cleanup_refs=[pin(N/name) for name in ("source-guard.cleanup.actual.json","source-guard.cleanup.fixed.actual.json")],STOP=True,FINAL=True))
assert all(pin(v["path"])==v for v in refs)
save("postseal.json",dict(status="PASS",input_pins_stable=59,handoff_ref=pin(N/"HDF.json"),manifest_ref=pin(N/"MF.json")))
print(json.dumps(dict(handoff_ref=pin(N/"HDF.json"),manifest_ref=pin(N/"MF.json"),postseal_ref=pin(N/"postseal.json"))))

