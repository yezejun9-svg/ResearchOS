import hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent
R=Path("D:/作品集/ResearchOS/research-os")
B=R/"execution/v2.4/receipts/W05/W05-99"
def pin(p):
 raw=p.read_bytes()
 return dict(path=str(p.resolve()),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def write(name,obj):
 with (N/name).open("x",encoding="utf-8",newline="\n") as f:f.write(json.dumps(obj,ensure_ascii=False,indent=2)+"\n")
inputs=[
(B/"original_trial_reconcile_readonly_codex/trial-reconcile-01a11f01/HDF.json","d1a82045915ee113e743404fa066a91786a71c32b436432595b426cae19a210f",1107),
(B/"original_trial_reconcile_readonly_codex/trial-reconcile-01a11f01/MF.json","ab949c3dadae7ec7d4a422b6c7629b190061b3a69121240e5fccd1965de5e082",15177),
(B/"original_trial_reconcile_readonly_codex/trial-reconcile-01a11f01/review.json","4c0accf6b210a5a0b8f0ee771e72c5f4324a6adf5cacb193967475b726be60ae",18244),
(B/"deepseek_harness_candidate_intake_codex/8dca23f4257346148c0a614e52a3afd0/report.md",None,None),
(B/"sdk_deepseek_source_resource_readonly_codex/b5f09979fe774fa18d306413ca26a94d/report.json",None,None),
(R/"AGENTS.md",None,None),
(R/"internal/domain/runtime_model_windows.go",None,None),
(R/"adapters/runtime/mu/worker.mjs",None,None)]
refs=[]
for p,sha,size in inputs:
 ref=pin(p)
 if sha:assert ref["sha256"]==sha and ref["bytes"]==size
 refs.append(ref)
sources=[]
for p in sorted(N.glob("*.fetch.json")):
 meta=json.loads(p.read_bytes())
 rawfile=N/p.name.removesuffix(".fetch.json")
 ref=pin(rawfile)
 assert meta["ok"] is True and meta["status"]==200
 assert ref["sha256"]==meta["sha256"] and ref["bytes"]==meta["bytes"]
 assert ref["bytes"]<=4*1024*1024
 sources.append(dict(url=meta["url"],http_status=meta["status"],authenticated=meta["authenticated"],source_ref=ref,fetch_ref=pin(p)))
commit=json.loads((N/"opencode-ref.json").read_bytes())["object"]["sha"]
assert commit=="388406238bd5ca15564a762840a2362c3a45bd9c"
issue=json.loads((N/"issue44189.json").read_bytes())
assert issue["state"]=="open"
assert "x-opencode-session" in (N/"go.mdx").read_text("utf-8")
failures=[]
for ordinal in [928,929,931]:
 p=N/f"failure-origin.{ordinal}.original-tool-io.json"
 item=json.loads(p.read_bytes())
 assert item["ordinal"]==ordinal
 failures.append(pin(p))
write("input-pins.json",refs)
write("primary-sources.json",dict(commit=commit,sources=sources,public_http_gets=len(sources),downloaded_bytes=sum(x["source_ref"]["bytes"] for x in sources),raw_source_is_deployment_proof=False))
write("result.json",dict(status="PUBLIC_RESOURCE_RESEARCH_COMPLETE_FINANCIAL_COVERAGE_NOT_PROVEN",official_commit=commit,original_account_api_calls=0,model_requests=0,original_dataroot_reads=0,main_canonical_writes_by_reviewer=0,source_files_executed=0,financial="OPEN",provider_requests=None,actual_cost=None,all_requests_and_charges_covered=False,legacy_usage_limits=True,migrated_account_contract_unverified=True,custom_headers_official_docs_verified=True,native_header_alias_parser_verified=False,followup_authority=False,sole_boundary_proposal="Existing Go broker metadata/receipt adapter; offline only; no replacement tool loop",failures=[928,929,931],new_failure_origin_refs=failures,formal_acceptance=False,STOP_FINAL=True))
members=[pin(p) for p in sorted(N.iterdir()) if p.is_file()]
write("MF.json",dict(schema="researchos.public-resource-review-manifest.v1",members=members,member_count=len(members)))
write("HDF.json",dict(schema="researchos.original-provider-public-audit-resource.v1",status="PUBLIC_RESOURCE_RESEARCH_COMPLETE_FINANCIAL_COVERAGE_NOT_PROVEN",manifest_ref=pin(N/"MF.json"),report_ref=pin(N/"REPORT.md"),result_ref=pin(N/"result.json"),sources_ref=pin(N/"primary-sources.json"),input_pins_ref=pin(N/"input-pins.json"),official_commit=commit,public_http_gets=len(sources),input_count=len(refs),financial="OPEN",provider_requests=None,actual_cost=None,account_requests=0,model_requests=0,original_dataroot_reads=0,main_canonical_writes=0,new_failure_origins=failures,formal_acceptance=False,execution_authority=False,STOP_FINAL=True))
for ref in members+refs:assert pin(Path(ref["path"]))==ref
write("postseal.json",dict(status="PASS_POSTSEAL",HDF=pin(N/"HDF.json"),MF=pin(N/"MF.json"),members=len(members),inputs=len(refs),all_pins_unchanged=True,guard_mode="ordinary readonly pre/post byte observations; no held OS handle claim"))
print(json.dumps(dict(HDF=pin(N/"HDF.json"),MF=pin(N/"MF.json"),postseal=pin(N/"postseal.json"),failure_origins=failures,public_gets=len(sources),downloaded_bytes=sum(x["source_ref"]["bytes"] for x in sources)),ensure_ascii=False))
