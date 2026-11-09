import sys
sys.dont_write_bytecode=True
import json,hashlib,pathlib,ast,types,datetime,sqlite3,struct,collections,uuid,subprocess,queue,threading,ctypes
P=pathlib.Path
N=P(__file__).resolve().parent
B=N.parent.parent
R=B.parents[4]
C=B/'root_native_c12_manual_caller_source_codex/c12-1a11ebe661670a1a49d0ea22092604a'
S=B/'integration_codex/native-cleanup-root-one-spec-source-1791517434000'
D=B/'integration_codex/native-cleanup-controller-source-root-1791517434000'
A=B/'integration_codex/native-cleanup-compile-source-root-1791516889000'
PR=B/'native_n12actual_c12source_independent_review_codex/ac-20261009-review'
checks=[];inputs={}
def ck(n,v): checks.append(dict(name=n,pass_=bool(v)))
def pin(p):
 p=P(p).resolve();raw=p.read_bytes()
 return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def norm(v): return dict(path=str(P(v['path']).resolve()),sha256=v['sha256'].removeprefix('sha256:'),bytes=v['bytes'])
def verify(v):
 v=norm(v);a=pin(v['path']);ck('exact-pin:'+v['path'],a==v)
 key=a['path'].casefold();ck('consistent-pin:'+a['path'],key not in inputs or inputs[key]==v);inputs[key]=v
 return v
def add(p): return verify(pin(p))
def read(p): return json.loads(P(p).read_text(encoding='utf-8-sig'))
def save(n,v):
 with (N/n).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
 return pin(N/n)
def fixed(p,h,z):return verify(dict(path=str(p),sha256=h,bytes=z))
def manifest(d):
 add(d/'HDF.json');add(d/'MF.json')
 m=read(d/'MF.json')['members'];m=m.values() if isinstance(m,dict) else m
 for v in m:verify(v)
fixed(C/'HDF.json','fbfb33051831833120af8a6f17c1b3c2d3882e69fa25864f1b3cf26cc8dbdf0c',3337)
fixed(C/'MF.json','4da1e1875907fc9aa9fe5948e32da39c5e8056bbef7e6855522b2d75eba089e3',5625)
fixed(S/'HDF.json','7666234c5be6bc899e69b56be2c5215b5c39fe138d15c20a4475e2714ab5d212',1139)
fixed(S/'MF.json','d09fa41a8987eee310b553564314f23d204cbd363fbca95bbbb261b130f3b22c',1001)
fixed(D/'controller.public.config.json','38a1305ed39835194678d0e9a6f06acec1b74b1f2ba1071bc1769841c57c2256',1106152)
fixed(D/'controller-config.prepared.json','8a25b52e2f2500e175684c059df427b320c327457e774a2b6a1d4bb274078162',4954)
fixed(PR/'HDF.json','69dc77e577a3fa7eee11af2baf0455f40cee08382919e2920f2f1139d5db5be1',2909)
fixed(PR/'MF.json','f3062d0b5dd700dbffc14f813bbf746e0c839b857015ae059f52dd78345cc839',2738)
for d in (C,S,D,PR):manifest(d)
prepared=read(D/'controller-config.prepared.json');cfg=read(D/'controller.public.config.json');hc=read(cfg['HarnessConfig']['path'])
for n in ('controller-config.prepared.json','config-prepare-root-original-tool-io.json','bootstrap-source-guard.cleanup.actual.json','config-input-source-guard.cleanup.actual.json'):add(D/n)
ck('root-correctly-derived',R.name=='research-os')
ck('prepared-status',prepared['status']=='FRESH_CTL4_CLEANUP_BROKER4_PROOF_CONTEXT_VALIDATED_NO_NATIVE_LAUNCH')
io=read(D/'config-prepare-root-original-tool-io.json')
ck('original-root-preparation-zero',io['original_tool_io']['exit_code']==0 and 'ROOT_PYTHON_EXIT=0' in io['original_tool_io']['output'] and not io['native_launched'])
for n in ('bootstrap-source-guard.cleanup.actual.json','config-input-source-guard.cleanup.actual.json'):
 g=read(D/n);ck('prepared-closed:'+n,g['closed'] and not g['errors'] and g['retained_handles_count']==0)
