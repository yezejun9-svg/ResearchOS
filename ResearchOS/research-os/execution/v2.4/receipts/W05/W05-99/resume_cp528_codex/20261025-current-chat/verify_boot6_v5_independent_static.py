import hashlib,json
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');N=Path(__file__).parent
V=R/'execution/v2.4/receipts/W05/W05-99/qualification_maintenance_c57_independent_review_codex/20261025-current-chat'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
refs={}
def verify(p,x=None):
 b=p.read_bytes();a={'path':str(p.resolve()),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
 if x:
  assert a['sha256']==x['sha256'],str(p)
  if 'bytes' in x:assert a['bytes']==x['bytes'],str(p)
 refs[a['path']]=a;return a
s=V/'PHASE1-boot6-v5-static-review-seal.json'
verify(s,{'sha256':'404b8b53a1652eebdf03161abdcd23c1145bdb84d3b5df0f5e4bf398bc972bb8'})
v=read(s)
for x in v['references']+v['prior_refs_unchanged']:
 p=Path(x['path']);verify(p if p.is_absolute() else V/p,x)
verify(Path(v['source_manifest']['path']),v['source_manifest'])
for x in v['six_source_entries']:verify(V/'BOOT6-v5-static-snapshot'/x['path'],x)
p=V/'037-boot6-static-final-seal';r=read(p/'result.json');assert r['native_exit']==0
for stream in ['stdout','stderr']:verify(p/(stream+'.raw'),{'sha256':r[stream+'_sha256']})
for name in ['recipe.json','result.json']:verify(p/name)
assert v['prepared_assertions_unchanged']==73 and v['candidate_tests_run']==0 and v['native_failure_new']==0 and len(v['findings'])==3
out={'schema':'researchos.C57-boot6-v5-independent-static-root-verification.v1','status':'NEEDS_WORK_THREE_P1_VERIFIED_NOT_SOURCE_ACCEPTANCE','verified_count':len(refs),'verified_refs':list(refs.values()),'findings':v['findings'],'prepared_assertions':73,'new_tests':0,'new_reviewer_native_failures':0,'prior_reviewer_native_failures':2,'source_current_mutability':'Verified immutable six-file reviewer snapshots, not currently edited working source','formal_increment':0}
with(N/'C57-boot6-v5-independent-static-root-verification.json').open('x',encoding='utf8') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write(chr(10))
print(json.dumps({'status':out['status'],'refs':len(refs),'findings':out['findings'],'formal_increment':0}))

