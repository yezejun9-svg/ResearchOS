"""Independent C-only frozen source and fresh-fixture checks; never product authority."""
from pathlib import Path
import datetime, hashlib, json, os, subprocess, sys, unittest

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reviews' / 'run-01'
OUT.mkdir(parents=True, exist_ok=False)
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def put(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
manifest_path = ROOT / 'evidence/attempt-01/source-manifest.json'
assert sha(manifest_path) == '3d3c766d174c4580658c8366225aeede36525a5ca6b1cf1e444b2813bf7f634d'
manifest = json.loads(manifest_path.read_bytes())
def sources_match():
    return all(sha(ROOT / f['path']) == f['sha256'] and (ROOT / f['path']).stat().st_size == f['bytes'] for f in manifest['files'])
assert sources_match()
tools = json.loads((ROOT / 'evidence/attempt-01/inputs.json').read_bytes())['tools']
for name in ('go', 'python'):
    assert sha(tools[name]['path']) == tools[name]['sha256']
assert Path(sys.executable).resolve() == Path(tools['python']['path']).resolve()
private = OUT / 'private'
overrides = {}
for name, relative in {'GOCACHE':'go-cache','GOPATH':'gopath','GOMODCACHE':'gopath/pkg/mod','GOTMPDIR':'go-tmp','TEMP':'tmp','TMP':'tmp','USERPROFILE':'profile','APPDATA':'profile/AppData/Roaming','LOCALAPPDATA':'profile/AppData/Local'}.items():
    path = private / relative
    path.mkdir(parents=True, exist_ok=True)
    overrides[name] = str(path)
overrides.update(GOROOT=str(Path(tools['go']['path']).parent.parent), GOPROXY='off', GOSUMDB='off', GOENV='off', GOTOOLCHAIN='local', GOTELEMETRY='off', GOWORK='off', GOFLAGS='-mod=readonly', GO111MODULE='on', CGO_ENABLED='0', GOCACHEPROG='', PYTHONDONTWRITEBYTECODE='1')
environment = dict(os.environ, **overrides)
os.environ.update(overrides)
put('inputs.json', {'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_manifest_sha256':sha(manifest_path),'tools':tools,'environment_overrides':overrides,'writes_scope':str(OUT),'scope':'C-only independent fixture integrity, no product auth / old database / D writes / LIVE','formal_increment':0})
results = []
for name, argv in [('go-vectors',[tools['go']['path'],'test','-count=1','-v','./cmd/canonicalhash']),('go-helper-build',[tools['go']['path'],'build','-o',str(OUT/'canonicalhash.exe'),'./cmd/canonicalhash'])]:
    put(name+'.command.json', {'argv':argv,'cwd':str(ROOT)})
    with (OUT/(name+'.stdout.txt')).open('wb') as out, (OUT/(name+'.stderr.txt')).open('wb') as err:
        process = subprocess.run(argv, cwd=ROOT, env=environment, stdout=out, stderr=err, timeout=300)
    result = {'name':name,'exit_code':process.returncode,'terminal':True}
    results.append(result); put(name+'.result.json',result)
    print(json.dumps(result),flush=True)
    if process.returncode:
        put('result.json',{'status':'INDEPENDENT_CHECK_FAILED','results':results,'source_unchanged':sources_match()})
        raise SystemExit(process.returncode)

sys.path.insert(0,str(ROOT))
import prototype as p
import test_bindings as author
canonical = p.Canonicalizer(OUT/'canonicalhash.exe',sha(OUT/'canonicalhash.exe'))
pristine=p.open_fixture();p.initialize_fixture(pristine);expected_schema=p.schema_snapshot(pristine);pristine.close()
fixtures=OUT/'fixtures';fixtures.mkdir()
def independent_setup(cls):
    cls.canonical=canonical;cls.expected_schema=expected_schema;cls.fixture_home=fixtures
author.BindingSchemaFixtureTests.setUpClass=classmethod(independent_setup)

class IndependentBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.db=p.open_fixture();p.initialize_fixture(self.db);self.addCleanup(self.db.close)
        self.consumer=p.FixtureConsumer(canonical,expected_schema)
        self.original=author.fixture_body('independent-original')
        p.put_subjects(self.db,self.original);self.db.execute(p.INSERT_SQL,p.row_for(self.original,canonical))
    def rows(self):return [tuple(row) for row in self.db.execute('SELECT * FROM coding_delivery_bindings ORDER BY project,task_id')]
    def test_new_primary_key_cannot_replace_ignore_or_upsert_qualified_identity(self):
        original=self.rows()
        for identity in ('goal','approval','lineage'):
            body=author.fixture_body('new-'+identity)
            if identity=='goal':body.update(project=self.original['project'],goal_id=self.original['goal_id'])
            if identity=='approval':body.update(approval_issuer_ref=self.original['approval_issuer_ref'],approval_ref=self.original['approval_ref'])
            if identity=='lineage':body.update(lineage_issuer_ref=self.original['lineage_issuer_ref'],business_anchor=self.original['business_anchor'])
            p.put_subjects(self.db,body);row=p.row_for(body,canonical)
            for recursive in (0,1):
                self.db.execute('PRAGMA recursive_triggers='+str(recursive))
                for sql in (p.INSERT_SQL.replace('INSERT INTO','INSERT OR REPLACE INTO',1),p.INSERT_SQL.replace('INSERT INTO','INSERT OR IGNORE INTO',1),p.INSERT_SQL+' ON CONFLICT DO NOTHING',p.INSERT_SQL+' ON CONFLICT DO UPDATE SET owner_root=excluded.owner_root'):
                    with self.subTest(identity=identity,recursive=recursive,sql=sql[-80:]):
                        with self.assertRaises(Exception) as caught:self.db.execute(sql,row)
                        self.assertIsInstance(caught.exception, __import__('sqlite3').DatabaseError)
                        self.assertEqual(self.rows(),original)
    def test_foreign_key_orphan_after_disabled_enforcement_is_refused(self):
        self.db.execute('PRAGMA foreign_keys=OFF')
        self.db.execute("DELETE FROM domain_objects WHERE kind='Goal'")
        self.db.execute('PRAGMA foreign_keys=ON')
        with self.assertRaises(p.IntegrityRejected):self.consumer.consume(self.db,self.original['project'],self.original['task_id'],p.SyntheticExpectedContext(self.original))
    def test_subject_relation_mutation_keeps_schema_but_refuses_context(self):
        self.db.execute("UPDATE domain_objects SET body=json_set(body,'$.goal_id','wrong-goal') WHERE kind='Task'")
        self.assertEqual(p.schema_snapshot(self.db),expected_schema)
        with self.assertRaises(p.IntegrityRejected):self.consumer.consume(self.db,self.original['project'],self.original['task_id'],p.SyntheticExpectedContext(self.original))
    def test_schema_valid_missing_claim_cannot_prove_approval_consumption(self):
        empty=p.open_fixture();self.addCleanup(empty.close);p.initialize_fixture(empty)
        with self.assertRaises(p.IntegrityRejected):self.consumer.consume(empty,self.original['project'],self.original['task_id'],p.SyntheticExpectedContext(self.original))
        self.assertEqual(self.consumer.restore_integrity(empty,{}),[])
        # Empty inventory is integrity-only; this API returns no permission token.
    def test_unicode_roundtrip_hash_is_actual_go_chain_and_immutable_context(self):
        body=author.fixture_body('unicode');body['owner_root']='C:/研究/😀/<>&/\u2028'
        p.put_subjects(self.db,body);self.db.execute(p.INSERT_SQL,p.row_for(body,canonical))
        context=p.SyntheticExpectedContext(body);body['owner_root']='changed-after-snapshot'
        result=self.consumer.consume(self.db,context.body['project'],context.body['task_id'],context)
        self.assertEqual(result['body']['owner_root'],'C:/研究/😀/<>&/\u2028')
        self.assertIs(result['authenticated'],False);self.assertIs(result['business_acceptance'],False)

suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(author.BindingSchemaFixtureTests),unittest.defaultTestLoader.loadTestsFromTestCase(IndependentBoundaryTests)])
with (OUT/'python-fixtures.stderr.txt').open('w',encoding='utf-8') as stream:
    checked=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
result={'name':'python-independent-fresh-fixtures','exit_code':0 if checked.wasSuccessful() else 1,'tests_run':checked.testsRun,'failures':len(checked.failures),'errors':len(checked.errors),'terminal':True}
results.append(result);put('python-fixtures.result.json',result);print(json.dumps(result),flush=True)
put('result.json',{'status':'INTEGRITY_FIXTURE_ONLY_REVIEWED' if checked.wasSuccessful() else 'INDEPENDENT_CHECK_FAILED','results':results,'source_unchanged':sources_match(),'source_manifest_sha256':sha(manifest_path),'helper_sha256':sha(OUT/'canonicalhash.exe'),'authenticated':False,'business_acceptance':False,'formal_increment':0,'D_writes':0,'old_database_connections':0,'native_model_runs':0})
raise SystemExit(0 if checked.wasSuccessful() and sources_match() else 1)
