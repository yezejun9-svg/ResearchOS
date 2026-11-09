"""Publish Bridge06 prepared Source; do not issue a Source acceptance or Root grant."""
from pathlib import Path
from datetime import datetime, timezone
import json, types

R = Path(r'D:\作品集\ResearchOS\research-os'); W = R / 'execution/v2.4/receipts/W09/W09-99'
D = Path(__file__).resolve().parent; OLD = D.parent / 'bridge-20261010-05'
RV = W / 'w09_formal_root_bridge_independent_source_review_codex/review-20261010-05-attach'
HELPER = W / 'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
s = types.ModuleType('receipt_support'); s.__file__ = str(HELPER)
exec(compile(HELPER.read_bytes(), str(HELPER), 'exec'), s.__dict__); s.D = D
def read(path): return json.loads(Path(path).read_bytes())
oh = read(OLD / 'HDF.json'); rh = read(RV / 'HDF.json')
controls = read(D / 'delta-controls.json'); built = controls['built']
assert controls['failure'] is None and controls['count'] == controls['passed']
for key in ('source_guard_ref', 'delta_guard_ref'):
    closed = read(built[key]['path'])
    assert closed['closed'] and closed['retained_handles_count'] == 0 and closed['errors'] == []
success = s.capture('dcc9e2', 0, 0)
s.write('actual-source-build-hostpair.json', success)
generation = 'bridge-20261010-06'; author = 'codex:/root/full_w09_source_review'
backend = '/root/full_w09_source_review'
now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

contract = dict(read(oh['root_calling_contract_ref']['path']))
contract.update(generation=generation, source_revision_uuid=controls['source_revision_uuid'],
    source_author=author, source_author_backend=backend, source_thread_id=s.THREAD,
    source_ref=built['source_ref'], consumer_launcher_ref=built['consumer_launcher_ref'],
    CLI_prefix=[str(Path(r'C:\Users\yqyyds\AppData\Local\Python\pythoncore-3.14-64\python.exe')),
                '-I', '-S', '-B', '-X', 'utf8', built['source_ref']['path']],
    base_hdf_ref=s.pin(OLD / 'HDF.json'), base_mf_ref=s.pin(OLD / 'MF.json'),
    base_source_ref=oh['source_ref'], independent_Request_Changes_ref=rh['decision_ref'],
    canonical_identity_contract=dict(
        changed_function_only='canonical_identity',
        root_relative_absolute_mapping='Path(path) if absolute else ROOT / Path(path)',
        identity_normalization='Path.resolve(strict=True), exactly as physical() resolves identity',
        no_live_bytes_read_by_classifier=True,
        original_reference_objects_never_rewritten=True,
        exact_ref_equality_still_required_for_request_authority=True,
        physical_checked_guard_path_rules_unchanged=True,
        uncovered_Canon_alias_in_historical_documents='REJECTED',
        Canon_alias_in_persistent_snapshots='REJECTED',
        conflicting_Canon_alias_in_request='REJECTED',
        new_generation_requires_fresh_Source_review_and_Root_proposal_scope=True),
    reused_BR5_controls_ref=oh['delta_controls_ref'], old_36_controls_rerun=False,
    original1190_io=controls['original1190_io'], original1185_io_preserved=oh['original1185_io'],
    actual_executed=False, independent_Source_review_required=True,
    execution_grant=False, formal_acceptance=False)

md = '''# Bridge06 Root calling contract

Source author: codex:/root/full_w09_source_review, actual backend /root/full_w09_source_review. Verifier remains /root/backup_regression_resources. This prepared Source requires an independent Source review and new real Root authority; it is not a Source acceptance, execution grant, Mode decision or formal acceptance.

Use the sealed Caller as __main__ with locked Python -I -S -B -X utf8. The existing ten stages, request schema, exact Source/HDF/MF/launcher bindings, actual Root and peer proofs, fresh current4, finite owner/worker lease, six Main routes and Main Native/Mode gates remain unchanged. A future fresh Root Scope.source_actor must bind /root/full_w09_source_review and this new generation; old Bridge05 authority cannot be borrowed.

The only business change is canonical_identity: map Root-relative paths to ROOT, then use Path.resolve(strict=True), matching physical()'s identity resolution. Absolute or Root-relative dot segments, Windows case and separator spellings therefore identify the same fixed Canon file. This is a classification operation and never rewrites a stored ref object. Existing physical(), checked(), SourceReadGuard and exact reference comparisons remain unchanged. Direct request Canon aliases must still equal the fresh current4 ref object exactly; a different spelling is not silently substituted.

Bridge05's historical contract remains mandatory: propose freezes four complete original Canon byte archives while current4 is guarded, in its own exact output directory; exact order, original SHA/bytes, proposal generation/source/review and SS/CM identities are required. Only the explicit validated proposal.current4 identity vector is archive-covered. Extra Canon references, including aliases, in proposal/publication/role input and persistent snapshot files are refused. Persistent snapshots omit all Canon identities, including aliases. Fresh authority snapshot/current4 Guard and the unchanged exclusive TP CAS remain separate and mandatory; TP stages hold no shared CP/OW handles.

Incremental controls use files exclusively inside this new Source directory. No live Canon content, Root stage, Scope issuance, Main module, Native, Go, SQL, dispatcher, model or TP was run. The BR5 36 successful controls are referenced without rerunning. Complete byte inverse recovers BR5; all other Source AST, original Full author, Backup verifier and the consumer launcher remain exact. Original1190's nonterminating PowerShell read diagnostic is retained with actual outer0/PythonNULL and original three-line I/O; original1185 and Attach review diagnostics remain in their immutable prior artifacts.
'''
with (D / 'ROOT_CALL_CONTRACT.md').open('xb') as stream:
    stream.write(md.encode('utf-8'))
