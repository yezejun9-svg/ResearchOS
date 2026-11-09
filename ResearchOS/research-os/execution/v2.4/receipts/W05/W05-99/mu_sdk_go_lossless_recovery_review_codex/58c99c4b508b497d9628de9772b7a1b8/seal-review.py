import hashlib,json,pathlib
p=pathlib.Path(__file__).resolve().parent
def ref(f):
 b=f.read_bytes(); return {"path":str(f).replace("\\\\","/"),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
items=[ref(f) for f in sorted(p.iterdir()) if f.is_file() and f.name not in ("manifest.json","handoff.json")]
m={"schema":"researchos.review-manifest.v1","actor":"codex:/root/w05_merge_review","members":items}
(p/"manifest.json").write_text(json.dumps(m,indent=2,ensure_ascii=True)+"\n",encoding="utf-8")
h={"schema":"researchos.review-handoff.v1","decision":"PARTIAL_DESIGN_REVIEW_NO_EXECUTION_AUTHORITY","formal":False,"execution_authority":False,"actor":"codex:/root/w05_merge_review","manifest_ref":ref(p/"manifest.json"),"review_ref":ref(p/"review.json"),"failure_origin_refs":[ref(p/"failure-origin.747.json"),ref(p/"failure-origin.748.json")]}
(p/"handoff.json").write_text(json.dumps(h,indent=2,ensure_ascii=True)+"\n",encoding="utf-8")
for v in items:
 f=pathlib.Path(v["path"]); assert ref(f)==v
print(json.dumps({"handoff_ref":ref(p/"handoff.json"),"manifest_ref":ref(p/"manifest.json"),"review_ref":ref(p/"review.json"),"failure_origin_refs":h["failure_origin_refs"],"verified_members":len(items)},ensure_ascii=True))

