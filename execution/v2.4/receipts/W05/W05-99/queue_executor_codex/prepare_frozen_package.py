from pathlib import Path
import json,hashlib
root=Path(__file__).parent
source=Path('D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4')
target=root/'frozen-package-input'
target.mkdir(exist_ok=False)
sha=lambda b:hashlib.sha256(b).hexdigest()
raw=(source/'PACKAGE_MANIFEST.json').read_bytes()
assert sha(raw)=='4666920727e189ed91dc84dae919f7ab9e52a2f9c45efd697ecdd790107d3964'
manifest=json.loads(raw)
(target/'PACKAGE_MANIFEST.json').write_bytes(raw)
files=[]
for entry in manifest['files']:
    path=entry['path']
    src=(source/path).resolve()
    assert src.is_relative_to(source.resolve())
    content=src.read_bytes()
    assert len(content)==entry['size_bytes'] and sha(content)==entry['sha256'],path
    dst=target/path
    dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_bytes(content)
    assert sha(dst.read_bytes())==entry['sha256']
    files.append(entry)
known={e['path'] for e in files}|{'PACKAGE_MANIFEST.json','PACKAGE_VALIDATION.json'}
extras=[p.relative_to(source).as_posix() for p in source.rglob('*') if p.is_file() and p.relative_to(source).as_posix() not in known]
report={'scope':'ISOLATED_EXACT_MANIFEST_TEST_FIXTURE','source_root':str(source),'destination':str(target.resolve()),'manifest_sha256':sha(raw),'files':files,'original_unlisted_files_excluded':extras,'original_files_changed':0}
(root/'frozen_package_input_receipt.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'Copied and verified all {len(files)} frozen manifest files; original package unchanged; {len(extras)} unlisted original files documented.')
