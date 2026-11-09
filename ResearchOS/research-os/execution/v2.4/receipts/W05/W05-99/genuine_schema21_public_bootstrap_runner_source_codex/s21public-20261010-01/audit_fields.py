"""Read only the actual author audit header and bounded recent tool shapes."""
import json, sys
from pathlib import Path
p=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T03-12-51-01a11cee-bf59-7a01-be0e-9f799f9b1084.jsonl')
with p.open('rb') as f:
    first=f.readline()
    header=json.loads(first)
    f.seek(0,2); size=f.tell()
    f.seek(max(len(first),size-2*1024*1024))
    if f.tell()!=len(first): f.readline()
    found=[]
    while True:
        at=f.tell(); raw=f.readline()
        if not raw or at+len(raw)>size: break
        obj=json.loads(raw); value=obj.get('payload',{})
        if obj.get('type')=='response_item' and type(value) is dict and value.get('type') in ('custom_tool_call','function_call','custom_tool_call_output','function_call_output'):
            found.append({'offset':at,'bytes':len(raw),'top_type':obj.get('type'),'payload_type':value.get('type'),'keys':sorted(value),'name':value.get('name'),'call_id':value.get('call_id')})
print(json.dumps({'header_type':header.get('type'),'header_payload':{k:v for k,v in header.get('payload',{}).items() if k in ('id','source','cwd','parent_thread_id','agent_path','agent_role','originator')},'header_payload_keys':sorted(header.get('payload',{})),'recent_tool_shapes':found[-12:],'prefix_size':size},ensure_ascii=False,sort_keys=True))
print('ROOT_PYTHON_EXIT=0')
