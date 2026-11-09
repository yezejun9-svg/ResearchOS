import sys
sys.dont_write_bytecode=True
from pathlib import Path
import hashlib,json,re,difflib,ast
from collections import Counter
Q=Path(__file__).parent
T=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-native-harness43-d74319468b584322b516e3b8b3aee4f2')
resources=json.loads((Q/'migration-resources.json').read_text(encoding='utf-8'))
if not resources['migration_prefix_matches_real_historical_source']:raise RuntimeError('no genuine historical migration prefix')
def pin(p):
 raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def write(path,raw):
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('xb') as f:f.write(raw)
 return pin(path)
def replace_one(text,old,new):
 if text.count(old)!=1:raise RuntimeError('exact source replacement mismatch')
 return text.replace(old,new,1)
names=['client_session_bootstrap_test.go','retrieval_test.go']
expected=['c4fec8172b1b95fde69766833d4f384d55d3af00165884106771668fc7ba7bfe','24bab4eb24cbc8ecfb9a9bc19968908bd855f358a520be56242c5020e913e9bb']
bases={}
for name,sha in zip(names,expected):
 p=T/'internal/domain'/name
 if pin(p)['sha256']!=sha:raise RuntimeError('immutable base source differs')
 bases[name]=p.read_text(encoding='utf-8')
for row in resources['migration_sources']:
 if pin(Path(row['actual_source_ref']['path']))!=row['actual_source_ref']:raise RuntimeError('frozen numbered source drift')

