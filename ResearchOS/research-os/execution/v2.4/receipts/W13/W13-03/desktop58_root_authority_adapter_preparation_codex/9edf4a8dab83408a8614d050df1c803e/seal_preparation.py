"""Seal own source-preparation evidence only; no candidate imports or execution."""
import ast,hashlib,json
from pathlib import Path
OUT=Path(__file__).parent
PY='C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe'
def pin(p):
    p=Path(p);b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(n,o):
    with (OUT/n).open('xb') as f:f.write((json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode())
error1='  File "<string>", line 1\n    import json;from pathlib import Path;q=json.loads(Path(\'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/cli43_successful_execution_independent_review_codex/6f07498ca19a49c7866b9e528d401aa0/qualification.json\').read_bytes());out={};exec(\'for k in [\\\n                                                                                                                                                                                                                                                                 ^\nSyntaxError: unterminated string literal (detected at line 1)\n'
error2='Traceback (most recent call last):\n  File "D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W13\\W13-03\\desktop58_root_authority_adapter_preparation_codex\\9edf4a8dab83408a8614d050df1c803e\\prepare_source.py", line 81, in <module>\n    assert oldreturn in grant\n           ^^^^^^^^^^^^^^^^^^\nAssertionError\n'
save('tool-result.d7ff58.json',{'chunk_id':'d7ff58','wall_time_seconds':0.643071,'exit_code':1,'original_token_count':157,'output':error1,'capture_kind':'visible_original_exec_command_result_fields; no separate native shell variable or OS argv capture'})
save('tool-result.533afb.json',{'chunk_id':'533afb','wall_time_seconds':0.7909354,'exit_code':1,'original_token_count':80,'output':error2,'capture_kind':'visible_original_exec_command_result_fields; no separate native shell variable'})
save('failure-origin.d7ff58.json',{
 'origin':'d7ff58','phase':'readonly metadata shape display','actual_outer_exit':1,'actual_native_exit':None,
 'original_tool':'functions.exec -> tools.exec_command','tool_result_ref':pin(OUT/'tool-result.d7ff58.json'),
 'input_known':{'cwd':'D:/作品集/ResearchOS','shell':'powershell','program':PY,'flags':['-I','-S','-X','utf8','-c'],
   'target':'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/cli43_successful_execution_independent_review_codex/6f07498ca19a49c7866b9e528d401aa0/qualification.json',
   'operation':'display selected existing evidence JSON shapes through nested exec string; escaped quotes were passed incorrectly'},
 'actual_OS_argv':None,'stderr_stream_separately_captured':False,
 'cause':'PowerShell/Python nested -c string SyntaxError; not a candidate or product failure',
 'same_input_retried':False,'candidate_Go_SQL_Node_DLL_HTTP_calls':0,'counter_reset':False})
save('failure-origin.533afb.json',{
 'origin':'533afb','phase':'pure IO candidate construction before first candidate write','actual_outer_exit':1,'actual_native_exit':None,
 'original_tool':'functions.exec -> tools.exec_command','tool_result_ref':pin(OUT/'tool-result.533afb.json'),
 'argv_request':[PY,'-I','-S','-X','utf8',str(OUT/'prepare_source.py')],'original_script_ref':pin(OUT/'prepare_source.py'),
 'cause':'Constructor expected CRLF inside grant return; actual frozen base has0CRLF/441LF. Assertion stopped before source write.',
 'actual_OS_argv':None,'stderr_stream_separately_captured':False,'same_input_retried':False,
 'new_input_correction_ref':pin(OUT/'constructor-v2-delta.json'),'candidate_Go_SQL_Node_DLL_HTTP_calls':0,'counter_reset':False})
success=[('26847a',0),('88a93e',0),('983652',0),('6c8a01',0),('4896fc',0),('e03079',0),('068792',0),('14f72f',0),('013729',0),('20daca',0),('b3891a',0),('354af9',0)]
save('tool-observations.json',{'successful_read_or_AST_IO_tools':[{'tool':x,'actual_outer_exit':v,'actual_native_exit':None} for x,v in success],
 'failed_tools':['d7ff58','533afb'],'candidate_or_product_execution':0,'native_values_not_inferred_from_outer':True,
 'note':'Underlying exec_command original tool refs remain authoritative; output JSON contains visible field transcripts, not invented per-process native captures.'})
inputs=json.loads((OUT/'inputs.final.before.json').read_bytes())
after=[pin(x['path']) for x in inputs]
assert inputs==after
save('inputs.sealed.after.json',after)
parsed=[]
for p in sorted(OUT.iterdir()):
    if p.suffix=='.py' or p.name=='extensions.proposed.py.txt':
        ast.parse(p.read_bytes());parsed.append(pin(p))
inv=json.loads((OUT/'whole-inverse.final.json').read_bytes())
assert hashlib.sha256(inv['old'].encode()).hexdigest()==inv['baseline_ref']['sha256']
assert inv['new'].encode()==Path(inv['candidate_ref']['path']).read_bytes()
scope=json.loads((OUT/'scope.final.proposed.json').read_bytes())
assert scope['preparation_only'] is True and scope['execution_authorized'] is False
for k in ['expected_registration','current58_CLI2_qualification_ref','resource_catalog_ref','source_catalog_ref','inner_seconds','outer_seconds']:
    assert scope[k] is None
save('seal-static-audit.json',{'AST_files':parsed,'AST_failed':0,'imports_or_candidate_executions':0,'whole_inverse_exact':True,
    'source_input_count':len(inputs),'source_input_drift':0,'same_original_controller_launcher':True,
    'future_refs_and_budgets_remain_NULL':True,'new_failure_origin_count':2,'source_ready_self_signed':False})
save('handoff.json',{
 'schema':'researchos.desktop58-root-authority-adapter-source-handoff.v1','author':'codex:/root/command_queue_impl','state':'STOPPED',
 'decision':'SOURCE_PREPARATION_REPORTED_PENDING_NONAUTHOR_REVIEW','source_acceptance':False,'execution_authorized':False,
 'adapter_ref':pin(OUT/'authorization_adapter.final.proposed.py'),'scope_proposal_ref':pin(OUT/'scope.final.proposed.json'),
 'contract_ref':pin(OUT/'contract.json'),'whole_inverse_ref':pin(OUT/'whole-inverse.final.json'),'static_ref':pin(OUT/'seal-static-audit.json'),
 'unchanged_consumers':{'controller_ref':scope['controller_ref'],'launcher_ref':scope['launcher_ref'],'byte_delta':0},
 'interface':'validate_grant(scope_path, scope_sha256, grant_path, grant_sha256): pure read/hash/JSON only; existing Desktop ABI unchanged.',
 'implemented':'Same-head closed CLI2 prerequisite, actual sealed registration/CAS four copies and failure prefix, exact reviewed fullscope and proposed WIP/lease, reused current58 source/forward history, fixed169+Go3 roster/alias/caps and Root explicit resources/IO budgets. No registration/grant producer or execution framework added.',
 'proposed_contract_not_existing_authority':'Desktop WIP/lease/review/grant schemas and resource union layout are explicit proposals. Actual Root adoption, current58 qualifier/resources, fullscope review, CAS seal/grant remain absent; NULL rejects. Unknown future qualifier schema also rejects; old a510 r331 is only a wire-schema example.',
 'limitations':['R333 source-head closure is historical source evidence, not fresh CLI/Desktop qualification.','Current58 CLI2 independent qualification is not yet available to this preparation; old43 cannot satisfy the gate.','The adapter validates and pairs evidence, and relies on exact pinned nonauthor qualification adjudication for detailed original fixture/OS proof. It is not an independent rerun or cryptographic tool-event attestation.','All actual compiler/resource/Root budget/registration bindings need independent review. No permission to install/show visible GUI, call SDK/model or accept formal cases.','Pure metadata source syntax/inverse checks are not runtime gate tests.'],
 'future_controls_ref':pin(OUT/'future-controls.NOT_RUN.json'),'future_cases':'169 Node + separate Go3 NOT_RUN;2 hidden/offscreen renderer controls included; installed/visible GUI0/SDK0/model0',
 'new_failure_origins':[pin(OUT/'failure-origin.d7ff58.json'),pin(OUT/'failure-origin.533afb.json')],
 'original_failures_preserved':True,'canonical_writes':0,'product_writes':0,'candidate_import_Go_SQL_Node_DLL_Job_HTTP_model_calls':0,
 'inputs_before_ref':pin(OUT/'inputs.final.before.json'),'inputs_after_ref':pin(OUT/'inputs.sealed.after.json'),
 'manifest_relative_path':'manifest.json'})
files=[pin(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='manifest.json']
save('manifest.json',{'schema':'researchos.source-preparation-manifest.v1','count':len(files),'entries':files,'self_excluded':True,'all_members_in_own_namespace':True})
print(json.dumps({'handoff':pin(OUT/'handoff.json'),'manifest':pin(OUT/'manifest.json'),'adapter':pin(OUT/'authorization_adapter.final.proposed.py'),'new_origins':[pin(OUT/'failure-origin.d7ff58.json'),pin(OUT/'failure-origin.533afb.json')],'listed':len(files)},ensure_ascii=False))
