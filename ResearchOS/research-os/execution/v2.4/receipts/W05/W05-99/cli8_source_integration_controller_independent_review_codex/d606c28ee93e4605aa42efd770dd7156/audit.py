import ast, hashlib, json, pathlib, sys, datetime
R=pathlib.Path('D:/作品集/ResearchOS/research-os')
O=R/'execution/v2.4/receipts/W05/W05-99/cli8_source_integration_controller_independent_review_codex/d606c28ee93e4605aa42efd770dd7156'
S=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/cli-exact8-source-integration-r323'
reads={};checks=[]
def check(v,n): checks.append({'check':n,'passed':bool(v)})
def p(v):
 q=pathlib.Path(v);return q if q.is_absolute() else R/q
def raw(v):
 q=p(v);b=q.read_bytes(); row={'path':str(q),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
 old=reads.get(str(q));check(old is None or old==row,'read-stable:'+str(q));reads[str(q)]=row;return b
def ref(v): raw(v);return dict(reads[str(p(v))])
def verify(x):
 b=raw(x['path']);check(len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256'],'ref:'+x['path']);return b
def doc(v):return json.loads(raw(v))
def refs(v):
 if isinstance(v,dict):
  if {'path','sha256','bytes'}<=v.keys():verify(v)
  else:
   for x in v.values():refs(x)
 elif isinstance(v,list):
  for x in v:refs(x)
def save(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
canon={n:raw('execution/v2.4/'+n+'.json') for n in ['checkpoint','path_ownership','step_state','commands']}
for n,b in canon.items():(O/('canonical.before.'+n+'.json')).write_bytes(b)
cp=json.loads(canon['checkpoint']);ow=json.loads(canon['path_ownership']);check([cp['revision'],ow['revision'],len(cp['failure_counters'])]==[322,150,425],'actual before tuple')
s=doc(S/'scope_registration.json');check(ref(S/'scope_registration.json')['sha256']=='52d8f686f07a606afaeb64eccca26f53edb2872bf93fa595132fd6afc067da71','scope exact');refs(s)
for name,sha in [('grant-producer.py','7c6b8877e523ad727cb8773651452e13cae2ac940ef28086639890f0bf829f6a'),('launcher.py','94f5aee1d4fe5b720a1aa418f5fb2836a5edb26a14782a2de8b5330fc4a6668d')]:
 b=raw(S/name);check(hashlib.sha256(b).hexdigest()==sha,name+'pin');ast.parse(b);(O/('input.'+name)).write_bytes(b)
b=verify(s['controller_ref']);ast.parse(b);(O/'input.controller.py').write_bytes(b);check(hashlib.sha256(b).hexdigest()=='f3301a8fad305ce207afa0595d0071c91842f9258ad3b2e58ddb709e1562922b','controller exact')
for name in ['scope-derivation-audit.json','executor-derivation-audit.json']:refs(doc(S/name))
MF=p(s['controller_ref']['path']).parent/'manifest.json';m=doc(MF);check(m['count']==len(m['entries'])==12,'preparation manifest12');refs(m)
vector=json.loads(verify(s['protected_source_vector_ref']));check(len(vector)==6839,'protected6839');refs(vector)
planned=json.loads(verify(s['protected_source_paths_ref']));actual=sorted(p(x['path']).relative_to(R).as_posix() for x in vector if p(x['path']).is_relative_to(R));check(actual==planned,'protected exhaustive planned paths')
e=json.loads(verify(s['exact8_ref']));check(len(e)==8 and len({x['path'] for x in e})==8,'exact8 unique');check(sum(x['shared_with_handler38'] for x in e)==3,'shared3 total43')
protected={p(x['path']) for x in vector};check(not protected.intersection(R/x['path'] for x in e),'owned8 excluded protected')
for x in e:
 b=raw(x['path']);check(len(b)==x['before_bytes'] and hashlib.sha256(b).hexdigest()==x['before_sha256'],'preimage:'+x['path']);check(x['a5_preimage']==x['cli_parent_preimage'],'parent preimage equality:'+x['path']);check(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==x['a5_preimage']['blob'],'preimageGitblob:'+x['path'])
patch=verify(s['patch_ref']);patchpaths=[line.decode().split(' b/',1)[1] for line in patch.splitlines() if line.startswith(b'diff --git a/')];check(patchpaths==[x['path'] for x in e],'patch exact8 order')
attr=json.loads(verify(s['root_attributes_proof_ref']));refs(attr);check(verify(attr['raw_ref'])==b'* -text\n','rootattrs raw')
mr=json.loads(verify(s['main38_execution_review_ref']));post=json.loads(verify(s['main38_post_registration_audit_ref']));check(mr['decision']=='EXACT38_MAIN_SOURCE_INTEGRATION_EVIDENCE_CLOSED','Main38 finalreview');
for key in ['completed_ref','manifest_ref']:check(mr[key]==post[key]==s['main38_'+key],'Main38 identical original dict:'+key)
check(mr['post_registration_audit_ref']==s['main38_post_registration_audit_ref'],'Main38 postaudit exactdict')
check(cp['head']==s['base']==post['registered_head'],'base actualregistered')
for x in s['old_deleted_paths']:check(not (R/x).exists(),'olddeleted:'+x)
check(len(s['old_deleted_paths'])==11,'old11')
check(s['expected_registration']==[323,151,425] and s['expected_before_registration']==[322,150,425],'future tuple explicit')
for n,b in canon.items():check(raw('execution/v2.4/'+n+'.json')==b,'canonical unchanged:'+n)
save('read-audit.json',{'checks':checks,'check_count':len(checks),'failed':[x for x in checks if not x['passed']],'inputs':list(reads.values()),'protected_files_hashed':len(vector),'target_execution':False,'product_executions':0,'canonical_writes':0})
print(json.dumps({'checks':len(checks),'failed':sum(not x['passed'] for x in checks),'reads':len(reads),'output':str(O)},ensure_ascii=True))
