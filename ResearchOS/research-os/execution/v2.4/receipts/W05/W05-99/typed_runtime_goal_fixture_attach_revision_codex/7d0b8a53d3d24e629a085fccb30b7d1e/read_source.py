import sys
sys.dont_write_bytecode = True
from pathlib import Path
import hashlib,json
Q=Path(__file__).parent
T=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-typed-q3-83b95f35e9bd4f81ad0c6682895a6ac1')
Q3=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/typed_runtime_goal_fixture_jsonl_digest_revision_codex/794a6ecddad942d69e6f8fb19bcc2e49')
spec=Path('D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4/contracts/client.protocol.schema.json')
requests=[
 (T/'internal/domain/client_protocol.go',[(680,725),(774,900),(1030,1080),(1095,1195)]),
 (T/'internal/domain/client_protocol_events.go',[(1,240)]),
 (T/'internal/domain/runtime_tool_integration_windows_test.go',[(25,60),(85,165)]),
 (T/'internal/domain/runtime_permission_windows_test.go',[(155,220)]),
 (T/'internal/domain/runtime_session_events_windows_test.go',[(450,505)]),
 (Q3/'candidate-root/internal/domain/runtime_typed_client_fixture_windows_test.go',[(560,585)]),
 (spec,[(1080,1155),(1655,1720),(4770,4810),(4920,4955)]),
]
pins=[]
allrows=[]
for p,ranges in requests:
 raw=p.read_bytes(); lines=raw.decode('utf-8').splitlines(); pin={'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}; pins.append(pin)
 print('SOURCE',json.dumps(pin,ensure_ascii=False))
 rows=[]
 for a,b in ranges:
  for n in range(a,min(b,len(lines))+1):
   row=str(n)+': '+lines[n-1]; rows.append(row); print(row)
 allrows.append({'pin':pin,'excerpts':rows})
(Q/'source-inspection.json').write_text(json.dumps(allrows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(Q/'source-pins.initial.json').write_text(json.dumps(pins,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
