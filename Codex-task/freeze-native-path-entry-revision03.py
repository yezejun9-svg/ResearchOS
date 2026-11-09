from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,difflib

cwd=Path(__file__).resolve().parent
root=cwd/'product-v1-native-path-entry-prepare-03'
old=cwd/'product-v1-native-path-entry-prepare-02'
actual=cwd/'product-v1-native-path-entry-中文-run-01/receipts'
def sha(file):return hashlib.sha256(file.read_bytes()).hexdigest()
def write(name,value):
    with (root/name).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
assert not (root/'FROZEN.json').exists()
checks=json.loads((root/'CHECKS.json').read_text(encoding='utf-8'))
assert all(item['exit_code']==0 for item in checks['checks'])
scope=json.loads((root/'scope.template.json').read_text(encoding='utf-8'))
scope['harness']={'runner_sha256':sha(root/'real-electron-flow.mjs'),'folder_helper_sha256':sha(root/'choose-owned-folder.ps1')}
(root/'scope.template.json').write_text(json.dumps(scope,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for name in ['choose-owned-folder.ps1','real-electron-flow.mjs']:
    (root/('helper.diff' if name.endswith('.ps1') else 'runner.diff')).write_text(''.join(difflib.unified_diff((old/name).read_text(encoding='utf-8').splitlines(True),(root/name).read_text(encoding='utf-8').splitlines(True),fromfile='freeze02/'+name,tofile='revision03/'+name)),encoding='utf-8')
assert sha(actual/'native-helper-stdout-prefix.bin')=='1ee999c21abe580a336669596078aba99a37d8e3eb9fef9f5885e564f17908b6'
assert sha(actual/'native-folder-automation.json')=='03fac74b38e9e4ab3302e30204fc214ff7a3e9d5b28f372b11146ab7c6283712'
write('BASELINE.json',{'schema':'researchos.native-path-entry-active-parser03-baseline/1','baseline':str(old),
 'baseline_manifest_sha256':sha(old/'MANIFEST.json'),'baseline_frozen_sha256':sha(old/'FROZEN.json'),
 'baseline_runner_sha256':sha(old/'real-electron-flow.mjs'),'baseline_helper_sha256':sha(old/'choose-owned-folder.ps1'),
 'inherited_pure_cases_not_rerun':28,'build07_source_bundle_contract_pins_unchanged':True,
 'actual01_original_stdout':{'path':str(actual/'native-helper-stdout-prefix.bin'),'bytes':(actual/'native-helper-stdout-prefix.bin').stat().st_size,'sha256':sha(actual/'native-helper-stdout-prefix.bin')},
 'actual01_original_wrapper':{'path':str(actual/'native-folder-automation.json'),'sha256':sha(actual/'native-folder-automation.json')},
 'actual01_status':'FAILED_UNCHANGED_NOT_RELABELED','actual01_no_ok_attempts':True,'actual01_outcome_uncertain':False,
 'actual01_path':'JSON decoded single backslash separators; Chinese exact expected scope path',
 'product_foreground_bug':'NOT_ESTABLISHED_NO_THREAD_ACTIVE_SNAPSHOT_FROM_ACTUAL01',
 'authorized_change':'Root authorized same-Core actual dialog TID active/focus guard and known helper BLOCKED parser semantics; no activation or new runtime'})
files=[{'path':file.name,'bytes':file.stat().st_size,'sha256':sha(file)} for file in sorted(root.iterdir()) if file.is_file()]
external=[cwd/'prepare-native-path-entry-revision03.py',Path(__file__)]
write('MANIFEST.json',{'schema':'researchos.native-path-entry-active-parser03-manifest/1','status':'C_ONLY_NOT_RUN_PENDING_FROZEN_SOURCE_REVIEW',
 'files':files,'external_support':[{'path':str(file),'sha256':sha(file)} for file in external],
 'actual_revision03_runtime':'NOT_RUN','source_modification_permitted':False})
write('FROZEN.json',{'schema':'researchos.native-path-entry-active-parser03-freeze/1','status':'FROZEN_NEW_PURE_SYNTAX_PASS_REAL_FLOW_NOT_RUN',
 'frozen_at':datetime.now(timezone.utc).isoformat(),'construction_frozen':True,'source_modification_permitted':False,
 'manifest_sha256':sha(root/'MANIFEST.json'),'scope_template_sha256':sha(root/'scope.template.json'),
 **scope['harness'],'new_active_thread_pure_cases':10,'new_parser_pure_cases':11,
 'node_syntax':'PASS','helper_ast':'PASS','inherited_pure_cases_not_rerun':28,
 'runner_import':0,'run_function':0,'helper_entrypoint':0,'app':0,'gui':0,'win32_calls':0,'cli':0,'model':0,'task':0,'formal_increment':0,'product_increment':0,
 'pending':['Independent frozen source boundary review','Fresh Root scope02 nonce/hash/runroot and original Job pins','Actual revision03 Native/Main binding NOT_RUN']})
print(json.dumps(json.loads((root/'FROZEN.json').read_text(encoding='utf-8')),ensure_ascii=False))
