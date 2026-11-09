from pathlib import Path
import ast, difflib, hashlib, json

ROOT = Path('D:/作品集/ResearchOS/research-os')
OUT = Path(__file__).parent
BASE = ROOT/'execution/v2.4/receipts/W05/W05-99/a04_formal_profile_source_revision_codex/02b58e39e08c457a8c48d10ce764fb94'
REVIEW = ROOT/'execution/v2.4/receipts/W05/W05-99/a04_formal_profile_revision_independent_review_codex/be0d42806fa145ee896d6da1a9379a33/review.json'

def pin(p):
    b=p.read_bytes()
    return {'path':p.as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}

def write(name,value):
    with (OUT/name).open('xb') as f:
        f.write(json.dumps(value,ensure_ascii=False,indent=2).encode('utf-8')+b'\n')
    return pin(OUT/name)

def check(ref):
    p=Path(ref['path'])
    if not p.is_absolute():p=ROOT/p
    got=pin(p)
    assert got['sha256']==ref['sha256'] and got['bytes']==ref['bytes'], ref['path']
    return got

review_raw=REVIEW.read_bytes()
assert hashlib.sha256(review_raw).hexdigest()=='086b9a327a4d1ce0aaa2df71fbd03b9a88c5b64e546ae716b3172b33f7122b05' and len(review_raw)==12652
review=json.loads(review_raw)
hdf=json.loads((BASE/'handoff.json').read_bytes())
assert pin(BASE/'handoff.json')['sha256']=='c81528f0d2cfba839fd6ef4036a9d04c2cf89976b0688effe50a372568e10e01'
mf=json.loads((BASE/'manifest.json').read_bytes())
assert pin(BASE/'manifest.json')['sha256']=='7a62badae4bcee8d0b0c56d47bc43aa429bc68faa927dcccac4e9a6c28d9f777'
members=[check(ref) for ref in mf['members']]
selected={target:check(ref) for target,ref in hdf['source_pins'].items()}
assert selected==review['selected_source_refs']
for p in [REVIEW,BASE/'handoff.json',BASE/'manifest.json']:
    with (OUT/('basis.'+p.parent.name[:8]+'.'+p.name)).open('xb') as f:f.write(p.read_bytes())

schema_paths={'domain':'internal/api/contracts/domain.schema.json','client':'internal/domain/contracts/client.protocol.schema.json','persistence':'internal/domain/contracts/persistence-v24.schema.json'}
docs={name:json.loads((ROOT/rel).read_bytes()) for name,rel in schema_paths.items()}
roots=[('domain','Task'),('domain','Run'),('domain','Artifact'),('client','SessionEvent'),('persistence','Task')]
pending=roots[:];seen=set()
allowed={'type','$ref','anyOf','allOf','if','then','else','const','enum','required','additionalProperties','properties','items','minItems','maxItems','minLength','maxLength','minimum','pattern','format'}
annotations={'description','title','$comment','default','examples','readOnly','writeOnly','deprecated'}
def project(node,group):
    if type(node) is list:return [project(x,group) for x in node]
    if type(node) is not dict:return node
    assert set(node)<=allowed|annotations, set(node)-(allowed|annotations)
    out={}
    for key,value in node.items():
        if key in annotations:continue
        if key=='$ref':
            filename,name=value.split('#/$defs/')
            assert filename in ('','domain.schema.json')
            target='domain' if filename else group
            pending.append((target,name))
            out[key]=target+':'+name
        elif key=='properties':
            out[key]={k:project(v,group) for k,v in value.items()}
        else:out[key]=project(value,group)
    if 'type' in out:assert out['type'] in ('object','array','string','integer','boolean','null')
    if 'format' in out:assert out['format']=='date-time'
    if 'additionalProperties' in out:assert type(out['additionalProperties']) is bool
    return out
schemas={name:{} for name in docs}
while pending:
    key=pending.pop()
    if key in seen:continue
    seen.add(key);schemas[key[0]][key[1]]=project(docs[key[0]]['$defs'][key[1]],key[0])
schemas={group:{name:values[name] for name in sorted(values)} for group,values in schemas.items()}
public_paths=list(schema_paths.values())+['internal/domain/store.go','internal/domain/client_protocol_events.go','internal/domain/client_protocol_schema.go','internal/domain/contracts.go','internal/domain/contracts_persistence_v24.go','internal/domain/runtime.go']
basis=[pin(ROOT/rel) for rel in public_paths]
for group,rel in schema_paths.items():
    with (OUT/('public.'+group+'.schema.original.json')).open('xb') as f:f.write((ROOT/rel).read_bytes())
