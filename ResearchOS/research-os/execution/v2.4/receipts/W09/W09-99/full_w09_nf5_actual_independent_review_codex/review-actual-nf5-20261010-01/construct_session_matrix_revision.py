import ast,hashlib,json,sys,traceback
from pathlib import Path
Q=Path(__file__).resolve().parent
def pin(p):
    raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def write(name,value):
    p=Q/name
    with p.open('xb')as f:f.write(value if type(value)is bytes else(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    return pin(p)
def main():
    base=Q/'review_actual_nf5.v7.py';raw=base.read_bytes();assert pin(base)['sha256']=='536d8fe75e527e4055d29156838714cffe0a2765191a3e592ed560fc221ec7a2'
    text=raw.decode('utf-8');nl='\r\n'if '\r\n'in text else '\n'
    before="    require(type(first.get('session_id'))is int and first['session_id']>0 and'write_stdin'in completed['call_payload'].get('input','')\n        and re.search(r'session_id\\s*:\\s*'+str(first['session_id'])+r'\\b',completed['call_payload']['input'])\n        and initial['output_ordinal']<completed['call_ordinal'],'SAME_PREPARE_HOST_SESSION')".replace('\n',nl)
    after="    require(type(first.get('session_id'))is int and first['session_id']>0\n        and observed_prepare_session(completed,c,first['session_id'])\n        and initial['output_ordinal']<completed['call_ordinal'],'SAME_PREPARE_HOST_SESSION')".replace('\n',nl)
    helper=r'''def observed_prepare_session(completed,c,session):
    text=completed['call_payload'].get('input','')
    direct=re.findall(r'tools\.write_stdin\(\{session_id\s*:\s*([0-9]+)\s*,',text)
    if direct:return direct==[str(session)]
    matrix=re.search(r'const sessions=(\[\[.*?\]\]);',text,re.S)
    require(matrix is not None,'EXACT_OBSERVED_PREPARE_SESSION_MATRIX')
    rows=decode(matrix.group(1))
    require(type(rows)is list and len(rows)==3 and all(type(r)is list and len(r)==2 and type(r[0])is str
        and type(r[1])is int and r[1]>0 for r in rows)and {r[0]for r in rows}=={'W09-G01','A06','C19'},'EXACT_THREE_PREPARE_SESSIONS')
    chosen=[r[1]for r in rows if r[0]==c['selector_key']]
    require(chosen==[session]and len({r[1]for r in rows})==3,'EXACT_SELECTOR_INITIAL_SESSION')
    require('sessions.map(([,id])=>tools.write_stdin({session_id:id,chars:"",yield_time_ms:1000,max_output_tokens:1600}))'in text
        and 'text({selector:sessions[i][0],...rs[i]})'in text,'ONLY_OBSERVED_SESSION_MAP_AND_RESULT_BINDING')
    chunk=completed['actual_host_result']['chunk_id']
    return any(type(d)is dict and d.get('selector')==c['selector_key']and type(d.get('value'))is dict
        and d['value'].get('chunk_id')==chunk for d in nested_documents(completed['output_payload']))

'''.replace('\n',nl)
    assert text.count(before)==1 and text.count('def root_prepare_pair(')==1
    changed=text.replace(before,after).replace('def root_prepare_pair(',helper+'def root_prepare_pair(').replace('actual-review-v7-guard.closed.json','actual-review-v8-guard.closed.json')
    ast.parse(changed)
    inverse=changed.replace('actual-review-v8-guard.closed.json','actual-review-v7-guard.closed.json').replace(helper,'').replace(after,before)
    assert inverse.encode('utf-8')==raw
    candidate=write('review_actual_nf5.v8.py',changed.encode('utf-8'))
    inv=write('session-matrix-revision.inverse.json',dict(base_ref=pin(base),candidate_ref=candidate,exact_inverse_byte_equal=True,before=before,after=after,helper=helper,only_actual_batch_session_observation=True,Native_runs=0,Go_runs=0))
    c=json.loads((Q/'input-contract.v8.json').read_bytes());c['reviewer_program_ref']=candidate;c['future_argv'][6]=candidate['path'];c['previous_contract_ref']=pin(Q/'input-contract.v8.json');c['inverse_ref']=inv
    cref=write('input-contract.v9.json',c);print(json.dumps(dict(program_ref=candidate,contract_ref=cref,inverse_ref=inv),ensure_ascii=False));return 0
if __name__=='__main__':
    rc=1
    try:rc=main()
    except BaseException:traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(rc));sys.exit(rc)
