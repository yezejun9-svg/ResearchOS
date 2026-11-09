"""Issue one finite continuation request from the actual post-close Root observation."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,os,sys,uuid
S=Path(__file__).resolve().parent;R=Path(r'D:\作品集\ResearchOS\research-os');V=R/'execution/v2.4';B=V/'receipts/W05/W05-99'
def pin(p):
    raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def doc(p):return json.loads(Path(p).read_bytes())
def verify(ref):
    assert pin(Path(ref['path']))==ref;return ref
def save(p,value):
    raw=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    return pin(p)
assert len(sys.argv)==4
ar=dict(path=sys.argv[1],sha256=sys.argv[2],bytes=int(sys.argv[3]));verify(ar);a=doc(ar['path'])
raw_ref=verify(a['original_capture_ref']);lines=Path(raw_ref['path']).read_bytes().splitlines(keepends=True);assert len(lines)==3
assert a['source_line_bytes']==[len(x) for x in lines] and a['original_line_sha256']==[hashlib.sha256(x).hexdigest() for x in lines]
ev=[json.loads(x) for x in lines];assert ev[0]['payload']['id']=='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
assert ev[1]['payload']['call_id']==ev[2]['payload']['call_id']==a['original_call_id']
def objects(v):
    if isinstance(v,dict):
        yield v
        for x in v.values():yield from objects(x)
    elif isinstance(v,list):
        for x in v:yield from objects(x)
    elif isinstance(v,str):
        try:yield from objects(json.loads(v))
        except ValueError:
            for line in v.splitlines():
                try: item=json.loads(line)
                except ValueError: continue
                if isinstance(item,(dict,list)): yield from objects(item)
obs=[x for x in objects(ev[2]['payload'].get('output')) if x.get('schema')=='researchos.root-public22-continuation-current-observation.v1']
assert len(obs)==1;q0=obs[0];current=q0['before_canonical_refs'];assert all(verify(x) for x in current)
with Path(a['source_audit_path']).open('rb') as f:
    for offset,line in zip(a['source_line_offsets'],lines):f.seek(offset);assert f.readline()==line
source=B/'public22_to_main23_continuation_caller_source_codex/continue-20261010-02';review=B/'public22_to_main23_continuation_independent_review_codex/review-20261010-02-full'
i=doc(source/'source-inputs.json');assert i['case_request_ref']==q0['case_request_ref']
now=datetime.now(timezone.utc);received=datetime.fromisoformat(ev[2]['timestamp'].replace('Z','+00:00'));assert received<=now
cid=uuid.uuid4().hex
q=dict(schema='researchos.root-public22-continuation-registration-request.v1',issued_by='codex:/root',mode='PUBLIC22_TO_MAIN23_CONTINUATION_ONLY',formal_acceptance=False,parent_acceptance=False,
    source_hdf_ref=pin(source/'HDF.json'),source_mf_ref=pin(source/'MF.json'),review_hdf_ref=pin(review/'HDF.json'),review_mf_ref=pin(review/'MF.json'),review_decision_ref=pin(review/'decision.json'),
    case_request_ref=i['case_request_ref'],evidence=i['evidence'],
    leaf_review_audit_ref=pin(S/'public22.readonly.peer.leaf-source.binding.root.json'),review_audit_ref=pin(S/'w05.continuation-source02-review.full-ref.binding.root.json'),
    existing22_review_audit_ref=pin(S/'main23.v4.peer.source-review.binding.root.json'),main23_review_audit_ref=pin(S/'main23.programme.peer.review.binding.root.json'),main23_root_binding_audit_ref=pin(S/'w05.main23-bound-existing-observation.full-ref.binding.root.json'),
    before_canonical_refs=current,expected_revisions=q0['expected_revisions'],postreview_live_audit_ref=ar,created_utc=now.isoformat(),continuation_id=cid,
    lease_id=uuid.uuid4().hex,lease_issued_at=now.isoformat(),lease_expires_at=(now+timedelta(minutes=55)).isoformat(),registration_root=str(B/'integration_codex'/('public22-continuation-registration-'+cid)),receipt_root=str(B/'integration_codex'/('public22-continuation-'+cid)))
assert q['source_hdf_ref']['sha256']=='59c0917ac7b778a6c15308602e73f2d4a47175958559bd2cca20bbda24f6373d' and q['source_mf_ref']['sha256']=='ae3a397a2c2a8ab9961dfe7cc5fda60a75ce0bab4d878ec5c547a10b720b5264'
assert q['review_decision_ref']==q0['review_decision_ref'] and not Path(q['registration_root']).exists() and not Path(q['receipt_root']).exists()
pr=save(S/('w05.public22-continuation.'+cid+'.registration.request.actual.root.json'),q)
print(json.dumps(dict(request_ref=pr,caller_ref=pin(source/'public22_to23_root.source.py'),continuation_id=cid,formal_acceptance=False,Canon_written=False),ensure_ascii=False))
