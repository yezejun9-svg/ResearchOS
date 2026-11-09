from pathlib import Path
import hashlib
import json
import shutil

root = Path(__file__).resolve().parent
author = root.parent / 'product-v1-cli-s04-author'
repo = Path('D:/作品集/ResearchOS/research-os')
scope_path = repo / 'execution/product-v1/receipts/single-harness-20261104/cli-s04/scope.json'
scope = json.loads(scope_path.read_text(encoding='utf-8-sig'))
wt = Path(scope['worktree'])
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
manifest_path = author / 'final/source-manifest.json'
assert sha(manifest_path) == '6138822e5c28a596cce3363a8850612e7a81ac119d67bd5659f0da8d349fc99a'
manifest = json.loads(manifest_path.read_text(encoding='utf-8-sig'))
assert manifest['author_stopped_source_changes'] and manifest['base_head'] == scope['base_head']
expected = {'apps/cli/main.go':'b2b6455010fd0c16f37dcb38204978403fe49ade372b4ce969ac5d5ef94faa5a',
            'apps/cli/productv1.go':'9fc3f0272a6c4671ab5caaa3d80d21490be26317b2a1e22cc51e98be9aca4cf4',
            'apps/cli/productv1_test.go':'7636b52a16e0ca72778239361bc85a81d1f2656c81105e49ea07e2a5e2e90af6'}
assert {row['path']:row['sha256'] for row in manifest['pins']} == expected
checks = []
overlay = {}
for name, digest in expected.items():
    frozen = author / 'final/source' / name
    assert sha(frozen) == digest == sha(wt/name)
    snapshot = root / 'source-snapshot' / name
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    assert not snapshot.exists()
    shutil.copyfile(frozen, snapshot)
    overlay[str(wt/name)] = str(snapshot)
    checks.append({'path':name,'sha256':digest,'live_and_author_and_snapshot_match':sha(snapshot)==digest})
contract = repo / 'execution/product-v1/contracts/harness.v1.interface.rev2.json'
assert sha(contract) == '046a49b2b1f82593fe86924913b2ee4d77152ac1cef7dbbb86562f6dfe0cfa1c'
for source, name in [(manifest_path,'author-source-manifest.json'),(scope_path,'scope.json'),(contract,'harness.v1.interface.rev2.json')]:
    shutil.copyfile(source,root/name)
(root/'overlay.json').write_text(json.dumps({'Replace':overlay},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(root/'pin-stage.json').write_text(json.dumps({'base_head':scope['base_head'],'worktree':str(wt),'scope_sha256':sha(scope_path),'author_manifest_sha256':sha(manifest_path),'interface_sha256':sha(contract),'exact3':checks,'all_match':True,'source_writes':0,'real_cli_native_model':0},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'exact3_matches':len(checks),'scope_sha256':sha(scope_path),'source_writes':0}))
