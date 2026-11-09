import hashlib, importlib.util, json, os, pathlib, shutil, subprocess, sys
R=pathlib.Path(__file__).resolve().parent
W=pathlib.Path(r'D:\作品集\ResearchOS\research-os\.local\worktrees\installer-p1a-20261028')
A=W/'.local/installer-p1a/candidate03'
S=R/'scratch'
locked=json.loads((W/'execution/toolchains/locked.json').read_bytes())['tools']
def sha(p):
 with pathlib.Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(n,v):(R/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
env=os.environ.copy();env.update({'GOENV':'off','GOTOOLCHAIN':'local','GOROOT':str(pathlib.Path(locked['go']['path']).parent.parent),'GO111MODULE':'on','GOPATH':str(S),'GOCACHE':str(S/'gocache'),'GOMODCACHE':str(S/'gomodcache'),'GOTMPDIR':str(S/'gotmp'),'GOPROXY':'off','GOSUMDB':'off','TEMP':str(S/'temp'),'TMP':str(S/'temp'),'LOCALAPPDATA':str(S/'localappdata'),'PYTHONDONTWRITEBYTECODE':'1'})
def run(label,argv,cwd=R):
 p=subprocess.run([str(a) for a in argv],env=env,cwd=cwd,capture_output=True)
 (R/(label+'.stdout.raw')).write_bytes(p.stdout);(R/(label+'.stderr.raw')).write_bytes(p.stderr)
 save(label+'.command.json',{'argv':[str(a) for a in argv],'cwd':str(cwd),'exit':p.returncode})
 return p
manifest=A/'payload-manifest.json';m=json.loads(manifest.read_bytes())
assert run('rebuild-bound-module',[locked['go']['path'],'build','-mod=readonly','-trimpath','-buildvcs=false','-ldflags=-X main.trustedManifestSHA256='+sha(manifest),'-o',S/'independent-finalizer-module.exe',W/'ops/release/product_installer/finalize/main.go'],W).returncode==0
save('rebuild-bound-module-result.json',{'author_sha256':sha(A/'finalizer.exe'),'independent_sha256':sha(S/'independent-finalizer-module.exe'),'exact_bytes_equal':sha(A/'finalizer.exe')==sha(S/'independent-finalizer-module.exe'),'prior_difference':'First rebuild explicitly used GO111MODULE=off; this rebuild matches author module mode and -mod=readonly.'})
assert sha(A/'finalizer.exe')==sha(S/'independent-finalizer-module.exe')
results=[]
for suffix in ('A','B'):
 root=S/('独立 中文 空格 '+suffix)
 shutil.copytree(A/'payload',root)
 p=run('relocation-'+suffix,[A/'finalizer.exe','--root',root,'--manifest',manifest]);assert p.returncode==0
 marker=json.loads((root/'installed-product.json').read_bytes())
 for f in marker['files']:
  file=root/f['path'];assert sha(file)==f['sha256'] and file.stat().st_size==f['bytes']
 assert len(marker['files'])==133 and [f for f in marker['files'] if f['path']!='apps/desktop/resources/control/runtime-verifier-installation.json']==m['files']
 assert len([f for f in root.rglob('*') if f.is_file()])==134
 assert not (root/'.installed-product.json.tmp').exists()
 verifier=root/'apps/desktop/resources/control/runtime-verifier-installation.json';v=json.loads(verifier.read_bytes())
 assert v['executable']==str(root/m['binaries']['verifier']['path']) and v['executable_hash']=='sha256:'+sha(v['executable'])
 # Preserve exact location-bound evidence before cleaning disposable copied payloads.
 shutil.copyfile(root/'installed-product.json',R/('relocation-'+suffix+'-marker.json'))
 shutil.copyfile(verifier,R/('relocation-'+suffix+'-verifier.json'))
 results.append({'root':str(root),'installation_id':marker['installation_id'],'payload_digest':sha(manifest),'inventory_digest':marker['inventory_digest'],'marker_sha256':sha(root/'installed-product.json'),'verifier_sha256':sha(verifier),'inventory_count':len(marker['files']),'native_product_executions':0})
assert results[0]['installation_id']!=results[1]['installation_id']
assert run('relocated-node-consumer',[locked['node']['path'],R/'consumer_probe.cjs',*[x['root'] for x in results]]).returncode==0
save('independent-relocation.json',{'status':'PASS_STATIC_FINALIZER_ONLY','roots':results,'formal_increment':0})
# Evaluate the builder output containment condition without allowing a build/write.
output=(W/'.local/../../escape-review').absolute();local=W/'.local'
save('builder-containment-observation.json',{'input':str(output),'lexical_is_relative_to_local':output.is_relative_to(local),'resolved':str(output.resolve()),'resolved_is_relative_to_local':output.resolve().is_relative_to(local.resolve()),'actual_build_invoked':False,'observation':'output lexical check accepts dotdot; caller used canonical authorized paths in reviewed run'})
print('module rebuild exact; two real payload relocation probes passed')
