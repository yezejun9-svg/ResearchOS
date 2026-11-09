from pathlib import Path
import hashlib,json
O=Path(__file__).resolve().parent
def meta(p):
 raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
intake=json.loads((O/"intake.json").read_bytes())
for ref in intake["files"]:
 a=meta(Path(ref["path"]));b=meta(O/ref["snapshot"])
 assert a["sha256"]==b["sha256"]==ref["sha256"] and a["bytes"]==b["bytes"]==ref["bytes"]
source=next(r for r in intake["files"] if "source_read_guard_revision_v2_codex" in r["path"] and Path(r["path"]).name=="source_read_guard.py")
source={k:source[k] for k in ["path","sha256","bytes"]}
mf=next(r for r in intake["files"] if "source_read_guard_revision_v2_codex" in r["path"] and Path(r["path"]).name=="manifest.json")
review=dict(schema="researchos.source-read-guard-independent-review.v2",decision="PASS_SOURCE_ONLY",reviewer="codex:/root/w05_merge_review",source_ref=source,source_manifest_ref={k:mf[k] for k in ["path","sha256","bytes"]},controls_ref=meta(O/"controls.json"),closed_findings=["R1"],new_memory_controls=31,reused_prior_independent_controls=28,real_winapi_calls=0,provider_requests=0,actual_cleanup_proven=False,whole_controller_ready=False,execution_grant_issued=False,main_or_canonical_writes=0,open=["ROOT_ACTUAL_WINDOWS_TEMP_TARGET_PROBE","ROOT_COMPLETE_TUPLE_GUARD_LIFETIME","ROOT_C4_O3_INDEPENDENT_REVIEW_AND_ACTUAL_JOB_CLEANUP"])
(O/"review.json").write_text(json.dumps(review,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
manifest=dict(schema="researchos.source-read-guard-independent-review-manifest.v2",decision="PASS_SOURCE_ONLY",source_ref=source,source_recheck="PASS",files=[meta(p) for p in sorted(O.rglob("*")) if p.is_file() and p!=O/"manifest.json"])
(O/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(dict(files=len(manifest["files"]),handoff=meta(O/"HANDOFF.md"),review=meta(O/"review.json"),manifest=meta(O/"manifest.json"),failure_origin693=meta(O/"failure-origin.693.json"))))

