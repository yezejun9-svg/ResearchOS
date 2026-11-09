"""Source-only exact Main resource rebase; never invokes the review entry."""
import ast
import copy
import difflib
import hashlib
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('D:/作品集/ResearchOS/research-os')
HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parent / 'prepare-20261010-01'
AUTHOR = 'codex:/root/backup_regression_resources'
BACKEND = '/root/backup_regression_resources'
THREAD = '01a11cee-bf59-7a01-be0e-9f799f9b1084'
ROOT_THREAD = '01a11007-5233-7ca1-b71f-9e9e5ce84c98'
GUARD = ROOT / 'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
GUARD_PIN = 'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
HDF_PIN = '14f8602c8918d608f2b11e51405a960bc70a178e8de8e33ac41c42fc4e5fa1e6'
MF_PIN = 'cd3659e8c2c0b6aadfca3a00b194863a54f1790f012fbc19ffcf1383b254f640'
ADOPTION = ROOT / 'execution/v2.4/receipts/W09/W09-99/main_w09_formal_router_sequence_root/fix-20261010-01/Main-adoption.closed.root.json'
ADOPTION_PIN = '6d2389c04f99f6a4f691d6a059a38f277cd26b2db7c04efa8e6a9f25f03b5e31'
NEW_MAIN = {'path': str(ROOT / 'execution/v2.4/formal_profile_w09.py'), 'sha256': '1e04865beef37fdbffa06d649d072721d7b6eb0ef5e525d87bb867da414e4087', 'bytes': 71403}
PYTHON = {'path': 'C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe', 'sha256': 'cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b', 'bytes': 106328}

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def reference(path, raw=None):
    path = Path(path)
    if raw is None:
        raw = path.read_bytes()
    return {'path': str(path), 'sha256': digest(raw), 'bytes': len(raw)}

def checked(path, sha, size):
    raw = Path(path).read_bytes()
    if digest(raw) != sha or len(raw) != size:
        raise ValueError('Source pin mismatch: ' + str(path))
    return raw

def publish(name, value):
    path = HERE / name
    if path.exists():
        raise FileExistsError('immutable Source member already exists: ' + name)
    raw = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').replace('\n', '\r\n').encode('utf-8')
    path.write_bytes(raw)
    return reference(path, raw)

def only_once(raw, old, new):
    if raw.count(old) != 1:
        raise ValueError('exact byte-span cardinality differs')
    return raw.replace(old, new, 1)

def same_ref(a, b, canonical):
    return canonical(a['path']) == canonical(b['path']) and a['sha256'] == b['sha256'] and a['bytes'] == b['bytes']

