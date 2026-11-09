"""Retain the genuine independent programme delivery and prepare Root readback."""
from pathlib import Path
from datetime import datetime, timezone
import ast, hashlib, json, os, sys, types
N=Path(__file__).resolve().parent; R=Path(r'D:\作品集\ResearchOS\research-os')
B=R/'execution/v2.4/receipts/W05/W05-99'; THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUDIT=Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
t=ast.parse((N/'seal_continuation.live1013.root.py').read_bytes())
exec(compile(ast.Module(body=[x for x in t.body if isinstance(x,ast.FunctionDef) and x.name in {'pin','save','exact'}],type_ignores=[]),'Root_functions_only','exec'),globals())
P=B/'schema21_programme_actual_independent_review_codex/actual-old21-20261010-01'
refs=[exact(P/name,sha,size) for name,sha,size in (
    ('HDF.json','ac73253e94fb0bf8b4980021946d2fdf6d5933296fcb2a8ee9254c425fe4f210',2044),
    ('MF.json','76222867cf25db836e2babab071012f8786af34822d81ad5055147533ff43331',21190),
    ('decision.json','efc83f5b76761f158e7254bf4d3935b407bf9d7a7b4479a70b1963d47d8d14c3',3422),
    ('programme-qualification.json','a390f4705ceb1e554bca8ce28f0cb8670041246523b837e13286941414e4cd5e',42640))]
seal=exact(P/'complete-hostpair-seal.json','4b1b3021c595b71843fbff9357a87736a68b38af512339f638d679260d67a6c5',2588)
hdf,mf,decision,q=[json.loads(Path(x['path']).read_bytes()) for x in refs]
peer='codex:/root/attach_fixture_source_review'
assert hdf['review_author']==decision['review_author']==q['review_author']==peer
assert peer not in (q['source_author'],q['caller_source_author'],q['build_executor'])
assert q['independent_non_author'] and q['status']==decision['verdict']=='QUALIFIED_OLD21_BUILD_PENDING_ROOT_BINDING'
assert q['Root_binding_required'] and q['Root_binding_ref'] is None
assert q['actual_Go_primary_exits']==[0]*9 and q['all_owned_jobs_idle_and_closed']
assert q['original_API_process_stdout_truncated'] and not q['original_process_stdout_complete'] and not q['original_stdout_reconstructed']
assert not any(q[k] for k in ('formal_acceptance','parent_acceptance','execution_grant','public_bootstrap_executed','backup_restore_executed','review_Go_runs','review_Native_runs','review_SQL_runs','review_model_requests','Canon_written'))
assert len(mf['members'])==66
prefix='Message Type: FINAL_ANSWER\nTask name: /root\nSender: /root/attach_fixture_source_review\nPayload:\n'
found=[];previous=None
with AUDIT.open('rb') as f:
    header=f.readline();assert json.loads(header)['payload']['id']==THREAD
    f.seek(0,2);size=f.tell();start=max(len(header),size-32*1024*1024);f.seek(start)
    if start>len(header):f.readline()
    while True:
        off=f.tell();raw=f.readline()
        if not raw:break
        e=json.loads(raw);p=e.get('payload',{})
        if e.get('type')=='response_item' and isinstance(p,dict) and p.get('type')=='agent_message' and p.get('author')==peer.removeprefix('codex:') and p.get('recipient')=='/root':
            content=p.get('content',[]);text=content[0].get('text','') if len(content)==1 else ''
            if text.startswith(prefix):
                try:d=json.loads(text[len(prefix):])
                except ValueError:d=None
                if isinstance(d,dict) and d.get('schema')=='researchos.old21-actual-programme-review-delivery.v1' and d.get('review_refs')==refs:
                    found.append((previous,(raw,off,e),d))
        previous=(raw,off,e)
