from pathlib import Path
import datetime,hashlib,json,shutil

Q=Path(__file__).resolve().parent
A=Q.parent/'product-v1-workbench-author'
R=Path('D:/作品集/ResearchOS/research-os')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
freeze=A/'FROZEN.json'; manifest=A/'EVIDENCE_MANIFEST.json'
assert sha(freeze)=='0146759979ed06a19392881eaaf2f031bbeef951ed0cd1befa2f3b9a97e7195f'
assert sha(manifest)=='395af27cf58170054bfce7d184a9233930d7ca8a0338608c03ef8c919272d30a'
f=json.loads(freeze.read_text(encoding='utf-8'));m=json.loads(manifest.read_text(encoding='utf-8'))
assert f['construction_frozen'] and not f['source_modification_permitted']
assert m['file_count']==len(m['files'])==276
for entry in m['files']:
    src=A/entry['path']
    assert src.resolve().is_relative_to(A.resolve())
    assert sha(src)==entry['sha256'] and src.stat().st_size==entry['bytes'],entry['path']
pins={**f['source_sha256'],**f['test_sha256']}
assert len(pins)==10
for n,h in pins.items():
    assert sha(Path(f['worktree'])/n)==h,n
    assert sha(A/'source-snapshot'/n)==h,n
S=Q/'stage01';S.mkdir(exist_ok=False)
copied={}
def cp(src,relative,kind):
    dst=S/relative;dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(src,dst)
    assert sha(src)==sha(dst)
    copied[relative]={'sha256':sha(dst),'source':str(src),'kind':kind}
for n in pins:cp(A/'source-snapshot'/n,n,'AUTHOR_FROZEN_SOURCE')
for src in (R/'apps/desktop/main/lib').iterdir():
    n=src.relative_to(R).as_posix()
    if src.is_file() and src.suffix in ('.js','.mjs') and n not in pins:cp(src,n,'UNCHANGED_BASELINE_DEPENDENCY')
for n in ['apps/web/package.json','apps/web/src/screens.jsx','tests/ui/desktop/activity-projection.test.mjs']:
    cp(R/n,n,'UNCHANGED_BASELINE_DEPENDENCY')
for n in ['execution/product-v1/contracts/harness.v1.interface.rev2.json','docs/product-v1/D03-native-platform-policy.md']:
    cp(R/n,n,'ROOT_FROZEN_CONTRACT')
for key in ['scope','interface']:
    assert sha(Path(f[key]['path']))==f[key]['sha256']
lock=json.loads((R/'execution/toolchains/locked.json').read_text(encoding='utf-8-sig'))
node=lock['tools']['node'];assert sha(Path(node['path']))==node['sha256']
report={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'base_head':f['base_head'],
 'freeze_path':str(freeze),'freeze_sha256':sha(freeze),'author_evidence_manifest_sha256':sha(manifest),
 'verified_author_evidence_files':276,'source_sha256_exact10':pins,'stage':str(S),'files':copied,
 'node':node,'limitations':['Stage dependency files are explicitly pinned baseline source, not real runtime qualification.','No source edited, product started or tests run by this staging operation.']}
with (Q/'stage01-manifest.json').open('x',encoding='utf-8') as out:json.dump(report,out,ensure_ascii=False,indent=2);out.write('\n')
print(json.dumps({'status':'STAGED_AND_PINS_VERIFIED','frozen_files':10,'author_evidence_files':276,'staged_files':len(copied),'stage_manifest_sha256':sha(Q/'stage01-manifest.json'),'node':node},ensure_ascii=True))
