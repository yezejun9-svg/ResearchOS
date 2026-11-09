from pathlib import Path
import hashlib,json,ast
O=Path(__file__).parent;old=O.parent/'dc00ad52f46c49acacc8058a58500820/audit.py';raw=old.read_bytes();s=raw.decode('utf-8')
changes=[('input_capture_v2/root-construction.parameters.desktop58.json','root-construction.parameters.desktop58.json'),('input_capture_v2/root-inputs.desktop58.pre-review.json','root-inputs.desktop58.pre-review.json'),('9c91d99e92192ee5e21183d2a1a064d0f765aa3afacd36556191566d8b906f0a','9b4543d58707a90b2c89cd4cd7ef308d6cd8d90e57669cbfac09f5492715bc42'),('[335,163,564]','[335,163,575]'),("len(cut['origins'])==32","len(cut['origins'])==43"),("'all32 unique',len(newsha)==32","'all43 unique',len(newsha)==43"),("observation=doc(N/'tool-observations.resource-capture.closed.json')","observation={'deferred_to_supplement':True}"),("desktop58_cli_root_closure_adapter_independent_source_review_codex/5ae97e98de0568903e5d77af5169ffc5/review.json","desktop58_cli2_fact_abi_independent_source_review_codex/9167c63720c740baaeef3d030da84d50/review.json"),("'new v3 adapter independent source no requests'","'new v4 adapter independent source no requests'")]
counts=[]
for a,b in changes:
 n=s.count(a)
 if n!=1:raise RuntimeError('derivation exact anchor count '+str((a,n)))
 counts.append({'old':a,'new':b,'count':n});s=s.replace(a,b)
ast.parse(s)
with (O/'audit.py').open('xb') as f:f.write(s.encode('utf-8'))
with (O/'audit-derivation.json').open('x',encoding='utf-8') as f:json.dump({'baseline':{'path':str(old),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)},'changes':counts,'candidate_executed':False},f,ensure_ascii=False,indent=2)
print('Derived own read-only audit; candidate execution 0')
