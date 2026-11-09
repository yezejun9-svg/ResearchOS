"""Pure receipt construction/AST inspection; no generated candidate is imported or run."""
from pathlib import Path
import ast
import difflib
import hashlib
import json

ROOT=Path('D:/作品集/ResearchOS/research-os')
NS=ROOT/'execution/v2.4/receipts/W05/W05-99'
OLD=NS/'cli43_root_binding_preparation_revision_codex/65d40dc010de45a3a06485b0b9a2c37b'
V5=NS/'cli43_root_binding_preparation_revision_codex/c16c5b73941e4e8a89b189594e53b4c5'
OUT=Path(__file__).absolute().parent
changes=[]

def ref(p):
    p=Path(p);raw=p.read_bytes()
    return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def write(name,raw):
    with (OUT/name).open('xb') as f:f.write(raw)
    return ref(OUT/name)
def save(name,value):return write(name,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
def revise(p,name,edits):
    raw=p.read_bytes();text=raw.decode('utf-8');rows=[]
    for old,new in edits:
        if text.count(old)!=1:raise RuntimeError('nonunique exact anchor '+name)
        text=text.replace(old,new,1);rows.append({'old':old,'new':new})
    inverse=text
    for r in reversed(rows):
        if inverse.count(r['new'])!=1:raise RuntimeError('nonunique inverse '+name)
        inverse=inverse.replace(r['new'],r['old'],1)
    if inverse.encode('utf-8')!=raw:raise RuntimeError('whole-file inverse bytes mismatch')
    ast.parse(text,filename=name)
    result=write(name,text.encode('utf-8'))
    write(name+'.diff',''.join(difflib.unified_diff(raw.decode('utf-8').splitlines(True),text.splitlines(True),fromfile=str(p),tofile=name)).encode('utf-8'))
    changes.append({'old_ref':ref(p),'new_ref':result,'edits':rows,'inverse_whole_original_bytes_equal':True})
    return result

old_module=OLD/'metadata_pipeline.v6.proposed.py'
if ref(old_module)['sha256']!='10f179c906ed5a0ed3b551fac06252e54fe2a21579c27b11c8f7c1499ce4f950':raise RuntimeError('original v6 SHA')
module=revise(old_module,'metadata_pipeline.v7.proposed.py',[(
    '    observation=util.module_observation(allowed,helper)\n    return helper,lock,save(output/(label+\'.json\'),observation)',
    '    observation=util.module_observation(allowed,helper)\n    observation[\'all_observed_inputs_pre_pinned\']=True\n    return helper,lock,save(output/(label+\'.json\'),observation)')])
wrappers=[]
for name in ('scope_builder.py','prepare.py','register.py','run.py','seal.py','grant_preflight.py'):
    wrappers.append(revise(OLD/name,name,[
        (repr(str(old_module)),repr(str(OUT/'metadata_pipeline.v7.proposed.py'))),
        ('10f179c906ed5a0ed3b551fac06252e54fe2a21579c27b11c8f7c1499ce4f950',module['sha256'])]))
old_ast=ast.parse(old_module.read_bytes());new_ast=ast.parse((OUT/'metadata_pipeline.v7.proposed.py').read_bytes())
functions=lambda tree:{n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
a=functions(old_ast);b=functions(new_ast)
if a.keys()!=b.keys() or any(a[k]!=b[k] for k in a if k!='runtime'):raise RuntimeError('other function changed')
prefix=[]
for base in (OLD,V5):
    m=json.loads((base/'manifest.json').read_bytes())
    if m['count']!=len(m['entries']):raise RuntimeError('old manifest count')
    for row in m['entries']:
        actual=ref(row['path'])
        if (actual['sha256'],actual['bytes'])!=(row['sha256'],row['bytes']):raise RuntimeError('old member drift')
    prefix.append({'manifest_ref':ref(base/'manifest.json'),'members':m['count'],'drift':[]})

proof=OUT/'producer-consumer-chain-review.json'
if not proof.is_file():raise RuntimeError('complete static producer/consumer coordination receipt required before sealing')
review=json.loads(proof.read_bytes())
if review['static_complete'] is not True or review['additional_code_changes_required']!=[]:
    raise RuntimeError('producer/consumer compatibility still open')
save('inverse-and-static-audit.json',{'schema':'researchos.cli43-metadata-v7-observation-marker.v1','changes':changes,
    'AST_modules':7,'AST_success':True,'only_changed_function':'runtime','only_new_producer_field':'all_observed_inputs_pre_pinned',
    'marker_assignment_follows_successful_strict_observation':True,'unknown_path_hash_or_bytes_guard_unchanged':True,
    'point_in_time_only_unchanged':True,'Python_lifecycle_proof_false_unchanged':True,
    'all_other_functions_AST_equal':sorted(k for k in a if k!='runtime'),'old_manifest_prefixes':prefix,
    'complete_static_chain_review_ref':ref(proof),'candidate_import_execute':False,'new_failure_origins':[]})
unchanged=json.loads((OLD/'handoff.json').read_bytes())['unchanged_refs']
for item in unchanged.values():
    actual=ref(item['path'])
    if actual['sha256']!=item['sha256'] or actual['bytes']!=item['bytes']:raise RuntimeError('preserved component drift')
save('binding-instructions.json',{'metadata_module_ref':module,'new_wrapper_refs':wrappers,'unchanged_refs':unchanged,
    'Root_metadata_code_refs':'Remain repository-relative exact refs for prepare; runtime v6 absolute allowlist conversion retained.',
    'scope_ref':'Root must supply ROOT-relative exact ref as agreed; producer template does not guess or rewrite Root refs.',
    'runtime_resources':'Root full explicit runtime inventory must include actual 6 staged wrappers + new metadata module + original binder ABS refs, with exact hashes. No fixed resource count embedded here.',
    'future_registration_tuple':None,'future_run_uuid':None,'future_origin_cut_ref':None,'actual_cases':'NOT_RUN'})
save('handoff.json',{'schema':'researchos.cli43-metadata-v7-preparation-handoff.v1','actor':'codex:/root/command_queue_impl',
    'status':'PREPARATION_REPORTED_PENDING_NONAUTHOR_STATIC_REVIEW','writer_status':'STOPPED','metadata_module_ref':module,
    'wrapper_refs':wrappers,'unchanged_refs':unchanged,'audit_ref':ref(OUT/'inverse-and-static-audit.json'),
    'producer_consumer_review_ref':ref(proof),'binding_instructions_ref':ref(OUT/'binding-instructions.json'),
    'old_handoff_ref':ref(OLD/'handoff.json'),'old_manifest_prefixes':prefix,
    'new_code_delta':'one marker assignment after strict module_observation returns successfully; wrapper module path/SHA only',
    'AST_modules':7,'candidate_templates_executed':0,'Go_Git_SQL_HTTP_DLL_helper_model_calls':0,
    'source_canonical_cache_index_writes':0,'new_failure_origins':[],'future_registration_tuple':None,
    'future_resources_ref':None,'future_origin_cut_ref':None,'actual_cases':'NOT_RUN','source_acceptance':False,'formal_increment':0,
    'limits_unchanged':['preflight ordering','W05 identity','two-file write/four-file CAS','single verified raw','2 cases','HTTP bounds','3600/3300/Go limits'],
    'limitation':'Static producer/consumer field audit and AST/inverse proof only; no native/runtime qualification'})
members=[ref(p) for p in sorted(OUT.rglob('*')) if p.is_file()]
save('manifest.json',{'entries':members,'count':len(members),'excluded_only_self':True})
print(json.dumps({'handoff':ref(OUT/'handoff.json'),'manifest':ref(OUT/'manifest.json'),'module':module,'wrappers':wrappers,'AST_modules':7,'new_failures':0},ensure_ascii=False))
