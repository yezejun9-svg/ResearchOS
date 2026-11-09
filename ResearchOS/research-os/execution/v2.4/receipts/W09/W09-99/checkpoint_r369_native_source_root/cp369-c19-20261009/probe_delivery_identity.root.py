"""Print only audit identity keys for the latest delivered agent events."""
import json
from pathlib import Path
p=Path('C:/Users/yqyyds/.codex/sessions/2026/10/06/rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
with p.open('rb') as f:
    sz=f.seek(0,2);f.seek(max(0,sz-4*1024*1024));lines=f.read().splitlines()[1:]
out=[]
for line in lines:
    try:r=json.loads(line)
    except (ValueError,UnicodeError):continue
    v=r.get('payload');kind=r.get('type')
    if kind=='inter_agent_communication_metadata' or (kind=='response_item' and isinstance(v,dict) and v.get('type')=='agent_message'):
        safe={}
        def inspect(obj,prefix=''):
            if isinstance(obj,dict):
                for k,value in obj.items():
                    label=prefix+k
                    if k in ('content','text','message','body','message_text'):safe[label]='CONTENT_REDACTED'
                    elif isinstance(value,(dict,list)):safe[label]=dict(type=type(value).__name__,keys=sorted(value) if isinstance(value,dict) else []);inspect(value,label+'.')
                    elif k.endswith('_id') or k in ('type','sender','receiver','recipient','sender_task_name','task_name','channel','timestamp'):safe[label]=value
                    else:safe[label]=dict(type=type(value).__name__)
            elif isinstance(obj,list):
                for i,value in enumerate(obj[:2]):inspect(value,prefix+str(i)+'.')
        inspect(r);out.append(safe)
print(json.dumps(out[-8:],ensure_ascii=False,indent=2))
