from pathlib import Path
import json,hashlib,shutil
root=Path(__file__).parent
task=root.parent
candidate=task/'product-v1-native-layout-visual-prepare-07'
old=task/'product-v1-native-layout-visual-prepare-06'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
write=lambda p,obj:p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
manifest=json.loads((candidate/'MANIFEST.json').read_text(encoding='utf-8-sig'))
checks=[{'path':r['path'],'expected':r['sha256'],'actual':sha(candidate/r['path'])} for r in manifest['files']]
assert all(r['expected']==r['actual'] for r in checks)
assert sha(candidate/'MANIFEST.json')=='c90a7a88316acdfee50284dcbc1a5066c695f5c72a95bf0bc56ef09ada59d01b'
assert sha(candidate/'FROZEN.json')=='9547148782baaf7d61696fcbe035cfd5fa03680e0214b465187e395bd258ebfb'
write(root/'candidate-integrity.json',{'checked_files':checks,'mismatches':0,'manifest_sha256':sha(candidate/'MANIFEST.json'),'frozen_sha256':sha(candidate/'FROZEN.json')})
old_manifest=json.loads((old/'MANIFEST.json').read_text(encoding='utf-8-sig'))
drift=[{'path':r['path'],'frozen_expected':r['sha256'],'observed_actual':sha(old/r['path'])} for r in old_manifest['files'] if sha(old/r['path'])!=r['sha256']]
write(root/'superseded06-integrity-diagnostic.json',{'candidate':str(old),'not_selected':True,'mismatches':drift,'author_explanation':'Author confirmed two files were modified in place after 06 freeze to narrow overlapsViewport and add two pure checks, then copied to 07. No restoration or overwrite requested. 06 remains superseded with stale frozen metadata.'})
(root/'candidate07').mkdir(exist_ok=True)
for name in [r['path'] for r in manifest['files']]+['MANIFEST.json','FROZEN.json']:
    shutil.copyfile(candidate/name,root/'candidate07'/name)
prior=task/'product-v1-native-layout-visual06-review-20261105'
for name in ['build08-pin-verification.json','partial-viewport-counterexample.mjs','partial-viewport-counterexample.log']:
    shutil.copyfile(prior/name,root/name)
