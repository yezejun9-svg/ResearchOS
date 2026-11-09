"""Root creates a bounded current request after the actual independent review."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, os, sys, uuid, types
N=Path(__file__).resolve().parent
R=Path(r'D:\作品集\ResearchOS\research-os'); W=R/'execution/v2.4/receipts/W09/W09-99'
A=W/'w09_profile_nf3_root_adoption_source_codex/adopt-20261010-01'
review=Path(sys.argv[1]); review_audit=Path(sys.argv[2]); pending_path=Path(sys.argv[3])
assert all(p.is_absolute() and p.is_relative_to(W) for p in (review,review_audit,pending_path))

def pin(path):
    raw=Path(path).read_bytes();return dict(path=str(Path(path)),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))

def read(ref):
    actual=pin(ref['path']);assert actual['sha256']==ref['sha256'] and actual['bytes']==ref['bytes']
    return json.loads(Path(ref['path']).read_bytes())

def save(name,value):
    p=N/name
    with p.open('xb') as f:
        f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
    return pin(p)

source_hdf=pin(A/'HDF.json');source_mf=pin(A/'MF.json')
assert (source_hdf['sha256'],source_hdf['bytes'])==('fae54fd911b86b8e11cb617c4fb35b22907609d69214d941728742635be45f9a',5083)
assert (source_mf['sha256'],source_mf['bytes'])==('868655ac82c62186414cc58ce05ed8b82d9f4acd88d5c62fe9dc9fd20e19be0b',9548)
source=read(source_hdf);pinsdoc=json.loads((A/'input-pins.json').read_bytes());pins=pinsdoc['refs']
review_hdf_ref=pin(review/'HDF.json')
review_hdf_doc=read(review_hdf_ref)
review_refs=[review_hdf_ref,pin(review/'MF.json'),review_hdf_doc['source_decision_ref']]
assert [(r['sha256'],r['bytes']) for r in review_refs]==[
    ('2333187de01b084b9e832d851034ff3e533a0eafb5f717165a262cbdd3902f9f',12233),
    ('68779a37df410e28eb8683eeedf2f001870335ef383a026761f80ace0182a783',10284),
    ('79fc814385bdd08564251e46243ced290606025b7484d809a54ac225a2ef9f83',11828)]
rh,rm,decision=[read(ref) for ref in review_refs]
assert rh['manifest_ref']==review_refs[1] and rh['source_decision_ref']==review_refs[2] and review_refs[2] in rm['members']
assert decision['decision']=='SOURCE_ACCEPTED_FOR_ROOT_W09_ADOPTION' and decision['actor_role']=='INDEPENDENT_NON_AUTHOR'
assert decision['source_handoff_ref']==source_hdf and decision['source_manifest_ref']==source_mf
assert decision['formal_acceptance'] is False and decision['execution_grant'] is False and decision['actual_executed'] is False
for key in ('caller_ref','core_ref','main_pair_ref','contract_ref'):
    assert decision[key]==source[key];read_bytes=Path(source[key]['path']).read_bytes()
    assert (hashlib.sha256(read_bytes).hexdigest(),len(read_bytes))==(source[key]['sha256'],source[key]['bytes'])
runtime_ref=pins['NF_runtime'];runtime=types.ModuleType('root_w09_request_actual_audits');runtime.__file__=runtime_ref['path']
raw=Path(runtime_ref['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==runtime_ref['sha256']
sys.modules[runtime.__name__]=runtime;exec(compile(raw,runtime.__file__,'exec'),runtime.__dict__)
author_audit=pin(N/'w09.adopter-author.actual-audit.root.json')
review_audit_ref=pin(review_audit)
runtime.actual_audit(author_audit,'codex:/root/native_temp_independent_review',source_hdf['sha256'])
runtime.actual_audit(review_audit_ref,decision['actor_id'],review_refs[2]['sha256'])
current=[pin(R/'execution/v2.4'/(name+'.json')) for name in ('checkpoint','path_ownership','step_state','commands')]
pending_ref=pin(pending_path);pending=read(pending_ref)
assert pending['current_canonical_refs']==current and pending['counter_reset'] is False and pending['registered_in_current_canon'] is False
cp=read(current[0]);start=cp['work_in_progress']['root_next_failure_ordinal_live']
assert type(start) is int and pending['source_cutoff_original_failure_ordinal']==start-1
assert [row['ordinal'] for row in pending['pending']]==list(range(start,pending['next_original_failure_ordinal']))
profile=pin(R/'execution/v2.4/formal_profile_w09.py');index=pin(R/'execution/v2.4/formal_case_index.py')
assert (profile['sha256'],profile['bytes'])==(pins['Q_profile_before']['sha256'],pins['Q_profile_before']['bytes'])
assert (index['sha256'],index['bytes'])==(pins['Q_index_before']['sha256'],pins['Q_index_before']['bytes'])
base=W/'w09_profile_nf3_root_adoption_root'
base.mkdir(exist_ok=True);assert not base.is_junction() and not base.is_symlink()
case=uuid.uuid4().hex;out=base/case;assert not out.exists()
now=datetime.now(timezone.utc);lease=dict(lease_id=uuid.uuid4().hex,lease_issued_at=now.isoformat(),lease_expires_at=(now+timedelta(minutes=50)).isoformat())
request=dict(schema='researchos.root-w09-profile-nf3-registration-request.v1',issued_by='codex:/root',created_utc=now.isoformat(),
    kind='PROFILE_ADOPTION',case_id=case,output_root=str(out),before_canonical_refs=current,
    main_profile_ref=profile,formal_index_ref=index,pending_ref=pending_ref,main23_qualification_ref=pins['main23_qualification'],
    reviewed_source_audits_ref=pins['peer_audits'],reviewed_source_audit_refs=pinsdoc['peer_audit_refs'],
    source_handoff_ref=source_hdf,source_manifest_ref=source_mf,source_review_handoff_ref=review_refs[0],
    source_review_manifest_ref=review_refs[1],source_review_decision_ref=review_refs[2],source_author_audit_ref=author_audit,
    source_review_audit_ref=review_audit_ref,lease=lease,native_leases={},profile_commit_ref=None,profile_commit_audit_ref=None,
    formal_acceptance=False,parent_acceptance=False,formal_dispatcher=False,automatic_retry=False,
    formal_case_accepted_delta=0,external_model_provider_requests=0,paid_provider_requests=0,production_DB_writes=0)
ref=save('w09.profile-adoption.'+case+'.request.actual.root.json',request)
print(json.dumps(dict(request_ref=ref,review_refs=review_refs,current_canonical_refs=current,case_id=case,
    output_root=str(out),actual_Main_implementation_written=False,actual_Canon_written=False),ensure_ascii=False,indent=2))
