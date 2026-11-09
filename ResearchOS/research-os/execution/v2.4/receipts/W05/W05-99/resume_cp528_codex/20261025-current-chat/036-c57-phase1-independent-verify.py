import hashlib,json,re
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');N=Path(__file__).parent;V=R/'execution/v2.4/receipts/W05/W05-99/qualification_maintenance_c57_independent_review_codex/20261025-current-chat'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
 p=p.resolve();b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
verified={}
def check(x,base):
 p=Path(x['path']);p=p if p.is_absolute()else base/p;a=ref(p)
 assert a['sha256']==x['sha256']and a['bytes']==x['bytes'],str(p)
 verified[str(p.resolve())]=a
seal=read(V/'PHASE1-seal.json');manifest=read(V/'PHASE1-manifest.json')
assert ref(V/'PHASE1-seal.json')['sha256']=='b6d293f2921b4a3619cd60f397eb6b6a725c89b1186329e2b42b11d427051c4b'
verified[str((V/'PHASE1-seal.json').resolve())]=ref(V/'PHASE1-seal.json')
for x in seal.values():
 if isinstance(x,dict)and 'path'in x and 'sha256'in x:check(x,V)
assert manifest['entry_count']==len(manifest['entries'])==57
for x in manifest['entries']:check(x,V)
audit=read(V/'PHASE1-input-hash-audit.json');assert audit['status']=='EXACT_MATCH'and len(audit['checked_refs'])==28
for x in audit['checked_refs']:
 assert x['match']
 expected,actual=x['expected'],x['actual']
 check(actual,R)
 ep=Path(expected['path']);ap=Path(actual['path'])
 assert expected['sha256']==actual['sha256'] and expected['bytes']==actual['bytes']
 if ep.is_absolute() or (R/ep).exists():check(expected,R)
 else:
  assert ap.is_absolute() and ap.as_posix().endswith('/'+ep.as_posix()),(expected,actual)

f=V/'013-phase1-finalizer';result=read(f/'result.json');assert result['native_exit']==0
for stream in ['stdout','stderr']:assert ref(f/(stream+'.raw'))['sha256']==result[stream+'_sha256']
for name in ['recipe.json','result.json','stdout.raw','stderr.raw']:verified[str((f/name).resolve())]=ref(f/name)
ids=[x.strip()for x in re.findall(r'^\| ([^|]+) \|', (V/'PHASE1-independent-matrix.md').read_text(encoding='utf8'),re.M)if x.strip()!='ID']
assert len(ids)==41 and len(set(ids))==41,(len(ids),ids)
assert seal['candidate_tests_executed']==0 and not seal['source_acceptance']and seal['formal_increment']==0
diag=read(V/'PHASE1-diagnostics-addendum-01.json');assert diag['native_nonzero_count_after_addendum']==2
out={'schema':'researchos.C57-phase1-independent-matrix-root-verification.v1','status':'FROZEN_PREPARATION_ARTIFACTS_VERIFIED_NO_SOURCE_ACCEPTANCE','verified_count':len(verified),'verified_refs':list(verified.values()),'independent_assertions':ids,'assertion_count':41,'fixed_input_refs':28,'candidate_tests_executed':0,'source_acceptance':False,'formal_increment':0,'native_nonzeros_to_preserve':2,'bootstrap_capture_limitation':'Initial commands only tool-combined output; explicit separate mixed diagnostic, no invented raw streams','mutable_findings':'M01 finalizer handle lifetime and M02 discarded Close errors retained; author-reported fix not independently verified'}
with(N/'C57-phase1-independent-root-verification-r2.json').open('x',encoding='utf8')as f:json.dump(out,f,ensure_ascii=False,indent=2)
print(json.dumps({k:v for k,v in out.items()if k not in ['verified_refs','independent_assertions']},ensure_ascii=False))
