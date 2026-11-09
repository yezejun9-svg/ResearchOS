import sys
sys.dont_write_bytecode=True
import pathlib,json,hashlib,re,types,collections
P=pathlib.Path;N=P(__file__).resolve().parent;B=N.parent.parent;R=B.parents[4]
A=B/'integration_codex/history20-r2-five-parent-target-root-1791521480000'
I=B/'integration_codex/history20-r2-five-parent-isolation-root-1791521480000'
C=B/'integration_codex/history20-r2-five-parent-caller-root-1791521480000'
S=B/'historical20_r2_caller_independent_review_codex/h20r2-caller-01a11ee7'
PR=B/'historical20_upgrade_source_independent_review_codex/h20r2-20261009-source-review'
OLD=B/'history20_failed_actual_independent_review_codex/h20a914-20261009-review'
T=R/'.local/worktrees/h20r2s-1791521480000'
checks=[];inputs={};canonical_paths=set()
def ck(n,v):checks.append(dict(name=n,passed=bool(v)))
def pin(p):
 p=P(p).resolve();raw=p.read_bytes()
 return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def verify(v):
 expected=dict(path=str(P(v['path']).resolve()),sha256=v['sha256'].removeprefix('sha256:'),bytes=v['bytes'])
 actual=pin(expected['path']);ck('pin:'+expected['path'],actual==expected)
 key=expected['path'].casefold();ck('pin-consistent:'+expected['path'],key not in inputs or inputs[key]==expected);inputs[key]=expected
 return expected
def add(p):return verify(pin(p))
def fixed(p,h,z):return verify(dict(path=str(p),sha256=h,bytes=z))
def read(p):return json.loads(P(p).read_bytes())
def save(n,v):
 with (N/n).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
 return pin(N/n)
fixed(I/'isolation.ready.json','3ca2c6700bcad61b3e614e2683b95898b38635c0a5b58acfd4e0400a49fa6deb',4045)
fixed(A/'validation.closed.json','b180ec16163730afbe03f0d62fa0caf368b3d087a048408ddb8d691d7e1fceac',26677)
fixed(C/'HDF.json','600510ddb529c4e390d8bac0fdb42bdcaf0161843ce10fcd72e57bd63892d7e1',2751)
fixed(C/'MF.json','4889fa6c17d39a4d448b7f55a4f30361ba1996cb9291c178618523c1ec3848c6',3010)
fixed(S/'HDF.json','51f3aaf04610a35883bd9fb3745bea2f399d8b2dcd5913d18e8788e8ac378936',4443)
fixed(S/'MF.json','4ed7a2c6d2d66df7862228d8f74752916749a3e5384951af2c64ba490402c113',10161)
fixed(PR/'HDF.json','1d273efbd61c3fba15115bc9a8faa6e5239fecf451997164f1d90faa9d06667c',2935)
fixed(PR/'MF.json','407af8ea1f4d0f1e42c82339c5a415d1afd04f44576769e2493cc820b1c9ddc6',2906)
fixed(OLD/'HDF.json','b130d4fd90f39391b6ef353990fab38cbcc7c4f5dd4a991caa9b8c6f395150e6',3321)
fixed(OLD/'MF.json','2c8f71f482c1d936f887bcbc2a864518a2470b55a4f85452adaf473c2fee6fa8',3774)
for d in (C,S,PR,OLD):
 for v in read(d/'MF.json')['members']:verify(v)
