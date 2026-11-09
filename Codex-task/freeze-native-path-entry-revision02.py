from pathlib import Path
from datetime import datetime,timezone
import json,hashlib

cwd=Path(__file__).resolve().parent
root=cwd/'product-v1-native-path-entry-prepare-02'
old=cwd/'product-v1-native-path-entry-prepare-01'
def sha(file):return hashlib.sha256(file.read_bytes()).hexdigest()
def write(name,value):
    with (root/name).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
assert not (root/'FROZEN.json').exists()
assert (root/'real-electron-flow.mjs').read_bytes()==(old/'real-electron-flow.mjs').read_bytes()
scope=json.loads((root/'scope.template.json').read_text(encoding='utf-8'))
assert scope['harness']['folder_helper_sha256']==sha(root/'choose-owned-folder.ps1')
write('CHECKS.json',{'schema':'researchos.native-path-entry-deadline02-checks/1',
 'status':'NEW_DEADLINE_PURE_AND_HELPER_AST_PASS_ACTUAL_NOT_RUN',
 'new_check':{'exit_code':0,'helper_ast':'PASS','cases':['action_before_deadline','action_equal_deadline',
 'rediscovery_crossed_action_deadline','cleanup_uses_independent_later_deadline','cleanup_expired_no_message']},
 'inherited_checks_path':str(old/'CHECKS.json'),'inherited_checks_sha256':sha(old/'CHECKS.json'),
 'inherited_pure_cases_not_rerun':23,'node_runner_byte_exact_to_frozen01':True,
 'safe_command':"& 'C:/Users/yqyyds/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe' -NoLogo -NoProfile -NonInteractive -File 'C:/Users/yqyyds/Documents/Codex/2026-11-04/task/native-path-entry-deadline02-purechecks.ps1'",
 'run_function':0,'runner_import':0,'helper_entrypoint':0,'gui':0,'app':0,'cli':0,'task':0,'model':0})
write('BASELINE.json',{'schema':'researchos.native-path-entry-deadline02-baseline/1','baseline':str(old),
 'baseline_manifest_sha256':sha(old/'MANIFEST.json'),'baseline_frozen_sha256':sha(old/'FROZEN.json'),
 'baseline_helper_sha256':sha(old/'choose-owned-folder.ps1'),'runner_byte_exact':True,
 'scope_change':'Only helper pin and NOT_RUN status label; build07/source/contract/Job policies unchanged',
 'authorized_change':'Root directed new02 final pure UTC guard before SetText and PostMessage, cleanup independent deadline',
 'frozen01_not_modified':True,'root_declined_running01':True})
external=[cwd/'prepare-native-path-entry-revision02.py',cwd/'native-path-entry-deadline02-purechecks.ps1',Path(__file__)]
files=[{'path':file.name,'bytes':file.stat().st_size,'sha256':sha(file)} for file in sorted(root.iterdir()) if file.is_file()]
write('MANIFEST.json',{'schema':'researchos.native-path-entry-deadline02-manifest/1','status':'C_ONLY_NOT_RUN_PENDING_FINAL_REVIEW',
 'files':files,'external_support':[{'path':str(file),'sha256':sha(file)} for file in external],
 'actual_runtime':'NOT_RUN','source_modification_permitted':False})
write('FROZEN.json',{'schema':'researchos.native-path-entry-deadline02-freeze/1','status':'FROZEN_NEW_DEADLINE_PURE_AST_PASS_REAL_FLOW_NOT_RUN',
 'frozen_at':datetime.now(timezone.utc).isoformat(),'construction_frozen':True,'source_modification_permitted':False,
 'manifest_sha256':sha(root/'MANIFEST.json'),'scope_template_sha256':sha(root/'scope.template.json'),
 'runner_sha256':sha(root/'real-electron-flow.mjs'),'helper_sha256':sha(root/'choose-owned-folder.ps1'),
 'new_pure_cases':5,'helper_ast':'PASS','inherited_pure_cases_not_rerun':23,
 'run_function':0,'runner_import':0,'helper_entrypoint':0,'app':0,'gui':0,'cli':0,'model':0,'task':0,'formal_increment':0,'product_increment':0,
 'pending':['Independent reviewer confirms narrow final deadline fix','Fresh Root scope nonce/hash/runroot and original Job pins','Actual UI/Native/Main binding NOT_RUN']})
print(json.dumps(json.loads((root/'FROZEN.json').read_text(encoding='utf-8')),ensure_ascii=False))
