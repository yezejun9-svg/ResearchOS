import hashlib
import json
from pathlib import Path

Q = Path(__file__).resolve().parent
R = Path('D:/作品集/ResearchOS/research-os')
B = R / 'execution/v2.4/receipts/W05/W05-99'
LOG = Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T03-12-51-01a11cee-bf59-7a01-be0e-9f799f9b1084.jsonl')
AUTHOR = 'codex:/root/backup_regression_resources'
THREAD = '01a11cee-bf59-7a01-be0e-9f799f9b1084'

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def pin(path):
    raw = path.read_bytes()
    return {'path': path.as_posix(), 'sha256': digest(raw), 'bytes': len(raw)}

def save(name, value):
    path = Q / name
    raw = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    with path.open('xb') as handle:
        handle.write(raw)
    return {'path': path.as_posix(), 'sha256': digest(raw), 'bytes': len(raw)}

def capture(chunks):
    prefix = LOG.stat().st_size
    calls = {}
    matches = {}
    offset = 0
    with LOG.open('rb') as handle:
        header_raw = handle.readline()
        header = json.loads(header_raw)
        assert header['payload']['id'] == THREAD
        offset = len(header_raw)
        while offset < prefix:
            raw = handle.readline()
            if not raw or offset + len(raw) > prefix:
                break
            row = json.loads(raw)
            payload = row.get('payload', {})
            kind = payload.get('type')
            call_id = payload.get('call_id')
            if kind in ('custom_tool_call', 'function_call') and call_id:
                source = str(payload.get('input', payload.get('arguments', '')))
                if 'task84_' in source:
                    calls[call_id] = (offset, raw, row)
            if kind in ('custom_tool_call_output', 'function_call_output') and call_id in calls:
                output = str(payload.get('output', ''))
                for chunk in chunks:
                    if chunk in output:
                        assert chunk not in matches
                        matches[chunk] = (calls[call_id], (offset, raw, row))
            offset += len(raw)
    assert set(matches) == set(chunks)
    result = []
    for chunk, ordinal in chunks.items():
        call, returned = matches[chunk]
        chosen = [(0, header_raw, header), call, returned]
        raw_path = Q / ('original-' + chunk + '.raw.jsonl')
        with raw_path.open('xb') as handle:
            handle.write(b''.join(row[1] for row in chosen))
        raw_ref = pin(raw_path)
        binding_ref = save('original-' + chunk + '.binding.json', {
            'schema': 'researchos.actual-tool-source-binding.v1',
            'source_actor': AUTHOR,
            'source_thread_id': THREAD,
            'parent_thread_id': header['payload'].get('parent_thread_id'),
            'original_failure_ordinal': ordinal,
            'original_chunk_id': chunk,
            'actual_tool_name': call[2]['payload'].get('name'),
            'original_call_id': call[2]['payload']['call_id'],
            'source_audit_path': LOG.as_posix(),
            'source_prefix_size_observed': prefix,
            'source_line_offsets': [row[0] for row in chosen],
            'source_line_bytes': [len(row[1]) for row in chosen],
            'original_line_sha256': [digest(row[1]) for row in chosen],
            'original_capture_ref': raw_ref,
            'tool_call_timestamp': call[2]['timestamp'],
            'tool_result_timestamp': returned[2]['timestamp'],
            'actual_outer_exit': 1,
            'actual_python_exit': None,
            'actual_rg_exit': None,
            'actual_go_exit': None,
            'actual_native_exit': None,
            'actual_sql_exit': None,
            'actual_model_exit': None,
            'actual_tp_exit': None,
            'representation': 'Exact original header/call/returnedoutput bytes. Batch return retains the actual observed tool truncation; no lost stdout bytes are reconstructed.',
            'formal_acceptance': False,
        })
        io_ref = save('original-' + chunk + '.complete-observed-IO.json', {
            'representation': 'Decoded complete actual original call and returnedoutput rows; exact original JSONL bytes are separately pinned.',
            'original_failure_ordinal': ordinal,
            'raw_ref': raw_ref,
            'binding_ref': binding_ref,
            'actual_original_call': call[2],
            'actual_original_returnedoutput': returned[2],
        })
        origin_ref = save('failure-origin.' + str(ordinal) + '.json', {
            'original_failure_ordinal': ordinal,
            'original_chunk_id': chunk,
            'failure_category': 'READONLY_SOURCE_DISCOVERY_OR_METADATA',
            'raw_ref': raw_ref,
            'binding_ref': binding_ref,
            'complete_observed_io_ref': io_ref,
            'actual_outer_exit': 1,
            'actual_python_exit': None,
            'actual_go_exit': None,
            'actual_native_exit': None,
            'actual_sql_exit': None,
            'actual_model_exit': None,
            'actual_tp_exit': None,
            'product_execution': False,
            'failure_count_reset': False,
        })
        result.append({'ordinal': ordinal, 'chunk': chunk, 'raw_ref': raw_ref, 'binding_ref': binding_ref, 'io_ref': io_ref, 'origin_ref': origin_ref})
    return result

