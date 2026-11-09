import pathlib,hashlib,json,subprocess,datetime,collections
O=pathlib.Path(__file__).resolve().parent;F=pathlib.Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/approved_readlane_combined_desktop_build_codex/20261012-current-chat');M=pathlib.Path('D:/作品集/ResearchOS/research-os')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def put(n,v):
 with (O/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def record(n,args,cwd):
 p=subprocess.run(args,cwd=cwd,capture_output=True);(O/(n+'.stdout.raw')).write_bytes(p.stdout);(O/(n+'.stderr.raw')).write_bytes(p.stderr);put(n+'.invocation.json',{'argv':args,'cwd':str(cwd),'exit':p.returncode});assert p.returncode==0,(n,p.stderr);return p.stdout
mf=F/'manifest.json';assert sha(mf)=='3c71b1c94b830166ddd57506d01da0b5453fe3df79acf7b25c2756110bce9574';m=read(mf);S=pathlib.Path(m['source_root']);P=pathlib.Path(m['package']['root']);refs={}
def visit(v):
 if isinstance(v,dict):
  if isinstance(v.get('path'),str) and isinstance(v.get('sha256'),str):
   p=pathlib.Path(v['path']);assert p.is_file() and sha(p)==v['sha256'],v
   if 'bytes' in v:assert p.stat().st_size==v['bytes'],v
   refs[str(p)]={'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
  for x in v.values():visit(x)
 elif isinstance(v,list):
  for x in v:visit(x)
visit(m);refs[str(mf)]={'path':str(mf),'sha256':sha(mf),'bytes':mf.stat().st_size}
assert record('source-status',['git','status','--porcelain'],S)==b''
source=record('source-identity',['git','rev-parse','HEAD','HEAD^{tree}'],S).decode().splitlines();assert source==[m['ui_source_commit'],m['ui_source_tree']]
main=record('main-identity',['git','rev-parse','HEAD','HEAD^{tree}'],M).decode().splitlines();assert main==[m['integrated_main_commit'],m['integrated_main_tree']]
base='c381cf0d8e8f3ae2bcd437a6e0866b38d7bd9ec0'
names=record('main-changed',['git','diff','--name-only',base,m['integrated_main_commit']],M).decode().splitlines();assert names==['apps/desktop/main/lib/ipc.js','apps/desktop/main/main.js','tests/ui/desktop/http-wire-boundary.test.mjs']
for n in names:
 raw=record('blob-'+pathlib.Path(n).name.replace('.','-'),['git','show',m['ui_source_commit']+':'+n],S);assert raw==(S/n).read_bytes();reviewed=pathlib.Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/qualification-read-lane-v2-review-20261012/source')/n;assert sha(reviewed)==sha(S/n)
core=S.parent/'workspace-projection-20261012';coreid=record('core-source-identity',['git','rev-parse',m['component_vector']['core_control_and_verifier_reused']+'^{tree}'],core).decode().strip();assert coreid==m['reviewed_core_source_tree']
composition=read(pathlib.Path(m['package']['composition']['path']));listed={r['path'] for r in composition['package_files']};actual={p.relative_to(P).as_posix() for p in P.rglob('*') if p.is_file()};assert listed==actual,(listed-actual,actual-listed);assert len(actual)==58
for r in composition['package_files']:
 p=P/r['path'];assert sha(p)==r['sha256'] and p.stat().st_size==r['bytes'],r
 if r['component']!='NEW_INSTALLATION_MANIFEST':assert sha(pathlib.Path(r['source']))==r['sha256'],r
assert sum(r['bytes'] for r in composition['package_files'])==175776752
app=P/'apps/desktop';descriptor=read(app/'resources/client-wire/descriptor.json');assert sha(app/'resources/client-wire/descriptor.json')==m['build']['new_descriptor']['sha256']
for r in composition['module_inventory']:assert sha(app/r['path'])==r['sha256']==next(x['sha256'] for x in descriptor['exact_module_source_inventory'] if x['path']==r['path'])
for r in composition['public_host_assets']:assert sha(P/r['path'])==sha(M/r['path'])==sha(S/r['path'])==r['sha256']
for r in composition['React_asset_inventory']:
 assert any(x['sha256']==r['sha256'] and x['bytes']==r['bytes'] and x['component']=='REACT_070E_FRESH_BOUND' for x in composition['package_files'])
assert len(composition['module_inventory'])==14 and len(composition['public_host_assets'])==32 and len(composition['React_asset_inventory'])==3
inputs=read(pathlib.Path(m['build']['full_input_manifest']['path']));assert len(inputs)==6444
digest=hashlib.sha256(json.dumps(inputs,sort_keys=True,separators=(',',':')).encode()).hexdigest();assert digest==m['build']['full_input_digest']==descriptor['build_input_digest']
for r in inputs:assert sha(pathlib.Path(r['path']))==r['sha256'],r['path']
archive=read(pathlib.Path(m['build']['compiler_archive_manifest']['path']));archrefs={}
for group,items in archive.items():
 for r in items:
  p=pathlib.Path(r['path']);assert p.is_file() and sha(p)==r['sha256'] and p.stat().st_size==r['bytes'],r;archrefs[str(p)]=r
for key in ['compile_invocation_ref','full_input_manifest_ref','compiler_generated_importcfg_archives_ref']:visit(descriptor[key])
for entry in m['build']['tools']:assert sha(pathlib.Path(entry['path']))==entry['sha256']
go=next(r['path'] for r in m['build']['tools'] if r['name']=='go');metadata={}
for name,rel,commit in [('validator','apps/desktop/resources/client-wire/researchos-client-wire-validator.exe',m['ui_source_commit']),('control','apps/desktop/resources/control/researchos-control.exe',m['component_vector']['core_control_and_verifier_reused']),('verifier','apps/desktop/resources/control/runtime-verifier.exe',m['component_vector']['core_control_and_verifier_reused'])]:
 text=record(name+'-metadata',[go,'version','-m',str(P/rel)],O).decode();assert 'vcs.revision='+commit in text and 'vcs.modified=false' in text
 if name=='validator':assert 'main.buildInputDigest='+digest in text
 metadata[name]={'source_commit':commit,'vcs_modified':False,'exe_sha256':sha(P/rel),'metadata_sha256':sha(O/(name+'-metadata.stdout.raw'))}
installer=read(pathlib.Path(m['package']['installation_manifest']['path']));assert pathlib.Path(installer['executable']).is_absolute() and pathlib.Path(installer['executable'])==app/'resources/control/runtime-verifier.exe';assert installer['executable_hash']=='sha256:'+metadata['verifier']['exe_sha256'] and installer['arguments']==[] and installer['source_commit']==m['component_vector']['core_control_and_verifier_reused']
mu=read(app/'resources/control/runtime/mu-worker.mjs.build.json');put('mu-build-original.json',mu)
old=read(pathlib.Path(m['old_core_provenance']['frozen_manifest']['path']));correction=read(pathlib.Path(m['old_core_provenance']['correction']['path']));supp=read(pathlib.Path(m['old_core_provenance']['supplement']['path']));assert correction['frozen_originals'][0]['corrected_value']==m['reviewed_core_source_tree'];assert correction['frozen_originals'][0]['original_value']!=m['reviewed_core_source_tree']
protected_path=M/'execution/v2.4/receipts/W05/W05-99/current_chat_integration_preflight_codex/20261012-current-chat/preflight-v2.json';protected=read(protected_path)['protected_source'];put('protected-source-baseline.json',{'path':str(protected_path),'sha256':sha(protected_path),'protected_source':protected})
put('binding-before.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'refs':list(refs.values()),'source_identity':source,'main_identity':main,'main_changed_paths':names,'reviewed_v2_source_bytes_match':True,'package_members':len(actual),'package_bytes':sum(r['bytes'] for r in composition['package_files']),'component_counts':dict(collections.Counter(r['component'] for r in composition['package_files'])),'full_input_count':len(inputs),'full_input_digest':digest,'compiler_archive_members':len(archrefs),'compiler_archive_group_counts':{k:len(v) for k,v in archive.items()},'metadata':metadata,'installer':installer,'D_writes':0,'product_launches':0})
print(json.dumps({'refs':len(refs),'package_members':len(actual),'inputs':len(inputs),'archives':len(archrefs),'source_main_tree_equal':source[1]==main[1],'metadata':metadata,'protected_source':protected},ensure_ascii=False))