contract['contract_ref'] = s.pin(D / 'ROOT_CALL_CONTRACT.md')
contract_ref = s.write('root-calling-contract.source.json', contract)

# Close a single Guard over the complete new package inventory, including Source fixtures.
g = s.guard(); held = [s.pin(path) for path in sorted(D.rglob('*'), key=lambda path: str(path)) if path.is_file()]
try:
    g.acquire(held)
    assert s.pin(D / 'w09_root_bridge.source.py') == built['source_ref']
    assert s.pin(D / 'consumer_launch.source.py') == built['consumer_launcher_ref']
    assert built['consumer_launcher_ref']['sha256'] == oh['consumer_launcher_ref']['sha256']
finally:
    seal_guard = s.write('seal-source-guard.closed.json', g.close())
sg = read(seal_guard['path'])
assert sg['closed'] and sg['retained_handles_count'] == 0 and sg['errors'] == []
mf = s.write('MF.json', dict(schema='researchos.w09-formal-root-bridge-source-manifest.v3',
    members=[s.pin(path) for path in sorted(D.rglob('*'), key=lambda path: str(path)) if path.is_file()],
    exclusions=['HDF.json', 'MF.json', 'postseal-tool-io.json'],
    fixture_members_are_Source_only=True))
hdf = s.write('HDF.json', dict(schema='researchos.w09-formal-root-bridge-source-handoff.v3',
    source_author=author, source_author_backend=backend, actual_source_thread=s.THREAD,
    actual_parent_thread='01a11007-5233-7ca1-b71f-9e9e5ce84c98',
    status='SOURCE_PREPARED_PENDING_INDEPENDENT_REVIEW', generation=generation, created_utc=now,
    source_revision_uuid=controls['source_revision_uuid'], source_ref=built['source_ref'],
    consumer_launcher_ref=built['consumer_launcher_ref'], contract_ref=contract['contract_ref'],
    root_calling_contract_ref=contract_ref, manifest_ref=mf,
    base_hdf_ref=s.pin(OLD / 'HDF.json'), base_mf_ref=s.pin(OLD / 'MF.json'), base_source_ref=oh['source_ref'],
    base_source_contribution=oh['base_source_contribution'],
    independent_Request_Changes_hdf_ref=s.pin(RV / 'HDF.json'),
    independent_Request_Changes_mf_ref=s.pin(RV / 'MF.json'),
    independent_Request_Changes_decision_ref=rh['decision_ref'], independent_findings_ref=rh['findings_ref'],
    exact_inverse_ref=built['inverse_ref'], patch_ref=built['patch_ref'], source_inputs_ref=built['inputs_ref'],
    delta_controls_ref=s.pin(D / 'delta-controls.json'), source_guard_ref=built['source_guard_ref'],
    delta_source_guard_ref=built['delta_guard_ref'], seal_source_guard_ref=seal_guard,
    actual_source_build_host=success, original1190_io=controls['original1190_io'], new_original_failures=[1190],
    original1185_io_preserved=oh['original1185_io'],
    prior_Attach_review_original_diagnostics_preserved=rh['new_original_diagnostics'],
    reused_BR5_controls_ref=oh['delta_controls_ref'], old_successful_controls_rerun=False,
    finite_delta_controls=controls['count'], finite_new_seal_checks=1,
    changed_business_functions=['canonical_identity'], changes=[
        'Canonical classification now resolves Root-relative/absolute identity with Path.resolve(strict=True), matching physical().',
        'Original ref spelling and all exact current4/archive/peer/Root/Guard/TP/Main/Mode gates remain unchanged.',
        'New generation/UUID/selfrefs and precise calling contract; actual Full author and Backup verifier remain truthful.'],
    guards_closed_zero=True, retained_handles_count=0, live_Canon_handles_held=0,
    new_package_complete_inventory_held_before_seal=True,
    independent_source_review_required=True, independent_source_review_ref=None,
    Source_author_self_acceptance=False, verifier_backend='/root/backup_regression_resources',
    future_Root_Scope_source_actor=backend, future_Root_Scope_source_author_canonical=author,
    future_Root_scope=None, future_Root_request=None, future_execution_grant=None, future_Mode_refs=None,
    execution_grant=False, formal_acceptance=False, parent_acceptance=False,
    actual_bridge_stages=0, actual_Main_module_calls=0, actual_Native_Go_SQL_model_TP_calls=0,
    Main_Canon_Scope_written=False,
    actual_product_exits=dict(Native=None, Go=None, SQL=None, dispatcher=None, model=None, TP=None), STOP=True))
print(json.dumps(dict(schema='researchos.w09-bridge-source-delivery.v1', operation='SOURCE_PREPARED',
    source_author=author, source_author_backend=backend, source_thread_id=s.THREAD,
    generation=generation, source_refs=[hdf, mf, contract_ref], source_ref=built['source_ref'],
    consumer_launcher_ref=built['consumer_launcher_ref'], exact_inverse_ref=built['inverse_ref'],
    changed_business_functions=['canonical_identity'], delta_controls=controls['count'],
    old_36_controls_reused_without_rerun=True, guard_refs=[built['source_guard_ref'], built['delta_guard_ref'], seal_guard],
    guards_closed_zero=True, retained_handles_count=0, original1190_io=controls['original1190_io'],
    original1185_io_preserved=oh['original1185_io'],
    independent_Source_acceptance=False, execution_grant=False, formal_acceptance=False,
    actual_product_exits=dict(Native=None, Go=None, SQL=None, dispatcher=None, model=None, TP=None), STOP=True),
    ensure_ascii=False))
