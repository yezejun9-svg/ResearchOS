from pathlib import Path
import ast, hashlib, json, traceback
R=Path('D:/作品集/ResearchOS/research-os'); P=R/'execution/v2.4/receipts/W05/W05-99'; O=Path(__file__).parent
N=P/'integration_codex/cli43-fresh-held2-r328-bf943a8137c74df09e010347615b0eec'
OLD=P/'integration_codex/cli43-fresh-held2-r327-efa7776ec48e4a7abaa92ce85eb0dace'
checks=[]; refs={}
def path(x):
 p=Path(x); return p if p.is_absolute() else R/p
def ref(x):
 p=path(x); b=p.read_bytes(); a={'path':p.as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}; refs[a['path']]=a; return a
def ck(n,v): checks.append({'check':n,'passed':bool(v)})
def verify(x):
 p=path(x['path']); a=ref(p); ck('pin '+a['path'],a['sha256']==x['sha256'] and a['bytes']==x['bytes']); return p
def read(x): ref(x); return json.loads(path(x).read_bytes())
def save(n,x):
 with (O/n).open('x',encoding='utf-8',newline='\n') as f: json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False); f.write('\n')
try:
 pins={'scope_registration.json':'edec4df6c5f4fcce632008517adff4c4b2a82f64bc4715d87c8a53e7fd3e19c3','bound-scope.manifest.json':'067dfda05d366176a6b7e3779b6d558ee6050d721f67e7ad2bf324f307bb5ff8','runtime-with-root-metadata.v4.json':'2748157e7e90b13cf62935805a2b1de7c3c960317d1d6d4031d684e6a1172c27'}
 for n,h in pins.items(): ck('supplied '+n,ref(N/n)['sha256']==h)
 mf=read(N/'bound-scope.manifest.json')
 for x in mf['entries']: verify(x)
 ck('31 unique manifest members self excluded',len(mf['entries'])==31 and len({path(x['path']) for x in mf['entries']})==31 and mf['self_excluded'] is True and N/'bound-scope.manifest.json' not in {path(x['path']) for x in mf['entries']})
 s=read(N/'scope_registration.json'); old=read(OLD/'scope_registration.json'); b=read(N/'binding.pre-review.json'); inp=read(N/'root-inputs.runtime-bound.json')
 for obj in [s,b,inp,inp['r328_changed_input_provenance']]:
  for k,v in obj.items():
   if k.endswith('_ref') and isinstance(v,dict) and 'sha256' in v: verify(v)
 ck('exact schema',s['schema']=='researchos.cli43-fresh-compiler-held2-scope.v2')
 ck('review path acyclic',path(s['controller_review_path'])==O/'review.json' and b['controller_review_path']==s['controller_review_path'] and b['controller_review_ref'] is None and inp['controller_review_ref'] is None)
 ck('tuple before after',s['expected_before_registration']==b['before']==inp['before']==[327,155,459] and s['expected_registration']==b['after']==inp['after']==[328,156,469])
 delta={k for k in s if s[k]!=old.get(k)}
 expected={'run_uuid','new_output_root','new_wrapper_root','new_export_root','new_authorization_root','registration_namespace','expected_registration','expected_before_registration','runner_ref','debug_tree_helper_ref','runtime_resources_ref','controller_review_path','new_grant_preflight_root'}
 ck('full scope declared delta only',s.keys()==old.keys() and delta==expected)
 roots=[s[k] for k in ['new_output_root','new_wrapper_root','new_export_root','new_authorization_root','new_grant_preflight_root']]
 ck('five distinct fresh leaves absent',len(set(roots))==5 and all(not path(x).exists() for x in roots))
 ck('prepare not begun',all(not (N/x).exists() for x in ['binding.json','prepare.started.json']))
 c=read(N/'canonical-before.json'); cp=read(R/'execution/v2.4/checkpoint.json'); ow=read(R/'execution/v2.4/path_ownership.json')
 ck('current tuple head',b['before']==[cp['revision'],ow['revision'],len(cp['failure_counters'])] and cp['head']==s['source_commit'])
 ck('ordered canonical4',[x['canonical_path'] for x in c['entries']]==['execution/v2.4/'+x+'.json' for x in ['checkpoint','path_ownership','step_state','commands']])
 desired=read(OLD/'prepared_refs.json')['desired_refs']
 for i,x in enumerate(c['entries']):
  p=verify(x['ref']); verify(x['live_original_ref']); d=verify(desired[i]); ck('current snapshot previous desired exact '+str(i),p.read_bytes()==(R/x['canonical_path']).read_bytes()==d.read_bytes())
 head=(R/'.git/HEAD').read_text(encoding='utf-8').strip(); headpath=R/'.git'/head[5:] if head.startswith('ref: ') else None
 actualhead=headpath.read_text(encoding='utf-8').strip() if headpath else head
 ck('direct Git HEAD same no native query',actualhead==s['source_commit']); ref(R/'.git/HEAD')
 if headpath: ref(headpath)
 prefix=read(N/'failure-prefix430.json'); ck('historical430 prefix intact',prefix['failure_counters']==cp['failure_counters'][:430])
 cut=read(N/'failure-origins.cut.json'); late=read(OLD/'late-origins.capture.for-r328.json')
 ck('fixed10 exact original capture',cut['origins']==late['origins'] and len(cut['origins'])==10 and cut['before']==b['before'] and cut['after']==b['after'] and cut['counter_reset'] is False)
 hashes=[]
 for i,row in enumerate(cut['origins']):
  payload=read(verify(row['evidence_ref'])); h=row['evidence_ref']['sha256']; hashes.append(h); ck('original payload unchanged '+str(i),payload==row['original_payload'])
  ck('not already current459 '+str(i),all(x.get('evidence_ref',{}).get('sha256')!=h for x in cp['failure_counters']))
  if 'original_container_ref' in row:
   container=read(verify(row['original_container_ref'])); ck('ZIP original container row exact '+str(i),container==row['original_container_payload'] and container['origins'][row['original_origin_index']]==row['original_origin_row'])
   ck('ZIP native remains NULL '+str(i),row['original_origin_row']['actual_native_exit'] is None)
 ck('ten unique underlying origins',len(set(hashes))==10 and hashes.count('a079d11193f27a3d8a4b0909c7865ae43230a4d83044f40e37bd4101bcb7e1e8')==1 and cut['nested_launch_exits_counted_once'] is True)
 ck('late3 remain outside fixed cut',late['observed_including_later_pending_at_capture']==472 and len(late['later_peer_origins_not_in_fixed_cut'])==3)
 controls=b['metadata_code_refs']; ck('exact eight metadata refs',len(controls)==8 and controls==read(N/'metadata-code-refs.json')['entries'])
 rt=read(verify(s['runtime_resources_ref'])); ort=read(verify(old['runtime_resources_ref'])); ck('1250 catalog original1242 unchanged',len(rt['files'])==1250 and rt['files'][:1242]==ort['files'][:1242])
 projected=[]
 for x in controls:
  p=verify(x); a=ref(p); ck('relative serialized exact '+p.name,x=={'path':p.relative_to(R).as_posix(),'sha256':a['sha256'],'bytes':a['bytes']}); projected.append({**x,'path':str(p.absolute())}); ast.parse(p.read_bytes())
  if p.parent==N: ck('wrapper same bytes '+p.name,p.read_bytes()==(OLD/p.name).read_bytes())
 ck('metadata ABS runtime membership exact',rt['files'][1242:]==projected)
 for key in ['runner_ref','launcher_ref','authorization_gate_ref','owned_process_helper_ref','debug_tree_helper_ref']:
  x=s[key]; p=verify(x); a=ref(p); ck('controller Windows ABS canonical '+key,x=={'path':str(p.absolute()),'sha256':a['sha256'],'bytes':a['bytes']}); ast.parse(p.read_bytes())
 template=read(N/'scope.template.runner-v7.json'); ot=read(OLD/'scope.template.runner-v6.json'); td={k for k in template if template[k]!=ot.get(k)}
 ck('template only runner diagnostic helper',template.keys()==ot.keys() and td=={'runner_ref','debug_tree_helper_ref'} and all(template[k]==s[k] for k in td))
 driver=(N/'root-metadata-phase.py').read_bytes(); ref(N/'root-metadata-phase.py'); olddriver=(OLD/'root-metadata-phase.py').read_bytes(); ref(OLD/'root-metadata-phase.py'); ast.parse(driver)
 ck('driver only scope SHA anchor',driver.count(pins['scope_registration.json'].encode())==1 and driver.replace(pins['scope_registration.json'].encode(),ref(OLD/'scope_registration.json')['sha256'].encode())==olddriver)
 ck('driver serialized ScopeRef matches Reader relative',b"scope_ref['path'] = (OUT / 'scope_registration.json').relative_to(ROOT).as_posix()" in driver)
 ck('source597 catalog same',read(N/'source-inputs.json')==read(OLD/'source-inputs.json') and len(read(N/'source-inputs.json')['files'])==597)
 for name in ['binding-build.invocation.json','scope-build.invocation.json']:
  x=read(N/name); verify(x['stdout_ref']); verify(x['stderr_ref']); ck('metadata0 explicit stage schema '+name,x['actual_native_exit']==0 and 'error' in x and x['error'] is None and x['product_executed'] is False and x['automatic_retry'] is False)
 stable=['limits','launch_limits','ordered_cases','public_environment','instrumentation_ref','instrumented_source_ref','instrumentation_helper_ref','roster_ref','compiler_resources_ref','catalog_ref','main_git','python_flags']
 ck('caps business resources preserved',all(s[k]==old[k] for k in stable))
 ck('no acceptance no retry',s['source_acceptance'] is False and s['Main_integration_authorized'] is False and s['formal_increment']==0 and s['same_input_automatic_retry'] is False and s['first_unexpected_stop'] is True)
 reused=[ref(P/'cli43_current_bound_scope_independent_review_codex/bbd110051f5647d8b6386372ed2cd08c/review.json'),ref(P/'cli43_root_binding_static_independent_review_codex/c1a6b02b51ac427eb35ea000155db1c7/review.json'),inp['r328_changed_input_provenance']['test2json_preparation_review_ref'],inp['r328_changed_input_provenance']['prior_run_independent_failed_closure_ref']]
 for x in reused: verify(x)
 for x in list(refs.values()):
  raw=path(x['path']).read_bytes(); ck('after unchanged '+x['path'],hashlib.sha256(raw).hexdigest()==x['sha256'] and len(raw)==x['bytes'])
 save('audit.json',{'checks':checks,'failed_checks':[x for x in checks if not x['passed']],'input_refs':list(refs.values()),'facts':{'scope_delta_keys':sorted(delta),'template_delta_keys':sorted(td),'canonical_before':c['entries'],'before':b['before'],'after':b['after'],'cut_origin_refs':[x['evidence_ref'] for x in cut['origins']],'reused_review_refs':reused,'fresh_roots':roots,'backing_compiler_OS_trees_rehashed':False,'future_graph_complete':None,'future_OS_lifecycle_complete':None,'future_time_fit':None,'source_status_index_basis':'unchanged saved Main facts; current four canonical bytes and direct HEAD checked, no new Git status command'},'target_executions':0,'new_failure_origins':[]})
 print(json.dumps({'checks':len(checks),'failed_checks':[x for x in checks if not x['passed']],'audit_ref':ref(O/'audit.json')},ensure_ascii=False))
except BaseException as e:
 save('audit.failure.json',{'error':repr(e),'traceback':traceback.format_exc(),'checks':checks,'input_refs':list(refs.values()),'target_executions':0}); raise
