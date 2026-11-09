from pathlib import Path
import json,hashlib,shutil,difflib
root=Path(__file__).parent; task=root.parent
candidate=task/'product-v1-native-layout-visual-prepare-09'; base=task/'product-v1-native-layout-visual08-review-20261105/candidate08'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
write=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
manifest=read(candidate/'MANIFEST.json'); scope=read(candidate/'scope.template.json'); old=read(base/'scope.template.json')
assert sha(candidate/'MANIFEST.json')=='c17090b690ba180884e12ae374349cef634acd8b9bd193a408203cc97a22a871'
assert sha(candidate/'FROZEN.json')=='93d0a340c743278041dbfbb4b4e1a52799e4dd21fa6ce62bae5ab1f7af080ee9'
assert sha(candidate/'scope.template.json')=='df0864b1c23238916958fac1669c5cc91d8e4dbbe36d1ede5335078d1d596d6a'
for f in manifest['files']:assert sha(candidate/f['path'])==f['sha256'] and (candidate/f['path']).stat().st_size==f['bytes']
assert len(manifest['files'])==16
for f in ['choose-owned-folder.ps1','visual-geometry-purechecks.mjs']:assert (candidate/f).read_bytes()==(base/f).read_bytes()
newcode=(candidate/'real-electron-flow.mjs').read_text(encoding='utf-8'); oldcode=(base/'real-electron-flow.mjs').read_text(encoding='utf-8')
begin='    // Require two successive stable layout samples after real loading clears.'
end="    activeRunEvidence.phase = 'WORKBENCH_OPEN_SAME_PROJECT_ZERO_TASK';"
assert newcode.split(begin)[0]==oldcode.split(begin)[0] and newcode.split(end)[1]==oldcode.split(end)[1]
def part(t,a,b):return t[t.index(a):t.index(b,t.index(a))]
assert part(newcode,'const hit=e=>','const centerIn=')==part(oldcode,'const hit=e=>','const centerIn=')
assert part(newcode,"      if(row.actual_theme!==row.requested_theme)",'      return findings;')==part(oldcode,"      if(row.actual_theme!==row.requested_theme)",'      return findings;')
assert part(newcode,"        if(!initial.heading_center_in_view",'    const initialScrollReset')==part(oldcode,"        if(!initial.heading_center_in_view",'    visual.findings=')
(root/'independent-runner.diff').write_text(''.join(difflib.unified_diff(oldcode.splitlines(True),newcode.splitlines(True),fromfile='archived08',tofile='frozen09')),encoding='utf-8')
assert scope['budget']==old['budget'] and scope['native_picker']==old['native_picker'] and scope['deadlines']==old['deadlines'] and scope['root_supervision']==old['root_supervision']
assert scope['source']['pins'][:-1]==old['source']['pins'][:-1] and len(scope['source']['pins'])==15
assert scope['source']['head']=='11e0395f30a9c9249c2644a6596276a364d2c294'
assert scope['source']['pins'][-1]=={'path':'apps/web/src/workbench.css','sha256':'1eb31349a959f826f462febddc13c2ebb2e66b9afb0c18d38b8b1f1605180647'}
assert scope['scope_nonce'] is None and scope['run_root'].endswith('product-v1-layout-visual-中文-run-03')
source_rows=[]
for row in scope['source']['pins']:
    actual=sha(Path(scope['source']['root'])/row['path']);assert actual==row['sha256'];source_rows.append({'path':row['path'],'sha256':actual})
bundle=Path(scope['bundle']['root'])
for name,expected in [('development-manifest.json',scope['bundle']['manifest_sha256']),('apps/desktop/resources/control/researchos-control.exe',scope['bundle']['control_sha256']),('runtime/electron/electron.exe',scope['bundle']['electron_sha256'])]:assert sha(bundle/name)==expected
assert sha(Path(scope['launcher']['path']))==scope['launcher']['sha256']
development=read(bundle/'development-manifest.json');assert development['source']['head']==scope['source']['head'] and len(development['files'])==134
checks=read(candidate/'CHECKS.json');assert checks['node_runner_syntax_exit']==checks['focused_main_scroll_pure_exit']==checks['focused_ancestor_clip_pure_exit']==0 and len(checks['focused_cases'])==19
assert checks['inherited_geometry_suite_rerun']==0
write(root/'independent-integrity-checks.json',{'candidate_manifest_files_verified':16,'source_pins_verified':source_rows,'bundle_manifest_core_electron_launcher_readback':'MATCH','native_helper_byte_identical':True,'native_previsual_and_postvisual_cleanup_code_byte_identical':True,'original_center_hit_function_byte_identical':True,'existing_finding_gate_suffix_byte_identical':True,'existing_scroll_and_focus_block_byte_identical':True,'author_focused_checks_read_not_rerun':checks})
(root/'candidate09').mkdir(exist_ok=True)
for name in [f['path'] for f in manifest['files']]+['MANIFEST.json','FROZEN.json']:
    dest=root/'candidate09'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(candidate/name,dest)
