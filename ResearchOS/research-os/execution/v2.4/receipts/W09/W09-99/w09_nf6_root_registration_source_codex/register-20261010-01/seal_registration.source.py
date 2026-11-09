"""Seal authored NF6 registrar Source; no issuer, product, or Canon operations."""
from pathlib import Path
from datetime import datetime, timezone
import copy, hashlib, json, traceback, types

R = Path(r'D:\作品集\ResearchOS\research-os')
W = R / 'execution/v2.4/receipts/W09/W09-99'
D = Path(__file__).resolve().parent
N = W / 'full_w09_main_native_producer_source_codex/fullw09-20261010-06'
OLD = W / 'w09_nf4_root_registration_source_codex/register-20261010-02'
sp = W / 'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
s = types.ModuleType('review_support')
s.__file__ = str(sp)
exec(compile(sp.read_bytes(), str(sp), 'exec'), s.__dict__)
s.D = D
AUTHOR = 'codex:/root/full_w09_source_review'
STATUS = 'CONDITIONAL_SOURCE_PENDING_MAIN_ADOPTION'

def load_ref(ref):
    raw = Path(ref['path']).read_bytes()
    if s.pin(ref['path']) != ref:
        raise ValueError('PERSISTED_SOURCE_REF_DRIFT')
    return json.loads(raw)

cref = {'path': str(D / 'delta-controls.json'),
        'sha256': '79f6b9080e578979f3e010432a00e51908b111ffae70b07adf08aeb7a0a18512',
        'bytes': 4839}
controls = load_ref(cref)
closed_build = load_ref(controls['guard_ref'])
if controls['failure'] is not None or controls['failed'] or controls['passed'] != 8:
    raise ValueError('PERSISTED_REGISTRAR_BUILD_NOT_PASSED')
if not closed_build['closed'] or closed_build['retained_handles_count'] or closed_build['errors']:
    raise ValueError('PERSISTED_REGISTRAR_BUILD_NOT_CLOSED')
built = controls['built_refs']
input_refs = load_ref(built['source_input_refs'])['refs']
old_hdf = load_ref(input_refs['old_reg_hdf'])
producer_hdf = load_ref(controls['producer_source_hdf_ref'])
producer_mf = load_ref(controls['producer_source_mf_ref'])
producer_controls = load_ref(producer_hdf['finite_controls_ref'])
producer_guard = load_ref(producer_hdf['source_guard_ref'])
if producer_controls['passed'] != 13 or producer_controls['failure'] is not None or producer_controls['failed']:
    raise ValueError('PERSISTED_PRODUCER_CONTROLS_NOT_PASSED')
if not producer_guard['closed'] or producer_guard['retained_handles_count'] or producer_guard['errors']:
    raise ValueError('PERSISTED_PRODUCER_GUARD_NOT_CLOSED')

actual_build = s.capture('cc85d3', 0, 0)
members_before = [s.pin(p) for p in sorted(D.iterdir(), key=lambda p: p.name)
                  if p.is_file() and p.name not in ('HDF.json', 'MF.json')]
held = members_before + [controls['producer_source_hdf_ref'], controls['producer_source_mf_ref']]
guard = s.guard()
checks = []
failure = None
def check(name, ok, evidence=None):
    checks.append({'name': name, 'passed': bool(ok), 'evidence': evidence})
    if not ok:
        raise ValueError(name)

try:
    guard.acquire(held)
    check('new_registrar_written_files_exact_match_persisted_build_refs',
          all(hashlib.sha256(guard.get_buffer(ref['path'])).hexdigest() == ref['sha256']
              and len(guard.get_buffer(ref['path'])) == ref['bytes'] for ref in built.values()),
          {'old_13_and_8_controls_reexecuted': False, 'compiler_resources_reexecuted': False})
    check('sealed_producer_exact_conditional_author_and_manifest_chain',
          producer_hdf['actor_id'] == AUTHOR and producer_hdf['status'] == STATUS
          and producer_hdf['manifest_ref'] == controls['producer_source_mf_ref']
          and all(producer_hdf[key] in producer_mf['members'] for key in (
              'calling_contract_ref', 'runtime_ref', 'launcher_ref', 'prepare_caller_ref',
              'producer_caller_ref', 'source_choice_ref', 'compiler_blueprint_ref'))
          and producer_hdf['current_Source21_qualification'] is False
          and producer_hdf['execution_grant'] is False and producer_hdf['formal_acceptance'] is False,
          {'Root_Scope_or_review_fixture_created': False, 'Main_current_qualification_claimed': False})
except BaseException as exc:
    failure = {'type': type(exc).__name__, 'message': str(exc), 'traceback': traceback.format_exc()}
finally:
    closed = guard.close()
    seal_guard_ref = s.write('seal-guard.closed.json', closed)
    seal_controls_ref = s.write('seal-controls.json', {
        'schema': 'researchos.w09-nf6-registration-source-seal-controls.v1',
        'actor_id': AUTHOR, 'created_utc': datetime.now(timezone.utc).isoformat(),
        'checks': checks, 'passed': sum(row['passed'] for row in checks),
        'failed': sum(not row['passed'] for row in checks), 'failure': failure,
        'guard_ref': seal_guard_ref, 'actual_source_build_host': actual_build,
        'persisted_registrar_controls_ref': cref,
        'old_successful_controls_rerun': False, 'product_calls': 0,
        'execution_grant': False, 'formal_acceptance': False})
