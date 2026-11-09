from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,difflib

cwd=Path(__file__).resolve().parent
root=cwd/'product-v1-native-path-entry-prepare-05'
old=cwd/'product-v1-native-path-entry-prepare-04'
def sha(file):return hashlib.sha256(file.read_bytes()).hexdigest()
def write(name,value):
    with (root/name).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
assert not (root/'FROZEN.json').exists()
checks=json.loads((root/'CHECKS.json').read_text(encoding='utf-8'))
assert all(item['exit_code']==0 for item in checks['checks'])
scope=json.loads((root/'scope.template.json').read_text(encoding='utf-8'))
selector=scope['native_picker']['validation_warning']['dismiss_selector']
evidence=Path(selector['evidence_path'])
assert selector['expected_control_id']==2 and selector['expected_button_count']==1
assert selector['evidence_event']=='WARNING_IDOK_CHILD_METADATA' and selector['evidence_event_sequence']==36
assert sha(evidence)==selector['evidence_sha256']=='392cd6f17926114f890b74dc28952dc1696d4b20a3444dfd2821b52ddb826423'
actual=json.loads(evidence.read_text(encoding='utf-8'));reply=json.loads(actual['stdout'])
events=[event for event in reply['history'] if event['sequence']==36 and event['event']=='WARNING_IDOK_CHILD_METADATA']
assert actual['exit']==2 and reply['status']=='BLOCKED' and len(events)==1
metadata=events[0]['evidence'];buttons=[row for row in metadata['rows'] if row['class_name']=='Button']
assert len(metadata['rows'])==3 and not metadata['truncated'] and metadata['enumeration_error'] is None
assert len(buttons)==1 and buttons[0]['control_id']==2 and buttons[0]['is_child'] and buttons[0]['visible'] and buttons[0]['enabled']
scope['harness']={'runner_sha256':sha(root/'real-electron-flow.mjs'),'folder_helper_sha256':sha(root/'choose-owned-folder.ps1')}
(root/'scope.template.json').write_text(json.dumps(scope,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for name in ['choose-owned-folder.ps1','real-electron-flow.mjs']:
    (root/('helper.diff' if name.endswith('.ps1') else 'runner.diff')).write_text(''.join(difflib.unified_diff((old/name).read_text(encoding='utf-8').splitlines(True),(root/name).read_text(encoding='utf-8').splitlines(True),fromfile='freeze04/'+name,tofile='revision05/'+name)),encoding='utf-8')
write('BASELINE.json',{'schema':'researchos.native-path-entry-dismiss05-baseline/1','baseline':str(old),
 'baseline_manifest_sha256':sha(old/'MANIFEST.json'),'baseline_frozen_sha256':sha(old/'FROZEN.json'),
 'baseline_runner_sha256':sha(old/'real-electron-flow.mjs'),'baseline_helper_sha256':sha(old/'choose-owned-folder.ps1'),
 'inherited_pure_cases_not_rerun':66,'build07_source_bundle_contract_pins_unchanged':True,
 'selector_evidence':selector,'selector_evidence_semantics':{'observed_rows':3,'actual_Button_count':1,'actual_Button_control_id':2,'other_controls':'Static20 and Static65535','prior_direct_ID1_lookup':0},
 'message_box_return_IDOK_is_child_control_id':False,'actual03_status':'FAILED_UNCHANGED_NOT_RELABELED',
 'authorized_change':'Root directed fixed owned MB_OK warning single actual Button expected control ID2 with exact runtime metadata evidence pin; no fallback; chooser direct IDs unchanged'})
files=[{'path':file.name,'bytes':file.stat().st_size,'sha256':sha(file)} for file in sorted(root.iterdir()) if file.is_file()]
external=[cwd/'prepare-native-path-entry-revision05.py',Path(__file__)]
write('MANIFEST.json',{'schema':'researchos.native-path-entry-dismiss05-manifest/1','status':'C_ONLY_NOT_RUN_PENDING_FROZEN_SOURCE_REVIEW',
 'files':files,'selector_evidence_input':{'path':str(evidence),'sha256':sha(evidence)},
 'external_support':[{'path':str(file),'sha256':sha(file)} for file in external],
 'actual_revision05_runtime':'NOT_RUN','source_modification_permitted':False})
write('FROZEN.json',{'schema':'researchos.native-path-entry-dismiss05-freeze/1','status':'FROZEN_NEW_PURE_SYNTAX_PASS_REAL_FLOW_NOT_RUN',
 'frozen_at':datetime.now(timezone.utc).isoformat(),'construction_frozen':True,'source_modification_permitted':False,
 'manifest_sha256':sha(root/'MANIFEST.json'),'scope_template_sha256':sha(root/'scope.template.json'),
 **scope['harness'],'new_helper_selector_evidence_pure_cases':13,'new_node_scope_pin_pure_cases':7,
 'helper_ast':'PASS','node_syntax':'PASS','inherited_pure_cases_not_rerun':66,
 'selector_expected_control_id':2,'selector_expected_button_count':1,'selector_evidence_sha256':sha(evidence),
 'runner_import':0,'run_function':0,'helper_entrypoint':0,'app':0,'gui':0,'win32_calls':0,'cli':0,'model':0,'task':0,'formal_increment':0,'product_increment':0,
 'pending':['Independent frozen source boundary review','Fresh Root scope04 nonce/hash/runroot and original Job pins including selector evidence outer input','Actual revision05 Native/Main binding NOT_RUN']})
print(json.dumps(json.loads((root/'FROZEN.json').read_text(encoding='utf-8')),ensure_ascii=False))
