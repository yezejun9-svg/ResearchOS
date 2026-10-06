"""Commit only this round's initial W02 bytes and pending findings checkpoint."""
from pathlib import Path
import json
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
CARD = HERE.parent
index = json.loads((HERE / 'exact_dispatch_results.json').read_bytes())
paths = ['execution/v2.4/checkpoint.json', 'execution/v2.4/step_state.json',
    HERE.relative_to(ROOT).as_posix(),
    (CARD / 'registered-dispatch').relative_to(ROOT).as_posix()]
for row in index['actual_registered_selectors']:
    folder = Path(row['child_receipt']).resolve().parent
    assert folder.is_relative_to(CARD.resolve())
    paths.append(folder.relative_to(ROOT).as_posix())
for name in ('ast_boundary_probe.py', 'ast_boundary_probe.json', 'g02_default_expression_mutant.txt'):
    paths.append((CARD / 'independent-review-codex' / name).relative_to(ROOT).as_posix())
subprocess.run(['git', 'add', '--', *paths], cwd=ROOT, check=True)
subprocess.run(['git', '-c', 'core.whitespace=cr-at-eol', 'diff', '--cached', '--check', '--', '.',
    ':(exclude)execution/v2.4/receipts/**'], cwd=ROOT, check=True)
subprocess.run(['git', 'commit', '-m', 'test(w02): preserve registered internal results and independent findings'],
    cwd=ROOT, check=True)
