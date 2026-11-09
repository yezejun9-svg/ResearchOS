import pathlib,json,subprocess,os,hashlib,collections,datetime
R=pathlib.Path.cwd();O=pathlib.Path(__file__).resolve().parent;W=R/'.local/worktrees/codex-w0599-model-stream';N='execution/v2.4/receipts/W05/W05-99/model_stream_executor_codex/quarantine-repair-d0b997f135f24c748c6e99e98a5e7f01';P=W/N;C='890d4c164bffad73e562ceacfdc216820d0313fd';B='0bbcef5347ed9bd3a1174c7d3df9dfd8a270e837'
sha=lambda b:hashlib.sha256(b).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def ref(p,root=W):
 b=p.read_bytes();return {'path':p.relative_to(root).as_posix(),'sha256':sha(b),'bytes':len(b)}
env={k:v for k,v in os.environ.items() if not k.upper().startswith('GIT_')};env['GIT_NO_REPLACE_OBJECTS']='1'
def git(*args):return subprocess.check_output(['git','--no-replace-objects',*args],cwd=W,env=env)
changed=git('diff-tree','--no-commit-id','--name-only','-r',C).decode().splitlines();manifest=load(P/'commit_manifest.json');errors=[];blobchecks=[]
# Batch exact committed blobs and compare filesystem bytes.
result=subprocess.run(['git','--no-replace-objects','cat-file','--batch'],cwd=W,env=env,input=''.join(C+':'+p+'\n' for p in changed).encode(),capture_output=True);assert result.returncode==0
pos=0
for p in changed:
 stop=result.stdout.index(b'\n',pos);head=result.stdout[pos:stop].split();size=int(head[2]);start=stop+1;data=result.stdout[start:start+size];pos=start+size+1;file=(W/p).read_bytes();ok=file==data;blobchecks.append({'path':p,'git_blob':head[0].decode(),'sha256':sha(data),'bytes':size,'filesystem_equal':ok});
 if not ok:errors.append(blobchecks[-1])
checks=[]
for x in manifest['files']:
 a=ref(W/x['path']);ok=a['sha256']==x['sha256'] and a['bytes']==x['bytes'];checks.append({**a,'match':ok});
 if not ok:errors.append(checks[-1])
manifestpaths={x['path'] for x in checks}|{N+'/commit_manifest.json'};delta={'manifest_not_changed':sorted(manifestpaths-set(changed)),'changed_not_manifest':sorted(set(changed)-manifestpaths)}
if delta['manifest_not_changed'] or delta['changed_not_manifest']:errors.append(delta)
handoff=load(P/'handoff.json');references=[];seen=set()
def walk(x):
 if isinstance(x,dict):
  if 'path' in x and 'sha256' in x and isinstance(x['path'],str) and x['path'].startswith('execution/'):
   key=(x['path'],x['sha256'])
   if key not in seen:
    seen.add(key);a=ref(W/x['path']);ok=a['sha256']==x['sha256'] and ('bytes' not in x or a['bytes']==x['bytes']);references.append({**a,'match':ok});
    if not ok:errors.append(references[-1])
  for v in x.values():walk(v)
 elif isinstance(x,list):
  for v in x:walk(v)
for n in ['handoff.json','failure_origins.json','all_new_runs.json','original_refs.json']:walk(load(P/n))
runs=[];common=None;current=[]
for rr in handoff['final_runs']:
 before=load(W/rr['source_before_ref']['path']);after=load(W/rr['source_after_ref']['path']);counts=collections.Counter();top=collections.Counter()
 for line in (W/rr['stdout_ref']['path']).read_text(encoding='utf-8').splitlines():
  try:x=json.loads(line)
  except ValueError:continue
  a=x.get('Action');t=x.get('Test')
  if t and a in ('pass','fail','skip'):
   counts[a]+=1
   if '/' not in t:top[a]+=1
 runs.append({'directory':rr['directory'],'before_after_equal':before==after,'input_count':len(before),'result':load(W/rr['directory']/'result.json'),'counts_including_subtests':dict(counts),'top_level_counts':dict(top),'invocation':load(W/rr['invocation_ref']['path'])})
 if before!=after:errors.append({'drift':rr['directory']})
 if common is None:common=before
 elif common!=before:errors.append({'different_final_vectors':True})
for path,h in common.items():
 kind,relative=path.split(':',1)
 p= W/relative if kind=='repo' else R/relative if kind=='main' else pathlib.Path(relative) if kind=='absolute' else None
 if p is None:raise ValueError('unexpected vector prefix '+kind)
 # Only explicit compile/source paths and the published fixture inputs in original vector.
 b=p.read_bytes();ok=sha(b)==h
 if not ok:errors.append({'input':path,'expected':h,'actual':sha(b)})
 current.append({'path':path,'sha256':sha(b),'bytes':len(b),'match':ok})
source=[]
for x in load(P/'source_manifest.json'):
 old=git('show',B+':'+x['path']);new=(W/x['path']).read_bytes();ok=sha(old)==x['before_sha256'] and sha(new)==x['after_sha256'];source.append({**x,'match':ok})
 if not ok:errors.append(source[-1])
old_nonroots=[]
# All files from base commit remain byte-identical in child except exact three approved files.
for p in git('diff','--name-only',B,C).decode().splitlines():
 if not p.startswith('execution/') and p not in handoff['exact_changed_source']:errors.append({'unauthorized_source':p})
protected={'worker':ref(W/'adapters/runtime/mu/worker.mjs'),'cli_v2':ref(W/'apps/cli/cli_v2.go'),'bundle':{'path':str(W/'.local/model-stream/mu-worker.mjs'),'sha256':sha((W/'.local/model-stream/mu-worker.mjs').read_bytes())}}
out={'schema':'researchos.independent-repaired-stream-audit.v1','candidate':C,'parent':B,'handoff':ref(P/'handoff.json'),'commit_manifest':ref(P/'commit_manifest.json'),'actual_commit_blob_count':len(changed),'manifest_entries':len(checks),'manifest_delta':delta,'commit_blob_checks':blobchecks,'manifest_checks':checks,'reference_checks':references,'source_checks':source,'final_runs':runs,'current_vector_count':len(current),'current_vector_checks':current,'protected':protected,'errors':errors,'git_status_after':git('status','--porcelain').decode(),'time':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(O/'integrity_audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'blobs':len(changed),'manifest':len(checks),'refs':len(references),'inputs':len(current),'runs':[(x['counts_including_subtests'],x['top_level_counts']) for x in runs],'errors':errors}));
