from pathlib import Path
import json

HERE = Path(__file__).resolve().parent
ROOT = Path('D:/作品集/ResearchOS/research-os/.local/worktrees/w14-peer-auth-seam-20261104')
NAMES = ['internal/host/native_peer_provenance_test.go', 'internal/domain/client_protocol_auth_context_test.go', 'internal/api/v2_auth_context_test.go']
for name in NAMES:
    assert not (ROOT/name).exists(), name
for name in NAMES:
    with (ROOT/name).open('x', encoding='utf-8', newline='\n') as out:
        out.write((HERE/Path(name).name).read_text(encoding='utf-8'))
print(json.dumps({'status': 'INSTALLED_ONLY_THREE_AUTHORIZED_NEW_TEST_FILES', 'files': NAMES}))
