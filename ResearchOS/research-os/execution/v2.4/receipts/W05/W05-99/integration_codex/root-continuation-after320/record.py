import sys
sys.dont_write_bytecode = True
import hashlib
import json
from pathlib import Path

assert sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode
ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
assert ROOT == Path('D:/作品集/ResearchOS/research-os').resolve()
READS = {}

def ref(path, expected=None):
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    raw = p.read_bytes()
    item = {'path': str(p), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    assert expected is None or item['sha256'] == expected, str(p)
    if p in READS:
        assert READS[p] == raw
    READS[p] = raw
    return item

def doc(path, expected=None):
    item = ref(path, expected)
    return json.loads(READS[Path(item['path'])]), item

def save(name, value):
    p = OUT / name
    raw = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
    with p.open('xb') as f:
        f.write(raw)
    return ref(p)

go3_dir = ROOT / 'execution/v2.4/receipts/W13/W13-03/desktop_go3_os_capture_revision_codex/01fc890602df43b89935fdbef4424137'
actual = go3_dir / 'actual-once'
spec, spec_ref = doc(go3_dir / 'spec.v2.json', '858463e5dd1f5570c372de42476c65042d5e3d675085317711fe377323a4db76')
grant, grant_ref = doc(ROOT / 'execution/v2.4/receipts/W13/W13-03/desktop_go3_root_once_authorization_codex/5b5e8bafa4fc41f18ccb058193b490d0/grant.json', '0b0b7230ff78213178c6fa82e5b324d682644d0470459014feedd227cde89956')
assert grant['authorized'] is True and grant['max_executions'] == 1
assert grant['spec_ref'] == spec_ref
for authority in grant['authority_refs']:
    assert ref(authority['path'], authority['sha256'])['bytes'] == authority['bytes']
for phase in ['inner', 'outer']:
    summary, summary_ref = doc(actual / (phase + '.summary.json'))
    owned, owned_ref = doc(actual / (phase + '.owned-result.json'))
    assert summary['status'] == 'COMPONENT_EVIDENCE_RECORDED'
    assert summary['first_failure'] is None and summary['diagnostics'] == []
    assert summary['actual_native_exit'] == owned['actual_native_exit'] == 0
    result = owned['result']
    assert result['actual_exit'] == 0 and result['timed_out'] is False and result['error'] is None
    cleanup = result['job_cleanup']
    assert cleanup['errors'] == []
    assert all(cleanup[k] is True for k in ['unnamed_exclusive_job', 'kill_on_job_close_configured', 'assigned_before_resume', 'job_idle_confirmed', 'primary_exit_confirmed', 'handles_closed'])
    after, after_ref = doc(actual / (phase + '.inputs.after.json'))
    assert after and all(row['match'] is True and row['error'] is None for row in after)
    for when in ['before', 'after']:
        runtime, runtime_ref = doc(actual / (phase + '.runtime.' + when + '.json'))
        assert runtime['measurement'] == 'POINT_IN_TIME_NOT_LIFECYCLE'
        assert runtime['transient_load_absence_proven'] is False

events, events_ref = doc(actual / 'inner.test-events.json')
assert len(events['passes']) == 64 and events['failure_or_skip'] == []
assert sorted(events['passes']) == sorted(spec['expected_pass_records'])
assert ref(actual / 'inner.stdout.raw')['sha256'] == events['stdout_sha256']
owned, owned_ref = doc(actual / 'inner.owned-result.json')
capture = owned['result']['debug_capture']
assert capture['complete'] is True
assert capture['create_process_count'] == capture['exit_process_count'] == capture['total_processes_last_observed'] == 1
assert capture['exit_event_code'] == owned['actual_native_exit'] == 0
assert capture['actual_loaded_file_handles_only'] is True
assert len(capture['modules']) == 10
assert all(row['before'] == row['after'] for row in capture['modules'])
manifest, original_manifest_ref = doc(actual / 'outer.manifest.json')
assert manifest['self_excluded'] is True
for item in manifest['entries']:
    assert ref(item['path'], item['sha256'])['bytes'] == item['bytes']

completion = save('go3.outer-tool-completion.json', {
    'schema': 'researchos.actual-tool-completion.v1', 'actor': 'codex:/root',
    'initial_tool_chunk': 'c030a4', 'initial_session_id': 30920,
    'final_tool_chunk': 'ce187a', 'actual_outer_exit': 0, 'actual_tool_output': '',
    'tool_trace_is_original_record': True,
    'capture_limit': 'Only the known returned fields are transcribed. This is not redirected native stdout/stderr. Native process exits and streams have independent owned-result/raw files.',
    'original_outer_manifest_ref': original_manifest_ref, 'grant_ref': grant_ref,
    'spec_ref': spec_ref, 'Go_native_exit': 0, 'inner_Python_native_exit': 0,
    'Go_debug_condition': 'DEBUG_ONLY_THIS_PROCESS_NEW_COMPONENT_OBSERVATION',
    'source_acceptance': False, 'Main_integration': False, 'formal_increment': 0,
})
origins = []
for chunk, bad_path, correction in [
    ('d2cc6b', 'execution/checkpoints/active.json', '093a39 found and read canonical execution/v2.4/checkpoint.json'),
    ('efbf62', 'execution/v2.4/receipts/W05/W05-99/integration_codex/parallel-source-and-go3-r320/prepared.json', '093a39 inventoried exact directory; 0d8c88 read actual prepared_refs.json'),
]:
    item = save('failure-origin.' + chunk + '.json', {
        'schema': 'researchos.actual-tool-failure-origin.v1',
        'origin_key': 'root-readonly-path-lookup-' + chunk, 'actor': 'codex:/root',
        'tool_trace': chunk, 'actual_outer_exit': 1, 'actual_native_product_exit': None,
        'event_kind': 'READONLY_POWERSHELL_FILE_LOOKUP', 'attempted_path': bad_path,
        'cause': 'Get-Content used a guessed nonexistent filename; valid preceding reads did not change the actual tool exit1.',
        'actual_error_excerpt': 'Cannot find path because it does not exist.',
        'raw_file': None,
        'raw_capture_limit': 'Original returned error and exit1 remain in tool trace; no redirected raw file was created. Large valid preceding outputs are not reconstructed.',
        'correction': correction, 'product_cases_run': 0, 'HTTP': 0,
        'canonical_registration': 'PENDING_AFTER_ROOT320_CUT',
        'count_once': True, 'counter_reset': False,
    })
    origins.append(item)
audit = save('audit.json', {
    'schema': 'researchos.root-go3-closed-evidence-summary.v1',
    'state': 'GO3_DEBUG_COMPONENT_CLOSED_PENDING_NONAUTHOR_EVIDENCE_REVIEW',
    'original_outer_manifest_ref': original_manifest_ref, 'outer_tool_completion_ref': completion,
    'grant_ref': grant_ref, 'spec_ref': spec_ref,
    'Go_native_exit': 0, 'inner_Python_native_exit': 0, 'actual_outer_exit': 0,
    'pass_records': 64, 'top_selectors': 3, 'skip_records': 0,
    'actual_loaded_file_handle_module_records': 10,
    'held_module_before_after_matches': 10, 'input_drift': 0,
    'own_Job_cleanup_complete': True, 'Go_debug_condition_is_new': True,
    'historical_normal_mode_OS_gap_rewritten': False,
    'Python_measurement': 'POINT_IN_TIME_NOT_LIFECYCLE',
    'product_reruns_by_this_recorder': 0,
    'source_acceptance': False, 'formal_increment': 0,
    'new_root_readonly_failure_origin_refs': origins,
})
ref(Path(__file__))
entries = [ref(p) for p in sorted(READS, key=str)]
mf = save('manifest.json', {'entries': entries, 'self_excluded': True})
handoff = save('handoff.json', {'audit_ref': audit, 'manifest_ref': mf,
    'status': 'CLOSED_GO3_COMPONENT_RECEIPTS_PENDING_INDEPENDENT_REVIEW',
    'formal_increment': 0, 'failure_origin_refs': origins})
assert all(path.read_bytes() == raw for path, raw in READS.items())
print(json.dumps({'handoff_ref': handoff, 'manifest_ref': mf, 'audit_ref': audit, 'failure_origin_refs': origins}, ensure_ascii=True))
