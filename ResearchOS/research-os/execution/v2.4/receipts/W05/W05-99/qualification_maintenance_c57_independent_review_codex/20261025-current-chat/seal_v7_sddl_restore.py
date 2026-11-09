import pathlib,json,hashlib
B=pathlib.Path(__file__).parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':str(p.relative_to(B)).replace('\\','/'),'sha256':sha(p),'bytes':p.stat().st_size}
prior={'PHASE1-boot6-v7-sddl-advisory.md':'35552687ffcddc761a39e21c8002ae19024e1215ba154c0eb0829efc6294fb15','PHASE1-boot6-v7-sddl-advisory-seal.json':'ee58febda27e5e63ba57f82a4f763d4da9e18936be7434a6c7ae3fad8ee5f0a6'}
for n,w in prior.items():assert sha(B/n)==w
ps=json.loads((B/'PHASE1-boot6-v7-sddl-advisory-seal.json').read_text(encoding='utf-8'))
for x in ps['prior_refs_unchanged']:assert sha(B/x['path'])==x['sha256'],x['path']
extract=B/'HISTORICAL-v7-sddl-contract-extract.json'; ex=json.loads(extract.read_text(encoding='utf-8'))
for x in ex['refs']:assert sha(pathlib.Path(x['path']))==x['sha256']
paths=[B/'PHASE1-boot6-v7-sddl-restore-supplement.md',B/'seal_v7_sddl_restore.py',B/'extract_v7_historical_sddl.py',extract]
paths+=sorted(B.glob('WEB-v7-sddl-restore-*.json'))
for n in range(41,46):
 ds=list(B.glob(f'{n:03d}-*'));assert len(ds)==1
 d=ds[0];r=json.loads((d/'result.json').read_text());assert r['native_exit']==0
 for stream in ['stdout','stderr']:assert sha(d/(stream+'.raw'))==r[stream+'_sha256']
 paths+=sorted(d.iterdir())
data={'status':'READ_ONLY_RESTORE_CAPABILITY_ADVISORY_NOT_ACCEPTANCE','candidate_tests_run':0,'new_permanent_assertions':0,'prepared_assertions_unchanged':73,'new_native_failures':0,'new_tool_diagnostics':0,'reviewer_native_failures_cumulative':2,'prior_refs_unchanged':[ref(B/n) for n in prior]+ps['prior_refs_unchanged'],'fixed_historical_inputs':ex['refs'],'references':[ref(p) for p in paths]}
out=B/'PHASE1-boot6-v7-sddl-restore-supplement-seal.json'
with out.open('x',encoding='utf-8') as f:json.dump(data,f,ensure_ascii=False,indent=2)
print(json.dumps({'report_sha256':sha(B/'PHASE1-boot6-v7-sddl-restore-supplement.md'),'seal_sha256':sha(out),'references':len(paths),'prior_unchanged':True,'new_native_failures':0},indent=2))

