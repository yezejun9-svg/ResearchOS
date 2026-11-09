from pathlib import Path
import hashlib
import json

root = Path(__file__).resolve().parent
name = 'tests/ui/desktop/harness-workbench.test.mjs'
target = root / 'candidate' / name
prior = root / 'attempt-01/failing-source' / name
prior.parent.mkdir(parents=True, exist_ok=True)
prior.write_bytes(target.read_bytes())
ui = 'apps/web/src/workbench.jsx'
saved_ui = root / 'attempt-01/failing-source' / ui
saved_ui.parent.mkdir(parents=True, exist_ok=True)
saved_ui.write_bytes((root / 'candidate' / ui).read_bytes())
raw = target.read_bytes()
before = b'removeEventListener() {}, changed() {}, tick() {}, document:'
after = b'removeEventListener() {}, changed() {}, tick() {}, visible() {}, document:'
assert raw.count(before) == 1
target.write_bytes(raw.replace(before, after))
wt = Path(json.loads((root / 'baseline-review.json').read_text(encoding='utf-8'))['worktree'])
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
old = json.loads((root / 'install-01.json').read_text(encoding='utf-8'))
for row in old['written']:
    assert sha(wt / row['path']) == row['sha256']
assert sha(prior) == next(row['sha256'] for row in old['written'] if row['path'] == name)
print(json.dumps({'repair':'VM visible callback only; assertions unchanged','before':sha(prior),'after':sha(target)}))
