import ast, hashlib, json
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os')
O=Path(__file__).resolve().parent
P=R/'execution/v2.4/receipts/W05/W05-99/main_exact38_integration_preparation_codex/revision-v2-ed1a1dab301a40b293dd6a177980cfaf'
S=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/fresh-handler38-source-integration-r321-v2'
reads={}; checks=[]
def read(p):
 p=Path(p); p=p if p.is_absolute() else R/p
 raw=p.read_bytes(); row={'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
 if str(p) in reads: check('unchanged-read:'+str(p),reads[str(p)]==row)
 reads[str(p)]=row
 return raw
def check(name,ok,detail=None):checks.append({'check':name,'pass':bool(ok),'detail':detail})
def verify(x):
 raw=read(x['path']); check('ref:'+x['path'],len(raw)==x['bytes'] and hashlib.sha256(raw).hexdigest()==x['sha256']); return raw
def doc(p):return json.loads(read(p))
def refs(value):
 if isinstance(value,dict):
  if {'path','sha256','bytes'}<=value.keys(): verify(value)
  else:
   for v in value.values():refs(v)
 elif isinstance(value,list):
  for v in value:refs(v)
def save(n,d):
 with (O/n).open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
pins={P/'integrate_exact38.v2.py':'e2f98bded200afc15cf1afecbc73d0423dcc1ab0a16e5497ca4a1dd7e244d6ff',P/'manifest.json':'d0f188833adec9b098f872c21134352f0ac4b67588b133472fe7d6abffecde7f',S/'scope_registration.json':'254642660280442df4352e355d0e01f6c0fc8bab8bc7337554d6bbc26a223f90',S/'grant-producer.py':'dfbed4a9feb172a46aafa426775605428a1dc1f47d69b3d1c6cf91c50b0d6577',S/'prepare.py':'d172c6f9f6ab781f90be1a20146111af697da64862690a1d6c7f3268e1cd31f6'}
for p,h in pins.items():
 raw=read(p);check('pin:'+str(p),hashlib.sha256(raw).hexdigest()==h)
 if p.suffix=='.py':ast.parse(raw,filename=str(p));check('AST:'+str(p),True)
mf=doc(P/'manifest.json');check('manifest20',mf['count']==len(mf['entries'])==20);refs(mf['entries'])
scope=doc(S/'scope_registration.json');refs(scope);refs(doc(P/'handoff.json'))
exact=json.loads(verify(scope['exact38_ref']));prot=json.loads(verify(scope['protected_ref']))
check('exact38',len(exact)==len({x['path'] for x in exact})==38)
check('protected5173',len(prot)==5173);refs(prot)
runtime=json.loads(verify(scope['runtime_resources_ref']));check('runtime1211',len(runtime['files'])==1211);refs(runtime['files'])
mode=json.loads(verify(scope['mode_supplement_ref']));attr=json.loads(verify(scope['root_attributes_supplement_ref']))
check('mode-exactkeys',set(mode)=={'schema','source_map_ref','exact38_ref','target_tree_ref','target_commit','relative_path','git_row'})
check('attr-exactkeys',set(attr)=={'schema','root_path','raw_ref','base_tree_ref','target_tree_ref','base_commit','target_commit','git_row','original_protected_ref'})
refs(mode);refs(attr)
def tree(ref):
 result={}
 for line in verify(ref).split(b'\0'):
  if not line:continue
  head,name=line.split(b'\t',1);m,k,b=head.decode('ascii').split();key=name.decode('utf-8');check('unique-tree:'+key,key not in result);result[key]={'mode':m,'kind':k,'blob':b}
 return result
before=tree(attr['base_tree_ref']);after=tree(attr['target_tree_ref'])
check('control-single-mode',mode['git_row']==after['apps/control/main.go'] and mode['git_row']['mode']=='100644' and mode['git_row']['kind']=='blob')
check('attribute-blob',before['.gitattributes']==after['.gitattributes']==attr['git_row'] and attr['git_row']['blob']=='fa1385d99a319b43c06f5309d1aae9fdd3adea46')
raw=verify(attr['raw_ref']);check('attribute-raw',raw==b'* -text\n' and hashlib.sha1(b'blob 8\0'+raw).hexdigest()==attr['git_row']['blob'])
oldprot=json.loads(verify(attr['original_protected_ref']));check('prefix5172-plus1',len(oldprot)==5172 and prot==oldprot+[attr['raw_ref']])
oldmap=json.loads(verify(mode['source_map_ref']));mapping={x['relative_path']:x for x in oldmap}
check('original37-mode-only-one-missing',[x['relative_path'] for x in oldmap if 'mode' not in x]==['apps/control/main.go'])
check('tree-only38',sorted(k for k in set(before)|set(after) if before.get(k)!=after.get(k))==[x['path'] for x in exact])
for x in exact:
 m=mapping[x['path']]
 check('source-map:'+x['path'],x['after_git']==after[x['path']] and x['after_sha256']==m['sha256'] and x['after_bytes']==m['bytes'] and x['after_git']['blob']==m['git_blob'] and x['after_git']['mode']==(mode['git_row']['mode'] if x['path']=='apps/control/main.go' else m['mode']))
 if x['before_worktree']:verify(x['before_worktree'])
 else:check('new-source-absent:'+x['path'],not (R/x['path']).exists())
copies=[]
for n in ['checkpoint','path_ownership','step_state','commands']:
 p=R/'execution/v2.4'/f'{n}.json';raw=read(p); old=read(P/f'canonical.current.{n}.json');check('canonical-current:'+n,raw==old)
 with (O/f'{n}.before.json').open('xb') as f:f.write(raw)
 copies.append({'canonical_path':str(p),'copied_path':str(O/f'{n}.before.json'),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
cp=doc(R/'execution/v2.4/checkpoint.json');ow=doc(R/'execution/v2.4/path_ownership.json');check('current320148417',[cp['revision'],ow['revision'],len(cp['failure_counters'])]==[320,148,417])
check('future-only321149422',scope['expected_registration']==[321,149,422] and scope['Main_integration_currently_authorized'] is False)
for p in scope['old_deleted_paths']:check('old-deletion:'+p,not (R/p).exists())
for p in [P/'controller.v1-v2.diff',S/'derivation-audit.json',S/'derive.py']:read(p)
save('checks.json',{'checks':checks,'failed':[x for x in checks if not x['pass']],'native_product_executions':0,'target_module_imports':0,'canonical_copies':copies})
save('reads.json',list(reads.values()))
print(json.dumps({'checks':len(checks),'failed':sum(not x['pass'] for x in checks),'reads':len(reads),'namespace':str(O)},ensure_ascii=True))
