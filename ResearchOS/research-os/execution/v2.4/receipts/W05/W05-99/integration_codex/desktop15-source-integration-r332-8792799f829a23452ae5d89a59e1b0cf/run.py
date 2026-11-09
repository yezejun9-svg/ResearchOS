"""UNEXECUTED TEMPLATE. Emitted by the reviewed metadata builder for sole Root.
The active scope is materialized only by seal after independently reviewed CAS.
No mode starts the source controller or launcher.
"""
import sys
sys.dont_write_bytecode = True
import copy
import datetime
import hashlib
import json
import os
from pathlib import Path
import time
import traceback
import types

MODE = 'run'
ROOT = Path('D:/作品集/ResearchOS/research-os')
OUT = Path(__file__).absolute().parent
CANON = [ROOT / 'execution/v2.4' / (x + '.json') for x in ['checkpoint', 'path_ownership', 'step_state', 'commands']]
EXTERNAL = {}
GIT_COUNT = 0
DEADLINE = None
HASHED = 0


def need(v, message):
    if not v:
        raise RuntimeError(message)


def parse(b):
    def pairs(items):
        d = {}
        for k, v in items:
            need(k not in d, 'duplicate JSON key')
            d[k] = v
        return d
    return json.loads(b.decode('utf-8', 'strict'), object_pairs_hook=pairs, parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))


def path(v, exists=True):
    p = Path(v)
    p = p if p.is_absolute() else ROOT / p
    need('..' not in p.parts and p.resolve(strict=exists) == p.absolute(), 'path alias')
    need(p.is_relative_to(ROOT) or p in EXTERNAL, 'unapproved external resource')
    for q in [p, *p.parents]:
        if os.path.lexists(q):
            need(not q.is_symlink() and not (getattr(q.lstat(), 'st_file_attributes', 0) & 0x400), 'reparse ancestor')
    return p


def raw(v):
    global HASHED
    p = path(v)
    need(p.stat().st_size <= 256 * 1024**2, '256MiB file bound')
    chunks = []
    with p.open('rb') as f:
        while True:
            need(DEADLINE is not None and time.monotonic() < DEADLINE, 'metadata observation deadline1200')
            b = f.read(1024**2)
            if not b:
                break
            HASHED += len(b)
            need(HASHED <= 32 * 1024**3, 'metadata read32GiB')
            chunks.append(b)
    return b''.join(chunks)


