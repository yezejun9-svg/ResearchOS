import hashlib
import json
from pathlib import Path
import sys

ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
PREVIOUS = OUT.parent / 'handler38-post-integration-r322'


def ref(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


def verify(item):
    assert ref(ROOT / item['path']) == item


def save(name, value):
    with (OUT / name).open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))
    return ref(OUT / name)


assert sys.flags.isolated and not sys.flags.optimize
invocation = json.loads((OUT / 'invocation.json').read_bytes())
assert invocation['actual_exit'] == 0 and invocation['automatic_retry'] is False and invocation['counter_reset'] is False
verify(invocation['review_ref'])
review = json.loads((ROOT / invocation['review_ref']['path']).read_bytes())
assert review['decision'] == 'REGISTRATION_DRAFT_REVIEWED_FOR_ROOT_EXECUTION'
for key, name in [('register_sha256', 'register.py'), ('wrapper_sha256', 'run.py'),
                  ('prepared_refs_sha256', 'prepared_refs.json'), ('audit_sha256', 'audit.json')]:
    assert review[key] == ref(OUT / name)['sha256']
assert invocation['runner_sha256'] == review['register_sha256'] and invocation['wrapper_sha256'] == review['wrapper_sha256']
assert invocation['stdout_sha256'] == ref(OUT / 'stdout.raw')['sha256']
assert invocation['stderr_sha256'] == ref(OUT / 'stderr.raw')['sha256']
before = []
desired = []
for name in ['checkpoint', 'path_ownership', 'step_state', 'commands']:
    original = (OUT / (name + '.original.json')).read_bytes()
    previous = PREVIOUS / (name + ('.desired.json' if name in ['checkpoint', 'path_ownership'] else '.original.json'))
    assert original == previous.read_bytes()
    after = (OUT / (name + ('.desired.json' if name in ['checkpoint', 'path_ownership'] else '.original.json'))).read_bytes()
    assert after == (ROOT / 'execution/v2.4' / (name + '.json')).read_bytes()
    before.append(original)
    desired.append(after)
cp_before, ow_before = [json.loads(raw) for raw in before[:2]]
cp_after, ow_after = [json.loads(raw) for raw in desired[:2]]
assert [cp_before['revision'], ow_before['revision'], len(cp_before['failure_counters'])] == [322, 150, 425]
assert [cp_after['revision'], ow_after['revision'], len(cp_after['failure_counters'])] == [323, 151, 425]
assert cp_after['failure_counters'] == cp_before['failure_counters']
assert cp_after['current_effective_formal_status'] == cp_before['current_effective_formal_status']
assert cp_before['head'] == 'a5d6d16ffaf129de0361470c3a1570228bd259a2'
assert cp_after['head'] == 'a5d6d16ffaf129de0361470c3a1570228bd259a2'
intent = json.loads((OUT / 'canonical-write.intent.json').read_bytes())
verified = json.loads((OUT / 'canonical-write.verified.json').read_bytes())
verify(verified['intent_ref'])
for item in intent['metadata']:
    verify(item['original_ref'])
    verify(item['desired_ref'])
    done = json.loads((OUT / ('canonical-write.' + Path(item['path']).stem + '.done.json')).read_bytes())
    assert done['sha256'] == item['desired_ref']['sha256']
prepared = json.loads((OUT / 'prepared_refs.json').read_bytes())
for item in prepared['verified_refs']:
    verify(item)
assert review['reviewer'] == 'codex:/root/w05_merge_review'
assert review['expected_before'] == [322, 150, 425] and review['expected_after'] == [323, 151, 425]
assert verified['checkpoint'] == 323 and verified['ownership'] == 151 and verified['failure_origins'] == 425
assert len(review['copied_canonical_before_refs']) == 4
for original, copyref, raw in zip(prepared['canonical_before'],review['copied_canonical_before_refs'],before):
    verify(copyref)
    assert (ROOT/copyref['path']).resolve().is_relative_to((ROOT/invocation['review_ref']['path']).resolve().parent)
    assert (ROOT/copyref['path']).read_bytes() == raw and copyref['sha256'] == original['sha256']
