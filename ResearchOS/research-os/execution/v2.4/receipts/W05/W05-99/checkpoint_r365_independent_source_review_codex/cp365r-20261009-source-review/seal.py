import hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent;C=N.parent.parent/"checkpoint_r365_source_preparation_codex/cp365-1a11f08"
def pin(p):
 raw=p.read_bytes();return dict(path=str(p.resolve()),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,obj):
 with (N/name).open("x",encoding="utf-8",newline="\n") as f:f.write(json.dumps(obj,ensure_ascii=False,indent=2)+"\n")
r=json.loads((N/"result.json").read_bytes());assert r["status"]=="CP365_OW169_SOURCE_GATE_ACCEPTED_PENDING_ROOT_ACTUAL" and not r["failures"]
for ref in json.loads((N/"input-pins.json").read_bytes()):assert pin(Path(ref["path"]))==ref
members=[pin(p) for p in sorted(N.iterdir()) if p.is_file() and p.name not in ("HDF.json","MF.json","postseal.json","seal.original-tool-io.json","postseal.original-tool-io.json")]
save("MF.json",dict(schema="researchos.independent-source-review-manifest.v1",members=members,member_count=len(members)))
save("HDF.json",dict(schema="researchos.cp365-ow169-independent-source-gate.v1",status=r["status"],reviewer="codex:/root/attach_fixture_source_review",source_author=False,candidate_handoff_ref=pin(C/"HDF.json"),candidate_manifest_ref=pin(C/"MF.json"),writer_ref=pin(C/"checkpoint_c12_failed_archived.atomic.py"),facts_ref=pin(C/"checkpoint.execution.facts.json"),calling_contract_ref=pin(C/"calling-contract.json"),manifest_ref=pin(N/"MF.json"),report_ref=pin(N/"REPORT.md"),checks_ref=pin(N/"checks.json"),input_pins_ref=pin(N/"input-pins.json"),pure_transform_ref=pin(N/"pure-transform-proof.json"),check_count=r["checks"],input_count=r["inputs"],old900_raw_and_semantic_preserved=True,append_original_ordinals=list(range(903,926)),registered_after=923,high=925,next_failure_at_cutoff=926,CP365_OW169_inverse_verified=True,Root_only_actual=True,SS_CM_unchanged=True,source_scope_only=True,actual_writer_executed=False,canonical_transaction_SourceReadGuard_imported=False,Native_API_SQL_model=False,Main_canonical_write=False,authority="ADMIN_SOURCE_CONSISTENCY_ONLY_NO_PRODUCT_PASS",new_failures=[],STOP_FINAL=True))
print(json.dumps(dict(HDF=pin(N/"HDF.json"),MF=pin(N/"MF.json")),ensure_ascii=False))

