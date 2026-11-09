"""Continue only sealer; exact actual call ID handles non-JSON tool rejection."""
import hashlib,json,sys,types
from pathlib import Path
Q=Path(__file__).resolve().parent
original=(Q/'seal_source.py').read_text(encoding='utf-8')
start=original.index("    diagnostics=json.loads((Q/'source-diagnostic-original-host.index.json').read_bytes());matches=[]")
end=original.index("    origin1134=save(",start)
replacement='''    discovery=json.loads((Q/'actual-tool-rejection-discovery.json').read_bytes())
    need(len(discovery)==1 and discovery[0]['call']['call_id']=='call_6938fdcff62d4daa99ab788aaac5d912','EXACT_1134_DISCOVERY_CALL_ID')
    entry=discovery[0];audit_path=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T03-12-51-01a11cee-bf59-7a01-be0e-9f799f9b1084.jsonl')
    with audit_path.open('rb') as f:
        header=f.readline();f.seek(entry['call']['offset']);call_line=f.readline();f.seek(entry['actual_return']['offset']);out_line=f.readline()
    need(hashlib.sha256(call_line).hexdigest()==entry['call']['line_sha256'] and hashlib.sha256(out_line).hexdigest()==entry['actual_return']['line_sha256'],'1134_ACTUAL_LINE_HASHES')
    head,call,out=[json.loads(x) for x in (header,call_line,out_line)]
    need(head['type']=='session_meta' and head['payload']['id']==THREAD and call['payload']['call_id']==out['payload']['call_id']==entry['call']['call_id'] and call['payload']['type']=='custom_tool_call' and out['payload']['type']=='custom_tool_call_output','1134_REAL_OWN_HEADER_CALL_RETURN')
    blocks=out['payload']['output'];need(type(blocks) is list and any(type(x) is dict and type(x.get('text')) is str and x['text'].startswith('Script error:\\napply_patch verification failed: Failed to find expected lines') for x in blocks),'1134_ACTUAL_NONJSON_REJECTION')
    raw=header+call_line+out_line
    with (Q/'original1134.actual.raw.jsonl').open('xb') as f:f.write(raw)
    raw_ref=pin(Q/'original1134.actual.raw.jsonl')
    bind_ref=save('original1134.actual.binding.json',dict(schema='researchos.actual-source-tool-rejection-binding.v1',capture_kind='ACTUAL_TOOL_REJECTION',source_author=AUTHOR,author_thread=THREAD,Root_parent_thread=ROOT_THREAD,source_audit_path=str(audit_path),source_line_offsets=[0,entry['call']['offset'],entry['actual_return']['offset']],source_prefix_size_observed=audit_path.stat().st_size,source_line_bytes=[len(x) for x in (header,call_line,out_line)],original_line_sha256=[hashlib.sha256(x).hexdigest() for x in (header,call_line,out_line)],original_capture_ref=raw_ref,call_id=entry['call']['call_id'],call_timestamp=call['timestamp'],return_timestamp=out['timestamp'],actual_process_exit=None,process_started=False))
    pair=dict(raw_ref=raw_ref,binding_ref=bind_ref)
'''
raw=original[:start]+replacement+original[end:]
raw=raw.replace("audit_ref=save('actual-source-author-host.index.json',audit)","""audit_ref=save('actual-source-author-host.index.json',audit)
    sealer_fail=[]
    for item in audit['completed_tool_pairs']:
        lines=[json.loads(x) for x in Path(item['raw_ref']['path']).read_bytes().splitlines()]
        hosts=[x for x in m.structured_documents(lines[2]['payload']['output']) if x.get('chunk_id')=='4d20d9' and type(x.get('exit_code')) is int]
        if hosts:sealer_fail.append((item,hosts))
    need(len(sealer_fail)==1 and len(sealer_fail[0][1])==1 and sealer_fail[0][1][0]['exit_code']==1,'EXACT_ORIGINAL1138_ACTUAL_RETURN')
    item,_=sealer_fail[0]
    save('failure-origin.1138.json',dict(schema='researchos.original-source-failure-origin.v1',original_ordinal=1138,original_chunk_id='4d20d9',complete_IO_ref=pin(Q/'failure-4d20d9.complete-original-IO.json'),raw_ref=item['raw_ref'],actual_host_binding_ref=item['binding_ref'],actual_outer_exit=1,actual_python_exit=1,actual_native_exit=None,actual_go_exit=None,actual_SQL_exit=None,actual_TP_exit=None,actual_model_exit=None,cause='sealer searched a prior capture index rather than actual rejection call ID; Source58 successful controls untouched',guard_state='NO_FULL_SEAL_GUARD_ACQUIRED; existing Source controls guard actually closed0',counter_reset=False,automatic_retry=False))""")
raw=raw.replace("[pin(Q/'failure-origin.1132.json'),origin1134]","[pin(Q/'failure-origin.1132.json'),origin1134,pin(Q/'failure-origin.1138.json')]")
m=types.ModuleType('public21_source_sealer_revision');m.__file__=str(Path(__file__).resolve())
code=1
try:
    exec(compile(raw,str(Path(__file__).resolve()),'exec'),m.__dict__);m.main();code=0
finally:print('ROOT_PYTHON_EXIT='+str(code),flush=True)
sys.exit(code)
