"""Pure Source review controls. Does not call Git, Go, native code, SQL, or a product CLI."""
import ast
import hashlib
import json
import re
import sys
import types
from pathlib import Path

sys.dont_write_bytecode = True
N = Path(__file__).resolve().parent
C = json.loads((N / 'contract.json').read_bytes())


def pin(path):
    path = Path(path).resolve()
    data = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}


def exact(ref):
    actual = pin(ref['path'])
    assert actual['sha256'] == ref['sha256'] and ('bytes' not in ref or actual['bytes'] == ref['bytes']), ref['path']
    return actual


def save(name, value):
    with (N / name).open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    return pin(N / name)


def module(path, data):
    mod = types.ModuleType('r21v2_source_guard')
    mod.__file__ = str(path)
    sys.modules[mod.__name__] = mod
    exec(compile(data, str(path), 'exec'), mod.__dict__)
    return mod


def main():
    assert len(sys.argv) == 1 and Path(sys.executable).resolve() == Path(C['python']['path']).resolve()
    names = ('h20_actual_review_handoff', 'h20_actual_review_manifest', 'h20_actual_closed',
        'h20_source_overlay', 'a21_v2_source_handoff', 'a21_v2_source_manifest',
        'a21_v2_review_handoff', 'a21_v2_review_manifest', 'a21_v2_overlay',
        'source_guard', 'owned_job', 'python', 'go', 'node', 'mu_bundle', 'test2json')
    refs = [exact(C[name]) for name in names]
    h20 = json.loads(Path(C['h20_source_overlay']['path']).read_bytes())['sources']
    a21 = json.loads(Path(C['a21_v2_overlay']['path']).read_bytes())['files']
    refs += [exact(x) for x in h20.values()]
    refs += [exact(x) for x in a21.values()]
    refs += [pin(N / name) for name in ('contract.json', 'prepare_root_actual.py',
        'validate_root_actual.py', 'original-failure.945.json', 'check_source.py')]
    for name in ('a21_v2_source_manifest', 'a21_v2_review_manifest'):
        manifest = json.loads(Path(C[name]['path']).read_bytes())
        refs += [exact(member) for member in manifest['members']]
    dedup = {}
    for ref in refs:
        key = ref['path'].casefold()
        assert key not in dedup or dedup[key] == ref
        dedup[key] = ref
    refs = list(dedup.values())
    gp = exact(C['source_guard'])
    guard_module = module(gp['path'], Path(gp['path']).read_bytes())
    guard = guard_module.SourceReadGuard(per_file_cap=256 * 1024 * 1024, total_cap=2 * 1024 * 1024 * 1024)
    guard.acquire(refs)
    checks = []

    def check(name, condition):
        checks.append({'name': name, 'passed': bool(condition)})
        assert condition, name

    try:
        check('H20 actual scoped acceptance', json.loads(Path(C['h20_actual_review_handoff']['path']).read_bytes())['status'] == 'COMPONENT_VALIDATION_ACCEPTED_A20_TO_PLAIN21_ONLY')
        check('A21 v2 independent Source acceptance', json.loads(Path(C['a21_v2_review_handoff']['path']).read_bytes())['status'] == 'SOURCE_ACCEPTED_P2_ADDRESSED_PENDING_RUNTIME_QUALIFICATION')
        check('exact H20 61 plus A21 5 yields 63', len(h20) == 61 and len(a21) == 5 and len(set(h20) | set(a21)) == 63)
        check('five fixed A21 paths', set(a21) == set(C['overlay_exact_paths']))
        check('precise overlay provenance', all(Path(v['path']).resolve().is_relative_to(Path(C['a21_v2_overlay']['path']).parent.resolve()) for v in a21.values()))
        roster = json.loads(Path(C['a21_v2_source_handoff']['path']).with_name('test-roster.json').read_bytes())
        check('nine parents four leaves source declaration', len(roster['parent_tests']) == 9 and len(set(roster['parent_tests'])) == 9 and len(roster['drift_subtests']) == 4)
        test = Path(a21['internal/domain/backup_restored21_upgrade_test.go']['path']).read_text(encoding='utf-8')
        for snippet in ('history20Fixture(t)', 'UpgradeLocal(context.Background(),prior)',
                        'if len(before["schema_migrations"])!=21', 'missing-restore-trigger',
                        'Bytes(report.Recovery),Bytes(persisted.Recovery)', 'restored21ReportHookControls(t)'):
            check('fixture source contains ' + snippet, snippet in test)
        check('no New current store fixture', 'store.New(' not in test and 'NewCurrent' not in test)
        old_upgrade = Path(h20['internal/domain/backup_upgrade.go']['path']).read_text(encoding='utf-8')
        new_upgrade = Path(a21['internal/domain/backup_upgrade.go']['path']).read_text(encoding='utf-8')
        check('H20 dispatch preserved', old_upgrade in new_upgrade.replace(
            '\tif opt.Plan == Restored21SessionUpgradePlan {\n\t\treturn upgradeRestored21Local(ctx, opt, verifier)\n\t}\n', ''))
        old_cli = Path(h20['ops/backup/main.go']['path']).read_text(encoding='utf-8')
        new_cli = Path(a21['ops/backup/main.go']['path']).read_text(encoding='utf-8')
        check('CLI only extends plan help', old_cli == new_cli.replace(
            ' or restored21-session-to22-client-command-queue-v1', ''))
        new_backup = Path(a21['internal/domain/backup.go']['path']).read_text(encoding='utf-8')
        check('H20 restore branch still present', 'preserveHistory20UpgradeWorkspaces' in new_backup)
        check('A21 report prepublish hook', 'upgradeRestored21PublishEvidence(policy, r.Recovery)' in new_backup)
        check('purpose and MAC byte authority remains A21 reviewed Source', 'backupMAC' in new_backup and 'readBackupPolicy' in new_backup)
        check('future fixed paths stay in intended areas', Path(C['worktree']).resolve().is_relative_to((Path(C['repository']) / '.local/worktrees').resolve())
              and all(Path(C[k]).resolve().is_relative_to((Path(C['repository']) / 'execution/v2.4/receipts/W05/W05-99/integration_codex').resolve()) for k in ('isolation_output','validation_output')))
        check('two future Root output directories absent during Source', not Path(C['isolation_output']).exists() and not Path(C['validation_output']).exists())
        for file in ('prepare_root_actual.py', 'validate_root_actual.py'):
            source = (N / file).read_text(encoding='utf-8')
            tree = ast.parse(source, filename=file)
            check(file + ' Python AST parsed', isinstance(tree, ast.Module))
            check(file + ' binary Owned IO', "with stdout_path.open('xb')" in source or "with out.open('xb')" in source)
            check(file + ' all guard close', '.close()' in source and 'retained_handles_count' in source)
            check(file + ' explicit Python exit', 'SOURCE_PYTHON_EXIT=0' in source and 'SOURCE_PYTHON_EXIT=1' in source)
            check(file + ' no direct subprocess', 'subprocess' not in source and 'os.system' not in source)
        validator = (N / 'validate_root_actual.py').read_text(encoding='utf-8')
        for snippet in ('len(actions) == 13', 'started == set(actions) == terminals',
                        'compiler_inventory_ref', 'actual-tagged-compiler-input-inventory.json',
                        'original_trial_provider_requests', 'descendant_test_binary_exit',
                        'source-guard.cleanup.actual.json'):
            check('validator requires ' + snippet, snippet in validator)
        check('full typed refs supplied by Root', C['prepare_argv'][1:10] == C['validate_argv'][1:10]
              and C['validate_argv'][-2:] == ['ISOLATION_READY_SHA256', 'ISOLATION_READY_BYTES'])
        check('no actual execution claim', C['Root_actual_only'] is True and C['formal_acceptance'] is False
              and C['real_21_22_release_program_provenance'] == 'OPEN')
        check('all original Source refs stable', all(pin(ref['path']) == ref for ref in refs))
        save('source-controls.json', {'status': 'PASS_SOURCE_STATIC_ONLY', 'count': len(checks), 'checks': checks,
            'input_ref_count': len(refs), 'actual_Git_Go_compiler_test2json_native_SQL_product_CLI_model': False,
            'actual_test_count': 0, 'future_Root_only': True, 'formal_acceptance': False})
        print(json.dumps({'source_checks': len(checks), 'input_refs': len(refs)}), flush=True)
    finally:
        cleanup = guard.close()
        save('source-guard.cleanup.actual.json', cleanup)
        assert cleanup['closed'] and not cleanup['errors'] and cleanup['retained_handles_count'] == 0


if __name__ == '__main__':
    try:
        main()
    except BaseException:
        print('SOURCE_PYTHON_EXIT=1', flush=True)
        raise
    print('SOURCE_PYTHON_EXIT=0', flush=True)
