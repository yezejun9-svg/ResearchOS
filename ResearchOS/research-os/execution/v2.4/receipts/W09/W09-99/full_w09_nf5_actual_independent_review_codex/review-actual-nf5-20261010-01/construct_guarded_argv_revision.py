import ast,hashlib,json,sys,traceback
from pathlib import Path
Q=Path(__file__).resolve().parent
def pin(p):
    b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def write(name,value):
    p=Q/name
    with p.open('xb')as f:f.write(value if type(value)is bytes else(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    return pin(p)
def main():
    p=Q/'review_actual_nf5.v6.py';raw=p.read_bytes()
    assert hashlib.sha256(raw).hexdigest()=='bdd59048240dfe981c3c8067b4001cfaf7748b521c9612877235a4f67134b3a0'
    before=b"template=decode('\"'+templated.group(1)+'\"')"
    after=b"template=decode('\"'+templated.group(1).replace('\"',r'\\\"')+'\"')"
    assert raw.count(before)==1
    revised=raw.replace(before,after).replace(b'actual-review-v6-guard.closed.json',b'actual-review-v7-guard.closed.json')
    assert revised.count(b'actual-review-v7-guard.closed.json')==2
    ast.parse(revised)
    assert revised.replace(after,before).replace(b'actual-review-v7-guard.closed.json',b'actual-review-v6-guard.closed.json')==raw
    ref=write('review_actual_nf5.v7.py',revised)
    inverse=write('observed-template-quote.inverse.json',dict(base_ref=pin(p),candidate_ref=ref,before_utf8=before.decode(),after_utf8=after.decode(),guard_output_revision=True,exact_inverse_byte_equal=True,actual_v6_executed=False,reason='Observed JS template contains literal double quotes; quote them only for JSON escape decoding, without evaluating template expressions.'))
    c=json.loads((Q/'input-contract.v7.json').read_text(encoding='utf-8'));c['reviewer_program_ref']=ref;c['future_argv'][6]=ref['path'];c['previous_contract_ref']=pin(Q/'input-contract.v7.json');c['inverse_ref']=inverse
    cref=write('input-contract.v8.json',c)
    print(json.dumps(dict(program_ref=ref,contract_ref=cref,inverse_ref=inverse),ensure_ascii=False));return 0
if __name__=='__main__':
    rc=1
    try:rc=main()
    except BaseException:traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(rc));sys.exit(rc)
