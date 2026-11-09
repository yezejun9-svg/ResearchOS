from pathlib import Path
import hashlib, json, difflib

OUT = Path(__file__).parent
BASE = Path('D:/作品集/ResearchOS/research-os')
LIVE = BASE / '.local/worktrees/w14-native-create-clients-20261104'
C = Path('C:/Users/yqyyds/Documents/Codex/2026-11-04/task/cp598-w14-clients-author/freeze-01')
D = BASE / 'execution/v2.4/receipts/W05/W05-99/continue-cp597-20261104/clients/author/freeze-01'
MANIFEST = '4b0adde5874c424eb43b1414cdfe36d6d919888f4c3fa69ecd41e4704e8a1c02'
rows = []
def pin(path, expected):
    data = path.read_bytes()
    actual = hashlib.sha256(data).hexdigest()
    rows.append(dict(path=str(path), bytes=len(data), expected=expected, actual=actual, match=actual == expected))
    assert actual == expected, str(path)
    return data
m = json.loads(pin(C/'MANIFEST.json', MANIFEST))
pin(D/'MANIFEST.json', MANIFEST)
for item in m['raw_and_support_files']:
    for base in (C, D):
        pin(base/item['path'], item['sha256'])
for item in m['source_pins']:
    pin(LIVE/item['path'], item['sha256'])
pin(BASE/'execution/v2.4/receipts/W05/W05-99/continue-cp597-20261104/core/author/INTERFACE.v1.json',
    '0a544c964ddd0dd1d4a29e3af75725a0acb1a2e71560c08543a624dd21a87393')
diff = []
for item in m['source_pins']:
    p = item['path']
    old = [] if item['baseline_sha256'] == 'ABSENT_BEFORE' else pin(BASE/p, item['baseline_sha256']).decode('utf-8').splitlines(keepends=True)
    new = (C/'source-snapshot'/p).read_text(encoding='utf-8').splitlines(keepends=True)
    diff.extend(difflib.unified_diff(old, new, fromfile='Main/'+p, tofile='frozen/'+p))
(OUT/'production-and-test.diff').write_text(''.join(diff), encoding='utf-8', newline='')
(OUT/'pin-verification.json').write_text(json.dumps(dict(status='ALL_MATCH', checks=len(rows), rows=rows), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
original = (C/'source-snapshot/apps/cli/cli_native_attestation_test.go').read_bytes()
extra = (OUT/'independent-go-extra.txt').read_bytes()
(OUT/'combined_native_attestation_test.go').write_bytes(original + b'\n' + extra)
overlay = {'Replace': {str(LIVE/'apps/cli/cli_native_attestation_test.go'): str(OUT/'combined_native_attestation_test.go')}}
(OUT/'go-overlay.json').write_text(json.dumps(overlay), encoding='utf-8')
print(json.dumps(dict(status='ALL_MATCH', checks=len(rows), source_paths=9, c_support=29, d_support=29, manifest=MANIFEST)))
