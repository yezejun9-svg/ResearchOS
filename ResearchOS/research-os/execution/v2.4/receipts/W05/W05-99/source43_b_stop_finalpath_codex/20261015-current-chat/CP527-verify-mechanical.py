import hashlib
import json
import pathlib

repo = pathlib.Path(r'D:\作品集\ResearchOS\research-os')
wt = pathlib.Path(r'D:\作品集\ResearchOS\research-os\.local\worktrees\source43-b-stop-finalpath-20261015')
here = pathlib.Path(__file__).resolve().parent
scope = json.loads((repo / 'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp527/source43-B-STOP-finalpath-source-scope.json').read_bytes())
pins = scope['mechanical_source41_pins']
actual = {}
for name, spec in pins.items():
    data = (wt / name).read_bytes()
    item = {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data), 'source_commit': spec['source_commit'], 'lane': spec['lane']}
    if item['sha256'] != spec['sha256'] or item['bytes'] != spec['bytes']:
        raise AssertionError(name)
    actual[name] = item
roots = wt / 'internal/host/roots_windows.go'
roots_data = roots.read_bytes()
baseline = {'schema': 'researchos.source43-mechanical41-baseline.v1', 'source_base_commit': scope['base_commit'], 'source_base_tree': scope['base_tree'], 'STOP_commit': scope['STOP_commit'], 'STOP_patch_sha256': '329d49149a013d34b431054ab48fdd6e89ca22d1c532a65570432acf7c507a80', 'mechanical41': actual, 'roots_before': {'path': 'internal/host/roots_windows.go', 'sha256': hashlib.sha256(roots_data).hexdigest(), 'bytes': len(roots_data)}}
(here / 'mechanical41-baseline.json').write_text(json.dumps(baseline, ensure_ascii=False, indent=2), encoding='utf-8')
print('MECHANICAL_41_MATCH_SCOPE', len(actual))
print('ROOTS_BEFORE', baseline['roots_before'])
