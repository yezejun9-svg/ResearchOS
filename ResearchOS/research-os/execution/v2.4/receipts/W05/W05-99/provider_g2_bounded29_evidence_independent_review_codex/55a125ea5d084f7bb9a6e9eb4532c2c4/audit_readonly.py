from pathlib import Path
import json,hashlib,re,subprocess,os
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).parent;N=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/root-g2-execute29-launch-r313'
refs={};checks=[]
def ck(n,v):checks.append({'check':n,'passed':bool(v)})
def path(x):
 p=Path(x);return p if p.is_absolute() else R/p
def read(p):
 p=path(p);b=p.read_bytes();refs[str(p)]={'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};return b
def doc(p):return json.loads(read(p))
def verify(x):
 b=read(x['path']);ck('SHA '+x['path'],hashlib.sha256(b).hexdigest()==x['sha256'] and len(b)==x['bytes']);return b
def save(n,d):
 p=O/n;p.write_bytes((json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode());return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
A=doc(N/'execution-audit.json');M=doc(N/'manifest.json');ck('Root audit expected pin',refs[str(N/'execution-audit.json')]['sha256']=='56832030b32ad62d494007cf55542c93ed742fbbcfa5007ccd2d2e3f90cd072e');ck('Root manifest expected pin',refs[str(N/'manifest.json')]['sha256']=='7839b708640f215320a2d62d1e44914ec739575123deed98f1ad0de0504ad26b')
ck('manifest count',len(M['entries'])==M['count']==484)
for x in M['entries']:verify(x)
print('manifest484 hashed',flush=True)
P=json.loads(verify(A['prepared_ref']));S=json.loads(verify(A['spec_ref']));G=doc(N/'authorization.execute.json');V=doc(N/'invocation.json');E=Path(G['output_root'])/'execute'
ck('actual outer/controller0',V['actual_exit']==0 and V['wrapper_error'] is None and A['actual_outer_exit']==A['actual_controller_exit']==0)
for k in ['runner','launcher','scope','grant','stdout','stderr']:verify(V[k])
ck('grant and exactcandidate',G['actual_registration_completed'] is True and G['candidate']==S['candidate']==P['source_commit']==A['candidate'])
ck('exact29grantroster',G['roster']==[r['selector'] for r in S['roster']] and len(S['roster'])==29)
ck('preparedgrant',G['prepared_sha256']==A['prepared_ref']['sha256'] and G['spec_sha256']==A['spec_ref']['sha256'])
verify(P['exe']);ck('exe pin',P['exe']==A['exe_ref'])
F=doc(E/'inputs.before-first.json');fm={x['path'].casefold():x for x in F['observed']};ck('41963 unique noerrors',len(fm)==len(F['observed'])==41963 and F['errors']==[]);ck('41958originalsubset',len(P['inputs'])==41958 and all(fm.get(x['path'].casefold())==x for x in P['inputs']))
results=[];summaries=[];snapshot_count=0;http_count=0;models=0
for i,entry in enumerate(A['qualified_finite_leaves']):
 d=json.loads(verify(entry['result_ref']));slot=S['roster'][i];folder=path(entry['result_ref']['path']).parent;proc=json.loads(verify(d['process']));pdir=path(d['process']['path']).parent
 ck('roster '+str(i),d['index']==i and d['selector']==slot['selector'] and entry['leaf']==slot['leaf'] and d['status']=='PASS_LOCAL_FIXTURE_NOT_ACCEPTED')
 for nm in ['all-inputs.before.json','all-inputs.after-native.json','all-inputs.after-fixtures.json']:
  vector=doc(folder/nm);ck(str(i)+' '+nm,vector['errors']==[] and vector['observed']==F['observed'])
 cleanup=proc['result']['job_cleanup'];ck('ownedjob '+str(i),proc['actual_exit']==proc['result']['actual_exit']==0 and proc['result']['resumed'] is True and proc['result']['error'] is None and proc['result']['timed_out'] is False and cleanup['errors']==[] and all(cleanup.get(k) is True for k in ['kill_on_job_close_configured','assigned_before_resume','primary_exit_confirmed','job_idle_confirmed','handles_closed']))
 ck('argv '+str(i),proc['argv'][0]==P['exe']['path'] and proc['argv'][-1]=='-test.run='+slot['selector'] and Path(proc['cwd'])==Path(G['work_root'])/'source/internal/domain')
 stdout=read(pdir/'stdout.raw').decode('utf-8');read(pdir/'stderr.raw');ck('exact nativePASS '+str(i),[v for v in re.findall(r'^\s*--- PASS: (\S+)',stdout,re.M) if '/' in v]==[slot['leaf']] and not re.search(r'^\s*--- (FAIL|SKIP):',stdout,re.M))
 for ev in d['evidence']:verify(ev)
 snaps=json.loads(verify(d['snapshot_audit']));snapshot_count+=len(snaps)
 for snap in snaps:
  verify(snap['snapshot']);ck('snapshotshape '+str(i),snap['integrity']==[['ok']] and snap['method']=='author fixture VACUUM INTO' and snap['source_original_file_retained'] is False and snap['implicit_rowid_checked'] is False and isinstance(snap['schema'],list) and isinstance(snap['tables'],dict))
 models+=d['MODEL'];ck('modelcap '+str(i),d['MODEL']==slot['MODEL_calls'])
 observed=[]
 for ev in d['evidence']:
  ep=path(ev['path'])
  if re.fullmatch(r'http-\d+\.json',ep.name):http_count+=1
  if ep.name=='provider-http-counts.json':
   pc=doc(ep);ck('loopbackcounts '+str(i),pc['external_paid_requests']==0 and pc['mode']=='LOOPBACK_FIXTURE' and pc['model_requests']==d['MODEL']);observed.append(pc)
  if ep.name=='quarantine.json':
   q=doc(ep);ck('quarantine '+str(i),q['original_state']=='UNKNOWN' and q['sdk_result_count']==0 and q['observation_count']==0 and q['model_calls']==1)
  if ep.name=='original-model-cause.json':
   q=doc(ep);ck('originalcause '+str(i),q['matches'] is True and type(q['model_success_ack']) is int and q['model_success_ack']==0)
 summaries.append({'index':i,'selector':slot['selector'],'native_exit':proc['actual_exit'],'snapshots':len(snaps),'MODEL':d['MODEL'],'provider_counts':observed,'result_ref':entry['result_ref']});results.append(d)
 print('case',i,'closed',flush=True)
aggregate=doc(E/'result.json');ck('aggregateexact',aggregate['results']==results and aggregate['MODEL_loopback']==models==4 and aggregate['snapshots']==snapshot_count==13 and http_count==4 and aggregate['source_ready'] is False)
final=doc(E/'inputs.after-all.json');ck('finalfullvector',final['errors']==[] and final['observed']==F['observed'])
protected=json.loads(verify(S['protected_functions']));ck('priorindependentprotectedproof',all(x['both_found'] and x['byte_equal'] and x['sha256']==x['author_body_sha256'] for x in protected['rows']))
# Read immutable Git blobs only; no candidate module import or source execution.
env={k:v for k,v in os.environ.items() if not k.upper().startswith('GIT_')};env.update(GIT_OPTIONAL_LOCKS='0',GIT_NO_REPLACE_OBJECTS='1',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='nul')
git='C:/Program Files/Git/cmd/git.exe';git_inv=[]
for index,name in enumerate(S['source_paths']):
 argv=[git,'-C',str(R),'show',S['candidate']+':'+name];z=subprocess.run(argv,env=env,capture_output=True);(O/f'git-source-{index}.stdout.raw').write_bytes(z.stdout);(O/f'git-source-{index}.stderr.raw').write_bytes(z.stderr);git_inv.append({'argv':argv,'actual_exit':z.returncode});ck('gitblobexit '+name,z.returncode==0)
 current=Path(G['work_root'])/'source'/name;b=read(current);ck('candidatecompiledsource '+name,z.stdout==b);ck('sourceinbeforefirst '+name,any(x['sha256']==hashlib.sha256(b).hexdigest() and x['bytes']==len(b) and Path(x['path'])==current for x in F['observed']))
changed=[git,'-C',str(R),'diff-tree','--no-commit-id','--name-only','-r',S['candidate']];z=subprocess.run(changed,env=env,capture_output=True);git_inv.append({'argv':changed,'actual_exit':z.returncode});(O/'git-delta.stdout.raw').write_bytes(z.stdout);(O/'git-delta.stderr.raw').write_bytes(z.stderr);ck('exact2immutablecommit',z.returncode==0 and set(z.stdout.decode().splitlines())==set(S['source_paths']))
save('git_invocations.json',git_inv);save('case_summary.json',summaries);save('input_refs.json',list(refs.values()));au=save('audit.json',{'checks':checks,'failed':[x for x in checks if not x['passed']],'manifest_entries':484,'casecount':29,'vectors_compared':89,'runtime_underlying41963_rehashed':False,'SQL_opened':False,'product_replayed':False})
r=save('review.json',{'schema':'researchos.provider-g2-bounded-finite-evidence-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'READY_FOR_REGISTERING_BOUNDED_FINITE29' if all(x['passed'] for x in checks) else 'REQUEST_CHANGES','requested_changes':[x for x in checks if not x['passed']],'candidate':S['candidate'],'audit_ref':au,'root_execution_audit_ref':refs[str(N/'execution-audit.json')],'root_manifest_ref':refs[str(N/'manifest.json')],'native_cases':29,'native_failures':0,'native_skips':0,'loopback_MODEL_calls':4,'snapshot_count':13,'original_prepared_inputs':41958,'execution_inputs':41963,'scope':'Registration of this bounded independent fixture cohort and exact2 test-source provenance only','limitations':['No new product/SQL/Node/HTTP/model execution by reviewer','Stored complete vectors compared; underlying41963 files not rehashed again','13 snapshots are VACUUM INTO images, not original live DB files; implicit rowid and original storage layout not proven','Bootstrap HTTP total remains UNKNOWN_NOT_INSTRUMENTED','Original UNKNOWN outcomes and zero successful SDK consumption in quarantine controls retained','Original history5/held positive/earlier failures remain; no retry authorization','No whole9 source qualification, Main23 composition, LIVE provider, parent or formal acceptance'],'source_acceptance':False,'Main_integration_authorized':False,'formal_increment':0,'failure_origins':[]})
entries=[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in sorted(O.iterdir()) if p.is_file()];m=save('manifest.json',{'entries':entries,'count':len(entries),'self_excluded':True});h=save('handoff.json',{'review_ref':r,'manifest_ref':m,'failure_origins':[]});print(json.dumps({'review':r,'manifest':m,'handoff':h,'checks':len(checks),'failures':[x for x in checks if not x['passed']]},ensure_ascii=False))