isolation=read(I/'isolation.ready.json');actual=read(A/'validation.closed.json');chdf=read(C/'HDF.json')
for k in ('source_overlay_ref','formatted_source_ref','compiler_inventory_ref','compiled_test_ref','canonical_pre_run_ref'):verify(actual[k])
for k in ('sparse_checkout_ref','project_identity_ref'):verify(isolation[k])
ck('actual-positive-scope-status',actual['status']=='HISTORY20_FIVE_PARENT_A20_TO21_SCOPE_PASSED_FULL20_TO24_OPEN' and actual['error'] is None)
ck('caller-source-accepted',read(S/'HDF.json')['status']=='SOURCE_APPROVED_FOR_ROOT_FRESH_SPARSE_AND_NARROW_VALIDATION')
rootio_path=C/'postseal-h20r2-actual-original-root-tool-io.json';add(rootio_path);rootio=read(rootio_path)
ck('root-isolation-initial',rootio['isolation_initial']['chunk_id']=='d52d25' and rootio['isolation_initial']['session_id']==26386)
ck('root-isolation-completed',rootio['isolation_completion']['chunk_id']=='dcebf4' and rootio['isolation_completion']['exit_code']==0 and 'ROOT_PYTHON_EXIT=0' in rootio['isolation_completion']['output'])
ck('root-validation-initial',rootio['validation_initial']['chunk_id']=='c585e3' and rootio['validation_initial']['session_id']==15116)
ck('root-validation-poll',rootio['validation_poll1']['chunk_id']=='fd412e' and rootio['validation_poll1']['session_id']==15116)
ck('root-validation-completed',rootio['validation_completion']['chunk_id']=='24f63b' and rootio['validation_completion']['exit_code']==0 and 'ROOT_PYTHON_EXIT=0' in rootio['validation_completion']['output'])
ck('precise-exit-claims',rootio['explicitRootPythonExit']==rootio['outerExit']==rootio['OwnedPrimaryTest2jsonExit']==0 and rootio['separateTestBinaryDescendantExit'] is None)
ck('old914-still-failed',rootio['original914']=='FAILED_IMMUTABLE')
jobs=[];results={}
for category,refs in [('isolation',isolation['invocation_refs']),('validation',actual['invocation_refs'])]:
 for v in refs:
  verify(v);p=P(v['path']);raw=p.read_text(encoding='utf-8');o=json.loads(raw);r=o['result'];j=r['job_cleanup'];label=p.name.removesuffix('.invocation.json')
  ck('actual-exit:'+label,o['actual_native_exit']==r['actual_exit']==0)
  ck('closed-job:'+label,not r['timed_out'] and r['error'] is None and o.get('exception') is None and j['active_processes_last_observed']==0 and not j['errors'] and all(j[k] for k in ('unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','primary_exit_confirmed','job_idle_confirmed','handles_closed')))
  ck('concrete-PID:'+label,type(r['owned_child_pid']) is int and r['owned_child_pid']>0)
  ft=re.search(r'"creation_time_100ns"\s*:\s*(\d+)',raw).group(1)
  ck('exact-FILETIME:'+label,type(r['creation_time_100ns']) is int and str(r['creation_time_100ns'])==ft)
  for k in ('stdout_ref','stderr_ref'):verify(o[k])
  jobs.append(dict(category=category,label=label,invocation_ref=v,primary_executable=o['argv'][0],pid=r['owned_child_pid'],creation_time_100ns_decimal=ft,actual_primary_exit=r['actual_exit'],descendant_test_binary_exit=None if label=='history20-five-parent-jsonl' else 'not separately asserted',job_closed=True))
  results[label]=o
ck('all-ten-jobs',len(jobs)==10 and len(isolation['invocation_refs'])==6 and len(actual['invocation_refs'])==4)
ck('distinct-process-identities',len({(j['pid'],j['creation_time_100ns_decimal']) for j in jobs})==10)
save('owned-job-audit.json',jobs)
guards=[];guardobjects={}
for d,names in [(I,['source','runtime-source']),(A,['input-source','runtime-source','candidate-source','compiler-source','binary-source'])]:
 for name in names:
  p=d/(name+'-guard.cleanup.actual.json');add(p);g=read(p);guardobjects[str(p)]=g
  ck('actual-guard-closed:'+str(p),g['closed'] and g['verification']=='PASSED' and not g['errors'] and g['retained_handles_count']==0 and g['failure'] is None)
  ck('actual-guard-entry-closure:'+str(p),all(e['verified'] and e['final_path_match'] and e['closed'] for e in g['entries']))
  for e in g['entries']:verify(e)
  guards.append(dict(ref=pin(p),entries=len(g['entries']),closed=True,no_retained_handles=True))
