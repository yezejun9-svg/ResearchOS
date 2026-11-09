import hashlib,json
from pathlib import Path
Q=Path(__file__).resolve().parent
LOG=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T03-12-51-01a11cee-bf59-7a01-be0e-9f799f9b1084.jsonl')
def pin(p):
    r=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(r).hexdigest(),bytes=len(r))
def save(n,v):
    p=Q/n
    with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    return pin(p)
def main():
    prefix=LOG.stat().st_size;rows=[];offset=0
    with LOG.open('rb') as f:
        while offset<prefix:
            raw=f.readline()
            if not raw or offset+len(raw)>prefix:break
            rows.append((offset,raw,json.loads(raw)));offset+=len(raw)
    header=rows[0];assert header[2]['payload']['id']=='01a11cee-bf59-7a01-be0e-9f799f9b1084'
    calls=[r for r in rows if r[2].get('payload',{}).get('type') in ('custom_tool_call','function_call') and 'task69_' in str(r[2]['payload'].get('input',r[2]['payload'].get('arguments','')))]
    index=[];unreturned=[]
    for call in calls:
        callid=call[2]['payload']['call_id'];outputs=[r for r in rows if r[2].get('payload',{}).get('type') in ('custom_tool_call_output','function_call_output') and r[2]['payload'].get('call_id')==callid]
        if not outputs:unreturned.append(dict(call_id=callid,call_offset=call[0],reason='Return not yet present in this immutable observed prefix'));continue
        assert len(outputs)==1;output=outputs[0];chosen=[header,call,output]
        name='Source-tool-'+hashlib.sha256(callid.encode()).hexdigest()[:24]
        p=Q/(name+'.raw.jsonl')
        with p.open('xb') as f:f.write(b''.join(r[1] for r in chosen))
        binding=save(name+'.binding.json',dict(schema='researchos.actual-Source-tool-capture-binding.v1',source_actor='codex:/root/backup_regression_resources',source_thread_id=header[2]['payload']['id'],parent_thread_id=header[2]['payload'].get('parent_thread_id'),actual_tool_name=call[2]['payload']['name'],original_call_id=callid,source_audit_path=str(LOG),source_line_offsets=[r[0] for r in chosen],source_line_bytes=[len(r[1]) for r in chosen],original_line_sha256=[hashlib.sha256(r[1]).hexdigest() for r in chosen],source_prefix_size_observed=prefix,original_capture_ref=pin(p),tool_call_timestamp=call[2]['timestamp'],tool_result_timestamp=output[2]['timestamp'],representation='Exact original header+call+returnedoutput LF bytes; no synthetic Root capture or Source peer issuance'))
        index.append(dict(call_id=callid,raw_ref=pin(p),binding_ref=binding))
    result=save('Source-actual-toolpairs.index.json',dict(schema='researchos.old21-Source-process-actual-toolpairs.v1',source_actor='codex:/root/backup_regression_resources',source_thread_id=header[2]['payload']['id'],parent_thread_id=header[2]['payload'].get('parent_thread_id'),observed_prefix_size=prefix,complete_returned_toolpairs=index,unreturned_at_capture=unreturned,Source_seal_full_call_return='Root must externally capture after seal return; current seal full return cannot be present causally before HDF sealing',Source_only=True,execution_grant=False,formal_acceptance=False))
    print(json.dumps(dict(index_ref=result,completed_actual_toolpairs=len(index),unreturned_at_capture=len(unreturned)),ensure_ascii=False))
if __name__=='__main__':
    try:main()
    except BaseException:print('ROOT_PYTHON_EXIT=1');raise
    print('ROOT_PYTHON_EXIT=0')
