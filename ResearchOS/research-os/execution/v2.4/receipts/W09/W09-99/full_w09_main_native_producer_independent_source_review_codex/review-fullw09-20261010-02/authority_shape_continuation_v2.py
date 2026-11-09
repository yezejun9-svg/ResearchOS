"""Correct the explicit in-memory fixture namespace; preserve all previous IO."""
from pathlib import Path

base = Path(__file__).with_name('authority_shape_continuation.py')
source = base.read_text(encoding='utf-8')
replacements = {
    'namespace=dict(m=m,c=c,contract=contract': 'namespace=dict(hashlib=hashlib,Path=Path,m=m,c=c,contract=contract',
    "'actual-v2-author-short-digest-Root-peer.raw.jsonl'": "'actual-v2-author-short-digest-Root-peer-v2.raw.jsonl'",
    "'actual-v2-author-short-digest-Root-peer.binding.json'": "'actual-v2-author-short-digest-Root-peer-v2.binding.json'",
    "'continuation-Source-guard.closed.json'": "'continuation-v2-Source-guard.closed.json'",
    "'complete-authority-shape-and-real-blockers.json'": "'complete-authority-shape-and-real-blockers-v2.json'",
}
for old, new in replacements.items():
    if source.count(old) != 1:
        raise ValueError('EXACT_FINITE_CORRECTION_CARDINALITY')
    source = source.replace(old, new)
exec(compile(source, str(__file__) + ':finite-corrected-source', 'exec'), globals())
