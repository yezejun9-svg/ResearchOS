import json,hashlib
from pathlib import Path
base=Path(__file__).resolve().parent
source=base/'binding-schema-prototype'
root=Path('D:/作品集/ResearchOS/research-os')
target=root/'execution/v2.4/receipts/W05/W05-99/continue-cp586-20261104/production-binding/c-prototype-reference'
assert not target.exists()
manifest=json.loads((source/'evidence/attempt-01/source-manifest.json').read_bytes())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
for item in manifest['files']:assert sha(source/item['path'])==item['sha256']
assert sha(source/'reviews/source-review.json')=='7fb052c2c22e19bbafc16fed13f5b39771441e368f05e84c69ca55d09944f899'
files={source/item['path'] for item in manifest['files']}
for folder in ['evidence','reviews','tools']:
    files.update(path for path in (source/folder).rglob('*') if path.is_file() and '__pycache__' not in path.parts)
target.mkdir();rows=[]
for path in sorted(files):
    relative=path.relative_to(source);destination=target/relative;raw=path.read_bytes()
    destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(raw)
    assert path.read_bytes()==destination.read_bytes()
    rows.append({'path':relative.as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
(target/'archive-manifest.json').write_text(json.dumps({'status':'FROZEN_C_REFERENCE_VERIFIED_ARCHIVED_NOT_PRODUCTION_AUTHENTICATION','files':rows,'no_caches_or_user_DB_or_profiles_copied':True,'formal_increment':0},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'archived_files':len(rows),'source_files':len(manifest['files']),'formal_increment':0}))
