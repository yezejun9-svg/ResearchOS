"""Preserve every completed Root host segment and read the full durable return losslessly."""
from pathlib import Path
from datetime import datetime, timezone
import ast, hashlib, json, os
R=Path(r'D:\作品集\ResearchOS\research-os');N=Path(__file__).resolve().parent
B=R/'execution/v2.4/receipts/W05/W05-99'
THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUDIT=Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
t=ast.parse((N/'seal_continuation.live1013.root.py').read_bytes())
exec(compile(ast.Module(body=[x for x in t.body if isinstance(x,ast.FunctionDef) and x.name in
    {'pin','save','exact','outputs','capture'}],type_ignores=[]),'Root_helper_functions_only','exec'),globals())
chunks=[(106036,'fabc19'),(106037,'1e8ac7'),(106038,'bc2712'),(106039,'d24278'),
    (106040,'d33198'),(106041,'59a3a4'),(106042,'4710a4'),(106043,'b5c6ba'),(106044,'56a923')]
pairs=[]
for number,chunk in chunks:
    def match(call,result):return any(x.get('chunk_id')==chunk for x in outputs(result['payload'].get('output')))
    pair=capture(AUDIT,number,match,root=True);assert pair,'MISSING_ACTUAL_ROOT_HOST_SEGMENT:'+chunk
    actual=json.loads(Path(pair[0]['path']).read_bytes().splitlines()[-1])
    hosts=[x for x in outputs(actual['payload']['output']) if x.get('chunk_id')==chunk]
    assert len(hosts)==1
    host=hosts[0]
    if chunk in ('fabc19','4710a4','b5c6ba','56a923'):assert host['exit_code']==0
    else:assert host['session_id']==17390 and 'exit_code' not in host
    if chunk=='4710a4':assert 'ROOT_ACTUAL_PYTHON_EXIT=0' in host['output']
    pairs.append(dict(actual_chunk_id=chunk,original_raw_ref=pair[0],capture_binding_ref=pair[1],
        actual_exit=host.get('exit_code'),actual_session_id=host.get('session_id'),
        original_api_output_truncation=('truncated output' in host.get('output',''))))
C=B/'integration_codex/old21-caller-9c80f2c133f443bb8a2a629680cbba5d'
caller_ref=exact(C/'caller-return.root.json','ddda653303194eacf23aec90543808802679eccd8378d6d5699b2cb228ebf2eb',11735797)
state_ref=exact(C/'builder-returned-state.root.json','476db49e358ca6b96b7c57c01b4282ae30d62c06c458080bddb26f552a7d74ca',6508341)
record=json.loads(Path(caller_ref['path']).read_bytes());state=json.loads(Path(state_ref['path']).read_bytes())
assert state==record['builder_returned_state'] and record['caller_error'] is None and state['first_failure'] is None
assert record['Root_failure_assignment_required'] is False and record['formal_acceptance'] is False and record['parent_acceptance'] is False
assert len(state['calls'])==9 and all(c['actual_exit']==0 for c in state['calls'])
assert [c['phase'] for c in state['calls']]==['go-version','control-declared','control-export','control-build','control-inspect','backup-declared','backup-export','backup-build','backup-inspect']
cleanup=record['source_guard_cleanup'];assert cleanup['closed'] is True and cleanup['retained_handles_count']==0 and not cleanup['errors']
assert state['closed_receipt']['status']=='PUBLISHED';closed_ref=state['closed_receipt']['ref']
exact(Path(closed_ref['path']),closed_ref['sha256'],closed_ref['bytes'])
programs={k:v['program_ref'] for k,v in state['target_results'].items()};assert set(programs)=={'control','backup'}
for ref in programs.values():exact(Path(ref['path']),ref['sha256'],ref['bytes'])
before=json.loads((N/'old21.v3.build.actual-request.root.json').read_bytes())['current_canonical_refs']
for ref in before:exact(Path(ref['path']),ref['sha256'],ref['bytes'])
seal=save('old21.v3.actual.complete-hostpair-seal.root.json',dict(schema='researchos.root-actual-old21-complete-hostpair-seal.v1',
    issued_by='codex:/root',root_thread_id=THREAD,created_utc=datetime.now(timezone.utc).isoformat(),
    actual_request_ref=pin(N/'old21.v3.build.actual-request.root.json'),complete_original_hostpairs=pairs,
    actual_Outer_Python_exit=0,actual_Go_exits=[0]*9,caller_return_ref=caller_ref,persisted_builder_state_ref=state_ref,
    closed_receipt_ref=closed_ref,program_refs=programs,full_durable_JSON_losslessly_read=True,FILETIME_numbers='PYTHON_INT_NO_JS_JSON_PARSE',
    actual_API_stdout_truncation_retained=True,full_durable_return_is_additional_evidence=True,
    Source_guard_closed=True,retained_handles_count=0,Canon_unchanged=True,current_canonical_refs=before,
    independent_programme_review_required=True,formal_acceptance=False,parent_acceptance=False,formal_case_accepted_delta=0))
print(json.dumps(dict(seal_ref=seal,caller_return_ref=caller_ref,persisted_builder_state_ref=state_ref,
    program_refs=programs,actual_Go_calls=9,actual_Go_exits=[0]*9,Root_actual_Python_exit=0,
    Source_guard_closed=True,retained_handles_count=0,Canon_unchanged=True,formal_acceptance=False),ensure_ascii=False,indent=2))
