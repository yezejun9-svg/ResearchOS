import hashlib,json
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os');HERE=Path(__file__).resolve().parent;BASE=ROOT/'execution/product-v1/receipts/single-harness-20261104/native-policy-binding';ORIGINAL=BASE/'scope.json';DEST=BASE/'scope.effective-v1.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
s=json.loads(ORIGINAL.read_bytes());wt=Path(s['worktree']);assert not DEST.exists();r=json.loads((HERE/'product-v1-native-policy-binding-author-20261105/final/SOURCE.json').read_bytes())
changed=[p for p,h in s['baseline_sha256'].items() if (sha(wt/p) if (wt/p).is_file() else 'ABSENT_BEFORE')!=h];assert len(changed)==9 and set(changed)<=set(s['production_paths']+s['test_paths'])
effective=dict(s);effective.update(schema_revision=2,original_lease_ref=str(ORIGINAL.relative_to(ROOT)),original_lease_sha256=sha(ORIGINAL),scope_change='NARROW_ACTUAL_DELTA_ONLY; original11file lease and test pins remain immutable',production_paths=[p for p in s['production_paths'] if p in changed],test_paths=[p for p in s['test_paths'] if p in changed],baseline_sha256={p:s['baseline_sha256'][p] for p in changed},reviewed_unchanged_sha256={p:h for p,h in s['baseline_sha256'].items() if p not in changed})
assert len(effective['production_paths'])==6 and len(effective['test_paths'])==3 and set(effective['reviewed_unchanged_sha256'])=={'internal/host/harness_windows.go','internal/host/harness_windows_test.go'}
DEST.write_bytes((json.dumps(effective,ensure_ascii=False,indent=2)+'\n').encode('utf8'));print(json.dumps(dict(path=str(DEST),sha256=sha(DEST),changed=9,unchanged_reviewed=2)))
