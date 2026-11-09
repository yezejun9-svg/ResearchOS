"""Additional static guards before freeze; creates new final files, preserves draft bytes."""
import ast,hashlib,json,pathlib,difflib
P=pathlib.Path(__file__).resolve().parent
def read(n):return (P/n).read_text(encoding='utf-8')
def put(n,b):
 with (P/n).open('xb') as f:f.write(b.encode() if isinstance(b,str) else b)
def save(n,x):put(n,json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def ref(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
common=read('controller_common.v2.py')
common=common.replace(" if g['source_commit']!=CANDIDATE", " if g.get('repository')!=scope.get('repository') or g.get('repository')!='D:\\\\作品集\\\\ResearchOS\\\\research-os':raise Stop('Exact public repository required')\n if g['source_commit']!=CANDIDATE",1)
# Forbid any current mutable canonical file from entering a long-lived authority vector.
common=common.replace(" for pin in members:\n", " for pin in members:\n  if Path(pin['path']) in {Path(g['repository'])/'execution/v2.4'/n for n in ['checkpoint.json','path_ownership.json','step_state.json','commands.json']}:raise Stop('Only immutable canonical copies permitted, not live files')\n",1)
put('controller_common.v2.final.py',common);cp=ref(P/'controller_common.v2.final.py')
source={n:read(n+'.v2.py') for n in ['controller','launch','case_worker','seal_readonly']}
for n,text in list(source.items()):
 text=text.replace("/'controller_common.v2.py'","/'controller_common.v2.final.py'")
 oldhash=ref(P/'controller_common.v2.py')['sha256'];text=text.replace(oldhash,cp['sha256'])
 source[n]=text
seal=source['seal_readonly']
seal=seal.replace(" attempts=result['attempts']",''' git=g['tools']['git']['path'];go=g['tools']['go']['path'];tree=root/'source'
 expected_argv={
  'git-parent':[git,'rev-parse',CANDIDATE+'^'],
  'git-four-diff':[git,'diff-tree','--no-commit-id','--name-only','-r',CANDIDATE],
  'git-export':[git,'cat-file','--batch'],
  'go-version':[go,'version'],
  'go-env':[go,'env','-json','GOROOT','GOVERSION','GOENV','GOTOOLCHAIN','GOMOD','GOMODCACHE','GOCACHE','GOTMPDIR','CGO_ENABLED','GOWORK','GOOS','GOARCH','GOAMD64','GOEXPERIMENT','GODEBUG']}
 for label,pkg in [('domain','./internal/domain'),('adapter','./adapters/retrieval')]:
  expected_argv['list-'+label]=[go,'list','-deps','-test','-compiled','-json','-mod=readonly','-work','-x',pkg]
  expected_argv['compile-'+label]=[go,'test','-c','-p=1','-mod=readonly','-work','-x','-o',str(root/(label+'.test.exe')),pkg]
  expected_argv['buildinfo-'+label]=[go,'version','-m',str(root/(label+'.test.exe'))]
 if g['resources']['junction']:
  resource=root/'junction-resource';expected_argv['junction-resource']=[g['tools']['cmd']['path'],'/D','/V:OFF','/S','/C','mklink /J "'+str(resource/'A/outside')+'" "'+str(resource/'B')+'"']
 for row in eligible:
  package='adapter' if row['file'].startswith('adapters/') else 'domain'
  expected_argv['case-'+row['id']]=[str(root/(package+'.test.exe')),'-test.run',row['test_run'],'-test.v','-test.count=1','-test.failfast','-test.timeout=120s']
 attempts=result['attempts']''')
seal=seal.replace("  require_job(inv['owned_result'],True)","  if inv['actualargv']!=expected_argv[label]:raise Stop('Actual native argv differs from fixed stage plan')\n  require_job(inv['owned_result'],True)")
seal=seal.replace(" for label in ['domain','adapter']:\n  graph=",''' for ownedroot in [root/'source',root/'gotmpdir',root/'gocache',Path(g['goroot']),Path(g['module_cache'])]:
  if {str(p) for p in walk_files(ownedroot)}!={p for p in frozenpaths if Path(p).is_relative_to(ownedroot)}:raise Stop('Complete actual compiled/input directory membership differs')
 work=walk_files(root/'gotmpdir');actual_mains=[file_ref(p) for p in work if p.name=='_testmain.go'];actual_cfgs=[file_ref(p) for p in work if p.name.startswith('importcfg')];actual_archives={}
 for pin in actual_cfgs:
  for line in Path(pin['path']).read_text(encoding='utf-8',errors='strict').splitlines():
   if line.startswith('packagefile '):
    p=no_alias(line.split('=',1)[1]);actual_archives[str(p)]=file_ref(p)
 if actual_mains!=derived['generated_testmain_refs'] or actual_cfgs!=derived['importcfg_refs'] or list(actual_archives.values())!=derived['archive_refs']:raise Stop('Actual generated/importcfg/archive multiset differs')
 for label in ['domain','adapter']:
  graph=''')
seal=seal.replace("  if not graph or len(graph)>4096 or any(x.get('Error') or x.get('DepsErrors') or x.get('Incomplete') for x in graph):raise Stop('Actual full Go graph failed')",'''  if not graph or len(graph)>4096 or any(x.get('Error') or x.get('DepsErrors') or x.get('Incomplete') for x in graph):raise Stop('Actual full Go graph failed')
  for package in graph:
   if not package.get('Dir'):continue
   directory=no_alias(package['Dir'])
   for key in ['GoFiles','CgoFiles','CompiledGoFiles','TestGoFiles','XTestGoFiles','EmbedFiles','TestEmbedFiles','XTestEmbedFiles','CFiles','CXXFiles','MFiles','HFiles','FFiles','SFiles','SwigFiles','SwigCXXFiles','SysoFiles']:
    for name in package.get(key,[]):
     p=Path(name);p=p if p.is_absolute() else directory/p
     if str(no_alias(p)) not in frozenpaths:raise Stop('Actual Go package input omitted from complete closure')
   if package.get('Module',{}).get('GoMod') and str(no_alias(package['Module']['GoMod'])) not in frozenpaths:raise Stop('Actual module metadata omitted')''')
source['seal_readonly']=seal
for n,text in source.items():put(n+'.v2.final.py',text)
s=json.loads((P/'spec.v2.json').read_bytes());files=['controller_common.v2.final.py','controller.v2.final.py','launch.v2.final.py','case_worker.v2.final.py','seal_readonly.v2.final.py','windows_debug_job_tree.py','windows_owned_process.py'];s['controller_refs']=[ref(P/n) for n in files]
for key,n in [('controller_ref','controller'),('case_worker_ref','case_worker'),('launcher_ref','launch'),('sealer_ref','seal_readonly')]:s[key]=ref(P/(n+'.v2.final.py'))
s['source_export_public_blob_count']=511;s['preparation_revision']='v2-final-static-only';save('spec.v2.final.json',s)
g=json.loads((P/'root-grant.UNAUTHORIZED.v2.template.json').read_bytes());g['spec_ref']=ref(P/'spec.v2.final.json');g['controller_refs']=s['controller_refs'];g['repository']=None;save('root-grant.UNAUTHORIZED.v2.final.template.json',g)
scope=json.loads((P/'root-scope.UNREGISTERED.v2.template.json').read_bytes());scope['spec_ref']=ref(P/'spec.v2.final.json');scope['controller_refs']=s['controller_refs'];scope['repository']='D:\\作品集\\ResearchOS\\research-os';save('root-scope.UNREGISTERED.v2.final.template.json',scope)
rows=[]
for name in files:
 tree=ast.parse(read(name),filename=str(P/name));rows.append({'ref':ref(P/name),'AST_PARSE':'PASS','imported':False,'executed':False})
save('ast-audit.final.json',{'files':rows,'candidate_execution':False,'native_Go_SQL_Node_HTTP_MODEL_calls':0})
for name in ['controller_common','controller','launch','case_worker','seal_readonly']:
 a=name+'.v2.py';b=name+'.v2.final.py';put(name+'.final-static-guard.diff',''.join(difflib.unified_diff(read(a).splitlines(True),read(b).splitlines(True),fromfile=a,tofile=b)))
print(json.dumps({'spec':ref(P/'spec.v2.final.json'),'controller':ref(P/'controller.v2.final.py'),'AST_only_modules':len(rows),'authorized':False},ensure_ascii=False))