helper=r'''package domain

// Synthetic migration primitive fixtures. These are not matching-program backup,
// isolated restore, historical release authority, or product upgrade acceptance.
import (
    "context"
    "database/sql"
    _ "embed"
    "fmt"
    "os"
    "path/filepath"
    "strings"
    "testing"
    "researchos.local/research-os/internal/store"
)

// Exact Git 3225a31fd25969c6a5e071a2fc686cb4a835e162 blob
// 9efc768f8f4cfb6ac31e1f88a78ad095877328af; never derived by dropping a current column.
//go:embed testdata/pretranscript-3225a31f.sql
var legacyTranscriptDDL3225 []byte

var legacyFixtureMigrationSources = []struct { filename, digest string }{
@@MIGRATION_ROWS@@
}

func legacyFixtureMigrationSQL(version int) ([]byte, error) {
    if version < 1 || version > len(legacyFixtureMigrationSources) {
        return nil, fmt.Errorf("legacy fixture migration version unavailable")
    }
    source := legacyFixtureMigrationSources[version-1]
    raw, err := os.ReadFile(filepath.Join("../../migrations/sqlite", source.filename))
    if err != nil { return nil, err }
    if Digest(raw) != source.digest {
        return nil, fmt.Errorf("legacy fixture migration source pin differs")
    }
    return raw, nil
}

func legacyFixtureMigrationFiles() []string {
    files := make([]string, 0, len(legacyFixtureMigrationSources))
    for _, source := range legacyFixtureMigrationSources {
        files = append(files, filepath.Join("../../migrations/sqlite", source.filename))
    }
    return files
}

// The actual historical SQL and its version row commit in the same transaction.
// No hole is filled by relabelling a current database or recording unexecuted SQL.
func applyLegacyFixtureMigration(ctx context.Context, db *sql.DB, version int, raw []byte) (sql.Result, error) {
    if version < 2 || version > len(legacyFixtureMigrationSources) || Digest(raw) != legacyFixtureMigrationSources[version-1].digest {
        return nil, fmt.Errorf("legacy fixture migration source pin differs")
    }
    applied, err := checkMigrationInventory(db, legacyFixtureMigrationFiles())
    if err != nil { return nil, err }
    if applied != version-1 {
        return nil, fmt.Errorf("legacy fixture migration is not the next contiguous version")
    }
    tx, err := db.BeginTx(ctx, nil)
    if err != nil { return nil, err }
    defer tx.Rollback()
    result, err := tx.ExecContext(ctx, string(raw))
    if err != nil { return nil, err }
    if _, err = tx.ExecContext(ctx, "INSERT INTO schema_migrations(version) VALUES(?)", version); err != nil { return nil, err }
    if err = tx.Commit(); err != nil { return nil, err }
    return result, nil
}

func applyLegacyFixtureMigrationRange(ctx context.Context, db *sql.DB, first, last int) error {
    if first < 2 || first > last || last > len(legacyFixtureMigrationSources) {
        return fmt.Errorf("legacy fixture migration range unavailable")
    }
    for version := first; version <= last; version++ {
        raw, err := legacyFixtureMigrationSQL(version)
        if err != nil { return err }
        if _, err = applyLegacyFixtureMigration(ctx, db, version, raw); err != nil { return err }
    }
    return nil
}

func legacyTranscriptFixtureDatabase(t *testing.T) (*sql.DB, error) {
    t.Helper()
    db, err := store.Open(filepath.Join(t.TempDir(), "historical20-transcript.sqlite"))
    if err != nil { return nil, err }
    t.Cleanup(func() { _ = db.Close() })
    if _, err = legacyFixtureMigrationSQL(1); err != nil { return nil, err }
    if err = store.Bootstrap(context.Background(), db, "../../migrations/sqlite/0001_bootstrap.sql"); err != nil { return nil, err }
    if err = applyLegacyFixtureMigrationRange(context.Background(), db, 2, 20); err != nil { return nil, err }
    if Digest(legacyTranscriptDDL3225) != "sha256:@@DDL_SHA@@" {
        return nil, fmt.Errorf("historical transcript DDL pin differs")
    }
    if _, err = db.Exec(string(legacyTranscriptDDL3225)); err != nil { return nil, err }
    var column int
    if err = db.QueryRow("SELECT count(*) FROM pragma_table_info('client_sessions') WHERE name='transcript_artifact_id'").Scan(&column); err != nil { return nil, err }
    if column != 0 { return nil, fmt.Errorf("historical transcript DDL already has current column") }
    return db, nil
}

// The project index is synthetic fixture data copied from the existing Project
// fixture, while all schema bytes and version rows are the genuine historical
// prefix. No authentication, credential, model, Run or runtime state is copied.
// This test uses only f.db/f.project afterward; it does not run f.s on this DB.
func useLegacyTranscriptFixture(t *testing.T, f *fixture) error {
    t.Helper()
    db, err := legacyTranscriptFixtureDatabase(t)
    if err != nil { return err }
    rows, err := f.db.Query("SELECT project,kind,id,revision,body,content_hash,immutable FROM domain_objects WHERE kind IN ('Project','ProjectProfile') AND id=? ORDER BY project,kind,id", f.project)
    if err != nil { return err }
    defer rows.Close()
    copied := 0
    for rows.Next() {
        var project, kind, id, body string
        var revision, immutable int64
        var contentHash sql.NullString
        if err = rows.Scan(&project, &kind, &id, &revision, &body, &contentHash, &immutable); err != nil { return err }
        if _, err = db.Exec("INSERT INTO domain_objects(project,kind,id,revision,body,content_hash,immutable) VALUES(?,?,?,?,?,?,?)", project, kind, id, revision, body, contentHash, immutable); err != nil { return err }
        copied++
    }
    if err = rows.Err(); err != nil { return err }
    if copied == 0 { return fmt.Errorf("historical transcript fixture lacks Project identity") }
    f.db = db
    return nil
}

// Hash all schema definitions and public synthetic fixture table values to prove
// rejected New performs no additional DDL or data mutation. Values are never logged.
func legacyFixtureFingerprint(t *testing.T, db *sql.DB) string {
    t.Helper()
    rows, err := db.Query("SELECT type,name,tbl_name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name")
    if err != nil { t.Fatal(err) }
    var schema []any
    var tables []string
    for rows.Next() {
        var typ, name, table string
        var ddl sql.NullString
        if err = rows.Scan(&typ,&name,&table,&ddl); err != nil { rows.Close(); t.Fatal(err) }
        schema = append(schema, Object{"type":typ,"name":name,"table":table,"sql":ddl})
        if typ == "table" { tables = append(tables,name) }
    }
    err = rows.Err()
    rows.Close()
    if err != nil { t.Fatal(err) }
    data := Object{}
    for _, name := range tables {
        quoted := strings.ReplaceAll(name, "\"", "\"\"")
        records, e := db.Query("SELECT * FROM \""+quoted+"\"")
        if e != nil { t.Fatal(e) }
        columns, e := records.Columns()
        if e != nil { records.Close(); t.Fatal(e) }
        values := []any{}
        for records.Next() {
            row := make([]any,len(columns))
            refs := make([]any,len(columns))
            for i := range refs { refs[i] = &row[i] }
            if e = records.Scan(refs...); e != nil { records.Close(); t.Fatal(e) }
            values = append(values,row)
        }
        e = records.Err()
        records.Close()
        if e != nil { t.Fatal(e) }
        data[name] = Object{"columns":columns,"rows":values}
    }
    return Hash(Object{"schema":schema,"data":data})
}

func legacyFixtureExpectNewRefusal(t *testing.T, db *sql.DB, code string) {
    t.Helper()
    before := legacyFixtureFingerprint(t,db)
    _, err := New(db,"../../spec/v2.0/contracts","../../migrations/sqlite/0002_domain.sql")
    if err == nil || !(err.Error() == code || strings.HasPrefix(err.Error(),code+":")) {
        t.Fatalf("ordinary startup did not preserve %s refusal: %v",code,err)
    }
    if after := legacyFixtureFingerprint(t,db); after != before {
        t.Fatal("rejected startup changed fixture schema or data")
    }
}
'''
rows='\n'.join('    {"'+r['filename']+'","sha256:'+r['actual_source_ref']['sha256']+'"},' for r in resources['migration_sources'])
helper=helper.replace('@@MIGRATION_ROWS@@',rows).replace('@@DDL_SHA@@',resources['historical_DDL_resource_ref']['sha256'])
transcript=bases[names[0]]
transcript=replace_one(transcript,'\t\t\tif _, err := f.db.Exec(' + chr(96) + 'ALTER TABLE client_sessions DROP COLUMN transcript_artifact_id' + chr(96) + '); err != nil {','\t\t\tif err := useLegacyTranscriptFixture(t, f); err != nil {')
transcript=replace_one(transcript,'\tif _, err := f.db.Exec(' + chr(96) + 'ALTER TABLE client_sessions DROP COLUMN transcript_artifact_id' + chr(96) + '); err != nil {','\tif err := useLegacyTranscriptFixture(t, f); err != nil {')
transcript += r'''

// This is explicitly current-schema corruption, not a historical upgrade fixture.
func TestClientTranscriptInstalledColumnRemovalRequiresPrebackup(t *testing.T) {
    f := contextFixture(t)
    if _, err := f.db.Exec("ALTER TABLE client_sessions DROP COLUMN transcript_artifact_id"); err != nil {
        t.Fatal(err)
    }
    legacyFixtureExpectNewRefusal(t, f.db, "MIGRATION_PREBACKUP_REQUIRED")
}
'''
retrieval=bases[names[1]]
retrieval=replace_one(retrieval,'\tlegacy, err := os.ReadFile("../../migrations/sqlite/0007_retrieval.sql")','\t// Pure frozen SQL9 migration semantics; current New correctly requires a\n\t// matching-program prebackup for populated legacy authority.\n\tif err = applyLegacyFixtureMigrationRange(context.Background(), db, 2, 6); err != nil {\n\t\tt.Fatal(err)\n\t}\n\tlegacy, err := legacyFixtureMigrationSQL(7)')
retrieval=replace_one(retrieval,'\tif _, err = db.Exec(string(legacy)); err != nil {','\tif _, err = applyLegacyFixtureMigration(context.Background(), db, 7, legacy); err != nil {')
retrieval=replace_one(retrieval,'\tif _, err = db.Exec("INSERT INTO schema_migrations(version) VALUES(7)"); err != nil {','\tif err = applyLegacyFixtureMigrationRange(context.Background(), db, 8, 8); err != nil {')
retrieval=replace_one(retrieval,'\tif _, err = New(db, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql"); err != nil {','\tif err = applyLegacyFixtureMigrationRange(context.Background(), db, 9, 9); err != nil {')
retrieval += r'''

// Preserve the old {1,7} input as an explicit rejected gap; it never reaches SQL9.
func TestW09LegacyRootMigrationRejectsGappedInventory(t *testing.T) {
    db, err := store.Open(filepath.Join(t.TempDir(), "gapped-legacy.sqlite"))
    if err != nil { t.Fatal(err) }
    defer db.Close()
    if _, err = legacyFixtureMigrationSQL(1); err != nil { t.Fatal(err) }
    if err = store.Bootstrap(context.Background(), db, "../../migrations/sqlite/0001_bootstrap.sql"); err != nil { t.Fatal(err) }
    legacy, err := legacyFixtureMigrationSQL(7)
    if err != nil { t.Fatal(err) }
    if _, err = db.Exec(string(legacy)); err != nil { t.Fatal(err) }
    if _, err = db.Exec("INSERT INTO retrieval_roots(project,id,path,revision) VALUES('legacy','old','C:/prior-root',1)"); err != nil { t.Fatal(err) }
    if _, err = db.Exec("INSERT INTO schema_migrations(version) VALUES(7)"); err != nil { t.Fatal(err) }
    legacyFixtureExpectNewRefusal(t,db,"MIGRATION_UNSUPPORTED_OR_GAPPED_VERSION")
}
'''

