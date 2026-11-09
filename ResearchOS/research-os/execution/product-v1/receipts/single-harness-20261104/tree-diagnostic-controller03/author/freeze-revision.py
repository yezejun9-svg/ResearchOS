"""Freeze C-only direct HWND diagnostics, no runtime execution."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,difflib
ROOT=Path(__file__).resolve().parent
OLD=ROOT.with_name('product-v1-real-electron-tree-diagnostic-revision-02')
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def row(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':h(p),'bytes':p.stat().st_size}
def write(n,o):
    with (ROOT/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(o,f,ensure_ascii=False,indent=2);f.write('\n')
for n in ['FROZEN.json','MANIFEST.json','ARCHIVE_FILES.json']:
    if (ROOT/n).exists():raise SystemExit('ALREADY_FROZEN')
b=json.loads((ROOT/'BASELINE.json').read_text())
if h(OLD/'FROZEN.json')!=b['baseline_freeze_sha256']:raise SystemExit('BASELINE_FREEZE_DRIFT')
for item in b['baseline_files']:
    if h(OLD/item['path'])!=item['sha256']:raise SystemExit('OLD_SOURCE_DRIFT')
oldrunner=(OLD/'real-electron-flow.mjs').read_text(encoding='utf-8');runner=(ROOT/'real-electron-flow.mjs').read_text(encoding='utf-8')
oldhelper=(OLD/'choose-owned-folder.ps1').read_text(encoding='utf-8');helper=(ROOT/'choose-owned-folder.ps1').read_text(encoding='utf-8')
for start,end in [('export function makeEnvironment(', 'function requireChatGPTAuthentication(')]:
    if runner[runner.index(start):runner.index(end)]!=oldrunner[oldrunner.index(start):oldrunner.index(end)]:raise SystemExit('ENV_CHANGED')
for start,end in [('function Convert-NativeDeadlineUtc(', 'function Convert-UiaAbsolutePath('),('  function Assert-Core(', '  Assert-Core\n')]:
    if helper[helper.index(start):helper.index(end,helper.index(start))]!=oldhelper[oldhelper.index(start):oldhelper.index(end,oldhelper.index(start))]:raise SystemExit('DATE_OR_CORE_OWNER_CHANGED')
for text in ['Get-OwnedDialogButton 1','$result.clicked_ok=$true','$okAttempted=$true']:
    if text in helper:raise SystemExit('OK_PATH')
for text in ['window.researchos.harness','submit.click(']:
    if text in runner:raise SystemExit('MODEL_PATH')
for n,old,new in [('real-electron-flow.mjs',oldrunner,runner),('choose-owned-folder.ps1',oldhelper,helper)]:
    (ROOT/(n+'.diff')).write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='diagnostic02/'+n,tofile='direct03/'+n)),encoding='utf-8')
p=ROOT/'scope.template.json';s=json.loads(p.read_text(encoding='utf-8'))
if s['status']!='NOT_RUN_TEMPLATE_REQUIRES_ROOT_REVIEW_AND_SUPERVISION':raise SystemExit('EXECUTION_SCOPE_NOT_EDITABLE')
s['native_picker']['diagnostic_only']=True;s['native_picker']['direct_native_tree']=True
s['native_picker']['direct_limits']={'enum_child_windows':64,'selected_elements':4,'public_value_chars':1024}
s['budget']['task_submissions']=0
s['harness']={'runner_sha256':h(ROOT/'real-electron-flow.mjs'),'folder_helper_sha256':h(ROOT/'choose-owned-folder.ps1')}
s['playwright']['inventory_path']=str(ROOT/'SDK_INVENTORY.json')
p.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
files=[row(p) for p in sorted(ROOT.iterdir()) if p.is_file()]
write('MANIFEST.json',{'schema':'researchos.direct-native-tree.manifest/1','files':files})
write('FROZEN.json',{'schema':'researchos.direct-native-tree.freeze/1','status':'SOURCE_DIAGNOSTIC_ONLY_NOT_RUN_PENDING_REVIEW','frozen_at':datetime.now(timezone.utc).isoformat(),'construction_frozen':True,'source_modification_permitted':False,'manifest_sha256':h(ROOT/'MANIFEST.json'),'scope_sha256':h(p),'source_sha256':{n:h(ROOT/n) for n in ['real-electron-flow.mjs','choose-owned-folder.ps1']},'baseline_sha256':h(ROOT/'BASELINE.json'),'old_sources_unchanged':True,'new_checks':{'node_pure':7,'helper_pure':11,'node_syntax_exit':0},'old_checks_not_recounted':True,'runner':0,'helper_entrypoint':0,'sdk':0,'add_type':0,'uia':0,'gui':0,'model':0,'formal_increment':0,'product_increment':0,'counter_reset':False,'pending':['Independent narrow direct-HWND review','Fresh Root diagnostic scope/exact outer Job','Actual provider and reliable path data NOT_RUN']})
files=[row(p) for p in sorted(ROOT.iterdir()) if p.is_file()]
write('ARCHIVE_FILES.json',{'root':str(ROOT),'files':files,'file_count':len(files),'total_bytes':sum(r['bytes'] for r in files),'excluded':['none; no SDK/cache/build copy']})
print(json.dumps({'status':'DIRECT03_FROZEN_NOT_RUN','freeze_sha256':h(ROOT/'FROZEN.json'),'manifest_sha256':h(ROOT/'MANIFEST.json'),'archive_sha256':h(ROOT/'ARCHIVE_FILES.json'),'scope_sha256':h(p),'source_sha256':{n:h(ROOT/n) for n in ['real-electron-flow.mjs','choose-owned-folder.ps1']},'files':len(files),'bytes':sum(r['bytes'] for r in files)}))
