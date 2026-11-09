from pathlib import Path
import hashlib
import json

root = Path(__file__).resolve().parent
repo = Path('D:/作品集/ResearchOS/research-os')
wt = repo / '.local/worktrees/product-v1-workbench-20261104'
scope = json.loads((repo / 'execution/product-v1/receipts/single-harness-20261104/workbench/scope.json').read_text(encoding='utf-8-sig'))
history = root / 'history/pre-interface-revision-02'
history.mkdir(parents=True, exist_ok=False)
pins = {}
for name in scope['production_paths'] + scope['test_paths']:
    raw = (wt / name).read_bytes()
    target = history / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    pins[name] = hashlib.sha256(raw).hexdigest()
(history / 'source-pins.json').write_text(json.dumps(pins, indent=2) + '\n', encoding='utf-8')
old = (root.parent / 'product-v1-host-interface.json').read_bytes()
assert hashlib.sha256(old).hexdigest() == '90d235a5ea83ecd282ae0490708e81d76a244947b90d4841b6a9da50bbc2cc66'
(root / 'contract-r1.interface.json').write_bytes(old)
new = (repo / 'execution/product-v1/contracts/harness.v1.interface.rev2.json').read_bytes()
assert hashlib.sha256(new).hexdigest() == '046a49b2b1f82593fe86924913b2ee4d77152ac1cef7dbbb86562f6dfe0cfa1c'
(root / 'contract-r2.interface.json').write_bytes(new)
before, after = json.loads(old), json.loads(new)
assert before['routes'] == after['routes']
assert len(after['$defs']) == 22
for field in ['hooks', 'mcp']:
    assert after['$defs']['Capabilities']['properties']['security_scope']['properties'][field]['const'] == 'PLATFORM_POLICY'
for name in ['harness-wire.template.js', 'refresh_wire.py']:
    target = root / name
    text = target.read_text(encoding='utf-8').replace('90d235a5ea83ecd282ae0490708e81d76a244947b90d4841b6a9da50bbc2cc66', '046a49b2b1f82593fe86924913b2ee4d77152ac1cef7dbbb86562f6dfe0cfa1c')
    text = text.replace('revision1,', 'revision2,').replace("root.parent / 'product-v1-host-interface.json'", "root / 'contract-r2.interface.json'")
    target.write_text(text, encoding='utf-8', newline='\n')
fixture = root / 'candidate/tests/ui/harness-bridge-fixture.cjs'
text = fixture.read_text(encoding='utf-8').replace('90d235a5ea83ecd282ae0490708e81d76a244947b90d4841b6a9da50bbc2cc66', '046a49b2b1f82593fe86924913b2ee4d77152ac1cef7dbbb86562f6dfe0cfa1c').replace("hooks: 'DISABLED', mcp: 'DISABLED'", "hooks: 'PLATFORM_POLICY', mcp: 'PLATFORM_POLICY'")
fixture.write_text(text, encoding='utf-8', newline='\n')
ui = root / 'candidate/apps/web/src/workbench.jsx'
raw = ui.read_bytes()
old_text = "工作区只读是请求策略；Windows 执行隔离{capabilities.security_scope.enforcement_verified ? '已由 Host 标记验证' : '尚未验证'}。".encode('utf-8')
new_text = "平台策略管理；只读边界{capabilities.security_scope.enforcement_verified ? '已由 Host 标记验证' : '未验证'}。登录与执行验证分别记录。".encode('utf-8')
assert raw.count(old_text) == 1
ui.write_bytes(raw.replace(old_text, new_text))
print('REV2_ADOPTED_OLD_SOURCE_AND_CONTRACT_PRESERVED')
