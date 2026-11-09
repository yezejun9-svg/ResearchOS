from pathlib import Path
import json,hashlib,ast,os,copy
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).parent;REG=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r335-72ff32d0d24a42c4a8effd849d54f882'
C=[];REF={}
def pin(p):
 p=Path(p);b=p.read_bytes();r={'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};REF[str(p)]=r;return r
def ck(n,v):C.append({'check':n,'passed':bool(v)})
def verify(r):
 p=Path(r['path']);a=pin(p);ck('pin '+str(p),a['sha256']==r['sha256']and a['bytes']==r['bytes']);return p
def pairs(items):
 d={}
 for k,v in items:
  if k in d:raise ValueError('duplicate JSON key '+k)
  d[k]=v
 return d
def read(p):
 p=verify(p)if isinstance(p,dict)else Path(p);pin(p);return json.loads(p.read_bytes(),object_pairs_hook=pairs,parse_constant=lambda v:(_ for _ in()).throw(ValueError(v)))
def save(n,d):
 with(O/n).open('xb')as f:f.write((json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())
audit=read(REG/'literal-staging.actual.json');q=read(audit['request_ref']);seed=read(audit['seed_ref']);alloc=read(audit['allocation_ref']);h=read(audit['source_handoff_ref']);m=read(audit['metadata_ref']);canon=read(REG/'canonical-before.json');constructor=verify(audit['constructor_ref']).read_bytes()
ck('literal expectedpin',audit['request_ref']['sha256']=='6baabbae4c91e5ac482e4dfdc4015ff6f63d7796339ed6ab5a8774e6ad88c75d');ck('constructor frozen2735',audit['constructor_ref']['sha256']=='2735a4c19b84721fe343662648766f9ffaf09b470ecd8c958a6ef5587d685df4')
ast.parse(constructor);ck('constructor AST only',True)
allowed={'after','allocation','before','builder_source_ref','canonical_copies','controller_review_path','metadata_code_refs','metadata_pipeline_ref','negative_alias_declarations','pending_origin_refs','pipeline_source_ref','scope_template_ref'}
changed=[k for k in sorted(set(q)|set(seed))if q.get(k)!=seed.get(k)];ck('topkey set same',set(q)==set(seed));ck('delta only declared exact fields',set(changed)<=allowed)
for k in q:
 if k not in allowed:ck('protected exact seed '+k,q[k]==seed[k])
old=seed['allocation']['run_uuid'];new=q['allocation']['run_uuid'];ck('expectedUID',new=='72ff32d0d24a42c4a8effd849d54f882'and old=='429e1734d9da4efba276680e78e2510b')
actualalloc={'run_uuid':alloc['run_uuid'],'registration_namespace':alloc['registration_namespace'],**alloc['roots']};ck('actual allocation projection',q['allocation']==actualalloc)
ck('allocation UUID inverse',json.loads(json.dumps(q['allocation']).replace(new,old))==seed['allocation'])
ck('controller future review exact',q['controller_review_path']==alloc['controller_review_path']and q['controller_review_path'].replace(new,old)==seed['controller_review_path'])
ck('exact tuple/count',q['before']==alloc['before']==[334,162,532]and q['after']==[335,163,580]and len(q['pending_origin_refs'])==48 and q['after'][2]==q['before'][2]+48)
ck('before unchanged',q['before']==seed['before'])
ck('no implicit grant',q['schema']=='researchos.desktop58-root-input-construction-request.v1'and q['actor']=='codex:/root'and q['source_acceptance']is False and q['compile_or_case_execution_authorized']is False and q['formal_increment']==0 and alloc['execution_authorized']is False and alloc['after_failure_count']is None)
ck('catalog/sourcehead frozen',q['source_commit']=='e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7'and q['main_git']==seed['main_git'])
ck('metadata8 exactselected',q['metadata_code_refs']==m['entries']and len(m['entries'])==8)
ck('consumed and alternate pipeline same current',q['metadata_pipeline_ref']==q['pipeline_source_ref']==h['pipeline']and h['pipeline']['sha256']=='c0a085f9b720ebdb89a78fb5cf367bd262d2823fe15a9f2686545b99aebe7755')
ck('template/builder selected',q['scope_template_ref']==h['template']and q['builder_source_ref']==h['builder'])
ck('consumed refs inmetadata8',q['metadata_pipeline_ref']in q['metadata_code_refs']and q['builder_source_ref']in q['metadata_code_refs'])
expectednames={'prepare.py','register.py','run.py','seal.py','scope_builder.py','grant_preflight.py',Path(h['builder']['path']).name,Path(h['pipeline']['path']).name};ck('constructor exact metadata8 names',{Path(r['path']).name for r in m['entries']}==expectednames)
for r in m['entries']:
 p=verify(r)
 if p.name in h['wrappers']:
  src=verify(h['wrappers'][p.name]);ck('wrapper source exact andRootallocation '+p.name,p.parent==REG and p.read_bytes()==src.read_bytes())
 else:ck('nonwrapper ref exact selected '+p.name,r in [h['builder'],h['pipeline']])
template=read(q['scope_template_ref']);ck('template real Gate2db',template['authorization_verifier_ref']==h['gate']);verify(h['gate'])
for r in audit['source_review_refs']:
 d=read(r);ck('source reviews actual READY '+r['path'],d['reviewer']=='codex:/root/w05_merge_review'and d['decision']=='READY_SOURCE_PREPARATION_ONLY'and d['requested_changes']==[])
ck('20aliases preserved count',len(q['negative_alias_declarations'])==len(seed['negative_alias_declarations'])==20)
for i,(a,b)in enumerate(zip(q['negative_alias_declarations'],seed['negative_alias_declarations'])):
 z=copy.deepcopy(a);ck('alias UID twice '+str(i),z['path'].count(new)==b['path'].count(old)==2);z['path']=z['path'].replace(new,old);ck('alias fullinverse '+str(i),z==b)
ck('ordinal14 maxcreates2 preserved',[x for x in q['negative_alias_declarations']if x['allocation_ordinal']==14]==[dict(x,path=x['path'].replace(old,new))for x in seed['negative_alias_declarations']if x['allocation_ordinal']==14])
ck('16images same seed',len(q['static_image_refs'])==16 and q['static_image_refs']==seed['static_image_refs'])
ck('budget literals exact',[q[k]for k in ['inner_seconds','outer_seconds','builder_seconds','controller_evidence_reserve_seconds','launcher_evidence_reserve_seconds']]==[7200,7500,1800,60,60])
origins=[]
for r in q['pending_origin_refs']:origins.append({'ref':r,'original_payload':read(r)})
ck('48unique origin refs',len({str(Path(r['path']))for r in q['pending_origin_refs']})==48)
ck('old43origins exactprefix',len(seed['pending_origin_refs'])==43 and q['pending_origin_refs'][:43]==seed['pending_origin_refs'])
ck('old opaque payload raw preserved',all(Path(a['path']).read_bytes()==Path(b['path']).read_bytes()for a,b in zip(q['pending_origin_refs'][:43],seed['pending_origin_refs'])))
expectedcanon=['execution/v2.4/'+n+'.json'for n in ['checkpoint','path_ownership','step_state','commands']]
ck('copies exact ordered',q['canonical_copies']==[x['ref']for x in canon['entries']]and [x['canonical_path']for x in canon['entries']]==expectedcanon)
docs=[]
for i,r in enumerate(q['canonical_copies']):
 p=verify(r);live=R/expectedcanon[i];pin(live);ck('live4 raw equality '+str(i),p.read_bytes()==live.read_bytes());ck('copy content preserves seed '+str(i),p.read_bytes()==verify(seed['canonical_copies'][i]).read_bytes());docs.append(read(r))
ck('actual tuple/head',[docs[0]['revision'],docs[1]['revision'],len(docs[0]['failure_counters'])]==q['before']and docs[0]['head']==q['source_commit'])
prefix=read(q['failure_prefix430_ref']);ck('old430 failureprefix',docs[0]['failure_counters'][:430]==prefix['failure_counters'])
fresh=[]
for k,v in alloc['roots'].items():fresh.append({'key':k,'path':v,'exists':os.path.lexists(v)});ck('5leaf absent '+k,not os.path.lexists(v))
ck('constructor output BASE same allocatedREG',Path(audit['constructor_ref']['path']).parent==REG==Path(q['allocation']['registration_namespace']))
ctor=constructor.decode();ck('real consumed pipeline and membership guard',"frozen(q['metadata_pipeline_ref'])"in ctor and "q['metadata_pipeline_ref'] in q['metadata_code_refs']"in ctor)
ck('Ctor input andoutput projection',"BASE = Path(__file__).resolve().parent"in ctor and "BASE / 'root-construction.parameters.desktop58.json'"in ctor and "'registration_namespace': allocation['registration_namespace']"in ctor)
ck('no constructor outputs yet',all(not os.path.lexists(REG/n)for n in ['root-inputs.desktop58.pre-review.json','resource-catalog.desktop58.json','scope_registration.json','binding.pre-review.json','binding.json','prepare.started.json']))
# Hash all direct pinned request inputs, but do not descend into resource-catalog members.
def refs(v):
 if type(v)is dict:
  if set(v)=={'path','sha256','bytes'}:verify(v)
  else:
   for x in v.values():refs(x)
 elif type(v)is list:
  for x in v:refs(x)
refs(q)
out={'schema':'researchos.desktop58-literal-input-independent-audit.v1','checks':C,'failed_checks':[x for x in C if not x['passed']],'request_ref':audit['request_ref'],'seed_ref':audit['seed_ref'],'constructor_ref':audit['constructor_ref'],'actual_changed_fields':changed,'protected_fields':[k for k in q if k not in allowed],'origin_count':len(origins),'opaque_origins':origins,'new_origins_vs_seed_count':5,'metadata_refs':m['entries'],'fresh_roots':fresh,'input_refs':list(REF.values()),'candidate_executed':False,'resource_tree_enumerated_or_rehashed':False,'new_failure_origins':[]};save('audit.json',out)
print(json.dumps({'checks':len(C),'failed':out['failed_checks'],'actual_changed_fields':changed,'audit_ref':pin(O/'audit.json'),'new_failures':0},ensure_ascii=False))
