from pathlib import Path
import hashlib,json

here=Path(__file__).resolve().parent
root=here.parent
old=root/'product-v1-native-layout-visual-prepare-07'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name in ['real-electron-flow.mjs','choose-owned-folder.ps1','runner.diff','visual-geometry-purechecks.mjs']:
    assert sha(here/name)==sha(old/name),(name,'INHERITED_07_BYTES_DRIFT')
scope_path=here/'scope.template.json'
scope=json.loads(scope_path.read_text(encoding='utf8'))
assert scope['status']=='NOT_RUN_TEMPLATE_REQUIRES_ROOT_REVIEW_NEW_SCOPE_AND_EXACT_JOB'
assert scope['scope_nonce'] is None
assert scope['root_supervision']['controller_sha256'] is None and scope['root_supervision']['launch_contract_sha256'] is None
assert scope['budget']['task_submissions']==scope['budget']['model_calls']==scope['budget']['automatic_retries']==0
assert scope['source']['head']=='5956907bd640d2d4f4abcb583aeb2520883e97c8'
assert scope['source']['root'].endswith('product-v1-build-09-20261105')
assert scope['run_root'].endswith('product-v1-layout-visual-中文-run-02')
assert scope['harness']['runner_sha256']==sha(here/'real-electron-flow.mjs')
assert scope['harness']['folder_helper_sha256']==sha(here/'choose-owned-folder.ps1')
assert scope['source']['pins'][-1]=={'path':'apps/web/src/workbench.css','sha256':'5ef1a169db8c193f77e0410bc9e4ed960ae66752f1bed1387bd2097640900f02'}
src=Path(scope['source']['root'])
assert src.is_dir()
for row in scope['source']['pins']:
    assert sha(src/row['path'])==row['sha256'],('SOURCE_PIN_MISMATCH',row['path'])
