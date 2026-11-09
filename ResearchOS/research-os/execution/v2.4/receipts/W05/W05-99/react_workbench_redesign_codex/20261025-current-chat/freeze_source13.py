"""Validate the exact Source13 staged set and retain a reviewable patch."""
import hashlib
import json
from pathlib import Path
import subprocess

REPO = Path(r"D:\作品集\ResearchOS\research-os\.local\worktrees\react-workbench-redesign-20261025")
OUT = Path(__file__).parent
SCOPE = Path(r"D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\resume_cp528_codex\20261025-current-chat\continuation-cp530\react-workbench-redesign-source-scope.json")


def git(name, *args):
    folder = OUT / "freeze-commands" / name
    folder.mkdir(parents=True, exist_ok=False)
    argv = ["git", "-c", "maintenance.auto=false", "-c", "gc.auto=0", *args]
    (folder / "recipe.json").write_text(json.dumps({"argv": argv, "cwd": str(REPO), "env_overrides": {}}, ensure_ascii=False, indent=2), encoding="utf-8")
    result = subprocess.run(argv, cwd=REPO, capture_output=True, check=False)
    (folder / "stdout.bin").write_bytes(result.stdout)
    (folder / "stderr.bin").write_bytes(result.stderr)
    (folder / "result.json").write_text(json.dumps({"native_exit": result.returncode}, indent=2), encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"{name} failed with {result.returncode}")
    return result.stdout


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    scope_bytes = SCOPE.read_bytes()
    if sha(scope_bytes) != '0483871074cfc46f0484257467324e822c71f3b7b9a5dcf726aa20ac4df85f7b':
        raise RuntimeError('source scope changed')
    scope = json.loads(scope_bytes)
    base = git('01-head', 'rev-parse', 'HEAD').decode().strip()
    if base != scope['base_commit']:
        raise RuntimeError(f'base mismatch: {base}')
    changed = git('02-staged-names', 'diff', '--cached', '--name-only', '-z').decode().strip('\0').split('\0')
    changed = [name for name in changed if name]
    if not changed or not set(changed) <= set(scope['source_allowlist']):
        raise RuntimeError(f'changed set exceeds allowlist: {changed}')
    if git('03-unstaged-names', 'diff', '--name-only'):
        raise RuntimeError('unstaged paths remain')
    if git('04-untracked-names', 'ls-files', '--others', '--exclude-standard'):
        raise RuntimeError('untracked paths remain')
    baseline = {}
    for index, item in enumerate(scope['baseline_source'], 5):
        path = item['path']
        original = git(f'{index:02d}-baseline', 'cat-file', 'blob', f'HEAD:{path}')
        actual = sha(original)
        baseline[path] = {'expected_sha256': item['sha256'], 'actual_sha256': actual, 'matches': actual == item['sha256']}
        if actual != item['sha256'] or len(original) != item['bytes']:
            raise RuntimeError(f'baseline mismatch: {path}')
    patch = git('20-staged-patch', 'diff', '--cached', '--binary', '--full-index')
    (OUT / 'source13.patch').write_bytes(patch)
    changed_hashes = {name: sha((REPO / name).read_bytes()) for name in changed}
    report = {'schema': 'researchos.source13-precommit.v1', 'scope_sha256': sha(scope_bytes), 'base_commit': base,
              'changed_paths': changed, 'changed_sha256': changed_hashes, 'baseline': baseline,
              'patch_path': str(OUT / 'source13.patch'), 'patch_sha256': sha(patch),
              'source_edit_authority': True, 'formal_increment': 0, 'independent_review': 'PENDING'}
    (OUT / 'SOURCE13-precommit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'changed_count': len(changed), 'patch_sha256': sha(patch)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
