import hashlib,json,os,subprocess,datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
R=Path(r'D:\作品集\ResearchOS\research-os');W=R/'.local/worktrees/desktop-installed-delivery-20261025'
B=W/'.local/product-layout-cp558-20261028-02'
A=R/'execution/v2.4/receipts/W05/W05-99/installed_delivery_codex/20261025-current-chat/continuation-20261028/build-02'
O=R/'execution/v2.4/receipts/W05/W05-99/product_host_independent_20261028/frozen-5ee2c694-review'
ROOTCHECK=R/'execution/v2.4/receipts/W05/W05-99/resume_cp528_codex/20261025-current-chat/continuation-cp561/product-host-final-build-root-verification.json'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def digest(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def js(p):return json.loads(Path(p).read_bytes())
def put(n,o):(O/n).write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
refs=[]
def read(p):
 raw=Path(p).read_bytes();refs.append({'path':str(p),'sha256':sha(raw),'bytes':len(raw)});return json.loads(raw)
root_raw=ROOTCHECK.read_bytes();assert sha(root_raw)=='49472a21d3c516d5ea2fa2640dd39c6bdad72f188181d64364824ccc8ae8cc4b'
root_report=read(ROOTCHECK)
marker=read(B/'installed-product.json');result=read(A/'result.json')
assert digest(B/'installed-product.json')=='7c04fc8d33b30382027fded7120265cf6cef61bd9785fe0c3cf02e15acf29144'
assert marker['source_commit']=='5ee2c694ee275a72f40e8aa1d6c377d719fb8631'
assert marker['installation_id']=='318a306090d0fd24573e38b23bdea775435dc26696f43766cf7dd2225b1d2bb2'
assert marker['mode']=='OWNED_PRODUCT_LAYOUT_NOT_INSTALLER' and len(marker['files'])==133
assert not result['source_drift'] and not result['input_drift']
closures={};file_refs={};conflicts=[]
for name in ('source','go-compiled-inputs','mu-compiled-inputs','mu-vendor-5083','public-mu'):
 before=read(A/(name+'.before.json'));after=read(A/(name+'.after.json'));assert before==after,name
 if name=='source':
  assert before['head']==marker['source_commit'] and not before['candidate_delta']
  assert before['tree']=='43e71226bbcb5d413bfa0ca2b11a767d255b2aec'
  rows=[dict(row,path=str(W/row['path'])) for row in before['files']]
 elif name=='public-mu':rows=[dict(row,path=str(R/rel)) for rel,row in before.items()]
 elif isinstance(before,list):rows=before
 else:rows=before['files']
 closures[name]={'rows':len(rows),'before_after_equal':True}
 for row in rows:
  k=str(Path(row['path'])).lower()
  if k in file_refs and (file_refs[k]['sha256'],file_refs[k]['bytes'])!=(row['sha256'],row['bytes']):conflicts.append(k)
  file_refs[k]=row
assert not conflicts,conflicts
client=read(A/'client-wire-builder/result.json');assert client['status']=='BUILT_NOT_TESTED' and not client['drift']
cb=read(A/'client-wire-builder/inputs.before.json');ca=read(A/'client-wire-builder/inputs.after.json')
assert len(cb)==len(ca)
for b,a in zip(cb,ca):
 assert b['path']==a['path'] and b['sha256']==a['sha256']==a['current_sha256'] and b['bytes']==a['bytes']
 k=str(Path(b['path'])).lower()
 if k in file_refs:assert (file_refs[k]['sha256'],file_refs[k]['bytes'])==(b['sha256'],b['bytes'])
 file_refs[k]=b
closures['client-wire-inputs']={'rows':len(cb),'before_after_equal':True}
def check(row):
 p=Path(row['path']);raw=p.read_bytes();actual=sha(raw)
 return {'path':str(p),'bytes':len(raw),'sha256':actual,'match':len(raw)==row['bytes'] and actual==row['sha256']}
with ThreadPoolExecutor(max_workers=4) as pool:checked=list(pool.map(check,file_refs.values()))
put('DEPENDENCY-RECHECK.json',checked)
assert all(r['match'] for r in checked),'dependency drift'
for key,n in [('go_compiled_input_sha256','go-compiled-inputs.before.json'),('mu_compiled_input_sha256','mu-compiled-inputs.before.json'),('mu_vendor_5083_sha256','mu-vendor-5083.before.json')]:assert marker[key]==digest(A/n),key
assert marker['client_wire_input_digest']==client['build_input_digest']
descriptor=read(B/'apps/desktop/resources/client-wire/descriptor.json')
assert descriptor['build_input_digest']==client['build_input_digest']
assert descriptor['binary_sha256']==marker['binaries']['validator']['sha256']==client['binary_sha256']
module_names=[]
for row in descriptor['exact_module_source_inventory']:
 p=B/'apps/desktop'/row['path'];assert digest(p)==row['sha256'];module_names.append(row['path'])
assert 'main/lib/product-layout.js' in module_names and 'main/main.js' in module_names
verifier=read(B/'apps/desktop/resources/control/runtime-verifier-installation.json')
assert verifier['executable']==str(B/marker['binaries']['verifier']['path']) and verifier['arguments']==[]
assert verifier['executable_hash']=='sha256:'+marker['binaries']['verifier']['sha256'] and verifier['source_commit']==marker['source_commit']
node=B/'apps/desktop/resources/control/runtime/node.exe';cli=B/'bin/researchos.exe';lock=read(W/'execution/toolchains/locked.json')
assert digest(node)==lock['tools']['node']['sha256']==marker['tool_hashes']['node']
assert digest(cli)==marker['binaries']['cli']['sha256']
C=O/'consumers';C.mkdir(exist_ok=False);local=C/'local';local.mkdir();tmp=C/'temp';tmp.mkdir();home=C/'home';home.mkdir()
env={k:v for k,v in os.environ.items() if not k.upper().startswith(('RESEARCHOS_','ROS_DESKTOP_','NODE_','ELECTRON_')) and k.upper() not in ('HTTP_PROXY','HTTPS_PROXY','ALL_PROXY')}
env.update(LOCALAPPDATA=str(local),APPDATA=str(local),USERPROFILE=str(home),HOME=str(home),TEMP=str(tmp),TMP=str(tmp))
node_script="const path=require('node:path');const p=require(path.join(process.argv[1],'apps/desktop/main/lib/product-layout.js'));const l=p.loadProductLayout(process.argv[1]);console.log(JSON.stringify({installation_id:l.installID,inventory_digest:l.inventoryDigest,files:l.marker.files.length}));"
runs=[]
for name,argv in [('js-loader',[str(node),'-e',node_script,str(B)]),('cli-version',[str(cli),'version']),('cli-help',[str(cli),'help']),('cli-commands',[str(cli),'commands'])]:
 before=datetime.datetime.now(datetime.timezone.utc).isoformat();p=subprocess.run(argv,cwd=C,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30)
 (C/(name+'.stdout.raw')).write_bytes(p.stdout);(C/(name+'.stderr.raw')).write_bytes(p.stderr)
 run={'name':name,'argv':argv,'cwd':str(C),'started_at':before,'ended_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit':p.returncode,'stdout_sha256':sha(p.stdout),'stderr_sha256':sha(p.stderr),'environment_isolation':{k:env[k] for k in ('LOCALAPPDATA','APPDATA','USERPROFILE','HOME','TEMP','TMP')}};runs.append(run)
 put('CONSUMER-RUNS.json',runs)
 assert p.returncode==0,name
 if name=='js-loader':assert json.loads(p.stdout)['installation_id']==marker['installation_id']
 if name=='cli-version':assert json.loads(p.stdout)['command']=='version' and json.loads(p.stdout)['status']=='COMPLETED'
 assert not list(local.iterdir()) and not list(home.iterdir()) and not list(tmp.iterdir()),'nonhost wrote profile/temp/data'
for d in (local,tmp,home):assert d.resolve().is_relative_to(O.resolve());d.rmdir()
for ref in refs:assert digest(ref['path'])==ref['sha256'],'input changed during review'
put('BUILD-INPUT-REFS.json',refs)
summary={'status':'BUILD_CLOSURES_AND_READONLY_CONSUMERS_PASS_PENDING_EXACT7_AND_FINAL_MANIFEST','source_commit':marker['source_commit'],'installation_id':marker['installation_id'],'manifest_sha256':digest(B/'installed-product.json'),'root_inventory_check_ref':str(ROOTCHECK),'root_inventory_check_sha256':sha(root_raw),'closures':closures,'unique_dependency_files_checked':len(checked),'dependency_mismatches':0,'descriptor_modules':len(module_names),'consumers':[{k:r[k] for k in ('name','exit')} for r in runs],'profile_data_writes':0,'nonhost_cli_process_runs':3,'node_helper_runs':1,'product_core_electron_runs':0,'formal_increment':0,'source_acceptance':False}
put('BUILD-REVIEW.json',summary);print(json.dumps(summary))