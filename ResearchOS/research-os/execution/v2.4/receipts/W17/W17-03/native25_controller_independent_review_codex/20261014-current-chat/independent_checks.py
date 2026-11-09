"""Independent unsigned synthetic checks. Never calls serve or sign_reviewed.
Context module loading, Job observations, file IDs, and read guards are explicit
mocks; no Native execution, authority, signing, SQL, or private-resource proof.
"""
import ast, copy, datetime as dt, hashlib, json, os, sys, types, unittest
from pathlib import Path
from unittest.mock import patch

E = Path(__file__).resolve().parent
R = Path('D:/作品集/ResearchOS/research-os')
A = R/'execution/v2.4/receipts/W17/W17-03/native25_controller_adaptation_codex/20261014-current-chat'
W = R/'.local/worktrees/schema24-to25-native-20261014'
S = A/'root_native_pause_migration_controller.py'
c = types.ModuleType('independent_native25_controller')
c.__file__ = str(S)
exec(compile(S.read_bytes(), str(S), 'exec'), c.__dict__)
F = E/'unsigned-fixtures'
F.mkdir(exist_ok=False)
T = R/'.local/native25-controller-independent-empty-temp-20261014'
T.mkdir(exist_ok=False)

def put(p, v):
    p.write_text(json.dumps(v, ensure_ascii=True, separators=(',', ':')), encoding='utf8')
    return c.public_ref(p)

def closed():
    return {'actual_exit':0, 'job_cleanup':dict(assigned_before_resume=True,
        unnamed_exclusive_job=True, kill_on_job_close_configured=True,
        primary_exit_confirmed=True, job_idle_confirmed=True,
        active_processes_last_observed=0, handles_closed=True, errors=[])}