for v in prepared['canonical_unchanged_refs']:verify(v)
cp=read(prepared['canonical_unchanged_refs'][0]['path']);ck('current-checkpoint364',cp['revision']==364)
for v in prepared['source_review_refs']:verify(v)
verify(prepared['compile_ref']);actual=read(prepared['compile_ref']['path'])
ck('35-unit-component-only',actual['unit_pass_count']==35 and actual['unit_fail_count']==actual['unit_skip_count']==actual['native_migration_cases_executed']==0 and actual['all_owned_jobs_closed'])
ck('43-source-count',actual['source_count']==43)
for v in actual['invocation_refs']:verify(v)
for v in actual['binary_refs'].values():verify(v)
for k in ('source_overlay_ref','formatted_source_ref','compiler_input_inventory_ref','unit_detail_ref','official_test2json_ref'):verify(actual[k])
formatted=read(actual['formatted_source_ref']['path'])
# manifest may be a list or mapping of relpath to exact refs.
formatted_values=formatted.values() if isinstance(formatted,dict) else formatted
for v in formatted_values:verify(v)
ck('formatted-source43',len(formatted)==43)
for v in cfg['FrozenInputs']:verify(v)
frozen={str(P(v['path']).resolve()).casefold():norm(v) for v in cfg['FrozenInputs']}
ck('frozen-4185-unique',len(cfg['FrozenInputs'])==len(frozen)==prepared['frozen_input_count']==4185)
def present(v):return frozen.get(str(P(v['path']).resolve()).casefold())==norm(v)
for k in ('ControllerSource','HarnessConfig','TestProgram','ObservedOwnedHelper','OriginalOwnedHelper','SourceReadGuard','CompilerInventory','BuildInvocation'):ck('required-frozen:'+k,present(cfg[k]))
for k in ('RootProgram','ControlProgram','BackupProgram','EnrollmentProgram','PythonProgram','BrokerSource','PrivateStdinHelper'):ck('harness-frozen:'+k,present(hc[k]))
inventory=read(cfg['CompilerInventory']['path'])
ck('inventory-counts',inventory['package_count']==364 and len(inventory['build_inputs'])==3793 and len(inventory['product_inventory'])==599 and len(inventory['compiler_tool_refs'])==8 and len(inventory['actual_embed_files'])==38)
for label,values in [('build',inventory['build_inputs']),('product',inventory['product_inventory']),('tools',inventory['compiler_tool_refs'])]:
 for v in values:ck(label+'-frozen:'+v['path'],present(v))
for v in inventory['actual_embed_files']:ck('embed-frozen:'+v['ref']['path'],present(v['ref']))
ck('Go-explicitly-frozen',present(inventory['GoRef']))
ck('official-test2json-frozen',present(actual['official_test2json_ref']))
ck('fresh-case',hc['Case']=='positive-replay' and hc['CaseID']=='t12cl149d6f49321')
programs=R/'.local/native-cleanup-compile-env-1791516889000/programs'
for k,label in [('RootProgram','maintenance-root-build'),('ControlProgram','control-build'),('BackupProgram','backup-build'),('EnrollmentProgram','enrollment-build')]:
 ck('actual-program:'+k,norm(hc[k])==norm(actual['binary_refs'][label]) and P(hc[k]['path']).parent==programs)
