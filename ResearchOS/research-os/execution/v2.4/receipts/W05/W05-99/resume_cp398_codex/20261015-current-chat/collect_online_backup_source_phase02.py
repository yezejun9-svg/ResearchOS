import datetime
import hashlib
import json
from pathlib import Path
import subprocess

R = Path('D:/作品集/ResearchOS/research-os')
E = R / 'execution/v2.4/receipts/W05/W05-99/online_backup_source_resource_map_codex/20261015-current-chat/phase02'
E.mkdir(exist_ok=False)
BASE = '4f4023c956f84d65743f39ce77d6c8899a21ada1'
records = []


def ref(p):
    b = p.read_bytes()
    return {'path': p.relative_to(R).as_posix(), 'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b)}


def new(p, v):
    with p.open('x', encoding='utf8') as f:
        json.dump(v, f, ensure_ascii=False, indent=2)
        f.write('\n')


def run(label, argv):
    recipe = E / (label + '.recipe.json')
    new(recipe, {'argv': argv, 'cwd': str(R), 'env_override': {}, 'read_only_source_query': True, 'actual_DB_API_access': False, 'at': datetime.datetime.now(datetime.timezone.utc).isoformat()})
    out, err = E / (label + '.stdout.raw'), E / (label + '.stderr.raw')
    with out.open('xb') as fo, err.open('xb') as fe:
        p = subprocess.run(argv, cwd=R, stdout=fo, stderr=fe)
    result = {'recipe': ref(recipe), 'stdout': ref(out), 'stderr': ref(err), 'native_exit_code': p.returncode}
    new(E / (label + '.result.json'), result)
    records.append(result)
    assert p.returncode == 0, result
    return out


p = run('host-constructor-locator', ['rg', '-n', '-g', '*.go', '-g', '!**/*_test.go', '^func New\(|^func .*SnapshotWorkspace|^func .*acquire.*[Ll]ock', 'internal/host'])
print(p.read_text(encoding='utf8'))
paths = sorted(set(line.split(':', 1)[0].replace('\\', '/') for line in p.read_text(encoding='utf8').splitlines() if 'func New(' in line))
paths += ['internal/store/sqlite.go', 'internal/host/backup_windows.go', 'internal/domain/backup_command_queue.go', 'internal/domain/backup_workspace.go']
for i, path in enumerate(paths):
    p = run('source-' + str(i), ['git', '-c', 'maintenance.auto=false', '-c', 'gc.auto=0', 'show', BASE + ':' + path])
    lines = p.read_text(encoding='utf8').splitlines()
    if path == 'internal/domain/backup_workspace.go':
        chosen = [(80, 120), (160, 229)]
    elif path == 'internal/store/sqlite.go':
        chosen = [(1, 150)]
    elif path == 'internal/host/backup_windows.go':
        chosen = [(1, 144)]
    elif path == 'internal/domain/backup_command_queue.go':
        chosen = [(1, 110)]
    else:
        selected = next(j for j, line in enumerate(lines) if line.startswith('func New('))
        chosen = [(selected + 1, selected + 135)]
    print('SOURCE ' + path)
    for a, b in chosen:
        print('\n'.join(f'{j+1}: {line}' for j, line in enumerate(lines[a-1:b], a-1)))
new(E / 'source-input-index.json', {'base_commit': BASE, 'records': records, 'actual_DB_API_access': False, 'formal_increment': 0})
print(json.dumps({'index': ref(E / 'source-input-index.json')}))