class Independent(unittest.TestCase):
    def test_01_all_inputs_exact_and_full_adaptation(self):
        expected = {'root_native_pause_migration_controller.py':'c95ed27b644368fd846bd5ddbd4fc8268cbfea65eb2a8165691456e707a221fa',
            'SOURCE_REPORT.json':'49b62b3b8fad2489b8d779ba22f5daee160e2d836be0d58e1ec63e98419ec3fa',
            'manifest.json':'bafd6a40f11ddc8f757abb08a21b5f906b69a97cf7c63e1b20fc11c46734ef67'}
        for name, h in expected.items():
            self.assertEqual(hashlib.sha256((A/name).read_bytes()).hexdigest(), h)
        members=json.loads((A/'manifest.json').read_bytes())['members']
        self.assertEqual(len(members),13)
        for p in members:
            raw=Path(p['path']).read_bytes()
            self.assertEqual(len(raw),p['bytes']); self.assertEqual(hashlib.sha256(raw).hexdigest(),p['sha256'])
        edits=json.loads((A/'adaptation.json').read_bytes())
        base=Path(edits['base']['path']).read_bytes()
        self.assertEqual(hashlib.sha256(base).hexdigest(),edits['base']['sha256'])
        reconstructed=base.decode()
        self.assertEqual(len(edits['changes']),14)
        for edit in edits['changes']:
            self.assertEqual(reconstructed.count(edit['before']),edit['occurrences'])
            reconstructed=reconstructed.replace(edit['before'],edit['after'])
        self.assertEqual(reconstructed.encode(),S.read_bytes())

    def test_02_actual_harness_and_signer_static_interface(self):
        harness=(W/'internal/domain/backup_pause_migration_windows_test.go').read_text()
        signer=(W/'internal/recoveryauthority/enrollment_windows.go').read_text()
        descriptor=(W/'internal/recoveryauthority/pause_migration.go').read_text()
        src=S.read_text()
        for token in ['RESEARCHOS_NATIVE_PAUSE_MIGRATION_HARNESS_CONFIG',
            'TestNativePauseMigrationAuthorityHarness','researchos.synthetic-native-pause-migration-config.v1',
            'current-schema24-to25-grant.json','consumed-schema24-to25-grants',
            'release-signed','grant-signed-and-invoke','06-release-fixture.approval.json',
            'RESEARCHOS_NATIVE_MIGRATION_HARNESS_TEMP_ROOT']:
            self.assertIn(token,harness); self.assertIn(token,src)
        for phase in c.PHASES.values():
            for name in phase: self.assertIn(name,harness)
        self.assertIn('case "pause-migration-grant":',signer)
        self.assertIn('grantFile: "current-schema24-to25-grant.json"',descriptor)
        self.assertIn('cfg.SourceBackupProgram.Path',harness)
        self.assertIn('now.Add(90 * time.Second)',harness)
        self.assertIn('time.After(time.Until(until.Add(time.Second)))',harness)
        self.assertLess(harness.index('pauseNativeSigned(t, filepath.Join(rootDir, "current-schema24-to25-grant.json")'),harness.index('time.After(time.Until(until.Add(time.Second)))'))
        nodes={n.name:n for n in ast.parse(src).body if isinstance(n,ast.FunctionDef)}
        for name in ['snapshot','context','release_fixture','publish_signed','serve']:
            body=ast.get_source_segment(src,nodes[name])
            self.assertNotIn('sign_reviewed(',body)
        body=ast.get_source_segment(src,nodes['sign_reviewed'])
        self.assertLess(body.index('.consumed.json'),body.index('.run_owned('))
        self.assertNotIn('02-grant.approval.json',body)
        self.assertIn('"harness_approval_published":False',body)

    def test_03_real_context_public_files_mock_modules(self):
        q=F/'context'; q.mkdir()
        p=q/'nonexecutable.fixture';p.write_bytes(b'unsigned inert fixture')
        pin=c.public_ref(p); raw={'role':'synthetic',**pin}
        hc={'Schema':'researchos.synthetic-native-pause-migration-config.v1','Case':'positive-replay',
            'BuildRoot':str(W),'OutputDirectory':str(q/'output')}
        for name in ['SourceBackupProgram','RootProgram','ControlProgram','BackupProgram','EnrollmentProgram','BrokerSource','PrivateStdinHelper']: hc[name]=raw
        hc['PythonProgram']={'role':'python',**c.public_ref(Path(sys.executable))}
        build={'argv':['go','test','-c','-o',str(p),'./internal/domain'], 'cwd':str(W),'actual_native_exit':0,'result':closed()}
        inv={'build_tag':'','includes_actual_test_and_embed_inputs':True,'build_inputs':[pin], 'product_inventory':[pin]}
        env={k:os.environ[k] for k in ['SystemRoot','WINDIR']}
        env.update(TEMP=str(T),TMP=str(T),RESEARCHOS_NATIVE_MIGRATION_HARNESS_TEMP_ROOT=str(T))
        def run(mutate=lambda h,b,i,e:None):
            h,b,i,e=copy.deepcopy((hc,build,inv,env));mutate(h,b,i,e)
            cfg={'Schema':'researchos.root-native-pause-migration-controller.v1','ControllerDirectory':str(q/'controller'),
                'ControllerSource':c.public_ref(S),'HarnessConfig':put(q/'hc.json',h),'TestProgram':pin,
                'CompilerInventory':put(q/'inventory.json',i),'BuildInvocation':put(q/'build.json',b),'Environment':e}
            for name in ['ObservedOwnedHelper','OriginalOwnedHelper','SourceReadGuard']:cfg[name]=pin
            allrefs=[v for v in cfg.values() if isinstance(v,dict) and set(v)=={'path','sha256','bytes'}]+[hc['PythonProgram']|{}]
            allrefs[-1]=c.from_raw_pin(allrefs[-1])
            cfg['FrozenInputs']=list({r['path']:r for r in allrefs}.values())
            with patch.object(c,'load_public_module',return_value=types.SimpleNamespace(runtime_resource_paths=lambda:[])):
                return c.context(put(q/'config.json',cfg))
        self.assertEqual(run()['hc']['Case'],'positive-replay')
        mutations=[lambda h,b,i,e:h.pop('SourceBackupProgram'),
            lambda h,b,i,e:h.update(Schema='researchos.synthetic-native-migration-config.v1'),
            lambda h,b,i,e:b['argv'].append('-tags=researchos_native_recovery_harness'),
            lambda h,b,i,e:b['argv'].remove('./internal/domain'),
            lambda h,b,i,e:i.update(build_tag='researchos_native_recovery_harness'),
            lambda h,b,i,e:i.update(includes_actual_test_and_embed_inputs=False),
            lambda h,b,i,e:b['result']['job_cleanup'].update(handles_closed=False),
            lambda h,b,i,e:e.update(TMP=str(F)),
            lambda h,b,i,e:e.pop('RESEARCHOS_NATIVE_MIGRATION_HARNESS_TEMP_ROOT')]
        for n,m in enumerate(mutations):
            with self.subTest(mutation=n),self.assertRaises((ValueError,KeyError)):run(m)
        run()

    def test_04_review_approval_time_and_bindings_with_explicit_mocks(self):
        q=F/'approval';q.mkdir();out=q/'output';out.mkdir()
        cp=put(q/'config.json',{'synthetic':True});hp=put(q/'harness.json',{'synthetic':True})
        fp=put(q/'fixture.json',{'root':str(q),'database':str(q/'nonexistent-synthetic-db')})
        def attempt(case='positive-replay',phase='grant',action='SIGN_EXACT_REVIEWED_PUBLIC_PAYLOAD',offset=-1,duration=90,alter=None,job='held-1'):
            now=dt.datetime.now(dt.timezone.utc)
            payload={'issued_utc':(now+dt.timedelta(seconds=offset)).isoformat(),'expires_utc':(now+dt.timedelta(seconds=offset+duration)).isoformat()}
            pp=put(out/c.PHASES[phase][0],payload);rp=put(out/c.PHASES[phase][1],{'synthetic':True})
            kind='release' if phase=='release' else ('grant' if case=='wrong-purpose' else 'pause-migration-grant')
            dest=str(q/c.PHASES[phase][3])
            snap={'phase':phase,'config_ref':cp,'case':case,'case_id':'fixture','harness_config_ref':hp,'ready_ref':rp,
                'payload_ref':pp,'signed_destination':dest,'sign_kind':kind,'job_binding_id':'held-1','fixture_public_ref':fp,
                'measured_native_ids':{'root':'mock-root','database':'mock-db'}}
            ap={'Schema':'researchos.root-native-concrete-approval.v1','Action':action,'ConfigSHA256':cp['sha256'],
                'Snapshot':put(q/'snapshot.json',snap),'Payload':pp,'SignedDestination':dest,'SignKind':kind}
            if action=='PUBLISH_REVIEWED_SIGNED_DOCUMENT':ap.update(SignedDocument={'synthetic':True},SigningReceipt={'synthetic':True})
            if alter:alter(ap)
            ctx={'hc':{'Case':case,'CaseID':'fixture','RootProgram':{'path':str(q/'root.fixture')}},'cfg':{'HarnessConfig':hp},'output':out}
            with patch.object(c,'context',return_value=ctx),patch.object(c,'_phase',return_value=phase),patch.object(c,'_live_observation',return_value=(None,{'job_binding_id':job})),patch.object(c,'native_file_id',side_effect=lambda p,d:'mock-root' if d else 'mock-db'):
                return c._approval(cp,put(q/'approval.json',ap),action)
        for case in c.CASES:
            self.assertEqual(attempt(case=case)[-1],'grant')
        self.assertEqual(attempt(phase='release')[-1],'release')
        self.assertEqual(attempt(case='expired-grant',action='PUBLISH_REVIEWED_SIGNED_DOCUMENT')[-1],'grant')
        bad=[dict(case='expired-grant',duration=91),dict(case='expired-grant',offset=-91),dict(offset=5),dict(duration=241),
            dict(job='different-held-job'),dict(alter=lambda a:a.update(SignKind='migration-grant')),
            dict(alter=lambda a:a.update(SignedDestination=str(q/'current-schema23-to24-grant.json'))),
            dict(action='PUBLISH_REVIEWED_SIGNED_DOCUMENT',offset=-91)]
        for kw in bad:
            with self.subTest(kw=kw),self.assertRaises(ValueError):attempt(**kw)

    def test_05_atomic_publication_and_partial_ready(self):
        q=F/'publication';q.mkdir();p=q/'new.json'
        c.write_new(p,{'synthetic':True})
        with self.assertRaises(FileExistsError):c.write_new(p,{'overwrite':True})
        self.assertEqual(json.loads(p.read_bytes()),{'synthetic':True})
        ready=q/c.PHASES['release'][1];ready.write_bytes(b'{')
        self.assertEqual(c._phase({'output':q}),'running')
        put(ready,{'synthetic':True});self.assertEqual(c._phase({'output':q}),'release')
        put(q/'06-fixture-retained.ready.json',{'synthetic':True});self.assertEqual(c._phase({'output':q}),'fixture-retained')
        with self.assertRaises(ValueError):c.decode(b'{"member":1,"member":2}')

    def test_06_strict_signed_serialization_without_signing(self):
        payload=b'{"synthetic":"unsigned"}'
        wrapper=b'{"payload":'+payload+b',"signature":"DUMMY-NOT-A-SIGNATURE"}'
        self.assertTrue(c._signed_payload_exact(wrapper,payload))
        for raw in [wrapper.replace(b':{',b': {',1),wrapper.replace(b'unsigned',b'changed'),wrapper.replace(b'DUMMY-NOT-A-SIGNATURE',b'')]:
            with self.assertRaises(ValueError):c._signed_payload_exact(raw,payload)

    def test_07_fixture_release_requires_independent_inspection(self):
        q=F/'release';q.mkdir();out=q/'out';out.mkdir();work=q/'work';work.mkdir()
        cp=put(q/'config.json',{'synthetic':True})
        sp=put(q/'snapshot.json',{'config_ref':cp,'phase':'fixture-retained','job_binding_id':'mock-held','evidence_refs':[]})
        base={'config_ref':cp,'snapshot_ref':sp,'fixture_read_complete':True,'whole_row_schema_review_complete':True,'private_credentials_recorded':False}
        def call(inspection):
            ap=put(q/'approval.json',{'Schema':'researchos.root-native-fixture-release.v1','Action':'RELEASE_AFTER_INDEPENDENT_FIXTURE_INSPECTION',
                'ConfigSHA256':cp['sha256'],'Snapshot':sp,'InspectionReceipt':put(q/'inspection.json',inspection)})
            with patch.object(c,'context',return_value={'output':out,'work':work}),patch.object(c,'_phase',return_value='fixture-retained'),patch.object(c,'_live_observation',return_value=(None,{'job_binding_id':'mock-held'})),patch.object(c,'_guard',return_value=types.SimpleNamespace(close=lambda:{'closed':True,'errors':[]})):
                return c.release_fixture(cp,ap)
        for key,val in [('fixture_read_complete',False),('whole_row_schema_review_complete',False),('private_credentials_recorded',True)]:
            with self.subTest(key=key),self.assertRaises(ValueError):call(base|{key:val})
            self.assertFalse((out/'06-release-fixture.approval.json').exists())
        call(base)
        self.assertEqual(json.loads((out/'06-release-fixture.approval.json').read_bytes()),{'Action':'release-fixture'})

if __name__=='__main__':
    try:
        suite=unittest.defaultTestLoader.loadTestsFromTestCase(Independent)
        result=unittest.TextTestRunner(verbosity=2).run(suite)
        raise SystemExit(not result.wasSuccessful())
    finally:
        T.rmdir()  # Only this empty, freshly created directory; no recursive cleanup.
