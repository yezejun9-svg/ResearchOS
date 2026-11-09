"""Local contract fixtures only: no signer, Native migration, or product database."""
import ast,copy,datetime as dt,hashlib,importlib.util,json,os,sys,types,unittest
from pathlib import Path
from unittest.mock import patch
B=Path(__file__).parent;SOURCE=B/'root_native_pause_migration_controller.py'
spec=importlib.util.spec_from_file_location('pause_controller_under_test',SOURCE)
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
R=Path('D:/作品集/ResearchOS/research-os')
T=R/'.local/native25-controller-fixtures-20261014'
T.mkdir(exist_ok=False)
def document(path,value):
 path.write_text(json.dumps(value,ensure_ascii=False),encoding='utf8');return c.public_ref(path)
def closed():return {'actual_exit':0,'job_cleanup':{'assigned_before_resume':True,'unnamed_exclusive_job':True,'kill_on_job_close_configured':True,'primary_exit_confirmed':True,'job_idle_confirmed':True,'active_processes_last_observed':0,'handles_closed':True,'errors':[]}}
def env():return {'SystemRoot':os.environ['SystemRoot'],'WINDIR':os.environ['WINDIR'],'TEMP':str(T),'TMP':str(T),'RESEARCHOS_NATIVE_MIGRATION_HARNESS_TEMP_ROOT':str(T)}
class ControllerTests(unittest.TestCase):
 def test_exact_adaptation_inverse(self):
  a=json.loads((B/'adaptation.json').read_text());s=SOURCE.read_bytes().decode()
  self.assertEqual(hashlib.sha256(SOURCE.read_bytes()).hexdigest(),a['target']['sha256'])
  base=Path(a['base']['path']).read_bytes();self.assertEqual(hashlib.sha256(base).hexdigest(),a['base']['sha256'])
  for edit in reversed(a['changes']):
   self.assertEqual(s.count(edit['after']),edit['occurrences']);s=s.replace(edit['after'],edit['before'])
  self.assertEqual(s,base.decode());ast.parse(s)
 def test_temp_binding_and_rejections(self):
  c._require_isolated_temp_environment(env())
  for update in [{'TEMP':os.environ['SystemRoot']},{'TMP':str(T.parent)},{'RESEARCHOS_NATIVE_MIGRATION_HARNESS_TEMP_ROOT':''},{'RESEARCHOS_NATIVE_MIGRATION_HARNESS_TEMP_ROOT':str(R/'.local'),'TEMP':str(R/'.local'),'TMP':str(R/'.local')},{'RESEARCHOS_NATIVE_MIGRATION_HARNESS_TEMP_ROOT':os.environ['SystemRoot'],'TEMP':os.environ['SystemRoot'],'TMP':os.environ['SystemRoot']}]:
   with self.subTest(update=update),self.assertRaises((ValueError,KeyError)):c._require_isolated_temp_environment(env()|update)
 def test_phase_schema_and_publication(self):
  self.assertEqual(c.PHASES['grant'][3],'current-schema24-to25-grant.json')
  target=T/'publication.json';p=c.write_new(target,{'value':1});self.assertEqual(c.decode(c.read_ref(p)),{'value':1})
  with self.assertRaises(FileExistsError):c.write_new(target,{'value':2})
  self.assertEqual(c.decode(target.read_bytes()),{'value':1})
  with self.assertRaises(ValueError):c.decode(b'{"a":1,"a":2}')
 def test_closed_native_requires_every_lifecycle_fact(self):
  self.assertTrue(c._closed_native(closed()))
  for key in ['assigned_before_resume','unnamed_exclusive_job','kill_on_job_close_configured','primary_exit_confirmed','job_idle_confirmed','handles_closed']:
   value=closed();value['job_cleanup'][key]=False
   with self.subTest(key=key):self.assertFalse(c._closed_native(value))
  for key,value in [('active_processes_last_observed',1),('errors',['failure'])]:
   result=closed();result['job_cleanup'][key]=value;self.assertFalse(c._closed_native(result))
  result=closed();result['actual_exit']=None;self.assertFalse(c._closed_native(result))
 def test_context_rejects_wrong_build_schema_and_missing_producer(self):
  q=T/'context';q.mkdir();build=q/'build';build.mkdir();binary=q/'program.bin';binary.write_bytes(b'fixture-not-executable')
  pin=c.public_ref(binary);raw={'role':'fixture',**pin}
  hc={'Schema':'researchos.synthetic-native-pause-migration-config.v1','Case':'positive-replay','BuildRoot':str(build),'OutputDirectory':str(q/'output')}
  for key in ['SourceBackupProgram','RootProgram','ControlProgram','BackupProgram','EnrollmentProgram','BrokerSource','PrivateStdinHelper']:hc[key]=raw
  hc['PythonProgram']={'role':'python-program',**c.public_ref(Path(sys.executable))}
  hp=q/'harness.json';hpin=document(hp,hc)
  inv={'build_tag':'','includes_actual_test_and_embed_inputs':True,'build_inputs':[],'product_inventory':[]};ip=q/'inventory.json';ipin=document(ip,inv)
  bi={'argv':['go','test','-c','-o',str(binary),'./internal/domain'],'cwd':str(build),'actual_native_exit':0,'result':closed()};bp=q/'build.json';bpin=document(bp,bi)
  cfg={'Schema':'researchos.root-native-pause-migration-controller.v1','ControllerDirectory':str(q/'controller'),'ControllerSource':c.public_ref(SOURCE),'HarnessConfig':hpin,'TestProgram':pin,'ObservedOwnedHelper':pin,'OriginalOwnedHelper':pin,'SourceReadGuard':pin,'CompilerInventory':ipin,'BuildInvocation':bpin,'Environment':env()}
  cfgp=q/'config.json'
  def attempt(harness=None,inventory=None,invocation=None,change=None):
   v=copy.deepcopy(cfg)
   v['HarnessConfig']=document(hp,harness or hc);v['CompilerInventory']=document(ip,inventory or inv);v['BuildInvocation']=document(bp,invocation or bi)
   if change:change(v)
   refs=[x for x in v.values() if isinstance(x,dict) and set(x)=={'path','sha256','bytes'}]+[c.public_ref(Path(sys.executable))]
   v['FrozenInputs']=list({x['path']:x for x in refs}.values())
   cp=document(cfgp,v)
   with patch.object(c,'load_public_module',return_value=types.SimpleNamespace(runtime_resource_paths=lambda:[])):
    return c.context(cp)
  self.assertEqual(attempt()['hc']['Case'],'positive-replay')
  tests=[('old-controller',lambda:attempt(change=lambda v:v.update(Schema='researchos.root-native-migration-controller.v1'))),('old-harness',lambda:attempt(harness=hc|{'Schema':'researchos.synthetic-native-migration-config.v1'})),('tagged-build',lambda:attempt(invocation=bi|{'argv':bi['argv']+['-tags=researchos_native_recovery_harness']})),('wrong-package',lambda:attempt(invocation=bi|{'argv':bi['argv'][:-1]+['./ops/backup']})),('tagged-inventory',lambda:attempt(inventory=inv|{'build_tag':'researchos_native_recovery_harness'})),('missing-temp-proof',lambda:attempt(change=lambda v:v['Environment'].pop('RESEARCHOS_NATIVE_MIGRATION_HARNESS_TEMP_ROOT')))]
  missing=copy.deepcopy(hc);missing.pop('SourceBackupProgram');tests.append(('missing-old-producer',lambda:attempt(harness=missing)))
  missingclosure=copy.deepcopy(bi);missingclosure['result']['job_cleanup']['handles_closed']=False;tests.append(('unclosed-build',lambda:attempt(invocation=missingclosure)))
  for name,run in tests:
   with self.subTest(name=name),self.assertRaises((ValueError,KeyError)):run()
 def test_concrete_approval_purpose_expiry_job_and_payload_binding(self):
  q=T/'approval';q.mkdir();out=q/'output';out.mkdir();root=q/'root.exe';root.write_bytes(b'fixture-not-executable')
  config={'path':str(q/'config.json'),'sha256':'sha256:'+'1'*64,'bytes':1};harness={'path':str(q/'harness.json'),'sha256':'sha256:'+'2'*64,'bytes':1}
  fixture=document(q/'fixture.json',{'root':str(q),'database':str(q/'fixture.db')})
  now=dt.datetime.now(dt.timezone.utc);basepayload={'issued_utc':(now-dt.timedelta(seconds=1)).isoformat(),'expires_utc':(now+dt.timedelta(seconds=89)).isoformat()}
  pp=out/c.PHASES['grant'][0];ready=document(out/c.PHASES['grant'][1],{'ready':True})
  def attempt(case='positive-replay',kind='pause-migration-grant',payload=None,mutate=None,job='job1',nativeids=None):
   payloadpin=document(pp,payload or basepayload)
   ctx={'hc':{'Case':case,'CaseID':'fixture1','RootProgram':{'path':str(root)}},'cfg':{'HarnessConfig':harness},'output':out}
   dest=str(q/'current-schema24-to25-grant.json')
   snap={'phase':'grant','config_ref':config,'case':case,'case_id':'fixture1','harness_config_ref':harness,'ready_ref':ready,'payload_ref':payloadpin,'signed_destination':dest,'sign_kind':kind,'job_binding_id':'job1','fixture_public_ref':fixture,'measured_native_ids':{'root':'root1','database':'db1'}}
   sp=document(q/'snapshot.json',snap)
   a={'Schema':'researchos.root-native-concrete-approval.v1','Action':'SIGN_EXACT_REVIEWED_PUBLIC_PAYLOAD','ConfigSHA256':config['sha256'],'Snapshot':sp,'Payload':payloadpin,'SignedDestination':dest,'SignKind':kind}
   if mutate:mutate(a)
   ap=document(q/'approval.json',a)
   with patch.object(c,'context',return_value=ctx),patch.object(c,'_phase',return_value='grant'),patch.object(c,'_live_observation',return_value=(None,{'job_binding_id':job})),patch.object(c,'native_file_id',side_effect=lambda p,d:(nativeids or {}).get('root' if d else 'database','root1' if d else 'db1')):
    return c._approval(config,ap,'SIGN_EXACT_REVIEWED_PUBLIC_PAYLOAD')
  self.assertEqual(attempt()[-1],'grant');self.assertEqual(attempt(case='expired-grant')[-1],'grant');self.assertEqual(attempt(case='wrong-purpose',kind='grant')[-1],'grant')
  tests=[('old-purpose',lambda:attempt(kind='migration-grant')),('wrong-purpose-not-isolated',lambda:attempt(kind='grant')),('wrongpurpose-incorrectkind',lambda:attempt(case='wrong-purpose')),('expired-already',lambda:attempt(case='expired-grant',payload={'issued_utc':(now-dt.timedelta(seconds=91)).isoformat(),'expires_utc':(now-dt.timedelta(seconds=1)).isoformat()})),('expiry-case-too-long',lambda:attempt(case='expired-grant',payload=basepayload|{'expires_utc':(now+dt.timedelta(seconds=90)).isoformat()})),('future-issued',lambda:attempt(payload={'issued_utc':(now+dt.timedelta(seconds=1)).isoformat(),'expires_utc':(now+dt.timedelta(seconds=89)).isoformat()})),('over-four-minutes',lambda:attempt(payload=basepayload|{'expires_utc':(now+dt.timedelta(seconds=240)).isoformat()})),('wrong-job',lambda:attempt(job='job2')),('wrong-nativeid',lambda:attempt(nativeids={'database':'db2'})),('wrong-destination',lambda:attempt(mutate=lambda a:a.update(SignedDestination=str(q/'current-schema23-to24-grant.json')))),('wrong-config',lambda:attempt(mutate=lambda a:a.update(ConfigSHA256='sha256:'+'3'*64))),('wrong-action',lambda:attempt(mutate=lambda a:a.update(Action='PUBLISH_REVIEWED_SIGNED_DOCUMENT')))]
  for name,run in tests:
   with self.subTest(name=name),self.assertRaises(ValueError):run()
 def test_signed_bytes_exact(self):
  payload=b'{"purpose":"fixture"}';self.assertTrue(c._signed_payload_exact(b'{"payload":'+payload+b',"signature":"fixture-only"}',payload))
  for candidate in [b'{"payload": {"purpose":"fixture"},"signature":"fixture-only"}',b'{"payload":{"purpose":"other"},"signature":"fixture-only"}',b'{"payload":{"purpose":"fixture"},"signature":""}']:
   with self.subTest(candidate=candidate),self.assertRaises(ValueError):c._signed_payload_exact(candidate,payload)
if __name__=='__main__':unittest.main(verbosity=2)
