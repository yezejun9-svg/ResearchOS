"""Copy only Root-authorized Go canonical source to C; never write D:."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = Path('D:/作品集/ResearchOS/research-os')
source = MAIN / 'internal/canonical/jcs.go'
expected = '7aad384f03ced5d4033145d5bf2953909be72c658642bbfc1b7795fd037f4d8d'
raw = source.read_bytes()
actual = hashlib.sha256(raw).hexdigest()
if actual != expected:
    raise SystemExit('canonical source drift')
target = ROOT / 'canonical/jcs.go'
target.parent.mkdir(parents=True, exist_ok=True)
with target.open('xb') as stream:
    stream.write(raw)
contracts = MAIN / 'internal/domain/contracts.go'
contract_bytes = contracts.read_bytes()
proof = {'copied_source': str(source), 'source_sha256': actual, 'copy': 'canonical/jcs.go',
         'copy_sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
         'hash_chain_source': str(contracts), 'hash_chain_source_sha256': hashlib.sha256(contract_bytes).hexdigest(),
         'hash_chain_excerpt': [{'line': i, 'text': line} for i, line in enumerate(contract_bytes.decode('utf-8').splitlines(), 1) if 90 <= i <= 106],
         'claim': 'Byte-identical canonical source copied to C; Go Hash-chain interoperability is limited to the actual helper/vector/DTO tests.',
         'D_writes': 0}
with (ROOT / 'canonical-provenance.json').open('x', encoding='utf-8') as stream:
    json.dump(proof, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps({'canonical_source_sha256': actual, 'copied_bytes': len(raw)}))
