"""Read-only qualification of the copied, controlled candidate; no raw rows."""
import json
import sqlite3
from pathlib import Path
from urllib.parse import quote

e = Path(__file__).resolve().parent
task = Path('D:/作品集/ResearchOS/research-os/.local/online-backup-fixture-qualification-20261015-tmp')
db = task / 'fixture/Q03/source-data/researchos.sqlite'
q03 = json.loads((e / 'q03-copied-db-census.stdout.raw').read_text(encoding='utf-8'))
q02 = json.loads((e / 'q02-db-before.stdout.raw').read_text(encoding='utf-8'))
uri = 'file:' + quote(str(db.resolve()).replace('\\','/'),safe='/:') + '?mode=ro'
con = sqlite3.connect(uri,uri=True)
con.execute('PRAGMA query_only=ON')
tables = q03['tables']
relevant = {name:info['rows'] for name,info in tables.items() if info['rows'] and any(word in name for word in ('run','effect','client','queue','artifact','receipt','content'))}
status = []
if 'domain_objects' in tables:
    status = con.execute("SELECT kind, json_extract(body,'$.status'), count(*) FROM domain_objects GROUP BY kind,json_extract(body,'$.status') ORDER BY kind,json_extract(body,'$.status')").fetchall()
out = {'candidate_source_schema_equal_q02':q03['schema_sha256']==q02['schema_sha256'],
       'candidate_schema_sha256':q03['schema_sha256'],'pinned_schema_sha256':q02['schema_sha256'],
       'table_count':len(tables),'integrity_check':q03['integrity_check'],
       'user_version':q03['user_version'],'nonempty_relevant_tables':relevant,
       'domain_object_status_counts':status}
if 'schema_migrations' in tables:
    migrations = [r[0] for r in con.execute('SELECT version FROM schema_migrations ORDER BY version')]
    out['migration_count'] = len(migrations)
    out['migration_min'] = min(migrations) if migrations else None
    out['migration_max'] = max(migrations) if migrations else None
bindings = [json.loads(r[0]) for r in con.execute("SELECT body FROM domain_objects WHERE kind='WorkspaceBinding' AND json_extract(body,'$.status')='ACTIVE'")]
out['active_workspace_bindings'] = len(bindings)
out['active_binding_paths_under_q03_task_root'] = all(Path(b.get('real_path','')).resolve().is_relative_to((task/'fixture/Q03').resolve()) for b in bindings)
current_db = task/'fixture/Q02/source-data/researchos.sqlite'
current_uri = 'file:' + quote(str(current_db.resolve()).replace('\\','/'),safe='/:') + '?mode=ro'
current = sqlite3.connect(current_uri,uri=True)
out['pinned_fixture_migration_max'] = current.execute('SELECT max(version) FROM schema_migrations').fetchone()[0]
current.close()
print(json.dumps(out,ensure_ascii=False,sort_keys=True,separators=(',',':')))
