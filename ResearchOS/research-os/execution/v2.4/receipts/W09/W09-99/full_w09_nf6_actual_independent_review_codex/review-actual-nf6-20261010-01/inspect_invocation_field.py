import ast,json
from pathlib import Path
Q=Path(__file__).resolve().parent
source=(Q.parent.parent/'full_w09_nf5_actual_independent_review_codex/review-actual-nf5-20261010-01/review_actual_nf5.v7.py').read_text(encoding='utf-8')
for node in ast.parse(source).body:
    if isinstance(node,ast.FunctionDef)and node.name=='job':print(ast.get_source_segment(source,node))
packet=json.loads((Q/'partial-input-observed.json').read_text(encoding='utf-8'))
closed=json.loads(Path(packet['groups']['W09-G01']['producer_closed_ref']['path']).read_text(encoding='utf-8'))
for row in closed['invocation_observations']:
    doc=json.loads(Path(row['ref']['path']).read_text(encoding='utf-8'))
    print(json.dumps({'label':row['label'],'keys':list(doc),'observation':doc.get('observation')},ensure_ascii=False))
print('ROOT_PYTHON_EXIT=0')
