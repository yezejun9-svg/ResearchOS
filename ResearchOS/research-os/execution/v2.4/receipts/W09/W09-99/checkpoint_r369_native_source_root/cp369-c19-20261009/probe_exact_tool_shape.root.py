import json
from pathlib import Path
P=Path('C:/Users/yqyyds/.codex/sessions/2026/10/06/rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
out=[]
with P.open('rb') as f:
    for line in f:
        r=json.loads(line);v=r.get('payload',{})
        if r.get('type')=='response_item' and isinstance(v,dict) and v.get('type') in ('custom_tool_call_output','function_call_output') and '468be1' in str(v.get('output','')):
            value=v.get('output'); shape=dict(kind=type(value).__name__)
            if isinstance(value,str):
                try: j=json.loads(value)
                except ValueError:j=None
                shape['parsed_type']=type(j).__name__;shape['parsed_keys']=list(j) if isinstance(j,dict) else None
                if isinstance(j,dict):shape['text_type']=type(j.get('text')).__name__
            out.append(dict(record_type=r['type'],payload_type=v['type'],call_id=v.get('call_id'),keys=list(v),output_shape=shape))
print(json.dumps(out,ensure_ascii=False),flush=True)
