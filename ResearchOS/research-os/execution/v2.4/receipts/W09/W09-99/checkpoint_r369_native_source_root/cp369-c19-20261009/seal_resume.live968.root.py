"""Append a current Root resume; no canonical mutation or acceptance."""
from datetime import datetime, timezone
import hashlib, json, os
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os')
N=Path(__file__).resolve().parent
W=R/'execution/v2.4/receipts/W09/W09-99'
B=R/'execution/v2.4/receipts/W05/W05-99'
def pin(p):
    p=p.resolve(strict=True); b=p.read_bytes()
    return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def read(ref):
    b=Path(ref['path']).read_bytes()
    assert set(ref)=={'path','sha256','bytes'} and hashlib.sha256(b).hexdigest()==ref['sha256'] and len(b)==ref['bytes']
    return b
def save(name,obj):
    with (N/name).open('xb') as f:
        f.write((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode('utf-8')); f.flush(); os.fsync(f.fileno())
    return pin(N/name)
canonical=[pin(R/'execution/v2.4'/name) for name in ('checkpoint.json','path_ownership.json','step_state.json','commands.json')]
expected=[('51c038a8f6de8415f66dfd0122241989591dd7ba0dad4adf0560e2bf6d7f52ac',4347568),('07b0aeea2b6bb84acde4982be576f7a7cbb22e04a76e5c89216ae3e43231048d',202735),('fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149',257446),('28b4ba18ce2ab3ce03287651e311ae2bd36293b53fd8c298e5bf1f231f56d027',68968)]
assert [(v['sha256'],v['bytes']) for v in canonical]==expected
identity=pin(R/'execution/project_identity.json')
assert (identity['sha256'],identity['bytes'])==('03f06a2b72ae85b3445d724058b10c8b13bcdb98f31feaf195e10b2e88fb26ec',420)
facts=json.loads((N/'checkpoint.execution.facts.json').read_bytes())
pending=json.loads((N/'pending-diagnostics.live968.root.json').read_bytes())
assert pending['next_original_failure_ordinal']==968
for v in facts['diagnostics']+pending['pending']: read(v['origin_ref'])
review=B/'restored21_runtime_v3_actual_independent_review_codex/actualreview-1a11fff'
actual_hdf=pin(review/'HDF.json'); assert (actual_hdf['sha256'],actual_hdf['bytes'])==('b923aff86455114fa850a37e6934948e238ac6fdb07070422146b5ab552f6673',3418)
actual_body=json.loads(read(actual_hdf)); actual_decision=actual_body['actual_decision_ref']; read(actual_decision)
formal_review=W/'w09_formal_profile_independent_review_codex/profr-01a12022'
formal_hdf=pin(formal_review/'HDF.json'); assert (formal_hdf['sha256'],formal_hdf['bytes'])==('7c9330f7b8ac782594625d3119c3cd67b24599d9540952033dbae1891cb1b458',2030)
formal_body=json.loads(read(formal_hdf)); formal_decision=formal_body['source_decision_ref']; read(formal_decision)
resume=dict(schema='researchos.root-resume.v1',issued_by='codex:/root',created_utc=datetime.now(timezone.utc).isoformat(),identity_ref=identity,canonical_refs=canonical,checkpoint_revision=368,ownership_revision=172,registered_failures=950,highest_registered_ordinal=952,next_at_source_cutoff=953,checkpoint_live_snapshot=958,next_original_failure_ordinal_live=968,pending_diagnostics_953_to_965=facts['diagnostics'],pending_diagnostics_966_to_967=pending['pending'],cp369_source_handoff_ref=pin(N/'HDF.json'),cp369_source_manifest_ref=pin(N/'MF.json'),cp369_source_status='SOURCE_READY_PENDING_INDEPENDENT_REVIEW_NO_CANON_WRITE',W05_actual_closed_ref=facts['W05_actual_closed_ref'],W05_actual_independent_review_handoff_ref=actual_hdf,W05_actual_independent_decision_ref=actual_decision,W05_qualification='ACTUAL_DEVELOPMENT_13_EVIDENCE_VERIFIED_COMPONENT_PARTIAL_NATIVE_QUALIFICATION_OPEN',W09_formal_profile_source_review_handoff_ref=formal_hdf,W09_formal_profile_source_decision_ref=formal_decision,W09_formal_profile_source_status='V1_REQUEST_CHANGES_5_P1_V2_IMPLEMENTING',W09_MainNative_actual='NOT_REGISTERED_OR_EXECUTED',Main7_adopted_and_independently_verified=True,active_construction_parents=['W05','W09'],historical_parent_records=6,current_formal_accepted=0,required_parents=22,required_formal=42,formal_acceptance=False,parent_acceptance=False,counter_reset=False,next_action='Obtain nonauthor CP369 Source decision; after its seal create fresh live968 or newer context, register exact Root C19 owner, run one bounded Main native producer. Independently revise profile five P1s without adopting source yet.')
print(json.dumps(dict(resume_ref=save('RESUME.cp369-source-pending.live968.root.json',resume),canonical_unchanged=True,formal_delta=0),ensure_ascii=False),flush=True)
