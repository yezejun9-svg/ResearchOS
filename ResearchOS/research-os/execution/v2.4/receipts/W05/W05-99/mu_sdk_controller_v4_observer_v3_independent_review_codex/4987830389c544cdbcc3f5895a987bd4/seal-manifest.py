import hashlib,json,pathlib
O=pathlib.Path(__file__).resolve().parent
def ref(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def write(name,x):
 p=O/name;p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n",encoding="utf-8");return ref(p)
r=json.loads((O/"independent-source-review.json").read_bytes())
members=[ref(p) for p in sorted(O.iterdir()) if p.is_file() and p.name not in ("manifest.json","handoff.json")]
m=write("manifest.json",{"schema":"researchos.immutable-independent-review-manifest.v1","decision":"REQUEST_CHANGES","members":members,"member_count":len(members),"excludes":["manifest.json","handoff.json"],"input_records":r["input_records"],"input_drift":0})
h=write("handoff.json",{"schema":"researchos.immutable-independent-review-handoff.v1","actor_id":"codex:/root/command_queue_impl","decision":"REQUEST_CHANGES","scope":"C4_O3_V9_SIX_REF_WHOLE_SOURCE_TUPLE_REVIEW","review_ref":ref(O/"independent-source-review.json"),"report_ref":ref(O/"review.md"),"findings_ref":ref(O/"findings.json"),"manifest_ref":m,"findings":["C4-R01"],"new_independent_controls":32,"matched":30,"distinct_findings":1,"reused_not_rerun":{"O2":39,"v9":8,"guard_v2":31,"guard_prior":28},"new_tool_failures":3,"failure_origin_refs":r["failure_origin_refs"],"external_693_ref":r["external_failure_693_ref"],"external_693_recounted":False,"WinAPI_SQL_product_provider_calls":0,"canonical_Main_writes":0,"grant_or_qualification":False,"stopped":True})
print(json.dumps({"handoff":h,"manifest":m,"review":ref(O/"independent-source-review.json"),"members":len(members)},ensure_ascii=False,indent=2))

