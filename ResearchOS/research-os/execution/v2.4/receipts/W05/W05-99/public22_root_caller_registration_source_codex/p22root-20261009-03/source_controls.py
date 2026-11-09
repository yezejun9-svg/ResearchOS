"""Finite Source controls for the v3 repair; no Canon, product, SQLite or native writes."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import runpy

N=Path(__file__).resolve().parent
R=Path(r'D:\作品集\ResearchOS\research-os')
B=R/'execution/v2.4/receipts/W05/W05-99'
ROOT_INPUT=R/'execution/v2.4/receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
reg=runpy.run_path(str(N/'register_public22.source.py'),run_name='pure_controls')
caller=runpy.run_path(str(N/'public22_root_caller.source.py'),run_name='pure_controls')
rows=[]

def check(label,ok,detail=None):
    rows.append({'id':label,'passed':bool(ok),'detail':detail,'scope':'PURE_SOURCE_ONLY'})
    if not ok: raise AssertionError(label)

def rejection(label,call,code):
    try:call()
    except ValueError as exc:check(label,str(exc)==code,str(exc))
    else:check(label,False,'unexpected acceptance')

def mutate(reference,**values):return {**reference,**values}

for name in ('register_public22.source.py','public22_root_caller.source.py'):
    tree=ast.parse((N/name).read_bytes())
    check('parse_'+name,tree is not None)
    check('import_side_effect_free_'+name,
          not any(isinstance(node,ast.Expr) and isinstance(node.value,ast.Call)
                  for node in tree.body))

before,cp,ow=reg['before']()
check('current_full_before4',len(before)==4 and reg['before']()[0]==before)
check('locked_python',reg['locked_python']()['sha256']==
      reg['read'](reg['pin'](R/'execution/toolchains/locked.json'))['tools']['python']['sha256'])
base=reg['pending']({'path':str(reg['BASE_PENDING'][0]),
                     'sha256':reg['BASE_PENDING'][1],'bytes':reg['BASE_PENDING'][2]})
check('base_first8',[x['ordinal'] for x in base['pending']]==list(range(1005,1013)))
live_ref={'path':str(ROOT_INPUT/'pending-diagnostics.cp370.live1016.root.json'),
          'sha256':'904233ae7c86c4f59e69f39f9f3dcb6db8355194b57a100ea4d66e3f6b4ceada',
          'bytes':11567}
check('live1016_exact_pin',reg['exact'](live_ref)==live_ref)
live=reg['pending'](live_ref)
check('live1016_first8_unchanged',live['pending'][:8]==base['pending'])
check('live1013_to1015_appended',[x['ordinal'] for x in live['pending'][8:]]==[1013,1014,1015]
      and live['next_original_failure_ordinal']==1016)
check('new_unknown_exits_null',all(x[k] is None for x in live['pending'][8:]
      for k in ('actual_native_exit','actual_dispatcher_exit','actual_model_exit')))

foreign_contract=caller['doc'](reg['pin'](B/'genuine_schema22_public_upgrade_runner_source_codex/s22public-20261009-01-v2/contract.json'))
foreign_review=caller['doc'](reg['pin'](B/'public22_runner_independent_source_review_codex/pub22r-20261009-02/HDF.json'))
foreign_source=caller['doc'](foreign_review['source_hdf_ref'])
for label,reference in [('guard',foreign_contract['source_guard']),
                        ('job',foreign_contract['owned_job']),
                        ('source_mf',foreign_source['manifest_ref']),
                        ('source_inputs',foreign_source['source_inputs_ref'])]:
    original=copy.deepcopy(reference)
    check('caller_accepts_foreign_'+label,
          len(caller['checked'](reference))==reference['bytes'] and reference==original)
    check('registrar_accepts_foreign_'+label,reg['exact'](reference)==reference)
    rejection('caller_rejects_changed_sha_'+label,
              lambda ref=reference:caller['checked'](mutate(ref,sha256='0'*64)),
              'REF_CHANGED')
    rejection('registrar_rejects_changed_bytes_'+label,
              lambda ref=reference:reg['exact'](mutate(ref,bytes=ref['bytes']+1)),
              'REF_CHANGED')

for label,value,code in [('unc','\\\\server\\share\\file','REF_LOCAL_PATH'),
                          ('relative','..\\source_guard.py','REF_LOCAL_PATH'),
                          ('traversal','D:/作品集/../source_guard.py','REF_REGULAR_PATH'),
                          ('ads','D:/作品集/file.py:alt','REF_LOCAL_PATH'),
                          ('device','D:/作品集/COM¹.txt','REF_REGULAR_PATH')]:
    rejection('caller_rejects_'+label,lambda v=value:caller['regular_path'](v),code)
    rejection('registrar_rejects_'+label,lambda v=value:reg['regular_path'](v),code)
for api,label in ((caller['checked'],'caller'),(reg['exact'],'registrar')):
    rejection(label+'_rejects_bool_bytes',
              lambda f=api:f(mutate(foreign_contract['source_guard'],bytes=True)),
              'REF_SHAPE')

resolved=caller['resolve_runner_source_hdf'](
    foreign_review,foreign_review['runner_ref'],foreign_review['contract_ref'])
check('real_foreign_hdf_source_inputs',resolved==foreign_source and
      len(caller['doc'](resolved['source_inputs_ref'])['references'])>100)
check('real_foreign_manifest_members_bound',
      all(any(caller['same_ref'](resolved[k],m) for m in caller['doc'](resolved['manifest_ref'])['members'])
          for k in ('runner_ref','contract_ref','source_inputs_ref')))
bad_review=dict(foreign_review,source_hdf_ref=reg['pin'](
    B/'public22_runner_independent_source_review_codex/pub22r-20261009-02/HDF.json'))
rejection('rejects_review_hdf_as_source_hdf',
          lambda:caller['resolve_runner_source_hdf'](
              bad_review,foreign_review['runner_ref'],foreign_review['contract_ref']),
          'RUNNER_SOURCE_HDF_BINDING')
rejection('rejects_swapped_runner_ref',
          lambda:caller['resolve_runner_source_hdf'](
              foreign_review,foreign_review['contract_ref'],foreign_review['contract_ref']),
          'RUNNER_SOURCE_HDF_BINDING')

alias=lambda r:mutate(r,path=r['path'].replace('\\','/'))
held=reg['held_without_canonical_pair'](
    [alias(before[0]),alias(before[1]),before[2],alias(before[2]),
     foreign_contract['source_guard'],alias(foreign_contract['source_guard'])],
    before[:2])
check('canonical_pair_excluded_under_slash_alias',
      len(held)==2 and all(reg['regular_path'](x['path']) not in
          {reg['regular_path'](y['path']) for y in before[:2]} for x in held))
dedup=caller['unique_refs']([foreign_contract['source_guard'],alias(foreign_contract['source_guard']),
                             foreign_contract['owned_job']])
check('caller_dedups_foreign_slash_alias',len(dedup)==2)

# A finite, actual-shaped CP370/OW174 projection. The synthetic owner/worker
# documents stand in only for Root outputs that have not been authorized yet.
synthetic=lambda c:{'path':'D:/Synthetic/'+c,'sha256':c*64,'bytes':1}
scope_ref,owner_ref,worker_ref=synthetic('1'),synthetic('2'),synthetic('3')
output='D:/Synthetic/schema22-public-'+'a'*32
common=dict(step_id='W05-99',slice_id=reg['SLICE'],state=reg['STATE'],
            scope_ref=scope_ref,output_root=output,owner='codex:/root',
            lease_status='ACTIVE',lease_expires_at='2099-01-01T00:00:00Z')
docs={scope_ref['sha256']:{'output_root':output},
      owner_ref['sha256']:dict(common,owner_id='codex:/root',selected_worker_id='codex:/root'),
      worker_ref['sha256']:dict(common,worker_id='codex:/root',selected_owner_ref=owner_ref)}
facts=dict(before_canonical_refs=before,scope_ref=scope_ref,owner_ref=owner_ref,
           worker_ref=worker_ref,source_hdf_ref=synthetic('4'),
           review_decision_ref=synthetic('5'),created_utc='2026-10-09T00:00:00Z')
transform=reg['transform'];namespace=transform.__globals__
real_read,real_pin=namespace['read'],namespace['pin']
pair_keys={reg['regular_path'](str(p)) for p in reg['CANON'][:2]}
attempted=[]
def exclusive_pin(path):
    if reg['regular_path'](str(path)) in pair_keys:
        attempted.append(str(path))
        raise PermissionError('SIMULATED_TP_SHAREMODE0_REOPEN_DENIED')
    return real_pin(path)
try:
    namespace['read']=lambda r:copy.deepcopy(docs[r['sha256']])
    namespace['pin']=exclusive_pin
    check_cp,check_ow=transform(cp,ow,facts,synthetic('6'),live,before,cp,ow)
    callback=lambda passed_cp,passed_ow:transform(
        passed_cp,passed_ow,facts,synthetic('6'),live,before,cp,ow)
    activate_cp,activate_ow=callback(copy.deepcopy(cp),copy.deepcopy(ow))
    check('check_projection_under_exclusive_pin',not attempted and check_cp==activate_cp
          and check_ow==activate_ow)
    rejection('activate_rejects_TP_passed_CP_drift',
              lambda:callback(dict(cp,revision=369),copy.deepcopy(ow)),
              'OWNER_WORKER_ACYCLIC')
    rejection('activate_rejects_before_vector_drift',
              lambda:transform(cp,ow,facts,synthetic('6'),live,
                               [mutate(before[0],sha256='0'*64),*before[1:]],cp,ow),
              'OWNER_WORKER_ACYCLIC')
finally:
    namespace['read']=real_read
    namespace['pin']=real_pin
check('full_inverse_and_pending1016_projection',
      check_cp['failure_counters'][:len(cp['failure_counters'])]==cp['failure_counters']
      and len(check_cp['failure_counters'])==len(cp['failure_counters'])+11
      and check_cp['work_in_progress']['root_next_failure_ordinal_live']==1016
      and check_cp['revision']==371 and check_ow['revision']==175)
check('actual_canon_untouched',reg['before']()[0]==before)
source_inputs=json.loads((N/'source-inputs.json').read_bytes())
check('v3_source_inputs_count',source_inputs['count']==47 and
      len(source_inputs['references'])==47)
check('v3_source_inputs_exact',all(reg['exact'](r)==r for r in source_inputs['references']))
check('v3_pending_and_first8_contract',
      source_inputs['pending_original_ordinals']==list(range(1005,1016)) and
      source_inputs['pending_first8_preserved'] is True and
      source_inputs['root_next_original_failure_ordinal']==1016)
calling_contract=json.loads((N/'root-calling-contract.source.json').read_bytes())
check('v3_contract_source_only',calling_contract['status']=='SOURCE_ONLY_NOT_REGISTERED_NOT_EXECUTED'
      and calling_contract['formal_acceptance'] is False and
      calling_contract['parent_acceptance'] is False)

raw={'schema':'researchos.root-public22-caller-registration-source-controls.v3',
     'scope':'PURE_SOURCE_ONLY_NO_PRODUCT_OR_CANON_WRITE','checks':rows,
     'count':len(rows),'pass':sum(x['passed'] for x in rows),
     'fail':sum(not x['passed'] for x in rows),'product_process_calls':0,
     'database_calls':0,'native_calls':0,'canonical_before_refs':before,
     'canonical_after_refs':reg['before']()[0],
     'actual_registration':False,'formal_acceptance':False}
p=N/'source-controls.locked.json'
p.write_bytes((json.dumps(raw,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps({'count':raw['count'],'pass':raw['pass'],'fail':raw['fail'],
                  'ref':{'path':str(p.resolve()),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
                         'bytes':p.stat().st_size}},ensure_ascii=False))
