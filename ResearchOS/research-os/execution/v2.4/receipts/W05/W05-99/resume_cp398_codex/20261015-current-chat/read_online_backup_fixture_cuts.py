import hashlib
import json
from pathlib import Path
import subprocess

R = Path('D:/作品集/ResearchOS/research-os')
O = R / 'execution/v2.4/receipts/W05/W05-99/online_backup_source_resource_map_codex/20261015-current-chat/fixture-qualification-intake02'
O.mkdir(exist_ok=False)
reads = {
    'internal/domain/backup_test.go': [(1, 160)],
    'internal/domain/backup_cli_test.go': [(1, 210)],
    'internal/domain/backup_workspace.go': [(1, 160)],
    'internal/domain/runtime_model_stream_test.go': [(1, 100)],
    'ops/backup/main.go': [(1, 280)],
}
def put(p, v):
    with p.open('x', encoding='utf8') as f:
        json.dump(v, f, ensure_ascii=False, indent=2)
        f.write('\n')
def ref(p):
    v = p.read_bytes()
    return {'path': p.relative_to(R).as_posix(), 'sha256': hashlib.sha256(v).hexdigest(), 'bytes': len(v)}
put(O / 'reads.recipe.json', {'reads': reads, 'actual_authority': False})
items = {}
for path, spans in reads.items():
    p = R / path
    lines = p.read_text(encoding='utf8').splitlines()
    text = '\n'.join(f'{n}: {line}' for a,b in spans for n,line in enumerate(lines,1) if a <= n <= b)
    q = O / (p.name + '.selected.txt')
    q.write_text(text, encoding='utf8')
    items[path] = {'source': ref(p), 'selected': ref(q)}
argv = ['rg', '-n', '--glob', '*.go', r'func .*AcquireDataRootLease|func .*newFixture|func .*newRuntimeFixture|type .*Fixture|func .*HostSnapshot|func .*SnapshotWorkspace', 'internal/runtime', 'internal/domain', 'internal/host']
put(O / '01-locators.recipe.json', {'argv': argv, 'cwd': str(R), 'env': {}})
z = subprocess.run(argv,cwd=R,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
(O/'01-locators.stdout.raw').write_bytes(z.stdout)
(O/'01-locators.stderr.raw').write_bytes(z.stderr)
put(O/'01-locators.result.json', {'native_exit': z.returncode})
assert z.returncode == 0
put(O/'intake.json', {'items': items, 'locators': [ref(O/('01-locators'+s)) for s in ['.recipe.json','.stdout.raw','.stderr.raw','.result.json']]})
print(json.dumps({'intake': ref(O/'intake.json'), 'selections': {p:(O/(Path(p).name+'.selected.txt')).read_text(encoding='utf8') for p in reads}, 'locators': z.stdout.decode('utf8')},ensure_ascii=False))
