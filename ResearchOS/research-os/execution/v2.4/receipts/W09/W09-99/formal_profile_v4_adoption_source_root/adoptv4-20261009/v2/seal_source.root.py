import hashlib,json,os
from pathlib import Path
N=Path(__file__).resolve().parent
def pin(p):
    p=p.resolve(strict=True);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(name,v):
    with (N/name).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
    return pin(N/name)
o=json.loads((N/'publication.outcome.check.json').read_bytes());g=json.loads((N/'source-guard.cleanup.check.json').read_bytes())
assert o['error'] is None and o['index_anchor_published'] is False and g['closed'] is True and g['retained_handles_count']==0 and not g['errors']
names=['adopt_formal_profile.source.py','seal_source.root.py','publication.intent.check.json','publication.outcome.check.json','source-guard.cleanup.check.json','source-check.original-tool-io.root.json','construction.original-tool-io.root.json','adopter.v1.full-byte-inverse.py','reviewer-gate.allowed-byte-change.json']
mf=save('MF.json',dict(schema='researchos.root-w09-profile-v4-publication-source-manifest.v1',members=[pin(N/n) for n in names]))
h=save('HDF.json',dict(schema='researchos.root-w09-profile-v4-publication-source-handoff.v1',actor_id='codex:/root',status='SOURCE_READY_PENDING_INDEPENDENT_REVIEW_NO_MAIN_WRITE',manifest_ref=mf,writer_ref=pin(N/'adopt_formal_profile.source.py'),source_check_outcome_ref=pin(N/'publication.outcome.check.json'),profile_source_handoff_ref=o['profile_source_handoff_ref'],profile_source_review_handoff_ref=o['profile_source_review_handoff_ref'],previous_adopter_handoff_ref=pin(N.parent/'HDF.json'),only_fix='ADOPTER-F1_EXACT_CANONICAL_NONAUTHOR_REVIEWER',expected_source_decision='SOURCE_ACCEPTED_FOR_ROOT_PROFILE_V4_PUBLICATION',scope='ONLY_TWO_REVIEWED_W09_MAIN_SOURCE_FILES',formal_case_accepted_delta=0,parent_acceptance=False))
print(json.dumps(dict(handoff_ref=h,manifest_ref=mf,writer_ref=pin(N/'adopt_formal_profile.source.py')),ensure_ascii=False),flush=True)
