import ast,hashlib,json,types
from pathlib import Path
Q=Path(__file__).resolve().parent
path=Q/'review_partial_delta.py';tree=ast.parse(path.read_bytes());lib=types.ModuleType('inspect_four');lib.__file__=str(path)
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom,ast.Assign,ast.FunctionDef))],type_ignores=[]),str(path)+'#definitions','exec'),lib.__dict__)
m=lib.support().reused_module();S=lib.S
refs={'four':(S/'nf6-four-closed-actual-input.root.json','7233219f2478fab5a30533c0be3f8a8db987fd3b144eb1f8481657b09a2236bf',9401),'progress':(S/'nf6-four-progress-actual-input.root.json','18b288a60b890aa46542dc7d6294dd68e04fa0175fa65d95fb5aab5a15e2d569',3042)}
docs={}
for key,(p,sha,size)in refs.items():
    raw=p.read_bytes();lib.need(len(raw)==size and hashlib.sha256(raw).hexdigest()==sha,'FIXED_ROOT_'+key.upper());docs[key]=m.decode(raw)
rows={}
for key,row in docs['four']['groups'].items():
    rows[key]={}
    for kind in ('prepare_initial_Root_capture_ref','run_initial_Root_capture_ref','run_completed_Root_capture_ref'):
        pair=m.root_pair(row[kind]);rows[key][kind]={'chunk':pair['actual_host_result']['chunk_id'],'session':pair['actual_host_result'].get('session_id'),'exit':pair['actual_host_result'].get('exit_code'),'call_input':pair['call_payload'].get('input'),'stdout':pair['actual_host_result']['output'][:2200]}
out={'four_schema':docs['four']['schema'],'four_keys':list(docs['four']),'groups':rows,'progress':docs['progress']}
with(Q/'four-closed-observed-shape.json').open('xb')as stream:stream.write((json.dumps(out,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
print(json.dumps(out,ensure_ascii=False))
print('ROOT_PYTHON_EXIT=0')
