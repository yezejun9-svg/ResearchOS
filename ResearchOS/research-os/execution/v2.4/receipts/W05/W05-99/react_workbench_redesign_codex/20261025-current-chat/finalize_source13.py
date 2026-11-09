"""Freeze Source13 commit, tree, clean status, and evidence boundaries."""
import hashlib
import json
from pathlib import Path
import subprocess

REPO = Path(r"D:\作品集\ResearchOS\research-os\.local\worktrees\react-workbench-redesign-20261025")
OUT = Path(__file__).parent
pre = json.loads((OUT / 'SOURCE13-precommit.json').read_text(encoding='utf-8'))


def git(name, *args):
    folder = OUT / 'final-commands' / name
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


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    commit = git('01-commit', 'rev-parse', 'HEAD').decode().strip()
    parent = git('02-parent', 'rev-parse', 'HEAD^').decode().strip()
    tree = git('03-tree', 'rev-parse', 'HEAD^{tree}').decode().strip()
    branch = git('04-branch', 'branch', '--show-current').decode().strip()
    status = git('05-status', 'status', '--porcelain=v1', '--untracked-files=all').decode()
    names = git('06-commit-paths', 'diff-tree', '--no-commit-id', '--name-only', '-r', '-z', 'HEAD').decode().strip('\0').split('\0')
    names = [name for name in names if name]
    if parent != pre['base_commit'] or branch != 'react-workbench-redesign-20261025' or status or names != pre['changed_paths']:
        raise RuntimeError('commit, branch, path set, or worktree clean check failed')
    if sha((OUT / 'source13.patch').read_bytes()) != pre['patch_sha256']:
        raise RuntimeError('precommit patch changed')
    source = {}
    for index, path in enumerate(names, 10):
        blob = git(f'{index:02d}-blob', 'cat-file', 'blob', f'HEAD:{path}')
        value = sha(blob)
        source[path] = value
        if value != pre['changed_sha256'][path]:
            raise RuntimeError(f'committed blob differs: {path}')
    dist = REPO / 'apps/web/dist'
    bundles = {str(file.relative_to(dist)).replace('\\', '/'): sha(file.read_bytes()) for file in sorted(dist.rglob('*')) if file.is_file()}
    report = {'schema': 'researchos.source13-final.v1', 'base_commit': parent, 'commit': commit, 'tree': tree,
              'branch': branch, 'clean': not bool(status), 'source_paths': names, 'source_sha256': source,
              'scope_sha256': pre['scope_sha256'], 'patch_sha256': pre['patch_sha256'], 'dist_sha256': bundles,
              'source_authority': True, 'fixture_browser': 'PASS', 'real_isolated_core_owner_sqlite_ui': 'PASS',
              'native_desktop': 'NOT_RUN', 'independent_review': 'PENDING', 'formal_increment': 0}
    (OUT / 'SOURCE13-final.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'commit': commit, 'tree': tree, 'clean': True, 'paths': len(names)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
