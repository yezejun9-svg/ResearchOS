import pathlib,json,hashlib
B=pathlib.Path(__file__).parent
R=pathlib.Path(r'D:\作品集\ResearchOS\research-os')
W=R/'.local/worktrees/qualification-maintenance-c57-20261025'
A=R/'execution/v2.4/receipts/W05/W05-99/qualification_recovery_boundary_boot6_codex/20261025-current-chat'
D=B/'MUTABLE-v7-sddl-snapshot';D.mkdir(exist_ok=False)
paths=[W/'internal/recoveryboundary/boot_windows.go',W/'internal/recoveryboundary/boot_windows_test.go']
paths+=sorted(A.glob('v7-*'))
refs=[]
for p in paths:
 if not p.is_file():continue
 raw=p.read_bytes();out=D/p.name;out.write_bytes(raw)
 refs.append({'original':str(p),'snapshot':str(out.relative_to(B)),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'mutable_input':str(p).startswith(str(W))})
for x in refs:
 p=pathlib.Path(x['original']);x['same_after_capture']=hashlib.sha256(p.read_bytes()).hexdigest()==x['sha256']
 assert x['same_after_capture'],str(p)
(D/'manifest.json').write_text(json.dumps(refs,ensure_ascii=False,indent=2),encoding='utf-8')
for x in refs:print(json.dumps(x,ensure_ascii=False))
for p in sorted(D.glob('*.stdout')):
 print('\n'+p.name+'\n'+p.read_text(encoding='utf-8',errors='replace'))
v=(D/'boot_windows.go').read_text().splitlines()
for lo,hi in [(1058,1118),(1209,1283),(1620,1800)]:
 for i in range(lo-1,min(hi,len(v))):print(f'{i+1}: {v[i]}')

