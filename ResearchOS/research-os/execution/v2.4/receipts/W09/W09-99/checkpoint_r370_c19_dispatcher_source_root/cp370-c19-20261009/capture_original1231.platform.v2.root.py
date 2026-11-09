"""Capture a genuine orchestration parser failure; no host exit is invented."""
from pathlib import Path
import hashlib,json,os
S=Path(__file__).resolve().parent
A=Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
def pin(p):
    b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(p,b):
    with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
    return pin(p)
def texts(v):
    if isinstance(v,str):yield v
    elif isinstance(v,list):
        for x in v:yield from texts(x)
    elif isinstance(v,dict):
        for x in v.values():yield from texts(x)
found=[];calls={}
with A.open('rb') as f:
    head=f.readline();assert json.loads(head)['payload']['id']=='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
    f.seek(0,2);size=f.tell();start=max(len(head),size-32*1024*1024);f.seek(start)
    if start>len(head):f.readline()
    while True:
        off=f.tell();raw=f.readline()
        if not raw:break
        e=json.loads(raw);p=e.get('payload',{})
        if e.get('type')!='response_item' or not isinstance(p,dict):continue
        if p.get('type') in ('function_call','custom_tool_call'):calls[p['call_id']]=(off,raw,e)
        elif p.get('type') in ('function_call_output','custom_tool_call_output') and p.get('call_id') in calls:
            value='\n'.join(texts(p.get('output')))
            if e['timestamp']>='2026-10-10T02:56:00' and any(t.strip()=="Script error:\nSyntaxError: Unexpected token ')'" for t in texts(p.get('output'))):found.append((calls[p['call_id']],(off,raw,e)))
assert len(found)==1,('EXACT_PLATFORM_PARSER_FAILURE_REQUIRED',len(found))
first,last=found[0];assert first[2]['ordinal']<last[2]['ordinal'];lines=[head,first[1],last[1]];offsets=[0,first[0],last[0]]
with A.open('rb') as f:
    for off,line in zip(offsets,lines):f.seek(off);assert f.readline()==line
rr=save(S/'original1231.platform-actual.raw.root.jsonl',b''.join(lines))
d=dict(schema='researchos.root-platform-original-failure.v1',issued_by='codex:/root',actor_id='codex:/root',original_ordinal=1231,source_audit_path=str(A),source_prefix_size_observed=size,source_line_offsets=offsets,source_line_bytes=[len(x) for x in lines],original_line_sha256=[hashlib.sha256(x).hexdigest() for x in lines],original_capture_ref=rr,original_call_id=first[2]['payload']['call_id'],actual_outer_exit=None,actual_python_exit=None,actual_native_exit=None,actual_Go_exit=None,actual_SQLite_exit=None,actual_dispatcher_exit=None,actual_model_exit=None,tool_code_executed=False,host_process_started=False,formal_acceptance=False,artifact_binding_authority=False,counter_reset=False)
br=save(S/'original1231.platform-actual.binding.root.json',(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps(dict(binding_ref=br,raw_ref=rr,all_actual_process_exits=None,formal_acceptance=False),ensure_ascii=False))
