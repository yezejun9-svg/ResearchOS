"""Capture only original received public W09 author and review deliveries."""
from pathlib import Path
import ast, hashlib, json, os, sys, types

R = Path(r'D:\作品集\ResearchOS\research-os')
N = Path(__file__).resolve().parent
W = R / 'execution/v2.4/receipts/W09/W09-99'
THREAD = '01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUDIT = Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
tree = ast.parse((N / 'seal_continuation.live1013.root.py').read_bytes())
exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x, ast.FunctionDef)
    and x.name in {'pin', 'exact', 'save'}], type_ignores=[]), 'Root_pin_helpers_only', 'exec'), globals())
nf = W / 'full_w09_main_native_producer_source_codex/fullw09-20261010-03'
runtime_ref = exact(nf / 'full_w09_runtime.source.py', '1709bc96848fb52fe4ddde8591fe063576515aaabdc63d35630b1023a82ccc08', 40829)
runtime = types.ModuleType('root_w09_actual_source_audit_reader')
runtime.__file__ = runtime_ref['path']
sys.modules[runtime.__name__] = runtime
exec(compile(Path(runtime_ref['path']).read_bytes(), runtime.__file__, 'exec'), runtime.__dict__)
targets = {
    'profile-author': ('codex:/root/backup_regression_resources', '6e4153cce0bf202d744014f49122beb623588690f2d940c687228ec3c5ad4920'),
    'profile-review': ('codex:/root/native_temp_independent_review', '6b1a91959477f4e22171f8608314af38adbaaf84e25d0f13426f73d95ec0dd66'),
    'producer-author': ('codex:/root/w09_formal_profile_source_impl', '0b3000c9ca1d46a1df980535dfb0e57c55798d7eb5d7819c09dcab792168a447'),
    'producer-review': ('codex:/root/attach_fixture_source_review', '7f4a1b1b98e149527db9985c65714e9a8b7a188063d3501b0aedfbd6ff7346a7')}
found = {key: [] for key in targets}
with AUDIT.open('rb') as stream:
    header_raw = stream.readline()
    assert json.loads(header_raw)['payload']['id'] == THREAD
    stream.seek(0, 2); size = stream.tell()
    start = max(len(header_raw), size - 128 * 1024 * 1024)
    stream.seek(start)
    if start > len(header_raw):
        stream.readline()
    previous = None
    while True:
        offset = stream.tell(); raw = stream.readline()
        if not raw:
            break
        event = json.loads(raw)
        payload = event.get('payload', {})
        if event.get('type') == 'response_item' and payload.get('type') == 'agent_message' and previous:
            meta, meta_raw, meta_offset = previous
            if (meta.get('type') == 'inter_agent_communication_metadata'
                and event['ordinal'] == meta['ordinal'] + 1 and event['timestamp'] == meta['timestamp']
                and event.get('metadata', {}).get('client_authored') is False
                and payload.get('recipient') == '/root'):
                for key, (actor, digest) in targets.items():
                    if payload.get('author') == actor.removeprefix('codex:') and digest in raw.decode('utf-8'):
                        found[key].append((meta_raw, raw, meta_offset, offset))
        previous = (event, raw, offset)
refs = {}
for key, (actor, digest) in targets.items():
    retained = N / ('w09.' + key + '.actual-audit.root.json')
    if retained.exists():
        ref = pin(retained)
        runtime.actual_audit(ref, actor, digest)
        refs[key] = ref
        continue
    candidates = found[key]
    final = [x for x in candidates if 'Message Type: FINAL_ANSWER' in x[1].decode('utf-8')]
    chosen = final[-1] if final else candidates[-1] if candidates else None
    assert chosen is not None, 'ACTUAL_RECEIVED_SOURCE_DELIVERY_REQUIRED:' + key
    meta_raw, message_raw, meta_offset, message_offset = chosen
    path = N / ('w09.' + key + '.original-peer.raw.jsonl')
    with path.open('xb') as stream:
        stream.write(header_raw + meta_raw + message_raw); stream.flush(); os.fsync(stream.fileno())
    ref = save('w09.' + key + '.actual-audit.root.json', dict(
        schema='researchos.w09-native-producer.actual-audit.v1', actor_id=actor, Root_thread_id=THREAD,
        source_audit_path=str(AUDIT), source_line_offsets=[0, meta_offset, message_offset],
        original_line_sha256=[hashlib.sha256(x).hexdigest() for x in (header_raw, meta_raw, message_raw)],
        source_prefix_size_observed=size, original_capture_ref=pin(path), binding_sha256=digest))
    runtime.actual_audit(ref, actor, digest)
    refs[key] = ref
manifest_ref = save('w09.reviewed-source-actual-audits.root.json', dict(
    schema='researchos.root-w09-reviewed-source-actual-audits.v1', issued_by='codex:/root',
    root_thread_id=THREAD, audit_refs=refs, original_bytes_preserved=True, execution_grant=False,
    formal_acceptance=False, Canonical_written=False))
print(json.dumps(dict(manifest_ref=manifest_ref, audit_refs=refs,
    actual_public_peer_deliveries=4, Canonical_written=False), ensure_ascii=False, indent=2))
