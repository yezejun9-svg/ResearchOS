import json
from pathlib import Path
root = Path('D:/作品集/ResearchOS/research-os')
out = root/'execution/v2.4/receipts/W05/W05-99/continue-cp579-20261104'
cp = json.loads((root/'execution/v2.4/checkpoint.json').read_bytes())
registry = json.loads((root/'execution/v2.4/commands.json').read_bytes())
print(json.dumps({'checkpoint_keys':list(cp), 'revision':cp['revision'], 'failures':len(cp['failure_counters']), 'last_failure':cp['failure_counters'][-1], 'registry_keys':list(registry), 'registry_revision':registry.get('revision')}))
rows=registry.get('commands')
print(json.dumps({'commands_type':type(rows).__name__}))
if isinstance(rows,dict): print(json.dumps(rows.get('test.runtime')))
elif isinstance(rows,list): print(json.dumps([r for r in rows if r.get('key')=='test.runtime']))
print(json.dumps({'receipt_files':[str(p.relative_to(out)) for p in out.rglob('*') if p.is_file() and len(p.relative_to(out).parts)<3]}))
