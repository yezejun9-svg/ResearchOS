"""Append-only audit supplement for the frozen 195-command index."""
import hashlib
import json
from pathlib import Path

e = Path(__file__).resolve().parent
index = json.loads((e / 'command-index.json').read_text(encoding='utf-8'))
rows = index['commands']
assert len(rows) == index['count'] == 195

def hash_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def capture_on_disk(id):
    return {kind: (e / f'{id}.{kind}').is_file() for kind in ('recipe.json','exit.json','stdout.raw','stderr.raw')}

def complete(id):
    return all(capture_on_disk(id).values())

snapshot_complete = sum(all(row.get(k) is not None for k in ('recipe','exit','stdout','stderr')) for row in rows)
now_complete = sum(complete(row['id']) for row in rows)
assert snapshot_complete == 193 and now_complete == 194
assert [r['id'] for r in rows if r.get('exit') is None] == ['bootstrap-read','freeze-evidence-seal']

expected_lease = {'q01-probe-before','q01-r2-probe-before','q01-r2-probe-after',
                  'q02-probe-before','q02-probe-after','q03-probe-before','q03-probe-after'}
expected_refusal = {'q02-refuse-existing-dest','q02-wrong-key-restore','q02-refuse-changed-workspace'}
primary_diagnostics = {'task-root-private-acl','run-q01','list-task-fixture-outputs',
                       'q03-build-current-fixture','run-q03-current','verify-q03-current-history',
                       'verify-q03-current-history-r2','verify-q03-current-history-r3'}
auxiliary_nonzero = {
    'build-fixture-setup': 'Go build rejected an internal-package import from outside its module; corrected with ownE Go overlay.',
    'find-fixture-api': 'rg included a nonexistent adapters/host path; inspection query error.',
    'inspect-q03-current-failure': 'Follow-on inspection named q03-create stderr before that command existed; original shell failure was already recorded.',
    'q01-files-before': 'Locked coordinator.lock caused the initial census failure inside run-q01; corrected census and Q01 r2 passed.',
    'q03-candidate-metadata': 'Inspection PowerShell path variable was null; subsequent immutable candidate copy and schema inspection succeeded.',
    'read-host-workspace-api': 'rg included a nonexistent internal/host/workspace_windows.go path; inspection query error.',
    'read-q03-goal-fixture-helper': 'rg targeted a nonexistent test filename; helper was subsequently located.'}
actual_nonzero = {r['id']: r['native_exit'] for r in rows if r.get('native_exit') not in (None, 0)}
groups = [expected_lease, expected_refusal, primary_diagnostics, set(auxiliary_nonzero)]
assert len(set.union(*groups)) == sum(map(len, groups)) == len(actual_nonzero) == 25
assert set.union(*groups) == set(actual_nonzero)
assert all(actual_nonzero[id] == 10 for id in expected_lease)
assert all(actual_nonzero[id] == 1 for id in expected_refusal)

ledger = json.loads((e / 'diagnostic-ledger.json').read_text(encoding='utf-8'))
assert {d['id'] for d in ledger if d['kind'] != 'untested_limit'} == primary_diagnostics
assert [d['id'] for d in ledger if d['kind'] == 'untested_limit'] == ['concurrent_writer']

def grouped(group, category):
    return [{'id': id, 'native_exit': actual_nonzero[id], 'classification': category} for id in sorted(group)]

start_errors = []
for row in rows:
    file = e / (row['id'] + '.exit.json')
    if file.is_file():
        exit_record = json.loads(file.read_text(encoding='utf-8-sig'))
        if exit_record.get('start_error'):
            start_errors.append({'id': row['id'], 'start_error': exit_record['start_error']})

