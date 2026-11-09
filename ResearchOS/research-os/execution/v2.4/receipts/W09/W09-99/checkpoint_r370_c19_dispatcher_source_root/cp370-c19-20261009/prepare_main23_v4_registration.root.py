"""Create a fresh build request from actual Root and non-author receipts."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,os,uuid
N=Path(__file__).resolve().parent
R=Path(r'D:\作品集\ResearchOS\research-os');B=R/'execution/v2.4/receipts/W05/W05-99'
M=B/'fresh_main23_root_caller_registration_source_codex/main23root-20261010-04'
THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
def pin(p):
    raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def exact(p,sha,size):
    a=pin(p);assert (a['sha256'],a['bytes'])==(sha,size);return a
def save(name,v):
    p=N/name
    with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
    return pin(p)
post_ref=exact(N/'main23.v4.postreview-current4.artifact.actual.root.json','835db2719cdb0bc81d1adac2b998707b1d098dcb6f810d29879aba1ccc791f3b',2142)
post=json.loads(Path(post_ref['path']).read_bytes())
for ref in post['canonical_refs']:
    exact(Path(ref['path']),ref['sha256'],ref['bytes'])
review=json.loads((N/'main23.v4.source-review.observer-input.root.json').read_bytes())
case_id=uuid.uuid4().hex
parent=B/'integration_codex'
out=parent/('fresh-main23-'+case_id)
caller=parent/('fresh-main23-caller-'+case_id)
registration=parent/('fresh-main23-registration-'+case_id)
assert not any(p.exists() for p in (out,caller,registration))
case_ref=save('main23.v4.case-request.actual.root.json',dict(case_id=case_id,output_root=str(out)))
now=datetime.now(timezone.utc)
q=dict(schema='researchos.root-main23-registration-request.v1',issued_by='codex:/root',formal_acceptance=False,
    before_canonical_refs=post['canonical_refs'],expected_revisions=post['expected_revisions'],
    public371_registration_ref=exact(B/'public22_root_caller_registration_source_codex/p22root-20261009-04/registration.activate.root.json',
        'd724b09865c9fbd3d885282e4784b6cfc975f706d35bdfbc37f8362a63a1fb64',2151),
    source_hdf_ref=exact(M/'HDF.json','348034a2f2f23342f6a309ed14ffe64183a3bbb031ed79d6c8ed5facf34c0fd3',32853),
    source_mf_ref=exact(M/'MF.json','dd65dabdff33ccc10b229222992cf7db5702837c60cd7ed565769248c09e88c1',22750),
    review_hdf_ref=review['observed_refs'][0],review_mf_ref=review['observed_refs'][1],review_decision_ref=review['observed_refs'][2],
    review_hostpair_witness_ref=exact(N/'main23.v4.source-review-witness.artifact.actual.root.json',
        '4a87ff6741285d56e4338e665649bef3d2a3c47364b45e69580b68dc197bff08',1475),
    root_resume_ref=post['root_resume_ref'],postreview_live_ref=post_ref,
    created_utc=now.isoformat(),lease_expires_at=(now+timedelta(hours=24)).isoformat(),
    case_request_ref=case_ref,caller_receipt_root=str(caller),registration_root=str(registration),
    pending_ref=exact(N/'pending-diagnostics.cp372.live1067.root.json','f7bde983e06e920a94cf67c34f111b5dd3fdba0a59ecf7188194882bc3343652',55852),
    runtime_qualification_ref=exact(N/'main23.v4.runtime-qualification-v2.issued.actual.root.json',
        'be5e4799f995222cf7867ec7d9319357dfac873a2bcf83b512ab219606b37c55',36864))
q_ref=save('main23.v4.registration-request.actual.root.json',q)
print(json.dumps(dict(registration_request_ref=q_ref,case_request_ref=case_ref,
    output_root=str(out),caller_receipt_root=str(caller),registration_root=str(registration)),ensure_ascii=False,indent=2))
