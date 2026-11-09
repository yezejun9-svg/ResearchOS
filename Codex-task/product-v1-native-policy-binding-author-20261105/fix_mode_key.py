from pathlib import Path
import hashlib, json

wt = Path(r'D:\作品集\ResearchOS\research-os\.local\worktrees\product-v1-native-policy-binding-20261105')
archive = Path(__file__).resolve().parent / 'prior-mode-key'
prior = json.loads((archive / 'diagnostic.json').read_text(encoding='utf-8'))['source_hashes']
for rel in ['adapters/runtime/codex_policy.go', 'adapters/runtime/codex_policy_test.go', 'internal/domain/runtime_harness_windows_test.go']:
    p = wt / rel
    raw = p.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == prior[rel], rel
    before = b'permissions.researchos-readonly.windows.sandbox'
    assert raw.count(before) == 1, (rel, raw.count(before))
    p.write_bytes(raw.replace(before, b'windows.sandbox'))
    print(rel, hashlib.sha256(p.read_bytes()).hexdigest())
