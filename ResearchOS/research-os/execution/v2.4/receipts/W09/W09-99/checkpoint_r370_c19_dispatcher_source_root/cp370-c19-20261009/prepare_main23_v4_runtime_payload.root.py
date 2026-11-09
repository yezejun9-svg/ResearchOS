"""Root binds a real runtime-review peer delivery before creating its qualification payload."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,os
N=Path(__file__).resolve().parent
R=Path(r'D:\作品集\ResearchOS\research-os');B=R/'execution/v2.4/receipts/W05/W05-99'
THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUDIT=Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
def pin(p):
    raw=Path(p).read_bytes();return dict(path=str(Path(p)),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,value):
    p=N/name
    with p.open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'));f.flush();os.fsync(f.fileno())
    return pin(p)
def check(ref):
    a=pin(ref['path']);assert (a['sha256'],a['bytes'])==(ref['sha256'],ref['bytes'])
review=B/'fresh_main23_runtime_resource_independent_review_codex/runtime-20261010-04-isolated'
refs=[pin(review/x) for x in ('HDF.json','MF.json','decision.json')]
assert [(x['sha256'],x['bytes']) for x in refs]==[
('b31820bcd2fd3cc9991156b9e580db867347d3aa3801bc3c37f964d208b062eb',4129),
('e723a4c3e1acf410c8870872a7b057148d1eb2602391a5ba56ab13383b0de3dc',58352),
('80a9e9e4031f65c1cb5a75d2c8eb7f5d9eea6aa9d3640ebf23feb13dc93b01d2',35939)]
peer='codex:/root/attach_fixture_source_review'
prefix='Message Type: FINAL_ANSWER\nTask name: /root\nSender: /root/attach_fixture_source_review\nPayload:\n'
found=[];previous=None
with AUDIT.open('rb') as f:
    header=f.readline();f.seek(0,2);size=f.tell();start=max(len(header),size-16*1024*1024);f.seek(start)
    if start>len(header):f.readline()
    while True:
        pos=f.tell();raw=f.readline()
        if not raw:break
        e=json.loads(raw);p=e.get('payload',{})
        if e.get('type')=='response_item' and isinstance(p,dict) and p.get('type')=='agent_message' and p.get('author')==peer.removeprefix('codex:') and p.get('recipient')=='/root':
            c=p.get('content',[])
            if isinstance(c,list) and len(c)==1 and c[0].get('type')=='input_text':
                text=c[0].get('text','')
                if text.startswith(prefix):
                    try:d=json.loads(text[len(prefix):])
                    except ValueError:d=None
                    if isinstance(d,dict) and d.get('schema')=='researchos.main23-peer-review-delivery.v2' and d.get('operation')=='RUNTIME_QUALIFICATION_ISSUANCE' and all(any(x['sha256']==r['sha256'] and x['bytes']==r['bytes'] for x in d['review_refs']) for r in refs):
                        found.append((previous,(raw,pos,e),d))
        previous=(raw,pos,e)
assert len(found)==1,'ONE_ACTUAL_M4_RUNTIME_FINAL_REQUIRED'
(first,fp,fe),(last,lp,le),delivery=found[0]
assert fe['type']=='inter_agent_communication_metadata' and type(fe['payload']['trigger_turn']) is bool
assert le['ordinal']==fe['ordinal']+1 and le['timestamp']==fe['timestamp'] and le['metadata']['client_authored'] is False
assert delivery['root_thread_id']==THREAD and delivery['review_author']==peer and delivery['verdict']=='ACCEPTED_SOURCE_ONLY'
assert delivery['formal_acceptance'] is False and delivery['execution_grant'] is False
lines=[header,first,last];offsets=[0,fp,lp]
with AUDIT.open('rb') as f:
    for off,line in zip(offsets,lines):f.seek(off);assert f.readline()==line
with (N/'main23.v4.peer.runtime.raw.jsonl').open('xb') as f:f.write(b''.join(lines));f.flush();os.fsync(f.fileno())
binding=save('main23.v4.peer.runtime.binding.root.json',dict(
    schema='researchos.root-actual-peer-capture-binding.v2',issued_by='codex:/root',root_thread_id=THREAD,
    peer_actor=peer,original_capture_ref=pin(N/'main23.v4.peer.runtime.raw.jsonl'),
    source_audit_path=AUDIT.as_posix(),source_prefix_size_observed=size,source_line_offsets=offsets,
    source_line_bytes=[len(x) for x in lines],original_line_sha256=[hashlib.sha256(x).hexdigest() for x in lines],
    message_id=le['payload']['id'],received_at=le['timestamp']))
d=json.loads(Path(refs[2]['path']).read_bytes())
scope=json.loads(Path(d['qualification_scope_ref']['path']).read_bytes())
for key in ('source_hdf_ref','source_mf_ref','caller_ref','builder_contract_ref','qualification_scope_ref','python_ref','go_ref'):
    check(d[key])
for ref in d['resource_refs']:check(ref)
assert d['verdict']=='RUNTIME_CLOSURE_ACCEPTED' and d['independent_non_author'] is True
now=datetime.now(timezone.utc)
assert datetime.fromisoformat(le['timestamp'].replace('Z','+00:00'))<=now
payload=dict(schema='researchos.root-main23-runtime-qualification-payload.v2',issued_by='codex:/root',
    root_thread_id=THREAD,status='QUALIFIED_FOR_MAIN23_BUILD',independent_non_author=True,formal_programme_qualification=False,
    review_author=peer,resource_refs=d['resource_refs'],review_hdf_ref=refs[0],review_mf_ref=refs[1],review_decision_ref=refs[2],
    review_hostpair_binding_ref=binding,payload_created_utc=now.isoformat())
for key in ('source_hdf_ref','source_mf_ref','caller_ref','builder_contract_ref','qualification_scope_ref','python_ref','go_ref'):
    payload[key]=d[key]
payload_ref=save('main23.v4.runtime-qualification.payload.actual.root.json',payload)
observed=[payload_ref,d['qualification_scope_ref'],*refs,binding]
request=save('main23.v4.runtime-qualification.observer-input.root.json',dict(
    operation='RUNTIME_QUALIFICATION_ISSUANCE',observed_refs=observed,peer_actor=None))
print(json.dumps(dict(payload_ref=payload_ref,peer_binding_ref=binding,observer_input_ref=request),ensure_ascii=False,indent=2))

