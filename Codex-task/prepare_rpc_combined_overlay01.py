import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=Path('D:/作品集/ResearchOS/research-os');WT=ROOT/'.local/worktrees/product-v1-native-rpc-wiring-20261105';OUT=HERE/'product-v1-native-rpc-combined-overlay01';assert not OUT.exists()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
orig=HERE/'product-v1-native-rpc-wiring-author-20261105';rev=HERE/'product-v1-native-rpc-wiring-rev3-tests-20261105';b1=HERE/'product-v1-native-rpc-runtime-author-20261105/rev3-test02-ready'
assert sha(orig/'MANIFEST.json')=='8588e7b60b302c5df8e88d4cadc0e2dc3bd1e94033fa18985317109a73767d22';assert sha(rev/'MANIFEST.json')=='4f9087adf2ce2262c3b3183d3c2f0a4afef8bc9ba47ccbbabcf9f2fb0b377ef8'
rows=read(orig/'MANIFEST.json')['files'];replacements={}
for row in rows:
 ref=row['path'];expected='14cf67c5f5de30a06e77269df40cd6d1e1daa9ffd7d67d19964c57cc15a8f08d' if ref=='internal/domain/runtime_harness_windows_test.go' else row['source_sha256'];assert sha(WT/ref)==expected,ref
scope=read(ROOT/'execution/product-v1/receipts/single-harness-20261104/native-rpc-runtime/scope.json')
for ref in scope['production_paths']+scope['test_paths']:
 f=b1/Path(ref).name;assert f.is_file();replacements[str(WT/ref)]=str(f)
assert sha(b1/'codex_rpc_windows_test.go')=='d7c34e9116c972bee3c90c8a4b36efea72913af62c96d32e66f86a4b1b3322e4'
OUT.mkdir();p=OUT/'overlay.json';p.write_bytes((json.dumps(dict(Replace=replacements),indent=2)+'\n').encode('utf8'));print(json.dumps(dict(overlay=str(p),sha256=sha(p),b1='frozen passing rev3/test02; security fixes pending; this is B2 fixture test only',b2_source_files=len(rows))))
