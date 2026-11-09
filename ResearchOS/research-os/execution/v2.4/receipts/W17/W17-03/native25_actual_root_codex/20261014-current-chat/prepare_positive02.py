"""Prepare public, isolated Native25 case configuration; start no process/signing."""
import hashlib,json,sys,types
from pathlib import Path
sys.dont_write_bytecode=True
R=Path('D:/作品集/ResearchOS/research-os');E=R/'execution/v2.4/receipts/W17/W17-03';B=R/'execution/v2.4/receipts/W05/W05-99';O=Path(__file__).parent
P=O/'positive-replay-02';S=R/'.local/native25-cases-20261014/positive-replay-02';C=E/'native25_test_compilation_codex/20261014-current-chat';A=E/'schema24_to25_source_codex/20261014-current-chat'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
 p=Path(p).resolve();raw=p.read_bytes();return {'path':str(p),'sha256':'sha256:'+hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def verify(v):
 actual=ref(v['path']);assert actual['sha256']==v['sha256'] if v['sha256'].startswith('sha256:') else actual['sha256']=='sha256:'+v['sha256'];assert actual['bytes']==v['bytes'];return actual
def new(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
 return ref(p)
def module(p):
 m=types.ModuleType('native25_prepare_'+p.stem);m.__file__=str(p);sys.modules[m.__name__]=m;exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
review=E/'native25_controller_independent_review_codex/20261014-current-chat/FINAL-report.json'
assert ref(review)['sha256']=='sha256:caa3edc2bea093a3d714b5bac35dde543b4b44ad94b4a4ae39b6950c57bddda4'
closed=read(C/'compilation.closed.json');assert closed['state']=='FIXED_SOURCE_TEST_BINARY_BUILT_NATIVE_NOT_RUN' and closed['all_guards_closed']
controller=E/'native25_controller_adaptation_codex/20261014-current-chat/root_native_pause_migration_controller.py';assert ref(controller)['sha256']=='sha256:c95ed27b644368fd846bd5ddbd4fc8268cbfea65eb2a8165691456e707a221fa'
cfg=read(A/'revision01/public-handoff04.config.json')
P.mkdir(exist_ok=False);S.mkdir(parents=True,exist_ok=False)
for name in ['programs','temp']:(S/name).mkdir()
for key in ['RootProgram','ControlProgram','BackupProgram','EnrollmentProgram']:
 old=verify(cfg[key]);dest=S/'programs'/Path(old['path']).name
 with dest.open('xb') as f:f.write(Path(old['path']).read_bytes())
 actual=ref(dest);assert actual['sha256']==old['sha256'] and actual['bytes']==old['bytes'];cfg[key]={'role':cfg[key]['role'],**actual}
cfg.update(Case='positive-replay',CaseID='root-positive-replay-02',OutputDirectory=str((P/'harness').resolve()))
harness=new(P/'harness.public.config.json',cfg)
gp=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
hp=B/'integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py'
op=B/'native_migration_atomic_publication_revision_codex/1a11d9c912f7c13799a37e93/windows_owned_observed.py'
assert ref(gp)['sha256']=='sha256:e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
assert ref(hp)['sha256']=='sha256:6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad'
assert ref(op)['sha256']=='sha256:fe102f02de5aa966945ef88218e412f1988509168705d03a8660dab8b282d4e3'
ctl=module(controller);module(gp);module(op);helper=module(hp)
inventory=read(C/'actual-test-compiler-input-inventory.json');frozen={}
def add(v):
 actual=verify(v);key=actual['path'].casefold()
 assert key not in frozen or frozen[key]==actual;frozen[key]=actual
for v in inventory['build_inputs']+inventory['product_inventory']+inventory['compiler_tool_refs']+[inventory['GoRef']]:add(v)
for path in [A/'source24-build-inputs/compiler-inputs.json',A/'revision01/target25-r4-build-inputs/compiler-inputs.json']:
 add(ref(path))
 for v in read(path)['inputs']:add(v)
# Old24 release contracts/DDL are live inputs to the fixture, in addition to its
# frozen old24 compiler inventory and old producer binary.
oldroot=Path(cfg['SourceReleaseRoot'])
for relative in ['spec/v2.0/contracts','migrations/sqlite']:
 for p in (oldroot/relative).rglob('*'):
  assert not p.is_symlink()
  if p.is_file():add(ref(p))
env={'SystemRoot':'C:\\Windows','WINDIR':'C:\\Windows','ComSpec':'C:\\Windows\\System32\\cmd.exe','PATH':'C:\\Windows\\System32','PATHEXT':'.COM;.EXE;.BAT;.CMD','TEMP':str(S/'temp'),'TMP':str(S/'temp'),'RESEARCHOS_NATIVE_MIGRATION_HARNESS_TEMP_ROOT':str(S/'temp')}
public={'Schema':'researchos.root-native-pause-migration-controller.v1','ControllerDirectory':str((P/'controller').resolve()),'ControllerSource':ref(controller),'HarnessConfig':harness,'TestProgram':verify(closed['test_program_ref']),'ObservedOwnedHelper':ref(op),'OriginalOwnedHelper':ref(hp),'SourceReadGuard':ref(gp),'CompilerInventory':ref(C/'actual-test-compiler-input-inventory.json'),'BuildInvocation':ref(C/'test-binary-compile.invocation.json'),'Environment':env}
for value in public.values():
 if isinstance(value,dict) and set(value)=={'path','sha256','bytes'}:add(value)
for key in ['SourceBackupProgram','RootProgram','ControlProgram','BackupProgram','EnrollmentProgram','PythonProgram','BrokerSource','PrivateStdinHelper']:add(cfg[key])
for path in helper.runtime_resource_paths():add(ref(path))
# Native system DLL loaded after actual child creation, independently verified v2 pin.
add(ref(Path('C:/Windows/System32/kernel.appcore.dll')))
caller_source=O/'root_concrete_operation_v2.template.py'
caller=P/'root_concrete_operation.py'
with caller.open('xb') as f:f.write(caller_source.read_bytes())
add(ref(caller_source));add(ref(caller))
for path in [review,C/'compilation.closed.json',Path(__file__)]:add(ref(path))
public['FrozenInputs']=list(frozen.values());config=new(P/'controller.public.config.json',public)
# This validates fixed public config and imports reviewed helpers only; it does
# not call serve/sign_reviewed/publish_signed or touch a private resource.
context=ctl.context(config)
new(P/'configuration.prepared.json',{'state':'PUBLIC_CONFIG_VERIFIED_NO_PROCESS_STARTED','config_ref':config,'harness_ref':harness,'source_head':closed['source_head'],'controller_review_ref':ref(review),'frozen_input_count':len(frozen),'frozen_input_bytes':sum(v['bytes'] for v in frozen.values()),'all_fixed_signed_names_absent':all(not (S/'programs'/n).exists() for n in ['recovery-release.json','current-schema24-to25-grant.json','consumed-schema24-to25-grants']),'original_database_touched':False,'private_resources_read':False,'signatures_created':0,'formal_increment':0})
print(json.dumps({'config_ref':config,'frozen_inputs':len(frozen),'children_started':0,'signatures_created':0}))
