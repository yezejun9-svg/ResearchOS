from pathlib import Path
import hashlib
import json
import shutil

base=Path(__file__).resolve().parent
root=base/'revision-02';root.mkdir(exist_ok=False)
author=base.parent/'product-v1-cli-s04-author'
repo=Path('D:/作品集/ResearchOS/research-os')
scope_path=repo/'execution/product-v1/receipts/single-harness-20261104/cli-s04/scope.json'
scope=json.loads(scope_path.read_text(encoding='utf-8-sig'));wt=Path(scope['worktree'])
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
metadata={
 'final-02/source-manifest.json':'ed50c9c8c75c40ebd964065cd9748ba93e5a04dca154812f128fad7758ebb90c',
 'final-02/freeze.json':'f610c711c16d5ce60db99e8d9470c11db1dc5b79f6d5d49c673ac596351b182b',
 'final-02/summary.json':'5118933642104d9abc42e2da401d2611ddccac9d098f9c00762dc01dfe441459',
 'diagnostics-02.json':'f11503dcbf074f23ea5a9ab28e9e544a5e46a6aab93c1ea4dfcbb9deaac5f839',
 'archive-file-list-02.json':'4c3355ba49aa7181a2248b053ce74c0460a328345356ffcd040c6c77f3a9bf88'}
for name,digest in metadata.items():assert sha(author/name)==digest
manifest=json.loads((author/'final-02/source-manifest.json').read_text(encoding='utf-8-sig'))
expected={row['path']:row['sha256'] for row in manifest['pins']}
assert set(expected)==set(scope['production_paths']+scope['test_paths'])
checks=[];overlay={}
for name,digest in expected.items():
 source=author/'final-02/source'/name
 assert sha(source)==digest==sha(wt/name)
 snapshot=root/'source-snapshot'/name;snapshot.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,snapshot)
 checks.append({'path':name,'sha256':digest,'live_and_author_and_snapshot_match':sha(snapshot)==digest})
 overlay[str(wt/name)]=str(snapshot)
for name in ['run_independent.py','independent_cli_test.go']:
 shutil.copyfile(base/name,root/name)
# Reuse only this reviewer's own excluded/reproducible cache, not author cache.
runner=root/'run_independent.py'
text=runner.read_text(encoding='utf-8').replace("'GOCACHE':str(root/'cache')","'GOCACHE':str(root.parent/'cache')")
runner.write_text(text,encoding='utf-8',newline='\n')
for source,name in [(scope_path,'scope.json'),(repo/'execution/product-v1/contracts/harness.v1.interface.rev2.json','harness.v1.interface.rev2.json')]:shutil.copyfile(source,root/name)
for name in list(metadata)+['attempt-04/test.jsonl','attempt-04/test.result.json','attempt-04/vet.log','attempt-04/vet.result.json','attempt-04/fmt.log','attempt-04/fmt.result.json','attempt-04/source-manifest.json','attempt-04.ps1','final-02/git-status.txt','final-02/git-diff-check.txt','final-02/main.diff']:
 source=author/name
 if source.is_file():
  target=root/'author-evidence'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
(root/'overlay.json').write_text(json.dumps({'Replace':overlay},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(root/'pin-stage.json').write_text(json.dumps({'base_head':scope['base_head'],'worktree':str(wt),'scope_sha256':sha(scope_path),'author_manifest_sha256':metadata['final-02/source-manifest.json'],'interface_sha256':sha(root/'harness.v1.interface.rev2.json'),'exact3':checks,'all_match':True,'source_writes':0,'real_cli_native_model':0,'old_review_sha256':sha(base/'review01/review.json'),'old_review_decision':'REQUIRES_CHANGES'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'revision':2,'exact3':checks,'old_review_unchanged':sha(base/'review01/review.json')=='e469b68c3765b4a702e1685c1f0f4a8db092839fe036d7dec3a4c42d7f050553'}))
