import json
from pathlib import Path
O=Path(__file__).parent;Q=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W13/W13-03/current58_cli_terminal_closure_codex/8f8e7259f3b8459f8de4ad05ca885c78')
out={}
for n in ['root-launch.outer-completion.json','root-launch.closed.manifest.json']:
 d=json.loads((Q/n).read_bytes());out[n]={'keys':list(d),'fields':{k:({'type':type(v).__name__,'len':len(v),'keys':list(v)[:30] if isinstance(v,dict) else None} if isinstance(v,(dict,list)) else v) for k,v in d.items()}}
 for k,v in d.items():
  if isinstance(v,dict) and {'path','sha256','bytes'}<=v.keys():out[n].setdefault('refs',{})[k]=v
with (O/'root-inspection.json').open('xb') as f:f.write((json.dumps(out,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps(out,ensure_ascii=False))
