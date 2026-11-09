"""Freeze C-only diagnostic profile. No SDK/helper/UIA invocation."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,difflib
ROOT=Path(__file__).resolve().parent
OLD=ROOT.with_name('product-v1-real-electron-harness-prepare-revision-04')
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def row(p): return {'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p),'bytes':p.stat().st_size}
def write(n,o):
    with (ROOT/n).open('x',encoding='utf-8',newline='\n') as f: json.dump(o,f,ensure_ascii=False,indent=2);f.write('\n')
for n in ['FROZEN.json','MANIFEST.json','ARCHIVE_FILES.json']:
    if (ROOT/n).exists(): raise SystemExit('ALREADY_FROZEN')
b=json.loads((ROOT/'BASELINE.json').read_text())
if digest(OLD/'FROZEN.json')!=b['freeze4_sha256']: raise SystemExit('OLD_FREEZE_DRIFT')
for item in b['baseline_files']:
    if digest(OLD/item['path'])!=item['sha256']: raise SystemExit('OLD_SOURCE_DRIFT')
for n in ['real-electron-flow.mjs','choose-owned-folder.ps1']:
    old=(OLD/n).read_text(encoding='utf-8');new=(ROOT/n).read_text(encoding='utf-8')
    (ROOT/(n+'.diff')).write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='approved04/'+n,tofile='diagnostic01/'+n)),encoding='utf-8')
helper=(ROOT/'choose-owned-folder.ps1').read_text(encoding='utf-8')
oldhelper=(OLD/'choose-owned-folder.ps1').read_text(encoding='utf-8')
for a,z in [('function Convert-NativeDeadlineUtc(', 'function Convert-UiaAbsolutePath('),('  function Assert-Core(', '  Assert-Core\n')]:
    if helper[helper.index(a):helper.index(z,helper.index(a))]!=oldhelper[oldhelper.index(a):oldhelper.index(z,oldhelper.index(a))]: raise SystemExit('DATE_OR_OWNER_GUARD_CHANGED')
runner=(ROOT/'real-electron-flow.mjs').read_text(encoding='utf-8')
for text in ['window.researchos.harness','submit.click(','getByLabel(\'Codex','POST /harness']:
    if text in runner: raise SystemExit('MODEL_PATH_REMAINS')
if '$okAttempted=$true' in helper or '$result.clicked_ok=$true' in helper or 'Get-OwnedDialogButton 1' in helper: raise SystemExit('OK_PATH_REMAINS')
p=ROOT/'scope.template.json';scope=json.loads(p.read_text(encoding='utf-8'))
if scope['status']!='NOT_RUN_TEMPLATE_REQUIRES_ROOT_REVIEW_AND_SUPERVISION': raise SystemExit('EXECUTION_SCOPE_NOT_EDITABLE')
scope['native_picker']['diagnostic_only']=True
scope['native_picker']['operator_fallback']=False
scope['native_picker']['diagnostic_limits']={'tree_candidates':16,'win32_children_on_zero':32,'text_chars':96,'stdout_bytes':65536}
scope['budget']['task_submissions']=0
scope['budget']['automatic_retries']=0
scope['budget']['provider_calls_per_task']='NOT_APPLICABLE_DIAGNOSTIC_ONLY'
scope['harness']={'runner_sha256':digest(ROOT/'real-electron-flow.mjs'),'folder_helper_sha256':digest(ROOT/'choose-owned-folder.ps1')}
scope['playwright']['inventory_path']=str(ROOT/'SDK_INVENTORY.json')
scope['diagnostic_result_semantics']='METADATA_ONLY_NORMAL_OWNED_CANCEL_NO_OK_NO_WORKSPACE_NO_MODEL'
p.write_text(json.dumps(scope,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
files=[row(p) for p in sorted(ROOT.iterdir()) if p.is_file()]
write('MANIFEST.json',{'schema':'researchos.owned-tree-diagnostic.manifest/1','files':files})
write('FROZEN.json',{'schema':'researchos.owned-tree-diagnostic.freeze/1','status':'DIAGNOSTIC_SOURCE_ONLY_NOT_RUN_PENDING_REVIEW','frozen_at':datetime.now(timezone.utc).isoformat(),'construction_frozen':True,'source_modification_permitted':False,'manifest_sha256':digest(ROOT/'MANIFEST.json'),'scope_sha256':digest(p),'source_sha256':{n:digest(ROOT/n) for n in ['real-electron-flow.mjs','choose-owned-folder.ps1']},'baseline_sha256':digest(ROOT/'BASELINE.json'),'approved04_unchanged':True,'ordinary_scope_budget_still_one':True,'new_checks':{'node_pure':19,'helper_pure':14,'node_syntax_exit':0},'runner':0,'helper_entrypoint':0,'sdk':0,'add_type':0,'uia':0,'gui':0,'native':0,'model':0,'formal_increment':0,'product_increment':0,'counter_reset':False,'pending':['Independent diagnostic-source review','New Root fresh actual diagnostic scope/exact outer Job','Real candidate data NOT_RUN']})
files=[row(p) for p in sorted(ROOT.iterdir()) if p.is_file()]
write('ARCHIVE_FILES.json',{'root':str(ROOT),'files':files,'file_count':len(files),'total_bytes':sum(r['bytes'] for r in files),'excluded':['none; no SDK/cache/build copy']})
print(json.dumps({'status':'DIAGNOSTIC01_FROZEN_NOT_RUN','freeze_sha256':digest(ROOT/'FROZEN.json'),'manifest_sha256':digest(ROOT/'MANIFEST.json'),'archive_sha256':digest(ROOT/'ARCHIVE_FILES.json'),'scope_sha256':digest(p),'source_sha256':{n:digest(ROOT/n) for n in ['real-electron-flow.mjs','choose-owned-folder.ps1']},'files':len(files),'bytes':sum(r['bytes'] for r in files)}))
