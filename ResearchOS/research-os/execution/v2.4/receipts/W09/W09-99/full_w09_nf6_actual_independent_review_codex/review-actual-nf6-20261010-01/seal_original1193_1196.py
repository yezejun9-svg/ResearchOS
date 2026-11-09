import hashlib,json
from pathlib import Path
Q=Path(__file__).resolve().parent
def ref(path):
    raw=Path(path).read_bytes();return {'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def save(name,doc):
    path=Q/name
    with path.open('xb')as out:out.write((json.dumps(doc,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    return ref(path)
rows=[]
for ordinal,chunk,outer,python,inner,script in [(1193,'5e4bd1',0,None,None,None),(1196,'4b13d9',1,1,None,'review_partial_delta.py')]:
    io=ref(Q/('original-'+chunk+'.fullIO.reencoded.json'))
    doc={'schema':'researchos.original-public-reencoded-binding.v1','original_ordinal':ordinal,'actual_host_chunk_id':chunk,'actor_id':'codex:/root/backup_regression_resources','backend_actor':'/root/backup_regression_resources','Root_thread_id':'01a11007-5233-7ca1-b71f-9e9e5ce84c98','author_thread_id':'01a11cee-bf59-7a01-be0e-9f799f9b1084','capture_kind':'REENCODED_STORED_TOOL_OBJECTS_NOT_RAW_AUDIT_BYTES','complete_stored_tool_io_ref':io,'original_capture_ref':None,'original_capture_status':'NOT_CAPTURED_PER_CURRENT_ROOT_NO_LIVE_AUDIT_INSTRUCTION','actual_outer_exit':outer,'actual_python_exit':python,'actual_inner_rg_exit':inner,'actual_native_exit':None,'actual_Go_exit':None,'actual_SQL_exit':None,'actual_model_exit':None,'actual_TP_exit':None,'actual_dispatcher_exit':None,'failure_counter_reset':False,'script_ref':ref(Q/script)if script else None,'guard_cleanup_ref':ref(Q/'partial-delta-SourceGuard.closed.json')if ordinal==1196 else None,'guard_acquired':ordinal==1196}
    rows.append(save('original'+str(ordinal)+'.public-binding.json',doc))
prefix={'schema':'researchos.w09-nf6-G01-successful-delta-prefix.v1','selector':'W09-G01','original1196_binding_ref':rows[1],'delta_script_ref':ref(Q/'review_partial_delta.py'),'exact_prior_G01_successful_prefix_ref':ref(Q/'G01.original1192-successful-prefix.json'),'delta_guard_cleanup_ref':ref(Q/'partial-delta-SourceGuard.closed.json'),'provenance':'CONTROL_FLOW_REACHED_THE_EXACT_PROGRESS_DOCUMENT_COUNT_GATE_AFTER_THESE_CHECKS_PASSED','passed_pending_conditions':['exact launcher started/closed/permit/Source21/run binding','returned runner0/oneUUID/cleanup0/stdlib and Main unchanged','FIXTURE all HTTP delivery IN_PROCESS_HTTptest_RECORDER and owned temp state predicate','Root initial yielded session to complete0/0','Root compiler progress actual3LF/boundchunk/same-session/ordinal and structured artifact reference'],'remaining':['progress document singleton gate and uint64 FILETIME equality','producer progress join','G02/A06/C19 first independent review'],'unpersisted_return_values':None,'Mode_issued':False,'formal_acceptance':False,'new_product_runs':0}
pr=save('G01.original1196-successful-delta-prefix.json',prefix)
print(json.dumps({'original_binding_refs':rows,'full_IO_refs':[ref(Q/'original-5e4bd1.fullIO.reencoded.json'),ref(Q/'original-4b13d9.fullIO.reencoded.json')],'G01_delta_prefix_ref':pr},ensure_ascii=False))
print('ROOT_PYTHON_EXIT=0')
