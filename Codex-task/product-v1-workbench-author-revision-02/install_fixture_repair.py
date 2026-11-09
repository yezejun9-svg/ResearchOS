from pathlib import Path
import hashlib
import json

root = Path(__file__).resolve().parent
baseline = json.loads((root / 'baseline-review.json').read_text(encoding='utf-8'))
wt = Path(baseline['worktree'])
expected = dict(baseline['baseline_sha256'])
expected.update({row['path']: row['sha256'] for row in json.loads((root / 'install-01.json').read_text(encoding='utf-8'))['written']})
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
assert not (root / 'install-02.json').exists()
assert all(sha(wt / name) == digest for name, digest in expected.items())
name = 'tests/ui/desktop/harness-workbench.test.mjs'
(wt / name).write_bytes((root / 'candidate' / name).read_bytes())
report = {'path': name, 'before_sha256': expected[name], 'after_sha256': sha(wt/name), 'only_fixture_changed': True}
(root / 'install-02.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report))
