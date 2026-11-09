"""Receipt-only v6 constructor: AST and inverse bytes, no candidate execution."""
from pathlib import Path
import ast
import difflib
import hashlib
import json

ROOT=Path('D:/作品集/ResearchOS/research-os')
NS=ROOT/'execution/v2.4/receipts/W05/W05-99'
OLD=NS/'cli43_root_binding_preparation_revision_codex/c16c5b73941e4e8a89b189594e53b4c5'
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
    original=p.read_bytes(); text=original.decode('utf-8'); rows=[]
    for a,b in edits:
        if text.count(a)!=1:raise RuntimeError('nonunique exact source anchor')
        text=text.replace(a,b,1);rows.append({'old':a,'new':b})
    inverse=text
    for row in reversed(rows):
        if inverse.count(row['new'])!=1:raise RuntimeError('nonunique inverse anchor')
        inverse=inverse.replace(row['new'],row['old'],1)
    if inverse.encode('utf-8')!=original:raise RuntimeError('whole-file inverse mismatch')
    ast.parse(text,filename=name)
    result=write(name,text.encode('utf-8'))
    write(name+'.diff',''.join(difflib.unified_diff(original.decode('utf-8').splitlines(True),text.splitlines(True),fromfile=str(p),tofile=name)).encode('utf-8'))
    changes.append({'old_ref':ref(p),'new_ref':result,'edits':rows,'whole_original_inverse_bytes_equal':True})
    return result

old_module=OLD/'metadata_pipeline.v5.proposed.py'
if ref(old_module)['sha256']!='60c38bf6663a758c74f130a2fd0abd6bf21257a9348cf2225f4bf3d429975689':raise RuntimeError('v5 source pin')
old_stmt="    allowed=rows+[b[k] for k in ('runner_ref','launcher_ref','authorization_gate_ref','owned_process_helper_ref','debug_tree_helper_ref')]+b['metadata_code_refs']"
new_stmt="    for r in b['metadata_code_refs']: verify(r)\n    allowed=rows+[b[k] for k in ('runner_ref','launcher_ref','authorization_gate_ref','owned_process_helper_ref','debug_tree_helper_ref')]+[{'path':str(safe(r['path'])),'sha256':r['sha256'],'bytes':r['bytes']} for r in b['metadata_code_refs']]"
module=revise(old_module,'metadata_pipeline.v6.proposed.py',[(old_stmt,new_stmt)])
wrappers=[]
for name in ('scope_builder.py','prepare.py','register.py','run.py','seal.py','grant_preflight.py'):
    wrappers.append(revise(OLD/name,name,[
        (repr(str(old_module)),repr(str(OUT/'metadata_pipeline.v6.proposed.py'))),
        ('60c38bf6663a758c74f130a2fd0abd6bf21257a9348cf2225f4bf3d429975689',module['sha256'])]))
manifest=json.loads((OLD/'manifest.json').read_bytes())
if manifest['count']!=len(manifest['entries']):raise RuntimeError('original manifest count')
for item in manifest['entries']:
    a=ref(item['path'])
    if a['sha256']!=item['sha256'] or a['bytes']!=item['bytes']:raise RuntimeError('sealed v5 drift')
