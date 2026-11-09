"""C-only data-integrity fixture consumer. This is not a product authorization gate."""
import base64
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import subprocess
from types import MappingProxyType

ROOT = Path(__file__).resolve().parent
SCHEMA_NAME = 'researchos.coding-delivery-binding-prototype'
SCHEMA_VERSION = 1
MAX_BODY_BYTES = 65536
HASH_RE = re.compile(r'sha256:[0-9a-f]{64}\Z')
INT64_RE = re.compile(r'[1-9][0-9]{0,18}\Z')

IDENTITY_COLUMNS = (
    'binding_schema', 'schema_version', 'project', 'goal_id', 'task_id',
    'approval_issuer_ref', 'approval_ref', 'lineage_issuer_ref', 'business_anchor',
    'owner_principal', 'owner_root', 'owner_host', 'task_contract_hash', 'goal_contract_hash',
)
BODY_STRING_FIELDS = tuple(name for name in IDENTITY_COLUMNS if name != 'schema_version') + (
    'parent_ref', 'parent_confirmation_hash', 'creation_method', 'client_id', 'command_id',
    'request_hash', 'session_ref', 'workspace_ref', 'workspace_hash',
    'profile_ref', 'profile_hash', 'policy_ref', 'policy_hash', 'suite_ref', 'suite_hash',
    'approved_plan_ref', 'approved_plan_hash', 'requirement_refs_ref', 'requirement_refs_hash',
    'input_refs_ref', 'input_refs_hash', 'origin_problem_id', 'candidate_id',
    'no_progress_ref', 'no_progress_input_key', 'creation_writer_epoch', 'creation_session_revision',
)
BODY_FIELDS = ('schema_version',) + BODY_STRING_FIELDS
HASH_FIELDS = (
    'business_anchor', 'task_contract_hash', 'goal_contract_hash', 'parent_confirmation_hash',
    'request_hash', 'workspace_hash', 'profile_hash', 'policy_hash', 'suite_hash',
    'approved_plan_hash', 'requirement_refs_hash', 'input_refs_hash', 'no_progress_input_key',
)
DECIMAL_FIELDS = ('creation_writer_epoch', 'creation_session_revision')
INSERT_COLUMNS = IDENTITY_COLUMNS + ('binding_body', 'binding_hash')

# Deliberately fake, minimal canonical subjects. No production migration is run.
FAKE_SUBJECT_DDL = '''
CREATE TABLE domain_objects (
 project TEXT NOT NULL,
 kind TEXT NOT NULL CHECK(kind IN ('Goal','Task')),
 id TEXT NOT NULL,
 fixture_only INTEGER NOT NULL CHECK(fixture_only=1),
 body TEXT NOT NULL CHECK(json_valid(body)),
 PRIMARY KEY(project,kind,id)
) STRICT, WITHOUT ROWID;
'''


class IntegrityRejected(ValueError):
    pass


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise IntegrityRejected('duplicate JSON name')
        result[key] = value
    return result


def strict_json(raw):
    try:
        if isinstance(raw, bytes):
            raw = raw.decode('utf-8')
        raw.encode('utf-8')  # Reject isolated surrogate strings too.
        return json.loads(raw, object_pairs_hook=_pairs,
                          parse_constant=lambda value: (_ for _ in ()).throw(IntegrityRejected('non-finite JSON')))
    except (ValueError, UnicodeError, TypeError) as error:
        if isinstance(error, IntegrityRejected):
            raise
        raise IntegrityRejected('strict JSON required') from error


def validate_dto(body):
    if type(body) is not dict or set(body) != set(BODY_FIELDS):
        raise IntegrityRejected('closed prototype DTO required')
    if type(body['schema_version']) is not int or body['schema_version'] != SCHEMA_VERSION or body['binding_schema'] != SCHEMA_NAME:
        raise IntegrityRejected('unknown prototype version')
    for name in BODY_STRING_FIELDS:
        value = body[name]
        if type(value) is not str or not value.strip() or '\x00' in value:
            raise IntegrityRejected('required nonempty string field: ' + name)
        try:
            value.encode('utf-8')
        except UnicodeError as error:
            raise IntegrityRejected('invalid Unicode field') from error
    if body['creation_method'] != 'goal.start':
        raise IntegrityRejected('only explicit goal.start provenance is represented')
    for name in HASH_FIELDS:
        if not HASH_RE.fullmatch(body[name]):
            raise IntegrityRejected('hash shape: ' + name)
    if body['task_contract_hash'] == body['goal_contract_hash']:
        raise IntegrityRejected('Task and Goal contract hashes must differ')
    for name in DECIMAL_FIELDS:
        value = body[name]
        if not INT64_RE.fullmatch(value) or int(value) > 9223372036854775807:
            raise IntegrityRejected('canonical positive int64 decimal string required')
    return body