report={
 'schema':'researchos.independent-native-layout-visual-source-review/1',
 'decision':'APPROVED_SOURCE_FIXTURE_ONLY','selected_candidate':str(candidate),
 'formal_increment':0,'product_increment':0,'actual_runtime':'NOT_RUN',
 'source_sha256':{name:sha(candidate/name) for name in ['real-electron-flow.mjs','choose-owned-folder.ps1','scope.template.json']},
 'candidate_manifest_sha256':sha(candidate/'MANIFEST.json'),'candidate_frozen_sha256':sha(candidate/'FROZEN.json'),
 'source_head':'1b3a131320c09f553bd3c2c5e3bd39ee6ecb61f2',
 'bundle_manifest_sha256':'7f18b5310a855039cef507ddd7093a568a53273a706d63e043ed6946fbc9dfbb',
 'core_sha256':'95da2a4eedd60a5e38f8a08dbe43e38ebb640ee36b826ae37902e21bb6b13b85',
 'pending_blockers':[],
 'execution_prerequisites':['Root must bind a fresh nonce/run_root and exact original Job controller/launch-contract hashes; this template is not executable authorization.','Actual build08 1440x1000 and 390x844 dark/light rendered screenshots, geometry, original Job terminal accounting and post-bundle no-drift evidence remain unobserved.','For each INITIAL_VIEWPORT row verify document.scroll_y and transcript_scroll.scroll_top are zero. Reset is explicit but runtime does not fail automatically on nonzero readback; a nonzero initial offset must not be accepted as initial-layout proof.'],
 'review_observations':[
  'Native05 helper remains byte-exact c0f1bf7c83fbf4efe5a9eabe2667866a622c0bcb220eb3d128f60c895644edd8. Diff adds UI8 source pin and post-Main-binding visual collection only; owner/PID/creation/image/PIDL-boundary observation, native deadlines, cleanup and original Job prerequisites remain inherited.',
  'Task submission/model/retry budgets remain exactly zero; visual actions are viewport resize, existing theme-button click, scrolling and focus. No starter activation, form submit, capability probe, model invocation or product source write introduced.',
  'Actual body loading markers clear before collection; each viewport/theme resets document and conversation descendants scroll then requires two stable geometry samples. Actual viewport and theme mismatch, missing required rectangles and horizontal document overflow are failure findings.',
  'Measurements read real rendered DOM rectangles and elementFromPoint at the true center; no injected DOM/CSS or clamped fake center. Raw and clipped rectangles are retained. Content overlap is clipped to transcript and viewport; partial visibility is separate from center-in-clip.',
  'Initial fullPage:false viewport snapshots/rows precede scroll probes. Initial overlap/center occlusion findings remain in aggregate even when a later scroll succeeds. Scrolled heading/composer/action accessibility is separately gated; actions are focused without click.',
  'Independent build08 readback verified 14 source pins and bundle manifest/Core/Electron pins; evidence is copied from the immediately preceding review and not rerun.',
  '06 drift is limited to author C preparation files, not product source or executed UI. 07 independently matches all 8 manifest entries and announced manifest/FROZEN hashes.'
 ],
 'validation':{'node_syntax_exit':0,'author_geometry_predicate_checks':18,'independent_extracted_classifier_counterexamples':8,'all_passed':True,'old_native_suites_rerun':0,'runner_import':0,'helper_entrypoint':0,'gui':0,'app':0,'cli':0,'model':0,'d_writes':0},
 'diagnostic_events':[
  {'origin_key':'native-layout-visual06:partial-viewport-false-covered','classification':'SOURCE_FIXTURE_FALSE_POSITIVE_FIXED_IN_07','detail':'06 classifier treats partial rectangle visibility as eligible center-hit occlusion. Pure counterexample with heading y840 height40 in viewport844 yields false HEADING_COVERED_INITIAL although center860 is offscreen and no occluder exists. 07 separates center-in-clip and preserves actual occlusion failures.'},
  {'origin_key':'native-layout-visual06:post-freeze-source-drift','classification':'C_PREPARATION_EVIDENCE_INTEGRITY_SUPERSEDED','detail':'Independent manifest readback found runner and geometry purechecks mismatch in superseded06; remaining six files match. Author confirmed post-freeze in-place overlap narrowing and test additions before copying07. 06 was neither restored nor selected. Exact expected/observed hashes preserved in superseded06-integrity-diagnostic.json.'},
  {'origin_key':'native-layout-visual07-review:python-app-alias-unavailable','classification':'REVIEW_ENVIRONMENT_LAUNCH_DIAGNOSTIC','detail':'One attempt to run C-only report writer via python resolved to WindowsApps/python.exe and failed ResourceUnavailable before script execution. Switched to existing codex-primary-runtime dependencies/python/python.exe. No candidate or product command ran in the failed attempt.'}
 ],
 'limitations':['This approves source/fixture boundaries only, not actual Windows behavior, screenshot appearance, full pixel occlusion coverage, model capability, J01 or product acceptance.','Center-hit/rectangle checks are bounded geometry probes; real screenshots still require review. Loading-marker absence does not establish model or capability readiness.','No GUI/App/CLI/model or old consumed scope was replayed.']
}
write(root/'review-report.json',report)
files=sorted(str(p.relative_to(root)).replace('\\','/') for p in root.rglob('*') if p.is_file() and p.name not in ['archive-file-list.json','archive-sha256.json'])
write(root/'archive-sha256.json',{f:sha(root/f) for f in files})
write(root/'archive-file-list.json',{'root':str(root),'files':files+['archive-sha256.json']})
print(json.dumps({'decision':report['decision'],'report':str(root/'review-report.json'),'report_sha256':sha(root/'review-report.json'),'archive':str(root/'archive-file-list.json'),'archive_sha256':sha(root/'archive-file-list.json'),'files':len(files)+1},indent=2))
