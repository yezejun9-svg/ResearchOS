from pathlib import Path
import hashlib, json

root = Path(r'D:\作品集\ResearchOS\research-os')
wt = root / '.local/worktrees/product-v1-native-policy-binding-20261105'
out = Path(__file__).resolve().parent / 'prior-mode-key'
scope = json.loads((root / 'execution/product-v1/receipts/single-harness-20261104/native-policy-binding/scope.json').read_text(encoding='utf-8'))
paths = [p for p in scope['production_paths'] + scope['test_paths'] if (wt / p).exists()]
files = {}
for rel in paths:
    raw = (wt / rel).read_bytes()
    dest = out / 'source' / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(raw)
    files[rel] = hashlib.sha256(raw).hexdigest()
record = {'diagnostic_id': 'native-policy-A:mode-key-wrong-namespace', 'state': 'source-only candidate, no Native or Go execution', 'issue': 'MXC option used permissions.researchos-readonly.windows.sandbox instead of global windows.sandbox', 'source_hashes': files, 'baseline_hashes': scope['baseline_sha256']}
(out / 'diagnostic.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'archive': str(out), 'files': len(files), 'policy_hash': files.get('adapters/runtime/codex_policy.go')}))
