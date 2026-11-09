from pathlib import Path
import ast, hashlib, json, traceback
R=Path('D:/作品集/ResearchOS/research-os'); P=R/'execution/v2.4/receipts/W05/W05-99'; O=Path(__file__).parent
N=P/'integration_codex/cli43-fresh-held2-r327-efa7776ec48e4a7abaa92ce85eb0dace'
OLD=P/'integration_codex/cli43-fresh-held2-r326-477e329b79944cb0b33f9ead24811760'
checks=[]; refs={}
def path(p):
 p=Path(p); return p if p.is_absolute() else R/p
def ref(p):
 p=path(p); raw=p.read_bytes(); r={'path':p.as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}; refs[r['path']]=r; return r
def ck(name,value): checks.append({'check':name,'passed':bool(value)})
def verify(x):
 p=path(x['path']); a=ref(p); ck('pin '+a['path'],a['sha256']==x['sha256'] and a['bytes']==x['bytes']); return p
def read(p):
 ref(p); return json.loads(path(p).read_bytes())
def write(name,obj):
 with (O/name).open('x',encoding='utf-8',newline='\n') as f: json.dump(obj,f,ensure_ascii=False,indent=2,allow_nan=False); f.write('\n')
try:
 pins={'scope_registration.json':'320fef447b526c1696075c9ae11fe8439d582d893239ed659c486b21562f5137','bound-scope.manifest.json':'309e212b9a56d8421f8acd7b95163f76e70646df38c29e0b789bd2cdf07803af','runtime-with-root-metadata.v4.json':'311cac1ec99fdc41de58c1b9cc5200b43f0cb901e6ac658adfa0c50a59699fb8'}
 for name,h in pins.items(): ck('supplied '+name,ref(N/name)['sha256']==h)
 mf=read(N/'bound-scope.manifest.json')
 for x in mf['entries']: verify(x)
 ck('manifest unique self excluded',mf['self_excluded'] is True and len({path(x['path']) for x in mf['entries']})==len(mf['entries']) and N/'bound-scope.manifest.json' not in {path(x['path']) for x in mf['entries']})
 s=read(N/'scope_registration.json'); old=read(OLD/'scope_registration.json'); b=read(N/'binding.pre-review.json'); inp=read(N/'root-inputs.runtime-bound.json')
 for obj in [s,inp]:
  for k,v in obj.items():
   if k.endswith('_ref') and isinstance(v,dict) and 'sha256' in v: verify(v)
 ck('schema',s['schema']=='researchos.cli43-fresh-compiler-held2-scope.v2')
 ck('fixed own review path no hash cycle',path(s['controller_review_path'])==O/'review.json' and b['controller_review_path']==s['controller_review_path'] and b['controller_review_ref'] is None)
 ck('exact tuples',s['expected_before_registration']==b['before']==[326,154,450] and s['expected_registration']==b['after']==[327,155,459])
 delta={k for k in s if s[k]!=old[k]}
 expected={'run_uuid','new_output_root','new_wrapper_root','new_export_root','new_authorization_root','registration_namespace','expected_registration','expected_before_registration','runner_ref','runtime_resources_ref','controller_review_path','new_grant_preflight_root'}
 ck('whole scope only declared delta',s.keys()==old.keys() and delta==expected)
 roots=[s[k] for k in ['new_output_root','new_wrapper_root','new_export_root','new_authorization_root','new_grant_preflight_root']]
 ck('five unique fresh leaves absent',len(set(roots))==5 and all(not path(x).exists() for x in roots))
 ck('binding and prepare not begun',not (N/'binding.json').exists() and not (N/'prepare.started.json').exists())
 c=read(N/'canonical-before.json'); cp=read(R/'execution/v2.4/checkpoint.json'); ow=read(R/'execution/v2.4/path_ownership.json')
 ck('actual tuple and head',b['before']==[cp['revision'],ow['revision'],len(cp['failure_counters'])] and cp['head']==s['source_commit'])
 ck('ordered four canonicals',[x['canonical_path'] for x in c['entries']]==['execution/v2.4/'+x+'.json' for x in ['checkpoint','path_ownership','step_state','commands']])
 desired=read(OLD/'prepared_refs.json')['desired_refs']
 for i,x in enumerate(c['entries']):
  p=verify(x['ref']); verify(x['live_original_ref']); d=verify(desired[i]); ck('live equals copied and actual r326 desired '+x['canonical_path'],p.read_bytes()==(R/x['canonical_path']).read_bytes()==d.read_bytes())
 prefix=read(N/'failure-prefix430.json'); ck('historic430 exact prefix',prefix['failure_counters']==cp['failure_counters'][:430] and prefix['actual_origin_count']==430)
 cut=read(N/'failure-origins.cut.json'); late=read(OLD/'late-origins.capture.json')
 ck('cut nine exact tuples',cut['before']==b['before'] and cut['after']==b['after'] and len(cut['origins'])==9 and cut['counter_reset'] is False)
 hashes=[]
 for row in cut['origins']:
  payload=read(verify(row['evidence_ref'])); hashes.append(row['evidence_ref']['sha256']); ck('complete original payload '+hashes[-1],payload==row['original_payload']); ck('not already in450 '+hashes[-1],all(x.get('evidence_ref',{}).get('sha256')!=hashes[-1] for x in cp['failure_counters']))
 ck('eight late identities retained',hashes[:8]==[x['origin_ref']['sha256'] for x in late['origins']])
 for i,row in enumerate(late['origins']):
  p=cut['origins'][i]['original_payload']
  for token in row['payload_pointer'].strip('/').split('/') if row['payload_pointer'] else []: p=p[int(token)] if isinstance(p,list) else p[token]
  ck('original late pointer payload '+str(i),p==row['original_payload'])
 ck('single nested build origin ninth',hashes[-1]=='c28ce01137b787d3f1a331d2a738ada8310fa83ac7adeb9ef2c36d42b9ec74d5' and len(set(hashes))==9 and cut['nested_launch_exits_counted_once'] is True)
 ck('prospective full450 prefix plus9 not rewritten',len(cp['failure_counters']+cut['origins'])==459 and cut['native_NULL_fields_and_original_payloads_preserved'] is True)
 controls=b['metadata_code_refs']; ck('metadata8 exact inventory',len(controls)==8 and controls==read(N/'metadata-code-refs.json')['entries'])
 rt=read(verify(s['runtime_resources_ref'])); priorrt=read(verify(old['runtime_resources_ref'])); ck('original1242 exact reused',len(rt['files'])==1250 and rt['files'][:1242]==priorrt['files'][:1242])
 projected=[]
 for x in controls:
  p=verify(x); a=ref(p); ck('serialized relative pin '+p.name,x=={'path':p.relative_to(R).as_posix(),'sha256':a['sha256'],'bytes':a['bytes']}); projected.append({**x,'path':str(p.absolute())}); ast.parse(p.read_bytes())
  if p.parent==N: ck('wrapper unchanged '+p.name,p.read_bytes()==(OLD/p.name).read_bytes())
 ck('runtime metadata eight ABS exact',rt['files'][1242:]==projected)
 for key in ['runner_ref','launcher_ref','authorization_gate_ref','owned_process_helper_ref','debug_tree_helper_ref']:
  x=s[key]; p=verify(x); a=ref(p); ck('Windows ABS exact '+key,x=={'path':str(p.absolute()),'sha256':a['sha256'],'bytes':a['bytes']})
 runner=verify(s['runner_ref']); previous=verify(old['runner_ref']); raw=runner.read_bytes(); priorraw=previous.read_bytes()
 pair=[(b"run('build-cli',[go,'build','-p=1','-mod=readonly'",b"run('build-cli',[go,'build','-mod=readonly'"),(b"run('build-test',[go,'test','-c','-p=1','-mod=readonly'",b"run('build-test',[go,'test','-c','-mod=readonly'")]
 inv=raw
 for a,z in pair: ck('unique compiler delta '+a.decode(),inv.count(a)==1); inv=inv.replace(a,z,1)
 ck('whole runner inverse byte exact',inv==priorraw and len(raw)-len(priorraw)==14)
 ck('whole runner inverse AST exact',ast.dump(ast.parse(inv))==ast.dump(ast.parse(priorraw)))
 template=read(N/'scope.template.runner-v6.json'); oldtemplate=read(OLD/'scope.template.runner-v5.json'); td={k for k in template if template[k]!=oldtemplate[k]}; ck('template only runner',template.keys()==oldtemplate.keys() and td=={'runner_ref'} and template['runner_ref']==s['runner_ref'])
 driver=(N/'root-metadata-phase.py').read_bytes(); ref(N/'root-metadata-phase.py'); ast.parse(driver); olddriver=(OLD/'root-metadata-phase.py').read_bytes(); ref(OLD/'root-metadata-phase.py')
 ck('outerdriver exact scopeSHA replacement',driver.count(pins['scope_registration.json'].encode())==1 and driver.replace(pins['scope_registration.json'].encode(),ref(OLD/'scope_registration.json')['sha256'].encode())==olddriver)
 ck('source597 rows unchanged',read(N/'source-inputs.json')==read(OLD/'source-inputs.json') and len(read(N/'source-inputs.json')['files'])==597)
 for name in ['binding-build.invocation.json','scope-build.invocation.json']:
  x=read(N/name); verify(x['stdout_ref']); verify(x['stderr_ref']); ck('metadata native0 explicit schema '+name,x['actual_native_exit']==0 and 'error' in x and x['error'] is None and x['product_executed'] is False and x['automatic_retry'] is False)
 stage=OLD/'stage-r327-parallel.py'; stagecode=stage.read_bytes(); stagepin=ref(stage); ast.parse(stagecode)
 ck('stage supplied byte size and hashprefix',stagepin['bytes']==12945 and stagepin['sha256'].startswith('1245e90d'))
 st=stagecode.decode('utf-8'); ck('stage exclusive outputs and canonical invariance',"open('xb')" in st and "need(not OUT.exists()" in st and "OUT.mkdir()" in st and "'Canonical untouched by staging'" in st and "'Original r326 namespace byte prefix preserved'" in st)
 ck('stage invokes metadata labels only',[n.args[0].value for n in ast.walk(ast.parse(stagecode)) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='invoke' and n.args and isinstance(n.args[0],ast.Constant)]==['binding-build','scope-build'])
 reusedpaths=[P/'cli43_current_bound_scope_independent_review_codex/7403e1aa621c4378820a3f79247e5b19/review.json',P/'cli43_compiler_parallelism_static_independent_review_codex/3cd7de459bfb4caf8cbfa7044c75381c/review.json',P/'cli43_root_binding_static_independent_review_codex/c1a6b02b51ac427eb35ea000155db1c7/review.json',P/'cli43_current_bound_scope_independent_review_codex/46bfd2f723c84ad68e321774d6e08b30/review.json',P/'cli43_failed_execution_independent_review_codex/f41d184815b341e086a26d2a750f0b60/review.json']
 reused=[ref(p) for p in reusedpaths]
 for x in inp['r327_changed_input_provenance'].values():
  if isinstance(x,dict) and 'sha256' in x: verify(x)
 ck('v7 strict success marker unchanged',controls[6]['sha256']=='095d4f4b86ad0432bd559d2df7221d7f26794eb484f07d313fcc67d3a54f3eed')
 ck('immutable caps and instrumentation exactly prior',[s[k] for k in ['limits','launch_limits','ordered_cases','public_environment','instrumentation_ref','instrumented_source_ref','instrumentation_helper_ref','roster_ref','compiler_resources_ref','catalog_ref']]==[old[k] for k in ['limits','launch_limits','ordered_cases','public_environment','instrumentation_ref','instrumented_source_ref','instrumentation_helper_ref','roster_ref','compiler_resources_ref','catalog_ref']])
 # End-of-read check detects changes to all verified public receipt/code inputs; no backing-tree expansion.
 for x in list(refs.values()):
  p=path(x['path']); data=p.read_bytes(); ck('after same '+x['path'],hashlib.sha256(data).hexdigest()==x['sha256'] and len(data)==x['bytes'])
 facts={'scope_ref':ref(N/'scope_registration.json'),'scope_delta_keys':sorted(delta),'template_delta_keys':sorted(td),'bound_manifest_members':len(mf['entries']),'canonical_before':c['entries'],'before':b['before'],'after':b['after'],'origin_refs':[x['evidence_ref'] for x in cut['origins']],'original450_preserved':True,'stage_ref':stagepin,'reused_review_refs':reused,'fresh_leaves':roots,'metadata8_actual_rehash':True,'source597_rows_reused':True,'runtime1242_rows_reused':True,'compiler22138_backing_files_rehashed':False,'actual_future_graph':None,'OS_lifecycle_complete':None,'time_fit_proved':False,'prior_build_root_cause':None}
 write('audit.json',{'checks':checks,'failed_checks':[x for x in checks if not x['passed']],'facts':facts,'input_refs':list(refs.values()),'target_executions':0,'new_failure_origins':[]})
 print(json.dumps({'checks':len(checks),'failed_checks':[x for x in checks if not x['passed']],'audit_ref':ref(O/'audit.json')},ensure_ascii=False))
except BaseException as e:
 write('audit.failure.json',{'error':repr(e),'traceback':traceback.format_exc(),'completed_checks':checks,'input_refs':list(refs.values()),'target_executions':0}); raise
