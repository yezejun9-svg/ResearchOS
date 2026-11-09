import hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent
C=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/restored21_session_receipt_v2_source_codex/r21receipt2-1a11f5e")
def pin(p):
 p=Path(p).resolve();b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(n,v):
 with (N/n).open("x",encoding="utf-8",newline="\n") as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+"\n")
refs=json.loads((N/"input-pins.json").read_bytes());result=json.loads((N/"result.json").read_bytes());cleanup=json.loads((N/"source-guard.cleanup.actual.json").read_bytes())
assert all(pin(v["path"])==v for v in refs)
assert cleanup["closed"] is True and not cleanup["errors"] and cleanup["retained_handles_count"]==0
assert result["independent_checks"]==87 and result["finite_input_count"]==69
save("MF.json",dict(schema="researchos.restored21-receipt-v2-independent-review-manifest.v1",members=[pin(p) for p in sorted(N.iterdir()) if p.is_file()]))
save("HDF.json",dict(schema="researchos.restored21-receipt-v2-independent-source-review.v1",status=result["status"],actor="codex:/root/attach_fixture_source_review",source_handoff_ref=pin(C/"HDF.json"),source_manifest_ref=pin(C/"MF.json"),manifest_ref=pin(N/"MF.json"),report_ref=pin(N/"REPORT.md"),result_ref=pin(N/"result.json"),finding_disposition_ref=pin(N/"finding-disposition.json"),guard_cleanup_ref=pin(N/"source-guard.cleanup.actual.json"),independent_controls=87,finite_exact_pins=69,P1_findings=0,P2_findings=0,original_P2_source_addressed=True,actual_test_count=0,parent_declarations=9,leaf_declarations=4,source_gate="PASS",runtime_qualification="OPEN",public_late_failure_no_publication="OPEN",genuine21_22_program_provenance="OPEN",B_branch="OPEN",overall20to24="OPEN",formal_acceptance=False,formal_case_accepted_delta=0,execution_grant=False,actual_SourceReadGuard=True,all_acquired_guards_closed=True,retained_handles=0,Go_parser_compiler_formatter_SQL_native_Git_API_model_consumer_executed=False,current_canonical_read_locked_written=False,Main_or_old_Source_or_SQL_or_candidate_modified=False,inherited_failure_administrative_mapping=[dict(ordinal=941,chunk_id="4e57d0",origin_ref=pin(C/"seal-syntax.original-tool-io.json"),sealed_source_ordinal=None,source_seal_unchanged=True)],new_original_failures=[],STOP=True,FINAL=True))
assert all(pin(v["path"])==v for v in refs)
save("postseal.json",dict(status="PASS",stable_input_pins=69,handoff_ref=pin(N/"HDF.json"),manifest_ref=pin(N/"MF.json")))
print(json.dumps(dict(handoff_ref=pin(N/"HDF.json"),manifest_ref=pin(N/"MF.json"),postseal_ref=pin(N/"postseal.json"))))

