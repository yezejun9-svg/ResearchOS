from pathlib import Path
import hashlib, json, re, shutil

out = Path(__file__).resolve().parent
root = out.parent
author = root / 'product-v1-native-policy-binding-author-20261105'
final = author / 'final'
source = json.loads((final / 'SOURCE.json').read_text())
manifest = json.loads((final / 'manifest.json').read_text())
snapshot = Path(source['source_snapshot'])
worktree = Path('D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-native-policy-binding-20261105')
repo = Path('D:/作品集/ResearchOS/research-os')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
changed = {k:v['source_sha256'] for k,v in source['changed'].items()}
all_source = changed | source['reviewed_unchanged_input']

def copy(src, relative):
    dest = out / relative
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest)

for rel, expected in manifest['files_sha256'].items():
    assert sha(final / rel) == expected, rel
    copy(final / rel, 'author-final/' + rel)
copy(final / 'manifest.json', 'author-final/manifest.json')
for rel, expected in all_source.items():
    assert sha(snapshot / rel) == sha(worktree / rel) == expected, rel
    copy(snapshot / rel, 'source/' + rel)
for run in ('product-v1-native-policy-tests-01', 'product-v1-native-policy-tests-02'):
    original = root / 'product-v1-owned-verification-20261104/runs' / run
    for rel in ('RESULT.json', 'stdout.raw', 'stderr.raw'):
        assert sha(original / rel) == sha(final / 'runs' / run / rel), (run, rel)
    copy(original / 'CONSUMED.json', 'original-consumption/' + run + '.json')
contract = repo / 'execution/product-v1/contracts/native-policy-binding.v1.md'
assert sha(contract) == 'fc52dd1ea75f0eebecd6ec09cd64524fccabc823b2bc593467bd388e2b7213a4'
copy(contract, 'contract/native-policy-binding.v1.md')
copy(repo / 'execution/product-v1/receipts/single-harness-20261104/native-policy-binding/scope.json', 'contract/source-scope.json')

run = final / 'runs/product-v1-native-policy-tests-02'
result = json.loads((run / 'RESULT.json').read_text())
log = (run / 'stdout.raw').read_text()
passed = re.findall(r'^\s*--- PASS: (\S+)', log, re.M)
assert result['root_exit_code'] == 0 and result['stop_proved'] and result['job_active_zero']
assert not result['errors'] and not result['input_drift']
assert result['terminate_job_attempts'] == result['terminate_original_root_attempts'] == 0
assert sum('/' not in x for x in passed) == 8 and sum('/' in x for x in passed) == 30
assert '--- SKIP:' not in log

