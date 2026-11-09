import pathlib,json,hashlib
B=pathlib.Path(__file__).parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':str(p.relative_to(B)).replace('\\','/'),'sha256':sha(p),'bytes':p.stat().st_size}
old={'PHASE1-boot6-v5-static-review.md':'a66d1f8aa47615b796dfd176dbfe3878b8b0fb921bd3b05b5fb4bb912638bc1f','PHASE1-boot6-v5-static-review-seal.json':'404b8b53a1652eebdf03161abdcd23c1145bdb84d3b5df0f5e4bf398bc972bb8'}
for name,want in old.items():assert sha(B/name)==want
prior=json.loads((B/'PHASE1-boot6-v5-static-review-seal.json').read_text(encoding='utf-8'))
for x in prior['prior_refs_unchanged']:assert sha(B/x['path'])==x['sha256'],x['path']
snapshot=B/'MUTABLE-v7-sddl-snapshot'
manifest=json.loads((snapshot/'manifest.json').read_text(encoding='utf-8'))
for x in manifest:assert sha(B/x['snapshot'])==x['sha256'],x['snapshot']
paths=[B/'PHASE1-boot6-v7-sddl-advisory.md',B/'snapshot_v7_sddl.py',B/'seal_v7_sddl.py']
paths+=sorted(snapshot.iterdir())
paths+=sorted(B.glob('WEB-v7-sddl-*.json'))
for n in [38,39]:
 ds=list(B.glob(f'{n:03d}-*'));assert len(ds)==1
 d=ds[0];r=json.loads((d/'result.json').read_text());assert r['native_exit']==0
 for stream in ['stdout','stderr']:assert sha(d/(stream+'.raw'))==r[stream+'_sha256']
 paths+=sorted(d.iterdir())
out=B/'PHASE1-boot6-v7-sddl-advisory-seal.json'
data={'status':'READ_ONLY_MUTABLE_SDDL_ADVISORY_NOT_ACCEPTANCE','candidate_tests_run':0,'new_permanent_assertions':0,'prepared_assertions_unchanged':73,'new_native_failures':0,'new_tool_diagnostics':0,'reviewer_native_failures_cumulative':2,'prior_refs_unchanged':[ref(B/n) for n in old]+prior['prior_refs_unchanged'],'mutable_inputs':[x for x in manifest if x['mutable_input']],'references':[ref(p) for p in paths]}
with out.open('x',encoding='utf-8') as f:json.dump(data,f,ensure_ascii=False,indent=2)
print(json.dumps({'report_sha256':sha(B/'PHASE1-boot6-v7-sddl-advisory.md'),'seal_sha256':sha(out),'references':len(paths),'prior73_and_v5_report_unchanged':True,'new_native_failures':0},indent=2))