util=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/typed_runtime_goal_fixture_source_codex/4396cf0cc13f1f247afbd3c567b1d931/construct.py')
if pin(util)['sha256']!='a2c5178d3d1605f88acadcedcd4675c9c05cb1a7c93104c316f5cc91f6736ebc':raise RuntimeError('lexical utility pin differs')
tree=ast.parse(util.read_text(encoding='utf-8'))
nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['tokens','close_index','call_nodes','assertion_if_nodes','balanced']]
env={'re':re,'Counter':Counter}
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(util),'exec'),env)
checks=[]
for name,after in zip(names,[transcript,retrieval]):
 before=bases[name]
 bt,at=env['tokens'](before),env['tokens'](after)
 bc,ac=Counter(env['call_nodes'](bt)),Counter(env['call_nodes'](at))
 missing=list((bc-ac).elements())
 oldTests=re.findall(r'^func (Test\w+)\(',before,re.M)
 newTests=re.findall(r'^func (Test\w+)\(',after,re.M)
 preserved=all(newTests.count(n)==oldTests.count(n) for n in oldTests)
 checks.append({'name':name,'base_ref':pin(T/'internal/domain'/name),'original_Test_names':oldTests,'new_Test_names':newTests,'original_Test_names_preserved':preserved,'original_assertion_call_count':sum(bc.values()),'candidate_assertion_call_count':sum(ac.values()),'missing_original_assertion_call_nodes':missing,'balanced':env['balanced'](at)})
 if missing or not preserved:raise RuntimeError('original assertion or Test removed')
