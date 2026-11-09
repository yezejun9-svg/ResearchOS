import hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent
C=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/restored21_session_runtime_caller_source_codex/r21v2caller-20261009-01")
def pin(p):
 p=Path(p).resolve();b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(n,v):
 with (N/n).open("x",encoding="utf-8",newline="\n") as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+"\n")
refs=json.loads((N/"input-pins.json").read_bytes());result=json.loads((N/"result.json").read_bytes())
assert all(pin(v["path"])==v for v in refs)
assert result["independent_checks"]==50 and result["finite_exact_inputs"]==132 and result["status"]=="REQUEST_CHANGES"
for name in ("source-guard.cleanup.actual.json","source-guard.cleanup.fixed.actual.json"):
 c=json.loads((N/name).read_bytes());assert c["closed"] and not c["errors"] and c["retained_handles_count"]==0
save("failure-disposition.json",dict(new_original_failures=[dict(ordinal=947,chunk_id="e6dd3e",origin_ref=pin(N/"review-failed.original-tool-io.json"),outer_exit=1,python_exit=1,native_exit=None,model_exit=None,cause="Reviewer assumed18 rejected paths; exact compound predicate rejects20",original_review_ref=pin(N/"review.py"),original_cleanup_ref=pin(N/"source-guard.cleanup.actual.json"),corrected_review_ref=pin(N/"review.fixed.py"),corrected_outer_exit=0,corrected_python_exit=0)],actual_product_failure=False))
save("MF.json",dict(schema="researchos.a21-runtime-caller-independent-review-manifest.v1",members=[pin(p) for p in sorted(N.iterdir()) if p.is_file()]))
save("HDF.json",dict(schema="researchos.a21-runtime-caller-independent-source-review.v1",status="REQUEST_CHANGES",actor="codex:/root/attach_fixture_source_review",source_handoff_ref=pin(C/"HDF.json"),source_manifest_ref=pin(C/"MF.json"),manifest_ref=pin(N/"MF.json"),report_ref=pin(N/"REPORT.md"),result_ref=pin(N/"result.json"),findings_ref=pin(N/"findings.json"),counterexamples_ref=pin(N/"counterexamples.json"),P1_findings=3,P2_findings=2,exact_source_rejection_count=20,composed_source_count=63,independent_controls=50,finite_exact_pins=132,actual_SourceReadGuard=True,all_acquired_guards_closed=True,retained_handles=0,guard_cleanup_refs=[pin(N/name) for name in ("source-guard.cleanup.actual.json","source-guard.cleanup.fixed.actual.json")],failure_disposition_ref=pin(N/"failure-disposition.json"),new_original_failures=[dict(ordinal=947,origin_ref=pin(N/"review-failed.original-tool-io.json"),outer_exit=1,python_exit=1,native_exit=None,model_exit=None)],actual_Git_Go_compiler_SQL_native_CLI_model_caller_executed=False,pure_AST_counterexamples_only=True,actual_test_count=0,expected_parent_count=9,expected_leaf_count=4,current_canonical_read_locked_written=False,Main_author_source_SQL_candidate_written=False,formal_acceptance=False,formal_case_accepted_delta=0,execution_grant=False,real21_22_program_provenance="OPEN",public_late_failure_no_publication="OPEN",overall20to24="OPEN",STOP=True,FINAL=True))
assert all(pin(v["path"])==v for v in refs)
save("postseal.json",dict(status="PASS_REVIEW_PACKAGE_STABLE",stable_input_pins=132,handoff_ref=pin(N/"HDF.json"),manifest_ref=pin(N/"MF.json")))
print(json.dumps(dict(handoff_ref=pin(N/"HDF.json"),manifest_ref=pin(N/"MF.json"),postseal_ref=pin(N/"postseal.json"))))

