from pathlib import Path
import hashlib,json
BASE=Path(__file__).resolve().parent
ROOT=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-public-health-20261104')
scope=json.loads(Path('D:/作品集/ResearchOS/research-os/execution/product-v1/receipts/single-harness-20261104/public-health/scope.json').read_text(encoding='utf-8'))
rel='apps/desktop/main/lib/ipc.js'; target=ROOT/rel
before=target.read_bytes()
assert hashlib.sha256(before).hexdigest()==scope['baseline_sha256'][rel]
assert not (ROOT/'tests/ui/desktop/public-health-bridge.test.mjs').exists()
old='''  const principal = host.principalFor(deps.fsImpl, deps.principalFile);
  if (!principal.ok) return { ok: false, reason: principal.reason, detail: principal.detail || null };
  const req = host.requestFor(client, method, body, principal.principal_id);
  if (!req.ok) return { ok: false, reason: req.reason, client, method };'''
new='''  let req;
  if (client === 'status' && method === 'health') {
    // /healthz is a public, empty observation. Fresh Native profiles need no
    // legacy principal file; caller fields cannot select a request or identity.
    const emptyBody = body == null || (typeof body === 'object' &&
      (Object.getPrototypeOf(body) === Object.prototype || Object.getPrototypeOf(body) === null) &&
      Reflect.ownKeys(body).length === 0);
    if (!emptyBody) return { ok: false, reason: 'EMPTY_HEALTH_REQUEST_REQUIRED', client, method };
    req = { verb: 'GET', path: '/healthz', payload: {}, headers: {} };
  } else {
    const principal = host.principalFor(deps.fsImpl, deps.principalFile);
    if (!principal.ok) return { ok: false, reason: principal.reason, detail: principal.detail || null };
    req = host.requestFor(client, method, body, principal.principal_id);
    if (!req.ok) return { ok: false, reason: req.reason, client, method };
  }'''
assert before.count(old.encode('utf-8'))==1
after=before.replace(old.encode('utf-8'),new.encode('utf-8'),1)
directory=BASE/'source-write-01';directory.mkdir(exist_ok=False)
(directory/'ipc.before.js').write_bytes(before)
(directory/'ipc.after.js').write_bytes(after)
test_source=BASE/'public-health-bridge.test.mjs'
assert test_source.exists()
target.write_bytes(after)
(ROOT/'tests/ui/desktop/public-health-bridge.test.mjs').write_bytes(test_source.read_bytes())
print(json.dumps({'status':'EXACT2_SOURCE_WRITTEN','source_sha256':{rel:hashlib.sha256(after).hexdigest(),'tests/ui/desktop/public-health-bridge.test.mjs':hashlib.sha256(test_source.read_bytes()).hexdigest()}}))
