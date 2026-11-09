"""Read-only count census of the exact synthetic fixture before targeted cleanup."""
import json
import pathlib
import sqlite3
import sys

db = pathlib.Path(sys.argv[1]).resolve(strict=True)
expected = pathlib.Path(sys.argv[2]).resolve(strict=True)
if db != expected or db.name != "researchos.sqlite" or "managed-client-coupling-fixture-1" not in db.parts:
    raise SystemExit("unexpected fixture database")
con = sqlite3.connect(db.as_uri() + "?mode=ro", uri=True, timeout=3)
con.execute("PRAGMA query_only=ON")
names = [row[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
needles = ("run", "effect", "dispatch", "model", "runtime", "qualification", "confirm", "ledger")
counts = {}
for name in names:
    if any(needle in name.lower() for needle in needles):
        escaped = name.replace('"', '""')
        counts[name] = con.execute(f'SELECT COUNT(*) FROM "{escaped}"').fetchone()[0]
con.close()
print(json.dumps({"mode": "read_only", "db": str(db), "relevant_table_counts": counts}, ensure_ascii=False, indent=2))
