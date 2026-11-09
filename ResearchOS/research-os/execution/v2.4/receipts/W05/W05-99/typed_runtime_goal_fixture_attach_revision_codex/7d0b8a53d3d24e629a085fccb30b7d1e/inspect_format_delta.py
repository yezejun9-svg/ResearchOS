import sys
sys.dont_write_bytecode=True
from pathlib import Path
import hashlib,json,difflib
Q=Path(__file__).parent
R=Path('D:/作品集/ResearchOS/research-os')
T=R/'.local/worktrees/codex-w0599-typed-q3-83b95f35e9bd4f81ad0c6682895a6ac1/internal/domain'
Q3=R/'execution/v2.4/receipts/W05/W05-99/typed_runtime_goal_fixture_jsonl_digest_revision_codex/794a6ecddad942d69e6f8fb19bcc2e49/candidate-root/internal/domain'
names=['runtime_permission_windows_test.go','runtime_tool_integration_windows_test.go','runtime_session_events_windows_test.go','client_protocol_goal_test.go']
def pin(p):
 raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
rows=[]
for name in names:
 base=(Q3/name).read_text(encoding='utf-8');current=(T/name).read_text(encoding='utf-8')
 diff=''.join(difflib.unified_diff(base.splitlines(keepends=True),current.splitlines(keepends=True),fromfile=str(Q3/name),tofile=str(T/name)))
 rows.append({'name':name,'base_ref':pin(Q3/name),'actual_T6_ref':pin(T/name),'byte_equal':(Q3/name).read_bytes()==(T/name).read_bytes(),'diff':diff})
 print(name,'byte_equal=',rows[-1]['byte_equal'])
 print(diff)
with (Q/'actual-format-delta.json').open('x',encoding='utf-8') as f:f.write(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
