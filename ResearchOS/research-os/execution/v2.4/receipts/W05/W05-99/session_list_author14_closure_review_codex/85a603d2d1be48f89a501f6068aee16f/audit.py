import base64, hashlib, json, pathlib, subprocess, datetime

MAIN=pathlib.Path('D:/作品集/ResearchOS/research-os')
WT=MAIN/'.local/worktrees/codex-w0599-session-list-proof-r312'
OUT=pathlib.Path(__file__).parent
NS=pathlib.Path('execution/v2.4/receipts/W05/W05-99/session_list_closedcopy_exact1_executor_codex')
SRC='a5d6d16ffaf129de0361470c3a1570228bd259a2'
BASE='534857db99fa5e694987f877af74c322eaa2a0b3'
REC='fa73a24f4dd5a9d3246650551aa54b98043fb8fd'
inputs={}; checks=[]; git_calls=[]
def sha(b): return hashlib.sha256(b).hexdigest()
def read(p):
 p=pathlib.Path(p); b=p.read_bytes(); inputs[str(p)]={'path':str(p),'sha256':sha(b),'bytes':len(b)}; return b
def j(p): return json.loads(read(p))
def save(n,v):
 p=OUT/n
 with p.open('x',encoding='utf8',newline='\n') as f: json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
 return {'path':str(p.relative_to(MAIN)).replace('\\','/'),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size}
def ck(name,condition,detail=None): checks.append({'check':name,'pass':bool(condition),'detail':detail})
def resolve(p):
 p=pathlib.Path(p); return p if p.is_absolute() else WT/p
def ref(r):
 b=read(resolve(r['path'])); ck('reference:'+r['path'],sha(b)==r['sha256'] and len(b)==r.get('bytes',len(b)));return b
def git(args):
 argv=['git','-c','core.quotepath=false',*args];r=subprocess.run(argv,cwd=WT,capture_output=True)
 idx=len(git_calls);(OUT/f'git-{idx}.stdout.raw').write_bytes(r.stdout);(OUT/f'git-{idx}.stderr.raw').write_bytes(r.stderr)
 git_calls.append({'argv':argv,'cwd':str(WT),'actual_exit':r.returncode,'stdout':f'git-{idx}.stdout.raw','stderr':f'git-{idx}.stderr.raw'})
 ck('git-exit:'+str(idx),r.returncode==0);return r.stdout

hpath=WT/NS/'postcommit-v4/final_handoff.json';h=j(hpath)
ck('handoff-pin',inputs[str(hpath)]['sha256']=='3d9d409ba5888dca94c22c380b22da1bb6b1a9d1ba0a145a33ecab5ea723ec7b')
s=json.loads(ref(h['execution_summary']));report=json.loads(ref(s['execution_report']))
pm=json.loads(ref(h['public_manifest']));post=json.loads(ref(h['postcommit_manifest']))
tree={}
for entry in git(['ls-tree','-rz',REC]).split(b'\0'):
 if entry:
  meta,p=entry.split(b'\t',1);tree[p.decode('utf8')]=meta.split()[2].decode()
public_git=0
for collection,label in [(pm['files'],'public'),(post['files'],'postcommit')]:
 for r in collection:
  b=ref(r);p=r['path'].replace('\\','/')
  if label=='public':
   ck('public-git-blob:'+p,tree.get(p)==hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest());public_git+=1
