from pathlib import Path
import json,hashlib,ast
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).parent;N=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r335-dc00ad52f46c49acacc8058a58500820'
checks=[];inputs={}
def check(n,v,d=None):checks.append({'name':n,'passed':bool(v),'detail':d})
def pin(p):
 p=Path(p);raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def verify(r):
 p=Path(r['path']);raw=p.read_bytes();a={'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)};inputs[str(p)]=a;check('pin:'+str(p),a['sha256']==r['sha256'] and a['bytes']==r['bytes']);return raw
def pairs(rows):
 d={}
 for k,v in rows:
  if k in d:raise ValueError('duplicate JSON key '+k)
  d[k]=v
 return d
def parse(raw):return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda v:(_ for _ in ()).throw(ValueError(v)))
def doc(r):return parse(verify(r))
def save(n,d):
 with (O/n).open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
st=doc({'path':str(N/'literal-staging.actual.json'),'sha256':'b008a6e30a3e2bf63c9b611127c6562e925c71a2f42a2cf2802617bec9432cae','bytes':2058})
q=doc(st['request_ref']);old=doc(st['old_request_ref']);alloc=doc(st['allocation_ref']);selected=doc(st['metadata_ref']);h=doc(st['source_handoff_ref'])
for k,v in q.items():
 if isinstance(v,dict) and set(v)=={'path','sha256','bytes'}:verify(v)
for k in ['canonical_copies','metadata_code_refs','static_image_refs']:
 for ref in q[k]:verify(ref)
origins=[doc(r) for r in q['pending_origin_refs']]
check('32 origin cut count',len(origins)==32 and q['after']==[q['before'][0]+1,q['before'][1]+1,q['before'][2]+len(origins)])
check('32 unique paths and hashes',len({str(Path(r['path']).resolve()).casefold() for r in q['pending_origin_refs']})==32 and len({r['sha256'] for r in q['pending_origin_refs']})==32)
check('original21 exact prefix',q['pending_origin_refs'][:21]==old['pending_origin_refs'])
check('before after exact',q['before']==[334,162,532] and q['after']==[335,163,564])
check('source-only declaration',q['actor']=='codex:/root' and q['schema']=='researchos.desktop58-root-input-construction-request.v1' and q['source_acceptance'] is False and q['compile_or_case_execution_authorized'] is False and q['formal_increment']==0)
cb=parse((N/'canonical-before.json').read_bytes());copies=[]
for i,row in enumerate(cb['entries']):
 check('ordered canonical snapshot:'+str(i),row['ref']==q['canonical_copies'][i]);raw=verify(row['ref']);live=(R/row['canonical_path']).read_bytes();check('actual live canonical identical:'+str(i),raw==live);copies.append(parse(raw))
check('actual tuple/head',copies[0]['revision']==334 and copies[1]['revision']==162 and len(copies[0]['failure_counters'])==532 and copies[0]['head']==q['source_commit']=='e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7')
prefix=doc(q['failure_prefix430_ref']);check('historical430 unchanged',copies[0]['failure_counters'][:430]==prefix['failure_counters'])
newid=alloc['run_uuid'];oldid=old['allocation']['run_uuid'];norm=parse(json.dumps(q,ensure_ascii=False).replace(newid,oldid))
allowed={'after','pending_origin_refs','metadata_code_refs','builder_source_ref','scope_template_ref','pipeline_source_ref'}
for k in set(old)|set(norm):
 if k not in allowed:check('unchanged normalized field:'+k,old.get(k)==norm.get(k))
check('allocation UUID/REG',q['allocation']['run_uuid']==newid and q['allocation']['registration_namespace']==alloc['registration_namespace'])
leafs=[]
for k,p in alloc['roots'].items():
 check('allocated future root:'+k,q['allocation'][k]==p);leafs.append({'key':k,'path':p,'exists':Path(p).exists(),'parent_exists':Path(p).parent.is_dir()})
