import hashlib,json,os,sys,traceback
from pathlib import Path
Q=Path(__file__).resolve().parent
AUDIT=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T03-12-51-01a11cee-bf59-7a01-be0e-9f799f9b1084.jsonl')
def pin(p):
    raw=Path(p).read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def docs(v):
    if type(v)in(dict,list):
        yield v
        for x in(v.values()if type(v)is dict else v):yield from docs(x)
    elif type(v)is str:
        for text in dict.fromkeys((v,*v.splitlines())):
            try:p=json.loads(text)
            except(ValueError,TypeError):continue
            if p!=v:yield from docs(p)
def main():
    head=None;calls={};matches=[]
    with AUDIT.open('rb')as stream:
        size=os.fstat(stream.fileno()).st_size;offset=0
        while offset<size:
            line=stream.readline();value=json.loads(line);payload=value.get('payload',{})
            if offset==0:head=(offset,line,value)
            if type(payload)is dict and payload.get('type')in('custom_tool_call','function_call'):calls[payload.get('call_id')]=(offset,line,value)
            if type(payload)is dict and payload.get('type')in('custom_tool_call_output','function_call_output'):
                observations=[x for x in docs(payload)if type(x)is dict and x.get('chunk_id')=='0a87ee']
                if observations:
                    call=calls.get(payload.get('call_id'))
                    if call and'nf5actual_owned_event_shape_read_in'in str(call[2]['payload']):matches.append((call,(offset,line,value)))
            offset+=len(line)
    assert len(matches)==1 and head[2]['payload']['id']=='01a11cee-bf59-7a01-be0e-9f799f9b1084'
    call,out=matches[0];rows=[head,call,out]
    with(Q/'original1164.actual.raw.jsonl').open('xb')as f:f.write(b''.join(row[1]for row in rows))
    binding=dict(schema='researchos.original-failure-actual-source-binding.v1',original_ordinal=1164,actor='codex:/root/backup_regression_resources',
        source_thread_id=head[2]['payload']['id'],Root_parent_thread_id='01a11007-5233-7ca1-b71f-9e9e5ce84c98',source_audit_path=str(AUDIT),
        source_line_offsets=[row[0]for row in rows],source_line_bytes=[len(row[1])for row in rows],original_line_sha256=[hashlib.sha256(row[1]).hexdigest()for row in rows],
        source_prefix_size_observed=size,original_capture_ref=pin(Q/'original1164.actual.raw.jsonl'),full_tool_IO_ref=pin(Q/'original1164.full-tool-IO.json'),
        actual_chunk_id='0a87ee',actual_outer_exit=1,actual_Python_exit=None,
        actual_Go_exit=None,actual_Native_exit=None,actual_SQL_exit=None,actual_model_exit=None,actual_TP_exit=None,actual_dispatcher_exit=None,
        guard_state='NOT_ACQUIRED_BY_THIS_CALL',failure='RG_REGEX_UNCLOSED_GROUP',failure_count_reset=False)
    with(Q/'original1164.binding.json').open('xb')as f:f.write((json.dumps(binding,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    print(json.dumps(dict(original_ordinal=1164,fullIO_ref=pin(Q/'original1164.full-tool-IO.json'),raw_ref=pin(Q/'original1164.actual.raw.jsonl'),
        binding_ref=pin(Q/'original1164.binding.json'),outer_exit=1,Python_exit=None),ensure_ascii=False));return 0
if __name__=='__main__':
    rc=1
    try:rc=main()
    except BaseException:traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(rc));sys.exit(rc)
