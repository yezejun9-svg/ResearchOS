import hashlib,json,re
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');N=Path(__file__).parent
B=R/'execution/v2.4/receipts/W05/W05-99/qualification_recovery_boundary_boot6_codex/20261025-current-chat'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
refs={}
def verify(p,x=None):
 b=p.read_bytes();a={'path':str(p.resolve()),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
 if x:
  assert a['sha256']==x['sha256'],str(p)
  if 'bytes'in x:assert a['bytes']==x['bytes'],str(p)
 refs[a['path']]=a;return a
seal=read(B/'final-v6-additive-seal.json');verify(B/'final-v6-additive-seal.json')
for x in seal['files']:verify(B/x['name'],x)
for name,key in [('diagnostic-ledger.jsonl','v5_ledger_sha256'),('final-v5-author-freeze-seal.json','v5_seal_sha256'),('final-v5-six-source-manifest.json','v5_source_manifest_sha256')]:verify(B/name,{'sha256':seal[key]})
scope=read(N/'continuation-cp538/C57-boot6-source-subscope.json')
roots=[Path(scope[k]).resolve()for k in ['own_temporary_root','own_ascii_native_fixture_root']]
runs=[]
for prefix in ['final-v6','final-v6b','final-v6c']:
 c=read(B/(prefix+'-owned-fixture-command-recipe.json'))
 for k in ['TEMP','TMP','GOTMPDIR','GOCACHE']:
  assert any(Path(c['environment'][k]).resolve().is_relative_to(r)for r in roots),k
 assert int((B/c['native_exit']).read_text(encoding='utf-8-sig').strip())==1
 stdout=(B/c['stdout']).read_text(encoding='utf-8-sig')
 runs.append({'id':prefix,'native_exit':1,'skipped':re.findall(r'^--- SKIP: ([^ ]+)',stdout,re.M),'failed':re.findall(r'^--- FAIL: ([^ ]+)',stdout,re.M)})
 assert runs[-1]['failed']==['TestSameHandleDescriptorMutationRejectsStaleExpected']
ledger=[json.loads(s)for s in(B/'diagnostic-ledger-v6.jsonl').read_text(encoding='utf-8-sig').splitlines()if s.strip()]
for x in ledger:
 if 'native_exit'in x:
  for k in ['stdout','stderr','exit']:verify(B/x[k])
  assert int((B/x['exit']).read_text(encoding='utf-8-sig').strip())==x['native_exit']
failed=[x for x in ledger if x['result']=='failed'];assert len(failed)==5
retained=seal['diagnostic_file_retained'];verify(Path(retained['path']),retained)
cleanup=read(B/'final-v6-owned-fixture-cleanup-check.json')
assert all(not x['remaining_test_temp_entries']for x in cleanup)
out={'schema':'researchos.C57-boot6-v6-root-verification.v1','status':'AUTHOR_OWNED_ENV_FAILURE_EVIDENCE_VERIFIED_SOURCE_DIAGNOSIS_OPEN','verified_count':len(refs),'verified_refs':list(refs.values()),'owned_environment_values_verified':True,'source_snapshot':'All v6 author manifests bind unchanged v5; current working source may be undergoing review fixes, not verified as v6 live','runs':runs,'native_failed_records':failed,'auto_review_cleanup':next(x for x in ledger if x['result']=='blocked_by_auto_review'),'source6_current_acceptance':False,'prior_scope_deviation_origin':'20261025|c57-author-fixture-environment-scope','cleanup_evidence':cleanup,'formal_increment':0}
with(N/'C57-boot6-v6-root-verification.json').open('x',encoding='utf8')as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write(chr(10))
print(json.dumps({'status':out['status'],'refs':len(refs),'native_failure_records':len(failed),'runs':runs,'cleanup_exception':retained['path'],'formal_increment':0},ensure_ascii=False))

