import json,hashlib
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");E=R/'execution/v2.4/receipts/W05/W05-99/source43_b_stop_finalpath_codex/20261025-current-chat'
for name in ['FINAL-manifest.json','diagnostic-ledger.json','claim-test-matrix.json','command-index.json']:
 p=E/name;v=json.loads(p.read_text(encoding='utf-8-sig'));print('FILE '+name+' '+hashlib.sha256(p.read_bytes()).hexdigest())
 if name=='FINAL-manifest.json':
  print(json.dumps({k:(x if not isinstance(x,(list,dict)) else {'type':type(x).__name__,'length':len(x),'sample':(x[:1] if isinstance(x,list) else list(x)[:8])}) for k,x in v.items()},ensure_ascii=False,indent=2))
 elif name=='command-index.json':print(json.dumps({'type':type(v).__name__,'length':len(v),'sample':v[:1] if isinstance(v,list)else list(v)[:5]},ensure_ascii=False))
 else:print(json.dumps(v,ensure_ascii=False,indent=2))
