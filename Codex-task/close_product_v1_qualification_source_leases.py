import hashlib, json, os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('D:/作品集/ResearchOS/research-os')
TARGETS = {
    'PRODUCT_V1_QUALIFICATION_BUILD_BINDING': 'qualification-build-binding',
    'PRODUCT_V1_NATIVE_PRELAUNCH_INTENT': 'native-prelaunch-intent',
}
OUT = ROOT/'execution/product-v1/receipts/single-harness-20261104/source-lease-close-cp681'
path = ROOT/'execution/product-v1/leases.json'
raw = path.read_bytes()
leases = json.loads(raw)
state = json.loads((ROOT/'execution/product-v1/state.json').read_bytes())
cp = json.loads((ROOT/'execution/v2.4/checkpoint.json').read_bytes())
assert cp['revision'] == 681 and cp['current_Main_HEAD'] == '998fc6330ba735056cd31f8ebf68dd50a8251c1b'
assert leases['revision'] == 27 and not OUT.exists()
now = datetime.now(timezone.utc).isoformat()
evidence = {}
for scope_id, kind in TARGETS.items():
    active = [s for s in state['active_scopes'] if s['scope_id'] == scope_id]
    owners = [s for s in leases['source_owners'] if s['scope_id'] == scope_id]
    assert len(active) == len(owners) == 1
    assert active[0]['status'] == 'SOURCE_INTEGRATED_NOT_LIVE_QUALIFIED'
    assert owners[0]['status'] == 'IMPLEMENTING'
    result_path = ROOT/'execution/product-v1/receipts/single-harness-20261104'/kind/'integration/integration.json'
    result = json.loads(result_path.read_bytes())
    assert result['status'] == 'INDEPENDENTLY_REVIEWED_SOURCE_INTEGRATED_NOT_LIVE_QUALIFIED'
    assert result['formal_increment'] == result['product_journey_increment'] == 0
    for ref, digest in result['source_sha256'].items():
        assert hashlib.sha256((ROOT/ref).read_bytes()).hexdigest() == digest
    evidence[scope_id] = dict(path=str(result_path.relative_to(ROOT)), sha256=hashlib.sha256(result_path.read_bytes()).hexdigest())
    owners[0]['status'] = active[0]['status']
    owners[0]['closed_at'] = now
    owners[0]['source_integration_ref'] = evidence[scope_id]
leases.update(revision=28, at=now)
OUT.mkdir()
(OUT/'leases.before.json').write_bytes(raw)
new = (json.dumps(leases, ensure_ascii=False, indent=2)+'\n').encode('utf8')
temp = path.with_name(path.name+'.cp681-close.new')
assert not temp.exists() and path.read_bytes() == raw
with temp.open('xb') as f:
    assert f.write(new) == len(new)
    f.flush()
    os.fsync(f.fileno())
os.replace(temp, path)
assert path.read_bytes() == new
receipt = dict(status='SOURCE_LEASES_CLOSED_AFTER_INTEGRATION', checkpoint=681, at=now, evidence=evidence, prior_leases_sha256=hashlib.sha256(raw).hexdigest(), leases_sha256=hashlib.sha256(new).hexdigest(), source_native_model_execution=False, formal_increment=0)
(OUT/'RESULT.json').write_bytes((json.dumps(receipt, ensure_ascii=False, indent=2)+'\n').encode('utf8'))
print(json.dumps(dict(checkpoint=681, leases_revision=28, active_product_source_owners=0, old_leases_preserved=True)))
