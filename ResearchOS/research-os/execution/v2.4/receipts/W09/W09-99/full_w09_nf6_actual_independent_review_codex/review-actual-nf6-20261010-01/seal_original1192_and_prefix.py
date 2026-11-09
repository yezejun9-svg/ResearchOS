import ast,hashlib,json,sys,traceback
from pathlib import Path
Q=Path(__file__).resolve().parent
def pin(p):
    raw=Path(p).read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(p,v):
    with p.open('xb')as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    return pin(p)
def main():
    result=json.loads((Q/'partial-actual-review-result.json').read_bytes())
    io=json.loads((Q/'original-1e2439.fullIO.reencoded.json').read_bytes())
    cleanup=json.loads((Q/'partial-actual-SourceGuard.closed.json').read_bytes())
    inputs=json.loads((Q/'partial-input-observed.json').read_bytes())
    if result['primary_error']!={'type':'ValueError','message':'STRUCTURED_ACTUAL_ROOT_ARTIFACT_REF_REQUIRED'}:raise ValueError('EXACT_ORIGINAL_REVIEWER_ERROR')
    if io['result']['chunk_id']!='1e2439' or io['result']['exit_code']!=1 or 'ROOT_PYTHON_EXIT=1'not in io['result']['output'].splitlines():raise ValueError('ACTUAL_OBSERVED_ERROR_HOST')
    if not(cleanup['closed'] and cleanup['retained_handles_count']==0 and cleanup['errors']==[] and len(cleanup['entries'])==1931 and all(x['verified'] and x['closed']for x in cleanup['entries'])):raise ValueError('ACTUAL_ORIGINAL_GUARD_CLOSURE')
    failed=Q/'review_partial_actual.py'
    source=failed.read_text(encoding='utf-8');tree=ast.parse(source)
    original=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W09/W09-99/full_w09_nf5_actual_independent_review_codex/review-actual-nf5-20261010-01/review_actual_nf5.v7.py')
    oldsource=original.read_text(encoding='utf-8');oldtree=ast.parse(oldsource)
    function=next(x for x in oldtree.body if isinstance(x,ast.FunctionDef)and x.name=='review_group')
    text=ast.get_source_segment(oldsource,function)
    if "for key in ('W09-G01','W09-G02'):"not in source or '*root_run_pair('not in text:raise ValueError('EXECUTED_G01_LINEAR_PREFIX_LOCATION')
    prefix=save(Q/'G01.original1192-successful-prefix.json',dict(schema='researchos.w09-nf6-actual-review-linear-prefix.v1',actor_id='codex:/root/backup_regression_resources',selector='W09-G01',run_id='9aca6259c1144ee6ba310bee23a4614c',
        status='KNOWN_REVIEWER_EXECUTED_PREFIX_BEFORE_ROOT_ARTIFACT_JOIN',original_ordinal=1192,actual_host_chunk_id='1e2439',outer_exit=1,python_exit=1,
        actual_input_refs=inputs['groups']['W09-G01'],failed_reviewer_program_ref=pin(failed),reused_linear_function_source_ref=pin(original),function_source_lines=[function.lineno,function.end_lineno],
        prefix_inference_basis='The observed traceback is inside root_run_pair reached after the preceding linear require/verify calls in review_group, in the first W09-G01 loop iteration. Values that were not serialized remain unavailable; no new execution or acceptance is inferred.',
        completed_check_groups=['ready/run statuses and allcleanup boundaries; same fixed request/Source21/run/selector','real Root Scope generation/executor and report interval within finite lease','exact report/native ToolRun/argv/Source21/status/noformal flags','native stream verification and event interval','owned raw business graph plus verify_c19 and verify_a06','two actual invocation receipts and Job closures','five guard receipts;3905 compiler pins membership;19 module equality and private export membership','Root prepare original initial/completed same-session publication'],
        unpersisted_values=None,pending_check_groups=['Root run artifact publication joined to separate real progress capture and final same-session completion','Mode predicate facts','launcher tail provenance','historical canonical ledger/archive join after all four scopes close'],
        original_resource_guard_ref=pin(Q/'partial-actual-SourceGuard.closed.json'),original_tool_io_ref=pin(Q/'original-1e2439.fullIO.reencoded.json'),
        Source_guard_verified_resources=1931,all_guards_closed=True,retained_handles_count=0,product_failed=False,overall_qualified=False,Mode_issued=False,formal_acceptance=False,formal_case_accepted_delta=0))
    binding=save(Q/'original1192.public-binding.json',dict(schema='researchos.original-tool-failure-public-binding.v1',original_ordinal=1192,actor_id='codex:/root/backup_regression_resources',backend_actor='/root/backup_regression_resources',thread_id='01a11cee-bf59-7a01-be0e-9f799f9b1084',actual_host_chunk_id='1e2439',actual_outer_exit=1,actual_python_exit=1,Native=None,Go=None,SQL=None,model=None,TP=None,dispatcher=None,
        original_tool_io_ref=pin(Q/'original-1e2439.fullIO.reencoded.json'),original_failed_script_ref=pin(failed),actual_review_result_ref=pin(Q/'partial-actual-review-result.json'),actual_guard_cleanup_ref=pin(Q/'partial-actual-SourceGuard.closed.json'),known_successful_prefix_ref=prefix,
        raw_capture_ref=None,raw_capture_status='NOT_CAPTURED_PER_CURRENT_ROOT_NO_LIVE_AUDIT_INSTRUCTION',serialization='STORED_TOOL_REQUEST_RESULT_REENCODED_NOT_RAW3LF',failure_kind='REVIEWER_EXTRA_ROOT_COMPLETION_STRUCTURE_ASSUMPTION',product_failure=False,automatic_retry=False,original_counter_reset=False))
    print(json.dumps(dict(original1192_binding_ref=binding,original_io_ref=pin(Q/'original-1e2439.fullIO.reencoded.json'),successful_G01_prefix_ref=prefix,guard_cleanup_ref=pin(Q/'partial-actual-SourceGuard.closed.json')),ensure_ascii=False))
    return 0
if __name__=='__main__':
    rc=1
    try:rc=main()
    except BaseException:traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(rc));sys.exit(rc)
