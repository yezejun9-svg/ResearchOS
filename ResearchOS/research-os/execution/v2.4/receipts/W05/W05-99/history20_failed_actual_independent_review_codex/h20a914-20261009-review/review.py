import sys
sys.dont_write_bytecode=True
import pathlib,json,hashlib,re,types,collections
P=pathlib.Path;N=P(__file__).resolve().parent;B=N.parent.parent;R=B.parents[4]
A=B/'integration_codex/history20-five-parent-sparse-target-root-h20v-1a11ebe6616'
I=B/'integration_codex/history20-five-parent-sparse-isolation-root-h20v-1a11ebe6616'
C=B/'integration_codex/history20-five-parent-sparse-root-source-h20v-1a11ebe661670a1a49d0ea22092604a'
S=B/'history20_five_parent_caller_independent_review_codex/h20v-20261009-source-review'
T=R/'.local/worktrees/h20s-1a11ebe6616'
checks=[];inputs={};canonical_paths=set()
def ck(n,v):checks.append(dict(name=n,passed=bool(v)))
def pin(p):
 p=P(p).resolve();raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def verify(v):
 x=dict(path=str(P(v['path']).resolve()),sha256=v['sha256'].removeprefix('sha256:'),bytes=v['bytes']);a=pin(x['path'])
 ck('pin:'+x['path'],a==x);key=x['path'].casefold();ck('pin-consistent:'+x['path'],key not in inputs or inputs[key]==x);inputs[key]=x
 return x
def add(p):return verify(pin(p))
def fixed(p,h,z):return verify(dict(path=str(p),sha256=h,bytes=z))
def read(p):return json.loads(P(p).read_bytes())
def save(n,v):
 with (N/n).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
 return pin(N/n)
fixed(I/'isolation.ready.json','21f41df3619d6954213b20f1480eaf408468a93b9b948843c19bed957aaebd2f',4090)
fixed(A/'validation.closed.json','8bab73ebf17c9eebc033ddaa8fc03645645e42f7c9f0a3e7a9aabc31c72e20fc',26709)
fixed(C/'HDF.json','fcc6de7fc2696474764cf8c2b27f9cfcd7942179bf5cdf6a589cf13ac45f4c76',3189)
fixed(C/'MF.json','39e8c747edc6f4f323f1842190edfe32b04ea45cacc3ebd73b7d1443882a0b1b',4962)
fixed(S/'HDF.json','e808790820ae697a5955483a7a9ba6600568ec27329859ce9efcd4c7fe9d207e',3530)
fixed(S/'MF.json','0263f752fa68b7017bae2cb9b0b91d4107ce00d878b359bd490ec3790e5d9fda',2921)
for d in (C,S):
 for v in read(d/'MF.json')['members']:verify(v)
