"""Recreate the first 86-line ledger as a separate, labeled candidate.

This never writes the current C51-DIAGNOSTIC-LEDGER.jsonl. The replacement
clauses are the exact initial generator clauses recorded in this chat.
"""

from pathlib import Path

root = Path(__file__).resolve().parent
source = (root / "make_c51_ledger.py").read_text(encoding="utf-8")
replacements = [
    ('OUT = ROOT / "C51-DIAGNOSTIC-LEDGER.jsonl"',
     'OUT = ROOT / "C51-DIAGNOSTIC-LEDGER-RECONSTRUCTED-86.jsonl"'),
    ('for number in range(18, 54):', 'for number in range(18, 50):'),
    ('"registered own fixture root explicit" if 42 <= number <= 52 else "not applicable to Git patch check" if number == 53 else "not independently captured in these fields",',
     '"registered own fixture root explicit" if 42 <= number <= 49 else "not independently captured in these fields",'),
    ('        "source_version_note": "six-file boot source changed during 050-052; before/after hashes retained, results are owned51 local diagnostics" if 50 <= number <= 52 else None,\n',
     ''),
    ('"numbered": 36, "interim": len(events) - 53,',
     '"numbered": 32, "interim": len(events) - 49,'),
]
for old, new in replacements:
    if source.count(old) != 1:
        raise RuntimeError(f"expected one original clause: {old!r}, found {source.count(old)}")
    source = source.replace(old, new)
candidate_script = root / "make_c51_ledger_reconstructed86.py"
candidate_script.write_text(source, encoding="utf-8")
print(candidate_script)
