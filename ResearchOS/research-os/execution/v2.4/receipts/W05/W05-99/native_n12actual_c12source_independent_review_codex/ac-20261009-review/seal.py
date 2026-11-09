import sys
sys.dont_write_bytecode=True
import hashlib,json
from pathlib import Path
O=Path(__file__).resolve().parent
def pin(p):
    raw=p.read_bytes();return dict(path=str(p.resolve()),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def write(n,v):
    with (O/n).open("x",encoding="utf-8",newline="\n") as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write("\n")
g=json.loads((O/"sourceguard.final.json").read_text(encoding="utf-8"))
assert all(pin(Path(r["path"]))==r for r in g["refs"])
members={p.name:pin(p) for p in sorted(O.iterdir()) if p.is_file() and p.name not in {"HDF.json","MF.json","postseal.json"}}
write("MF.json",dict(schema="researchos.N12actual-C12source-independent-review-manifest.v1",members=members,formal_acceptance=False))
write("HDF.json",dict(schema="researchos.N12actual-C12source-independent-review-handoff.v1",reviewer="codex:/root/attach_fixture_source_review",N12_decision="ACCEPTED_BUILD_AND_PURE_UNIT_COMPONENT_ONLY",C12_decision="SOURCE_ACCEPTED_FOR_ROOT_PREPARE_PENDING_FINAL_PRELAUNCH_REVIEW",manifest_ref=pin(O/"MF.json"),manifest_member_count=len(members),report_ref=pin(O/"report.md"),result_ref=pin(O/"review-result.json"),sourceguard_ref=pin(O/"sourceguard.final.json"),actual_audit_ref=pin(O/"actual-job-audit.json"),original_tool_io_ref=pin(O/"original-tool-io.json"),checks=9907,source_inputs=4131,N12_observed_jobs=dict(Git=6,build_and_unit=8,guards_closed=7),N12_units=dict(parents=3,leaves=32,PASS=35,FAIL=0,SKIP=0),gofmt_byte_changes=0,actual_inventory=dict(packages=364,build_inputs=3793,product=599,embeds=38),measured_core_input_bytes=273843291,current_reviewer_Git_Go_native_SQL_model=False,C12_builder_executed_by_reviewer=False,private_read=False,Main_canonical_write=False,full_native_retention_qualified=False,formal_Owner_whole9_acceptance=False,new_mechanical_failures=[],STOP=True))
assert all(pin(Path(r["path"]))==r for r in members.values())
assert all(pin(Path(r["path"]))==r for r in g["refs"])
write("postseal.json",dict(status="EXACT_PIN_RECHECK_PASS",HDF=pin(O/"HDF.json"),MF=pin(O/"MF.json"),manifest_members=len(members),source_inputs_unchanged=len(g["refs"]),formal_acceptance=False))
print(json.dumps(dict(HDF=pin(O/"HDF.json"),MF=pin(O/"MF.json"),postseal=pin(O/"postseal.json"))))

