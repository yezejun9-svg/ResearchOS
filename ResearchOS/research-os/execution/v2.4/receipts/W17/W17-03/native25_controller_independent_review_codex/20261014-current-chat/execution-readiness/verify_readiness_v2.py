"""Read-only actual public evidence review. No tested binary, signer, or harness execution."""
import hashlib,json,os,subprocess,sys,types,datetime as dt
from pathlib import Path
sys.dont_write_bytecode=True
E=Path(__file__).resolve().parent/'revision02'
E.mkdir(exist_ok=False)
R=Path('D:/作品集/ResearchOS/research-os')
B=R/'execution/v2.4/receipts/W17/W17-03'
C=B/'native25_test_compilation_codex/20261014-current-chat'
P=B/'native25_actual_root_codex/20261014-current-chat/positive-replay-01'
A=B/'schema24_to25_source_codex/20261014-current-chat'
W=R/'.local/worktrees/schema24-to25-native-20261014'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def ref(p):
 p=Path(p);raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def verify(v):
 actual=ref(v['path']);assert actual['sha256']==v['sha256'].removeprefix('sha256:') and actual['bytes']==v['bytes'],str(v['path']);return actual
def dump(name,v):
 with (E/name).open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def key(p):return str(Path(p).resolve()).casefold()
def refs(values):return {key(v['path']):(v['sha256'].removeprefix('sha256:'),v['bytes']) for v in values}
def run(label,argv,cwd,env=None):
 result=subprocess.run(argv,cwd=cwd,env=env,capture_output=True,timeout=45)
 (E/(label+'.stdout.raw')).write_bytes(result.stdout);(E/(label+'.stderr.raw')).write_bytes(result.stderr)
 dump(label+'.invocation.json',{'argv':argv,'cwd':str(cwd),'actual_native_exit':result.returncode,'public_environment':env,
  'stdout_ref':ref(E/(label+'.stdout.raw')),'stderr_ref':ref(E/(label+'.stderr.raw')),'kind':'READ_ONLY_TOOL_METADATA_NOT_PRODUCT_EXECUTION'})
 assert result.returncode==0,(label,result.returncode)
 return result.stdout.decode('utf8').strip()

summary={'schema':'researchos.native25-actual-readiness-independent-review/1','reviewer':'codex:/root/native25_controller_review',
 'state':'IN_PROGRESS','native_harness_runs':0,'signatures_created':0,'private_resources_read':0,'product_database_reads':0,'product_database_writes':0,'formal_increment':0,'formal_accepted_cases':'0/42','parent_tasks_open':22}
