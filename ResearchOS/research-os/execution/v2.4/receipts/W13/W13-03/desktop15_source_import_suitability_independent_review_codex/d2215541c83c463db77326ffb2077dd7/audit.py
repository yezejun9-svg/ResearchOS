import pathlib,json,hashlib,subprocess,os,shutil,datetime
R=pathlib.Path('D:/作品集/ResearchOS/research-os')
W=R/'.local/worktrees/codex-w1303-desktop-http-r311'
P=R/'execution/v2.4/receipts/W13/W13-03'
O=P/'desktop15_source_import_suitability_independent_review_codex/d2215541c83c463db77326ffb2077dd7'
B=P/'desktop_exact15_integration_preparation_codex/f5ac31fcc8884b43ba7d25fc4fc75735'
S=P/'desktop_http_exact15_revision_independent_review_codex/874a69212bac4d44be6316a27dc0bf32'
D=P/'desktop_exact15_integration_preparation_revision_codex/e908291811794b64874f5f6f66507916'
G=P/'desktop_go3_debug_component_evidence_independent_review_codex/35ff2da3523e4619b3f7bd763b2c91f2'
C=R/'execution/v2.4/receipts/W05/W05-99/cli43_closed_execution_independent_review_codex/62e0bad3597f4faa9addb47da466fe3e'
checks=[]; inputs={}; cmds=[]
def h(b):return hashlib.sha256(b).hexdigest()
def read(p):
 p=pathlib.Path(p); b=p.read_bytes();inputs[str(p)]={'path':str(p),'sha256':h(b),'bytes':len(b)};return b
def j(p):return json.loads(read(p))
def ck(label,value):checks.append({'check':label,'pass':bool(value)})
def ref(p):read(p);return inputs[str(pathlib.Path(p))]
def pin(v,base=R):
 p=pathlib.Path(v['path']);p=p if p.is_absolute() else base/p
 b=read(p);ck('sha:'+str(p),h(b)==v['sha256']);ck('bytes:'+str(p),len(b)==v['bytes']);return b
rows=j(B/'exact15.json');ck('exact15',len(rows)==15)
source={};before={}
for row in rows:
 p=row['path']; source[p]=pin(row['final_blob_ref']); current=read(W/p)
 ck('WT-equals-frozen:'+p,current==source[p]);ck('mode:'+p,row['after_git']['mode']=='100644' and row['after_git']['kind']=='blob')
 ck('Gitblob:'+p,hashlib.sha1(b'blob '+str(len(current)).encode()+b'\0'+current).hexdigest()==row['after_git']['blob'])
 if row['before_blob_ref']: before[p]=pin(row['before_blob_ref']);ck('Mainpreimage:'+p,read(R/p)==before[p])
 else:ck('Main-new-absent:'+p,not(R/p).exists())
ck('9-existing-6-new',len(before)==9 and len(rows)-len(before)==6)
protected=j(S/'protected17.independent.json')
for row in protected:
 e=row['expected']; b=b''.join(before[e['path']].splitlines(keepends=True)[e['first_line']-1:e['last_line']]);ck('protected-source-hash:'+e['path']+':'+str(e['first_line']),h(b)==e['sha256'] and len(b)==e['bytes']);ck('protected-exact-present:'+e['path']+':'+str(e['first_line']),b in source[e['path']])
ck('protected17',len(protected)==17)
# Hash preparation package; source/evidence modules are read, never imported.
m=j(D/'manifest.json')
for e in m['entries']:pin(e)
prior={}
for label,p in [('source_revision',S/'review.json'),('go3',G/'review.json'),('CLI43',C/'review.json'),('preparation',P/'desktop_exact15_integration_revision_independent_review_codex/87707854354a4cd8ad3a26aaf7627007/review.json')]:
 prior[label]=j(p);ck('prior-no-requests:'+label,prior[label].get('requested_changes')==[])
for p in [S/'collect-audit.json',S/'supplement.actualraw.json',S/'source-diff.stdout.raw',S/'cases.independent.json',G/'raw-summary.json',G/'audit-summary.json']:
 if p.exists():read(p)