def main():
    if HERE.name != 'prepare-20261010-02':
        raise ValueError('exclusive new namespace differs')
    reserved = ['basis.json', 'br6_actual_review.v3.source.py', 'input-contract.v3.json', 'rebase-metadata.json', 'rebase-controls.result.json', 'rebase-SourceGuard.closed.json']
    if any((HERE / name).exists() for name in reserved):
        raise FileExistsError('immutable output already present')
    old_hdf_raw = checked(PREVIOUS / 'HDF.json', HDF_PIN, 11537)
    old_mf_raw = checked(PREVIOUS / 'MF.json', MF_PIN, 7619)
    old_hdf = json.loads(old_hdf_raw.decode('utf-8'))
    guard_raw = checked(GUARD, GUARD_PIN, 11404)
    module_spec = importlib.util.spec_from_file_location('br6_main_rebase_source_guard', GUARD)
    guard_module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(guard_module)
    guard = guard_module.SourceReadGuard(per_file_cap=128 * 1024 * 1024, total_cap=512 * 1024 * 1024)
    refs = [reference(PREVIOUS / 'HDF.json', old_hdf_raw), reference(PREVIOUS / 'MF.json', old_mf_raw)]
    refs.extend(old_hdf[key] for key in ['caller_ref', 'contract_ref', 'basis_ref', 'decision_ref', 'future_input_template_ref'])
    refs.extend([NEW_MAIN, {'path': str(ADOPTION), 'sha256': ADOPTION_PIN, 'bytes': 2138}, reference(GUARD, guard_raw), PYTHON])
    closure = None
    controls = []
    try:
        guard.acquire(refs)
        old_caller = guard.get_buffer(old_hdf['caller_ref']['path'])
        old_basis_raw = guard.get_buffer(old_hdf['basis_ref']['path'])
        old_basis = json.loads(old_basis_raw.decode('utf-8'))
        old_contract = json.loads(guard.get_buffer(old_hdf['contract_ref']['path']).decode('utf-8'))
        adoption = json.loads(guard.get_buffer(str(ADOPTION)).decode('utf-8'))
        current_main = guard.get_buffer(NEW_MAIN['path'])
        old_main = old_contract['Main_profile_ref']
        if not same_ref(adoption['target_before_ref'], old_main, guard_module._canonical):
            raise ValueError('actual adoption before does not bind previous Main')
        if not same_ref(adoption['target_after_ref'], NEW_MAIN, guard_module._canonical):
            raise ValueError('actual adoption after does not bind new Main')
        if adoption['writer'] != 'codex:/root' or adoption['Main_integrated'] is not True or adoption['formal_acceptance'] is not False:
            raise ValueError('actual adoption boundary differs')
        main_refs = [r for r in old_basis['source_refs'] if guard_module._canonical(r['path']) == guard_module._canonical(NEW_MAIN['path'])]
        if len(main_refs) != 1 or not same_ref(main_refs[0], old_main, guard_module._canonical):
            raise ValueError('basis does not bind exactly one old Main')
        new_basis_raw = only_once(old_basis_raw, old_main['sha256'].encode('ascii'), NEW_MAIN['sha256'].encode('ascii'))
        old_bytes = ('"bytes": ' + str(old_main['bytes'])).encode('ascii')
        new_bytes = ('"bytes": ' + str(NEW_MAIN['bytes'])).encode('ascii')
        new_basis_raw = only_once(new_basis_raw, old_bytes, new_bytes)
        expected_basis = copy.deepcopy(old_basis)
        index = old_basis['source_refs'].index(main_refs[0])
        expected_basis['source_refs'][index] = dict(main_refs[0], sha256=NEW_MAIN['sha256'], bytes=NEW_MAIN['bytes'])
        if json.loads(new_basis_raw.decode('utf-8')) != expected_basis:
            raise ValueError('basis delta exceeds one Main ref')
        restored_basis = only_once(new_basis_raw, NEW_MAIN['sha256'].encode('ascii'), old_main['sha256'].encode('ascii'))
        restored_basis = only_once(restored_basis, new_bytes, old_bytes)
        if restored_basis != old_basis_raw:
            raise ValueError('basis inverse is not byte exact')
        new_basis_ref = reference(HERE / 'basis.json', new_basis_raw)
        if len(new_basis_raw) != old_hdf['basis_ref']['bytes']:
            raise ValueError('basis byte count changed unexpectedly')
        old_caller_span = ('BASIS_SHA = ' + repr(old_hdf['basis_ref']['sha256'])).encode('ascii')
        new_caller_span = ('BASIS_SHA = ' + repr(new_basis_ref['sha256'])).encode('ascii')
        new_caller = only_once(old_caller, old_caller_span, new_caller_span)
        restored_caller = only_once(new_caller, new_caller_span, old_caller_span)
        if restored_caller != old_caller:
            raise ValueError('caller inverse is not byte exact')
        old_ast = ast.dump(ast.parse(old_caller.decode('utf-8')), include_attributes=False)
        new_ast = ast.dump(ast.parse(new_caller.decode('utf-8')), include_attributes=False)
        if old_ast != new_ast.replace(new_basis_ref['sha256'], old_hdf['basis_ref']['sha256']):
            raise ValueError('caller AST delta exceeds basis constant')
        compile(new_caller.decode('utf-8'), 'br6_actual_review.v3.source.py', 'exec')
        compile(current_main.decode('utf-8'), str(NEW_MAIN['path']), 'exec')
        controls = [
            {'id': 'ACTUAL_MAIN_PIN_AND_ADOPTION_BEFORE_AFTER', 'status': 'PASS'},
            {'id': 'BASIS_SINGLE_REF_AND_BYTE_EXACT_INVERSE', 'status': 'PASS', 'restored_sha256': digest(restored_basis)},
            {'id': 'CALLER_AST_SINGLE_CONSTANT_AND_BYTE_EXACT_INVERSE', 'status': 'PASS', 'restored_sha256': digest(restored_caller)},
            {'id': 'CALLER_AND_CURRENT_MAIN_AST_COMPILE_NO_EXECUTION', 'status': 'PASS'},
        ]
        (HERE / 'basis.json').write_bytes(new_basis_raw)
        (HERE / 'br6_actual_review.v3.source.py').write_bytes(new_caller)
        caller_ref = reference(HERE / 'br6_actual_review.v3.source.py', new_caller)
        contract = copy.deepcopy(old_contract)
        contract['caller_ref'] = caller_ref
        contract['Main_profile_ref'] = dict(old_main, sha256=NEW_MAIN['sha256'], bytes=NEW_MAIN['bytes'])
        contract['basis_ref'] = new_basis_ref
        contract['phase_one_future_argv'][6] = caller_ref['path']
        contract['previous_preparation_contract_ref'] = old_hdf['contract_ref']
        contract['Main_pin_rebase'] = {
            'schema': 'researchos.w09-formal-review-preparation-main-rebase.v1',
            'actual_adoption_ref': refs[-3],
            'previous_hdf_ref': refs[0],
            'previous_mf_ref': refs[1],
            'previous_caller_ref': old_hdf['caller_ref'],
            'previous_basis_ref': old_hdf['basis_ref'],
            'basis_change': 'only existing source_refs Main SHA/bytes; all embedded BR6 material is historical unchanged input',
            'caller_change': 'only BASIS_SHA constant; basis byte count remains 31811',
            'prior_controls_reused_not_replayed': '18 + 3 Source controls and four Native/six Modes',
            'BR7_Source_review': 'OPEN_PENDING_EXACT_SEALED_INPUTS_SEPARATE_NONAUTHOR_TASK',
            'future_current4': 'dynamic actual pins; no CP387 or later grant is manufactured',
            'future_actual_review_called': False,
            'Root_stages_called': 0,
            'execution_grant': False,
            'formal_acceptance': False,
        }
        if contract['existing_six_Mode_refs'] != old_contract['existing_six_Mode_refs'] or contract['OPEN'] != old_contract['OPEN']:
            raise ValueError('future or Native/Mode contract changed')
        contract_ref = publish('input-contract.v3.json', contract)
        metadata = {
            'schema': 'researchos.w09-formal-review-main-rebase-metadata.v1',
            'Source_author': AUTHOR, 'backend_actor': BACKEND,
            'author_thread': THREAD, 'Root_thread': ROOT_THREAD,
            'created_utc': datetime.now(timezone.utc).isoformat(),
            'previous_preparation_hdf_ref': refs[0], 'previous_preparation_mf_ref': refs[1],
            'previous_caller_ref': old_hdf['caller_ref'], 'previous_basis_ref': old_hdf['basis_ref'],
            'previous_contract_ref': old_hdf['contract_ref'], 'previous_decision_ref': old_hdf['decision_ref'],
            'old_Main_ref': old_main, 'new_Main_ref': NEW_MAIN,
            'actual_adoption_ref': refs[-3], 'caller_ref': caller_ref,
            'basis_ref': new_basis_ref, 'contract_ref': contract_ref,
            'future_input_template_ref': old_hdf['future_input_template_ref'],
            'Source_inputs_held': refs,
            'inverse': {'caller_restored_sha256': digest(restored_caller), 'basis_restored_sha256': digest(restored_basis), 'exact': True},
            'new_control_count': len(controls), 'controls': controls,
            'prior_controls_not_replayed': '18+3, all prior Native and Mode success',
            'future_actual_review_called': False, 'execution_grant': False,
            'formal_acceptance': False, 'Main_Canon_Scope_writes': 0,
            'Native_calls': 0, 'Go_calls': 0, 'SQLite_calls': 0, 'model_calls': 0, 'TP_calls': 0,
        }
        publish('rebase-metadata.json', metadata)
        publish('rebase-controls.result.json', {'schema': 'researchos.w09-formal-review-main-pin-controls.v1', 'controls': controls, 'prior18plus3_not_replayed': True, 'entry_called': False})
        for label, before, after in [('basis', old_basis_raw, new_basis_raw), ('caller', old_caller, new_caller)]:
            delta = ''.join(difflib.unified_diff(before.decode('utf-8').splitlines(keepends=True), after.decode('utf-8').splitlines(keepends=True), fromfile='previous/' + label, tofile='new/' + label))
            (HERE / (label + '.exact.diff')).write_bytes(delta.encode('utf-8'))
        publish('inverse.json', {'schema': 'researchos.byte-exact-main-rebase-inverse.v1', 'caller': {'before_ref': old_hdf['caller_ref'], 'after_ref': caller_ref, 'old_span': old_caller_span.decode('ascii'), 'new_span': new_caller_span.decode('ascii'), 'inverse_sha256': digest(restored_caller)}, 'basis': {'before_ref': old_hdf['basis_ref'], 'after_ref': new_basis_ref, 'old_sha256': old_main['sha256'], 'new_sha256': NEW_MAIN['sha256'], 'old_byte_span': old_bytes.decode('ascii'), 'new_byte_span': new_bytes.decode('ascii'), 'inverse_sha256': digest(restored_basis)}, 'exact_inverse': True})
    finally:
        closure = guard.close()
        publish('rebase-SourceGuard.closed.json', closure)
    if closure['closed'] is not True or closure['retained_handles_count'] != 0 or closure['errors']:
        raise ValueError('Source Guard did not fully close')
    print(json.dumps({'status': 'PREPARED_SOURCE_ONLY_REBASED_MAIN_PIN', 'caller_ref': caller_ref, 'basis_ref': new_basis_ref, 'contract_ref': contract_ref, 'new_controls': len(controls), 'guard_closed': True, 'future_review_called': False}, ensure_ascii=False))

if __name__ == '__main__':
    try:
        main()
    except BaseException:
        print('ROOT_PYTHON_EXIT=1', flush=True)
        raise
    else:
        print('ROOT_PYTHON_EXIT=0', flush=True)
