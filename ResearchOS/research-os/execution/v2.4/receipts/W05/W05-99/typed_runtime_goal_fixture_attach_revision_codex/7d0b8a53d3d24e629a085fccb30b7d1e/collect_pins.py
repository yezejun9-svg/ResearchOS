import sys
sys.dont_write_bytecode=True
from pathlib import Path
import hashlib,json
Q=Path(__file__).parent
R=Path('D:/作品集/ResearchOS/research-os')
T=R/'.local/worktrees/codex-w0599-typed-q3-83b95f35e9bd4f81ad0c6682895a6ac1'
Q3=R/'execution/v2.4/receipts/W05/W05-99/typed_runtime_goal_fixture_jsonl_digest_revision_codex/794a6ecddad942d69e6f8fb19bcc2e49'
A=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/typed-q3-epoch-targeted-root-0c4318e1c10443f2'
files=[T/'internal/domain/client_protocol.go',T/'internal/domain/client_protocol_journal.go',T/'internal/domain/client_protocol_sessions.go',T/'internal/domain/v24_sessions.go',T/'internal/domain/client_protocol_events.go',T/'internal/domain/client_session_fence.go',Path('D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4/22_CLIENT_INTERFACE_DETAILS.md'),Path('D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4/contracts/client.protocol.schema.json')]
names=['client_protocol_goal_test.go','runtime_permission_windows_test.go','runtime_tool_integration_windows_test.go','runtime_session_events_windows_test.go','runtime_typed_client_fixture_windows_test.go']
files += [Q3/'candidate-root/internal/domain'/n for n in names]
files += [T/'internal/domain'/n for n in names]
files += [A/'validation.closed.json',A/'actual-tagged-compiler-input-inventory.json']
def pin(p):
 raw=p.read_bytes();raw.decode('utf-8');return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
pins=[pin(p) for p in files]
inventory=json.loads((A/'actual-tagged-compiler-input-inventory.json').read_text(encoding='utf-8'))
print('inventory_shape',json.dumps({k:type(v).__name__ for k,v in inventory.items()},ensure_ascii=False))
def refs(x):
 if isinstance(x,dict):
  if 'path' in x and isinstance(x['path'],str): yield x
  for v in x.values():yield from refs(v)
 elif isinstance(x,list):
  for v in x:yield from refs(v)
selected=[]
for row in refs(inventory):
 if any(str(p).replace('\\','/').lower()==row['path'].replace('\\','/').lower() for p in files):selected.append(row)
out={'authority':'NONE','input_pins':pins,'actual_inventory_selected_refs':selected,'actual_inventory_selected_count':len(selected)}
(Q/'source-pins.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('selected',len(selected))
print('pins',len(pins))
print('source-pins',json.dumps(pin(Q/'source-pins.json'),ensure_ascii=False))
