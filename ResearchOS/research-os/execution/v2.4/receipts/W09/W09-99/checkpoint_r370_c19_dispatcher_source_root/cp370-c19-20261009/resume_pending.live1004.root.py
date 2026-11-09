"""Append actual original invocations to durable Root resume; no authority changes."""
from datetime import datetime, timezone
from pathlib import Path
import copy, hashlib, json, os

N = Path(__file__).resolve().parent
W = N.parent.parent
S = W / 'checkpoint_r369_native_source_root/cp369-c19-20261009'
RV = W / 'cp370_registrar_v2_independent_review_codex/regr2-01a120ab'
THREAD = '01a11007-5233-7ca1-b71f-9e9e5ce84c98'
EXITS = ('actual_outer_exit', 'actual_python_exit', 'actual_native_exit',
         'actual_dispatcher_exit', 'actual_model_exit')

def pin(path):
    path = path.resolve(strict=True)
    raw = path.read_bytes()
    return dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))

def read(ref):
    assert set(ref) == {'path', 'sha256', 'bytes'}
    assert pin(Path(ref['path'])) == ref
    return Path(ref['path']).read_bytes()

def save(path, value):
    with path.open('xb') as file:
        file.write((json.dumps(value, ensure_ascii=False, indent=2)+'\n').encode())
        file.flush(); os.fsync(file.fileno())
    return pin(path)

def validate_capture(ref, binding_ref, actor, call_id):
    raw = read(ref); binding = json.loads(read(binding_ref))
    lines = raw.splitlines(keepends=True)
    assert len(lines) == 3
    assert binding.get('original_capture_ref', binding.get('capture_ref')) == ref
    assert len(binding['source_line_offsets']) == len(binding['source_line_bytes']) == len(binding['original_line_sha256']) == 3
    with Path(binding['source_audit_path']).open('rb') as audit:
        for line, offset, size, sha in zip(lines, binding['source_line_offsets'], binding['source_line_bytes'], binding['original_line_sha256']):
            assert type(offset) is int and type(size) is int and offset >= 0 and size > 0
            assert len(line) == size and hashlib.sha256(line).hexdigest() == sha
            audit.seek(offset); assert audit.read(size) == line
    header, call, output = [json.loads(line) for line in lines]
    spawn = header['payload']['source']['subagent']['thread_spawn']
    assert header['type'] == 'session_meta' and spawn['parent_thread_id'] == THREAD and spawn['agent_path'] == actor
    assert call['payload']['call_id'] == output['payload']['call_id'] == call_id
    assert binding.get('original_call_id', binding.get('call_id')) == call_id
    for key in EXITS:
        assert binding[key] is None or type(binding[key]) is int
    return binding

resume = json.loads((S/'RESUME.cp369-main-profile-adopted.live996.root.json').read_bytes())
for ref in [resume['identity_ref'], *resume['canonical_refs']]: read(ref)
pending = json.loads(read(resume['pending_diagnostics_ref']))
assert [row['ordinal'] for row in pending['pending']] == list(range(966, 996))
prefix = copy.deepcopy(pending['pending'])
index_ref = pin(N/'originals996-1001.actual-child-host.index.root.json')
assert index_ref['sha256'] == '2b616c09924456780d6cc73f8b123246f1855b0c26938357ee390b5c01049a5e'
index = json.loads(read(index_ref))
descriptions = {
    996: 'Source worker apply_patch attempted Delete and Add of the same contract in one patch; tool rejected it. No numeric process exit was observed.',
    997: 'Source worker resolved the pending input relative to the wrong parent directory; original outer0/Python1, no Native or Canon operation.',
    998: 'Source controls supplied full diagnostics rows instead of the strict three-field live projection; original outer0/Python1.',
    999: 'Source negative control asserted a later rejection code although prior continuity validation correctly rejected first; original outer0/Python1.',
    1000: 'Source worker guessed a nonexistent v1 HDF path instead of following the prepared manifest; original outer0/Python1.',
    1001: 'Source worker bounded HDF/MF rg lookup found no v1 files; original outer1, Python/Native/dispatcher/model unknown.',
    1002: 'Independent Source reviewer guessed a nonexistent Caller source filename; original outer1. OS error 2 does not qualify an unobserved rg child exit.',
    1003: 'Independent Source reviewer guessed a nonexistent closeout.py, then a bounded rg file inventory succeeded in the same original invocation; outer0, unobserved child exits NULL.',
}
new_rows = []
for event in index['originals']:
    number = event['ordinal']; assert number in range(996, 1002)
    call_id = event['origin_selector'].removeprefix('call_id=')
    binding = validate_capture(event['origin_ref'], event['capture_binding_ref'], '/root/w09_formal_profile_source_impl', call_id)
    assert all(binding[key] == event[key] and type(binding[key]) is type(event[key]) for key in EXITS)
    row = dict(ordinal=number, origin_ref=event['origin_ref'], origin_selector=event['origin_selector'],
               description=descriptions[number], origin_capture_completeness='SOURCE_RECORDED_ORIGINAL_TOOL_IO',
               capture_binding_ref=event['capture_binding_ref'], actual_capture_format='ACTUAL_CHILD_HOST_ORIGINAL_PAIR')
    row.update({key: event[key] for key in EXITS}); new_rows.append(row)
