import ast,hashlib,json,sys,traceback
from pathlib import Path
Q=Path(__file__).resolve().parent
def pin(p):
    b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def write(name,data):
    p=Q/name
    with p.open('xb')as f:f.write(data if type(data)is bytes else(json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    return pin(p)
def main():
    base=Q/'review_actual_nf5.v4.py';raw=base.read_bytes()
    assert hashlib.sha256(raw).hexdigest()=='cdba143c8695779cd6c4029b7a8bab58366d7a99a2604bfa7c0654ed5c8dfeef'
    text=raw.decode('utf-8');edits=[]
    def change(before,after,count):
        nonlocal text
        assert text.count(before)==count,(before,text.count(before))
        for _ in range(count):
            start=text.index(before);edits.append(dict(start=start,before=before,after=after))
            text=text[:start]+after+text[start+len(before):]
    change('    unique={key(ref):ref for ref in refs}',
           "    unique={key(ref):dict(path=str(ref_shape(ref)),sha256=ref['sha256'],bytes=ref['bytes'])for ref in refs}",1)
    change('actual-review-guard.closed.json','actual-review-v5-guard.closed.json',2)
    ast.parse(text);restored=text
    for e in reversed(edits):
        assert restored[e['start']:e['start']+len(e['after'])]==e['after']
        restored=restored[:e['start']]+e['before']+restored[e['start']+len(e['after']):]
    assert restored.encode('utf-8')==raw
    candidate=write('review_actual_nf5.v5.py',text.encode('utf-8'))
    inverse=write('guard-spelling-revision.inverse.json',dict(schema='researchos.readonly-review-source-exact-inverse.v1',base_ref=pin(base),
        candidate_ref=candidate,edits=edits,exact_inverse_byte_equal=True,report_Source_literals_unchanged=True,
        physical_path_sha_bytes_binding_unchanged=True,old_controls_rerun=False,Native_runs=0,Go_runs=0,formal_acceptance=False))
    contract=json.loads((Q/'input-contract.v5.json').read_text(encoding='utf-8'));contract['reviewer_program_ref']=candidate
    contract['future_argv'][6]=candidate['path'];contract['previous_contract_ref']=pin(Q/'input-contract.v5.json');contract['inverse_ref']=inverse
    contract['Guard_only_path_normalization']='R-relative owned report refs become verified same physical absolute path with exact original SHA/bytes at Guard boundary; original Source/report/request unchanged.'
    cref=write('input-contract.v6.json',contract)
    print(json.dumps(dict(program_ref=candidate,contract_ref=cref,inverse_ref=inverse,exact_inverse_pass=True),ensure_ascii=False));return 0
if __name__=='__main__':
    rc=1
    try:rc=main()
    except BaseException:traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(rc));sys.exit(rc)
