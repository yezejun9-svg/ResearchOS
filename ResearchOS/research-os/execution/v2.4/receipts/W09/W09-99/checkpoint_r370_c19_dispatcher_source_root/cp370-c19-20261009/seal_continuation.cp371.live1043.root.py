from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json,os
R=Path(r'D:\作品集\ResearchOS\research-os');N=Path(__file__).resolve().parent
t=ast.parse((N/'seal_continuation.live1013.root.py').read_bytes())
exec(compile(ast.Module(body=[v for v in t.body if isinstance(v,ast.FunctionDef) and v.name in ('pin','save')],type_ignores=[]),'prior_root_helpers_only','exec'),globals())
P=R/'execution/v2.4/receipts/W09/W09-99/full_w09_main_native_producer_independent_source_review_codex/review-fullw09-20261009-01'
source_binding_ref=pin(P/'actual-first-seal-failure-hostpair.binding.json');bd=json.loads(Path(source_binding_ref['path']).read_bytes())
rawref=pin(P/'actual-first-seal-failure-hostpair.raw.jsonl')
assert rawref['sha256'] in json.dumps(bd)
standardref=save('original1042.standard-binding.root.json',dict(schema='researchos.root-original-diagnostic-capture-binding.v1',issued_by='codex:/root',original_capture_ref=rawref,original_source_binding_ref=source_binding_ref,actual_outer_exit=1,actual_python_exit=1,formal_authority=False,original_raw_unchanged=True))
prior_pending=N/'pending-diagnostics.cp371.registration-ready.live1042.root.json';pending=json.loads(prior_pending.read_bytes())
pending['pending'].append(dict(ordinal=1042,origin_ref=rawref,origin_selector='$',description='Independent fullW09 Source seal initially required canonical codex actor to equal raw /root task author. Real peer inspection proved the same production Source bug; review CHANGES_REQUIRED, no product call.',capture_completeness='ACTUAL_HOST_ORIGINAL_PAIR',capture_binding_ref=standardref,actual_outer_exit=1,actual_python_exit=1,actual_native_exit=None,actual_Go_exit=None,actual_SQLite_exit=None,actual_dispatcher_exit=None,actual_model_exit=None))
assert [v['ordinal'] for v in pending['pending']]==list(range(1024,1043))
pending.update(prior_pending_ref=pin(prior_pending),next_original_failure_ordinal=1043)
pendingref=save('pending-diagnostics.cp371.live1043.root.json',pending)
prior=N/'RESUME.cp371-leaf-v3-source-accepted.live1042.root.json';resume=json.loads(prior.read_bytes())
assert [pin(Path(v['path'])) for v in resume['canonical_refs']]==resume['canonical_refs']
resume.update(created_utc=datetime.now(timezone.utc).isoformat(),prior_resume_ref=pin(prior),pending_diagnostics_ref=pendingref,pending_diagnostic_originals=list(range(1024,1044)),next_original_failure_ordinal_live=1044,
    unsealed_pending_diagnostic_originals=[dict(ordinal=1043,source_actor='codex:/root/native_temp_independent_review',chunk_id='72e203',actual_outer_exit=1,actual_python_exit=1,origin_ref=None,full_original_IO_status='AWAITING_AUTHOR_SEALED_REF',description='Readonly caller Source runtime closure omitted two required modules already in Source inputs; strict gate retained; no product process.')],
    W09_full_native_source_status='CHANGES_REQUIRED_ACTUAL_PEER_AUTHOR_MAPPING_NEW_SOURCE_V2_IN_PROGRESS',
    full_w09_source_review_hdf_ref=pin(P/'HDF.json'),full_w09_source_review_mf_ref=pin(P/'MF.json'),full_w09_source_review_decision_ref=pin(P/'source-review-decision.json'),
    W05_current_Main23_root_caller_status='V2_SEALED_ROOT_STATIC_IDENTITY_MAPPING_BLOCKER_NEW_V3_SOURCE_REPAIR_IN_PROGRESS')
resumeref=save('RESUME.cp371-peer-source-changes-required.live1043.root.json',resume)
print(json.dumps(dict(resume_ref=resumeref,pending_ref=pendingref,current_formal_accepted=0,next_original=1044,sealed_pending_through=1042,unsealed_pending=[1043],canonical_unchanged=True),ensure_ascii=False),flush=True)
