"""Prepare fixed physical C parents after the prior AppData alias refusal."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,shutil

R=Path(r'D:\作品集\ResearchOS\research-os')
N=Path(__file__).resolve().parent
BASE=Path(r'C:\Users\yqyyds')
FIRST=BASE/'.researchos'
SECOND=FIRST/'w09-native-v5'
def pin(p):
    p=Path(p);raw=p.read_bytes()
    return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(path,value):
    raw=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
    with path.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    return pin(path)
identity_ref=pin(R/'execution/project_identity.json')
assert identity_ref['sha256']=='03f06a2b72ae85b3445d724058b10c8b13bcdb98f31feaf195e10b2e88fb26ec'
identity=json.loads(Path(identity_ref['path']).read_bytes())
assert identity['project_id']=='aede0678-7308-43dc-b9f2-cfe3d90cfdfb' and identity['repository_root']==str(R)
for p in (BASE,*BASE.parents):
    assert p.is_dir() and not p.is_symlink() and not p.is_junction() and p.resolve(strict=True)==p
intent=dict(schema='researchos.w09-fixed-physical-C-resource-parent-intent.v1',
    actor_id='codex:/root',created_at=datetime.now(timezone.utc).isoformat(),
    authorization='User authorized full project implementation and autonomous local resource preparation.',
    project_identity_ref=identity_ref,exact_parent_paths=[str(FIRST),str(SECOND)],
    supersedes_failed_C_AppData_attempt_original_ordinal=1142,
    prior_intent_ref=pin(N/'C-native-resource-parents.intent.root.json'),
    per_run_scratch_created=False,RootScope_issued=False,Native_calls=0,canonical_written=False)
save(N/'physical-C-native-v5-resource-parents.intent.root.json',intent)
created=[];observed=[]
for p in (FIRST,SECOND):
    existed=p.exists()
    if not existed:p.mkdir();created.append(str(p))
    assert p.is_dir() and not p.is_symlink() and not p.is_junction()
    assert p.resolve(strict=True)==p
    observed.append(dict(path=str(p),existed_before=existed,real_path=str(p.resolve(strict=True)),
        directory=True,symlink=False,junction=False,file_attributes=p.stat().st_file_attributes))
owner=dict(schema='researchos.w09-native-private-resource-owner.v1',
    project_id=identity['project_id'],repository_root=str(R),scratch_parent=str(SECOND))
marker=SECOND/'RESOURCE_OWNER.json'
if marker.exists():assert json.loads(marker.read_bytes())==owner
else:save(marker,owner)
assert pin(R/'execution/project_identity.json')==identity_ref
receipt=save(N/'physical-C-native-v5-resource-parents.closed.root.json',dict(intent,
    actually_created_directories=created,actual_directory_observations=observed,
    resource_owner_marker_ref=pin(marker),free_C_bytes_observed=shutil.disk_usage(SECOND).free,
    resource_scope_only=True,execution_grant=False,Source_runtime_qualified=False,
    per_run_scratch_created=False,formal_acceptance=False))
print(json.dumps(dict(resource_parent_receipt_ref=receipt,actual_physical_C_parent=str(SECOND),
    directories_created=created,per_run_scratch_created=False,
    Native_calls=0,Scope_issued=False,Canonical_written=False),ensure_ascii=False))
