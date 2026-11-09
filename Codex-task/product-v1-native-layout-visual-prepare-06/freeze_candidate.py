from pathlib import Path
import hashlib, json, difflib, subprocess

here=Path(__file__).resolve().parent
root=here.parent
old=root/'product-v1-native-path-entry-prepare-05'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(here/'choose-owned-folder.ps1')==sha(old/'choose-owned-folder.ps1')=='c0f1bf7c83fbf4efe5a9eabe2667866a622c0bcb220eb3d128f60c895644edd8'
runner=here/'real-electron-flow.mjs'
scope_path=here/'scope.template.json'
scope=json.loads(scope_path.read_text(encoding='utf8'))
assert scope['status']=='NOT_RUN_TEMPLATE_REQUIRES_ROOT_REVIEW_NEW_SCOPE_AND_EXACT_JOB'
assert scope['scope_nonce'] is None and scope['root_supervision']['controller_sha256'] is None and scope['root_supervision']['launch_contract_sha256'] is None
assert scope['source']['head']=='1b3a131320c09f553bd3c2c5e3bd39ee6ecb61f2'
assert scope['source']['pins'][8]['sha256']=='060ce0ddaa52e955d797dc82c9a1f0372f9e9a417f1a50453fc3132680b0c125'
assert scope['bundle']['manifest_sha256']=='7f18b5310a855039cef507ddd7093a568a53273a706d63e043ed6946fbc9dfbb'
assert scope['bundle']['control_sha256']=='95da2a4eedd60a5e38f8a08dbe43e38ebb640ee36b826ae37902e21bb6b13b85'
assert scope['budget']['task_submissions']==scope['budget']['model_calls']==scope['budget']['automatic_retries']==0
scope['harness']['runner_sha256']=sha(runner)
scope_path.write_text(json.dumps(scope,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
diff=''.join(difflib.unified_diff((old/'real-electron-flow.mjs').read_text(encoding='utf8').splitlines(True),runner.read_text(encoding='utf8').splitlines(True),fromfile='prepare05/real-electron-flow.mjs',tofile='visual06/real-electron-flow.mjs'))
(here/'runner.diff').write_text(diff,encoding='utf8',newline='\n')
node='C:/nvm4w/nodejs/node.exe'
checks=[]
for name,args in [('runner_node_syntax',['--check',str(runner)]),('new_geometry_pure_counterexamples',[str(here/'visual-geometry-purechecks.mjs')])]:
    result=subprocess.run([node,*args],capture_output=True,text=True,encoding='utf8')
    assert result.returncode==0,(name,result.stderr)
    checks.append({'name':name,'exit_code':result.returncode,'stdout':result.stdout.strip() or None})
checkdoc={'schema':'researchos.native-layout-visual-prepare06-checks/1','status':'NEW_PURE_AND_SYNTAX_PASS_RUNTIME_NOT_RUN',
  'checks':checks,'inherited_native_suites_rerun':0,'runner_import':0,'helper_entrypoint':0,
  'app':0,'gui':0,'cli':0,'model':0,'task':0,'formal_increment':0,'product_increment':0}
(here/'CHECKS.json').write_text(json.dumps(checkdoc,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
files=['README.md','CHECKS.json','choose-owned-folder.ps1','real-electron-flow.mjs','runner.diff','scope.template.json','visual-geometry-purechecks.mjs','freeze_candidate.py']
manifest={'schema':'researchos.native-layout-visual-prepare06-manifest/1','status':'C_ONLY_NOT_RUN_PENDING_ROOT_REVIEW',
  'source_head':scope['source']['head'],'source_workbench_sha256':scope['source']['pins'][8]['sha256'],
  'bundle_manifest_sha256':scope['bundle']['manifest_sha256'],
  'historical_warning_selector_evidence':scope['native_picker']['validation_warning']['dismiss_selector'],
  'files':[{'path':name,'bytes':(here/name).stat().st_size,'sha256':sha(here/name)} for name in files],
  'actual_runtime':'NOT_RUN','task_submissions':0,'model_calls':0,'source_modification_permitted':False}
(here/'MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
frozen={'schema':'researchos.native-layout-visual-prepare06-frozen/1','status':'C_ONLY_NOT_RUN_ROOT_REVIEW_PENDING',
  'manifest_sha256':sha(here/'MANIFEST.json'),'runner_sha256':sha(runner),'helper_sha256':sha(here/'choose-owned-folder.ps1'),
  'scope_template_sha256':sha(scope_path),'source_head_supplied_by_root':scope['source']['head'],
  'source_workbench_sha256':scope['source']['pins'][8]['sha256'],'bundle_manifest_sha256':scope['bundle']['manifest_sha256'],
  'core_sha256':scope['bundle']['control_sha256'],'actual_app_gui_cli_model_task_run':'NOT_RUN'}
(here/'FROZEN.json').write_text(json.dumps(frozen,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps({'runner_sha256':sha(runner),'helper_sha256':sha(here/'choose-owned-folder.ps1'),
 'scope_template_sha256':sha(scope_path),'manifest_sha256':sha(here/'MANIFEST.json'),'frozen_sha256':sha(here/'FROZEN.json'),
 'checks_sha256':sha(here/'CHECKS.json')},ensure_ascii=False))