check('five fresh leaves absent',len(leafs)==5 and all(not x['exists'] and x['parent_exists'] for x in leafs),leafs)
check('review path exact',q['controller_review_path']==alloc['controller_review_path'])
check('all20 alias inverse',len(q['negative_alias_declarations'])==20 and norm['negative_alias_declarations']==old['negative_alias_declarations'])
for i,row in enumerate(q['negative_alias_declarations']):
 check('alias path doubleUUID:'+str(i),row['path'].count(newid)==2 and oldid not in row['path'] and Path(row['path']).is_relative_to(Path(q['allocation']['new_export_root'])))
check('alias ordinal14 remains two creates',next(r for r in q['negative_alias_declarations'] if r['allocation_ordinal']==14)['max_creates']==2)
check('metadata selected exact8',selected['entries']==q['metadata_code_refs'] and len(q['metadata_code_refs'])==8)
for ref in q['metadata_code_refs'][:6]:
 name=Path(ref['path']).name;source=h['wrapper_refs'][name];check('Root wrapper exact sealed source:'+name,verify(ref)==verify(source));ast.parse(Path(ref['path']).read_text(encoding='utf-8'))
check('metadata builder exact',q['metadata_code_refs'][6]==q['builder_source_ref']==h['builder_ref'])
check('metadata pipeline selected exactv3',q['metadata_code_refs'][7]==q['pipeline_source_ref']==h['pipeline_ref'])
check('constructor metadata_pipeline_ref membership',q['metadata_pipeline_ref'] in q['metadata_code_refs'],{'actual_request_ref':q['metadata_pipeline_ref'],'required_actual_pipeline':h['pipeline_ref']})
check('scope template exact source',q['scope_template_ref']==h['scope_template_ref'])
t=doc(q['scope_template_ref']);check('template adapter exact',t['authorization_verifier_ref']==h['adapter_ref']);verify(h['adapter_ref'])
check('images16 and environment preserved',len(q['static_image_refs'])==16 and q['static_image_refs']==old['static_image_refs'] and q['public_environment']==old['public_environment'])
for k,v in {'inner_seconds':7200,'outer_seconds':7500,'builder_seconds':1800,'controller_evidence_reserve_seconds':60,'launcher_evidence_reserve_seconds':60}.items():check('budget:'+k,q[k]==v)
check('template cleanup5',t['cleanup_seconds']==5)
reviewpath=R/'execution/v2.4/receipts/W13/W13-03/desktop58_cli_root_closure_adapter_independent_source_review_codex/5ae97e98de0568903e5d77af5169ffc5/review.json'
sr=parse(reviewpath.read_bytes());inputs[str(reviewpath)]=pin(reviewpath)
check('adapter nonauthor source reviewed',sr['requested_changes']==[])
ctor=N/'construct_root_inputs.desktop58.v3.py';source=ctor.read_text(encoding='utf-8');inputs[str(ctor)]=pin(ctor);ast.parse(source)
check('constructor consumes exact mandatory key',"q['metadata_pipeline_ref'] in q['metadata_code_refs']" in source and 'pipeline_source_ref' not in source)
save('audit.json',{'schema':'researchos.desktop58-literal-delta-readonly-audit.v1','checks':checks,'passed':sum(x['passed'] for x in checks),'failed':[x for x in checks if not x['passed']],'input_refs':list(inputs.values()),'origin_payloads_opaque_unchanged':True,'origin_payload_keys':[list(x) if isinstance(x,dict) else type(x).__name__ for x in origins],'source_review_ref':pin(reviewpath),'constructor_ref':pin(ctor),'target_execution_performed':False,'resource_backing_tree_rehashed':False,'new_failure_origins':[]})
print(json.dumps({'checks':len(checks),'passed':sum(x['passed'] for x in checks),'failed':[x for x in checks if not x['passed']],'source_review_ref':pin(reviewpath),'constructor_ref':pin(ctor)},ensure_ascii=False))
