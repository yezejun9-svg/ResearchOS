"""Preserve actual scope activation and publish the current bounded continuation."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,os
R=Path(r'D:\作品集\ResearchOS\research-os');N=Path(__file__).resolve().parent
W=R/'execution/v2.4/receipts/W09/W09-99';CASE='646e71a406c74abda1990f72fb0a34e6'
def pin(p):
    p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def exact(p,sha,size):
    r=pin(p);assert r['sha256']==sha and r['bytes']==size;return r
def save(name,d):
    p=N/name
    with p.open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
    return pin(p)
P=W/'w09_profile_nf3_root_adoption_root'/CASE
activation=exact(P/'activate.completed.json','0c7034aa0b048d38ff4813df89f39fec68919b9a131e7eb20c72a53a7f699776',3517)
a=json.loads(Path(activation['path']).read_bytes());assert a['status']=='ROOT_SCOPE_REGISTERED' and a['all_guards_closed']
current=[pin(R/'execution/v2.4'/(name+'.json')) for name in ('checkpoint','path_ownership','step_state','commands')]
assert current==a['canonical_after_refs']
docs=[json.loads(Path(x['path']).read_bytes()) for x in current];assert [x.get('revision') for x in docs]==[376,180,None,40]
assert docs[0]['work_in_progress']['root_next_failure_ordinal_live']==1117
for ref,name in zip(current,('checkpoint','path_ownership','step_state','commands')):
    with (N/('historical.cp376.before-native.'+name+'.json')).open('xb') as f:f.write(Path(ref['path']).read_bytes());f.flush();os.fsync(f.fileno())
audits={key:exact(N/('w09.native02-scope-'+stem+'-'+CASE+'.actual-audit.root.json'),sha,1118)
    for key,stem,sha in (
        ('W09-G01','G01','6c1604f5d3005c4fd0fa3bddc9576392f2f1aadb89b93344e70cfe6f71586c2a'),
        ('W09-G02','G02','d4de3500e77f11cf22b41ed04edbdbf1bae87fce3b1296ae9ecaebbc39149958'),
        ('A06','A06','cc38ba874c46e3317278b6783f66d2faa64fb399cc8d7efccb9710e295d84592'))}
bundle=save('w09.native02.scope-audits.'+CASE+'.root.json',dict(
    schema='researchos.root-w09-native-scope-actual-audits.v1',issued_by='codex:/root',activation_ref=activation,scope_audit_refs=audits))
prior_ref=pin(N/'RESUME.cp375-old21-qualified.live1113.root.json');prior=json.loads(Path(prior_ref['path']).read_bytes())
resume=save('RESUME.cp376-w09-native-registered.live1117.root.json',dict(prior,
    created_utc=datetime.now(timezone.utc).isoformat(),prior_resume_ref=prior_ref,canonical_refs=current,expected_revisions=[376,180,None,40],
    canonical_next_failure_ordinal=1117,next_original_failure_ordinal=1117,pending_ref=None,pending_diagnostic_ordinals=[],
    registered_new_diagnostics_once=list(range(1109,1117)),
    W09='THREE_NATIVE_SCOPES_ACTUALLY_REGISTERED_CP376_OW180_COMPLETED_SCOPE_AUDITS_READY_SELECTORS_NOT_STARTED',
    native_activation_ref=activation,native_scope_refs=a['scope_refs'],native_scope_audit_bundle_ref=bundle,
    old21='QUALIFIED_OLD21_BUILD_ROOT_BINDING_INDEPENDENTLY_VERIFIED_300_PLUS57_CHECKS',
    old21_binding_review_refs=[pin(R/'execution/v2.4/receipts/W05/W05-99/schema21_programme_root_binding_independent_review_codex/bind-old21-20261010-01'/name)
        for name in ('HDF.json','MF.json','decision.json')],
    next_actions=['Finalize current native requests with the completed actual scope audit bundle.',
                  'Prepare and run each reviewed W09 selector once, then independently review actual outputs.',
                  'Continue old21 public bootstrap Source and independent review; no formal acceptance from programme qualification.']))
handoff=R/'execution/v2.4/HANDOFF_RESUME_PACK.md';old=handoff.read_bytes()
with (N/'historical.HANDOFF.before-cp376.live1117.root.md').open('xb') as f:f.write(old);f.flush();os.fsync(f.fileno())
prefix=('# Current Root continuation: CP376 / OW180 / CM40 / live next1117\n\n'
    'W09 three Native scopes actually registered; completed actual scope audit bundle ready, selectors not started. Old21 programme qualification and Root binding independently verified. Goal ACTIVE; formal0/42. Diagnostics1109..1116 registered once, old failures preserved.\n\n'
    'Current resume: '+resume['path']+'\nSHA256 '+resume['sha256']+' bytes '+str(resume['bytes'])+'\n\n').encode()
with handoff.open('wb') as f:f.write(prefix+old);f.flush();os.fsync(f.fileno())
assert [pin(Path(x['path'])) for x in current]==current and handoff.read_bytes().endswith(old)
print(json.dumps(dict(bundle_ref=bundle,resume_ref=resume,current_canonical_refs=current,
    canonical_next_failure_ordinal=1117,Canon_unchanged=True,formal_acceptance=False),ensure_ascii=False,indent=2))
