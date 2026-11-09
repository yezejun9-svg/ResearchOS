"""Receipt-only construction and AST inspection; never executes a candidate."""
from pathlib import Path
import ast
import difflib
import hashlib
import json

ROOT=Path('D:/作品集/ResearchOS/research-os')
NS=ROOT/'execution/v2.4/receipts/W05/W05-99'
OUT=Path(__file__).absolute().parent
V4=NS/'cli43_root_binding_preparation_revision_codex/1496044d76eb4a919217533814612807'
V3=NS/'cli43_root_binding_preparation_codex/629d2cb794ab4ae4a04a1db9d8a3f8ef'
V2=NS/'cli43_fresh_compiler_preparation_revision_codex/bb395255ecb14df6820b2e20631c9c39'
REVIEW=NS/'cli43_root_binding_static_independent_review_codex/f3fcbb1b93a14bf5b289082612b26a9c/review.json'
changes=[]

def ref(p):
    p=Path(p); b=p.read_bytes()
    return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def write(name,b):
    with (OUT/name).open('xb') as f:f.write(b)
    return ref(OUT/name)
def save(name,d):return write(name,(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
def revision(source,name,edits):
    original=source.read_bytes(); text=original.decode('utf-8'); recorded=[]
    for old,new in edits:
        if text.count(old)!=1:raise RuntimeError('nonunique constructor anchor '+name)
        text=text.replace(old,new,1);recorded.append({'old':old,'new':new})
    inverse=text
    for e in reversed(recorded):
        if inverse.count(e['new'])!=1:raise RuntimeError('nonunique inverse '+name)
        inverse=inverse.replace(e['new'],e['old'],1)
    if inverse.encode('utf-8')!=original:raise RuntimeError('inverse byte mismatch')
    ast.parse(text,filename=name)
    target=write(name,text.encode('utf-8'))
    write(name+'.diff',''.join(difflib.unified_diff(original.decode('utf-8').splitlines(True),text.splitlines(True),fromfile=str(source),tofile=name)).encode('utf-8'))
    changes.append({'original_ref':ref(source),'new_ref':target,'edits':recorded,'inverse_original_bytes_equal':True})
    return target

if ref(REVIEW)['sha256']!='3ec092da679105198c872c001560d3d5576b47f430aea143a453565f51c1eaa4':raise RuntimeError('actual v3 review SHA')
gate=revision(V3/'authorization_gate.v3.proposed.py','authorization_gate.v5.proposed.py',[
    ("reg_review['reviewer'] != 'codex:/root'", "reg_review['reviewer'] == 'codex:/root/w05_merge_review'")])
old=(V4/'metadata_pipeline.v4.proposed.py').read_text(encoding='utf-8')
start=old.index('def grant(b,output,scope_ref):\n');end=old.index('\ndef main(mode):\n',start)
grant_old=old[start:end]
grant_new=(OUT/'grant-function.v5.py.txt').read_text(encoding='utf-8')
metadata=revision(V4/'metadata_pipeline.v4.proposed.py','metadata_pipeline.v5.proposed.py',[
    ("OWNED_GRANT_ROOT = None", "OWNED_GRANT_ROOT = None\nOWNED_GRANT_PREFLIGHT_ROOT = None"),
    ("7933e679bbda76df1aca4f21119d34a5b18791343d4b442481e19ed1df0c85b1",gate['sha256']),
    ("    safe(b['controller_review_path'],False)",
     "    safe(b['controller_review_path'],False)\n    pf=safe(b['new_grant_preflight_root'],False)\n    need(pf.is_relative_to(RECEIPTS) and b['run_uuid'] in pf.name,'explicit bounded preflight UUID leaf')\n    roots=[safe(b[k],False) for k in ('new_output_root','new_wrapper_root','new_export_root','new_authorization_root')]\n    need(all(pf!=p and not pf.is_relative_to(p) and not p.is_relative_to(pf) for p in roots),'preflight disjoint from four run roots')"),
    ("'run_uuid','new_output_root','new_wrapper_root','new_export_root','new_authorization_root',",
     "'run_uuid','new_output_root','new_wrapper_root','new_export_root','new_authorization_root','new_grant_preflight_root',"),
    ("d['reviewer']!='codex:/root'", "d['reviewer']=='codex:/root/w05_merge_review'"),
    (grant_old,grant_new),
    ("            if OWNED_GRANT_ROOT is not None:\n                save(OWNED_GRANT_ROOT/'failure.origin.json',first)",
     "            if OWNED_GRANT_PREFLIGHT_ROOT is not None:\n                save(OWNED_GRANT_PREFLIGHT_ROOT/'failure.origin.json',first)\n                members=[pin(p) for p in sorted(OWNED_GRANT_PREFLIGHT_ROOT.rglob('*')) if p.is_file()]\n                save(OWNED_GRANT_PREFLIGHT_ROOT/'manifest.partial.json',{'entries':members,'count':len(members),'grant_usable':False})\n            if OWNED_GRANT_ROOT is not None:\n                save(OWNED_GRANT_ROOT/'failure.origin.json',first)"),
    ("            elif out is not None: save(out/('failure.'+mode+'.json'),first)",
     "            elif OWNED_GRANT_PREFLIGHT_ROOT is None and out is not None: save(out/('failure.'+mode+'.json'),first)")])

builder=revision(V4/'build_binding.v4.proposed.py','build_binding.v5.proposed.py',[
    ("7933e679bbda76df1aca4f21119d34a5b18791343d4b442481e19ed1df0c85b1",gate['sha256']),
    ("'new-export-root','new-authorization-root','output'):","'new-export-root','new-authorization-root','new-grant-preflight-root','output'):"),
    ("('new_output_root','new_wrapper_root','new_export_root','new_authorization_root')]",
     "('new_output_root','new_wrapper_root','new_export_root','new_authorization_root','new_grant_preflight_root')]"),
    ("len(set(roots))==4", "len(set(roots))==5"),
    ("    need(all(not x.is_relative_to(y) for x in roots for y in roots if x!=y),'overlap')",
     "    need(all(not x.is_relative_to(y) for x in roots for y in roots if x!=y),'overlap')\n    need(roots[4].is_relative_to(ROOT/'execution/v2.4/receipts/W05/W05-99'),'preflight receipt boundary')"),
    ("'new_output_root','new_wrapper_root','new_export_root','new_authorization_root'):",
     "'new_output_root','new_wrapper_root','new_export_root','new_authorization_root','new_grant_preflight_root'):")])

wrappers=[]
for name in ('scope_builder.py','prepare.py','register.py','run.py','seal.py','grant_preflight.py'):
    wrappers.append(revision(V4/name,name,[
        (repr(str(V4/'metadata_pipeline.v4.proposed.py')),repr(str(OUT/'metadata_pipeline.v5.proposed.py'))),
        ('aa94f1633ade4f940c15651cf766a3899f7a172a99cadadb47eec5a4319f7478',metadata['sha256'])]))
scope=json.loads((V4/'scope.v4.proposed.json').read_bytes());scope['authorization_gate_ref']=gate;scope['new_grant_preflight_root']=None
scope_ref=save('scope.v5.proposed.json',scope)
prefix=[]
for folder,mf,count in [(V2,'manifest.complete.json',25),(V3,'manifest.json',20),(V4,'manifest.json',None)]:
    m=json.loads((folder/mf).read_bytes())
    if m['count']!=len(m['entries']) or (count is not None and m['count']!=count):raise RuntimeError('old manifest count')
    for r in m['entries']:
        a=ref(Path(r['path']))
        if a['sha256']!=r['sha256'] or a['bytes']!=r['bytes']:raise RuntimeError('old sealed prefix drift')
    prefix.append({'manifest_ref':ref(folder/mf),'members':m['count'],'drift':[]})
save('exact-differences-and-inverse.json',{'changes':changes,'scope_changed_fields_only':['authorization_gate_ref','new_grant_preflight_root:null'],
     'old_manifest_prefixes':prefix,'candidate_import_execute':False})
save('findings-mapping.json',{'independent_review_ref':ref(REVIEW),'findings':[
    {'finding':'single raw / consume verified bytes','status':'PRESERVED_V4','refs':[ref(V4/'current43_runner.v4.proposed.py'),builder,metadata]},
    {'finding':'final long-guard canonical recheck','status':'PRESERVED_V4','ref':metadata,'per_replace_original_guard_unchanged':True},
    {'finding':'authority/Git facts before auth leaf','status':'V5_STATIC_REVISION','ref':metadata,'new_scope_field':'new_grant_preflight_root'},
    {'finding':'actual nonauthor identity','status':'V5_STATIC_REVISION','refs':[gate,metadata],'exact_reviewer':'codex:/root/w05_merge_review'}],
    'actual_negative_controls':'NOT_RUN','source_acceptance':False})
save('timing-and-failure-contract.json',{
 'order':['validate bounded fifth leaf and disjoint/fresh roots','exclusive preflight leaf, no authorization leaf',
          'sealed registration + actual four canonical snapshots and same live bytes','admission real owned Git head/status/index + live4',
          'exclusive auth leaf only after prior facts','byte-identical canonical copies and sealed authority revalidation',
          'grant-final independent new owned Git head/status/index + Python/OS after point observation',
          'byte-identical original fact copies and copy map','immediate live4 comparison','grant write then gate verification','completed + manifests; no launcher execution'],
 'fact_copy_semantics':'All copied original JSON/raw bytes remain identical. Final prelaunch JSON retains original preflight Git raw refs; copy map separately pins identical auth mirrors. Canonical and observation refs consumed by gate point to auth copies.',
 'time_semantics':'Each Git round has actual start/end recorded at future execution. They are point-in-time facts, not continuous repository or OS lifecycle proof. Final round uses newly executed Git, never substitutes admission dict.',
 'failure_semantics':'Before preflight ownership: original stderr fallback. Once preflight owned: first cause + partial manifest retained. Before admission failure: auth leaf absent. After admission failure: possible auth leaf with no usable completed grant; original children raw/result retained. No retry or rollback.',
 'actual_stage_native_exit':'NULL unless an actual owned child result exists, which is recorded in its invocation rather than inherited by Python stages',
 'future_Git_children':6,'each_Git_timeout_seconds':30,'metadata_child_timeout_seconds':600,'original_product_inner_seconds':3300,'original_product_outer_seconds':3600,
 'actual_product_executions':0,'actual_Git_children_executed_by_this_preparation':0,'actual_grants':0})
save('handoff.json',{'schema':'researchos.cli43-root-binding-v5-preparation-handoff.v1','actor':'codex:/root/command_queue_impl',
 'status':'PREPARATION_REPORTED_PENDING_NONAUTHOR_REVIEW','writer_status':'STOPPED',
 'gate_ref':gate,'scope_ref':scope_ref,'metadata_pipeline_ref':metadata,'binding_builder_ref':builder,'wrapper_refs':wrappers,
 'unchanged_runner_ref':ref(V4/'current43_runner.v4.proposed.py'),'unchanged_launcher_ref':ref(V2/'launch.proposed.py'),
 'v4_handoff_ref':ref(V4/'handoff.json'),'independent_v3_review_ref':ref(REVIEW),
 'finding_mapping_ref':ref(OUT/'findings-mapping.json'),'timing_contract_ref':ref(OUT/'timing-and-failure-contract.json'),
 'inverse_ref':ref(OUT/'exact-differences-and-inverse.json'),'old_manifest_prefixes':prefix,
 'mandatory_new_CLI_argument':'--new-grant-preflight-root (explicit Root bounded receipts leaf containing run UUID; disjoint from all four execution roots)',
 'future_registration_before':None,'future_registration_after':None,'future_origin_cut_ref':None,
 'future_runtime_resources_ref':None,'future_compiler_resources_ref':None,'new_grant_preflight_root':None,
 'AST_modules':len(changes),'candidate_import_execute':False,'Go_SQL_HTTP_Node_DLL_MODEL_calls':0,
 'source_canonical_index_writes':0,'new_failure_origins':[],'actual_cases':'NOT_RUN','source_acceptance':False,'formal_increment':0,
 'no_new_review_hash_cycle':'scope binds review path and full v5 scope SHA is signed later; exact review ref comes from sealed CP',
 'limitations':['AST/inverse only; no candidate/native/SQL/HTTP execution','Root full actual resources and explicit tuples still required','Directory creation/copy never establishes authority by itself','Root must require producer completed proof and actual success before separate once-only launcher']})
members=[ref(p) for p in sorted(OUT.rglob('*')) if p.is_file()]
save('manifest.json',{'entries':members,'count':len(members),'excluded_only_self':True})
print(json.dumps({'handoff':ref(OUT/'handoff.json'),'manifest':ref(OUT/'manifest.json'),'gate':gate,'scope':scope_ref,'metadata':metadata,'AST_modules':len(changes),'new_failure_origins':0},ensure_ascii=False))
