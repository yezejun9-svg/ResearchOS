from pathlib import Path
import hashlib, json
OUT = Path(__file__).parent
BASE = Path('D:/作品集/ResearchOS/research-os')
C = Path('C:/Users/yqyyds/Documents/Codex/2026-11-04/task/cp598-w14-clients-author/freeze-01')
assert hashlib.sha256((C/'MANIFEST.json').read_bytes()).hexdigest() == '4b0adde5874c424eb43b1414cdfe36d6d919888f4c3fa69ecd41e4704e8a1c02'
m = json.loads((C/'MANIFEST.json').read_bytes())
pins = {p['path']: p['sha256'] for p in m['source_pins']}
rows = []
for rel in ('apps/desktop/main/lib/native.js', 'apps/desktop/main/lib/http-wire.js', 'apps/desktop/main/lib/ipc.js', 'tests/ui/native-create-attestation-fixture.cjs'):
    data = (C/'source-snapshot'/rel).read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    assert digest == pins[rel]
    dest = OUT/'isolated-frozen-node'/rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    rows.append(dict(source=str(C/'source-snapshot'/rel), target=str(dest), sha256=digest, origin='frozen-candidate'))
for rel in ('apps/desktop/main/lib/host.js', 'apps/desktop/main/lib/v2.js', 'apps/desktop/main/lib/wire-values.mjs'):
    data = (BASE/rel).read_bytes()
    dest = OUT/'isolated-frozen-node'/rel
    dest.write_bytes(data)
    rows.append(dict(source=str(BASE/rel), target=str(dest), sha256=hashlib.sha256(data).hexdigest(), origin='unchanged-Main-dependency'))
data = (BASE/'apps/desktop/main/lib/http-wire.js').read_bytes()
assert hashlib.sha256(data).hexdigest() == '216ff4f4c46b112d83984d4aae3895ce00d9a4ff1d9a92685f9d54b4dcde0d38'
(OUT/'baseline-http-wire.js').write_bytes(data)
(OUT/'frozen-node-staging.json').write_text(json.dumps(dict(status='STAGED_FROM_FROZEN_COPY_NO_LIVE_CANDIDATE_READ',rows=rows), ensure_ascii=False, indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(status='STAGED',files=len(rows),live_candidate_reads=0)))
