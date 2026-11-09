import ast
from pathlib import Path

R = Path('D:/作品集/ResearchOS/research-os')
for rel, names in {
    'execution/v2.4/formal_case_index.py': {'Reader', '_profile_api'},
    'execution/v2.4/formal_profile_w09.py': {'_trusted_closure', '_router_contract', '_producer_sources', '_review_execution_cutoff'},
}.items():
    text = (R / rel).read_text(encoding='utf-8')
    tree = ast.parse(text)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names:
            print(rel, node.lineno)
            print(ast.get_source_segment(text, node))
print('ROOT_PYTHON_EXIT=0')