ck('seven-actual-guards',len(guards)==7);save('actual-guard-audit.json',guards)
for d in (I,A):
 add(d/'canonical.pre-run.exact.json');c=read(d/'canonical.pre-run.exact.json');ck('canonical-revision364:'+str(d),c['revision']==364)
 for v in c['refs']:verify(v);canonical_paths.add(str(P(v['path']).resolve()).casefold())
ck('same-four-canonical-pins',read(I/'canonical.pre-run.exact.json')['refs']==read(A/'canonical.pre-run.exact.json')['refs'] and len(canonical_paths)==4)
ck('live-CP364',read(R/'execution/v2.4/checkpoint.json')['revision']==364)
dirty=P(results['tracked-status']['stdout_ref']['path']).read_text(encoding='utf-8').splitlines()
ck('actual-original-dirty-13-and11D',dirty==isolation['tracked_dirty_paths'] and len(dirty)==13 and sum(x.startswith(' D ') for x in dirty)==11)
ck('actual-original-empty-index',not P(results['staged-status']['stdout_ref']['path']).read_bytes().strip())
for name in ('head-before','head-after'):ck('isolation-HEAD:'+name,P(results[name]['stdout_ref']['path']).read_text(encoding='utf-8').strip()=='adc460c2138528f163f7fdab5e8d81dde157b7fb')
ck('no-post-validation-Git-claimed',len(isolation['invocation_refs'])==6)
overlay=read(actual['source_overlay_ref']['path']);composition=read(S/'composition.json');choice=read(chdf['choice_ref']['path'])
def identity(v):return dict(path=str(P(v['path']).resolve()),sha256=v['sha256'].removeprefix('sha256:'),bytes=v['bytes'])
normdict=lambda d:{k:identity(v) for k,v in d.items()}
ck('61-preformat-source-composition',normdict(overlay['sources'])==normdict(composition['sources']) and len(overlay['sources'])==61)
verify(choice['actual_T11_overlay_ref']);t11=read(choice['actual_T11_overlay_ref']['path'])['sources'];h20=set(choice['h20_candidate_paths'])
ck('non-H20-T11-preserved',all(identity(overlay['sources'][k])==identity(v) for k,v in t11.items() if k not in h20))
ck('AF-exact',identity(overlay['sources']['internal/domain/client_protocol_attach_contract_windows_test.go'])==identity(t11['internal/domain/client_protocol_attach_contract_windows_test.go']))
ck('five-H20R2-exact-paths',h20=={'internal/domain/backup.go','internal/domain/backup_upgrade.go','internal/domain/backup_history20_upgrade.go','internal/domain/backup_history20_upgrade_test.go','ops/backup/main.go'})
fixed(overlay['sources']['internal/domain/backup_history20_upgrade_test.go']['path'],'914792b2e903f15026ea0a6d0652e1db5401076dc24fc9132bebaad3fa930f2f',10174)
formatted=read(actual['formatted_source_ref']['path']);ck('61-formatted-members',len(formatted)==61);format_delta=[]
for v in formatted:
 verify(v);rel=P(v['path']).relative_to(T).as_posix();old=overlay['sources'][rel];verify(old)
 if (v['sha256'],v['bytes'])!=(old['sha256'],old['bytes']):format_delta.append(dict(relative_path=rel,before_ref=old,formatted_ref=v))
