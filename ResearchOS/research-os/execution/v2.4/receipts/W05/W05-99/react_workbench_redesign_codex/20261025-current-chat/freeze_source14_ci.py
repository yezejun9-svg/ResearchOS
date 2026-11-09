"""Freeze the authorized CI-only Source14 delta before its append commit."""
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
    folder = OUT / 'source14-pre-commands' / name
    folder.mkdir(parents=True, exist_ok=False)
    argv = ['git', '-c', 'maintenance.auto=false', '-c', 'gc.auto=0', *args]
    (folder / 'recipe.json').write_text(json.dumps({'argv': argv, 'cwd': str(REPO), 'env_overrides': {}}, ensure_ascii=False, indent=2), encoding='utf-8')
    result = subprocess.run(argv, cwd=REPO, capture_output=True, check=False)
    (folder / 'stdout.bin').write_bytes(result.stdout)
    (folder / 'stderr.bin').write_bytes(result.stderr)
    (folder / 'result.json').write_text(json.dumps({'native_exit': result.returncode}, indent=2), encoding='utf-8')
    if result.returncode:
        raise RuntimeError(f'{name} failed with {result.returncode}')
    return result.stdout


def main():
    raw = SCOPE.read_bytes()
    if sha(raw) != '32d51c0ba52c5c02094ae06ca735d188dea2fc0c9f6501f61f4d51bb526a3b24':
        raise RuntimeError('Source14 scope hash changed')
    scope = json.loads(raw)
    head = git('01-source13-head', 'rev-parse', 'HEAD').decode().strip()
    assert head == scope['previous_source13_commit']
    baseline = git('02-ci-baseline', 'cat-file', 'blob', 'HEAD:ops/ci/ui.py')
    pinned = next(item for item in scope['baseline_source'] if item['path'] == 'ops/ci/ui.py')
    assert sha(baseline) == pinned['sha256'] and len(baseline) == pinned['bytes']
    staged = git('03-staged', 'diff', '--cached', '--name-only').decode().splitlines()
    assert staged == ['ops/ci/ui.py']
    assert not git('04-unstaged', 'diff', '--name-only')
    assert not git('05-untracked', 'ls-files', '--others', '--exclude-standard')
    patch = git('06-ci-patch', 'diff', '--cached', '--binary', '--full-index')
    (OUT / 'source14-ci.patch').write_bytes(patch)
    report = {'schema': 'researchos.source14-ci-precommit.v1', 'scope_sha256': sha(raw),
              'source13_commit': head, 'changed_paths': staged, 'ci_baseline_sha256': sha(baseline),
              'ci_new_sha256': sha((REPO / 'ops/ci/ui.py').read_bytes()),
              'ci_patch_sha256': sha(patch), 'probe': 'SOURCE14-CI-PROBE.json', 'formal_increment': 0}
    (OUT / 'SOURCE14-precommit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'changed_paths': staged, 'patch_sha256': sha(patch)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
