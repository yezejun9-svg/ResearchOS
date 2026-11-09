from pathlib import Path
import json,hashlib,collections
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).parent
Q=R/'execution/v2.4/receipts/W05/W05-99/cli58_successful_execution_independent_review_codex/83c89c410a1744b8b77d121fd44e5c5e/qualification.json'
def ref(p):
 p=Path(p);b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def small(x):
 if isinstance(x,dict):return {'type':'dict','keys':list(x)}
 if isinstance(x,list):return {'type':'list','length':len(x)}
 return x
q=json.loads(Q.read_bytes());refs=q['evidence_refs'];mf=Path(refs['root_closed_manifest_ref']['path']);mp=json.loads(mf.read_bytes());cp=Path(refs['root_completion_ref']['path']);c=json.loads(cp.read_bytes())
out={'qualification_ref':ref(Q),'qualification_keys':list(q),'evidence_refs':refs,'manifest_ref':ref(mf),'manifest_shape':{k:small(v) for k,v in mp.items()},'completion_ref':ref(cp),'completion_shape':{k:small(v) for k,v in c.items()},'member_parents':dict(collections.Counter(str(Path(x['path']).parent) for x in mp['members']))}
with (O/'inspection.json').open('xb') as f:f.write((json.dumps(out,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps(out,ensure_ascii=False))
