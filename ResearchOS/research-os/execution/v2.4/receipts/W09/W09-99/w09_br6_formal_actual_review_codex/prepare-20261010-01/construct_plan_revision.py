import ast
import hashlib
import json
import sys
import traceback
import types
from pathlib import Path

Q = Path(__file__).resolve().parent
R = Path('D:/作品集/ResearchOS/research-os')
PLAN = R.parent / 'ResearchOS_Implementation_Package_v2.4/contracts/execution.plan.json'
GUARD = R / 'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'

def pin(path):
    raw = Path(path).read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def save(name, value):
    path = Q / name
    with path.open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    return pin(path)

def main():
    base_path = Q / 'br6_actual_review.source.py'
    raw = base_path.read_bytes()
    assert pin(base_path)['sha256'] == '472eaea679f62b1cf7af286c7aaafa61b16446286622ef17d731f77819d851ee'
    replacements = [
        (b"HERE = Path(__file__).resolve().parent\n", b"HERE = Path(__file__).resolve().parent\nPLAN = ROOT.parent / 'ResearchOS_Implementation_Package_v2.4/contracts/execution.plan.json'\n"),
        (b"plan = reader.read(reader.path('contracts/execution.plan.json'))", b"plan = reader.read(PLAN.resolve(strict=True))"),
        (b"need(pin(input_ref['path']) == input_ref, 'INPUT_PIN')", b"observed_input = pin(input_ref['path'])\n    need(observed_input['sha256'] == input_ref['sha256'] and observed_input['bytes'] == input_ref['bytes'], 'INPUT_PIN')"),
        (b"need(authorized.get(guard_module._canonical(basis_ref['path'])) == basis_ref, 'BASIS_NOT_HELD')", b"held_basis = authorized.get(guard_module._canonical(basis_ref['path']))\n        need(held_basis is not None and same_ref(held_basis, basis_ref, guard_module._canonical), 'BASIS_NOT_HELD')"),
        (b"need(authorized.get(guard_module._canonical(ref['path'])) == ref, 'MAIN_SOURCE_NOT_HELD')", b"held_source = authorized.get(guard_module._canonical(ref['path']))\n            need(held_source is not None and same_ref(held_source, ref, guard_module._canonical), 'MAIN_SOURCE_NOT_HELD')"),
    ]
    revised = raw
    for before, after in replacements:
        assert revised.count(before) == 1
        revised = revised.replace(before, after, 1)
    restored = revised
    for before, after in reversed(replacements):
        assert restored.count(after) == 1
        restored = restored.replace(after, before, 1)
    assert restored == raw
    tree = ast.parse(revised)
    compile(revised, 'br6_actual_review.v2.source.py', 'exec')
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    assert any(isinstance(node.func, ast.Attribute) and node.func.attr == 'read'
               and node.args and ast.unparse(node.args[0]) == 'PLAN.resolve(strict=True)' for node in calls)
    delta = {'schema': 'researchos.w09-br6-review-preparation-delta.v1',
             'base_source_ref': pin(base_path), 'exact_inverse': restored == raw,
             'restored_sha256': hashlib.sha256(restored).hexdigest(),
             'changes': ['actual BR6 K-package PLAN identity', 'equivalent path spelling does not fail exact SHA/bytes pins'],
             'new_checks': ['AST_COMPILE_PASS', 'ACTUAL_PLAN_READ_BINDING_PASS', 'FULL_EXACT_INVERSE_PASS'],
             'prior18_controls_not_replayed': True, 'future_entry_called': False, 'formal_acceptance': False}
    source_path = Q / 'br6_actual_review.v2.source.py'
    with source_path.open('xb') as stream:
        stream.write(revised)
    source_ref = pin(source_path)
    contract = json.loads((Q / 'input-contract.json').read_text(encoding='utf-8'))
    contract['caller_ref'] = source_ref
    contract['plan_ref'] = pin(PLAN)
    contract['phase_one_future_argv'][6] = source_ref['path']
    contract['path_spelling_rule'] = 'physical canonical path identity and exact SHA/bytes; original reference spelling retained'
    contract['original_contract_ref'] = pin(Q / 'input-contract.json')
    contract['SourceOnly_static_revision'] = delta
    contract_ref = save('input-contract.v2.json', contract)
    delta_ref = save('new-plan-and-ref-spelling-delta.json', delta)
    guard_raw = GUARD.read_bytes()
    assert hashlib.sha256(guard_raw).hexdigest() == 'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
    module = types.ModuleType('br6_review_revision_guard'); module.__file__ = str(GUARD)
    exec(compile(guard_raw, str(GUARD), 'exec'), module.__dict__)
    guard = module.SourceReadGuard(per_file_cap=128 * 1024 * 1024, total_cap=512 * 1024 * 1024)
    try:
        guard.acquire([source_ref, contract_ref, delta_ref, pin(PLAN)])
        assert guard.get_buffer(source_ref['path']) == revised
    finally:
        closed = guard.close()
        close_ref = save('revision-SourceGuard.closed.json', closed)
    assert closed['closed'] and closed['retained_handles_count'] == 0 and closed['errors'] == []
    result = save('preparation.v2.result.json', {
        'schema': 'researchos.w09-br6-formal-actual-review-preparation.v1',
        'status': 'PREPARED_NOT_EXECUTED_WAITING_ROOT_ACTUAL_INPUTS',
        'caller_ref': source_ref, 'contract_ref': contract_ref, 'delta_ref': delta_ref,
        'guard_ref': close_ref, 'previous_preparation_ref': pin(Q / 'preparation.result.json'),
        'future_review_ref': None, 'formal_acceptance': False, 'execution_grant': False,
        'Source_controls': {'initial_passed': 18, 'initial_replayed': 0, 'new_static_passed': 3},
        'Main_Canon_Scope_writes': 0, 'product_calls': 0})
    print(json.dumps({'result_ref': result, 'caller_ref': source_ref, 'contract_ref': contract_ref,
                      'new_checks': 3, 'closed': True, 'retained_handles_count': 0}, ensure_ascii=False))
    return 0

if __name__ == '__main__':
    try:
        code = main()
    except BaseException:
        traceback.print_exc(); code = 1
    print('ROOT_PYTHON_EXIT=' + str(code))
    sys.exit(code)