root=Q/'candidate-root/internal/domain'
members=[write(root/n,t.encode('utf-8')) for n,t in zip(names,[transcript,retrieval])]
members.append(write(root/'legacy_migration_fixture_test.go',helper.encode('utf-8')))
members.append(write(root/'testdata/pretranscript-3225a31f.sql',Path(resources['historical_DDL_resource_ref']['path']).read_bytes()))
diffs={}
for name,after in zip(names,[transcript,retrieval]):
 diff=''.join(difflib.unified_diff(bases[name].splitlines(keepends=True),after.splitlines(keepends=True),fromfile=str(T/'internal/domain'/name),tofile=str(root/name)))
 p=Q/'diffs'/(name+'.diff');write(p,diff.encode('utf-8'));diffs[name]=pin(p)
checks.append({'name':'legacy_migration_fixture_test.go','balanced':env['balanced'](env['tokens'](helper)),'no_production_Source_files':True})
out={'authority':'NONE','formal_acceptance':False,'Go_native_SQL_model_execution':None,'member_refs':members,'diff_refs':diffs,'static_checks':checks,'lexical_utility_ref':pin(util),'transcript_ordinary_status':'BLOCKED_HISTORICAL20_MATCHING_PROGRAM_BACKUP_RESTORE_UPGRADE','restored_and_transaction_primitive_status':'SOURCE_PREPARED_NOT_EXECUTED','retrieval_frozen_SQL9_status':'SOURCE_PREPARED_NOT_PRODUCT_UPGRADE'}
write(Q/'construction.json',(json.dumps(out,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
print(json.dumps({'members':members,'checks':checks,'ordinary_status':out['transcript_ordinary_status'],'production_Source_changed':0},ensure_ascii=False))