ck('fresh-tagged-binary',norm(cfg['TestProgram'])==norm(actual['binary_refs']['tagged-test-harness']) and P(cfg['TestProgram']['path']).parent==programs)
ck('current-build-root',hc['BuildRoot']==actual['current_source_root'])
env=cfg['Environment'];ck('isolated-temp-binding',env['TEMP']==env['TMP']==env['RESEARCHOS_NATIVE_MIGRATION_HARNESS_TEMP_ROOT'] and P(env['TEMP'])==R/'.local/native-cleanup-controller-env-1791517434000/temp')
ck('profile-fresh',env['USERPROFILE']==env['LOCALAPPDATA']==env['APPDATA'] and P(env['USERPROFILE'])==R/'.local/native-cleanup-controller-env-1791517434000/profile')
for p in (P(cfg['ControllerDirectory']),P(hc['OutputDirectory'])):ck('uncreated-native-output:'+str(p),not p.exists())
authority=read(S/'precise_launch_authority.source.json')
ck('exact-authority-config',norm(authority['config_ref'])==pin(D/'controller.public.config.json'))
ck('explicit-deadline-order',authority['main_seconds']==1200 and authority['independent_cleanup_seconds']==authority['grant_seconds']==240 and authority['Go_global_seconds']==1500 and authority['controller_owned_seconds']==1560 and authority['outer_seconds']==1800 and 1200+240<1500<1560<1800)
for p in authority['Root_outputs']:
 p=P(p);ck('fresh-empty-root-output:'+str(p),p.is_dir() and not p.is_symlink() and not list(p.iterdir()))
for name in ('recovery-release.json','current-schema23-to24-grant.json'):
 ck('signed-output-absent:'+name,not (programs/name).exists() and not (P(hc['OutputDirectory'])/name).exists())
ck('fresh-temp-empty',not list(P(env['TEMP']).iterdir()))
ctl=P(cfg['ControllerSource']['path']).read_text(encoding='utf-8')
ck('CTL4-exact',cfg['ControllerSource']['sha256']=='sha256:e7538c580d2e07217512e036e00272b3be94cb11551ace6885cc46316a67b3b3' and cfg['ControllerSource']['bytes']==42696)
ck('CTL4-inner26-loop26plus10','case_deadline_seconds":1560' in ctl and 'stderr, 1560,' in ctl and 'time.monotonic() + 1570' in ctl)
harness=P(hc['BuildRoot'])/'internal/domain/native_migration_authority_harness_windows_test.go'
htext=harness.read_text(encoding='utf-8')
ck('harness-main20min','20*time.Minute' in htext or '20 * time.Minute' in htext)
ck('harness-independent-cleanup','context.WithTimeout(context.Background(), 4*time.Minute)' in htext or 'context.WithTimeout(context.Background(), 4 * time.Minute)' in htext)
for v in read(C/'source-replacements.json'):
 verify(v['base']);new=P(v['candidate']).read_text(encoding='utf-8');old=P(v['base']['path']).read_text(encoding='utf-8');inv=new
 for before,after in reversed(v['replacements']):
  ck('inverse-unique:'+P(v['candidate']).name+':'+before,inv.count(after)==1);inv=inv.replace(after,before,1)
 ck('exact-base-inverse:'+P(v['candidate']).name,inv==old)
prov=read(D/'adaptation.provenance.json');verify(prov['base_ref']);verify(prov['new_ref']);inv=P(prov['new_ref']['path']).read_text(encoding='utf-8')
for v in reversed(prov['changes']):
 ck('builder-inverse-unique:'+v['before'],inv.count(v['after'])==v['count']);inv=inv.replace(v['after'],v['before'])
ck('builder-exact-byte-inverse',inv.encode()==P(prov['base_ref']['path']).read_bytes())
srcs={}
for p in [C/'serve_one_positive_c12.actual_owned.py',C/'root_public_api_c12.actual.py',C/'prepare_one_root_request.py',S/'prepare_one_spec.actual.py',D/'prepare_native_cleanup_controller_public_config.actual.py']:
 raw=p.read_text(encoding='utf-8');ast.parse(raw);ck('Python-AST:'+p.name,True);srcs[p.name]=raw
serve=srcs['serve_one_positive_c12.actual_owned.py'];api=srcs['root_public_api_c12.actual.py'];prep=srcs['prepare_one_root_request.py'];spec=srcs['prepare_one_spec.actual.py']
ck('outer1800-only-source','env,stdout,stderr,1800,creation_flags' in serve)
for n,t in [('serve',serve),('api',api)]:
 ck(n+'-exact-config-on-entry','expected_config_sha' in t and 'config_plain["sha256"]==expected_config_sha' in t and 'config_plain["bytes"]==expected_config_bytes' in t)
 ck(n+'-frozen-plus-runtime-guard','cfg["FrozenInputs"]' in t and 'runtime_pins()' in t and 'helper.runtime_resource_paths()' in t and 'guard.acquire(refs)' in t and 'retained_handles_count' in t)
 ck(n+'-fresh-case-and-controller','t12cl149d6f49321' in t and 'e7538c580d2e07217512e036e00272b3be94cb11551ace6885cc46316a67b3b3' in t)
