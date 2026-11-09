import ast
import hashlib
import json
import pathlib
from datetime import datetime, timezone

OUT = pathlib.Path(__file__).resolve().parent
ROOT = pathlib.Path('D:/作品集/ResearchOS/research-os')
def ref(p, b=None):
    if b is None:
        b = p.read_bytes()
    return {'path': str(p), 'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b)}
def write(name, value):
    b = (json.dumps(value, ensure_ascii=False, indent=2)+'\n').encode('utf-8')
    with (OUT/name).open('xb') as f:
        f.write(b)
    return ref(OUT/name, b)

ast.parse((OUT/'observe.py').read_text(encoding='utf-8'))
ast.parse(pathlib.Path(__file__).read_text(encoding='utf-8'))
findings = json.loads((OUT/'findings.json').read_text(encoding='utf-8'))
old = ROOT/'execution/v2.4/receipts/W05/W05-99/cli43_windows_resource_observation_codex/7a89658e87ad469dab9d17c80ed7270d/windows-os-union.evidence.json'
oldraw = old.read_bytes()
oldref = ref(old, oldraw)
assert oldref['sha256'] == '05f8a8fd63b1a4b091ac5ea589796b499cbfef91b104fb0a519758c98200d93e'
rows = json.loads(oldraw)
prior = []
for i, row in enumerate(rows):
    assert len(row['versions']) == 1
    v = row['versions'][0]
    prior.append({'path': row['path'], 'sha256': v['sha256'], 'bytes': v['bytes'],
                  'basis_classes': sorted({e['basis'] for e in v['evidence']}),
                  'prior_evidence_ref': oldref, 'locator': {'json_pointer': '/'+str(i)},
                  'current_task_loaded_observation': False})
priorref = write('prior-25-basis-index.json', {'files': prior,
    'basis_is_inherited_metadata_not_reobserved_loading': True})
assert ref(old) == oldref
src = json.loads((OUT/'frozen-go-source-scan.json').read_text(encoding='utf-8'))
source_by_path = {r['path']: r for r in src['files']}
bridges = []
for suffix, lo, hi in [('internal/syscall/windows/sysdll/sysdll.go', 1, 100),
                      ('syscall/dll_windows.go', 121, 165),
                      ('runtime/os_windows.go', 247, 249)]:
    matches = [r for r in src['files'] if r['path'].replace('\\','/').endswith('/src/'+suffix)]
    assert len(matches) == 1
    p = pathlib.Path(matches[0]['path'])
    raw = p.read_bytes()
    assert ref(p, raw) == matches[0]
    lines = raw.decode('utf-8').splitlines()
    bridges.append({'source_ref': matches[0], 'line_start': lo, 'line_end': min(hi,len(lines)),
                    'lines': [{'line': i, 'text': lines[i-1]} for i in range(lo,min(hi,len(lines))+1)]})
bridgeref = write('system32-static-loader-bridges.json', {
    'basis': 'STATIC_SOURCE_SYSTEM_DIRECTORY_SELECTION_NOT_RUNTIME_RESOLUTION_PROOF', 'bridges': bridges})
docref = write('official-pe-format-reference.json', {
    'url': 'https://learn.microsoft.com/en-us/windows/win32/debug/pe-format',
    'publisher': 'Microsoft', 'browsing_content_returned': True,
    'actual_HTTP_status': None, 'native_exit': None,
    'used_sections': ['MS-DOS stub / PE signature', 'COFF File Header',
                      'Optional Header Standard Fields', 'Optional Header Windows-Specific Fields',
                      'Optional Header Data Directories', 'Section Table',
                      'Import Directory Table', 'Delay-Load Directory Table'],
    'parser_policy': ['Validate PE signature, optional magic and number/size of directory entries.',
                      'Map RVAs only to uniquely matched backed section bytes or bounded header bytes.',
                      'Read null-terminated ASCII DLL names and stop at zero descriptors.',
                      'Delay descriptor VA form or unknown attributes remains UNKNOWN.',
                      'Never load or run an image; do not recursively parse OS DLL imports.']})
tools = [
    ('11ebda', 'Read sealed compiler images/runtime/manifest shapes'),
    ('a453ce', 'Inventory System32 DLL filenames and fixed source literal lines'),
    ('4aa590', 'Read actual runtime uint16 arrays, loader calls and old25 shape'),
    ('fce216', 'Parse observe.py with ast only'),
    ('cfe698', 'Execute public byte-only observation, no PE/DLL execution'),
    ('92ea61', 'Read sealed results and source loader selection lines'),
    ('ae17a2', 'Read inherited old25 evidence structure')]
diagnosticsref = write('tool-diagnostics.json', {
    'schema': 'researchos.readonly-resource-tool-observations.v1',
    'rows': [{'tool_chunk': chunk, 'purpose': purpose, 'actual_outer_exit': 0,
              'actual_native_python_exit': 0, 'bridge': 'PowerShell explicit exit $LASTEXITCODE',
              'separate_native_raw_stream_files': None, 'original_tool_result_location': 'conversation tool chunk '+chunk}
             for chunk, purpose in tools],
    'earlier_successful_discovery_chunks': ['92cea3','6ef9b3'],
    'no_new_nonzero_origin': True, 'counter_reset': False,
    'historical_origin_3409e4_untouched_and_not_recounted': True,
    'product_execution': 0, 'process_module_enumeration_or_DLL_load': 0})
runtime = json.loads((OUT/'runtime-v2.json').read_text(encoding='utf-8'))
union = json.loads((OUT/'system32-union.files.json').read_text(encoding='utf-8'))
assert len(runtime['files']) == 1221 and len(union['files']) == 33
assert len(runtime['added_static_candidate_files']) == 8
assert len({r['path'].casefold() for r in runtime['files']}) == 1221
assert json.loads((OUT/'inputs.before.json').read_text(encoding='utf-8'))['files'] == json.loads((OUT/'inputs.after.json').read_text(encoding='utf-8'))['files']
handoff = write('handoff.json', {
    'schema': 'researchos.public-static-resource-catalog-handoff.v1',
    'actor': 'codex:/root/sources_parent_impl', 'status': 'SEALED_STATIC_CANDIDATE_CATALOG_STOPPED',
    'source_writer': 'STOPPED', 'findings_ref': ref(OUT/'findings.json'),
    'runtime_v2_ref': ref(OUT/'runtime-v2.json'), 'system32_union_ref': ref(OUT/'system32-union.files.json'),
    'candidate_evidence_ref': ref(OUT/'os-candidate-evidence.json'), 'prior_basis_ref': priorref,
    'static_loader_bridge_ref': bridgeref, 'official_format_reference_ref': docref,
    'tool_diagnostics_ref': diagnosticsref,
    'counts': {k: findings[k] for k in ['system32_inventory_count','go_source_files_scanned','pe_images',
              'source_and_pe_literal_observations','static_distinct_system32_names','prior_os_count',
              'os_union_count','added_os_count','runtime_v2_count','inputs_count']},
    'added_names': findings['added_names'], 'input_drift': [],
    'three_PE_direct_imports': 'kernel32.dll only; all delay directories zero',
    'resource_use': 'files exactrefs may be used as finite preauthorization candidates after Root review; recheck current bytes before any future use',
    'inherited_other_runtime_rows': 'Original 1213 refs copied exactly; 25 System32 rows rehashed here; remaining rows not rehashed by this observation.',
    'old25_basis': 'Inherited actual handle/priorpointtime/resourceinventory evidence remains scoped to original process; no new loaded claim.',
    'source_selection': 'Fixed manifest inventory under runtime, syscall, internal/syscall/windows and net, .go/.s excluding *_test.go/testdata; not a compiled reachability proof.',
    'open_gates': findings['open_gates'], 'future_complete_network_DLL_trace': None,
    'future_execution_authorized': False, 'source_acceptance': False, 'formal_increment': 0,
    'Go_Node_SQL_HTTP_model_calls': 0, 'DLL_loads_or_API_enumeration': 0,
    'source_canonical_index_writes': 0, 'new_failure_origins': [],
    'registered_and_pending_counters_modified': False,
    'manifest_path': str(OUT/'manifest.json'), 'sealed_at': datetime.now(timezone.utc).isoformat()})
entries = [ref(p) for p in sorted(OUT.iterdir(), key=lambda p:p.name) if p.is_file() and p.name != 'manifest.json']
mf = write('manifest.json', {'schema': 'researchos.public-observation-manifest.v1',
    'actor': 'codex:/root/sources_parent_impl', 'entries': entries, 'count': len(entries),
    'self_excluded': True, 'handoff_included': True, 'product_execution': 0})
print(json.dumps({'handoff_ref': handoff, 'manifest_ref': mf,
                  'runtime_v2_ref': ref(OUT/'runtime-v2.json'),
                  'os_union_ref': ref(OUT/'system32-union.files.json'),
                  'diagnostics_ref': diagnosticsref}, ensure_ascii=False))