bundle=Path(scope['bundle']['root'])
assert bundle.is_dir()
expected_manifest='27659d100d38f8af8fca841f176feaf471fdc9d674fbd202ee9f4b12cad7d329'
expected_core='b251f950ab626b6fd8620d5a2a4be41feff44d996545dbce03d90fd350a0fed9'
assert sha(bundle/'development-manifest.json')==expected_manifest
assert sha(bundle/'apps/desktop/resources/control/researchos-control.exe')==expected_core
assert sha(bundle/'runtime/electron/electron.exe')==scope['bundle']['electron_sha256']
assert sha(Path(scope['launcher']['path']))==scope['launcher']['sha256']
scope['bundle']['manifest_sha256']=expected_manifest
scope['bundle']['control_sha256']=expected_core
scope['bundle']['source_binding_review']='ROOT_REVIEW_REQUIRED_BUILD09'
scope['selector_binding']['bundle_manifest_sha256']=expected_manifest
assert scope['selector_binding']['source_head']==scope['source']['head']
assert scope['selector_binding']['source_sha256']['apps/web/src/workbench.css']==scope['source']['pins'][-1]['sha256']
scope['source']['pin_status']='BUILD09_LOCAL_SOURCE_PINS_HASH_VERIFIED_ROOT_REVIEW_PENDING'
scope_path.write_text(json.dumps(scope,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
(here/'README.md').write_text('''# Native responsive visual candidate 08 — C-only NOT_RUN

The runner, Native helper, runner diff and pure geometry predicates are byte-identical to candidate 07. No visual policy or finding gate changed. The fresh template targets build09 and `product-v1-layout-visual-中文-run-02`; its HEAD, full listed source pins including the final `workbench.css` fix, bundle manifest, Electron, Core and launcher hashes were locally re-read. `workbench.jsx` keeps SHA `060ce0ddaa52e955d797dc82c9a1f0372f9e9a417f1a50453fc3132680b0c125`.

Root must independently review this candidate, supply a new scope nonce and original f13 Job/controller/launch-contract pins, and verify the source-bound build before an actual zero-model UI run. The template status, null nonce and null Root pins fail closed. No App, Native, CLI, task or model execution was performed here; no pure geometry suite was rerun. Candidate 07 and its consumed actual run remain unchanged.
''',encoding='utf8',newline='\n')
delta={'schema':'researchos.native-layout-visual08-delta/1','status':'C_ONLY_NOT_RUN_ROOT_REVIEW_PENDING',
  'base':'product-v1-native-layout-visual-prepare-07',
  'byte_identical_to_07':{name:sha(here/name) for name in ['real-electron-flow.mjs','choose-owned-folder.ps1','runner.diff','visual-geometry-purechecks.mjs']},
  'changed_from_07':['scope.template.json','README.md','DELTA.json','CHECKS.json','MANIFEST.json','FROZEN.json','freeze08.py'],
  'source_head_root_supplied':scope['source']['head'],'bundle_manifest_sha256':expected_manifest,'core_sha256':expected_core,
  'css_sha256':scope['source']['pins'][-1]['sha256'],'runner_import':0,'helper_entrypoint':0,
  'app':0,'native':0,'cli':0,'model':0,'task':0,'pure_geometry_suites_rerun':0}
(here/'DELTA.json').write_text(json.dumps(delta,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
checks={'schema':'researchos.native-layout-visual08-checks/1','status':'STATIC_HASH_PINS_PASS_RUNTIME_NOT_RUN',
  'checks':['07_inherited_four_files_byte_identical','09_all_listed_source_pins_match','09_manifest_core_electron_launcher_match','scope_zero_budget_and_null_root_pins'],
  'pure_geometry_suites_rerun':0,'node_syntax_rerun':0,'app':0,'native':0,'cli':0,'model':0,'task':0}
(here/'CHECKS.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
names=['README.md','CHECKS.json','DELTA.json','choose-owned-folder.ps1','real-electron-flow.mjs','runner.diff','scope.template.json','visual-geometry-purechecks.mjs','freeze08.py']
manifest={'schema':'researchos.native-layout-visual08-manifest/1','status':'C_ONLY_NOT_RUN_ROOT_REVIEW_PENDING',
  'source_head':scope['source']['head'],'bundle_manifest_sha256':expected_manifest,'core_sha256':expected_core,
  'source_workbench_sha256':scope['selector_binding']['source_sha256']['apps/web/src/workbench.jsx'],
  'source_css_sha256':scope['selector_binding']['source_sha256']['apps/web/src/workbench.css'],
  'files':[{'path':name,'bytes':(here/name).stat().st_size,'sha256':sha(here/name)} for name in names],
  'actual_runtime':'NOT_RUN','task_submissions':0,'model_calls':0,'source_modification_permitted':False}
(here/'MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
frozen={'schema':'researchos.native-layout-visual08-frozen/1','status':'C_ONLY_NOT_RUN_ROOT_REVIEW_PENDING',
  'manifest_sha256':sha(here/'MANIFEST.json'),'scope_template_sha256':sha(scope_path),
  'runner_sha256':sha(here/'real-electron-flow.mjs'),'helper_sha256':sha(here/'choose-owned-folder.ps1'),
  'source_head_root_supplied':scope['source']['head'],'bundle_manifest_sha256':expected_manifest,
  'core_sha256':expected_core,'css_sha256':scope['source']['pins'][-1]['sha256'],
  'actual_app_native_cli_model_task_run':'NOT_RUN'}
(here/'FROZEN.json').write_text(json.dumps(frozen,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
archive={'root':str(root),'files':[{'path':f'{here.name}/{p.name}','sha256':sha(p)} for p in sorted(here.iterdir()) if p.is_file()],
  'status':'C_ONLY_NOT_RUN_ROOT_REVIEW_PENDING','actual_runtime':'NOT_RUN','model_calls':0,'task_submissions':0}
(root/'product-v1-native-layout-visual08-author-archive.json').write_text(json.dumps(archive,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps({'scope_sha256':sha(scope_path),'manifest_sha256':sha(here/'MANIFEST.json'),'frozen_sha256':sha(here/'FROZEN.json'),
  'archive_sha256':sha(root/'product-v1-native-layout-visual08-author-archive.json'),'archive_files':len(archive['files'])},ensure_ascii=False))
