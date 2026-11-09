"""Prepare only fixed C-drive resource parents; issue no execution scope."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,os,shutil

R=Path(r'D:\作品集\ResearchOS\research-os')
N=Path(__file__).resolve().parent
BASE=Path(r'C:\Users\yqyyds\AppData\Local')
FIRST=BASE/'ResearchOS'
SECOND=FIRST/'w09-native-v4'
IDENTITY=R/'execution/project_identity.json'
def pin(p):
    p=Path(p);raw=p.read_bytes()
    return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(path,value):
    raw=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
    with path.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    return pin(path)
identity_ref=pin(IDENTITY)
assert identity_ref['sha256']=='03f06a2b72ae85b3445d724058b10c8b13bcdb98f31feaf195e10b2e88fb26ec'
identity=json.loads(IDENTITY.read_bytes())
assert identity['project_id']=='aede0678-7308-43dc-b9f2-cfe3d90cfdfb' and identity['repository_root']==str(R)
assert BASE.is_dir() and BASE.resolve(strict=True)==BASE
for p in (BASE,*BASE.parents):
    assert not p.is_symlink() and not p.is_junction() and p.resolve(strict=True)==p
review=R/'execution/v2.4/receipts/W09/W09-99/full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/resource-report.json'
review_ref=pin(review)
assert review_ref['sha256']=='f5f274d449c6ba68d6de66cdb300eea5225caf105273d2ecc0a33f92623de81a'
intent=dict(schema='researchos.w09-fixed-C-resource-parent-intent.v1',actor_id='codex:/root',
    authorization='User authorized full project implementation and autonomous resource preparation.',
    created_at=datetime.now(timezone.utc).isoformat(),project_identity_ref=identity_ref,
    readonly_resource_report_ref=review_ref,exact_parent_paths=[str(FIRST),str(SECOND)],
    per_run_scratch_created=False,RootScope_issued=False,product_calls=0,formal_acceptance=False)
save(N/'C-native-resource-parents.intent.root.json',intent)
created=[];observed=[]
for p in (FIRST,SECOND):
    if not p.exists():p.mkdir();created.append(str(p))
    assert p.is_dir() and not p.is_symlink() and not p.is_junction()
    assert p.resolve(strict=True)==p
    observed.append(dict(path=str(p),directory=True,real_path=str(p.resolve(strict=True)),
        symlink=False,junction=False,file_attributes=p.stat().st_file_attributes))
owner=dict(schema='researchos.w09-native-private-resource-owner.v1',
    project_id=identity['project_id'],repository_root=str(R),scratch_parent=str(SECOND))
marker=SECOND/'RESOURCE_OWNER.json'
if marker.exists():
    assert json.loads(marker.read_bytes())==owner
else:save(marker,owner)
assert pin(IDENTITY)==identity_ref
receipt=save(N/'C-native-resource-parents.closed.root.json',dict(intent,
    actually_created_directories=created,actual_directory_observations=observed,
    resource_owner_marker_ref=pin(marker),free_C_bytes_observed=shutil.disk_usage(BASE).free,
    source_scope_or_runtime_qualification_granted=False,Native_or_model_started=False,
    per_run_scratch_created=False,canonical_written=False))
print(json.dumps(dict(resource_parent_receipt_ref=receipt,actual_parent=str(SECOND),
    directories_created=created,per_run_scratch_created=False,execution_grant=False,
    Native_calls=0,Canonical_written=False),ensure_ascii=False))
