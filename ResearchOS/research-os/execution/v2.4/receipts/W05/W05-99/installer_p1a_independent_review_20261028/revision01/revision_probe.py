import hashlib, importlib.util, json, os, pathlib, shutil, subprocess, sys
R=pathlib.Path(__file__).resolve().parent; W=pathlib.Path(r'D:\作品集\ResearchOS\research-os\.local\worktrees\installer-p1a-20261028'); REPO=pathlib.Path(r'D:\作品集\ResearchOS\research-os')
sys.dont_write_bytecode=True
def sha(p):
 with pathlib.Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(name,v):(R/name).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
scope=REPO/'execution/v2.4/receipts/W05/W05-99/resume_cp528_codex/20261025-current-chat/continuation-cp570/Installer-P1a-exact4-revision-scope.json'
author=REPO/'execution/v2.4/receipts/W05/W05-99/installer_p1a_source_codex/20261028/revision01/FINAL-MANIFEST.json'
assert sha(scope)=='27a928d09ede129bab29090d4db9c7705354fd02cb2788fad0db80922ec3b3bf'
assert sha(author)=='40fa563318ff28d1998df1886f419864d212d39196dfc09842bed677ad328499'
a=json.loads(author.read_bytes());s=json.loads(scope.read_bytes())
git=['git','-c','gc.auto=0','-c','maintenance.auto=false','-C',str(W)]
def g(*args):
 p=subprocess.run(git+list(args),capture_output=True); assert p.returncode==0,p.stderr; return p.stdout
assert g('rev-parse','HEAD').decode().strip()==a['commit'];assert g('rev-parse','HEAD^{tree}').decode().strip()==a['tree'];assert not g('status','--porcelain=v1').strip()
diff=g('diff','--name-status',a['base_commit'],a['commit']).decode().splitlines();assert sorted(diff)==sorted('M\t'+p for p in s['allowed_source_paths'])
for f in a['source_files']:
 assert sha(W/f['path'])==f['sha256']; assert hashlib.sha256(g('show','HEAD:'+f['path'])).hexdigest()==f['sha256']
save('binding.json',{'scope_sha256':sha(scope),'author_sha256':sha(author),'head':a['commit'],'tree':a['tree'],'clean':True,'diff':diff,'source_files':a['source_files']})
(R/'source.diff').write_bytes(g('diff',a['base_commit'],a['commit'],'--',*s['allowed_source_paths']))
locked=json.loads((W/'execution/toolchains/locked.json').read_bytes())['tools'];save('toolchains.json',{k:locked[k] for k in ('go','python')})
for k in ('go','python'):assert sha(locked[k]['path'])==locked[k]['sha256']
scratch=R/'scratch';scratch.mkdir()
for d in ('gocache','gotmp','gomodcache','temp'): (scratch/d).mkdir()
env=os.environ.copy();env.update({'GOENV':'off','GOTOOLCHAIN':'local','GOROOT':str(pathlib.Path(locked['go']['path']).parent.parent),'GO111MODULE':'off','GOPATH':str(scratch),'GOCACHE':str(scratch/'gocache'),'GOMODCACHE':str(scratch/'gomodcache'),'GOTMPDIR':str(scratch/'gotmp'),'GOPROXY':'off','GOSUMDB':'off','TEMP':str(scratch/'temp'),'TMP':str(scratch/'temp'),'PYTHONDONTWRITEBYTECODE':'1'})
def run(label,argv):
 p=subprocess.run([str(x) for x in argv],cwd=R,env=env,capture_output=True)
 (R/(label+'.stdout.raw')).write_bytes(p.stdout);(R/(label+'.stderr.raw')).write_bytes(p.stderr)
 save(label+'.command.json',{'argv':[str(x) for x in argv],'cwd':str(R),'exit':p.returncode});return p
for f in ('main.go','main_test.go'):shutil.copyfile(W/'ops/release/product_installer/finalize'/f,R/f)
shutil.copyfile(W/'ops/release/product_installer/build.py',R/'candidate-build.py')
py=run('python-author',[locked['python']['path'],'-B',W/'tests/release/product_installer_build_test.py'])
go=run('go-publication',[locked['go']['path'],'test','-count=1','-v','-run','TestPublishMarkerNoReplace|TestIndependent',R/'main.go',R/'main_test.go',R/'independent_test.go'])
spec=importlib.util.spec_from_file_location('candidate_builder',W/'ops/release/product_installer/build.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
observations={'author_python_exit':py.returncode,'targeted_go_exit':go.returncode}
assert b.bound_roots(str(scope))==(s['artifact_root'],s['receipt_root'])
same=R/'identical-scope-new-path.json';same.write_bytes(scope.read_bytes())
new=R/'explicit-new-scope.json';ns={**s,'artifact_root':str(scratch/'future-artifacts'),'receipt_root':str(scratch/'future-receipts')};new.write_bytes(b.encode(ns))
for path in (same,new):
 try: result=b.bound_roots(str(path));observations[path.name]={'accepted':True,'value':result}
 except Exception as e:observations[path.name]={'accepted':False,'sha256':sha(path),'error':str(e)}
observations['scope_interface']='CLI only accepts --scope; trusted path/hash are source constants. authorized_roots is internal Python test injection, not explicit authenticated CLI scope input.'
# Additional failure ownership checks, using only this isolated root.
from types import SimpleNamespace
owned=scratch/'owned-receipts';owned.mkdir();st=owned.lstat();args=SimpleNamespace(_owned_receipts=(owned,st.st_dev,st.st_ino))
first=b.write_owned_failure(args,ValueError('first'));firstbytes=(owned/'failed.json').read_bytes();second=b.write_owned_failure(args,ValueError('second'))
assert first is True and second is False and (owned/'failed.json').read_bytes()==firstbytes
stale=scratch/'replacement';stale.mkdir();args2=SimpleNamespace(_owned_receipts=(stale,st.st_dev,st.st_ino));assert b.write_owned_failure(args2,ValueError('foreign')) is False and not list(stale.iterdir())
observations['failure_receipt_create_new_preserves_first']=True;observations['foreign_inode_refused']=True
# Original preexisting receipt failure through actual CLI is now nonmutating.
existing=scratch/'preexisting';existing.mkdir();(existing/'sentinel.txt').write_bytes(b'preserve')
before={p.name:sha(p) for p in existing.iterdir()}
reject=run('preexisting-cli',[locked['python']['path'],'-B',W/'ops/release/product_installer/build.py','--candidate',str(scratch),'--output',str(scratch/'unused'),'--receipts',str(existing),'--go',locked['go']['path'],'--scope',str(scope)])
after={p.name:sha(p) for p in existing.iterdir()};assert reject.returncode!=0 and before==after
observations['preexisting_cli_unchanged']={'before':before,'after':after,'exit':reject.returncode,'note':'Outside bound roots refused before mkdir; author tests independently exercise admissible-root preexisting receipt.'}
artifact=pathlib.Path(a['artifact']);assert sha(artifact/'payload-manifest.json')==a['payload_manifest_sha256'];assert sha(artifact/'finalizer.exe')==a['finalizer_sha256']
observations['unchanged_payload_digest']=a['payload_manifest_sha256'];observations['new_finalizer_digest']=a['finalizer_sha256'];observations['full_relocation_repeated']=False
save('observations.json',observations)
print(json.dumps(observations,ensure_ascii=False,indent=2))
