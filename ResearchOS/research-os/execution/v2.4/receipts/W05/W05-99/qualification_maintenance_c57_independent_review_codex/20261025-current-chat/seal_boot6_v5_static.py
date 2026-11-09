import hashlib,json,pathlib
B=pathlib.Path(__file__).parent
R=pathlib.Path(r'D:\作品集\ResearchOS\research-os')
W=R/'.local/worktrees/qualification-maintenance-c57-20261025'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):
 return {'path':str(p.relative_to(B)).replace('\\','/'),'sha256':sha(p),'bytes':p.stat().st_size}
old={
'PHASE1-independent-matrix.md':'53c640281feee3039ceb56c7588189706a40651b028168a12f61f3aaca1b8527',
'PHASE1-manifest.json':'4f3965cf95e9f81e24087f162a16bd0eace4fafd1b18b7c7a3093804b1da9ba8',
'PHASE1-seal.json':'b6d293f2921b4a3619cd60f397eb6b6a725c89b1186329e2b42b11d427051c4b',
'PHASE1-boot-plan-binding-addendum-seal.json':'dabf5e26c77608af81ad3f755c8f07083d4db44c689232bdf3b9ec2986ca892b',
'PHASE1-persistent-fence-control-addendum-seal.json':'4fc32056b6f7777fc06f0a219f1c81c399abd20ab921e021fa127355517f6122',
'PHASE1-os-ancestor-token-semantics-addendum-seal.json':'ef81922a508df3a9b1e1f5bc742979a87705b8d08e67c7d1f9ff70950f45bfcf',
'PHASE1-business-token-api-contract-addendum-seal.json':'6e5e0a19d1208f926d377bc940db188d89d2b6cbe076129aa546f6523ce547d9'}
for name,expected in old.items(): assert sha(B/name)==expected,name
m=R/'execution/v2.4/receipts/W05/W05-99/qualification_recovery_boundary_boot6_codex/20261025-current-chat/final-v5-six-source-manifest.json'
assert sha(m)=='175b24b640edf7d8a7924db527c93400125299278632e58d8f73ffeceb31a3d0'
six=json.loads(m.read_text(encoding='utf-8-sig'))
assert len(six)==6
for x in six:
 assert sha(W/x['path'])==x['sha256'],x['path']
 assert sha(B/'BOOT6-v5-static-snapshot'/x['path'])==x['sha256'],x['path']
paths=[B/'PHASE1-boot6-v5-static-review.md',B/'seal_boot6_v5_static.py',B/'snapshot_boot6_v5.py']
paths+=sorted((B/'BOOT6-v5-static-snapshot').rglob('*'))
paths+=sorted(B.glob('WEB-boot6-*.json'))
for n in range(30,37):
 dirs=list(B.glob(f'{n:03d}-*'));assert len(dirs)==1,n
 d=dirs[0]
 result=json.loads((d/'result.json').read_text())
 assert result['native_exit']==0,str(d)
 for stream in ['stdout','stderr']: assert sha(d/(stream+'.raw'))==result[stream+'_sha256']
 paths+=sorted(d.iterdir())
paths=[p for p in paths if p.is_file()]
seal={'status':'PHASE1_FROZEN_SIX_STATIC_REVIEW_NEEDS_WORK_NOT_ACCEPTANCE','findings':[{'id':'BOOT6-V5-01','priority':'P1','topic':'foreign original owner restore eligibility missing before mutation'},{'id':'BOOT6-V5-02','priority':'P1','topic':'per-record file protection not verified'},{'id':'BOOT6-V5-03','priority':'P1','topic':'disabled enableable group authority omitted'}],'prepared_assertions_unchanged':73,'new_permanent_assertions':0,'candidate_tests_run':0,'formal_acceptance':False,'combined57_phase2':False,'native_failure_new':0,'native_failure_cumulative':2,'tool_diagnostics_new':0,'prior_refs_unchanged':[ref(B/n) for n in old],'source_manifest':{'path':str(m),'sha256':sha(m)},'six_source_entries':six,'references':[ref(p) for p in paths]}
out=B/'PHASE1-boot6-v5-static-review-seal.json'
with out.open('x',encoding='utf-8') as f: json.dump(seal,f,ensure_ascii=False,indent=2)
print(json.dumps({'report_sha256':sha(B/'PHASE1-boot6-v5-static-review.md'),'seal_sha256':sha(out),'references':len(paths),'exact6_snapshot_and_worktree_match':True,'prior_73_unchanged':True,'new_failures':0},indent=2))

