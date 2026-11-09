import sys
sys.dont_write_bytecode=True
import hashlib,json
from pathlib import Path
O=Path(__file__).resolve().parent
def pin(p):
    raw=p.read_bytes();return dict(path=str(p.resolve()),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def write(name,value):
    with (O/name).open("x",encoding="utf-8",newline="\n") as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write("\n")
g=json.loads((O/"sourceguard.final.json").read_text(encoding="utf-8"))
assert all(pin(Path(r["path"]))==r for r in g["refs"])
members={p.name:pin(p) for p in sorted(O.iterdir()) if p.is_file() and p.name not in {"HDF.json","MF.json","postseal.json"}}
write("MF.json",dict(schema="researchos.NHR001-independent-rereview-manifest.v1",members=members,formal_acceptance=False))
write("HDF.json",dict(schema="researchos.NHR001-independent-rereview-handoff.v1",status="SOURCE_ACCEPTED_PENDING_ROOT_ACTUAL",reviewer="codex:/root/attach_fixture_source_review",finding="NHR-001",finding_status="CLOSED_IN_SOURCE",helper_sha256="122f586885a2f3cd8141f4697175655d03441667603fc378cdac662e21a65ac2",helper_bytes=29098,manifest_ref=pin(O/"MF.json"),manifest_member_count=len(members),report_ref=pin(O/"report.md"),result_ref=pin(O/"review-result.json"),sourceguard_ref=pin(O/"sourceguard.final.json"),original_tool_io_ref=pin(O/"original-tool-io.json"),checks=108,source_inputs=24,exact_inverse_original_helper=True,public_RawPin_unchanged=True,other_phase_gates_unchanged=True,actual_Git_Go_native_SQL_model=False,private_database_read=False,approval_generated=False,future_unseen_grant_approved=False,new_mechanical_failures=[],formal_acceptance=False,STOP=True))
assert all(pin(Path(r["path"]))==r for r in members.values())
assert all(pin(Path(r["path"]))==r for r in g["refs"])
write("postseal.json",dict(status="EXACT_PIN_RECHECK_PASS",HDF=pin(O/"HDF.json"),MF=pin(O/"MF.json"),manifest_members=len(members),source_inputs_unchanged=len(g["refs"]),formal_acceptance=False))
print(json.dumps(dict(HDF=pin(O/"HDF.json"),MF=pin(O/"MF.json"),postseal=pin(O/"postseal.json"))))

