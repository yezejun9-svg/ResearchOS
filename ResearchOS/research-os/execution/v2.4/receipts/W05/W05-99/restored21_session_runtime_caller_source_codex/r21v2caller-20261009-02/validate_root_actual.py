"""Root-only component validation. Never run during Source review."""
import hashlib
import json
import re
import sys
import types
from pathlib import Path, PurePosixPath

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
    assert all(int(values[i]) > 0 for i in (1, 2, 4, 6, 8, 10))
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
    roster_ref = exact(C['exact_source_roster'])
    reviewed_roster = json.loads(Path(roster_ref['path']).read_bytes())
    assert reviewed_roster['composed_count'] == 63 and reviewed_roster['sources'] == sources
    for name in sources:
        relative = PurePosixPath(name)
        assert name == relative.as_posix() and not relative.is_absolute() and len(relative.parts) >= 2
        assert all(part not in ('', '.', '..') for part in relative.parts)
        assert '\\' not in name and ':' not in name and '\0' not in name
        assert (T / name).resolve().is_relative_to(T.resolve())
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
    checkpoint_revision = json.loads(before[CANONICAL[0]])['revision']
    ownership_revision = json.loads(before[CANONICAL[1]])['revision']
    assert type(checkpoint_revision) is int and checkpoint_revision > 0 and checkpoint_revision == int(values[2])
    assert type(ownership_revision) is int and ownership_revision > 0
    isolation_ref = exact({'path': str(ISO / 'isolation.ready.json'), 'sha256': values[9], 'bytes': int(values[10])})
    isolated = json.loads(Path(isolation_ref['path']).read_bytes())
    assert isolated['status'] == 'DETACHED_CANDIDATE_WORKTREE_READY_NO_SOURCE_OVERLAY'
    assert isolated['head'] == head and Path(isolated['worktree_root']).resolve() == T.resolve()
    assert isolated['canonical_refs'] == expected and isolated['all_owned_jobs_closed'] is True
    assert isolated['source_overlay'] is False and isolated['Main_canonical_unchanged'] is True
    preparation_cleanup_ref = exact(isolated['cleanup_closed_ref'])
    preparation_cleanup = json.loads(Path(preparation_cleanup_ref['path']).read_bytes())
    assert preparation_cleanup['canonical_refs'] == expected
    assert preparation_cleanup['all_guards_closed'] is True and preparation_cleanup['all_owned_jobs_closed'] is True
    assert len(preparation_cleanup['guard_refs']) == 2 and len(preparation_cleanup['jobs']) == 6
    assert all(exact(ref) == ref for ref in preparation_cleanup['guard_refs'])
    assert all(item['closed'] is True for item in preparation_cleanup['jobs'])
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
    inputs = unique(source_refs + [exact(C['python']), isolation_ref, preparation_cleanup_ref,
        *[exact(ref) for ref in preparation_cleanup['guard_refs']],
        roster_ref, pin(__file__), pin(N / 'contract.json'), pin(N / 'HDF.json'), pin(N / 'MF.json'),
        pin(roster_path), gp, hp, go, fmt, node, mu, test2json, *sources.values(),
        *[pin(p) for p in main_before], *expected, pin(R / 'execution/project_identity.json'),
        pin(Path(go['path']).parent.parent / 'VERSION'), pin(Path(go['path']).parent.parent / 'src/go.mod')])
    gm = module(gp['path'], Path(gp['path']).read_bytes())
    input_guard = gm.SourceReadGuard(per_file_cap=256 * 1024 * 1024, total_cap=2 * 1024 * 1024 * 1024)
    runtime_guard = candidate_guard = compiler_guard = binary_guard = evidence_guard = None
    invocations, jobs, actions, started = [], [], {}, set()
    formatted_ref = inventory_ref = overlay_ref = binary = typed_evidence_ref = None
    phase_error = None
    guard_cleanup_refs = []
    all_guards_closed = True
    actual_test_jsonl_primary_ref = None
    development_tests_observed = False
    try:
        input_guard.acquire(inputs)
        helper = module(hp['path'], input_guard.get_buffer(hp['path']))
        runtime_guard = gm.SourceReadGuard(per_file_cap=256 * 1024 * 1024, total_cap=2 * 1024 * 1024 * 1024)
        runtime_guard.acquire(unique([pin(p) for p in helper.runtime_resource_paths()]))
        scratch = Path(C['environment']) / 'validation'
        assert not scratch.exists()
        for sub in ('profile', 'temp', 'programs', 'gocache'):
            (scratch / sub).mkdir(parents=True)
        evidence = scratch / 'typed-child-evidence'
        assert not evidence.exists()
        env = {'SystemRoot': 'C:/Windows', 'WINDIR': 'C:/Windows', 'ComSpec': 'C:/Windows/System32/cmd.exe',
            'PATH': str(Path(go['path']).parent) + ';C:/Windows/System32', 'PATHEXT': '.COM;.EXE;.BAT;.CMD',
            'USERPROFILE': str(scratch / 'profile'), 'LOCALAPPDATA': str(scratch / 'profile'),
            'APPDATA': str(scratch / 'profile'), 'TEMP': str(scratch / 'temp'), 'TMP': str(scratch / 'temp'),
            'GOROOT': str(Path(go['path']).parent.parent), 'GOPATH': str(R / '.local/gopath'),
            'GOCACHE': str(scratch / 'gocache'), 'GOENV': 'off', 'GOTOOLCHAIN': 'local', 'GOPROXY': 'off',
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
                primary_pid = result.get('owned_child_pid') if isinstance(result, dict) else None
                primary_filetime = result.get('creation_time_100ns') if isinstance(result, dict) else None
                typed_primary = ({'pid_decimal': str(primary_pid), 'creation_filetime_100ns_decimal': str(primary_filetime)}
                                 if type(primary_pid) is int and primary_pid > 0 and
                                    type(primary_filetime) is int and primary_filetime > 0 else None)
                ref = save(label + '.invocation.json', {'argv': argv, 'cwd': str(cwd), 'public_environment': env,
                    'result': result, 'exception': exception, 'actual_native_exit': result.get('actual_exit') if result else None,
                    'typed_primary_identity': typed_primary,
                    'stdout_ref': pin(out), 'stderr_ref': pin(err), 'external_model_requests': 0,
                    'original_trial_provider_requests': None, 'production_DB_writes': 0})
                invocations.append(ref)
                print(json.dumps({'progress': label, 'receipt_ref': ref}), flush=True)
            cleanup = result.get('job_cleanup', {}) if isinstance(result, dict) else {}
            closed = (exception is None and result is not None and not cleanup.get('errors') and
                      cleanup.get('active_processes_last_observed') == 0 and
                      all(cleanup.get(k) is True for k in ('unnamed_exclusive_job', 'kill_on_job_close_configured',
                          'assigned_before_resume', 'primary_exit_confirmed', 'job_idle_confirmed', 'handles_closed')))
            jobs.append({'label': label, 'invocation_ref': ref, 'closed': bool(closed),
                         'primary_identity_observed': typed_primary is not None})
            assert exception is None and result is not None and not result['timed_out'] and result['error'] is None and closed, label
            return result

        def success(label, argv, wall, cwd=T):
            result = invoke(label, argv, wall, cwd)
            assert result['actual_exit'] == 0, label + ' actual exit nonzero'
            return result

        def closed(status, error=None):
            canonical_unchanged = all(p.read_bytes() == raw for p, raw in before.items())
            main_unchanged = all(p.read_bytes() == raw for p, raw in main_before.items())
            jobs_closed = bool(jobs) and all(item['closed'] is True for item in jobs)
            ref = save('validation.closed.json', {'status': status, 'error': error, 'source_count': len(sources),
                'source_overlay_ref': overlay_ref, 'formatted_source_ref': formatted_ref,
                'compiler_inventory_ref': inventory_ref, 'compiled_test_ref': pin(binary) if binary and binary.is_file() else None,
                'exact_parent_names': parents, 'expected_terminal_names': sorted(terminals),
                'started_names': sorted(started), 'actions': actions,
                'pass_count': sum(a == 'pass' for a in actions.values()),
                'fail_count': sum(a == 'fail' for a in actions.values()),
                'skip_count': sum(a == 'skip' for a in actions.values()),
                'invocation_refs': invocations, 'jobs': jobs, 'all_owned_jobs_closed': jobs_closed,
                'guard_cleanup_refs': guard_cleanup_refs, 'all_guards_closed': all_guards_closed,
                'preparation_cleanup_ref': preparation_cleanup_ref,
                'actual_test_jsonl_primary_ref': actual_test_jsonl_primary_ref,
                'typed_fixture_evidence_inventory_ref': typed_evidence_ref,
                'canonical_refs': expected, 'canonical_unchanged': canonical_unchanged,
                'Main_8_guarded_files_unchanged': main_unchanged, 'Main_adopted': False,
                'component_scope': C['component_scope'], 'genuine21_22_release_program_provenance': 'OPEN',
                'public_late_failure_no_publication': 'OPEN', 'overall20to24': 'OPEN', 'formal_acceptance': False,
                'original_trial_DB_touched': False, 'external_model_requests': 0,
                'original_trial_provider_requests': None, 'descendant_test_binary_exit': None,
                'individual_descendant_PID_FILETIME_and_raw_streams': None,
                'native_qualification_accepted': False, 'component_validation_accepted': False})
            print(json.dumps({'closed_ref': ref, 'status': status}), flush=True)
            return ref

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
        success('tagged-compiler-input-list', [go['path'], 'list', '-export', '-test', '-deps', '-compiled',
            '-tags=researchos_native_recovery_harness', '-json', './internal/domain'], 600)
        raw = (O / 'tagged-compiler-input-list.stdout.raw').read_text(encoding='utf-8')
        decoder, pos, packages, build_inputs, embeds = json.JSONDecoder(), 0, [], {}, []
        exports, module_manifests = {}, {}
        while pos < len(raw):
            while pos < len(raw) and raw[pos].isspace():
                pos += 1
            if pos == len(raw):
                break
            pkg, pos = decoder.raw_decode(raw, pos)
            assert not pkg.get('Error') and not pkg.get('DepsErrors')
            packages.append(pkg.get('ImportPath'))
            if pkg.get('Export'):
                ref = pin(pkg['Export'])
                exports[ref['path']] = ref
            module = pkg.get('Module')
            if isinstance(module, dict) and module.get('GoMod'):
                ref = pin(module['GoMod'])
                module_manifests[ref['path']] = ref
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
        assert packages and build_inputs and exports and module_manifests
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
            'export_refs': list(exports.values()), 'module_go_mod_refs': list(module_manifests.values()),
            'fresh_private_GOCACHE': str(scratch / 'gocache'),
            'includes_actual_test_embed_export_and_module_inputs': True, 'build_tag': 'researchos_native_recovery_harness',
            'test2json_executable_ref': test2json, 'Root_component_only': True})
        test_source = str(T / 'internal/domain/backup_restored21_upgrade_test.go')
        assert any(ref['path'].casefold() == test_source.casefold() for ref in build_inputs.values())
        compiler_guard = gm.SourceReadGuard(per_file_cap=256 * 1024 * 1024, total_cap=2 * 1024 * 1024 * 1024)
        compiler_guard.acquire(unique([*build_inputs.values(), *product.values(), *exports.values(),
            *module_manifests.values(), *compiler_tools, go, inventory_ref]))
        binary = scratch / 'programs/restored21-v2-component.test.exe'
        success('tagged-test-binary-compile', [go['path'], 'test', '-c', '-tags=researchos_native_recovery_harness',
            '-trimpath', '-buildvcs=false', '-o', str(binary), './internal/domain'], 600)
        binary_guard = gm.SourceReadGuard(per_file_cap=256 * 1024 * 1024, total_cap=2 * 1024 * 1024 * 1024)
        binary_guard.acquire([pin(binary), test2json])
        selector = '^(' + '|'.join(sorted(parents)) + ')$'
        result = invoke('restored21-v2-nine-parent-jsonl', [test2json['path'], '-p',
            'researchos.local/research-os/internal/domain', '-t', str(binary), '-test.v=test2json',
            '-test.run=' + selector, '-test.count=1', '-test.timeout=14m'], 900, T / 'internal/domain')
        actual_test_jsonl_primary_ref = invocations[-1]
        assert type(result['owned_child_pid']) is int and result['owned_child_pid'] > 0
        assert type(result['creation_time_100ns']) is int and result['creation_time_100ns'] > 0
        assert jobs[-1]['primary_identity_observed'] is True and jobs[-1]['closed'] is True
        assert pin(binary) == pin(scratch / 'programs/restored21-v2-component.test.exe')
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
        # These nine parents do not select the separate typed runtime fixture.
        # If its directory unexpectedly appears, retain every bounded raw file
        # but still leave individual descendant qualification OPEN.
        evidence_files = []
        if evidence.exists():
            assert evidence.is_dir() and not evidence.is_symlink()
            files = sorted(p for p in evidence.rglob('*') if p.is_file())
            assert len(files) <= 128 and all(not p.is_symlink() for p in evidence.rglob('*'))
            assert sum(p.stat().st_size for p in files) <= 64 * 1024 * 1024
            if files:
                evidence_guard = gm.SourceReadGuard(per_file_cap=16 * 1024 * 1024, total_cap=64 * 1024 * 1024)
                evidence_guard.acquire([pin(p) for p in files])
                archive = O / 'typed-evidence-archive'
                archive.mkdir()
                for path in files:
                    relative = path.relative_to(evidence)
                    target = archive / relative
                    assert target.resolve().is_relative_to(archive.resolve())
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with target.open('xb') as stream:
                        stream.write(evidence_guard.get_buffer(str(path.resolve())))
                    evidence_files.append({'source_ref': pin(path), 'archive_ref': pin(target), 'relative': relative.as_posix()})
        typed_evidence_ref = save('typed-evidence-inventory.json', {
            'environment_directory': str(evidence), 'directory_observed': evidence.exists(),
            'files': evidence_files, 'selected_roster_has_typed_fixture_parent': False,
            'individual_descendant_PID_FILETIME_raw_streams_exit': None,
            'native_qualification_accepted': False})
        development_tests_observed = True
    except BaseException as err:
        phase_error = repr(err)
    finally:
        for guard, name in ((binary_guard, 'binary'), (compiler_guard, 'compiler'),
                            (evidence_guard, 'evidence'), (candidate_guard, 'candidate'),
                            (runtime_guard, 'runtime'), (input_guard, 'input')):
            if guard is not None:
                try:
                    cleanup = guard.close()
                except BaseException as error:
                    cleanup = {'closed': False, 'errors': [repr(error)], 'retained_handles_count': None}
                guard_cleanup_refs.append(save(name + '-source-guard.cleanup.actual.json', cleanup))
                all_guards_closed = (all_guards_closed and cleanup['closed'] is True and
                                     not cleanup['errors'] and cleanup['retained_handles_count'] == 0)
    jobs_closed = bool(jobs) and len(jobs) == len(invocations) and all(item['closed'] is True for item in jobs)
    canonical_unchanged = all(p.read_bytes() == raw for p, raw in before.items())
    main_unchanged = all(p.read_bytes() == raw for p, raw in main_before.items())
    required_guard_count = 5 + (1 if evidence_guard is not None else 0)
    clean = all_guards_closed and len(guard_cleanup_refs) == required_guard_count and jobs_closed and canonical_unchanged and main_unchanged
    if not clean and phase_error is None:
        phase_error = 'Required guard, Job, canonical, or Main closure was not observed'
    if phase_error is None and development_tests_observed:
        closed('DEVELOPMENT_TESTS_13_ACTUAL_PASS_COMPONENT_PARTIAL_NATIVE_QUALIFICATION_OPEN')
    else:
        closed('FAILED_RESTORED21_V2_ACTUAL_CLOSED_NO_COMPONENT_ACCEPTANCE', phase_error or 'Development test controls incomplete')
        raise RuntimeError(phase_error or 'Development test controls incomplete')


if __name__ == '__main__':
    try:
        main()
    except BaseException:
        print('SOURCE_PYTHON_EXIT=1', flush=True)
        raise
    print('SOURCE_PYTHON_EXIT=0', flush=True)
