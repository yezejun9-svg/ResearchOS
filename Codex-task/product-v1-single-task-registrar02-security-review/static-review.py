"""Read-only AST/JSON review. Never import, compile-execute, or invoke registrar."""
import ast, hashlib, json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
script = ROOT / 'register_product_v1_single_task_flow02.py'
raw = script.read_bytes()
digest = hashlib.sha256(raw).hexdigest()
assert digest == '5b518d944ea0d5551a6bbe230036f1d785187ba39804c8a0f158a86ea76482d0'
tree = ast.parse(raw.decode('utf-8-sig'), filename=str(script))
def scope_path(node):
    if isinstance(node, ast.Name) and node.id == 'scope': return 'scope'
    if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
        base = scope_path(node.value)
        if base: return base + '.' + node.slice.value
    return None
writes = {}
for node in ast.walk(tree):
    if isinstance(node, ast.Assign):
        for target in node.targets:
            name = scope_path(target)
            if name and name != 'scope': writes[name] = {'line': node.lineno, 'expression': ast.unparse(node.value)}
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'update':
        name = scope_path(node.func.value)
        if name:
            for kw in node.keywords:
                if kw.arg: writes[name + '.' + kw.arg] = {'line': node.lineno, 'expression': ast.unparse(kw.value)}
template_path = ROOT / 'product-v1-real-electron-single-task-prepare-04/scope.template.json'
template = json.loads(template_path.read_bytes())
required = []
def walk(value, prefix='scope'):
    if isinstance(value, dict):
        for key, child in value.items(): walk(child, prefix + '.' + key)
    elif value is None or isinstance(value, str) and ('<ROOT-NEW-NONCE>' in value or value.startswith('NOT_RUN_TEMPLATE') or value == 'BUILD07_POST_ZERO_FLOW_INTEGRITY_RECHECK_REQUIRED'):
        required.append(prefix)
walk(template)
assert all(key in writes for key in required), [key for key in required if key not in writes]
assert writes['scope.source.pin_status']['expression'] == "'ROOT_VERIFIED_COMPLETE_INTEGRATED_SOURCE'"
assert writes['scope.bundle.source_binding_review']['expression'] == "'ROOT_VERIFIED_COMPLETE_INTEGRATED_SOURCE'"
source = raw.decode('utf-8-sig')
bundle_loop = next(n for n in tree.body if isinstance(n, ast.For) and ast.unparse(n.iter) == "m['files']")
source_loop = next(n for n in tree.body if isinstance(n, ast.For) and ast.unparse(n.iter) == 'pins.items()')
no_extra = next(n for n in tree.body if isinstance(n, ast.Assert) and 'BUNDLE.rglob' in ast.unparse(n))
native_gate = next(n for n in tree.body if isinstance(n, ast.Assert) and "read(nr)['decision']" in ast.unparse(n))
for key in ['scope.source.pin_status', 'scope.bundle.source_binding_review']:
    assert writes[key]['line'] > max(bundle_loop.end_lineno, source_loop.end_lineno, no_extra.end_lineno, native_gate.end_lineno)
assert source.index("scope['bundle']['source_binding_review']") < source.index('OUT.mkdir()')
assert "OUT=HERE/'product-v1-single-task-flow-02-registration'" in source
assert "scope_id='product-v1-single-task-flow-02'" in source
assert "sp=CONTROL/'scopes/product-v1-single-task-flow-02.json'" in source
assert "archive=BASE/'single-task-flow-02'" in source
assert 'secrets.token_hex(24)' in source and "assert not Path(scope['run_root']).exists()" in source
assert 'assert not p.exists()' in source and 'assert not OUT.exists()' in source
assert "meta_review,Path(__file__),previous/'RESULT.json',previous/'stdout.raw'" in source
prior = ROOT / 'product-v1-owned-verification-20261104/runs/product-v1-single-task-flow-01'
job = json.loads((prior/'RESULT.json').read_bytes())
failure = json.loads((prior/'stdout.raw').read_bytes())
consumed = json.loads((prior/'CONSUMED.json').read_bytes())
outer_file = ROOT/'product-v1-owned-verification-20261104/scopes/product-v1-single-task-flow-01.json'
inner_file = ROOT/'product-v1-single-task-flow-01-registration/real-flow.scope.json'
outer, inner = json.loads(outer_file.read_bytes()), json.loads(inner_file.read_bytes())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert job['scope_sha256'] == consumed['scope_sha256'] == sha(outer_file)
assert outer['argv'][-1] == sha(inner_file)
assert next(r for r in job['raw'] if r['file'] == 'stdout.raw')['sha256'] == sha(prior/'stdout.raw')
assert job['status'] == 'CHILD_NONZERO_STOPPED' and job['root_exit_code'] == 2
assert job['stop_proved'] and job['job_active_zero'] and job['job_total_processes'] == 2
assert job['job_assigned'] and job['resumed'] and job['root_signaled']
assert not job['errors'] and not job['input_drift'] and not job['automatic_retry']
assert job['terminate_job_attempts'] == job['terminate_original_root_attempts'] == 0
assert failure['code'] == 'SOURCE_BOUND_BUILD_REQUIRED' and failure['phase'] == 'PREFLIGHT'
assert failure['run_root'] is None and failure['electron_launch_attempted'] is False
assert failure['task_submissions'] == 0 and failure['model_outcome'] == 'NOT_RUN'
assert inner['bundle']['source_binding_review'] is None and not Path(inner['run_root']).exists()
runner = (ROOT/'product-v1-real-electron-single-task-prepare-04/real-electron-flow.mjs').read_text(encoding='utf-8')
assert runner.index("'SOURCE_BOUND_BUILD_REQUIRED'") < runner.index("activeRunEvidence.phase = 'CREATE_FRESH_RUN_ROOT'") < runner.index("activeRunEvidence.phase = 'ELECTRON_LAUNCH_ATTEMPTED'")
print(json.dumps({'status':'STATIC_AST_AND_C_EVIDENCE_CHECKS_PASS','registrar_sha256':digest,'registrar_executed':False,'required_template_fields':{k:writes[k] for k in required},'required_fields_missing':[],'metadata_after_verification':True,'informational_fields_retained':['scope.product_acceptance=NOT_RUN','scope.native_picker.runtime_verified=false','scope.native_picker.validation_warning.status=EXPECTED_TEXT_REQUIRES_INDEPENDENT_BUILD07_REVIEW'],'previous_failure':{'code':failure['code'],'phase':failure['phase'],'app_launch_attempted':False,'task_submissions':0,'model_outcome':'NOT_RUN','job_processes':job['job_total_processes'],'job_active_zero':True,'original_scope_consumed':True,'run_root_absent':True},'evidence_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [script,prior/'RESULT.json',prior/'stdout.raw',prior/'CONSUMED.json',inner_file,outer_file,template_path]},'formal_increment':0},indent=2))
