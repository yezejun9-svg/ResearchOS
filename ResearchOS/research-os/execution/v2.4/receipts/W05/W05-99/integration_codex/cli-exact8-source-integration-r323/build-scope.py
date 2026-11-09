"""Freeze actual Main38 public inputs for a new, still unregistered CLI8 scope."""
import sys
sys.dont_write_bytecode = True
import ast
import hashlib
import json
import os
from pathlib import Path
import time
import types
import uuid

assert sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode and not sys.flags.optimize
ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
ROOT322 = OUT.parent / 'handler38-post-integration-r322'
CLI = ROOT / 'execution/v2.4/receipts/W05/W05-99/cli_exact8_integration_preparation_codex/revision-v2-5c9a5e8f634449fbad0ff484f165da2a'
BEFORE = [322, 150, 425]
AFTER = [323, 151, 425]
READS = {}
BYTES = 0
DEADLINE = time.monotonic() + 900

def read(path):
    global BYTES
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    p = p.absolute()
    assert p.is_relative_to(ROOT) or p == Path(sys.executable).absolute()
    assert p.resolve() == p and '..' not in p.parts and not p.is_symlink()
    for q in [p] + list(p.parents):
        if os.path.lexists(q):
            assert not getattr(os.lstat(q), 'st_file_attributes', 0) & 0x400
    assert p.stat().st_size <= 268435456 and time.monotonic() < DEADLINE
    chunks = []
    with p.open('rb') as stream:
        while True:
            assert time.monotonic() < DEADLINE
            data = stream.read(1048576)
            if not data:
                break
            BYTES += len(data)
            assert BYTES <= 34359738368
            chunks.append(data)
    raw = b''.join(chunks)
    assert p not in READS or READS[p] == raw
    READS[p] = raw
    return raw

