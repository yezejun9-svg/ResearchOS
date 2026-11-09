"""Stage and locally commit the exact 53 frozen composition paths only."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path('D:/作品集/ResearchOS/research-os')
SOURCE = ROOT / '.local/worktrees/schema25-core-composition-20261015'
HERE = Path(__file__).resolve().parent
MAP = ROOT / 'execution/v2.4/receipts/W17/W17-03/composition_map_independent_codex/20261015-current-chat/COMPOSITION-MAP.json'
BASE = '4f4023c956f84d65743f39ce77d6c8899a21ada1'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run(name, args):
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    argv = ['git', '-c', 'maintenance.auto=false', '-c', 'gc.auto=0', *args]
    proc = subprocess.run(argv, cwd=SOURCE, capture_output=True)
    stdout, stderr = HERE / (name + '.stdout'), HERE / (name + '.stderr')
    stdout.write_bytes(proc.stdout)
    stderr.write_bytes(proc.stderr)
    row = {'argv': argv, 'cwd': str(SOURCE), 'started_at': started,
           'ended_at': dt.datetime.now(dt.timezone.utc).isoformat(),
           'native_exit': proc.returncode,
           'stdout': {'bytes': stdout.stat().st_size, 'sha256': sha(stdout)},
           'stderr': {'bytes': stderr.stat().st_size, 'sha256': sha(stderr)}}
    with (HERE / (name + '.json')).open('x', encoding='utf-8', newline='\n') as f:
        json.dump(row, f, ensure_ascii=False, indent=2)
        f.write('\n')
    if proc.returncode:
        raise RuntimeError(name + ': ' + proc.stderr.decode('utf-8', 'replace')[-500:])
    return proc.stdout.decode('utf-8', 'replace').strip()

def main():
    plan = json.loads(MAP.read_bytes())
    paths = sorted(plan['bounded_builder_scope']['source_paths'])
    if len(paths) != 53 or len(set(paths)) != 53:
        raise RuntimeError('map paths')
    if run('commit-pre-head', ['rev-parse', 'HEAD']) != BASE:
        raise RuntimeError('HEAD changed')
    run('commit-stage', ['add', '--', *paths])
    staged = run('commit-staged-paths', ['diff', '--cached', '--name-only']).splitlines()
    if staged != paths:
        raise RuntimeError('staged paths differ from exact53')
    run('commit-diff-check', ['diff', '--cached', '--check'])
    run('commit-local', ['commit', '-m', 'Compose frozen schema25, native pause, core and bridge sources'])
    head = run('commit-post-head', ['rev-parse', 'HEAD'])
    tree = run('commit-post-tree', ['rev-parse', 'HEAD^{tree}'])
    delta = run('commit-post-delta', ['diff', '--name-only', BASE, head]).splitlines()
    if delta != paths:
        raise RuntimeError('committed delta differs from exact53')
    if run('commit-post-status', ['status', '--porcelain=v1', '--untracked-files=no']) != '':
        raise RuntimeError('candidate tracked dirty after commit')
    with (HERE / 'candidate-commit.json').open('x', encoding='utf-8', newline='\n') as f:
        json.dump({'schema': 'researchos.schema25-combined-candidate-commit/1',
                   'base': BASE, 'commit': head, 'tree': tree, 'changed_paths_exact': paths,
                   'status': 'CLEAN_CANDIDATE_UNTESTED', 'main_integration': False,
                   'formal_increment': 0}, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print(json.dumps({'status': 'CLEAN_CANDIDATE_UNTESTED', 'commit': head, 'tree': tree,
                      'changed_paths': len(paths)}))

if __name__ == '__main__':
    main()
