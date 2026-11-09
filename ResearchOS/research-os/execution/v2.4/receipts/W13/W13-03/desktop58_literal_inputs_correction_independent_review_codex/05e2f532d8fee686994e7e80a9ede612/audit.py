from pathlib import Path
import json,hashlib,ast,re
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).parent;N=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r335-dc00ad52f46c49acacc8058a58500820';C=N/'input_capture_v2'
checks=[];inputs={}
def pin(p):
 p=Path(p);b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def check(n,v,d=None):checks.append({'name':n,'passed':bool(v),'detail':d})
def verify(r):
 p=Path(r['path']);b=p.read_bytes();a=pin(p);inputs[str(p)]=a;check('pin:'+str(p),a['sha256']==r['sha256'] and a['bytes']==r['bytes']);return b
def doc(r):return json.loads(verify(r))
def write(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
d=doc({'path':str(C/'input-correction.audit.json'),'sha256':'fc229eea33908e6db8fdb99e627542ba20f2c8838396ba2ec4adc4f0b29989b4','bytes':2840})
raw=verify(d['new_request_ref']);oldraw=verify(d['old_request_ref']);q=json.loads(raw);old=json.loads(oldraw)
changed=[k for k in set(q)|set(old) if q.get(k)!=old.get(k)];check('exact single field changed',changed==['metadata_pipeline_ref'],changed)
restored=dict(q);restored['metadata_pipeline_ref']=old['metadata_pipeline_ref'];check('whole JSON inverse',restored==old)
pattern=rb'("metadata_pipeline_ref": )(\{[^{}]*\})';before=re.search(pattern,oldraw);after=re.search(pattern,raw)
check('whole bytes inverse',before is not None and after is not None and raw[:after.start(2)]+before.group(2)+raw[after.end(2):]==oldraw)
check('new consumed pipeline equals selected pipeline',q['metadata_pipeline_ref']==q['pipeline_source_ref']==q['metadata_code_refs'][7])
check('exact pipeline60078 pin',q['metadata_pipeline_ref']['sha256']=='60078d505a33da7570e7c747ecf4cc81bd46e66560120a07cd85162606421d98' and q['metadata_pipeline_ref']['bytes']==38316)
for r in q['metadata_code_refs']:verify(r)
check('metadata8 exactnames',len(q['metadata_code_refs'])==8 and {Path(x['path']).name for x in q['metadata_code_refs']}=={'scope_builder.py','prepare.py','register.py','run.py','seal.py','grant_preflight.py',Path(q['builder_source_ref']['path']).name,Path(q['metadata_pipeline_ref']['path']).name})
check('constructor membership predicate now true',q['builder_source_ref'] in q['metadata_code_refs'] and q['metadata_pipeline_ref'] in q['metadata_code_refs'])
source=verify(d['constructor_ref']);previous=pin(N/'construct_root_inputs.desktop58.v3.py');inputs[previous['path']]=previous
check('constructor exact original2735',source==(N/'construct_root_inputs.desktop58.v3.py').read_bytes() and previous['sha256']=='2735a4c19b84721fe343662648766f9ffaf09b470ecd8c958a6ef5587d685df4')
text=source.decode('utf-8');tree=ast.parse(text);compile(tree,str(C/'construct_root_inputs.desktop58.v3.py'),'exec')
check('BASE request actualpath',"BASE = Path(__file__).resolve().parent" in text and "q = parse((BASE / 'root-construction.parameters.desktop58.json').read_bytes())" in text)
save_node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='save');save_source=ast.get_source_segment(text,save_node)
check('resources saved under BASE',"BASE / name" in save_source)
check('registration independent of BASE',"'registration_namespace': allocation['registration_namespace']" in text)
check('metadata absolute then ROOTrelative explicit',"for ref in q['metadata_code_refs']:" in text and "Path(row['path']).relative_to(ROOT).as_posix()" in text)
check('runtime paths from auth allocation',"Path(allocation['new_authorization_root']) / (phase + '.json')" in text)
check('actual input parent is distinct registration child',Path(q['allocation']['registration_namespace'])==N and C.parent==N and C!=N)
check('only input files exist in capture container',{p.name for p in C.iterdir()}=={'root-construction.parameters.desktop58.json','input-correction.audit.json','construct_root_inputs.desktop58.v3.py'})
check('same actual tuple/cut/UID',q['before']==[334,162,532] and q['after']==[335,163,564] and len(q['pending_origin_refs'])==32 and q['allocation']['run_uuid']=='dc00ad52f46c49acacc8058a58500820')
leaf_facts={k:Path(v).exists() for k,v in q['allocation'].items() if k.startswith('new_')}
check('five future leaves absent',len(leaf_facts)==5 and not any(leaf_facts.values()),leaf_facts)
cb=json.loads((N/'canonical-before.json').read_bytes())
for row in cb['entries']:
 check('current canonical stays exact:'+row['canonical_path'],(R/row['canonical_path']).read_bytes()==verify(row['ref']))
baseline=R/'execution/v2.4/receipts/W13/W13-03/desktop58_literal_inputs_delta_independent_review_codex/85f2d55021aa3fc185ef8b46cc0f16c5/review.json'
br=doc({'path':str(baseline),'sha256':'74bc6e59f4bc2ae8dedb0582078473b37d140417b65bc628115308c45c493721','bytes':9743})
check('previous finding precisely one',len(br['requested_changes'])==1 and br['requested_changes'][0]['id']=='LITERAL-01')
write('audit.json',{'schema':'researchos.desktop58-literal-correction-readonly-audit.v1','checks':checks,'passed':sum(x['passed'] for x in checks),'failed':[x for x in checks if not x['passed']],'input_refs':list(inputs.values()),'baseline_review_ref':pin(baseline),'constructor_save_source':save_source,'new_failure_origins':[],'target_execution_performed':False,'resource_backing_tree_rehashed':False})
print(json.dumps({'checks':len(checks),'passed':sum(x['passed'] for x in checks),'failed':[x for x in checks if not x['passed']],'audit_ref':pin(O/'audit.json')},ensure_ascii=False))
