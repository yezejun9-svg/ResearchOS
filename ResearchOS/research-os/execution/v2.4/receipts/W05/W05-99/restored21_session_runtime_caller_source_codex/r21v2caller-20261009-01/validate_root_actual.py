"""Root-only component validation. Never run during Source review."""
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
O = Path(C['validation_output'])
ISO = Path(C['isolation_output'])
CANONICAL = [R / 'execution/v2.4' / x for x in C['four_exact_current_canonical_refs']]
FIELDS = ('GoFiles', 'CgoFiles', 'CFiles', 'CXXFiles', 'MFiles', 'HFiles', 'FFiles', 'SFiles', 'SwigFiles',
          'SwigCXXFiles', 'SysoFiles', 'CompiledGoFiles', 'TestGoFiles', 'XTestGoFiles', 'EmbedFiles',
          'TestEmbedFiles', 'XTestEmbedFiles')


def pin(path):
    path = Path(path).resolve()
    data = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}


def exact(ref):
    actual = pin(ref['path'])
    assert actual['sha256'] == ref['sha256'] and ('bytes' not in ref or actual['bytes'] == ref['bytes']), ref['path']
    return actual


def unique(refs):
    result = {}
    for ref in refs:
        key = ref['path'].casefold()
        assert key not in result or result[key] == ref
        result[key] = ref
    return list(result.values())


def save(name, value):
    path = O / name
    with path.open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    return pin(path)


def module(path, data):
    mod = types.ModuleType('r21v2_validation_' + Path(path).stem)
    mod.__file__ = str(path)
    sys.modules[mod.__name__] = mod
    exec(compile(data, str(path), 'exec'), mod.__dict__)
    return mod


