"""Exact-case authorized independent observer. No signing/approval/fixture release."""
import hashlib,json,os,subprocess,sys,time,traceback,types
from pathlib import Path
E=Path(__file__).resolve().parent
P=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W17/W17-03/native25_actual_root_codex/20261014-current-chat/missing-native-channel-05')
CONFIG=P/'controller.public.config.json';CONFIG_SHA='sha256:2d17ae23c832ba615a6bf2c8f36d7a024096dc687b6b4cd1aa8a191d0fe890ae'
HELPER=E.parent/'review_negative_v2.py';HELPER_SHA='sha256:67d2a0a18c13d3d4d464ae3c643e46b91cc77349049e635fb09254549057f1a9'
def ref(p):
 p=Path(p);b=p.read_bytes();return {'path':str(p.resolve()),'sha256':'sha256:'+hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def read(p):return json.loads(Path(p).read_bytes())
def new(p,v):
 with Path(p).open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=True,indent=2);f.write('\n')
def emit(v):print(json.dumps(v,ensure_ascii=True),flush=True)
assert ref(CONFIG)['sha256']==CONFIG_SHA and ref(CONFIG)['bytes']==1155756
assert ref(HELPER)['sha256']==HELPER_SHA
cfg=read(CONFIG);hc=read(cfg['HarnessConfig']['path']);assert hc['Case']=='missing-native-channel' and hc['CaseID']=='root-missing-native-channel-05'
assert cfg['ControllerSource']['sha256']=='sha256:c95ed27b644368fd846bd5ddbd4fc8268cbfea65eb2a8165691456e707a221fa'
assert ref(cfg['ControllerSource']['path'])['sha256']==cfg['ControllerSource']['sha256']
C=Path(cfg['ControllerDirectory']);H=Path(hc['OutputDirectory']);TEMP=Path(cfg['Environment']['TEMP']);assert C.parent==P and H.parent==P
assert TEMP.parts[-2:] == ('missing-native-channel-05','temp')
controller=types.ModuleType('independent_case05_public_snapshot');controller.__file__=cfg['ControllerSource']['path'];sys.modules[controller.__name__]=controller
exec(compile(Path(controller.__file__).read_bytes(),controller.__file__,'exec'),controller.__dict__)
config_ref={'path':str(CONFIG),'sha256':CONFIG_SHA,'bytes':1155756}
baseline=E/'release-01-root-invoked-independent-checker/report.json'
started=time.monotonic();max_seconds=1500;counter=0;archived=False;terminal=None;closure=None;failed=False
ready={'state':'INDEPENDENT_OBSERVER_ARMED','pid':os.getpid(),'config_ref':config_ref,'observer_ref':ref(__file__),'checker_ref':ref(HELPER),'max_duration_seconds':max_seconds,'root_authority_actions':0,'watch_paths':[str(H/'02-grant.ready.json'),str(H/'05-case.result.json'),str(H/'06-fixture-retained.ready.json'),str(C/'controller.closed.json')],'baseline_operator':'ROOT_INVOKED_CHECKER','terminal_operator':'INDEPENDENT_REVIEW_AGENT_OBSERVER','authorized_external_write_scope':str(P/'public-retained-inputs')}
new(E/'observer.armed.json',ready);emit(ready)
def archive_public():
 ready=read(H/'02-grant.ready.json');payload=H/'02-grant.payload.json';assert ref(payload)['sha256']==ready['payload_sha256'];g=read(payload)
 assert ready['synthetic_case']=='missing-native-channel' and g['purpose']=='RESEARCHOS_RUNTIME_PAUSE_SCHEMA24_TO25_V1'
 chosen={str(Path(p['path'])):p for p in g['pins'] if Path(p['path']).is_relative_to(TEMP)};assert len(chosen)==5
 roles={p['role'] for p in chosen.values()}
 assert roles=={'encrypted-backup-manifest','isolated-restore-rehearsal','encrypted-backup-payload:command-queue.json.enc','encrypted-backup-payload:portable.json.enc','encrypted-backup-payload:state.sqlite.enc'}
 dest=P/'public-retained-inputs';dest.mkdir(exist_ok=False);mapping=[]
 for i,(name,pin) in enumerate(sorted(chosen.items()),1):
  src=Path(name);assert src.is_file() and not src.is_symlink() and src.resolve()==src and src.suffix.casefold() not in {'.key','.dpapi','.sqlite','.db'}
  assert src.name in {'manifest.json','runtime-pause-schema-rehearsal.json','command-queue.json.enc','portable.json.enc','state.sqlite.enc'}
  before=ref(src);assert before['sha256']==pin['sha256'] and before['bytes']==pin['bytes']
  out=dest/(str(i).zfill(3)+'-'+src.name)
  with out.open('xb') as f:f.write(src.read_bytes())
  after=ref(src);saved=ref(out);assert before==after and saved['sha256']==before['sha256'] and saved['bytes']==before['bytes']
  mapping.append({'original_ref':before,'archived_ref':saved})
 receipt={'schema':'researchos.public-native-input-retention/1','case':'missing-native-channel-05','copied_files':5,'public_refs_only':True,'private_key_or_database_read':False,'mapping':mapping,'operator':'INDEPENDENT_REVIEW_AGENT_OBSERVER','observer_ref':ref(__file__)}
 new(dest/'retention.json',receipt);new(E/'observer.archive.json',{'state':'FIVE_PUBLIC_TEMP_INPUTS_ARCHIVED','retention_ref':ref(dest/'retention.json'),'no_private_or_database_copy':True});emit({'event':'PUBLIC_ARCHIVE_COMPLETE','retention_ref':ref(dest/'retention.json')})