write('public-schema-projection.actual.json',{'schema':'researchos.a04.closed-public-schema-projection.v1','basis_refs':basis,'roots':roots,'reachable_definitions':sorted(seen),'allowed_assertion_keywords':sorted(allowed),'projection':schemas,'description_annotations_only_removed':True,'external_refs_or_schema_network':False})
snips=(OUT/'replacement_functions.source.txt').read_text(encoding='utf-8')
helpers=(OUT/'schema_helpers.source.txt').read_text(encoding='utf-8')
ast.parse(snips);ast.parse(helpers)
replacement={node.name:ast.get_source_segment(snips,node) for node in ast.parse(snips).body if isinstance(node,ast.FunctionDef)}
old=Path(selected['execution/v2.4/formal_profile_w05.py']['path']).read_text(encoding='utf-8')
lines=old.splitlines(keepends=True)
tree=ast.parse(old)
for node in sorted([n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in replacement],key=lambda n:n.lineno,reverse=True):
    lines[node.lineno-1:node.end_lineno]=[replacement[node.name]+'\n']
new=''.join(lines)+'\n\n# Exact public schema assertion closure; SOURCE data, not dynamically loaded code.\nPUBLIC_SCHEMAS = '+repr(schemas)+'\n\n'+helpers
ast.parse(new)
p=OUT/'formal_profile_w05.binding.v3.proposed.py'
with p.open('xb') as f:f.write(new.encode('utf-8'))
new_profile=pin(p)
runtime_target='ops/ci/runtime_w05_live.py'
old_runtime=Path(selected[runtime_target]['path']).read_bytes()
old_sha=selected['execution/v2.4/formal_profile_w05.py']['sha256'].encode()
assert old_runtime.count(old_sha)==2
new_runtime=old_runtime.replace(old_sha,new_profile['sha256'].encode())
ast.parse(new_runtime)
names={runtime_target:'runtime_w05_live.binding.v3.proposed.py',
       'ops/ci/export_a04_live.py':'export_a04_live.binding.v3.proposed.py',
       'execution/v2.4/formal_case_index.py':'formal_case_index.w05.binding.v3.proposed.py',
       'ops/ci/runtime.py':'runtime.w05.route.binding.v3.proposed.py'}
source_pins={'execution/v2.4/formal_profile_w05.py':new_profile}
inverses=[]
for target,name in names.items():
    original=Path(selected[target]['path']).read_bytes()
    updated=new_runtime if target==runtime_target else original
    with (OUT/name).open('xb') as f:f.write(updated)
    source_pins[target]=pin(OUT/name)
for target,after in source_pins.items():
    before=selected[target];old_text=Path(before['path']).read_text(encoding='utf-8');new_text=Path(after['path']).read_text(encoding='utf-8')
    delta=list(difflib.ndiff(old_text.splitlines(keepends=True),new_text.splitlines(keepends=True)))
    assert ''.join(difflib.restore(delta,1))==old_text
    assert ''.join(difflib.restore(delta,2))==new_text
    bt,nt=ast.parse(old_text),ast.parse(new_text)
    old_defs={n.name:n for n in bt.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    new_defs={n.name:n for n in nt.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    unchanged=[];changed=[]
    for key,n in old_defs.items():
        other=new_defs[key]
        is_same=ast.dump(n,include_attributes=False)==ast.dump(other,include_attributes=False) and ast.get_source_segment(old_text,n)==ast.get_source_segment(new_text,other)
        (unchanged if is_same else changed).append(key)
    if target=='execution/v2.4/formal_profile_w05.py':assert set(changed)==set(replacement)
    elif target==runtime_target:assert changed==['verify_bundle']
    else:assert not changed and before['sha256']==after['sha256']
    inverses.append({'target':target,'before_ref':before,'after_ref':after,'exact_copy':before['sha256']==after['sha256'],'ndiff':delta,'unchanged_definitions':unchanged,'changed_definitions':changed,'new_definitions':sorted(set(new_defs)-set(old_defs)),'whole_forward_inverse_exact':True})
write('source.inverse.actual.json',{'schema':'researchos.a04-source-inverse.v1','entries':inverses,'candidate_module_imports':0})
write('construction.actual.json',{'schema':'researchos.a04-binding-source-construction.v1','author_id':'codex:/root/f08_whole_scope_review','basis_review_ref':pin(REVIEW),'basis_handoff_ref':pin(BASE/'handoff.json'),'basis_manifest_ref':pin(BASE/'manifest.json'),'all_prior_members_verified':members,'public_source_basis':basis,'source_pins':source_pins,'schema_definition_count':len(seen),'changed_profile_definitions':sorted(replacement),'unchanged_profile_definitions':[x for x in inverses[0]['unchanged_definitions']],'runtime_exact_pin_replacements':2,'exact_copy_count':3,'module_imports':0,'SQL_Go_CLI_model_native_calls':0,'canonical_writes':0,'formal_accepted_delta':0})
print(json.dumps({'source_pins':source_pins,'prior_member_count':len(members),'schema_definitions':len(seen),'profile_changed':sorted(replacement),'failure_count':0},ensure_ascii=False))