allowed_cp = {'revision','expected_previous_revision','updated_at','updated_by','work_in_progress','next_command','integrity_events','evidence_index'}
assert {k:v for k,v in cp_after.items() if k not in allowed_cp} == {k:v for k,v in cp_before.items() if k not in allowed_cp}
allowed_wip = {'cli_exact8_source_integration_state','cli_exact8_source_integration_scope_ref','cli_exact8_source_integration_controller_review_ref','cli_exact8_source_integration_launcher_ref','cli_exact8_source_integration_grant_producer_ref','cli_exact8_fresh43_validation_authorized','r323_cut_pending_actual_tool_origin_refs','observed_actual_tool_origin_lower_bound_after_r323_cut'}
assert {k:v for k,v in cp_after['work_in_progress'].items() if k not in allowed_wip} == {k:v for k,v in cp_before['work_in_progress'].items() if k not in allowed_wip}
assert cp_after['integrity_events'][:-1] == cp_before['integrity_events']
assert cp_after['evidence_index'][:len(cp_before['evidence_index'])] == cp_before['evidence_index']
compare_ow = json.loads(json.dumps(ow_after))
cli = compare_ow['card_path_bindings']['W05-99']['subtasks'].pop('cli_exact8_source_integration')
assert cli['owner'] == cli['current_source_writer'] == 'codex:/root' and len(cli['source_paths']) == 8
for key in ['revision','amended_at','amended_by']:
    if key in ow_before: compare_ow[key] = ow_before[key]
    else: compare_ow.pop(key,None)
assert compare_ow == ow_before
assert cp_after['work_in_progress']['cli_exact8_source_integration_scope_ref'] == prepared['pins']['scope']
assert cp_after['work_in_progress']['cli_exact8_source_integration_controller_review_ref'] == prepared['pins']['integration_controller_review']
assert cp_after['work_in_progress']['r323_cut_pending_actual_tool_origin_refs'] == prepared['pending_origin_refs']
assert len(prepared['pending_origin_refs']) == 2 and cp_after['work_in_progress']['observed_actual_tool_origin_lower_bound_after_r323_cut'] == 427
audit = save('registration-audit.json', {
    'schema': 'researchos.cli8-source-integration-registration-audit.v1',
    'actor': 'codex:/root', 'status': 'ACTUAL_CANONICAL_REGISTRATION_CLOSED_NO_CASE_ACCEPTANCE',
    'before': [322,150,425], 'after': [323,151,425], 'actual_registration_exit': 0,
    'review_ref': invocation['review_ref'], 'invocation_ref': ref(OUT/'invocation.json'),
    'intent_ref': ref(OUT/'canonical-write.intent.json'), 'verified_ref': ref(OUT/'canonical-write.verified.json'),
    'pending_origin_refs': prepared['pending_origin_refs'], 'pending_origin_count':2,
    'registered_failure_origins':425, 'observed_actual_tool_origin_lower_bound':427,
    'old425_failure_prefix_unchanged': True, 'step_state_commands_unchanged': True,
    'scope_ref': prepared['pins']['scope'], 'controller_review_ref': prepared['pins']['integration_controller_review'],
    'registered_head': cp_after['head'], 'exact_source_path_cap':8,
    'actual_source_import':False, 'source_acceptance':False, 'formal_increment':0,
    'fresh43_validation_authorized':False, 'Main_integration_authorized':'ONLY_ONCE_AFTER_SEAL_AND_EXCLUSIVE_GRANT'})
entries = [ref(path) for path in sorted(OUT.rglob('*')) if path.is_file() and path.name != 'manifest.json']
manifest = save('manifest.json', {'entries': entries, 'count': len(entries), 'self_excluded': True,
    'at_seal_only': True, 'future_temporal_append_not_covered': True})
print(json.dumps({'registration_audit': audit, 'manifest': manifest, 'current': [323, 151, 425]}, ensure_ascii=True))
