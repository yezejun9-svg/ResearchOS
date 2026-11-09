from pathlib import Path
import hashlib,json
O=Path(__file__).resolve().parent
def meta(p):
    b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(name,value):
    with (O/name).open("xb") as f:f.write((json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode("utf-8"))
review=json.loads((O/"review.json").read_bytes())
assert review["decision"]=="PASS_ACTUAL_COMPONENT" and len(review["checks"])==77 and not review["findings"]
save("manifest.json",dict(schema="researchos.independent-component-review-manifest.v1",reviewer="codex:/root/w05_merge_review",excluded=["manifest.json","handoff.json"],members=[meta(p) for p in sorted(O.rglob("*")) if p.is_file() and p not in {O/"manifest.json",O/"handoff.json"}]))
save("handoff.json",dict(schema="researchos.canonical-pair-independent-review-handoff.v1",reviewer="codex:/root/w05_merge_review",decision="PASS_ACTUAL_COMPONENT",scope="Root actual canonical exclusive-pair component CP345→346 OW168 unchanged",review_ref=meta(O/"review.json"),manifest_ref=meta(O/"manifest.json"),handoff_markdown_ref=meta(O/"HANDOFF.md"),original_tool_io_ref=meta(O/"review.original-tool-io.json"),failure708_origin_ref=meta(O/"failure-origin.708.json"),root_handoff_ref=review["root_handoff_ref"],root_proof_ref=review["proof_ref"],checks_passed=77,checks_failed=0,source_input_count=28,canonical_revision=346,ownership_revision=168,registered_failure_cut=707,subsequent_review_failure_pending_root_registration=708,candidate_calls=0,canonical_mutations=0,real_winapi_calls=0,provider_calls=0,runtime_qualification=False,formal_acceptance=False,stop_all_review_namespace_writes=True))
print(json.dumps(dict(review=meta(O/"review.json"),manifest=meta(O/"manifest.json"),handoff=meta(O/"handoff.json"),failure708=meta(O/"failure-origin.708.json"),stop=True),ensure_ascii=False))