ck('preparer-no-execute-or-private','subprocess' not in prep and 'sqlite3' not in prep and 'exec(' not in prep and 'Private resource paths in metadata are never followed.' in prep)
ck('preparer-original-grant','total_seconds() == 240' in prep and 'existing validity elapsed; no renewal' in prep)
ck('preparer-actual-only','actual snapshot binding' in prep and 'actual current-phase approval' in prep and 'actual successful signing receipt and signed document required' in prep)
ck('preparer-whole-inspection-normalization','inputs.obj(spec["InspectionReceipt"], style="bare")' in prep and 'request["InspectionReceipt"] = normalized' in prep)
ck('preparer-exclusive-and-recheck','destination.open("xb")' in prep and 'inputs.close_check()' in prep)
ck('api-whole-SQL-reads','mode=ro' in api and 'PRAGMA query_only=ON' in api and 'SELECT * FROM ' in api and 'CASE WHEN 1 THEN ' in api and 'db.execute("BEGIN")' in api)
ck('api-typed-row-identity','struct.pack(">d",value)' in api and 'primary_and_WAL_bytes_unchanged' in api and 'data_version_before==data_version_after' in api)
ck('api-whole-target-check','rows==after' in api and 'versions==list(range(1,25))' in api and 'runtime_prepared_abandonments' in api)
ck('api-no-auto-release','elif action=="inspect":' in api and 'output["inspection_ref"]' in api and 'controller.release_fixture(config_ref,approval_ref)' in api)
# Execute only the previously accepted immutable source-read guard module.
gref=norm(cfg['SourceReadGuard']);raw=P(gref['path']).read_bytes();ck('guard-module-exact',pin(gref['path'])==gref)
m=types.ModuleType('independent_c12_source_guard');m.__file__=gref['path'];sys.modules[m.__name__]=m;exec(compile(raw,gref['path'],'exec'),m.__dict__)
add(__file__);add(sys.executable)
for mod in list(sys.modules.values()):
 for attr in ('__file__','__cached__'):
  p=getattr(mod,attr,None)
  if p and P(p).is_file():add(p)
allrefs=list(inputs.values());ck('all-file-caps',all(v['bytes']<=256*1024*1024 for v in allrefs) and sum(v['bytes'] for v in allrefs)<2*1024*1024*1024)
guard=m.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
try:
 guard.acquire(allrefs)
 ck('guard-all-inputs-acquired',True)
 ck('guarded-config-exact',guard.get_buffer(str((D/'controller.public.config.json').resolve()))==(D/'controller.public.config.json').read_bytes())
 for k,v in inputs.items():ck('final-unchanged:'+v['path'],pin(v['path'])==v)
finally:
 cleanup=guard.close();save('sourceguard.final.json',cleanup)
ck('review-guard-released',cleanup['closed'] and not cleanup['errors'] and cleanup['retained_handles_count']==0)
save('input-pins.json',list(inputs.values()))
save('checks.json',dict(checks=checks,passed=sum(v['pass_'] for v in checks),failed=sum(not v['pass_'] for v in checks),input_count=len(inputs)))
save('scope.json',dict(native_cases_executed=0,Git_Go_SQL_API_calls=0,private_key_reads=0,issuer_signatures=0,external_model_calls=0,Main_canonical_candidate_writes=0,formal_acceptance=False))
print(json.dumps(dict(check_count=len(checks),failed=[v for v in checks if not v['pass_']],input_count=len(inputs),guard_closed=cleanup['closed'],input_bytes=sum(v['bytes'] for v in inputs.values())),ensure_ascii=True))

