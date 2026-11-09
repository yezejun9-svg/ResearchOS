"""Archive exact Root tool pair and probe only native-review delivery metadata."""
import hashlib,json,os
from pathlib import Path
N=Path(__file__).resolve().parent
P=Path('C:/Users/yqyyds/.codex/sessions/2026/10/06/rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
def pin(p):
    b=p.read_bytes();return dict(path=str(p.resolve()),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(name,value):
    with (N/name).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
    return pin(N/name)
calls={};matches=[];deliveries=[]
with P.open('rb') as f:
    for raw in f:
        r=json.loads(raw);v=r.get('payload',{})
        if r.get('type')!='response_item' or not isinstance(v,dict):continue
        if v.get('type')=='custom_tool_call':calls[v.get('call_id')]=v
        elif v.get('type')=='custom_tool_call_output':
            try:out=json.loads(v.get('output','{}'))
            except (ValueError,TypeError):continue
            text=out.get('text','') if isinstance(out,dict) else ''
            try: result=json.loads(text)
            except (ValueError,TypeError):continue
            if isinstance(result,dict) and result.get('chunk_id')=='468be1':
                matches.append(dict(original_call=calls.get(v.get('call_id')),original_output=v,outer_result=result))
        elif v.get('type')=='agent_message' and v.get('author')=='/root/native_temp_independent_review' and v.get('recipient')=='/root':
            content=v.get('content',[])
            plain=isinstance(content,list) and bool(content) and all(isinstance(x,dict) and set(x)=={'type','text'} and x['type']=='input_text' for x in content)
            deliveries.append(dict(id=v.get('id'),received_at=r.get('timestamp'),plain=plain,text_sha256=hashlib.sha256(''.join(x['text'] for x in content).encode()).hexdigest() if plain else None))
assert len(matches)==1 and matches[0]['original_call'] is not None
ref=save('failure981.original-tool-io.root.json',dict(schema='researchos.root-original-tool-failure.v1',ordinal=981,original_tool_io=matches[0],actual_outer_exit=0,observed_rg_child_exit=2,actual_python_exit=None,actual_native_exit=None,actual_model_exit=None,diagnostic='Root readonly rg used absent execution/v2.4/dispatch.py; actual dispatcher discovered as execution/command_dispatcher/dispatch.py. Final Get-Content succeeded, outer0 retained. No retry/reset.'))
print(json.dumps(dict(failure981_origin_ref=ref,native_review_delivery_metadata=deliveries[-8:]),ensure_ascii=False),flush=True)
