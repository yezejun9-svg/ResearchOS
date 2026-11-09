import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent


def ref(p):
    b = p.read_bytes()
    return {'path': str(p), 'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b)}


def save(name, d):
    with (P / name).open('xb') as f:
        f.write((json.dumps(d, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    return ref(P / name)


inputs = json.loads((P / 'metadata-inputs.after.json').read_text(encoding='utf-8'))
for r in inputs:
    assert ref(Path(r['path'])) == r
diagnostics = save('tool-diagnostics.json', {
    'kind': 'VISIBLE_TOOL_KNOWN_FIELDS_NOT_RECONSTRUCTED_NATIVE_STREAMS',
    'read_inventory_outer_zero': ['36c116', '4c2a66', '2ae5a8'],
    'readonly_python_outer_native_zero': ['f24bc7', '8e3c9c', 'def5d1', '08aa7a', '03894b', 'b04a16'],
    'output_truncation': ['f24bc7 selected full-path runtime too broadly, actual0; not a new native failure.', '3409e4 printed full list before the known AttributeError; original visible output truncated.'],
    'failed_tool_origin_ref': ref(P / 'failure-origin.3409e4.json'),
    'failure_count_increment': 1, 'counter_reset': False,
    'successful_extraction': {'tool_chunk': 'b04a16', 'actual_outer_exit': 0, 'actual_native_python_exit': 0,
        'bridge': 'Pinned Python followed by explicit PowerShell exit $LASTEXITCODE',
        'argv': ['C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe', '-I', '-S', '-X', 'utf8', str(P / 'extract-public-receipts.py')],
        'known_stdout': {'union': 25, 'metadata_reads': 84, 'conflicts': 0, 'missing_hashes': 0},
        'separate_native_stdout_stderr_captured': False},
    'OS_files_opened_hashed_loaded': 0, 'ProcessModule_probe_calls': 0, 'product_SQL_Go_Node_HTTP_MODEL_calls': 0,
    'source_canonical_index_writes': 0,
})
handoff = save('handoff.json', {
    'schema': 'researchos.cli43-windows-resource-observation-handoff.v1', 'actor': 'codex:/root/sources_parent_impl',
    'state': 'READONLY_OBSERVATION_SEALED_STOPPED', 'authorized_execution': False, 'source_acceptance': False,
    'union_count': 25, 'basis_counts_overlapping': {'loaded_actual_handle': 9, 'priorpointtime': 23, 'resourceinventory': 23},
    'candidate_refs': ref(P / 'windows-os-union.candidate-refs.json'), 'per_row_evidence_ref': ref(P / 'windows-os-union.evidence.json'),
    'findings_ref': ref(P / 'findings.json'), 'input_before_ref': ref(P / 'metadata-inputs.before.json'), 'input_after_ref': ref(P / 'metadata-inputs.after.json'),
    'tool_diagnostics_ref': diagnostics, 'failure_origin_refs': [ref(P / 'failure-origin.3409e4.json')],
    'current_root_failure_count_not_modified': True, 'metadata_input_files_rechecked': 84, 'input_drift': 0,
    'minimal_union': 'Existing23 OS refs plus powrprof.dll and umpdc.dll from actual Go3 debug hFile records; the latter are not guessed names.',
    'resource_basis': 'The sealed historical bytes/path references were extracted, not the current OS files read or hashed. Original extended paths/case preserved in evidence, normalized only for dedup.',
    'http_cli_module_claim': 'UNKNOWN: Root14 HTTP78/G2 fixture4 do not turn their Python controller DLL point snapshots into native Go/CLI/worker loaded-module proof.',
    'future_requirement': 'Root may use these25 as concrete preauthorization candidates. Future current resources/actual child debug-tree loads require separate grant and fresh observation; unknown network DLLs remain UNKNOWN, not silently whitelisted.',
    'remaining': ['current OS bytes verification', 'actual CLI43 child network module set', 'whole lifecycle proof', 'future Root execution grant'],
    'no_model_credential_private_access': True, 'no_product_or_CAS_invocation': True, 'formal_increment': 0,
})
entries = [ref(x) for x in sorted(P.iterdir()) if x.is_file()]
mf = save('manifest.json', {'count': len(entries), 'entries': entries, 'self_excluded': True, 'execution_authorized': False})
print(json.dumps({'handoff': handoff, 'manifest': mf, 'failure_origin': ref(P / 'failure-origin.3409e4.json'), 'STOPPED': True}, ensure_ascii=False))
