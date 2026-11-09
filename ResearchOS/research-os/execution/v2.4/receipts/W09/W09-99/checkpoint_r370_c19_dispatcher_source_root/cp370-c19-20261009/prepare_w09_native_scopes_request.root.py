"""Prepare finite Root native scopes after the completed actual CM40 adoption."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,hashlib,os,uuid
R=Path(r'D:\作品集\ResearchOS\research-os');N=Path(__file__).resolve().parent
W=R/'execution/v2.4/receipts/W09/W09-99'
def pin(p):
    p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,d):
    p=N/name
    with p.open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
    return pin(p)
old=json.loads((N/'w09.profile-adoption.b97a3739b43c4118984b4a6d2a2d0d10.request.actual.root.json').read_bytes())
current=[pin(R/'execution/v2.4'/(name+'.json')) for name in ('checkpoint','path_ownership','step_state','commands')]
assert [(r['sha256'],r['bytes']) for r in current]==[
    ('e75f9146266ce896a1eebd2fd4e6d1869bd4aadc6767d6e2b64c7344949d7fad',4739207),
    ('c064f519b5e6c10d64f54ae3d88260c33e00bdb20a4f1ed99dca156d6c21c91f',219480),
    ('fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149',257446),
    ('12141a8ba01d34c7181ee35e054f4762732ca8627cbee87271610e65d6f28b97',67323)]
cp=json.loads(Path(current[0]['path']).read_bytes());assert cp['revision']==375
assert cp['work_in_progress']['root_next_failure_ordinal_live']==1109
pending=save('pending-diagnostics.cp375.live1109.native.root.json',dict(schema='researchos.root-pending-diagnostics.v1',
    issued_by='codex:/root',counter_reset=False,source_cutoff_original_failure_ordinal=1108,
    next_original_failure_ordinal=1109,registered_in_current_canon=False,pending=[],current_canonical_refs=current))
base=W/'w09_profile_nf3_root_adoption_root';case=uuid.uuid4().hex;out=base/case;assert not out.exists()
commit=pin(base/'b97a3739b43c4118984b4a6d2a2d0d10/apply-profile.completed.json')
assert (commit['sha256'],commit['bytes'])==('0300932c5dd55fc068db4046d15b54bc027b6c9f62170290e871685bf227d35b',3873)
audit=pin(N/'w09.profile-commit-b97a3739b43c4118984b4a6d2a2d0d10.actual-audit.root.json')
assert (audit['sha256'],audit['bytes'])==('e1bdf76c3fe53eeffa44224cfffb7c3b293551195b4b12c2abbdda02c17c0aa7',1114)
now=datetime.now(timezone.utc)
def lease(minutes):return dict(lease_id=uuid.uuid4().hex,lease_issued_at=now.isoformat(),lease_expires_at=(now+timedelta(minutes=minutes)).isoformat())
request=dict(old,created_utc=now.isoformat(),kind='NATIVE_SCOPES',case_id=case,output_root=str(out),
    before_canonical_refs=current,main_profile_ref=pin(R/'execution/v2.4/formal_profile_w09.py'),pending_ref=pending,
    lease=lease(55),native_leases={k:lease(50) for k in ('W09-G01','W09-G02','A06')},
    profile_commit_ref=commit,profile_commit_audit_ref=audit)
ref=save('w09.native-scopes.'+case+'.request.actual.root.json',request)
print(json.dumps(dict(request_ref=ref,case_id=case,output_root=str(out),pending_ref=pending,
    current_canonical_refs=current,actual_Go_runs=0,Canon_unchanged=True,formal_acceptance=False),ensure_ascii=False,indent=2))
