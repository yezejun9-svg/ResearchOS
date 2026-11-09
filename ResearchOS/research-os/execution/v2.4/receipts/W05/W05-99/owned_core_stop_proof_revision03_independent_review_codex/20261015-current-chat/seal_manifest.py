from pathlib import Path
import datetime, hashlib, json

e = Path(__file__).parent
active = [p for p in (e / 'command-captures').iterdir() if not (p / 'after.json').exists()]
files = []
for p in sorted(e.rglob('*')):
    if not p.is_file() or p.name == 'evidence-manifest.json' or any(a in p.parents for a in active):
        continue
    raw = p.read_bytes()
    files.append({'path': str(p), 'relative_path': p.relative_to(e).as_posix(), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
by_name = {x['relative_path']: x for x in files}
review = json.loads((e / 'review.json').read_text(encoding='utf-8'))
assert review['verdict'] == 'NEEDS_CHANGES'
assert len(review['findings']) == 1
assert review['formal_increment'] == 0
for name in ('review.json', 'review.md', 'diagnostic-ledger.json', 'author-evidence-audit.json'):
    assert name in by_name
result = {'schema': 'researchos.owned-core-stop-r3-independent-evidence-manifest.v1', 'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'reviewer': review['reviewer'], 'candidate': review['candidate'], 'tree': review['tree'], 'verdict': review['verdict'], 'review_json': by_name['review.json'], 'review_md': by_name['review.md'], 'diagnostic_ledger': by_name['diagnostic-ledger.json'], 'file_count': len(files), 'files': files, 'excluded_active_capture_directories': [str(p) for p in active], 'finite_snapshot_note': 'Manifest excludes itself and its in-progress sealing capture. Their completed raw command capture is retained outside this finite manifest snapshot. All prior captures, including successful report writer, are included. No later Source edits permitted by this review.', 'source_edit_authority': False, 'actual_authority': False, 'formal_increment': 0}
p = e / 'evidence-manifest.json'
p.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
raw = p.read_bytes()
print(json.dumps({'manifest': str(p), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw), 'file_count': len(files), 'verdict': result['verdict'], 'excluded_active_captures': len(active)}, ensure_ascii=False, indent=2))
