"""Preserve failed original; replace only named literal AST resolver."""
from pathlib import Path
import ast, hashlib, json, sys, traceback
Q=Path(__file__).resolve().parent
def main():
    path=Q/'review_source.py'; raw=path.read_bytes()
    old=b'            return ast.literal_eval(n.value)'
    new=b'            return strict_literal(tree, n.value)'
    if raw.count(old)!=1: raise AssertionError('EXACT_ONE_CONST_RETURN')
    helper='''def strict_literal(tree, node):
    if isinstance(node, ast.Name):
        if node.id not in {'GUARD','TP','OWNED'}:
            raise AssertionError('UNKNOWN_LITERAL_NAME:'+node.id)
        actual = next(n for n in tree.body if isinstance(n,ast.Assign)
                      and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)
                      and n.targets[0].id==node.id)
        value = ast.literal_eval(actual.value)
        if type(value) is not str: raise AssertionError('NAME_LITERAL_STRING')
        return value
    if isinstance(node,ast.Dict):
        return {strict_literal(tree,k):strict_literal(tree,v) for k,v in zip(node.keys,node.values)}
    return ast.literal_eval(node)

'''.encode('utf-8')
    marker=b'def const(tree, name):'
    if raw.count(marker)!=1: raise AssertionError('EXACT_CONST_MARKER')
    result=raw.replace(old,new).replace(marker,helper+marker)
    ast.parse(result); compile(result,'review_source_revision.py','exec')
    inverse=result.replace(helper,b'',1).replace(new,old,1)
    if inverse!=raw: raise AssertionError('EXACT_INVERSE_BYTES')
    with (Q/'review_source_revision.py').open('xb') as f: f.write(result)
    doc={'schema':'researchos.Source-mechanical-resolver-revision.v1','original1144_preserved':True,'base_ref':{'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)},'revision_ref':{'path':str(Q/'review_source_revision.py'),'sha256':hashlib.sha256(result).hexdigest(),'bytes':len(result)},'original_bytes_restored_exactly':True,'Name_allowlist':['GUARD','TP','OWNED'],'bridge_Source_or_Main_changed':False,'runtime_stages_called':False}
    with (Q/'review-resolver-exact-inverse.json').open('xb') as f: f.write((json.dumps(doc,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    print(json.dumps(doc,ensure_ascii=False)); return 0
if __name__=='__main__':
    code=1
    try: code=main()
    except BaseException: traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(code));sys.exit(code)
