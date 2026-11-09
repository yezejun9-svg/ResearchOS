import pathlib,json,hashlib
B=pathlib.Path(__file__).parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':str(p.relative_to(B)).replace('\\','/'),'sha256':sha(p),'bytes':p.stat().st_size}
old={'PHASE1-boot6-v7-sddl-restore-supplement.md':'8a32168b5ec6351cb1027ea8c3c2744ce90f102d6875f20430c67eb2f1be1293','PHASE1-boot6-v7-sddl-restore-supplement-seal.json':'04771a4a90def00d3a74e9d0f5cbe19430d6661bdcd3398b69de52c0f71f5cef'}
for n,h in old.items():assert sha(B/n)==h
pr=json.loads((B/'PHASE1-boot6-v7-sddl-restore-supplement-seal.json').read_text(encoding='utf-8'))
for x in pr['prior_refs_unchanged']:assert sha(B/x['path'])==x['sha256']
manifest=json.loads((B/'BINARY-contract-snapshot/manifest.json').read_text(encoding='utf-8'))
for x in manifest:assert sha(B/x['snapshot'])==x['sha256']
limits=json.loads((B/manifest[7]['snapshot']).read_text(encoding='utf-8-sig'))
assert limits['design_review']['sha256']==manifest[6]['sha256']
def walk(x):
 if isinstance(x,dict):
  yield x
  for v in x.values():yield from walk(v)
 elif isinstance(x,list):
  for v in x:yield from walk(v)
ind=json.loads((B/manifest[6]['snapshot']).read_text(encoding='utf-8-sig'))
arc=json.loads((B/manifest[3]['snapshot']).read_text(encoding='utf-8-sig'))
for i in [4,5]:assert any(x.get('sha256')==manifest[i]['sha256'] for x in walk(ind))
for i in [0,1,2]:assert any(x.get('sha256')==manifest[i]['sha256'] for x in walk(arc))
assert any(x.get('sha256')==manifest[3]['sha256'] for x in walk(ind))
paths=[B/'PHASE1-binary-sd-contract-clarification.md',B/'inspect_binary_contract.py',B/'seal_binary_contract.py',B/'BINARY-native-ace-diff.json',B/'WEB-binary-ace-header-primary.json']
paths+=sorted((B/'BINARY-contract-snapshot').iterdir())
for n in range(47,51):
 ds=list(B.glob(f'{n:03d}-*'));assert len(ds)==1
 d=ds[0];r=json.loads((d/'result.json').read_text());assert r['native_exit']==0
 for stream in ['stdout','stderr']:assert sha(d/(stream+'.raw'))==r[stream+'_sha256']
 paths+=sorted(d.iterdir())
out=B/'PHASE1-binary-sd-contract-clarification-seal.json'
data={'status':'READ_ONLY_CONTRACT_CLARIFICATION_NATIVE_ACE_DRIFT_NOT_ACCEPTANCE','contract_explicit_query_buffer_memcmp_found':False,'original_binary_preimage_required':True,'native_ACE_flag_drift_reported':[85,109,129,149],'source_binary_preimage_gap_observed':True,'candidate_tests_run':0,'new_permanent_assertions':0,'prepared_assertions_unchanged':73,'new_native_failures':0,'new_tool_diagnostics':0,'reviewer_native_failures_cumulative':2,'prior_refs_unchanged':[ref(B/n) for n in old]+pr['prior_refs_unchanged'],'source_refs':manifest,'references':[ref(p) for p in paths]}
with out.open('x',encoding='utf-8') as f:json.dump(data,f,ensure_ascii=False,indent=2)
print(json.dumps({'report_sha256':sha(B/'PHASE1-binary-sd-contract-clarification.md'),'seal_sha256':sha(out),'references':len(paths),'adopted_reference_chain_verified':True,'new_native_failures':0},indent=2))

