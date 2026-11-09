import hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent
C=N.parent.parent/"w09_c19_caller_source_revision_codex/w09c19r2-1a11f08"
def pin(p):
 raw=p.read_bytes();return dict(path=str(p.resolve()),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,obj):
 with (N/name).open("x",encoding="utf-8",newline="\n") as f:f.write(json.dumps(obj,ensure_ascii=False,indent=2)+"\n")
r=json.loads((N/"review-result.json").read_bytes())
assert r["status"]=="SOURCE_ACCEPTED_PENDING_ROOT_SCOPE_REGISTRATION_VECTOR_AND_ACTUAL" and not r["failures"]
for ref in json.loads((N/"input-pins.json").read_bytes()):assert pin(Path(ref["path"]))==ref
members=[pin(p) for p in sorted(N.iterdir()) if p.is_file() and p.name not in ("HDF.json","MF.json","postseal.json","seal.original-tool-io.json","postseal.original-tool-io.json")]
save("MF.json",dict(schema="researchos.independent-review-manifest.v1",members=members,member_count=len(members)))
save("HDF.json",dict(schema="researchos.w09-c19-r2-independent-source-review.v1",status=r["status"],source_resource_gate=r["source_resource_gate"],actual_resource_gate="NOT_RUN",candidate_handoff_ref=pin(C/"HDF.json"),candidate_manifest_ref=pin(C/"MF.json"),calling_contract_ref=pin(C/"root-calling-contract.json"),scope_proposal_ref=pin(C/"root-scope-registration-proposal.json"),manifest_ref=pin(N/"MF.json"),report_ref=pin(N/"report.md"),checks_ref=pin(N/"checks.json"),input_pins_ref=pin(N/"input-pins.json"),guard_ref=pin(N/"sourceguard.final.json"),synthetic_controls_ref=pin(N/"synthetic-controls.json"),independent_inverse_ref=pin(N/"independent-inverse.json"),check_count=r["checks"],input_count=r["input_count"],exact_six_sources_and_selected_order_unchanged=True,complete_caller_inverse=True,five_fixed_paths_unchanged_and_absent=True,canonical_revision_at_review=364,four_canonical_unchanged=True,CP3_and_VECTOR3_explicit=True,prepare_producer_same_vector_required=True,old_canonical_pins_provenance_only=True,Root_registration_required=True,actual_vector_created=False,actual_Git_Go_SQL_API_producer_model=False,formal_consumers="NOT_RUN_REGISTRY_UNBOUND",formal42_new_acceptance=0,execution_grant=False,formal_acceptance=False,new_mechanical_failures=[],guard_closed=True,STOP_FINAL=True))
print(json.dumps(dict(HDF=pin(N/"HDF.json"),MF=pin(N/"MF.json")),ensure_ascii=False))

