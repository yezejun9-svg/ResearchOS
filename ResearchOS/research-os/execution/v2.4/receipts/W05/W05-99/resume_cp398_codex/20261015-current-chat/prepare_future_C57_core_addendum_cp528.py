from pathlib import Path
import json,hashlib
R=Path('D:/作品集/ResearchOS/research-os');B=Path(__file__).parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
 x=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(x).hexdigest(),'bytes':len(x)}
r=read(B/'continuation-cp528/RESUME.current.json');found={}
for k in ['qualification_failure_architecture_ref','qualification_failure_architecture_review_ref','qualification_failure_revision02_ref','qualification_failure_revision02_independent_ref','qualification_failure_revision03_design_ref','qualification_repair_composition_input_map_ref','qualification_failure_revision02_scope_ref']:
 x=r.get(k);print('REF_INPUT',k,json.dumps(x,ensure_ascii=False))
 if isinstance(x,dict)and 'path'in x:
  p=Path(x['path']);p=p if p.is_absolute()else R/p
  if p.is_file():
   assert hashlib.sha256(p.read_bytes()).hexdigest()==x['sha256'];found[k]=ref(p)
   if p.name=='FINAL-manifest.json':
    m=read(p);print('MANIFEST_ENTRIES',k,[z.get('path',z.get('name'))for z in m.get('files',m.get('entries',[]))if isinstance(z,dict)and any(t in str(z.get('path',z.get('name',''))).lower()for t in ['architecture','c-','scope','test','contract','status'])])
p=B/'future-C57-core-contract-input-addendum-cp528.json'
with p.open('x',encoding='utf8')as f:json.dump({'status':'UNISSUED_READONLY_CORE_CONTRACT_INPUTS','original_core_inputs':found,'base_input_map':ref(B/'future-C57-unissued-input-map-cp528.json'),'Source_authority':False,'actual_authority':False,'formal_increment':0},f,ensure_ascii=False,indent=2);f.write(chr(10))
print('OUTPUT',ref(p))
