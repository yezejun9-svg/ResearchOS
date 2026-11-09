from pathlib import Path
import datetime,hashlib,json,os,re,subprocess,sys
R=Path(__file__).resolve().parent
A=R.parent/'product-v1-assistant-startup-author'
MAIN=Path('D:/作品集/ResearchOS/research-os')
WT=MAIN/'.local/worktrees/product-v1-assistant-home-20261104'
RUN=R/'run-01';TREE=RUN/'source';NODE=Path('C:/nvm4w/nodejs/node.exe')
MODULES=MAIN/'.local/product-v1-build-inputs-20261104/web-node_modules-02/node_modules'
PINS={'final/source-manifest.json':'245e5f1a82dc2e744eae92971e0bbfd55f3c8b694d6c99a1533bedfd4fba1055','final/FROZEN.json':'0f1b44740fcd2c1e4d165851fa69e61f7c0f4c706dbe705a6878ea0282c5b201','final/summary.json':'95326bea73522ae71e99a1e4deaf02a4150e8e968faf07fa7f32c521396e61ec','final/diagnostics.json':'c1912ecc230a6b0435ea862a06d942f3f35d7bf8fd95233825ebe31c8371de0b','EVIDENCE_MANIFEST.json':'b180b9750455a33e66fea5b980adbe7d699ced22f98d5e2a29c9b26de91f1057','archive-file-list.json':'3eb25a156ac3e05aab1e1c6bd2ae5c3fe4d8c04f3cb45526fa806992ea02f499'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,value):
 p=RUN/name;assert not p.exists(),str(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
def cache_inventory():
 rows=[]
 for p in sorted(MODULES.rglob('*')):
  assert not (getattr(p.lstat(),'st_file_attributes',0)&0x400),str(p)
  if p.is_file():rows.append({'path':p.relative_to(MODULES).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size})
 assert len(rows)==365,len(rows)
 return rows
def prepare():
 assert not RUN.exists()
 for name,pin in PINS.items():assert sha(A/name)==pin,name
 m=json.loads((A/'final/source-manifest.json').read_bytes())
 scope=MAIN/'execution/product-v1/receipts/single-harness-20261104/assistant-home/scope.json'
 assert sha(scope)==m['scope_sha256']
 s=json.loads(scope.read_bytes());assert set(m['source_sha256'])==set(s['production_paths']+s['test_paths']) and len(m['source_sha256'])==8
 assert m['construction_frozen'] and not m['source_modification_permitted']
 assert sha(NODE)=='5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6'
 cache=MODULES.parent/'INPUTS-02.json';assert sha(cache)=='75beb02ce4a6a6c0eec69ede2d8da6a29cca4596632bbb6b2c29956473766493'
 RUN.mkdir();inputs={}
 def copy(source,rel,classification):
  source=Path(source);assert source.is_file() and not source.is_symlink(),str(source)
  target=TREE/rel
  if target.exists():assert sha(target)==sha(source);return
  target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source.read_bytes())
  inputs[rel]={'sha256':sha(target),'bytes':target.stat().st_size,'source_path':str(source),'classification':classification}
 for rel,pin in m['source_sha256'].items():
  assert sha(A/'final/source'/rel)==pin and sha(WT/rel)==pin,rel
  copy(A/'final/source'/rel,rel,'FROZEN_EXACT8')
 for rel,pin in m['unchanged_boundary_sha256'].items():assert sha(WT/rel)==pin,rel
 # Only the necessary frontend import closure, public static contracts and
 # selected pure-test dependencies; never export/archive the Git repository.
 for p in (WT/'apps/web/src').rglob('*'):
  if p.is_file():copy(p,p.relative_to(WT).as_posix(),'READONLY_FRONTEND_BUILD_DEPENDENCY')
 for rel in ['apps/web/package.json','apps/web/index.html']:
  copy(WT/rel,rel,'READONLY_FRONTEND_BUILD_DEPENDENCY')
 for rel in ['spec/v2.0/ui/design-tokens.json','spec/v2.0/contracts/openapi.json']:
  copy(MAIN/rel,rel,'IMMUTABLE_PUBLIC_CONTRACT_BUILD_DEPENDENCY')
 for rel in ['tests/ui/desktop/harness-workbench.test.mjs','tests/ui/desktop/activity-projection.test.mjs','tests/ui/desktop/development-smoke.test.mjs','tests/ui/desktop/w13-react.test.js']:
  copy(WT/rel,rel,'SELECTED_EXISTING_PURE_TEST')
 seen=set()
 def closure(p):
  p=p.resolve();rel=p.relative_to(WT.resolve()).as_posix()
  if rel in seen:return
  seen.add(rel);copy(p,rel,'PURE_TEST_LOCAL_MODULE_DEPENDENCY')
  if p.suffix not in ['.js','.mjs','.cjs']:return
  text=p.read_text(encoding='utf-8')
  for match in re.finditer(r"(?:require\s*\(|import\s*\()\s*['\"](\.[^'\"]+)['\"]",text):
   q=p.parent/match.group(1)
   candidates=[q,q.with_suffix('.js'),q.with_suffix('.mjs'),q/'index.js']
   found=next((v for v in candidates if v.is_file()),None)
   assert found is not None,(p,match.group(1));closure(found)
 for name in ['ipc.js','app-protocol.js','first-use.js','v2.js','wire-values.mjs']:closure(WT/'apps/desktop/main/lib'/name)
 for name in PINS:
  target=RUN/'author'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((A/name).read_bytes())
 (RUN/'scope.json').write_bytes(scope.read_bytes());(RUN/'INPUTS-02.json').write_bytes(cache.read_bytes())
 inv=cache_inventory();save('cache-inventory.json',inv)
 save('inputs.json',{'source_sha256':m['source_sha256'],'unchanged_boundary_sha256':m['unchanged_boundary_sha256'],'files':inputs,'node':str(NODE),'node_sha256':sha(NODE),'module_root':str(MODULES),'cache_inventory_sha256':sha(RUN/'cache-inventory.json'),'cache_declared_root_digest':'e1c316403d5e6614a48ade25ad8169227d39200a30426f213dbec73bcdebde26','cache_inventory_format':'Independent sorted path/sha256/bytes JSON; declared Root digest not asserted to use this same serialization','scope_sha256':sha(scope),'author_pins':PINS,'base_head':m['base_head'],'controller_sha256':sha(__file__),'formal_increment':0})
 print(json.dumps({'prepared':True,'exact_files':8,'necessary_dependency_files':len(inputs)-8,'inputs_sha256':sha(RUN/'inputs.json')}))
