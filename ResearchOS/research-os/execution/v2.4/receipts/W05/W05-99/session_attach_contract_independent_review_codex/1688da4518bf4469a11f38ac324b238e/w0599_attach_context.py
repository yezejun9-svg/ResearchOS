from pathlib import Path
import sys,json
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99';Q=B/'session_attach_contract_revision_codex/1a11ded594f5378b7512125d';T=R/'.local/worktrees/codex-w0599-typed-q3-83b95f35e9bd4f81ad0c6682895a6ac1'
def show(p,start=1,end=100000):
 print('FILE',str(p))
 for i,l in enumerate(p.read_text(encoding='utf-8').splitlines(),1):
  if start<=i<=end:print(f'{i}: {l}')
if sys.argv[1]=='contract':show(R.parent/'ResearchOS_Implementation_Package_v2.4/22_CLIENT_INTERFACE_DETAILS.md')
elif sys.argv[1]=='production':
 show(Q/'candidate-root/internal/domain/client_protocol.go',390,780)
 show(Q/'candidate-root/internal/domain/client_protocol.go',980,1235)
elif sys.argv[1]=='related':
 for name in ('v24_sessions.go','client_protocol_journal.go','client_session_fence.go'):
  show(T/'internal/domain'/name)
elif sys.argv[1]=='q4':
 p=B/'typed_runtime_goal_fixture_attach_revision_codex/7d0b8a53d3d24e629a085fccb30b7d1e';print('FILES',[x.name for x in p.iterdir() if x.is_file()]);show(p/'HDF.json')
elif sys.argv[1]=='slice':show(Path(sys.argv[2]),int(sys.argv[3]),int(sys.argv[4]))
elif sys.argv[1]=='find':
 for p in (T/'internal/domain').glob('*.go'):
  lines=p.read_text(encoding='utf-8').splitlines()
  hits=[(i,l) for i,l in enumerate(lines,1) if any(term in l for term in sys.argv[2:])]
  if hits:print('FILE',str(p));print('\n'.join(f'{i}: {l}' for i,l in hits))
