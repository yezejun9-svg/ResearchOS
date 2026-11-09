import hashlib,json,sys
from pathlib import Path
Q=Path(__file__).resolve().parent
LOG=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T03-12-51-01a11cee-bf59-7a01-be0e-9f799f9b1084.jsonl')
def pin(p):
    raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,value):
    p=Q/name
    with p.open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    return pin(p)
def main():
    prefix=LOG.stat().st_size;rows=[];offset=0
    with LOG.open('rb') as f:
        while offset<prefix:
            raw=f.readline()
            if not raw or offset+len(raw)>prefix:break
            value=json.loads(raw);rows.append((offset,raw,value));offset+=len(raw)
    header=rows[0];assert header[2]['type']=='session_meta'
    saved=[]
    for ordinal,chunk in [(1071,'026f85'),(1072,'728e81')]:
        outputs=[r for r in rows if r[2].get('payload',{}).get('type') in ('custom_tool_call_output','function_call_output') and chunk in str(r[2]['payload'].get('output',''))]
        assert outputs
        output=outputs[0];callid=output[2]['payload']['call_id']
        calls=[r for r in rows if r[2].get('payload',{}).get('type') in ('custom_tool_call','function_call') and r[2]['payload'].get('call_id')==callid]
        assert len(calls)==1;call=calls[0];chosen=[header,call,output]
        p=Q/('original'+str(ordinal)+'.actual-host.raw.jsonl')
        with p.open('xb') as f:f.write(b''.join(r[1] for r in chosen))
        binding=save('original'+str(ordinal)+'.actual-host.binding.json',dict(schema='researchos.actual-Source-original-host-binding.v1',source_actor='codex:/root/backup_regression_resources',source_thread_id=header[2]['payload']['id'],parent_thread_id=header[2]['payload'].get('parent_thread_id'),original_call_id=callid,actual_tool_name=call[2]['payload']['name'],source_audit_path=str(LOG),source_line_offsets=[r[0] for r in chosen],source_line_bytes=[len(r[1]) for r in chosen],original_line_sha256=[hashlib.sha256(r[1]).hexdigest() for r in chosen],source_prefix_size_observed=prefix,original_capture_ref=pin(p),tool_call_timestamp=call[2]['timestamp'],tool_result_timestamp=output[2]['timestamp']))
        origin=save('failure-origin.'+str(ordinal)+'.json',dict(schema='researchos.original-failure.v1',ordinal=ordinal,chunk_id=chunk,actual_outer_exit=1,actual_python_exit=1,actual_Go_exit=None,actual_native_exit=None,actual_SQL_exit=None,actual_model_exit=None,actual_TP_exit=None,original_tool_IO_ref=pin(Q/'original1071-1072.complete-tool-IO.json'),capture_binding_ref=binding,original_capture_ref=pin(p),failed_script_ref=pin(Q/('read_Task69_basis.py' if ordinal==1071 else 'read_Task69_basis_revision.py')),old_input_retried=False,counter_reset=False,failed_guard_receipt='UNKNOWN_NOT_SERIALIZED',candidate_writes=0,live_Canon_reads=0))
        saved.append(dict(ordinal=ordinal,origin_ref=origin,binding_ref=binding,raw_ref=pin(p)))
    print(json.dumps(dict(records=saved),ensure_ascii=False),flush=True)
if __name__=='__main__':
    try:main()
    except BaseException:print('ROOT_PYTHON_EXIT=1');raise
    print('ROOT_PYTHON_EXIT=0')
