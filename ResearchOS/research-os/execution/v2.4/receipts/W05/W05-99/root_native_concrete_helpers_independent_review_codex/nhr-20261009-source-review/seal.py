import sys
sys.dont_write_bytecode=True
import hashlib,json
from pathlib import Path
O=Path(__file__).resolve().parent
def pin(p):
    raw=p.read_bytes();return dict(path=str(p.resolve()),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def write(name,value):
    with (O/name).open("x",encoding="utf-8",newline="\n") as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write("\n")
guard=json.loads((O/"sourceguard.final.json").read_text(encoding="utf-8"))
assert all(pin(Path(ref["path"]))==ref for ref in guard["refs"])
members={p.name:pin(p) for p in sorted(O.iterdir()) if p.is_file() and p.name not in {"MF.json","HDF.json","postseal.json"}}
write("MF.json",dict(schema="researchos.independent-source-review-manifest.v1",members=members,authority="NONE",formal_acceptance=False))
write("HDF.json",dict(schema="researchos.root-concrete-helper-independent-review.v1",status="REQUEST_CHANGES",reviewer="codex:/root/attach_fixture_source_review",manifest_ref=pin(O/"MF.json"),manifest_member_count=len(members),report_ref=pin(O/"report.md"),finding_ref=pin(O/"finding.NHR-001.json"),result_ref=pin(O/"review-result.json"),source_guard_ref=pin(O/"sourceguard.final.json"),original_tool_io_ref=pin(O/"original-tool-io.json"),checks=107,guarded_source_refs=41,mechanical_failures=[897,898],outer_python_native_exits_for_schema_errors=None,actual_native_SQL_model_Git_Go=False,private_read=False,formal_acceptance=False,STOP=True))
assert all(pin(Path(ref["path"]))==ref for ref in members.values())
assert all(pin(Path(ref["path"]))==ref for ref in guard["refs"])
write("postseal.json",dict(status="EXACT_PIN_RECHECK_PASS",HDF=pin(O/"HDF.json"),MF=pin(O/"MF.json"),manifest_members=len(members),source_inputs_unchanged=len(guard["refs"]),formal_acceptance=False))
print(json.dumps(dict(HDF=pin(O/"HDF.json"),MF=pin(O/"MF.json"),postseal=pin(O/"postseal.json"))))

