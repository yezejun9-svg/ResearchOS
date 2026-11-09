"""Seal this author-only receipt directory; no candidate/template import."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def ref(p):
    b = p.read_bytes()
    return {'path': str(p), 'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b)}


def save(name, value):
    with (HERE / name).open('xb') as f:
        f.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))
    return ref(HERE / name)


assert sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode
before = json.loads((HERE / 'inputs.before.json').read_text(encoding='utf-8'))
after = json.loads((HERE / 'inputs.after.json').read_text(encoding='utf-8'))
assert before == after
for item in after:
    assert ref(Path(item['path'])) == item
tool = save('tool-diagnostics.json', {
    'schema': 'researchos.author-preparation-tool-diagnostics.v1', 'actor': 'codex:/root/sources_parent_impl',
    'kind': 'KNOWN_FIELDS_FROM_VISIBLE_TOOL_RESULTS_NOT_FULL_NATIVE_STREAM_CAPTURE',
    'earlier_readonly_tools_reported_outer_zero': ['9ee7ca', '73d9b6', '70e107', 'a5ad9e', 'aa75c3'],
    'namespace_creation_tool': {'chunk': '01029e', 'actual_outer_exit': 0, 'actual_native_python_exit': 0, 'source_canonical_index_writes': 0},
    'current_readonly_tools': [{'chunk': x, 'actual_outer_exit': 0, 'actual_native_exit': None, 'operation': 'PowerShell public read/list only'} for x in ['3cb314', '66fbea', '52c73f', 'ab045b', 'bf18e3', '245897', '660c59', 'cf290f']],
    'apply_patch': {'result': 'successful tool return objects', 'actual_native_exit': None, 'scope': 'only this new author receipt namespace'},
    'static_receipt_AST_invocation': {
        'chunk': '3feb8f', 'actual_outer_exit': 0, 'actual_native_python_exit': 0,
        'exit_bridge': 'PowerShell invokes the pinned Python command then explicit exit $LASTEXITCODE.',
        'argv': ['C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe', '-I', '-S', '-X', 'utf8', str(HERE / 'prepare-static-receipts.py')],
        'cwd': 'D:/作品集/ResearchOS/research-os',
        'stdout_known_fields': {'status': 'PREPARATION_STATIC_AST_ONLY', 'AST_records': 8, 'fixed_inputs': 28, 'drift': 0, 'template_executions': 0},
        'stderr_visible': '', 'separate_native_stdout_stderr_files': False,
    },
    'new_actual_nonzero_origins': [], 'counter_reset': False,
    'other_actors_pending_origins': 'Not selected or counted by this preparation. Future Root supplies its actual cut; current430 and observed>=433 are parent observations, not values inferred or written by this author.',
    'candidate_helpers_CAS_Go_Node_SQL_HTTP_MODEL_calls': 0,
    'actual_native_lifecycle_claim': False,
})
handoff = save('handoff.json', {
    'schema': 'researchos.desktop15-root-binding-preparation-handoff.v1', 'actor': 'codex:/root/sources_parent_impl',
    'status': 'PREPARATION_ONLY_STOPPED_PENDING_NONAUTHOR_REVIEW_AND_EXPLICIT_ROOT_PARAMETERS',
    'source_writer': 'STOPPED', 'authorized': False, 'future_root_grant': None,
    'source_acceptance': False, 'parent_acceptance': False, 'formal_increment': 0,
    'scripts': {name: ref(HERE / name) for name in ['build-scope.py', 'build-metadata-templates.py', 'metadata-engine.template.py']},
    'spec_ref': ref(HERE / 'spec.json'), 'plan_ref': ref(HERE / 'grant-launcher-derivation-plan.json'),
    'request_example_ref': ref(HERE / 'root-request.example.json'), 'metadata_example_ref': ref(HERE / 'metadata-input.example.json'),
    'origin_cut_example_ref': ref(HERE / 'origin-cut.example.json'), 'static_audit_ref': ref(HERE / 'static-audit.json'),
    'before_ref': ref(HERE / 'inputs.before.json'), 'after_ref': ref(HERE / 'inputs.after.json'), 'tool_diagnostics_ref': tool,
    'actual_work': {'templates_executed': 0, 'AST_records': 8, 'fixed_inputs_rechecked': 28, 'input_drift': 0,
        'Git_commands': 0, 'source_canonical_index_writes': 0, 'Go_Node_SQL_HTTP_MODEL_calls': 0, 'new_nonzero_origins': 0},
    'fixed_source_scope': 'Only future exact15 patch1/commit1 onto actual closed43 produces58; no receipt ancestry, no generated binaries, no Mu replacement.',
    'resolved_input': 'New nonauthor suitability6333ec is explicitly referenced; it is conditional source-only suitability, not an execution grant.',
    'future_missing_inputs': ['Root explicit before/after revisions and confirmed origin cut', 'Root actual current canonical4/head/branch/status/handoff/MF',
        'Root new exact public runtime catalog and exclusive operation/output', 'new nonauthor actual bound-scope and metadata-template review',
        'new nonauthor actual emitted metadata review', 'Root actual CAS/seal and unique grant', 'separate actual outer Job source-launch authority'],
    'important_temporal_contract': 'activation-plan and scope-registration.payload contain reviewable future bytes but are unauthorized containers. Only actual reviewed CAS plus successful seal materializes active scope_registration.json. Grant is exclusive and separate; no preparation program invokes the source controller.',
    'important_evidence_contract': 'ABS/REL paths normalized for content checks; actual original completion/MF dictionaries are reused for fixed controller comparisons. External resources are exact runtime-catalog rows only. Old425/430 and later branch failure counts are not reconstructed here.',
    'remaining_open': ['fresh58 compilation/closure', 'independent current169 replay', 'GUI/install/NVDA/native frame/Web',
        'P02 checkpoint restore', 'live Host/provider/model', 'all formal acceptance'],
    'next': 'Root/nonauthor review this preparation first. Future commands and fields are specified in plan; placeholders deliberately fail until Root supplies actuals. Do not execute examples.',
})
entries = [ref(p) for p in sorted(HERE.iterdir()) if p.is_file()]
manifest = save('manifest.json', {'schema': 'researchos.sealed-preparation-manifest.v1', 'count': len(entries), 'entries': entries, 'self_excluded': True,
    'source_acceptance': False, 'execution_authorized': False})
print(json.dumps({'handoff': handoff, 'manifest': manifest, 'scripts': {name: ref(HERE / name) for name in ['build-scope.py', 'build-metadata-templates.py', 'metadata-engine.template.py']}, 'status': 'STOPPED'}, ensure_ascii=False))
