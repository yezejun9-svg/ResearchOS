"""Preserve one Source read error as an append; do not alter Canon or old cuts."""
from pathlib import Path
from datetime import datetime, timezone
import json,hashlib,os
R=Path(r'D:\作品集\ResearchOS\research-os');N=Path(__file__).resolve().parent
def pin(p):
    raw=p.read_bytes();return dict(path=str(p.resolve(strict=True)),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,v):
    with (N/name).open('xb') as f:
        f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
    return pin(N/name)
old_pending_ref=pin(N/'pending-diagnostics.cp370.live1016.root.json')
assert old_pending_ref['sha256']=='904233ae7c86c4f59e69f39f9f3dcb6db8355194b57a100ea4d66e3f6b4ceada' and old_pending_ref['bytes']==11567
old_resume_ref=pin(N/'RESUME.cp370-public22-fixing.live1016.root.json')
assert old_resume_ref['sha256']=='43b61539c9ff9d4cb454ae88b3bf15d7cde978d34deeb851bf169fee6c404e84' and old_resume_ref['bytes']==8314
pending=json.loads(Path(old_pending_ref['path']).read_bytes());resume=json.loads(Path(old_resume_ref['path']).read_bytes())
canonical=resume['canonical_refs'];assert [pin(Path(x['path'])) for x in canonical]==canonical
origin=pin(R/'execution/v2.4/receipts/W05/W05-99/fresh_main23_root_caller_registration_source_codex/main23root-20261009-01/original-pending-f38b4f.fullhostpair.json')
assert origin['sha256']=='6d0c98b06a8ab5c32b91ea56e90e400cd3f53ea84d3a722a01ebe6fd52ac90dd' and origin['bytes']==6351
pending['pending'].append(dict(ordinal=1016,origin_ref=origin,origin_selector='$',
    description='Source author guessed decision.json instead of HDF source-decision.json; other reads succeeded, outer0; no Python/product invocation.',
    capture_completeness='SOURCE_REENCODED_FULL_ORIGINAL_HOST_PAIR',capture_binding_ref=None,
    actual_outer_exit=0,actual_python_exit=None,actual_native_exit=None,actual_dispatcher_exit=None,actual_model_exit=None))
pending['next_original_failure_ordinal']=1017
assert [x['ordinal'] for x in pending['pending']]==list(range(1005,1017))
assert pending['pending'][:-1]==json.loads(Path(old_pending_ref['path']).read_bytes())['pending']
pr=save('pending-diagnostics.cp370.live1017.root.json',pending)
resume.update(created_utc=datetime.now(timezone.utc).isoformat(),prior_resume_ref=old_resume_ref,
    next_original_failure_ordinal_live=1017,pending_diagnostics_ref=pr,
    W05_public22_root_caller_status='V3_SOURCE_REPAIR_SEALED_PENDING_NEW_INDEPENDENT_REVIEW',
    W05_current_Main23_root_caller_status='SEPARATE_FUTURE_SCOPE_SOURCE_IN_PROGRESS')
rr=save('RESUME.cp370-public22-v3-review.live1017.root.json',resume)
partial=save('original1017.root-recorded-incomplete.json',dict(
    schema='researchos.root-recorded-tool-error.v1',operation='collaboration.followup_task',
    target='/root/w09_formal_profile_source_impl',
    description='Dispatch Source-only public22 v4 single internal identity-path repair while all slots active.',
    observed_tool_error='collab tool failed: agent thread limit reached',
    original_full_host_pair_captured=False,actual_outer_exit=None,actual_python_exit=None,
    actual_native_exit=None,actual_dispatcher_exit=None,actual_model_exit=None))
pending['pending'].append(dict(ordinal=1017,origin_ref=partial,origin_selector='$',
    description='Root followup task rejected by active agent slot limit; no command or product invocation.',
    capture_completeness='ROOT_RECORDED_PARTIAL_ORIGINAL_TOOL_IO',capture_binding_ref=None,
    actual_outer_exit=None,actual_python_exit=None,actual_native_exit=None,actual_dispatcher_exit=None,actual_model_exit=None))
pending['next_original_failure_ordinal']=1018
pr18=save('pending-diagnostics.cp370.live1018.root.json',pending)
resume.update(created_utc=datetime.now(timezone.utc).isoformat(),prior_resume_ref=rr,
    pending_diagnostics_ref=pr18,next_original_failure_ordinal_live=1018,
    W05_public22_root_caller_status='V3_REVIEW_INTERNAL_IDENTITY_PATH_BLOCKER_V4_REPAIR_AWAITING_AGENT_SLOT')
rr18=save('RESUME.cp370-public22-v4-pending.live1018.root.json',resume)
assert [pin(Path(x['path'])) for x in canonical]==canonical
print(json.dumps(dict(resume_ref=rr18,pending_ref=pr18,next_original=1018,new_originals=2,
    pending_total=13,old_pending_preserved=True,Canon_unchanged=True,formal_delta=0),ensure_ascii=False),flush=True)
