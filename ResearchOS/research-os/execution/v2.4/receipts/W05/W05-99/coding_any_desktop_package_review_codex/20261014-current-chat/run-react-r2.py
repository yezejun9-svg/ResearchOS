import pathlib,json,subprocess,hashlib,os,time
E=pathlib.Path(__file__).parent;W=E/'react-source/apps/web';N='C:/Users/yqyyds/AppData/Local/nvm/v24.9.0/node.exe';V='D:/作品集/ResearchOS/research-os/apps/web/node_modules/vite/bin/vite.js'
argv=[N,V,'build','--outDir',str(E/'react-dist')];start=time.time();p=subprocess.run(argv,cwd=W,capture_output=True,timeout=60)
(E/'react-build-r2.stdout.raw').write_bytes(p.stdout);(E/'react-build-r2.stderr.raw').write_bytes(p.stderr)
r={'argv':argv,'cwd':str(W),'native_exit':p.returncode,'seconds':time.time()-start,'node_sha256':hashlib.sha256(pathlib.Path(N).read_bytes()).hexdigest(),'vite_sha256':hashlib.sha256(pathlib.Path(V).read_bytes()).hexdigest()}
(E/'react-build-r2.process.json').write_text(json.dumps(r,ensure_ascii=True,indent=2),encoding='utf8')
assert p.returncode==0
P=pathlib.Path('C:/Users/yqyyds/.codex/researchos-resource-cache/normal-coding-any-a7ec7ebf-20261014/apps/web/dist');records=[]
for f in (E/'react-dist').rglob('*'):
 if f.is_file():
  rel=f.relative_to(E/'react-dist');assert f.read_bytes()==(P/rel).read_bytes();records.append({'path':rel.as_posix(),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size})
assert len(records)==3
junction=W/'node_modules';assert junction.is_junction() and junction.parent.resolve()==W.resolve();os.rmdir(junction)
(E/'react-build-comparison.json').write_text(json.dumps({'independent_build_equal_package':True,'assets':records,'junction_removed_without_traversal':True},indent=2),encoding='utf8')
print(json.dumps({'native_exit':0,'assets':len(records),'byte_identical':True}))
