"""Read the complete persisted return with lossless integers, not truncated API text."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,types
N=Path(__file__).resolve().parent
R=Path(r'D:\作品集\ResearchOS\research-os');B=R/'execution/v2.4/receipts/W05/W05-99'
out=B/'integration_codex/fresh-main23-3ef8ee61a94e4adca86a00f55a8b7a13'
receipt=B/'integration_codex/fresh-main23-caller-3ef8ee61a94e4adca86a00f55a8b7a13'
def pin(p):
    raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
refs=[pin(receipt/x) for x in ('caller-return.root.json','builder-returned-state.root.json')]
assert [(r['sha256'],r['bytes']) for r in refs]==[
 ('809d7c96852cf6a53a5ffef2ea4b3f6f7186090ce9d71e57b2259c6dcf2f705f',11809063),
 ('f627d47e08ab0f0e57a96e1ad3291c92a12b6dbb9cd6074844880331e7ac1361',6510571)]
guard_path=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
guard_raw=guard_path.read_bytes();assert hashlib.sha256(guard_raw).hexdigest()=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
guard_module=types.ModuleType('root_main23_actual_return_guard');guard_module.__file__=str(guard_path)
exec(compile(guard_raw,str(guard_path),'exec'),guard_module.__dict__)
held=guard_module.SourceReadGuard(per_file_cap=512*1024*1024,total_cap=1024*1024*1024)
cleanup=None
try:
    held.acquire(refs)
    returned=json.loads(Path(refs[0]['path']).read_bytes())
    state=json.loads(Path(refs[1]['path']).read_bytes())
    assert returned['builder_returned_state']==state
    assert returned['caller_error'] is None and not returned['Root_failure_assignment_required']
    assert state['status']=='BUILT_CANDIDATE_PENDING_NONAUTHOR_PROGRAMME_REVIEW'
    calls=[]
    for value in state['calls']:
        o=value['observation'];j=o['job_cleanup'];ct=o['creation_time_100ns']
        assert type(ct) is int and 0<ct<2**64 and type(o['owned_child_pid']) is int
        assert value['actual_exit']==o['actual_exit']==0 and not o['timed_out'] and o['error'] is None
        assert j['job_idle_confirmed'] and j['handles_closed'] and j['assigned_before_resume'] and not j['errors']
        calls.append(dict(phase=value['phase'],actual_exit=value['actual_exit'],pid=o['owned_child_pid'],
            creation_time_100ns_decimal=str(ct),job_idle_confirmed=True,handles_closed=True,
            stdout_ref=value['stdout_ref'],stderr_ref=value['stderr_ref'],result_ref=value['result_ref']))
    assert len(calls)==5
    assert returned['source_guard_cleanup']['closed'] and returned['source_guard_cleanup']['retained_handles_count']==0
    state_refs={k:v for k,v in state.items() if isinstance(v,dict) and set(v)=={'path','sha256','bytes'}}
    record=dict(schema='researchos.root-main23-actual-return-file-observation.v1',issued_by='codex:/root',
        root_thread_id='01a11007-5233-7ca1-b71f-9e9e5ce84c98',created_utc=datetime.now(timezone.utc).isoformat(),
        full_persisted_return_refs=refs,state_keys=list(state),state_refs=state_refs,calls=calls,
        actual_outer_exit=0,actual_python_exit=0,caller_error=None,product_first_failure=state.get('first_failure'),
        original_API_process_stdout_truncated=True,original_process_stdout_complete_not_asserted=True,
        original_API_response_must_be_preserved_unchanged=True,independent_programme_qualification=None,
        formal_acceptance=False,parent_acceptance=False)
finally:cleanup=held.close()
assert cleanup['closed'] and cleanup['retained_handles_count']==0 and not cleanup['errors']
def save(name,v):
    p=N/name
    with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
    return pin(p)
record['read_guard_closed_ref']=save('main23.v4.actual-return-read.guard.closed.root.json',cleanup)
observation_ref=save('main23.v4.actual-return-file-observation.root.json',record)
print(json.dumps(dict(observation_ref=observation_ref,state_keys=record['state_keys'],
    state_refs=record['state_refs'],calls=calls,full_return_refs=refs,guard_closed_zero=True,
    independent_programme_qualification=None,process_stdout_truncation_retained=True),ensure_ascii=False,indent=2))
