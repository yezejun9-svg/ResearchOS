"""Root preserves exact original Main23 scope call and actual plaintext peer records."""
from pathlib import Path
import hashlib, json, os
N=Path(__file__).resolve().parent
THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
ROOT='codex:/root'
AUDIT=Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
def pin(path):
    path=Path(path).resolve(strict=True); raw=path.read_bytes()
    return dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,value):
    with (N/name).open('xb') as f:
        f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'));f.flush();os.fsync(f.fileno())
    return pin(N/name)
def outputs(value):
    if isinstance(value,list):
        for x in value: yield from outputs(x)
    elif isinstance(value,dict):
        if 'chunk_id' in value: yield value
        else:
            for x in value.values():yield from outputs(x)
    elif isinstance(value,str):
        try:yield from outputs(json.loads(value))
        except ValueError:return
def seal(name,header,first,last,size,*,peer=False):
    lines=[x[0] for x in (header,first,last)]
    offsets=[x[1] for x in (header,first,last)]
    rows=[json.loads(x) for x in lines]
    assert rows[0]['type']=='session_meta' and rows[0]['ordinal']==0 and rows[0]['payload']['id']==THREAD
    with AUDIT.open('rb') as f:
        for raw,offset in zip(lines,offsets):
            f.seek(offset);assert f.readline()==raw
    with (N/(name+'.raw.jsonl')).open('xb') as f:
        f.write(b''.join(lines));f.flush();os.fsync(f.fileno())
    raw_ref=pin(N/(name+'.raw.jsonl'))
    binding=dict(schema='researchos.root-actual-peer-capture-binding.v2' if peer else 'researchos.root-actual-tool-capture-binding.v1',
        issued_by=ROOT,root_thread_id=THREAD,original_capture_ref=raw_ref,source_audit_path=AUDIT.as_posix(),
        source_prefix_size_observed=size,source_line_offsets=offsets,source_line_bytes=[len(x) for x in lines],
        original_line_sha256=[hashlib.sha256(x).hexdigest() for x in lines],formal_authority=False,parent_acceptance=False)
    if peer:
        payload=rows[2]['payload']
        assert rows[1]['type']=='inter_agent_communication_metadata' and type(rows[1]['payload']['trigger_turn']) is bool
        assert rows[2]['ordinal']==rows[1]['ordinal']+1 and rows[1]['timestamp']==rows[2]['timestamp']
        assert payload['type']=='agent_message' and payload['author']=='/root/attach_fixture_source_review' and payload['recipient']=='/root'
        assert rows[2]['metadata']['client_authored'] is False
        binding.update(peer_actor='codex:/root/attach_fixture_source_review',message_id=payload['id'],received_at=rows[2]['timestamp'])
    else:
        assert rows[1]['payload']['call_id']==rows[2]['payload']['call_id']
        binding.update(original_call_id=rows[1]['payload']['call_id'],tool_call_timestamp=rows[1]['timestamp'],tool_result_timestamp=rows[2]['timestamp'])
    binding_ref=save(name+'.binding.root.json',binding)
    return dict(raw_ref=raw_ref,binding_ref=binding_ref)
with AUDIT.open('rb') as f:
    header=(f.readline(),0)
    f.seek(0,2);size=f.tell();start=max(len(header[0]),size-64*1024*1024);f.seek(start)
    if start>len(header[0]):f.readline()
    calls={};tool=[];peers={};previous=None
    while True:
        offset=f.tell();raw=f.readline()
        if not raw:break
        e=json.loads(raw);p=e.get('payload',{})
        if e.get('type')=='response_item' and isinstance(p,dict):
            kind=p.get('type');cid=p.get('call_id')
            if kind in ('custom_tool_call','function_call'):calls[cid]=(raw,offset)
            elif kind in ('custom_tool_call_output','function_call_output') and cid in calls:
                if any(x.get('chunk_id')=='057548' for x in outputs(p.get('output'))):tool.append((calls[cid],(raw,offset)))
            elif kind=='agent_message' and p.get('author')=='/root/attach_fixture_source_review' and p.get('recipient')=='/root':
                content=p.get('content')
                if isinstance(content,list) and len(content)==1 and content[0].get('type')=='input_text':
                    text=content[0].get('text','')
                    prefix='Message Type: FINAL_ANSWER\nTask name: /root\nSender: /root/attach_fixture_source_review\nPayload:\n'
                    if text.startswith(prefix):text=text[len(prefix):]
                    try:d=json.loads(text)
                    except (ValueError,TypeError):d=None
                    if isinstance(d,dict) and d.get('schema')=='researchos.main23-peer-review-delivery.v2':
                        op=d.get('operation')
                        assert previous is not None and previous[2]['type']=='inter_agent_communication_metadata'
                        assert op not in peers
                        peers[op]=(previous[:2],(raw,offset),d)
        previous=(raw,offset,e)
assert len(tool)==1 and set(peers)=={'SOURCE_REVIEW_WITNESS','RUNTIME_QUALIFICATION_ISSUANCE'}
result=dict(scope_call=seal('main23.v3.runtime-scope.original057548',header,*tool[0],size))
for op,(first,last,delivery) in peers.items():
    for ref in delivery['review_refs']:
        actual=pin(ref['path']);assert actual['sha256']==ref['sha256'] and actual['bytes']==ref['bytes']
    result[op]=seal('main23.v3.peer.'+op.lower(),header,first,last,size,peer=True)
index=save('main23.v3.original-provenance.index.root.json',dict(schema='researchos.root-main23-original-provenance.v1',
    issued_by=ROOT,root_thread_id=THREAD,records=result,formal_acceptance=False,execution_grant=False))
print(json.dumps(dict(index_ref=index,records=result),ensure_ascii=False,indent=2))

