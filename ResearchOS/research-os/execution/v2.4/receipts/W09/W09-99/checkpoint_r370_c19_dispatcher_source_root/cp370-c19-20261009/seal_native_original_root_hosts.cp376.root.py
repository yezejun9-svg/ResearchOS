"""Keep exact bounded Root tool host records, including observed failures."""
from pathlib import Path
import hashlib, json, os, re
N = Path(__file__).resolve().parent
AUDIT = Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
THREAD = '01a11007-5233-7ca1-b71f-9e9e5ce84c98'
TARGETS = {
    'G01-initial': ('c18f37', None),
    'G01-final': ('8d91e4', None),
    'G02-initial': ('175ec0', None),
    'G02-final-original1121': ('823cae', 1121),
    'A06-initial': ('11e55c', None),
    'A06-progress': ('c988a0', None),
    'A06-final-original1125': ('03fa48', 1125),
}

def pin(path):
    raw = Path(path).read_bytes()
    return dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))

def save(name, raw):
    path = N/name
    with path.open('xb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    return pin(path)

def documents(value):
    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from documents(item)
    elif isinstance(value, list):
        for item in value:
            yield from documents(item)
    elif isinstance(value, str):
        try:
            decoded = json.loads(value)
        except ValueError:
            return
        yield from documents(decoded)

found = {}
calls = {}
with AUDIT.open('rb') as stream:
    header = stream.readline()
    assert json.loads(header)['payload']['id'] == THREAD
    stream.seek(0, 2)
    prefix = stream.tell()
    start = max(len(header), prefix-32*1024*1024)
    stream.seek(start)
    if start > len(header):
        stream.readline()
    while stream.tell() < prefix:
        offset = stream.tell()
        raw = stream.readline()
        event = json.loads(raw)
        payload = event.get('payload', {})
        if event.get('type') != 'response_item' or not isinstance(payload, dict):
            continue
        if payload.get('type') in ('function_call', 'custom_tool_call'):
            calls[payload.get('call_id')] = (offset, raw)
        elif payload.get('type') in ('function_call_output', 'custom_tool_call_output'):
            call_id = payload.get('call_id')
            if call_id not in calls:
                continue
            rows = list(documents(payload.get('output')))
            for name, (chunk, ordinal) in TARGETS.items():
                matches = [row for row in rows if row.get('chunk_id') == chunk]
                if matches:
                    assert len(matches) == 1 and name not in found
                    found[name] = (calls[call_id], (offset, raw), matches[0])
assert set(found) == set(TARGETS)
published = []
with AUDIT.open('rb') as stream:
    for name, (chunk, ordinal) in TARGETS.items():
        (call_offset, call), (result_offset, result), observation = found[name]
        lines = [header, call, result]
        offsets = [0, call_offset, result_offset]
        for offset, line in zip(offsets, lines):
            stream.seek(offset)
            assert stream.readline() == line
        raw_ref = save('native.'+name+'.actual-host.raw.jsonl', b''.join(lines))
        outer = observation.get('exit_code')
        text = observation.get('output', '')
        marked = re.findall(r'(?m)^ROOT_ACTUAL_PYTHON_EXIT=(-?\d+)\s*$', text)
        python_exit = int(marked[0]) if len(marked) == 1 else None
        if ordinal is not None:
            assert outer == python_exit == 1
        binding = dict(schema='researchos.root-native-original-host-binding.v1',
                       actor_id='codex:/root', Root_thread_id=THREAD,
                       original_failure_ordinal=ordinal, original_chunk_id=chunk,
                       source_audit_path=str(AUDIT), source_prefix_size_observed=prefix,
                       source_line_offsets=offsets,
                       original_line_sha256=[hashlib.sha256(line).hexdigest() for line in lines],
                       original_capture_ref=raw_ref, actual_outer_exit=outer,
                       marked_actual_python_exit=python_exit,
                       actual_session_id=observation.get('session_id'),
                       automatic_retry=False, counter_reset=False,
                       unobserved_child_exits_are_null=True)
        binding_ref = save('native.'+name+'.actual-host.binding.json',
                           (json.dumps(binding, ensure_ascii=False, indent=2)+'\n').encode())
        published.append(dict(name=name, raw_ref=raw_ref, binding_ref=binding_ref,
                              actual_outer_exit=outer, actual_python_exit=python_exit))
manifest_ref = save('native.current-three.actual-root-hosts.cp376.json',
                    (json.dumps(dict(schema='researchos.root-three-native-host-manifest.v1',
                                     entries=published, formal_acceptance=False,
                                     counter_reset=False), ensure_ascii=False, indent=2)+'\n').encode())
print(json.dumps(dict(manifest_ref=manifest_ref, captured_original_pairs=len(published),
                      original_failed_ordinals=[1121,1125],
                      Main_written=False, Canon_written=False,
                      formal_acceptance=False), ensure_ascii=False))
