"""Root publishes independently reviewed exact bytes; preserve the prior index."""
from pathlib import Path
import copy,hashlib,json,os
R=Path(r'D:\作品集\ResearchOS\research-os');V=R/'execution/v2.4';RUN=V/'receipts/W09/W09-99/w09_br8_actual_root/actual-20261010-01'
P=RUN/'capture-7d7d176970554ad3b9cdb72bc3b1ce8a/root-corrected-publication01/result.json'
def checked(ref):
 p=Path(ref['path']);p=p if p.is_absolute() else R/p;b=p.read_bytes();assert hashlib.sha256(b).hexdigest()==ref['sha256'] and len(b)==ref['bytes'];return b
def save(p,b):
 with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
 return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
raw=P.read_bytes();assert hashlib.sha256(raw).hexdigest()=='04f15daf5921e4955859af90b39bde8f6283128c91da7db6713f1e5e8c433ce8' and len(raw)==6146
d=json.loads(raw);ix=R/d['fixed_path'];before=ix.read_bytes();assert hashlib.sha256(before).hexdigest()=='ce0424c83c54d08e82682382be3fbdd1c856fff8c2f697b8104a5a761962d9cb'
payloads=[checked(d[key]) for key in ('origin_payload_ref','capture_payload_ref','payload_ref')]
old_index=json.loads(before);new_index=json.loads(payloads[2]);assert new_index['entries'][:-1]==old_index['entries'] and len(new_index['entries'])==len(old_index['entries'])+1
assert {k:v for k,v in new_index.items() if k!='entries'}=={k:v for k,v in old_index.items() if k!='entries'}
assert json.loads(payloads[1])['source_audit_path'].startswith('C:/Users/yqyyds/.codex/sessions/')
targets=[R/d['origin_fixed_path'],R/d['capture_fixed_path']]
for p in targets:
 assert p.resolve().is_relative_to(V) and not p.exists() and p.parent.is_dir()
 for parent in (p,*p.parents):assert not parent.is_symlink() and not parent.is_junction()
out=RUN/'literal02-fixed-publication.root';assert not out.exists();out.mkdir()
archive=save(out/'index.before.raw.json',before);staged=save(out/'index.desired.raw.json',payloads[2])
published=[save(p,b) for p,b in zip(targets,payloads[:2])]
assert ix.read_bytes()==before
os.replace(out/'index.desired.raw.json',ix);assert ix.read_bytes()==payloads[2]
index_ref=dict(path=ix.relative_to(R).as_posix(),sha256=hashlib.sha256(payloads[2]).hexdigest(),bytes=len(payloads[2]))
previous=dict(path=ix.relative_to(R).as_posix(),sha256=hashlib.sha256(before).hexdigest(),bytes=len(before))
cp=json.loads((V/'checkpoint.json').read_bytes());assert cp['work_in_progress']['w09_root_delivery_capture_index_ref']==previous
extras=dict(publication_ref=dict(path=str(P),sha256='04f15daf5921e4955859af90b39bde8f6283128c91da7db6713f1e5e8c433ce8',bytes=6146),expected_previous_registry_ref=previous)
er=save(RUN/'literal02-registration.actual.extras.root.json',(json.dumps(extras,ensure_ascii=False,indent=2)+'\n').encode())
receipt=save(out/'published.closed.json',(json.dumps(dict(original_index_archive_ref=archive,index_ref=index_ref,published_refs=published,previous_checkpoint_registry_ref=previous,Root_actor='codex:/root',old_index_entries_preserved=True,old_capture_and_original_unchanged=True,SS_written=False,Native_replayed=False,formal_review_replayed=False),ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps(dict(receipt_ref=receipt,index_ref=index_ref,extras_ref=er,SS_written=False),ensure_ascii=False))
