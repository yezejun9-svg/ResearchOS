"""Root-only candidate isolation. Source preparation must not execute this file."""
import hashlib
import json
import re
import sys
import types
from pathlib import Path

sys.dont_write_bytecode = True
N = Path(__file__).resolve().parent
C = json.loads((N / 'contract.json').read_bytes())
R = Path(C['repository'])
T = Path(C['worktree'])
O = Path(C['isolation_output'])
CANONICAL = [R / 'execution/v2.4' / x for x in C['four_exact_current_canonical_refs']]


def pin(path):
    path = Path(path).resolve()
    data = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}


def exact(ref):
    actual = pin(ref['path'])
    assert actual['sha256'] == ref['sha256'] and ('bytes' not in ref or actual['bytes'] == ref['bytes']), ref['path']
    return actual


def save(name, value):
    path = O / name
    with path.open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    return pin(path)


def module(path, data):
    mod = types.ModuleType('r21v2_isolation_' + Path(path).stem)
    mod.__file__ = str(path)
    sys.modules[mod.__name__] = mod
    exec(compile(data, str(path), 'exec'), mod.__dict__)
    return mod


def main():
    assert len(sys.argv) == 11, 'expected exactly ten typed Root arguments from contract.json'
    head = sys.argv[1]
    assert re.fullmatch('[0-9a-f]{40}', head)
    values = sys.argv[2:]
    assert all(re.fullmatch('[0-9a-f]{64}', values[i]) for i in (0, 3, 5, 7))
    assert all(values[i].isdecimal() for i in (1, 2, 4, 6, 8))
    assert all(int(values[i]) > 0 for i in (1, 2, 4, 6, 8))
    assert Path(sys.executable).resolve() == Path(C['python']['path']).resolve()
    exact(C['python'])
    expected = [
        {'path': str(CANONICAL[0]), 'sha256': values[0], 'bytes': int(values[1])},
        {'path': str(CANONICAL[1]), 'sha256': values[3], 'bytes': int(values[4])},
        {'path': str(CANONICAL[2]), 'sha256': values[5], 'bytes': int(values[6])},
        {'path': str(CANONICAL[3]), 'sha256': values[7], 'bytes': int(values[8])},
    ]
    before = {p: p.read_bytes() for p in CANONICAL}
    assert [exact(v) for v in expected] == [pin(p) for p in CANONICAL]
    checkpoint_revision = json.loads(before[CANONICAL[0]])['revision']
    ownership_revision = json.loads(before[CANONICAL[1]])['revision']
    assert type(checkpoint_revision) is int and checkpoint_revision > 0 and checkpoint_revision == int(values[2])
    assert type(ownership_revision) is int and ownership_revision > 0
    assert not T.exists() and not O.exists()
    assert T.resolve().is_relative_to((R / '.local/worktrees').resolve())
    assert O.resolve().is_relative_to((R / 'execution/v2.4/receipts/W05/W05-99/integration_codex').resolve())
    O.mkdir(parents=True)
    save('canonical.pre-run.exact.json', {'refs': expected, 'revision': int(values[2]), 'formal_acceptance': False})
    git = Path('C:/Program Files/Git/cmd/git.exe')
    gp, hp = exact(C['source_guard']), exact(C['owned_job'])
    frozen = [pin(__file__), pin(N / 'contract.json'), pin(N / 'HDF.json'), pin(N / 'MF.json'),
              exact(C['exact_source_roster']), pin(git), pin(R / 'execution/project_identity.json'),
              *expected, gp, hp, exact(C['python'])]
    for relative in ('go.mod', 'go.sum', 'internal/domain/store.go', 'internal/domain/runtime_coordinator_windows.go', 'internal/domain/backup_migration.go'):
        frozen.append(pin(R / relative))
    for mod in list(sys.modules.values()):
        for field in ('__file__', '__cached__'):
            candidate = getattr(mod, field, None)
            if candidate and Path(candidate).is_file():
                frozen.append(pin(candidate))
    gm = module(gp['path'], Path(gp['path']).read_bytes())
    guard = gm.SourceReadGuard(per_file_cap=256 * 1024 * 1024, total_cap=2 * 1024 * 1024 * 1024)
    runtime_guard = None
    ready_payload = None
    cleanup_refs = []
    cleanup_ok = True
    jobs = []
    try:
        guard.acquire(list({x['path'].casefold(): x for x in frozen}.values()))
        helper = module(hp['path'], guard.get_buffer(hp['path']))
        runtime_guard = gm.SourceReadGuard(per_file_cap=256 * 1024 * 1024, total_cap=2 * 1024 * 1024 * 1024)
        runtime_guard.acquire([pin(p) for p in helper.runtime_resource_paths()])
        scratch = Path(C['environment']) / 'isolation'
        assert not scratch.exists()
        for sub in ('profile', 'temp', 'empty-hooks'):
            (scratch / sub).mkdir(parents=True)
        env = {'SystemRoot': 'C:/Windows', 'WINDIR': 'C:/Windows', 'ComSpec': 'C:/Windows/System32/cmd.exe',
               'PATH': str(git.parent) + ';C:/Windows/System32', 'PATHEXT': '.COM;.EXE;.BAT;.CMD',
               'USERPROFILE': str(scratch / 'profile'), 'LOCALAPPDATA': str(scratch / 'profile'),
               'APPDATA': str(scratch / 'profile'), 'TEMP': str(scratch / 'temp'), 'TMP': str(scratch / 'temp'),
               'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': 'NUL', 'GIT_TERMINAL_PROMPT': '0'}
        invocations = []

        def invoke(label, argv, wall, cwd=R):
            stdout_path, stderr_path = O / (label + '.stdout.raw'), O / (label + '.stderr.raw')
            result, exception = None, None
            try:
                with stdout_path.open('xb') as stdout, stderr_path.open('xb') as stderr:
                    result = helper.run_owned(argv, str(cwd), env, stdout, stderr, wall, creation_flags=0x08000000)
            except BaseException as err:
                exception = repr(err)
            finally:
                ref = save(label + '.invocation.json', {'argv': argv, 'cwd': str(cwd), 'public_environment': env,
                    'result': result, 'exception': exception, 'actual_native_exit': result.get('actual_exit') if result else None,
                    'stdout_ref': pin(stdout_path), 'stderr_ref': pin(stderr_path), 'external_model_requests': 0,
                    'original_trial_provider_requests': None})
                invocations.append(ref)
                print(json.dumps({'progress': label, 'receipt_ref': ref}), flush=True)
            cleanup = result.get('job_cleanup', {}) if isinstance(result, dict) else {}
            closed = (exception is None and bool(result) and not cleanup.get('errors') and
                      cleanup.get('active_processes_last_observed') == 0 and
                      all(cleanup.get(k) is True for k in ('unnamed_exclusive_job', 'kill_on_job_close_configured',
                          'assigned_before_resume', 'primary_exit_confirmed', 'job_idle_confirmed', 'handles_closed')))
            jobs.append({'label': label, 'invocation_ref': ref, 'closed': bool(closed)})
            assert exception is None and result is not None and result['actual_exit'] == 0 and not result['timed_out'] and result['error'] is None and closed, label
            return ref

        invoke('head-before', [str(git), 'rev-parse', 'HEAD'], 30)
        assert (O / 'head-before.stdout.raw').read_text(encoding='utf-8').strip() == head
        invoke('tracked-status', [str(git), '--no-optional-locks', 'status', '--porcelain=v1', '--untracked-files=no'], 30)
        tracked = (O / 'tracked-status.stdout.raw').read_text(encoding='utf-8').splitlines()
        invoke('staged-status', [str(git), '--no-optional-locks', 'diff', '--cached', '--name-only'], 30)
        assert not (O / 'staged-status.stdout.raw').read_bytes().strip()
        invoke('create-worktree', [str(git), '-c', 'core.hooksPath=' + str(scratch / 'empty-hooks'),
                                  'worktree', 'add', '--no-checkout', '--detach', str(T), head], 180)
        dotgit = (T / '.git').read_text(encoding='utf-8').strip()
        assert dotgit.startswith('gitdir: ')
        metadata = Path(dotgit[8:]).resolve()
        assert metadata.is_relative_to((R / '.git/worktrees').resolve())
        assert (metadata / 'gitdir').read_text(encoding='utf-8').strip().replace('\\', '/').casefold() == str(T / '.git').replace('\\', '/').casefold()
        sparse = metadata / 'info/sparse-checkout'
        assert not sparse.exists()
        sparse.parent.mkdir(exist_ok=True)
        product_dirs = ('adapters', 'apps', 'bootstrap', 'contracts', 'docs', 'evaluation', 'internal', 'migrations',
                        'ops', 'qualification', 'release', 'scripts', 'spec', 'tests', 'third_party')
        patterns = '/*\n!/*/\n' + ''.join('/' + name + '/\n' for name in product_dirs) + '/execution/\n!/execution/*/\n/execution/toolchains/\n'
        with sparse.open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(patterns)
        sparse_ref = save('sparse-checkout.patterns.public.json', {'worktree': str(T), 'metadata': str(metadata),
            'pattern_ref': pin(sparse), 'patterns': patterns, 'excluded_history_receipts': True,
            'shared_git_config_mutated': False})
        invoke('checkout-product-source', [str(git), '-C', str(T), '-c', 'core.hooksPath=' + str(scratch / 'empty-hooks'),
               '-c', 'core.sparseCheckout=true', '-c', 'core.sparseCheckoutCone=false', 'read-tree', '-mu', 'HEAD'], 180)
        assert not (T / 'execution/v2.4/receipts').exists() and not (T / 'execution/verifier').exists()
        assert (T / 'execution/toolchains/locked.json').is_file()
        assert all((T / name).is_dir() for name in product_dirs)
        invoke('head-after', [str(git), 'rev-parse', 'HEAD'], 30)
        assert (O / 'head-after.stdout.raw').read_text(encoding='utf-8').strip() == head
        assert all(p.read_bytes() == raw for p, raw in before.items())
        assert all(pin(v['path']) == v for v in frozen)
        ready_payload = {'status': 'DETACHED_CANDIDATE_WORKTREE_READY_NO_SOURCE_OVERLAY',
            'repository_root': str(R), 'worktree_root': str(T), 'head': head, 'canonical_refs': expected,
            'invocation_refs': invocations, 'sparse_checkout_ref': sparse_ref, 'tracked_dirty_paths': tracked,
            'staged_index_empty': True, 'source_overlay': False,
            'Main_canonical_unchanged': True, 'provider_requests': 0, 'formal_acceptance': False}
    finally:
        for g, name in ((runtime_guard, 'runtime'), (guard, 'input')):
            if g is not None:
                try:
                    cleanup = g.close()
                except BaseException as error:
                    cleanup = {'closed': False, 'errors': [repr(error)], 'retained_handles_count': None}
                cleanup_refs.append(save(name + '-source-guard.cleanup.actual.json', cleanup))
                cleanup_ok = cleanup_ok and cleanup['closed'] is True and not cleanup['errors'] and cleanup['retained_handles_count'] == 0
    assert len(cleanup_refs) == 2 and cleanup_ok
    assert len(jobs) == len(invocations) == 6 and all(item['closed'] is True for item in jobs)
    cleanup_ref = save('isolation.cleanup.closed.json', {'guard_refs': cleanup_refs, 'jobs': jobs,
        'all_guards_closed': cleanup_ok, 'all_owned_jobs_closed': True, 'canonical_refs': expected})
    assert ready_payload is not None and all(p.read_bytes() == raw for p, raw in before.items())
    ready_payload['all_owned_jobs_closed'] = True
    ready_payload['cleanup_closed_ref'] = cleanup_ref
    ready = save('isolation.ready.json', ready_payload)
    print(json.dumps({'ready_ref': ready, 'owned_jobs': len(jobs)}), flush=True)


if __name__ == '__main__':
    try:
        main()
    except BaseException:
        print('SOURCE_PYTHON_EXIT=1', flush=True)
        raise
    print('SOURCE_PYTHON_EXIT=0', flush=True)
