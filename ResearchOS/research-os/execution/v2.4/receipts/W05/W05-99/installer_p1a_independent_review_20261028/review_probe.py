import hashlib, importlib.util, json, os, pathlib, shutil, subprocess, sys
R = pathlib.Path(__file__).resolve().parent
W = pathlib.Path(r'D:\作品集\ResearchOS\research-os\.local\worktrees\installer-p1a-20261028')
REPO = pathlib.Path(r'D:\作品集\ResearchOS\research-os')
sys.dont_write_bytecode = True
def sha(p):
    with pathlib.Path(p).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def save(n,v): (R/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def run(label,argv,env=None,cwd=None):
    p=subprocess.run([str(x) for x in argv],cwd=cwd or R,env=env,capture_output=True)
    (R/(label+'.stdout.raw')).write_bytes(p.stdout); (R/(label+'.stderr.raw')).write_bytes(p.stderr)
    save(label+'.command.json',{'argv':[str(x) for x in argv],'cwd':str(cwd or R),'exit':p.returncode})
    return p
git=['git','-c','gc.auto=0','-c','maintenance.auto=false','-C',str(W)]
def g(*args):
    p=subprocess.run(git+list(args),capture_output=True); assert p.returncode==0,p.stderr; return p.stdout
author_path=REPO/'execution/v2.4/receipts/W05/W05-99/installer_p1a_source_codex/20261028/FINAL-MANIFEST.json'
author=json.loads(author_path.read_bytes())
scope_path=REPO/'execution/v2.4/receipts/W05/W05-99/resume_cp528_codex/20261025-current-chat/continuation-cp568/Installer-P1a-source-scope.json'
scope=json.loads(scope_path.read_bytes())
assert sha(author_path)=='9dbf53f83e2d5b6d3fba152450887541b256dcf523b35ca3ccca7d7b12b2bdf1'
assert sha(scope_path)=='64d7670422ded2533826feeba61bdf64a793e3e9bcb7dbd5a93a943b163233f7'
assert not g('status','--porcelain=v1').strip()
assert g('rev-parse','HEAD').decode().strip()==author['commit']
assert g('rev-parse','HEAD^{tree}').decode().strip()==author['tree']
diff=g('diff','--name-status',author['base_commit'],'HEAD').decode().splitlines()
assert sorted(diff)==sorted('A\t'+x for x in scope['allowed_source_paths'])
for f in author['source_files']:
    assert sha(W/f['path'])==f['sha256']
    assert hashlib.sha256(g('show','HEAD:'+f['path'])).hexdigest()==f['sha256']
save('source-binding.json',{'scope_sha256':sha(scope_path),'author_sha256':sha(author_path),'head':author['commit'],'tree':author['tree'],'diff':diff,'source_files':author['source_files'],'clean':True})
locked=json.loads((W/'execution/toolchains/locked.json').read_bytes())['tools']
for name in ('go','python','node'): assert sha(locked[name]['path'])==locked[name]['sha256']
save('toolchains.json',{k:locked[k] for k in ('go','python','node')})
spec=importlib.util.spec_from_file_location('candidate_builder',W/'ops/release/product_installer/build.py')
b=importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
manifest=pathlib.Path(author['payload_manifest']); raw=manifest.read_bytes(); p=json.loads(raw)
assert sha(manifest)==author['payload_manifest_sha256']
assert sha(author['finalizer'])==author['finalizer_sha256']
source=pathlib.Path(scope['input_bundle']); original=json.loads((source/'installed-product.json').read_bytes())
assert sha(source/'installed-product.json')==scope['input_marker_ref']['sha256']
assert b.encode(b.freeze(source))==raw
payload=manifest.parent/'payload'
def rows_verified(root,rows,extras):
    actual={f.relative_to(root).as_posix() for f in root.rglob('*') if f.is_file()}
    assert actual=={f['path'] for f in rows}|set(extras),(root,actual)
    for f in rows:
        q=root/f['path']; assert q.stat().st_size==f['bytes'] and sha(q)==f['sha256'],q
    return len(rows)
rows_verified(payload,p['files'],[])
assert p['files']==[r for r in original['files'] if r['path']!=b.VERIFIER_PATH]
assert p['metadata']=={k:v for k,v in original.items() if k not in ('files','binaries','install_root','installation_id','inventory_digest')}
assert p['binaries']==original['binaries'] and len(p['binaries'])==5
extras=b.source_extras(source,original['files']); assert extras==author['source_extras_excluded']
roots=[]
for item in author['final_roots']:
    root=pathlib.Path(item['root']); m=json.loads((root/'installed-product.json').read_bytes())
    rows_verified(root,m['files'],['installed-product.json'])
    assert [r for r in m['files'] if r['path']!=b.VERIFIER_PATH]==p['files']
    assert sha(root/'installed-product.json')==item['marker_sha256']
    inventory=hashlib.sha256(('researchos.product-inventory/1\n'+''.join(f"{r['path']}\n{r['sha256']}\n{r['bytes']}\n" for r in m['files'])).encode()).hexdigest()
    fields=[m['schema'],str(root),m['source_commit'],m['source_digest'],inventory,m['product_version'],m['client_protocol'],str(m['schema_version'])]+[m['binaries'][r]['sha256'] for r in b.ROLES]
    iid=hashlib.sha256(('\n'.join(fields)+'\n').encode()).hexdigest()
    assert inventory==m['inventory_digest'] and iid==m['installation_id']
    v=json.loads((root/b.VERIFIER_PATH).read_bytes()); assert v['executable']==str(root/p['binaries']['verifier']['path'])
    assert v['executable_hash']=='sha256:'+sha(v['executable'])
    roots.append({'root':str(root),'installation_id':iid,'inventory_digest':inventory,'count':len(m['files']),'marker_sha256':sha(root/'installed-product.json'),'verifier_sha256':sha(root/b.VERIFIER_PATH)})
assert roots[0]['installation_id']!=roots[1]['installation_id']
save('artifact-verification.json',{'payload_sha256':sha(manifest),'payload_count':len(p['files']),'original_inventory_count':len(original['files']),'source_extras':extras,'finalizer_sha256':sha(author['finalizer']),'roots':roots,'metadata_and_all_roles_preserved':True,'deterministic_freeze_bytes_equal':True})
scratch=R/'scratch'; scratch.mkdir(exist_ok=True)
for d in ('gocache','gotmp','gomodcache','temp','localappdata'): (scratch/d).mkdir(exist_ok=True)
env=os.environ.copy(); env.update({'GOENV':'off','GOTOOLCHAIN':'local','GOROOT':str(pathlib.Path(locked['go']['path']).parent.parent),'GO111MODULE':'off','GOPATH':str(scratch),'GOCACHE':str(scratch/'gocache'),'GOMODCACHE':str(scratch/'gomodcache'),'GOTMPDIR':str(scratch/'gotmp'),'GOPROXY':'off','GOSUMDB':'off','TEMP':str(scratch/'temp'),'TMP':str(scratch/'temp'),'LOCALAPPDATA':str(scratch/'localappdata'),'PYTHONDONTWRITEBYTECODE':'1'})
for f in ('main.go','main_test.go'): shutil.copyfile(W/'ops/release/product_installer/finalize'/f,R/f)
js=g('show','HEAD:apps/desktop/main/lib/product-layout.js'); (R/'product-layout.js').write_bytes(js)
go_source=g('show','HEAD:apps/cli/product_host_windows.go'); (R/'product_host_windows.go.source').write_bytes(go_source)
save('consumer-source.json',{'javascript_sha256':hashlib.sha256(js).hexdigest(),'go_sha256':hashlib.sha256(go_source).hexdigest(),'origin_commit':author['commit'],'go_runtime_loader_execution':'NOT_RUN; source contract compared only'})
assert run('python-author-tests',[locked['python']['path'],W/'tests/release/product_installer_build_test.py'],env).returncode==0
assert run('go-tests',[locked['go']['path'],'test','-count=1','-v',R/'main.go',R/'main_test.go',R/'independent_test.go'],env).returncode==0
assert run('node-consumer',[locked['node']['path'],R/'consumer_probe.cjs',*[r['root'] for r in roots]],env).returncode==0
assert run('rebuild-bound',[locked['go']['path'],'build','-trimpath','-buildvcs=false','-ldflags=-X main.trustedManifestSHA256='+sha(manifest),'-o',scratch/'independent-finalizer.exe',W/'ops/release/product_installer/finalize/main.go'],env,cwd=W).returncode==0
save('rebuild-bound-result.json',{'author_finalizer_sha256':sha(author['finalizer']),'independent_finalizer_sha256':sha(scratch/'independent-finalizer.exe'),'exact_bytes_equal':sha(author['finalizer'])==sha(scratch/'independent-finalizer.exe')})
# Executable receives a changed manifest and must reject before touching root.
changed=R/'changed-manifest.json'; changed.write_bytes(raw+b' ')
rejectroot=scratch/'digest-reject-root'; rejectroot.mkdir(exist_ok=False)
x=run('bound-digest-negative',[author['finalizer'],'--root',rejectroot,'--manifest',changed],env)
assert x.returncode!=0 and not list(rejectroot.iterdir())
print('independent probes complete')