save('format-delta.json',format_delta)
inv=read(actual['compiler_inventory_ref']['path'])
for v in inv['build_inputs']+inv['product_inventory']+inv['compiler_tool_refs']+[inv['GoRef'],inv['test2json_executable_ref']]:verify(v)
ck('352-3733-607-8-39-counts',inv['package_count']==352 and len(inv['build_inputs'])==3733 and len(inv['product_inventory'])==607 and len(inv['compiler_tool_refs'])==8 and len(inv['actual_embed_files'])==39)
list_raw=P(results['tagged-compiler-input-list']['stdout_ref']['path']).read_text(encoding='utf-8')
decoder=json.JSONDecoder();pos=0;packages=[];raw_inputs={};embeds=[]
fields=('GoFiles','CgoFiles','CFiles','CXXFiles','MFiles','HFiles','FFiles','SFiles','SwigFiles','SwigCXXFiles','SysoFiles','CompiledGoFiles','TestGoFiles','XTestGoFiles','EmbedFiles','TestEmbedFiles','XTestEmbedFiles')
while pos<len(list_raw):
 while pos<len(list_raw) and list_raw[pos].isspace():pos+=1
 if pos==len(list_raw):break
 pkg,pos=decoder.raw_decode(list_raw,pos);ck('listed-package-clean:'+str(pkg.get('ImportPath')),not pkg.get('Error') and not pkg.get('DepsErrors'));packages.append(pkg.get('ImportPath'))
 if not pkg.get('Dir'):continue
 for field in fields:
  for name in pkg.get(field,[]):
   p=P(name);p=p if p.is_absolute() else P(pkg['Dir'])/p;v=pin(p);raw_inputs[v['path']]=v
   if field.endswith('EmbedFiles'):embeds.append(dict(package=pkg['ImportPath'],field=field,ref=v))
ck('raw-list-package-exact',packages==inv['packages'])
ck('raw-list-compiler-input-exact',raw_inputs=={v['path']:v for v in inv['build_inputs']})
ck('raw-list-embed-exact',embeds==inv['actual_embed_files'])
product={}
for rel in ('apps/control','internal','adapters','evaluation','ops','migrations/sqlite','spec/v2.0/contracts'):
 for p in (T/rel).rglob('*'):
  ck('product-not-symlink:'+str(p),not p.is_symlink())
  if p.is_file():v=pin(p);product[v['path']]=v
for rel in ('go.mod','go.sum','execution/toolchains/locked.json'):v=pin(T/rel);product[v['path']]=v
ck('whole-product607-exact',product=={v['path']:v for v in inv['product_inventory']})
compiler=results['tagged-test-binary-compile'];argv=compiler['argv']
ck('actual-tagged-compile-output',argv[argv.index('-o')+1]==actual['compiled_test_ref']['path'] and '-tags=researchos_native_recovery_harness' in argv and argv[-1]=='./internal/domain')
ck('domain-H20-compiled-CLI-only-inventory',all(str(T/p) in raw_inputs for p in h20 if p.startswith('internal/domain/')) and str(T/'ops/backup/main.go') not in raw_inputs and str(T/'ops/backup/main.go') in product)
fixed(actual['compiled_test_ref']['path'],'14c7fc727df6ac4e12b5a08aa871a7d1ba917f01b6fa9fbb43e3d4066762e992',42653696)
runner=results['history20-five-parent-jsonl']
ck('official-primary-and-actual-binary',runner['argv'][0]==inv['test2json_executable_ref']['path'] and runner['argv'][4]==actual['compiled_test_ref']['path'] and inv['test2json_executable_ref']['sha256']=='dead8050fd4e0e0471407380898fe9642b9107048e0ad119cb652821dfe58f7c')
selector='-test.run=^('+('|'.join(sorted(choice['exact_parent_names'])))+')$'
ck('exact-five-parent-selector',selector in runner['argv'] and '-test.count=1' in runner['argv'] and '-test.timeout=14m' in runner['argv'])
events=[json.loads(line) for line in P(runner['stdout_ref']['path']).read_text(encoding='utf-8').splitlines()]
starts=[];actions={};outputs=[]
for e in events:
 ck('event-package',e['Package']=='researchos.local/research-os/internal/domain')
 name=e.get('Test')
 if not name:continue
 ck('only-selected-parent',name.split('/',1)[0] in choice['exact_parent_names'])
 if e['Action']=='run':starts.append(name)
 if e['Action'] in ('pass','fail','skip'):
  ck('unique-terminal:'+name,name not in actions);actions[name]=e['Action']
 if e['Action']=='output':outputs.append(e)
