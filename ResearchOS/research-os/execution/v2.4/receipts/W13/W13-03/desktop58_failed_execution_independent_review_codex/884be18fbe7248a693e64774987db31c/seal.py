import json,hashlib
from pathlib import Path
O=Path(__file__).parent;R=Path("D:/作品集/ResearchOS/research-os")
def ref(p):
 b=p.read_bytes();return {"path":p.relative_to(R).as_posix(),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def put(n,d):
 with (O/n).open("xb")as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+"\n").encode())
 return ref(O/n)
review=json.loads((O/"review.json").read_bytes())
assert review["decision"]=="FAILED_EXECUTION_EVIDENCE_CLOSED_QUALIFICATION_WITHHELD"
entries=[ref(p) for p in sorted(O.iterdir()) if p.is_file() and p.name not in ("manifest.json","handoff.json")]
mf=put("manifest.json",{"schema":"researchos.public-review-manifest.v1","reviewer":"codex:/root/w05_merge_review","entries":entries,"count":len(entries),"self_excluded":True,"mutable_after_seal":False})
h=put("handoff.json",{"schema":"researchos.independent-review-handoff.v1","reviewer":"codex:/root/w05_merge_review","decision":review["decision"],"review_ref":ref(O/"review.json"),"manifest_ref":mf,"audit_ref":ref(O/"audit.json"),"supplement_ref":ref(O/"supplement.json"),"final_corrections_ref":ref(O/"final-corrections.v2.json"),"new_failure_origins":[ref(O/"failure-origin.afe7fb.json")],"new_failure_count":1,"qualification":False,"source_acceptance":False,"formal_increment":0,"same_scope_retry":False,"status":"STOPPED"})
print(json.dumps({"review_ref":ref(O/"review.json"),"manifest_ref":mf,"handoff_ref":h,"entries":len(entries),"new_failure_origin":ref(O/"failure-origin.afe7fb.json")},ensure_ascii=False))

