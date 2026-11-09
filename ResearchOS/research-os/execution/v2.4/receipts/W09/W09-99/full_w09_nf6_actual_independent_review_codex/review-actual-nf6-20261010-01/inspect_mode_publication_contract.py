import ast,json
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');Q=Path(__file__).resolve().parent
source=(R/'ops/ci/w09_evidence_closure.py').read_text(encoding='utf-8')
for node in ast.parse(source).body:
    if isinstance(node,ast.FunctionDef)and node.name=='verify_mode':print(ast.get_source_segment(source,node))
shape=json.loads((Q/'six-mode-schema.json').read_text(encoding='utf-8'))
print(json.dumps(shape,ensure_ascii=False))
facts=json.loads((Q/'W09-G02.actual.facts.json').read_text(encoding='utf-8'))
print(json.dumps({'G02_mode_facts':facts['mode_predicate_facts'],'G02_job_summary':facts['jobs']},ensure_ascii=False))
print('ROOT_PYTHON_EXIT=0')