assert len(found)==1,'ONE_TRUE_PROGRAMME_REVIEW_FINAL_REQUIRED'
(first,fp,fe),(last,lp,le),delivery=found[0]
assert fe['type']=='inter_agent_communication_metadata' and le['ordinal']==fe['ordinal']+1
gap=(datetime.fromisoformat(le['timestamp'].replace('Z','+00:00'))-datetime.fromisoformat(fe['timestamp'].replace('Z','+00:00'))).total_seconds()
assert 0<=gap<=1 and le['metadata']['client_authored'] is False
assert delivery['review_author']==peer and delivery['root_thread_id']==THREAD and delivery['verdict']==decision['verdict']
assert delivery['complete_hostpair_seal_ref']==seal and delivery['independent_non_author'] and delivery['Root_binding_required']
assert not any(delivery[k] for k in ('formal_acceptance','parent_acceptance','execution_grant'))
assert delivery['original_diagnostic_ordinals']==[1101,1102,1108]
lines=[header,first,last];offsets=[0,fp,lp]
with AUDIT.open('rb') as f:
    for off,line in zip(offsets,lines):f.seek(off);assert f.readline()==line
raw_path=N/'old21.programme.peer.review.raw.jsonl'
with raw_path.open('xb') as f:f.write(b''.join(lines));f.flush();os.fsync(f.fileno())
binding=save('old21.programme.peer.review.binding.root.json',dict(
    schema='researchos.root-actual-peer-capture-binding.v2',issued_by='codex:/root',root_thread_id=THREAD,peer_actor=peer,
    original_capture_ref=pin(raw_path),source_audit_path=AUDIT.as_posix(),source_prefix_size_observed=size,
    source_line_offsets=offsets,source_line_bytes=[len(x) for x in lines],original_line_sha256=[hashlib.sha256(x).hexdigest() for x in lines],
    message_id=le['payload']['id'],received_at=le['timestamp'],actual_metadata_to_final_gap_seconds=gap,
    formal_acceptance=False,parent_acceptance=False,execution_grant=False))
current=[pin(R/'execution/v2.4'/(name+'.json')) for name in ('checkpoint','path_ownership','step_state','commands')]
assert [json.loads(Path(x['path']).read_bytes()).get('revision') for x in current]==[375,179,None,40]
def all_refs(v):
    if isinstance(v,dict):
        if set(v)=={'path','sha256','bytes'}:yield v
        else:
            for x in v.values():yield from all_refs(x)
    elif isinstance(v,list):
        for x in v:yield from all_refs(x)
held={}
for ref in [*refs,seal,*current,*mf['members'],*all_refs(q)]:
    key=str(Path(ref['path'])).casefold();old=held.setdefault(key,ref);assert old['sha256']==ref['sha256'] and old['bytes']==ref['bytes']
guard_path=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
exact(guard_path,'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85',11404)
m=types.ModuleType('root_old21_programme_delivery_guard');m.__file__=str(guard_path);sys.modules[m.__name__]=m
exec(compile(guard_path.read_bytes(),str(guard_path),'exec'),m.__dict__)
guard=m.SourceReadGuard(per_file_cap=64*1024*1024,total_cap=256*1024*1024)
try:guard.acquire(list(held.values()))
finally:closed=guard.close()
assert closed['closed'] and not closed['errors'] and closed['retained_handles_count']==0
closed_ref=save('old21.programme.delivery-guard.closed.root.json',closed)
payload=save('old21.programme.root-binding.payload.json',dict(
    schema='researchos.root-old21-programme-binding-payload.v1',issued_by='codex:/root',root_thread_id=THREAD,
    review_author=peer,review_refs=refs,review_complete_seal_ref=seal,program_refs=q['program_refs'],
    independent_peer_delivery_binding_ref=binding,current_canonical_refs=current,delivery_guard_ref=closed_ref,
    created_utc=datetime.now(timezone.utc).isoformat(),formal_acceptance=False,parent_acceptance=False,execution_grant=False))
observer=save('old21.programme.root-binding.observer-input.json',dict(
    operation='OLD21_PROGRAMME_QUALIFICATION_BINDING',payload_ref=payload,
    observed_refs=[payload,binding,closed_ref,*held.values()],peer_actor=peer))
print(json.dumps(dict(payload_ref=payload,observer_input_ref=observer,peer_binding_ref=binding,guard_ref=closed_ref,
    held_refs=len(held),metadata_to_final_gap_seconds=gap,formal_acceptance=False,Canon_unchanged=True),ensure_ascii=False,indent=2))
