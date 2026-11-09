import pathlib,json,hashlib
B=pathlib.Path(__file__).parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(B/'PHASE1-parent51-static-review.md')=='b25628c14a9f8b47ce1f62d133482fb0f439e8490461ec8a8f5710026d08e085'
assert sha(B/'PHASE1-parent51-static-review-seal.json')=='89ce92686cc716ca2bd0d1d867e341bad85b9a4a3992d3d3961a6ba272ee9fbb'
v=json.loads((B/'C51-static-snapshot-verification.json').read_text(encoding='utf-8'))
assert all(sha(B/'C51-static-snapshot'/i['path'])==i['sha256'] for i in v['files'])
files=list((B/'C51-frozen-base-schema').iterdir())
for n in range(66,72):
 dirs=[p for p in B.glob(f'{n:03d}-*') if p.is_dir()]
 assert len(dirs)==1
 result=json.loads((dirs[0]/'result.json').read_text())
 assert result['native_exit']==(1 if n==68 else 0),(n,result)
 assert sha(dirs[0]/'stdout.raw')==result['stdout_sha256']
 assert sha(dirs[0]/'stderr.raw')==result['stderr_sha256']
 files.extend(dirs[0].iterdir())
for name in ['PHASE1-parent51-static-review.md','PHASE1-parent51-static-review-seal.json','PHASE1-parent51-nine-table-addendum.md','snapshot_parent51_base_schema.py','seal_parent51_nine_tables.py','C51-static-snapshot-verification.json']:
 files.append(B/name)
refs=[{'path':str(p.relative_to(B)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(files)) if p.is_file()]
result={'schema':'researchos.c57.phase1.parent51-nine-table-addendum.v1','status':'P1_BLOCKED_STATIC_ONLY','frozen_preseal_sha256':v['preseal_sha256'],'base_commit':'085b4711afe0c1288448b174eef24ecd5af0551b','same_failure_mechanism_sites':['runtime_dispatches missing five unchanged columns','domain_objects immutable compares equivalence to 1 rather than exact expected value'],'new_native_nonzero':1,'prior_reviewer_native_nonzero':2,'total_reviewer_native_nonzero':3,'nonzero_reason':'068 exploratory git grep no matches, not a candidate test','candidate_tests_run':False,'assertions_unchanged':73,'files':refs}
with (B/'PHASE1-parent51-nine-table-addendum-seal.json').open('x',encoding='utf-8') as f: json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps({'refs':len(refs),'report_sha256':sha(B/'PHASE1-parent51-nine-table-addendum.md'),'seal_sha256':sha(B/'PHASE1-parent51-nine-table-addendum-seal.json'),'total_reviewer_native_nonzero':3}))
