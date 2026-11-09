from __future__ import annotations
import ast, hashlib, json, sys
from pathlib import Path

Q=Path(__file__).resolve().parent
ACTOR='codex:/root/backup_regression_resources'
THREAD='01a11cee-bf59-7a01-be0e-9f799f9b1084'
ROOT_THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUDIT=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T03-12-51-01a11cee-bf59-7a01-be0e-9f799f9b1084.jsonl')
def require(value,code):
    if not value:raise ValueError(code)
def load(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def pin(path):
    p=Path(path);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def checked(ref):
    raw=Path(ref['path']).read_bytes();require(hashlib.sha256(raw).hexdigest()==ref['sha256'] and len(raw)==ref['bytes'],'EXACT_REF');return raw
def save(name,value):
    p=Q/name;require(not p.exists(),'NEW_FILE_ONLY');p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');return pin(p)
def values(value):
    yield value
    if isinstance(value,dict):
        for v in value.values():yield from values(v)
    elif isinstance(value,list):
        for v in value:yield from values(v)
def author_capture(row):
    a=json.loads(checked(row['binding_ref']));raw=checked(row['raw_ref']);lines=raw.splitlines(keepends=True)
    require(a['source_actor']=='codex:/root/native_temp_independent_review' and a['source_thread_id']=='01a11e22-ecb2-7720-80d2-af63727d414d','SOURCE_AUTHOR')
    require(a['original_capture_ref']==row['raw_ref'] and len(lines)==3,'THREE_SOURCE_RECORDS')
    records=[json.loads(v) for v in lines];head,first,last=records;fp=first['payload'];lp=last['payload']
    require(head['type']=='session_meta' and head['payload']['id']==a['source_thread_id'],'SOURCE_HEADER')
    require(first['type']==last['type']=='response_item' and fp['type'] in ('custom_tool_call','function_call') and lp['type'] in ('custom_tool_call_output','function_call_output'),'SOURCE_TOOLPAIR')
    require(fp['call_id']==lp['call_id']==a['original_call_id'],'SOURCE_CALL_ID')
    require(a['source_line_bytes']==[len(v) for v in lines] and a['original_line_sha256']==[hashlib.sha256(v).hexdigest() for v in lines],'SOURCE_LINE_PINS')
    with Path(a['source_audit_path']).open('rb') as f:
        for off,line in zip(a['source_line_offsets'],lines):
            require(off+len(line)<=a['source_prefix_size_observed'],'SOURCE_PREFIX');f.seek(off);require(f.read(len(line))==line,'SOURCE_ORIGINAL_BYTES')
    text=json.dumps(lp.get('output'),ensure_ascii=False)
    markers=[x for x in ('ROOT_PYTHON_EXIT=0','ROOT_PYTHON_EXIT=1','"exit_code":0','"exit_code":1','"exit_code": 0','"exit_code": 1') if x in text]
    return dict(chunk_id=row['chunk_id'],binding_ref=row['binding_ref'],raw_ref=row['raw_ref'],actual_tool_name=fp.get('name'),observed_exit_markers=markers,original_bytes_verified=True)
def capture_own():
    require(AUDIT.is_file(),'OWN_AUDIT_EXISTS');size=AUDIT.stat().st_size;header=None;calls={};outputs={}
    with AUDIT.open('rb') as f:
        while f.tell()<size:
            off=f.tell();raw=f.readline()
            if not raw.endswith(b'\n'):break
            row=json.loads(raw);p=row.get('payload',{})
            if header is None:
                require(row.get('type')=='session_meta' and p.get('id')==THREAD and p.get('parent_thread_id')==ROOT_THREAD,'OWN_PARENT_IDENTITY');header=(off,raw,row)
            if row.get('type')!='response_item':continue
            typ=p.get('type');cid=p.get('call_id')
            if typ in ('custom_tool_call','function_call') and cid:
                args=p.get('arguments',p.get('input',''))
                if 'task54_' in str(args):calls[cid]=(off,raw,row)
            elif typ in ('custom_tool_call_output','function_call_output') and cid:outputs[cid]=(off,raw,row)
    result=[]
    for cid,first in calls.items():
        if cid not in outputs:continue
        last=outputs[cid];require(first[2]['ordinal']<last[2]['ordinal'],'OWN_CALL_ORDER');lines=[header[1],first[1],last[1]]
        tag=cid.removeprefix('call_');rp=Q/('actual-review-tool-'+tag+'.raw.jsonl');require(not rp.exists(),'NEW_CAPTURE');rp.write_bytes(b''.join(lines))
        binding=dict(source_actor=ACTOR,source_thread_id=THREAD,source_parent_thread_id=ROOT_THREAD,source_audit_path=str(AUDIT),source_prefix_size_observed=size,source_line_offsets=[header[0],first[0],last[0]],source_line_bytes=[len(v) for v in lines],original_line_sha256=[hashlib.sha256(v).hexdigest() for v in lines],original_capture_ref=pin(rp),original_call_id=cid,actual_tool_name=first[2]['payload'].get('name'))
        br=save('actual-review-tool-'+tag+'.binding.json',binding);result.append(dict(binding_ref=br,raw_ref=pin(rp),actual_tool_name=binding['actual_tool_name']))
    require(len(result)>0,'REAL_REVIEW_TOOLPAIRS');return result
def main():
    basis=load(Q/'verified-source-basis.index.json');members={Path(x['path']).name:x for x in basis['members']};source=basis['source_hdf_ref'];h=json.loads(checked(source));contract=json.loads(checked(h['calling_contract_ref']))
    caller=checked(h['caller_ref']).decode('utf-8');tree=ast.parse(caller);lines=caller.splitlines()
    functions={n.name:dict(line=n.lineno,end_line=n.end_lineno) for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    names={n.id for n in ast.walk(tree) if isinstance(n,ast.Name)}
    require(not names.intersection({'subprocess','Popen','OwnedJob','CreateProcessW'}),'NO_PRODUCT_PROCESS_ENTRY')
    require('leaf.recheck_existing_public22(' in caller and 'leaf.run(' not in caller,'EXACT_EXISTING_READONLY_LEAF')
    require('guard.acquire(refs_unique(refs,CANON[:2]))' in caller,'REGISTRATION_EXCLUDES_EXCLUSIVE_PAIR')
    projection=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='projection')
    transform=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='transform')
    for fn in (projection,transform):
        called={ast.unparse(n.func) for n in ast.walk(fn) if isinstance(n,ast.Call)}
        require(not any(x in called for x in ('doc','checked','pin','load','open','Path','current_four','guard.acquire')),'TP_CALLBACK_NO_FILE_OR_GUARD_IO')
    captures=json.loads(checked(members['source-tool-capture-index.json']))
    rows=[author_capture(row) for row in captures['actual_pairs']]
    require(len(rows)==18 and captures['original_failures']==[1043],'SOURCE_CAPTURE_INVENTORY')
    case=json.loads(checked(contract['original_case_request_ref']));require(set(case)=={'case_id','output_root','end_version'},'THREE_ORIGINAL_CASE_FIELDS')
    own=capture_own()
    result=dict(schema='researchos.public22-existing-independent-static-and-host-evidence.v1',status='PASS_SOURCE_ONLY',actor_id=ACTOR,author_reviewed=h['source_author'],functions=functions,original_case_request_ref=contract['original_case_request_ref'],original_case_fields=list(case),original_case_bytes_unchanged=True,fixed_nine_evidence=contract['fixed_evidence'],source_capture_original_pairs=rows,own_actual_toolpairs=own,source_original_failure1043_retained=True,original1025_result='FAILED_RETAINED',review_controls_ref=pin(Q/'independent-controls.json'),review_guard_closed_ref=pin(Q/'independent-controls.guard.closed.json'),SQL_queries=0,new_native_children=0,Go_runs=0,dispatcher_runs=0,model_calls=0,actual_registration=False,execution_grant=False,formal_acceptance=False)
    rr=save('static-and-host-evidence.json',result)
    print(json.dumps(dict(result_ref=rr,author_pairs=len(rows),review_actual_pairs=len(own),SQL_queries=0,new_native_children=0),ensure_ascii=False),flush=True)
if __name__=='__main__':
    try:main()
    except BaseException:print('ROOT_PYTHON_EXIT=1',flush=True);raise
    print('ROOT_PYTHON_EXIT=0',flush=True)
