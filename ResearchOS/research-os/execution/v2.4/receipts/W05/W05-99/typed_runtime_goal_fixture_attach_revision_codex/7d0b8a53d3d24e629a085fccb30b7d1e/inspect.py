import sys
sys.dont_write_bytecode = True
from pathlib import Path
import hashlib, json

Q = Path(__file__).parent
R = Path('D:/作品集/ResearchOS/research-os')
A = R / 'execution/v2.4/receipts/W05/W05-99/integration_codex/typed-q3-epoch-targeted-root-0c4318e1c10443f2'
E = R / '.local/typed-q3-epoch-run-env-3c6a88ed57744a0a/typed-child-evidence'
def read(p):
    raw = p.read_bytes()
    return raw, {'path':str(p), 'sha256':hashlib.sha256(raw).hexdigest(), 'bytes':len(raw)}
pins = []
actual = {}
for name in ['source.integration.choice.json', 'format.invocation.json', 'tagged-test-binary-compile.invocation.json', 'typed-q3-epoch-parent-jsonl.invocation.json', 'actual-tagged-compiler-input-inventory.json']:
    raw, pin = read(A / name)
    pins.append(pin)
    data = json.loads(raw.decode('utf-8'))
    actual[name] = {'keys':list(data) if isinstance(data,dict) else 'array'}
    if name != 'actual-tagged-compiler-input-inventory.json':
        actual[name]['data'] = data
parents = []
for d in sorted(p for p in E.iterdir() if p.is_dir()):
    row = {'parent':d.name}
    for name in ['child-result.json', 'child-event-verdict.json', 'parent-result.json', 'child-invocation.json']:
        raw, pin = read(d / name)
        pins.append(pin)
        row[name] = json.loads(raw.decode('utf-8'))
    raw, pin = read(d / 'child.stdout.jsonl')
    pins.append(pin)
    rows = []
    for ln, text in enumerate(raw.decode('utf-8').splitlines(),1):
        event = json.loads(text)
        if event.get('Action') in ['run','fail','skip','pass'] or any(s in event.get('Output','') for s in ['typed command','Error','FAIL']):
            rows.append({'line':ln, 'event':event})
    row['events'] = rows
    parents.append(row)
out = {'authority':'NONE', 'scope':'read-only Root actual diagnostic', 'actual':actual, 'parents':parents, 'input_pins':pins}
(Q / 'actual-inspection.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for name,data in actual.items():
    print(name, json.dumps(data,ensure_ascii=False))
for p in parents:
    print('PARENT',p['parent'])
    print('RESULT',json.dumps(p['child-result.json'],ensure_ascii=False))
    print('VERDICT',json.dumps(p['child-event-verdict.json'],ensure_ascii=False))
    for event in p['events']:
        print(json.dumps(event,ensure_ascii=False))
print('inspection',json.dumps(read(Q / 'actual-inspection.json')[1],ensure_ascii=False))
