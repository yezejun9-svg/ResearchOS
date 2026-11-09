"""Use observed list-of-text output protocol; preserve original observations once."""
from datetime import datetime,timezone
import hashlib,json,os
from pathlib import Path
N=Path(__file__).resolve().parent
P=Path('C:/Users/yqyyds/.codex/sessions/2026/10/06/rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
def pin(p):
    b=p.read_bytes();return dict(path=str(p.resolve()),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(name,value):
    with (N/name).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
    return pin(N/name)
def parsed_outputs(value):
    if isinstance(value,list):
        for x in value:yield from parsed_outputs(x)
    elif isinstance(value,dict) and isinstance(value.get('text'),str):
        try:yield json.loads(value['text'])
        except ValueError:pass
    elif isinstance(value,str):
        try:yield json.loads(value)
        except ValueError:pass
calls={};originals={};delivery=[];prev=None
with P.open('rb') as f:
    header_raw=f.readline();header=json.loads(header_raw)
    assert header['type']=='session_meta' and header['payload']['id']=='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
    while True:
        offset=f.tell();line=f.readline()
        if not line:break
        r=json.loads(line);v=r.get('payload',{})
        if r.get('type')=='response_item' and isinstance(v,dict):
            if v.get('type') in ('custom_tool_call','function_call'):calls[v.get('call_id')]=v
            elif v.get('type') in ('custom_tool_call_output','function_call_output'):
                for result in parsed_outputs(v.get('output')):
                    if isinstance(result,dict) and result.get('chunk_id') in ('468be1','ddd584','cf453b'):
                        key=result['chunk_id'];assert key not in originals
                        originals[key]=dict(original_call=calls.get(v.get('call_id')),original_output=v,outer_result=result)
            elif v.get('type')=='agent_message' and v.get('author')=='/root/native_temp_independent_review' and v.get('recipient')=='/root':
                blocks=v.get('content',[])
                plain=isinstance(blocks,list) and bool(blocks) and all(isinstance(x,dict) and set(x)=={'type','text'} and x['type']=='input_text' for x in blocks)
                text=''.join(x['text'] for x in blocks) if plain else ''
                if text.startswith('Main C19 Native') and '22,461' in text and 'two-consumer-mode-interface.json' in text:
                    assert prev is not None and prev[0]['type']=='inter_agent_communication_metadata' and prev[0]['timestamp']==r['timestamp'] and type(r['ordinal']) is int and r['ordinal']==prev[0]['ordinal']+1
                    delivery.append((prev[1],line,prev[2],offset,r))
        prev=(r,line,offset)
    observed_size=f.tell()
assert set(originals)=={'468be1','ddd584','cf453b'} and all(v['original_call'] is not None for v in originals.values())
refs=[]
for chunk,ordinal,outer,py in [('468be1',981,0,None),('ddd584',982,1,1)]:
    refs.append(save('failure'+str(ordinal)+'.original-tool-io.root.json',dict(schema='researchos.root-original-tool-failure.v1',ordinal=ordinal,original_tool_io=originals[chunk],actual_outer_exit=outer,actual_python_exit=py,actual_native_exit=None,actual_model_exit=None,observed_rg_child_exit=2 if ordinal==981 else None,counter_reset=False,diagnostic='Incorrect readonly dispatcher path; final child success retains outer0.' if ordinal==981 else 'Root original-output parser expected object/string; actual list protocol was subsequently observed. Failed before archive write or Native.')))
resume_io=save('resume-live981.original-tool-io.root.json',originals['cf453b'])
assert len(delivery)==1,'EXACT_PLAINTEXT_NATIVE_FINAL'
a,b,ao,bo,event=delivery[0]
raw_path=N/'Main-C19-mode-review-delivery.original.root.jsonl'
with raw_path.open('xb') as f:f.write(header_raw+a+b);f.flush();os.fsync(f.fileno())
binding=save('Main-C19-mode-review-delivery.binding.root.json',dict(schema='researchos.root-actual-mode-review-delivery.v1',issued_by='codex:/root',captured_at=datetime.now(timezone.utc).isoformat(),original_capture_ref=pin(raw_path),source_audit_path=str(P),source_prefix_size_observed=observed_size,source_line_offsets=[0,ao,bo],original_line_sha256=[hashlib.sha256(x).hexdigest() for x in (header_raw,a,b)],root_thread_id=header['payload']['id'],message_id=event['payload']['id'],sender=event['payload']['author'],recipient='/root',received_at=event['timestamp'],review_handoff_ref=dict(path=str(N.parent.parent/'main_c19_native_actual_independent_review_codex/review-1a12035-v2/HDF.json'),sha256='49dd4ae646af95ecc38004f9650245e7e6ed9e04aa9fe8711b5fd945dd840270',bytes=6428),formal_authority=False,parent_acceptance=False))
print(json.dumps(dict(failure_origin_refs=refs,resume_original_io_ref=resume_io,mode_review_delivery_binding_ref=binding,mode_review_original_capture_ref=pin(raw_path),native_rerun=False,formal_delta=0),ensure_ascii=False),flush=True)
