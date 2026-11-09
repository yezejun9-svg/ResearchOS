"""Pure Source controls; no registrar action, child process, SQLite, or Native call."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import runpy

N=Path(__file__).resolve().parent
reg=runpy.run_path(str(N/'register_public22.source.py'),run_name='source_controls')
caller=runpy.run_path(str(N/'public22_root_caller.source.py'),run_name='source_controls')
rows=[]
def check(label,value):
    if not value:raise AssertionError(label)
    rows.append({'id':label,'passed':True,'scope':'PURE_SOURCE_ONLY'})

for name in ('register_public22.source.py','public22_root_caller.source.py'):
    tree=ast.parse((N/name).read_bytes())
    check('parse_'+name,tree is not None)
    check('import_has_no_execution_'+name,
          not any(isinstance(node,ast.Expr) and isinstance(node.value,ast.Call)
                  for node in tree.body))
check('current_CP370_OW174_fullbefore4',len(reg['before']()[0])==4)
check('locked_python_identity',reg['locked_python']()['sha256']==
      reg['read'](reg['pin'](reg['R']/'execution/toolchains/locked.json'))['tools']['python']['sha256'])
live=reg['pending']({'path':str(reg['BASE_PENDING'][0]),
    'sha256':reg['BASE_PENDING'][1],'bytes':reg['BASE_PENDING'][2]})
check('original_pending_1005_to_1012_exact',
      [row['ordinal'] for row in live['pending']]==list(range(1005,1013)) and
      live['pending'][-1]['actual_outer_exit'] is None and
      live['pending'][-1]['actual_python_exit'] is None)
before,cp,ow=reg['before']()
held=reg['held_without_canonical_pair']([before[0],before[1],before[2],before[2]],before[:2])
check('canonical_pair_verified_but_not_held_during_update_pair',held==[before[2]])
ref=lambda c:{'path':'D:/Synthetic/'+c,'sha256':c*64,'bytes':1}
scope_ref,owner_ref,worker_ref=ref('1'),ref('2'),ref('3')
output='D:/Synthetic/schema22-public-'+'a'*32
common=dict(step_id='W05-99',slice_id=reg['SLICE'],state=reg['STATE'],
    scope_ref=scope_ref,output_root=output,owner='codex:/root',
    lease_status='ACTIVE',lease_expires_at='2099-01-01T00:00:00Z')
docs={scope_ref['sha256']:{'output_root':output},
      owner_ref['sha256']:dict(common,owner_id='codex:/root',
          selected_worker_id='codex:/root'),
      worker_ref['sha256']:dict(common,worker_id='codex:/root',
          selected_owner_ref=owner_ref)}
facts=dict(before_canonical_refs=before,scope_ref=scope_ref,owner_ref=owner_ref,
    worker_ref=worker_ref,source_hdf_ref=ref('4'),review_decision_ref=ref('5'),
    created_utc='2026-10-09T00:00:00Z')
transform=reg['transform'];global_map=transform.__globals__
original_read=global_map['read']
try:
    global_map['read']=lambda r:copy.deepcopy(docs[r['sha256']])
    after_cp,after_ow=transform(cp,ow,facts,ref('6'),live)
finally:global_map['read']=original_read
check('projection_registers_unique_root_worker',
      len(after_cp['workers'])==len(cp['workers'])+1 and
      after_ow['card_path_bindings']['W05-99']['subtasks'][reg['KEY']]['owner']=='codex:/root')
check('projection_appends_exact_eight_once_with_null_unknown',
      len(after_cp['failure_counters'])==len(cp['failure_counters'])+8 and
      after_cp['failure_counters'][:len(cp['failure_counters'])]==cp['failure_counters'] and
      after_cp['failure_counters'][-1]['original_payload']['actual_outer_exit'] is None and
      after_cp['work_in_progress']['root_next_failure_ordinal_live']==1013)
check('projection_revisions_no_formal_acceptance',
      after_cp['revision']==371 and after_ow['revision']==175 and
      after_ow['card_path_bindings']['W05-99']['subtasks'][reg['KEY']]['formal_case_accepted_delta']==0)
check('canonical_unchanged_after_projection',reg['before']()[0]==before)
register_tree=ast.parse((N/'register_public22.source.py').read_bytes())
check('activation_calls_trusted_update_pair',any(
    isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and
    node.func.attr=='update_pair' for node in ast.walk(register_tree)))
check('postreview_refresh_and_external_hostpair_gates',
      'ROOT_POSTREVIEW_LIVE_REFRESH' in (N/'register_public22.source.py').read_text() and
      'ROOT_EXTERNAL_REVIEW_HOSTPAIR' in (N/'register_public22.source.py').read_text() and
      'ACTIVATION_WITNESS_NOT_BOUND' in (N/'register_public22.source.py').read_text())
try:caller['LiveScope'](scope_ref,ref('7'),owner_ref,worker_ref,ref('8'),output,None,{})._fresh()
except ValueError as exc:check('no_live_capability_without_held_closure',str(exc)=='ROOT_HELD_CLOSURE_RELEASED')
else:raise AssertionError('UNHELD_SCOPE_ACCEPTED')
raw={'schema':'researchos.root-public22-caller-registration-source-controls.v1',
     'scope':'PURE_SOURCE_ONLY_NO_PRODUCT_OR_CANON_WRITE',
     'checks':rows,'count':len(rows),'pass':len(rows),'fail':0,
     'product_process_calls':0,'database_calls':0,'native_calls':0,
     'canonical_after_refs':before,'actual_registration':False,
     'formal_acceptance':False}
p=N/'source-controls.locked.json'
with p.open('xb') as f:f.write((json.dumps(raw,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps({'count':len(rows),'pass':len(rows),'fail':0,
                  'ref':{'path':str(p.resolve()),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
                         'bytes':p.stat().st_size}},ensure_ascii=False))
