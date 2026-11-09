import ast,json
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');Q=Path(__file__).resolve().parent
source=(R/'ops/ci/w09_evidence_closure.py').read_text(encoding='utf-8')
tree=ast.parse(source)
for node in tree.body:
    if isinstance(node,ast.FunctionDef) and node.name=='verify_native':
        for child in ast.walk(node):
            if isinstance(child,ast.Return):print(ast.get_source_segment(source,child))
packet=json.loads((Q/'partial-input-observed.json').read_text(encoding='utf-8'))
closed=json.loads(Path(packet['groups']['W09-G01']['producer_closed_ref']['path']).read_text(encoding='utf-8'))
report=json.loads(Path(closed['summary']['report_ref']['path']).read_text(encoding='utf-8'))
guard=json.loads(Path(closed['guard_cleanups'][0]['ref']['path']).read_text(encoding='utf-8'))
print(json.dumps({'version_manifest':report['version_manifest'],'guard_keys':list(guard),'entry0':guard['entries'][0]},ensure_ascii=False))
print('ROOT_PYTHON_EXIT=0')
