import hashlib
import json
from pathlib import Path

task = Path(__file__).resolve().parent.parent
root = Path('D:/作品集/ResearchOS/research-os')
goroot = root / '.local/tools/go1.27.1/go'
out = Path(__file__).resolve().parent
prepared = task / 'cp598-coding-delivery-next-scope'

def record(path):
    raw = path.read_bytes()
    return {'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

frozen = json.loads((prepared / 'MANIFEST.json').read_bytes())
manifest_checks = []
for entry in frozen['entries']:
    actual = record(prepared / entry['path'])
    manifest_checks.append({'path': entry['path'], **actual,
                            'matches': actual['sha256'] == entry['sha256'] and actual['bytes'] == entry['bytes']})
assert all(x['matches'] for x in manifest_checks), manifest_checks
report = json.loads((out / 'design-review.json').read_bytes())
assert report['formal_increment'] == 0
assert report['native_model_database_runs'] == 0
assert report['d_source_or_control_writes'] == 0

repo_paths = [
    'ops/experiment_sandbox/sandbox_windows.go',
    'ops/experiment_sandbox/async_windows.go',
    'internal/domain/runtime_tools.go',
    'internal/domain/runtime_tools_windows.go',
    'internal/host/runtime_check_windows.go',
    'internal/host/runtime_tools_windows.go',
    'internal/host/paths.go',
    'internal/deliverygate/validate.go',
]
go_paths = ['src/os/root.go', 'src/os/root_windows.go',
            'src/os/types_windows.go', 'src/internal/syscall/windows/at_windows.go']
seal = {
    'schema': 'researchos.independent-design-review-inputs.v1',
    'base_head': report['base_head'],
    'source_only': True,
    'formal_increment': 0,
    'frozen_preparation_checks': manifest_checks,
    'preparation_inputs': {name: record(prepared / name) for name in
                           ('NEXT_SLICE.json', 'READINESS.md', 'CLARIFICATION-01.md', 'MANIFEST.json')},
    'source_sha256': {name: record(root / name) for name in repo_paths},
    'goroot_source_sha256': {name: record(goroot / name) for name in go_paths},
    'deliverables': {name: record(out / name) for name in
                     ('design-review.json', 'sandbox-child-drain-review.md')},
    'statement': 'Hashes bind actual existing-source reads and C-only review artifacts; no tests or activation occurred.'
}
target = out / 'review-manifest.json'
assert not target.exists(), 'Never overwrite a sealed review manifest'
target.write_text(json.dumps(seal, ensure_ascii=True, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'manifest': str(target), **record(target), 'deliverables': seal['deliverables'],
                  'preparation_mismatches': 0}, ensure_ascii=True))
