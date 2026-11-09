"""Freeze only optional managed Legacy branch; no runtime invocation."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,difflib
ROOT=Path(__file__).resolve().parent
OLD=ROOT.with_name('product-v1-real-electron-tree-diagnostic-revision-04')
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
if h(ROOT/'real-electron-flow.mjs')!=h(OLD/'real-electron-flow.mjs'):raise SystemExit('RUNNER_CHANGED')
old=(OLD/'choose-owned-folder.ps1').read_bytes().decode('utf-8');new=(ROOT/'choose-owned-folder.ps1').read_bytes().decode('utf-8')
oa=old.index('      foreach ($provider in @(',old.index('    function Read-PublicPatterns('));oz=old.index('        Assert-DirectNativeTree',oa)
a=new.index('      $providers=',new.index('    function Read-PublicPatterns('));z=new.index('        Assert-DirectNativeTree',a)
reverse=new[:a]+old[oa:oz]+new[z:]
if reverse.encode('utf-8')!=(OLD/'choose-owned-folder.ps1').read_bytes():raise SystemExit('NOT_OPTIONAL_TYPE_BRANCH_ONLY')
(ROOT/'helper.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='direct04/helper',tofile='optionalLegacy05/helper')),encoding='utf-8')
p=ROOT/'scope.template.json';s=json.loads(p.read_text(encoding='utf-8'))
if s['status']!='NOT_RUN_TEMPLATE_REQUIRES_ROOT_REVIEW_AND_SUPERVISION':raise SystemExit('EXECUTION_SCOPE_NOT_EDITABLE')
s['harness']={'runner_sha256':h(ROOT/'real-electron-flow.mjs'),'folder_helper_sha256':h(ROOT/'choose-owned-folder.ps1')}
s['playwright']['inventory_path']=str(ROOT/'SDK_INVENTORY.json')
p.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
files=[row(p) for p in sorted(ROOT.iterdir()) if p.is_file()]
write('MANIFEST.json',{'schema':'researchos.optional-managed-legacy05.manifest/1','files':files})
write('FROZEN.json',{'schema':'researchos.optional-managed-legacy05.freeze/1','status':'SOURCE_FIX_PASSIVE_TYPES_PURE_ONLY_PENDING_REVIEW','frozen_at':datetime.now(timezone.utc).isoformat(),'construction_frozen':True,'source_modification_permitted':False,'manifest_sha256':h(ROOT/'MANIFEST.json'),'scope_sha256':h(p),'source_sha256':{n:h(ROOT/n) for n in ['real-electron-flow.mjs','choose-owned-folder.ps1']},'baseline_sha256':h(ROOT/'BASELINE.json'),'actual05_type_failure_preserved':True,'runner_unchanged':True,'reverse_optional_branch_byte_exact':True,'new_checks':{'managed_type_metadata_exit':0,'missing_legacy_pure':4,'helper_ast_syntax_exit':0},'passive_assembly_loads':{'metadata_process':2,'pure_fake_process':2},'dynamic_csharp_compile':0,'com_objects':0,'uia_element_calls':0,'helper_entrypoint':0,'gui':0,'model':0,'formal_increment':0,'product_increment':0,'counter_reset':False,'old_suites_not_rerun':True,'pending':['Independent narrow optional-type/P2guard review','Root fresh diagnostic scope/exact outer Job','Real Value/Selection reliable path NOT_RUN']})
files=[row(p) for p in sorted(ROOT.iterdir()) if p.is_file()]
write('ARCHIVE_FILES.json',{'root':str(ROOT),'files':files,'file_count':len(files),'total_bytes':sum(r['bytes'] for r in files),'excluded':['none; no SDK/cache/build copy']})
print(json.dumps({'status':'DIRECT05_OPTIONAL_TYPE_FROZEN_NOT_GUI','freeze_sha256':h(ROOT/'FROZEN.json'),'manifest_sha256':h(ROOT/'MANIFEST.json'),'archive_sha256':h(ROOT/'ARCHIVE_FILES.json'),'scope_sha256':h(p),'source_sha256':{n:h(ROOT/n) for n in ['real-electron-flow.mjs','choose-owned-folder.ps1']},'files':len(files),'bytes':sum(r['bytes'] for r in files)}))
