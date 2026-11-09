import json,hashlib
from pathlib import Path
root=Path('D:/作品集/ResearchOS/research-os')
archive=root/'execution/v2.4/receipts/W05/W05-99/continue-cp586-20261104/production-binding/c-prototype-reference'
file=archive/'archive-manifest.json';raw=file.read_bytes();manifest=json.loads(raw)
prefix='reviews/run-01/private/'
removed=[row for row in manifest['files'] if row['path'].startswith(prefix)]
assert removed and archive.resolve().is_relative_to((root/'execution/v2.4/receipts/W05/W05-99/continue-cp586-20261104/production-binding').resolve())
saved=archive/'archive-manifest.before-cache-prune.json';assert not saved.exists();saved.write_bytes(raw)
for row in removed:
    path=archive/row['path'];assert path.resolve().is_relative_to((archive/'reviews/run-01/private').resolve()) and not path.is_symlink()
    assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']
for row in removed:(archive/row['path']).unlink()
for folder in sorted((archive/'reviews/run-01/private').rglob('*'),key=lambda p:len(p.parts),reverse=True):
    if folder.is_dir() and not list(folder.iterdir()):folder.rmdir()
folder=archive/'reviews/run-01/private'
if not list(folder.iterdir()):folder.rmdir()
manifest['files']=[row for row in manifest['files'] if not row['path'].startswith(prefix)]
manifest['copied_private_test_cache_pruned']={'files':len(removed),'bytes':sum(row['bytes'] for row in removed),'scope':'Only exact new D archive copies; original C evidence/cache untouched','source_hashes_verified_before_each_unlink':True}
file.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'pruned_new_cache_copies':len(removed),'kept_evidence_files':len(manifest['files']),'original_C_or_user_files_removed':False}))
