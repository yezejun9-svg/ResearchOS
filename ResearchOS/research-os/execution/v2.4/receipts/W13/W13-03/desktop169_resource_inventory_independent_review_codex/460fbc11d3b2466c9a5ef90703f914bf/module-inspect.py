from pathlib import Path
import json,hashlib
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).parent;W=R/'.local/worktrees/codex-w1303-desktop-http-r311';I=json.loads((O/'inspection.json').read_bytes());m=json.loads(Path(I['module_ref']['ref']['path']).read_bytes());out=[]
for row in m['observations']:
 p=W/row['ref']['path'];raw=p.read_bytes();d=json.loads(raw);out.append({'ref':{'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)},'keys':list(d),'shape':{k:{'type':type(v).__name__,'len':len(v),'first':v[:1] if isinstance(v,list) else list(v)[:4]} for k,v in d.items() if isinstance(v,(list,dict))}})
with (O/'module-inspection.json').open('xb') as f:f.write((json.dumps(out,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps({'count':len(out),'first':out[0]},ensure_ascii=False))
