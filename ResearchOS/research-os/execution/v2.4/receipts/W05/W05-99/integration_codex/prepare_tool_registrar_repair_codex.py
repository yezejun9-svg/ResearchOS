"""Keep the executed registrar intact; retain its real interface failure and repair a copy."""
from pathlib import Path
import datetime as dt
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
old = HERE/'register_additional_slice_codex.py'
digest = hashlib.sha256(old.read_bytes()).hexdigest()
assert digest == '8fdf09eb67544a06a71592b537c798f44c035ce26bca2b6e3d8aa82867c5f928'
failure = {
    'schema': 'researchos.w05.root-registration-failure.v1',
    'observed_at': dt.datetime.now(dt.timezone.utc).isoformat(),
    'observer': 'codex:/root',
    'command': ['C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe','-B','-X','utf8',
        'execution/v2.4/receipts/W05/W05-99/integration_codex/register_additional_slice_codex.py',
        '--slice','tools','--expected-revision','222','--expected-path-revision','55',
        '--review-sha256','329e0c6f2646044dc739b7b4f97f0a98c2a54e4c4660a0b7c47edcba1ebdbb05'],
    'exit_code': 1, 'tool_chunk_id': '77f5dc', 'tool_wall_time_seconds': 0.68955,
    'merged_tool_output': 'Traceback (most recent call last):\n  File "D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W05\\W05-99\\integration_codex\\register_additional_slice_codex.py", line 39, in <module>\n    assert review[\'approved_exact_paths\'] == proposal[\'exact_paths\']\n           ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^\nKeyError: \'approved_exact_paths\'\n',
    'timing_limit': 'The tool supplied elapsed time and output; exact process start/end times and separate raw stderr bytes were not captured.',
    'failed_source_ref': {'path':old.relative_to(ROOT).as_posix(),'sha256':digest},
    'failure_class': 'ROOT_REGISTRAR_REVIEW_SHAPE_NOT_PRODUCT',
    'state_mutation_before_failure': False, 'product_calls':0, 'product_failure_count_delta':0,
    'reason': 'The Goal scope schema used approved_exact_paths, while the signed Tool scope schema used exact_paths; the original registrar assumed the Goal field name.',
    'follow_on_stage_failure': {'tool_chunk_id':'2389c7','detail':'Explicit git add named the not-yet-created tool_source_scope_codex.json and refused before staging. No production or checkpoint writes from this command.'},
    'repair_failure': {'tool_chunk_id':'eaf959','exit_code':1,'tool_wall_time_seconds':0.6079262,
        'cause':'NameError: name datetime is not defined; imported as dt.',
        'failed_source_path':'execution/v2.4/receipts/W05/W05-99/integration_codex/prepare_tool_registrar_repair_attempt1_source.py',
        'failed_source_sha256':hashlib.sha256((HERE/'prepare_tool_registrar_repair_attempt1_source.py').read_bytes()).hexdigest(),
        'follow_on_missing_child_chunk':'fe0e05','no_file_or_checkpoint_writes':True},
}
failure_path = HERE/'tool_registration_failure_codex.json'
with failure_path.open('x',encoding='utf8',newline='\n') as stream:
    json.dump(failure,stream,ensure_ascii=False,indent=2);stream.write('\n')
source = old.read_text(encoding='utf8')
source = source.replace("assert review['approved_exact_paths'] == proposal['exact_paths']", "assert args.slice == 'tools'\nassert review['exact_paths'] == proposal['exact_paths']")
needle = "scope_path = HERE / (kind + '_source_scope_codex.json')"
replacement = """failure_path = HERE / 'tool_registration_failure_codex.json'
failure_record = load(failure_path)
cp['failure_counters'].append({'origin_key':'W05-root-tools-scope-REVIEW_FIELD_SHAPE', 'attempts':1,
    'candidate_id':proposal['source_head'], 'input_hash':failure_record['failed_source_ref']['sha256'],
    'status':'RECORDED_WITH_CHANGED_REGISTRAR_INPUT', 'classification':'ROOT_REGISTRAR_INTERFACE_FAILURE_NOT_PRODUCT',
    'evidence':ref(failure_path), 'failed_script':failure_record['failed_source_ref'], 'product_failure_count_delta':0,
    'detail':'Actual tools scope registration failed before writes on exact_paths versus approved_exact_paths. The original script is retained; this exact reviewed tools registrar uses its signed schema field.'})
cp['failure_counters'].append({'origin_key':'W05-root-tools-scope-REPAIR_SCRIPT_DATETIME_ALIAS','attempts':1,
    'candidate_id':proposal['source_head'],'input_hash':failure_record['repair_failure']['failed_source_sha256'],
    'status':'RECORDED_WITH_CHANGED_REPAIR_INPUT','classification':'ROOT_REGISTRAR_INTERFACE_FAILURE_NOT_PRODUCT',
    'evidence':ref(failure_path),'failed_script':{'path':failure_record['repair_failure']['failed_source_path'],'sha256':failure_record['repair_failure']['failed_source_sha256']},
    'product_failure_count_delta':0,'detail':'Repair preparation failed before writes on a Python import alias. Failed source retained; current preparation uses the actual dt binding. Missing dependent child is retained under this same cause.'})
scope_path = HERE / (kind + '_source_scope_codex.json')"""
assert source.count(needle)==1
source = source.replace(needle,replacement)
source = source.replace("after['failure_counters'] == old_cp['failure_counters']", "after['failure_counters'][:-2] == old_cp['failure_counters'] and len(after['failure_counters']) == 86")
with (HERE/'register_tools_slice_codex.py').open('x',encoding='utf8',newline='\n') as stream: stream.write(source)
print(json.dumps({'status':'CHANGED_REGISTRAR_PREPARED','old_source_preserved':True,
    'failure_ref':{'path':failure_path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(failure_path.read_bytes()).hexdigest()}}))