if failure or not closed['closed'] or closed['retained_handles_count'] or closed['errors']:
    print(json.dumps({'status': 'SOURCE_SEAL_FAILED', 'failure': failure,
                      'seal_controls_ref': seal_controls_ref, 'guard_ref': seal_guard_ref}, ensure_ascii=False))
    raise SystemExit(1)

mf = s.write('MF.json', {
    'schema': 'researchos.w09-nf4-registration-source-manifest.v1',
    'members': [s.pin(p) for p in sorted(D.iterdir(), key=lambda p: p.name)
                if p.is_file() and p.name not in ('HDF.json', 'MF.json')],
    'conditional_Main_adoption_required': True,
    'execution_grant': False, 'formal_acceptance': False})
h = copy.deepcopy(old_hdf)
h.update(
    actor_id=AUTHOR, source_actor_backend=s.ACTOR, source_thread_id=s.THREAD,
    status=STATUS, generation='fullw09-20261010-06', manifest_ref=mf,
    caller_ref=built['caller_ref'], core_ref=built['core_ref'], contract_ref=built['contract_ref'],
    input_pins_ref=built['input_pins_ref'], source_delta_ref=built['source_delta_ref'],
    source_input_refs=built['source_input_refs'], source_guard_ref=controls['guard_ref'],
    finite_controls_ref=cref,
    new_finite_controls={'passed': 8, 'failed': 0, 'pure_Source_only': True},
    seal_guard_ref=seal_guard_ref, seal_controls_ref=seal_controls_ref,
    new_seal_controls={'passed': 2, 'failed': 0, 'pure_Source_only': True},
    producer_source_hdf_ref=controls['producer_source_hdf_ref'],
    producer_source_mf_ref=controls['producer_source_mf_ref'],
    producer_contract_ref=producer_hdf['calling_contract_ref'],
    created_utc=datetime.now(timezone.utc).isoformat(),
    actual_source_build_host=actual_build,
    prior_source_hdf_ref=input_refs['old_reg_hdf'], prior_source_mf_ref=input_refs['old_reg_mf'],
    prior_Source_author={'actor_id': old_hdf['actor_id'], 'source_thread_id': old_hdf['source_thread_id']},
    conditional_Main_adoption_required=True,
    actual_Main_observed_ref=producer_hdf['actual_Main_observed_ref'],
    conditional_Main_after_ref=producer_hdf['conditional_Main_after_ref'],
    current_Main_qualification=False, current_Source21_qualification=False,
    independent_source_review_required=True, independent_source_review_refs=None,
    expected_non_author_reviewer='codex:/root/backup_regression_resources',
    all_source_guards_closed=True, retained_handles_count=0,
    old_successful_controls_rerun=False, compiler_3905_controls_rerun=False,
    new_original_failures=[], Rootexecute=False,
    actual_executed=False, actual_TP_calls=0, actual_Go_runs=0, actual_Native_runs=0,
    actual_dispatcher_runs=0, actual_SQL_runs=0, actual_model_provider_calls=0,
    Main_written=False, Canon_written=False, current_CanonicalPair_held=False,
    formal_case_accepted_delta=0, formal_acceptance=False, parent_acceptance=False,
    execution_grant=False, future_Root_scope=None, future_Root_request=None, future_registration=None,
    parallel_schedule=json.loads(Path(built['contract_ref']['path']).read_bytes())['parallel_schedule'],
    next_gate='Actual Root adoption of the single-line Main candidate, fresh current Source21 reobservation, real non-author Source reviews/peer audits, then Root-only dynamic current4 and complete pending suffix, finite new-generation leases and shared TP registration.',
    interface_schema_note='Existing four-selector producer and registrar v1 schemas/review decisions are retained. Exact NF6 Source pins and generation identify this version; the handoff is conditional Source, not current qualification or a Root grant.')
href = s.write('HDF.json', h)
print(json.dumps({
    'status': 'CONDITIONAL_SOURCE_PACKAGES_SEALED',
    'actor_id': AUTHOR, 'backend_actor_id': s.ACTOR, 'source_thread_id': s.THREAD,
    'producer_refs': {'hdf': controls['producer_source_hdf_ref'],
                      'mf': controls['producer_source_mf_ref'],
                      'calling_contract': producer_hdf['calling_contract_ref']},
    'registrar_refs': {'hdf': href, 'mf': mf, 'calling_contract': built['contract_ref']},
    'controls': {'producer': producer_hdf['finite_controls_ref'], 'registrar': cref,
                 'seal': seal_controls_ref, 'passed': [13, 8, 2]},
    'guards': [producer_hdf['source_guard_ref'], controls['guard_ref'], seal_guard_ref],
    'actual_source_hosts': [producer_hdf['actual_source_build_host'], actual_build],
    'actual_Main_observed_ref': producer_hdf['actual_Main_observed_ref'],
    'conditional_Main_after_ref': producer_hdf['conditional_Main_after_ref'],
    'all_guards_closed': True, 'retained_handles_count': 0, 'new_original_failures': [],
    'current_Main_qualification': False, 'current_Source21_qualification': False,
    'Rootexecute': False, 'execution_grant': False, 'formal_acceptance': False,
    'old_successful_controls_rerun': False, 'compiler_3905_controls_rerun': False,
    'actual_Native_Go_SQL_model_TP_dispatcher_calls': 0}, ensure_ascii=False))
