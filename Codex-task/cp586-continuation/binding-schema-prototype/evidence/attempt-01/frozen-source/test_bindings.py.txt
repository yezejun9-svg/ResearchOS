"""Fresh C/in-memory SQLite invariants; no authority or business acceptance tests."""
import copy
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest

from prototype import (
    BODY_FIELDS, DECIMAL_FIELDS, HASH_FIELDS, IDENTITY_COLUMNS, INSERT_COLUMNS, INSERT_SQL,
    ROOT, SCHEMA_NAME, Canonicalizer, FixtureConsumer, IntegrityRejected,
    SyntheticExpectedContext, initialize_fixture, open_fixture, put_subjects,
    row_for, schema_snapshot, strict_json,
)


def fake_digest(label):
    return 'sha256:' + hashlib.sha256(('FAKE-FIXTURE:' + label).encode()).hexdigest()


def fixture_body(suffix='1'):
    body = {name: 'FAKE-ref-' + name + '-' + suffix for name in BODY_FIELDS if name != 'schema_version'}
    body.update(binding_schema=SCHEMA_NAME, schema_version=1, project='project-' + suffix,
                task_id='task-' + suffix, goal_id='goal-' + suffix,
                approval_issuer_ref='FAKE-approval-issuer', approval_ref='approval-' + suffix,
                lineage_issuer_ref='FAKE-lineage-issuer', owner_principal='FAKE-owner-' + suffix,
                owner_root='FAKE-root-' + suffix, owner_host='FAKE-host-' + suffix,
                creation_method='goal.start', creation_writer_epoch='9007199254740993',
                creation_session_revision='9223372036854775807')
    for field in HASH_FIELDS:
        body[field] = fake_digest(field + '-' + suffix)
    return body


class BindingSchemaFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        manifest = json.loads((ROOT / '.local/canonical-helper.json').read_text(encoding='utf-8'))
        cls.canonical = Canonicalizer(manifest['path'], manifest['sha256'])
        pristine = open_fixture()
        initialize_fixture(pristine)
        cls.expected_schema = schema_snapshot(pristine)
        pristine.close()
        cls.fixture_home = ROOT / '.local/fixtures'
        cls.fixture_home.mkdir(parents=True, exist_ok=True)

    def setUp(self):
        self.db = open_fixture()
        initialize_fixture(self.db)
        self.addCleanup(self.db.close)
        self.consumer = FixtureConsumer(self.canonical, self.expected_schema)
        self.body = fixture_body()

    def insert(self, body=None, db=None):
        body = self.body if body is None else body
        db = self.db if db is None else db
        put_subjects(db, body)
        row = row_for(body, self.canonical)
        db.execute(INSERT_SQL, row)
        return row

    def raw_row(self, body, columns=None, body_text=None, digest=None):
        columns = self.body if columns is None else columns
        raw = json.dumps(body, ensure_ascii=False, separators=(',', ':')) if body_text is None else body_text
        return tuple(columns.get(name) for name in IDENTITY_COLUMNS) + (raw, digest or fake_digest('shape-only'))

    def binding_rows(self, db=None):
        db = self.db if db is None else db
        return [tuple(row) for row in db.execute('SELECT * FROM coding_delivery_bindings ORDER BY project,task_id')]

    def assert_sql_rejected(self, row, sql=INSERT_SQL):
        before = self.binding_rows()
        with self.assertRaises(sqlite3.DatabaseError):
            self.db.execute(sql, row)
        self.assertEqual(self.binding_rows(), before)

    def fresh_file(self, name='fixture.sqlite'):
        temporary = tempfile.TemporaryDirectory(dir=self.fixture_home)
        self.addCleanup(temporary.cleanup)
        return Path(temporary.name) / name

    def test_complete_sql_and_fake_context_match_is_not_authentication(self):
        self.insert()
        result = self.consumer.consume(self.db, self.body['project'], self.body['task_id'], SyntheticExpectedContext(self.body))
        self.assertEqual(result['classification'], 'INTEGRITY_FIXTURE_ONLY')
        self.assertFalse(result['authenticated'])
        self.assertFalse(result['business_acceptance'])
        self.assertNotIn('run_id', result['body'])
        self.assertNotIn('lease_epoch', result['body'])

    def test_required_fields_and_json_null_cannot_pass_sql_null(self):
        put_subjects(self.db, self.body)
        # These requirements are explicitly anchored to the brief, not inferred
        # only from the implementation's field list.
        for name in ['owner_principal', 'owner_root', 'owner_host', 'workspace_ref', 'profile_ref',
                     'policy_ref', 'suite_ref', 'approved_plan_ref', 'no_progress_ref',
                     'origin_problem_id', 'candidate_id', 'lineage_issuer_ref', 'business_anchor',
                     'parent_ref', 'command_id', 'request_hash', 'requirement_refs_ref', 'input_refs_ref']:
            self.assertIn(name, BODY_FIELDS)
        for name in BODY_FIELDS:
            for mode in ['missing', 'null']:
                with self.subTest(field=name, mode=mode):
                    body = copy.deepcopy(self.body)
                    if mode == 'missing':
                        del body[name]
                    else:
                        body[name] = None
                    self.assert_sql_rejected(self.raw_row(body))
        for name in IDENTITY_COLUMNS:
            with self.subTest(column=name):
                columns = dict(self.body, **{name: None})
                self.assert_sql_rejected(self.raw_row(self.body, columns))

    def test_column_body_identity_and_version_types(self):
        put_subjects(self.db, self.body)
        for name in IDENTITY_COLUMNS:
            with self.subTest(field=name):
                body = dict(self.body)
                body[name] = 2 if name == 'schema_version' else 'mismatched-' + str(body[name])
                self.assert_sql_rejected(self.raw_row(body))
        for version in [True, '1', 1.0, 9223372036854775808]:
            body = dict(self.body, schema_version=version)
            self.assert_sql_rejected(self.raw_row(body))

    def test_closed_dto_duplicate_escaped_unknown_and_case_alias_keys(self):
        put_subjects(self.db, self.body)
        raw = json.dumps(self.body, separators=(',', ':'))
        escaped = raw.replace('"project":', '"\\u0070roject":"other","project":', 1)
        duplicate = raw.replace('"project":', '"project":"other","project":', 1)
        for value in [duplicate, escaped, raw[:-1] + ',"unknown":"x"}', raw[:-1] + ',"Owner_Root":"x"}']:
            self.assert_sql_rejected(self.raw_row(self.body, body_text=value))
        for value in ['null', '[]', '{}', '{bad json}']:
            self.assert_sql_rejected(self.raw_row(self.body, body_text=value))
        for value in ['{"x":1,"x":2}', '{"x":{"y":1,"y":2}}', '{"x":NaN}']:
            with self.assertRaises(IntegrityRejected):
                strict_json(value)

    def test_hash_shapes_distinct_and_body_cannot_contain_own_hash(self):
        put_subjects(self.db, self.body)
        bad = ['0' * 64, 'sha256:' + 'A' * 64, 'sha256:' + 'g' * 64, 'sha256:' + '0' * 63, 'sha256:' + '0' * 64 + '\x00tail']
        for name in HASH_FIELDS:
            for value in bad:
                with self.subTest(field=name, value=value[:12]):
                    body = dict(self.body, **{name: value})
                    self.assert_sql_rejected(self.raw_row(body, columns=body))
        for value in bad:
            self.assert_sql_rejected(self.raw_row(self.body, digest=value))
        same = dict(self.body, goal_contract_hash=self.body['task_contract_hash'])
        self.assert_sql_rejected(self.raw_row(same, columns=same))
        body = dict(self.body, binding_hash=fake_digest('self-hash'))
        self.assert_sql_rejected(self.raw_row(body))

    def test_creation_int64_decimal_strings_exact_no_fake_runtime_epoch(self):
        for index, value in enumerate(['1', '9007199254740993', '9223372036854775807']):
            body = fixture_body('large-' + str(index))
            for name in DECIMAL_FIELDS:
                body[name] = value
            self.insert(body)
            result = self.consumer.consume(self.db, body['project'], body['task_id'], SyntheticExpectedContext(body))
            self.assertEqual(result['body']['creation_writer_epoch'], value)
        put_subjects(self.db, self.body)
        for name in DECIMAL_FIELDS:
            for value in ['0', '01', '+1', '-1', ' 1', '1.0', '9223372036854775808', '99999999999999999999', 1, 9223372036854775808]:
                body = dict(self.body, **{name: value})
                self.assert_sql_rejected(self.raw_row(body))
        for name in ['run_id', 'run_epoch', 'lease_epoch']:
            self.assert_sql_rejected(self.raw_row(dict(self.body, **{name: 'invented'})))

    def test_primary_goal_approval_and_lineage_uniqueness_cross_principal(self):
        self.insert()
        variants = {}
        variants['Task'] = dict(fixture_body('task-conflict'), project=self.body['project'], task_id=self.body['task_id'], goal_id=self.body['goal_id'])
        variants['Goal'] = dict(fixture_body('goal-conflict'), project=self.body['project'], goal_id=self.body['goal_id'])
        variants['approval-global'] = dict(fixture_body('approval-conflict'), approval_issuer_ref=self.body['approval_issuer_ref'], approval_ref=self.body['approval_ref'])
        variants['lineage-global'] = dict(fixture_body('lineage-conflict'), lineage_issuer_ref=self.body['lineage_issuer_ref'], business_anchor=self.body['business_anchor'])
        for name, body in variants.items():
            with self.subTest(identity=name):
                self.assertNotEqual(body['owner_principal'], self.body['owner_principal'])
                put_subjects(self.db, body)
                self.assert_sql_rejected(row_for(body, self.canonical))
        self.assertEqual(len(self.binding_rows()), 1)

    def test_given_business_anchor_survives_project_root_approval_renaming(self):
        self.insert()
        body = fixture_body('new-project-root-goal-task-approval')
        body['lineage_issuer_ref'] = self.body['lineage_issuer_ref']
        body['business_anchor'] = self.body['business_anchor']
        put_subjects(self.db, body)
        self.assert_sql_rejected(row_for(body, self.canonical))

    def test_issuer_qualification_and_database_scope_are_explicit_limits(self):
        self.insert()
        other = fixture_body('different-issuer')
        other['approval_ref'] = self.body['approval_ref']
        other['approval_issuer_ref'] = 'DIFFERENT-FAKE-ISSUER'
        self.insert(other)
        # A separate DB can hold the same rows. SQL is not a global native scope
        # journal, and changing a claimed issuer is not authenticated here.
        separate = open_fixture()
        self.addCleanup(separate.close)
        initialize_fixture(separate)
        self.insert(self.body, separate)
        self.assertEqual(separate.execute('SELECT count(*) FROM coding_delivery_bindings').fetchone()[0], 1)

    def test_update_delete_noop_and_all_conflict_forms_preserve_bytes(self):
        row = self.insert()
        original = self.binding_rows()
        for recursive in [0, 1]:
            self.db.execute('PRAGMA recursive_triggers=' + str(recursive))
            for sql, values in [
                ('UPDATE coding_delivery_bindings SET owner_root=owner_root', ()),
                ('UPDATE coding_delivery_bindings SET binding_hash=?', (fake_digest('tampered'),)),
                ('DELETE FROM coding_delivery_bindings', ()),
                (INSERT_SQL.replace('INSERT INTO', 'INSERT OR REPLACE INTO', 1), row),
                (INSERT_SQL.replace('INSERT INTO', 'INSERT OR IGNORE INTO', 1), row),
                (INSERT_SQL + ' ON CONFLICT(project,task_id) DO NOTHING', row),
                (INSERT_SQL + ' ON CONFLICT(project,task_id) DO UPDATE SET binding_hash=excluded.binding_hash', row),
            ]:
                with self.subTest(recursive=recursive, sql=sql[:60]):
                    self.assert_sql_rejected(values, sql)
                    self.assertEqual(self.binding_rows(), original)

    def test_fk_subjects_and_same_goal_task_relation(self):
        row = row_for(self.body, self.canonical)
        self.assert_sql_rejected(row)
        put_subjects(self.db, self.body)
        self.db.execute("UPDATE domain_objects SET body=json_set(body,'$.goal_id','foreign-goal') WHERE kind='Task'")
        self.assert_sql_rejected(row)
        self.db.execute("UPDATE domain_objects SET body=json_set(body,'$.goal_id',?) WHERE kind='Task'", (self.body['goal_id'],))
        self.db.execute(INSERT_SQL, row)
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("DELETE FROM domain_objects WHERE kind='Goal'")

    def test_transaction_rollback_has_no_orphan_objects_or_claim(self):
        self.db.execute('BEGIN')
        self.insert()
        self.db.execute('ROLLBACK')
        self.assertEqual(self.db.execute('SELECT count(*) FROM domain_objects').fetchone()[0], 0)
        self.assertEqual(self.binding_rows(), [])
        # This demonstrates only SQL rollback, never that a native approval can
        # be used again or that an external UNKNOWN action is undone.
        self.db.execute('BEGIN')
        put_subjects(self.db, self.body)
        invalid = dict(self.body, suite_ref='')
        with self.assertRaises(sqlite3.DatabaseError):
            self.db.execute(INSERT_SQL, self.raw_row(invalid))
        self.db.execute('ROLLBACK')
        self.assertEqual(self.db.execute('SELECT count(*) FROM domain_objects').fetchone()[0], 0)
        self.assertEqual(self.binding_rows(), [])

    def test_two_connections_only_one_approval_commits(self):
        path = self.fresh_file()
        setup = open_fixture(path)
        initialize_fixture(setup)
        bodies = [fixture_body('race-a'), fixture_body('race-b')]
        bodies[1]['approval_issuer_ref'] = bodies[0]['approval_issuer_ref']
        bodies[1]['approval_ref'] = bodies[0]['approval_ref']
        for body in bodies:
            put_subjects(setup, body)
        rows = [row_for(body, self.canonical) for body in bodies]
        setup.close()
        barrier = threading.Barrier(2)
        outcomes = []
        def write(row):
            db = open_fixture(path, restored=True)
            try:
                barrier.wait(timeout=5)
                db.execute('BEGIN IMMEDIATE')
                db.execute(INSERT_SQL, row)
                db.execute('COMMIT')
                outcomes.append('committed')
            except sqlite3.IntegrityError:
                if db.in_transaction:
                    db.execute('ROLLBACK')
                outcomes.append('refused')
            finally:
                db.close()
        threads = [threading.Thread(target=write, args=(row,)) for row in rows]
        for thread in threads: thread.start()
        for thread in threads: thread.join(timeout=15)
        self.assertTrue(all(not thread.is_alive() for thread in threads))
        self.assertEqual(sorted(outcomes), ['committed', 'refused'])
        check = open_fixture(path, restored=True)
        self.addCleanup(check.close)
        self.assertEqual(check.execute('SELECT count(*) FROM coding_delivery_bindings').fetchone()[0], 1)

    def test_backup_restore_complete_schema_rows_and_fake_context(self):
        self.insert()
        path = self.fresh_file('restored.sqlite')
        restored = open_fixture(path)
        self.addCleanup(restored.close)
        self.db.backup(restored)
        records = {(self.body['project'], self.body['task_id']): SyntheticExpectedContext(self.body)}
        result = self.consumer.restore_integrity(restored, records)
        self.assertEqual(len(result), 1)
        self.assertEqual(schema_snapshot(restored), self.expected_schema)
        self.assertFalse(result[0]['authenticated'])

    def test_restore_missing_trigger_index_table_or_inventory_refuses(self):
        self.insert()
        for sql in [
            'DROP TRIGGER coding_delivery_no_update',
            'DROP INDEX coding_delivery_lineage_unique',
            'DROP TABLE coding_delivery_bindings; CREATE TABLE coding_delivery_bindings(project TEXT,task_id TEXT)',
        ]:
            with self.subTest(sql=sql):
                restored = open_fixture()
                try:
                    self.db.backup(restored)
                    restored.executescript(sql)
                    with self.assertRaises(IntegrityRejected):
                        self.consumer.validate_schema(restored)
                finally:
                    restored.close()
        empty = open_fixture()
        self.addCleanup(empty.close)
        initialize_fixture(empty)
        with self.assertRaises(IntegrityRejected):
            self.consumer.restore_integrity(empty, {(self.body['project'], self.body['task_id']): SyntheticExpectedContext(self.body)})
        with self.assertRaises(IntegrityRejected):
            self.consumer.restore_integrity(self.db, {})

    def test_valid_shape_corrupt_digest_stores_but_consumer_and_restore_refuse(self):
        put_subjects(self.db, self.body)
        row = list(row_for(self.body, self.canonical))
        row[-1] = fake_digest('not-the-actual-body-digest')
        self.db.execute(INSERT_SQL, row)  # SQL proves shape, not SHA correctness.
        with self.assertRaises(IntegrityRejected):
            self.consumer.consume(self.db, self.body['project'], self.body['task_id'], SyntheticExpectedContext(self.body))
        restored = open_fixture()
        self.addCleanup(restored.close)
        self.db.backup(restored)
        with self.assertRaises(IntegrityRejected):
            self.consumer.restore_integrity(restored, {(self.body['project'], self.body['task_id']): SyntheticExpectedContext(self.body)})

    def test_correct_hash_with_foreign_owner_root_host_profile_suite_contract_refuses_context(self):
        self.insert()
        for field in ['owner_principal', 'owner_root', 'owner_host', 'profile_ref', 'suite_ref', 'workspace_ref', 'approved_plan_ref', 'no_progress_ref']:
            expected = dict(self.body, **{field: 'FOREIGN-' + self.body[field]})
            with self.subTest(field=field), self.assertRaises(IntegrityRejected):
                self.consumer.consume(self.db, self.body['project'], self.body['task_id'], SyntheticExpectedContext(expected))
        swapped = dict(self.body, task_contract_hash=self.body['goal_contract_hash'], goal_contract_hash=self.body['task_contract_hash'])
        with self.assertRaises(IntegrityRejected):
            self.consumer.consume(self.db, self.body['project'], self.body['task_id'], SyntheticExpectedContext(swapped))
        with self.assertRaises(IntegrityRejected):
            self.consumer.consume(self.db, 'missing-project', 'missing-task', SyntheticExpectedContext(self.body))

    def test_consumer_strict_json_and_noncanonical_stored_bytes_refuse(self):
        put_subjects(self.db, self.body)
        row = list(row_for(self.body, self.canonical))
        row[-2] = json.dumps(self.body, ensure_ascii=False, indent=2)
        self.db.execute(INSERT_SQL, row)
        with self.assertRaises(IntegrityRejected):
            self.consumer.consume(self.db, self.body['project'], self.body['task_id'], SyntheticExpectedContext(self.body))
        for raw in [b'{"a":1,"a":2}', b'{"a":1,"\\u0061":2}', b'{"a":"\\ud800"}', b'{"x":1e999}']:
            with self.assertRaises(IntegrityRejected):
                self.canonical.raw(raw)


if __name__ == '__main__':
    unittest.main(verbosity=2)