class Canonicalizer:
    """Call only the locally built, pinned C helper using copied Go canonical code."""
    def __init__(self, helper, expected_sha256):
        self.helper = Path(helper).resolve()
        if not self.helper.is_relative_to(ROOT) or not self.helper.is_file():
            raise IntegrityRejected('canonical helper must be a C prototype artifact')
        self.expected_sha256 = expected_sha256

    def raw(self, raw):
        if not isinstance(raw, bytes) or len(raw) > MAX_BODY_BYTES:
            raise IntegrityRejected('canonical input byte limit')
        if hashlib.sha256(self.helper.read_bytes()).hexdigest() != self.expected_sha256:
            raise IntegrityRejected('canonical helper binary drift')
        result = subprocess.run([str(self.helper)], input=raw, capture_output=True, cwd=ROOT, timeout=10)
        if result.returncode != 0:
            raise IntegrityRejected('copied Go canonicalizer rejected input')
        response = strict_json(result.stdout)
        if response.get('valid') is not True:
            raise IntegrityRejected('invalid canonical helper response')
        try:
            canonical = base64.b64decode(response['canonical_base64'], validate=True)
        except (ValueError, KeyError) as error:
            raise IntegrityRejected('invalid canonical bytes response') from error
        digest = 'sha256:' + hashlib.sha256(canonical).hexdigest()
        if response.get('hash') != digest:
            raise IntegrityRejected('canonical digest response mismatch')
        return canonical, digest

    def value(self, value):
        # This is transport only; Go performs the actual Marshal -> JCS -> Digest chain.
        try:
            raw = json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')
        except (ValueError, TypeError, UnicodeError) as error:
            raise IntegrityRejected('JSON transport value rejected') from error
        return self.raw(raw)


def _fixture_path(path, must_exist):
    path = Path(path).resolve()
    if not path.is_relative_to(ROOT) or path.suffix != '.sqlite' or path.exists() != must_exist:
        raise IntegrityRejected('only explicitly new/restored C prototype SQLite files are allowed')
    return path


