from pathlib import Path
import ast,hashlib,json,os
R=Path(r'D:\作品集\ResearchOS\research-os');N=Path(__file__).resolve().parent
THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUDIT=Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
tree=ast.parse((N/'seal_continuation.live1013.root.py').read_bytes())
exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in ('pin','save','outputs','capture')],type_ignores=[]),'<Root-capture-functions>','exec'),globals())
def match_chunk(chunk):
    return lambda call,result:any(x.get('chunk_id')==chunk for x in outputs(result['payload'].get('output')))
records={}
for number,label,chunk in ((106003,'build_start','fcf4e8'),(106004,'build_complete','d45596'),
    (106005,'check_start','523cdc'),(106006,'check_complete','ea072e'),(106007,'activate_start','153124'),
    (106008,'activate_complete','655ad8'),(106009,'readonly_start','a0f785'),(106010,'readonly_complete','98d0a5')):
    raw,binding=capture(AUDIT,number,match_chunk(chunk),root=True)
    records[label]=dict(chunk_id=chunk,raw_ref=raw,binding_ref=binding)
out=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/public22-recheck-observation-b9fbaa2bb39e4d85857f0354f2425dba'
caller=pin(out/'caller-return.root.json');observation=pin(out/'readonly-observation.root.json');guard=pin(out/'readonly.guard.closed.json')
d=json.loads(Path(caller['path']).read_bytes());g=json.loads(Path(guard['path']).read_bytes())
assert d['status']=='READONLY_83_TABLES_VALIDATED_PENDING_NONAUTHOR_REVIEW' and d['error'] is None and not d['secondary_errors']
assert d['leaf_returned']['table_count']==83 and d['new_native_children']==0 and d['original1025_result']=='FAILED_RETAINED'
assert g['closed'] is True and g['retained_handles_count']==0 and not g['errors']
o=json.loads((N/'public22.readonly.activation.after.observed.root.json').read_bytes())
for ref in o['current_canonical_refs']:
    current=pin(Path(ref['path']));assert (current['sha256'],current['bytes'])==(ref['sha256'],ref['bytes'])
bundle=save('public22.readonly.actual.complete-hostpair-seal.root.json',dict(
    schema='researchos.root-public22-existing-actual-hostpair-seal.v1',issued_by='codex:/root',root_thread_id=THREAD,
    records=records,source_caller_request_ref=pin(N/'public22.readonly.registration-request.actual.root.json'),
    actual_request_ref=pin(N/'public22.readonly.actual-request.root.json'),activation_observation_ref=pin(N/'public22.readonly.activation.after.observed.root.json'),
    caller_return_ref=caller,observation_ref=observation,source_guard_closed_ref=guard,current_canonical_refs=o['current_canonical_refs'],
    actual_outer_exit=0,actual_python_exit=0,new_native_children=0,original1025_result='FAILED_RETAINED',
    formal_acceptance=False,parent_acceptance=False,independent_review_status='PENDING'))
print(json.dumps(dict(bundle_ref=bundle,caller_return_ref=caller,observation_ref=observation,guard_closed_ref=guard,Source_guard_held_count=g['retained_handles_count']),ensure_ascii=False,indent=2))

