from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent
RECEIPT=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/continue-cp597-20261104/core')
ROOT=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/w14-native-create-core-20261104')
s=json.loads((RECEIPT/'scope.json').read_text(encoding='utf-8-sig'))
for n,h in s['baseline_sha256'].items():
    p=ROOT/n
    assert (not p.exists()) if h=='ABSENT_BEFORE' else hashlib.sha256(p.read_bytes()).hexdigest()==h,n
raw=(HERE/'INTERFACE.v1.json').read_bytes();json.loads(raw)
with (RECEIPT/'author/INTERFACE.v1.json').open('xb') as f:f.write(raw)
print(json.dumps({'status':'BASELINE22_VERIFIED_INTERFACE_SAVED','sha256':hashlib.sha256(raw).hexdigest()}))
