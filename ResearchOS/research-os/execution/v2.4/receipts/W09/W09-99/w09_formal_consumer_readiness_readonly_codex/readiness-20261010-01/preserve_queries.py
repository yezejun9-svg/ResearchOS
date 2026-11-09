"""Preserve bounded actual readonly query IO; creates no Source authority."""
from pathlib import Path
import hashlib,json

D=Path(__file__).resolve().parent
LOG=Path(r'C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T23-50-03-01a1215b-7210-7613-b033-756b9d553b83.jsonl')
ACTOR='codex:/root/full_w09_source_review'
THREAD='01a1215b-7210-7613-b033-756b9d553b83'

def pin(p):
    p=Path(p);raw=p.read_bytes()
    return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}

def save(name,value):
    with (D/name).open('xb') as f:
        f.write((json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8'))
    return pin(D/name)

def documents(value):
    result=[]
    if type(value) is dict:
        result.append(value)
        for item in value.values():result.extend(documents(item))
    elif type(value) is list:
        for item in value:result.extend(documents(item))
    elif type(value) is str:
        try:result.extend(documents(json.loads(value)))
        except (ValueError,TypeError):pass
    return result

def capture(chunk,ordinal,classification,python_exit=None):
    size=LOG.stat().st_size;calls={};found=[]
    with LOG.open('rb') as f:
        header=f.readline()
        assert json.loads(header)['payload']['id']==THREAD
        start=max(0,size-64*1024*1024);f.seek(start)
        if start:f.readline()
        while f.tell()<size:
            offset=f.tell();raw=f.readline();row=json.loads(raw);payload=row.get('payload',{})
            if payload.get('type')=='custom_tool_call':calls[payload['call_id']]=(offset,raw,row)
            if payload.get('type')=='custom_tool_call_output':
                matches=[item for item in documents(payload.get('output')) if item.get('chunk_id')==chunk]
                if matches and payload['call_id'] in calls:found.append((calls[payload['call_id']],(offset,raw,row),matches))
    assert len(found)==1 and len(found[0][2])==1,(chunk,len(found))
    call,returned,values=found[0];value=values[0]
    assert value['exit_code']==1
    lines=[header,call[1],returned[1]];offsets=[0,call[0],returned[0]]
    with LOG.open('rb') as f:
        for offset,line in zip(offsets,lines):
            f.seek(offset);assert f.read(len(line))==line
    stem='original-'+str(ordinal) if ordinal is not None else 'query-'+chunk
    with (D/(stem+'.raw.jsonl')).open('xb') as f:f.write(b''.join(lines))
    raw_ref=pin(D/(stem+'.raw.jsonl'))
    binding=save(stem+'.binding.json',dict(schema='researchos.readonly-query-host-binding.v1',actor_id=ACTOR,actor_thread_id=THREAD,
        original_failure_ordinal=ordinal,classification=classification,source_audit_path=str(LOG),source_prefix_size_observed=size,
        source_line_offsets=offsets,source_line_bytes=[len(x) for x in lines],source_line_sha256=[hashlib.sha256(x).hexdigest() for x in lines],
        actual_call_id=call[2]['payload']['call_id'],actual_chunk_id=chunk,original_raw_ref=raw_ref,
        actual_outer_exit=value['exit_code'],actual_python_exit=python_exit,actual_native_exit=None,actual_go_exit=None,actual_sql_exit=None,
        actual_dispatcher_exit=None,actual_model_exit=None,actual_host_result=value,product_calls=0,live_Canon_handles=0,
        execution_grant=False,formal_acceptance=False))
    return {'raw_ref':raw_ref,'binding_ref':binding}

if __name__=='__main__':
    refs={chunk:capture(chunk,ordinal,kind) for chunk,ordinal,kind in (
        ('65719e',None,'SEARCH_NO_MATCHES'),('cd1861',None,'SEARCH_NO_MATCHES'),
        ('ac10c0',None,'FILE_GLOB_NO_MATCHES'),('c36dd3',1117,'READONLY_REVIEWER_GUESSED_MISSING_DIRECTORY'))}
    index=save('readonly-query-originals.json',dict(schema='researchos.w09-consumer-readiness-query-originals.v1',actor_id=ACTOR,
        captures=refs,original1117_counted_once_by_Root=True,successful_Source_controls_repeated=False,product_calls=0,
        live_Canon_handles=0,execution_grant=False,formal_acceptance=False))
    print(json.dumps({'captures':refs,'query_originals_ref':index,'product_calls':0,'execution_grant':False,'formal_acceptance':False},ensure_ascii=False),flush=True)
