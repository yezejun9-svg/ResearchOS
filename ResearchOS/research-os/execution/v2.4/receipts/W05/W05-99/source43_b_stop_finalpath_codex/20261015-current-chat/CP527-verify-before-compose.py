import hashlib
import json
import pathlib
import shutil

repo = pathlib.Path(r'D:\作品集\ResearchOS\research-os')
wt = pathlib.Path(r'D:\作品集\ResearchOS\research-os\.local\worktrees\source43-b-stop-finalpath-20261015')
scope_path = repo / 'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp527/source43-B-STOP-finalpath-source-scope.json'
scope = json.loads(scope_path.read_bytes())
pin = scope['mechanical_source41_pins']
b = [name for name, spec in pin.items() if spec['source_commit'] == scope['base_commit']]
stop = [name for name, spec in pin.items() if spec['source_commit'] == scope['STOP_commit']]
assert len(b) == 22 and len(stop) == 19
assert sorted(b + stop) == sorted(scope['mechanical_source_paths'])
for name in b:
    data = (wt / name).read_bytes()
    assert len(data) == pin[name]['bytes'] and hashlib.sha256(data).hexdigest() == pin[name]['sha256'], name
patch = repo / 'execution/v2.4/receipts/W05/W05-99/owned_core_stop_effect_state_revision05_source_codex/20261015-current-chat/candidate-37a1f6d3-final/whole19-Main4f-to-r5.patch'
data = patch.read_bytes()
assert hashlib.sha256(data).hexdigest() == '329d49149a013d34b431054ab48fdd6e89ca22d1c532a65570432acf7c507a80'
print('BASE_B22_PIN_OK', len(b))
print('STOP19_PATCH_SHA256_OK', patch, len(data))
print('DISK_FREE_BYTES', shutil.disk_usage(wt).free)
