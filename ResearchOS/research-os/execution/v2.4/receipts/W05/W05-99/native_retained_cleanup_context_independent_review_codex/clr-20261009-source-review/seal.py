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
members={p.name:pin(p) for p in sorted(O.iterdir()) if p.is_file() and p.name not in {"MF.json","HDF.json","postseal.json"}}
write("MF.json",dict(schema="researchos.cleanup-independent-review-manifest.v1",members=members,formal_acceptance=False))
write("HDF.json",dict(schema="researchos.cleanup-independent-review-handoff.v1",status="SOURCE_ACCEPTED_PENDING_RESOURCE_PREREQUISITE_AND_ROOT_ACTUAL",reviewer="codex:/root/attach_fixture_source_review",manifest_ref=pin(O/"MF.json"),manifest_member_count=len(members),report_ref=pin(O/"report.md"),result_ref=pin(O/"review-result.json"),sourceguard_ref=pin(O/"sourceguard.final.json"),original_tool_io_ref=pin(O/"original-tool-io.json"),source_checks=82,source_inputs=17,whole_original_byte_inverse=True,all_90_original_assertions_preserved=True,all_nine_cases_preserved=True,full_four_minute_native_retention_qualified=False,prerequisite="Separate reviewed inner-controller1560/1570 revision; existing inner1260/1270 is shorter than main20+cleanup4. Outer30 does not replace inner limit.",Go_AST_compile_tests_run=False,actual_Git_Go_native_SQL_model=False,new_mechanical_failures=[],formal_acceptance=False,STOP=True))
assert all(pin(Path(r["path"]))==r for r in members.values())
assert all(pin(Path(r["path"]))==r for r in g["refs"])
write("postseal.json",dict(status="EXACT_PIN_RECHECK_PASS",HDF=pin(O/"HDF.json"),MF=pin(O/"MF.json"),manifest_members=len(members),source_inputs_unchanged=len(g["refs"]),formal_acceptance=False))
print(json.dumps(dict(HDF=pin(O/"HDF.json"),MF=pin(O/"MF.json"),postseal=pin(O/"postseal.json"))))

