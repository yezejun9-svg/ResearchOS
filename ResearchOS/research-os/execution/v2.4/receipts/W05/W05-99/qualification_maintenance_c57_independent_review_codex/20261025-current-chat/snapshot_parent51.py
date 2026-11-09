import pathlib,json,hashlib
B=pathlib.Path(__file__).parent
R=pathlib.Path(r'D:/作品集/ResearchOS/research-os')
P=R/'execution/v2.4/receipts/W05/W05-99/qualification_maintenance_c57_codex/20261025-current-chat/C51-PRESEAL.json'
E=R/'execution/v2.4/receipts/W05/W05-99/resume_cp528_codex/20261025-current-chat/C51-root-preseal-verification-r3.json'
sha=lambda d:hashlib.sha256(d).hexdigest()
raw=P.read_bytes()
assert sha(raw)=='cd99649c24552dbd6394ba97daf04bb835da16170cd02c4ef0808684614b29fb'
p=json.loads(raw); W=pathlib.Path(p['worktree']); items=p['owned_files']
assert len(items)==51 and len({i['path'] for i in items})==51
D=B/'C51-static-snapshot'; D.mkdir(exist_ok=False)
(D/'C51-PRESEAL.json').write_bytes(raw); eraw=E.read_bytes(); (D/E.name).write_bytes(eraw)
for i in items:
 src=W/i['path']; data=src.read_bytes()
 assert len(data)==i['bytes'] and sha(data)==i['sha256'], i['path']
 out=D/i['path']; out.parent.mkdir(parents=True,exist_ok=True); out.write_bytes(data)
 assert sha(out.read_bytes())==i['sha256']
assert all(sha((W/i['path']).read_bytes())==i['sha256'] for i in items)
v={'phase':'PHASE1_STATIC_ONLY_NO_ACCEPTANCE','preseal_sha256':sha(raw),'root_verification_sha256':sha(eraw),'source_worktree':str(W),'count':len(items),'source_recheck_unchanged':True,'files':items}
(B/'C51-static-snapshot-verification.json').write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in v.items() if k!='files'},ensure_ascii=False))
for i in items: print(i['path'],i['sha256'])
