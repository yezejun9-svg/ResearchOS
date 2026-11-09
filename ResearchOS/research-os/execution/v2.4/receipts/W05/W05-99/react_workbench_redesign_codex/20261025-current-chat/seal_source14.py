"""One final seal for the two-commit Source14 candidate."""
import hashlib
import json
from pathlib import Path
import subprocess

REPO = Path(r'D:\作品集\ResearchOS\research-os\.local\worktrees\react-workbench-redesign-20261025')
OUT = Path(__file__).parent
SCOPE = Path(r'D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\resume_cp528_codex\20261025-current-chat\continuation-cp534\react-workbench-redesign-source14-scope.json')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git(name, *args):
    folder = OUT / 'source14-seal-commands' / name
    folder.mkdir(parents=True, exist_ok=False)
    argv = ['git', '-c', 'maintenance.auto=false', '-c', 'gc.auto=0', *args]
    (folder / 'recipe.json').write_text(json.dumps({'argv': argv, 'cwd': str(REPO), 'env_overrides': {}}, ensure_ascii=False, indent=2), encoding='utf-8')
    result = subprocess.run(argv, cwd=REPO, capture_output=True, check=False)
    (folder / 'stdout.bin').write_bytes(result.stdout)
    (folder / 'stderr.bin').write_bytes(result.stderr)
    (folder / 'result.json').write_text(json.dumps({'native_exit': result.returncode}, indent=2), encoding='utf-8')
    if result.returncode:
        raise RuntimeError(f'{name} failed: {result.returncode}')
    return result.stdout


def main():
    scope_raw = SCOPE.read_bytes()
    assert sha(scope_raw) == '32d51c0ba52c5c02094ae06ca735d188dea2fc0c9f6501f61f4d51bb526a3b24'
    scope = json.loads(scope_raw)
    source13 = json.loads((OUT / 'SOURCE13-final.json').read_text(encoding='utf-8'))
    pre = json.loads((OUT / 'SOURCE14-precommit.json').read_text(encoding='utf-8'))
    probe = json.loads((OUT / 'SOURCE14-CI-PROBE.json').read_text(encoding='utf-8'))
    assert probe['status'] == 'PASS'
    commit = git('01-head', 'rev-parse', 'HEAD').decode().strip()
    parent = git('02-parent', 'rev-parse', 'HEAD^').decode().strip()
    tree = git('03-tree', 'rev-parse', 'HEAD^{tree}').decode().strip()
    branch = git('04-branch', 'branch', '--show-current').decode().strip()
    status = git('05-clean-status', 'status', '--porcelain=v1', '--untracked-files=all').decode()
    ci_only = git('06-ci-only-paths', 'diff-tree', '--no-commit-id', '--name-only', '-r', 'HEAD').decode().splitlines()
    full = git('07-full-paths', 'diff', '--name-only', scope['base_commit'], 'HEAD').decode().splitlines()
    assert parent == scope['previous_source13_commit'] == source13['commit']
    assert branch == scope['branch'] and not status and ci_only == ['ops/ci/ui.py']
    assert len(full) == 12 and set(full) == set(source13['source_paths']) | {'ops/ci/ui.py'}
    assert set(full) <= set(scope['source_allowlist'])
    for index, (path, expected) in enumerate(source13['source_sha256'].items(), 10):
        actual = sha(git(f'{index:02d}-source13-blob', 'cat-file', 'blob', f'HEAD:{path}'))
        assert actual == expected, path
    ci_blob = git('30-ci-blob', 'cat-file', 'blob', 'HEAD:ops/ci/ui.py')
    assert sha(ci_blob) == pre['ci_new_sha256']
    for index, name in enumerate(('apps/web/src/continuity.jsx', 'tests/ui/desktop/w13-react.test.js'), 31):
        pinned = next(item['sha256'] for item in scope['baseline_source'] if item['path'] == name)
        assert sha(git(f'{index:02d}-unchanged-blob', 'cat-file', 'blob', f'HEAD:{name}')) == pinned
    patch = git('40-full-patch', 'diff', '--binary', '--full-index', scope['base_commit'], 'HEAD')
    (OUT / 'source14-full.patch').write_bytes(patch)
    active_dist = json.loads((OUT / 'CLEANUP.json').read_text(encoding='utf-8'))['active_dist_sha256']
    for name, expected in active_dist.items():
        assert sha((REPO / 'apps/web/dist' / name).read_bytes()) == expected
    seal = {'schema': 'researchos.react-workbench-source14-seal.v1', 'status': 'SOURCE_FROZEN',
            'scope_sha256': sha(scope_raw), 'base_commit': scope['base_commit'],
            'source13_commit': parent, 'source14_ci_commit': commit, 'final_commit': commit, 'final_tree': tree,
            'branch': branch, 'worktree': str(REPO), 'clean': True,
            'allowed_paths': len(scope['source_allowlist']), 'actual_changed_paths': full, 'actual_changed_count': len(full),
            'ci_only_paths': ci_only, 'source_sha256': {path: sha((REPO / path).read_bytes()) for path in full},
            'ci_new_sha256': sha(ci_blob), 'ci_delta_patch_sha256': pre['ci_patch_sha256'],
            'full_patch_sha256': sha(patch), 'active_dist_sha256': active_dist,
            'ci_ast_probe_sha256': sha((OUT / 'SOURCE14-CI-PROBE.json').read_bytes()),
            'browser_fixture': {'status': 'PASS', 'report': 'browser-fixture-05/report.json', 'checks': 60, 'screenshots': 12},
            'real_isolated_core_sqlite_owner_ui': {'status': 'PASS', 'report': 'real-isolated-03/report.json', 'checks': 5},
            'w13_react_unit': {'status': 'PASS', 'receipt': 'commands/20261025T143226-w13-react-node-test-5c38d89a', 'tests': 5},
            'build': {'status': 'PASS', 'receipt': 'commands/20261025T143549-npm-build-final-5059427c'},
            'native_desktop': 'NOT_RUN', 'independent_source_review': 'PENDING', 'formal_increment': 0}
    (OUT / 'SOURCE14-SEAL.json').write_text(json.dumps(seal, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'commit': commit, 'tree': tree, 'paths': len(full), 'clean': True, 'patch_sha256': sha(patch)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