report = {
    'schema': 'researchos.independent-source-fixture-review.v1',
    'reviewer': '/root/native_path_entry_review',
    'decision': 'APPROVED_SOURCE_FIXTURE_ONLY',
    'source_head': source['base_head'],
    'selected_candidate': str(snapshot),
    'candidate_manifest': str(final / 'manifest.json'),
    'candidate_manifest_sha256': sha(final / 'manifest.json'),
    'source_sha256': changed,
    'reviewed_unchanged_inputs': source['reviewed_unchanged_input'],
    'formal_increment': 0,
    'product_increment': 0,
    'pending_blockers': [],
    'integrity': {
        'author_manifest_entries_verified': len(manifest['files_sha256']),
        'snapshot_and_current_worktree_exact_source_files': len(all_source),
        'original_outer_result_and_raw_files_matched': 6,
        'mismatches': [],
        'contract_sha256': sha(contract),
        'scope_consumed': True,
        'automatic_retry_authorized': False
    },
    'review_findings': [
        {'boundary': 'Canonical requested policy', 'conclusion': 'The shared argv builder emits the exact global windows.sandbox="mxc" once. Permission profile remains root deny, minimal read, selected workspace read, network disabled, approval never and extensions disabled. Config identity hashes this same builder with Host source/cwd placeholders; it is a requested-config identity, not effective managed permission proof.'},
        {'boundary': 'Fresh shared readiness', 'conclusion': 'Capabilities/Submit, scan, launch/gate, BeforeResume and driver Start use the shared predicate with freshly obtained readiness and canonical expected identity. Descriptor failure, any nonempty snapshot reason, non-READY state or any identity-field mismatch rejects. Driver checks again while its child is suspended before calling Host BeforeResume.'},
        {'boundary': 'Production composition', 'conclusion': 'Ordinary NewCodexCLI exposes UNVERIFIED readiness. The unchanged actual Host calls that constructor. The separate Go-only fixture constructor is used by trusted test composition; no environment, JSON, HTTP or renderer READY import was added. PermissionOverrides now reject nonempty values.'},
        {'boundary': 'Immutable source binding', 'conclusion': 'New Host-sealed task input binds ref, principal, project, requested READ_ONLY, actual binding access, revision and canonical RealPath digest. Admission, scan and launch gates compare the snapshot. BeforeResume additionally compares the fresh binding RealPath and revision against the exact binding used to populate driver Start input; a valid replacement path cannot authorize the previously selected path.'},
        {'boundary': 'Suspended failure and no replay', 'conclusion': 'The existing launchWithCallback lifecycle calls BeforeResume before ResumeThread and terminates the owned Job on callback failure. The new rebind counterexample observes one start, no result/assistant content, and no second start after another Scan. Existing claim, identity and stop fences remain in place.'},
        {'boundary': 'Internal sealed policy and history', 'conclusion': 'Internal v2 sandbox/command/revision/mode/profile/hash fields are required; registration uses a distinct MXC V2 name and full identity comparisons. Old profile/input without source snapshot cannot gain new admission. Get/List/taskView/harnessTaskInput history readers have no changed body in the supplied baseline patches and do not impose the new snapshot gate on reads. No migration or automatic requeue is added.'},
        {'boundary': 'Public DTO', 'conclusion': 'No public DTO shape or verification enum is added. The capabilities response preserves profile_id codex-workspace-read-v1, UNVERIFIED verification values, and enforcement_verified=false; only can_submit/reason_codes consume the stronger readiness predicate.'}
    ],
    'test_evidence': {
        'execution': 'Read existing original f13 test02 receipts and matching author copies; reviewer ran no tests or processes under test.',
        'scope_sha256': result['scope_sha256'],
        'result_sha256': sha(run / 'RESULT.json'),
        'stdout_sha256': sha(run / 'stdout.raw'),
        'status': result['status'],
        'root_exit_code': result['root_exit_code'],
        'top_level_pass': 8, 'subtest_pass': 30, 'skip': 0,
        'job_total_processes': result['job_total_processes'],
        'job_active_zero': True, 'stop_proved': True,
        'forced_termination_attempts': 0, 'input_drift': False,
        'targeted_counterexamples': ['contradictory_ready', 'mode_mutation', 'template_mutation', 'revision_mutation', 'TestCodexReadinessMutationBeforeResume', 'WORKSPACE_REBIND', 'TestHarnessSourceRebindBeforeResume'],
        'coverage_limit': 'The fake-chain uses a fake executable with the production argument builder. Some private adapter lifecycle tests use fixture arguments. Legacy Get/List, old sealed profile rejection and full policy-field equality are also supported by static review; this report does not claim an explicit test for every such combination or a full repository test run.'
    },
    'diagnostic_events': [
        {'origin_key': 'native-policy-binding:workspace-snapshot-toctou', 'classification': 'RESOLVED_SOURCE_FIXTURE', 'detail': 'Previously reported pre-review finding, not a new event: sealed source snapshot and explicit driver-selected path/revision comparison close the valid-rebind-before-resume gap. Test02 includes pre-scan and before-resume rebind counterexamples.'},
        {'origin_key': 'native-policy-binding:ready-with-reason-accepted', 'classification': 'RESOLVED_SOURCE_FIXTURE', 'detail': 'Previously reported pre-review finding, not a new event: Evaluate now rejects every nonempty readiness reason before accepting READY; contradictory_ready passes in test02.'}
    ],
    'observations': [
        'The earlier wrong-namespace candidate and test01 evidence are retained. Existing event native-policy-A:mode-key-wrong-namespace is not counted again.',
        'The earlier read-only guessed workspace-source filename miss remains in prereview01; it required no reset and is not counted again.',
        'CONSUMED.json is the immutable pre-launch consumption marker; the terminal RESULT.json resolves that run outcome. Neither consumed test scope is replayable.',
        'No new source defect was found in the final nine-file candidate within this review scope.'
    ],
    'remaining_runtime_limit': 'A trustworthy same-start native effective-policy barrier is not implemented by Slice A. Production remains UNVERIFIED and blocked. No actual Native CLI, model invocation, effective filesystem permission or product journey has been verified or approved by this review.',
    'review_actions': {'source_mutations': 0, 'D_writes': 0, 'app_launches': 0, 'native_cli_launches': 0, 'model_invocations': 0, 'test_reruns': 0}
}
(out / 'review-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
files = sorted(p.relative_to(out).as_posix() for p in out.rglob('*') if p.is_file() and p.name not in ('archive-file-list.json', 'SHA256SUMS.json'))
(out / 'archive-file-list.json').write_text(json.dumps({'root': str(out), 'files': files + ['SHA256SUMS.json']}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
(out / 'SHA256SUMS.json').write_text(json.dumps({rel:sha(out / rel) for rel in files}, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'report': str(out / 'review-report.json'), 'report_sha256': sha(out / 'review-report.json'), 'archive': str(out / 'archive-file-list.json'), 'archive_sha256': sha(out / 'archive-file-list.json'), 'archive_files': len(files) + 1, 'candidate_manifest_sha256': sha(final / 'manifest.json')}, indent=2))
