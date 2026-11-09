import pathlib,json,hashlib
B=pathlib.Path(__file__).parent;D=B/'C51-r2-static-snapshot'
P=pathlib.Path(r'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/qualification_maintenance_c57_codex/20261025-current-chat')
manifest=json.loads((D/'C51-R2-FINAL.json').read_text())
sha=lambda data:hashlib.sha256(data).hexdigest()
T=D/'author-test-receipts';T.mkdir(exist_ok=False)
for ref in manifest['test_receipts']:
 data=(P/ref['path']).read_bytes(); assert sha(data)==ref['sha256'],ref['path']
 (T/ref['path']).write_bytes(data)
print('Verified author receipt refs:',len(manifest['test_receipts']))
print('Author latest recipe:')
print((T/'058-r2-domain.recipe.txt').read_text(encoding='utf-8-sig'))
print('Author latest native exit:',(T/'058-r2-domain.native-exit.txt').read_text(encoding='utf-8-sig').strip())
raw=(T/'058-r2-domain.stdout.raw').read_text(encoding='utf-8-sig')
for line in raw.splitlines():
 if any(s in line for s in ['HistoricalQualification','PASS','FAIL','SKIP','ok ']):print(line)
