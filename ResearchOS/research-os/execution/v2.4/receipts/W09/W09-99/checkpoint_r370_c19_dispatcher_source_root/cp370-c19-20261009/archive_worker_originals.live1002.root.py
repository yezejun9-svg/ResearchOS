"""Actual child-host original pairs, exact immutable ranges, one ordinal per call."""
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json,os
N=Path(__file__).resolve().parent
P=Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\09\rollout-2026-10-09T17-49-39-01a12011-7d41-7991-a01c-de2d71701ff7.jsonl')
ROOT_THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
ACTOR='codex:/root/w09_formal_profile_source_impl'
def pin(p):
    b=p.read_bytes();return dict(path=str(p.resolve(strict=True)),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(name,v):
    with (N/name).open('xb') as f:
        f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
    return pin(N/name)
def parsed(v):
    if isinstance(v,list):
        for x in v:yield from parsed(x)
    elif isinstance(v,dict):
        if 'chunk_id' in v:yield v
        else:
            for x in v.values():yield from parsed(x)
    elif isinstance(v,str):
        try:x=json.loads(v)
        except ValueError:return
        yield from parsed(x)
targets={'714e04':(997,0,1),'9b596c':(998,0,1),'cbbd9b':(999,0,1),'8c25b6':(1000,0,1),'a6cb75':(1001,1,None)}
calls={};found={}
with P.open('rb') as f:
    head=f.readline();header=json.loads(head)
    meta=header['payload'];spawn=meta['source']['subagent']['thread_spawn']
    assert header['type']=='session_meta' and spawn['parent_thread_id']==ROOT_THREAD and spawn['agent_path']=='/root/w09_formal_profile_source_impl'
    while True:
        off=f.tell();raw=f.readline()
        if not raw:break
        evt=json.loads(raw);v=evt.get('payload',{})
        if evt.get('type')!='response_item' or not isinstance(v,dict):continue
        if v.get('type') in ('custom_tool_call','function_call'):
            calls[v.get('call_id')]=(evt,raw,off)
        elif v.get('type') in ('custom_tool_call_output','function_call_output'):
            matches=[]
            for result in parsed(v.get('output')):
                key=result.get('chunk_id')
                if key in targets:
                    ordinal,outer,py=targets[key]
                    assert result['exit_code']==outer and type(result['exit_code']) is int
                    if py is not None:assert 'ROOT_SOURCE_PYTHON_EXIT='+str(py) in result['output']
                    matches.append((ordinal,outer,py,result))
            output_text=json.dumps(v.get('output'),ensure_ascii=False)
            if ('apply_patch verification failed: invalid patch: multiple operations target' in output_text
                and 'cp370proposal-20261009-v2' in output_text and 'ROOT_BUILDER_CONTRACT.source.md' in output_text):
                matches.append((996,None,None,None))
            for ordinal,outer,py,result in matches:
                assert ordinal not in found and v.get('call_id') in calls
                found[ordinal]=(calls[v['call_id']],evt,raw,off,outer,py,result)
    observed_size=f.tell()
assert set(found)==set(range(996,1002)),('EXACT_SIX_ORIGINALS_REQUIRED',sorted(found))
origins=[]
for ordinal in range(996,1002):
    (call,call_raw,call_off),evt,out_raw,out_off,outer,py,result=found[ordinal]
    assert call['payload']['call_id']==evt['payload']['call_id']
    raws=(head,call_raw,out_raw)
    path=N/('original'+str(ordinal)+'.actual-child-host.raw.jsonl')
    with path.open('xb') as f:f.write(b''.join(raws));f.flush();os.fsync(f.fileno())
    raw_ref=pin(path)
    with P.open('rb') as f:
        for off,raw in zip((0,call_off,out_off),raws):f.seek(off);assert f.read(len(raw))==raw
    br=save('original'+str(ordinal)+'.actual-child-host.binding.root.json',dict(schema='researchos.child-host-original-tool-capture.v1',issued_by='codex:/root',root_thread_id=ROOT_THREAD,
        child_thread_id=meta['id'],actor_id=ACTOR,original_capture_ref=raw_ref,source_audit_path=str(P),source_prefix_size_observed=observed_size,
        source_line_offsets=[0,call_off,out_off],source_line_bytes=[len(x) for x in raws],original_line_sha256=[hashlib.sha256(x).hexdigest() for x in raws],original_call_id=call['payload']['call_id'],
        original_ordinal=ordinal,actual_outer_exit=outer,actual_python_exit=py,actual_native_exit=None,actual_dispatcher_exit=None,actual_model_exit=None,formal_acceptance=False,parent_acceptance=False))
    origins.append(dict(ordinal=ordinal,origin_ref=raw_ref,origin_selector='call_id='+call['payload']['call_id'],capture_binding_ref=br,
        actual_outer_exit=outer,actual_python_exit=py,actual_native_exit=None,actual_dispatcher_exit=None,actual_model_exit=None,
        capture_completeness='ACTUAL_CHILD_HOST_ORIGINAL_PAIR'))
summary=save('originals996-1001.actual-child-host.index.root.json',dict(schema='researchos.root-original-capture-index.v1',issued_by='codex:/root',created_utc=datetime.now(timezone.utc).isoformat(),
    root_thread_id=ROOT_THREAD,source_actor=ACTOR,originals=origins,next_original_failure_ordinal=1002,formal_acceptance=False,parent_acceptance=False,counter_reset=False))
print(json.dumps(dict(originals_index_ref=summary,originals=origins,next_original=1002,Native_rerun=False,Canonical_written=False,formal_delta=0),ensure_ascii=False),flush=True)
