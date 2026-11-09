"""Owned pure IO/AST preparation. Never imports or executes a candidate."""
import ast
import copy
import difflib
import hashlib
import json
from pathlib import Path

ROOT=Path('D:/作品集/ResearchOS/research-os')
OUT=Path(__file__).resolve().parent
MAPPING=ROOT/'execution/v2.4/receipts/W13/W13-03/fresh58_validation_reference_mapping_codex/c745e294c1304498a6094777a42ed6e2/mapping.json'
OLD='a510dbef4a7e08fb5c428df44c39b133f3ffa856'
HEAD='e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7'
BEFORE={}

def need(ok,msg):
    if not ok: raise RuntimeError(msg)

def pin(p):
    p=Path(p);raw=p.read_bytes()
    return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}

def read(ref):
    p=Path(ref['path']);p=p if p.is_absolute() else ROOT/p
    raw=p.read_bytes()
    need(len(raw)==ref['bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256'],'Input pin '+str(p))
    BEFORE[str(p)]=pin(p)
    return raw

def put(name,raw):
    if not isinstance(raw,bytes): raw=(json.dumps(raw,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    p=OUT/name
    with p.open('xb') as f:f.write(raw)
    return pin(p)

def edit(raw,old,new):
    need(raw.count(old)==1,'Nonunique exact edit '+repr(old[:70]))
    return raw.replace(old,new,1)

mapping_raw=read({'path':str(MAPPING),'sha256':'bc3abc71c485fa48c53a576e476ae5606d0dd02a4197ec89c68b7d7950691e0d','bytes':15097})
mapping=json.loads(mapping_raw);refs=mapping['references']
keys=['old_cli_scope','runner_ref','authorization_gate_ref','launcher_ref','owned_process_helper_ref',
      'debug_tree_helper_ref','instrumentation_ref','instrumented_source_ref','instrumentation_helper_ref',
      'roster_ref','toolchain_lock_ref','catalog_ref','current43_authority_ref','source_commit_closure']
raws={k:read(refs[k]) for k in keys}
oldrunner=raws['runner_ref'];oldgate=raws['authorization_gate_ref']
runner=edit(oldrunner,('SOURCE = '+repr(OLD)).encode(),('SOURCE = '+repr(HEAD)).encode())
gate_edits=[]
def ged(old,new):
    global gate
    before=gate;gate=edit(gate,old,new);gate_edits.append({'old':old.decode(),'new':new.decode()})
gate=oldgate
ged(('SOURCE = '+repr(OLD)).encode(),('SOURCE = '+repr(HEAD)).encode())
ged(b"PARENT = 'a5d6d16ffaf129de0361470c3a1570228bd259a2'",('PARENT = '+repr(OLD)).encode())

addition='''def validate_current58_source(reader, scope, authority, cp, ow):
    # Legacy current43 wire names are retained; this authority applies ONLY to SOURCE/current58.
    require(cp['head'] == SOURCE and authority['source_parent'] == PARENT and
            authority['unique_combined_source_paths'] == 58 and
            authority['source_acceptance'] is False and
            authority['fresh_compilation_or_cases_accepted'] is False,
            'Current58 source identity; no old qualification inheritance')
    closure_ref = authority['source_commit_closure_ref']
    require(bounded_path(closure_ref['path']) == ROOT/'execution/v2.4/receipts/W13/W13-03/desktop58_source_execution_independent_review_codex/a76cb528a87f45529adb3da26418eabb/review.json' and
            closure_ref['sha256'] == '7d82779e61ff50c3072e9d008531b2409e3ee288235ec7ad12a24f276f4de4b7' and
            closure_ref['bytes'] == 12270, 'Actual Desktop15 source closure pin')
    closure = reader.doc(closure_ref)
    require(closure['schema'] == 'researchos.desktop58-source-execution-independent-review.v1' and
            closure['reviewer'] == 'codex:/root/w05_merge_review' and
            closure['decision'] == 'SOURCE_COMMIT_EVIDENCE_CLOSED' and closure['requested_changes'] == [] and
            closure['actual_new_head'] == SOURCE and closure['actual_parent'] == PARENT and
            closure['unique_combined_paths'] == 58 and closure['source_path_count'] == 15 and
            closure['source_acceptance'] is False and closure['fresh58_qualified'] is False,
            'Closed source import is not current58 execution qualification')
    for key in ['completed_ref','manifest_ref','outer_manifest_ref','outer_invocation_ref',
                'source_intent_ref','root_tool_observations_ref','scope_ref','grant_ref']:
        reader.verify(closure[key])
    wip = cp['work_in_progress']
    require(wip['desktop_exact15_source_integration_state'] == 'CLOSED_PENDING_FRESH58_VALIDATION' and
            wip['desktop_exact15_actual58_head'] == SOURCE and
            wip['desktop_exact15_actual_combined_source_paths'] == 58,
            'Desktop source import forward registration absent')
    for key, value in [('desktop_exact15_source_integration_execution_review_ref',closure_ref),
                       ('desktop_exact15_source_integration_completed_ref',closure['completed_ref']),
                       ('desktop_exact15_source_integration_manifest_ref',closure['manifest_ref']),
                       ('desktop_exact15_source_integration_outer_manifest_ref',closure['outer_manifest_ref']),
                       ('desktop_exact15_source_integration_grant_ref',closure['grant_ref'])]:
        require(reader.verify(wip[key]) == reader.verify(value), 'Canonical current58 closure mismatch ' + key)
    lease = ow['card_path_bindings']['W13-03']['subtasks']['desktop_exact15_source_integration']
    require(lease['current_source_writer'] is None and lease['state'] == 'CLOSED_PENDING_FRESH58_VALIDATION',
            'Desktop source writer lease not closed')
    source_set = reader.doc(authority['combined_source_set_ref'])
    require(source_set['schema'] == 'researchos.current58-combined-source-set.v1' and
            source_set['source_commit'] == SOURCE and source_set['source_parent'] == PARENT and
            source_set['source_commit_closure_ref'] == closure_ref and len(source_set['files']) == 58,
            'Exact current58 source set missing')
    catalog = reader.doc(scope['catalog_ref'])
    require(catalog['commit'] == SOURCE and catalog['file_count'] == len(catalog['files']), 'Fresh current58 catalogue')
    cat = {x['path']: x for x in catalog['files']}
    require(len(cat) == len(catalog['files']), 'Duplicate catalogue source path')
    seen = set()
    for item in source_set['files']:
        p = bounded_path(item['path'])
        relative = p.relative_to(ROOT).as_posix()
        require(item['path'] == relative and relative not in seen and relative in cat,
                'Source set duplicate/alias/not in fresh catalogue')
        seen.add(relative)
        reader.verify(item)
        require(item['sha256'] == cat[relative]['sha256'] and item['bytes'] == cat[relative]['bytes'],
                'Current58 source set/catalogue differs')
    require(set(closure['source_paths']).issubset(seen), 'Desktop15 absent from actual58 source set')
    forward_ref = authority['forward_head_audit_ref']
    mf_ref = authority['forward_head_manifest_ref']
    mf = reader.doc(mf_ref)
    require(len(mf['entries']) == mf['count'] and mf['self_excluded'] is True, 'Forward manifest shape')
    listed = {}
    base = bounded_path(mf_ref['path']).parent
    for item in mf['entries']:
        p = bounded_path(item['path'])
        require(p.parent == base and str(p) not in listed, 'Forward manifest foreign/duplicate member')
        reader.verify(item)
        listed[str(p)] = item
    def sealed(item):
        require(listed.get(str(bounded_path(item['path']))) == item, 'Unsealed forward fact')
        return reader.doc(item)
    audit = sealed(forward_ref)
    require(audit['schema'] == 'researchos.desktop58-forward-head-registration-audit.v1' and
            audit['actor'] == 'codex:/root' and audit['registered_head'] == SOURCE and
            audit['actual_registration_exit'] == 0 and audit['source_acceptance'] is False and
            audit['formal_increment'] == 0 and audit['grant_materialized'] is False and
            audit['compile_GUI_HTTP_models_authorized'] is False and
            reader.verify(audit['source_closure_review_ref']) == reader.verify(closure_ref),
            'Actual source-head forward seal missing')
    inv = sealed(audit['invocation_ref'])
    intent = sealed(audit['intent_ref'])
    verified = sealed(audit['verified_ref'])
    reader.verify(audit['request_ref'])
    require(inv['actual_exit'] == 0 and inv['wrapper_error'] is None and inv['automatic_retry'] is False,
            'Forward registration did not complete')
    require([verified['checkpoint'],verified['ownership'],verified['failure_origins']] == audit['after'] and
            verified['intent_ref'] == audit['intent_ref'] and
            audit['after'][0] <= cp['revision'] and audit['after'][1] <= ow['revision'],
            'Forward registered tuple does not precede current authorization')
    require(all(x in authority['sealed_integration_refs'] for x in [closure_ref,forward_ref,mf_ref]),
            'Current58 source closure/forward chain not bound by authority')


'''
anchor=b'def validate_authority(reader, scope, scope_ref, canonical_copies, registration):\n'
ged(anchor,addition.encode()+anchor)
ged(b"    require(len(authority['sealed_integration_refs'])>=3, 'Actual Main38/CLI8 and head-forward refs missing')\n",
    b"    require(len(authority['sealed_integration_refs'])>=3, 'Actual Main38/CLI8 and head-forward refs missing')\n    validate_current58_source(reader, scope, authority, cp, ow)\n")

rr=put('runner.current58.proposed.py',runner)
gr=put('authorization_gate.current58.proposed.py',gate)
put('runner.edits.json',[{'old':"SOURCE = "+repr(OLD),'new':"SOURCE = "+repr(HEAD)}])
put('gate.edits.json',gate_edits)
for name,old,new in [('runner',oldrunner,runner),('gate',oldgate,gate)]:
    put(name+'.diff', ''.join(difflib.unified_diff(old.decode().splitlines(True),new.decode().splitlines(True),fromfile='original',tofile='candidate')).encode())
back=gate
for x in reversed(gate_edits):back=edit(back,x['new'].encode(),x['old'].encode())
need(back==oldgate,'Gate whole inverse')
need(edit(runner,('SOURCE = '+repr(HEAD)).encode(),('SOURCE = '+repr(OLD)).encode())==oldrunner,'Runner whole inverse')
trees={n:ast.parse(raw.decode('utf-8'),filename=n) for n,raw in [('runner',runner),('gate',gate),('launcher',raws['launcher_ref'])]}
def defs(raw):
    t=ast.parse(raw.decode());return {x.name:ast.dump(x,include_attributes=False) for x in t.body if isinstance(x,(ast.FunctionDef,ast.ClassDef))}
od,nd=defs(oldrunner),defs(runner);need(od==nd,'Runner functions changed')
og,ng=defs(oldgate),defs(gate)
unchanged=[k for k in og if k!='validate_authority']
need(all(og[k]==ng[k] for k in unchanged),'Old gate unrelated function changed')
main_test=ROOT/'apps/cli/cli_sessions_test.go';main_raw=main_test.read_bytes();BEFORE[str(main_test)]=pin(main_test)
plan=json.loads(raws['instrumentation_ref'])
need(hashlib.sha256(main_raw).hexdigest()==plan['original_sha256'],'Current Main test preimage mismatch')
reverse=raws['instrumented_source_ref'].decode()
for c in reversed(plan['changes']):
    need(reverse.count(c['new'])==1,'Instrumentation reverse ambiguous')
    reverse=reverse.replace(c['new'],c['old'],1)
need(reverse.encode()==main_raw,'Instrumentation whole inverse Main test')
scope=json.loads(raws['old_cli_scope'])
for k in ['run_uuid','new_output_root','new_wrapper_root','new_export_root','new_authorization_root',
          'registration_namespace','expected_registration','expected_before_registration','catalog_ref',
          'runtime_resources_ref','compiler_resources_ref','current43_authority_ref','controller_review_path',
          'new_grant_preflight_root','registration_metadata_paths','public_environment']:
    scope[k]=None
scope.update(preparation_only=True,execution_authorized=False,source_commit=HEAD,actual_candidate_parent_expected=OLD,
             runner_ref=rr,authorization_gate_ref=gr,actual_runtime_inputs=None,actual_compile_graph=None,actual_cases=None)
scope['main_git']={'head':HEAD,'status_sha256':None,'status_bytes':None,'status_rows':13,'deleted_rows':11,'index_empty':True}
scope['draft_history']={'old_scope_ref':refs['old_cli_scope'],'mapping_ref':pin(MAPPING),'original_files_unchanged':True}
scope['not_run_reason']='Future Root current58 authority/source catalog/runtime binding, actual forward seal, full-scope independent review, registration and unique grant required. Old current43 wire labels are compatibility names only.'
put('scope.current58.proposed.json',scope)
authority=json.loads(raws['current43_authority_ref'])
authority.update(source_commit=HEAD,source_parent=OLD,current_canonical_head=HEAD,source_integration_completed=None,
                 unique_combined_source_paths=58,sealed_integration_refs=None,current_canonical_refs=None,
                 resource_preparation_audit_ref=None,source_commit_closure_ref=refs['source_commit_closure'],
                 combined_source_set_ref=None,forward_head_audit_ref=None,forward_head_manifest_ref=None)
authority['restriction']='PROPOSED_ONLY: legacy cli43 schema/field name binds current58; actual Root forward closure is absent. No execution, case, product or formal acceptance.'
put('current58-authority.proposed.json',authority)
put('combined58-source-set.proposed.json',{'schema':'researchos.current58-combined-source-set.v1','source_commit':HEAD,
    'source_parent':OLD,'source_commit_closure_ref':refs['source_commit_closure'],'files':None,
    'provenance':'Root must derive exact union Main38+CLI8+Desktop15 and compare sealed actual58 Git tree; 58 current-byte relative refs, no invented 597 catalogue.'})
put('input.before.json',list(BEFORE.values()))
put('static-audit.json',{'schema':'researchos.fresh58-cli2-source-preparation-static.v1','candidate_imported':False,
    'candidate_executed':False,'AST_files':3,'runner_whole_inverse':True,'gate_whole_inverse':True,
    'runner_all_functions_AST_equal':sorted(od),'gate_unchanged_definitions_AST_equal':unchanged,
    'gate_changed_existing_definitions':['validate_authority'],'gate_added_definitions':['validate_current58_source'],
    'launcher_reused_byte_exact':refs['launcher_ref'],'instrumentation_current_Main_test_whole_inverse':True,
    'current_Main_test_ref':pin(main_test),'native_calls':0,'Go_SQL_Node_HTTP_SDK_model_calls':0,
    'runtime_behavior_verified':False,'source_acceptance':False,'new_failure_origins':[],
    'actual_compile_graph':None,'actual_cases':None,'future_Root_tuple':None})
put('inputs.after.json',[pin(p) for p in BEFORE])
need(list(BEFORE.values())==[pin(p) for p in BEFORE],'Inputs changed during preparation')
print(json.dumps({'runner':rr,'gate':gr,'inputs':len(BEFORE),'source_only':True},ensure_ascii=False))
