from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parent
REPO = Path('D:/作品集/ResearchOS/research-os')
WT = REPO / '.local/worktrees/product-v1-workbench-20261104'
SCOPE = REPO / 'execution/product-v1/receipts/single-harness-20261104/workbench/scope.json'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

scope = json.loads(SCOPE.read_text(encoding='utf-8-sig'))
checks = []
for name in scope['production_paths'] + scope['test_paths']:
    path = WT / name
    actual = digest(path) if path.exists() else 'ABSENT_BEFORE'
    expected = scope['baseline_sha256'][name]
    checks.append({'path': name, 'expected': expected, 'actual': actual, 'matched': actual == expected})
    if actual != expected:
        raise SystemExit('BASELINE_MISMATCH: ' + name)
    if path.exists():
        target = ROOT / 'baseline' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and target.read_bytes() != path.read_bytes():
            raise SystemExit('BASELINE_COPY_CONFLICT: ' + name)
        target.write_bytes(path.read_bytes())

report = {'scope_path': str(SCOPE), 'scope_sha256': digest(SCOPE), 'worktree': str(WT),
          'base_head': scope['base_head'], 'checks': checks, 'all_matched': True,
          'native_runs': 0, 'model_runs': 0, 'source_writes': 0}
(ROOT / 'baseline-check.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'all_matched': True, 'paths': len(checks), 'scope_sha256': report['scope_sha256']}))