isolation=read(I/'isolation.ready.json');actual=read(A/'validation.closed.json')
for k in ('source_overlay_ref','formatted_source_ref','compiler_inventory_ref','compiled_test_ref','canonical_pre_run_ref'):verify(actual[k])
for k in ('sparse_checkout_ref','project_identity_ref'):verify(isolation[k])
ck('failed-status-original-retained',actual['status']=='FAILED_HISTORY20_FIVE_PARENT_COMPILE_OR_TARGET_EXECUTION_CLOSED' and actual['error']=='AssertionError()')
failure=read(C/'postseal-failure-origin.914.json');add(C/'postseal-failure-origin.914.json')
ck('914-single-origin-qualified-exits',failure['ordinal']==914 and failure['attempt_count']==1 and failure['actual_outer_exit']==failure['actual_python_exit']==failure['actual_native_exit']==1 and failure['actual_test_binary_exit'] is None)
ck('isolation-original-initial-session',failure['original_isolation_initial']['chunk_id']=='ac2b92' and failure['original_isolation_initial']['session_id']==18654)
finaliso=failure['original_isolation_polls'][-1]
ck('isolation-original-final-exit',finaliso['chunk_id']=='a14101' and finaliso['exit_code']==0 and 'ROOT_PYTHON_EXIT=0' in finaliso['output'])
ck('validation-original-session',failure['original_validation_initial']['chunk_id']=='2a83a5' and failure['original_validation_initial']['session_id']==23379)
f=failure['original_validation_completion']
ck('validation-original-final-exit',f['chunk_id']=='f53be7' and f['exit_code']==1 and 'ROOT_PYTHON_EXIT=1' in f['output'])
jobs=[];results={}
for category,refs in [('isolation',isolation['invocation_refs']),('validation',actual['invocation_refs'])]:
 for v in refs:
  verify(v);p=P(v['path']);raw=p.read_text(encoding='utf-8');o=json.loads(raw);r=o['result'];j=r['job_cleanup'];label=p.name.removesuffix('.invocation.json')
  expected=1 if label=='history20-five-parent-jsonl' else 0
  ck('actual-exit:'+label,o['actual_native_exit']==r['actual_exit']==expected)
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
guards=[]
for d,names in [(I,['source','runtime-source']),(A,['input-source','runtime-source','candidate-source','compiler-source','binary-source'])]:
 for name in names:
  p=d/(name+'-guard.cleanup.actual.json');add(p);g=read(p)
  ck('actual-guard-closed:'+str(p),g['closed'] and not g['errors'] and g['retained_handles_count']==0 and g['failure'] is None)
  ck('actual-guard-entry-closure:'+str(p),all(e['verified'] and e['final_path_match'] and e['closed'] for e in g['entries']))
  for e in g['entries']:verify(e)
  guards.append(dict(ref=pin(p),entries=len(g['entries']),closed=True,no_retained_handles=True))
ck('seven-actual-guards',len(guards)==7)
save('actual-guard-audit.json',guards)
for d in (I,A):
 add(d/'canonical.pre-run.exact.json');c=read(d/'canonical.pre-run.exact.json');ck('canonical-revision364:'+str(d),c['revision']==364)
 for v in c['refs']:verify(v);canonical_paths.add(str(P(v['path']).resolve()).casefold())
