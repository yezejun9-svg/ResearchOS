from pathlib import Path
import datetime, hashlib, json, types

R = Path(r'D:/作品集/ResearchOS/research-os')
B = R/'execution/v2.4/receipts/W05/W05-99'
W = R/'execution/v2.4/receipts/W09/W09-99'
D = Path(__file__).resolve().parent
SUPPORT = W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
helper = SUPPORT.read_bytes()
assert len(helper) == 4940 and hashlib.sha256(helper).hexdigest() == '567f53cadfab3781d6345ed1c6b04b52b85135e0843ce3c217e2f7fadf2a021a'
s = types.ModuleType('native_authority_metadata_support'); s.__file__ = str(SUPPORT)
exec(compile(helper, str(SUPPORT), 'exec'), s.__dict__); s.D = D
assert not (D/'metadata-decision.json').exists()
cp_path = R/'execution/v2.4/checkpoint.json'
cp_raw = cp_path.read_bytes()
cp_ref = {'path':str(cp_path), 'sha256':hashlib.sha256(cp_raw).hexdigest(), 'bytes':len(cp_raw)}
cp = json.loads(cp_raw)
cp_copy = D/'checkpoint.observed.raw.json'
with cp_copy.open('xb') as stream: stream.write(cp_raw)
cp_archive_ref = s.pin(cp_copy)
wip = cp['work_in_progress']
composition_ref = s.exact_ref(B/'public23_to24_root_integration_preparation_codex/prepare-20261010-01/composition-map.json', '55602273e20c126d1e6485a0ca0223b69be85c2e96f9a101a56342f0a334ea87', 77989)
guide_ref = s.exact_ref(Path(composition_ref['path']).parent/'ROOT_INTEGRATION_GUIDE.md', '51d1621a7d79b49636d5e15a4de16b59b75051c67cd70742b1d045cbcf24c372', 8820)
composition = json.loads(Path(composition_ref['path']).read_bytes())
v1_refs = {k:composition['tiers'][1][k] for k in ('HDF_ref','MF_ref')}
v2_refs = {k:composition['tiers'][2][k] for k in ('HDF_ref','MF_ref')}
v2_hdf = json.loads(Path(v2_refs['HDF_ref']['path']).read_bytes())
contract_ref = v2_hdf['current_contract_ref']
source_review_hdf_ref = wip['mu_sdk_prepared_native_authority_v2_source_review_ref']
component_review_hdf_ref = wip['mu_sdk_prepared_native_authority_v2_independent_actual_ref']
source_review_hdf = json.loads(Path(source_review_hdf_ref['path']).read_bytes())
component_review_hdf = json.loads(Path(component_review_hdf_ref['path']).read_bytes())
actual_ref = wip['mu_sdk_prepared_native_authority_v2_actual_ref']
actual = json.loads(Path(actual_ref['path']).read_bytes())
overlay_ref = actual['source_overlay_ref']
refs = [composition_ref, guide_ref, *v1_refs.values(), *v2_refs.values(), contract_ref,
        source_review_hdf_ref, source_review_hdf['manifest_ref'], source_review_hdf['review_ref'],
        component_review_hdf_ref, component_review_hdf['manifest_ref'], component_review_hdf['review_ref'],
        actual_ref, actual['source_overlay_ref'], actual['formatted_source_ref'],
        wip['mu_sdk_prepared_native_authority_v2_actual_original_io_ref'], cp_archive_ref,
        s.pin(Path(__file__)), s.pin(SUPPORT)]