for number, name in ((1002, '6d29ff'), (1003, '6e5aa2')):
    ref = pin(RV/('failure-'+name+'.actual-host.raw.jsonl'))
    binding_ref = pin(RV/('failure-'+name+'.binding.json'))
    binding0 = json.loads(read(binding_ref))
    binding = validate_capture(ref, binding_ref, '/root/attach_fixture_source_review', binding0['call_id'])
    row = dict(ordinal=number, origin_ref=ref, origin_selector='call_id='+binding['call_id'],
               description=descriptions[number], origin_capture_completeness='SOURCE_RECORDED_ORIGINAL_TOOL_IO',
               capture_binding_ref=binding_ref, actual_capture_format='ACTUAL_CHILD_HOST_ORIGINAL_PAIR')
    row.update({key: binding[key] for key in EXITS}); new_rows.append(row)
pending['pending'].extend(new_rows)
pending['next_original_failure_ordinal'] = 1004
assert pending['pending'][:len(prefix)] == prefix
assert [row['ordinal'] for row in pending['pending']] == list(range(966, 1004))
for row in pending['pending']: read(row['origin_ref'])
pending_ref = save(S/'pending-diagnostics.live1004.root.json', pending)
resume.update(created_utc=datetime.now(timezone.utc).isoformat(), next_original_failure_ordinal_live=1004,
              pending_diagnostics_ref=pending_ref, CP370_status='REGISTRAR_V3_SOURCE_INDEPENDENT_REVIEW_PENDING',
              Root_original_qualification_ref_historical=resume['Root_original_qualification_ref'])
resume['CP370_registrar_v3_source_hdf_ref'] = pin(W/'checkpoint_r370_c19_dispatcher_source_codex/cp370proposal-20261009-v3/HDF.json')
resume['CP370_registrar_v3_source_mf_ref'] = pin(W/'checkpoint_r370_c19_dispatcher_source_codex/cp370proposal-20261009-v3/MF.json')
resume['CP370_registrar_v2_final_review_hdf_ref'] = pin(RV/'HDF.final.json')
resume['CP370_registrar_v2_final_review_mf_ref'] = pin(RV/'MF.final.json')
resume['CP370_registrar_v2_final_review_decision_ref'] = pin(RV/'source-decision.final.json')
resume['current_original_qualification_status'] = 'PENDING_NEW_ROOT_SEED_OBSERVATION_AFTER_SOURCE_REVIEW'
for ref in resume['canonical_refs']: read(ref)
resume_ref = save(S/'RESUME.cp369-main-profile-adopted.live1004.root.json', resume)
print(json.dumps(dict(resume_ref=resume_ref, pending_ref=pending_ref, next_original=1004,
                     Canonical_unchanged=True, formal_delta=0), ensure_ascii=False), flush=True)
