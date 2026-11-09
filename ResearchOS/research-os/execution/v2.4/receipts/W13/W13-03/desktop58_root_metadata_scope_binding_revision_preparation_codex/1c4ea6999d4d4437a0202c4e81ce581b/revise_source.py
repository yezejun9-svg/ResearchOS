"""Pure-IO source revision. No prepared controller import or execution."""
import ast
import hashlib
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
ROOT=Path('D:/作品集/ResearchOS/research-os')
BASE=Path(__file__).resolve().parent
OLD=ROOT/'execution/v2.4/receipts/W13/W13-03/desktop58_root_metadata_binding_preparation_codex/a03b8a59d79049ae87694932ac40ce5d'
def need(v,m):
    if not v: raise RuntimeError(m)
def pin(p):
    raw=p.read_bytes()
    return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def replace_one(s,old,new):
    need(s.count(old)==1,'source anchor not unique')
    return s.replace(old,new,1)
def write(name,raw):
    with (BASE/name).open('xb') as f: f.write(raw)
    return pin(BASE/name)
def save(name,obj):
    return write(name,(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())
need(sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode,'pinned flags')
for p in [BASE,OLD]:
    for q in [p,*p.parents]:
        if q.exists():need(not q.is_symlink() and not(getattr(q.lstat(),'st_file_attributes',0)&0x400),'reparse')
        if q==ROOT:break
src=(OLD/'metadata_pipeline.desktop58.proposed.py').read_bytes()
need(hashlib.sha256(src).hexdigest()=='15df7a4c54a58df2d11036ae7a1a1c8080ef6461264e75a3c89f52db1c795cff','old pipeline pin')
text=src.decode()
changes=[]
def change(old,new):
    global text
    text=replace_one(text,old,new);changes.append({'old':old,'new':new})
change("'origin_cut_ref','canonical_before_ref','source_inputs_ref','failure_prefix430_ref'):\n        need", "'origin_cut_ref','canonical_before_ref','source_inputs_ref','failure_prefix430_ref','scope_template_ref'):\n        need")
change("def scope_build(b, scope_template_ref, dest):\n    s=doc(scope_template_ref)\n", "def project_scope(b, template):\n    s=copy.deepcopy(template)\n")
change("    return save(dest,s)\n\ndef prepare(b, scope_ref, output):", """    basis=('scope_template_ref','runtime_resources_ref','compiler_resources_ref','current43_authority_ref',
        'origin_cut_ref','canonical_before_ref','source_inputs_ref','failure_prefix430_ref')
    s['Root_metadata_binding_inputs']={'refs':{k:b[k] for k in basis},
        'metadata_code_refs':copy.deepcopy(b['metadata_code_refs'])}
    return s

def reviewed_scope_match(b, scope):
    # Compare every projected field; the later review REF remains outside the scope.
    need(scope==project_scope(b,doc(b['scope_template_ref'])),
         'Final Root metadata binding differs from independently reviewed full scope')

def scope_build(b, scope_template_ref, dest):
    need(scope_template_ref==b['scope_template_ref'],'Scope template binding differs')
    return save(dest,project_scope(b,doc(scope_template_ref)))

def prepare(b, scope_ref, output):""")
change("    s=doc(scope_ref); need(s['registration_namespace']==output.relative_to(ROOT).as_posix(),'registration directory')\n    gate=", "    s=doc(scope_ref)\n    reviewed_scope_match(b,s)\n    need(s['registration_namespace']==output.relative_to(ROOT).as_posix(),'registration directory')\n    gate=")
change("    scope=doc(scope_ref)\n    need(scope['new_grant_preflight_root']", "    scope=doc(scope_ref)\n    reviewed_scope_match(b,scope)\n    need(scope['new_grant_preflight_root']")
reversed_text=text
for h in reversed(changes): reversed_text=replace_one(reversed_text,h['new'],h['old'])
need(reversed_text.encode()==src,'whole inverse')
old_funcs={n.name:ast.dump(n,include_attributes=False) for n in ast.parse(src).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
new_funcs={n.name:ast.dump(n,include_attributes=False) for n in ast.parse(text).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
modified={'binding','scope_build','prepare','grant'}
unchanged=[k for k in old_funcs if k not in modified]
need(all(new_funcs[k]==old_funcs[k] for k in unchanged),'unrelated function AST changed')
need(set(new_funcs)-set(old_funcs)=={'project_scope','reviewed_scope_match'},'new definitions')
pipeline=write('metadata_pipeline.desktop58.bound.v2.proposed.py',text.encode())
builder_raw=(OLD/'build_binding.desktop58.proposed.py').read_bytes()
need(hashlib.sha256(builder_raw).hexdigest()=='ae09196949b50b452b6d0429123865b22fabadeebd960dd3db0b2fd2447cbe96','builder pin')
builder_old=builder_raw.decode()
builder_new=replace_one(builder_old,"    b['toolchain_lock_ref']=a.toolchain_lock_ref\n","    b['toolchain_lock_ref']=a.toolchain_lock_ref\n    b['scope_template_ref']=a.scope_template_ref\n")
need(builder_new.replace("    b['scope_template_ref']=a.scope_template_ref\n",'',1).encode()==builder_raw,'builder inverse')
ast.parse(builder_new)
builder=write('build_binding.desktop58.bound.v2.proposed.py',builder_new.encode())
wrappers=[]
for name in ('scope_builder.py','prepare.py','register.py','run.py','seal.py','grant_preflight.py'):
    raw=(OLD/name).read_bytes();original=raw.decode()
    oldpath=repr(str(OLD/'metadata_pipeline.desktop58.proposed.py'))
    newpath=repr(pipeline['path'])
    revised=replace_one(original,oldpath,newpath)
    revised=replace_one(revised,'15df7a4c54a58df2d11036ae7a1a1c8080ef6461264e75a3c89f52db1c795cff',pipeline['sha256'])
    inverse=revised.replace(pipeline['sha256'],'15df7a4c54a58df2d11036ae7a1a1c8080ef6461264e75a3c89f52db1c795cff',1).replace(newpath,oldpath,1)
    need(inverse.encode()==raw,'wrapper inverse')
    ast.parse(revised)
    wrappers.append(write(name,revised.encode()))
save('inverse.json',{'old_pipeline_ref':pin(OLD/'metadata_pipeline.desktop58.proposed.py'),'new_pipeline_ref':pipeline,
    'hunks':changes,'whole_inverse':True,'unchanged_function_names':unchanged,'changed_functions':sorted(modified),
    'new_functions':['project_scope','reviewed_scope_match'],'builder_single_assignment_inverse':True,
    'wrapper_inverse':True,'actual_native_target_calls':0,'canonical_writes':0})
handoff=save('handoff.json',{'schema':'researchos.desktop58-root-metadata-scope-binding-revision.v1',
    'owner':'codex:/root','decision':'SOURCE_PREPARATION_REPORTED_PENDING_NONAUTHOR_REVIEW',
    'pipeline_ref':pipeline,'builder_ref':builder,'wrappers':wrappers,'template_ref':pin(OLD/'scope.desktop58.template.json'),
    'original_handoff_ref':pin(OLD/'handoff.json'),
    'repair':'Complete projected binding/scope equality before prepare module load/native/drafts and before grant preflight mkdir. Later review REF remains outside projection; full scope now pins all actual metadata basis refs and metadata code.',
    'target_calls':0,'canonical_writes':0,'source_acceptance':False,'formal_increment':0,'counter_reset':False})
entries=[pin(p) for p in sorted(BASE.iterdir()) if p.is_file() and p.name!='manifest.json']
manifest=save('manifest.json',{'schema':'researchos.source-preparation-manifest.v1','entries':entries,'count':len(entries),'self_excluded':True})
print(json.dumps({'handoff_ref':handoff,'manifest_ref':manifest,'pipeline_ref':pipeline,'builder_ref':builder,'unchanged_function_count':len(unchanged)}))
