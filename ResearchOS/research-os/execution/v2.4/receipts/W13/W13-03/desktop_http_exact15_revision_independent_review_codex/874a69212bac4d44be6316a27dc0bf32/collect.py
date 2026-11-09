from pathlib import Path
import hashlib,json,subprocess,os,zipfile,re,datetime
R=Path('D:/作品集/ResearchOS/research-os');W=R/'.local/worktrees/codex-w1303-desktop-http-r311';O=Path(__file__).parent
N=W/'execution/v2.4/receipts/W13/W13-03/desktop_http_exact15_executor_codex/revision-r317-a7f44ed9b4ae4225bd072adcf708e24b';F=N/'final-audit-2d44db33d4874f8bb806b44137292e08';C=N/'cohort-19e75d3970f54c2eab44fcac2f43d61d';P=W/'execution/v2.4/receipts/W13/W13-03/desktop_http_exact15_executor_codex/revision-r317-postcommit-460fe81bdb0b47bb80dd2ade52c554f3';OLD=R/'execution/v2.4/receipts/W13/W13-03/desktop_http_exact15_source_independent_review_codex/094badb378bf4323a24a5d8bb2c09ab1'
checks=[];inputs=[];gitrecords=[]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def ref(p):p=Path(p);return {'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
def ck(n,v):checks.append({'check':n,'passed':bool(v)})
def save(n,v):
 b=v if isinstance(v,bytes) else (json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
 with (O/n).open('xb') as f:f.write(b)
 return ref(O/n)
def doc(p):return json.loads(Path(p).read_bytes())
def resolve(x,base=W):p=Path(x['path']);return p if p.is_absolute() else base/p
def verify(x,base=W):
 p=resolve(x,base);a=ref(p);inputs.append(a);ck('ref '+str(p),a['sha256']==x['sha256'] and a['bytes']==x['bytes']);return p
E={k:v for k,v in os.environ.items() if not k.upper().startswith('GIT_')};E.update(GIT_OPTIONAL_LOCKS='0',GIT_NO_REPLACE_OBJECTS='1',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='nul')
def git(label,*args):
 argv=['C:/Program Files/Git/cmd/git.exe',*args];z=subprocess.run(argv,cwd=W,env=E,capture_output=True);gitrecords.append({'argv':argv,'actual_exit':z.returncode,'cwd':str(W),'stdout_ref':save(label+'.stdout.raw',z.stdout),'stderr_ref':save(label+'.stderr.raw',z.stderr)});ck('git '+label,z.returncode==0);return z.stdout
ck('posthandoff',sha(P/'handoff.json')=='bceaaf04d37a6a18186eda1c29480c916239ccfc438b1a483327c8c53966d583');h=doc(F/'handoff.json');ck('handoff pin',sha(F/'handoff.json')=='53d6d8796982540bf4f6b4b42f9b40047e7633ccaed560bdbd3ef438015e469c')
for k,x in h.items():
 if isinstance(x,dict) and {'path','sha256','bytes'}<=x.keys():verify(x)
for name in ['handoff.json','manifest.json','whole15.current.json','finite-matrix.json','revision-accounting.json','source-commit.json','failure-origins.json']:save('input.'+name,(F/name).read_bytes())
source='06b1fbcb5934cbc70e5d65a46481e60c05c6594b';head='f630d97574df11ff1d7c692a50312ddde3f6743f';prior='0f708eaf0c624fb721f7c9a00d5465ef5f13a68c';base='2cdb0d43d5a600eef13c8f1735946a9adf52d079'
ck('head',git('head','rev-parse','HEAD').decode().strip()==head);ck('tracked clean',git('status','status','--porcelain=v1','--untracked-files=no')==b'');ck('parent',git('parent','rev-parse',source+'^').decode().strip()==prior)
changes=git('delta','diff','--name-only',prior,source).decode().splitlines();whole=doc(F/'whole15.current.json');delta=doc(F/'source-commit.json')['delta_paths'];ck('exact6',set(changes)=={x['path'] for x in delta} and len(changes)==6);ck('whole15',set(git('whole','diff','--name-only',base,source,'--','apps','tests').decode().splitlines())=={x['path'] for x in whole} and len(whole)==15)
git('source-diff','diff',prior,source,'--');post=git('evidencepaths','diff','--name-only',source,head).decode().splitlines();ck('receipt2519only',len(post)==2519 and all(x.startswith('execution/v2.4/receipts/W13/W13-03/') for x in post))
source_map={};olds={}
for i,x in enumerate(whole):
 b=verify(x).read_bytes();source_map[x['path']]=b;save('source-%02d.current'%i,b);ck('source Git '+x['path'],git('blob-%02d'%i,'show',source+':'+x['path'])==b)
priorfacts=doc(OLD/'protected-independent.json');originalscope=doc(OLD/'input-source-scope-audit.json')
for i,x in enumerate(originalscope['rows']):
 if not x['new']:olds[x['path']]=(OLD/('base-blob-%02d.stdout.raw'%i)).read_bytes()
spans=[]
for x in priorfacts:
 e=x['expected'];b=b''.join(olds[e['path']].splitlines(keepends=True)[e['first_line']-1:e['last_line']]);ok=hashlib.sha256(b).hexdigest()==e['sha256'] and len(b)==e['bytes'] and b in source_map[e['path']];ck('protected '+e['path']+str(e['first_line']),ok);spans.append({'expected':e,'preserved':ok})
save('protected17.independent.json',spans);ck('protected count',len(spans)==17)
manifest=doc(F/'manifest.json');mf=[]
for x in manifest['files']:
 p=verify(x);mf.append({'path':str(p),'matched':checks[-1]['passed']})
save('manifest.independent.json',{'manifest_ref':ref(F/'manifest.json'),'count':len(mf),'rows':mf})
# Independently match immutable tree IDs and current bytes, including evidence-only commit.
rawtree=git('tree','ls-tree','-rz',head);tree={}
for line in rawtree.split(b'\0'):
 if line:
  meta,path=line.split(b'\t',1);tree[path.decode('utf-8')]=meta.split()[2].decode()
blobs=[]
for x in doc(P/'evidence-git-blobs.json'):
 b=(W/x['path']).read_bytes();oid=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();ok=oid==x['git_blob']==tree.get(x['path']);ck('receipt Git '+x['path'],ok);blobs.append({'path':x['path'],'blob':oid,'matched':ok})
save('receipt-blobs.independent.json',blobs)
print(json.dumps({'stage':'source/manifest/Git','checks':len(checks),'failed':[x for x in checks if not x['passed']]},ensure_ascii=True),flush=True)
frozen=doc(C/'full-finite-inputs.json');current=doc(F/'full-inputs.current.json');norm=lambda rows:[{k:x[k] for k in ['path','sha256','bytes']} for x in rows];ck('8577 vector exact',len(frozen)==len(current)==8577 and norm(frozen)==norm(current));iv=[]
for x in current:
 a=ref(Path(x['path']));ok=a['sha256']==x['sha256']==x['current_sha256'] and a['bytes']==x['bytes'];ck('current '+x['path'],ok);iv.append({'expected':x,'actual':a,'matched':ok})
save('inputs.independent-current.json',iv)
archive=doc(F/'archive-entries.json');zp=verify(archive['archive']);zs=[]
with zipfile.ZipFile(zp) as z:
 ck('zip names',len(z.namelist())==len(archive['entries']) and set(z.namelist())=={x['entry'] for x in archive['entries']})
 for x in archive['entries']:
  b=z.read(x['entry']);ok=hashlib.sha256(b).hexdigest()==x['sha256'] and len(b)==x['bytes'];ck('zip '+x['entry'],ok);zs.append({'entry':x['entry'],'matched':ok})
save('archive.independent.json',zs)
m=doc(F/'finite-matrix.json');ck('counts169',len(m['rows'])==162 and len(m['regressions'])==7 and m['original159_actual_pass']==159 and m['supplemental3_actual_pass']==3 and m['regressions7_actual_pass']==7 and m['Node_leaf_and_program_fail']==m['skip']==m['not_run']==0)
cases=[]
for group in ['rows','regressions']:
 for row in m[group]:
  inv=doc(verify(row['invocation_ref']));out=verify(row['stdout_ref']).read_bytes();verify(row['stderr_ref']);ck('case '+row['name'],row['actualargv']==inv['actualargv'] and row['actual_native_exit']==inv['actual_native_exit']==0 and row['timed_out'] is False and row['status']=='PASS' and row['http_count']<=row['http_cap'] and row['child_count']<=row['child_cap'])
  if group=='rows':ck('TAP '+row['name'],b'# pass 1' in out and b'# fail 0' in out and b'# skipped 0' in out and row['name'].encode() in out)
  cases.append({'group':group,'name':row['name'],'invocation_ref':row['invocation_ref'],'stdout_ref':row['stdout_ref'],'http':row['http_count'],'children':row['child_count']})
for x in m['actual_runs']:
 p=verify(x);v=doc(p);ck('cohort '+str(p),v['cohort']==m['cohort']=='19e75d3970f54c2eab44fcac2f43d61d' and not v['drift'] and v['full_input_count']==8577 and v['not_run']==0 and v['first_unexpected'] is None);after=doc(p.parent/'inputs.after.json');ck('after exact '+str(p),norm(after)==norm(frozen) and all(q['sha256']==q['current_sha256'] for q in after));inputs.append(ref(p.parent/'inputs.after.json'))
ck('current HTTP158',sum(x['http'] for x in cases)==158);save('cases.independent.json',cases)
account=doc(F/'revision-accounting.json');ck('history bounds',account['current_cohort_HTTP']==158 and account['r317_author_all_HTTP']==162 and account['all_history_HTTP']==464 and account['all_history_cap']==692 and account['failed_leaf_0bbcd5_still_fail'] is True)
for x in doc(F/'failure-origins.json').values():
 if isinstance(x,dict) and 'path' in x:verify(x)
for x in whole:verify(x)
save('collect-audit.json',{'checks':checks,'failed':[x for x in checks if not x['passed']],'input_refs':inputs,'git_invocations':gitrecords,'counts':{'manifest':len(mf),'evidenceGit':len(blobs),'currentinputs':len(iv),'archive':len(zs),'Node':169},'actual_product_execution':False});print(json.dumps({'stage':'complete','checks':len(checks),'failed':[x for x in checks if not x['passed']]},ensure_ascii=True),flush=True)