ck('source-parent',git(['rev-parse',SRC+'^']).decode().strip()==BASE)
ck('receipt-parent',git(['rev-parse',REC+'^']).decode().strip()==SRC)
sp=git(['diff-tree','--no-commit-id','--name-only','-r',SRC]).decode().splitlines()
rp=git(['diff-tree','--no-commit-id','--name-only','-r',REC]).decode().splitlines()
ck('source-exact1',sp==['internal/api/v2_sessions_test.go'],sp)
ck('receipts-exact-namespace',len(rp)==1505 and all(p.startswith(str(NS).replace('\\','/')+'/') for p in rp),{'count':len(rp)})
source=git(['show',SRC+':internal/api/v2_sessions_test.go']);base=git(['show',BASE+':internal/api/v2_sessions_test.go']);old=git(['show','22752a6a41732c8c158d7d7e1b8932ec958f8cb8:internal/api/v2_sessions_test.go'])
ck('source-expected-hash',sha(source)==h['source_sha256']);ck('source-current-equal',read(WT/h['source_path'])==source)
marker=b'// Only the host';oldbody=old[old.index(marker):];ck('protected-body',len(oldbody)==14633 and sha(oldbody)=='c8451df67e00833e54d95219693301916f20a45dbda236196a14f9956c2688b1' and oldbody in source)
suffix=b'func TestSessionListHTTPOriginalContextIdentity';ck('original14-suffix',source[source.index(suffix):]==base[base.index(suffix):])
git(['diff',BASE,SRC,'--','internal/api/v2_sessions_test.go'])
domain=git(['show',SRC+':internal/domain/client_protocol_sessions.go']);ck('domain-unchanged',sha(domain)=='7fb40c79ba73d4605431e6f8b5aec5730fc32de5b4a7e8537cdfc603b6862ce3')
exe=ref(s['compiled_exe']);exe_hash=sha(exe)
vectors=[];anchor=None
for x in s['before_after_checks']:
 v=json.loads(ref(x['ref']));rows={i['path']:(i['sha256'],i['bytes']) for i in v['files']};ck('vector-errors:'+x['ref']['path'],not v['errors'] and not x['errors'])
 if len(rows)==18264:
  if anchor is None: anchor=rows
  ck('full-vector-exact-equal:'+x['ref']['path'],rows==anchor)
 vectors.append({'ref':x['ref'],'count':len(rows),'equal_to_full_anchor':rows==anchor})
ck('full-vectors-at-least42',sum(v['count']==18264 for v in vectors)>=42)
cases=[];http=0
for c in report['cases']:
 inv=json.loads(ref(c['process']));result=inv['result'];job=result['job_cleanup'];rawdir=resolve(c['process']['path']).parent
 stdout=read(rawdir/'stdout.raw').decode('utf8');stderr=read(rawdir/'stderr.raw')
 ck('case-native:'+c['name'],inv['actual_exit']==c['actual_native_exit']==0 and not result['timed_out'] and not result['error'] and not inv['wrapper_error'])
 ck('case-native-stdout:'+c['name'],f'--- PASS: TestSessionListHTTPOriginalContextIdentity/{c["name"]} ' in stdout and '\nPASS\n' in stdout.replace('\r\n','\n') and '--- SKIP:' not in stdout and '--- FAIL:' not in stdout)
 ck('case-owned-job:'+c['name'],all(job[k] for k in ['unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','job_idle_confirmed','primary_exit_confirmed','handles_closed']) and job['active_processes_last_observed']==0 and not job['errors'])
 ck('case-binary:'+c['name'],anchor.get(inv['argv'][0],(None,))[0]==exe_hash)
 db=ref(c['DB']['database']);d=resolve(c['DB']['database']['path']).parent
 proof=j(d/'closed-proof.json');assertions=j(d/'assertions.json');original=j(d/'closed-original.files.json')
 ck('case-closed-db:'+c['name'],sha(db)==proof['closed_copy_sha256']==original['']['sha256'] and original['-wal'] is None and original['-shm'] is None and not proof['case_failed'])
 for name in ['closed-original.sidecars.json','closed-copy.before.sidecars.json','closed-copy.after.sidecars.json']:
  sides=j(d/name);ck('sidecars:'+c['name']+':'+name,all(not v['exists'] and v['error'] is None for v in sides.values()))
 ck('current-copy-sidecars-absent:'+c['name'],all(not pathlib.Path(str(d/'closed.sqlite')+suffix).exists() for suffix in ['-wal','-shm']))
 before=j(d/'closed.rows.json');after=j(d/'post-open.rows.json');ck('all-schema-typed-row-equal:'+c['name'],before==after)
 pairs=sorted(d.glob('http-*.request.raw'));n=len(pairs);http+=n
 ck('case-http-count:'+c['name'],n==proof['HTTP_calls_including_setup']==assertions['HTTP_calls_including_setup']==c['wire']['HTTP_calls_including_setup'] and n<=8)
 for req in pairs:
  for kind in ['request','response']:
   raw=req.with_name(req.name.replace('request',kind));meta=j(raw.with_suffix('.json'));b=read(raw);ck('wire-raw:'+raw.name+':'+c['name'],sha(b)==meta['sha256'] and len(b)==meta['bytes'])
 ck('assertions-reached:'+c['name'],assertions['all_assertions_reached'])
 # Validate private original-envelope bytes against saved request; no SQL or protocol hash reimplementation.
 for jp in sorted(d.glob('journal-*.json')):
  jr=j(jp)
  if isinstance(jr,dict) and jr.get('headers'):
   hdr=json.loads(jr['headers']);raw=base64.b64decode(hdr['raw_envelope_base64'],validate=True)
   ck('journal-original-raw:'+c['name']+':'+jp.name,any(raw==p.read_bytes() for p in pairs))
 cases.append({'name':c['name'],'native_exit':inv['actual_exit'],'HTTP':n,'owned_job':job,'process_ref':c['process'],'database_ref':c['DB']['database'],'proof':{'path':str(d/'closed-proof.json'),'sha256':inputs[str(d/'closed-proof.json')]['sha256']}})
