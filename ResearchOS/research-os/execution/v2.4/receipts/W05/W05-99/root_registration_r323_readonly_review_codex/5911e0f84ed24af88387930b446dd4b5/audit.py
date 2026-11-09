import pathlib,json,hashlib,ast,subprocess,os,datetime
R=pathlib.Path('D:/作品集/ResearchOS/research-os');N=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/cli-exact8-source-integration-r323';O=R/'execution/v2.4/receipts/W05/W05-99/root_registration_r323_readonly_review_codex/5911e0f84ed24af88387930b446dd4b5'
reads={};checks=[]
def ck(v,n):checks.append({'check':n,'passed':bool(v)})
def path(p):
 p=pathlib.Path(p);return p if p.is_absolute() else R/p
def raw(p):
 p=path(p);b=p.read_bytes();pin={'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};ck(str(p) not in reads or reads[str(p)]==pin,'stable:'+str(p));reads[str(p)]=pin;return b
def verify(r):
 b=raw(r['path']);ck(hashlib.sha256(b).hexdigest()==r['sha256'] and len(b)==r['bytes'],'ref:'+r['path']);return b
def doc(p):return json.loads(raw(p))
def ref(p):raw(p);return reads[str(path(p))]
def save(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
pins={'register.py':'5fa3de9b52cb2c2f1076a031c973a17dfccf5adff198a1d41fd8f5da69af903d','run.py':'3e8226c840b88c1d6ca3f418098b788c3281e525a879359d168b070007a6b63a','seal.py':'4ec1727827e88550955432c9e07ccb8e3c31044d8526684d5eb81aeb4af6ed9f','prepared_refs.json':'93355cd7761167b826f488aee4f783c70eec6ed86c220d8b69f105270a7a8229','audit.json':'fec142952a0cf57752ae2a2ad12871772c904efd23160b008800eaf7df917a12'}
for n,h in pins.items():
 b=raw(N/n);ck(hashlib.sha256(b).hexdigest()==h,'draft exact:'+n)
 if n.endswith('.py'):ast.parse(b);(O/('input.'+n)).write_bytes(b)
p=doc(N/'prepared_refs.json');a=doc(N/'audit.json');original=[];copies=[]
for r in p['canonical_before']:
 b=verify(r);original.append(b);target=O/('canonical.before.'+pathlib.Path(r['path']).name)
 with target.open('xb') as f:f.write(b)
 copies.append(ref(target))
cp,ow=[json.loads(x) for x in original[:2]];ck([cp['revision'],ow['revision'],len(cp['failure_counters'])]==[322,150,425],'actual322150425');ck(cp['head']==p['head']=='a5d6d16ffaf129de0361470c3a1570228bd259a2','actualregisteredbase')
ck([r['path'] for r in p['canonical_before']]==['execution/v2.4/'+x+'.json' for x in ['checkpoint','path_ownership','step_state','commands']],'canonical ordered4')
for r in p['verified_refs']:verify(r)
by={r['path']:r for r in p['verified_refs']};ck(len(by)==len(p['verified_refs']),'verified unique')
for k,r in p['pins'].items():verify(r);ck(by.get(r['path'])==r,'pin inverified:'+k)
ck(not set(by).intersection(r['path'] for r in p['canonical_before']),'no livecanonical immutableverified')
s=json.loads(verify(p['pins']['scope']));rv=json.loads(verify(p['pins']['integration_controller_review']));ck(rv['decision']=='READY_FOR_ROOT_EXACT8_SOURCE_COMMIT_ONCE_WITH_OPEN_GATES' and rv['scope_sha256']==p['pins']['scope']['sha256'] and rv['launcher_sha256']==p['pins']['launcher']['sha256'],'controller scope launcher currentREADY')
ck(a['expected_before']==s['expected_before_registration']==[322,150,425] and a['expected_after']==s['expected_registration']==[323,151,425],'fixed transition');ck(p['origins']==[] and a['new_origins']==[],'zero neworigins in323')
pending=json.loads(verify(p['pins']['postcut_pending_origins']));ck(pending['origin_refs']==p['pending_origin_refs']==a['pending_origin_refs'] and len(p['pending_origin_refs'])==2,'two pending exactrefs');ck(pending['observed_lower_bound']==p['observed_actual_tool_origin_lower_bound']==427,'observed427')
for row,r in zip(pending['origins'],pending['origin_refs']):
 rawdoc=json.loads(verify(r));ck(row['evidence_ref']==r and row['original_payload']==rawdoc,'pending exact original payload:'+row['origin_key']);ck(row['actual_native_product_exit'] is None and row['product_cases_run']==0,'pending notproduct:'+row['origin_key'])
ck(pending['origins'][0]['actual_native_exit'] is None,'036820nativeNULL');ck(pending['origins'][1]['actual_native_exit']==pending['origins'][1]['original_payload']['actual_native_python_exit']==1,'48480eactualPython1')
cl=json.loads(verify(p['pins']['controller_review_input_closure_manifest']));ck(cl['count']==len(cl['entries'])==15,'additiveclosure15')
for r in cl['entries']:verify(r)
ck({path(x['path']) for x in cl['entries']} >= {path(p['pins'][k]['path']) for k in ['integration_controller_review','controller_review_manifest','controller_review_handoff']},'review MF handoff allclosed')
prev=N.parent/'handler38-post-integration-r322'
for i,n in enumerate(['checkpoint','path_ownership','step_state','commands']):ck(original[i]==raw(prev/(n+('.desired.json' if i<2 else '.original.json'))),'322actualsealercontinuity:'+n)
# Bounded read-only Git, never candidate imports or target scripts.
lock=doc(R/'execution/toolchains/locked.json')['tools'];git=lock['git']['path'];ck(ref(git)['sha256']==lock['git']['sha256'],'Git lock current');ck(ref(os.sys.executable)['sha256']==lock['python']['sha256'],'Python lock current')
env={k:v for k,v in os.environ.items() if not k.upper().startswith('GIT_')};env.update(GIT_OPTIONAL_LOCKS='0',GIT_NO_REPLACE_OBJECTS='1',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull)
gitfacts=[]
for label,args in [('head',['rev-parse','HEAD']),('status',['status','--porcelain=v1','--untracked-files=no']),('index',['diff','--cached','--name-only'])]:
 argv=[git,'--no-optional-locks','-c','core.fsmonitor=false','-c','core.untrackedCache=false']+args
 result=subprocess.run(argv,cwd=R,env=env,capture_output=True,timeout=30)
 for suffix,b in [('stdout.raw',result.stdout),('stderr.raw',result.stderr)]:
  with (O/(label+'.'+suffix)).open('xb') as f:f.write(b)
 save(label+'.invocation.json',{'argv':argv,'cwd':str(R),'actual_native_exit':result.returncode,'read_only':True,'automatic_retry':False,'stdout_ref':ref(O/(label+'.stdout.raw')),'stderr_ref':ref(O/(label+'.stderr.raw'))})
 ck(result.returncode==0,'readonlyGit:'+label)
 if result.returncode!=0:raise RuntimeError('Readonly Git failed; stop')
 gitfacts.append({'label':label,'exit':result.returncode})
 if label=='head':ck(result.stdout.decode().strip()==p['head'],'actualMainHEAD')
 if label=='status':ck(hashlib.sha256(result.stdout).hexdigest()==p['git_status_sha256'] and len(result.stdout.splitlines())==13 and sum(x[:2]==b' D' for x in result.stdout.splitlines())==11,'status13 old11D')
 if label=='index':ck(result.stdout==b'','indexempty')
for r,b in zip(p['canonical_before'],original):ck(raw(r['path'])==b,'canonical after unchanged:'+r['path'])
for n,h in pins.items():ck(ref(N/n)['sha256']==h,'draft aftersame:'+n)
save('read-audit.json',{'checks':checks,'check_count':len(checks),'failed':[x for x in checks if not x['passed']],'inputs':list(reads.values()),'verified_ref_count':len(p['verified_refs']),'readonly_git':gitfacts,'copied_canonical_before_refs':copies,'target_script_execution':False,'product_calls':0,'canonical_source_index_writes':0})
print(json.dumps({'checks':len(checks),'failed':sum(not x['passed'] for x in checks),'inputs':len(reads),'verified':len(p['verified_refs']),'Git_readonly_exits':[x['exit'] for x in gitfacts]},ensure_ascii=True))
