import ast,json,sys,traceback
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');Q=Path(__file__).resolve().parent
def main():
    source=(R/'ops/ci/w09_evidence_closure.py').read_text(encoding='utf-8');tree=ast.parse(source)
    function=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='verify_owned')
    text=ast.get_source_segment(source,function)
    basis=json.loads((Q/'partial-basis-shapes.json').read_bytes())
    result=dict(verify_owned_source=text,captures={key:{field:row['binding']for field,row in value['captures'].items()}for key,value in basis.items()})
    with (Q/'remaining-review-shapes.json').open('xb')as f:f.write((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    print(text)
    return 0
if __name__=='__main__':
    rc=1
    try:rc=main()
    except BaseException:traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(rc));sys.exit(rc)
