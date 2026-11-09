import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path('D:/作品集/ResearchOS/research-os').resolve()
WT = ROOT / '.local/worktrees/codex-w0599-command-queue'
REL = 'execution/v2.4/receipts/W05/W05-99/cancel_finalization_design_revision_codex/246ac4e22a3c48fe8d86753b44a6cd78'
SOURCE = (WT / REL).resolve()
OUT = Path(__file__).resolve().parent


def ref(p):
    b = p.read_bytes()
    return {'path': str(p), 'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b)}


manifest_ref = ref(SOURCE / 'manifest.json')
assert manifest_ref['sha256'] == '487b5a772de101a6c419808659ba086bd9e69727ed48d4cda0a0276368279edc'
manifest = json.loads((SOURCE / 'manifest.json').read_bytes())
assert len(manifest['files']) == manifest['count'] == 89
items = [*manifest['files'], manifest_ref]
rows = []
for expected in items:
    source = Path(expected['path']).resolve()
    assert source.is_relative_to(SOURCE)
    current = ref(source)
    assert current['sha256'] == expected['sha256'] and current['bytes'] == expected['bytes']
    rel = source.relative_to(WT.resolve())
    target = (ROOT / rel).resolve()
    assert target.is_relative_to(ROOT / REL)
    target.parent.mkdir(parents=True, exist_ok=True)
    b = source.read_bytes()
    if target.exists():
        assert target.read_bytes() == b
    else:
        with target.open('xb') as f:
            f.write(b)
    got = ref(target)
    assert got['sha256'] == expected['sha256'] and got['bytes'] == expected['bytes']
    rows.append({'original': current, 'copy': got})
result = {'schema': 'researchos.root.readonly-design-public-copy.v1', 'actor': 'codex:/root',
          'at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'files': rows, 'count': len(rows),
          'proposal_sha256': '70dbfcec98e10f6872982daf03588746d3aa1bc90d7096c28f9b1e30ee5d24a6',
          'source_mutations': 0, 'canonical_mutations': 0, 'SQL_tests_models_HTTP': 0,
          'status': 'PUBLIC_DESIGN_BYTES_COPIED_ONLY_D05_AND_D02_REVIEW_GATES_OPEN',
          'source_scope_authorized': False, 'formal_increment': 0}
with (OUT / 'copy_audit.json').open('xb') as f:
    f.write((json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
print(json.dumps({'copied': len(rows), 'audit': ref(OUT / 'copy_audit.json'), 'source_scope_authorized': False}, ensure_ascii=True))