def open_fixture(path=None, *, restored=False, recursive_triggers=False):
    filename = ':memory:' if path is None else str(_fixture_path(path, restored))
    db = sqlite3.connect(filename, isolation_level=None, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    db.execute('PRAGMA recursive_triggers=' + ('ON' if recursive_triggers else 'OFF'))
    return db


def initialize_fixture(db):
    db.executescript(FAKE_SUBJECT_DDL)
    db.executescript((ROOT / 'coding_delivery_bindings.sql').read_text(encoding='utf-8'))


def put_subjects(db, body):
    for kind, identity in [('Goal', body['goal_id']), ('Task', body['task_id'])]:
        if db.execute('SELECT 1 FROM domain_objects WHERE project=? AND kind=? AND id=?', (body['project'], kind, identity)).fetchone():
            continue
        value = {'fixture_only': True, 'project': body['project'], 'kind': kind, 'id': identity}
        if kind == 'Task':
            value['goal_id'] = body['goal_id']
        db.execute('INSERT INTO domain_objects VALUES(?,?,?,?,?)',
                   (body['project'], kind, identity, 1, json.dumps(value, separators=(',', ':'))))


def row_for(body, canonicalizer):
    validate_dto(body)
    canonical, digest = canonicalizer.value(body)
    return tuple(body[name] for name in IDENTITY_COLUMNS) + (canonical.decode('utf-8'), digest)


INSERT_SQL = 'INSERT INTO coding_delivery_bindings (' + ','.join(INSERT_COLUMNS) + ') VALUES (' + ','.join('?' for _ in INSERT_COLUMNS) + ')'


def schema_snapshot(db):
    objects = [list(row) for row in db.execute("SELECT type,name,tbl_name,sql FROM sqlite_schema WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name")]
    tables = {}
    for table in ('domain_objects', 'coding_delivery_bindings'):
        columns = [list(row) for row in db.execute('PRAGMA table_xinfo(' + table + ')')]
        foreign_keys = [list(row) for row in db.execute('PRAGMA foreign_key_list(' + table + ')')]
        indexes = []
        for row in db.execute('PRAGMA index_list(' + table + ')'):
            indexes.append({'row': list(row), 'columns': [list(part) for part in db.execute('PRAGMA index_xinfo("' + row[1] + '")')]})
        tables[table] = {'columns': columns, 'foreign_keys': foreign_keys, 'indexes': indexes}
    return {'objects': objects, 'tables': tables}


@dataclass(frozen=True)
class SyntheticExpectedContext:
    """Fixture-owned expected values, explicitly not an authenticated Host context."""
    body: object

    def __post_init__(self):
        validate_dto(dict(self.body))
        object.__setattr__(self, 'body', MappingProxyType(dict(self.body)))


class FixtureConsumer:
    def __init__(self, canonicalizer, expected_schema):
        self.canonicalizer = canonicalizer
        self.expected_schema = strict_json(json.dumps(expected_schema))

    def validate_schema(self, db):
        if db.execute('PRAGMA foreign_keys').fetchone()[0] != 1 or schema_snapshot(db) != self.expected_schema:
            raise IntegrityRejected('schema/index/trigger/FK fingerprint mismatch')
        if db.execute('PRAGMA foreign_key_check').fetchall():
            raise IntegrityRejected('foreign key integrity mismatch')

    def consume(self, db, project, task_id, expected):
        self.validate_schema(db)
        if not isinstance(expected, SyntheticExpectedContext):
            raise IntegrityRejected('explicit synthetic expected context required')
        rows = db.execute('SELECT * FROM coding_delivery_bindings WHERE project=? AND task_id=?', (project, task_id)).fetchall()
        if len(rows) != 1:
            raise IntegrityRejected('exactly one immutable binding required')
        row = rows[0]
        raw = row['binding_body'].encode('utf-8')
        if len(raw) > MAX_BODY_BYTES:
            raise IntegrityRejected('binding body byte limit')
        body = validate_dto(strict_json(raw))
        for name in IDENTITY_COLUMNS:
            if type(row[name]) is not type(body[name]) or row[name] != body[name]:
                raise IntegrityRejected('column/body identity mismatch')
        canonical, digest = self.canonicalizer.raw(raw)
        if canonical != raw or not HASH_RE.fullmatch(row['binding_hash']) or row['binding_hash'] != digest:
            raise IntegrityRejected('binding canonical bytes or digest mismatch')
        if body != dict(expected.body):
            raise IntegrityRejected('synthetic expected context mismatch; no Host authentication claimed')
        for kind, identity in [('Goal', body['goal_id']), ('Task', body['task_id'])]:
            subject = db.execute('SELECT fixture_only,body FROM domain_objects WHERE project=? AND kind=? AND id=?', (project, kind, identity)).fetchone()
            if subject is None or subject['fixture_only'] != 1:
                raise IntegrityRejected('fake canonical subject missing')
            subject_body = strict_json(subject['body'])
            if subject_body.get('project') != project or subject_body.get('kind') != kind or subject_body.get('id') != identity or kind == 'Task' and subject_body.get('goal_id') != body['goal_id']:
                raise IntegrityRejected('fake canonical subject relation mismatch')
        return {'classification': 'INTEGRITY_FIXTURE_ONLY', 'binding_hash': digest,
                'body': MappingProxyType(body), 'authenticated': False, 'business_acceptance': False}

    def restore_integrity(self, db, expected_records):
        self.validate_schema(db)
        actual = {(row[0], row[1]) for row in db.execute('SELECT project,task_id FROM coding_delivery_bindings')}
        if actual != set(expected_records):
            raise IntegrityRejected('complete restored binding inventory mismatch')
        return [self.consume(db, project, task, expected_records[(project, task)]) for project, task in sorted(actual)]
