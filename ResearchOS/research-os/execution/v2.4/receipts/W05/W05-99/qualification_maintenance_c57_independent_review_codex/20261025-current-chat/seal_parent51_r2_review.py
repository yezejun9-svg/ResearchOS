import pathlib,json,hashlib
B=pathlib.Path(__file__).parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
D=B/'C51-r2-static-snapshot'
m=json.loads((D/'C51-R2-SOURCEFREEZE.json').read_text())
files=list(D.rglob('*'))
for i in m['owned_files']:
 p=(D if i['changed_from_preseal'] else B/'C51-static-snapshot')/i['path']
 assert sha(p)==i['sha256'],i['path']
for n in range(73,77):
 dirs=[p for p in B.glob(f'{n:03d}-*') if p.is_dir()];assert len(dirs)==1
 result=json.loads((dirs[0]/'result.json').read_text());assert result['native_exit']==0
 assert sha(dirs[0]/'stdout.raw')==result['stdout_sha256']
 assert sha(dirs[0]/'stderr.raw')==result['stderr_sha256']
 files.extend(dirs[0].iterdir())
for name in ['C51-r2-static-snapshot-verification.json','snapshot_parent51_r2.py','read_parent51_r2.py','snapshot_parent51_r2_author_receipts.py','seal_parent51_r2_review.py','PHASE1-parent51-r2-targeted-review.md','PHASE1-parent51-static-review-seal.json','PHASE1-parent51-nine-table-addendum-seal.json','C51-static-snapshot/internal/qualificationmaintenancejournal/journal_windows.go','C51-static-snapshot/internal/host/qualification_failure_maintenance_windows.go']:
 files.append(B/name)
refs=[{'path':str(p.relative_to(B)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(files)) if p.is_file()]
out={'schema':'researchos.c57.phase1.parent51-r2-targeted-static-review.v1','status':'P1_BLOCKED_STATIC_INTEGRATION','sourcefreeze_sha256':sha(D/'C51-R2-SOURCEFREEZE.json'),'original_two_classifier_sites':'STATIC_FIX_CONFIRMED_COMPONENT_ONLY','remaining_p1':'Domain beforeHash includes dispatch_row; journal full-plan validator omits dispatch_row','candidate_tests_run':False,'new_native_nonzero':0,'total_reviewer_native_nonzero':3,'assertions_unchanged':73,'files':refs}
with (B/'PHASE1-parent51-r2-targeted-review-seal.json').open('x',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
print(json.dumps({'refs':len(refs),'report_sha256':sha(B/'PHASE1-parent51-r2-targeted-review.md'),'seal_sha256':sha(B/'PHASE1-parent51-r2-targeted-review-seal.json'),'status':out['status']}))
