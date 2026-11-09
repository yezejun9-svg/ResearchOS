from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,re

cwd=Path(__file__).resolve().parent
root=cwd/'product-v1-native-path-entry-prepare-04'
old=cwd/'product-v1-native-path-entry-prepare-03'
actual=cwd/'product-v1-native-path-entry-中文-run-02/receipts'
def sha(file):return hashlib.sha256(file.read_bytes()).hexdigest()
def write(name,value):
    with (root/name).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
assert not (root/'FROZEN.json').exists()
assert (root/'real-electron-flow.mjs').read_bytes()==(old/'real-electron-flow.mjs').read_bytes()
scope=json.loads((root/'scope.template.json').read_text(encoding='utf-8'))
assert scope['harness']['runner_sha256']==sha(root/'real-electron-flow.mjs')
assert scope['harness']['folder_helper_sha256']==sha(root/'choose-owned-folder.ps1')
test=(root/'warning-idok-purechecks.ps1').read_text(encoding='utf-8')
cases=[]
for match in re.finditer(r"(?:\$passed\.Add\('([^']+)'\)|Expect-Code '([^']+)')",test):cases.append(match.group(1) or match.group(2))
assert len(cases)==17
write('CHECKS.json',{'schema':'researchos.native-path-entry-warning04-checks/1','status':'NEW_IDENTITY_SELECTOR_PURE_AST_PASS_RUNTIME_NOT_RUN',
 'new_check':{'exit_code':0,'helper_ast':'PASS','pure_cases':cases},
 'inherited_checks_path':str(old/'CHECKS.json'),'inherited_checks_sha256':sha(old/'CHECKS.json'),
 'inherited_pure_cases_not_rerun':49,'runner_byte_exact_to_frozen03':True,'node_syntax':'INHERITED_PASS_BYTE_EXACT_RUNNER_NOT_RERUN',
 'safe_command':"& 'C:/Users/yqyyds/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe' -NoLogo -NoProfile -NonInteractive -File 'C:/Users/yqyyds/Documents/Codex/2026-11-04/task/product-v1-native-path-entry-prepare-04/warning-idok-purechecks.ps1'",
 'runner_import':0,'run_function':0,'helper_entrypoint':0,'dynamic_csharp_compile':0,'gui':0,'app':0,'win32_calls':0,'cli':0,'task':0,'model':0})
record=json.loads((actual/'native-folder-automation.json').read_text(encoding='utf-8'))
reply=json.loads(record['stdout'])
assert record['exit']==2 and reply['status']=='BLOCKED' and reply['reason']=='FOREIGN_WINDOW_PID'
assert reply['invalid_ok_attempted'] is True and reply['valid_ok_attempted'] is False and reply['outcome_uncertain'] is False
assert reply['invalid_warning']['observed'] is True
write('BASELINE.json',{'schema':'researchos.native-path-entry-warning04-baseline/1','baseline':str(old),
 'baseline_manifest_sha256':sha(old/'MANIFEST.json'),'baseline_frozen_sha256':sha(old/'FROZEN.json'),
 'baseline_runner_sha256':sha(old/'real-electron-flow.mjs'),'baseline_helper_sha256':sha(old/'choose-owned-folder.ps1'),
 'runner_byte_exact':True,'inherited_pure_cases_not_rerun':49,'build07_source_bundle_contract_pins_unchanged':True,
 'actual02_original_wrapper':{'path':str(actual/'native-folder-automation.json'),'sha256':sha(actual/'native-folder-automation.json')},
 'actual02_original_stdout':{'path':str(actual/'native-helper-stdout-prefix.bin'),'sha256':sha(actual/'native-helper-stdout-prefix.bin')},
 'actual02_status':'FAILED_UNCHANGED_NOT_RELABELED','actual02_observed':'Invalid path exact; INVALID_OK posted; exact owned warning verified; no warning-dismiss post; no valid OK',
 'actual02_unrecorded_lookup_hwnd':'UNKNOWN_ZERO_OR_NESTING_OR_FOREIGN_NOT_PROVEN',
 'authorized_change':'Root directed warning-only bounded actual IDOK discovery; chooser strict direct guards and all effect/authority/deadline gates retained'})
files=[{'path':file.name,'bytes':file.stat().st_size,'sha256':sha(file)} for file in sorted(root.iterdir()) if file.is_file()]
external=[cwd/'prepare-native-path-entry-revision04.py',Path(__file__)]
write('MANIFEST.json',{'schema':'researchos.native-path-entry-warning04-manifest/1','status':'C_ONLY_NOT_RUN_PENDING_FROZEN_SOURCE_REVIEW',
 'files':files,'external_support':[{'path':str(file),'sha256':sha(file)} for file in external],
 'actual_revision04_runtime':'NOT_RUN','source_modification_permitted':False})
write('FROZEN.json',{'schema':'researchos.native-path-entry-warning04-freeze/1','status':'FROZEN_NEW_PURE_AST_PASS_REAL_FLOW_NOT_RUN',
 'frozen_at':datetime.now(timezone.utc).isoformat(),'construction_frozen':True,'source_modification_permitted':False,
 'manifest_sha256':sha(root/'MANIFEST.json'),'scope_template_sha256':sha(root/'scope.template.json'),
 **scope['harness'],'new_identity_selector_pure_cases':17,'helper_ast':'PASS','runner_byte_exact_to_frozen03':True,
 'inherited_node_syntax':'PASS_NOT_RERUN','inherited_pure_cases_not_rerun':49,
 'runner_import':0,'run_function':0,'helper_entrypoint':0,'app':0,'gui':0,'win32_calls':0,'cli':0,'model':0,'task':0,'formal_increment':0,'product_increment':0,
 'pending':['Independent frozen source boundary review','Fresh Root scope nonce/hash/runroot and original Job pins','Actual revision04 Native/Main binding NOT_RUN']})
print(json.dumps(json.loads((root/'FROZEN.json').read_text(encoding='utf-8')),ensure_ascii=False))
