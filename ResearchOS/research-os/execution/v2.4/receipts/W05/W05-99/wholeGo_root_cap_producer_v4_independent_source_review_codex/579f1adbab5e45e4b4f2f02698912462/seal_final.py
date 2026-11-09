from pathlib import Path
import hashlib,json
p=Path(__file__).parent
def pin(f):
 b=f.read_bytes();return {"path":str(f),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def put(n,v):
 with (p/n).open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(p/n)
refs=[pin(f) for f in sorted(p.iterdir()) if f.is_file()]
m=put("manifest.final.json",{"schema":"researchos.public-review-manifest.v1","entries":refs,"count":len(refs),"self_excluded":True})
h=put("handoff.final.json",{"schema":"researchos.whole-go-cap-v4-independent-review-handoff.v1","review_ref":pin(p/"review.json"),"audit_ref":pin(p/"audit.json"),"manifest_ref":m,"decision":"READY_SOURCE_PREPARATION_ONLY","new_failure_count":0,"status":"STOPPED","candidate_executed":False})
print(json.dumps({"review_ref":pin(p/"review.json"),"manifest_ref":m,"handoff_ref":h},ensure_ascii=False))

