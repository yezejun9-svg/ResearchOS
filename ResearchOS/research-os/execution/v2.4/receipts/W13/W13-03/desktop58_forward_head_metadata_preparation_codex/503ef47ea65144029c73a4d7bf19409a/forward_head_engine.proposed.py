"""UNEXECUTED TEMPLATE. Emitted by the reviewed metadata builder for sole Root.
Head-forward metadata only. No source scope or grant is created by any mode.
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

MODE = 'register'
ROOT = Path('D:/作品集/ResearchOS/research-os')
OUT = Path(__file__).absolute().parent
CANON = [ROOT / 'execution/v2.4' / (x + '.json') for x in ['checkpoint', 'path_ownership', 'step_state', 'commands']]
EXTERNAL = {}
GIT_COUNT = 0
DEADLINE = None
HASHED = 0
READS = {}
REQUEST_REF = None
OWN_OUT = False


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
    need(type(r) is dict and set(r) == {'path', 'sha256', 'bytes'} and type(r['bytes']) is int and r['bytes'] >= 0, 'exact REF shape')
    q = path(r['path'])
    need(q not in CANON, 'live canonical belongs to CAS only')
    b = raw(q)
    need(hashlib.sha256(b).hexdigest() == r['sha256'] and len(b) == r['bytes'], 'reference drift')
    normalized = {'path': str(q), 'sha256': r['sha256'], 'bytes': r['bytes']}
    need(q not in READS or READS[q] == normalized, 'same path changed during read')
    READS[q] = normalized
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
    q, runtime, r, origins = initialize_request()
    if MODE == 'prepare':
        prepare_request(q, runtime, r, origins)
        return None, None, None
    p = parse(raw(OUT / 'prepared_refs.json'))
    need(path(p['registration_namespace']) == OUT and p['authorized'] is False and p['future_root_grant'] is None, 'metadata only')
    need(same(p['request_ref'], REQUEST_REF), 'prepared current immutable request')
    pairs = [('head', 'head_after'), ('head_before', 'head_before'), ('before_tuple', 'before_tuple'), ('after_tuple', 'after_tuple'),
             ('timestamp', 'timestamp'), ('status_ref', 'status_ref'), ('old_deleted_paths', 'old_deleted_paths'),
             ('toolchain_lock_ref', 'toolchain_lock_ref'), ('helper_ref', 'helper_ref'), ('source_closure_review_ref', 'source_closure_review_ref'),
             ('source_closure_manifest_ref', 'source_closure_manifest_ref'), ('origin_cut_ref', 'origin_cut_ref')]
    need(all(p[a] == q[b] for a, b in pairs) and p['runtime_files'] == runtime and p['origins'] == origins and p['source_paths'] == r['source_paths'], 'prepared/request fields')
    for key, name in [('completed_ref', 'completed_ref'), ('source_manifest_ref', 'manifest_ref'), ('outer_manifest_ref', 'outer_manifest_ref'), ('source_grant_ref', 'grant_ref'), ('source_scope_ref', 'scope_ref')]:
        need(same(p[key], r[name]), 'prepared actual closure relation')
    need(len(p['original_refs']) == len(p['desired_refs']) == 4, 'prepared four')
    for original, copied in zip(q['original_copy_refs'], p['original_refs']):
        need(verify(original) == verify(copied) and path(copied['path']).parent == OUT, 'prepared original copy')
    lock = doc(p['toolchain_lock_ref'])['tools']
    need(Path(sys.executable).resolve() == Path(lock['python']['path']).resolve(), 'Python exact path')
    for k in ['python', 'git']:
        need(ref(lock[k]['path'])['sha256'] == lock[k]['sha256'], 'tool bytes')
    for item in p['immutable_inputs']:
        verify(item)
    need(set(READS) <= {path(x['path']) for x in p['immutable_inputs']}, 'all request/closure reads immutable')
    need(set(p['script_refs']) == {'engine', 'builder', 'register', 'run', 'seal'}, 'no grant producer')
    source = verify(q['code_refs']['engine'])
    for mode in ['register', 'run', 'seal']:
        actual = p['script_refs'][mode]
        need(path(actual['path']) == OUT / (mode + '.py'), 'script layout')
        need(verify(actual) == source.replace(b"MODE = 'register'", ("MODE = '" + mode + "'").encode(), 1), 'only emitted mode differs')
    for k in ['engine', 'builder']:
        need(same(p['script_refs'][k], q['code_refs'][k]), 'preparation code provenance')
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


def manifest_members(item):
    data = doc(item)
    rows = data['entries']
    need(type(data['count']) is int and data['count'] == len(rows) and rows, 'sealed manifest cardinality')
    parent = path(item['path']).parent
    result = {}
    for row in rows:
        q = path(row['path'])
        need(q.is_relative_to(parent) and q != path(item['path']) and q not in result, 'manifest boundary/duplicate')
        verify(row)
        result[q] = row
    return result


def member(members, parent, name):
    q = parent / name
    need(q in members, 'required sealed member: ' + name)
    return members[q]


def refs_in(value):
    if isinstance(value, dict):
        if {'path', 'sha256', 'bytes'} <= set(value):
            yield {k: value[k] for k in ['path', 'sha256', 'bytes']}
        else:
            for child in value.values():
                yield from refs_in(child)
    elif isinstance(value, list):
        for child in value:
            yield from refs_in(child)


def closure(q):
    r = doc(q['source_closure_review_ref'])
    need(r['schema'] == 'researchos.desktop58-source-execution-independent-review.v1' and r['reviewer'] == 'codex:/root/w05_merge_review', 'source closure reviewer')
    need(r['decision'] == 'SOURCE_COMMIT_EVIDENCE_CLOSED' and r['requested_changes'] == [] and r['actual_source_integration_evidence_closed'] is True, 'source closure decision')
    need(r['source_acceptance'] is False and r['fresh58_qualified'] is False and r['formal_increment'] == 0 and r['product_native_compile_SQL_HTTP_model_calls'] == 0, 'bounded closure only')
    need(r['actual_parent'] == q['head_before'] and r['actual_new_head'] == q['head_after'] and r['canonical_tuple'] == q['before_tuple'], 'actual closed head/tuple')
    need(r['source_path_count'] == 15 and len(r['source_paths']) == len(set(r['source_paths'])) == 15 and r['unique_combined_paths'] == 58, 'exact15/58')
    need([r[k] for k in ['apply_attempts', 'commit_attempts', 'actual_git_invocations', 'actual_git_native_nonzero', 'controller_owned_native_exit', 'outer_tool_exit', 'outer_explicit_python_exit']] == [1, 1, 43, 0, 0, 0, 0], 'actual finite source evidence')
    review_members = manifest_members(q['source_closure_manifest_ref'])
    need(path(q['source_closure_review_ref']['path']) in review_members and same(review_members[path(q['source_closure_review_ref']['path'])], q['source_closure_review_ref']), 'source review sealed')
    inner = manifest_members(r['manifest_ref'])
    outer = manifest_members(r['outer_manifest_ref'])
    ip, op = path(r['manifest_ref']['path']).parent, path(r['outer_manifest_ref']['path']).parent
    for name in ['completed_ref', 'source_intent_ref']:
        need(path(r[name]['path']) in inner and same(inner[path(r[name]['path'])], r[name]), 'inner relation')
    need(path(r['outer_invocation_ref']['path']) in outer and same(outer[path(r['outer_invocation_ref']['path'])], r['outer_invocation_ref']), 'outer relation')
    c, intent, invocation = doc(r['completed_ref']), doc(r['source_intent_ref']), doc(r['outer_invocation_ref'])
    scope, grant = doc(r['scope_ref']), doc(r['grant_ref'])
    need(c['actor'] == 'codex:/root' and c['status'] == 'DESKTOP_EXACT15_SOURCE_COMMIT_CLOSED_PENDING_FRESH58_VALIDATION', 'actual completion')
    need(c['parent'] == r['actual_parent'] and c['actual_new_commit'] == r['actual_new_head'] and c['source_candidate'] == r['source_candidate'], 'completion heads')
    need(c['source_paths'] == r['source_paths'] and c['unique_combined_paths'] == 58, 'completion exact source paths')
    need([c[k] for k in ['apply_attempts', 'commit_attempts', 'Git_steps', 'canonical_writes', 'compile_SQL_HTTP_models', 'formal_increment']] == [1, 1, 43, 0, 0, 0] and c['source_acceptance'] is False, 'completion bounds')
    for d in [c, intent, grant]:
        need(same(d['scope_ref'], r['scope_ref']), 'actual scope cross-binding')
    for d in [c, intent]:
        need(same(d['grant_ref'], r['grant_ref']), 'actual grant cross-binding')
    need(scope['schema'] == 'researchos.desktop15-source-integration-scope.v1' and scope['authorized'] is True and scope['owner'] == 'codex:/root', 'historical actual source scope')
    need(scope['expected_registration'] == q['before_tuple'] and scope['expected_cli43_head'] == q['head_before'] and scope['candidate'] == r['source_candidate'], 'source scope origin')
    need(same(scope['status_ref'], q['status_ref']) and scope['old_deleted_paths'] == q['old_deleted_paths'], 'same source status/deletions')
    need(same(scope['toolchain_lock_ref'], q['toolchain_lock_ref']) and same(scope['owned_process_helper_ref'], q['helper_ref']), 'same source toolchain/helper')
    need([scope[k] for k in ['exact_paths', 'union_paths', 'apply_cap', 'commit_cap']] == [15, 58, 1, 1], 'source scope caps')
    need(grant['schema'] == 'researchos.desktop15-source-integration-grant.v1' and grant['authorized'] is True and grant['actual_registration_completed'] is True and grant['status'] == 'ROOT_REGISTERED_EXECUTION_AUTHORIZED', 'real historical grant')
    need(grant['operation_uuid'] == scope['operation_uuid'] and grant['automatic_retry'] is False, 'grant operation')
    need(intent['base'] == q['head_before'] and intent['candidate'] == r['source_candidate'] and intent['canonical_copies'] == grant['canonical_copies'], 'source intent authority')
    need(len(grant['canonical_copies']) == 4, 'source grant four originals')
    for canonical, copied, original in zip(CANON, grant['canonical_copies'], q['original_copy_refs']):
        need(ROOT / copied['canonical_path'] == canonical and verify(copied['ref']) == verify(original), 'source grant same original four')
    registration = grant['registration_refs']
    rm = manifest_members(registration['manifest'])
    for name in ['audit', 'invocation', 'intent', 'verified']:
        need(path(registration[name]['path']) in rm and same(registration[name], rm[path(registration[name]['path'])]), 'source registration sealed relation')
    ra, ri = doc(registration['audit']), doc(registration['invocation'])
    need(ra['after'] == q['before_tuple'] and ra['actual_registration_exit'] == 0 and ri['actual_exit'] == 0 and ri['wrapper_error'] is None, 'actual prior Root registration')
    job_ok(ri['owned_result'])
    need(invocation['first_error'] is None and invocation['secondary_errors'] == [] and invocation['actual_native_controller_exit'] == 0 and invocation['automatic_retry'] is False and invocation['counter_reset'] is False, 'outer actual source completion')
    job_ok(invocation['owned_result'])
    started = doc(member(outer, op, 'inner.started.json'))
    need(invocation['argv'] == started['argv'], 'actual source argv pairing')
    argv = invocation['argv']
    need(argv[1:5] == ['-I', '-S', '-X', 'utf8'] and path(argv[5]) == path(scope['controller_ref']['path']), 'source controller argv')
    need(argv[6:] == ['--scope', str(path(r['scope_ref']['path'])), '--scope-sha256', r['scope_ref']['sha256'], '--grant', str(path(r['grant_ref']['path'])), '--grant-sha256', r['grant_ref']['sha256']], 'source exact argv refs')
    verify(scope['controller_ref']); verify(scope['launcher_ref'])
    observations = doc(r['root_tool_observations_ref'])
    need(observations['schema'] == 'researchos.root-owned-source-launch-tool-observations.v1' and observations['actor'] == 'codex:/root' and observations['closed'] is True, 'Root tool observation schema')
    need(observations['actual_outer_tool_exit'] == 0 and observations['actual_python_exit'] == 0 and observations['counter_reset'] is False, 'original tool exits')
    need(same(observations['actual_scope_ref'], r['scope_ref']) and same(observations['actual_grant_ref'], r['grant_ref']), 'Root launch refs')
    initial = observations['initial_result']
    polls = observations['polls']
    need(type(initial['session_id']) is int and polls and observations['terminal_result'] == polls[-1]['result'], 'original terminal pairing')
    for index, poll in enumerate(polls):
        need(poll['input']['session_id'] == initial['session_id'] and poll['input']['chars'] == '', 'original poll session/read-only')
        if index != len(polls) - 1:
            need('exit_code' not in poll['result'], 'no continued polling after terminal')
    terminal = polls[-1]['result']
    need(terminal['exit_code'] == 0 and 'ACTUAL_PYTHON_EXIT=0' in terminal['output'], 'original explicit Python exit observation')
    need(path(observations['initial_input']['workdir']) == ROOT, 'Root launch cwd')
    need(r['root_tool_observations_are_original_native_streams'] is False, 'tool bridge not native stream claim')
    need(verify(member(inner, ip, 'head-after.stdout.raw')).decode().strip() == q['head_after'], 'sealed source head')
    need(verify(member(inner, ip, 'commit-parent.stdout.raw')).decode().split() == [q['head_after'], q['head_before']], 'sealed direct parent')
    need(verify(member(inner, ip, 'delta-after.stdout.raw')).decode().splitlines() == r['source_paths'], 'sealed exact15 delta')
    need(verify(member(inner, ip, 'index-after.stdout.raw')) == b'' and verify(member(inner, ip, 'status-after.stdout.raw')) == verify(q['status_ref']), 'sealed status/index')
    calls = [x for v, x in inner.items() if v.name.endswith('.invocation.json')]
    need(len(calls) == 43, '43 actual source Git calls')
    for item in calls:
        d = doc(item)
        need(d['actual_native_exit'] == 0 and d['wrapper_error'] is None and d['automatic_retry'] is False and path(d['cwd']) == ROOT, 'source Git actual0')
        job_ok(d['process_observation'])
    return r


def initialize_request():
    global OUT, REQUEST_REF
    need(len(sys.argv) in [3, 5], 'request path+SHA then optional review path+SHA')
    REQUEST_REF = ref(sys.argv[1])
    need(REQUEST_REF['sha256'] == sys.argv[2], 'explicit immutable Root request SHA')
    q = doc(REQUEST_REF)
    need(q['schema'] == 'researchos.desktop58-forward-head-request.v1' and q['actor'] == 'codex:/root', 'Root request schema')
    need(q['authorized'] is False and q['source_acceptance'] is False and q['formal_increment'] == 0 and q['new_execution_grant'] is None, 'metadata only request')
    ns = path(q['registration_namespace'], False)
    base = ROOT / 'execution/v2.4/receipts/W05/W05-99/integration_codex'
    need(ns.parent == base and ns.name.startswith('desktop58-post-integration-') and len(q['run_uuid']) == 32 and all(x in '0123456789abcdef' for x in q['run_uuid']) and q['run_uuid'] in ns.name, 'new metadata namespace')
    need(not path(REQUEST_REF['path']).is_relative_to(ns), 'request is immutable external input')
    if MODE == 'prepare':
        OUT = ns
        need(ns.parent.is_dir() and not ns.exists(), 'fresh draft namespace')
    else:
        need(ns == OUT, 'request matches actual script namespace')
    need(q['before_tuple'] == [332, 160, 516], 'fixed current source closure baseline')
    need(q['head_before'] == 'a510dbef4a7e08fb5c428df44c39b133f3ffa856' and q['head_after'] == 'e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7', 'actual source pair')
    need(type(q['after_tuple']) is list and len(q['after_tuple']) == 3 and all(type(x) is int for x in q['after_tuple']), 'explicit Root after tuple')
    need(q['after_tuple'][:2] == [q['before_tuple'][0] + 1, q['before_tuple'][1] + 1], 'one forward revision')
    need(datetime.datetime.fromisoformat(q['timestamp']).tzinfo is not None, 'explicit timestamp')
    runtime = doc(q['runtime_resources_ref'])
    need(len(runtime['files']) == 1212, 'existing runtime1212 no widening')
    for r in runtime['files']:
        v = Path(r['path'])
        if not v.is_relative_to(ROOT):
            need(v.is_absolute() and (v not in EXTERNAL or EXTERNAL[v] == r), 'external catalog duplicate')
            EXTERNAL[v] = r
    need(len(q['original_copy_refs']) == len(q['canonical_before']) == 4, 'original four layout')
    for canonical, copied, original in zip(CANON, q['original_copy_refs'], q['canonical_before']):
        need(path(original['path']) == canonical and path(copied['path']) not in CANON, 'canonical refs separate from immutable copies')
        b = verify(copied)
        need(hashlib.sha256(b).hexdigest() == original['sha256'] and len(b) == original['bytes'], 'original copy exactbytes')
    for r in q['immutable_inputs']:
        verify(r)
    for r in q['code_refs'].values():
        verify(r)
    need(set(q['code_refs']) == {'engine', 'builder'}, 'exact preparation code2')
    if MODE == 'prepare':
        need(verify(q['code_refs']['engine']) == raw(Path(__file__)) and path(q['code_refs']['builder']['path']) == Path(sys.argv[0]).resolve(), 'actual builder/engine pairing')
    need(q['old_deleted_paths'] and len(q['old_deleted_paths']) == len(set(q['old_deleted_paths'])) == 11, 'old11D')
    rows = verify(q['status_ref']).decode('utf-8').splitlines()
    need(len(rows) == 13 and sorted(x[3:] for x in rows if x.startswith(' D ')) == sorted(q['old_deleted_paths']), 'status old11D')
    need(sorted(x for x in rows if not x.startswith(' D ')) == [' M execution/v2.4/checkpoint.json', ' M execution/v2.4/path_ownership.json'], 'status exact CP/OW only')
    need(all(path(r['path']) not in CANON for r in q['immutable_inputs']), 'live canonical is not immutable input')
    r = closure(q)
    cut = doc(q['origin_cut_ref'])
    need(cut['schema'] == 'researchos.desktop58-forward-origin-cut.v1' and cut['before_tuple'] == q['before_tuple'] and cut['after_tuple'] == q['after_tuple'], 'explicit immutable failure cut')
    need(cut['counter_reset'] is False and q['after_tuple'][2] == q['before_tuple'][2] + len(cut['origins']), 'append count')
    old = parse(verify(q['original_copy_refs'][0]))['failure_counters']
    seen = {x['sha256'] for x in refs_in(old)}
    keys = set()
    for row in cut['origins']:
        item = row['evidence_ref']
        need(row['original_payload'] == doc(item) and row['count_once'] is True and row['counter_reset'] is False, 'original failure payload preserved')
        need(item['sha256'] not in seen and item['sha256'] not in keys, 'origin already registered/duplicate')
        keys.add(item['sha256'])
    return q, runtime['files'], r, cut['origins']


def prepare_request(q, runtime, r, origins):
    global OWN_OUT
    need(MODE == 'prepare' and len(sys.argv) == 3, 'prepare only request args')
    lock = doc(q['toolchain_lock_ref'])['tools']
    need(Path(sys.executable).resolve() == Path(lock['python']['path']).resolve(), 'builder actual Python')
    for key in ['python', 'git']:
        need(ref(lock[key]['path'])['sha256'] == lock[key]['sha256'], 'fixed tool bytes')
    need(q['helper_ref']['sha256'] == '6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad', 'unchanged owned helper')
    verify(q['helper_ref'])
    before = [verify(x) for x in q['original_copy_refs']]
    need(all(raw(v) == b for v, b in zip(CANON, before)), 'prepare current four')
    p = {'authorized': False, 'future_root_grant': None, 'registration_namespace': str(OUT), 'request_ref': REQUEST_REF,
         'head': q['head_after'], 'head_before': q['head_before'], 'before_tuple': q['before_tuple'], 'after_tuple': q['after_tuple'],
         'timestamp': q['timestamp'], 'original_refs': q['original_copy_refs'], 'origins': origins, 'source_paths': r['source_paths'],
         'source_closure_review_ref': q['source_closure_review_ref'], 'source_closure_manifest_ref': q['source_closure_manifest_ref'],
         'completed_ref': r['completed_ref'], 'source_manifest_ref': r['manifest_ref'], 'outer_manifest_ref': r['outer_manifest_ref'],
         'source_grant_ref': r['grant_ref'], 'source_scope_ref': r['scope_ref'], 'origin_cut_ref': q['origin_cut_ref'],
         'status_ref': q['status_ref'], 'old_deleted_paths': q['old_deleted_paths'], 'runtime_files': runtime,
         'toolchain_lock_ref': q['toolchain_lock_ref'], 'helper_ref': q['helper_ref'], 'source_acceptance': False, 'formal_increment': 0,
         'script_refs': q['code_refs']}
    # Pure IO preparation: inspect already-loaded Python only; no helper/DLL/Git invocation.
    observed = loaded(p)
    source = verify(q['code_refs']['engine'])
    need(source.count(b"MODE = 'register'") == 1, 'engine mode anchor')
    before_again = [raw(v) for v in CANON]
    need(before_again == before and not OUT.exists(), 'preallocation fresh/current four')
    OUT.mkdir()
    OWN_OUT = True
    save('request.original.json', verify(REQUEST_REF), True)
    p['original_refs'] = [save(v.stem + '.original.json', b, True) for v, b in zip(CANON, before)]
    p['script_refs'] = dict(q['code_refs'])
    for mode in ['register', 'run', 'seal']:
        p['script_refs'][mode] = save(mode + '.py', source.replace(b"MODE = 'register'", ("MODE = '" + mode + "'").encode(), 1), True)
    _, targets = desired(p)
    p['desired_refs'] = [save(v.stem + '.desired.json', b, True) for v, b in zip(CANON, targets)]
    p['immutable_inputs'] = list(READS.values())
    for item in [*p['original_refs'], *p['script_refs'].values()]:
        if all(not same(item, old) for old in p['immutable_inputs']):
            p['immutable_inputs'].append(item)
    need(all(path(x['path']) not in CANON for x in p['immutable_inputs']), 'no live canon in immutable set')
    save('prepared_refs.json', p)
    save('audit.json', {'schema': 'researchos.desktop58-forward-head-draft-audit.v1', 'request_ref': REQUEST_REF,
         'before': p['before_tuple'], 'after': p['after_tuple'], 'head_before': p['head_before'], 'head_after': p['head'],
         'pure_IO_prepare': True, 'Git_helper_DLL_product_calls': 0, 'canonical_writes': 0, 'source_acceptance': False,
         'formal_increment': 0, 'source_closure_review_ref': p['source_closure_review_ref'], 'observed_runtime': observed,
         'immutable_count': len(p['immutable_inputs']), 'canonical_before': q['canonical_before']})
    need(all(raw(v) == b for v, b in zip(CANON, before)), 'prepare finish canonical unchanged')
    save('preparation.manifest.json', {'entries': [ref(x) for x in sorted(OUT.iterdir()) if x.is_file()], 'self_excluded': True})



def desired(p):
    before = [verify(x) for x in p['original_refs']]
    cp, ow = [parse(x) for x in before[:2]]
    original_cp, original_ow = copy.deepcopy(cp), copy.deepcopy(ow)
    a, b = p['before_tuple'], p['after_tuple']
    need([cp['revision'], ow['revision'], len(cp['failure_counters'])] == a and cp['head'] == p['head_before'], 'before tuple/head')
    need(b[:2] == [a[0] + 1, a[1] + 1] and b[2] == a[2] + len(p['origins']), 'explicit tuple increments')
    cp['failure_counters'].extend(copy.deepcopy(p['origins']))
    cp.update(head=p['head'], revision=b[0], expected_previous_revision=a[0], updated_at=p['timestamp'], updated_by='codex:/root')
    additions = {'desktop_exact15_source_integration_state': 'CLOSED_PENDING_FRESH58_VALIDATION',
        'desktop_exact15_source_integration_completed_ref': p['completed_ref'],
        'desktop_exact15_source_integration_manifest_ref': p['source_manifest_ref'],
        'desktop_exact15_source_integration_outer_manifest_ref': p['outer_manifest_ref'],
        'desktop_exact15_source_integration_grant_ref': p['source_grant_ref'],
        'desktop_exact15_source_integration_execution_review_ref': p['source_closure_review_ref'],
        'desktop_exact15_actual58_head': p['head'], 'desktop_exact15_actual_combined_source_paths': 58,
        'desktop_fresh58_validation_authorized': False, 'desktop_GUI_install_NVDA_authorized': False}
    need(same(cp['work_in_progress']['desktop_exact15_source_integration_scope_ref'], p['source_scope_ref']), 'current registered source scope')
    cp['work_in_progress'].update(additions)
    cp['next_command'] = 'Desktop source15/combined58 source commit closed; prepare separately reviewed fresh58 validation. No fresh compiler, runtime, GUI, SQL24 or formal acceptance is authorized by this head-forward registration.'
    cp['integrity_events'].append({'event': 'ROOT_DESKTOP58_FORWARD_HEAD_REGISTRATION', 'actor': 'codex:/root', 'at': p['timestamp'],
        'before': a, 'after': b, 'head_before': p['head_before'], 'head_after': p['head'],
        'completed_ref': p['completed_ref'], 'execution_review_ref': p['source_closure_review_ref'],
        'origin_refs': [x['evidence_ref'] for x in p['origins']], 'counter_reset': False, 'formal_increment': 0})
    for item in [p['request_ref'], p['completed_ref'], p['source_manifest_ref'], p['outer_manifest_ref'], p['source_grant_ref'], p['source_closure_review_ref'], p['source_closure_manifest_ref'], p['origin_cut_ref']]:
        if item['path'] not in cp['evidence_index']:
            cp['evidence_index'].append(item['path'])
    sub = ow['card_path_bindings']['W13-03']['subtasks']['desktop_exact15_source_integration']
    need(sub['owner'] == sub['current_source_writer'] == 'codex:/root' and sub['state'] == 'ROOT_REGISTERED_WAIT_SEAL_AND_EXCLUSIVE_GRANT', 'specific existing Root source lease')
    need(sub['source_paths'] == p['source_paths'] and same(sub['scope_ref'], p['source_scope_ref']), 'existing exact15 lease')
    sub.update(current_source_writer=None, state='CLOSED_PENDING_FRESH58_VALIDATION', actual_head=p['head'],
        actual_unique_source_paths=58, actual_source_paths=15, completed_ref=p['completed_ref'], manifest_ref=p['source_manifest_ref'],
        outer_manifest_ref=p['outer_manifest_ref'], grant_ref=p['source_grant_ref'], execution_review_ref=p['source_closure_review_ref'],
        source_acceptance=False, formal_increment=0, compile_test_SQL_HTTP_model_authorized=False, GUI_authorized=False)
    ow.update(revision=b[1], amended_at=p['timestamp'], amended_by='codex:/root')
    compare = copy.deepcopy(ow)
    compare['card_path_bindings']['W13-03']['subtasks']['desktop_exact15_source_integration'] = original_ow['card_path_bindings']['W13-03']['subtasks']['desktop_exact15_source_integration']
    for k in ['revision', 'amended_at', 'amended_by']:
        if k in original_ow: compare[k] = original_ow[k]
        else: compare.pop(k, None)
    need(compare == original_ow, 'other ownership changed')
    allowed = {'head', 'revision', 'expected_previous_revision', 'updated_at', 'updated_by', 'failure_counters', 'work_in_progress', 'next_command', 'integrity_events', 'evidence_index'}
    need({k: v for k, v in cp.items() if k not in allowed} == {k: v for k, v in original_cp.items() if k not in allowed}, 'other CP changed')
    need({k: v for k, v in cp['work_in_progress'].items() if k not in additions} == {k: v for k, v in original_cp['work_in_progress'].items() if k not in additions}, 'other WIP changed')
    need(cp['current_effective_formal_status'] == original_cp['current_effective_formal_status'], 'formal state changed')
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
    need(len(sys.argv) == 5, 'register request-path request-sha review-path review-sha')
    review_ref = ref(sys.argv[3])
    need(review_ref['sha256'] == sys.argv[4], 'metadata review SHA')
    review_ok(p, review_ref)
    before, target = desired(p)
    need(all(raw(q) == b for q, b in zip(CANON, before)), 'canonical before mismatch')
    source_guard(p, lock, helper, 'register-start')
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
    need(len(sys.argv) == 5, 'run request-path request-sha review-path review-sha')
    item = ref(sys.argv[3])
    need(item['sha256'] == sys.argv[4], 'review SHA')
    review_ok(p, item)
    before, target = desired(p)
    need(all(raw(q) == b for q, b in zip(CANON, before)), 'current canonical before')
    source_guard(p, lock, helper, 'run-start')
    result = None
    error = None
    argv = [lock['python']['path'], '-I', '-S', '-X', 'utf8', str(OUT / 'register.py'), str(path(REQUEST_REF['path'])), REQUEST_REF['sha256'], str(path(item['path'])), item['sha256']]
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
    need(len(sys.argv) == 3, 'seal request-path request-sha')
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
    need(all(raw(q) == b for q, b in zip(CANON, target)), 'four targets after seal source guard')
    audit = save('registration-audit.json', {'schema': 'researchos.desktop58-forward-head-registration-audit.v1', 'actor': 'codex:/root',
        'before': p['before_tuple'], 'after': p['after_tuple'], 'actual_registration_exit': 0, 'registered_head': p['head'],
        'invocation_ref': ref(OUT / 'invocation.json'), 'intent_ref': intent_ref, 'verified_ref': ref(OUT / 'canonical-write.verified.json'),
        'request_ref': p['request_ref'], 'source_closure_review_ref': p['source_closure_review_ref'], 'source_acceptance': False, 'formal_increment': 0,
        'grant_materialized': False, 'compile_GUI_HTTP_models_authorized': False})
    save('handoff-running.json', {'actor': 'codex:/root', 'canonical_refs': [ref(q) for q in CANON], 'head': p['head'],
        'tuple': p['after_tuple'], 'request_ref': p['request_ref'], 'audit_ref': audit, 'formal_increment': 0})





def main():
    global DEADLINE
    DEADLINE = time.monotonic() + 1200
    first = None
    secondary = []
    p = lock = helper = None
    try:
        p, lock, helper = setup()
        if MODE != 'prepare':
            {'register': register, 'run': run, 'seal': seal}[MODE](p, lock, helper)
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
                if MODE != 'prepare' or OWN_OUT:
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
    if first is None and time.monotonic() >= DEADLINE:
        first = {'phase': MODE + '-completion-deadline', 'error': 'metadata deadline1200 exceeded', 'actual_native_exit': None}
        print(json.dumps(first, ensure_ascii=False), file=sys.stderr)
    return 1 if first is not None else 0


if __name__ == '__main__':
    raise SystemExit(main())
