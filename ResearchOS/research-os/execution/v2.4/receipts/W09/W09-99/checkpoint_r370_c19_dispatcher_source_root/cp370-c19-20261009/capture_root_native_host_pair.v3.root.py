"""Seal exact actual Root Native prepare/run hosts, including yielded starts."""
from pathlib import Path
import hashlib, json, os, sys

N = Path(__file__).resolve().parent
AUDIT = Path('C:/Users/yqyyds/.codex/sessions/2026/10/06/rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
THREAD = '01a11007-5233-7ca1-b71f-9e9e5ce84c98'

def docs(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from docs(child)
    elif isinstance(value, list):
        for child in value:
            yield from docs(child)
    elif isinstance(value, str):
        try:
            yield from docs(json.loads(value))
        except ValueError:
            pass

def save(path, raw):
    with path.open('xb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    return dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))

stem, chunk, expected_exit, session = sys.argv[1:5]
assert stem.startswith('nf6-') and stem.replace('-', '').isalnum() and len(chunk) == 6
expected_exit = None if expected_exit == 'NULL' else int(expected_exit)
session = None if session == 'NULL' else int(session)
assert (expected_exit is None and session is not None) or (expected_exit in (0,1) and session is None)
matches, calls = [], {}
with AUDIT.open('rb') as stream:
    header = stream.readline()
    assert json.loads(header)['payload']['id'] == THREAD
    stream.seek(0, 2); size = stream.tell()
    start = max(len(header), size - 32 * 1024 * 1024)
    stream.seek(start)
    if start > len(header):
        stream.readline()
    while True:
        offset = stream.tell(); raw = stream.readline()
        if not raw:
            break
        event = json.loads(raw); payload = event.get('payload', {})
        if event.get('type') != 'response_item' or not isinstance(payload, dict):
            continue
        if payload.get('type') in ('function_call', 'custom_tool_call'):
            calls[payload['call_id']] = (offset, raw, event)
        elif payload.get('type') in ('function_call_output', 'custom_tool_call_output') and payload.get('call_id') in calls:
            hosts = [host for host in docs(payload.get('output')) if host.get('chunk_id') == chunk]
            if hosts:
                assert len(hosts) == 1
                host = hosts[0]
                assert host.get('exit_code') == expected_exit and host.get('session_id') == session
                if expected_exit is not None:
                    assert f'ROOT_ACTUAL_PYTHON_EXIT={expected_exit}' in host['output']
                matches.append((calls[payload['call_id']], (offset, raw, event), host))
assert len(matches) == 1
first, last, host = matches[0]
assert first[2]['ordinal'] < last[2]['ordinal']
offsets, lines = [0, first[0], last[0]], [header, first[1], last[1]]
with AUDIT.open('rb') as stream:
    for offset, line in zip(offsets, lines):
        stream.seek(offset); assert stream.readline() == line
raw_ref = save(N / (stem + '.original.raw.jsonl'), b''.join(lines))
binding = dict(schema='researchos.root-native-actual-host-pair.v1', issued_by='codex:/root',
    root_thread_id=THREAD, source_audit_path=str(AUDIT), source_line_offsets=offsets,
    source_prefix_size_observed=size, original_line_sha256=[hashlib.sha256(line).hexdigest() for line in lines],
    source_line_bytes=[len(line) for line in lines], original_capture_ref=raw_ref,
    original_call_id=first[2]['payload']['call_id'], actual_host_chunk_id=chunk,
    tool_call_timestamp=first[2]['timestamp'], tool_result_timestamp=last[2]['timestamp'],
    actual_outer_exit=expected_exit, actual_python_exit=expected_exit,
    actual_exec_session_id=session, process_completion_observed=expected_exit is not None,
    yielded_session_is_completed=False if expected_exit is None else None,
    formal_acceptance=False, canonical_written=False)
ref = save(N / (stem + '.host-pair.root.json'),
           (json.dumps(binding, ensure_ascii=False, indent=2) + '\n').encode())
print(json.dumps(dict(actual_host_binding_ref=ref, original_capture_ref=raw_ref,
                     process_completion_observed=expected_exit is not None, formal_acceptance=False), ensure_ascii=False))