def main():
    # Root allocates each original ordinal. This script never updates that ledger.
    errors = capture({'834171': 1103, 'eabfc0': 1104, '2615aa': 1105})
    paths = {
        'queue_upgrade': R / 'internal/domain/backup_queue_upgrade.go',
        'configuration_upgrade': R / 'internal/domain/backup_configuration_upgrade.go',
        'prepared_upgrade_source': B / 'prepared_abandonment_schema_upgrade_revision_codex/6b0cb88050554e688314092dbebc6ba6/candidate-root/internal/domain/backup_prepared_abandonment_upgrade.go',
        'builder_contract': B / 'schema21_programme_builder_source_codex/main21b-20261010-01/contract.v2.json',
        'formal_profile_source_proposal': B / 'a04_formal_profile_json_identity_revision_codex/90e455115bf34f81bd29e601debf511a/formal_profile_w05.identity.v4.proposed.py',
        'restored21_runtime_caller': B / 'restored21_session_runtime_caller_v3_source_codex/r21v3caller-20261009-01/contract.json',
    }
    refs = {name: pin(path) for name, path in paths.items()}
    assert refs['builder_contract']['sha256'] == '1472e40c8806dcb82de62352378c306077fef8e674925b57941f305527bf4402'
    assert refs['builder_contract']['bytes'] == 22410
    report = {
        'schema': 'researchos.old21-programme-consumer-readonly.v1',
        'source_actor': AUTHOR,
        'decision': 'NO_FIXED_OLD21_PROGRAMME_QUALIFICATION_JSON_SCHEMA_IN_INSPECTED_CONSUMERS',
        'scope': 'Only actual enumerated W05 consumer code and known immutable Source contract; no product execution or acceptance.',
        'consumer_refs': refs,
        'findings': [
            {'consumer': 'queue_upgrade', 'lines': [320, 325, 329, 352, 355, 374, 385], 'required_inputs': ['LocalUpgradeOptions.SourceRoot', 'TargetRoot', 'SourceProgram', 'TargetProgram', 'Source', 'KeyFile', 'Snapshot', 'Destination', 'Plan'], 'use': 'Exact frozen Source release21 and target release22, exact contiguous database migrations1..21 and expected source schema, read actual programme bytes and bind Digest(source/target) into rehearsal plan. No programme qualification JSON parameter/decoder.'},
            {'consumer': 'configuration_upgrade', 'lines': [179, 183, 206, 209, 228, 239], 'required_inputs': ['SourceRoot22', 'TargetRoot23', 'SourceProgram', 'TargetProgram', 'source_database_schema22'], 'use': 'Separate schema22-to23 path. It consumes programme bytes/release inventories, not old21 qualification JSON.'},
            {'consumer': 'prepared_upgrade_source', 'lines': [26, 397, 405, 409, 421, 423, 425, 451, 456, 458], 'required_inputs': ['Plan=schema23-to24-prepared-abandonment-v1', 'SourceRoot23', 'TargetRoot24', 'SourceProgram', 'TargetProgram', 'actual current executable hash'], 'use': 'Require exact23/24 inventory and actual invoking executable == source or target programme Digest. Rehearsal report records source_program_sha256, target_program_sha256, source/target inventory/schema pins; separate native apply authority is required. Old21 cannot substitute for SourceRoot23/programme.'},
            {'consumer': 'builder_contract', 'lines': [300, 341, 374], 'required_inputs': ['independent actual provenance review before qualification', 'externally captured full actual build call/return'], 'use': 'Builder candidates only, qualification_ref remains null; contract states qualification required but does not define a downstream old21 programme qualification schema.'},
            {'consumer': 'restored21_runtime_caller', 'lines': [42], 'required_inputs': ['individual descendant actual PID/FILETIME/raw streams/exit', 'genuine21/22 programme qualification'], 'use': 'Nine-parent development evidence cannot qualify genuine21/22 programmes; explicitly PARTIAL/open. No programme qualification JSON decoder in this caller contract.'},
            {'consumer': 'formal_profile_source_proposal', 'lines': [394, 604, 721, 732, 737, 758, 773], 'required_inputs': ['formal current owner/exact frozen plan', 'live original capture bundle and Root original grant/review delivery'], 'use': 'This is a historical Source proposal, not proved current Main file; no dedicated old21 programme qualification field/schema in its inspected definitions. Embedded domain Qualification schemas are product/model qualification, not built programme provenance.'},
        ],
        'actual_programmes_root_reported_not_reexecuted': {
            'control': {'sha256': 'cf84d4dc025f25ee97cb7189b06be892e87a14899acb48b3d9640e4f9f1d775a', 'bytes': 31963136},
            'backup': {'sha256': '774eb63e00e6eae6e0194d92cd778adeb540ec997508ef423973fc3be0bef441', 'bytes': 17053184},
        },
        'limits': ['No global schema absence claim; conclusion limited to inspected actual consumer code.', 'Current formal_profile_w05 Main path was not confirmed; proposed Source is explicitly labeled.', 'Programme qualification, runtime resource qualification, public upgrade acceptance and formal case acceptance remain distinct.', 'Task83 actual independent programme review remains Root-owned; this report issues no qualification.'],
        'diagnostics': errors,
        'authority': 'NONE',
        'execution_grant': False,
        'formal_acceptance': False,
        'product_invocations': 0,
        'canonical_writes': 0,
        'live_canonical_handles_held': False,
    }
    report_ref = save('consumer-readonly-result.json', report)
    print(json.dumps({'report_ref': report_ref, 'consumer_refs': refs, 'diagnostics': errors}, ensure_ascii=False))

if __name__ == '__main__':
    try:
        main()
    except BaseException:
        print('ROOT_PYTHON_EXIT=1')
        raise
    print('ROOT_PYTHON_EXIT=0')