def main():
    assert len(sys.argv) == 13, 'expected exactly twelve typed Root arguments from contract.json'
    head, values = sys.argv[1], sys.argv[2:]
    assert re.fullmatch('[0-9a-f]{40}', head)
    assert all(re.fullmatch('[0-9a-f]{64}', values[i]) for i in (0, 3, 5, 7, 9))
    assert all(values[i].isdecimal() for i in (1, 2, 4, 6, 8, 10))
    assert Path(sys.executable).resolve() == Path(C['python']['path']).resolve()
    source_refs = [exact(C[name]) for name in ('h20_actual_review_handoff', 'h20_actual_review_manifest',
        'h20_actual_closed', 'h20_source_overlay', 'a21_v2_source_handoff', 'a21_v2_source_manifest',
        'a21_v2_review_handoff', 'a21_v2_review_manifest', 'a21_v2_overlay')]
    assert json.loads(Path(C['h20_actual_review_handoff']['path']).read_bytes())['status'] == 'COMPONENT_VALIDATION_ACCEPTED_A20_TO_PLAIN21_ONLY'
    assert json.loads(Path(C['a21_v2_review_handoff']['path']).read_bytes())['status'] == 'SOURCE_ACCEPTED_P2_ADDRESSED_PENDING_RUNTIME_QUALIFICATION'
    old_closed = json.loads(Path(C['h20_actual_closed']['path']).read_bytes())
    assert old_closed['source_count'] == 61 and old_closed['pass_count'] == 9 and old_closed['fail_count'] == 0
    source_old = json.loads(Path(C['h20_source_overlay']['path']).read_bytes())['sources']
    overlay = json.loads(Path(C['a21_v2_overlay']['path']).read_bytes())
    source_new = overlay['files']
    assert len(source_old) == C['expected_base_sources'] == 61
    assert set(source_new) == set(C['overlay_exact_paths']) and len(source_new) == 5
    assert set(overlay['changed_paths']) == {'internal/domain/backup_restored21_upgrade.go',
        'internal/domain/backup.go', 'internal/domain/backup_restored21_upgrade_test.go'}
    assert set(overlay['unchanged_paths']) == {'internal/domain/backup_upgrade.go', 'ops/backup/main.go'}
    assert len(set(source_new) - set(source_old)) == 2
    sources = {name: exact(ref) for name, ref in source_old.items()}
    sources.update({name: exact(ref) for name, ref in source_new.items()})
    assert len(sources) == C['expected_composed_sources'] == 63
    assert all(name.startswith(('internal/domain/', 'ops/backup/')) and name.endswith('.go') for name in sources)
    roster_path = Path(C['a21_v2_source_handoff']['path']).with_name('test-roster.json')
    roster = json.loads(roster_path.read_bytes())
    parents = roster['parent_tests']
    assert len(parents) == len(set(parents)) == C['expected_parents'] == 9
    assert len(roster['drift_subtests']) == 4
    drift_parent = 'TestRestored21RejectsForeignPartialSessionAndMissingFence'
    assert drift_parent in parents
    terminals = set(parents) | {drift_parent + '/' + name for name in roster['drift_subtests']}
    assert len(terminals) == C['expected_unique_test_runs'] == 13
    assert 'history20Fixture(t)' in Path(source_new['internal/domain/backup_restored21_upgrade_test.go']['path']).read_text(encoding='utf-8')
    assert 'UpgradeLocal(context.Background(),prior)' in Path(source_new['internal/domain/backup_restored21_upgrade_test.go']['path']).read_text(encoding='utf-8')
    assert 'if len(before["schema_migrations"])!=21' in Path(source_new['internal/domain/backup_restored21_upgrade_test.go']['path']).read_text(encoding='utf-8')
    expected = [
        {'path': str(CANONICAL[0]), 'sha256': values[0], 'bytes': int(values[1])},
        {'path': str(CANONICAL[1]), 'sha256': values[3], 'bytes': int(values[4])},
        {'path': str(CANONICAL[2]), 'sha256': values[5], 'bytes': int(values[6])},
        {'path': str(CANONICAL[3]), 'sha256': values[7], 'bytes': int(values[8])},
    ]
    before = {p: p.read_bytes() for p in CANONICAL}
    assert [exact(ref) for ref in expected] == [pin(p) for p in CANONICAL]
    assert json.loads(before[CANONICAL[0]])['revision'] == int(values[2])
    isolation_ref = exact({'path': str(ISO / 'isolation.ready.json'), 'sha256': values[9], 'bytes': int(values[10])})
    isolated = json.loads(Path(isolation_ref['path']).read_bytes())
    assert isolated['status'] == 'DETACHED_CANDIDATE_WORKTREE_READY_NO_SOURCE_OVERLAY'
    assert isolated['head'] == head and Path(isolated['worktree_root']).resolve() == T.resolve()
    assert isolated['canonical_refs'] == expected and isolated['all_owned_jobs_closed'] is True
    assert isolated['source_overlay'] is False and isolated['Main_canonical_unchanged'] is True
    assert not O.exists()
    assert O.resolve().is_relative_to((R / 'execution/v2.4/receipts/W05/W05-99/integration_codex').resolve())
    O.mkdir(parents=True)
    save('canonical.pre-run.exact.json', {'refs': expected, 'revision': int(values[2]), 'formal_acceptance': False})
    main_paths = ('go.mod', 'go.sum', 'internal/domain/client_workspace_test.go',
                  'internal/domain/client_protocol_goal_test.go', 'internal/domain/runtime_permission_windows_test.go',
                  'internal/domain/runtime_tool_integration_windows_test.go', 'internal/domain/runtime_session_events_windows_test.go',
                  'internal/domain/store.go')
    main_before = {R / rel: (R / rel).read_bytes() for rel in main_paths}
    gp, hp, go, node, mu, test2json = [exact(C[k]) for k in ('source_guard', 'owned_job', 'go', 'node', 'mu_bundle', 'test2json')]
    fmt = pin(Path(go['path']).with_name('gofmt.exe'))
    inputs = unique(source_refs + [exact(C['python']), isolation_ref, pin(__file__), pin(N / 'contract.json'),
        pin(roster_path), gp, hp, go, fmt, node, mu, test2json, *sources.values(),
        *[pin(p) for p in main_before], *expected, pin(R / 'execution/project_identity.json'),
        pin(Path(go['path']).parent.parent / 'VERSION'), pin(Path(go['path']).parent.parent / 'src/go.mod')])
    gm = module(gp['path'], Path(gp['path']).read_bytes())
    input_guard = gm.SourceReadGuard(per_file_cap=256 * 1024 * 1024, total_cap=2 * 1024 * 1024 * 1024)
    input_guard.acquire(inputs)
    runtime_guard = candidate_guard = compiler_guard = binary_guard = None
    invocations, jobs, actions, started = [], [], {}, set()
    formatted_ref = inventory_ref = overlay_ref = binary = None
    try:
        helper = module(hp['path'], input_guard.get_buffer(hp['path']))
        runtime_guard = gm.SourceReadGuard(per_file_cap=256 * 1024 * 1024, total_cap=2 * 1024 * 1024 * 1024)
        runtime_guard.acquire(unique([pin(p) for p in helper.runtime_resource_paths()]))
        scratch = Path(C['environment']) / 'validation'
        assert not scratch.exists()
        for sub in ('profile', 'temp', 'programs'):
            (scratch / sub).mkdir(parents=True)
        evidence = scratch / 'typed-child-evidence'
        assert not evidence.exists()
        env = {'SystemRoot': 'C:/Windows', 'WINDIR': 'C:/Windows', 'ComSpec': 'C:/Windows/System32/cmd.exe',
            'PATH': str(Path(go['path']).parent) + ';C:/Windows/System32', 'PATHEXT': '.COM;.EXE;.BAT;.CMD',
            'USERPROFILE': str(scratch / 'profile'), 'LOCALAPPDATA': str(scratch / 'profile'),
            'APPDATA': str(scratch / 'profile'), 'TEMP': str(scratch / 'temp'), 'TMP': str(scratch / 'temp'),
            'GOROOT': str(Path(go['path']).parent.parent), 'GOPATH': str(R / '.local/gopath'),
            'GOCACHE': str(R / '.local/gocache'), 'GOENV': 'off', 'GOTOOLCHAIN': 'local', 'GOPROXY': 'off',
            'GOSUMDB': 'off', 'GOWORK': 'off', 'CGO_ENABLED': '0', 'GOFLAGS': '-mod=readonly -p=1',
            'GOMAXPROCS': '2', 'RESEARCHOS_GO': go['path'], 'RESEARCHOS_NODE': node['path'],
            'RESEARCHOS_MU_BUNDLE': mu['path'], 'RESEARCHOS_TEST2JSON': test2json['path'],
            'RESEARCHOS_TEST2JSON_SHA256': test2json['sha256'], 'RESEARCHOS_TYPED_RUNTIME_EVIDENCE_DIR': str(evidence)}

        def invoke(label, argv, wall, cwd=T):
            out, err = O / (label + '.stdout.raw'), O / (label + '.stderr.raw')
            result, exception = None, None
            try:
                with out.open('xb') as stdout, err.open('xb') as stderr:
                    result = helper.run_owned(argv, str(cwd), env, stdout, stderr, wall, creation_flags=0x08000000)
            except BaseException as caught:
                exception = repr(caught)
            finally:
                ref = save(label + '.invocation.json', {'argv': argv, 'cwd': str(cwd), 'public_environment': env,
                    'result': result, 'exception': exception, 'actual_native_exit': result.get('actual_exit') if result else None,
                    'stdout_ref': pin(out), 'stderr_ref': pin(err), 'external_model_requests': 0,
                    'original_trial_provider_requests': None, 'production_DB_writes': 0})
                invocations.append(ref)
                print(json.dumps({'progress': label, 'receipt_ref': ref}), flush=True)
            assert exception is None and result is not None and not result['timed_out'] and result['error'] is None, label
            cleanup = result['job_cleanup']
            closed = (not cleanup['errors'] and cleanup['active_processes_last_observed'] == 0 and
                      all(cleanup[k] for k in ('unnamed_exclusive_job', 'kill_on_job_close_configured',
                          'assigned_before_resume', 'primary_exit_confirmed', 'job_idle_confirmed', 'handles_closed')))
            jobs.append(closed)
            assert closed, label + ' owned job not fully closed'
            return result

        def success(label, argv, wall, cwd=T):
            result = invoke(label, argv, wall, cwd)
            assert result['actual_exit'] == 0, label + ' actual exit nonzero'
            return result

        def closed(status, error=None):
            assert all(p.read_bytes() == raw for p, raw in before.items())
            assert all(p.read_bytes() == raw for p, raw in main_before.items())
            ref = save('validation.closed.json', {'status': status, 'error': error, 'source_count': len(sources),
                'source_overlay_ref': overlay_ref, 'formatted_source_ref': formatted_ref,
                'compiler_inventory_ref': inventory_ref, 'compiled_test_ref': pin(binary) if binary and binary.is_file() else None,
                'exact_parent_names': parents, 'expected_terminal_names': sorted(terminals),
                'started_names': sorted(started), 'actions': actions,
                'pass_count': sum(a == 'pass' for a in actions.values()),
                'fail_count': sum(a == 'fail' for a in actions.values()),
                'skip_count': sum(a == 'skip' for a in actions.values()),
                'invocation_refs': invocations, 'all_owned_jobs_closed': all(jobs),
                'canonical_refs': expected, 'Main_canonical_unchanged': True, 'Main_adopted': False,
                'component_scope': C['component_scope'], 'genuine21_22_release_program_provenance': 'OPEN',
                'public_late_failure_no_publication': 'OPEN', 'overall20to24': 'OPEN', 'formal_acceptance': False,
                'original_trial_DB_touched': False, 'external_model_requests': 0,
                'original_trial_provider_requests': None, 'descendant_test_binary_exit': None})
            print(json.dumps({'closed_ref': ref, 'status': status}), flush=True)

        for name, ref in sources.items():
            target = T / name
            assert target.resolve().is_relative_to(T.resolve()) and not target.is_symlink()
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(input_guard.get_buffer(ref['path']))
        overlay_ref = save('source-overlay.json', {'sources': sources, 'Source_count': len(sources),
            'h20_accepted_actual_ref': exact(C['h20_actual_review_handoff']),
            'a21_v2_independent_source_ref': exact(C['a21_v2_review_handoff']),
            'Main_adopted': False})
        success('format', [fmt['path'], '-w', *[str(T / name) for name in sources if name.endswith('.go')]], 45)
        formatted = [pin(T / name) for name in sources]
        formatted_ref = save('formatted.source-members.json', formatted)
        candidate_guard = gm.SourceReadGuard(per_file_cap=256 * 1024 * 1024, total_cap=2 * 1024 * 1024 * 1024)
        candidate_guard.acquire(formatted + [formatted_ref])
        success('tagged-compiler-input-list', [go['path'], 'list', '-test', '-deps', '-compiled',
            '-tags=researchos_native_recovery_harness', '-json', './internal/domain'], 240)
        raw = (O / 'tagged-compiler-input-list.stdout.raw').read_text(encoding='utf-8')
        decoder, pos, packages, build_inputs, embeds = json.JSONDecoder(), 0, [], {}, []
        while pos < len(raw):
            while pos < len(raw) and raw[pos].isspace():
                pos += 1
            if pos == len(raw):
                break
            pkg, pos = decoder.raw_decode(raw, pos)
            assert not pkg.get('Error') and not pkg.get('DepsErrors')
            packages.append(pkg.get('ImportPath'))
            if not pkg.get('Dir'):
                continue
            directory = Path(pkg['Dir'])
            for field in FIELDS:
                for name in pkg.get(field, []):
                    path = Path(name)
                    path = path if path.is_absolute() else directory / path
                    ref = pin(path)
                    build_inputs[ref['path']] = ref
                    if field.endswith('EmbedFiles'):
                        embeds.append({'package': pkg['ImportPath'], 'field': field, 'ref': ref})
        assert packages and build_inputs
        product = {}
        for relative in ('apps/control', 'internal', 'adapters', 'evaluation', 'ops', 'migrations/sqlite', 'spec/v2.0/contracts'):
            for path in (T / relative).rglob('*'):
                assert not path.is_symlink()
                if path.is_file():
                    ref = pin(path)
                    product[ref['path']] = ref
        for relative in ('go.mod', 'go.sum', 'execution/toolchains/locked.json'):
            ref = pin(T / relative)
            product[ref['path']] = ref
        compiler_tools = [pin(p) for p in (Path(go['path']).parent.parent / 'pkg/tool/windows_amd64').iterdir() if p.is_file()]
        inventory_ref = save('actual-tagged-compiler-input-inventory.json', {'package_count': len(packages),
            'packages': packages, 'build_inputs': list(build_inputs.values()), 'product_inventory': list(product.values()),
            'compiler_tool_refs': compiler_tools, 'GoRef': go, 'actual_embed_files': embeds,
            'includes_actual_test_and_embed_inputs': True, 'build_tag': 'researchos_native_recovery_harness',
            'test2json_executable_ref': test2json, 'Root_component_only': True})
        test_source = str(T / 'internal/domain/backup_restored21_upgrade_test.go')
        assert any(ref['path'].casefold() == test_source.casefold() for ref in build_inputs.values())
        compiler_guard = gm.SourceReadGuard(per_file_cap=256 * 1024 * 1024, total_cap=2 * 1024 * 1024 * 1024)
        compiler_guard.acquire(unique([*build_inputs.values(), *product.values(), *compiler_tools, go, inventory_ref]))
        binary = scratch / 'programs/restored21-v2-component.test.exe'
        success('tagged-test-binary-compile', [go['path'], 'test', '-c', '-tags=researchos_native_recovery_harness',
            '-trimpath', '-buildvcs=false', '-o', str(binary), './internal/domain'], 240)
        binary_guard = gm.SourceReadGuard(per_file_cap=256 * 1024 * 1024, total_cap=2 * 1024 * 1024 * 1024)
        binary_guard.acquire([pin(binary), test2json])
        selector = '^(' + '|'.join(sorted(parents)) + ')$'
        result = invoke('restored21-v2-nine-parent-jsonl', [test2json['path'], '-p',
            'researchos.local/research-os/internal/domain', '-t', str(binary), '-test.v=test2json',
            '-test.run=' + selector, '-test.count=1', '-test.timeout=14m'], 900, T / 'internal/domain')
        events = [json.loads(line) for line in (O / 'restored21-v2-nine-parent-jsonl.stdout.raw').read_text(encoding='utf-8').splitlines()]
        assert events and not (O / 'restored21-v2-nine-parent-jsonl.stderr.raw').read_bytes()
        for event in events:
            assert event['Package'] == 'researchos.local/research-os/internal/domain'
            name = event.get('Test')
            if not name:
                continue
            assert name in terminals
            if event['Action'] == 'run':
                assert name not in started
                started.add(name)
            elif event['Action'] in ('pass', 'fail', 'skip'):
                assert name in started and name not in actions
                actions[name] = event['Action']
        assert result['actual_exit'] == 0 and started == set(actions) == terminals
        assert len(actions) == 13 and all(action == 'pass' for action in actions.values())
        assert events[-1]['Action'] == 'pass' and 'Test' not in events[-1]
        closed('COMPONENT_A20_TO_PLAIN21_TO_SESSION_READY21_TO22_WITH_REPORT_DISK_EQUALITY_PASSED')
    except BaseException as err:
        if not (O / 'validation.closed.json').exists():
            closed('FAILED_RESTORED21_V2_COMPONENT_ACTUAL_CLOSED', repr(err))
        raise
    finally:
        for guard, name in ((binary_guard, 'binary'), (compiler_guard, 'compiler'),
                            (candidate_guard, 'candidate'), (runtime_guard, 'runtime'), (input_guard, 'input')):
            if guard is not None:
                cleanup = guard.close()
                save(name + '-source-guard.cleanup.actual.json', cleanup)
                assert cleanup['closed'] and not cleanup['errors'] and cleanup['retained_handles_count'] == 0


if __name__ == '__main__':
    try:
        main()
    except BaseException:
        print('SOURCE_PYTHON_EXIT=1', flush=True)
        raise
    print('SOURCE_PYTHON_EXIT=0', flush=True)
