"""Capture only one actual nonformal delivery; no user message or credential scan/output."""
from datetime import datetime, timezone
import hashlib, json, os
from pathlib import Path
N=Path(__file__).resolve().parent
P=Path('C:/Users/yqyyds/.codex/sessions/2026/10/06/rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
with P.open('rb') as f:
    header_raw=f.readline();header=json.loads(header_raw)
    assert header['type']=='session_meta' and header['payload']['id']=='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
    size=f.seek(0,2);start=max(0,size-4*1024*1024);f.seek(start);raw=f.read()
def flatten(value):
    if isinstance(value,str):return value
    if isinstance(value,list):return ''.join(flatten(x) for x in value)
    if isinstance(value,dict):return flatten(value.get('text',''))
    return ''
prev=None;matches=[];offset=start
for i,line in enumerate(raw.splitlines(keepends=True)):
    line_offset=offset;offset+=len(line)
    if i==0 and start>0:continue
    try:record=json.loads(line)
    except (ValueError,UnicodeError):prev=None;continue
    v=record.get('payload')
    if record.get('type')=='response_item' and isinstance(v,dict) and v.get('type')=='agent_message' and v.get('recipient')=='/root' and 'CP369/OW173 Actual 行政独审 PASS' in flatten(v.get('content')):
        assert prev is not None
        before,before_line,before_offset=prev
        assert before['type']=='inter_agent_communication_metadata' and before['timestamp']==record['timestamp']
        assert type(before['ordinal']) is int and type(record['ordinal']) is int and record['ordinal']==before['ordinal']+1
        assert type(v['id']) is str and type(v['author']) is str
        matches.append((before_line,line,before_offset,line_offset,record))
    prev=(record,line,line_offset)
assert len(matches)==1, 'EXACT_ACTUAL_ADMIN_MESSAGE'
a,b,ao,bo,event=matches[0]
capture_path=N/'nonformal-registration-delivery.original.root.jsonl'
with capture_path.open('xb') as f:
    f.write(header_raw+a+b);f.flush();os.fsync(f.fileno())
def pin(p):
    data=p.read_bytes();return dict(path=str(p.resolve(strict=True)),sha256=hashlib.sha256(data).hexdigest(),bytes=len(data))
binding=dict(schema='researchos.root-actual-audit-delivery-protocol-sample.v1',issued_by='codex:/root',captured_utc=datetime.now(timezone.utc).isoformat(),original_capture_ref=pin(capture_path),source_audit_path=str(P),source_prefix_size_observed=size,source_line_offsets=[0,ao,bo],original_line_sha256=[hashlib.sha256(x).hexdigest() for x in (header_raw,a,b)],Root_thread_id=header['payload']['id'],message_id=event['payload']['id'],sender=event['payload']['author'],recipient=event['payload']['recipient'],received_at=event['timestamp'],review_decision_ref=dict(path='D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W09\\W09-99\\cp369_registration_actual_independent_review_codex\\review-1a12035\\actual-decision.json',sha256='44ba4d7c0cf8665ca7fad43e61e8758b7f21e257adc9141115b439c7c50b72cb',bytes=5102),protocol_observation_only=True,W09_parent_or_formal_delivery=False,formal_case_accepted_delta=0,canonical_capture_index_approval='NOT_YET_PRESENT')
out=N/'nonformal-registration-delivery.binding.root.json'
with out.open('xb') as f:
    f.write((json.dumps(binding,ensure_ascii=False,indent=2)+'\n').encode('utf-8'));f.flush();os.fsync(f.fileno())
print(json.dumps(dict(binding_ref=pin(out),original_capture_ref=binding['original_capture_ref'],Root_thread_id=binding['Root_thread_id'],sender=binding['sender'],recipient='/root',received_at=binding['received_at'],protocol_only=True,formal_delta=0),ensure_ascii=False),flush=True)
