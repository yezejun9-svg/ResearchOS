"""Copy only the actual Main23 v4 Source author's completed delivery rows."""
from pathlib import Path
import hashlib,json,os
N=Path(__file__).resolve().parent
THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUDIT=Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
actor='/root/backup_regression_resources'
prefix='Message Type: FINAL_ANSWER\nTask name: /root\nSender: '+actor+'\nPayload:\n'
pins=['348034a2f2f23342f6a309ed14ffe64183a3bbb031ed79d6c8ed5facf34c0fd3',
      'dd65dabdff33ccc10b229222992cf7db5702837c60cd7ed565769248c09e88c1']
found=[];previous=None
with AUDIT.open('rb') as f:
    header=f.readline();f.seek(0,2);size=f.tell();f.seek(max(len(header),size-16*1024*1024))
    if f.tell()>len(header):f.readline()
    while True:
        off=f.tell();raw=f.readline()
        if not raw:break
        e=json.loads(raw);p=e.get('payload',{})
        if e.get('type')=='response_item' and isinstance(p,dict) and p.get('type')=='agent_message' and p.get('author')==actor and p.get('recipient')=='/root':
            c=p.get('content',[])
            if isinstance(c,list) and len(c)==1 and c[0].get('type')=='input_text':
                body=c[0].get('text','')
                if body.startswith(prefix) and all(x in body for x in pins):found.append((previous,(raw,off,e)))
        previous=(raw,off,e)
assert len(found)==1,'ONE_TRUE_SOURCE_AUTHOR_FINAL_REQUIRED'
(first,fp,fe),(last,lp,le)=found[0]
assert fe['type']=='inter_agent_communication_metadata' and le['ordinal']==fe['ordinal']+1
assert le['timestamp']==fe['timestamp'] and le['metadata']['client_authored'] is False
lines=[header,first,last];offsets=[0,fp,lp]
with AUDIT.open('rb') as f:
    for off,line in zip(offsets,lines):f.seek(off);assert f.read(len(line))==line
def pin(p):
    raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,v):
    p=N/name
    with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
    return pin(p)
raw_path=N/'main23.v4.peer.source-author.raw.jsonl'
with raw_path.open('xb') as f:f.write(b''.join(lines));f.flush();os.fsync(f.fileno())
raw_ref=pin(raw_path)
binding=save('main23.v4.peer.source-author.binding.root.json',dict(
    schema='researchos.root-actual-peer-capture-binding.v2',issued_by='codex:/root',root_thread_id=THREAD,
    peer_actor='codex:'+actor,original_capture_ref=raw_ref,source_audit_path=AUDIT.as_posix(),
    source_prefix_size_observed=size,source_line_offsets=offsets,source_line_bytes=[len(x) for x in lines],
    original_line_sha256=[hashlib.sha256(x).hexdigest() for x in lines],
    message_id=le['payload']['id'],received_at=le['timestamp']))
print(json.dumps(dict(raw_ref=raw_ref,binding_ref=binding,actual_ordinal=le['ordinal'],source_author='codex:'+actor),ensure_ascii=False,indent=2))
