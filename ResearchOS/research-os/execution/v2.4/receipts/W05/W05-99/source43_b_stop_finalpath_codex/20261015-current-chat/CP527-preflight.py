import hashlib
import json
import pathlib

repo = pathlib.Path(r'D:\作品集\ResearchOS\research-os')
scope_path = repo / 'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp527/source43-B-STOP-finalpath-source-scope.json'
raw = scope_path.read_bytes()
assert len(raw) == 25208
assert hashlib.sha256(raw).hexdigest() == '299359f2caa34c6a883d63738c6580cd7d176f55097a2f8f59508b5728ac5692'
scope = json.loads(raw)
assert len(scope['mechanical_source41_pins']) == 41
assert len(scope['source_allowlist']) == 43
for item in scope['inputs']:
    path = repo / item['path']
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    assert len(data) == item['bytes'] and digest == item['sha256'], str(path)
    print('INPUT_OK', item['path'], len(data), digest)
stop_manifest = json.loads((repo / scope['inputs'][9]['path']).read_text(encoding='utf-8'))
print('STOP_MANIFEST_KEYS', sorted(stop_manifest))
print('STOP_PATCHES', json.dumps(stop_manifest.get('patches'), ensure_ascii=False))
print('SOURCE_SCOPE_OK', len(scope['mechanical_source41_pins']), len(scope['source_allowlist']))
