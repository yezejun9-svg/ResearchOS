"""Author receipt/AST writer only. Never imports or executes any supplied template."""
import ast
import datetime
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path('D:/作品集/ResearchOS/research-os')
HERE = Path(__file__).resolve().parent
N05 = ROOT / 'execution/v2.4/receipts/W05/W05-99'
N13 = ROOT / 'execution/v2.4/receipts/W13/W13-03'
PYTHON = 'C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe'


def ref(p):
    p = Path(p)
    b = p.read_bytes()
    return {'path': str(p), 'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b)}


def doc(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))


def save(name, value):
    with (HERE / name).open('xb') as f:
        f.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))
    return ref(HERE / name)


assert sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode and not sys.flags.optimize
revision = N13 / 'desktop_exact15_integration_preparation_revision_codex/e908291811794b64874f5f6f66507916'
review_dir = N13 / 'desktop_exact15_integration_revision_independent_review_codex/87707854354a4cd8ad3a26aaf7627007'
source_dir = N13 / 'desktop15_source_import_suitability_independent_review_codex/d2215541c83c463db77326ffb2077dd7'
cli_dir = N05 / 'cli43_closed_execution_independent_review_codex/62e0bad3597f4faa9addb47da466fe3e'
fixed = [
    (revision / 'integrate_desktop15.v2.py', '2344b9ce8446b273215892b4a9822a06087494532cb544d16ed405ca40ba6412'),
    (revision / 'launch_desktop15.v2.py', '3669c0c76413728de8157b4f03e27773b25f3c9ad6da600d237629df2c4ae87b'),
    (revision / 'scope.v3.proposed.json', '73f48cfb9aa7ffe7632a263202cda8da017f0b58e51c3f20f907f48f5ac5e227'),
    (review_dir / 'review.json', 'af1625660f48b4e1b70585dd2242aa852029503d03b73833835675c00af5665f'),
    (review_dir / 'manifest.json', '29a67e458e2e8631fc7c571c66d6b9423e0201b59a4f2a2d01575e5e2976c580'),
    (source_dir / 'review.json', '6333ecbda1ba14da25cf80094e1e94547ee5407c999d366adc472f2cd5be90aa'),
    (source_dir / 'manifest.json', '28f9726cdd76efa03067b40102178bc8561f9a1aaa977ab298884f8cb70899b7'),
    (source_dir / 'handoff.json', 'b3914c31c8784e95593cb4b1c8f2b622f674776172d698281ac172f28365fc6a'),
    (cli_dir / 'review.json', 'fe7d4cb67d28517c4c55ca82461c0448f791635b128020faa1278b86d971fbf8'),
    (cli_dir / 'manifest.json', '874c7461649170aad345357f2634cb5bf77f335871a4df1300f1fef45a0025a5'),
    (cli_dir / 'handoff.json', '0171b054b4c2b23efc91faad32c388e7860d21fb056ead6551d524a64b804206'),
]
inputs = {}
for p, expected in fixed:
    r = ref(p)
    assert r['sha256'] == expected, str(p)
    inputs[str(p)] = r
scope = doc(revision / 'scope.v3.proposed.json')
closed = doc(cli_dir / 'review.json')
source = doc(source_dir / 'review.json')
assert source['source_integration_permitted'] is True and source['requested_changes'] == []
assert source['execution_authority_granted_by_this_review'] is False
assert closed['decision'] == 'EXACT43_MAIN_SOURCE_INTEGRATION_EVIDENCE_CLOSED'
for key in ['controller_ref', 'launcher_ref', 'exact15_ref', 'patch_ref', 'logical43_tree_ref', 'protected_source_paths_ref', 'toolchain_lock_ref', 'owned_process_helper_ref', 'root_attributes_proof_ref']:
    r = scope[key]
    assert ref(r['path']) == r
    inputs[r['path']] = r
for key in ['completed_ref', 'manifest_ref', 'post_registration_audit_ref', 'root_registration_manifest_ref', 'root_registration_handoff_ref']:
    r = closed[key]
    p = Path(r['path'])
    if not p.is_absolute():
        p = ROOT / p
    actual = ref(p)
    assert actual['sha256'] == r['sha256'] and actual['bytes'] == r['bytes']
    inputs[str(p)] = actual
for name in ['build-scope.py', 'build-metadata-templates.py', 'metadata-engine.template.py', 'prepare-static-receipts.py']:
    inputs[str(HERE / name)] = ref(HERE / name)
