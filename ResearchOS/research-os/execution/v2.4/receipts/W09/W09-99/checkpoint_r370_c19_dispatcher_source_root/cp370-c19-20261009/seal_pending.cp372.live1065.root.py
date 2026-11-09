from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json,os
R=Path(r'D:\作品集\ResearchOS\research-os');N=Path(__file__).resolve().parent
B=R/'execution/v2.4/receipts/W05/W05-99';W=R/'execution/v2.4/receipts/W09/W09-99'
THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUDIT=Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
tree=ast.parse((N/'seal_continuation.live1013.root.py').read_bytes())
exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in ('pin','exact','save','outputs','capture')],type_ignores=[]),'<Root-original-functions>','exec'),globals())
def verify(ref):
    value=pin(Path(ref['path']));assert (value['sha256'],value['bytes'])==(ref['sha256'],ref['bytes']);return ref
p=json.loads((N/'pending-diagnostics.cp371.live1059.root.json').read_bytes())
rows=list(p['pending']);assert [x['ordinal'] for x in rows]==list(range(1024,1059))
def add(number,ref,binding,description,outer,python,kind='ACTUAL_HOST_ORIGINAL_PAIR'):
    verify(ref)
    wrapper=None
    if binding is not None:
        verify(binding)
        wrapper=save('original%d.standard-binding.live1065.root.json'%number,dict(
            schema='researchos.root-original-diagnostic-binding.v1',issued_by='codex:/root',
            original_capture_ref=ref,original_source_binding_ref=binding,original_source_binding_selector='$',
            original_ordinal=number,original_bytes_unchanged=True,formal_authority=False))
    rows.append(dict(ordinal=number,origin_ref=ref,origin_selector='$',description=description,
        capture_completeness=kind,capture_binding_ref=wrapper,actual_outer_exit=outer,actual_python_exit=python,
        actual_native_exit=None,actual_Go_exit=None,actual_SQLite_exit=None,actual_dispatcher_exit=None,actual_model_exit=None))
nr=W/'full_w09_main_native_producer_independent_source_review_codex/review-fullw09-20261010-03'
originals=json.loads((nr/'original-failures-preserved.json').read_bytes())
descriptions={
1059:'Independent Source reviewer guessed schema23 meant23 source inputs; actual21 immutable keys matched. One invocation start9c0bf7/session15349/end68bba7; no new product.',
1060:'Independent Source reviewer guessed historical count54+15; exact original evidence54+14+1. One invocation bc71b6/session95656/a3fee4; old controls not rerun.',
1063:'Independent Source review report read wrapper guard.closed instead of actual cleanup.closed. Earlier genuine package/author/read_inputs checks preserved; original close result remains UNKNOWN_NOT_SERIALIZED.'}
for value in originals['originals']:
    add(value['ordinal'],value['completion_ref'],value['completion_binding_ref'],descriptions[value['ordinal']],value['outer_exit'],value['python_exit'])
v=originals['read_diagnostic']
add(1061,v['raw_ref'],v['binding_ref'],'Independent Source reviewer rg guessed old script name; no matching file, actual outer1, Python not invoked.',1,None)
def rootjs(call,result):
    return 'RESUME_POINTER.live1062.root.json' in str(call['payload'].get('input',call['payload'].get('arguments',''))) and 'Unexpected string' in str(result['payload'].get('output',''))
pair=capture(AUDIT,1062,rootjs,root=True);assert pair is not None
add(1062,pair[0],pair[1],'Root functions.exec JavaScript template had unescaped backticks. Parser rejected before shell or Python; all process exits remain NULL.',None,None)
io=exact(B/'fresh_main23_root_caller_registration_source_codex/main23root-20261010-04/failure-52671c.complete-original-IO.json',
    '0c916ded294975c780c778367f455345e373b5b5568ef496d0bc2417e28ea5df',1815)
add(1064,io,None,'Source M4 constructor guessed HDF calling_contract_ref; actual field contract_ref. Original constructor stopped before candidate source/contract/input writes. Actual process1/1; close result not serialized.',1,1,'SOURCE_REENCODED_FULL_ORIGINAL_HOST_PAIR')
rows.sort(key=lambda x:x['ordinal']);assert [x['ordinal'] for x in rows]==list(range(1024,1065))
o=json.loads((N/'public22.readonly.activation.after.observed.root.json').read_bytes())
canonical=[verify(x) for x in o['current_canonical_refs']]
cp=json.loads(Path(canonical[0]['path']).read_bytes());ow=json.loads(Path(canonical[1]['path']).read_bytes())
assert cp['revision']==372 and ow['revision']==176 and cp['work_in_progress']['root_next_failure_ordinal_live']==1024
assert len(cp['failure_counters'])==1021
pending=save('pending-diagnostics.cp372.live1065.root.json',dict(p,pending=rows,
    next_original_failure_ordinal=1065,registered_in_current_canon=False,counter_reset=False,current_canonical_refs=canonical))
resume=save('RESUME.cp372-public22-readonly-actual.live1065.root.json',dict(
    schema='researchos.root-execution-resume.v1',issued_by='codex:/root',root_thread_id=THREAD,
    created_utc=datetime.now(timezone.utc).isoformat(),canonical_refs=canonical,
    expected_revisions=dict(checkpoint=372,path_ownership=176,step_state=None,commands=39),
    registered_failure_records=1021,next_original_failure_ordinal=1065,pending_ref=pending,counter_reset=False,
    formal_cases_current_accepted=0,formal_cases_required=42,parent_tasks_required=22,
    original_public22_result='FAILED_ORIGINAL1025_RETAINED',public22_readonly_actual_status='READONLY_83_TABLES_VALIDATED_PENDING_NONAUTHOR_REVIEW',
    actual_root_bundle_ref=exact(N/'public22.readonly.actual.complete-hostpair-seal.root.json','e5d4e7628a0fbeb3e2a9640ff7e11f37a0c7eaf2aad9915269964d749a1dcc89',9275),
    Main23='M4_SOURCE_AUTHOR_TASK61_ACTIVE_NO_ACTUAL_BUILD',
    W09='V3_SOURCE_NONAUTHOR_ACCEPTED_NO_THREE_GROUP_EXECUTION',
    old21='ORIGINAL_SOURCE_RESOURCE_DISCOVERY_TASK63_ONLY_NO_BUILD',
    independent_actual_review='TASK64_ACTIVE_NO_SELF_ACCEPTANCE',
    goal_status='ACTIVE',formal_acceptance=False,parent_acceptance=False,
    prior_resume_ref=pin(N/'RESUME.cp371-time-contract-live1059.root.json')))
print(json.dumps(dict(pending_ref=pending,resume_ref=resume,pending_rows=len(rows),next_original_failure_ordinal=1065,Canonical_unchanged=True),ensure_ascii=False,indent=2))

