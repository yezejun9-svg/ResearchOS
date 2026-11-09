import hashlib,json,sys,traceback
from pathlib import Path
Q=Path(__file__).resolve().parent
def pin(p):
    raw=Path(p).read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def main():
    base=Q/'review_actual_nf5.py';raw=base.read_bytes()
    old=b"choices=decode((BASE/'source.choice.json').read_bytes())['selectors'];bp=decode((BASE/'compiler-source-blueprint.json').read_bytes())"
    new=b"all_choices=decode((BASE/'source.choice.json').read_bytes());choices={name:dict(all_choices['common'],**partial)for name,partial in all_choices['selectors'].items()};bp=decode((BASE/'compiler-source-blueprint.json').read_bytes())"
    assert raw.count(old)==1
    revised=raw.replace(old,new);compile(revised,str(Q/'review_actual_nf5.v2.py'),'exec');assert revised.replace(new,old)==raw
    with(Q/'review_actual_nf5.v2.py').open('xb')as f:f.write(revised)
    failed=Q/'close_prepared_Source_guard.py';raw_guard=failed.read_bytes()
    before=b"choice=json.loads(Path(h['source_choice_ref']['path']).read_bytes())['selectors']['W09-G02']"
    after=b"all_choices=json.loads(Path(h['source_choice_ref']['path']).read_bytes());choice=dict(all_choices['common'],**all_choices['selectors']['W09-G02'])"
    assert raw_guard.count(before)==1
    guard=raw_guard.replace(before,after).replace(b"input-contract.v2.json",b"input-contract.v3.json").replace(b"'review_actual_nf5.py','input-contract.json'",b"'review_actual_nf5.v2.py','input-contract.json'")
    compile(guard,str(Q/'close_prepared_Source_guard_revision.py'),'exec')
    with(Q/'close_prepared_Source_guard_revision.py').open('xb')as f:f.write(guard)
    c=json.loads((Q/'input-contract.v2.json').read_bytes());c['previous_contract_ref']=pin(Q/'input-contract.v2.json');c['reviewer_program_ref']=pin(Q/'review_actual_nf5.v2.py')
    c['choice_assembly']='exact frozen runtime.choice: dict(all_choices.common, **selectors[selector]); partial selectors cannot replace common Source21/tool refs'
    c['original1155_ref']=pin(Q/'original1155.binding.json')
    with(Q/'input-contract.v3.json').open('xb')as f:f.write((json.dumps(c,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    inverse=dict(schema='researchos.nf5-actual-reviewer-choice-inverse.v1',base_ref=pin(base),candidate_ref=pin(Q/'review_actual_nf5.v2.py'),old_hex=old.hex(),new_hex=new.hex(),exact_inverse=True,
        original1155_preserved=pin(Q/'original1155.binding.json'),old_13_checks_repeated=False,Native_runs=0,formal_acceptance=False)
    with(Q/'choice-revision.inverse.json').open('xb')as f:f.write((json.dumps(inverse,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    print(json.dumps(dict(program_ref=pin(Q/'review_actual_nf5.v2.py'),contract_ref=pin(Q/'input-contract.v3.json'),guard_revision_ref=pin(Q/'close_prepared_Source_guard_revision.py'),exact_inverse=True,old_checks_repeated=False),ensure_ascii=False));return 0
if __name__=='__main__':
    rc=1
    try:rc=main()
    except BaseException:traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(rc));sys.exit(rc)
