import hashlib
import json
from pathlib import Path
import sys

ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
PREVIOUS = OUT.parent / 'session-list-closedcopy-root-r318'


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
assert [cp_before['revision'], ow_before['revision'], len(cp_before['failure_counters'])] == [318, 146, 410]
assert [cp_after['revision'], ow_after['revision'], len(cp_after['failure_counters'])] == [319, 147, 413]
assert cp_after['failure_counters'][:410] == cp_before['failure_counters']
assert cp_after['current_effective_formal_status'] == cp_before['current_effective_formal_status']
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
audit = save('registration-audit.json', {
    'actor': 'codex:/root', 'status': 'ACTUAL_CANONICAL_REGISTRATION_CLOSED_NO_CASE_ACCEPTANCE',
    'before': [318, 146, 410], 'after': [319, 147, 413], 'actual_registration_exit': 0,
    'review_ref': invocation['review_ref'], 'invocation_ref': ref(OUT / 'invocation.json'),
    'intent_ref': ref(OUT / 'canonical-write.intent.json'), 'verified_ref': ref(OUT / 'canonical-write.verified.json'),
    'old410_failure_prefix_unchanged': True, 'step_state_commands_unchanged': True,
    'targeted_harness_scope_ref': prepared['pins']['scope'], 'runner_review_ref': prepared['pins']['runner_review'],
    'new_Root_non_site_independent14': 'NOT_STARTED_AT_REGISTRATION_SEAL', 'source_acceptance': False,
    'Main_integration_authorized': False, 'formal_increment': 0})
entries = [ref(path) for path in sorted(OUT.rglob('*')) if path.is_file() and path.name != 'manifest.json']
manifest = save('manifest.json', {'entries': entries, 'count': len(entries), 'self_excluded': True,
    'at_seal_only': True, 'future_temporal_append_not_covered': True})
print(json.dumps({'registration_audit': audit, 'manifest': manifest, 'current': [319, 147, 413]}, ensure_ascii=True))
