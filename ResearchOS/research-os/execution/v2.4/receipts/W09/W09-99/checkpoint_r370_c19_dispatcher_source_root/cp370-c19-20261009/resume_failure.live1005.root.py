"""Preserve the one actual pre-write registrar refusal, without retrying it."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib, json, os

N=Path(__file__).resolve().parent
S=N.parent.parent/'checkpoint_r369_native_source_root/cp369-c19-20261009'
P=Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'

def pin(path):
    path=path.resolve(strict=True);raw=path.read_bytes()
    return dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))

def read(ref):
    assert set(ref)=={'path','sha256','bytes'} and pin(Path(ref['path']))==ref
    return Path(ref['path']).read_bytes()

def save(path,value):
    with path.open('xb') as file:
        file.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode());file.flush();os.fsync(file.fileno())
    return pin(path)

def results(value):
    if isinstance(value,list):
        for child in value:yield from results(child)
    elif isinstance(value,dict):
        if 'chunk_id' in value:yield value
        else:
            for child in value.values():yield from results(child)
    elif isinstance(value,str):
        try: parsed=json.loads(value)
        except ValueError:return
        yield from results(parsed)

io_ref=pin(N/'failure1004.original-tool-io.root.json');io=json.loads(read(io_ref))
assert io['ordinal']==1004 and io['actual_outer_exit']==io['actual_python_exit']==1
assert all(io[key] is None for key in ('actual_native_exit','actual_dispatcher_exit','actual_model_exit'))
calls={};found=[]
with P.open('rb') as file:
    header_raw=file.readline();header=json.loads(header_raw)
    assert header['type']=='session_meta' and header['payload']['id']==THREAD
    while True:
        offset=file.tell();raw=file.readline()
        if not raw:break
        event=json.loads(raw);payload=event.get('payload',{})
        if event.get('type')!='response_item' or not isinstance(payload,dict):continue
        if payload.get('type')=='custom_tool_call':calls[payload['call_id']]=(event,raw,offset)
        elif payload.get('type')=='custom_tool_call_output':
            for result in results(payload.get('output')):
                if result.get('chunk_id')=='c58628':found.append((calls[payload['call_id']],event,raw,offset,result))
    observed_size=file.tell()
assert len(found)==1
(call,call_raw,call_offset),event,output_raw,output_offset,result=found[0]
assert result==io['result'] and call['payload']['call_id']==event['payload']['call_id']
raws=(header_raw,call_raw,output_raw)
capture_path=N/'original1004.actual-root-host.raw.jsonl'
with capture_path.open('xb') as file:file.write(b''.join(raws));file.flush();os.fsync(file.fileno())
capture_ref=pin(capture_path)
with P.open('rb') as file:
    for offset,raw in zip((0,call_offset,output_offset),raws):file.seek(offset);assert file.read(len(raw))==raw
binding_ref=save(N/'original1004.actual-root-host.binding.root.json',dict(schema='researchos.root-actual-tool-capture-binding.v1',issued_by='codex:/root',root_thread_id=THREAD,
    original_capture_ref=capture_ref,source_audit_path=str(P),source_prefix_size_observed=observed_size,
    source_line_offsets=[0,call_offset,output_offset],source_line_bytes=[len(raw) for raw in raws],original_line_sha256=[hashlib.sha256(raw).hexdigest() for raw in raws],
    original_call_id=call['payload']['call_id'],tool_result_chunk_id='c58628',tool_call_timestamp=call['timestamp'],tool_result_timestamp=event['timestamp'],formal_authority=False,parent_acceptance=False))
resume=json.loads((S/'RESUME.cp369-main-profile-adopted.seed.live1004.root.json').read_bytes())
for ref in resume['canonical_refs']:read(ref)
pending=json.loads(read(resume['pending_diagnostics_ref']))
assert [row['ordinal'] for row in pending['pending']]==list(range(966,1004))
pending['pending'].append(dict(ordinal=1004,origin_ref=capture_ref,origin_selector='call_id='+call['payload']['call_id'],
    description='Root actual CP370 registrar v3 build rejected the genuine two-block host output as HOST_OUTPUT_NOT_PLAINTEXT before any Scope/facts/Canon write; original outer/Python1, no Native/dispatcher/model execution.',
    origin_capture_completeness='ROOT_RECORDED_ORIGINAL_TOOL_IO',capture_binding_ref=binding_ref,original_tool_io_ref=io_ref,
    actual_outer_exit=1,actual_python_exit=1,actual_native_exit=None,actual_dispatcher_exit=None,actual_model_exit=None))
pending['next_original_failure_ordinal']=1005
pending_ref=save(S/'pending-diagnostics.live1005.root.json',pending)
resume.update(created_utc=datetime.now(timezone.utc).isoformat(),next_original_failure_ordinal_live=1005,pending_diagnostics_ref=pending_ref,
    CP370_status='V3_REAL_BUILD_HOST_LAYOUT_REFUSED_PREWRITE_V4_SOURCE_FIX_PENDING',original1004_actual_host_ref=capture_ref,
    original1004_capture_binding_ref=binding_ref,current_original_qualification_status='SEED1004_FROZEN_NEW1004_PENDING_POSTSEAL_QUALIFICATION')
for ref in resume['canonical_refs']:read(ref)
resume_ref=save(S/'RESUME.cp369-main-profile-adopted.live1005.root.json',resume)
print(json.dumps(dict(resume_ref=resume_ref,pending_ref=pending_ref,original1004_capture_ref=capture_ref,next_original=1005,Canonical_unchanged=True,formal_delta=0),ensure_ascii=False),flush=True)
