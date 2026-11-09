import ast
from pathlib import Path

Q = Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W09/W09-99/full_w09_nf6_actual_independent_review_codex/review-actual-nf6-20261010-01')
old = Q.parent.parent / 'full_w09_nf5_actual_independent_review_codex' / 'review-actual-nf5-20261010-01' / 'review_actual_nf5.v7.py'
for path, selected in [(old, {'root_pair','root_capture','review_group','reviewed_launcher_tail','collect_actual_refs'}), (Q / 'review_partial_actual.py', {'mode_facts','main','reused_module'})]:
    source = path.read_text(encoding='utf-8')
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in selected:
            print('SOURCE ' + str(path) + ':' + str(node.lineno) + ' ' + node.name)
            print(ast.get_source_segment(source, node))
print('ROOT_PYTHON_EXIT=0')
