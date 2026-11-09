"""Read-only, selected Q03 restore invariants; no token or row contents emitted."""
import json
import sqlite3
from pathlib import Path
from urllib.parse import quote

base = Path('D:/作品集/ResearchOS/research-os/.local/online-backup-fixture-qualification-20261015-tmp/fixture/Q03')
evidence = Path(__file__).resolve().parent

def connect(path):
    uri = 'file:' + quote(str(path.resolve()).replace('\\','/'), safe='/:') + '?mode=ro'
    db = sqlite3.connect(uri, uri=True)
    db.execute('PRAGMA query_only=ON')
    return db

def counts(db, query):
    return {str(a): int(b) for a, b in db.execute(query)}

def facts(db):
    return {
        'integrity': db.execute('PRAGMA integrity_check').fetchone()[0],
        'run_status': counts(db, "SELECT json_extract(body,'$.status'),count(*) FROM domain_objects WHERE kind='Run' GROUP BY 1"),
        'effect_state': counts(db, "SELECT json_extract(body,'$.state'),count(*) FROM resource_effects GROUP BY 1"),
        'queue_state': counts(db, 'SELECT state,count(*) FROM client_command_queue GROUP BY state'),
        'queue_fence': counts(db, 'SELECT state,count(*) FROM client_queue_fences GROUP BY state'),
        'control_state': counts(db, 'SELECT state,count(*) FROM client_control_requests GROUP BY state'),
        'queue_receipts': db.execute('SELECT count(*) FROM client_control_receipts').fetchone()[0],
        'workspace_status': counts(db, "SELECT json_extract(body,'$.status'),count(*) FROM domain_objects WHERE kind='WorkspaceBinding' GROUP BY 1"),
    }

source = connect(base / 'current-data-r2/researchos.sqlite')
restored = connect(base / 'restored-data/researchos.sqlite')
a, b = facts(source), facts(restored)
source.close(); restored.close()
print(json.dumps({'source': a, 'restored': b}, ensure_ascii=False, sort_keys=True, separators=(',',':')))
assert a['integrity'] == b['integrity'] == 'ok'
assert a['run_status'].get('QUEUED', 0) == 1
assert b['run_status'].get('RECONCILING', 0) == 1
assert a['effect_state'].get('UNKNOWN', 0) >= 1
assert b['effect_state'].get('UNKNOWN', 0) >= 1
assert a['queue_state'].get('UNKNOWN', 0) >= 1
assert b['queue_state'].get('UNKNOWN', 0) >= 1
assert b['control_state'].get('RECONCILING', 0) >= 1
assert a['workspace_status'] == b['workspace_status'] == {'REVOKED': 1}
comparison = json.loads((evidence / 'compare-q03-current.stdout.raw').read_text(encoding='utf-8'))
assert comparison['source_table_count'] == comparison['restored_table_count'] == 88
assert comparison['source_all_tables_equal'] and comparison['source_schema_equal'] and comparison['source_version_equal']
assert comparison['source_integrity_before'] == comparison['source_integrity_after'] == comparison['restored_integrity'] == 'ok'
expected_restore_changes = {'auth_credentials','backup_restore_barriers','client_command_queue','client_control_receipts',
    'client_control_requests','client_queue_fences','domain_objects','domain_refs','domain_versions',
    'event_state_snapshots','outbox','resource_effects'}
assert set(comparison['restored_table_differences']) == expected_restore_changes
assert (evidence / 'q03-acl-before.stdout.raw').read_bytes() == (evidence / 'q03-acl-after.stdout.raw').read_bytes()
assert set(comparison['source_file_differences']) == {'researchos.sqlite-wal','researchos.sqlite-shm'}
print(json.dumps({'assertions': 'PASS', 'source_all_tables_equal': True, 'native_acl_equal': True,
    'restored_changed_tables': sorted(expected_restore_changes), 'unchanged_immutable_content_tables': True},
    ensure_ascii=False, sort_keys=True, separators=(',',':')))
