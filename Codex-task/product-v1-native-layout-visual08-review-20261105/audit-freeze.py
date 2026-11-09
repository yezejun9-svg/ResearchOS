from pathlib import Path
import json,hashlib,shutil
root=Path(__file__).parent; task=root.parent
candidate=task/'product-v1-native-layout-visual-prepare-08'
base=task/'product-v1-native-layout-visual07-review-20261105/candidate07'
cp=Path('D:/作品集/ResearchOS/research-os/execution/product-v1/receipts/single-harness-20261104/progress-cp656')
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
write=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
manifest=read(candidate/'MANIFEST.json'); scope=read(candidate/'scope.template.json'); old=read(base/'scope.template.json')
assert sha(candidate/'MANIFEST.json')=='e4a3cda10b3abf68d1c544eb8bd1705560a2f0d93ed4b03881df8025bb8fa601'
assert sha(candidate/'FROZEN.json')=='fbc3a98ec95cd8571f865f9afd48bca2cd32dbb7ca8305053b428bbbf71e0607'
assert sha(candidate/'scope.template.json')=='0d7d686176caf4a3e2dfeb13368de1436f0d4a7dd4149c0fd66fb772b3f0b1c9'
for f in manifest['files']:assert sha(candidate/f['path'])==f['sha256'] and (candidate/f['path']).stat().st_size==f['bytes']
same=['real-electron-flow.mjs','choose-owned-folder.ps1','runner.diff','visual-geometry-purechecks.mjs']
for f in same:assert (candidate/f).read_bytes()==(base/f).read_bytes()
delta=[]
def compare(a,b,p=''):
    if isinstance(a,dict) and isinstance(b,dict):
        for k in sorted(a.keys()|b.keys()):compare(a.get(k),b.get(k),p+'/'+k)
    elif a!=b:delta.append({'path':p,'before':a,'after':b})
compare(old,scope)
allowed={'/run_root','/source/root','/source/head','/source/pin_status','/source/pins','/bundle/root','/bundle/manifest_sha256','/bundle/control_sha256','/bundle/source_binding_review','/launcher/path','/product_acceptance','/selector_binding/source_head','/selector_binding/bundle_manifest_sha256','/selector_binding/source_sha256/apps/web/src/workbench.css','/visual_profile/source_css_pin_required'}
assert all(r['path'] in allowed for r in delta)
assert scope['source']['pins'][:-1]==old['source']['pins']
assert scope['source']['pins'][-1]=={'path':'apps/web/src/workbench.css','sha256':'5ef1a169db8c193f77e0410bc9e4ed960ae66752f1bed1387bd2097640900f02'}
assert scope['scope_nonce'] is None and scope['root_supervision']['controller_sha256'] is None and scope['root_supervision']['launch_contract_sha256'] is None
assert scope['budget']==old['budget'] and scope['deadlines']==old['deadlines'] and scope['native_picker']==old['native_picker']
assert scope['run_root'].endswith('product-v1-layout-visual-中文-run-02')
source_rows=[]
for p in scope['source']['pins']:
    actual=sha(Path(scope['source']['root'])/p['path']); assert actual==p['sha256']; source_rows.append({'path':p['path'],'sha256':actual,'matches':True})
