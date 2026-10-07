import datetime,hashlib,json,os,pathlib,shutil,subprocess,sys,uuid
R=pathlib.Path(r'D:/作品集/ResearchOS/research-os');W=R;D=pathlib.Path(__file__).parent/('closure-'+uuid.uuid4().hex);D.mkdir();G=R/'.local/tools/go1.27.1/go';N=pathlib.Path('C:/nvm4w/nodejs/node.exe');B=R/'.local/w0599-main-stream-integration-r268/mu-worker.mjs'
E=os.environ.copy();E.update(GOROOT=str(G),GOENV='off',GOTOOLCHAIN='local',GOPATH=str(R/'.local/gopath'),GOCACHE=str(R/'.local/gocache'),GOPROXY='off',GOSUMDB='off',RESEARCHOS_GO=str(G/'bin/go.exe'),RESEARCHOS_NODE=str(N),RESEARCHOS_MU_BUNDLE=str(B))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,obj):(D/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def run(name,args):
 start=datetime.datetime.now(datetime.timezone.utc).isoformat()
 with (D/(name+'.stdout.raw')).open('wb') as out,(D/(name+'.stderr.raw')).open('wb') as err: c=subprocess.run(args,cwd=W,env=E,stdout=out,stderr=err,timeout=600)
 save(name+'.invocation.json',dict(argv=args,cwd=str(W),started_at=start,finished_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),actual_exit=c.returncode,stdout_sha256=sha(D/(name+'.stdout.raw')),stderr_sha256=sha(D/(name+'.stderr.raw'))))
 return c.returncode
if run('go-list',[str(G/'bin/go.exe'),'list','-deps','-test','-json','./apps/cli','./internal/domain','./adapters/runtime']):raise SystemExit('actual go list failed; original evidence preserved')
raw=(D/'go-list.stdout.raw').read_text(encoding='utf8');dec=json.JSONDecoder();packages=[]
while raw.strip():
 raw=raw.lstrip();p,end=dec.raw_decode(raw);packages.append(p);raw=raw[end:]
paths=set()
for p in packages:
 if not p.get('Dir'):continue
 folder=pathlib.Path(p['Dir']);paths.update(x for x in folder.glob('*.go') if x.is_file())
 for key in ['EmbedFiles','TestEmbedFiles','XTestEmbedFiles','SFiles','HFiles','SysoFiles','CFiles','CXXFiles']:
  for name in p.get(key,[]):paths.add(folder/name)
 if p.get('Module',{}).get('GoMod'):paths.add(pathlib.Path(p['Module']['GoMod']))
for name in ['internal','adapters','apps','tests/runtime','migrations','spec/v2.0/contracts']:
 paths.update(p for p in (W/name).rglob('*') if p.is_file() and p.suffix in ['.go','.mjs','.json','.sql'])
for folder in ['internal','adapters','tests']:
 for data in (W/folder).rglob('testdata'):paths.update(p for p in data.rglob('*') if p.is_file())
for name in ['packages','node_modules']:paths.update(p for p in (R/'third_party/mu'/name).rglob('*') if p.is_file() and '.git' not in p.parts)
for name in ['third_party/mu/package.json','third_party/mu/package-lock.json','third_party/mu.MANIFEST.json','third_party/VENDORED_FROM.md','execution/v2.4/component_lock.json']:paths.add(R/name)
paths.update([W/'go.mod',W/'go.sum',G/'bin/go.exe',N,B,pathlib.Path(__file__).resolve(),pathlib.Path(sys.executable)])
paths.update(p for p in (G/'pkg/tool').rglob('*') if p.is_file())
powershell=pathlib.Path(shutil.which('powershell.exe'));paths.add(powershell)
paths.update(p for p in powershell.parent.glob('*.dll') if p.is_file())
for name in ['csc.exe','csc.exe.config','Microsoft.CSharp.dll','mscorlib.dll','System.dll','System.Core.dll']:
 p=pathlib.Path(E['SYSTEMROOT'])/'Microsoft.NET/Framework64/v4.0.30319'/name
 if p.is_file():paths.add(p)