def run_checker(stage,snapshot,attempt):
 argv=[sys.executable,'-B','-X','utf8',str(HELPER),'--stage',stage,'--config',str(CONFIG),'--config-sha256',CONFIG_SHA,'--snapshot',snapshot['path'],'--snapshot-sha256',snapshot['sha256'],'--attempt',attempt]
 if stage=='terminal':argv+=['--baseline-report',str(baseline)]
 else:argv+=['--terminal-report',terminal['report_ref']['path']]
 start=time.monotonic();proc=subprocess.run(argv,capture_output=True,timeout=90)
 (E/('observer-'+stage+'.stdout.raw.json')).write_bytes(proc.stdout);(E/('observer-'+stage+'.stderr.raw.txt')).write_bytes(proc.stderr)
 new(E/('observer-'+stage+'.invocation.json'),{'argv':argv,'actual_exit':proc.returncode,'elapsed_seconds':time.monotonic()-start,'operator':'INDEPENDENT_REVIEW_AGENT_OBSERVER','checker_ref':ref(HELPER),'snapshot_ref':snapshot,'root_authority_actions':0})
 value=json.loads(proc.stdout);assert proc.returncode==0 and value['state']=='PASS','independent checker failed; original stdout/stderr/report preserved'
 return value
try:
 while time.monotonic()-started<max_seconds:
  if (C/'controller.closed.json').is_file():
   if terminal is not None:
    closure=run_checker('closure',ref(C/'controller.closed.json'),'01-independent-observer');emit({'event':'INDEPENDENT_CLOSURE_PASS',**closure})
   else:
    failed=True;new(E/'observer.closed-before-terminal.json',{'state':'NO_FRESH_TERMINAL_ACCEPTANCE','controller_closed_ref':ref(C/'controller.closed.json')});emit({'event':'CLOSED_BEFORE_TERMINAL','accepted':False})
   break
  if not archived and (H/'02-grant.ready.json').is_file():
   archive_public();archived=True
  if terminal is None and (H/'05-case.result.json').is_file() and (H/'06-fixture-retained.ready.json').is_file() and baseline.is_file():
   assert archived,'terminal reached without required public archive'
   # Explicitly authorized exact-case public observation/snapshot, never approval.
   snap=controller.snapshot(config_ref);new(E/'observer.terminal-snapshot.json',{'snapshot_ref':snap,'operator':'INDEPENDENT_REVIEW_AGENT_OBSERVER','root_authority_actions':0})
   terminal=run_checker('terminal',snap,'01-independent-observer');new(E/'observer.terminal-pass.json',{'state':'INDEPENDENT_FRESH_TERMINAL_PASS','result':terminal,'baseline_operator':'ROOT_INVOKED_CHECKER','terminal_operator':'INDEPENDENT_REVIEW_AGENT_OBSERVER','root_authority_actions':0});emit({'event':'INDEPENDENT_TERMINAL_PASS',**terminal})
  time.sleep(0.25)
 else:
  failed=True;emit({'event':'OBSERVER_DEADLINE','accepted':False})
except BaseException as exc:
 failed=True;(E/'observer.failure.traceback.raw.txt').write_text(traceback.format_exc(),encoding='utf8');new(E/'observer.failure.json',{'state':'OBSERVER_FAILED_NOT_ACCEPTED','error_type':type(exc).__name__,'error':str(exc)});emit({'event':'OBSERVER_FAILED','error_type':type(exc).__name__,'accepted':False})
finally:
 summary={'state':'OBSERVER_CLOSED','pid':os.getpid(),'elapsed_seconds':time.monotonic()-started,'public_inputs_archived':archived,'terminal_result':terminal,'closure_result':closure,'failed':failed,'root_authority_actions':0,'formal_increment':0,'inner_native_job_id_independently_observed':False}
 new(E/'observer.closed.json',summary);emit(summary)
raise SystemExit(1 if failed else 0)
