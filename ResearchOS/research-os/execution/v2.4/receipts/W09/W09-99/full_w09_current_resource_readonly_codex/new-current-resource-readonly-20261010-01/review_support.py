from pathlib import Path
import ast, datetime, hashlib, json, types

R=Path(r'D:/作品集/ResearchOS/research-os')
D=Path(__file__).resolve().parent
W=R/'execution/v2.4/receipts/W09/W09-99'
N=W/'full_w09_main_native_producer_source_codex/fullw09-20261010-03'
A=W/'w09_profile_nf3_root_adoption_source_codex/adopt-20261010-02'
T=W/'full_w09_actual_native_independent_review_codex/actual-three-20261010-01'
S=W/'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
G=R/'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
GREF={'path':str(G),'sha256':'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85','bytes':11404}
LOG=Path(r'C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T23-50-03-01a1215b-7210-7613-b033-756b9d553b83.jsonl')
THREAD='01a1215b-7210-7613-b033-756b9d553b83'
ACTOR='/root/full_w09_source_review'

def pin(path):
    path=Path(path);raw=path.read_bytes()
    return {'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}

def write(name,value):
    path=D/name
    with path.open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8'))
    return pin(path)

def inert(path,raw=None):
    path=Path(path);m=types.ModuleType(path.stem);m.__file__=str(path)
    exec(compile(path.read_bytes() if raw is None else raw,str(path),'exec'),m.__dict__)
    return m

def guard():
    assert pin(G)==GREF
    return inert(G).SourceReadGuard(per_file_cap=512*1024*1024,total_cap=2*1024*1024*1024)

def exact_ref(path,sha,size):
    return {'path':str(path),'sha256':sha,'bytes':size}

def shape(value):
    if type(value) is dict:
        return {'type':'dict','keys':list(value),'scalars':{k:v for k,v in value.items() if v is None or type(v) in (str,int,bool,float)}}
    if type(value) is list:
        return {'type':'list','length':len(value),'first_two':[shape(x) for x in value[:2]]}
    return {'type':type(value).__name__,'value':value}

def docs(value):
    if type(value) is dict:
        yield value
        for v in value.values():yield from docs(v)
    elif type(value) is list:
        for v in value:yield from docs(v)
    elif type(value) is str:
        try:yield from docs(json.loads(value))
        except (ValueError,TypeError):pass

def capture(chunk,outer_exit,python_exit,ordinal=None):
    calls={};matches=[];size=LOG.stat().st_size
    with LOG.open('rb') as f:
        header=f.readline();assert json.loads(header)['payload']['id']==THREAD
        f.seek(max(0,size-64*1024*1024))
        if f.tell():f.readline()
        while f.tell()<size:
            offset=f.tell();line=f.readline();row=json.loads(line);v=row.get('payload',{})
            if v.get('type')=='custom_tool_call':calls[v['call_id']]=(offset,line,row)
            elif v.get('type')=='custom_tool_call_output':
                values=[x for x in docs(v.get('output')) if x.get('chunk_id')==chunk]
                if values and v['call_id'] in calls:matches.append((calls[v['call_id']],(offset,line,row),values))
    assert len(matches)==1 and len(matches[0][2])==1
    call,result,values=matches[0];value=values[0]
    assert value['exit_code']==outer_exit
    if python_exit is not None:assert 'Python_exit='+str(python_exit) in value['output']
    lines=[header,call[1],result[1]];offsets=[0,call[0],result[0]]
    with LOG.open('rb') as f:
        for offset,line in zip(offsets,lines):f.seek(offset);assert f.read(len(line))==line
    prefix='original-'+str(ordinal) if ordinal is not None else 'actual-'+chunk
    rawpath=D/(prefix+'.raw.jsonl')
    with rawpath.open('xb') as f:f.write(b''.join(lines))
    raw=pin(rawpath)
    binding=write(prefix+'.binding.json',{'schema':'researchos.w09-resource-readonly-host-binding.v1','actor_id':ACTOR,'actor_thread_id':THREAD,'source_audit_path':str(LOG),'source_prefix_size_observed':size,'source_line_offsets':offsets,'original_line_sha256':[hashlib.sha256(line).hexdigest() for line in lines],'original_line_bytes':[len(line) for line in lines],'original_raw_ref':raw,'actual_call_id':call[2]['payload']['call_id'],'actual_chunk_id':chunk,'original_ordinal':ordinal,'actual_outer_exit':outer_exit,'actual_python_exit':python_exit,'actual_native_exit':None,'actual_go_exit':None,'actual_sql_exit':None,'actual_dispatcher_exit':None,'actual_model_exit':None,'product_calls':0,'execution_grant':False,'formal_acceptance':False})
    return {'raw_ref':raw,'binding_ref':binding}

def code_evidence(raw,path,functions):
    text=raw.decode('utf-8');tree=ast.parse(text,filename=str(path));lines=text.splitlines()
    result=[]
    for node in tree.body:
        if isinstance(node,(ast.FunctionDef,ast.ClassDef)) and node.name in functions:
            result.append({'name':node.name,'line':node.lineno,'end_line':node.end_lineno,'source':'\n'.join(lines[node.lineno-1:node.end_lineno])})
    return result
