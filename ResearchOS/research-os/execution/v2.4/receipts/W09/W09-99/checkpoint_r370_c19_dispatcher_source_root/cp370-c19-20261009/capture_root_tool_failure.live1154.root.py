"""Preserve a failed actual Root host pair without an invented artifact digest."""
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

ordinal, chunk, python_exit = int(sys.argv[1]), sys.argv[2], sys.argv[3]
assert ordinal in (1152, 1153) and len(chunk) == 6
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
                assert len(hosts) == 1 and hosts[0].get('exit_code') == 1
                matches.append((calls[payload['call_id']], (offset, raw, event), hosts[0]))
assert len(matches) == 1
first, last, host = matches[0]
assert first[2]['ordinal'] < last[2]['ordinal']
if python_exit != 'NULL':
    assert python_exit == '1' and 'ROOT_ACTUAL_PYTHON_EXIT=1' in host['output']
offsets, lines = [0, first[0], last[0]], [header, first[1], last[1]]
with AUDIT.open('rb') as stream:
    for offset, line in zip(offsets, lines):
        stream.seek(offset); assert stream.readline() == line
raw_ref = save(N / ('original' + str(ordinal) + '.actual-root.raw.jsonl'), b''.join(lines))
binding = dict(schema='researchos.root-actual-tool-original-binding.v1', issued_by='codex:/root',
    root_thread_id=THREAD, original_ordinal=ordinal, source_audit_path=str(AUDIT),
    source_line_offsets=offsets, source_prefix_size_observed=size,
    original_line_sha256=[hashlib.sha256(line).hexdigest() for line in lines],
    source_line_bytes=[len(line) for line in lines], original_capture_ref=raw_ref,
    original_call_id=first[2]['payload']['call_id'], actual_host_chunk_id=chunk,
    tool_call_timestamp=first[2]['timestamp'], tool_result_timestamp=last[2]['timestamp'],
    actual_outer_exit=1, actual_python_exit=None if python_exit == 'NULL' else 1,
    actual_Native_exit=None, actual_Go_exit=None, actual_SQL_exit=None,
    actual_dispatcher_exit=None, actual_model_probe_exit=None, actual_TP_exit=None,
    counter_reset=False, formal_acceptance=False)
ref = save(N / ('original' + str(ordinal) + '.actual-root.binding.json'),
           (json.dumps(binding, ensure_ascii=False, indent=2) + '\n').encode())
print(json.dumps(dict(original_ordinal=ordinal, binding_ref=ref, original_capture_ref=raw_ref,
                     canonical_written=False, counter_reset=False), ensure_ascii=False))
