import datetime
import hashlib
import json
from pathlib import Path
import subprocess

R = Path('D:/作品集/ResearchOS/research-os')
E = R / 'execution/v2.4/receipts/W05/W05-99/online_backup_source_resource_map_codex/20261015-current-chat'
E.mkdir(parents=True, exist_ok=False)
BASE = '4f4023c956f84d65743f39ce77d6c8899a21ada1'
index = []


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
    result = {'label': label, 'recipe': ref(recipe), 'stdout': ref(out), 'stderr': ref(err), 'native_exit_code': p.returncode}
    new(E / (label + '.result.json'), result)
    index.append(result)
    assert p.returncode == 0, result
    return out


paths = ['internal/domain/backup.go', 'internal/domain/backup_workspace.go', 'internal/domain/backup_command_queue.go', 'internal/domain/backup_host_configuration.go', 'internal/domain/backup_recovery.go', 'internal/host/backup_windows.go', 'ops/backup/main.go', 'apps/control/main.go']
sources = {}
for i, path in enumerate(paths, 1):
    p = run(f'source-{i:02d}', ['git', '-c', 'maintenance.auto=false', '-c', 'gc.auto=0', 'show', BASE + ':' + path])
    sources[path] = ref(p)
    if path == 'internal/domain/backup.go':
        lines = p.read_text(encoding='utf8').splitlines()
        for a, b in [(290, 361), (362, 493)]:
            print('\n'.join(f'{j+1}: {line}' for j, line in enumerate(lines[a-1:b], a-1)))
    if path == 'ops/backup/main.go':
        print('OPS_BACKUP ' + path)
        print(p.read_text(encoding='utf8'))
for label, pattern, dirs in [
    ('callers', r'CreateBackupWithWorkspaces|CreateBackup\(|/backups|SnapshotWorkspace', ['internal/domain', 'internal/host', 'apps/cli', 'apps/control', 'ops/backup']),
    ('bootstrap-locks', r'AcquireDataRootLease|store.Open|CreateBackup|handleBackup|backup.create|backups', ['apps/control', 'internal/domain', 'ops/backup']),
]:
    p = run(label, ['rg', '-n', '-g', '*.go', '-g', '!**/*_test.go', pattern] + dirs)
    print(label.upper())
    lines = p.read_text(encoding='utf8').splitlines()
    print('\n'.join(lines[:85]))
    if len(lines) > 85:
        print('Selected85lines; fullraw retained: ' + str(p))
new(E / 'source-input-index.json', {'base_commit': BASE, 'source_inputs': sources, 'commands': index, 'actual_DB_API_access': False, 'Source_acceptance': False, 'formal_increment': 0})
print(json.dumps({'source_input_index': ref(E / 'source-input-index.json'), 'source_count': len(paths)}))
