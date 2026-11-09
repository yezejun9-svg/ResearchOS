from pathlib import Path
import json,hashlib
R=Path('D:/作品集/ResearchOS/research-os'); O=Path(__file__).parent; N=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r335-1c4ea6999d4d4437a0202c4e81ce581b'
def shape(d):
 if isinstance(d,dict):return {k:({'type':'list','length':len(v),'first':v[:1]} if isinstance(v,list) else {'type':'dict','keys':list(v)} if isinstance(v,dict) else v) for k,v in d.items()}
 return {'type':type(d).__name__,'length':len(d),'first':d[:1]}
files=['binding.pre-review.json','root-inputs.desktop58.pre-review.json','root-construction.audit.json','root-membership.actual.json','resource-catalog.desktop58.json','runtime-resources.desktop58.json','compiler-resources.desktop58.json','canonical-before.constructed.json','failure-origins.cut.json','resource-capture.tool-observation.closed.json','binding-pre-review.tool-observation.closed.json']
out={}
for name in files:
 raw=(N/name).read_bytes();out[name]={'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'shape':shape(json.loads(raw))}
with (O/'inspection.json').open('xb') as f:f.write((json.dumps(out,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps(out,ensure_ascii=False))
