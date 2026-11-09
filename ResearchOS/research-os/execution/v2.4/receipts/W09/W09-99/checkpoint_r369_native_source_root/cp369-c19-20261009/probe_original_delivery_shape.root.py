"""Inspect only metadata of recent audit records; never emit user text or credentials."""
import json
from pathlib import Path
p=Path('C:/Users/yqyyds/.codex/sessions/2026/10/06/rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
with p.open('rb') as f:
    size=f.seek(0,2);f.seek(max(0,size-8*1024*1024));tail=f.read()
lines=tail.splitlines();summary={};matched=[]
for line in lines[1:]:
    try:o=json.loads(line)
    except (ValueError,UnicodeError):continue
    payload=o.get('payload');key=(str(o.get('type')),str(payload.get('type')) if isinstance(payload,dict) else '')
    summary[key]=summary.get(key,0)+1
    if isinstance(payload,dict) and (key[0]=='event_msg' or any(k in payload for k in ('sender','sender_id','agent_id','thread_id','message_id'))):
        matched.append(dict(record_type=key[0],payload_type=key[1],payload_keys=sorted(payload),timestamp=o.get('timestamp'),role=payload.get('role'),channel=payload.get('channel')))
print(json.dumps(dict(size_bytes=size,tail_bytes=len(tail),types=[dict(record_type=k[0],payload_type=k[1],count=v) for k,v in summary.items()],recent_metadata=matched[-24:]),ensure_ascii=False))