# Actual same-cohort author raw records; reuse previous closed compiler/OS audits explicitly.
fm=j(S/'input.finite-matrix.json'); case_rows=[]
for key,value in fm.items():
 if isinstance(value,list):
  for row in value:
   if isinstance(row,dict) and 'actual_native_exit' in row:case_rows.append((key,row))
for group,row in case_rows:
 ck('author-native0:'+row['name'],row['actual_native_exit']==0 and not row.get('timed_out',False) and row.get('status')=='PASS')
 for key in ['stdout_ref','stderr_ref','invocation_ref']:
  if isinstance(row.get(key),dict):pin(row[key],W)
ck('author-169-current-records',len(case_rows)==169)
# Query-only Git, disabled optional locks/replacements; full native output retained.
git=shutil.which('git');ref(git)
env=os.environ.copy();env.update({'GIT_OPTIONAL_LOCKS':'0','GIT_NO_REPLACE_OBJECTS':'1'})
for k in list(env):
 if k.startswith('GIT_') and k not in ['GIT_OPTIONAL_LOCKS','GIT_NO_REPLACE_OBJECTS']:env.pop(k)
def query(name,args,cwd=R):
 argv=[git,'--no-optional-locks',*args]; cp=subprocess.run(argv,cwd=cwd,env=env,capture_output=True,timeout=60)
 for suffix,b in [('stdout.raw',cp.stdout),('stderr.raw',cp.stderr)]:
  with(O/(name+'.'+suffix)).open('xb')as f:f.write(b)
 cmds.append({'name':name,'argv':argv,'cwd':str(cwd),'actual_native_exit':cp.returncode,'stdout_ref':ref(O/(name+'.stdout.raw')),'stderr_ref':ref(O/(name+'.stderr.raw'))});ck('Git0:'+name,cp.returncode==0)
 if cp.returncode:raise RuntimeError('read-only Git failed:'+name)
 return cp.stdout
head=query('main-head',['rev-parse','HEAD']).decode().strip();ck('current-Main43-head',head=='a510dbef4a7e08fb5c428df44c39b133f3ffa856')
changed=query('main43-paths',['diff','--name-only','2cdb0d43d5a600eef13c8f1735946a9adf52d079',head,'--','apps','internal','tests','adapters','ops','go.mod','go.sum']).decode().splitlines()
ck('Main43-exact-unique',len(changed)==43 and len(set(changed))==43);ck('disjoint15',not(set(changed)&set(source)));ck('union58',len(set(changed)|set(source))==58)
tree=query('candidate15-tree',['ls-tree','-r','-z','06b1fbcb5934cbc70e5d65a46481e60c05c6594b','--',*source],W)
actual={}
for entry in tree.split(b'\0'):
 if entry:
  meta,p=entry.split(b'\t',1);mode,kind,blob=meta.decode().split();actual[p.decode()]={'mode':mode,'kind':kind,'blob':blob}
ck('candidate-tree-exact15',set(actual)==set(source))
for row in rows:ck('actual-tree:'+row['path'],actual.get(row['path'])==row['after_git'])
# Original current source files rehashed at end; no changes accepted into the baseline.
for p,b in source.items():ck('WT-after-stable:'+p,read(W/p)==b)
for p,b in before.items():ck('Main-preimage-after-stable:'+p,read(R/p)==b)
for row in rows:
 if row['path'] not in before:ck('Main-absence-after:'+row['path'],not(R/row['path']).exists())
result={'schema':'researchos.desktop15-import-suitability-read-audit.v1','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':checks,'failed':[x for x in checks if not x['pass']],'inputs':list(inputs.values()),'git_invocations':cmds,'source15':rows,'main43_paths':changed,'candidate_tree':actual,'author_case_records':len(case_rows),'reuse_limits':['Prior full 8577 compilation/runtime qualification closure not re-executed or fully rehashed this turn.','Prior Go3 actual evidence review retained; no SQL/process/module import performed.'],'actual_product_executions':0,'canonical_mutations':0}
with(O/'read-audit.json').open('x',encoding='utf-8',newline='\n')as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'checks':len(checks),'failed':result['failed'],'inputs':len(inputs),'author_records':len(case_rows),'git_calls':len(cmds),'audit':ref(O/'read-audit.json')},ensure_ascii=False))