def ref(path, expected=None):
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    raw = read(p)
    p = p.absolute()
    result = {'path': p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else str(p),
        'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    assert expected is None or result['sha256'] == expected
    return result

def doc(item):
    assert ref(item['path'], item['sha256'])['bytes'] == item['bytes']
    return json.loads(read(item['path']))

def save(name, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
    with (OUT / name).open('xb') as stream:
        stream.write(raw)
    return ref(OUT / name)

assert len(sys.argv) == 3
review_ref = ref(sys.argv[1], sys.argv[2])
review = doc(review_ref)
assert review['schema'] == 'researchos.main38-closed-execution-review.v1'
assert review['reviewer'] != 'codex:/root' and review['decision'] == 'EXACT38_MAIN_SOURCE_INTEGRATION_EVIDENCE_CLOSED'
assert review['requested_changes'] == []
post_ref = ref(ROOT322 / 'registration-audit.json', 'd3bd87694dc7e61a3601e2bb4db77e2cb48356e90690458eac3adea4e64b1383')
post = doc(post_ref)
assert post['schema'] == 'researchos.main38-post-integration-registration-audit.v1'
assert post['actual_registration_exit'] == 0 and post['after'] == BEFORE
assert post['registered_head'] == 'a5d6d16ffaf129de0361470c3a1570228bd259a2'
assert review['completed_ref'] == post['completed_ref'] and review['manifest_ref'] == post['manifest_ref']
assert review['post_registration_audit_ref'] == post_ref
doc(post['completed_ref'])
doc(post['manifest_ref'])
canonical_before = [ref(ROOT / 'execution/v2.4' / (name + '.json'))
    for name in ['checkpoint', 'path_ownership', 'step_state', 'commands']]
cp, ow = [doc(item) for item in canonical_before[:2]]
assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == BEFORE
assert cp['head'] == post['registered_head'] and cp['project_id'] == 'aede0678-7308-43dc-b9f2-cfe3d90cfdfb'
proposal_ref = ref(CLI / 'scope.v2.proposed.json', 'e00af3444b9aebb305b718493ad8350d9322c0ccf29359d2f0e14117eb8fb0bc')
scope = doc(proposal_ref)
assert scope['status'] == 'PREPARATION_ONLY_NOT_EXECUTABLE' and scope['authorized'] is False
assert scope['expected_registration'] is None and scope['base'] == cp['head']
assert scope['controller_ref']['sha256'] == 'f3301a8fad305ce207afa0595d0071c91842f9258ad3b2e58ddb709e1562922b'
ref(scope['controller_ref']['path'], scope['controller_ref']['sha256'])
planned = doc(scope['protected_source_paths_ref'])
assert len(planned) == len(set(planned)) == 6839
exact = doc(scope['exact8_ref'])
assert len(exact) == 8 and not set(planned).intersection({row['path'] for row in exact})
protected = [ref(ROOT / name) for name in planned]
mu = '.local/w0599-main-stream-integration-r268/mu-worker.mjs'
assert len([r for r in protected if r['path'] == mu and r['sha256'] == '2a8e70132a914affc6122c1f1db29cfa315b655c93d4200145852ebbc853d441']) == 1
assert not {r['path'] for r in protected}.intersection({r['path'] for r in canonical_before})
for row in exact:
    assert row['existing_file_not_absent'] is True
    assert ref(row['path'], row['before_sha256'])['bytes'] == row['before_bytes']
lock = doc(scope['toolchain_lock_ref'])['tools']
assert Path(sys.executable).absolute() == Path(lock['python']['path']).absolute()
assert hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest() == lock['python']['sha256']
assert hashlib.sha256(Path(lock['git']['path']).read_bytes()).hexdigest() == lock['git']['sha256']
hr = scope['owned_process_helper_ref']
helper_bytes = read(hr['path'])
assert hashlib.sha256(helper_bytes).hexdigest() == hr['sha256'] == '6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad'
helper = types.ModuleType('cli8_scope_readonly_owned_job')
helper.__file__ = str(ROOT / hr['path']) if not Path(hr['path']).is_absolute() else hr['path']
exec(compile(helper_bytes, helper.__file__, 'exec'), helper.__dict__)
environment = {k: v for k, v in os.environ.items() if k.upper() in ['SYSTEMROOT', 'WINDIR', 'COMSPEC', 'PATHEXT']}
environment.update(PATH='C:/Windows/System32;C:/Windows', GIT_OPTIONAL_LOCKS='0', GIT_NO_REPLACE_OBJECTS='1',
    GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT='0')
prefix = [lock['git']['path'], '-c', 'core.fsmonitor=false', '-c', 'core.untrackedCache=false']

def query(name, args):
    argv = prefix + args
    with (OUT / (name + '.stdout.raw')).open('xb') as so, (OUT / (name + '.stderr.raw')).open('xb') as se:
        result = helper.run_owned(argv, str(ROOT), environment, so, se, 30)
    save(name + '.invocation.json', {'argv': argv, 'cwd': str(ROOT), 'environment': environment,
        'process_observation': result, 'actual_native_exit': result.get('actual_exit'),
        'automatic_retry': False, 'source_mutations': 0})
    assert result['actual_exit'] == 0 and result['error'] is None and not result['timed_out'] and result['resumed']
    cleanup = result['job_cleanup']
    assert cleanup['errors'] == [] and all(cleanup[k] for k in ['unnamed_exclusive_job', 'assigned_before_resume',
        'kill_on_job_close_configured', 'primary_exit_confirmed', 'job_idle_confirmed', 'handles_closed'])
    return read(OUT / (name + '.stdout.raw'))

assert query('current-head', ['rev-parse', 'HEAD']).decode().strip() == scope['base']
status = query('current-status', ['status', '--porcelain=v1', '--untracked-files=no'])
assert hashlib.sha256(status).hexdigest() == 'e03849874f27dcf3b079cb84c9bae69ad97311118da47c3122a5a9b32b9611b4'
assert query('current-index', ['diff', '--cached', '--name-only']) == b''
operation = uuid.uuid4().hex
scope.update(status='ROOT_REGISTERED_CLI8_SOURCE_COMMIT_ONCE', authorized=True,
    expected_before_registration=BEFORE, expected_registration=AFTER,
    registration_namespace=OUT.relative_to(ROOT).as_posix(), operation_uuid=operation,
    new_output_root='execution/v2.4/receipts/W05/W05-99/cli_exact8_integration_executor_codex/' + operation,
    protected_source_vector_ref=save('protected.actual-main38.json', protected),
    status_ref=ref(OUT / 'current-status.stdout.raw'), main38_completed_ref=post['completed_ref'],
    main38_manifest_ref=post['manifest_ref'], main38_post_registration_audit_ref=post_ref,
    main38_execution_review_ref=review_ref)
scope['root_registration_condition'] = 'Only actual reviewed323 CAS+seal+exclusive Root grant permits the one source-only import; this file alone grants nothing.'
scope_ref = save('scope_registration.json', scope)
assert all(p.read_bytes() == raw for p, raw in READS.items())
audit = save('scope-derivation-audit.json', {'proposal_ref': proposal_ref, 'scope_ref': scope_ref,
    'actual_before': BEFORE, 'future_expected_registration': AFTER,
    'main38_execution_review_ref': review_ref, 'protected_files': len(protected), 'owned_source_paths': 8,
    'source_import_executed': False, 'Go_SQL_HTTP_models': 0, 'formal_increment': 0,
    'Python_actual_runtime_full_lifecycle_proven': False, 'filesystem_deadline': 'CHECKED_BETWEEN_CHUNKS_NOT_HARD_SYSCALL_TIMEOUT'})
print(json.dumps({'scope_ref': scope_ref, 'audit_ref': audit, 'protected_files': len(protected)}, ensure_ascii=True))
