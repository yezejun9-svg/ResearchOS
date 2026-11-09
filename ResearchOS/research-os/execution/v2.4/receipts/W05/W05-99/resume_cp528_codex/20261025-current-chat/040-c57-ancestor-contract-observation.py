import hashlib,json
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');N=Path(__file__).parent;E=R/'execution/v2.4/receipts/W05/W05-99'
p=E/'qualification_official_entry_resource_map_codex/20261015-current-chat/file-ancestor-metadata.json';raw=p.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='f4c58e80940d0dc81ce9c0bac70a1131030238c27cfe7e9347e749ac33d71cc5'
d=json.loads(raw.decode('utf-8-sig'));rows=[x for x in d['records']if x['path'].replace(chr(92),'/').lower()=='d:/'];assert len(rows)==1
s=R/'.local/worktrees/qualification-maintenance-c57-20261025/internal/recoveryboundary/boot_windows.go';sb=s.read_bytes()
snapshot=N/'040-boot-ancestor-mutable-source.snapshot.txt'
with snapshot.open('xb')as f:f.write(sb)
out={'schema':'researchos.Root-C57-ancestor-contract-observation.v1','status':'FIXED_RESOURCE_REVIEW_WITH_MUTABLE_SOURCE_NOT_ACCEPTANCE','historical_resource':{'path':str(p),'sha256':hashlib.sha256(raw).hexdigest()},'D_drive_frozen_record':rows[0],'mutable_source_snapshot':{'path':str(snapshot),'sha256':hashlib.sha256(sb).hexdigest(),'bytes':len(sb)},'source_path':str(s),'observation':'Current ancestor predicate trusts only management SID and SYSTEM for owner/dangerous ALLOW; compare against adopted F02 legitimate OS ancestor policies and deny-only/inherit-only semantics. No permission to modify drive ACL. Do not solve this by blanket OS-root skip.','actual_current_drive_read':False,'source_edit':False,'formal_increment':0}
with(N/'C57-ancestor-contract-observation-cp540.json').open('x',encoding='utf8')as f:json.dump(out,f,ensure_ascii=False,indent=2)
print(json.dumps({'frozen_resource_sha256':out['historical_resource']['sha256'],'mutable_source_sha256':out['mutable_source_snapshot']['sha256'],'D_drive_acl':rows[0].get('acl')},ensure_ascii=False))
