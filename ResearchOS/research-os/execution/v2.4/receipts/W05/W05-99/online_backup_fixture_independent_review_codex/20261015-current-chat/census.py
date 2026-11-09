"""Fixture-only read-only logical SQLite and source-file census. Emits digests, not rows."""
import base64
import hashlib
import json
import os
import sqlite3
import sys
from pathlib import Path
from urllib.parse import quote

def sha(data):
    return hashlib.sha256(data).hexdigest()

def canonical(value):
    if value is None:
        return ["null", None]
    if isinstance(value, bytes):
        return ["blob", base64.b64encode(value).decode("ascii")]
    if isinstance(value, int):
        return ["integer", str(value)]
    if isinstance(value, float):
        return ["real", value.hex()]
    return ["text", value]

def database(path):
    uri = "file:" + quote(str(Path(path).resolve()).replace("\\", "/"), safe="/:") + "?mode=ro"
    con = sqlite3.connect(uri, uri=True)
    con.execute("PRAGMA query_only=ON")
    con.execute("BEGIN")
    user_version = con.execute("PRAGMA user_version").fetchone()[0]
    application_id = con.execute("PRAGMA application_id").fetchone()[0]
    integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
    schema = con.execute("SELECT type,name,tbl_name,sql FROM sqlite_schema ORDER BY type,name,tbl_name").fetchall()
    table_names = [r[0] for r in con.execute("SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name")]
    tables = {}
    for name in table_names:
        escaped = name.replace('"', '""')
        rows = []
        for row in con.execute('SELECT * FROM "' + escaped + '"'):
            rows.append(json.dumps([canonical(v) for v in row], ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
        rows.sort()
        tables[name] = {"rows": len(rows), "sha256": sha(b"\n".join(rows))}
    con.rollback()
    con.close()
    return {"kind":"sqlite_all_tables","user_version":user_version,"application_id":application_id,
            "integrity_check":integrity,"schema_sha256":sha(json.dumps(schema, ensure_ascii=False, separators=(",", ":")).encode("utf-8")),
            "tables":tables}

def files(path):
    root = Path(path).resolve()
    entries = {}
    for current, dirs, names in os.walk(root):
        dirs.sort(); names.sort()
        for name in dirs + names:
            p = Path(current) / name
            rel = p.relative_to(root).as_posix()
            st = p.lstat()
            item = {"type":"directory" if p.is_dir() else "file","mtime_ns":st.st_mtime_ns,"mode_bits":oct(st.st_mode),"size":st.st_size}
            if p.is_file():
                try:
                    with p.open("rb") as f:
                        item["sha256"] = sha(f.read())
                except OSError as exc:
                    # The real held coordinator.lock denies reads on Windows.
                    item["read_error"] = type(exc).__name__
            entries[rel] = item
    return {"kind":"source_file_tree","root":str(root),"entries":entries}

if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("db", "files"):
        raise SystemExit("usage: census.py db|files <fixture-only path>")
    print(json.dumps(database(sys.argv[2]) if sys.argv[1] == "db" else files(sys.argv[2]), ensure_ascii=False, sort_keys=True, separators=(",", ":")))
