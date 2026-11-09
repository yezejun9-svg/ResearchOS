import pathlib,hashlib,json
B=pathlib.Path(__file__).parent;R=pathlib.Path(r'D:/作品集/ResearchOS/research-os')
P=R/'execution/v2.4/receipts/W05/W05-99/qualification_maintenance_c57_codex/20261025-current-chat'
W=R/'.local/worktrees/qualification-maintenance-c57-20261025'
sha=lambda x:hashlib.sha256(x).hexdigest()
expect={'C51-R2-SOURCEFREEZE.json':'f76ac75feffbbe174c6268f505512a49447296953868f7d914889663c008525a','C51-R2-FINAL.json':'5a2738da447227dc52af4c44514e560d1850e3f138a2d48ac4034eed511b102c','C51-R2-DELTA.patch':'2553a14ec3394abf6936736e9c532273165ad93e50e5c6315c58346d610fb758'}
D=B/'C51-r2-static-snapshot';D.mkdir(exist_ok=False)
for name,h in expect.items():
 raw=(P/name).read_bytes();assert sha(raw)==h,name;(D/name).write_bytes(raw)
m=json.loads((D/'C51-R2-SOURCEFREEZE.json').read_text())
old=json.loads((B/'C51-static-snapshot-verification.json').read_text(encoding='utf-8'))
oldmap={i['path']:i for i in old['files']}
items=m['owned_files'];assert len(items)==51
changes=[i for i in items if i['sha256']!=oldmap[i['path']]['sha256']]
assert len(changes)==2 and all(i['changed_from_preseal'] for i in changes)
for i in changes:
 raw=(W/i['path']).read_bytes();assert len(raw)==i['bytes'] and sha(raw)==i['sha256'],i['path']
 out=D/i['path'];out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(raw)
assert all(sha((W/i['path']).read_bytes())==i['sha256'] for i in items)
out={'phase':'PHASE1_R2_TARGETED_STATIC_ONLY','freeze_sha256':expect['C51-R2-SOURCEFREEZE.json'],'all_live51_rechecked':True,'changed_count':2,'changed_files':changes,'unchanged49_bind_old_snapshot':True}
with (B/'C51-r2-static-snapshot-verification.json').open('x',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
print(json.dumps(out,ensure_ascii=False,indent=2))
print((D/'C51-R2-FINAL.json').read_text(encoding='utf-8'))
print((D/'C51-R2-DELTA.patch').read_text(encoding='utf-8'))
