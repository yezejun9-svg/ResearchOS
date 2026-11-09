"""Owned preparation constructor only. Reads public sealed source, writes this new namespace.
Does not import or execute any generated candidate.
"""
from pathlib import Path
import ast
import difflib
import hashlib
import json

ROOT=Path('D:/作品集/ResearchOS/research-os')
NS=ROOT/'execution/v2.4/receipts/W05/W05-99'
OUT=Path(__file__).absolute().parent
V3=NS/'cli43_root_binding_preparation_codex/629d2cb794ab4ae4a04a1db9d8a3f8ef'
V2=NS/'cli43_fresh_compiler_preparation_revision_codex/bb395255ecb14df6820b2e20631c9c39'
changes=[]

def ref(p):
    p=Path(p);b=p.read_bytes()
    return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}

def write(name,raw):
    with (OUT/name).open('xb') as f:f.write(raw)
    return ref(OUT/name)

def save(name,d):return write(name,(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))

def revision(source,name,edits):
    original=source.read_bytes();text=original.decode('utf-8'); done=[]
    for old,new in edits:
        if text.count(old)!=1:raise RuntimeError('nonunique exact constructor anchor: '+name)
        text=text.replace(old,new,1);done.append({'old':old,'new':new})
    inverse=text
    for item in reversed(done):
        if inverse.count(item['new'])!=1:raise RuntimeError('inverse anchor: '+name)
        inverse=inverse.replace(item['new'],item['old'],1)
    if inverse.encode('utf-8')!=original:raise RuntimeError('whole original inverse mismatch')
    ast.parse(text,filename=name)
    result=write(name,text.encode('utf-8'))
    diff=''.join(difflib.unified_diff(original.decode('utf-8').splitlines(True),text.splitlines(True),fromfile=str(source),tofile=name))
    write(name+'.diff',diff.encode('utf-8'))
    changes.append({'original_ref':ref(source),'new_ref':result,'edits':done,'inverse_original_whole_bytes_equal':True,'AST_ONLY':True})
    return result

runner=revision(V2/'current43_runner.proposed.py','current43_runner.v4.proposed.py',[(
"def verify(ref):\n    need(set(ref) == {'path', 'sha256', 'bytes'} and pin(ref['path']) == ref, 'Immutable input mismatch')\n    return Path(ref['path']).read_bytes()",
"def verify(ref):\n    need(isinstance(ref, dict) and set(ref) == {'path', 'sha256', 'bytes'}, 'Immutable input ref shape')\n    need(isinstance(ref['path'], str) and type(ref['bytes']) is int and ref['bytes'] >= 0\n         and isinstance(ref['sha256'], str) and len(ref['sha256']) == 64\n         and all(c in '0123456789abcdef' for c in ref['sha256']), 'Immutable input ref fields')\n    p = Path(ref['path']).absolute()\n    need(str(p) == ref['path'], 'Immutable input absolute path spelling')\n    raw = p.read_bytes()\n    need(len(raw) == ref['bytes'] and hashlib.sha256(raw).hexdigest() == ref['sha256'], 'Immutable input mismatch')\n    return raw")])

metadata=revision(V3/'metadata_pipeline.proposed.py','metadata_pipeline.v4.proposed.py',[
("job_ok(result); records.append(item); outputs.append(a.read_bytes())",
 "job_ok(result); records.append(item); outputs.append(verify(item['stdout_ref']))"),
("    unchanged_reads(); git_guard(b,output,'register-after')\n    save(output/'canonical-write.verified.json'",
 "    unchanged_reads(); git_guard(b,output,'register-after')\n    need(all((ROOT/x).read_bytes()==r for x,r in zip(CANON,desired)),'post-source-guard final four CAS')\n    save(output/'canonical-write.verified.json'"),
("    git_guard(b,output,'seal')\n    save(output/'registration-audit.json'",
 "    git_guard(b,output,'seal')\n    need(all((ROOT/x).read_bytes()==r for x,r in zip(CANON,desired)),'post-source-guard seal four CAS')\n    save(output/'registration-audit.json'")])

builder=revision(V3/'build_binding.proposed.py','build_binding.v4.proposed.py',[
("def pinned(value):", "VERIFIED_BYTES = {}\n\ndef verified_bytes(ref):\n    p=Path(ref['path']); p=p if p.is_absolute() else ROOT/p\n    return VERIFIED_BYTES[str(p.absolute())]\n\ndef pinned(value):"),
("    raw=p.read_bytes(); need(len(raw)==r['bytes'] and hashlib.sha256(raw).hexdigest()==r['sha256'],'ref bytes')\n    return r",
 "    raw=p.read_bytes(); need(len(raw)==r['bytes'] and hashlib.sha256(raw).hexdigest()==r['sha256'],'ref bytes')\n    key=str(p.absolute())\n    if key in VERIFIED_BYTES: need(VERIFIED_BYTES[key]==raw,'public input drift during binding')\n    VERIFIED_BYTES[key]=raw\n    return r"),
("s=strict(safe(a.scope_template_ref['path']).read_bytes())", "s=strict(verified_bytes(a.scope_template_ref))"),
("code=strict(safe(a.metadata_code_refs_ref['path']).read_bytes())['entries']", "code=strict(verified_bytes(a.metadata_code_refs_ref))['entries']")])

