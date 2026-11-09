import json,hashlib,pathlib,subprocess,datetime,re,sys
R=pathlib.Path('D:/作品集/ResearchOS/research-os'); O=pathlib.Path(__file__).parent
P=R/'.local/worktrees/codex-w0599-provider-binding'; H=R/'.local/worktrees/codex-w0599-host-configuration-handler'
PRE='execution/v2.4/receipts/W05/W05-99/'
C='6fb5263681c17f0e50920c354dc07ed440a23714'; B='396287cc5427eb125aaedb8a2b7fadf63e6b9322'
def sha(b): return hashlib.sha256(b).hexdigest()
def put(n,v):
 p=O/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');return ref(p)
def ref(p):
 b=p.read_bytes();return {'path':str(p).replace('\\','/'),'sha256':sha(b),'bytes':len(b)}
inputs=[]
def snap(label,base,rel):
 p=base/rel;b=p.read_bytes(); dest=O/'snapshots'/label/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
 row={'label':label,'relative_path':rel,'original':ref(p),'snapshot':ref(dest)};inputs.append(row);return b
inv=[]
def git(base,*args):
 a=['git','-C',str(base),*args]; t=datetime.datetime.now(datetime.timezone.utc).isoformat(); q=subprocess.run(a,capture_output=True);i=len(inv); (O/f'git-{i}.stdout.raw').write_bytes(q.stdout);(O/f'git-{i}.stderr.raw').write_bytes(q.stderr);inv.append({'argv':a,'at':t,'actual_exit_code':q.returncode,'stdout':ref(O/f'git-{i}.stdout.raw'),'stderr':ref(O/f'git-{i}.stderr.raw')});
 if q.returncode: raise RuntimeError('readonly git failed')
 return q.stdout
paths=['adapters/runtime/mu/worker.mjs','adapters/runtime/mu/worker-provider-binding.test.mjs','internal/domain/runtime_model.go','internal/domain/runtime_broker_windows.go','internal/domain/runtime_model_windows.go','internal/domain/runtime_model_stream.go','internal/domain/runtime_model_verification.go','internal/domain/runtime_provider_binding_test.go','internal/domain/runtime_provider_binding_windows_test.go']
heads={name:git(base,'rev-parse','HEAD').decode().strip() for name,base in [('candidate',P),('main',R),('handler_unfrozen',H)]};assert heads['candidate']==C
sources=[]
for rel in paths:
 b=snap('candidate',P,rel);blob=git(P,'show',C+':'+rel);assert b==blob
 row={'path':rel,'candidate_sha256':sha(b),'git_blob_bytes_equal':True,'main_exists':(R/rel).is_file()}
 if row['main_exists']: row['main_sha256']=sha(snap('main',R,rel));row['main_equal']=row['main_sha256']==row['candidate_sha256']
 sources.append(row)
diff=git(P,'diff',B,C,'--',*paths);(O/'candidate-whole9.diff').write_bytes(diff)
scope_rel=PRE+'integration_codex/handler-source-scope-r287/scope_registration.json'
scope=json.loads(snap('main',R,scope_rel)); hp=[x['path'] for x in scope['exact_source_scope']]
cli6=['apps/cli/cli_continuation_test.go','apps/cli/cli_doctor_test.go','apps/cli/cli_first_use_integration_windows_test.go','apps/cli/cli_model_stream_integration_windows_test.go','apps/cli/cli_queue_integration_windows_test.go','apps/cli/cli_sessions_test.go']
for rel in hp+cli6: snap('handler_unfrozen',H,rel)
for rel in ['adapters/runtime/mu/build.mjs','adapters/runtime/mu/package.json','adapters/runtime/mu/worker-stream.test.mjs','adapters/runtime/mu/worker-control.test.mjs']: snap('candidate',P,rel)
for rel in ['apps/cli/cli_contract.go','internal/domain/runtime_model_stream_windows_test.go','internal/domain/runtime_command_queue_windows_test.go','internal/domain/backup_command_queue.go','internal/domain/backup_host_configuration.go','internal/domain/store.go']: snap('main',R,rel)
author=PRE+'provider_binding_executor_codex/provider-39d6478d4a884156b0881788325e4c63/'
for name in ['handoff.json','P01-P12-evidence-matrix.json','held_candidate_10_seal.json','failure_origins.v2.json','current-test-counts.json']: snap('candidate',P,author+name)
for rel in [PRE+'integration_codex/configuration-main-scope-r282/scope_registration.json',PRE+'integration_codex/cli6-and-reference-closure-r294/cli6_scope_amendment.json']:
 snap('main',R,rel)
prior=PRE+'provider_typed_route_independent_replay_codex/public-r294-1816149c-d1d2-4998-b76b-2acd0ed57126/'
for n in ['review.json','handoff.json','public-resource-chains.json','public-refusal-causes.json']: snap('main',R,prior+n)
put('source_comparison.json',{'heads':heads,'source9':sources,'candidate_handler_exact33_path_intersection':sorted(set(paths)&set(hp+cli6)),'handler_exact33':hp+cli6,'handler_is_mutable':True,'no_handler_source_ready':True})
put('git_invocations.json',inv)
selectors={}
for x in inputs:
 if x['relative_path'].endswith('.go'):
  text=pathlib.Path(x['snapshot']['path']).read_text(encoding='utf-8-sig'); names=re.findall(r'^func (Test\w+)\(',text,re.M)
  if names: selectors[x['label']+':'+x['relative_path']]=names
put('actual_selector_inventory.json',selectors)
after=[]
for x in inputs:
 p=pathlib.Path(x['original']['path']);a=ref(p);after.append({'path':a['path'],'before_sha256':x['original']['sha256'],'after_sha256':a['sha256'],'unchanged':a['sha256']==x['original']['sha256'],'handler_mutable_observation_only':x['label']=='handler_unfrozen'})
put('read_audit.json',{'operation':'read public source/Git/JSON only; copy exact snapshots to own namespace','inputs':inputs,'after':after,'input_count':len(inputs),'all_observed_unchanged':all(x['unchanged'] for x in after),'qualification_compile_closure':False,'cases':0,'sql':0,'node':0,'model':0,'http':0,'paid':0,'private_or_holdout_data':0,'production_mutations':0})
print(json.dumps({'own':str(O),'heads':heads,'source9':sources,'scope_intersection':sorted(set(paths)&set(hp+cli6)),'inputs':len(inputs),'drift':[x for x in after if not x['unchanged']]},ensure_ascii=False))
