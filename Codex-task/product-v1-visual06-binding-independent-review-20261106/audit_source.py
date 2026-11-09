"""Read/hash/AST audit only; does not import or invoke any candidate."""
import ast
import hashlib
import json
from pathlib import Path

C = Path(__file__).resolve().parents[1]
D = Path('D:/作品集/ResearchOS/research-os')
OUT = Path(__file__).resolve().parent
def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''): h.update(b)
    return h.hexdigest()
def read(p): return json.loads(p.read_bytes())
candidate = C / 'product-v1-layout-visual-06-binding-candidate-20261106'
regpath = D / 'execution/product-v1/receipts/single-harness-20261104/build14-scope/registration.json'
reg = read(regpath)
wt = Path(reg['clean_worktree'])
pins = reg['source_sha256']
scopepath = C / 'product-v1-owned-verification-20261104/scopes/product-v1-build-14.json'
scope = read(scopepath)
tree = ast.parse((candidate/'register_visual06.py').read_text(encoding='utf-8'))
constants = {n.targets[0].id: ast.literal_eval(n.value) for n in tree.body
             if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name)
             and isinstance(n.value,(ast.Constant,ast.Tuple))}
files = []
for folder, name in [(candidate,'MANIFEST.json'), (C/'product-v1-native-layout-visual-prepare-12','MANIFEST.json')]:
    manifest = read(folder/name)
    for row in manifest['files']:
        p=folder/row['path']
        files.append(dict(path=str(p),sha256=sha(p),matches=sha(p)==row['sha256'],bytes_match=p.stat().st_size==row['bytes']))
source = [dict(path=p,expected_sha256=s,main_sha256=sha(D/p),worktree_sha256=sha(wt/p)) for p,s in pins.items()]
inputs = [dict(path=r['path'],expected_sha256=r['sha256'],actual_sha256=sha(Path(r['path']))) for r in scope['inputs']]
refs = [C/'product-v1-native-layout-visual12-independent-review-20261105/review-report.json',
        C/'product-v1-visual12-purechecks01-independent-review-20261105/review-report.json',
        C/'product-v1-owned-verification-20261104/owned_run.py',
        C/'researchos-workbench-assistant-newline-amended-review-20261105/review.json',
        regpath,scopepath,candidate/'MANIFEST.json',candidate/'register_visual06.py']
old=(C/'product-v1-workbench-assistant-refinement-20261105-freeze-03/candidate/apps/web/src/workbench.jsx').read_bytes()
current=(wt/'apps/web/src/workbench.jsx').read_bytes()
launcher='apps/desktop/launch-development.mjs'
report=dict(schema='researchos.independent-visual06-registrar-static-audit/1',
    registrar_ast_parse=True, files=files, reference_hashes={str(p):sha(p) for p in refs},
    source_count=len(source),source=source,source_all_match=all(r['main_sha256']==r['worktree_sha256']==r['expected_sha256'] for r in source),
    source_union_sha256=hashlib.sha256(json.dumps(pins,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
    selection_path_set_sha256=hashlib.sha256(json.dumps(sorted(pins),ensure_ascii=False,separators=(',',':')).encode()).hexdigest(),
    selector_source_sha256={p:pins[p] for p in constants['OWNERS']},
    build_scope_input_count=len(inputs),build_scope_inputs=inputs,build_scope_inputs_all_match=all(r['expected_sha256']==r['actual_sha256'] for r in inputs),
    launcher_in_source_union=launcher in pins,launcher_scope_input=[r for r in inputs if Path(r['path'])==wt/launcher],
    newline_amendment=dict(old_sha256=hashlib.sha256(old).hexdigest(),current_sha256=hashlib.sha256(current).hexdigest(),exact_single_CR_deletion_at_32692=(old[32692:32694]==b'\r\n' and old[:32692]+old[32693:]==current)),
    final_build_result_present=(C/'product-v1-owned-verification-20261104/runs/product-v1-build-14/RESULT.json').exists(),
    final_bundle_manifest_present=(Path(reg['bundle'])/'development-manifest.json').exists(),
    registration_executed=False,apps_tests_builds_native_model_executed=False,d_writes=0)
with (OUT/'source-audit.json').open('x',encoding='utf-8',newline='\n') as f: json.dump(report,f,ensure_ascii=False,indent=2); f.write('\n')
print(json.dumps({k:report[k] for k in ['registrar_ast_parse','source_count','source_all_match','source_union_sha256','selection_path_set_sha256','build_scope_input_count','build_scope_inputs_all_match','launcher_in_source_union','newline_amendment','final_build_result_present','final_bundle_manifest_present']},ensure_ascii=False))
