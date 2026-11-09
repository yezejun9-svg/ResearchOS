from pathlib import Path
import hashlib
import json
import sys

root = Path(__file__).resolve().parent
scope_path = Path('D:/作品集/ResearchOS/research-os/execution/product-v1/receipts/single-harness-20261104/workbench/scope.json')
scope = json.loads(scope_path.read_text(encoding='utf-8-sig'))
wt = Path(scope['worktree'])
attempt = sys.argv[1]
receipt = root / ('install-' + attempt + '.json')
if receipt.exists():
    raise SystemExit('INSTALL_RECEIPT_ALREADY_EXISTS')
names = scope['production_paths'] + (scope['test_paths'] if '--tests' in sys.argv else [])
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else 'ABSENT_BEFORE'
previous = {}
for record in sorted(root.glob('install-*.json')):
    prior = json.loads(record.read_text(encoding='utf-8'))
    for item in prior.get('written', []):
        previous[item['path']] = item['sha256']
for name in names:
    candidate = root / 'candidate' / name
    if not candidate.is_file():
        raise SystemExit('CANDIDATE_ABSENT: ' + name)
    expected = previous.get(name, scope['baseline_sha256'][name])
    if sha(wt / name) != expected:
        raise SystemExit('CURRENT_SOURCE_DRIFT: ' + name)
report = {'scope_sha256': sha(scope_path), 'attempt': attempt, 'written': [], 'complete': False}
try:
    for name in names:
        target = wt / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((root / 'candidate' / name).read_bytes())
        report['written'].append({'path': name, 'sha256': sha(target)})
    report['complete'] = True
finally:
    receipt.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'complete': report['complete'], 'written': len(report['written']), 'receipt': str(receipt)}))
