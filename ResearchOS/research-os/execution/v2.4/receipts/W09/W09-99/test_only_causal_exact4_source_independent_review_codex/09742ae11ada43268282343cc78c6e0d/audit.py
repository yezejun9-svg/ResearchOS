import hashlib,json,os,pathlib,re,subprocess,datetime
OUT=pathlib.Path(__file__).parent
R=pathlib.Path('D:/作品集/ResearchOS/research-os')
W=R/'.local/worktrees/codex-w0999-causal-controls-r320-9a15d49131e8'
N=W/'execution/v2.4/receipts/W09/W09-99/test_only_causal_exact4_executor_codex/9a15d49131e846159a16b8125ed79c99'
SOURCE='cd0d818baa703fbc59a6f7c8187d467d41570094'
RECEIPT='a4b545828653f6343bae73b180493de478c4cb1d'
BASE='2cdb0d43d5a600eef13c8f1735946a9adf52d079'
HANDLER='22752a6a41732c8c158d7d7e1b8932ec958f8cb8'
checks=[]; reads={}; git_calls=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(p,v):
 with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
def read(p):
 p=pathlib.Path(p); b=p.read_bytes(); reads[str(p)]={'path':str(p),'sha256':sha(b),'bytes':len(b)};return b
def check(name,ok,details=None):checks.append({'name':name,'passed':bool(ok),'details':details})
def refcheck(r,label):
 b=read(r['path']);check(label,sha(b)==r['sha256'] and len(b)==r['bytes']);return b
