from pathlib import Path
import hashlib,json,subprocess,collections,re,gzip,sys
sys.stdout.reconfigure(encoding='utf-8');o=Path(__file__).parent;r=o.parents[6];w=r/'.local/worktrees/codex-w0599-model-stream';c='c571781e9703bc7a96fa63629e0cc3bee7f3deec';b=w/'execution/v2.4/receipts/W05/W05-99/model_stream_executor_codex';s=b/'signed-zero-repair-437e95d3f0ef47b486f0c29594d3f6d2'
h=lambda x:hashlib.sha256(x).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def git(*args):return subprocess.check_output(['git',*args],cwd=w)
files=git('diff-tree','--no-commit-id','--name-only','-r',c).decode().splitlines();errors=[];blobs=[]
for f in files:
 raw=git('show',c+':'+f);actual=(w/f).read_bytes();blobs.append({'path':f,'sha256':h(raw),'bytes':len(raw)});
 if raw!=actual:errors.append(['COMMIT_BYTES',f])
manifest=load(s/'commit_manifest.final.json'); listed={x['path']:x['sha256']for x in manifest['files']}
for f,sha in listed.items():
 if h((w/f).read_bytes())!=sha:errors.append(['MANIFEST',f])
extra=set(files)-set(listed)
refs=[]
def walk(x):
 if isinstance(x,dict):
  if isinstance(x.get('path'),str)and isinstance(x.get('sha256'),str):
   p=w/x['path']
   if not p.is_file()or h(p.read_bytes())!=x['sha256']:errors.append(['REF',x['path']])
   refs.append(x['path'])
  for y in x.values():walk(y)
 elif isinstance(x,list):
  for y in x:walk(y)
for p in s.glob('*.json'):
 if p.name!='commit_manifest.final.json':walk(load(p))
cohorts=[]
for n in ['closure-39d83fc9302f42ceb4e91d3403a96044','closure-6f4e2cb1bf1d4aa48376dbc02eeb2b8c']:
 p=b/n;v=load(p/'source_before.json');a=load(p/'source_after.json');drift=[]
 for key,sha in v.items():
  prefix,rel=key.split(':',1);actual={'main':r,'repo':w}.get(prefix,Path())/rel
  if not actual.is_file()or h(actual.read_bytes())!=sha:drift.append(key)
 raw=(p/'test.stdout').read_text(encoding='utf-8');counts={k:len(re.findall(r'^\s*--- '+k+r':',raw,re.M)) for k in ['PASS','FAIL','SKIP']}
 cohorts.append({'path':n,'count':len(v),'before_after_equal':v==a,'current_drift':drift,'raw_counts':counts,'exit':load(p/'test.invocation.json')['exit'],'raw_sha256':h((p/'test.stdout').read_bytes())})
 if drift or v!=a:errors.append(['CLOSURE',n])
current=load(b/'closure-39d83fc9302f42ceb4e91d3403a96044/source_before.json'); prior_candidates=[]
for p in b.glob('closure-*/source_before.json'):
 old=load(p)
 if len(old)==39053 and old.get('repo:internal/domain/runtime_model_stream.go')=='6120a450686530b6e98ddb28b7f4df9c1b06ad6aea402add4361a5874d91b075':prior_candidates.append(p)
prior=load(prior_candidates[0]);removed={k:v for k,v in prior.items()if k not in current};changed={k:{'before':prior[k],'after':v}for k,v in current.items()if k in prior and prior[k]!=v}
status=git('status','--porcelain','-z');(o/'candidate-status.raw').write_bytes(status);deleted=[]
for line in status.decode().split('\0'):
 if line.startswith(' D '):
  f=line[3:];raw=git('show',c+':'+f);old=git('show','890d4c164bffad73e562ceacfdc216820d0313fd:'+f);deleted.append({'path':f,'candidate_blob_sha256':h(raw),'prior_blob_equal':raw==old,'absent_from_candidate_diff':f not in files})
check=load(s/'commit_check_failure.json');gz=gzip.decompress((s/'broad-check.stdout.gz').read_bytes());gzip_ok=h(gz)==check['stdout_sha256'] and len(gz)==check['stdout_bytes']
x={'commit':c,'changed_commit_blobs':len(files),'blob_inventory':blobs,'manifest_entries':len(listed),'unlisted_commit_paths':sorted(extra),'validated_json_refs':len(refs),'cohorts':cohorts,'prior_vector_ref':str(prior_candidates[0]),'removed_inputs':removed,'changed_inputs':changed,'added_inputs':sorted(set(current)-set(prior)),'unstaged_deletions':deleted,'worktree_clean':not status,'preserved_commit_check_raw_verified':gzip_ok,'errors':errors}
(o/'audit.json').write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in x.items()if k not in ['blob_inventory','unstaged_deletions']},ensure_ascii=False))
