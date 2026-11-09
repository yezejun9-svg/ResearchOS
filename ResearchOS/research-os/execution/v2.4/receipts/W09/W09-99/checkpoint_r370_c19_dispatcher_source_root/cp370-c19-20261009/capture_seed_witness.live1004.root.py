"""Capture actual Root host tool bytes; grants no activation or formal authority."""
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json,os
N=Path(__file__).resolve().parent
P=Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
def pin(p):
    b=p.read_bytes();return dict(path=str(p.resolve(strict=True)),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def read(r):
    assert set(r)=={'path','sha256','bytes'}
    b=Path(r['path']).read_bytes();assert len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256'];return b
def save(name,v):
    with (N/name).open('xb') as f:
        f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
    return pin(N/name)
def parsed_outputs(v):
    if isinstance(v,list):
        for x in v:yield from parsed_outputs(x)
    elif isinstance(v,dict):
        if 'chunk_id' in v:yield v
        else:
            for x in v.values():yield from parsed_outputs(x)
    elif isinstance(v,str):
        try:x=json.loads(v)
        except ValueError:return
        yield from parsed_outputs(x)
qr=pin(N/'original-diagnostic-qualifications.seed.live1004.root.json');q=json.loads(read(qr))
assert qr['sha256']=='c4de0877dadf3aba8d8c9f227590dd4a0fc094769b5f21ad8456f8cf4e5a0b7f'
assert q['issued_by']=='codex:/root' and q['next_original_failure_ordinal']==1004
io_ref=pin(N/'qualification-seed.live1004.actual.original-tool-io.root.json');io=json.loads(read(io_ref))
assert io['actor_id']=='codex:/root' and type(io['actual_outer_exit']) is int and io['actual_outer_exit']==0 and io['actual_python_exit']==0
for r in q['before_canonical_refs']:read(r)
calls={};selected=[]
with P.open('rb') as f:
    header_raw=f.readline();header=json.loads(header_raw)
    assert header['type']=='session_meta' and header['payload']['id']==THREAD
    while True:
        pos=f.tell();raw=f.readline()
        if not raw:break
        event=json.loads(raw);v=event.get('payload',{})
        if event.get('type')!='response_item' or not isinstance(v,dict):continue
        if v.get('type') in ('custom_tool_call','function_call'):
            calls[v.get('call_id')]=(event,raw,pos)
        elif v.get('type') in ('custom_tool_call_output','function_call_output'):
            for result in parsed_outputs(v.get('output')):
                if result.get('chunk_id')=='37dfc7':
                    assert v.get('call_id') in calls
                    selected.append((calls[v['call_id']],event,raw,pos,result))
    observed_size=f.tell()
assert len(selected)==1,'EXACT_ROOT_HOST_TOOL_PAIR_REQUIRED'
(call,call_raw,call_pos),event,result_raw,result_pos,result=selected[0]
assert call['payload']['call_id']==event['payload']['call_id'] and result==io['result']
assert 'qualification_seed.live1004.root.py' in call['payload'].get('input',call['payload'].get('arguments',''))
assert type(result['exit_code']) is int and result['exit_code']==0 and 'ROOT_SOURCE_PYTHON_EXIT=0' in result['output']
raws=(header_raw,call_raw,result_raw)
out=N/'qualification-seed.live1004.creator.actual-host.raw.jsonl'
with out.open('xb') as f:
    f.write(b''.join(raws));f.flush();os.fsync(f.fileno())
capture=pin(out)
binding=save('qualification-seed.live1004.creator.actual-host.binding.root.json',dict(schema='researchos.root-actual-tool-capture-binding.v1',issued_by='codex:/root',root_thread_id=THREAD,
    original_capture_ref=capture,source_audit_path=str(P),source_prefix_size_observed=observed_size,
    source_line_offsets=[0,call_pos,result_pos],source_line_bytes=[len(x) for x in raws],original_line_sha256=[hashlib.sha256(x).hexdigest() for x in raws],
    original_call_id=call['payload']['call_id'],tool_result_chunk_id='37dfc7',tool_call_timestamp=call['timestamp'],tool_result_timestamp=event['timestamp'],formal_authority=False,parent_acceptance=False))
with P.open('rb') as f:
    for pos,raw in zip((0,call_pos,result_pos),raws):f.seek(pos);assert f.read(len(raw))==raw
witness=save('seed.actual-observation-witness.live1004.root.json',dict(schema='researchos.root-cp370-actual-observation-witness.v1',issued_by='codex:/root',root_thread_id=THREAD,created_utc=datetime.now(timezone.utc).isoformat(),phase='SEED',
    next_original_failure_ordinal=1004,canonical_refs=q['before_canonical_refs'],qualification_ref=qr,original_tool_io_ref=io_ref,actual_host_capture_ref=capture,capture_binding_ref=binding,registrar_review_refs=[],formal_acceptance=False,parent_acceptance=False,counter_reset=False))
for r in q['before_canonical_refs']:read(r)
print(json.dumps(dict(witness_ref=witness,actual_host_capture_ref=capture,capture_binding_ref=binding,original_io_ref=io_ref,actual_qualification_creator_verified=True,Canonical_unchanged=True,activation_grant=False,formal_delta=0),ensure_ascii=False),flush=True)