inputs[str(ROOT / 'AGENTS.md')] = ref(ROOT / 'AGENTS.md')
before = list(inputs.values())
save('inputs.before.json', before)
asts = []
for name in ['build-scope.py', 'build-metadata-templates.py', 'metadata-engine.template.py', 'prepare-static-receipts.py']:
    tree = ast.parse((HERE / name).read_text(encoding='utf-8'), filename=name)
    asts.append({'file_ref': ref(HERE / name), 'AST_PARSE': 'PASS', 'nodes': sum(1 for _ in ast.walk(tree)), 'executed': False})
template = (HERE / 'metadata-engine.template.py').read_text(encoding='utf-8')
marker = '\nMODE = ' + repr('register') + '\n'
assert template.count(marker) == 1
for mode in ['register', 'run', 'seal', 'grant']:
    variant = template.replace(marker, '\nMODE = ' + repr(mode) + '\n', 1)
    ast.parse(variant, filename=mode + '.unexecuted.py')
    asts.append({'derived_mode': mode, 'AST_PARSE': 'PASS', 'bytes': len(variant.encode('utf-8')), 'sha256': hashlib.sha256(variant.encode('utf-8')).hexdigest(), 'materialized': False, 'executed': False})

request = {
    'schema': 'researchos.desktop15-root-binding-parameters.v1', 'actor': 'codex:/root',
    'action': 'PREPARE_BOUND_PROPOSAL_ONLY', 'authorized': False, 'future_root_grant': None,
    'expected_before': None, 'expected_after': None, 'expected_cli43_head': 'a510dbef4a7e08fb5c428df44c39b133f3ffa856',
    'expected_main_branch': None, 'operation_uuid': None, 'registration_namespace': None, 'binding_output_root': None,
    'canonical_before_refs': None, 'current_root_handoff_ref': None, 'current_root_manifest_ref': None,
    'runtime_resources_ref': None, 'status_ref': None, 'origin_cut_ref': None, 'confirmed_pending_origins': None,
    'desktop_source_review_ref': ref(source_dir / 'review.json'), 'desktop_source_review_manifest_ref': ref(source_dir / 'manifest.json'),
    'example_not_executable': True,
}
save('root-request.example.json', request)
save('metadata-input.example.json', {
    'schema': 'researchos.desktop15-metadata-template-parameters.v1', 'actor': 'codex:/root',
    'action': 'PREPARE_METADATA_TEMPLATES_ONLY', 'authorized': False, 'future_root_grant': None,
    'binding_ref': None, 'binding_manifest_ref': None, 'controller_review_ref': None, 'controller_review_manifest_ref': None,
    'metadata_engine_ref': ref(HERE / 'metadata-engine.template.py'), 'example_not_executable': True,
})
save('origin-cut.example.json', {
    'schema': 'researchos.root-pending-origin-cut.v1', 'actor': 'codex:/root',
    'registered_before': None, 'registration_after': None, 'confirmed_origins': None,
    'retained_aftercut_origin_refs': None, 'counter_reset': False, 'example_not_executable': True,
    'row_contract': {'actor': 'ACTUAL_ORIGIN_ACTOR', 'evidence_ref': None, 'original_payload': None,
        'actual_outer_exit': None, 'actual_native_exit': None, 'product_cases_run': 0, 'count_once': True, 'counter_reset': False},
    'notes': ['Root chooses an explicit confirmed cut; no current or future revision is inferred.',
        'Nullable exits remain nullable. Do not infer native from a traceback or outer status.',
        'After-cut refs are pinned and retained; they do not silently increase this registration count.'],
})
save('spec.json', {
    'schema': 'researchos.desktop15-root-scope-binding-preparation.v1', 'actor': 'codex:/root/sources_parent_impl',
    'status': 'PREPARATION_ONLY_NOT_EXECUTED', 'authorized': False, 'future_root_grant': None,
    'source_writer': 'STOPPED', 'source_acceptance': False, 'formal_increment': 0,
    'candidate_source': scope['candidate'], 'actual_closed43': closed['registered_head'] if 'registered_head' in closed else 'a510dbef4a7e08fb5c428df44c39b133f3ffa856',
    'expected_composition': {'base2cdb': scope['original_base'], 'existing_unique43': 43, 'desktop_exact15': 15, 'disjoint_union58': 58,
        'existing_desktop_preimages': 9, 'absent_desktop_paths': 6, 'imported_receipt_ancestry': 0},
    'fixed_controller_ref': scope['controller_ref'], 'fixed_launcher_ref': scope['launcher_ref'],
    'reviewed_skeleton_scope_ref': ref(revision / 'scope.v3.proposed.json'), 'independent_skeleton_review_ref': ref(review_dir / 'review.json'),
    'independent_source_suitability_ref': ref(source_dir / 'review.json'), 'closed43_review_ref': ref(cli_dir / 'review.json'),
    'existing_completed_manifest_ref_objects': {k: closed[k] for k in ['completed_ref', 'manifest_ref', 'post_registration_audit_ref']},
    'ref_rule': 'Normalize ABS/REL only to compare content/path identity. Retain original source MF ref dictionaries for unchanged controller dict comparisons.',
    'source_guards': {'exact15_ref': scope['exact15_ref'], 'planned_protected_paths_ref': scope['protected_source_paths_ref'],
        'required_actual_protected_count': 6983, 'missing_is_refusal': True, 'root_attributes_bytes_hex': b'* -text\n'.hex(),
        'root_attributes_blob': 'fa1385d99a319b43c06f5309d1aae9fdd3adea46', 'root_attributes_mode': '100644',
        'main_runtime_bundle_ref': scope['main_runtime_bundle_ref'], 'old_deleted_paths': scope['old_deleted_paths'],
        'index_required_empty': True, 'active_nested_info_attributes_and_local_filter_include': 'REFUSE'},
    'future_explicit_inputs': ['before/after complete tuples', 'canonical4 exact current refs', 'current Root handoff+MF',
        'actual current status and branch', 'new operation UUID and exclusive output namespaces', 'confirmed origin cut and original payloads',
        'new actual public Python/Git/OS runtime catalog', 'new W05 exact bound scope/controller/launcher/template review',
        'new W05 actual emitted metadata draft review before CAS'],
    'caps': {'binding_readonly_Git_max': 16, 'binding_current_Git_calls': 10, 'Git_query_seconds': 30,
        'binding_observed_seconds': 1200, 'metadata_each_mode_observed_seconds': 1200, 'metadata_Git_max_per_mode': 15,
        'metadata_planned_Git_calls': {'run': 3, 'register': 12, 'seal': 3, 'grant': 3},
        'max_file_bytes': 268435456, 'max_cumulative_hash_read_bytes_per_mode': 34359738368,
        'source_import_Git_cap': 80, 'source_apply': 1, 'source_commit': 1, 'source_path_cap': 15,
        'source_controller_seconds': 900, 'source_outer_owned_job_seconds': 1200, 'cleanup_seconds': 5,
        'product_Go_Node_SQL_HTTP_MODEL_calls': 0},
    'runtime_claim': 'Before-import source/cache pins plus actual loaded Python/OS point observations, not complete lifecycle telemetry. Every spawned child is held by an exclusive unnamed KILL_ON_CLOSE Job with creation identity and actual cleanup evidence. Hard syscall timeout requires the separately reviewed Root outer Job.',
    'external_files': 'Only exact rows in the explicit public runtime catalog may be hashed outside ROOT; all writes remain exclusive ROOT receipt destinations.',
    'failure_policy': 'Stop at first unexpected result, preserve raw stdout/stderr, nullable actual exits, first+secondary errors and owned Job cleanup. No retry, rollback, reset or HEAD inference.',
    'recovery': 'After a partial CAS or later sealing failure, inspect exact own completed prefix; separate Root forward-only recovery decision. Do not rerun scripts or reconstruct success.',
    'old_evidence': {'author_Node169': 'Retained author evidence only; not Root fresh replay.', 'Go3': 'Separate bounded DEBUG component; old normal-run OS gap remains.'},
    'held': ['Root explicit future binding invocation', 'new independent bound-scope review', 'new independent metadata review/CAS/seal/oncegrant',
        'source import actual execution', 'post-import head registration/non-author closure', 'fresh58 build and independent169 replay',
        'GUI/install/NVDA/native frame/Web', 'P02 checkpoint restore', 'live Host/provider/model qualification', 'formal42'],
})
save('grant-launcher-derivation-plan.json', {
    'schema': 'researchos.desktop15-grant-launcher-derivation-plan.v1', 'authorized': False, 'future_root_grant': None,
    'controller_changed': False, 'launcher_changed': False, 'fixed_controller_ref': scope['controller_ref'], 'fixed_launcher_ref': scope['launcher_ref'],
    'ordered_stages': [
        {'stage': 1, 'owner': 'codex:/root', 'action': 'Supply actual root-request and runtime catalog, observe all explicit current preconditions; separately authorize preparation invocation.',
            'argv': [PYTHON, '-I', '-S', '-X', 'utf8', str(HERE / 'build-scope.py'), '--request', '<ACTUAL_ABS_REQUEST>', '--request-sha256', '<ACTUAL_SHA>']},
        {'stage': 2, 'owner': 'codex:/root/w05_merge_review', 'action': 'Review new bound scope and activation-plan exact future scope bytes, controller/launcher and both metadata files. Required additional fields: bound_proposal_sha256, metadata_template_builder_sha256, metadata_engine_sha256; no execution claims.'},
        {'stage': 3, 'owner': 'codex:/root', 'action': 'Supply actual metadata-input; emit reviewed registration drafts only. The active scope file does not exist yet.',
            'argv': [PYTHON, '-I', '-S', '-X', 'utf8', str(HERE / 'build-metadata-templates.py'), '--input', '<ACTUAL_ABS_INPUT>', '--input-sha256', '<ACTUAL_SHA>']},
        {'stage': 4, 'owner': 'codex:/root/w05_merge_review', 'action': 'New root_registration_r<AFTER_CP>_readonly_review_codex/UUID review, ordered actual canonical copies under its own parent; review actual four emitted code/prepared/audit hashes and desired transition.'},
        {'stage': 5, 'owner': 'codex:/root', 'action': 'After separate actual grant execute run.py review-path review-SHA under owned Job. It launches register.py with the same review, preserves actual native/raw/cleanup. Check four canonical bytes and source guards before each CP/OW replacement; ST/CM never replaced.'},
        {'stage': 6, 'owner': 'codex:/root', 'action': 'Only successful reviewed CAS permits seal.py. Seal verifies actual result, raw and desired4, materializes scope_registration.json and closes MF. Failure blocks grant; no auto recovery.'},
        {'stage': 7, 'owner': 'codex:/root', 'action': 'Only actual sealed registration permits grant-producer.py, exclusive operation leaf and canonical4 copies. It does not call launcher/controller. Grant runtime files are new append-only evidence; old registration MF is never rewritten.'},
        {'stage': 8, 'owner': 'codex:/root', 'action': 'Separate actual source execution decision: use approved fixed launcher named-argument interface, from ROOT under separately reviewed Root outer Job; never bypass it or run the inner controller directly.',
            'argv': [PYTHON, '-I', '-S', '-X', 'utf8', scope['launcher_ref']['path'], '--scope', '<ACTUAL_SCOPE_ABS>', '--scope-sha256', '<ACTUAL_SCOPE_SHA>', '--grant', '<ACTUAL_GRANT_ABS>', '--grant-sha256', '<ACTUAL_GRANT_SHA>']},
        {'stage': 9, 'owner': 'codex:/root + nonauthor', 'action': 'Observe source-only15 import actual result, forward-register actual new HEAD without guessing, nonauthor close it. Fresh58/renderer/GUI/model scopes remain separate.'},
    ],
    'cwd': str(ROOT), 'current_stage_executed': None, 'no_root_actor_impersonation': True,
})
after = [ref(x['path']) for x in before]
assert before == after
save('inputs.after.json', after)
save('static-audit.json', {
    'schema': 'researchos.desktop15-binding-author-static-audit.v1', 'actor': 'codex:/root/sources_parent_impl',
    'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'kind': 'AUTHOR_PREPARATION_NOT_ACCEPTANCE',
    'AST_results': asts, 'fixed_input_hashes_checked': len(before), 'input_drift': 0,
    'template_import_or_execution': 0, 'metadata_desired_transform_executed': 0, 'Git_calls': 0,
    'source_canonical_index_writes': 0, 'product_Go_Node_SQL_HTTP_MODEL_calls': 0,
    'manifest_check_level': 'These listed fixed refs and metadata content only. Actual future binder rehashes every sealed member and all6983 current protection paths; this AST turn does not claim that future current vector.',
    'current_root_tuple_inferred': False, 'future_root_grant': None, 'source_acceptance': False,
})
print(json.dumps({'status': 'PREPARATION_STATIC_AST_ONLY', 'AST_records': len(asts), 'fixed_inputs': len(before), 'drift': 0, 'template_executions': 0, 'output': str(HERE)}, ensure_ascii=False))
