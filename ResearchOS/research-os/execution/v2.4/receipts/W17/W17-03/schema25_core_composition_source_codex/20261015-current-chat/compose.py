"""Apply only frozen COMPOSITION-MAP blobs to an exclusive 4f worktree."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path('D:/作品集/ResearchOS/research-os')
SOURCE = ROOT / '.local/worktrees/schema25-core-composition-20261015'
HERE = ROOT / 'execution/v2.4/receipts/W17/W17-03/schema25_core_composition_source_codex/20261015-current-chat'
SCOPE = ROOT / 'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp492/four-branch-source-composition-scope.json'
MAP = ROOT / 'execution/v2.4/receipts/W17/W17-03/composition_map_independent_codex/20261015-current-chat/COMPOSITION-MAP.json'
MAIN = '4f4023c956f84d65743f39ce77d6c8899a21ada1'
TREE = '3db13a15cc52b2b0bd75cae3452c66509a9f55c9'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def file_ref(path):
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': digest(path.read_bytes())}

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')

def need(ok, why):
    if not ok:
        raise RuntimeError(why)

def git(*args):
    return subprocess.check_output(['git', '-c', 'maintenance.auto=false', '-c', 'gc.auto=0', *args], cwd=SOURCE)

def current(path):
    target = SOURCE / path
    return target.read_bytes() if target.exists() else None

def verify(raw, expected, label):
    if expected is None:
        need(raw is None, label + ': expected absent')
        return
    need(raw is not None, label + ': missing')
    need(len(raw) == expected['bytes'] and digest(raw) == expected['sha256'] and
         hashlib.sha1(f'blob {len(raw)}\0'.encode() + raw).hexdigest() == expected['blob'], label + ': hash mismatch')

def main():
    need(digest(SCOPE.read_bytes()) == '49235b6c2c5c627e1ddc7be06eef8dc8018e5ac9025a8a3db0ba27db687b04f4', 'scope hash')
    need(digest(MAP.read_bytes()) == '4580099f8f80b2171c5a2cd5a8932f7ce075979cbfc7aa6b843dbca8fa5a920c', 'map hash')
    scope, plan = json.loads(SCOPE.read_bytes()), json.loads(MAP.read_bytes())
    need(scope['bounded_builder_scope']['source_paths'] == plan['bounded_builder_scope']['source_paths'], 'scope/map path list')
    need(git('rev-parse', 'HEAD').decode().strip() == MAIN and git('rev-parse', 'HEAD^{tree}').decode().strip() == TREE, 'worktree base')
    need(git('status', '--porcelain=v1', '--untracked-files=no') == b'', 'worktree dirty before composition')
    allowed = set(plan['bounded_builder_scope']['source_paths'])
    need(len(allowed) == 53 and len(plan['stages']) == 4 and
         [s['name'] for s in plan['stages']] == ['storage25', 'native25', 'core', 'bridge'], 'stage plan')
    union = {row['path'] for stage in plan['stages'] for row in stage['files']}
    need(union == allowed and sum(len(s['files']) for s in plan['stages']) == 54, 'stage scope')
    protected = {row['path']: row['main'] for row in plan['main']['protected']}
    need(len(protected) == 10 and set(protected) == set(scope['bounded_builder_scope']['protected_main_paths']), 'protected set')
    for path, expected in protected.items():
        verify(current(path), expected, 'protected-before:' + path)
    stage_refs = []
    for ordinal, stage in enumerate(plan['stages'], 1):
        need(len(stage['files']) == stage['scope_count'], 'stage count:' + stage['name'])
        writes = []
        for row in stage['files']:
            rel = row['path']
            need(rel in allowed and row['action'] == 'APPLY_EXACT_ACCEPTED_DELTA', 'unexpected action:' + rel)
            verify(current(rel), row['expected_before'], 'stage-precondition:' + stage['name'] + ':' + rel)
            raw = git('cat-file', 'blob', row['candidate']['blob'])
            verify(raw, row['candidate'], 'candidate-object:' + stage['name'] + ':' + rel)
            writes.append((rel, raw, row))
        for rel, raw, row in writes:
            path = SOURCE / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
            verify(current(rel), row['candidate'], 'stage-readback:' + stage['name'] + ':' + rel)
        for path, expected in protected.items():
            verify(current(path), expected, 'protected-after:' + stage['name'] + ':' + path)
        changed = set(git('diff', '--name-only', '--', '.').decode().splitlines())
        untracked = set(git('ls-files', '--others', '--exclude-standard').decode().splitlines())
        need(changed | untracked <= allowed, 'out-of-scope delta after:' + stage['name'])
        report = {'schema': 'researchos.schema25-composition-stage/1', 'at': dt.datetime.now(dt.timezone.utc).isoformat(),
                  'stage': stage['name'], 'ordinal': ordinal, 'source_commit': MAIN,
                  'stage_head': stage['head'], 'stage_tree': stage['tree'],
                  'path_count': len(writes), 'paths': [{'path': rel, 'expected_before': row['expected_before'],
                    'candidate': row['candidate']} for rel, _, row in writes],
                  'protected_count': len(protected), 'changed_tracked_count': len(changed),
                  'untracked_allowed_count': len(untracked), 'precondition': 'PASS', 'readback': 'PASS'}
        path = HERE / f'stage-{ordinal:02d}-{stage["name"]}.json'
        write(path, report)
        stage_refs.append(file_ref(path))
    for path, expected in plan['bounded_builder_scope']['expected_final_blobs'].items():
        verify(current(path), expected, 'final:' + path)
    need(len(plan['bounded_builder_scope']['expected_final_blobs']) == 53, 'final blob count')
    need(git('hash-object', '--', 'internal/domain/backup.go').decode().strip() == '3ddc9e42a9f443cb3cb61370bde4c979cf11060b', 'backup final blob')
    changed = set(git('diff', '--name-only', '--', '.').decode().splitlines())
    untracked = set(git('ls-files', '--others', '--exclude-standard').decode().splitlines())
    need(changed | untracked == allowed, 'final exact53 delta')
    write(HERE / 'composition-result.json', {'schema': 'researchos.schema25-core-source-composition/1',
          'at': dt.datetime.now(dt.timezone.utc).isoformat(), 'source_base_commit': MAIN, 'source_base_tree': TREE,
          'scope': file_ref(SCOPE), 'independent_map': file_ref(MAP), 'stage_receipts': stage_refs,
          'changed_paths_exact': sorted(allowed), 'protected_main_count': len(protected),
          'final_blobs_match': True, 'backup_go_final_source': 'f80955594bdd0373ae1c961cd02ab6be96f2c196',
          'status': 'COMPOSED_UNTESTED_UNCOMMITTED', 'formal_increment': 0})
    print(json.dumps({'status': 'COMPOSED_UNTESTED_UNCOMMITTED', 'changed_paths': len(allowed),
                      'stages': len(stage_refs), 'formal_increment': 0}))

if __name__ == '__main__':
    main()
