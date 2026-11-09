"""Read only recent agent event content structure, print no message text."""
import hashlib,json
from pathlib import Path
p=Path('C:/Users/yqyyds/.codex/sessions/2026/10/06/rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
with p.open('rb') as f:
    size=f.seek(0,2);f.seek(max(0,size-4*1024*1024));lines=f.read().splitlines()[1:]
def shape(v,depth=0):
    if depth>4:return type(v).__name__
    if isinstance(v,str):return dict(type='str',length=len(v),sha256=hashlib.sha256(v.encode()).hexdigest())
    if isinstance(v,dict):return {k:shape(x,depth+1) for k,x in v.items()}
    if isinstance(v,list):return [shape(x,depth+1) for x in v[:3]]
    return dict(type=type(v).__name__)
out=[]
for line in lines:
    try:o=json.loads(line)
    except (ValueError,UnicodeError):continue
    v=o.get('payload')
    if o.get('type')=='response_item' and isinstance(v,dict) and v.get('type')=='agent_message':out.append(dict(timestamp=o['timestamp'],author=v.get('author'),id=v.get('id'),recipient=v.get('recipient'),content_shape=shape(v.get('content'))))
print(json.dumps(out[-12:],ensure_ascii=False,indent=2))
