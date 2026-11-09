import ast,hashlib,json,sys,traceback
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W09/W09-99';Q=Path(__file__).resolve().parent
P=B/'full_w09_main_native_producer_source_codex/fullw09-20261010-06';G=B/'w09_nf6_root_registration_source_codex/register-20261010-01'
def pin(p):
    raw=Path(p).read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def doc(p):return json.loads(Path(p).read_bytes())
def slim(v):
    if type(v)is dict:return {k:dict(type='dict',keys=list(x))if type(x)is dict and set(x)!={'path','sha256','bytes'}else dict(type='list',count=len(x))if type(x)is list else x for k,x in v.items()}
    return v
def main():
    ph=doc(P/'HDF.json');rh=doc(G/'HDF.json');pc=doc(ph['calling_contract_ref']['path']);rc=doc(rh['contract_ref']['path'])
    choice=doc(ph['source_choice_ref']['path']);bp=doc(ph['compiler_blueprint_ref']['path']);inputs=doc(rh['input_pins_ref']['path'])
    code={}
    for key,ref in dict(runtime=ph['runtime_ref'],overrides=ph['overrides_ref'],launcher=ph['launcher_ref'],caller=rh['caller_ref'],core=rh['core_ref']).items():
        tree=ast.parse(Path(ref['path']).read_text(encoding='utf-8'))
        code[key]=dict(ref=ref,functions=[dict(name=n.name,line=n.lineno,end=n.end_lineno)for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))])
    result=dict(producer_hdf_ref=pin(P/'HDF.json'),registrar_hdf_ref=pin(G/'HDF.json'),producer_contract=pc,registrar_contract=rc,
        choice_fields=slim(choice),blueprint_fields=slim(bp),registration_inputs_fields=slim(inputs),code=code,
        producer_inverse_ref=ph['source_delta_ref'],registration_inverse_ref=rh['source_delta_ref'])
    out=Q/'basis-index.json'
    with out.open('xb')as f:f.write((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    print(json.dumps(dict(basis_ref=pin(out),choice_fields=slim(choice),blueprint_fields=slim(bp),registration_inputs_fields=slim(inputs),code=code),ensure_ascii=False))
    return 0
if __name__=='__main__':
    rc=1
    try:rc=main()
    except BaseException:traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(rc));sys.exit(rc)
