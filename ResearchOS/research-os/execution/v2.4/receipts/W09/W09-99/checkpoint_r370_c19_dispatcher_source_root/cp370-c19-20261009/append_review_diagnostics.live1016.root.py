"""Append actual review-tool diagnostics; leaves Source cutoffs and Canon intact."""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, os, types, sys
R=Path(r'D:\作品集\ResearchOS\research-os');N=Path(__file__).resolve().parent
B=R/'execution/v2.4/receipts/W05/W05-99'
RV=B/'public22_root_caller_registration_independent_review_codex/review-v2-01a120dd'

def pin(p):
    raw=p.read_bytes();return dict(path=str(p.resolve(strict=True)),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def exact(p,sha,size):
    ref=pin(p);assert ref['sha256']==sha and ref['bytes']==size;return ref
def save(name,value):
    with (N/name).open('xb') as f:
        f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
    return pin(N/name)
base_ref=exact(N/'pending-diagnostics.cp370.live1013.root.json','4013a2f77a6dced4e369159f84afc2d507b88519c7534c0a437c2fb380464005',8152)
pending=json.loads(Path(base_ref['path']).read_bytes())
resume_ref=exact(N/'RESUME.cp370-consumers-qualified.live1013.root.json','38e8633ef8796e3f59663d8fa2464b33155d623112fc1fc5e26a8cb6bf3158ac',6145)
resume=json.loads(Path(resume_ref['path']).read_bytes());canon=resume['canonical_refs']
assert [pin(Path(x['path'])) for x in canon]==canon
rows=[]
for ordinal,chunk,raw_sha,raw_bytes,binding_sha,binding_bytes,py,description in [
 (1013,'36367b','77d2e7a63fc5a28adbe71b1e7a2de51f1048c817d573dd82a34b6a8bce19a407',25035,'03883c6a40743f6b4a0e38ccd9cd3ab88c58a763f7e90719ba50648c007fbde1',1106,None,'Source reviewer guessed missing read_batch.py; outer1 without Python/product invocation.'),
 (1014,'92b59f','6fb9faf08a45ffb0382fbc64155d5a9f611a399027fb79648bc85fddb32e45c2',27336,'19e03a20a97e386413c1ad4621a0d909c786236baebd651d17a2d5b503a5a781',1107,1,'Source reviewer stdin JSON regex escape rejected before Guard acquire; no product or registration.'),
 (1015,'328b81','b6715c79ab4d0d5ba1a6d19bec4315380690a08b9087e9b681e914d43b430d0e',25898,'cc78270aed05e74375a6908c14e1fb65c99f32bc960a0b4d486c5ff5a0012045',1106,1,'Source reviewer compared forward/backslash reference dictionaries; unchanged file rejected before Guard acquire.')]:
    raw=exact(RV/('failure-'+chunk+'.actual-host.raw.jsonl'),raw_sha,raw_bytes)
    binding=exact(RV/('failure-'+chunk+'.actual-host.binding.json'),binding_sha,binding_bytes)
    doc=json.loads(Path(binding['path']).read_bytes());assert doc['actual_capture_ref']==raw
    rows.append(dict(ordinal=ordinal,origin_ref=raw,origin_selector='$',description=description,
        capture_completeness='ACTUAL_HOST_ORIGINAL_PAIR',capture_binding_ref=binding,
        actual_outer_exit=1,actual_python_exit=py,actual_native_exit=None,actual_dispatcher_exit=None,actual_model_exit=None))
review_refs=[exact(RV/name,sha,size) for name,sha,size in [
 ('HDF.json','2eaa87c7ebb3f755b4bd79f7b8aaaf15137599abe480776caa9fbebca285ec5e',3395),
 ('MF.json','fdc064846af6fbbc81591e0c8af7d13405b4a8144e6e04aca07a058446a4fcd5',20848),
 ('source-decision.json','6be1e80b64f11d6ee4c4bf5131c7ccaa89181611d58324ed6db5e383f29cbbeb',13258)]]
fr=B/'fresh_main23_programme_builder_independent_source_review_codex/src-review-20261009-01'
fresh_refs=[exact(fr/name,sha,size) for name,sha,size in [
 ('HDF.json','82ecde9ed24945a270084458f1c0fe5c1e745e68a2457696aba200bf37ac2a67',3349),
 ('MF.json','d5a5d0b2f1d9f43703819d7d4973493e2780a494679527db1932530c4ff46c8b',2678),
 ('source-decision.json','e0cded4833f8dd3fb24236312377c967ae181936fad0ff85ca53676b7cf34623',3887)]]
gp=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
gr=exact(gp,'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85',11404)
gm=types.ModuleType('root_append_review_guard');gm.__file__=str(gp);sys.modules[gm.__name__]=gm
exec(compile(gp.read_bytes(),str(gp),'exec'),gm.__dict__)
refs=[*canon,base_ref,resume_ref,gr,*review_refs,*fresh_refs]
for row in rows:refs.extend([row['origin_ref'],row['capture_binding_ref']])
guard=gm.SourceReadGuard(per_file_cap=32*1024*1024,total_cap=128*1024*1024)
try:
    guard.acquire(refs)
    assert json.loads(guard.get_buffer(review_refs[2]['path']))['decision']=='REQUEST_CHANGES_SOURCE_ONLY'
    assert json.loads(guard.get_buffer(fresh_refs[2]['path']))['verdict']=='SOURCE_ACCEPTED_FOR_ROOT_REGISTRATION'
finally:closed=guard.close()
assert closed['closed'] and closed['retained_handles_count']==0 and not closed['errors']
gc=save('diagnostic-append-source-guard.live1016.closed.root.json',closed)
pending['pending'].extend(rows);pending['next_original_failure_ordinal']=1016
assert pending['pending'][:8]==json.loads(Path(base_ref['path']).read_bytes())['pending']
assert [row['ordinal'] for row in pending['pending']]==list(range(1005,1016))
pr=save('pending-diagnostics.cp370.live1016.root.json',pending)
resume.update(created_utc=datetime.now(timezone.utc).isoformat(),prior_resume_ref=resume_ref,
    next_original_failure_ordinal_live=1016,pending_diagnostics_ref=pr,source_guard_closed_ref=gc,
    W05_public22_root_caller_status='V2_REQUEST_CHANGES_THREE_SOURCE_BLOCKERS_V3_IN_PROGRESS',
    W05_public22_root_caller_review_refs=review_refs,
    W05_current_Main23_programme_status='SOURCE_ACCEPTED_FOR_ROOT_REGISTRATION_ACTUAL_BUILD_NOT_RUN',
    W05_current_Main23_builder_independent_review_refs=fresh_refs,
    W09_profile_registry_compat_status='SOURCE_PROPOSAL_IN_PROGRESS_NOT_ADOPTED')
rr=save('RESUME.cp370-public22-fixing.live1016.root.json',resume)
assert [pin(Path(x['path'])) for x in canon]==canon
print(json.dumps(dict(resume_ref=rr,pending_ref=pr,new_originals=3,pending_total=11,next_original=1016,
    old_pending_prefix_preserved=True,Canon_unchanged=True,formal_delta=0),ensure_ascii=False),flush=True)
