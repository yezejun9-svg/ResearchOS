from pathlib import Path
import hashlib,json
O=Path(__file__).resolve().parent
def meta(p):
 raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
report=json.loads((O/"source-preparation.v3.json").read_bytes())
for ref in report["inputs"]:
 a=meta(Path(ref["path"]));b=meta(O/ref["snapshot"])
 assert a["sha256"]==b["sha256"]==ref["sha256"] and a["bytes"]==b["bytes"]==ref["bytes"]
mf=dict(schema="researchos.source-preparation-manifest.v1",decision="SOURCE_PREPARATION_ONLY_WITH_OPEN",source_author="codex:/root/w05_merge_review",inventory_scope="All files except manifest and subsequent handoff.json",excluded=["manifest.json","handoff.json"],members=[meta(p) for p in sorted(O.rglob("*")) if p.is_file() and p.name not in {"manifest.json","handoff.json"}])
# Include input snapshots named manifest/handoff as exact evidence too.
mf["members"]=[meta(p) for p in sorted(O.rglob("*")) if p.is_file() and p not in {O/"manifest.json",O/"handoff.json"}]
(O/"manifest.json").write_text(json.dumps(mf,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
h=dict(schema="researchos.mu-sdk-observer-source-handoff.v3",decision="SOURCE_PREPARATION_ONLY_WITH_OPEN",source_author="codex:/root/w05_merge_review",source_ref=meta(O/"mu_sdk_job_observer.v3.proposed.py"),runner_ref=report["runner_ref"],manifest_ref=meta(O/"manifest.json"),handoff_markdown_ref=meta(O/"HANDOFF.md"),review_template_ref=meta(O/"independent-source-review.v3.template.json"),report_ref=meta(O/"source-preparation.v3.json"),stop_source_writes=True,target_native_calls=0,provider_requests=0,formal_acceptance_delta=0,independent_review_issued=False)
(O/"handoff.json").write_text(json.dumps(h,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
print(json.dumps(dict(members=len(mf["members"]),source=h["source_ref"],manifest=h["manifest_ref"],handoff_json=meta(O/"handoff.json"),handoff_markdown=h["handoff_markdown_ref"],stop_source_writes=True)))

