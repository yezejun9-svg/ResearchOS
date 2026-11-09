import hashlib
import json
from pathlib import Path

E = Path(__file__).resolve().parent
T = Path('D:/作品集/ResearchOS/research-os/.local/online-backup-fixture-qualification-20261015-tmp')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(name):
    return json.loads((E / name).read_text(encoding='utf-8-sig'))

def exit_code(stem):
    return read(stem + '.exit.json')['native_exit']

for prefix in ['q01-r2', 'q02', 'q03']:
    for step, expected in [('probe-before',10),('create',0),('probe-after',10),('probe-released',0),('restore',0)]:
        assert exit_code(prefix + '-' + step) == expected, (prefix, step)
assert exit_code('q03-build-current-fixture-r2') == 0
assert exit_code('verify-q03-current-history-r5') == 0
assert exit_code('q02-refuse-existing-dest') == exit_code('q02-wrong-key-restore') == exit_code('q02-refuse-changed-workspace') == 1
assert read('compare-q03-current.stdout.raw')['source_all_tables_equal']

cases = {
    'schema': 'researchos.online-backup-fixture-qualification.v1',
    'source_commit': '4f4023c956f84d65743f39ce77d6c8899a21ada1',
    'source_tree': '3db13a15cc52b2b0bd75cae3452c66509a9f55c9',
    'scope_sha256': '5ce1dd8bea33a4205a2e357b4ca2364b41505a077fab9d2deb64b053fa65ea22',
    'actual_backup_authority': False,
    'formal_acceptance_increment': 0,
    'self_acceptance': False,
    'cases': {
        'Q01': {'status': 'FINITE_FIXTURE_PASS', 'run': 'run-q01-r2', 'source_census': 'compare-q01-r2.stdout.raw', 'restore': 'verify-q01-r2-restore.stdout.raw'},
        'Q02': {'status': 'FINITE_FIXTURE_PASS', 'run': 'run-q02', 'source_census': 'compare-q02.stdout.raw', 'restore': 'verify-q02-restore-r2.stdout.raw', 'negative_cuts': 'verify-negative-cuts.stdout.raw'},
        'Q03': {'status': 'FINITE_FIXTURE_PASS', 'run': 'run-q03-current-r2', 'builder': 'q03-build-current-fixture-r2',
                'source_census': 'compare-q03-current.stdout.raw', 'restore': 'verify-q03-current-history-r5.stdout.raw',
                'fixture_only_sql': ['UNKNOWN client_command_queue receipt/state', 'REVOKED workspace binding'],
                'public_api': ['goalCommand', 'PrepareEffect', 'BeginEffect', 'ObserveEffect UNKNOWN'],
                'old_candidate_excluded': 'inspect-q03-candidate-r3.stdout.raw'},
    },
    'remaining_limit': 'No controlled concurrent business writer point-in-time assertion; idle held lease only.',
}
(E / 'qualification-report.json').write_text(json.dumps(cases, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

matrix = {
    'Q01': {'lease_probe_before': exit_code('q01-r2-probe-before'), 'create': exit_code('q01-r2-create'), 'lease_probe_after': exit_code('q01-r2-probe-after'), 'lease_probe_after_release': exit_code('q01-r2-probe-released'), 'restore': exit_code('q01-r2-restore'), 'source_all_tables_equal': read('compare-q01-r2.stdout.raw')['source_all_tables_equal']},
    'Q02': {'lease_probe_before': exit_code('q02-probe-before'), 'create': exit_code('q02-create'), 'lease_probe_after': exit_code('q02-probe-after'), 'lease_probe_after_release': exit_code('q02-probe-released'), 'restore': exit_code('q02-restore'), 'source_all_tables_equal': read('compare-q02.stdout.raw')['source_all_tables_equal']},
    'Q03': {'lease_probe_before': exit_code('q03-probe-before'), 'create': exit_code('q03-create'), 'lease_probe_after': exit_code('q03-probe-after'), 'lease_probe_after_release': exit_code('q03-probe-released'), 'restore': exit_code('q03-restore'),
            'source_all_tables_equal': read('compare-q03-current.stdout.raw')['source_all_tables_equal'],
            'history_assertions': 'verify-q03-current-history-r5.stdout.raw'},
    'cuts': read('verify-negative-cuts.stdout.raw'),
}
(E / 'Q01-Q03-cuts-matrix.json').write_text(json.dumps(matrix, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

helper_names = ['Invoke-EvidenceCommand.ps1', 'run_case.ps1', 'census.py', 'compare_census.py', 'verify_restore.py', 'verify_q03.py',
                'negative_summary.py', 'inspect_q03.py', 'copy_q03_candidate.ps1', 'change_workspace_identity.ps1',
                'compare_host_constructor.py', 'fixture_setup.go', 'fixture_setup.overlay.json', 'q03_fixture_test.go',
                'q03_fixture.overlay.json', 'host_constructor_probe.go', 'host_constructor_probe.overlay.json',
                'lease_holder.go', 'lease_probe.go', 'freeze_evidence.py']
sources = {name: {'sha256': sha(E / name), 'bytes': (E / name).stat().st_size} for name in helper_names}
packages = {}
for case, sub in [('Q01', 'encrypted-backup-r2'), ('Q02', 'encrypted-backup'), ('Q03', 'encrypted-backup')]:
    root = T / 'fixture' / case / sub
    packages[case] = {'path': str(root), 'files': {p.name: {'sha256': sha(p), 'bytes': p.stat().st_size} for p in sorted(root.iterdir()) if p.is_file()}}
manifest = {'source_commit': cases['source_commit'], 'source_tree': cases['source_tree'], 'source_edit': False, 'helper_and_overlay': sources, 'encrypted_fixture_packages': packages,
            'q03_candidate_copy': {'path': str(T / 'fixture/Q03/source-data/researchos.sqlite'), 'sha256': sha(T / 'fixture/Q03/source-data/researchos.sqlite'), 'qualifies_current_schema': False},
            'q03_current_fixture': {'path': str(T / 'fixture/Q03/current-data-r2/researchos.sqlite'),
                                    'sha256': sha(T / 'fixture/Q03/current-data-r2/researchos.sqlite'),
                                    'builder_overlay_sha256': sha(E / 'q03_fixture.overlay.json'), 'fixture_only_sql_disclosed': True},
            'key_retention': 'Separate task-private key directory; key paths and bytes intentionally omitted from evidence manifest.'}
(E / 'source-helper-overlay-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

recipes = sorted(E.glob('*.recipe.json'))
commands = []
for r in recipes:
    stem = r.name[:-len('.recipe.json')]
    exit_path = E / (stem + '.exit.json')
    item = {'id': stem, 'recipe': r.name, 'recipe_sha256': sha(r), 'exit': exit_path.name if exit_path.exists() else None,
            'native_exit': read(exit_path.name).get('native_exit') if exit_path.exists() else None,
            'stdout': stem + '.stdout.raw' if (E / (stem + '.stdout.raw')).exists() else None,
            'stderr': stem + '.stderr.raw' if (E / (stem + '.stderr.raw')).exists() else None}
    commands.append(item)
(E / 'command-index.json').write_text(json.dumps({'count': len(commands), 'commands': commands}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

diagnostics = [
    {'id': 'task-root-private-acl', 'kind': 'setup_failure', 'reason': 'Initial SID formatting error 1332; corrected in task-root-private-acl-retry.'},
    {'id': 'run-q01', 'kind': 'observation_failure', 'reason': 'Initial file census tried to read locked coordinator.lock; corrected census records PermissionError; Q01 r2 succeeded.'},
    {'id': 'list-task-fixture-outputs', 'kind': 'inspection_failure', 'reason': 'PowerShell filter typo; corrected by list-task-fixture-outputs-r2.'},
    {'id': 'q03-build-current-fixture', 'kind': 'builder_failure', 'reason': 'Goal problem-id mismatch; corrected in q03-build-current-fixture-r2 using a separate root.'},
    {'id': 'run-q03-current', 'kind': 'shell_failure', 'reason': 'Nested Windows PowerShell 5 lacked utf8NoBOM; rerun with installed pwsh in run-q03-current-r2.'},
    {'id': 'verify-q03-current-history', 'kind': 'verifier_failure', 'reason': 'Initial verifier queried absent resource_effects.state; corrected to body JSON state.'},
    {'id': 'verify-q03-current-history-r2', 'kind': 'verifier_failure', 'reason': 'Initial status assertion expected RUNNING; observed valid source QUEUED and corrected to QUEUED -> RECONCILING.'},
    {'id': 'verify-q03-current-history-r3', 'kind': 'verifier_failure', 'reason': 'Diagnostic output captured source QUEUED and restored RECONCILING before correcting assertion.'},
    {'id': 'concurrent_writer', 'kind': 'untested_limit', 'reason': cases['remaining_limit']},
]
(E / 'diagnostic-ledger.json').write_text(json.dumps(diagnostics, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

final_names = ['qualification-report.md', 'qualification-report.json', 'Q01-Q03-cuts-matrix.json', 'source-helper-overlay-manifest.json', 'command-index.json', 'diagnostic-ledger.json']
final = {'schema': 'researchos.online-backup-fixture-qualification-final-manifest.v1', 'files': {name: {'sha256': sha(E / name), 'bytes': (E / name).stat().st_size} for name in final_names}, 'raw_command_count': len(commands), 'actual_backup_authority': False, 'formal_acceptance_increment': 0, 'self_acceptance': False}
(E / 'FINAL-manifest.json').write_text(json.dumps(final, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'files': final_names + ['FINAL-manifest.json'], 'raw_command_count': len(commands), 'Q03': 'FINITE_FIXTURE_PASS'}, ensure_ascii=False))
