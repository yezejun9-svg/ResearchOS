import ast,hashlib,json,types
from pathlib import Path
Q=Path(__file__).resolve().parent;B=Q.parent.parent
def pin(p):
    r=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(r).hexdigest(),bytes=len(r))
def save(n,v):
    p=Q/n
    with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
    return pin(p)
def main():
    root=B/'schema21_programme_builder_independent_source_review_codex/review-main21b-20261010-01'
    refs=dict(hdf=dict(path=(root/'HDF.json').as_posix(),sha256='5c50677387c3d737561124eb1cd4b0d0e0b87e9ebdb5bce38f1230a6dd697ed1',bytes=4353),mf=dict(path=(root/'MF.json').as_posix(),sha256='15047b67e37c5423a2a5a711111f2e3580bd88cbd818d58a0ae3c86c366c0a06',bytes=8413),decision=dict(path=(root/'decision.json').as_posix(),sha256='820a39f52557593591877f47f346321a97cffd5229adf98dcc9fc2a71f5937ee',bytes=7082))
    guardmodule=types.ModuleType('finite_Task68_guard');guardmodule.__file__=str(Q/'read_Task69_basis_revision.py');exec(compile(Path(guardmodule.__file__).read_bytes(),guardmodule.__file__,'exec'),guardmodule.__dict__);guard=guardmodule.Guard()
    closed=False
    try:
        vals={}
        for k,r in refs.items():raw,_=guard.read(r['path'],r);vals[k]=json.loads(raw)
        p=Q/'old21_root.source.py';old=p.read_bytes();initial=Q/'old21_root.source.pre-Task68.py'
        with initial.open('xb') as f:f.write(old)
        text=old.decode('utf-8');line='_guard_module = None'
        assert text.count(line)==1;text=text.replace(line,'BUILDER_ACCEPTED_REVIEW_REFS = '+repr(refs)+'\n'+line)
        anchor='    need(review.get("status") == "SOURCE_ACCEPTED_FOR_ROOT_REGISTRATION"'
        assert text.count(anchor)==1
        extra='    need(all(same_ref(review_refs[k], BUILDER_ACCEPTED_REVIEW_REFS[k]) for k in review_refs), "EXACT_ACCEPTED_OLD21_SOURCE_REVIEW")\n'
        text=text.replace(anchor,extra+anchor)
        compile(text,str(p),'exec');p.write_bytes(text.encode('utf-8'))
        save('Task68-review-pin-revision.inverse.json',dict(schema='researchos.exact-Source-pin-revision.v1',initial_ref=pin(initial),candidate_ref=pin(p),inserted_constant='BUILDER_ACCEPTED_REVIEW_REFS = '+repr(refs)+'\n',inserted_condition=extra,full_inverse_verified=text.replace('BUILDER_ACCEPTED_REVIEW_REFS = '+repr(refs)+'\n','').replace(extra,'').encode()==old,previous_inverse_ref=pin(Q/'numbered-SQL-exact-revision.inverse.json')))
        # One new actual Source-schema/pin check; not a new review or runtime grant.
        module=types.ModuleType('actual_Task68_source_check');module.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),module.__dict__)
        basis=json.loads((Q/'source-inputs.basis.json').read_text(encoding='utf-8'))
        source=json.loads(Path(basis['builder_source_hdf_ref']['path']).read_text(encoding='utf-8'));mf=json.loads(Path(basis['builder_source_mf_ref']['path']).read_text(encoding='utf-8'));contract=json.loads(Path(source['contract_ref']['path']).read_text(encoding='utf-8'))
        for r in basis['references']+[pin(p)]:guard.read(r['path'],r)
        module.validate_builder_chain(refs,vals['hdf'],vals['mf'],vals['decision'],source,mf,contract)
        altered={k:dict(v) for k,v in refs.items()};altered['decision']['bytes']+=1
        try:module.validate_builder_chain(altered,vals['hdf'],vals['mf'],vals['decision'],source,mf,contract)
        except ValueError as e:assert str(e)=='EXACT_ACCEPTED_OLD21_SOURCE_REVIEW'
        else:raise AssertionError('mutated review pin accepted')
        closure=save('actual-Task68-review.guard.closed.json',guard.close());closed=True
        result=save('actual-Task68-review-source-binding.json',dict(schema='researchos.actual-old21-builder-Source-review-binding.v1',review_refs=refs,builder_Source_refs=module.BUILDER_SOURCE_REFS,review_author=vals['decision']['review_author'],source_author=vals['decision']['source_author'],Source_chain_and_exact_pin_controls_pass=2,previous25_controls_ref=pin(Q/'finite-delta-controls.json'),previous25_scope='Pre exact accepted-review pin condition; not reexecuted',guard_ref=closure,actual_Root_delivery_witness=None,Root_scope_grant=None,runtime_qualification=None,programme_qualification=None,formal_acceptance=False,execution_grant=False))
        print(json.dumps(dict(caller_ref=pin(p),actual_Source_review_binding_ref=result,guard_ref=closure,Source_delta_controls_pass=2),ensure_ascii=False))
    finally:
        if not closed and any(not s.closed for s,_,_ in guard.held):save('actual-Task68-attempt-failure.guard.closed.json',guard.close())
if __name__=='__main__':
    try:main()
    except BaseException:print('ROOT_PYTHON_EXIT=1');raise
    print('ROOT_PYTHON_EXIT=0')
