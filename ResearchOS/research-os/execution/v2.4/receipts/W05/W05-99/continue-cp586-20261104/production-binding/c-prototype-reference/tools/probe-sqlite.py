"""Independent SQLite semantics probe; in-memory fixtures only, no binding DDL."""
import json
import os
from pathlib import Path
import sqlite3
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'evidence/sqlite-prerequisite-probe-01.json'
OUT.parent.mkdir(parents=True, exist_ok=True)
report = {'sqlite_version': sqlite3.sqlite_version, 'database': ':memory:', 'd_access': False,
          'command': [sys.executable, *sys.argv], 'cwd': os.getcwd(),
          'binding_schema_executed': False, 'observations': [], 'passed': False}
try:
    with sqlite3.connect(':memory:') as db:
        db.execute('PRAGMA foreign_keys=ON')
        assert db.execute('PRAGMA foreign_keys').fetchone()[0] == 1
        assert db.execute("SELECT json_valid('{\"x\":1}'),json_type('{}')").fetchone() == (1, 'object')
        db.execute("CREATE TABLE null_probe(body TEXT CHECK(json_extract(body,'$.id')='expected'))")
        db.execute("INSERT INTO null_probe VALUES('{}')")
        assert db.execute('SELECT count(*) FROM null_probe').fetchone()[0] == 1
        report['observations'].append('SQLite CHECK(NULL) accepts a missing JSON field; explicit non-NULL/type checks are required.')
        db.execute('PRAGMA recursive_triggers=OFF')
        db.execute('CREATE TABLE replace_probe(id TEXT PRIMARY KEY,body TEXT NOT NULL)')
        db.execute("CREATE TRIGGER replace_no_delete BEFORE DELETE ON replace_probe BEGIN SELECT RAISE(ABORT,'immutable');END")
        db.execute("INSERT INTO replace_probe VALUES('key','original')")
        db.execute("INSERT OR REPLACE INTO replace_probe VALUES('key','replacement')")
        assert db.execute('SELECT body FROM replace_probe').fetchone()[0] == 'replacement'
        report['observations'].append('INSERT OR REPLACE bypasses the delete trigger when recursive_triggers=OFF.')
        db.execute("CREATE TRIGGER replace_conflict_guard BEFORE INSERT ON replace_probe WHEN EXISTS(SELECT 1 FROM replace_probe WHERE id=NEW.id) BEGIN SELECT RAISE(ABORT,'conflict');END")
        try:
            db.execute("INSERT OR REPLACE INTO replace_probe VALUES('key','changed')")
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError('insert-conflict guard did not reject REPLACE')
        assert db.execute('SELECT body FROM replace_probe').fetchone()[0] == 'replacement'
        report['observations'].append('A BEFORE INSERT conflict guard prevents that REPLACE bypass.')
    report['passed'] = True
except Exception:
    report['error'] = traceback.format_exc()
with OUT.open('x', encoding='utf-8') as stream:
    json.dump(report, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps(report, ensure_ascii=False))
raise SystemExit(0 if report['passed'] else 1)
