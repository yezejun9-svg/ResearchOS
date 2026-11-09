"""Bind the real completed non-author delivery; prepare the Root observation."""
from pathlib import Path
import hashlib,json,os
N=Path(__file__).resolve().parent
R=Path(r'D:\作品集\ResearchOS\research-os')
B=R/'execution/v2.4/receipts/W05/W05-99'
THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUDIT=Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
def pin(p):
    raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,v):
    p=N/name
    with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
    return pin(p)
review=B/'fresh_main23_root_caller_registration_independent_source_review_codex/review-20261010-04'
refs=[pin(review/x) for x in ('HDF.json','MF.json','decision.json')]
decision=json.loads(Path(refs[2]['path']).read_bytes())
assert decision['verdict']=='SOURCE_ACCEPTED_FOR_ROOT_REGISTRATION'
peer='codex:/root/full_w09_source_review'
assert decision['review_author']==peer and decision['independent_non_author'] is True
assert decision['formal_acceptance'] is False and decision['execution_grant'] is False
prefix='Message Type: FINAL_ANSWER\nTask name: /root\nSender: '+peer.removeprefix('codex:')+'\nPayload:\n'
found=[];previous=None
def refset(values):
    return {(str(Path(x['path']).resolve()).casefold(),x['sha256'],x['bytes']) for x in values}
with AUDIT.open('rb') as f:
    header=f.readline();f.seek(0,2);size=f.tell();f.seek(max(len(header),size-16*1024*1024))
    if f.tell()>len(header):f.readline()
    while True:
        off=f.tell();raw=f.readline()
        if not raw:break
        e=json.loads(raw);p=e.get('payload',{})
        if e.get('type')=='response_item' and isinstance(p,dict) and p.get('type')=='agent_message' and p.get('author')==peer.removeprefix('codex:') and p.get('recipient')=='/root':
            c=p.get('content',[])
            if isinstance(c,list) and len(c)==1 and c[0].get('type')=='input_text':
                text=c[0].get('text','')
                if text.startswith(prefix):
                    try:d=json.loads(text[len(prefix):])
                    except ValueError:d=None
                    if isinstance(d,dict) and d.get('schema')=='researchos.main23-peer-review-delivery.v2' and d.get('operation')=='SOURCE_REVIEW_WITNESS' and refset(d.get('review_refs',[]))==refset(refs):
                        found.append((previous,(raw,off,e),d))
        previous=(raw,off,e)
assert len(found)==1,'ONE_ACTUAL_M4_NONAUTHOR_FINAL_REQUIRED'
(first,fp,fe),(last,lp,le),delivery=found[0]
assert fe['type']=='inter_agent_communication_metadata' and le['ordinal']==fe['ordinal']+1
assert le['timestamp']==fe['timestamp'] and le['metadata']['client_authored'] is False
assert delivery['review_author']==peer and delivery['root_thread_id']==THREAD and delivery['verdict']=='ACCEPTED_SOURCE_ONLY'
assert delivery['formal_acceptance'] is False and delivery['execution_grant'] is False
lines=[header,first,last];offsets=[0,fp,lp]
with AUDIT.open('rb') as f:
    for off,line in zip(offsets,lines):f.seek(off);assert f.read(len(line))==line
p=N/'main23.v4.peer.source-review.raw.jsonl'
with p.open('xb') as f:f.write(b''.join(lines));f.flush();os.fsync(f.fileno())
binding=save('main23.v4.peer.source-review.binding.root.json',dict(
    schema='researchos.root-actual-peer-capture-binding.v2',issued_by='codex:/root',root_thread_id=THREAD,
    peer_actor=peer,original_capture_ref=pin(p),source_audit_path=AUDIT.as_posix(),
    source_prefix_size_observed=size,source_line_offsets=offsets,source_line_bytes=[len(x) for x in lines],
    original_line_sha256=[hashlib.sha256(x).hexdigest() for x in lines],message_id=le['payload']['id'],received_at=le['timestamp']))
request=save('main23.v4.source-review.observer-input.root.json',dict(
    operation='SOURCE_REVIEW_WITNESS',observed_refs=refs,peer_actor=peer,peer_delivery_binding_ref=binding))
print(json.dumps(dict(observer_input_ref=request,peer_binding_ref=binding,review_refs=refs),ensure_ascii=False,indent=2))
