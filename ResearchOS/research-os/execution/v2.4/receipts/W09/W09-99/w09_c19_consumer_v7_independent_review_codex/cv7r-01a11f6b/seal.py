import hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent
C=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W09/W09-99/w09_c19_consumer_v7_caller_source_codex/consv7-1a11f5e")
def pin(p):
 p=Path(p).resolve();b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(n,v):
 with (N/n).open("x",encoding="utf-8",newline="\n") as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+"\n")
refs=json.loads((N/"input-pins.json").read_bytes())
assert all(pin(v["path"])==v for v in refs)
result=json.loads((N/"result.json").read_bytes());cleanup=json.loads((N/"source-guard.cleanup.actual.json").read_bytes())
assert result["checks"]==176 and cleanup["closed"] and not cleanup["errors"] and cleanup["retained_handles_count"]==0
save("MF.json",dict(schema="researchos.independent-review-manifest.v1",members=[pin(p) for p in sorted(N.iterdir()) if p.is_file()]))
save("HDF.json",dict(schema="researchos.w09-c19-v7-consumer-caller-independent-source-review.v1",status=result["status"],actor="codex:/root/attach_fixture_source_review",source_handoff_ref=pin(C/"HDF.json"),source_manifest_ref=pin(C/"MF.json"),candidate_ref=pin(C/"run_c19_consumers.actual_owned.py"),manifest_ref=pin(N/"MF.json"),report_ref=pin(N/"REPORT.md"),result_ref=pin(N/"result.json"),guard_cleanup_ref=pin(N/"source-guard.cleanup.actual.json"),independent_checks=176,finite_input_pins=103,all_acquired_guards_closed=True,retained_handles=0,formal_acceptance=False,formal_case_count=1,formal_case_accepted_delta=0,execution_grant=False,actual_consumer_native_Go_SQL_Git_API_model=False,current_canonical_read_locked_or_written=False,actual_ready=False,required_next="NEW_PRODUCER_INDEPENDENT_QUALIFICATION_TWO_NONAUTHOR_MODE_DECISIONS_COMMON_REVIEW_EXACT_ROOT_CONSUMER_SCOPE",new_original_failures=[dict(ordinal=937,origin_ref=pin(N/"failure-origin.937.original-tool-io.json"),outer_shell_exit=1,python_exit=None,native_exit=None,model_exit=None)],STOP=True,FINAL=True))
assert all(pin(v["path"])==v for v in refs)
save("postseal.json",dict(status="PASS",all_inputs_stable=True,input_count=len(refs),handoff_ref=pin(N/"HDF.json"),manifest_ref=pin(N/"MF.json")))
print(json.dumps(dict(handoff_ref=pin(N/"HDF.json"),manifest_ref=pin(N/"MF.json"),postseal_ref=pin(N/"postseal.json"))))