ck('exact-nine-start-and-terminal',len(starts)==len(set(starts))==9 and set(starts)==set(actions)==set(choice['expected_terminal_names']))
ck('actual-actions-equal-closed',actions==actual['actions'])
ck('9PASS0FAIL0SKIP',collections.Counter(actions.values())=={'pass':9} and actual['pass_count']==9 and actual['fail_count']==actual['skip_count']==0)
ck('package-final-pass',events[-1]['Action']=='pass' and 'Test' not in events[-1])
ck('no-test-error-output',not any(e.get('OutputType')=='error' for e in outputs))
ck('stderr-empty',P(runner['stderr_ref']['path']).read_bytes()==b'')
ck('59preserved54unselected',len(actual['preserved_parent_source_names'])==59 and len(actual['nonselected_parent_sources'])==54 and actual['nonselected_parents_executed_or_newly_accepted'] is False)
declared=set()
for name in overlay['sources']:
 if name.endswith('_test.go'):declared.update(re.findall(r'^func (Test[A-Za-z0-9_]+)\(', (T/name).read_text(encoding='utf-8'),re.M))
ck('137-declared-Source-only',declared==set(choice['all_source_file_declared_parent_names']) and len(declared)==137)
ck('nonselected-not-run',not (set(actual['nonselected_parent_sources'])&set(starts)))
save('terminal-audit.json',dict(started=starts,actions=actions,primary_test2json_exit=0,descendant_test_binary_exit=None,final_package_action=events[-1]['Action'],selected_parent_count=5,drift_leaf_count=4,unselected_preserved_parent_count=54,all_overlay_declared_parent_count=137))
test=(T/'internal/domain/backup_history20_upgrade_test.go').read_text(encoding='utf-8')
positive=test.split('func TestHistory20PublicUpgradePreservesSourceAndRevokesRestoredCredentials',1)[1].split('func TestHistory20RejectsReleaseAndSourceDrift',1)[0]
drift=test.split('func TestHistory20RejectsReleaseAndSourceDrift',1)[1].split('func TestHistory20MigrationRollsBack',1)[0]
generic=test.split('func TestHistory20RestoreFailureRetainsEncryptedBackupAndSource',1)[1].split('func TestHistory20ImplicitStartup',1)[0]
ck('separate-source-key-directories','Source: filepath.Join(base, "source", "source.sqlite")' in test and 'KeyFile: filepath.Join(base, "key", "recovery.key")' in test)
ck('no-skips-or-early-success-return','t.Skip' not in test and 'return' not in positive)
ck('positive-source-rows-schema-owner-revocation',all(x in positive for x in ['UpgradeLocal(context.Background(), opt)','Hash(history20Rows(t, opt.Source)) != Hash(before)','upgradeHistory20RecoveryInvariant(before, after, opt.Destination, true)','len(after["schema_migrations"]) != 21','after["client_sessions"]','Hash(before["auth_principals"]) != Hash(after["auth_principals"])','revoked != 1']))
ck('matching-policy-correct-key-precedes-wrong-key',positive.index('readBackupPolicy(opt.Snapshot, key, policy)')<positive.index('readBackupPolicy(opt.Snapshot, wrong, policy)') and 'format: localUpgradeFormat' in positive and 'purpose: manifest.Purpose' in positive and 'err.Error() != "BACKUP_MANIFEST_INVALID" || wrongFiles != nil' in positive and 'len(files["state.sqlite"]) == 0' in positive and 'Hash(verified.Migrations) != Hash(upgradeVersions(20))' in positive)
ck('four-specific-guard-errors',all(x in drift for x in ['"migration-hash":           "UPGRADE_RELEASE_HASH: 0021_research_pending_windows.sql"','"extra-numbered-migration": "UPGRADE_RELEASE_MIGRATIONS: require exact 1..20"','"foreign-table":            "UPGRADE_SOURCE_SCHEMA"','"session-addon":            "UPGRADE_SOURCE_SCHEMA"','err == nil || err.Error() != expectedError']))
ck('four-rejections-no-publication-source-preserved','[]string{opt.Destination, opt.Snapshot}' in drift and 'Hash(history20Rows(t, opt.Source)) != Hash(before)' in drift)
ck('generic-callback-reached-after-DDL-and-specific-cancel',generic.index('callbackCalled = true')<generic.index('CREATE TABLE fixture_unpublished')<generic.index('return context.Canceled') and '!callbackCalled || !errors.Is(err, context.Canceled)' in generic)
ck('generic-manifest-preserved-destination-unpublished-source-equal','!bytes.Equal(backupManifestBefore, backupManifestAfter)' in generic and 'os.Stat(opt.Destination); !os.IsNotExist(err)' in generic and 'Hash(now) != Hash(before)' in generic)
ck('ledger-rollback-specific','strings.Contains(err.Error(), "fixture ledger failure")' in test and 'before != after || Hash(rows) != Hash(now)' in test)
ck('startup-specific','strings.Contains(err.Error(), "MIGRATION_PREBACKUP_REQUIRED")' in test)
main_names=('go.mod','go.sum','internal/domain/client_workspace_test.go','internal/domain/client_protocol_goal_test.go','internal/domain/runtime_permission_windows_test.go','internal/domain/runtime_tool_integration_windows_test.go','internal/domain/runtime_session_events_windows_test.go','internal/domain/store.go')
input_entries={str(P(e['path']).resolve()):e for e in guardobjects[str(A/'input-source-guard.cleanup.actual.json')]['entries']}
for rel in main_names:
 p=str((R/rel).resolve());ck('Main-guarded-input:'+rel,p in input_entries and identity(input_entries[p])==pin(p))
