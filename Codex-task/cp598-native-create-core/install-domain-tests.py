from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent
ROOT=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/w14-native-create-core-20261104')
AUTHOR=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/continue-cp597-20261104/core/author')
record=json.loads((AUTHOR/'compile01/results.json').read_text(encoding='utf-8'))
p=ROOT/'internal/domain/client_writer_origin.go'
assert hashlib.sha256(p.read_bytes()).hexdigest()==record['sources']['internal/domain/client_writer_origin.go']
text=p.read_text(encoding='utf-8');assert text.count('s.currentAuthorityRoot(')==1 and text.count('s.Domain.currentAuthorityRoot(')==1
text=text.replace('s.currentAuthorityRoot(','currentAuthorityRoot(').replace('s.Domain.currentAuthorityRoot(','currentAuthorityRoot(')
p.write_text(text,encoding='utf-8',newline='\n')
for name in ['internal/domain/client_writer_origin_test.go','internal/domain/client_native_writer_origin_store_test.go','internal/domain/backup_client_native_writer_origins_test.go']:
    p=ROOT/name;assert not p.exists();p.write_bytes((HERE/'tests'/name).read_bytes())
print(json.dumps({'status':'FIXED_ONLY_TWO_FREE_FUNCTION_QUALIFIERS_AND_INSTALLED_THREE_DOMAIN_TEST_FILES'}))