env={k:v for k,v in os.environ.items() if not k.upper().startswith('GIT_')}
env.update(GIT_OPTIONAL_LOCKS='0',GIT_NO_REPLACE_OBJECTS='1',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='nul')
def git(args,label):
 argv=['C:/Program Files/Git/cmd/git.exe','-C',str(W)]+args
 p=subprocess.run(argv,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 (OUT/(label+'.stdout.raw')).write_bytes(p.stdout);(OUT/(label+'.stderr.raw')).write_bytes(p.stderr)
 rec={'argv':argv,'actual_exit':p.returncode,'stdout_ref':{'path':str(OUT/(label+'.stdout.raw')),'sha256':sha(p.stdout),'bytes':len(p.stdout)},'stderr_ref':{'path':str(OUT/(label+'.stderr.raw')),'sha256':sha(p.stderr),'bytes':len(p.stderr)}}
 git_calls.append(rec)
 if p.returncode:raise RuntimeError('Git read failed '+label)
 return p.stdout
pins={'handoff.json':'1340758a56842800acef0c2a3384195d95d741eaa5b88698fd044dae90f07de0','manifest.json':'466734e217bab0ffc0dac5c3be90a8c6d04f76f0993349d8a2f0e6baf6afc564','protected-source-audit.json':'c9f963b797c983b1bf7a7340bdf3c9ff21f9dae3249e7fdb077c7fae7cffd2c3','implemented-roster.json':'822bba59a1db04ef551467363f7b17bfbdc1dc3296008ec083fb79451f3616ac'}
docs={}
for name,h in pins.items():
 b=read(N/name);check('input-pin:'+name,sha(b)==h);docs[name]=json.loads(b)
check('head-receipt',git(['rev-parse','HEAD'],'head').decode().strip()==RECEIPT)
check('tracked-clean',not git(['status','--porcelain=v1','--untracked-files=no'],'status').strip())
check('source-parent',git(['rev-parse',SOURCE+'^'],'source-parent').decode().strip()==BASE)
check('receipt-parent',git(['rev-parse',RECEIPT+'^'],'receipt-parent').decode().strip()==SOURCE)
paths=docs['protected-source-audit.json']['source_paths']
delta=git(['diff-tree','--no-commit-id','--name-only','-r',SOURCE],'source-delta').decode().splitlines()
check('source-exact4',set(delta)==set(paths) and len(delta)==4,delta)
receipt_delta=git(['diff-tree','--no-commit-id','--name-only','-r',RECEIPT],'receipt-delta').decode().splitlines()
members=docs['manifest.json']['members'];check('manifest179',len(members)==179)
expected={str(pathlib.Path(x['path']).relative_to(W)).replace('\\','/') for x in members}|{str((N/'manifest.json').relative_to(W)).replace('\\','/')}
check('receipt-exact180',set(receipt_delta)==expected and len(receipt_delta)==180)
objects=git(['ls-tree','-r',RECEIPT,'--',str(N.relative_to(W)).replace('\\','/')],'receipt-tree').decode().splitlines()
blobmap={line.split('\t',1)[1]:line.split('\t',1)[0].split()[2] for line in objects}
for row in members+[{'path':str(N/'manifest.json'),'sha256':pins['manifest.json'],'bytes':len(read(N/'manifest.json'))}]:
 b=refcheck(row,'receipt-current:'+pathlib.Path(row['path']).name)
 rp=str(pathlib.Path(row['path']).relative_to(W)).replace('\\','/')
 bh=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
 check('receipt-gitblob:'+rp,blobmap.get(rp)==bh)
handler_delta=set(git(['diff-tree','--no-commit-id','--name-only','-r',HANDLER],'handler-delta').decode().splitlines())
check('disjoint-handler38',len(handler_delta)==38 and not set(paths)&handler_delta)
source_rows=[];tops=[]
for i,row in enumerate(docs['protected-source-audit.json']['rows']):
 p=row['path']; current=read(W/p);before=git(['show',BASE+':'+p],f'base-{i}');committed=git(['show',SOURCE+':'+p],f'source-{i}');handler=git(['show',HANDLER+':'+p],f'handler-{i}')
 check('source-current-blob:'+p,current==committed)
 check('base-handler-identical:'+p,before==handler)
 check('base-pin:'+p,sha(before)==row['before_sha256'])
 snap=refcheck(row['current_ref'],'source-snapshot:'+p);check('snapshot-current:'+p,snap==current)
 # Exact original post-import body, not normalized text or a suffix-only proxy.
 original_end=before.index(b'\n)\n')+3 if b'\n)\n' in before else before.index(b'\r\n)\r\n')+5
 body=before[original_end:];offset=row['protected_current_byte_offset'];check('protected-body:'+p,len(body)==row['protected_body_bytes'] and sha(body)==row['protected_body_sha256'] and current[offset:offset+len(body)]==body)
 prefix=current[:offset]
 for imp in row['added_imports']:prefix=prefix.replace(('\t"'+imp+'"\n').encode(),b'').replace(('\t"'+imp+'"\r\n').encode(),b'')
 check('imports-only:'+p,prefix==before[:original_end])
 tail=current[offset+len(body):].decode('utf-8');newtops=re.findall(r'^func (Test\w+)\(',tail,re.M)
 check('new-top-count:'+p,len(newtops)==row['new_top_functions'])
 check('no-skips-or-trigger-removal:'+p,not re.search(r'\bt\.Skip|(?i:DROP\s+TRIGGER)',tail))
 tops.extend(newtops);source_rows.append({'path':p,'sha256':sha(current),'bytes':len(current),'old_body_sha256':sha(body),'old_body_bytes':len(body),'new_top_functions':newtops})
inputs=json.loads(read(N/'public-inputs.before-after.json'));check('31-static-inputs',len(inputs['before'])==len(inputs['after'])==31 and inputs['drift_during_capture']==[])
after={r['path']:r for r in inputs['after']}
for row in inputs['before']:
 actual=refcheck(row['actual_ref'],'static-input-current');snapshot=refcheck(row['snapshot_ref'],'static-input-snapshot');check('snapshot-current-equal',actual==snapshot)
 check('before-after-equal',row['actual_ref']==after.get(row['actual_ref']['path']))
 if not row['authorized_test_change']:check('original-proposal-unchanged',row['actual_ref']['sha256']==row['original_proposal_ref']['sha256'])
roster=docs['implemented-roster.json'];check('roster-counts',len(roster['rows'])==41 and len(set(r['selector'] for r in roster['rows']))==41 and len(tops)==21 and len(roster['old_regressions'])==8)
check('roster-top-mapping',set(r['selector'].split('/')[0] for r in roster['rows'])==set(tops))
check('all-not-run',all(r['execution']=='NOT_RUN' for r in roster['rows']+roster['old_regressions']))
check('conditional2',sum(bool(r['resource_conditional']) for r in roster['rows'])==2)
for k in (1,2):
 d=json.loads(read(N/f'format-{k:02}.invocation.json'));res=d['result'];job=res['job_cleanup']
 check(f'gofmt-{k}-actual0',d['actual_native_exit']==res['actual_exit']==0 and res['resumed'] is True and not res['timed_out'] and res['error'] is None and all(job[x] is True for x in ['assigned_before_resume','job_idle_confirmed','primary_exit_confirmed','handles_closed']) and job['errors']==[])
# Read-only production inputs for the human causal review; no DB or program execution.
for p in ['internal/domain/auth.go','internal/domain/materialize.go','internal/domain/retrieval_local.go','internal/domain/sources.go','internal/domain/evidence_origin.go','internal/domain/retrieval.go','adapters/retrieval/local.go','migrations/sqlite/0002_domain.sql']:
 b=read(W/p);q=OUT/'reviewed-source'/p;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b)
for p in paths:
 q=OUT/'reviewed-source'/p;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(read(W/p))
dump(OUT/'read_audit.json',{'schema':'researchos.independent-read-audit.v1','inputs':list(reads.values()),'git_invocations':git_calls,'source_rows':source_rows,'checks':checks,'failed_checks':[x for x in checks if not x['passed']],'actual_product_executions':0,'actual_SQL_reads':0,'semantic_compilation':'NOT_RUN'})
print(json.dumps({'checks':len(checks),'failed_checks':[x for x in checks if not x['passed']],'manifest_members':len(members),'source_rows':source_rows},ensure_ascii=False))
