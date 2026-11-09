"""Add exact framing metadata to a previously captured genuine Root pair."""
from pathlib import Path
import hashlib, json, os, sys

def pin(p):
    p = Path(p); b = p.read_bytes()
    return dict(path=str(p), sha256=hashlib.sha256(b).hexdigest(), bytes=len(b))

assert len(sys.argv) == 5
source = dict(path=sys.argv[1], sha256=sys.argv[2], bytes=int(sys.argv[3]))
assert pin(source['path']) == source
audit = json.loads(Path(source['path']).read_bytes())
assert audit['actor_id'] == 'codex:/root'
assert audit['Root_thread_id'] == '01a11007-5233-7ca1-b71f-9e9e5ce84c98'
raw_ref = audit['original_capture_ref']; assert pin(raw_ref['path']) == raw_ref
lines = Path(raw_ref['path']).read_bytes().splitlines(keepends=True)
assert len(lines) == 3
assert [hashlib.sha256(x).hexdigest() for x in lines] == audit['original_line_sha256']
events = [json.loads(x) for x in lines]
assert events[0]['payload']['id'] == audit['Root_thread_id']
assert events[1]['payload']['type'] in ('function_call', 'custom_tool_call')
assert events[2]['payload']['type'] in ('function_call_output', 'custom_tool_call_output')
call_id = events[1]['payload']['call_id']
assert events[2]['payload']['call_id'] == call_id
with Path(audit['source_audit_path']).open('rb') as f:
    for offset, line in zip(audit['source_line_offsets'], lines):
        f.seek(offset); assert f.readline() == line
audit.update(source_line_bytes=[len(x) for x in lines], original_call_id=call_id)
target = Path(sys.argv[4]); data = (json.dumps(audit, ensure_ascii=False, indent=2)+'\n').encode('utf-8')
with target.open('xb') as f:
    f.write(data); f.flush(); os.fsync(f.fileno())
assert pin(raw_ref['path']) == raw_ref
print(json.dumps(dict(binding_ref=pin(target), framing_added_only=True, original_capture_ref=raw_ref,
    canonical_written=False, formal_acceptance=False), ensure_ascii=False))
