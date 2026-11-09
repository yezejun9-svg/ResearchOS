import pathlib,hashlib,json
B=pathlib.Path(__file__).parent
R=pathlib.Path(r'D:\作品集\ResearchOS\research-os')
W=R/'.local/worktrees/qualification-maintenance-c57-20261025'
M=R/'execution/v2.4/receipts/W05/W05-99/qualification_recovery_boundary_boot6_codex/20261025-current-chat/final-v5-six-source-manifest.json'
assert hashlib.sha256(M.read_bytes()).hexdigest()=='175b24b640edf7d8a7924db527c93400125299278632e58d8f73ffeceb31a3d0'
manifest=json.loads(M.read_text(encoding='utf-8-sig'))
out=B/'BOOT6-v5-static-snapshot';out.mkdir(exist_ok=False)
for ref in manifest:
 p=W/ref['path'];raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==ref['sha256'] and len(raw)==ref['bytes'],str(p)
 dest=out/ref['path'];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
 for i,line in enumerate(raw.decode('utf-8-sig').splitlines(),1):
  if line.startswith('func ') or line.startswith('type '): print(f'{ref["path"]}:{i}:{line}')
for ref in manifest:assert hashlib.sha256((W/ref['path']).read_bytes()).hexdigest()==ref['sha256']
(out/'verified-source-manifest.json').write_text(json.dumps({'status':'EXACT_V5_SIX_BYTES_BEFORE_AND_AFTER_READ','entries':manifest},indent=2),encoding='utf-8')
print('EXACT6_BEFORE_AFTER_SHA256_MATCH')
