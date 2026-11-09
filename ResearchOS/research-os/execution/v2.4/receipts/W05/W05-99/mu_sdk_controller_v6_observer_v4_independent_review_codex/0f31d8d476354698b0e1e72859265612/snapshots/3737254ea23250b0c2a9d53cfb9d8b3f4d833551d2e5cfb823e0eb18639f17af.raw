from pathlib import Path
import hashlib,json
O=Path(__file__).resolve().parent
def meta(p):
    raw=p.read_bytes()
    return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def write(name,obj):
    p=O/name
    assert not p.exists()
    p.write_bytes((json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode("utf-8"))
report=json.loads((O/"source-preparation.v4.json").read_bytes())
assert meta(Path(report["source_ref"]["path"])) == report["source_ref"]
for ref in report["inputs"]:
    current=meta(Path(ref["path"])); snapshot=meta(O/ref["snapshot"])
    assert current["sha256"]==snapshot["sha256"]==ref["sha256"]
    assert current["bytes"]==snapshot["bytes"]==ref["bytes"]
controls=json.loads((O/"pure-controls.v4.json").read_bytes())
assert controls["passed"]==controls["total"]==167 and all(c["passed"] for c in controls["controls"])
write("manifest.json",dict(schema="researchos.source-preparation-manifest.v1",decision="SOURCE_PREPARATION_ONLY_WITH_OPEN",source_author="codex:/root/w05_merge_review",inventory_scope="All files except manifest.json and subsequent handoff.json",excluded=["manifest.json","handoff.json"],members=[meta(p) for p in sorted(O.rglob("*")) if p.is_file() and p not in {O/"manifest.json",O/"handoff.json"}]))
write("handoff.json",dict(schema="researchos.mu-sdk-observer-source-handoff.v4",decision="SOURCE_PREPARATION_ONLY_WITH_OPEN",source_author="codex:/root/w05_merge_review",source_ref=report["source_ref"],runner_ref=report["runner_ref"],manifest_ref=meta(O/"manifest.json"),handoff_markdown_ref=meta(O/"HANDOFF.md"),review_template_ref=meta(O/"independent-source-review.v4.template.json"),report_ref=meta(O/"source-preparation.v4.json"),controls_ref=meta(O/"pure-controls.v4.json"),caller_contract_ref=meta(O/"root-caller-contract.md"),failure_origin_ref=meta(O/"failure-origin.705.json"),pure_controls_passed=167,stop_source_writes=True,candidate_module_imports=0,target_native_calls=0,provider_requests=0,formal_acceptance_delta=0,independent_review_issued=False))
print(json.dumps(dict(manifest=meta(O/"manifest.json"),handoff=meta(O/"handoff.json"),failure_origin=meta(O/"failure-origin.705.json"),source=report["source_ref"],stop_source_writes=True),ensure_ascii=False))

