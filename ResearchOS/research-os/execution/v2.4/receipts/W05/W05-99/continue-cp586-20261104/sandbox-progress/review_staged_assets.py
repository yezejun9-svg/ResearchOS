import hashlib,json,os,stat
from pathlib import Path
from datetime import datetime,timezone
base=Path(__file__).resolve().parent
assets_root=base/'owned-model-resource'
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
manifest_file=assets_root/'MANIFEST.json'
assert digest(manifest_file)=='1ee48d848976e0d1aff869c474516cc6ce90bdc7373fd2735b27b6dc6b61fd24'
m=json.loads(manifest_file.read_bytes());rows=m['assets']
assert m['status']=='ASSETS_STAGED_NOT_STARTED' and len(rows)==981
assert m['asset_bytes']==5686303776
for key in ['process_starts','process_stops','metadata_requests','inference_calls','credentials_read','original_asset_writes','hardlinks_or_junctions_created','ResearchOS_D_writes','formal_increment']:
    assert m[key] in (False,0),key
assert not m['CP587_written'] and not m['counter_reset']
for field in ['scope','source_index','copy_log']:
    assert digest(Path(m[field+'_path']))==m[field+'_sha256']
names=set();total=0
for row in rows:
    rel=row['destination_relative'];path=assets_root/rel
    assert rel not in names and path==Path(row['destination'])
    assert rel=='runtime/ollama.exe' or rel.startswith('runtime/lib/ollama/') or rel.startswith('models/blobs/sha256-') or rel=='models/manifests/registry.ollama.ai/library/qwen3/4b-instruct',rel
    assert path.resolve().is_relative_to(assets_root.resolve())
    info=path.lstat();assert stat.S_ISREG(info.st_mode) and not info.st_file_attributes&0x400
    assert info.st_nlink==1 and info.st_size==row['bytes']
    assert digest(path)==row['source_sha256']==row['destination_sha256'],rel
    names.add(rel);total+=info.st_size
assert total==5686303776
actual={str(path.relative_to(assets_root)).replace('\\','/') for folder in ['runtime','models'] for path in (assets_root/folder).rglob('*') if path.is_file()}
assert actual==names
assert next(r for r in rows if r['destination_relative']=='runtime/ollama.exe')['destination_sha256']=='4e91d8fb44e0909ab69feec21c3699ae82843b56ce631b37491255c2dc6b0792'
model_path=assets_root/'models/manifests/registry.ollama.ai/library/qwen3/4b-instruct'
assert digest(model_path)=='0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0'
model=json.loads(model_path.read_bytes());descriptors=[model['config'],*model['layers']]
assert len(descriptors)==5
for d in descriptors:
    blob=assets_root/'models/blobs'/d['digest'].replace(':','-')
    assert blob.stat().st_size==d['size']
    assert next(r for r in rows if Path(r['destination'])==blob)['destination_sha256']==d['digest'].split(':')[1]
for row in m['private_empty_directories']:
    folder=Path(row['path']);assert folder.resolve().is_relative_to(assets_root.resolve()) and not list(folder.iterdir())
report={'status':'INDEPENDENT_ASSET_READBACK_PASSED_NOT_STARTED_NOT_QUALIFIED','at':datetime.now(timezone.utc).isoformat(),'manifest_sha256':digest(manifest_file),'verified_files':len(rows),'verified_bytes':total,'exact_asset_inventory':True,'no_target_reparse_or_hardlinks':True,'empty_profiles_verified':True,'model_descriptors_verified':5,'processes_started_by_this_review':0,'requests_by_this_review':0,'inference_calls':0,'D_writes':0,'formal_increment':0}
(assets_root/'INDEPENDENT-REVIEW.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
checkpoint=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/checkpoint.json')
raw=checkpoint.read_bytes();cp=json.loads(raw)
assert cp['revision']==586 and len(cp['failure_counters'])==2380
saved=base/'checkpoint.baseline.json'
if saved.exists():assert saved.read_bytes()==raw
else:saved.write_bytes(raw)
print(json.dumps({'asset_review':report['status'],'files':len(rows),'bytes':total,'checkpoint_baseline_copy_sha256':hashlib.sha256(raw).hexdigest()}))
