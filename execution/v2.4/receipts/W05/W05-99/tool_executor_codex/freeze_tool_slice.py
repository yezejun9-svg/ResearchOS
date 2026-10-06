from pathlib import Path
import datetime, hashlib, json, subprocess

HERE = Path(__file__).resolve().parent
WT = HERE.parents[5]
MAIN = Path('D:/作品集/ResearchOS/research-os')
REL = HERE.relative_to(WT)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def ref(path, root=WT):
    return {'path': path.relative_to(root).as_posix(), 'sha256': sha(path), 'bytes': path.stat().st_size}

def read(path):
    return json.loads(path.read_bytes())

scopes = [MAIN/'execution/v2.4/receipts/W05/W05-99/integration_codex'/name for name in ('tools_source_scope_codex.json', 'tool_recovery_test_source_scope_codex.json')]
paths = [p for scope in scopes for p in read(scope)['exact_paths']]
assert len(paths) == len(set(paths)) == 5
changed = subprocess.check_output(['git', 'diff', '--name-only'], cwd=WT, text=True).splitlines()
untracked = subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard'], cwd=WT, text=True).splitlines()
assert all(p in paths or p.startswith(REL.as_posix()+'/') for p in changed+untracked), (changed, untracked)

full = HERE/'runs/20261006T001547Z-8ebe9d6dfe'
target = HERE/'runs/20261006T002037Z-7117ab5404'
def check_run(run, expected):
    result, inputs = read(run/'result.json'), read(run/'inputs.json')
    assert result['exit_code'] == 0 and result['package_pass']
    assert not result['test_fail'] and not result['test_skip'] and not result['source_changed_during_run']
    assert result['inputs_sha256'] == sha(run/'inputs.json')
    assert result['stdout_sha256'] == sha(run/'stdout.jsonl')
    assert result['stderr_sha256'] == sha(run/'stderr.txt')
    rows = [json.loads(line) for line in (run/'stdout.jsonl').read_text(encoding='utf8').splitlines()]
    actual = {action: [row['Test'] for row in rows if row.get('Action') == action and row.get('Test')] for action in ('pass', 'fail', 'skip')}
    assert actual['pass'] == result['test_pass'] and not actual['fail'] and not actual['skip']
    assert len(actual['pass']) == expected
    assert sha(run/'runner_snapshot.py.txt') == inputs['runner_sha256']
    source_by_path = {row['path']: row['sha256'] for row in inputs['source_inputs']}
    for p in paths:
        assert source_by_path[p] == sha(run/'source_snapshot'/p)
    return {**ref(run/'result.json'), 'inputs': ref(run/'inputs.json'), 'stdout': ref(run/'stdout.jsonl'), 'stderr': ref(run/'stderr.txt'), 'runner_snapshot': ref(run/'runner_snapshot.py.txt'), 'test_and_subtest_pass_count': expected, 'fail_count': 0, 'skip_count': 0, 'package_pass': True}

full_ref, target_ref = check_run(full, 47), check_run(target, 2)
for p in paths:
    assert sha(WT/p) == sha(target/'source_snapshot'/p)
    if p != 'internal/domain/runtime_sessions_windows_test.go':
        assert sha(full/'source_snapshot'/p) == sha(target/'source_snapshot'/p)
before = (full/'source_snapshot/internal/domain/runtime_sessions_windows_test.go').read_bytes()
after = (WT/'internal/domain/runtime_sessions_windows_test.go').read_bytes()
marker = b'func TestW14SessionProjectionRecoveryAfterReportCommit('
assert before.split(marker)[0] == after.split(marker)[0]
assert before.count(marker) == after.count(marker) == 1
assert before.rstrip().endswith(b'}') and after.rstrip().endswith(b'}')
assert b'func ' not in after.split(marker)[1]

diff = subprocess.run(['git', '-c', 'core.whitespace=cr-at-eol', 'diff', '--check', '--', *paths, (REL/'run_tool_checks.py').as_posix(), (REL/'freeze_tool_slice.py').as_posix()], cwd=WT, capture_output=True)
(HERE/'diff_check.stdout.txt').write_bytes(diff.stdout)
(HERE/'diff_check.stderr.txt').write_bytes(diff.stderr)
assert diff.returncode == 0, diff.stderr

