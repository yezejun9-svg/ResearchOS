import json,hashlib
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');E=R/'execution/v2.4/receipts/W05/W05-99';B=Path(__file__).parent;S=E/'original_online_backup_readonly_resource_codex/20261015-current-chat'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
 x=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(x).hexdigest(),'bytes':len(x)}
mp=S/'FINAL-manifest.json';assert ref(mp)['sha256']=='2998736ad37e5078aad5c8bc3269de78bbe7bde225d46aa5dd58eb60f92420ae';m=read(mp);verified=[];unresolved=[]
def nested(v):
 if isinstance(v,dict):
  if isinstance(v.get('path'),str)and isinstance(v.get('sha256'),str):
   p=Path(v['path']);opts=[p]if p.is_absolute()else[S/p,R/p];matches=[p for p in opts if p.is_file()and ref(p)['sha256']==v['sha256']]
   if matches:verified.append(ref(matches[0]))
   else:unresolved.append(v)
  for x in v.values():nested(x)
 elif isinstance(v,list):
  for x in v:nested(x)
nested(m)
if isinstance(m.get('files'),dict):
 for k,v in m['files'].items():nested(dict(v,path=v.get('path',k)))
md=(S/'RESOURCE-MAP.md').read_text(encoding='utf-8-sig');print('MD_LENGTH',len(md),'TEXT\n'+md[:6500])
v=read(S/'resource-map.json');print('MAP_KEYS',json.dumps({k:({'type':type(x).__name__,'len':len(x)}if isinstance(x,(dict,list))else x)for k,x in v.items()},ensure_ascii=False))
print('LEDGER',json.dumps(read(S/'diagnostic-ledger.json'),ensure_ascii=False))
out={'manifest':ref(mp),'verified':len(verified),'refs':verified,'unresolved':unresolved,'resource_map':ref(S/'resource-map.json'),'md':ref(S/'RESOURCE-MAP.md'),'original_backup_gate_accepted':False}
p=B/'original-backup-resource-root-input-verification.json';assert not p.exists();p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('VERIFICATION',json.dumps({'output':ref(p),'verified':len(verified),'unresolved':unresolved},ensure_ascii=False))
