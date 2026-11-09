"""Freeze only C environment/cwd revision; no runtime or D writes."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,difflib
ROOT=Path(__file__).resolve().parent
OLD=ROOT.with_name('product-v1-real-electron-tree-diagnostic-01')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def row(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p),'bytes':p.stat().st_size}
def write(n,o):
    with (ROOT/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(o,f,ensure_ascii=False,indent=2);f.write('\n')
for n in ['FROZEN.json','MANIFEST.json','ARCHIVE_FILES.json']:
    if (ROOT/n).exists():raise SystemExit('ALREADY_FROZEN')
b=json.loads((ROOT/'BASELINE.json').read_text())
if digest(OLD/'FROZEN.json')!=b['baseline_freeze_sha256']:raise SystemExit('OLD_FREEZE_DRIFT')
for item in b['baseline_files']:
    if digest(OLD/item['path'])!=item['sha256']:raise SystemExit('OLD_SOURCE_DRIFT')
for n in ['choose-owned-folder.ps1','diagnostic-purechecks.ps1','diagnostic-runner-purechecks.mjs','SELECTOR_BINDING.json']:
    if digest(ROOT/n)!=digest(OLD/n):raise SystemExit('OUTSIDE_ENV_SCOPE:'+n)
old=(OLD/'real-electron-flow.mjs').read_bytes()
new=(ROOT/'real-electron-flow.mjs').read_bytes().decode('utf-8')
lines=new.splitlines(keepends=True)
removed=[line for line in lines if line.startswith('  const systemDrive = path.parse(root).root.replace(') or line.startswith("  requireThat(/^[A-Za-z]:$/.test(systemDrive), 'WINDOWS_SYSTEMROOT_DRIVE_REQUIRED');")]
if len(removed)!=2:raise SystemExit('EXPECTED_TWO_DERIVATION_LINES')
reverse=''.join(line for line in lines if line not in removed)
reverse=reverse.replace('SystemRoot: root, WINDIR: root, SystemDrive: systemDrive.toUpperCase(), OS:', 'SystemRoot: root, WINDIR: root, OS:')
reverse=reverse.replace("argv: [path.join(bundle.bundle, 'apps/desktop')], electron_cwd: scope.run_root,", "argv: [path.join(bundle.bundle, 'apps/desktop')],")
reverse=reverse.replace("args: [path.join(bundle.bundle, 'apps/desktop')], cwd: scope.run_root,", "args: [path.join(bundle.bundle, 'apps/desktop')], cwd: bundle.bundle,")
if reverse.encode('utf-8')!=old:raise SystemExit('ENV_CWD_DIFF_NOT_EXACT_REVERSIBLE')
(ROOT/'runner.diff').write_text(''.join(difflib.unified_diff(old.decode('utf-8').splitlines(True),new.splitlines(True),fromfile='diagnostic01/runner',tofile='diagnostic-env02/runner')),encoding='utf-8')
p=ROOT/'scope.template.json';s=json.loads(p.read_text(encoding='utf-8'))
if s['status']!='NOT_RUN_TEMPLATE_REQUIRES_ROOT_REVIEW_AND_SUPERVISION':raise SystemExit('EXECUTION_SCOPE_NOT_EDITABLE')
s['harness']={'runner_sha256':digest(ROOT/'real-electron-flow.mjs'),'folder_helper_sha256':digest(ROOT/'choose-owned-folder.ps1')}
s['playwright']['inventory_path']=str(ROOT/'SDK_INVENTORY.json')
s['environment_note']='SystemDrive derived from validated drive-rooted SystemRoot; Electron cwd owned run_root; Core explicit REPO unchanged'
p.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
files=[row(p) for p in sorted(ROOT.iterdir()) if p.is_file()]
write('MANIFEST.json',{'schema':'researchos.tree-diagnostic-env02.manifest/1','files':files})
write('FROZEN.json',{'schema':'researchos.tree-diagnostic-env02.freeze/1','status':'SOURCE_ENV_CWD_ONLY_NOT_RUN_PENDING_REVIEW','frozen_at':datetime.now(timezone.utc).isoformat(),'construction_frozen':True,'source_modification_permitted':False,'manifest_sha256':digest(ROOT/'MANIFEST.json'),'scope_sha256':digest(p),'source_sha256':{n:digest(ROOT/n) for n in ['real-electron-flow.mjs','choose-owned-folder.ps1']},'baseline_sha256':digest(ROOT/'BASELINE.json'),'reverse_env_cwd_patch_byte_exact':True,'helper_unchanged':True,'core_cwd_changed':False,'electron_cwd':'scope.run_root after mkdir','new_checks':{'env_cwd_pure':8,'node_syntax_exit':0},'old_checks_not_recounted':True,'sdk':0,'gui':0,'core':0,'uia':0,'model':0,'formal_increment':0,'product_increment':0,'counter_reset':False,'pending':['Independent narrow env/cwd source review','Root exact2 product environment fix/fresh artifact and reviewed scope','Actual GUI/cache behavior NOT_RUN']})
files=[row(p) for p in sorted(ROOT.iterdir()) if p.is_file()]
write('ARCHIVE_FILES.json',{'root':str(ROOT),'files':files,'file_count':len(files),'total_bytes':sum(r['bytes'] for r in files),'excluded':['none; no SDK/cache/build copy']})
print(json.dumps({'status':'DIAGNOSTIC_ENV02_FROZEN_NOT_RUN','freeze_sha256':digest(ROOT/'FROZEN.json'),'manifest_sha256':digest(ROOT/'MANIFEST.json'),'archive_sha256':digest(ROOT/'ARCHIVE_FILES.json'),'scope_sha256':digest(p),'source_sha256':{n:digest(ROOT/n) for n in ['real-electron-flow.mjs','choose-owned-folder.ps1']},'files':len(files),'bytes':sum(r['bytes'] for r in files)}))
