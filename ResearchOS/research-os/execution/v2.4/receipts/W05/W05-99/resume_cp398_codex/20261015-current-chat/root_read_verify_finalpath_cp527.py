from pathlib import Path
import hashlib,json,shutil
R=Path(r'D:\\作品集\\ResearchOS\\research-os');B=Path(__file__).parent;E=R/'execution/v2.4/receipts/W05/W05-99/host_stored_finalpath_diagnosis_codex/20261015-current-chat'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
for n in ['DIAGNOSIS.md','diagnosis.json','diagnostic-ledger.json','diagnostic-ledger.jsonl','FINAL-manifest.json']:
 p=E/n
 if not p.is_file():continue
 print('REF',ref(p))
 if n!='FINAL-manifest.json':print(p.read_text(encoding='utf-8-sig'))
 else:
  v=read(p);print('MANIFEST_KEYS',list(v));print(json.dumps({k:x for k,x in v.items()if k not in ['files','entries']},ensure_ascii=False));print('FILES_FIRST',json.dumps(v.get('files',v.get('entries',[]))[:2],ensure_ascii=False))
m=read(E/'FINAL-manifest.json');checked=[];bad=[]
def walk(v):
 if isinstance(v,dict):
  if isinstance(v.get('path'),str)and isinstance(v.get('sha256'),str):
   p=Path(v['path']);p=p if p.is_absolute()else E/p
   if not p.is_file():bad.append({'missing':str(p)})
   else:
    x=ref(p)
    if x['sha256']!=v['sha256']or('bytes'in v and x['bytes']!=v['bytes']):bad.append({'expected':v,'actual':x})
    else:checked.append(x)
  for x in v.values():walk(x)
 elif isinstance(v,list):
  for x in v:walk(x)
walk(m)
p=B/'host-finalpath-root-input-verification.json'
with p.open('x',encoding='utf8')as f:json.dump({'manifest':ref(E/'FINAL-manifest.json'),'verified':len(checked),'refs':checked,'unresolved':bad,'actual_access':False},f,ensure_ascii=False,indent=2);f.write(chr(10))
assert json.loads(p.read_bytes())['verified']==len(checked)
print('VERIFIED',len(checked),'BAD',json.dumps(bad,ensure_ascii=False),'OUTPUT',json.dumps(ref(p),ensure_ascii=False))
print('DISK_FREE',json.dumps({'D':shutil.disk_usage('D:/').free,'C':shutil.disk_usage('C:/').free}))
assert not bad
