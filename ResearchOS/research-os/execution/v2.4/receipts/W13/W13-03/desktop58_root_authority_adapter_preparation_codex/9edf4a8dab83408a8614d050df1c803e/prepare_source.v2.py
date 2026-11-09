"""Pure IO/AST source construction. Does not import or execute any candidate."""
import ast, difflib, hashlib, json
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os')
OUT=Path(__file__).parent
P13=ROOT/'execution/v2.4/receipts/W13/W13-03'
P05=ROOT/'execution/v2.4/receipts/W05/W05-99'
BASE=P13/'fresh58_cli2_controller_revision_preparation_codex/48d76385c123478e90864ebbfc2ad24a/authorization_gate.current58.final.proposed.py'
OLD=P13/'fresh58_desktop169_go3_revision_preparation_codex/736e757cdbc148a286c1d2426b8a7382'
Q=P05/'cli43_successful_execution_independent_review_codex/6f07498ca19a49c7866b9e528d401aa0'
READS={}
def read(p):
    p=Path(p);raw=p.read_bytes();READS[str(p)]=raw;return raw
def ref(p):
    p=Path(p);raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def save(name,obj):
    with (OUT/name).open('xb') as f:f.write((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode())
def put(name,raw):
    with (OUT/name).open('xb') as f:f.write(raw)
raw=read(BASE)
assert hashlib.sha256(raw).hexdigest()=='6ff7a907980da9ffe50a7a2f3ba5669820cd1d99a820be476e5327abd0dec782'
scope=json.loads(read(OLD/'scope.v2.proposed.json'))
assert ref(OLD/'scope.v2.proposed.json')['sha256']=='3192c8c1d1250d6d8a3513c80d7b8b1ffa69e3be2cceb87d624498de11b958af'
for name in ['handoff.json','manifest.json']:
    read(OLD/name)
review=P13/'fresh58_desktop169_go3_revision_independent_review_codex/967f715e57e24a4981d20e85bebc4292/review.json'
assert hashlib.sha256(read(review)).hexdigest()=='85eb2611574614802423730cb3232e0611364e719da80eb15fa25b9f1390e47f'
for name in ['qualification.json','review.json','manifest.json']:
    read(Q/name)
q=json.loads(READS[str(Q/'qualification.json')])
for k in ['result_ref','executor_manifest_ref','launcher_completed_ref','launcher_manifest_ref','root_closed_manifest_ref']:
    read(Path(q['evidence_refs'][k]['path']))
fixed={k:v for k,v in scope.items() if k.endswith('_ref') and v is not None}
for key,r in fixed.items():
    data=read(r['path']);assert len(data)==r['bytes'] and hashlib.sha256(data).hexdigest()==r['sha256'],key
text=raw.decode('utf-8');tree=ast.parse(text);lines=text.splitlines(keepends=True)
defs={n.name:''.join(lines[n.lineno-1:n.end_lineno]) for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
reuse=['require','strict_json','bounded_path','Reader','registration_refs','validate_current58_source']
prefix=text[:text.index('def require(')]
prefix=prefix.replace('Pure read-only authorization verifier. No process, SQLite, or DLL calls.',
    'Desktop authority adapter SOURCE PREPARATION ONLY. No process, SQLite, DLL, writes or registration implementation. Future Root/W05 binding required.')
extension=read(OUT/'extensions.proposed.py.txt').decode()
authority=defs['validate_authority']
replacements=[
 ('cli43_fresh_compiler_held2_scope_ref','desktop58_finite_validation_scope_ref'),
 ('cli43_fresh_compiler_current_source_authority_ref','desktop58_finite_validation_current_source_authority_ref'),
 ("scope['current43_authority_ref']","scope['current_source_authority_ref']"),
 ('cli43_fresh_compiler_controller_review_ref','desktop58_finite_validation_controller_review_ref'),
 ('researchos.cli43-compiler-controller-static-review.v1','researchos.desktop58-controller-static-review.v1'),
 ('READY_FOR_ROOT_CURRENT43_HELD2_ONCE','READY_FOR_ROOT_CURRENT58_DESKTOP169_GO3_ONCE'),
 ("scope['runner_ref']","scope['controller_ref']"),
 ("scope['authorization_gate_ref']","scope['authorization_verifier_ref']"),
 ("'runner_sha256', scope['controller_ref']","'controller_sha256', scope['controller_ref']"),
 ("validate_current58_source(reader, scope, authority, cp, ow)","validate_current58_source(reader, {'catalog_ref':scope['source_catalog_ref']}, authority, cp, ow)")]
for old,new in replacements:
    assert old in authority,old
    authority=authority.replace(old,new)
anchor="    runner_ref = wip['desktop58_finite_validation_controller_review_ref']"
extra="""    require(wip['desktop58_finite_validation_CLI2_qualification_ref'] == scope['current58_CLI2_qualification_ref'] and
            wip['desktop58_finite_validation_state'] == 'REGISTERED_PENDING_ONCE_EXECUTION', 'Desktop prerequisite/lease state')
    lease = ow['card_path_bindings']['W13-03']['subtasks']['desktop58_finite_validation']
    require(lease['owner'] == 'codex:/root' and lease['current_source_writer'] is None and
            lease['state'] == 'REGISTERED_PENDING_ONCE_EXECUTION' and lease['scope_ref'] == scope_ref and
            lease['run_uuid'] == scope['run_uuid'] and lease['source_commit'] == SOURCE,
            'Actual Desktop finite execution lease absent')
    validate_cli2(reader, scope)
    same_ref(reader, scope['Root_forward_head_seal_ref'], authority['forward_head_manifest_ref'])
"""
assert authority.count(anchor)==1
authority=authority.replace(anchor,extra+anchor)
grant=defs['validate_grant']
for old,new in [
 ('researchos.cli43-compiler-authorization.v1','researchos.desktop58-finite-authorization.v1'),
 ("'authorization_gate_ref'","'authorization_verifier_ref'"),
 ("'owned_process_helper_ref'","'owned_helper_ref'"),
 ("'runner_ref'","'controller_ref'"),
 ("'debug_tree_helper_ref'","'debug_helper_ref'")]:
    assert old in grant
    grant=grant.replace(old,new)
oldreturn="    return {'authorization_paths': sorted(reader.raw), 'scope':scope, 'grant':grant,\n            'authorization_input_refs':[reader.ref(p, external=not Path(p).is_relative_to(ROOT)) for p in sorted(reader.raw)]}"
assert oldreturn in grant
grant=grant.replace(oldreturn,"""    # Return absolute refs: both existing consumers require canonical absolute paths.
    refs = []
    for path in sorted(reader.raw):
        raw = reader.read(path, external=not Path(path).is_relative_to(ROOT))
        refs.append({'path':path, 'sha256':hashlib.sha256(raw).hexdigest(), 'bytes':len(raw)})
    return {'authorization_paths':sorted(reader.raw), 'authorization_input_refs':refs,
            'scope':scope, 'grant':grant, 'source_commit':SOURCE,
            'fresh_current58_CLI2_qualified':True, 'original_CLI2_case_count':2,
            'registered_Root_scope_and_grant_verified':True}
""")
# Additional registration/qualification refs are part of the grant's actual authority chain.
old="    require(grant['authority_review_refs'] == authority, 'Grant review links')"
new="""    authority.update({'CLI2_qualification_ref':scope['current58_CLI2_qualification_ref'],
                      'CLI2_review_ref':scope['current58_CLI2_review_ref'],
                      'CLI2_manifest_ref':scope['current58_CLI2_manifest_ref']})
    require(grant['authority_review_refs'] == authority, 'Grant review links')
    require(grant['fresh_roots_observed_absent'] == [scope[k] for k in ['output_root','outer_output_root','export_root']] and
            grant['automatic_retry'] is False and grant['counter_reset'] is False,
            'Once/fresh allocation statement must be bound and independently reviewed')"""
assert old in grant;grant=grant.replace(old,new)
# Do not use mutable live canon at execution: original sealed registration desired copies are the authority.
code_keys=list(fixed)+['authorization_verifier_ref','source_catalog_ref']
constants='\nFIXED_CODE = '+repr(fixed)+'\nCODE_KEYS = '+repr(code_keys)+'\n\n'
candidate=prefix+constants+'\r\n\r\n'.join(defs[k] for k in reuse)+'\n\n'+extension+'\n\n'+authority+'\n\n'+grant+'\n'
ast.parse(candidate)
put('authorization_adapter.proposed.py',candidate.encode())
# Whole replacement inverse is explicit because this is a new ABI adapter, not a change to any original.
save('whole-inverse.json',{'baseline_ref':ref(BASE),'candidate_ref':ref(OUT/'authorization_adapter.proposed.py'),
    'old':text,'new':candidate,'reason':'New desktop ABI adapter; original six reusable definitions are byte/AST identical.'})
put('source.diff', ''.join(difflib.unified_diff(text.splitlines(True),candidate.splitlines(True),fromfile=str(BASE),tofile=str(OUT/'authorization_adapter.proposed.py'))).encode())
newtree=ast.parse(candidate);newlines=candidate.splitlines(True)
newdefs={n.name:''.join(newlines[n.lineno-1:n.end_lineno]) for n in newtree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
checks=[{'name':'exact-reused-'+k,'ok':newdefs[k]==defs[k]} for k in reuse]
checks += [{'name':'controller-original-fullbytes','ok':ref(scope['controller_ref']['path'])==scope['controller_ref']},
 {'name':'launcher-original-fullbytes','ok':ref(scope['launcher_ref']['path'])==scope['launcher_ref']},
 {'name':'whole-inverse','ok':candidate.replace(candidate,text,1).encode()==raw},
 {'name':'candidate-no-write-or-native-import','ok':not any(isinstance(n,(ast.Import,ast.ImportFrom)) and any(x.name.split('.')[0] in ['subprocess','ctypes','sqlite3'] for x in n.names) for n in ast.walk(newtree))},
 {'name':'actual-old43-source-rejected-by-literal-relation','ok':q['source_commit']!='e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7'},
 {'name':'exact-consumer-return-ABI','ok':all(repr(x) in grant for x in ['scope','source_commit','fresh_current58_CLI2_qualified','original_CLI2_case_count','registered_Root_scope_and_grant_verified','authorization_input_refs'])}]
assert all(x['ok'] for x in checks)
scope['authorization_verifier_ref']=ref(OUT/'authorization_adapter.proposed.py')
for key in ['expected_before_registration','registration_metadata_paths','controller_review_path','current_source_authority_ref',
            'current58_CLI2_review_ref','current58_CLI2_manifest_ref','compiler_resources_ref','runtime_resources_ref',
            'new_authorization_root','main_git','negative_alias_declarations']:
    scope[key]=None
scope['python_flags']=['-I','-S','-X','utf8']
save('scope.proposed.json',scope)
before=[{'path':k,'sha256':hashlib.sha256(v).hexdigest(),'bytes':len(v)} for k,v in READS.items()]
save('inputs.before.json',before)
after=[ref(k) for k in READS]
assert before==after
save('inputs.after.json',after)
save('static-checks.json',{'candidate_imported':False,'candidate_executed':False,'checks':checks,'failed':0,
    'inputs':len(before),'input_drift':0,'runtime_tests':'NOT_RUN','new_controller_or_launcher_changes':0,
    'original_controller_ref':scope['controller_ref'],'original_launcher_ref':scope['launcher_ref']})
print(json.dumps({'adapter':ref(OUT/'authorization_adapter.proposed.py'),'scope':ref(OUT/'scope.proposed.json'),'checks':len(checks),'input_count':len(before)},ensure_ascii=False))
