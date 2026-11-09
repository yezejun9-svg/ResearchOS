"""Root writes actual build inputs only after the independently sealed review.

No product, Canon mutation, retry or acceptance. The original two Source
failures extend the immutable live1018 prefix rather than replacing it.
"""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, os, sys, uuid

R = Path(r'D:\作品集\ResearchOS\research-os')
N = Path(__file__).resolve().parent
B = R / 'execution/v2.4/receipts/W05/W05-99'
ROOT = 'codex:/root'
THREAD = '01a11007-5233-7ca1-b71f-9e9e5ce84c98'

def pin(path):
    p = Path(path).resolve(strict=True)
    raw = p.read_bytes()
    return dict(path=str(p), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))

def exact(ref):
    assert set(ref) == {'path', 'sha256', 'bytes'}
    assert pin(ref['path']) == ref, 'EXACT_ROOT_INPUT_CHANGED'
    return ref

def read(ref):
    return json.loads(Path(exact(ref)['path']).read_bytes())

def save(name, value):
    with (N / name).open('xb') as f:
        f.write((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode())
        f.flush(); os.fsync(f.fileno())
    return pin(N / name)

def time_now(): return datetime.now(timezone.utc).isoformat()

assert len(sys.argv) == 4
config_ref = dict(path=sys.argv[1], sha256=sys.argv[2], bytes=int(sys.argv[3]))
config = read(config_ref)
assert config['issued_by'] == ROOT and type(config['live_next']) is int
live_next = config['live_next']
old_pending_ref = config['prior_pending_ref']; old_pending = read(old_pending_ref)
old_resume_ref = config['prior_resume_ref']; old_resume = read(old_resume_ref)
assert old_pending['next_original_failure_ordinal'] == 1018
assert old_resume['next_original_failure_ordinal_live'] == 1018
canonical = [pin(R / 'execution/v2.4' / (x + '.json'))
             for x in ('checkpoint', 'path_ownership', 'step_state', 'commands')]
assert canonical == old_resume['canonical_refs']
source_hdf_ref = config['source_hdf_ref']; source = read(source_hdf_ref)
source_mf_ref = source['manifest_ref']; read(source_mf_ref)
seal = read(config['review_seal_ref'])
review_hdf_ref = seal['review_refs']['HDF']; hdf = read(review_hdf_ref)
review_mf_ref = seal['review_refs']['MF']; read(review_mf_ref)
review_decision_ref = seal['review_refs']['decision']; decision = read(review_decision_ref)
assert decision['decision'] == 'ACCEPTED_SOURCE_ONLY'
assert decision['actor_id'] == 'codex:/root/attach_fixture_source_review'
assert decision['source_hdf_ref'] == source_hdf_ref
assert decision['source_mf_ref'] == source_mf_ref
assert decision['formal_acceptance'] is False and decision['execution_grant'] is False
assert hdf['actor_id'] == decision['actor_id'] and hdf['manifest_ref'] == review_mf_ref
raw_ref = seal['actual_review_host_capture_ref']; raw = Path(exact(raw_ref)['path']).read_bytes()
binding_ref = seal['actual_review_host_binding_ref']; binding = read(binding_ref)
assert binding.get('actual_capture_ref', binding.get('original_capture_ref')) == raw_ref
assert seal['actual_outer_exit'] == 0 and seal['actual_python_exit'] == 0
parts = raw.splitlines(keepends=True)
assert len(parts) == 3 and len(binding['source_line_offsets']) == 3
assert [len(p) for p in parts] == binding['source_line_bytes']
assert [hashlib.sha256(p).hexdigest() for p in parts] == binding['original_line_sha256']
with Path(binding['source_audit_path']).open('rb') as audit:
    for offset, part in zip(binding['source_line_offsets'], parts):
        audit.seek(offset); assert audit.read(len(part)) == part, 'ACTUAL_PEER_AUDIT_BYTES_CHANGED'
header, call, returned = map(json.loads, parts)
origin = json.dumps(header['payload'].get('source', {}))
assert THREAD in origin and '/root/attach_fixture_source_review' in origin
assert call['payload']['call_id'] == returned['payload']['call_id'] == binding['original_call_id']
assert call['payload']['type'] in ('function_call', 'custom_tool_call')
assert returned['payload']['type'] in ('function_call_output', 'custom_tool_call_output')
assert review_decision_ref['sha256'] in json.dumps(returned['payload'], ensure_ascii=False)
root_binding_ref = save('public22.v4.review-hostpair.binding.root.json', dict(
    schema='researchos.root-public22-external-review-binding.v1', issued_by=ROOT,
    review_hdf_ref=review_hdf_ref, review_mf_ref=review_mf_ref,
    review_decision_ref=review_decision_ref, original_capture_ref=raw_ref,
    original_call_id=binding['original_call_id'], verified_peer_binding_ref=binding_ref,
    actual_audit_bytes_verified=True, formal_acceptance=False, created_utc=time_now()))
pending = json.loads(json.dumps(old_pending))
for item in config['originals']:
    assert item['ordinal'] == 1005 + len(pending['pending'])
    exact(item['origin_ref'])
    pending['pending'].append(item)
assert [r['ordinal'] for r in pending['pending']] == list(range(1005, live_next))
assert pending['pending'][:13] == old_pending['pending']
pending['next_original_failure_ordinal'] = live_next
pending_ref = save('pending-diagnostics.cp370.live%d.root.json' % live_next, pending)
resume = json.loads(json.dumps(old_resume))
resume.update(created_utc=time_now(), prior_resume_ref=old_resume_ref,
    pending_diagnostics_ref=pending_ref, next_original_failure_ordinal_live=live_next,
    W05_public22_root_caller_status='V4_INDEPENDENT_SOURCE_ACCEPTED_ROOT_BUILD_INPUTS_CREATED',
    W05_public22_root_caller_review_refs=[review_hdf_ref, review_mf_ref, review_decision_ref])
resume_ref = save('RESUME.cp370-public22-v4-source-accepted.live%d.root.json' % live_next, resume)
created = time_now()
assert datetime.fromisoformat(created) > datetime.fromisoformat(hdf['reviewed_utc'].replace('Z', '+00:00'))
live_ref = save('public22.v4.reviewed-live.root.json', dict(issued_by=ROOT,
    root_resume_ref=resume_ref, review_decision_ref=review_decision_ref,
    current_canonical_refs=canonical, created_utc=created, formal_acceptance=False))
case_id = uuid.uuid4().hex
output_root = B / 'integration_codex' / ('schema22-public-' + case_id)
caller_root = B / 'integration_codex' / ('schema22-public-caller-' + case_id)
assert not output_root.exists() and not caller_root.exists()
case_ref = save('public22.v4.case-request.actual.root.json', dict(
    case_id=case_id, output_root=str(output_root), end_version=22))
build_ref = save('public22.v4.registration-build-request.actual.root.json', dict(
    schema='researchos.root-public22-registration-build.v1', issued_by=ROOT,
    before_canonical_refs=canonical, source_hdf_ref=source_hdf_ref,
    source_mf_ref=source_mf_ref, review_decision_ref=review_decision_ref,
    review_hdf_ref=review_hdf_ref, review_mf_ref=review_mf_ref,
    review_hostpair_binding_ref=root_binding_ref, root_resume_ref=resume_ref,
    reviewed_root_live_ref=live_ref, pending_ref=pending_ref, case_request_ref=case_ref,
    output_root=str(output_root), caller_receipt_root=str(caller_root),
    lease_expires_at=(datetime.now(timezone.utc)+timedelta(hours=24)).isoformat(),
    created_utc=time_now(), formal_acceptance=False, parent_acceptance=False))
assert [pin(Path(r['path'])) for r in canonical] == canonical
print(json.dumps(dict(build_request_ref=build_ref, pending_ref=pending_ref,
    root_resume_ref=resume_ref, case_request_ref=case_ref, source_review_ref=review_decision_ref,
    external_review_binding_ref=root_binding_ref, new_originals=len(config['originals']), next_original=live_next,
    canonical_unchanged=True, formal_delta=0), ensure_ascii=False), flush=True)
