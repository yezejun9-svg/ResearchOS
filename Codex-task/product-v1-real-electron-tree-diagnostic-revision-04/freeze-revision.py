"""Freeze C-only metadata owner-order fix, no runtime execution."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,difflib
ROOT=Path(__file__).resolve().parent
OLD=ROOT.with_name('product-v1-real-electron-tree-diagnostic-revision-03')
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def row(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':h(p),'bytes':p.stat().st_size}
def write(n,o):
    with (ROOT/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(o,f,ensure_ascii=False,indent=2);f.write('\n')
for n in ['FROZEN.json','MANIFEST.json','ARCHIVE_FILES.json']:
    if (ROOT/n).exists():raise SystemExit('ALREADY_FROZEN')
b=json.loads((ROOT/'BASELINE.json').read_text())
if h(OLD/'FROZEN.json')!=b['baseline_freeze_sha256']:raise SystemExit('BASELINE_DRIFT')
for item in b['baseline_files']:
    if h(OLD/item['path'])!=item['sha256']:raise SystemExit('OLD_SOURCE_DRIFT')
for item in b['prior_review']:
    if h(Path(item['path']))!=item['sha256'] or h(ROOT/item['copied_path'])!=item['sha256']:raise SystemExit('PRIOR_REVIEW_DRIFT')
if h(ROOT/'real-electron-flow.mjs')!=h(OLD/'real-electron-flow.mjs'):raise SystemExit('RUNNER_CHANGED')
old=(OLD/'choose-owned-folder.ps1').read_bytes().decode('utf-8')
new=(ROOT/'choose-owned-folder.ps1').read_bytes().decode('utf-8')
start='function Project-TreeDiagnostic(';end='# These functions are pure string/evidence predicates.'
a=new.index(start);z=new.index(end,a);oa=old.index(start);oz=old.index(end,oa)
reverse=new[:a]+old[oa:oz]+new[z:]
reverse=reverse.replace('Project-TreeDiagnostic $element 0 $coreId','Project-TreeDiagnostic $element 0')
reverse=reverse.replace('Project-TreeDiagnostic $selected[$i] $i $coreId','Project-TreeDiagnostic $selected[$i] $i')
if reverse.encode('utf-8')!=(OLD/'choose-owned-folder.ps1').read_bytes():raise SystemExit('NOT_OWNER_PROJECTOR_ONLY_BYTE_REVERSAL')
(ROOT/'helper.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='blocked-direct03/helper',tofile='owner-fixed04/helper')),encoding='utf-8')
p=ROOT/'scope.template.json';s=json.loads(p.read_text(encoding='utf-8'))
if s['status']!='NOT_RUN_TEMPLATE_REQUIRES_ROOT_REVIEW_AND_SUPERVISION':raise SystemExit('EXECUTION_SCOPE_NOT_EDITABLE')
s['harness']={'runner_sha256':h(ROOT/'real-electron-flow.mjs'),'folder_helper_sha256':h(ROOT/'choose-owned-folder.ps1')}
s['playwright']['inventory_path']=str(ROOT/'SDK_INVENTORY.json')
p.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
files=[row(p) for p in sorted(ROOT.rglob('*')) if p.is_file()]
write('MANIFEST.json',{'schema':'researchos.direct-owner-order04.manifest/1','files':files})
write('FROZEN.json',{'schema':'researchos.direct-owner-order04.freeze/1','status':'SOURCE_FIX_NOT_RUN_PENDING_REVIEW','frozen_at':datetime.now(timezone.utc).isoformat(),'construction_frozen':True,'source_modification_permitted':False,'manifest_sha256':h(ROOT/'MANIFEST.json'),'scope_sha256':h(p),'source_sha256':{n:h(ROOT/n) for n in ['real-electron-flow.mjs','choose-owned-folder.ps1']},'baseline_sha256':h(ROOT/'BASELINE.json'),'prior_P2_and_raw_preserved':True,'runner_unchanged':True,'reverse_projector_and_two_calls_byte_exact':True,'new_checks':{'owner_order_pure':3,'helper_ast_syntax_exit':0},'old_suites_not_rerun':True,'runner':0,'helper_entrypoint':0,'sdk':0,'add_type':0,'uia':0,'gui':0,'model':0,'formal_increment':0,'product_increment':0,'counter_reset':False,'pending':['Independent narrow owner-order review','Root fresh diagnostic scope/exact outer Job','Actual UIA/provider still NOT_RUN']})
files=[row(p) for p in sorted(ROOT.rglob('*')) if p.is_file()]
write('ARCHIVE_FILES.json',{'root':str(ROOT),'files':files,'file_count':len(files),'total_bytes':sum(r['bytes'] for r in files),'excluded':['none; no SDK/cache/build copy']})
print(json.dumps({'status':'DIRECT04_OWNER_ORDER_FROZEN_NOT_RUN','freeze_sha256':h(ROOT/'FROZEN.json'),'manifest_sha256':h(ROOT/'MANIFEST.json'),'archive_sha256':h(ROOT/'ARCHIVE_FILES.json'),'scope_sha256':h(p),'source_sha256':{n:h(ROOT/n) for n in ['real-electron-flow.mjs','choose-owned-folder.ps1']},'files':len(files),'bytes':sum(r['bytes'] for r in files)}))