locked_path=W/'execution/toolchains/locked.json';paths.add(locked_path)
locked=json.loads(locked_path.read_bytes());git_path=pathlib.Path(locked['tools']['git']['path']);paths.add(git_path)
assert sha(git_path)==locked['tools']['git']['sha256']
paths=sorted(paths)
def snap():
 out={}
 for p in paths:
  if p.is_relative_to(W):key='repo:'+p.relative_to(W).as_posix()
  elif p.is_relative_to(R):key='main:'+p.relative_to(R).as_posix()
  else:key='absolute:'+p.as_posix()
  out[key]=sha(p) if p.is_file() else 'MISSING'
 return out
save('environment.json',{k:E[k] for k in ['GOROOT','GOENV','GOTOOLCHAIN','GOPATH','GOCACHE','GOPROXY','GOSUMDB','RESEARCHOS_GO','RESEARCHOS_NODE','RESEARCHOS_MU_BUNDLE']})
run('git-status',['git','status','--porcelain=v1','--untracked-files=no']);before=snap();save('source_before.json',before);assert 'MISSING' not in before.values()
print(json.dumps({'actual_directory':str(D),'input_count':len(before),'phase':'actual fullCLI test after closed source snapshot'}),flush=True)
assert sha(B)=='2a8e70132a914affc6122c1f1db29cfa315b655c93d4200145852ebbc853d441'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=W).decode().strip()=='1c7d7d8af69fbb523586e0e3a874cff5f17a3c00'
save('composition_provenance.json',{'main_repaired_source_head':'1c7d7d8af69fbb523586e0e3a874cff5f17a3c00','cli_scope_ref':{'path':'execution/v2.4/receipts/W05/W05-99/integration_codex/cli-read-causal-scope-r267/scope_registration.json','sha256':'b950974027f665aaf543029dd4dffbf5cbee23fb5b38a3e819a35dc508a333dc'},'rebase_ref':'execution/v2.4/receipts/W05/W05-99/cli_read_interrupt_executor_codex/composition-rebase-r269/result.json','original_three_scope_proof_is_historical':True,'new_exact4_current_composition':True,'root_main_actual_integration':'execution/v2.4/receipts/W05/W05-99/integration_codex/main-cli-source-integration-r272/result.json','independent_source_review_sha256':'ecfb699818af3fae4aaf404263b0752382984f2f3dbbc3f21e3b3f2d91eaf0f9','lock_and_actual_git_inputs_included':True,'formal_increment':0})
code=run('test',[str(G/'bin/go.exe'),'test','-json','-count=1','-timeout=480s','./apps/cli']+(['-run','^TestCLIRead'] if 'focused' in sys.argv else []));after=snap();save('source_after.json',after);counts={'pass':0,'fail':0,'skip':0};tops={'pass':0,'fail':0,'skip':0}
for line in (D/'test.stdout.raw').read_bytes().splitlines():
 try:row=json.loads(line)
 except:continue
 if row.get('Test') and row.get('Action') in counts:
  counts[row['Action']]+=1
  if '/' not in row['Test']:tops[row['Action']]+=1
 if row.get('Action')=='fail' or row.get('OutputType')=='error':print(json.dumps(row,ensure_ascii=False))
result={'measurement_mode':'FIXTURE_NOT_LIVE_NOT_FORMAL','actual_exit':code,'source_drift':before!=after,'input_count':len(before),'assertion_counts':counts,'top_counts':tops,'source_before_sha256':sha(D/'source_before.json'),'source_after_sha256':sha(D/'source_after.json'),'bundle_sha256':sha(B),'formal_increment':0};save('result.json',result);print(json.dumps(result,ensure_ascii=False),flush=True);sys.exit(code or int(before!=after) or int(counts['pass']==0 or counts['skip']!=0))