from pathlib import Path
import json,hashlib,subprocess,re
M=Path('D:/作品集/ResearchOS/research-os');S=Path('D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4');N=Path(__file__).resolve().parent
repo=['AGENTS.md','execution/project_identity.json','apps/desktop/main/main.js','apps/desktop/main/lib/native.js','apps/desktop/main/lib/v2.js','apps/desktop/main/lib/ipc.js','apps/desktop/main/lib/host.js','apps/desktop/main/lib/first-use.js','apps/desktop/main/lib/context.js','apps/desktop/main/lib/app-protocol.js','apps/desktop/main/workbench.html','apps/desktop/preload/preload.js','apps/desktop/package.json','apps/desktop/package-lock.json','apps/desktop/tests/w14-native.js','apps/desktop/tests/w14-review.js','apps/web/src/v2client.js','apps/web/src/workbench.jsx','apps/web/src/continuity.jsx','apps/web/src/main.jsx','apps/web/src/screens.jsx','apps/web/src/api.js','apps/web/package.json','apps/web/package-lock.json','internal/api/contracts/client.protocol.schema.json','internal/api/contracts/domain.schema.json','internal/host/native.go','internal/host/native_pipe_windows.go','internal/api/v2.go','tests/ui/check/main.py','tests/ui/continuity/check/main.py','tests/ui/continuity/surfaces_driver.js','tests/ui/continuity/producer_probe.py','tests/ui/desktop/w13-react.test.js','tests/ui/w1303/check.py','tests/ui/w1303/run.py','tests/ui/w1303/screen_reader_run.py','tests/contracts/fixtures/client_protocol_v2_fixtures.json','tests/contracts/fixtures/client.protocol.schema.json','tests/contracts/fixtures/domain.schema.json','execution/toolchains/locked.json']
spec=['08_AGENT_EXECUTION_GOAL.md','05_WBS.md','06_ACCEPTANCE_TESTS.md','10_UI_UX_DESIGN.md','17_USER_JOURNEYS_AND_VALUE.md','19_DESKTOP_IMPLEMENTATION_BLUEPRINT.md','22_CLIENT_INTERFACE_DETAILS.md','contracts/tasks.json','contracts/acceptance.json','contracts/harness.contract.json','contracts/ui.contract.json','contracts/client.protocol.schema.json','contracts/domain.schema.json','tasks/steps/W13-01.md','tasks/steps/W13-02.md','tasks/steps/W13-03.md','tasks/steps/W13-99.md']
def sha(b):return hashlib.sha256(b).hexdigest()
rows=[]
for root,group,paths in [(M,'repo',repo),(S,'frozen',spec)]:
 for rel in paths:
  p=root/rel
  if not p.is_file():
   rows.append({'path':str(p),'relative':rel,'group':group,'exists':False});continue
  raw=p.read_bytes();raw.decode('utf-8-sig');dest=N/'snapshot'/group/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
  rows.append({'path':str(p),'relative':rel,'group':group,'exists':True,'sha256':sha(raw),'bytes':len(raw),'copy':str(dest.relative_to(M))})
(N/'inputs.before.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
(N/'git-head.txt').write_bytes(subprocess.check_output(['git','rev-parse','HEAD'],cwd=M))
(N/'git-status.before.txt').write_bytes(subprocess.check_output(['git','status','--short','--untracked-files=no'],cwd=M))
doc=json.loads((M/'internal/api/contracts/client.protocol.schema.json').read_text(encoding='utf-8'))
names=['CommandResponse','PendingResult','SessionSnapshot','AttachResult','NativeUserBootstrapResult','NativeWorkspaceChooseResult','NativeCredentialImportResult']
selected={k:doc['$defs'][k] for k in names}
(N/'schema-selected.json').write_text(json.dumps(selected,ensure_ascii=False,indent=2),encoding='utf-8')
keywords=set();formats=set();refs=set()
def visit(x):
 if not isinstance(x,dict):return
 keywords.update(x)
 if 'format' in x:formats.add(x['format'])
 if '$ref' in x:refs.add(x['$ref'])
 for k in ['properties','$defs','patternProperties','dependentSchemas']:
  for v in x.get(k,{}).values():visit(v)
 for k in ['items','additionalProperties','unevaluatedProperties','contains','not','if','then','else','propertyNames']:visit(x.get(k))
 for k in ['oneOf','allOf','anyOf','prefixItems']:
  for v in x.get(k,[]):visit(v)
visit(doc);visit(json.loads((M/'internal/api/contracts/domain.schema.json').read_text(encoding='utf-8')))
(N/'schema-keywords.json').write_text(json.dumps({'keywords':sorted(keywords),'formats':sorted(formats),'external_refs':[x for x in sorted(refs) if not x.startswith('#')]},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'inputs':len(rows),'missing':[x['path'] for x in rows if not x['exists']],'keywords':sorted(keywords),'formats':sorted(formats)},ensure_ascii=False))
