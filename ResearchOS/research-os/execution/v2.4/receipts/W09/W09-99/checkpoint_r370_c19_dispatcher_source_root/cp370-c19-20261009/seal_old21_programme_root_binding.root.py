"""Bind the already accepted independent programme review to actual Root readback."""
from pathlib import Path
from datetime import datetime, timezone
import ast,hashlib,json,os,sys,types
N=Path(__file__).resolve().parent;R=Path(r'D:\作品集\ResearchOS\research-os')
B=R/'execution/v2.4/receipts/W05/W05-99';THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUDIT=Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
t=ast.parse((N/'seal_continuation.live1013.root.py').read_bytes())
exec(compile(ast.Module(body=[x for x in t.body if isinstance(x,ast.FunctionDef) and x.name in {'pin','save','exact','outputs','capture'}],type_ignores=[]),'Root_functions_only','exec'),globals())
request=json.loads((N/'old21.programme.root-binding.observer-input.json').read_bytes())
payload_ref=request['payload_ref'];payload=json.loads(Path(payload_ref['path']).read_bytes())
def match(call,result):return any(x.get('chunk_id')=='ce7571' for x in outputs(result['payload'].get('output')))
pair=capture(AUDIT,106045,match,root=True);assert pair
binding=json.loads(Path(pair[1]['path']).read_bytes())
binding.update(source_audit_path=AUDIT.as_posix(),operation=request['operation'])
issued_binding=save('old21.programme.root-issuance.binding.json',binding)
lines=Path(pair[0]['path']).read_bytes().splitlines(keepends=True)
assert len(lines)==3 and [hashlib.sha256(x).hexdigest() for x in lines]==binding['original_line_sha256']
with AUDIT.open('rb') as f:
    for off,line in zip(binding['source_line_offsets'],lines):f.seek(off);assert f.readline()==line
call,result=[json.loads(x) for x in lines[1:]]
assert call['payload']['call_id']==result['payload']['call_id']==binding['original_call_id']
source=call['payload'].get('input',call['payload'].get('arguments'))
assert 'tools.exec_command' in source and 'OLD21_CAPTURE_OPERATION:OLD21_PROGRAMME_QUALIFICATION_BINDING' in source
hosts=[x for x in outputs(result['payload']['output']) if x.get('chunk_id')=='ce7571']
assert len(hosts)==1 and hosts[0]['exit_code']==0 and 'ROOT_SOURCE_PYTHON_EXIT=0' in hosts[0]['output']
observer=json.loads(hosts[0]['output'].splitlines()[0])
assert observer['schema']=='researchos.root-old21-capture-result.v2' and observer['issued_by']==observer['observer_actor']=='codex:/root'
assert observer['root_thread_id']==THREAD and observer['operation']==request['operation'] and observer['source']=='tools.exec_command'
assert observer['observed_refs']==request['observed_refs'] and observer['peer_actor']==payload['review_author']
assert not any(observer[x] for x in ('formal_acceptance','parent_acceptance','execution_grant'))
peer_binding=json.loads(Path(payload['independent_peer_delivery_binding_ref']['path']).read_bytes())
peer_lines=Path(peer_binding['original_capture_ref']['path']).read_bytes().splitlines(keepends=True)
assert len(peer_lines)==3 and [hashlib.sha256(x).hexdigest() for x in peer_lines]==peer_binding['original_line_sha256']
with AUDIT.open('rb') as f:
    for off,line in zip(peer_binding['source_line_offsets'],peer_lines):f.seek(off);assert f.readline()==line
