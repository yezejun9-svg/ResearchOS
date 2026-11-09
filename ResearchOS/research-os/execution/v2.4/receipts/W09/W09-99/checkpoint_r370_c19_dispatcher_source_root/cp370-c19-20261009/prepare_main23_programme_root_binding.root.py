"""Bind the real non-author programme review before Root's actual readback."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os
N=Path(__file__).resolve().parent
R=Path(r'D:\作品集\ResearchOS\research-os');B=R/'execution/v2.4/receipts/W05/W05-99'
THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUDIT=Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
def pin(p):
    raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def exact(p,sha,size):
    ref=pin(p);assert (ref['sha256'],ref['bytes'])==(sha,size);return ref
def save(name,v):
    p=N/name
    with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
    return pin(p)
review=B/'fresh_main23_programme_actual_independent_review_codex/actual-main23-20261010-01'
refs=[exact(review/name,sha,size) for name,sha,size in [
 ('HDF.json','f24b32276c19aa9ca942b5c92f863cb8338037cb57f216b62d17d3789eaead80',1677),
 ('MF.json','74a536545d20c90498bd8b5cef7a638a1cb6d8a77f5f5f837240c5693f3c6dfe',14667),
 ('decision.json','66aeba1a1b197afa00f93c1ef797d9d66543822875f98410667ccdc0467f7fe9',4404),
 ('programme-qualification.json','b7794982048b9ba3286f82ab80f373863f7702a5624e7f5738682e0d4d64e308',12219)]]
hdf,mf,decision,qualification=[json.loads(Path(ref['path']).read_bytes()) for ref in refs]
for member in mf['members']:exact(Path(member['path']),member['sha256'],member['bytes'])
assert hdf['manifest_ref']==refs[1] and hdf['qualification_ref']==decision['qualification_ref']==refs[3]
assert decision['independent_non_author'] and decision['verdict']=='QUALIFIED_CURRENT_MAIN23_BUILD_PENDING_ROOT_BINDING'
peer='codex:/root/attach_fixture_source_review'
assert decision['review_actor']==peer and qualification['review_author']==peer
assert qualification['source_author']=='codex:/root/native_temp_independent_review' and qualification['independent_non_author']
program_ref=qualification['program_ref'];exact(Path(program_ref['path']),program_ref['sha256'],program_ref['bytes'])
assert program_ref==hdf['program_ref']==decision['program_ref']
for ref in qualification['source_refs']:exact(Path(ref['path']),ref['sha256'],ref['bytes'])
prefix='Message Type: FINAL_ANSWER\nTask name: /root\nSender: '+peer.removeprefix('codex:')+'\nPayload:\n'
found=[];previous=None
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
                    if isinstance(d,dict) and d.get('schema')=='researchos.current-main23-programme-review-delivery.v1' and d.get('qualification_ref')==refs[3]:
                        found.append((previous,(raw,off,e),d))
        previous=(raw,off,e)
assert len(found)==1,'ONE_TRUE_PROGRAMME_REVIEW_FINAL_REQUIRED'
(first,fp,fe),(last,lp,le),delivery=found[0]
assert fe['type']=='inter_agent_communication_metadata' and le['ordinal']==fe['ordinal']+1
assert le['timestamp']==fe['timestamp'] and le['metadata']['client_authored'] is False
assert delivery['review_actor']==peer and delivery['root_thread_id']==THREAD and delivery['verdict']==decision['verdict']
assert delivery['hdf_ref']==refs[0] and delivery['mf_ref']==refs[1] and delivery['decision_ref']==refs[2]
assert delivery['independent_non_author'] and not delivery['formal_acceptance'] and not delivery['parent_acceptance'] and not delivery['execution_grant']
lines=[header,first,last];offsets=[0,fp,lp]
with AUDIT.open('rb') as f:
    for off,line in zip(offsets,lines):f.seek(off);assert f.read(len(line))==line
raw_path=N/'main23.programme.peer.review.raw.jsonl'
with raw_path.open('xb') as f:f.write(b''.join(lines));f.flush();os.fsync(f.fileno())
binding=save('main23.programme.peer.review.binding.root.json',dict(
    schema='researchos.root-actual-peer-capture-binding.v2',issued_by='codex:/root',root_thread_id=THREAD,
    peer_actor=peer,original_capture_ref=pin(raw_path),source_audit_path=AUDIT.as_posix(),source_prefix_size_observed=size,
    source_line_offsets=offsets,source_line_bytes=[len(x) for x in lines],
    original_line_sha256=[hashlib.sha256(x).hexdigest() for x in lines],message_id=le['payload']['id'],received_at=le['timestamp']))
current=[pin(R/'execution/v2.4'/(name+'.json')) for name in ('checkpoint','path_ownership','step_state','commands')]
assert [json.loads(Path(x['path']).read_bytes()).get('revision') for x in current]==[373,177,None,39]
payload=save('main23.programme.root-binding.payload.json',dict(
    schema='researchos.root-current-main23-programme-binding-payload.v1',issued_by='codex:/root',root_thread_id=THREAD,
    review_author=peer,review_refs=refs,program_ref=program_ref,source_refs=qualification['source_refs'],
    independent_peer_delivery_binding_ref=binding,current_canonical_refs=current,
    created_utc=datetime.now(timezone.utc).isoformat(),formal_acceptance=False,parent_acceptance=False,execution_grant=False))
request=save('main23.programme.root-binding.observer-input.json',dict(
    operation='PROGRAMME_QUALIFICATION_BINDING',observed_refs=[payload,binding]+refs+[program_ref]+qualification['source_refs']+current,
    peer_actor=peer,payload_ref=payload))
print(json.dumps(dict(payload_ref=payload,observer_input_ref=request,peer_binding_ref=binding,review_refs=refs),ensure_ascii=False,indent=2))
