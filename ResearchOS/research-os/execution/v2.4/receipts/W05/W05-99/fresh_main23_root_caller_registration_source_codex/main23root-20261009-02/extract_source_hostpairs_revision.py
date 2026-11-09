import sys
sys.dont_write_bytecode=True
import hashlib
import json
from pathlib import Path
import traceback

Q=Path(__file__).resolve().parent
AUDIT=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T03-12-51-01a11cee-bf59-7a01-be0e-9f799f9b1084.jsonl')
THREAD='01a11cee-bf59-7a01-be0e-9f799f9b1084'
KEYS={'main23v2_read':'input-read','main23v2_construct':'original1031','main23v2_construct_or_session_0':'original1032','main23v2_construct_or_log_0':'candidate-construct','main23v2_original_controls':'original22-controls','main23v2_target_controls':'targeted43-controls'}

def pin(path,raw):return {'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def save(name,value,raw=False):
    path=Q/name;path.parent.mkdir(parents=True,exist_ok=True)
    data=value if raw else (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    with path.open('xb') as stream:assert stream.write(data)==len(data)
    return pin(path,data)

def dictionaries(value):
    result=[]
    def visit(v,depth=0):
        if depth>24:return
        if type(v) is dict:
            result.append(v)
            for x in v.values():visit(x,depth+1)
        elif type(v) is list:
            for x in v:visit(x,depth+1)
        elif type(v) is str:
            seen=set()
            for text in [v]+v.splitlines():
                text=text.strip()
                if text in seen or not text.startswith(('{','[')):continue
                seen.add(text)
                try:p=json.loads(text)
                except json.JSONDecodeError:continue
                visit(p,depth+1)
    visit(value)
    return result

def main():
    items=json.loads((Q/'complete-source-tool-dictionary-io.json').read_text(encoding='utf-8'))['items']
    expected={KEYS[x['key']]:x['response'] for x in items if x['key'] in KEYS}
    assert len(expected)==6
    # Promise.all orchestration entries store the inner actual host dictionary.
    for label,value in list(expected.items()):
        if type(value) is dict and 'result' in value:expected[label]=value['result']
        elif type(value) is dict and value.get('status')=='fulfilled':expected[label]=value['value']
    chunks={v['chunk_id']:k for k,v in expected.items()}
    calls={};outputs={};found={};prefix=AUDIT.stat().st_size
    with AUDIT.open('rb') as stream:
        header_raw=stream.readline();header=json.loads(header_raw)
        assert header['type']=='session_meta' and header['ordinal']==0 and header['payload']['id']==THREAD
        while stream.tell()<prefix:
            offset=stream.tell();raw=stream.readline()
            if offset+len(raw)>prefix:break
            row=json.loads(raw);payload=row.get('payload',{})
            if row.get('type')!='response_item' or type(payload) is not dict:continue
            call_id=payload.get('call_id')
            if payload.get('type') in ('custom_tool_call','function_call') and payload.get('name')=='functions.exec':
                calls[call_id]=(offset,raw,row)
            elif payload.get('type') in ('custom_tool_call_output','function_call_output') and call_id in calls:
                if not any(chunk in raw.decode('utf-8') for chunk in chunks):continue
                for host in dictionaries(payload.get('output')):
                    chunk=host.get('chunk_id');label=chunks.get(chunk)
                    if not label or host!=expected[label]:continue
                    assert label not in found,(label,'duplicate actual host result')
                    found[label]=(calls[call_id],(offset,raw,row),host)
    assert set(found)==set(expected),(sorted(found),sorted(expected))
    refs=[]
    for label,(call,output,host) in found.items():
        records=[(0,header_raw,header),call,output]
        raw=b''.join(x[1] for x in records)
        rawref=save('actual-source-hostpairs/'+label+'.jsonl',raw,True)
        binding=save('actual-source-hostpairs/'+label+'.binding.json',{
            'schema':'researchos.actual-source-tool-pair-binding.v1','authority':'NONE',
            'author_session_id':THREAD,'actual_agent_path':'/root/backup_regression_resources',
            'parent_task_path':'/root','parent_task_binding_source':'Root collaboration NEW_TASK and canonical agent path; no invented audit parent field',
            'source_audit_path':str(AUDIT),'source_prefix_size_observed':prefix,
            'source_line_offsets':[x[0] for x in records],'source_line_ordinals':[x[2]['ordinal'] for x in records],
            'source_line_bytes':[len(x[1]) for x in records],
            'source_line_sha256':[hashlib.sha256(x[1]).hexdigest() for x in records],
            'actual_call_id':call[2]['payload']['call_id'],'actual_tool_name':call[2]['payload']['name'],
            'actual_host_chunk_id':host['chunk_id'],'actual_outer_exit':host['exit_code'],
            'actual_Python_exit':0 if 'ROOT_PYTHON_EXIT=0' in host['output'] else 1 if 'ROOT_PYTHON_EXIT=1' in host['output'] else None,
            'Go_Native_SQLite_dispatcher_model_exits':None,'raw_original_capture_ref':rawref,
            'original_source_selected_lines_match':True,'no_source_log_write':True,
            'header_payload_fields':sorted(header['payload']),
            'header_public_identity':{k:header['payload'][k] for k in ('id','cwd','originator') if k in header['payload']}})
        refs.append({'label':label,'raw_ref':rawref,'binding_ref':binding,'actual_outer_exit':host['exit_code'],
            'actual_Python_exit':0 if 'ROOT_PYTHON_EXIT=0' in host['output'] else 1 if 'ROOT_PYTHON_EXIT=1' in host['output'] else None})
    ref=save('actual-source-hostpairs.index.json',{'schema':'researchos.actual-source-hostpair-index.v1',
        'source_author':'codex:/root/backup_regression_resources','thread_id':THREAD,
        'source_audit_metadata_only_size':prefix,'pairs':refs,'authority':'NONE',
        'retained_handles':0,'no_qualification_or_product_authority':True})
    print(json.dumps({'index_ref':ref,'pairs':refs,'retained_handles':0},ensure_ascii=False))

if __name__=='__main__':
    code=0
    try:main()
    except BaseException:traceback.print_exc();code=1
    print('ROOT_PYTHON_EXIT='+str(code));raise SystemExit(code)
