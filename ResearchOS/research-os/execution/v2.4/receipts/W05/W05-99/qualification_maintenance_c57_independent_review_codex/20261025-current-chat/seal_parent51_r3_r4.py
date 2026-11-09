import pathlib,json,hashlib
B=pathlib.Path(__file__).parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
D=B/'C51-r3-r4-static-snapshot'
v=json.loads((B/'C51-r3-r4-static-snapshot-verification.json').read_text())
for name,h in v['control_hashes'].items():assert sha(D/name)==h
m=json.loads((D/'C51-R4-SOURCEFREEZE.json').read_text())
for item in m['owned_files']:
 for root in [D,B/'C51-r2-static-snapshot',B/'C51-static-snapshot']:
  p=root/item['path']
  if p.exists():break
 assert sha(p)==item['sha256'],item['path']
files=list(D.rglob('*'))
for n in range(78,81):
 dirs=[p for p in B.glob(f'{n:03d}-*') if p.is_dir()];assert len(dirs)==1
 r=json.loads((dirs[0]/'result.json').read_text());assert r['native_exit']==0
 assert sha(dirs[0]/'stdout.raw')==r['stdout_sha256'];assert sha(dirs[0]/'stderr.raw')==r['stderr_sha256']
 files.extend(dirs[0].iterdir())
names=['C51-r3-r4-static-snapshot-verification.json','snapshot_parent51_r3_r4.py','read_parent51_r3_r4.py','seal_parent51_r3_r4.py','PHASE1-parent51-r3-r4-targeted-addendum.md','PHASE1-parent51-r2-targeted-review-seal.json','PHASE1-parent51-nine-table-addendum-seal.json','C51-r2-static-snapshot/internal/domain/qualification_failure_maintenance_windows.go','C51-static-snapshot/internal/host/qualification_failure_maintenance_windows.go','C51-static-snapshot/internal/domain/backup_source_lease_windows.go','C51-static-snapshot/internal/domain/backup_upgrade.go','C51-static-snapshot/internal/domain/backup_prepared_abandonment_upgrade.go','C51-static-snapshot/internal/domain/backup_prepared_abandonment_handoff.go','C51-static-snapshot/internal/domain/backup_prepared_abandonment_upgrade_windows.go']
files.extend(B/name for name in names)
refs=[{'path':str(p.relative_to(B)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(files)) if p.is_file()]
out={'schema':'researchos.c57.phase1.parent51-r3-r4-targeted-addendum.v1','status':'STATIC_FIX_CONFIRMED_PENDING_PHASE2','r3_sourcefreeze_sha256':sha(D/'C51-R3-SOURCEFREEZE.json'),'r4_sourcefreeze_sha256':sha(D/'C51-R4-SOURCEFREEZE.json'),'candidate_tests_run':False,'new_native_nonzero':0,'total_reviewer_native_nonzero':3,'assertions_unchanged':73,'files':refs}
with (B/'PHASE1-parent51-r3-r4-targeted-addendum-seal.json').open('x',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
print(json.dumps({'refs':len(refs),'status':out['status'],'report_sha256':sha(B/'PHASE1-parent51-r3-r4-targeted-addendum.md'),'seal_sha256':sha(B/'PHASE1-parent51-r3-r4-targeted-addendum-seal.json')}))
