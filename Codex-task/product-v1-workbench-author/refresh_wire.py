from pathlib import Path
import json
import hashlib
root = Path(__file__).resolve().parent
raw = (root / 'contract-r2.interface.json').read_bytes()
assert hashlib.sha256(raw).hexdigest() == '046a49b2b1f82593fe86924913b2ee4d77152ac1cef7dbbb86562f6dfe0cfa1c'
template = (root / 'harness-wire.template.js').read_text(encoding='utf-8')
output = template.replace('__DEFINITIONS__', json.dumps(json.loads(raw)['$defs'], ensure_ascii=False, separators=(',', ':')))
(root / 'candidate/apps/desktop/main/lib/harness-wire.js').write_text(output, encoding='utf-8', newline='\n')
print('WIRE_REFRESHED_FROM_PINNED_CONTRACT')
