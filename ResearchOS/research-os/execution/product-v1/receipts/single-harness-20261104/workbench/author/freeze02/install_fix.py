from pathlib import Path
import hashlib
import json

root = Path(__file__).resolve().parent
baseline = json.loads((root / 'baseline-review.json').read_text(encoding='utf-8'))
wt = Path(baseline['worktree'])
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
receipt = root / 'install-01.json'
assert not receipt.exists()
changed = []
for name, digest in baseline['baseline_sha256'].items():
    assert sha(wt / name) == digest
    if sha(root / 'candidate' / name) != digest:
        changed.append(name)
assert set(changed) == {'apps/web/src/workbench.jsx', 'tests/ui/desktop/harness-workbench.test.mjs'}
report = {'written': [], 'unchanged_paths': sorted(set(baseline['baseline_sha256']) - set(changed)), 'complete': False}
try:
    for name in changed:
        (wt / name).write_bytes((root / 'candidate' / name).read_bytes())
        report['written'].append({'path': name, 'sha256': sha(wt / name)})
    report['complete'] = True
finally:
    receipt.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report))