try:
 expected={'actual-test-compiler-input-inventory.json':'284ff7d231c734f9cf62162300a895e4283406f4cfb1833dc50abfb2ec885acc',
  'test-binary-compile.invocation.json':'8606ed3994519300373e9ceb5ff17e0c98762c291132b0fb2ebdd5d96ca14f72'}
 for name,sha in expected.items():assert ref(C/name)['sha256']==sha
 configref=ref(P/'controller.public.config.v2.json');assert configref['sha256']=='f21d508263674ca57672fddf2db897e78ffd06b355a6512acc47738b46f2c7fc' and configref['bytes']==1155039
 cfg=read(configref['path']);harness=read(cfg['HarnessConfig']['path']);inventory=read(C/'actual-test-compiler-input-inventory.json');closed=read(C/'compilation.closed.json')
 verify(closed['test_program_ref']);assert closed['test_program_ref']['sha256']=='a3e2f46ffad34d32b7384a4694dc3338ac1ee8e546a52c1a7dbc0a1450c992ac' and closed['test_program_ref']['bytes']==43845120
 assert closed['state']=='FIXED_SOURCE_TEST_BINARY_BUILT_NATIVE_NOT_RUN' and closed['all_guards_closed'] and not closed['native_harness_executed']
 assert refs([cfg['TestProgram']])==refs([closed['test_program_ref']])
 assert run('harness-head',['git','rev-parse','HEAD'],W)=='f80955594bdd0373ae1c961cd02ab6be96f2c196'
 assert run('harness-status',['git','status','--porcelain=v1'],W)==''
 oldroot=Path(harness['SourceReleaseRoot'])
 assert run('old24-head',['git','rev-parse','HEAD'],oldroot)=='a7ec7ebf2d53848ea163b6115667b3e3761a6bd2'
 assert run('old24-status',['git','status','--porcelain=v1'],oldroot)==''
 invocations=[]
 for receipt in closed['invocations']:
  verify(receipt);v=read(receipt['path']);invocations.append(v)
  assert v['actual_native_exit']==0 and v['exception'] is None
  rr=v['result'];jj=rr['job_cleanup'];assert rr['actual_exit']==0 and rr['error'] is None and not rr['timed_out'] and rr['resumed']
  assert all(jj[k] for k in ['unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','primary_exit_confirmed','job_idle_confirmed','handles_closed'])
  assert jj['active_processes_last_observed']==0 and not jj['errors']
  verify(v['stdout_ref']);verify(v['stderr_ref'])
  env=v['public_environment']
  for name,value in {'GOENV':'off','GOTOOLCHAIN':'local','GOPROXY':'off','GOSUMDB':'off','GOWORK':'off','CGO_ENABLED':'0','GOFLAGS':'-mod=readonly -p=1'}.items():assert env[name]==value
  assert not any(x.startswith('-tags') for x in v['argv'])
  assert Path(v['cwd'])==W
 listing,build=invocations
 assert listing['argv'][1:]==['list','-test','-deps','-compiled','-json','./internal/domain']
 assert build['argv'][1:]==['test','-c','-trimpath','-buildvcs=true','-o',closed['test_program_ref']['path'],'./internal/domain']
 assert listing['public_environment']==build['public_environment']

 # Independently reconstruct the complete declared selected path set from raw Go JSON.
 text=(C/'compiler-input-list.stdout.raw').read_text(encoding='utf8');decoder=json.JSONDecoder();offset=0;packages=[];selected=set();embeds=[];mods=set()
 suffixes=['GoFiles','CgoFiles','CFiles','CXXFiles','MFiles','HFiles','FFiles','SFiles','SwigFiles','SwigCXXFiles','SysoFiles','CompiledGoFiles','TestGoFiles','XTestGoFiles','EmbedFiles','TestEmbedFiles','XTestEmbedFiles']
 while offset<len(text):
  if text[offset].isspace():offset+=1;continue
  pkg,offset=decoder.raw_decode(text,offset);packages.append(pkg)
  assert not pkg.get('Error') and not pkg.get('DepsErrors')
  for field in suffixes:
   for path in pkg.get(field,[]):
    p=Path(path)
    if not p.is_absolute():p=Path(pkg['Dir'])/p
    selected.add(key(p))
    if field.endswith('EmbedFiles'):embeds.append((pkg['ImportPath'],field,key(p)))
  module=pkg.get('Module',{})
  for mod in [module,module.get('Replace',{})]:
   if mod.get('GoMod'):mods.add(key(mod['GoMod']))
 selected|=mods
 assert selected==set(refs(inventory['build_inputs']))
 assert mods==set(refs(inventory['module_files']))
 assert embeds==[(r['package'],r['field'],key(r['ref']['path'])) for r in inventory['actual_embed_files']]
 assert [p['ImportPath'] for p in packages]==inventory['packages']
 domain=[p for p in packages if p['ImportPath']=='researchos.local/research-os/internal/domain'][0]
 assert 'backup_pause_migration_windows_test.go' in domain['TestGoFiles']
 assert any(p.get('ForTest')=='researchos.local/research-os/internal/domain' for p in packages)
 assert 'researchos.local/research-os/internal/domain.test' in inventory['packages']
 assert inventory['build_tag']=='' and inventory['includes_actual_test_and_embed_inputs']
 assert inventory['package_count']==len(packages)==352 and len(selected)==3771
 assert len(embeds)==38 and len(mods)==19
 assert any('contracts/runtime_pause_activations.sql' in p.replace('\\','/') for _,_,p in embeds)
 # Product snapshot set must match all actual live product directories and contracts.
 products=set()
 for d in ['apps/control','internal','adapters','evaluation','ops','migrations/sqlite','spec/v2.0/contracts']:
  for p in (W/d).rglob('*'):
   assert not p.is_symlink()
   if p.is_file():products.add(key(p))
 products.update(key(W/p) for p in ['go.mod','go.sum','execution/toolchains/locked.json'])
 assert products==set(refs(inventory['product_inventory'])) and len(products)==648
 verify(inventory['GoRef']);go=Path(inventory['GoRef']['path'])
 tools={key(p) for p in (go.parent.parent/'pkg/tool/windows_amd64').iterdir() if p.is_file()}
 assert tools==set(refs(inventory['compiler_tool_refs'])) and len(tools)==8
 allinputs=inventory['build_inputs']+inventory['product_inventory']+inventory['compiler_tool_refs']+[inventory['GoRef']]+closed['runtime_resources']
 hashed={}
 for pin in allinputs:
  if key(pin['path']) not in hashed:hashed[key(pin['path'])]=verify(pin)
 guards={}
 for entry in closed['cleanup']:
  verify(entry['ref']);g=read(entry['ref']['path']);guards[entry['name']]=g
  assert g['attempted'] and g['verification']=='PASSED' and g['share_mode']=='FILE_SHARE_READ_ONLY'
  assert g['closed'] and g['retained_handles_count']==0 and g['failure'] is None and not g['errors']
  assert all(x['verified'] and x['final_path_match'] and x['closed'] for x in g['entries'])
 assert set(refs(guards['selected_compiler_inputs']['entries']))==selected|{key(C/'actual-test-compiler-input-inventory.json')}
 productguard=refs(guards['product_and_runtime']['entries'])
 for pin in inventory['product_inventory']+inventory['compiler_tool_refs']+[inventory['GoRef']]+closed['runtime_resources']:
  assert productguard[key(pin['path'])]==(pin['sha256'].removeprefix('sha256:'),pin['bytes'])
 meta=run('test-binary-metadata',[str(go),'version','-m',closed['test_program_ref']['path']],W,build['public_environment'])
 assert 'go1.27.1' in meta and 'researchos.local/research-os/internal/domain.test' in meta
 assert '-tags=' not in meta and 'GOOS=windows' in meta and 'GOARCH=amd64' in meta

 # Entire public freeze rechecked before any config acceptance.
 assert len(cfg['FrozenInputs'])==4373
 frozen=refs(cfg['FrozenInputs']);assert len(frozen)==4373
 for pin in cfg['FrozenInputs']:
  if key(pin['path']) not in hashed:hashed[key(pin['path'])]=verify(pin)
  actual=hashed[key(pin['path'])];assert (actual['sha256'],actual['bytes'])==frozen[key(pin['path'])]
 for pin in allinputs:
  assert frozen[key(pin['path'])]==(pin['sha256'].removeprefix('sha256:'),pin['bytes'])
 for pin in [cfg[n] for n in ['ControllerSource','HarnessConfig','TestProgram','ObservedOwnedHelper','OriginalOwnedHelper','SourceReadGuard','CompilerInventory','BuildInvocation']]:verify(pin)
 assert harness['Case']=='positive-replay' and harness['CaseID']=='root-positive-replay-01'
 assert Path(harness['BuildRoot'])==W
 original=read(A/'revision01/public-handoff04.config.json')
 for name in ['SourceBackupProgram','PythonProgram','BrokerSource','PrivateStdinHelper']:
  assert harness[name]==original[name];verify(harness[name])
 for name in ['RootProgram','ControlProgram','BackupProgram','EnrollmentProgram']:
  assert harness[name]['sha256']==original[name]['sha256'] and harness[name]['bytes']==original[name]['bytes']
  assert key(harness[name]['path'])!=key(original[name]['path']);verify(harness[name]);verify(original[name])
 assert harness['RootSigningPublicKey']==original['RootSigningPublicKey'] and len(bytes.fromhex(harness['RootSigningPublicKey']))==32
 extra_inputs=[]
 for pinfile in [A/'source24-build-inputs/compiler-inputs.json',A/'revision01/target25-r4-build-inputs/compiler-inputs.json']:
  for pin in read(pinfile)['inputs']:
   assert frozen[key(pin['path'])]==(pin['sha256'].removeprefix('sha256:'),pin['bytes'])
  extra_inputs.append({'inventory_ref':ref(pinfile),'members':len(read(pinfile)['inputs'])})
 for rel in ['spec/v2.0/contracts','migrations/sqlite']:
  for p in (oldroot/rel).rglob('*'):
   assert not p.is_symlink()
   if p.is_file():assert key(p) in frozen
 rootdir=Path(harness['RootProgram']['path']).parent
 assert rootdir==Path(harness['ControlProgram']['path']).parent
 assert rootdir==R/'.local/native25-cases-20261014/positive-replay-01/programs'
 assert {p.name for p in rootdir.iterdir()}=={'recovery-root.exe','control.exe','backup.exe','enrollment.exe'}
 for name in ['recovery-release.json','current-schema24-to25-grant.json','consumed-schema24-to25-grants']:
  assert not os.path.lexists(rootdir/name)
 assert not os.path.lexists(cfg['ControllerDirectory']) and not os.path.lexists(harness['OutputDirectory'])
 temp=Path(cfg['Environment']['TEMP']);assert temp==Path(cfg['Environment']['TMP']) and str(temp)==cfg['Environment']['RESEARCHOS_NATIVE_MIGRATION_HARNESS_TEMP_ROOT']
 assert temp==rootdir.parent/'temp' and temp.is_dir() and not list(temp.iterdir())
 assert str(temp.resolve()).casefold()==str(temp).casefold()
 # Import the exact reviewed controller and invoke only public context validation.
 controller=types.ModuleType('actual_readiness_controller');controller.__file__=cfg['ControllerSource']['path']
 exec(compile(Path(controller.__file__).read_bytes(),controller.__file__,'exec'),controller.__dict__)
 publicconfig={**configref,'sha256':'sha256:'+configref['sha256']}
 validated=controller.context(publicconfig)
 assert validated['hc']['Case']=='positive-replay'
 assert not os.path.lexists(cfg['ControllerDirectory']) and not os.path.lexists(harness['OutputDirectory'])
 assert ref(configref['path'])==configref
 assert ref(closed['test_program_ref']['path'])['sha256']==closed['test_program_ref']['sha256']
 summary.update(state='READY_FOR_ROOT_ISOLATED_POSITIVE_HARNESS_TO_FIRST_PUBLIC_PAYLOAD_ONLY',findings=[],config_ref=configref,
  harness_ref=ref(cfg['HarnessConfig']['path']),test_program_ref=closed['test_program_ref'],compiler_inventory_ref=ref(C/'actual-test-compiler-input-inventory.json'),
  build_invocation_ref=ref(C/'test-binary-compile.invocation.json'),compile_closed_ref=ref(C/'compilation.closed.json'),
  validated_counts={'packages':len(packages),'selected_compiler_inputs':len(selected),'embed_occurrences':len(embeds),'module_files':len(mods),'product_files':len(products),'compiler_tools':len(tools),'frozen_public_inputs':len(frozen),'distinct_current_files_hashed':len(hashed)},
  older_program_compiler_inventories=extra_inputs,actual_controller_context_validation='PASS_WITHOUT_MOCKS_NO_SERVE',
  compile_evidence_level='Independently reparsed raw actual go list, verified current selected inputs and public recorded Job/read-guard closure; read-only Go binary metadata inspected. No rebuild and no retroactive independent observation of original compilation Job.',
  allowance='Root may start only this exact fresh isolated positive-replay controller/harness to its first release payload review pause, after rechecking unchanged pins and fresh output paths. This review itself starts nothing.',
  mandatory_pause='Do not sign or publish on this report. Root must inspect the concrete first payload, fixture identity, current held Job observation, whole-row/schema evidence and current public pins, then separately decide each signing and publication step.',
  limitations=['No private resource/DPAPI/key examined; compiled public trust compatibility must still be checked by Root before any signing authority is used.','No actual fixture created/read, no native migration, and no test binary run in this review.','Finite harness/controller deadlines remain; failed/pre-payload fixture construction may require Root independent retained-fixture inspection.','First phase includes synthetic old24 backup and isolated new25 rehearsal; no original product DB path is present in public config.'],
  signatures_authorized=False,formal_acceptance=False,previous_33_member_manifest_unchanged=True)
except BaseException as exc:
 summary.update(state='FINDINGS_OR_REVIEW_CHECK_FAILED',error_type=type(exc).__name__,error=str(exc));raise
finally:
 summary['at']=dt.datetime.now(dt.timezone.utc).isoformat()
 dump('readiness-report.json',summary)
 print(json.dumps({'state':summary['state'],'report_ref':ref(E/'readiness-report.json')},ensure_ascii=True))