g = s.guard()
try:
    g.acquire(refs)
    def read(ref): return json.loads(g.get_buffer(ref['path']))
    source = read(source_review_hdf_ref)
    component = read(component_review_hdf_ref)
    validation = read(actual_ref)
    contract = read(contract_ref)
    snapshot = read(cp_archive_ref)
    current = snapshot['work_in_progress']
    assert current['mu_sdk_prepared_native_authority_v2_handoff_ref'] == v2_refs['HDF_ref']
    assert current['mu_sdk_prepared_native_authority_v2_manifest_ref'] == v2_refs['MF_ref']
    assert source['reviewed_source_revision'] == 'b1599aaf259c435db5a0a5313ab0ea65'
    assert source['reviewed_source_HDF_sha256'] == v2_refs['HDF_ref']['sha256']
    assert source['reviewed_source_MF_sha256'] == v2_refs['MF_ref']['sha256']
    assert component['reviewed_validation_sha256'] == actual_ref['sha256']
    assert validation['main_canonical_unchanged'] is True and validation['formal_acceptance'] is False
    assert current['mu_sdk_prepared_native_authority_v2_state'] == 'READY_SOURCE_AND_ACTUAL_LEAF_BUILD_COMPONENT_ONLY_MAIN_UNADOPTED'
    overlay = read(overlay_ref)
    overlay_v2_pointers = []
    def collect(value, pointer=''):
        if isinstance(value, dict):
            for key, item in value.items(): collect(item, pointer+'/'+key)
        elif isinstance(value, list):
            for i, item in enumerate(value): collect(item, pointer+'/'+str(i))
        elif isinstance(value, str) and 'b1599aaf259c435db5a0a5313ab0ea65' in value:
            overlay_v2_pointers.append({'pointer':pointer,'value':value})
    collect(overlay)
    assert overlay_v2_pointers
    facts = {
        'schema':'researchos.native-authority-provenance-readonly-facts.v1',
        'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z'),
        'current_checkpoint_observation':{'original_ref':cp_ref,'archive_ref':cp_archive_ref,'revision':snapshot['revision'],
            'state_pointer':'/work_in_progress/mu_sdk_prepared_native_authority_v2_state',
            'state':current['mu_sdk_prepared_native_authority_v2_state']},
        'v1_source_refs':v1_refs,
        'v2_source_refs':v2_refs,
        'v2_current_contract_ref':contract_ref,
        'v1_contract_status':contract['supersedes_current_claims_of'],
        'source_review_refs':[source_review_hdf_ref,source['manifest_ref'],source['review_ref']],
        'source_review_decision':source['decision'],
        'source_review_actor':source['actor_id'],
        'source_review_binds_exact_v2_HDF_MF':True,
        'actual_component_validation_ref':actual_ref,
        'actual_component_status':validation['status'],
        'actual_component_overlay_ref':overlay_ref,
        'actual_component_overlay_v2_pointers':overlay_v2_pointers,
        'actual_component_formatted_source_ref':validation['formatted_source_ref'],
        'actual_component_original_io_ref':current['mu_sdk_prepared_native_authority_v2_actual_original_io_ref'],
        'actual_component_independent_review_refs':[component_review_hdf_ref,component['manifest_ref'],component['review_ref']],
        'actual_component_independent_decision':component['decision'],
        'actual_component_review_actor':component['actor_id'],
        'actual_component_Main_Canon_unchanged':validation['main_canonical_unchanged'],
        'composition_map_ref':composition_ref,
        'integration_guide_ref':guide_ref,
        'old_evidence_recomputed_or_reclassified':False,
        'old_tests_or_Source_controls_replayed':False,
        'live_Canon_guard_handles':0,
        'new_product_calls':0,
        'Main_Canon_Scope_writes':0,
        'private_key_or_OWNER_contents_read_or_hashed':False,
    }
finally:
    closed = g.close()
    guard_ref = s.write('metadata-read-guard.closed.json', closed)
assert closed['verification']=='PASSED' and closed['closed'] is True and closed['retained_handles_count']==0 and closed['failure'] is None and closed['errors']==[]
facts_ref = s.write('provenance-facts.json', facts)
decision_ref = s.write('metadata-decision.json', {
    'schema':'researchos.native-authority-composition-source-resolution.v1',
    'status':'READONLY_METADATA_RESOLVED',
    'decision':'USE_REVIEWED_V2_COMPOSITION_SOURCE_MAIN_ADOPTION_PENDING',
    'review_author':'codex:/root/full_w09_source_review',
    'backend_actor_id':'/root/full_w09_source_review',
    'selected_source_revision':'b1599aaf259c435db5a0a5313ab0ea65',
    'selected_source_refs':v2_refs,
    'v1_revision':'f6373acf36474d869fa8a64f3c490864',
    'v1_role':'PRESERVED_PREDECESSOR_LINEAGE_CURRENT_CLAIMS_SUPERSEDED_BY_V2',
    'independent_source_review_refs':facts['source_review_refs'],
    'actual_component_ref':actual_ref,
    'independent_actual_component_review_refs':facts['actual_component_independent_review_refs'],
    'current_Canon_Main_adoption_state':facts['current_checkpoint_observation'],
    'Main_adopted':False,
    'Root_next_integration_requirement':'Compose the reviewed v2 authority with the other declared Source layers, reconcile actual existing Main targets, then establish the new exact composed Source/toolchain/build and operation qualification. Historical component evidence does not qualify the new Main24 executable.',
    'facts_ref':facts_ref,
    'guard_ref':guard_ref,
    'new_tests_or_Source_controls':0,
    'retained_handles_count':0,
    'live_Canon_guard_handles':0,
    'product_calls':0,
    'execution_grant':False,
    'formal_acceptance':False,
    'new_Source_acceptance_issued':False,
    'prior_acceptance_modified':False,
    'STOP':True,
})
print(json.dumps({'metadata_decision_ref':decision_ref,'facts_ref':facts_ref,'guard_ref':guard_ref,
    'selected_source_revision':'b1599aaf259c435db5a0a5313ab0ea65','Main_adopted':False,
    'retained_handles_count':0,'live_Canon_guard_handles':0},ensure_ascii=False))
