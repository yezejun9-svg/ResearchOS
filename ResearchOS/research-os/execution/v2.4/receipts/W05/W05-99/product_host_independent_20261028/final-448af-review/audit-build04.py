import pathlib,json,hashlib,subprocess,stat
P=pathlib.Path;R=P('D:/作品集/ResearchOS/research-os');W=R/'.local/worktrees/desktop-installed-delivery-20261025'
AUTH=R/'execution/v2.4/receipts/W05/W05-99/installed_delivery_codex/20261025-current-chat/continuation-20261028'
A=AUTH/'marker-fixture-cp563/build-04';B=W/'.local/product-layout-cp558-20261028-04';E=P(__file__).resolve().parent
HEAD='448af57c208a3f29199d10e0fa9d9c7311776fad';TREE='c4c9a19b5dce33a390620cb460e5b1c88d28cfc2';BASE='9361c1b63fa658251f730771bc12633ff5f12c08'
def sha(p):
 h=hashlib.sha256()
 with P(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def hashbytes(b):return hashlib.sha256(b).hexdigest()
def js(p):return json.loads(P(p).read_bytes())
def put(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def req(v,m):
 if not v:raise RuntimeError(m)
refs=[]
def read(p):
 p=P(p);refs.append({'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size});return js(p)
def git(*a):return subprocess.check_output(['git','-C',str(W),*a]).decode('utf8').strip()
req(git('rev-parse','HEAD')==HEAD and git('rev-parse','HEAD^{tree}')==TREE and git('rev-parse','HEAD^')==BASE and not git('status','--porcelain'),'git freeze')
changed=git('diff','--name-only',BASE,HEAD).splitlines();req(changed==['tests/ui/desktop/product-host.test.mjs'],'exact1')
(E/'exact1.diff').write_text(git('diff',BASE,HEAD)+'\n',encoding='utf8')
marker=read(B/'installed-product.json');result=read(A/'result.json');req(marker['source_commit']==HEAD and not result['source_drift'] and not result['input_drift'],'build provenance')
req(marker['mode']=='OWNED_PRODUCT_LAYOUT_NOT_INSTALLER' and marker['schema']=='researchos.product-layout/1','marker schema')
rows=marker['files'];req(len(rows)==133,'133 inventory')
names=[x['path'] for x in rows];req(names==sorted(names) and len(set(x.lower() for x in names))==133,'inventory aliases')
actual={x.relative_to(B).as_posix() for x in B.rglob('*') if x.is_file()}-{'installed-product.json'};req(actual==set(names),'exact actual files')
for row in rows:
 rel=P(row['path']);req(not rel.is_absolute() and '..' not in rel.parts and '\\' not in row['path'],'relative')
 p=B/rel;req(p.stat().st_size==row['bytes'] and sha(p)==row['sha256'],row['path'])
 for x in [p,*p.parents]:
  if x==B.parent:break
  req(not getattr(x.lstat(),'st_file_attributes',0)&stat.FILE_ATTRIBUTE_REPARSE_POINT,'reparse')
inventory_id=hashbytes(('researchos.product-inventory/1\n'+''.join(f"{r['path']}\n{r['sha256']}\n{r['bytes']}\n" for r in rows)).encode())
req(inventory_id==marker['inventory_digest'],'inventory digest')
parts=[marker['schema'],marker['install_root'],HEAD,marker['source_digest'],inventory_id,marker['product_version'],marker['client_protocol'],str(marker['schema_version'])]+[marker['binaries'][k]['sha256'] for k in ['cli','control','electron','verifier','validator']]
req(hashbytes(('\n'.join(parts)+'\n').encode())==marker['installation_id'],'install id')
old={str(P(r['path'])).lower():r for r in read(E.parent/'build03-review/DEPENDENCY-RECHECK.json')};allrows={};closures={}
for n in ['source','go-compiled-inputs','mu-compiled-inputs','mu-vendor-5083','public-mu']:
 b=read(A/(n+'.before.json'));a=read(A/(n+'.after.json'));req(b==a,n+' drift')
 if n=='source':
  req(b['head']==HEAD and b['tree']==TREE and not b['candidate_delta'],'source freeze');rs=[dict(r,path=str(W/r['path'])) for r in b['files']]
 elif n=='public-mu':rs=[dict(r,path=str(R/k)) for k,r in b.items()]
 elif isinstance(b,list):rs=b
 else:rs=b['files']
 closures[n]=len(rs)
 for r in rs:allrows[str(P(r['path'])).lower()]=r
client=read(A/'client-wire-builder/result.json');cb=read(A/'client-wire-builder/inputs.before.json');ca=read(A/'client-wire-builder/inputs.after.json');req(not client['drift'] and len(cb)==len(ca),'client drift')
for b,a in zip(cb,ca):
 req(b['path']==a['path'] and b['sha256']==a['sha256']==a['current_sha256'] and b['bytes']==a['bytes'],'client before after');allrows[str(P(b['path'])).lower()]=b
closures['client-wire-inputs']=len(cb);checks=[]
for k,r in allrows.items():
 prior=old.get(k);same=prior and prior['match'] and prior['sha256']==r['sha256'] and prior['bytes']==r['bytes']
 if not same:req(sha(r['path'])==r['sha256'] and P(r['path']).stat().st_size==r['bytes'],'changed input')
 checks.append({'path':r['path'],'sha256':r['sha256'],'bytes':r['bytes'],'match':True,'verification':'SAME_BOUND_BEFORE_AFTER_RECORD_AS_BUILD03' if same else 'CURRENT_HASH'})
put('DEPENDENCY-DELTA.json',checks)
for key,n in [('go_compiled_input_sha256','go-compiled-inputs.before.json'),('mu_compiled_input_sha256','mu-compiled-inputs.before.json'),('mu_vendor_5083_sha256','mu-vendor-5083.before.json')]:req(marker[key]==sha(A/n),key)
descriptor=read(B/'apps/desktop/resources/client-wire/descriptor.json');req(descriptor['binary_sha256']==marker['binaries']['validator']['sha256']==client['binary_sha256'] and descriptor['build_input_digest']==marker['client_wire_input_digest']==client['build_input_digest'],'client bind')
for r in descriptor['exact_module_source_inventory']:req(sha(B/'apps/desktop'/r['path'])==r['sha256'],'client module')
verifier=read(B/'apps/desktop/resources/control/runtime-verifier-installation.json');req(verifier['executable']==str(B/marker['binaries']['verifier']['path']) and verifier['arguments']==[] and verifier['executable_hash']=='sha256:'+marker['binaries']['verifier']['sha256'] and verifier['source_commit']==HEAD,'verifier')
node_before=read(AUTH/'marker-fixture-cp563/source.before.json');node_after=read(AUTH/'marker-fixture-cp563/source.after.json');req(node_before['files']==node_after['files'] and node_before['node_sha256']==node_after['node_sha256'],'node test drift')
for r in node_before['files']:
 req(sha(W/r['path'])==r['sha256'] and hashbytes(subprocess.check_output(['git','-C',str(W),'show',HEAD+':'+r['path']]))==r['sha256'],'node test commit bytes')
req(read(AUTH/'marker-fixture-cp563/exit.json')['exit_code']==0,'node8')
for p in ['stdout.raw','stderr.raw','recipe.json']:readpath=AUTH/'marker-fixture-cp563'/p;refs.append({'path':str(readpath),'sha256':sha(readpath),'bytes':readpath.stat().st_size})
raw=(AUTH/'marker-fixture-cp563/stdout.raw').read_text(encoding='utf8');req('tests 8' in raw and 'pass 8' in raw and 'fail 0' in raw,'8/8 raw')
for ref in refs:req(sha(ref['path'])==ref['sha256'],'review input drift')
req(git('rev-parse','HEAD')==HEAD and not git('status','--porcelain'),'git drift')
put('INPUTS.json',refs)
summary={'status':'CURRENT_BUILD04_AND_TEST_ONLY_DELTA_VERIFIED','head':HEAD,'tree':TREE,'parent':BASE,'exact_delta':changed,'marker_sha256':sha(B/'installed-product.json'),'installation_id':marker['installation_id'],'inventory_files_rehashed':133,'electron_runtime_files':sum(x.startswith('runtime/electron/') for x in names),'closures':closures,'unique_dependency_records':len(checks),'changed_dependency_records_rehashed':sum(x['verification']=='CURRENT_HASH' for x in checks),'node8':'AUTHOR_PASS_REVIEWED_PRECOMMIT_BYTES_EQUAL_FINAL_COMMIT','behavior_reruns_by_reviewer':0,'build03_consumers_reused':'Product implementation unchanged; packaging bytes/identity freshly verified. Not claimed executed on build04.','formal_increment':0}
put('BUILD04-REVIEW.json',summary);print(json.dumps(summary))