ck('same-four-canonical-pins',read(I/'canonical.pre-run.exact.json')['refs']==read(A/'canonical.pre-run.exact.json')['refs'])
ck('live-CP364',read(R/'execution/v2.4/checkpoint.json')['revision']==364)
dirty=(I/'tracked-status.stdout.raw').read_text(encoding='utf-8').splitlines()
ck('actual-original-dirty-13-and11D',dirty==isolation['tracked_dirty_paths'] and len(dirty)==13 and sum(x.startswith(' D ') for x in dirty)==11)
ck('actual-original-empty-index',not (I/'staged-status.stdout.raw').read_bytes().strip())
for p in (I/'head-before.stdout.raw',I/'head-after.stdout.raw'):ck('isolation-HEAD:'+str(p),p.read_text(encoding='utf-8').strip()=='adc460c2138528f163f7fdab5e8d81dde157b7fb')
ck('no-post-validation-Git-claimed',len(isolation['invocation_refs'])==6)
overlay=read(actual['source_overlay_ref']['path']);composition=read(C/'composition.json')
ck('61-preformat-source-composition',overlay['sources']==composition['final_sources'] and len(overlay['sources'])==61)
choice=read(C/'source.integration.choice.json');verify(choice['actual_T11_overlay_ref']);t11=read(choice['actual_T11_overlay_ref']['path'])['sources']
h20=set(choice['h20_candidate_paths'])
ck('non-H20-T11-preserved',all(overlay['sources'][k]==v for k,v in t11.items() if k not in h20))
ck('AF-exact',overlay['sources']['internal/domain/client_protocol_attach_contract_windows_test.go']==t11['internal/domain/client_protocol_attach_contract_windows_test.go'])
formatted=read(actual['formatted_source_ref']['path']);ck('61-formatted-members',len(formatted)==61)
format_delta=[]
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
runner=results['history20-five-parent-jsonl']
ck('official-primary-and-actual-binary',runner['argv'][0]==inv['test2json_executable_ref']['path'] and runner['argv'][4]==actual['compiled_test_ref']['path'] and inv['test2json_executable_ref']['sha256']=='dead8050fd4e0e0471407380898fe9642b9107048e0ad119cb652821dfe58f7c')
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
ck('8PASS1FAIL0SKIP',collections.Counter(actions.values())=={'pass':8,'fail':1})
ck('only-public-upgrade-fails',[k for k,v in actions.items() if v=='fail']==['TestHistory20PublicUpgradePreservesSourceAndRevokesRestoredCredentials'])
ck('package-final-fail',events[-1]['Action']=='fail' and 'Test' not in events[-1])
errors=[e for e in outputs if e.get('OutputType')=='error']
ck('actual-error-line91',len(errors)==1 and 'backup_history20_upgrade_test.go:91: UPGRADE_PATH_OVERLAP: source, key, snapshot and target require separate directories' in errors[0]['Output'])
save('terminal-audit.json',dict(started=starts,actions=actions,actual_error_events=errors,primary_test2json_exit=1,descendant_test_binary_exit=None,final_package_action=events[-1]['Action']))
test=(T/'internal/domain/backup_history20_upgrade_test.go').read_text(encoding='utf-8')
upgrade=(T/'internal/domain/backup_history20_upgrade.go').read_text(encoding='utf-8')
paths=(T/'internal/domain/backup_upgrade.go').read_text(encoding='utf-8')
backup=(T/'internal/domain/backup.go').read_text(encoding='utf-8')
ck('fixture-collision-source-key','Source: filepath.Join(base, "source.sqlite")' in test and 'KeyFile: filepath.Join(base, "recovery.key")' in test)
ck('fixture-collision-descendants','Snapshot: filepath.Join(base, "backup")' in test and 'Destination: filepath.Join(base, "candidate")' in test)
ck('first-upgrade-guard-precedes-release',upgrade.index('upgradePaths(&opt)')<upgrade.index('sourceRelease, _, e := upgradeHistory20Release'))
ck('production-overlap-guard-preserved','dirs := []string{filepath.Dir(opt.Source), filepath.Dir(opt.KeyFile), opt.Snapshot, opt.Destination}' in paths and 'upgradeInside(a, b) || upgradeInside(b, a)' in paths)
drift=test.split('func TestHistory20RejectsReleaseAndSourceDrift',1)[1].split('func TestHistory20MigrationRollsBack',1)[0]
ck('drift-any-error-not-specific','if err == nil {' in drift and 'err.Error()' not in drift and 'strings.Contains(err.Error()' not in drift)
generic=test.split('func TestHistory20RestoreFailureRetainsEncryptedBackupAndSource',1)[1].split('func TestHistory20ImplicitStartup',1)[0]
ck('generic-callback-not-observed','return context.Canceled' in generic and 'if err == nil {' in generic and 'errors.Is' not in generic and 'called' not in generic and 'reached' not in generic)
ck('callback-error-wrapped-for-future-Is','MIGRATION_FAILED: isolated copy discarded; stable backup retained: %w' in backup)
ck('ledger-rollback-specific','strings.Contains(err.Error(), "fixture ledger failure")' in test and 'before != after || Hash(rows) != Hash(now)' in test)
ck('startup-specific','strings.Contains(err.Error(), "MIGRATION_PREBACKUP_REQUIRED")' in test)
gp=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
fixed(gp,'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85',11404)
raw=gp.read_bytes();m=types.ModuleType('h20a914_independent_source_guard');m.__file__=str(gp);sys.modules[m.__name__]=m;exec(compile(raw,str(gp),'exec'),m.__dict__)
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
print(json.dumps(dict(check_count=len(checks),input_count=len(inputs),failed=[v for v in checks if not v['passed']],format_changed=len(format_delta),guard_released=cleanup['closed'],actual_reviewer_Git_Go_SQL_native_model=False),ensure_ascii=True))

