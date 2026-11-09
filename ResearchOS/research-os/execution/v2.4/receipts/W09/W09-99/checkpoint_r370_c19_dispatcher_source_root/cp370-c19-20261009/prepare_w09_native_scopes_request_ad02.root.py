"""Issue fresh bounded Native scopes using the independently accepted path repair."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,hashlib,os,uuid
R=Path(r'D:\作品集\ResearchOS\research-os');N=Path(__file__).resolve().parent
W=R/'execution/v2.4/receipts/W09/W09-99'
def pin(p):
    p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def exact(p,sha,size):
    ref=pin(p);assert ref['sha256']==sha and ref['bytes']==size;return ref
def save(name,d):
    p=N/name
    with p.open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
    return pin(p)
old=json.loads((N/'w09.native-scopes.3973828e064e4d7dbf9d1559c436340d.request.actual.root.json').read_bytes())
current=[pin(R/'execution/v2.4'/(name+'.json')) for name in ('checkpoint','path_ownership','step_state','commands')]
assert [(r['sha256'],r['bytes']) for r in current]==[
    ('e75f9146266ce896a1eebd2fd4e6d1869bd4aadc6767d6e2b64c7344949d7fad',4739207),
    ('c064f519b5e6c10d64f54ae3d88260c33e00bdb20a4f1ed99dca156d6c21c91f',219480),
    ('fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149',257446),
    ('12141a8ba01d34c7181ee35e054f4762732ca8627cbee87271610e65d6f28b97',67323)]
pending=exact(N/'pending-diagnostics.cp375.live1114.root.json','b8158bb3ee7b4f6b3665d0029935c78620f9c44852851b32c06266bd49f4d8da',7790)
d=json.loads(Path(pending['path']).read_bytes());assert d['current_canonical_refs']==current
assert [x['ordinal'] for x in d['pending']]==list(range(1109,1114)) and d['next_original_failure_ordinal']==1114
source=W/'w09_profile_nf3_root_adoption_source_codex/adopt-20261010-02'
review=W/'w09_profile_nf3_root_adoption_independent_review_codex/review-adopt-20261010-02'
source_refs=[exact(source/name,sha,size) for name,sha,size in (
    ('HDF.json','265747939bf081d26225de5937e8cca7e5787d23320c1d59b7f4ff6c004f1a92',6617),
    ('MF.json','540bc3571c13b77c5333ea71b7461aca20de12dbf2d0cb5879a7299dc253c003',13386))]
review_refs=[exact(review/name,sha,size) for name,sha,size in (
    ('HDF.json','9986d0af1f90d9019d00fe64f48b450956bd31a937680e3cdc9f8eb4f0d0dd18',8846),
    ('MF.json','66f687499ff11332400caa54f9c6b42371598a7f4e4af3748d321ee8bd761b39',6725),
    ('Source-decision.json','962904b077ca2a3959df443cbe3c0ab0c4614511be0480705520c02ed429e359',9291))]
author=exact(N/'w09.adopter02-author.actual-audit.root.json','47caf620af643b2231d91552be61344f5f25604a1b57323adc7fc7e9927f5b3b',1111)
reviewer=exact(N/'w09.adopter02-review.actual-audit.root.json','d5e33f5ef661f606373396e5c07881f8c689301183d0a5a9c32157f3139719ab',1106)
now=datetime.now(timezone.utc)
def lease(minutes):return dict(lease_id=uuid.uuid4().hex,lease_issued_at=now.isoformat(),lease_expires_at=(now+timedelta(minutes=minutes)).isoformat())
case=uuid.uuid4().hex;out=W/'w09_profile_nf3_root_adoption_root'/case;assert not out.exists()
request=dict(old,created_utc=now.isoformat(),case_id=case,output_root=str(out),before_canonical_refs=current,
    pending_ref=pending,source_handoff_ref=source_refs[0],source_manifest_ref=source_refs[1],
    source_review_handoff_ref=review_refs[0],source_review_manifest_ref=review_refs[1],source_review_decision_ref=review_refs[2],
    source_author_audit_ref=author,source_review_audit_ref=reviewer,
    lease=lease(55),native_leases={key:lease(50) for key in ('W09-G01','W09-G02','A06')})
ref=save('w09.native-scopes-ad02.'+case+'.request.actual.root.json',request)
print(json.dumps(dict(request_ref=ref,case_id=case,output_root=str(out),pending_ref=pending,
    current_canonical_refs=current,actual_Go_runs=0,Canon_unchanged=True,formal_acceptance=False),ensure_ascii=False,indent=2))