old_ast=ast.parse(old_module.read_bytes());new_ast=ast.parse((OUT/'metadata_pipeline.v6.proposed.py').read_bytes())
oldfunc={n.name:ast.dump(n,include_attributes=False) for n in old_ast.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
newfunc={n.name:ast.dump(n,include_attributes=False) for n in new_ast.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
if oldfunc.keys()!=newfunc.keys() or any(oldfunc[k]!=newfunc[k] for k in oldfunc if k!='runtime'):raise RuntimeError('unexpected function change')
projection=[]
for r in wrappers:
    p=Path(r['path']); relative=p.relative_to(ROOT).as_posix()
    if (ROOT/relative).resolve()!=p.absolute():raise RuntimeError('static wrapper canonical mapping')
    projection.append({'serialized_ref':{'path':relative,'sha256':r['sha256'],'bytes':r['bytes']},
        'runtime_allowlist_ref':r,'expected_observed_absolute_path':str(p.absolute()),'same_SHA_and_bytes':True})
save('six-wrapper-static-path-projection.json',{'entries':projection,'count':6,
    'kind':'static path/ref projection, not module_observation execution',
    'unknown_guard_unchanged':"need(bypath.get(os.path.normcase(p)) == row, 'Unpinned observed Python/OS resource: ' + p)",
    'candidate_module_or_helper_imported':False,'negative_runtime_controls':'NOT_RUN'})
save('inverse-and-static-audit.json',{'schema':'researchos.cli43-metadata-runtime-path-normalization.v1',
    'changes':changes,'AST_modules':7,'AST_success':True,'other_functions_byte_inverse_and_AST_unchanged':sorted(k for k in oldfunc if k!='runtime'),
    'changed_function':'runtime','changed_statements':2,'input_ref_bytes_fields_mutated':False,
    'local_metadata_refs_verified_before_path_projection':True,
    'six_wrapper_projection_ref':ref(OUT/'six-wrapper-static-path-projection.json'),
    'relative_exactrefs_prepare_logic_unchanged':True,'unknown_modules_still_rejected':True,
    'old_manifest_ref':ref(OLD/'manifest.json'),'old_members':manifest['count'],'old_drift':[],
    'candidate_import_execute':False,'Go_Git_SQL_DLL_helper_HTTP_model_calls':0,'new_failure_origins':[]})
unchanged={
 'binding_builder':ref(OLD/'build_binding.v5.proposed.py'),
 'scope_template':ref(OLD/'scope.v5.proposed.json'),
 'gate':ref(OLD/'authorization_gate.v5.proposed.py'),
 'runner':ref(NS/'cli43_root_binding_preparation_revision_codex/1496044d76eb4a919217533814612807/current43_runner.v4.proposed.py'),
 'launcher':ref(NS/'cli43_fresh_compiler_preparation_revision_codex/bb395255ecb14df6820b2e20631c9c39/launch.proposed.py')}
save('binding-instructions.json',{'metadata_module_ref':module,'new_wrapper_refs':wrappers,'reuse_unchanged_refs':unchanged,
    'Root_staging_rule':'Stage six wrappers byte-for-byte in the explicit new Root registration namespace; metadata_code_refs use repository-relative exact refs for prepare pin equality. Include the actual new module and wrapper files in the frozen public runtime inventory.',
    'runtime_only_conversion':'Each already verified metadata code ref gets a fresh object whose path is str(safe(original_path)); SHA and bytes copy exactly. Original binding refs remain unchanged.',
    'scope_template_has_no_metadata_module_ref':'No scope-template byte changes needed; future binding supplies the new metadata_code_refs and code inventory.',
    'future_registration_tuple':None,'future_run_uuid':None,'future_origin_cut_ref':None,'actual_cases':'NOT_RUN',
    'source_acceptance':False,'formal_increment':0})
save('handoff.json',{'schema':'researchos.cli43-metadata-v6-preparation-handoff.v1','actor':'codex:/root/command_queue_impl',
    'status':'PREPARATION_REPORTED_PENDING_NONAUTHOR_STATIC_REVIEW','writer_status':'STOPPED',
    'metadata_module_ref':module,'wrapper_refs':wrappers,'unchanged_refs':unchanged,
    'audit_ref':ref(OUT/'inverse-and-static-audit.json'),'binding_instructions_ref':ref(OUT/'binding-instructions.json'),
    'old_handoff_ref':ref(OLD/'handoff.json'),'old_manifest_ref':ref(OLD/'manifest.json'),
    'only_runtime_allowlist_local_delta':True,'AST_modules':7,'candidate_templates_executed':0,
    'product_source_canonical_index_cache_writes':0,'new_failure_origins':[],
    'future_registration_tuple':None,'future_resources_ref':None,'future_origin_cut_ref':None,
    'actual_Go_Git_SQL_DLL_helper_HTTP_model_calls':0,'source_acceptance':False,'formal_increment':0,
    'limits_and_policies_unchanged':['W05 reviewer identity','preflight-before-auth-directory','single verified byte consumption','immediate and final four-file CAS','3600/3300 and native limits','two-case roster and HTTP caps'],
    'limitation':'AST/whole-file inverse only, no execution or OS module-observation claim'})
members=[ref(p) for p in sorted(OUT.rglob('*')) if p.is_file()]
save('manifest.json',{'entries':members,'count':len(members),'excluded_only_self':True})
print(json.dumps({'handoff':ref(OUT/'handoff.json'),'manifest':ref(OUT/'manifest.json'),'module':module,'wrappers':wrappers,'AST_modules':7,'new_failures':0},ensure_ascii=False))
