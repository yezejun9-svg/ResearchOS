import hashlib
import json
from pathlib import Path

out = Path(__file__).resolve().parent
main = out.parents[3]
checkout = main / '.local/worktrees/c02-review'
author = checkout / 'execution/receipts/W17/c02/20260930T142902Z-f4f3ea0f54'

def entry(path, root):
    raw = path.read_bytes()
    return {'path': path.relative_to(root).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

source_paths = [
    'AGENTS.md', 'internal/domain/remote_isolation_test.go', 'tests/security/c02_fixture.py',
    'tests/security/c02_expected.json', 'internal/domain/materialize.go',
    'internal/domain/retrieval_local.go', 'internal/domain/retrieval.go', 'internal/domain/context.go',
    'internal/domain/context_test.go', 'spec/v2.0/contracts/acceptance.json',
    'spec/v2.0/03_DATA_CONTRACTS.md', 'execution/toolchains/locked.json'
]
data = {
    'schema': 'researchos.independent-evidence-index.v1',
    'source_revision': 'c3991c0775f79382617459b369e1f369e9e3b960',
    'review_checkout_revision': 'bbaf59187388d3da961856e805468a91507bf479',
    'local_files': [entry(p, out) for p in sorted(out.rglob('*')) if p.is_file() and p.name != 'evidence-index.json'],
    'reviewed_sources': [entry(checkout / p, checkout) for p in source_paths],
    'author_evidence': [entry(p, checkout) for p in sorted(author.iterdir()) if p.is_file()],
    'index_self_hash': 'Returned separately to coordinator to avoid self-reference.'
}
target = out / 'evidence-index.json'
target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'review_sha256': entry(out / 'review.json', out)['sha256'], 'index_sha256': entry(target, out)['sha256'], 'local_files': len(data['local_files'])}))