history = []
for run in sorted((HERE/'runs').iterdir()):
    if not (run/'result.json').is_file():
        continue
    result = read(run/'result.json')
    entry = {**ref(run/'result.json'), 'inputs': ref(run/'inputs.json'), 'stdout': ref(run/'stdout.jsonl'), 'stderr': ref(run/'stderr.txt'), 'exit_code': result['exit_code'], 'pass_count': len(result['test_pass']), 'failed_tests': result['test_fail'], 'skipped_tests': result['test_skip']}
    if (run/'runner_snapshot_provenance.json').is_file():
        entry['runner_snapshot_provenance'] = ref(run/'runner_snapshot_provenance.json')
        entry['runner_capture'] = 'RECONSTRUCTED_HASH_MATCHED_ORIGINAL_MANIFEST_NOT_PROCESS_CAPTURE'
    else:
        entry['runner_capture'] = 'CAPTURED_BEFORE_PROCESS_START'
    history.append(entry)

receipt = {
    'schema': 'researchos.w05.tool-projection-execution.v1',
    'status': 'EXECUTED_PENDING_INDEPENDENT_SOURCE_REVIEW',
    'slice_id': 'W05-99-S3-DURABLE-TOOL-EVENTS',
    'owner': 'codex:/root',
    'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'candidate_worktree': str(WT),
    'base_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=WT, text=True).strip(),
    'registered_scopes': [ref(path, MAIN) for path in scopes],
    'independent_scope_reviews': [read(path)['independent_scope_review_ref'] for path in scopes],
    'current_source': [ref(WT/p) for p in paths],
    'full_selected_regression': full_ref,
    'final_targeted_regression': target_ref,
    'test_snapshot_relationship': '47 passes bind their original exact snapshot; final 2 passes bind strengthened recovery test and existing MuQualificationBroker. The only intervening source change is three integrity assertions inside the registered recovery function. All three product sources and dedicated projection tests are byte-identical between both runs.',
    'actual_modes': ['CANONICAL_SQLITE_AND_HOST_JOURNAL_FIXTURE', 'REAL_CURRENT_MU_SDK_WITH_LOCAL_MODEL_AND_HOST_TOOL_FIXTURE_PORTS'],
    'behavior': [
        'Commit deterministic TOOL_STARTED in the same beginEffect transaction before physical tool IO; projection failure rolls back admission and performs no tool call.',
        'Project canonical effect history including UNKNOWN followed by a trusted late outcome; distinguish failed tool, refusal, unknown and success from Run settlement.',
        'Validate original dispatch identity, request/reservation/receipt/manifest and raw evidence before deriving immutable report and exact stdout/stderr artifacts.',
        'Project each real immutable ledger once; unknown/reserve placeholder cost remains null and unknown, while actual known local-tool zero is explicit.',
        'Repair historical Run usage using its original session association and current writer; sealed sessions acquire no new event and do not block billing or scanning.',
        'Preserve original Run/Task status and no-self-acceptance; repeated recovery preserves the complete event bytes and watermark.'
    ],
    'run_history': history,
    'additional_failures_retained': [ref(HERE/name) for name in ('format_failure.json', 'format_failure_original_source.go.txt', 'process_creation_failure.json')],
    'diff_check': {'exit_code': diff.returncode, 'stdout': ref(HERE/'diff_check.stdout.txt'), 'stderr': ref(HERE/'diff_check.stderr.txt')},
    'limits': [
        'No external provider call, installed-product LIVE demonstration, formal A04, W05 parent or independent product acceptance.',
        'SDK parent tool hierarchy and token streaming are not implemented by this slice; parent_tool_call_id is null without proven facts.',
        'Original failed runs and reconstructed-runner provenance are retained; no failed invocation is promoted as passing evidence.',
        'Changed domain sources invalidate the prior current W04 source vector after integration; historical proof is retained and current revalidation is required.'
    ],
    'external_provider_calls': 0,
    'formal_case_count_delta': 0,
    'parent_acceptance_issued': False,
    'independent_acceptance_issued': False
}
out = HERE/'execution_receipt.json'
out.write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
print(json.dumps({'receipt': ref(out), 'source_files': len(paths), 'full_pass': 47, 'targeted_pass': 2, 'run_history_count': len(history)}, ensure_ascii=True))
