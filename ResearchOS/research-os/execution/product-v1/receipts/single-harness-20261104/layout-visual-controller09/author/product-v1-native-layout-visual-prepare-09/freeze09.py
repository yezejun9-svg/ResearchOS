from pathlib import Path
import hashlib,json

here=Path(__file__).resolve().parent
root=here.parent
base=root/'product-v1-native-layout-visual-prepare-08'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
scope_path=here/'scope.template.json'
scope=json.loads(scope_path.read_text(encoding='utf8'))
assert scope['status']=='NOT_RUN_TEMPLATE_REQUIRES_ROOT_REVIEW_NEW_SCOPE_AND_EXACT_JOB'
assert scope['scope_nonce'] is None and scope['root_supervision']['controller_sha256'] is None and scope['root_supervision']['launch_contract_sha256'] is None
assert scope['budget']['task_submissions']==scope['budget']['model_calls']==scope['budget']['automatic_retries']==0
assert scope['source']['head']=='11e0395f30a9c9249c2644a6596276a364d2c294'
assert scope['source']['root'].endswith('product-v1-build-10-20261105')
assert scope['run_root'].endswith('product-v1-layout-visual-中文-run-03')
assert sha(here/'choose-owned-folder.ps1')==sha(base/'choose-owned-folder.ps1')=='c0f1bf7c83fbf4efe5a9eabe2667866a622c0bcb220eb3d128f60c895644edd8'
assert sha(here/'visual-geometry-purechecks.mjs')==sha(base/'visual-geometry-purechecks.mjs')
assert sha(here/'prior-preclip/real-electron-flow.mjs')=='829f999e545cc838e6d118a7e09fb2340c324398a99ff41adff593e3558cf3c6'
assert sha(here/'real-electron-flow.mjs')=='f3a540bde9a7b332ed7852834bd073fad68543a6b5e32190cf96d19bce24d047'
assert scope['harness']['runner_sha256']==sha(here/'real-electron-flow.mjs')
assert scope['harness']['folder_helper_sha256']==sha(here/'choose-owned-folder.ps1')
assert scope['source']['pins'][-1]=={'path':'apps/web/src/workbench.css','sha256':'1eb31349a959f826f462febddc13c2ebb2e66b9afb0c18d38b8b1f1605180647'}
assert scope['selector_binding']['source_sha256']['apps/web/src/workbench.jsx']=='060ce0ddaa52e955d797dc82c9a1f0372f9e9a417f1a50453fc3132680b0c125'
src=Path(scope['source']['root'])
assert src.is_dir()
for row in scope['source']['pins']:
    assert sha(src/row['path'])==row['sha256'],('SOURCE_PIN_MISMATCH',row['path'])
