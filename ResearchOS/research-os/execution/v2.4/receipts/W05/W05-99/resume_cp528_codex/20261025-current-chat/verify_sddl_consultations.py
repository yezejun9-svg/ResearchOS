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
 refs[a['path']]=a;return a
def resolve(x):
 p=Path(x['path'])
 if p.is_absolute():return p
 if(V/p).is_file():return V/p
 return R/p
for name,finalizer in [('PHASE1-boot6-v7-sddl-advisory-seal.json','040-sddl-advisory-seal'),('PHASE1-boot6-v7-sddl-restore-supplement-seal.json','046-sddl-restore-supplement-seal')]:
 p=V/name;a=verify(p);s=read(p)
 if name.endswith('restore-supplement-seal.json'):assert a['sha256']=='04771a4a90def00d3a74e9d0f5cbe19430d6661bdcd3398b69de52c0f71f5cef'
 else:assert a['sha256'].startswith('ee58febd')
 assert s['candidate_tests_run']==0 and s['prepared_assertions_unchanged']==73 and s['new_native_failures']==0
 for x in s['references']+s['prior_refs_unchanged']+s.get('fixed_historical_inputs',[]):verify(resolve(x),x)
 d=V/finalizer;r=read(d/'result.json');assert r['native_exit']==0
 for stream in ['stdout','stderr']:verify(d/(stream+'.raw'),{'sha256':r[stream+'_sha256']})
 for name2 in ['recipe.json','result.json']:verify(d/name2)
out={'schema':'researchos.C57-SDDL-consultation-root-verification.v1','status':'BOUNDED_NATIVE_CONTRACT_ADVISORIES_VERIFIED_NO_SOURCE_ACCEPTANCE','verified_count':len(refs),'verified_refs':list(refs.values()),'prepared_assertions':73,'native_candidate_tests_by_reviewer':0,'new_reviewer_failure':0,'contract_findings':['Read OWNER/GROUP/DACL consistently','SetSecurityInfo addsAUTO_INHERITED; InstalledSD planning can account for native output, original preimage cannot be silently normalized','Historical fixed22targets contain16AI Cpackage and6noAI Drepo; noAIblanketrefusal breaks adopted support and is not final implementation','NtSetSecurityObject samehandle fullSD is a documented candidate, must prove exactnative roundtrip for supportedclasses; SetKernelObjectSecurity filesystem shortcut not permitted','Postmutation mismatch must be FAIL with explicit cleanup, not resourceSKIP'],'current_author_progress':'Owned noAI NtSetSecurityObject roundtrip reported0 withSDDLexact; production switching/fullsuite/binarySD binding still pending authorfreeze and independentphase2','original_environment_live_probe':False,'formal_increment':0}
with(N/'C57-SDDL-consultation-root-verification.json').open('x',encoding='utf8')as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write(chr(10))
print(json.dumps({'status':out['status'],'refs':len(refs),'prepared_assertions':73,'formal_increment':0}))