wrappers=[]
for name in ('scope_builder.py','prepare.py','register.py','run.py','seal.py','grant_preflight.py'):
    wrappers.append(revision(V3/name,name,[
        (repr(str(V3/'metadata_pipeline.proposed.py')),repr(str(OUT/'metadata_pipeline.v4.proposed.py'))),
        ("80fd67893401eed8821139c49ba82c8b2aab87ac1ab5fa5bdc70255bbe1bda93",metadata['sha256'])]))

scope=json.loads((V3/'scope.v3.proposed.json').read_bytes())
prior_runner=scope['runner_ref'];scope['runner_ref']=runner
scope_ref=save('scope.v4.proposed.json',scope)
save('scope-delta.json',{'old_scope_ref':ref(V3/'scope.v3.proposed.json'),'new_scope_ref':scope_ref,
    'only_changed_field':'runner_ref','before':prior_runner,'after':runner,'all_other_scope_fields_equal':True})

prefix=[]
for folder,name,count in ((V3,'manifest.json',20),(V2,'manifest.complete.json',25)):
    m=json.loads((folder/name).read_bytes())
    if len(m['entries'])!=m['count'] or m['count']!=count:raise RuntimeError('old manifest count')
    for r in m['entries']:
        actual=ref(Path(r['path']))
        if actual['sha256']!=r['sha256'] or actual['bytes']!=r['bytes']:raise RuntimeError('old member drift')
    prefix.append({'manifest_ref':ref(folder/name),'members':count,'drift':[]})
save('exact-differences-and-inverse.json',{'changes':changes,'old_prefixes':prefix})
save('static-audit.json',{'schema':'researchos.cli43-single-read-and-cas-static-revision.v1',
 'actor':'codex:/root/command_queue_impl','candidate_imported':False,'candidate_executed':False,
 'AST_modules':len(changes),'Python_AST_success':True,'new_actual_failure_origins':[],
 'unchanged_refs':{'gate_v3':ref(V3/'authorization_gate.v3.proposed.py'),'launcher':ref(V2/'launch.proposed.py')},
 'inspection':{
   'runner_verify':'one read; exact dict keys, absolute path spelling, type/size/SHA check; returns that same raw',
   'metadata_verify_doc_load_module':'already same raw consumed; unchanged',
   'binding_builder':'two prior parse-after-independent-read sites now consume cached already verified bytes; repeated normalized path drift rejected',
   'metadata_Git_raw':'consumed stdout now verified against captured ref instead of unchecked second read',
   'per_replace':'unchanged: Git/source guard followed immediately by all-four original/desired-prefix CAS, then replace',
   'registration_final':'added all-four check after final Git/source guard before verified receipt',
   'seal_final':'added all-four check after final Git/source guard before registration audit',
   'grant':'already final all-four check after source/runtime guard; unchanged',
   'gate_reader':'already verifies/caches/compares the raw it returns; unchanged',
   'launcher_module':'already compiles same verified raw; unchanged'},
 'unchanged_behavior':['HTTP observations','business assertions','two case roster','native counts','32+32/128 caps','3300 inner/3600 outer','Go individual deadlines','source/a510','future NULL resource and tuple binding'],
 'limitations':['AST/static inverse only; no race test or candidate run','Not atomic multi-file lock: immediate CAS limits the known gap; Root remains sole canonical writer','Actual full resources and all future Root grants still required']})
save('handoff.json',{'schema':'researchos.cli43-root-binding-v4-preparation-handoff.v1','actor':'codex:/root/command_queue_impl',
 'status':'PREPARATION_REPORTED_PENDING_NONAUTHOR_REVIEW','writer_status':'STOPPED',
 'runner_ref':runner,'metadata_pipeline_ref':metadata,'binding_builder_ref':builder,'scope_ref':scope_ref,'wrapper_refs':wrappers,
 'unchanged_gate_ref':ref(V3/'authorization_gate.v3.proposed.py'),'unchanged_launcher_ref':ref(V2/'launch.proposed.py'),
 'v3_handoff_ref':ref(V3/'handoff.json'),'old_manifest_prefixes':prefix,
 'static_audit_ref':ref(OUT/'static-audit.json'),'inverse_and_exact_diff_ref':ref(OUT/'exact-differences-and-inverse.json'),
 'future_before':None,'future_after':None,'future_origin_cut_ref':None,'future_runtime_resources_ref':None,'future_compiler_resources_ref':None,
 'current43_authority_ref':None,'controller_review_ref':None,'actual_cases':'NOT_RUN','model_SQL_HTTP_Go_Node_DLL_calls':0,
 'canonical_product_source_index_writes':0,'source_acceptance':False,'formal_increment':0,'counter_reset':False})
entries=[ref(p) for p in sorted(OUT.rglob('*')) if p.is_file()]
save('manifest.json',{'entries':entries,'count':len(entries),'excluded_only_self':True})
print(json.dumps({'handoff':ref(OUT/'handoff.json'),'manifest':ref(OUT/'manifest.json'),'runner':runner,'metadata':metadata,'builder':builder,'scope':scope_ref,'AST_modules':len(changes),'old_members_unchanged':45,'new_failures':0},ensure_ascii=False))