def ref(v):
    p = path(v)
    b = raw(p)
    return {'path': str(p), 'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b)}


def verify(r):
    b = raw(r['path'])
    need(hashlib.sha256(b).hexdigest() == r['sha256'] and len(b) == r['bytes'], 'reference drift')
    return b


def same(a, b):
    return path(a['path']) == path(b['path']) and a['sha256'] == b['sha256'] and a['bytes'] == b['bytes']


def doc(r):
    return parse(verify(r))


def encode(d):
    return (json.dumps(d, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')


def save(name, d, is_raw=False, target=None):
    directory = OUT if target is None else target
    need(directory.is_relative_to(ROOT), 'output Root only')
    with (directory / name).open('xb') as f:
        f.write(d if is_raw else encode(d))
    return ref(directory / name)


def loaded(p, helper=None):
    expected = {path(x['path']): x for x in p['runtime_files']}
    expected.update({path(x['path']): x for x in p['script_refs'].values()})
    expected[path(p['helper_ref']['path'])] = p['helper_ref']
    paths = {Path(sys.executable)}
    for m in list(sys.modules.values()):
        for k in ['__file__', '__cached__']:
            v = getattr(m, k, None)
            if v and Path(v).is_file():
                paths.add(Path(v))
    if helper is not None:
        paths.update(Path(x) for x in helper.runtime_resource_paths())
    rows = []
    for v in sorted(paths):
        q = path(v)
        need(q in expected, 'unfrozen actual Python/OS runtime')
        verify(expected[q])
        rows.append(ref(q))
    return rows


def setup():
    need(sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode and not sys.flags.optimize, 'Python flags')
    need(Path.cwd().resolve() == ROOT, 'Root cwd')
    p = parse(raw(OUT / 'prepared_refs.json'))
    need(path(p['registration_namespace']) == OUT and p['authorized'] is False and p['future_root_grant'] is None, 'template preparation cannot grant')
    for r in p['runtime_files']:
        q = Path(r['path'])
        if not q.is_relative_to(ROOT):
            need(q.is_absolute() and q not in EXTERNAL, 'external catalog duplicate')
            EXTERNAL[q] = r
    lock = doc(p['toolchain_lock_ref'])['tools']
    need(Path(sys.executable).resolve() == Path(lock['python']['path']).resolve(), 'Python exact path')
    for k in ['python', 'git']:
        need(ref(lock[k]['path'])['sha256'] == lock[k]['sha256'], 'tool bytes')
    for r in p['immutable_inputs']:
        verify(r)
    for r in p['script_refs'].values():
        verify(r)
    save(MODE + '.runtime.before-import.json', {'kind': 'ACTUAL_POINT_IN_TIME_NOT_LIFECYCLE', 'files': loaded(p)})
    h = p['helper_ref']
    need(h['sha256'] == '6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad', 'owned helper')
    helper = types.ModuleType('desktop_registration_owned')
    helper.__file__ = str(path(h['path']))
    sys.modules[helper.__name__] = helper
    exec(compile(verify(h), helper.__file__, 'exec'), helper.__dict__)
    save(MODE + '.runtime.before.json', {'kind': 'ACTUAL_POINT_IN_TIME_NOT_LIFECYCLE', 'files': loaded(p, helper)})
    return p, lock, helper


def job_ok(result):
    need(result and result.get('actual_exit') == 0 and result.get('error') is None and result.get('timed_out') is False and result.get('resumed') is True, 'owned process failed')
    need(result.get('owned_child_pid', 0) > 0 and result.get('creation_time_100ns', 0) > 0, 'owned identity')
    c = result.get('job_cleanup', {})
    need(c.get('errors') == [] and c.get('active_processes_last_observed') == 0, 'Job cleanup')
    need(all(c.get(k) is True for k in ['unnamed_exclusive_job', 'kill_on_job_close_configured', 'assigned_before_resume', 'primary_exit_confirmed', 'job_idle_confirmed', 'handles_closed']), 'Job flags')


def owned_call(p, helper, label, argv, timeout):
    result = None
    error = None
    env = {k: v for k, v in os.environ.items() if k.upper() in ['SYSTEMROOT', 'WINDIR', 'COMSPEC', 'PATHEXT']}
    env.update(GIT_OPTIONAL_LOCKS='0', GIT_NO_REPLACE_OBJECTS='1', GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='nul', GIT_TERMINAL_PROMPT='0')
    try:
        with (OUT / (label + '.stdout.raw')).open('xb') as so, (OUT / (label + '.stderr.raw')).open('xb') as se:
            result = helper.run_owned(argv, str(ROOT), env, so, se, timeout)
        job_ok(result)
    except BaseException as exc:
        error = repr(exc)
        raise
    finally:
        save(label + '.invocation.json', {'actor': 'codex:/root', 'argv': argv, 'cwd': str(ROOT), 'owned_result': result,
            'actual_exit': result.get('actual_exit') if isinstance(result, dict) else None, 'wrapper_error': error,
            'automatic_retry': False, 'counter_reset': False})
    return raw(OUT / (label + '.stdout.raw'))


def source_guard(p, lock, helper, label):
    global GIT_COUNT
    queries = [('head', ['rev-parse', 'HEAD']), ('status', ['status', '--porcelain=v1', '--untracked-files=no']), ('index', ['diff', '--cached', '--name-only'])]
    results = []
    for name, args in queries:
        GIT_COUNT += 1
        need(GIT_COUNT <= 15, 'metadata Git15 cap per mode')
        results.append(owned_call(p, helper, label + '-' + name, [lock['git']['path'], '-c', 'core.fsmonitor=false', *args], 30))
    need(results[0].decode().strip() == p['head'] and results[1] == verify(p['status_ref']) and results[2] == b'', 'HEAD/status/index drift')
    for item in p['immutable_inputs']:
        verify(item)
    for name in p['old_deleted_paths']:
        need(not os.path.lexists(ROOT / name), 'old deletion restored')


def desired(p):
    before = [verify(x) for x in p['original_refs']]
    cp, ow = [parse(x) for x in before[:2]]
    original_cp, original_ow = copy.deepcopy(cp), copy.deepcopy(ow)
    a, b = p['before_tuple'], p['after_tuple']
    need([cp['revision'], ow['revision'], len(cp['failure_counters'])] == a and cp['head'] == p['head'], 'before tuple/head')
    need(b[:2] == [a[0] + 1, a[1] + 1] and b[2] == a[2] + len(p['origins']), 'explicit tuple increments')
    cp['failure_counters'].extend(copy.deepcopy(p['origins']))
    cp.update(revision=b[0], expected_previous_revision=a[0], updated_at=p['timestamp'], updated_by='codex:/root')
    additions = {'desktop_exact15_source_integration_scope_ref': p['future_scope_ref'],
        'desktop_exact15_source_integration_controller_review_ref': p['controller_review_ref'],
        'desktop_exact15_source_integration_state': 'ROOT_REGISTERED_WAIT_SEAL_AND_EXCLUSIVE_GRANT',
        'desktop_fresh58_validation_authorized': False, 'desktop_GUI_install_NVDA_authorized': False}
    cp['work_in_progress'].update(additions)
    cp['next_command'] = 'Complete Desktop exact15 metadata seal; only the separately generated once-only Root grant may authorize the source-only15 import. No compiler/runtime/GUI qualification.'
    cp['integrity_events'].append({'event': 'ROOT_DESKTOP15_SCOPE_REGISTRATION', 'before': a, 'after': b, 'scope_ref': p['future_scope_ref'], 'counter_reset': False, 'formal_increment': 0})
    for item in [p['future_scope_ref'], p['controller_review_ref'], p['binding_ref']]:
        if item['path'] not in cp['evidence_index']:
            cp['evidence_index'].append(item['path'])
    task = ow['card_path_bindings']['W13-03']
    sub = task.setdefault('subtasks', {})
    need('desktop_exact15_source_integration' not in sub, 'existing lease')
    sub['desktop_exact15_source_integration'] = {'owner': 'codex:/root', 'current_source_writer': 'codex:/root',
        'state': 'ROOT_REGISTERED_WAIT_SEAL_AND_EXCLUSIVE_GRANT', 'scope_ref': p['future_scope_ref'],
        'controller_review_ref': p['controller_review_ref'], 'source_paths': p['source_paths'], 'candidate': p['candidate'],
        'source_path_cap': 15, 'apply_cap': 1, 'commit_cap': 1, 'compile_test_SQL_HTTP_model_authorized': False,
        'source_acceptance': False, 'formal_increment': 0}
    ow.update(revision=b[1], amended_at=p['timestamp'], amended_by='codex:/root')
    compare = copy.deepcopy(ow)
    compare['card_path_bindings']['W13-03'] = original_ow['card_path_bindings']['W13-03']
    for k in ['revision', 'amended_at', 'amended_by']:
        if k in original_ow:
            compare[k] = original_ow[k]
        else:
            compare.pop(k, None)
    need(compare == original_ow, 'other ownership changed')
    allowed = {'revision', 'expected_previous_revision', 'updated_at', 'updated_by', 'failure_counters', 'work_in_progress', 'next_command', 'integrity_events', 'evidence_index'}
    need({k: v for k, v in cp.items() if k not in allowed} == {k: v for k, v in original_cp.items() if k not in allowed}, 'other CP changed')
    need({k: v for k, v in cp['work_in_progress'].items() if k not in additions} == {k: v for k, v in original_cp['work_in_progress'].items() if k not in additions}, 'other WIP changed')
    need(cp['head'] == original_cp['head'] and cp['current_effective_formal_status'] == original_cp['current_effective_formal_status'], 'formal/head changed')
    need(cp['failure_counters'][:a[2]] == original_cp['failure_counters'], 'failure prefix')
    return before, [encode(cp), encode(ow), before[2], before[3]]


def review_ok(p, item):
    review = doc(item)
    need(review['schema'] == 'researchos.root-registration-source-review.v1' and review['reviewer'] == 'codex:/root/w05_merge_review', 'actual independent metadata reviewer')
    need(review['decision'] == 'REGISTRATION_DRAFT_REVIEWED_FOR_ROOT_EXECUTION' and review['requested_changes'] == [] and review['actual_registration_executed'] is False, 'metadata review decision')
    need(review['expected_before'] == p['before_tuple'] and review['expected_after'] == p['after_tuple'], 'review tuple')
    for key, name in [('register_sha256', 'register.py'), ('wrapper_sha256', 'run.py'), ('prepared_refs_sha256', 'prepared_refs.json'), ('audit_sha256', 'audit.json')]:
        need(review[key] == ref(OUT / name)['sha256'], 'metadata code pin')
    need(len(review['copied_canonical_before_refs']) == len(review['canonical_before']) == 4, 'review copies4')
    parent = path(item['path']).parent
    expected_parent = ROOT / 'execution/v2.4/receipts/W05/W05-99' / ('root_registration_r' + str(p['after_tuple'][0]) + '_readonly_review_codex')
    need(parent.parent == expected_parent and len(parent.name.replace('-', '')) == 32 and all(c in '0123456789abcdef' for c in parent.name.replace('-', '')), 'metadata review namespace/UUID')
    for canonical, original, copied, actual in zip(CANON, p['original_refs'], review['copied_canonical_before_refs'], review['canonical_before']):
        need(path(copied['path']).is_relative_to(parent) and verify(copied) == verify(original), 'copied original bytes')
        need(path(actual['path']) == canonical and actual['sha256'] == original['sha256'] and actual['bytes'] == original['bytes'], 'canonical original ordered identity/hash')
    return review


def register(p, lock, helper):
    need(len(sys.argv) == 3, 'register review-path review-sha; cannot bypass independent metadata review')
    review_ref = ref(sys.argv[1])
    need(review_ref['sha256'] == sys.argv[2], 'metadata review SHA')
    review_ok(p, review_ref)
    before, target = desired(p)
    need(all(raw(q) == b for q, b in zip(CANON, before)), 'canonical before mismatch')
    source_guard(p, lock, helper, 'register-start')
    need(not path(p['future_scope_ref']['path'], False).exists(), 'active scope must not yet exist')
    intent = save('canonical-write.intent.json', {'actor': 'codex:/root', 'Main_head': p['head'],
        'transition': {'checkpoint': [p['before_tuple'][0], p['after_tuple'][0]], 'ownership': [p['before_tuple'][1], p['after_tuple'][1]], 'failures': [p['before_tuple'][2], p['after_tuple'][2]]},
        'metadata': [{'path': q.relative_to(ROOT).as_posix(), 'original_ref': a, 'desired_ref': b} for q, a, b in zip(CANON[:2], p['original_refs'][:2], p['desired_refs'][:2])],
        'unchanged': [{'path': q.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(b).hexdigest()} for q, b in zip(CANON[2:], before[2:])],
        'recovery': 'Forward-only review exact own completed prefix; no automatic retry/reset/rollback.', 'formal_increment': 0})
    for q, b, expected in zip(CANON, target, p['desired_refs']):
        need(verify(expected) == b, 'desired bytes mismatch')
    for q, b in zip(CANON[:2], target[:2]):
        with q.with_name(q.name + '.desktop-registration.tmp').open('xb') as f:
            f.write(b)
    live = list(before)
    for i, q in enumerate(CANON[:2]):
        need(all(raw(x) == b for x, b in zip(CANON, live)), 'four canonical completed prefix drift')
        source_guard(p, lock, helper, 'register-pre-' + str(i))
        need(all(raw(x) == b for x, b in zip(CANON, live)), 'four canonical completed prefix drift after source guard')
        os.replace(q.with_name(q.name + '.desktop-registration.tmp'), q)
        live[i] = target[i]
        need(raw(q) == target[i], 'replace did not match')
        save('canonical-write.' + q.stem + '.done.json', {'sha256': hashlib.sha256(target[i]).hexdigest()})
    need(all(raw(q) == b for q, b in zip(CANON, target)), 'post canonical')
    source_guard(p, lock, helper, 'register-after')
    need(all(raw(q) == b for q, b in zip(CANON, target)), 'four canonical target drift after final source guard')
    save('canonical-write.verified.json', {'checkpoint': p['after_tuple'][0], 'ownership': p['after_tuple'][1], 'failure_origins': p['after_tuple'][2], 'intent_ref': intent, 'formal_increment': 0})


def run(p, lock, helper):
    need(len(sys.argv) == 3, 'run review-path review-sha')
    item = ref(sys.argv[1])
    need(item['sha256'] == sys.argv[2], 'review SHA')
    review_ok(p, item)
    before, target = desired(p)
    need(all(raw(q) == b for q, b in zip(CANON, before)), 'current canonical before')
    source_guard(p, lock, helper, 'run-start')
    result = None
    error = None
    argv = [lock['python']['path'], '-I', '-S', '-X', 'utf8', str(OUT / 'register.py'), str(path(item['path'])), item['sha256']]
    try:
        with (OUT / 'stdout.raw').open('xb') as so, (OUT / 'stderr.raw').open('xb') as se:
            env = {k: v for k, v in os.environ.items() if k.upper() in ['SYSTEMROOT', 'WINDIR', 'COMSPEC', 'PATHEXT']}
            result = helper.run_owned(argv, str(ROOT), env, so, se, 1200)
        job_ok(result)
    except BaseException as exc:
        error = repr(exc)
        raise
    finally:
        save('invocation.json', {'actor': 'codex:/root', 'argv': argv, 'cwd': str(ROOT), 'actual_exit': result.get('actual_exit') if isinstance(result, dict) else None,
            'owned_result': result, 'wrapper_error': error, 'review_ref': item,
            'runner_sha256': ref(OUT / 'register.py')['sha256'], 'wrapper_sha256': ref(OUT / 'run.py')['sha256'],
            'stdout_sha256': ref(OUT / 'stdout.raw')['sha256'], 'stderr_sha256': ref(OUT / 'stderr.raw')['sha256'], 'automatic_retry': False, 'counter_reset': False})


def seal(p, lock, helper):
    need(len(sys.argv) == 1, 'seal no args')
    need(not (OUT / 'register.failure.json').exists() and not (OUT / 'run.failure.json').exists(), 'later mode failure cannot be hidden by child0')
    need((OUT / 'register.runtime.after.json').is_file() and (OUT / 'run.runtime.after.json').is_file(), 'actual post-mode closure missing')
    invocation = doc(ref(OUT / 'invocation.json'))
    need(invocation['actual_exit'] == 0 and invocation['wrapper_error'] is None and invocation['automatic_retry'] is False, 'actual registration failure')
    job_ok(invocation['owned_result'])
    review_ok(p, invocation['review_ref'])
    need(invocation['stdout_sha256'] == ref(OUT / 'stdout.raw')['sha256'] and invocation['stderr_sha256'] == ref(OUT / 'stderr.raw')['sha256'], 'raw streams')
    before, target = desired(p)
    need(all(raw(q) == b for q, b in zip(CANON, target)), 'actual desired4')
    verified = doc(ref(OUT / 'canonical-write.verified.json'))
    need([verified['checkpoint'], verified['ownership'], verified['failure_origins']] == p['after_tuple'], 'actual target tuple')
    intent_ref = ref(OUT / 'canonical-write.intent.json')
    need(same(verified['intent_ref'], intent_ref), 'intent binding')
    for q, item in zip(CANON[:2], p['desired_refs'][:2]):
        need(doc(ref(OUT / ('canonical-write.' + q.stem + '.done.json')))['sha256'] == item['sha256'], 'incomplete replace')
    source_guard(p, lock, helper, 'seal-current')
    active = doc(p['active_scope_payload_ref'])['scope']
    need(active['authorized'] is True and active['status'] == 'ROOT_REGISTERED_DESKTOP15_SOURCE_COMMIT_ONCE', 'active payload')
    b = encode(active)
    need(hashlib.sha256(b).hexdigest() == p['future_scope_ref']['sha256'] and len(b) == p['future_scope_ref']['bytes'], 'future scope exact bytes')
    need(path(p['future_scope_ref']['path'], False) == OUT / 'scope_registration.json', 'scope materialization destination')
    save('scope_registration.json', b, True)
    audit = save('registration-audit.json', {'schema': 'researchos.desktop15-source-integration-registration-audit.v1', 'actor': 'codex:/root',
        'before': p['before_tuple'], 'after': p['after_tuple'], 'actual_registration_exit': 0, 'registered_head': p['head'],
        'invocation_ref': ref(OUT / 'invocation.json'), 'intent_ref': intent_ref, 'verified_ref': ref(OUT / 'canonical-write.verified.json'),
        'scope_ref': p['future_scope_ref'], 'controller_review_ref': p['controller_review_ref'], 'source_acceptance': False, 'formal_increment': 0,
        'grant_materialized': False, 'compile_GUI_HTTP_models_authorized': False})
    save('handoff-running.json', {'actor': 'codex:/root', 'canonical_refs': [ref(q) for q in CANON], 'head': p['head'],
        'tuple': p['after_tuple'], 'scope_ref': p['future_scope_ref'], 'audit_ref': audit, 'formal_increment': 0})


def grant(p, lock, helper):
    need(len(sys.argv) == 1, 'grant no args')
    scope = doc(p['future_scope_ref'])
    need(scope['authorized'] is True, 'scope not actual')
    manifest = doc(ref(OUT / 'manifest.json'))
    need(manifest['count'] == len(manifest['entries']), 'registration seal count')
    members = {}
    for item in manifest['entries']:
        q = path(item['path'])
        need(q.is_relative_to(OUT) and q not in members, 'registration MF boundary')
        verify(item)
        members[q] = item
    needed = ['registration-audit.json', 'invocation.json', 'canonical-write.intent.json', 'canonical-write.verified.json', 'scope_registration.json']
    need(all(OUT / name in members for name in needed), 'unsealed actual registration')
    audit = doc(members[OUT / 'registration-audit.json'])
    need(audit['actual_registration_exit'] == 0 and audit['after'] == p['after_tuple'], 'actual registration authority')
    need(not any((OUT / name).exists() for name in ['register.failure.json', 'run.failure.json', 'seal.failure.json']), 'registration has preserved failure')
    invocation = doc(members[OUT / 'invocation.json'])
    need(invocation['actual_exit'] == 0 and invocation['wrapper_error'] is None and invocation['automatic_retry'] is False and invocation['counter_reset'] is False, 'actual registration invocation')
    job_ok(invocation['owned_result'])
    review_ok(p, invocation['review_ref'])
    need(invocation['stdout_sha256'] == ref(OUT / 'stdout.raw')['sha256'] and invocation['stderr_sha256'] == ref(OUT / 'stderr.raw')['sha256'], 'actual registration streams')
    need(audit['invocation_ref'] == members[OUT / 'invocation.json'] and audit['intent_ref'] == members[OUT / 'canonical-write.intent.json'] and audit['verified_ref'] == members[OUT / 'canonical-write.verified.json'], 'sealed actual audit relations')
    before, target = desired(p)
    need(all(raw(q) == b for q, b in zip(CANON, target)), 'canonical drift after seal')
    source_guard(p, lock, helper, 'grant-current')
    destination = ROOT / 'execution/v2.4/receipts/W13/W13-03/desktop_exact15_integration_root_grant_codex' / scope['operation_uuid']
    need(destination.parent.is_dir() and not destination.exists(), 'exclusive grant leaf; Root parent preparation required')
    path(destination, False).mkdir()
    copies = [{'canonical_path': q.relative_to(ROOT).as_posix(), 'ref': save(q.stem + '.actual.json', b, True, destination)} for q, b in zip(CANON, target)]
    rr = {key: members[OUT / name] for key, name in [('audit', 'registration-audit.json'), ('invocation', 'invocation.json'), ('intent', 'canonical-write.intent.json'), ('verified', 'canonical-write.verified.json')]}
    rr['manifest'] = ref(OUT / 'manifest.json')
    save('grant.json', {'schema': 'researchos.desktop15-source-integration-grant.v1', 'actor': 'codex:/root', 'authorized': True,
        'actual_registration_completed': True, 'status': 'ROOT_REGISTERED_EXECUTION_AUTHORIZED', 'scope_ref': p['future_scope_ref'],
        'controller_review_ref': p['controller_review_ref'], 'operation_uuid': scope['operation_uuid'], 'automatic_retry': False,
        'canonical_copies': copies, 'registration_refs': rr, 'source_acceptance': False, 'formal_increment': 0}, target=destination)
    rows = [ref(q) for q in sorted(destination.iterdir()) if q.is_file()]
    save('manifest.json', {'count': len(rows), 'entries': rows, 'self_excluded': True}, target=destination)


def main():
    global DEADLINE
    DEADLINE = time.monotonic() + 1200
    first = None
    secondary = []
    p = lock = helper = None
    try:
        p, lock, helper = setup()
        {'register': register, 'run': run, 'seal': seal, 'grant': grant}[MODE](p, lock, helper)
    except BaseException as exc:
        first = {'phase': MODE, 'error': repr(exc), 'traceback': traceback.format_exc(), 'actual_native_exit': None}
        print(json.dumps(first, ensure_ascii=False), file=sys.stderr)
    finally:
        if p is not None and helper is not None:
            try:
                save(MODE + '.runtime.after.json', {'kind': 'ACTUAL_POINT_IN_TIME_NOT_LIFECYCLE', 'files': loaded(p, helper)})
            except BaseException as exc:
                entry = {'phase': MODE + '-runtime-after', 'error': repr(exc), 'actual_native_exit': None}
                if first is None:
                    first = entry
                else:
                    secondary.append(entry)
        if first is not None:
            try:
                save(MODE + '.failure.json', {'first_error': first, 'secondary_errors': secondary, 'counter_reset': False, 'automatic_retry': False})
            except BaseException as exc:
                secondary.append({'phase': 'failure-evidence', 'error': repr(exc), 'actual_native_exit': None})
            print(json.dumps({'first_error': first, 'secondary_errors': secondary}, ensure_ascii=False), file=sys.stderr)
        elif MODE == 'seal':
            try:
                rows = [ref(q) for q in sorted(OUT.iterdir()) if q.is_file()]
                save('manifest.json', {'count': len(rows), 'entries': rows, 'self_excluded': True})
            except BaseException as exc:
                first = {'phase': 'seal-manifest', 'error': repr(exc), 'actual_native_exit': None}
                print(json.dumps(first, ensure_ascii=False), file=sys.stderr)
    return 1 if first is not None else 0


if __name__ == '__main__':
    raise SystemExit(main())
