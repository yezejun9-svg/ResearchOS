"""Prepare a fresh NF6 Root request after actual independent Source delivery."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, sys, types, uuid

R=Path('D:/作品集/ResearchOS/research-os'); V=R/'execution/v2.4'; W=V/'receipts/W09/W09-99'
N=Path(__file__).resolve().parent; REG=W/'w09_nf6_root_registration_source_codex/register-20261010-01'
AUTHOR='codex:/root/full_w09_source_review'; ROOT='codex:/root'; GENERATION='fullw09-20261010-06'
entry=REG/'register_w09_adoption.source.py'; raw=entry.read_bytes()
assert len(raw)==31668 and hashlib.sha256(raw).hexdigest()=='0e79cd007d6378fa8bf0c984a1e638398362b04e8544607ee85a9dcf1d8ea963'
api=types.ModuleType('root_nf6_reviewed_registrar'); api.__file__=str(entry)
exec(compile(raw,api.__file__,'exec'),api.__dict__)
pin=api.pin
assert len(sys.argv)==4
inputs_ref=dict(path=sys.argv[1],sha256=sys.argv[2],bytes=int(sys.argv[3])); inputs=api.doc(inputs_ref)
assert inputs['schema']=='researchos.root-nf6-preparation-inputs.v1' and inputs['issued_by']==ROOT
assert inputs['formal_acceptance'] is False
stop=inputs['next_original_failure_ordinal']; assert type(stop) is int and stop==1185
source=api.doc(dict(path=str(REG/'input-pins.json'),sha256='a8da09218e791c2e2c8f608a5d35cbd52c86389bcf26923d9e33336bf5b4ef15',bytes=12757))
current=[pin(p) for p in api.CANON]; cp=api.doc(current[0])
assert cp['revision']==382 and cp['work_in_progress']['root_next_failure_ordinal_live']==1162
assert current==inputs['current_canonical_refs']
pending=inputs['pending_ref']; pending_value=api.doc(pending)
assert pending_value['current_canonical_refs']==current
assert [x['ordinal'] for x in pending_value['pending']]==list(range(1162,stop))
assert pending_value['next_original_failure_ordinal']==stop and pending_value['counter_reset'] is False
pr=inputs['producer_review_refs']; rr=inputs['registrar_review_refs']
assert set(pr)==set(rr)=={'hdf','mf','decision'}
pd=api.doc(pr['decision']); rd=api.doc(rr['decision'])
assert pd['schema']=='researchos.w09-four-selector-producer-independent-source-decision.v1'
assert rd['schema']=='researchos.w09-nf4-registration-independent-source-decision.v1'
assert pd['decision']=='SOURCE_ACCEPTED_FOR_ROOT_FOUR_SELECTOR_NATIVE'
assert rd['decision']=='SOURCE_ACCEPTED_FOR_ROOT_NF4_REGISTRATION'
assert pd['actor_id']==rd['actor_id']=='codex:/root/backup_regression_resources' and pd['actor_id'] not in (ROOT,AUTHOR)
assert rd['source_author_id']==AUTHOR
assert api.doc(source['refs']['NF_hdf'])['actor_id']==AUTHOR
assert pd['source_handoff_ref']==source['refs']['NF_hdf'] and pd['source_manifest_ref']==source['refs']['NF_mf']
assert pin(R/'ops/ci/retrieval.py')['sha256']=='b85fb90d9927a2427ee29a5ff756b8e7d18b0639e9a3910a7621991bc3788f11'
adopt=api.doc(inputs['Main_actual_component_review_ref'])
assert adopt['decision']=='ACCEPTED_ACTUAL_MAIN_ADOPTION_COMPONENT_ONLY'
old=api.doc(pin(N/'w09.native-scopes-ad02.0b3e193c2c04437eadcea7a0bee5164b.request.actual.root.json'))
start=datetime.now(timezone.utc)
def lease(minutes):
    return dict(lease_id=uuid.uuid4().hex,lease_issued_at=start.isoformat(),lease_expires_at=(start+timedelta(minutes=minutes)).isoformat())
cid=uuid.uuid4().hex; parent=api.OUTPUT_BASE
assert parent.parent==W
if not parent.exists(): api.path_checked(str(parent),True); parent.mkdir()
api.path_checked(str(parent)); out=parent/cid; assert not out.exists()
peers=dict(source['peer_audit_refs'])
peers['producer-author']=inputs['producer_author_audit_ref']; peers['producer-review']=inputs['producer_review_audit_ref']
q=dict(old,schema='researchos.root-w09-nf4-registration-request.v1',generation=GENERATION,
    created_utc=start.isoformat(),case_id=cid,output_root=str(out),before_canonical_refs=current,pending_ref=pending,
    source_handoff_ref=pin(REG/'HDF.json'),source_manifest_ref=pin(REG/'MF.json'),
    source_review_handoff_ref=rr['hdf'],source_review_manifest_ref=rr['mf'],source_review_decision_ref=rr['decision'],
    source_author_audit_ref=inputs['registrar_author_audit_ref'],source_review_audit_ref=inputs['registrar_review_audit_ref'],
    producer_review_handoff_ref=pr['hdf'],producer_review_manifest_ref=pr['mf'],producer_review_decision_ref=pr['decision'],
    reviewed_source_audits_ref=source['refs']['peer_audits'],reviewed_source_audit_refs=peers,
    lease=lease(55),native_leases={key:lease(50) for key in ('W09-G01','W09-G02','A06','C19')},
    main_profile_ref=pin(V/'formal_profile_w09.py'),formal_index_ref=pin(V/'formal_case_index.py'))
assert set(q)==api.REQUEST_FIELDS
api.require(all(q[k] is False for k in ('formal_acceptance','parent_acceptance','formal_dispatcher','automatic_retry')),'ROOT_FALSE_GRANTS')
assert [pin(p) for p in api.CANON]==current
ref=api.save(N/('w09.nf6-registration.'+cid+'.request.actual.root.json'),q)
print(json.dumps(dict(request_ref=ref,case_id=cid,generation=GENERATION,current_canonical_refs=current,
    runtime_not_invoked=True,canonical_unchanged=True,formal_acceptance=False),ensure_ascii=False))
