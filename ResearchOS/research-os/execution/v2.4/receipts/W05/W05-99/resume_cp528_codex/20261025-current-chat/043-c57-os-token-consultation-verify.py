import hashlib,json
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');N=Path(__file__).parent;V=R/'execution/v2.4/receipts/W05/W05-99/qualification_maintenance_c57_independent_review_codex/20261025-current-chat'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
 p=p.resolve();b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
refs={}
def check(x,base):
 p=Path(x['path']);p=p if p.is_absolute()else base/p;a=ref(p)
 assert a['sha256']==x['sha256']and a['bytes']==x['bytes'],str(p)
 refs[str(p.resolve())]=a
cases=[
 ('PHASE1-os-ancestor-token-semantics-addendum-seal.json','ef81922a508df3a9b1e1f5bc742979a87705b8d08e67c7d1f9ff70950f45bfcf',58,8,'025-os-ancestor-addendum-finalizer'),
 ('PHASE1-business-token-api-contract-addendum-seal.json','6e5e0a19d1208f926d377bc940db188d89d2b6cbe076129aa546f6523ce547d9',66,7,'029-token-api-addendum-finalizer')]
for name,sha,previous,added,finalizer in cases:
 p=V/name;assert ref(p)['sha256']==sha;refs[str(p.resolve())]=ref(p);d=read(p)
 assert d['previous_assertions_preserved']==previous and len(d['added_assertions'])==added and d['new_native_nonzero']==0 and d['cumulative_reviewer_native_nonzero']==2
 assert d['candidate_tests_executed']==0 and d['formal_increment']==0
 for x in d['entries']+d['prior_refs_unchanged']+d.get('fixed_inputs',[]):check(x,V)
 f=V/finalizer;out=read(f/'result.json');assert out['native_exit']==0
 for st in ['stdout','stderr']:assert ref(f/(st+'.raw'))['sha256']==out[st+'_sha256']
 for item in ['recipe.json','result.json','stdout.raw','stderr.raw']:refs[str((f/item).resolve())]=ref(f/item)
out={'schema':'researchos.C57-OS-token-consultation-root-verification.v1','status':'FIXED_CONTRACT_AND_MUTABLE_FINDINGS_VERIFIED_NO_SOURCE_ACCEPTANCE','verified_count':len(refs),'verified_refs':list(refs.values()),'prepared_assertions':73,'candidate_tests_executed':0,'formal_increment':0,'source_acceptance':False,'native_nonzero_increment':0,'cumulative_reviewer_native_nonzero':2,'findings':['Do not reject adopted legitimate OS ACL through blanket two-SID or INHERIT_ONLY misinterpretation; verify actual business token attributes and individual dangerous rights','WTSQueryUserToken as a required normal recovery branch adds LocalSystem/SeTcb requirements absent from adopted distinctSID admin mechanism; repair source rather than label sole path resource-unavailable'],'closure_state':'NOT_INDEPENDENTLY_VERIFIED_CLOSED','web_capture_note':'Relied-on primary sources persisted; initial unused exploratory search only tool transcript, not native-command capture gap'}
with(N/'C57-OS-token-consultation-root-verification.json').open('x',encoding='utf8')as f:json.dump(out,f,ensure_ascii=False,indent=2)
print(json.dumps({k:v for k,v in out.items()if k not in ['verified_refs','findings']},ensure_ascii=False))
