import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

R = Path('D:/作品集/ResearchOS/research-os')
B = Path(__file__).parent
E = R / 'execution/v2.4/receipts/W05/W05-99/online_backup_source_resource_map_codex/20261015-current-chat'
O = E / 'fixture-qualification-intake'
O.mkdir(exist_ok=False)
PY = 'C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe'

def put(p, v):
    with p.open('x', encoding='utf8') as f:
        json.dump(v, f, ensure_ascii=False, indent=2)
        f.write('\n')

def ref(p):
    v = p.read_bytes()
    return {'path': p.relative_to(R).as_posix(), 'bytes': len(v), 'sha256': hashlib.sha256(v).hexdigest()}

def run(n, argv):
    p = O / n
    put(p.with_suffix('.recipe.json'), {'argv': argv, 'cwd': str(R), 'env': {}, 'no_source_or_actual_mutation_authority': True})
    z = subprocess.run(argv, cwd=R, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.with_suffix('.stdout.raw').write_bytes(z.stdout)
    p.with_suffix('.stderr.raw').write_bytes(z.stderr)
    put(p.with_suffix('.result.json'), {'native_exit': z.returncode, 'stdout': ref(p.with_suffix('.stdout.raw')), 'stderr': ref(p.with_suffix('.stderr.raw'))})
    return z

paths = ['AGENTS.md', 'internal/domain/backup.go', 'internal/domain/backup_test.go', 'internal/domain/backup_configuration_upgrade_test.go', 'ops/backup/main.go', 'internal/domain/backup_host_snapshot.go', 'internal/domain/runtime_data_root_lease_windows.go']
put(O / 'reads.recipe.json', {'paths': paths + [str(E / 'SOURCE-MAP.md'), str(E / 'COLLECTION-manifest.json')], 'purpose': 'Prepare finite unchanged-Source online backup fixture qualification only'})
copies = []
for i, path in enumerate(paths):
    p = R / path
    if p.is_file():
        q = O / (str(i).zfill(2) + '-' + p.name + '.source.txt')
        q.write_bytes(p.read_bytes())
        copies.append({'original': ref(p), 'copy': ref(q)})
    else:
        copies.append({'path': path, 'exists': False, 'kind': 'optional_locator_not_failed_read'})
for name in ['SOURCE-MAP.md', 'COLLECTION-manifest.json']:
    q = O / (name + '.copy.txt')
    q.write_bytes((E / name).read_bytes())
    copies.append({'original': ref(E / name), 'copy': ref(q)})
z = run('01-locators', ['rg', '-n', '--glob', '*.go', 'func Test.*Backup|func .*AcquireDataRootLease|func .*HostSnapshot|func .*Restore|CreateBackup\(', 'internal/domain', 'ops/backup'])
assert z.returncode == 0
put(O / 'intake.json', {'copies': copies, 'source_authority': False, 'actual_authority': False, 'formal_increment': 0, 'commands': [ref(O / ('01-locators' + s)) for s in ['.recipe.json', '.stdout.raw', '.stderr.raw', '.result.json']]})
print(json.dumps({'intake': ref(O / 'intake.json'), 'source_map': (E / 'SOURCE-MAP.md').read_text(encoding='utf8'), 'locators': z.stdout.decode('utf8')}, ensure_ascii=False))