peer_event=json.loads(peer_lines[-1]);text=peer_event['payload']['content'][0]['text']
prefix='Message Type: FINAL_ANSWER\nTask name: /root\nSender: /root/attach_fixture_source_review\nPayload:\n'
assert text.startswith(prefix);delivery=json.loads(text[len(prefix):])
assert delivery['review_refs']==payload['review_refs'] and delivery['review_author']==payload['review_author']
assert delivery['verdict']=='QUALIFIED_OLD21_BUILD_PENDING_ROOT_BINDING' and delivery['independent_non_author']
q=json.loads(Path(payload['review_refs'][3]['path']).read_bytes())
now=datetime.now(timezone.utc)
def when(x):return datetime.fromisoformat(x.replace('Z','+00:00'))
assert when(q['reviewed_at_utc'])<=when(peer_event['timestamp'])<=when(payload['created_utc'])<=when(call['timestamp'])<=when(result['timestamp'])<=now
for ref in request['observed_refs']:exact(Path(ref['path']),ref['sha256'],ref['bytes'])
qualified=save('old21.programme.qualification.bound.actual.root.json',dict(
    schema='researchos.root-old21-programme-qualification.v1',issued_by='codex:/root',root_thread_id=THREAD,
    status='QUALIFIED_OLD21_BUILD',created_utc=now.isoformat(),review_author=payload['review_author'],
    source_author=q['source_author'],caller_source_author=q['caller_source_author'],build_executor=q['build_executor'],
    independent_non_author=True,review_refs=payload['review_refs'],qualification_ref=payload['review_refs'][3],
    program_refs=q['program_refs'],provenance_ref=q['provenance_ref'],source_commit=q['source_commit'],source_tree=q['source_tree'],
    source_schema_version=q['source_schema_version'],database_schema_observation=q['database_schema_observation'],
    payload_ref=payload_ref,root_issuance_binding_ref=issued_binding,
    independent_peer_delivery_binding_ref=payload['independent_peer_delivery_binding_ref'],current_canonical_refs=payload['current_canonical_refs'],
    actual_Go_primary_exits=[0]*9,all_owned_jobs_idle_and_closed=True,complete_original_API_records_verified=True,
    original_API_process_stdout_truncated=True,original_process_stdout_complete=False,original_stdout_reconstructed=False,
    independent_durable_return_exact_readback_verified=True,programme_qualification=True,formal_acceptance=False,
    parent_acceptance=False,execution_grant=False,formal_case_accepted_delta=0,public_bootstrap_executed=False,
    backup_restore_executed=False,formal_old21_case='OPEN',full20to24='OPEN',original_diagnostic_ordinals=[1101,1102,1108],goal_status='ACTIVE'))
prior_ref=pin(N/'RESUME.cp375-w09-profile-adopted.live1111.root.json');prior=json.loads(Path(prior_ref['path']).read_bytes())
resume=save('RESUME.cp375-old21-qualified.live1111.root.json',dict(prior,
    created_utc=now.isoformat(),prior_resume_ref=prior_ref,old21='QUALIFIED_OLD21_BUILD_ACTUAL_NINE_GO_ZERO_INDEPENDENT_REVIEW_ROOT_BOUND',
    old21_programme_qualification_ref=qualified))
handoff=R/'execution/v2.4/HANDOFF_RESUME_PACK.md';old=handoff.read_bytes()
with (N/'historical.HANDOFF.before-old21-binding.live1111.root.md').open('xb') as f:f.write(old);f.flush();os.fsync(f.fileno())
prefix=('# Current Root continuation: CP375 / OW179 / CM40 / live next1111\n\n'
    'Old21 actual nine Go phases passed; independent programme review now bound to completed Root readback. Public bootstrap, restore and formal old21 case remain OPEN. W09 profile/CM40 adopted; minimal Native scope path repair independently under review. Goal ACTIVE; formal0/42; original1109..1110 pending.\n\n'
    'Current resume: '+resume['path']+'\nSHA256 '+resume['sha256']+' bytes '+str(resume['bytes'])+'\n\n').encode()
with handoff.open('wb') as f:f.write(prefix+old);f.flush();os.fsync(f.fileno())
assert handoff.read_bytes().endswith(old)
print(json.dumps(dict(root_bound_qualification_ref=qualified,root_issuance_binding_ref=issued_binding,resume_ref=resume,
    actual_root_observer_outer_exit=0,status='QUALIFIED_OLD21_BUILD',Canon_unchanged=True,formal_case_accepted_delta=0),ensure_ascii=False,indent=2))