ck('case-totals',len(cases)==report['PASS_leaves']==s['leaf_pass']==14 and report['SKIP']==s['skip']==0 and http==report['HTTP_total']==s['HTTP_total']==78)
for oldfail in s['prior_three_origins']:
 f=json.loads(ref(oldfail['failure']));iv=json.loads(ref(oldfail['driver']));ck('prior-origin:'+oldfail['tool_ref'],oldfail['driver_exit']==oldfail['outer_exit']==1 and oldfail['unique_origin']==1 and oldfail['cases_executed']==0)
save('git_invocations.json',git_calls)
save('case_audit.json',cases);save('vector_audit.json',vectors)
before=list(inputs.values());save('input_before.json',before)
after=[]
for r in before:
 b=pathlib.Path(r['path']).read_bytes();after.append({'path':r['path'],'sha256':sha(b),'bytes':len(b)})
save('input_after.json',after);ck('review-inputs-no-drift',before==after)
save('checks.json',checks)
failed=[x for x in checks if not x['pass']]
review={'actor':'codex:/root/sources_parent_impl','status':'REQUEST_CHANGES' if failed else 'READY_FOR_ROOT_INDEPENDENT_FINITE14','scope':'Non-author exact1 source and sealed author14 evidence audit; not Root replay or source acceptance','source_commit':SRC,'receipt_commit':REC,'public_manifest_count':len(pm['files']),'public_git_blob_count':public_git,'postcommit_manifest_count':len(post['files']),'author_actual_leaves':14,'author_skip':0,'HTTP_total_recounted':http,'full_vector_count':18264,'recorded_vectors_audited':len(vectors),'owned_job_count':len(cases),'old_origins_preserved':s['prior_three_origins'],'failed_checks':failed,'review_product_executions':0,'review_SQL_open_or_queries':0,'review_network':0,'source_acceptance':False,'formal_increment':0,'limits':['Recorded schema and typed-row exports compared byte/structure-wise; no independent SQLite execution in this read-only review.','Same-user file-path TOCTOU and implicit rowid not separately exported remain stated limits.','Author outer bff0ef exit0 is sealed author/root-reported provenance; this reviewer did not rerun its tool.','Ready only for Root independent finite14; not CURRENT/Main/formal acceptance.']}
rv=save('source_review.json',review)
manifest=save('manifest.json',{'files':[{'path':str(p.relative_to(MAIN)).replace('\\','/'),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size} for p in sorted(OUT.iterdir()) if p.is_file()]})
hand=save('handoff.json',{'status':review['status'],'review':rv,'manifest':manifest,'writer':'STOPPED','source_acceptance':False,'failed_checks_count':len(failed)})
print(json.dumps({'handoff':hand,'review':rv,'manifest':manifest,'failed_checks':failed,'input_count':len(before)},ensure_ascii=False))
