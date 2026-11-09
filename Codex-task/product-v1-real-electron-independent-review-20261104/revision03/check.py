from pathlib import Path
import hashlib,json,os,subprocess,sys
R=Path(__file__).resolve().parent
OLD=R.parent/'revision02';S=R.parents[1]/'product-v1-real-electron-harness-prepare-revision-03'
NODE=Path('C:/nvm4w/nodejs/node.exe');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
PINS={'FROZEN.json':'f5118a259fb30c4f823cf7e755459922b07986595b675faa52db8dc883344b60','MANIFEST.json':'862f5ee070a9cd1d68df6c8d5e287b015b0e0aa2ed125d3ed6637645d74eaba9','real-electron-flow.mjs':'68458e0ff59d091d2481356f19bec7d557a3dc9924ee3f91cc8c47e77b1d450b','choose-owned-folder.ps1':'b5a826fab09c149f8affce7385c4d45efeb5ddc124a438fbb0677ee3f33bc38e'}
def save(name,value):
 p=R/name;assert not p.exists();p.write_text(json.dumps(value,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
def prepare():
 for name,pin in PINS.items():assert sha(S/name)==pin,name
 m=json.loads((S/'MANIFEST.json').read_bytes())
 for row in m['files']:assert sha(S/row['path'])==row['sha256'],row['path']
 assert sha(NODE)=='5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6'
 assert (S/'choose-owned-folder.ps1').read_bytes()==(OLD/'source/choose-owned-folder.ps1').read_bytes()
 old=(OLD/'source/real-electron-flow.mjs').read_text(encoding='utf-8');new=(S/'real-electron-flow.mjs').read_text(encoding='utf-8')
 # Exact delta is only UI8 pin constants/guard and the entry selectors.
 fixed=new
 a=fixed.index('const UI8_SELECTOR_SOURCE = {');b=fixed.index('};\n',a)+3;fixed=fixed[:a]+fixed[b:]
 a=fixed.index('  for (const [name, expected] of Object.entries(UI8_SELECTOR_SOURCE)) {');b=fixed.index('  }\n',a)+4;fixed=fixed[:a]+fixed[b:]
 a=fixed.index("    const nameOptions = page.locator('details.project-name-option');");b=fixed.index('    const helperOutcome = ',a)
 oa=old.index("    await bounded(() => page.getByLabel('项目显示名称'");ob=old.index('    const helperOutcome = ',oa)
 fixed=fixed[:a]+old[oa:ob]+fixed[b:]
 fixed=fixed.replace("const open = page.getByRole('button', { name: '打开工作台', exact: true });","const open = page.getByRole('button', { name: '配置模型并打开工作台', exact: true });")
 assert fixed==old,'Unexpected non-selector delta'
 build=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-build-03-20261104')
 bm=build/'.local/desktop-v1-build-03/development-manifest.json'
 assert sha(bm)=='a800bca4a7fe808a85c6b175547c5e1788e7d4f10b59fe58e17a94f7f4a713fa'
 manifest=json.loads(bm.read_bytes());assert manifest['source']['head']=='c4029c0b57599e1aafed6d01ea4034b0cf465ccd'
 ui={'apps/web/src/workbench.jsx':'e0f4c6db45757b0f506b950fb5eb004de7358f1667cbaf876ab5addee7eadd19','apps/web/src/screens.jsx':'d7405a7bf396b97907dca9ac4bf9182295fba5251b9766e276a67f9ef6b573be'}
 for rel,pin in ui.items():assert sha(build/rel)==pin,rel
 dest=R/'source';dest.mkdir(exist_ok=False)
 for name in ['FROZEN.json','MANIFEST.json','real-electron-flow.mjs','choose-owned-folder.ps1','SELECTOR_BINDING.json','scope.template.json']:(dest/name).write_bytes((S/name).read_bytes())
 save('inputs.json',{'pins':PINS,'manifest_files':len(m['files']),'helper_byte_identical_to_independent_revision02':True,'runner_exact_delta_only_UI8':True,'node_sha256':sha(NODE),'build03_manifest':str(bm),'build03_manifest_sha256':sha(bm),'build03_source_head':manifest['source']['head'],'build03_two_UI_source_pins':ui,'reuse':{'path8':'../revision02/independent-path.result.json','node7':'../revision02/independent-node-02.result.json'},'formal_increment':0})
 print(json.dumps({'prepared':True,'helper_same':True,'exact_UI8_delta':True,'build03_binding':True}))
def execute(name,args):
 env={key:os.environ[key] for key in ['SystemRoot','WINDIR','COMSPEC','TEMP','TMP'] if key in os.environ};env['PATH']=str(NODE.parent)
 save(name+'.command.json',{'argv':[str(NODE)]+args,'environment':env,'controller_sha256':sha(Path(__file__)),'source_sha256':PINS,'no_SDK_GUI_model':True})
 with (R/(name+'.stdout.raw')).open('xb') as out,(R/(name+'.stderr.raw')).open('xb') as err:
  code=subprocess.run([str(NODE)]+args,cwd=R,env=env,stdout=out,stderr=err,timeout=20).returncode
 save(name+'.result.json',{'exit_code':code,'stdout_sha256':sha(R/(name+'.stdout.raw')),'stderr_sha256':sha(R/(name+'.stderr.raw')),'formal_increment':0})
 print(json.dumps({'phase':name,'exit_code':code}));return code
if __name__=='__main__':
 if sys.argv[1]=='prepare':prepare()
 elif sys.argv[1]=='selector':sys.exit(execute('independent-selectors',[str(R/'selectors.mjs')]))
 elif sys.argv[1]=='syntax':sys.exit(execute('runner-syntax',['--check',str(R/'source/real-electron-flow.mjs')]))
