"""Copy and verify finite actual Root or peer records for W09 adoption."""
from pathlib import Path
import hashlib, json, os, sys, types
N=Path(__file__).resolve().parent
R=Path(r'D:\作品集\ResearchOS\research-os')
W=R/'execution/v2.4/receipts/W09/W09-99'
THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUDIT=Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')

def pin(p):
    raw=Path(p).read_bytes();return dict(path=str(Path(p)),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))

def documents(value):
    if isinstance(value,dict):
        yield value
        for x in value.values():yield from documents(x)
    elif isinstance(value,list):
        for x in value:yield from documents(x)
    elif isinstance(value,str):
        try:yield from documents(json.loads(value))
        except ValueError:pass

kind,stem,actor,digest=sys.argv[1:5]
assert kind in ('peer','root') and stem.replace('-','').isalnum() and len(digest)==64
chunk=sys.argv[5] if kind=='root' else None
found=[];calls={};previous=None
with AUDIT.open('rb') as f:
    header=f.readline();assert json.loads(header)['payload']['id']==THREAD
    f.seek(0,2);size=f.tell();start=max(len(header),size-32*1024*1024);f.seek(start)
    if start>len(header):f.readline()
    while True:
        off=f.tell();raw=f.readline()
        if not raw:break
        e=json.loads(raw);p=e.get('payload',{});pt=p.get('type') if isinstance(p,dict) else None
        if kind=='peer' and e.get('type')=='response_item' and pt=='agent_message' and p.get('author')==actor.removeprefix('codex:') and p.get('recipient')=='/root':
            c=p.get('content',[]);text=c[0].get('text','') if len(c)==1 else ''
            if digest in text and text.startswith('Message Type: FINAL_ANSWER\nTask name: /root\nSender: '+actor.removeprefix('codex:')+'\nPayload:\n'):
                found.append((previous,(raw,off,e)))
        elif kind=='root' and e.get('type')=='response_item':
            if pt in ('function_call','custom_tool_call'):calls[p.get('call_id')]=(raw,off,e)
            elif pt in ('function_call_output','custom_tool_call_output') and p.get('call_id') in calls:
                if any(x.get('chunk_id')==chunk for x in documents(p.get('output'))):
                    found.append((calls[p['call_id']],(raw,off,e)))
        previous=(raw,off,e)
assert len(found)==1,'EXACT_ONE_ACTUAL_RECORD_REQUIRED'
(first,fp,fe),(last,lp,le)=found[0];lines=[header,first,last]
with AUDIT.open('rb') as f:
    for offset,line in zip((0,fp,lp),lines):f.seek(offset);assert f.readline()==line
raw_path=N/('w09.'+stem+'.original.raw.jsonl')
with raw_path.open('xb') as f:f.write(b''.join(lines));f.flush();os.fsync(f.fileno())
audit_path=N/('w09.'+stem+'.actual-audit.root.json')
audit=dict(schema='researchos.w09-native-producer.actual-audit.v1',actor_id=actor,Root_thread_id=THREAD,
    source_audit_path=str(AUDIT),source_line_offsets=[0,fp,lp],
    original_line_sha256=[hashlib.sha256(x).hexdigest() for x in lines],source_prefix_size_observed=size,
    original_capture_ref=pin(raw_path),binding_sha256=digest)
with audit_path.open('xb') as f:
    f.write((json.dumps(audit,ensure_ascii=False,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
runtime_path=W/'full_w09_main_native_producer_source_codex/fullw09-20261010-03/full_w09_runtime.source.py'
assert pin(runtime_path)['sha256']=='1709bc96848fb52fe4ddde8591fe063576515aaabdc63d35630b1023a82ccc08'
m=types.ModuleType('w09_root_adopter_audit_check');m.__file__=str(runtime_path);sys.modules[m.__name__]=m
exec(compile(runtime_path.read_bytes(),str(runtime_path),'exec'),m.__dict__)
m.actual_audit(pin(audit_path),actor,digest)
print(json.dumps(dict(audit_ref=pin(audit_path),actor_id=actor,binding_sha256=digest,
    metadata_timestamp=fe['timestamp'],result_timestamp=le['timestamp'],actual_original_validated=True,
    Main_written=False,Canon_written=False,formal_acceptance=False),ensure_ascii=False,indent=2))
