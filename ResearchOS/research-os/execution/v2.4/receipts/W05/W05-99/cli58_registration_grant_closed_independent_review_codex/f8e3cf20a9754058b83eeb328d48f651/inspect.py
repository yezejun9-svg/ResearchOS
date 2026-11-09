import json
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');P=R/'execution/v2.4/receipts/W05/W05-99';N=P/'integration_codex/cli58-fresh-held2-r334-v2-0e298790cd484ec9ba319a379e7e34ed';A=P/'cli58_fresh_compiler_authorization_codex/0e298790cd484ec9ba319a379e7e34ed';S=P/'integration_codex/cli58-r334-stage-close-0e298790cd484ec9ba319a379e7e34ed'
out={}
for p in [N/'manifest.json',A/'manifest.json',S/'before-cli-launch.json',N/'canonical-write.intent.json']:
 d=json.loads(p.read_bytes());out[str(p)]={'keys':list(d),'fields':{k:({'type':type(v).__name__,'len':len(v),'keys':list(v)[:20] if isinstance(v,dict) else None} if isinstance(v,(dict,list)) else v) for k,v in d.items()}}
 if p.name=='manifest.json':out[str(p)]['first_two']=d.get('entries',d.get('files',d.get('members',[])))[:2]
with (Path(__file__).parent/'inspection.json').open('xb') as f:f.write((json.dumps(out,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps(out,ensure_ascii=False))
