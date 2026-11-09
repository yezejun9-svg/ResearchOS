import hashlib,json,pathlib
p=pathlib.Path(__file__).resolve().parent
old=pathlib.Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/P05/prepared_run_abandonment_source_codex/210b172f33a046d082258618207c631f")
def ref(f):
 raw=f.read_bytes();return dict(path=f.as_posix(),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
mf=json.loads((old/"MF.json").read_text(encoding="utf-8"))
inputs=[]
for n,v in mf["members"].items():
 r=ref(old/"candidate-root"/n);assert r["sha256"]==v["sha256"] and r["bytes"]==v["bytes"];inputs.append(r)
for n in ("HDF.json","MF.json","source-diff.patch","source-static-evidence.json","contracts/prepared-run-abandonment.v1.json"):inputs.append(ref(old/n))
assert inputs[-1]["sha256"]==mf["contract"]["sha256"]
(p/"inspected-source-pins.json").write_text(json.dumps(dict(source_root=str(old),refs=inputs,verified_member_count=6),indent=2,ensure_ascii=True)+"\n",encoding="utf-8")
items=[ref(f) for f in sorted(p.iterdir()) if f.is_file() and f.name not in ("manifest.json","handoff.json")]
(p/"manifest.json").write_text(json.dumps(dict(schema="researchos.source-critique-manifest.v1",members=items),indent=2,ensure_ascii=True)+"\n",encoding="utf-8")
h=dict(schema="researchos.source-critique-handoff.v1",actor_id="codex:/root/w05_merge_review",decision="BLOCKED_SOURCE_TARGET_PREPARATION_COMPATIBILITY",formal=False,execution_authority=False,manifest_ref=ref(p/"manifest.json"),review_ref=ref(p/"review.json"),failure_origin_ref=ref(p/"failure-origin.752.json"))
(p/"handoff.json").write_text(json.dumps(h,indent=2,ensure_ascii=True)+"\n",encoding="utf-8")
for v in items:assert ref(pathlib.Path(v["path"]))==v
print(json.dumps(dict(handoff_ref=ref(p/"handoff.json"),manifest_ref=ref(p/"manifest.json"),review_ref=ref(p/"review.json"),failure_origin_ref=ref(p/"failure-origin.752.json"),verified_members=len(items)),ensure_ascii=True))