save('scope.json',dict(review_actual_Git_Go_SQL_product_native_API_private_model=False,actual_test_primary='official test2json',actual_test_descendant_exit=None,actual_component_fixture_SQL_executed_by_Root=True,real_original_trial_DB_touched=False,CLI_compiled_or_executed=False,Main_byte_comparison_evidence='8 explicitly guarded Main files + four canonical files; no post-validation Git or whole-repository hash invented',Main_actual_mutation_paths='reviewed caller confines overlays to fresh worktree and receipts/environment outputs',other54_parents_executed=False,original914='FAILED_IMMUTABLE',full20to24_originalOwner_nineNative_formal42='OPEN'))
gp=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
fixed(gp,'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85',11404)
raw=gp.read_bytes();m=types.ModuleType('h20r2actual_independent_source_guard');m.__file__=str(gp);sys.modules[m.__name__]=m;exec(compile(raw,str(gp),'exec'),m.__dict__)
add(__file__);add(sys.executable)
for mod in list(sys.modules.values()):
 for attr in ('__file__','__cached__'):
  p=getattr(mod,attr,None)
  if p and P(p).is_file():add(p)
guard=m.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
try:
 guard.acquire([v for k,v in inputs.items() if k not in canonical_paths])
 for v in inputs.values():ck('post-review-unchanged:'+v['path'],pin(v['path'])==v)
finally:
 cleanup=guard.close();save('sourceguard.final.json',cleanup)
ck('independent-guard-released',cleanup['closed'] and not cleanup['errors'] and cleanup['retained_handles_count']==0)
save('input-pins.json',list(inputs.values()))
save('checks.json',dict(checks=checks,passed=sum(v['passed'] for v in checks),failed=sum(not v['passed'] for v in checks),input_count=len(inputs)))
print(json.dumps(dict(check_count=len(checks),input_count=len(inputs),failed=[v for v in checks if not v['passed']],format_changed=len(format_delta),guard_released=cleanup['closed'],actual_reviewer_Git_Go_SQL_product_native_model=False),ensure_ascii=True))
sys.exit(1 if any(not v['passed'] for v in checks) else 0)

