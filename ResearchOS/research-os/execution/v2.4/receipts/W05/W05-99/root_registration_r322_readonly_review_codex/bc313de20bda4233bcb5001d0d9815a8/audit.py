import ast,hashlib,json
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).resolve().parent
S=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/handler38-post-integration-r322'
P=S.parent/'fresh-handler38-source-integration-r321-v2'
reads={};checks=[]
def check(n,v):checks.append({'check':n,'pass':bool(v)})
def path(p):
 p=Path(p);return p if p.is_absolute() else R/p
def read(p):
 p=path(p);b=p.read_bytes();rr={'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
 if str(p) in reads:check('unchanged:'+str(p),reads[str(p)]==rr)
 reads[str(p)]=rr;return b
def verify(x):
 b=read(x['path']);check('ref:'+x['path'],hashlib.sha256(b).hexdigest()==x['sha256'] and len(b)==x['bytes']);return b
def ref(p):read(p);return reads[str(path(p))]
def doc(p):return json.loads(read(p))
def refs(v):
 if isinstance(v,dict):
  if {'path','sha256','bytes'}<=v.keys():verify(v)
  else:
   for x in v.values():refs(x)
 elif isinstance(v,list):
  for x in v:refs(x)
def save(n,d):
 with (O/n).open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
 return ref(O/n)
fixed={'register.py':'7c1c077e48676929eb8eed10244b357c5080350317b09c9fef15def5745ada3a','run.py':'56e0b20a7e5b3944a683d0e87a7e09285f57c7805d916ba8e2c9486d6bef03f5','prepared_refs.json':'7807254f66783f87e65b4f6eb3181d17e4ba06d539435e0696d09d56ef8b89db','audit.json':'52067306f29465d72baa31e4e83b0a7ccea7ae6f89d739f497b87a91e1f79e0e','seal.py':'3f97359ecc5d0de268a4497e8face97b5e2ac99ade618ce1eeda009ffb3e64e9'}
texts={}
for n,h in fixed.items():
 b=read(S/n);check('fixed:'+n,hashlib.sha256(b).hexdigest()==h)
 if n.endswith('.py'):ast.parse(b,filename=n);texts[n]=b.decode();check('AST:'+n,True)
p=doc(S/'prepared_refs.json');a=doc(S/'audit.json');refs(p);refs(a)
check('verified250',len(p['verified_refs'])==250)
canon=p['canonical_before'];names=['checkpoint','path_ownership','step_state','commands']
check('ordered4',[x['path'] for x in canon]==['execution/v2.4/'+n+'.json' for n in names])
copies=[];docs=[]
for n,x in zip(names,canon):
 b=verify(x);docs.append(json.loads(b));prev=P/(n+('.desired.json' if n in names[:2] else '.original.json'))
 check('previous321-bytes:'+n,b==read(prev))
 dest=O/(n+'.before.json')
 with dest.open('xb') as f:f.write(b)
 c=ref(dest).copy();c['path']=dest.relative_to(R).as_posix();copies.append(c)
cp,ow=docs[:2];check('actual321149422',[cp['revision'],ow['revision'],len(cp['failure_counters'])]==[321,149,422])
check('canonical-old-head',cp['head']=='2cdb0d43d5a600eef13c8f1735946a9adf52d079')
check('new-prepared-head',p['head']=='a5d6d16ffaf129de0361470c3a1570228bd259a2')
check('status-fixed',p['git_status_sha256']=='e03849874f27dcf3b079cb84c9bae69ad97311118da47c3122a5a9b32b9611b4')
check('audit-tuple',a['expected_before']==[321,149,422] and a['expected_after']==[322,150,425])
check('audit-origin-list',a['new_origins']==p['origins'])
keys=[x['origin_key'] for x in p['origins']];oldkeys={x.get('origin_key') for x in cp['failure_counters']}
check('unique3-new',len(keys)==len(set(keys))==3 and not oldkeys.intersection(keys))
for i,x in enumerate(p['origins']):
 original=json.loads(verify(x['evidence_ref']));check('original-exact:'+x['origin_key'],original==x['original_payload'])
 check('exits:'+x['origin_key'],x['actual_outer_exit']==1 and x['actual_native_exit']==[None,1,1][i] and x['actual_native_product_exit'] is None and x['product_cases_run']==0)
check('old-two-pending-to-register',p['pending_origin_refs']==cp['work_in_progress']['r321_cut_pending_actual_tool_origin_refs'] and [x['sha256'] for x in p['pending_origin_refs']]==[x['evidence_ref']['sha256'] for x in p['origins'][:2]])
pins=p['pins'];closed=json.loads(verify(pins['main38_completed']));mf=json.loads(verify(pins['main38_manifest']))
check('completed38-one',closed['actual_head']==p['head'] and closed['unique_paths']==38 and closed['merge_attempts']==1 and closed['canonical_writes']==0 and closed['whole_W05_acceptance'] is False)
check('manifest179',mf['count']==len(mf['entries'])==179);refs(mf['entries'])
invs=[x for x in mf['entries'] if x['path'].endswith('.invocation.json')];check('56-native-invocations',len(invs)==56)
ff=0
for x in invs:
 d=json.loads(verify(x));pr=d['process_observation'];jc=pr['job_cleanup']
 check('owned0:'+Path(x['path']).name,d['actual_native_exit']==pr['actual_exit']==0 and d['wrapper_error'] is None and pr['error'] is None and pr['timed_out'] is False and pr['resumed'] is True and jc['errors']==[] and all(jc[k] is True for k in ['unnamed_exclusive_job','assigned_before_resume','kill_on_job_close_configured','primary_exit_confirmed','job_idle_confirmed','handles_closed']))
 refs(d['stdout_ref']);refs(d['stderr_ref'])
 if Path(x['path']).name=='fast-forward.invocation.json':
  ff+=1;check('exact-one-FF-argv',d['argv'][-5:]==['merge','--ff-only','--no-autostash','--no-edit',p['head']])
check('oneFF',ff==1)
outer=json.loads(verify(pins['main38_outer_completion']));check('outer-null-native',outer['actual_outer_exit']==0 and outer['reported_root_launcher_exit']==0 and outer['actual_root_launcher_native_exit_separately_observed'] is None and outer['this_record_is_not_original_native_stdout_or_stderr'] is True)
source=json.loads(verify(pins['main38_source_after']));check('source38',len(source)==38)
for row in source:verify(row)
ex=path(pins['main38_completed']['path']).parent
for n,want in [('after-head.stdout.raw',(p['head']+'\n').encode()),('after-status.stdout.raw',read(path(json.loads(verify(pins['scope']))['status_ref']['path']))),('after-index.stdout.raw',b'')]:check('saved-final:'+n,read(ex/n)==want)
r=texts['register.py'];w=texts['run.py'];s=texts['seal.py']
guards={
 'all4-before-replace':'assert all(canonical.read_bytes() == expected_live[canonical] for canonical in CANON)',
 'expected-live-update':'expected_live[path] = raw','READS-update':'READS[path] = raw',
 'ref-current-before-write':'assert all(path.read_bytes() == raw for path, raw in READS.items())',
 'old422-prefix':"assert actual['failure_counters'][:422] == old_failures",
 'formal-unchanged':"assert actual['current_effective_formal_status'] == json.loads(before[CANON[0]])['current_effective_formal_status']",
 'head-forward-only':"cp['head'] = head",
 'explicit-validation-not-authorised':'handler38_fresh_combined_validation_authorized=False',
 'writer-release':"integration.update(current_source_writer=None",
 'no-optimisation':'if sys.flags.optimize:',
 'failure-intent':"save('canonical-write.exception.json'"}
for n,t in guards.items():check(n,t in r)
check('intent-first',r.index("intent_ref = save(")<r.index('os.replace('))
check('copies-bound-within-parent','assert copied_path.is_relative_to(review_path.parent)' in w)
check('wrapper-checks-before-start',w.index("for item in prepared['canonical_before']:")<w.index('subprocess.run('))
check('sealer-schema',"'schema': 'researchos.main38-post-integration-registration-audit.v1'" in s)
check('sealer-completed-manifest-head',all(t in s for t in ["'completed_ref': prepared['pins']['main38_completed']","'manifest_ref': prepared['pins']['main38_manifest']","'registered_head': cp_after['head']"]))
check('sealer-actual0',"assert invocation['actual_exit'] == 0" in s)
check('sealer-no-new-authority',"'Main_integration_authorized': False" in s and "'source_acceptance': False" in s)
for name in ['checkpoint','ownership','failure_origins']:check('final-output:'+name,('"'+name+'"') in r or ("'"+name+"'") in r)
for pth,row in list(reads.items()):
 b=Path(pth).read_bytes();check('current-stable:'+pth,len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256'])
save('checks.json',{'checks':checks,'failed':[x for x in checks if not x['pass']],'product_executions':0,'target_imports':0})
save('reads.json',list(reads.values()));save('canonical-copies.json',copies)
print(json.dumps({'checks':len(checks),'failed':sum(not x['pass'] for x in checks),'reads':len(reads)},ensure_ascii=True))
