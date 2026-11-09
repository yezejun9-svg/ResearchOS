import pathlib,json,hashlib
B=pathlib.Path(__file__).parent; R=pathlib.Path(r'D:/作品集/ResearchOS/research-os')
P=R/'execution/v2.4/receipts/W05/W05-99/qualification_maintenance_c57_codex/20261025-current-chat'
W=R/'.local/worktrees/qualification-maintenance-c57-20261025'
D=B/'C51-r3-r4-static-snapshot';D.mkdir(exist_ok=False)
sha=lambda d:hashlib.sha256(d).hexdigest()
expect={'C51-R3-SOURCEFREEZE.json':'73dd30e430f8c2114b05327df1f4ae28105468f3465c4bbf499c367207b32f5b','C51-R3-INCREMENT.json':'d369d5f1fa7e1bced52f0a67b9ac3178a053a406e54c874748c2ba99704b5ca4','C51-R3-DELTA.patch':'91a739fec5da60714640ac8167d288a5d21a47d252c17ab5925aeaed7556eab5','C51-R4-SOURCEFREEZE.json':'fdb59f3f6385b77b97c58d9fe55d0abb5ed0b2115ffdfedd21f523a6176bdba2','C51-R4-INCREMENT.json':'695d80430c5b0bcf15c62525b166709518206b60ef0120361b95a29226ab15c0','C51-R4-DELTA.patch':'46ea18918f91d11eb7c9ea041c5e1a7ef4bc2b26f7de6c8ccf75fa6d67b624f7'}
for name,h in expect.items():
 data=(P/name).read_bytes();assert sha(data)==h,name;(D/name).write_bytes(data)
m2=json.loads((B/'C51-r2-static-snapshot/C51-R2-SOURCEFREEZE.json').read_text())
m3=json.loads((D/'C51-R3-SOURCEFREEZE.json').read_text());m4=json.loads((D/'C51-R4-SOURCEFREEZE.json').read_text())
maps=[{i['path']:i for i in m['owned_files']} for m in [m2,m3,m4]]
assert all(len(m)==51 for m in maps)
diffs=[]
for idx in [1,2]:
 diff=[n for n,i in maps[idx].items() if i['sha256']!=maps[idx-1][n]['sha256']]
 assert len(diff)==(3 if idx==1 else 1),diff
 diffs.extend(diff)
for path in diffs:
 data=(W/path).read_bytes();i=maps[2][path]
 assert sha(data)==i['sha256'] and len(data)==i['bytes'],path
 out=D/path;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(data)
assert all(sha((W/i['path']).read_bytes())==i['sha256'] for i in maps[2].values())
T=D/'author-receipts';T.mkdir(exist_ok=False)
for rev in [3,4]:
 inc=json.loads((D/f'C51-R{rev}-INCREMENT.json').read_text())
 for ref in inc['test_receipts']:
  data=(P/ref['path']).read_bytes();assert sha(data)==ref['sha256'],ref['path']
  (T/ref['path']).write_bytes(data)
 print('R'+str(rev)+' DELTA')
 print((D/f'C51-R{rev}-DELTA.patch').read_text())
print('COPIED',json.dumps(diffs))
for name in ['061-r3-journal','combined-065-domain','070-domain-lease-isolate','071-domain-lease-isolate','073-domain-lease-d-env','074-domain-combined-r4']:
 print('AUTHOR',name,'EXIT', (T/(name+'.native-exit.txt')).read_text(encoding='utf-8-sig').strip())
 print((T/(name+'.recipe.txt')).read_text(encoding='utf-8-sig'))
 for line in (T/(name+'.stdout.raw')).read_text(encoding='utf-8-sig').splitlines():
  if any(k in line for k in ['--- FAIL','FAIL','--- PASS','=== RUN','UPGRADE_SOURCE','ok ']): print(line)
out={'phase':'PHASE1_R3_R4_TARGETED_STATIC_ONLY','control_hashes':expect,'changed_paths':diffs,'all51_live_match_r4':True,'author_receipts':len(list(T.iterdir()))}
with (B/'C51-r3-r4-static-snapshot-verification.json').open('x',encoding='utf-8') as f:json.dump(out,f,indent=2)
