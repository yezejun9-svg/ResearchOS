"""Read-only audit of the frozen command-index and its capture files."""
import json
from pathlib import Path

e = Path(__file__).resolve().parent
index = json.loads((e / 'command-index.json').read_text(encoding='utf-8'))
rows = index['commands']
assert len(rows) == index['count'] == 195

def exists(name):
    return bool(name) and (e / name).is_file()

completed = [r['id'] for r in rows if all(exists(r.get(k)) for k in ('recipe','exit','stdout','stderr'))]
missing_exit = []
nonzero = []
other_incomplete = []
for r in rows:
    capture = {k: bool(exists(r.get(k))) for k in ('recipe','exit','stdout','stderr')}
    if not capture['exit']:
        actual = e / (r['id'] + '.exit.json')
        missing_exit.append({'id': r['id'], 'indexed_exit': r.get('exit'), 'actual_exit_now': actual.is_file(),
                             'capture': capture})
    if r.get('native_exit') not in (None, 0):
        nonzero.append({'id': r['id'], 'native_exit': r['native_exit']})
    if not all(capture.values()):
        other_incomplete.append({'id': r['id'], 'capture': capture})
ledger = (e / 'diagnostic-ledger.json')
diagnostics = json.loads(ledger.read_text(encoding='utf-8'))
bootstrap = json.loads((e / 'bootstrap-read.recipe.json').read_text(encoding='utf-8'))
first_ledger = (e / 'command-ledger.ndjson').read_text(encoding='utf-8').splitlines()[0]
print(json.dumps({'index_count': len(rows), 'completed_all_four_captures': len(completed),
    'missing_exit': missing_exit, 'other_incomplete': other_incomplete, 'nonzero': nonzero,
    'diagnostic_ledger': diagnostics, 'bootstrap_recipe': bootstrap, 'bootstrap_ledger_first_line': first_ledger},
    ensure_ascii=False, sort_keys=True, separators=(',',':')))
