import hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent
def pin(p):
 raw=p.read_bytes();return dict(path=str(p.resolve()),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,x):
 with (N/name).open("x",encoding="utf-8",newline="\n") as f:f.write(json.dumps(x,ensure_ascii=False,indent=2)+"\n")
refs=json.loads((N/"input-pins.json").read_bytes())
for ref in refs:assert pin(Path(ref["path"]))==ref
checks=json.loads((N/"checks.json").read_bytes());assert checks["all_passed"]
members=[pin(p) for p in sorted(N.iterdir()) if p.is_file() and p.name not in ("HDF.json","MF.json","postseal.json","seal.original-tool-io.json","postseal.original-tool-io.json")]
save("MF.json",dict(schema="researchos.readonly-handoff-manifest.v1",members=members,member_count=len(members)))
save("HDF.json",dict(schema="researchos.w09-c19-consumer-contract-readonly-handoff.v1",status="READ_ONLY_CODE_DERIVED_CONTRACT_NOT_EXECUTION_GRANT",manifest_ref=pin(N/"MF.json"),report_ref=pin(N/"REPORT.md"),contract_ref=pin(N/"consumer-contract.json"),mode_fields_ref=pin(N/"mode-receipt-required-fields.json"),registry_observed_ref=pin(N/"registry-observed.json"),input_pins_ref=pin(N/"input-pins.json"),checks_ref=pin(N/"checks.json"),check_count=checks["count"],input_count=len(refs),component_consumption_before_formal_registration_possible=True,Root_new_consumer_scope_required=True,same_candidate_same_packet_required=True,source_roster_count=21,registry_only_change_after_closed_producer_does_not_require_reproducer=True,producer_vector_historical_after_new_canonical_registration=True,two_route_specific_decisions_required=True,actual_producer_consumers_Git_Go_SQL_model=False,Main_canonical_write=False,formal_case_accepted_delta=0,new_mechanical_failures=[],STOP_FINAL=True))
print(json.dumps(dict(HDF=pin(N/"HDF.json"),MF=pin(N/"MF.json")),ensure_ascii=False))

