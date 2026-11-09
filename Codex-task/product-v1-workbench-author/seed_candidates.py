from pathlib import Path
import shutil
import json
import hashlib

root = Path(__file__).resolve().parent
for path in (root / 'baseline').rglob('*'):
    if path.is_file():
        target = root / 'candidate' / path.relative_to(root / 'baseline')
        if target.exists():
            raise SystemExit('CANDIDATE_ALREADY_EXISTS: ' + str(target))
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
contract_path = root.parent / 'product-v1-host-interface.json'
contract_bytes = contract_path.read_bytes()
assert hashlib.sha256(contract_bytes).hexdigest() == '90d235a5ea83ecd282ae0490708e81d76a244947b90d4841b6a9da50bbc2cc66'
contract = json.loads(contract_bytes)
template = (root / 'harness-wire.template.js').read_text(encoding='utf-8')
target = root / 'candidate/apps/desktop/main/lib/harness-wire.js'
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(template.replace('__DEFINITIONS__', json.dumps(contract['$defs'], ensure_ascii=False, separators=(',', ':'))), encoding='utf-8', newline='\n')
print('CANDIDATES_SEEDED_CONTRACT_PINNED')
