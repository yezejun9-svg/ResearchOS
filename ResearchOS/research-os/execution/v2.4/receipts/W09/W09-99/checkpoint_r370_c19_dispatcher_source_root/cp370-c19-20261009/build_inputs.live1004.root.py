"""Root builds one-way inputs after an accepted registrar definition and real seed."""
from datetime import datetime, timezone, timedelta
from pathlib import Path
import hashlib, json, os

N=Path(__file__).resolve().parent
W=N.parent.parent
S=W/'checkpoint_r369_native_source_root/cp369-c19-20261009'
C=W/'w09_main_c19_dispatcher_caller_source_codex/c19call-01a12d10-v6'
CR=W/'main_c19_dispatcher_caller_independent_review_codex/c19v6-review-20261009'
NR=W/'main_c19_native_actual_independent_review_codex/review-1a12035-v2'

def pin(path):
    path=path.resolve(strict=True); raw=path.read_bytes()
    return dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))

def read(ref):
    assert set(ref)=={'path','sha256','bytes'} and pin(Path(ref['path']))==ref
    return Path(ref['path']).read_bytes()

def exact(path,sha,size):
    ref=dict(path=str(path.resolve(strict=True)),sha256=sha,bytes=size);read(ref);return ref

def save(path,value):
    with path.open('xb') as file:
        file.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode());file.flush();os.fsync(file.fileno())
    return pin(path)

resume=json.loads((S/'RESUME.cp369-main-profile-adopted.seed.live1004.root.json').read_bytes())
for ref in resume['canonical_refs']:read(ref)
pending=json.loads(read(resume['pending_diagnostics_ref']))
qualification_ref=exact(N/'original-diagnostic-qualifications.seed.live1004.root.json','c4de0877dadf3aba8d8c9f227590dd4a0fc094769b5f21ad8456f8cf4e5a0b7f',70982)
witness_ref=exact(N/'seed.actual-observation-witness.live1004.root.json','4810a89cbf434c58e65462aab1bb936afb140a2713f9d88fc0750064a201b4e9',2668)
witness=json.loads(read(witness_ref))
assert witness['qualification_ref']==qualification_ref and witness['phase']=='SEED' and witness['next_original_failure_ordinal']==1004
live=dict(schema='researchos.root-cp370-source-live-context.v2',issued_by='codex:/root',root_thread_id='01a11007-5233-7ca1-b71f-9e9e5ce84c98',
    created_utc=datetime.now(timezone.utc).isoformat(),source_cutoff={'highest_ordinal':965,'next_failure_ordinal':966},next_original_failure_ordinal=1004,
    pending=[{key:row[key] for key in ('ordinal','origin_ref','description')} for row in pending['pending']],qualification_ref=qualification_ref,seed_witness_ref=witness_ref)
live_ref=save(N/'source-live-context.seed.live1004.root.json',live)
request=dict(schema='researchos.root-cp370-c19-dispatcher-build-request.v1',issued_by='codex:/root',created_utc=datetime.now(timezone.utc).isoformat(),
    caller_hdf_ref=exact(C/'HDF.json','8a5c60ca1a8ec12ad273f098091b5ff580de5be8f72ffe38c19afb8ae64ddd78',3988),
    caller_mf_ref=exact(C/'MF.json','68e4889942de67e656ebecc5ffab7007109271c482c2f287aac1f312ae71b077',3609),
    review_hdf_ref=exact(CR/'HDF.json','103ec67601f523d545499c8a7d0dc3b16f21d601c8152c232309f916815e0174',3327),
    review_mf_ref=exact(CR/'MF.json','0da7ad889c241c41c80ac309b32ea3cfc17e1401ac4a75ca9d32c56050a9a53c',3181),
    review_decision_ref=exact(CR/'source-decision.json','0586fb5d30533d656fbfd6d4a4d2741bc1e088cdf34bcac1801af88e500fae26',3653),
    native_hdf_ref=exact(NR/'HDF.json','49dd4ae646af95ecc38004f9650245e7e6ed9e04aa9fe8711b5fd945dd840270',6428),
    native_handoff_ref=exact(S/'Main-C19-actual-handoff.root.json','cc4e8de2bf69b1b322fb500369b85bc4d737b26f761fa746a52e8088c6257835',4474),
    native_historical_request_ref=exact(S/'Main-C19-single-native-request.actual.root.json','8c0b984f4bdcd4a89464645e82780dfafbaeba8dfcdb0dbed0958df7b283e84e',1051),
    frozen_plan_ref=exact(Path('D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4/contracts/execution.plan.json'),'a6669dd94b16bc833526f569c3c86ab08180ff6a39087ca9921ea898817eea17',374645),
    historical_cp369_archives=resume['historical_canonical_refs'],before_canonical_refs=resume['canonical_refs'],source_reviewer='codex:/root/native_temp_independent_review',
    lease_expires_at=(datetime.now(timezone.utc)+timedelta(hours=24)).isoformat(),authorized_output_root=str((N/'actual-consumers').resolve()),
    live_ref=live_ref,source_qualification_ref=qualification_ref,no_actual_consumer_run=True)
assert len(request['historical_cp369_archives'])==4
for ref in request['historical_cp369_archives']:read(ref)
for ref in resume['canonical_refs']:read(ref)
request_ref=save(N/'build-request.seed.live1004.root.json',request)
print(json.dumps(dict(build_request_ref=request_ref,live_ref=live_ref,next_original=1004,Canonical_unchanged=True,formal_delta=0),ensure_ascii=False),flush=True)
