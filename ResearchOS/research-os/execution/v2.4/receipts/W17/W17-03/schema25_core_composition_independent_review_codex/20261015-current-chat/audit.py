import pathlib,json,hashlib,subprocess,collections,datetime
R=pathlib.Path('D:/作品集/ResearchOS/research-os'); E=pathlib.Path(__file__).parent
A=R/'execution/v2.4/receipts/W17/W17-03/schema25_core_composition_source_codex/20261015-current-chat'
W=R/'.local/worktrees/schema25-core-composition-20261015'
S=R/'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp495/four-branch-composition-independent-review-scope.json'
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def sha(b):return hashlib.sha256(b).hexdigest()
def pin(p):return dict(path=str(p),sha256=sha(p.read_bytes()),bytes=p.stat().st_size)
def write(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def git(*a,cwd=W):return subprocess.check_output(['git','-c','maintenance.auto=false','-c','gc.auto=0',*a],cwd=cwd)
scope=read(S);assert sha(S.read_bytes())=='97359676bf50db701388c12a7ee5bab9d1a4e7cc2929bf8897e1227fda82ae11'
verified={}
def refs(x):
 if isinstance(x,dict):
  if 'path' in x and 'sha256' in x and ('bytes' in x or pathlib.Path(x['path']).is_absolute()):
   p=pathlib.Path(x['path']);p=p if p.is_absolute() else R/p
   assert p.is_file(),str(p)
   assert sha(p.read_bytes())==x['sha256'],str(p)
   if 'bytes' in x:assert p.stat().st_size==x['bytes'],str(p)
   verified[str(p)]=pin(p)
  for v in x.values():refs(v)
 elif isinstance(x,list):
  for v in x:refs(v)
refs(scope)
final=read(A/'FINAL.json');add=read(A/'FINAL-ADDENDUM.json');refs(final);refs(add)
plan=read(R/scope['map_ref']['path']);refs(plan['inputs'])
for f in ['source-input-inventory.json','NATIVE-EVIDENCE-MANIFEST.json','T1-summary.json','T3R-historical-pins.json','T5R-queue-assets.json']:
 if (A/f).exists():refs(read(A/f))
assert git('rev-parse','HEAD').decode().strip()==scope['candidate']
assert git('rev-parse','HEAD^{tree}').decode().strip()==scope['candidate_tree']
assert git('status','--porcelain=v1')==b''
changed=git('diff','--name-only',scope['base'],scope['candidate']).decode().splitlines()
assert changed==sorted(plan['bounded_builder_scope']['source_paths'])==final['exact_changed_paths']
expected=plan['bounded_builder_scope']['expected_final_blobs']
for p,b in expected.items():
 raw=git('show',scope['candidate']+':'+p);assert sha(raw)==b['sha256'] and sha((W/p).read_bytes())==b['sha256']
for p in plan['main']['protected']:
 assert sha(git('show',scope['candidate']+':'+p['path']))==p['main']['sha256']==sha((W/p['path']).read_bytes())
for stage in plan['stages']:
 for x in stage['files']:
  for key in ['base','candidate','expected_before']:
   b=x[key]
   if b:assert sha(git('cat-file','blob',b['blob']))==b['sha256']
full=read(A/'candidate-full-tree.json')
entries=[]
for row in git('ls-tree','-r','-z',scope['candidate']).split(b'\0'):
 if not row:continue
 meta,p=row.split(b'\t',1);mode,kind,oid=meta.decode().split();entries.append(dict(path=p.decode(),mode=mode,kind=kind,object=oid))
assert entries==full['entries']
assert git('diff','--binary','--no-ext-diff','--no-textconv',scope['base'],scope['candidate'])==(A/'candidate-source.patch').read_bytes()
tests=[]
for t in final['tests']:
 c=read(t['receipt']['path']);refs(c);raw=pathlib.Path(c['stdout']['path']).read_text(encoding='utf-8-sig');counts=collections.Counter();names=[]
 for line in raw.splitlines():
  try:x=json.loads(line)
  except ValueError:continue
  if isinstance(x,dict) and x.get('Action') in ['pass','fail','skip'] and x.get('Test') and '/' not in x['Test']:counts[x['Action']]+=1;names.append([x['Action'],x['Test']])
 if c.get('go_test_top_level'):assert {k:counts[k] for k in ['pass','fail','skip']}==c['go_test_top_level']
 assert c['native_exit']==t['native_exit']
 if 'source_guard_before_sha256' in c:assert c['source_guard_before_sha256']==c['source_guard_after_sha256'] and not c['source_guard_drift']
 tests.append(dict(label=t['label'],argv=c['argv'],cwd=c['cwd'],native_exit=c['native_exit'],counts=dict(counts),names=names,environment=c.get('environment_allowlist')))
original=read(R/'execution/v2.4/receipts/W05/W05-99/current_chat_integration_preflight_codex/20261012-current-chat/preflight-v2.json')['protected_source']
for x in original:assert sha((R/x['path']).read_bytes())==x['sha256'] and x['path'] not in changed
write('main-original9-guard.json',dict(files=original,project_identity=pin(R/'execution/project_identity.json')))
mainstatus=git('status','--porcelain=v1','--untracked-files=no',cwd=R).decode().splitlines()
assert len(mainstatus)==20 and not git('diff','--cached','--name-only',cwd=R)
assert git('rev-parse','HEAD',cwd=R).decode().strip()==scope['base']
write('audit.json',dict(status='PASS',scope=pin(S),verified_references=list(verified.values()),verified_count=len(verified),candidate=scope['candidate'],tree=scope['candidate_tree'],full_tree_entries=len(entries),source_paths=changed,protected_main=plan['main']['protected'],main_tracked_status=mainstatus,main_index_empty=True,tests=tests,formal_increment=0))
print(json.dumps(dict(status='PASS',verified=len(verified),full_tree_entries=len(entries),source_count=len(changed),tests=len(tests))))