def check():
 i=json.loads((RUN/'inputs.json').read_bytes())
 for rel,v in i['files'].items():assert sha(TREE/rel)==v['sha256'],rel
 return i
def run(name,args,cwd=None):
 i=check()
 private=RUN/'private'
 for part in ['profile','appdata','localappdata','tmp']:(private/part).mkdir(parents=True,exist_ok=True)
 env={key:os.environ[key] for key in ['SystemRoot','WINDIR','COMSPEC'] if key in os.environ}
 env.update({'PATH':str(NODE.parent)+os.pathsep+str(Path(env['SystemRoot'])/'System32'),'USERPROFILE':str(private/'profile'),'HOME':str(private/'profile'),'APPDATA':str(private/'appdata'),'LOCALAPPDATA':str(private/'localappdata'),'TEMP':str(private/'tmp'),'TMP':str(private/'tmp'),'CI':'1','NO_COLOR':'1'})
 command=[str(NODE)]+args
 save(name+'.command.json',{'argv':command,'cwd':str(cwd or TREE),'environment':env,'controller_sha256':sha(__file__),'node_sha256':sha(NODE),'classification':'C_PURE_NODE_FIXTURE_OR_WEB_COMPILER_ONLY_NO_ELECTRON_NATIVE_DB_MODEL'})
 (RUN/(name+'.controller.py.txt')).write_bytes(Path(__file__).read_bytes())
 save(name+'.started.json',{'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
 with (RUN/(name+'.stdout.raw')).open('wb') as out,(RUN/(name+'.stderr.raw')).open('wb') as err:
  r=subprocess.run(command,cwd=cwd or TREE,env=env,stdout=out,stderr=err,timeout=100)
 out=(RUN/(name+'.stdout.raw')).read_text(encoding='utf-8',errors='strict')
 counts={key:int(m.group(1)) for key in ['tests','suites','pass','fail','cancelled','skipped','todo'] if (m:=re.search(r'^# '+key+r' (\d+)\s*$',out,re.M))}
 check();save(name+'.result.json',{'exit_code':r.returncode,'tap_summary':counts,'stdout_sha256':sha(RUN/(name+'.stdout.raw')),'stderr_sha256':sha(RUN/(name+'.stderr.raw')),'formal_increment':0})
 print(json.dumps({'phase':name,'exit_code':r.returncode,'tap_summary':counts}));return r.returncode
def vite():
 dest=RUN/'vite';dest.mkdir(exist_ok=False)
 aliases=[{'find':'react-dom/client','replacement':(MODULES/'react-dom/client.js').as_posix()},{'find':'react/jsx-runtime','replacement':(MODULES/'react/jsx-runtime.js').as_posix()},{'find':'react','replacement':(MODULES/'react/index.js').as_posix()}]
 config=dest/'vite.config.mjs';config.write_text('export default '+json.dumps({'resolve':{'alias':aliases}})+'\n',encoding='utf-8')
 result=run('vite-build',[str(MODULES/'vite/bin/vite.js'),'build',str(TREE/'apps/web'),'--config',str(config),'--outDir',str(dest/'dist')],R)
 outputs=[{'path':p.relative_to(RUN).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted((dest/'dist').rglob('*')) if p.is_file()]
 save('vite/outputs.json',{'files':outputs,'source_unchanged':True,'cache_unchanged':cache_inventory()==json.loads((RUN/'cache-inventory.json').read_bytes()),'formal_increment':0})
 return result
def readback():
 i=check()
 for rel,pin in i['source_sha256'].items():assert sha(WT/rel)==pin and sha(A/'final/source'/rel)==pin,rel
 for rel,pin in i['unchanged_boundary_sha256'].items():assert sha(WT/rel)==pin,rel
 assert cache_inventory()==json.loads((RUN/'cache-inventory.json').read_bytes())
 save('no-drift.json',{'exact8_match_current_worktree_author_and_C':True,'source_sha256':i['source_sha256'],'ipc_preload_boundary_unchanged':True,'module_cache_unchanged':True,'formal_increment':0})
 print(json.dumps({'no_drift':True,'sha256':sha(RUN/'no-drift.json')}))
if __name__=='__main__':
 phase=sys.argv[1]
 if phase=='prepare':prepare()
 elif phase=='required':sys.exit(run('required-tests',['--test','--test-reporter=tap','tests/ui/desktop/assistant-startup.test.mjs','tests/ui/desktop/harness-workbench.test.mjs','tests/ui/desktop/activity-projection.test.mjs','tests/ui/desktop/development-smoke.test.mjs']))
 elif phase=='mu':sys.exit(run('mu-first-use',['--test','--test-reporter=tap','--test-name-pattern=^first use consumes native choice','tests/ui/desktop/w13-react.test.js']))
 elif phase=='independent':sys.exit(run('independent-tests',['--test','--test-reporter=tap',str(R/'independent.test.mjs')]))
 elif phase=='vite':sys.exit(vite())
 elif phase=='readback':readback()
 else:raise SystemExit('unknown phase')