shutil.copyfile(bundle/'development-manifest.json',root/'build10-development-manifest.json')
report={
 'schema':'researchos.independent-native-layout-visual09-source-review/1','decision':'APPROVED_SOURCE_FIXTURE_ONLY','selected_candidate':str(candidate),'candidate_manifest_sha256':sha(candidate/'MANIFEST.json'),'candidate_frozen_sha256':sha(candidate/'FROZEN.json'),
 'source_sha256':{n:sha(candidate/n) for n in ['real-electron-flow.mjs','choose-owned-folder.ps1','scope.template.json']},'formal_increment':0,'product_increment':0,'pending_blockers':[],
 'build_binding':{'head':scope['source']['head'],'manifest_sha256':scope['bundle']['manifest_sha256'],'core_sha256':scope['bundle']['control_sha256'],'css_sha256':scope['source']['pins'][-1]['sha256'],'template_source_pin_count':15,'listed_manifest_entries':134},
 'observations':[
  '16 frozen manifest entries and announced MANIFEST/FROZEN/scope hashes match. Independently read exact15 source pins plus manifest/Core/Electron/launcher; all match build10. Manifest HEAD agrees. No full134-file enumeration or build rerun.',
  'Native helper c0f1bf... remains byte-identical to approved08. Runner code before visual stability collection and after visual outcome is byte-identical; Core ownership, PID/creation/image, warning/chooser guards, PIDL-to-Main observation, deadlines, cleanup and Job prerequisites remain inherited.',
  'Each initial case resets actual main-area scrollTop/Left in addition to window/conversation descendants. Main rect participates in layout stability; each row records actual main scrollTop/clientHeight/scrollHeight/overflowY/rect. Missing main geometry or nonzero initial document/transcript/main scroll becomes a failure after safe capture.',
  'clipFor walks actual parentElement ancestors for every heading/action/composer. It starts at the actual viewport and uses computed overflowX and overflowY separately. Clipping axes auto/scroll/hidden/clip/overlay intersect actual client bounds derived from bounding rect plus clientLeft/Top and clientWidth/Height. Visible axes remain unclipped. Raw rectangles and complete clipchains preserve the basis of visibility.',
  'Original-center elementFromPoint implementation, old finding suffix and scroll/focus interaction block are byte-identical. A center genuinely inside its effective visible clip but covered still fails. Offscreen/clipped content must become visible, hit and focused after scrolling. Initial findings persist. No nav64 constant, event filter, substituted DOM/CSS or shortcut/task activation was introduced.',
  'Author19 focused checks cover initial offsets/missingmain, actualmain clipping, visible overflow and nav occlusion, scroll accessibility/occlusion, composer clipping, axis independence and nonzero client inset. Their frozen CHECKS and test sources were read; this reviewer did not rerun tests. Inherited geometry test file is retained historical material and was not executed against changed extraction markers.',
  'Budget remains task0/model0/retry0. README honestly states source preparation only, superseded preclip retained, fresh scope/Job required. Prior actualvisual01/02 failures remain consumed failures.'
 ],
 'diagnostic_events':[{'origin_key':'native-layout-visual09:missing-main-ancestor-clipping','classification':'PRE_FREEZE_SOURCE_GEOMETRY_DEFECT_RESOLVED','detail':'Initial09 runner829f999e... reset/recorded main scroll but clipped only transcript and viewport, which could misclassify content outside the new main scrollport as covered. Independent prereview identified this; finalf3a540... uses real per-axis ancestor client clipping for headings/actions/composer and retains original-center hit/focus gates. Superseded unfrozen source is preserved under prior-preclip and not selected. No actual UI run occurred for this diagnostic.'}],
 'execution_prerequisites':['Root must register a fresh nonce and exact original Job/controller/launch-contract pins; this template retains fail-closed status/null pins.','Actual build10 visual03 must capture four initial viewport/theme cases with document/transcript/main scrollTop0, raw rectangles/clipchains/screenshots, then successful after-scroll heading/composer/action checks. Capture validates actual new main scrollport and nav relationship.','Original Job terminal accounting, exact postbundle no-drift and independent actual review remain required. Source approval cannot establish actual UI/J13/product acceptance or model capability.'],
 'limitations':['Axis-aligned client-rectangle geometry and center hit tests are bounded observations, not exhaustive pixel-occlusion verification. Actual screenshots remain necessary.','No tests, App, Native GUI, CLI, task or model were executed by this review; no D writes or private userdata/auth/config reads.'],
 'review_execution':{'node_syntax_rerun':0,'pure_suites_rerun':0,'runner_import':0,'helper_entrypoint':0,'app':0,'native_gui':0,'cli':0,'model':0,'task':0,'d_writes':0},'actual_runtime':'NOT_RUN'
}
write(root/'review-report.json',report)
files=sorted(p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and p.name not in ['archive-file-list.json','archive-sha256.json'])
write(root/'archive-sha256.json',{f:sha(root/f) for f in files});write(root/'archive-file-list.json',{'root':str(root),'files':files+['archive-sha256.json']})
print(json.dumps({'decision':report['decision'],'report':str(root/'review-report.json'),'report_sha256':sha(root/'review-report.json'),'archive_sha256':sha(root/'archive-file-list.json'),'files':len(files)+1}))