supplement = {
  'schema': 'researchos.online-backup-capture-index-supplement.v1',
  'scope': 'Append-only qualification evidence audit; no product test rerun and no change to frozen report, index, ledger, or manifest.',
  'frozen_pins': {
      'command_index_count': 195,
      'command_index_sha256': hash_file(e / 'command-index.json'),
      'final_manifest_sha256': hash_file(e / 'FINAL-manifest.json'),
      'diagnostic_ledger_sha256': hash_file(e / 'diagnostic-ledger.json'),
  },
  'capture_counts': {
      'all_four_captures_in_frozen_index': snapshot_complete,
      'incomplete_in_frozen_index': 2,
      'all_four_captures_now_on_disk_among_same_195_ids': now_complete,
      'native_start_errors_among_available_exit_records': start_errors,
  },
  'missing_exit_in_frozen_index': [
      {'id': 'bootstrap-read', 'recipe_present': True, 'exit_stdout_stderr_present': False,
       'classification': 'DIRECT_READ_EXECUTED_WITHOUT_OWN_E_RAW_CAPTURE',
       'logger_invocation_under_this_id': False, 'product_command_never_executed': False,
       'execution_before_logger_capture': True,
       'actual_read': 'Get-FileHash SHA256 of sole scope card, Get-Content AGENTS.md and the scope card; direct tool output showed SHA256 5ce1dd8bea33a4205a2e357b4ca2364b41505a077fab9d2deb64b053fa65ea22. Corrected ownE bootstrap recipe and command-ledger first line later record completed/native_exit 0, but this is a post-hoc record, not raw process capture.',
       'evidence': ['bootstrap-read.recipe.json', 'command-ledger.ndjson first line'],
       'boundary': 'No ownE stdout/stderr/native exit file; independent reviewer should not count this as a complete four-file capture.'},
      {'id': 'freeze-evidence-seal', 'recipe_present': True, 'exit_stdout_stderr_present_at_freeze': False,
       'classification': 'SELF_SEAL_SNAPSHOT_EXCLUSION', 'logger_invocation_under_this_id': True,
       'execution_before_failure': False, 'native_exit_now': 0,
       'capture_files_now_present': capture_on_disk('freeze-evidence-seal'),
       'boundary': 'The index was written while this command was still running; logger wrote exit/stdout/stderr afterward.'},
  ],
  'pre_execution_failures_among_missing_exit_ids': [],
  'misplaced_bootstrap_prewrite': {
      'initial_wrong_directory': 'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp519/online_backup_fixture_qualification_codex/20261015-current-chat',
      'files': ['bootstrap-read.recipe.json', 'command-ledger.ndjson'],
      'sequence': 'Initial apply_patch prewrote these two files under the scope-card directory subtree. The direct AGENTS/scope read then ran. A subsequent apply_patch created the corrected ownE records and deleted the two misplaced files; read-only audit confirms both wrong-path files absent.',
      'source_edit': False,
  },
  'nonzero_native_exit': {
      'count': len(actual_nonzero),
      'expected_lease_probe_10': grouped(expected_lease, 'EXPECTED_LEASE_CONTENTION'),
      'expected_cli_refusal_1': grouped(expected_refusal, 'EXPECTED_CLI_REFUSAL'),
      'primary_diagnostic_failures_8': grouped(primary_diagnostics, 'DIAGNOSTIC_FAILURE_RETAINED'),
      'auxiliary_nonzero_7': [dict(grouped({id}, 'AUXILIARY_INSPECTION_OR_CHILD_FAILURE')[0], reason=reason)
                             for id, reason in sorted(auxiliary_nonzero.items())],
  },
  'diagnostic_vs_limit': {
      'primary_diagnostic_failure_count': 8,
      'diagnostic_ledger_entries': 9,
      'concurrent_writer': 'UNTESTED_LIMIT: no controlled business writer point-in-time assertion; not a product failure, not a ninth diagnostic failure.',
      'auxiliary_nonzero_count': 7,
      'auxiliary_boundary': 'These are separately retained child or inspection command exits; several belong to the eight primary incidents and are not additional product behavior failures.'},
  'authority': {'source_edit': False, 'actual_backup_authority': False, 'formal_acceptance_increment': 0,
                'self_acceptance': False},
  'audit_capture': ['audit-capture-index-supplement.recipe.json', 'audit-capture-index-supplement.stdout.raw',
                    'audit-capture-index-supplement.stderr.raw', 'audit-capture-index-supplement.exit.json',
                    'audit-capture-nonzero-details.recipe.json', 'audit-capture-nonzero-details.stdout.raw',
                    'audit-capture-nonzero-details.stderr.raw', 'audit-capture-nonzero-details.exit.json',
                    'audit-capture-hashes-and-bootstrap.recipe.json', 'audit-capture-hashes-and-bootstrap.stdout.raw',
                    'audit-capture-hashes-and-bootstrap.stderr.raw', 'audit-capture-hashes-and-bootstrap.exit.json'],
}
dest = e / 'capture-index-supplement.json'
assert not dest.exists(), 'supplement already exists; do not overwrite'
dest.write_text(json.dumps(supplement, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'path': str(dest), 'sha256': hash_file(dest), 'completed_in_snapshot': snapshot_complete,
                  'completed_now': now_complete, 'nonzero': len(actual_nonzero),
                  'primary_diagnostic_failures': len(primary_diagnostics)}, ensure_ascii=False))
