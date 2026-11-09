import hashlib,json,pathlib
p=pathlib.Path(__file__).resolve().parent
def ref(f):
 b=f.read_bytes();return dict(path=f.as_posix(),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def check(v):
 r=ref(pathlib.Path(v["path"]));assert r["sha256"]==v["sha256"] and r["bytes"]==v["bytes"]
review=json.loads((p/"review.json").read_text(encoding="utf-8"))
actual=json.loads((p/"actual-component-intake.json").read_text(encoding="utf-8"))
for v in actual["verified_refs"]:check(v)
for k in ("source_handoff_ref","source_manifest_ref","source_ref","test_source_ref","actual_component_closed_ref","actual_original_tool_io_ref","binary_ref"):check(review[k])
items=[ref(f) for f in sorted(p.iterdir()) if f.is_file() and f.name not in ("manifest.json","handoff.json")]
m=dict(schema="researchos.independent-review-manifest.v1",actor_id=review["actor_id"],members=items)
(p/"manifest.json").write_text(json.dumps(m,indent=2,ensure_ascii=True)+"\n",encoding="utf-8")
h=dict(schema="researchos.independent-review-handoff.v1",actor_id=review["actor_id"],decision=review["decision"],formal=False,execution_authority=False,model_trial_authority=False,manifest_ref=ref(p/"manifest.json"),review_ref=ref(p/"review.json"),failure_origin_ref=ref(p/"failure-origin.750.json"))
(p/"handoff.json").write_text(json.dumps(h,indent=2,ensure_ascii=True)+"\n",encoding="utf-8")
for v in items:check(v)
for f in ("manifest.json","handoff.json","review.json","failure-origin.750.json"):json.loads((p/f).read_text(encoding="utf-8"))
print(json.dumps(dict(handoff_ref=ref(p/"handoff.json"),manifest_ref=ref(p/"manifest.json"),review_ref=ref(p/"review.json"),failure_origin_ref=ref(p/"failure-origin.750.json"),verified_members=len(items),decision=review["decision"]),ensure_ascii=True))