bundle=Path(scope['bundle']['root'])
assert bundle.is_dir()
manifest_sha='be2cfd213234a5550a3241cfdbe49ce25effcfb41c0e1a96d36d422367441a8e'
core_sha='7ed68638d7b65395dc0235cccf7d7fd67caf768c14b014eab38f6ba27509c09b'
assert sha(bundle/'development-manifest.json')==manifest_sha
assert sha(bundle/'apps/desktop/resources/control/researchos-control.exe')==core_sha
assert sha(bundle/'runtime/electron/electron.exe')==scope['bundle']['electron_sha256']
assert sha(Path(scope['launcher']['path']))==scope['launcher']['sha256']
scope['bundle']['manifest_sha256']=manifest_sha
scope['bundle']['control_sha256']=core_sha
scope['bundle']['source_binding_review']='ROOT_REVIEW_REQUIRED_BUILD10'
scope['selector_binding']['bundle_manifest_sha256']=manifest_sha
assert scope['selector_binding']['source_head']==scope['source']['head']
assert scope['selector_binding']['source_sha256']['apps/web/src/workbench.css']==scope['source']['pins'][-1]['sha256']
scope['source']['pin_status']='BUILD10_LOCAL_SOURCE_PINS_HASH_VERIFIED_ROOT_REVIEW_PENDING'
scope_path.write_text(json.dumps(scope,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
(here/'README.md').write_text('''# Native responsive visual candidate 09 — C-only NOT_RUN

This candidate preserves 08's Native helper, JSX selector pin, four viewport/theme cases, real screenshots, original-center elementFromPoint hit checks, and action scroll/focus gate. It adds explicit main-area scroll reset and recorded main scroll geometry. Nonzero initial document, transcript or main scroll produces `INITIAL_SCROLL_NOT_RESET` after all safe captures.

The visibility calculation walks each element's real ancestor chain. Computed overflowX/Y clip only their respective axes for auto, scroll, hidden, clip and overlay using actual ancestor padding/client bounds. Visible overflow does not clip. Raw rectangles, clipped rectangles, and every heading/action/composer clipchain are recorded. A truly visible covered control still fails; every action must be visible, hit and focused after scrolling. No fixed nav offset, DOM/CSS substitution or finding filter exists.

The prior-preclip 09 runner (SHA `829f999e545cc838e6d118a7e09fb2340c324398a99ff41adff593e3558cf3c6`) is preserved under `prior-preclip/` and superseded because it omitted main-area ancestor clipping. The corrected runner has SHA `f3a540bde9a7b332ed7852834bd073fad68543a6b5e32190cf96d19bce24d047`. Candidate 08 remains unchanged.

Build10 source HEAD, all listed source pins including CSS, bundle manifest, Core, Electron and launcher were locally rehashed. Root must independently review this C scope and bind a fresh nonce and original f13 Job/controller/launch-contract pins before an actual run. Template status and null Root pins fail closed. No App, Native, CLI, task or model execution occurred; only new focused scroll and ancestor-clip pure countercases plus Node syntax were checked, not the inherited suite.
''',encoding='utf8',newline='\n')
delta={'schema':'researchos.native-layout-visual09-delta/1','status':'C_ONLY_NOT_RUN_ROOT_REVIEW_PENDING',
  'base':'product-v1-native-layout-visual-prepare-08','superseded_preclip_runner_sha256':sha(here/'prior-preclip/real-electron-flow.mjs'),
  'resolved_preclip_diagnostic':'Previous clip used transcript and viewport only; main-area overflow could falsely mark normal clipped content as covered.',
  'runner_sha256':sha(here/'real-electron-flow.mjs'),'helper_byte_identical_to_08_sha256':sha(here/'choose-owned-folder.ps1'),
  'new_behavior':['explicit_main_scroll_reset','main_scroll_geometry_and_initial_zero_gate','computed_per_axis_ancestor_client_clipping','raw_rect_and_clipchain_evidence'],
  'unchanged':['original_center_elementFromPoint','four_viewport_theme_cases','after_scroll_action_visible_hit_focus','zero_task_model_budget'],
  'source_head_root_supplied':scope['source']['head'],'css_sha256':scope['source']['pins'][-1]['sha256'],
  'bundle_manifest_sha256':manifest_sha,'core_sha256':core_sha,'app':0,'native':0,'cli':0,'model':0,'task':0,'inherited_geometry_suite_rerun':0}
(here/'DELTA.json').write_text(json.dumps(delta,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
names=['README.md','CHECKS.json','DELTA.json','choose-owned-folder.ps1','real-electron-flow.mjs','runner.diff','scope.template.json','visual-geometry-purechecks.mjs','main-scroll-purechecks.mjs','ancestor-clip-purechecks.mjs','freeze09.py']
names += [str(p.relative_to(here)).replace('\\','/') for p in sorted((here/'prior-preclip').iterdir()) if p.is_file()]
manifest={'schema':'researchos.native-layout-visual09-manifest/1','status':'C_ONLY_NOT_RUN_ROOT_REVIEW_PENDING',
  'source_head':scope['source']['head'],'source_css_sha256':scope['source']['pins'][-1]['sha256'],
  'source_workbench_sha256':scope['selector_binding']['source_sha256']['apps/web/src/workbench.jsx'],
  'bundle_manifest_sha256':manifest_sha,'core_sha256':core_sha,
  'files':[{'path':name,'bytes':(here/name).stat().st_size,'sha256':sha(here/name)} for name in names],
  'actual_runtime':'NOT_RUN','task_submissions':0,'model_calls':0,'source_modification_permitted':False}
(here/'MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
frozen={'schema':'researchos.native-layout-visual09-frozen/1','status':'C_ONLY_NOT_RUN_ROOT_REVIEW_PENDING',
  'manifest_sha256':sha(here/'MANIFEST.json'),'scope_template_sha256':sha(scope_path),
  'runner_sha256':sha(here/'real-electron-flow.mjs'),'helper_sha256':sha(here/'choose-owned-folder.ps1'),
  'source_head_root_supplied':scope['source']['head'],'css_sha256':scope['source']['pins'][-1]['sha256'],
  'bundle_manifest_sha256':manifest_sha,'core_sha256':core_sha,'actual_app_native_cli_model_task_run':'NOT_RUN'}
(here/'FROZEN.json').write_text(json.dumps(frozen,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
archive={'root':str(root),'files':[{'path':str(p.relative_to(root)).replace('\\','/'),'sha256':sha(p)} for p in sorted(here.rglob('*')) if p.is_file()],
  'status':'C_ONLY_NOT_RUN_ROOT_REVIEW_PENDING','actual_runtime':'NOT_RUN','model_calls':0,'task_submissions':0}
(root/'product-v1-native-layout-visual09-author-archive.json').write_text(json.dumps(archive,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps({'scope_sha256':sha(scope_path),'manifest_sha256':sha(here/'MANIFEST.json'),'frozen_sha256':sha(here/'FROZEN.json'),
  'archive_sha256':sha(root/'product-v1-native-layout-visual09-author-archive.json'),'archive_files':len(archive['files'])},ensure_ascii=False))
