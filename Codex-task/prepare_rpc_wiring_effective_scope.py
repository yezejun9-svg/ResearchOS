import hashlib,json
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os');BASE=ROOT/'execution/product-v1/receipts/single-harness-20261104/native-rpc-wiring';HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
orig=BASE/'scope.json';am=BASE/'scope.amendment01.json';dest=BASE/'scope.effective-v1.json';assert not dest.exists()
assert sha(orig)=='45f8730e83bbedc0796f2a843dd386ed271dd24a80daf0f3aad6cde985efc096' and sha(am)=='a6aaffc05a37a92d95dc6a9e33e189c920e3b0e1780e73c8fb07b40a148533dd'
s=json.loads(orig.read_bytes());a=json.loads(am.read_bytes());s['production_paths']+=a['added_production_paths'];s['test_paths']+=a['added_test_paths'];s['baseline_sha256'].update(a['baseline_sha256']);s.update(original_lease_ref=str(orig.relative_to(ROOT)),original_lease_sha256=sha(orig),amendment_ref=str(am.relative_to(ROOT)),amendment_sha256=sha(am),effective_scope_role='EXACT_UNION_ORIGINAL_LEASE_AND_PRE_REGISTERED_NAMED_JOURNAL_AMENDMENT_NO_NEW_AUTHORITY')
r=json.loads((HERE/'product-v1-native-rpc-wiring-final-review-20261105/review-report.json').read_bytes());assert set(r['source_sha256'])==set(s['production_paths']+s['test_paths']) and len(r['source_sha256'])==8
dest.write_bytes((json.dumps(s,ensure_ascii=False,indent=2)+'\n').encode('utf8'));print(json.dumps(dict(scope_ref=str(dest.relative_to(ROOT)),sha256=sha(dest),source_files=8,status='INTEGRATION_INPUT_PREPARED_NOT_INTEGRATED')))
