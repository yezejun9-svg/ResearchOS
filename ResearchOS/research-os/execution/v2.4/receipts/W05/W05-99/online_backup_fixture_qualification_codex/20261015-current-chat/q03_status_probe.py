"""Read-only status census of the copied controlled candidate; omits raw identities and content."""
import json
import re
import sqlite3
from pathlib import Path
from urllib.parse import quote

db = Path('D:/作品集/ResearchOS/research-os/.local/online-backup-fixture-qualification-20261015-tmp/fixture/Q03/source-data/researchos.sqlite')
uri = 'file:' + quote(str(db.resolve()).replace('\\','/'),safe='/:') + '?mode=ro'
con = sqlite3.connect(uri,uri=True)
con.execute('PRAGMA query_only=ON')
names = [row[0] for row in con.execute("SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name")]
out = {}
for name in names:
    if not any(word in name for word in ('effect','client_','runtime_','queue')): continue
    escaped = name.replace('"','""')
    count = con.execute('SELECT count(*) FROM "'+escaped+'"').fetchone()[0]
    if count == 0: continue
    columns = [r[1] for r in con.execute('PRAGMA table_info("'+escaped+'")')]
    parts = {}
    for col in columns:
        if re.search(r'(status|state|outcome|phase)',col,re.I):
            esc_col = col.replace('"','""')
            parts[col] = con.execute('SELECT "'+esc_col+'",count(*) FROM "'+escaped+'" GROUP BY "'+esc_col+'"').fetchall()
    out[name] = {'rows':count,'status_values':parts}
con.close()
print(json.dumps(out,ensure_ascii=False,sort_keys=True,separators=(',',':')))
