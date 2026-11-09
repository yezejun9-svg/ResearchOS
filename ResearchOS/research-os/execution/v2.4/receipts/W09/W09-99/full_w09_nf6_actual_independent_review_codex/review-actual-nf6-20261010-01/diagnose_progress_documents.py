import ast,json,types
from pathlib import Path
Q=Path(__file__).resolve().parent
partial=Q/'review_partial_delta.py';tree=ast.parse(partial.read_bytes())
nodes=[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom,ast.Assign,ast.FunctionDef))]
lib=types.ModuleType('diagnose_progress');lib.__file__=str(partial)
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(partial)+'#definitions-only','exec'),lib.__dict__)
m=lib.support().reused_module()
ref=lib.progress_refs('W09-G01')['compiler-input-list']
pair=m.root_pair(ref);docs=[v for v in m.nested_documents(pair['actual_host_result']['output'])if type(v)is dict and v.get('progress')=='compiler-input-list']
print(json.dumps({'count':len(docs),'docs':docs,'exact_host_stdout':pair['actual_host_result']['output']},ensure_ascii=False))
print('ROOT_PYTHON_EXIT=0')
