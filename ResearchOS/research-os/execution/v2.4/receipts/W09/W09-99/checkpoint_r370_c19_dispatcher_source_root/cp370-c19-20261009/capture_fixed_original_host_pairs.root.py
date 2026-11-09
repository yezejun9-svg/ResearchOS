"""Capture fixed failed tool pairs as diagnostics, without artifact authority."""
from pathlib import Path
import hashlib, json, os, sys

S = Path(__file__).resolve().parent
ROOT_ID = '01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUDITS = {
    'root': ('codex:/root', ROOT_ID, Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')),
    'backup': ('codex:/root/backup_regression_resources', '01a11cee-bf59-7a01-be0e-9f799f9b1084', Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\09\rollout-2026-10-09T03-12-51-01a11cee-bf59-7a01-be0e-9f799f9b1084.jsonl')),
}
SPECS = {
    1192: ('backup', '1e2439', 1, 1),
    1193: ('backup', '5e4bd1', 0, None),
    1196: ('backup', '4b13d9', 1, 1),
    1200: ('backup', '0ed939', 1, None),
    1203: ('root', 'e9b9d4', 1, 1),
    1204: ('root', 'ba869a', 1, 1),
}

def pin(p):
    p = Path(p); raw = p.read_bytes()
    return dict(path=str(p), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))

def save(p, raw):
    with p.open('xb') as f:
        f.write(raw); f.flush(); os.fsync(f.fileno())
    return pin(p)

def docs(value):
    if isinstance(value, dict):
        yield value
        for child in value.values(): yield from docs(child)
    elif isinstance(value, list):
        for child in value: yield from docs(child)
    elif isinstance(value, str):
        try: item = json.loads(value)
        except ValueError:
            for line in value.splitlines():
                try: item = json.loads(line)
                except ValueError: continue
                if isinstance(item, (dict, list)): yield from docs(item)
        else:
            if isinstance(item, (dict, list)): yield from docs(item)

def capture(ordinal):
    who, chunk, outer, pyexit = SPECS[ordinal]
    actor, thread, audit = AUDITS[who]
    found = []; calls = {}
    with audit.open('rb') as f:
        header = f.readline(); assert json.loads(header)['payload']['id'] == thread
        f.seek(0, 2); size = f.tell(); start = max(len(header), size - 32*1024*1024)
        f.seek(start)
        if start > len(header): f.readline()
        while True:
            offset = f.tell(); raw = f.readline()
            if not raw: break
            event = json.loads(raw); payload = event.get('payload', {})
            if event.get('type') != 'response_item' or not isinstance(payload, dict): continue
            typ = payload.get('type')
            if typ in ('function_call', 'custom_tool_call'):
                calls[payload['call_id']] = (offset, raw, event)
            elif typ in ('function_call_output', 'custom_tool_call_output') and payload.get('call_id') in calls:
                hosts = [x for x in docs(payload.get('output')) if x.get('chunk_id') == chunk and 'wall_time_seconds' in x and 'output' in x and ('exit_code' in x or 'session_id' in x)]
                if not hosts: continue
                assert len(hosts) == 1
                host = hosts[0]
                assert host.get('exit_code') == outer and host.get('session_id') is None
                if pyexit is not None:
                    assert f'ROOT_ACTUAL_PYTHON_EXIT={pyexit}' in host['output'] or f'ROOT_PYTHON_EXIT={pyexit}' in host['output'] or f'PYTHON_EXIT={pyexit}' in host['output']
                found.append((calls[payload['call_id']], (offset, raw, event), host))
    assert len(found) == 1, (ordinal, 'EXACT_ONE_FIXED_ACTUAL_HOST_REQUIRED', len(found))
    first, last, host = found[0]
    assert first[2]['ordinal'] < last[2]['ordinal']
    lines = [header, first[1], last[1]]; offsets = [0, first[0], last[0]]
    with audit.open('rb') as f:
        for off, line in zip(offsets, lines): f.seek(off); assert f.readline() == line
    raw_ref = save(S/f'original{ordinal}.fixed-actual.raw.root.jsonl', b''.join(lines))
    binding = dict(schema='researchos.root-original-host-failure-capture.v1', issued_by='codex:/root', actor_id=actor, actor_thread_id=thread, Root_thread_id=ROOT_ID, original_ordinal=ordinal,
        source_audit_path=str(audit), source_prefix_size_observed=size, source_line_offsets=offsets,
        original_line_sha256=[hashlib.sha256(x).hexdigest() for x in lines], source_line_bytes=[len(x) for x in lines], original_capture_ref=raw_ref,
        original_call_id=first[2]['payload']['call_id'], actual_host_chunk_id=chunk, actual_outer_exit=outer, actual_python_exit=pyexit,
        actual_native_exit=None, actual_Go_exit=None, actual_SQLite_exit=None, actual_dispatcher_exit=None, actual_model_exit=None,
        artifact_binding_authority=False, formal_acceptance=False, automatic_retry=False, counter_reset=False)
    ref = save(S/f'original{ordinal}.fixed-actual.binding.root.json', (json.dumps(binding,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    print(json.dumps(dict(original_ordinal=ordinal, binding_ref=ref, raw_ref=raw_ref, raw_kind='ACTUAL_HEADER_CALL_RESULT_3LF', formal_acceptance=False),ensure_ascii=False),flush=True)

assert len(sys.argv) >= 2
for arg in sys.argv[1:]: capture(int(arg))
