"""Prepare a bounded fixture delta; do not modify Main or run a product."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os, difflib, types

N = Path(__file__).resolve().parent
R = Path(r'D:\作品集\ResearchOS\research-os')
O = N / 'legacy-fixture-repair-20261010-01'
AUTHOR = 'codex:/root'
GUARD = R / ('execution/v2.4/receipts/W05/W05-99/'
             'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py')

def pin(path):
    raw = Path(path).read_bytes()
    return dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))

def save(name, raw):
    path = O / name
    with path.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return pin(path)

def doc(name, value):
    return save(name, (json.dumps(value, ensure_ascii=False, indent=2)+'\n').encode())

target = R/'internal/domain/retrieval_test.go'
target_ref = pin(target)
assert target_ref['sha256'] == '518c6dbd8dbb774b88434138fd3f10f3e231843acf83f086a1ad7a381e2ffe69'
guard_ref = pin(GUARD)
assert guard_ref['sha256'] == 'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
inputs = [target_ref, pin(R/'internal/domain/backup_migration.go'),
          pin(R/'internal/domain/store.go'), pin(R/'internal/store/sqlite.go'),
          *[pin(path) for path in sorted((R/'migrations/sqlite').glob('000[1-9]_*.sql'))],
          pin(N/'w09.G02-native-failed-original1121.actual-audit.root.json')]
namespace = types.ModuleType('root_fixture_source_read_guard')
namespace.__file__ = str(GUARD)
exec(compile(GUARD.read_bytes(), str(GUARD), 'exec'), namespace.__dict__)
guard = namespace.SourceReadGuard(per_file_cap=64*1024*1024, total_cap=256*1024*1024)
closed = None
O.mkdir(exist_ok=False)
try:
    guard.acquire(inputs)
    before = target.read_bytes()
    text = before.decode('utf-8')
    begin = text.index('func TestW09LegacyRootMigrationRevokesUnidentifiedRoot(')
    tail = text[begin:]
    old_setup = '''\tlegacy, err := os.ReadFile("../../migrations/sqlite/0007_retrieval.sql")
\tif err != nil {
\t\tt.Fatal(err)
\t}
\tif _, err = db.Exec(string(legacy)); err != nil {
\t\tt.Fatal(err)
\t}
'''
    new_setup = '''\t// Build the actual contiguous pre-identity schema in this isolated unit
\t// fixture. A ledger entry is recorded only after its real SQL succeeds.
\tfor version := 2; version <= 8; version++ {
\t\tfiles, readErr := filepath.Glob(fmt.Sprintf("../../migrations/sqlite/%04d_*.sql", version))
\t\tif readErr != nil || len(files) != 1 {
\t\t\tt.Fatalf("legacy migration %d inventory: %v %v", version, files, readErr)
\t\t}
\t\traw, readErr := os.ReadFile(files[0])
\t\tif readErr != nil {
\t\t\tt.Fatal(readErr)
\t\t}
\t\tif _, err = db.Exec(string(raw)); err != nil {
\t\t\tt.Fatal(err)
\t\t}
\t\tif _, err = db.Exec("INSERT INTO schema_migrations(version) VALUES(?)", version); err != nil {
\t\t\tt.Fatal(err)
\t\t}
\t}
'''
    old_entry = '''\tif _, err = db.Exec("INSERT INTO schema_migrations(version) VALUES(7)"); err != nil {
\t\tt.Fatal(err)
\t}
\tif _, err = New(db, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql"); err != nil {
\t\tt.Fatal(err)
\t}
'''
    new_entry = '''\t// A populated old database still needs a verified pre-upgrade backup.
\t// This test observes the production refusal before testing migration 9's
\t// root-revocation SQL directly; it grants no public upgrade authority.
\tif _, err = New(db, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql"); err == nil || !strings.Contains(err.Error(), "MIGRATION_PREBACKUP_REQUIRED") {
\t\tt.Fatalf("legacy authority bypassed pre-backup gate: %v", err)
\t}
\tidentityMigration, err := os.ReadFile("../../migrations/sqlite/0009_retrieval_root_identity.sql")
\tif err != nil {
\t\tt.Fatal(err)
\t}
\tif _, err = db.Exec(string(identityMigration)); err != nil {
\t\tt.Fatal(err)
\t}
\tif _, err = db.Exec("INSERT INTO schema_migrations(version) VALUES(9)"); err != nil {
\t\tt.Fatal(err)
\t}
'''
    if '\r\n' in tail:
        old_setup = old_setup.replace('\n', '\r\n')
        new_setup = new_setup.replace('\n', '\r\n')
        old_entry = old_entry.replace('\n', '\r\n')
        new_entry = new_entry.replace('\n', '\r\n')
    # Preserve every other test, assertion ID and original expected outcome.
    assert tail.count(old_setup) == tail.count(old_entry) == 1
    candidate_tail = tail.replace(old_setup, new_setup, 1).replace(old_entry, new_entry, 1)
    after = (text[:begin]+candidate_tail).encode('utf-8')
    assert after[:begin] == before[:begin]
    assert candidate_tail[candidate_tail.index('\tvar identity string'):] == tail[tail.index('\tvar identity string'):]
    before_ref = save('retrieval_test.before.go', before)
    candidate_ref = save('retrieval_test.candidate.go', after)
    patch_ref = save('retrieval_test.patch', ''.join(difflib.unified_diff(
        text.splitlines(keepends=True), after.decode().splitlines(keepends=True),
        fromfile='a/internal/domain/retrieval_test.go',
        tofile='b/internal/domain/retrieval_test.go')).encode())
    proposal_ref = doc('proposal.json', dict(
        schema='researchos.w09-legacy-root-fixture-repair-source.v1',
        actor_id=AUTHOR, created_at=datetime.now(timezone.utc).isoformat(),
        original_failure_ordinal=1121, original_Main_ref=target_ref,
        original_copy_ref=before_ref, candidate_ref=candidate_ref, patch_ref=patch_ref,
        input_refs=inputs, source_only=True, Main_written=False,
        code_change_scope='Only the legacy migration unit fixture; production migration gates unchanged.',
        preservation=dict(all_other_tests=True, legacy_assertion_ids=True,
                          original_revocation_expectations=True,
                          gap_guard=True, prebackup_guard=True),
        independent_review='NOT_RUN_REQUIRED', actual_Go_test='NOT_RUN',
        public_upgrade='NOT_RUN', formal_acceptance=False,
        source_change_requires_current_evidence_revalidation=True))
finally:
    closed = guard.close()
    doc('source-guard.closed.json', closed)
assert closed['closed'] is True and not closed['errors'] and closed['retained_handles_count'] == 0
assert pin(target) == target_ref
print(json.dumps(dict(proposal_ref=proposal_ref, candidate_ref=candidate_ref,
                      patch_ref=patch_ref, all_guards_closed=True,
                      Main_written=False, product_called=False,
                      independent_review_required=True), ensure_ascii=False))
