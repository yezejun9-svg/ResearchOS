"""Construct receipt-only source adaptations; AST only, no candidate imports."""
import ast, difflib, hashlib, json
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os')
P13=ROOT/'execution/v2.4/receipts/W13/W13-03'
BASE=P13/'fresh58_cli2_root_metadata_preparation_codex/900837a405be433f83524eddcc1c6bd8'
ADAPTER=P13/'desktop58_root_authority_adapter_revision_preparation_codex/fde71451a31d4404b8e3d57b396f270c'
OUT=Path(__file__).resolve().parent
def ref(p):
    raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def save(n,x):
    raw=x if isinstance(x,bytes) else (json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode()
    with (OUT/n).open('xb') as f:f.write(raw)
inputs=[BASE/n for n in ['metadata_pipeline.current58.proposed.py','build_binding.current58.proposed.py','handoff.json','scope_builder.py','prepare.py','register.py','run.py','seal.py','grant_preflight.py']]
inputs += [ADAPTER/n for n in ['authorization_adapter.v2.proposed.py','scope.v2.proposed.json','contract.v2.json','handoff.json','manifest.json']]
before=[ref(p) for p in inputs]
assert before[0]['sha256']=='4a5913346f0fa83f65824861077a05087de9244530be2754f138063821f7aeb4'
assert before[1]['sha256']=='62ba221620b4e04a35f17a2799285b74d3f2b75f7c4983e8dba4be4cb0de2a68'
original=inputs[0].read_bytes(); source=original.decode()
edits=[]
def swap(old,new):
    global source
    assert source.count(old)==1, (old[:100],source.count(old))
    source=source.replace(old,new)
    edits.append({'before':old,'after':new})
swap("V3_GATE_SHA = '6ff7a907980da9ffe50a7a2f3ba5669820cd1d99a820be476e5327abd0dec782'", "V3_GATE_SHA = '6a8b87dd4b1edfcbe669a656d02fe5b0bc16a7ac1eca1412be5d737e1c4dadd8'")
swap("WIP_KEYS = ('cli43_fresh_compiler_held2_scope_ref',\n            'cli43_fresh_compiler_current_source_authority_ref',\n            'cli43_fresh_compiler_controller_review_ref')", """WIP_KEYS = ('desktop58_finite_validation_scope_ref',
            'desktop58_finite_validation_current_source_authority_ref',
            'desktop58_finite_validation_controller_review_ref',
            'desktop58_finite_validation_CLI2_qualification_ref',
            'desktop58_finite_validation_state')
DESKTOP_RECEIPTS = ROOT/'execution/v2.4/receipts/W13/W13-03'
OBSERVATION_PHASES = ('admission.runtime','grant-final.runtime','grant-final.runtime.after')
DESKTOP_VALUE_KEYS = ('source_catalog_ref','resource_catalog_ref','current58_CLI2_qualification_ref',
    'current58_CLI2_review_ref','current58_CLI2_manifest_ref','Root_forward_head_seal_ref',
    'Root_forward_head_review_ref','negative_alias_declarations','inner_seconds','outer_seconds',
    'builder_seconds','controller_evidence_reserve_seconds','launcher_evidence_reserve_seconds',
    'expected_runtime_observation_paths','runtime_observation_phases')

def wip_values(b, scope_ref):
    return [scope_ref,b['current43_authority_ref'],b['controller_review_ref'],
            b['desktop_scope_values']['current58_CLI2_qualification_ref'],'REGISTERED_PENDING_ONCE_EXECUTION']

def desktop_lease(b, scope_ref):
    return {'owner':'codex:/root','current_source_writer':None,'state':'REGISTERED_PENDING_ONCE_EXECUTION',
            'scope_ref':scope_ref,'run_uuid':b['run_uuid'],'source_commit':SOURCE}
""")
swap("util=load_module(b['runner_ref'],'root_cli43_runtime_definitions')", "util=load_module(b['utility_ref'],'root_desktop58_runtime_definitions')")
swap("    allowed=rows+[b[k] for k in ('runner_ref','launcher_ref','authorization_gate_ref','owned_process_helper_ref','debug_tree_helper_ref')]+[{'path':str(safe(r['path'])),'sha256':r['sha256'],'bytes':r['bytes']} for r in b['metadata_code_refs']]", """    actual_code=[b[k] for k in ('runner_ref','launcher_ref','authorization_gate_ref','owned_process_helper_ref','debug_tree_helper_ref','utility_ref')]+b['metadata_code_refs']
    allowed={os.path.normcase(str(Path(r['path']).absolute())):r for r in rows}
    for r in actual_code:
        raw=verify(r); path=str(safe(r['path']))
        need(os.path.normcase(path) in allowed and allowed[os.path.normcase(path)]['sha256']==hashlib.sha256(raw).hexdigest()
             and allowed[os.path.normcase(path)]['bytes']==len(raw),'current metadata/controller absent from Root runtime catalogue')
    allowed=list(allowed.values())""")
swap("    observation['all_observed_inputs_pre_pinned']=True", "    observation['all_observed_inputs_pre_pinned']=True\n    observation['producer_stage']=label")
swap("b['schema']=='researchos.cli43-root-metadata-binding.v1'", "b['schema']=='researchos.desktop58-root-metadata-binding.v1'")
swap("    need(pf.is_relative_to(RECEIPTS) and b['run_uuid'] in pf.name,'explicit bounded preflight UUID leaf')", "    need(pf.is_relative_to(DESKTOP_RECEIPTS) and b['run_uuid'] in pf.name,'explicit bounded preflight UUID leaf')")
swap("    for x in b['metadata_code_refs']: verify(x)\n    return b", """    for x in b['metadata_code_refs']: verify(x)
    values=b['desktop_scope_values']
    need(type(values)is dict and set(values)==set(DESKTOP_VALUE_KEYS) and all(values[k] is not None for k in DESKTOP_VALUE_KEYS),'all Desktop future values explicit')
    for k in DESKTOP_VALUE_KEYS:
        if k.endswith('_ref'):verify(values[k])
    root=safe(b['new_authorization_root'],False)
    expected=[str(root/(phase+'.json')) for phase in OBSERVATION_PHASES]
    need(values['expected_runtime_observation_paths']==expected,'Root exact observation paths must match actual three producer stages')
    need(values['runtime_observation_phases']==[{'stage':phase,'path':path} for phase,path in zip(OBSERVATION_PHASES,expected)],'Root frozen observation stage mapping')
    need(safe(b['new_output_root'],False).is_relative_to(DESKTOP_RECEIPTS) and
         safe(b['new_wrapper_root'],False).is_relative_to(DESKTOP_RECEIPTS) and root.is_relative_to(DESKTOP_RECEIPTS),'Desktop receipt roots')
    return b""")
start=source.index('def scope_build(');end=source.index('\ndef prepare(',start)
swap(source[start:end], """def scope_build(b, scope_template_ref, dest):
    s=doc(scope_template_ref)
    need(s['preparation_only'] is True and s['execution_authorized'] is False,'original preparation template required')
    aliases={'output_root':'new_output_root','outer_output_root':'new_wrapper_root','export_root':'new_export_root',
        'new_authorization_root':'new_authorization_root','new_grant_preflight_root':'new_grant_preflight_root',
        'current_source_authority_ref':'current43_authority_ref','authorization_verifier_ref':'authorization_gate_ref',
        'controller_ref':'runner_ref','owned_helper_ref':'owned_process_helper_ref','debug_helper_ref':'debug_tree_helper_ref'}
    for key,src in aliases.items():s[key]=b[src]
    for k in ('run_uuid','registration_namespace','runtime_resources_ref','compiler_resources_ref',
              'controller_review_path','main_git','public_environment','launcher_ref','utility_ref','toolchain_lock_ref'):
        s[k]=b[k]
    s.update(b['desktop_scope_values'])
    s.update(preparation_only=False,execution_authorized=True,expected_before_registration=b['before'],
             expected_registration=b['after'],registration_metadata_paths=CANON[:2])
    need(s['source_commit']==SOURCE and s['node_cases']==169 and s['Go_top_cases']==3,'fixed source/roster')
    return save(dest,s)
""")
swap("review['schema']=='researchos.cli43-compiler-controller-static-review.v1'", "review['schema']=='researchos.desktop58-controller-static-review.v1'")
swap("review['decision']=='READY_FOR_ROOT_CURRENT43_HELD2_ONCE'", "review['decision']=='READY_FOR_ROOT_CURRENT58_DESKTOP169_GO3_ONCE'")
swap("('runner_sha256',s['runner_ref']['sha256'])", "('controller_sha256',s['controller_ref']['sha256'])")
swap("('gate_sha256',s['authorization_gate_ref']['sha256'])", "('gate_sha256',s['authorization_verifier_ref']['sha256'])")
swap("    before=canonical_expected(b); cp,ow=map(parse,before[:2]); rows=origins(b,cp)", """    before=canonical_expected(b); cp,ow=map(parse,before[:2]); rows=origins(b,cp)
    reader=gate.Reader()
    gate.validate_cli2(reader,s)
    gate.validate_current58_source(reader,{'catalog_ref':s['source_catalog_ref']},doc(b['current43_authority_ref']),cp,ow)
    for path,raw in reader.raw.items():
        if path in READS:need(READS[path]==raw,'qualification/source input drift')
        READS[path]=raw""")
swap("    wipvalues=[scope_ref,b['current43_authority_ref'],b['controller_review_ref']]", "    wipvalues=wip_values(b,scope_ref)")
swap("    desiredow.update(revision=b['after'][1],amended_at=stamp,amended_by='codex:/root')", """    desiredow.update(revision=b['after'][1],amended_at=stamp,amended_by='codex:/root')
    card=desiredow['card_path_bindings']['W13-03']
    need(type(card['subtasks'])is dict,'Root actual W13-03 subtask map required')
    prior=card['subtasks'].get('desktop58_finite_validation')
    need(prior is None or prior.get('state') not in ('REGISTERED_PENDING_ONCE_EXECUTION','RUNNING'),'cannot replace active Desktop lease')
    card['subtasks']['desktop58_finite_validation']=desktop_lease(b,scope_ref)""")
swap("    need(protectedcp==oldcp and protectedow==oldow,'unrelated canonical field modified')", """    expectedcard=copy.deepcopy(oldow['card_path_bindings']['W13-03'])
    expectedcard['subtasks']['desktop58_finite_validation']=desktop_lease(b,p['scope_ref'])
    need(ow['card_path_bindings']['W13-03']==expectedcard,'only registered finite Desktop sublease may change')
    protectedow['card_path_bindings']['W13-03']=oldow['card_path_bindings']['W13-03']
    need(protectedcp==oldcp and protectedow==oldow,'unrelated canonical field modified')""")
swap("[p['scope_ref'],b['current43_authority_ref'],b['controller_review_ref']], 'desired scope/review authority values'", "wip_values(b,p['scope_ref']), 'desired scope/review authority values'")
swap("    others=[safe(scope[k],False) for k in ('new_output_root','new_wrapper_root','new_export_root')]", "    others=[safe(scope[k],False) for k in ('output_root','outer_output_root','export_root')]")
swap("    need(pf.is_relative_to(RECEIPTS) and b['run_uuid'] in pf.name,'bounded preflight leaf/UUID')", "    need(pf.is_relative_to(DESKTOP_RECEIPTS) and b['run_uuid'] in pf.name,'bounded preflight leaf/UUID')")
swap("    ar=gate.validate_authority(reader,scope,scope_ref,copies,rr)\n    final_records", """    ar=gate.validate_authority(reader,scope,scope_ref,copies,rr)
    ar.update({'CLI2_qualification_ref':scope['current58_CLI2_qualification_ref'],
        'CLI2_review_ref':scope['current58_CLI2_review_ref'],'CLI2_manifest_ref':scope['current58_CLI2_manifest_ref']})
    final_records""")
swap("    preflight_pre=save(pf/'prelaunch.json',{'runtime_resources_ref':scope['runtime_resources_ref'],", """    observed=[]
    for phase,r in zip(OBSERVATION_PHASES,(first_observed,final_observed,after_observed)):
        need(safe(r['path'])==pf/(phase+'.json'),'actual observation producer/path mismatch')
        copyref=copy_fact(safe(r['path']))
        observed.append({'path':str(safe(copyref['path'])),'sha256':copyref['sha256'],'bytes':copyref['bytes']})
    need([r['path'] for r in observed]==scope['expected_runtime_observation_paths'],'actual ordered observation selection differs from frozen scope')
    preflight_pre=save(pf/'prelaunch.json',{'runtime_observation_refs':observed,'runtime_resources_ref':scope['runtime_resources_ref'],""")
swap("    observed=[copy_fact(safe(r['path'])) for r in (first_observed,final_observed,after_observed)]\n", "")
swap("    gr=save(root/'authorization.execute.json',{'schema':'researchos.cli43-compiler-authorization.v1','actor':'codex:/root',", """    need(all(not os.path.lexists(p) for p in others),'fresh execution leaves appeared before grant')
    gr=save(root/'authorization.execute.json',{'schema':'researchos.desktop58-finite-authorization.v1','actor':'codex:/root',""")
swap("'prelaunch_evidence_ref':pre,'runtime_observation_refs':observed})", "'prelaunch_evidence_ref':pre,'runtime_observation_refs':observed,\n        'fresh_roots_observed_absent':[scope[k] for k in ('output_root','outer_output_root','export_root')],\n        'automatic_retry':False,'counter_reset':False})")
new=source.encode();ast.parse(new)
inverse=source
for e in reversed(edits):
    if e['after']:
        assert inverse.count(e['after'])==1, e['after'][:80]
        inverse=inverse.replace(e['after'],e['before'])
    else:
        anchor="    save(root/'preflight-copy-map.json'"
        assert inverse.count(anchor)==1
        inverse=inverse.replace(anchor,e['before']+anchor)
assert inverse.encode()==original
save('metadata_pipeline.desktop58.proposed.py',new)
save('pipeline.inverse.json',{'original_ref':before[0],'selected_ref':ref(OUT/'metadata_pipeline.desktop58.proposed.py'),'edits':edits,'whole_byte_inverse_equal':True})
save('pipeline.diff',''.join(difflib.unified_diff(original.decode().splitlines(True),source.splitlines(True),fromfile='old.current58.py',tofile='desktop58.proposed.py')).encode())
olddefs={n.name:ast.dump(n,include_attributes=False) for n in ast.parse(original).body if isinstance(n,ast.FunctionDef)}
newdefs={n.name:ast.dump(n,include_attributes=False) for n in ast.parse(new).body if isinstance(n,ast.FunctionDef)}
same=[name for name in olddefs if olddefs[name]==newdefs.get(name)]
for name in ('need','parse','encoded','safe','pin','verify','doc','argref','write','save','now','unchanged_reads','load_module','job_ok','git_guard','canonical_expected','origins','registration_review','register','run_registration','seal','main'):
    assert name in same,name
save('definition-audit.json',{'unchanged_AST_definitions':same,'changed_definitions':[n for n in olddefs if n not in same],'new_definitions':[n for n in newdefs if n not in olddefs],'candidate_imported':False})
module=ref(OUT/'metadata_pipeline.desktop58.proposed.py')
for name in ('scope_builder.py','prepare.py','register.py','run.py','seal.py','grant_preflight.py'):
    oldraw=(BASE/name).read_bytes();text=oldraw.decode()
    oldliteral=repr(str(BASE/'metadata_pipeline.current58.proposed.py'))
    newliteral=repr(module['path'])
    assert text.count(oldliteral)==1 and text.count(before[0]['sha256'])==1
    updated=text.replace(oldliteral,newliteral).replace(before[0]['sha256'],module['sha256'])
    assert updated.replace(newliteral,oldliteral).replace(module['sha256'],before[0]['sha256'])==text
    ast.parse(updated);save(name,updated.encode())
save('inputs.before.json',before)
after=[ref(p) for p in inputs];assert before==after
save('inputs.after.json',after)
print(json.dumps({'module_ref':module,'unchanged_definitions':len(same),'source_input_count':len(before),'target_calls':0},ensure_ascii=False))
