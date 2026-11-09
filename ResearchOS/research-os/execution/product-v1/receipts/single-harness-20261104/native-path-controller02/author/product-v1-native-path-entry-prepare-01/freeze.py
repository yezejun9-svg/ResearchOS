from pathlib import Path
from datetime import datetime, timezone
import json, hashlib

root=Path(__file__).resolve().parent
def sha(file):return hashlib.sha256(file.read_bytes()).hexdigest()
def write(name,value):
    with (root/name).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
if (root/'FROZEN.json').exists():raise SystemExit('ALREADY_FROZEN_NO_OVERWRITE')
scope=json.loads((root/'scope.template.json').read_text(encoding='utf-8'))
checks=json.loads((root/'CHECKS.json').read_text(encoding='utf-8'))
assert scope['budget']=={'task_submissions':0,'model_calls':0,'automatic_retries':0,'harness_id':'codex'}
assert scope['scope_nonce'] is None and scope['status'].startswith('NOT_RUN_')
assert scope['harness']['runner_sha256']==sha(root/'real-electron-flow.mjs')
assert scope['harness']['folder_helper_sha256']==sha(root/'choose-owned-folder.ps1')
assert scope['bundle']['manifest_sha256']=='ba4fbefa07e1ba9597ee54c894949edb5d33847e38b10d3f53ee8704d84fd6e7'
assert all(row['exit_code']==0 for row in checks['checks'])
assert not any(row['path'].startswith('execution/') for row in scope['source']['pins'])
base=root.parent/'product-v1-real-electron-tree-diagnostic-revision-05'
write('BASELINE.json',{'schema':'researchos.native-path-entry-baseline/1','baseline':str(base),
 'runner_sha256':sha(base/'real-electron-flow.mjs'),'helper_sha256':sha(base/'choose-owned-folder.ps1'),
 'source_head':scope['source']['head'],'source_native_sha256':scope['native_picker']['validation_warning']['source_sha256'],
 'bundle':scope['bundle'],'reuse':'R5 owner-first/strictUTC/env/cwd/normalpwsh/originalJob; R4 React real entry; SDK111 reference unchanged',
 'not_reused':'Old tree selector/provider and every task/model branch removed',
 'main_observation':'Existing readonly bridges; not original chooseWorkspace Promise',
 'researchos_cli_repeated':False,'app':0,'gui':0,'model':0,'task':0})
files=[{'path':file.name,'bytes':file.stat().st_size,'sha256':sha(file)} for file in sorted(root.iterdir()) if file.is_file() and file.name not in ('MANIFEST.json','FROZEN.json')]
write('MANIFEST.json',{'schema':'researchos.native-path-entry-source-manifest/1','status':'C_ONLY_NOT_RUN_PENDING_INDEPENDENT_REVIEW',
 'files':files,'file_count':len(files),'source_modification_permitted':False,'actual_runtime':'NOT_RUN'})
write('FROZEN.json',{'schema':'researchos.native-path-entry-freeze/1','status':'FROZEN_PURE_SYNTAX_PASS_REAL_FLOW_NOT_RUN',
 'frozen_at':datetime.now(timezone.utc).isoformat(),'construction_frozen':True,'source_modification_permitted':False,
 'manifest_sha256':sha(root/'MANIFEST.json'),'scope_template_sha256':sha(root/'scope.template.json'),
 'runner_sha256':sha(root/'real-electron-flow.mjs'),'helper_sha256':sha(root/'choose-owned-folder.ps1'),
 'node_syntax':'PASS','helper_ast':'PASS','new_runner_pure_cases':14,'new_helper_pure_cases':9,
 'runner_import':0,'run_function':0,'helper_entrypoint':0,'app':0,'gui':0,'researchos_cli':0,'model':0,'task':0,
 'formal_increment':0,'product_increment':0,
 'pending':['Independent frozen candidate review','Fresh Root-approved scope nonce/hash/runroot','Root f13 original unnamed Job controller/launch-contract pins and final accounting','Actual invalid/valid Native UI and Main binding NOT_RUN']})
print(json.dumps(json.loads((root/'FROZEN.json').read_text(encoding='utf-8')),ensure_ascii=False))
