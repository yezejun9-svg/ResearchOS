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
  if 'bytes'in x:assert a['bytes']==x['bytes'],str(p)
 refs[a['path']]=a
 return a
p=V/'PHASE1-binary-sd-contract-clarification-seal.json';s=read(p)
verify(p,{'sha256':'0073a6ccba0aeb0255501a0f7a2f14c86081d6173594392831229852d0ada8a4'})
for x in s['references']+s['prior_refs_unchanged']:
 q=Path(x['path']);verify(q if q.is_absolute()else V/q,x)
for x in s['source_refs']:
 verify(V/x['snapshot'],x)
 if not x['mutable_source']:verify(Path(x['source']),x)
d=V/'051-binary-contract-clarification-seal';r=read(d/'result.json');assert r['native_exit']==0
for stream in ['stdout','stderr']:verify(d/(stream+'.raw'),{'sha256':r[stream+'_sha256']})
for name in ['recipe.json','result.json']:verify(d/name)
assert s['original_binary_preimage_required']and not s['contract_explicit_query_buffer_memcmp_found']and s['native_ACE_flag_drift_reported']==4
assert s['candidate_tests_run']==0 and s['prepared_assertions_unchanged']==73 and s['new_native_failures']==0
out={'schema':'researchos.C57-binary-SD-contract-root-verification.v1','status':'NATIVE_ACE_INHERITANCE_DRIFT_AND_MISSING_BINARY_PREIMAGE_CONFIRMED_REQUIRES_SOURCE_FIX','verified_count':len(refs),'verified_refs':list(refs.values()),'existing_contract':'Save original native binary preimage and restore all meaningful native security fields/control/ACE inheritance; no newly invented query-buffer padding/layout byte threshold','observed_drift':{'offsets':[85,109,129,149],'before':'00','after':'10','field':'ACE Header.AceFlags / INHERITED_ACE','padding_difference':False},'required_fix':'Samehandle NtQuery raw capture/storage/binding; derive displaySDDL fromraw; restore consumes originalraw, verifies native fields and reports rawbytecomparison separately; keep exact original history','mutable_source_already_fixed':False,'candidate_tests_by_reviewer':0,'formal_increment':0}
with(N/'C57-binary-SD-contract-root-verification.json').open('x',encoding='utf8')as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write(chr(10))
print(json.dumps({'status':out['status'],'refs':len(refs),'formal_increment':0}))

