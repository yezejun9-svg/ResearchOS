import ast,hashlib,json,sys,traceback
from pathlib import Path
Q=Path(__file__).resolve().parent
def pin(p):
    b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def write(name,obj):
    p=Q/name
    with p.open('xb')as f:f.write(obj if type(obj)is bytes else(json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    return pin(p)
def main():
    base=Q/'review_actual_nf5.v3.py';raw=base.read_bytes()
    assert hashlib.sha256(raw).hexdigest()=='1bd82953aac2fab96fb659e3ccc9c5e837b787cb85f6e9cdee6f8e270f5a85d4'
    text=raw.decode('utf-8');nl='\r\n'if '\r\n'in text else '\n';edits=[]
    def change(before,after):
        nonlocal text
        before=before.replace('\n',nl);after=after.replace('\n',nl)
        assert text.count(before)==1
        start=text.index(before);edits.append(dict(start=start,before=before,after=after))
        text=text[:start]+after+text[start+len(before):]
    change("    return dict(binding_ref=binding_ref,raw_ref=b['original_capture_ref'],binding_sha256=b.get('binding_sha256'),",
           "    return dict(binding_ref=binding_ref,binding_schema=b['schema'],raw_ref=b['original_capture_ref'],binding_sha256=b.get('binding_sha256'),")
    change("    require(pair['binding_sha256']==artifact_ref['sha256']and has_ref(pair['output_payload'],artifact_ref),'STRUCTURED_ACTUAL_ROOT_ARTIFACT_REF_REQUIRED')",
           "    require(((pair['binding_schema']=='researchos.w09-native-producer.actual-audit.v1'and pair['binding_sha256']==artifact_ref['sha256'])\n        or(pair['binding_schema']=='researchos.root-native-actual-host-pair.v1'and pair['binding_sha256']is None))\n        and has_ref(pair['output_payload'],artifact_ref),'STRUCTURED_ACTUAL_ROOT_ARTIFACT_REF_REQUIRED')")
    ast.parse(text);restored=text
    for e in reversed(edits):
        assert restored[e['start']:e['start']+len(e['after'])]==e['after']
        restored=restored[:e['start']]+e['before']+restored[e['start']+len(e['after']):]
    assert restored.encode('utf-8')==raw
    old_ast=ast.parse(raw);new_ast=ast.parse(text)
    unchanged={n.name:ast.dump(n,include_attributes=False)for n in old_ast.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))and n.name not in('root_pair','root_capture')}
    assert unchanged=={n.name:ast.dump(n,include_attributes=False)for n in new_ast.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))and n.name not in('root_pair','root_capture')}
    candidate=write('review_actual_nf5.v4.py',text.encode('utf-8'))
    inverse=write('Root-host-schema-revision.inverse.json',dict(schema='researchos.readonly-review-source-exact-inverse.v1',base_ref=pin(base),
        candidate_ref=candidate,edits=edits,exact_inverse_byte_equal=True,unchanged_functions_classes=len(unchanged),
        changed_only=['root_pair recorded binding_schema','root_capture consumes exact known host-pair schema plus structured complete artifact ref'],
        C19_refusal_preserved=True,old_controls_rerun=False,Native_runs=0,Go_runs=0,formal_acceptance=False))
    contract=json.loads((Q/'input-contract.v4.json').read_text(encoding='utf-8'));contract['reviewer_program_ref']=candidate
    contract['future_argv'][6]=candidate['path'];contract['previous_contract_ref']=pin(Q/'input-contract.v4.json')
    contract['Root_run_capture_schemas']=['researchos.w09-native-producer.actual-audit.v1','researchos.root-native-actual-host-pair.v1']
    contract['Root_run_capture_binding']='Both require exact actual Root header/call/output and immutable offset/hash/bytes, exact current invocation structured path/sha/bytes in returned output; original audit schema additionally binds binding_sha256.'
    contract['inverse_ref']=inverse
    cref=write('input-contract.v5.json',contract)
    print(json.dumps(dict(program_ref=candidate,contract_ref=cref,inverse_ref=inverse,AST_and_inverse_pass=True,unchanged_functions_classes=len(unchanged)),ensure_ascii=False));return 0
if __name__=='__main__':
    rc=1
    try:rc=main()
    except BaseException:traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(rc));sys.exit(rc)
