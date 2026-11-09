import hashlib
import json
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
WORKTREE = pathlib.Path(r'D:\作品集\ResearchOS\research-os\.local\worktrees\qualification-failure-b-r3-20261015')
RUNNER = HERE / 'CP522-run.py'
PYTHON = sys.executable
FOUR = [
    'adapters/runtime/qualification_failure_proof_windows.go',
    'adapters/runtime/qualification_failure_proof_windows_test.go',
    'internal/domain/runtime_qualification_failure_windows.go',
    'internal/domain/runtime_qualification_failure_windows_test.go',
]
PRIOR = json.loads((HERE.parent.parent / 'qualification_failure_b_revision02_source_codex' / '20261015-current-chat' / 'FINAL-manifest.json').read_text(encoding='utf-8'))
NINE = PRIOR['combined_source_paths']


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def record(id_, argv):
    recipe = HERE / (id_ + '.json')
    recipe.write_text(json.dumps({'id': id_, 'argv': argv, 'cwd': str(WORKTREE), 'env': {}}, ensure_ascii=False, indent=2), encoding='utf-8')
    result = subprocess.run([PYTHON, str(RUNNER), str(recipe)], capture_output=True)
    if result.returncode:
        raise RuntimeError(f'{id_}: {result.returncode}: {result.stderr.decode("utf-8", errors="replace")}')
    return (HERE / id_ / 'stdout.raw').read_bytes()


def git(*args):
    return ['git', '-c', 'maintenance.auto=false', '-c', 'gc.auto=0', '-C', str(WORKTREE), *args]


commit = record('067-final-head', git('rev-parse', 'HEAD')).decode().strip()
tree = record('068-final-tree', git('rev-parse', 'HEAD^{tree}')).decode().strip()
status = record('069-final-status', git('status', '--porcelain=v1'))
if status:
    raise RuntimeError(f'worktree not clean: {status!r}')
actual_four = record('070-exact-four-diff-names', git('diff', '--name-only', '1d3cc504da79df5bf0f69755011738d5adb827b0', commit)).decode().splitlines()
if sorted(actual_four) != sorted(FOUR):
    raise RuntimeError(f'changed source paths mismatch: {actual_four}')
whole_changed = record('071-whole-nine-diff-names', git('diff', '--name-only', 'f48fca0e', commit)).decode().splitlines()
if sorted(whole_changed) != sorted(NINE):
    raise RuntimeError(f'combined source paths mismatch: {whole_changed}')
patch4 = record('072-exact-four-patch', git('diff', '--binary', '--full-index', '1d3cc504da79df5bf0f69755011738d5adb827b0', commit, '--', *FOUR))
patch9 = record('073-whole-nine-patch', git('diff', '--binary', '--full-index', 'f48fca0e', commit, '--', *NINE))
(HERE / 'delta-exact-four-from-1d3cc504.patch').write_bytes(patch4)
(HERE / 'whole-nine-from-f48fca0e.patch').write_bytes(patch9)

hashes = {}
for path in NINE:
    data = (WORKTREE / path).read_bytes()
    hashes[path] = {'sha256': sha256(data), 'bytes': len(data)}
    if path not in FOUR and hashes[path] != PRIOR['source_hashes'][path]:
        raise RuntimeError(f'prior source drift: {path}')

index = []
for invocation_path in sorted(HERE.glob('*/invocation.json')):
    directory = invocation_path.parent
    exit_path = directory / 'exit.json'
    stdout_path = directory / 'stdout.raw'
    stderr_path = directory / 'stderr.raw'
    if not all(p.is_file() for p in (exit_path, stdout_path, stderr_path)):
        raise RuntimeError(f'incomplete command capture: {directory}')
    invocation = json.loads(invocation_path.read_text(encoding='utf-8'))
    exit_info = json.loads(exit_path.read_text(encoding='utf-8'))
    index.append({'id': directory.name, 'argv': invocation['argv'], 'cwd': invocation['cwd'], 'exit': exit_info['exit'], 'start_utc': invocation['start_utc'], 'end_utc': exit_info['end_utc'], 'stdout': {'path': str(stdout_path.relative_to(HERE)), 'sha256': sha256(stdout_path.read_bytes()), 'bytes': stdout_path.stat().st_size}, 'stderr': {'path': str(stderr_path.relative_to(HERE)), 'sha256': sha256(stderr_path.read_bytes()), 'bytes': stderr_path.stat().st_size}})
(HERE / 'command-index.json').write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding='utf-8')

checks = {
    'fresh_pre_fix_f01': '030-pref-f01-repro',
    'fresh_pre_fix_f02': '035-pref-f02-repro-final',
    'own_f01_after': '044-adapter-f01-after',
    'positive_after': '045-domain-positive-after',
    'private_cuts_after': '047-domain-new-tests',
    'transaction_hold_after': '049-domain-positive-replay-post-hold',
    'domain_matrix_after': '050-domain-qualification-matrix',
    'adapter_matrix_after': '051-adapter-qualification-matrix',
    'independent_f01_after': '052-independent-f01-after',
    'independent_f02_after': '053-independent-f02-after',
    'pinned_mu_after': '057-mu-original-three',
    'pinned_mu_integrity': '058-mu-integrity',
    'format': '062-gofmt-check',
    'diff_hygiene': '063-diff-check',
}
known = {e['id']: e for e in index}
matrix = {}
for name, command_id in checks.items():
    if command_id not in known:
        raise RuntimeError(f'missing check: {command_id}')
    row = known[command_id]
    matrix[name] = {'command_id': command_id, 'exit': row['exit'], 'stdout': row['stdout'], 'stderr': row['stderr']}
(HERE / 'claim-test-matrix.json').write_text(json.dumps(matrix, ensure_ascii=False, indent=2), encoding='utf-8')

manifest = {
    'schema': 'researchos.qualification-failure-B-r3-source-final.v1',
    'scope_authority_path': str(HERE.parent.parent / 'resume_cp398_codex' / '20261015-current-chat' / 'continuation-cp522' / 'qualification-failure-B-revision03-source-scope.json'),
    'scope_authority_sha256': '6633dc25b4143d95601dd31606ef4649b48779e87a4fb462eabd0233a1658373',
    'base_commit': '1d3cc504da79df5bf0f69755011738d5adb827b0',
    'combined_base': 'f48fca0e',
    'commit': commit,
    'tree': tree,
    'branch': 'codex/qualification-failure-b-r3-20261015',
    'worktree': str(WORKTREE),
    'source_allowlist': FOUR,
    'combined_source_paths': NINE,
    'source_hashes': hashes,
    'patches': {
        'delta_exact_four_from_1d3cc504': {'path': 'delta-exact-four-from-1d3cc504.patch', 'sha256': sha256(patch4), 'bytes': len(patch4), 'source_paths': FOUR},
        'whole_nine_from_f48fca0e': {'path': 'whole-nine-from-f48fca0e.patch', 'sha256': sha256(patch9), 'bytes': len(patch9), 'source_paths': NINE},
    },
    'command_index': 'command-index.json',
    'diagnostic_ledger': 'diagnostic-ledger.jsonl',
    'claim_test_matrix': 'claim-test-matrix.json',
    'worktree_clean_at_finalization': True,
    'formal_increment': 0,
    'actual_authority': False,
    'independent_review': 'PENDING',
    'self_acceptance': False,
}
(HERE / 'FINAL-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'commit': commit, 'tree': tree, 'commands': len(index), 'source_paths': len(hashes), 'patch4_sha256': sha256(patch4), 'patch9_sha256': sha256(patch9)}, ensure_ascii=False))
