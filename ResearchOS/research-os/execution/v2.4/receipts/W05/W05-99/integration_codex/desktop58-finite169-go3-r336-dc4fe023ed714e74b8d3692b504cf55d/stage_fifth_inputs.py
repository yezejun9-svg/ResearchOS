import sys, os, copy, json, hashlib, ast
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(r"D:/作品集/ResearchOS/research-os")
BASE=Path(__file__).resolve().parent
def need(x,m):
    if not x: raise RuntimeError(m)
def checked(p):
    p=Path(p)
    if not p.is_absolute(): p=ROOT/p
    need(p.is_absolute() and '..' not in p.parts,'absolute canonical path')
    for c in (p,*p.parents):
        if os.path.lexists(c): need(not c.is_symlink() and not (getattr(c.lstat(),'st_file_attributes',0)&0x400),'reparse rejected')
    return p
def pin(p):
    p=checked(p);b=p.read_bytes()
    return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def raw(r):
    p=checked(r['path']);b=p.read_bytes()
    need(len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256'],'pin mismatch '+r['path'])
    return b
def doc(r): return json.loads(raw(r))
def put(n,b):
    p=checked(BASE/n);need(p.parent==BASE and not os.path.lexists(p),'exclusive stage name')
    with p.open('xb') as f:f.write(b)
    return pin(p)
def save(n,v):return put(n,(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8'))
need(sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode,'pinned flags')
cfg=json.loads((BASE/'literal-inputs.original.json').read_bytes())
old=doc(cfg['seed_ref']);q=copy.deepcopy(old)
need(cfg['before']==[335,163,580] and cfg['after']==[336,164,603],'fixed cut')
review=doc(cfg['constructor_review_ref']);need(review['decision']=='READY_SOURCE_PREPARATION_ONLY' and not review['requested_changes'],'non-author constructor review')
doc(cfg['failed_closure_review_ref'])
mf=doc(cfg['constructor_manifest_ref'])
for e in mf['members']:raw(e)
orig603=save('failure-origin-603.original.json',cfg['root_origin603'])
refs=cfg['prior_pending']+cfg['late_origins']+[orig603]
need(len(refs)==23 and cfg['before'][2]+len(refs)==cfg['after'][2],'all 23 original origins')
seen=set()
for r in refs:
    b=raw(r);json.loads(b);key=os.path.normcase(str(checked(r['path'])));need(key not in seen,'duplicate origin');seen.add(key)
refs=[pin(checked(r['path'])) for r in refs]
copies=[]
for i,r in enumerate(cfg['canonical_refs']):
    b=raw(r)
    need((ROOT/r['path']).read_bytes()==b,'canonical changed')
    copies.append(put(Path(r['path']).stem+'.snapshot-before.json',b))
uid=cfg['fifth_uid']; need(uid=='dc4fe023ed714e74b8d3692b504cf55d','actual allocation')
need(BASE==ROOT/cfg['fifth_rel'],'new REG namespace')
allocation={'run_uuid':uid,'registration_namespace':str(BASE)}
for key,group in [('new_output_root','desktop58_finite_executor_codex'),('new_wrapper_root','desktop58_finite_launcher_codex'),('new_authorization_root','desktop58_finite_authorization_codex'),('new_grant_preflight_root','desktop58_finite_grant_preflight_codex')]:
    allocation[key]=str(ROOT/'execution/v2.4/receipts/W13/W13-03'/group/uid)
allocation['new_export_root']=str(ROOT/'.local'/('desktop58-export-'+uid))
for k,v in allocation.items():
    if k not in ('run_uuid','registration_namespace'):need(not os.path.lexists(checked(v)),'fresh future leaf')
q['before']=cfg['before'];q['after']=cfg['after'];q['canonical_copies']=copies;q['pending_origin_refs']=refs;q['allocation']=allocation
q['controller_review_path']=str(ROOT/'execution/v2.4/receipts/W13/W13-03/desktop58_current_bound_scope_independent_review_codex'/uid/'review.json')
for row in q['negative_alias_declarations']:
    need(row['path'].count(old['allocation']['run_uuid'])==2,'exact both alias UID occurrences')
    row['path']=row['path'].replace(old['allocation']['run_uuid'],uid)
metadata=[]
for r in old['metadata_code_refs']:
    b=raw(r);name=Path(r['path']).name
    if name in ('scope_builder.py','prepare.py','register.py','run.py','seal.py','grant_preflight.py'):
        ast.parse(b);metadata.append(put(name,b))
    else: metadata.append(r)
need(len(metadata)==8,'metadata8 stable')
q['metadata_code_refs']=metadata
q.update(cfg['wldp_fields'])
ctor=raw(cfg['constructor_ref']);ast.parse(ctor)
ctorref=put('construct_root_inputs.desktop58.wldp.py',ctor)
allowed={'before','after','canonical_copies','pending_origin_refs','allocation','controller_review_path','negative_alias_declarations','metadata_code_refs'}
for k,v in old.items():
    if k not in allowed:need(q[k]==v,'preserved seed field '+k)
need(set(q)-set(old)=={'wldp_static_ref','wldp_candidate_report_ref'},'only added explicit resource fields')
allocref=save('root-allocation.actual.json',{'schema':'researchos.root-literal-allocation.v1','actor':'codex:/root','before':cfg['before'],'after':cfg['after'],'allocation':allocation,'caller_output':str(ROOT/'execution/v2.4/receipts/W13/W13-03/desktop58_root_terminal_closure_codex/baaf93516e9d42e2b583972e5a30df91'),'execution_authorized':False})
cb=save('canonical-before.json',{'entries':[{'canonical_path':r['path'],'ref':c} for r,c in zip(cfg['canonical_refs'],copies)]})
metaref=save('metadata-code-refs.selected.json',{'entries':metadata})
qr=save('root-construction.parameters.desktop58.json',q)
audit=save('literal-staging.actual.json',{'schema':'researchos.desktop58-literal-staging.v1','actor':'codex:/root','seed_ref':cfg['seed_ref'],'constructor_ref':ctorref,'constructor_review_ref':cfg['constructor_review_ref'],'failed_closure_review_ref':cfg['failed_closure_review_ref'],'canonical_before_ref':cb,'request_ref':qr,'metadata_ref':metaref,'allocation_ref':allocref,'changed_fields':sorted(allowed|{'wldp_static_ref','wldp_candidate_report_ref'}),'protected_fields_equal':True,'before':cfg['before'],'after':cfg['after'],'origin_count':len(refs),'canonical_writes':0,'product_calls':0,'formal_increment':0,'old_scope_rerun':False})
print(json.dumps({'request_ref':qr,'constructor_ref':ctorref,'audit_ref':audit,'allocation_ref':allocref,'canonical_before_ref':cb,'pending_origin_refs':refs,'before':cfg['before'],'after':cfg['after']},ensure_ascii=False))

