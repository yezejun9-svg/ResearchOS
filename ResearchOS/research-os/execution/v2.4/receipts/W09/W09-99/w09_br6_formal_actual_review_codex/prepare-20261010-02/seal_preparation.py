"""Seal only the new Source preparation package, without future actual review."""
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path('D:/作品集/ResearchOS/research-os')
GUARD = ROOT / 'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
GUARD_SHA = 'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'

def ref(path):
    path = Path(path)
    raw = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def load(name):
    return json.loads((HERE / name).read_text(encoding='utf-8'))

def publish(name, value):
    path = HERE / name
    if path.exists():
        raise FileExistsError('immutable sealed member already exists: ' + name)
    raw = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').replace('\n', '\r\n').encode('utf-8')
    path.write_bytes(raw)
    return ref(path)

def main():
    metadata = load('rebase-metadata.json')
    prior_closure = load('rebase-SourceGuard.closed.json')
    if prior_closure['closed'] is not True or prior_closure['retained_handles_count'] != 0 or prior_closure['errors']:
        raise ValueError('rebase input Guard has not fully closed')
    guard_ref = ref(GUARD)
    if guard_ref['sha256'] != GUARD_SHA or guard_ref['bytes'] != 11404:
        raise ValueError('fixed Source Guard pin differs')
    spec = importlib.util.spec_from_file_location('br6_rebase_publication_guard', GUARD)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    refs = [metadata[k] for k in ['caller_ref', 'basis_ref', 'contract_ref']]
    refs += [ref(HERE / name) for name in ['rebase-metadata.json', 'rebase-controls.result.json', 'inverse.json', 'rebase_source.py', 'source-tool-io.reencoded.json']]
    refs += [guard_ref]
    guard = module.SourceReadGuard(per_file_cap=128 * 1024 * 1024, total_cap=512 * 1024 * 1024)
    closure = None
    try:
        guard.acquire(refs)
        held_contract = json.loads(guard.get_buffer(metadata['contract_ref']['path']).decode('utf-8'))
        if held_contract['Main_profile_ref']['sha256'] != metadata['new_Main_ref']['sha256']:
            raise ValueError('publication Main ref differs')
        controls = json.loads(guard.get_buffer(str(HERE / 'rebase-controls.result.json')).decode('utf-8'))
        if len(controls['controls']) != 4 or any(row['status'] != 'PASS' for row in controls['controls']):
            raise ValueError('new delta controls not all passed')
    finally:
        closure = guard.close()
        publish('publication-SourceGuard.closed.json', closure)
    if closure['closed'] is not True or closure['retained_handles_count'] != 0 or closure['errors']:
        raise ValueError('publication Guard has not fully closed')
    guard_refs = [ref(HERE / 'rebase-SourceGuard.closed.json'), ref(HERE / 'publication-SourceGuard.closed.json')]
    decision = {
        'schema': 'researchos.w09-br6-formal-review-preparation-decision.v1',
        'decision': 'PREPARED_SOURCE_ONLY_REBASED_MAIN_PIN_WAITING_ACTUAL_INPUTS',
        'author_id': metadata['Source_author'], 'backend_actor': metadata['backend_actor'],
        'author_thread': metadata['author_thread'], 'Root_thread': metadata['Root_thread'],
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'caller_ref': metadata['caller_ref'], 'contract_ref': metadata['contract_ref'],
        'basis_ref': metadata['basis_ref'], 'metadata_ref': ref(HERE / 'rebase-metadata.json'),
        'previous_hdf_ref': metadata['previous_preparation_hdf_ref'],
        'previous_mf_ref': metadata['previous_preparation_mf_ref'],
        'previous_decision_ref': metadata['previous_decision_ref'],
        'Main_before_ref': metadata['old_Main_ref'], 'Main_after_ref': metadata['new_Main_ref'],
        'actual_Main_adoption_ref': metadata['actual_adoption_ref'],
        'inverse_ref': ref(HERE / 'inverse.json'), 'exact_inverse': True,
        'controls_ref': ref(HERE / 'rebase-controls.result.json'), 'new_control_count': 4,
        'old18plus3_controls_replayed': False, 'old_four_Native_replayed': False, 'old_six_Mode_replayed': False,
        'guard_refs': guard_refs, 'all_guards_closed': True,
        'Main_rebase_extent': 'one basis Main sha/bytes reference plus one caller BASIS_SHA constant; other caller bytes unchanged',
        'BR6_embedded_material': 'unchanged historical Source; no BR7 Source acceptance inferred',
        'BR7_Source_review': 'OPEN_WAITING_EXACT_SEALED_SOURCE_INPUTS_SEPARATE_NONAUTHOR_TASK',
        'future_actual_inputs': held_contract['OPEN'],
        'future_input_template_ref': metadata['future_input_template_ref'],
        'future_context_ref': None, 'future_consumers_ref': None, 'future_Root_scope_ref': None,
        'future_current4_refs': None, 'future_issuance_ref': None, 'future_formal_review_ref': None,
        'future_entry_called': False, 'Root_stages_called': 0,
        'Native_calls': 0, 'Go_calls': 0, 'SQLite_calls': 0, 'dispatcher_calls': 0, 'model_calls': 0, 'TP_calls': 0,
        'Main_Canon_Scope_writes': 0, 'original_failures_added': 0,
        'execution_grant': False, 'formal_acceptance': False, 'STOP': True,
    }
    decision_ref = publish('preparation-decision.json', decision)
    exclusions = ['HDF.json', 'MF.json', 'publication-seal.actual-tool-io.reencoded.json']
    members = [ref(path) for path in sorted(HERE.iterdir(), key=lambda p: p.name) if path.is_file() and path.name not in exclusions]
    manifest = {'schema': 'researchos.w09-br6-formal-review-preparation-manifest.v1', 'author_id': metadata['Source_author'], 'members': members, 'member_count': len(members), 'exclusions': exclusions, 'exclusion_reason': 'manifest/handoff avoid self-reference; final seal invocation output is captured afterward as explicitly external IO', 'formal_acceptance': False, 'execution_grant': False}
    manifest_ref = publish('MF.json', manifest)
    handoff = {
        'schema': 'researchos.w09-br6-formal-review-preparation-handoff.v1',
        'decision': decision['decision'], 'author_id': metadata['Source_author'],
        'backend_actor': metadata['backend_actor'], 'author_thread': metadata['author_thread'],
        'Root_thread': metadata['Root_thread'], 'manifest_ref': manifest_ref,
        'decision_ref': decision_ref, 'caller_ref': metadata['caller_ref'],
        'contract_ref': metadata['contract_ref'], 'basis_ref': metadata['basis_ref'],
        'future_input_template_ref': metadata['future_input_template_ref'],
        'previous_preparation_hdf_ref': metadata['previous_preparation_hdf_ref'],
        'previous_preparation_mf_ref': metadata['previous_preparation_mf_ref'],
        'source_inputs': metadata['Source_inputs_held'], 'actual_Main_adoption_ref': metadata['actual_adoption_ref'],
        'new_Main_profile_ref': metadata['new_Main_ref'], 'guard_refs': guard_refs,
        'new_controls': 4, 'prior18plus3_controls_not_replayed': True,
        'existing_six_Mode_refs': held_contract['existing_six_Mode_refs'],
        'future_actual_review_called': False, 'BR7_Source_review': decision['BR7_Source_review'],
        'Root_stages_called': 0, 'Native_calls': 0, 'Go_calls': 0, 'SQLite_calls': 0, 'model_calls': 0, 'TP_calls': 0,
        'Main_Canon_Scope_writes': 0, 'formal_acceptance': False, 'execution_grant': False,
        'stop_after_delivery': True,
    }
    hdf_ref = publish('HDF.json', handoff)
    print(json.dumps({'decision': decision['decision'], 'HDF': hdf_ref, 'MF': manifest_ref, 'decision_ref': decision_ref, 'caller_ref': metadata['caller_ref'], 'contract_ref': metadata['contract_ref'], 'basis_ref': metadata['basis_ref'], 'member_count': len(members), 'all_guards_closed': True}, ensure_ascii=False))

if __name__ == '__main__':
    try:
        main()
    except BaseException:
        print('ROOT_PYTHON_EXIT=1', flush=True)
        raise
    else:
        print('ROOT_PYTHON_EXIT=0', flush=True)
