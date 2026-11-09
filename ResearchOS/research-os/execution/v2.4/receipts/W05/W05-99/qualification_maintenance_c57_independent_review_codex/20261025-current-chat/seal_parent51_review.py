import pathlib,json,hashlib
B=pathlib.Path(__file__).parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
v=json.loads((B/'C51-static-snapshot-verification.json').read_text(encoding='utf-8'))
for i in v['files']:
 p=B/'C51-static-snapshot'/i['path']
 assert p.stat().st_size==i['bytes'] and sha(p)==i['sha256'],i['path']
baseline={'PHASE1-independent-matrix.md':'53c640281feee3039ceb56c7588189706a40651b028168a12f61f3aaca1b8527','PHASE1-manifest.json':'4f3965cf95e9f81e24087f162a16bd0eace4fafd1b18b7c7a3093804b1da9ba8'}
for name,digest in baseline.items(): assert sha(B/name)==digest,name
files=list((B/'C51-static-snapshot').rglob('*'))
for n in range(52,66):
 dirs=[p for p in B.glob(f'{n:03d}-*') if p.is_dir()]
 assert len(dirs)==1,(n,dirs)
 result=json.loads((dirs[0]/'result.json').read_text())
 assert result['native_exit']==0
 assert sha(dirs[0]/'stdout.raw')==result['stdout_sha256']
 assert sha(dirs[0]/'stderr.raw')==result['stderr_sha256']
 files.extend(dirs[0].iterdir())
for name in ['snapshot_parent51.py','read_parent51.py','review_read.py','seal_parent51_review.py','C51-static-snapshot-verification.json','PHASE1-parent51-static-review.md',*baseline]:
 files.append(B/name)
refs=[{'path':str(p.relative_to(B)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(files)) if p.is_file()]
result={'schema':'researchos.c57.phase1.parent51-static-review.v1','status':'P1_BLOCKED_STATIC_REVIEW_NOT_ACCEPTANCE','preseal_sha256':v['preseal_sha256'],'snapshot_count':51,'findings':[{'priority':'P1','summary':'runtime_dispatches residual excludes whole row but exact classifier omits unchanged columns','existing_assertions':['DB-02','DB-05','JRN-01','JRN-02']}],'candidate_tests_run':False,'new_native_nonzero':0,'prior_reviewer_native_nonzero':2,'total_reviewer_native_nonzero':2,'tool_protocol_diagnostics':0,'assertion_count_unchanged':73,'files':refs}
with (B/'PHASE1-parent51-static-review-seal.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps({'references':len(refs),'snapshot_count':51,'report_sha256':sha(B/'PHASE1-parent51-static-review.md'),'seal_sha256':sha(B/'PHASE1-parent51-static-review-seal.json'),'status':result['status']},ensure_ascii=False))
