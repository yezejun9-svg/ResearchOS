from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent
ROOT=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/w14-native-create-core-20261104')
AUTHOR=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/continue-cp597-20261104/core/author')
r=json.loads((AUTHOR/'focused01/results.json').read_text(encoding='utf-8'))
p=ROOT/'internal/domain/client_writer_origin.go';assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sources']['internal/domain/client_writer_origin.go']
text=p.read_text(encoding='utf-8');assert text.count('currentAuthorityRoot(ctx, tx,')==2
p.write_text(text.replace('currentAuthorityRoot(ctx, tx,','currentAuthorityRoot(tx,'),encoding='utf-8',newline='\n')
for name in ['internal/host/native_client_attestation_test.go','internal/api/v2_native_create_test.go']:
    p=ROOT/name;assert not p.exists();p.write_bytes((HERE/'tests'/name).read_bytes())
print(json.dumps({'status':'EXACT17_PRODUCTION_PLUS_FIVE_TESTS_PRESENT_FREEFUNC_ARITY_FIXED'}))
