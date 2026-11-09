import ast,hashlib,json,sys,traceback
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');Q=Path(__file__).resolve().parent
C=R/'execution/v2.4/receipts/W05/W05-99/public22_to_main23_continuation_caller_source_codex/continue-20261010-01'
def pin(p):
    raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def main():
    h=json.loads((C/'HDF.json').read_bytes());i=json.loads(Path(h['source_inputs_ref']['path']).read_bytes());src=Path(h['caller_ref']['path']).read_bytes();tree=ast.parse(src)
    records={k:dict(type=type(v).__name__,length=len(v)if type(v)in(dict,list,str)else None,keys=list(v)if type(v)is dict else None)for k,v in i.items()}
    direct={k:v for k,v in i.items()if type(v)is dict and set(v)=={'path','sha256','bytes'}}
    resources=i.get('source_resource_refs',[])
    result=dict(HDF_ref=pin(C/'HDF.json'),MF_ref=pin(C/'MF.json'),source_fields=records,direct_refs=direct,source_resource_count=len(resources),private_resource_ref_paths=[r.get('path')for r in resources if type(r)is dict and ('/private/'in str(r.get('path','')).replace('\\','/').lower()or str(r.get('path','')).lower().endswith(('.key','owner.token')))],Source_functions=[dict(name=n.name,line=n.lineno,end=n.end_lineno)for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))],source_changes=json.loads((C/'source-changes.json').read_bytes()),source_decision=json.loads((C/'source-decision.json').read_bytes()),source_controls=json.loads((C/'delta-source-controls.json').read_bytes()))
    p=Q/'basis-index.json'
    with p.open('xb')as f:f.write((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    print(json.dumps(dict(basis_ref=pin(p),basis=result),ensure_ascii=False));return 0
if __name__=='__main__':
    rc=1
    try:rc=main()
    except BaseException:traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(rc));sys.exit(rc)