bundle=Path(scope['bundle']['root'])
for name,expected in [('development-manifest.json',scope['bundle']['manifest_sha256']),('apps/desktop/resources/control/researchos-control.exe',scope['bundle']['control_sha256']),('runtime/electron/electron.exe',scope['bundle']['electron_sha256'])]:assert sha(bundle/name)==expected
assert sha(Path(scope['launcher']['path']))==scope['launcher']['sha256']
resume=read(cp/'RESUME.json'); registration=read(cp/'build09.registration.json'); outer=read(cp/'build09.outer.RESULT.json'); development=read(cp/'development-manifest.json')
assert sha(cp/'development-manifest.json')==scope['bundle']['manifest_sha256']=='27659d100d38f8af8fca841f176feaf471fdc9d674fbd202ee9f4b12cad7d329'
assert scope['source']['head']==registration['main_head']==resume['main_head']==development['source']['head']=='5956907bd640d2d4f4abcb583aeb2520883e97c8'
assert scope['bundle']['control_sha256']==resume['desktop']['control_sha256']=='b251f950ab626b6fd8620d5a2a4be41feff44d996545dbce03d90fd350a0fed9'
assert len(registration['source_sha256'])==resume['desktop']['source_pins_verified']==43
assert len(development['files'])==resume['desktop']['listed_files_verified']==134
assert registration['source_sha256']['apps/web/src/workbench.css']==scope['source']['pins'][-1]['sha256']
assert outer['root_exit_code']==0 and outer['job_active_zero'] and outer['stop_proved'] and not outer['input_drift'] and not outer['errors'] and outer['terminate_job_attempts']==outer['terminate_original_root_attempts']==0
write(root/'independent-delta-and-pin-checks.json',{'scope_delta':delta,'byte_identical_files':{n:sha(candidate/n) for n in same},'manifest_files_verified':len(manifest['files']),'direct_source_pins_verified':source_rows,'bundle_manifest_core_electron_launcher_exact_readback':'PASS','cp656_receipts':{n:sha(cp/n) for n in ['RESUME.json','development-manifest.json','build09.registration.json','build09.outer.RESULT.json']},'no_tests_or_runtime_executed':True})
(root/'candidate08').mkdir(exist_ok=True)
for name in [f['path'] for f in manifest['files']]+['MANIFEST.json','FROZEN.json']:shutil.copyfile(candidate/name,root/'candidate08'/name)
(root/'cp656-evidence').mkdir(exist_ok=True)
for n in ['RESUME.json','development-manifest.json','build09.registration.json','build09.outer.RESULT.json']:shutil.copyfile(cp/n,root/'cp656-evidence'/n)
report={
 'schema':'researchos.independent-native-layout-visual08-delta-review/1','decision':'APPROVED_SOURCE_FIXTURE_ONLY','selected_candidate':str(candidate),'candidate_manifest_sha256':sha(candidate/'MANIFEST.json'),'candidate_frozen_sha256':sha(candidate/'FROZEN.json'),
 'source_sha256':{n:sha(candidate/n) for n in ['real-electron-flow.mjs','choose-owned-folder.ps1','scope.template.json']},'formal_increment':0,'product_increment':0,'pending_blockers':[],'diagnostic_events':[],
 'observations':['Runner, Native helper, geometry purechecks and runner.diff are byte-identical to independently archived07; no finding threshold, interaction, cleanup, ownership, authorization or model boundary changed.','Scope delta is restricted to build09 source/root/head/manifest/Core/launcher, workbench.css pin, new run02 root and review metadata. Previous14 source pins remain byte-for-byte values; CSS is the sole added15th template source pin.','Independent precise readback of15 listed source files, bundle manifest/Core/Electron and launcher matched; CP656 archived build receipts agree with HEAD/CSS/Core/manifest. No134-file traversal or build/test rerun.','CP656 reports134 verified bundle files and43 integrated source pins. Its original build Job exited0/stopped with1358 total processes, zero active, no force/errors/input drift; build success is not UI success.','Prior visual01 actual mobile-overlap findings and consumed scope remain failures. Controller retains initial viewport screenshots, scroll offsets, clipped overlap and real center-hit findings, including failures before later scroll probes.'],
 'build_binding':{'head':scope['source']['head'],'manifest_sha256':scope['bundle']['manifest_sha256'],'core_sha256':scope['bundle']['control_sha256'],'css_sha256':scope['source']['pins'][-1]['sha256'],'template_source_pin_count':15,'cp656_integrated_pin_count':43,'cp656_listed_file_count':134},
 'execution_prerequisites':['Root must register a fresh nonce and exact original Job/controller/launch-contract pins. Template status and null pins remain fail-closed.','Each actual INITIAL_VIEWPORT row must have exact viewport/theme and document.scroll_y=0/transcript.scroll_top=0 before claiming initial-layout evidence.','Actual build09 dark/light1440x1000 and390x844 screenshots/geometry, original Job terminal accounting and post-bundle readback remain pending; no UI/J13/product acceptance granted.'],
 'review_execution':{'node_syntax_rerun':0,'pure_suites_rerun':0,'runner_import':0,'helper_entrypoint':0,'app':0,'native_gui':0,'cli':0,'model':0,'task':0,'d_writes':0,'private_userdata_auth_config_reads':0},
 'actual_runtime':'NOT_RUN'
}
write(root/'review-report.json',report)
files=sorted(p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and p.name not in ['archive-file-list.json','archive-sha256.json'])
write(root/'archive-sha256.json',{f:sha(root/f) for f in files})
write(root/'archive-file-list.json',{'root':str(root),'files':files+['archive-sha256.json']})
print(json.dumps({'decision':report['decision'],'report':str(root/'review-report.json'),'report_sha256':sha(root/'review-report.json'),'archive_sha256':sha(root/'archive-file-list.json'),'files':len(files)+1,'delta_fields':len(delta)}))
