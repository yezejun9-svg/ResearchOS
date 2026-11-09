from pathlib import Path
import hashlib, json, difflib

root = Path(r'D:\作品集\ResearchOS\research-os')
wt = root / '.local/worktrees/product-v1-native-policy-binding-20261105'
out = Path(__file__).resolve().parent / 'test01-source'
scope = json.loads((root / 'execution/product-v1/receipts/single-harness-20261104/native-policy-binding/scope.json').read_text(encoding='utf-8'))
files = {}
for rel in scope['production_paths'] + scope['test_paths']:
    src = wt / rel
    if not src.exists():
        files[rel] = 'ABSENT'; continue
    raw = src.read_bytes()
    dest = out / 'source' / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(raw)
    files[rel] = hashlib.sha256(raw).hexdigest()
    base = root / rel
    old = base.read_bytes() if base.exists() else b''
    patch = ''.join(difflib.unified_diff(old.decode('utf-8').splitlines(True), raw.decode('utf-8').splitlines(True), fromfile='a/'+rel, tofile='b/'+rel))
    patch_path = out / 'patches' / (rel.replace('/', '__') + '.patch')
    patch_path.parent.mkdir(parents=True, exist_ok=True)
    patch_path.write_text(patch, encoding='utf-8', newline='')
(out / 'manifest.json').write_text(json.dumps({'scope_id': scope['scope_id'], 'state': 'f13 test01 input source; no product acceptance implied', 'source_hashes': files, 'baseline_hashes': scope['baseline_sha256']}, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'source_count': len(files), 'archive': str(out), 'policy_hash': files['adapters/runtime/codex_policy.go']}))
