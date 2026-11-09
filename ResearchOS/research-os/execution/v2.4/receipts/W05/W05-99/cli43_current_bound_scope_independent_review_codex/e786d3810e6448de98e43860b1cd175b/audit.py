from pathlib import Path
import ast,hashlib,json,traceback
R=Path('D:/作品集/ResearchOS/research-os');P=R/'execution/v2.4/receipts/W05/W05-99';O=Path(__file__).parent
N=P/'integration_codex/cli43-fresh-held2-r330-b802270f725f47dc86f9ec829a60931a'
OLD=P/'integration_codex/cli43-fresh-held2-r329-246c20b781664b0e80fae7fd29b9b2b4'
checks=[];refs={}
def path(x):
 p=Path(x);return p if p.is_absolute() else R/p
def ref(x):
 p=path(x);b=p.read_bytes();a={'path':p.as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};refs[a['path']]=a;return a
def ck(n,v):checks.append({'check':n,'passed':bool(v)})
def verify(x):
 p=path(x['path']);a=ref(p);ck('pin '+a['path'],a['sha256']==x['sha256'] and a['bytes']==x['bytes']);return p
def read(x):ref(x);return json.loads(path(x).read_bytes())
def save(n,x):
 with (O/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
try:
 pins={'scope_registration.json':'b9b29be36829a2f85fc666da222ca64d7654916062ef8504b7ef0f3a5ab89359','bound-scope.manifest.json':'fbcb4505f642fdddac3aa9e1036fbd91c89ab795fdbd4eac51c69505a049fd5f','runtime-with-root-metadata.v4.json':'035940835570659170b78308b5ddf8198fedad3b3a2424dcbe0e300b5a22b49a'}
 for n,h in pins.items():ck('supplied '+n,ref(N/n)['sha256']==h)
 mf=read(N/'bound-scope.manifest.json')
 for x in mf['entries']:verify(x)
 ck('31 unique manifest entries',len(mf['entries'])==len({path(x['path']) for x in mf['entries']})==31 and mf['self_excluded'] is True)
 s=read(N/'scope_registration.json');old=read(OLD/'scope_registration.json');b=read(N/'binding.pre-review.json');inp=read(N/'root-inputs.runtime-bound.json');prov=inp['r330_changed_input_provenance']
 for obj in [s,b,inp,prov]:
  for k,v in obj.items():
   if k.endswith('_ref') and isinstance(v,dict) and 'sha256' in v:verify(v)
 ck('scope exact schema',s['schema']=='researchos.cli43-fresh-compiler-held2-scope.v2')
 ck('review path no SHA cycle',path(s['controller_review_path'])==O/'review.json' and b['controller_review_path']==s['controller_review_path'] and b['controller_review_ref'] is None and inp['controller_review_ref'] is None)
 ck('tuple before after',s['expected_before_registration']==b['before']==inp['before']==[329,157,481] and s['expected_registration']==b['after']==inp['after']==[330,158,502])
 delta={k for k in s if s[k]!=old.get(k)}
 expected={'run_uuid','new_output_root','new_wrapper_root','new_export_root','new_authorization_root','registration_namespace','expected_registration','expected_before_registration','instrumentation_ref','instrumentation_helper_ref','instrumented_source_ref','runtime_resources_ref','controller_review_path','new_grant_preflight_root'}
 ck('complete declared scope delta only',s.keys()==old.keys() and delta==expected)
 roots=[s[k] for k in ['new_output_root','new_wrapper_root','new_export_root','new_authorization_root','new_grant_preflight_root']]
 ck('five distinct absent leaves',len(set(roots))==5 and all(not path(x).exists() for x in roots))
 ck('prepare not begun',all(not (N/x).exists() for x in ['binding.json','prepare.started.json']))
 c=read(N/'canonical-before.json');cp=read(R/'execution/v2.4/checkpoint.json');ow=read(R/'execution/v2.4/path_ownership.json')
 ck('live tuple head',b['before']==[cp['revision'],ow['revision'],len(cp['failure_counters'])] and cp['head']==s['source_commit'])
 ck('ordered canonical4',[x['canonical_path'] for x in c['entries']]==['execution/v2.4/'+x+'.json' for x in ['checkpoint','path_ownership','step_state','commands']])
 desired=read(OLD/'prepared_refs.json')['desired_refs']
 for i,x in enumerate(c['entries']):
  p=verify(x['ref']);verify(x['live_original_ref']);d=verify(desired[i]);ck('live snapshot prior desired '+str(i),p.read_bytes()==(R/x['canonical_path']).read_bytes()==d.read_bytes())
 head=(R/'.git/HEAD').read_text(encoding='utf-8').strip();hp=R/'.git'/head[5:] if head.startswith('ref: ') else None
 ck('direct HEAD without Git invocation',(hp.read_text(encoding='utf-8').strip() if hp else head)==s['source_commit']);ref(R/'.git/HEAD')
 if hp:ref(hp)
 prefix=read(N/'failure-prefix430.json');ck('old430 preserved within481',prefix['failure_counters']==cp['failure_counters'][:430])
 cut=read(N/'failure-origins.cut.json');late=read(verify(prov['late_cut_capture_ref']))
 ck('exact21 frozen cut',cut['origins']==late['origins'] and len(cut['origins'])==21 and cut['before']==b['before'] and cut['after']==b['after'] and cut['counter_reset'] is False)
 hashes=[];mapping=[]
 for i,row in enumerate(cut['origins']):
  payload=read(verify(row['evidence_ref']));h=row['evidence_ref']['sha256'];hashes.append(h)
  ck('full original payload '+str(i),payload==row['original_payload'])
  ck('not in old481 '+str(i),all(x.get('evidence_ref',{}).get('sha256')!=h for x in cp['failure_counters']))
  if 'original_container_ref' in row:
   container=read(verify(row['original_container_ref']));original=container['new_origins'][row['original_origin_index']]
   ck('mapping original container and row '+str(i),container==row['original_container_payload'] and original==row['original_origin_row']==payload and row['leaf_extraction_only_not_new_execution'] is True)
   mapping.append({'index':i,'evidence_ref':row['evidence_ref'],'original_container_ref':row['original_container_ref'],'original_origin_index':row['original_origin_index'],'original_native_exit':payload['native_exit']})
 ck('21 unique and one r329 cause',len(set(hashes))==21 and hashes.count('6da76d8b2958f08c6aba95d471149c137f3f25dcd4ac74e4081e9ffc16c44d23')==1 and cut['nested_launch_exits_counted_once'] is True)
 ck('all current cut rows direct full payload',len(mapping)==0)
 controls=b['metadata_code_refs'];ck('eight metadata refs',len(controls)==8 and controls==read(N/'metadata-code-refs.json')['entries'])
 rt=read(verify(s['runtime_resources_ref']));ort=read(verify(old['runtime_resources_ref']));ck('1250 original1242 exact',len(rt['files'])==1250 and rt['files'][:1242]==ort['files'][:1242])
 projected=[]
 for x in controls:
  p=verify(x);a=ref(p);ck('ROOT-relative serialization '+p.name,x=={'path':p.relative_to(R).as_posix(),'sha256':a['sha256'],'bytes':a['bytes']});projected.append({**x,'path':str(p.absolute())});ast.parse(p.read_bytes())
  if p.parent==N:ck('wrapper unchanged '+p.name,p.read_bytes()==(OLD/p.name).read_bytes())
 ck('ABS metadata runtime membership',rt['files'][1242:]==projected)
 for k in ['runner_ref','launcher_ref','authorization_gate_ref','owned_process_helper_ref','debug_tree_helper_ref']:
  x=s[k];p=verify(x);a=ref(p);ck('canonical ABS code '+k,x=={'path':str(p.absolute()),'sha256':a['sha256'],'bytes':a['bytes']} and x==old[k]);ast.parse(p.read_bytes())
 template=read(N/'scope.template.runner-v7.json');ot=read(OLD/'scope.template.runner-v7.json');td={k for k in template if template[k]!=ot.get(k)}
 ck('template only instrumentation three refs',template.keys()==ot.keys() and td=={'instrumentation_ref','instrumentation_helper_ref','instrumented_source_ref'} and all(template[k]==s[k] for k in td))
 driver=(N/'root-metadata-phase.py').read_bytes();ref(N/'root-metadata-phase.py');od=(OLD/'root-metadata-phase.py').read_bytes();ref(OLD/'root-metadata-phase.py');ast.parse(driver)
 ck('outer driver one scope SHA only',driver.count(pins['scope_registration.json'].encode())==1 and driver.replace(pins['scope_registration.json'].encode(),ref(OLD/'scope_registration.json')['sha256'].encode())==od)
 ck('ScopeRef ROOT-relative matches Reader',b"scope_ref['path'] = (OUT / 'scope_registration.json').relative_to(ROOT).as_posix()" in driver)
 prep=read(OLD/'stage-r330-source-preparation.json');stage=verify(prep['new_ref']);originalstage=verify(prep['old_ref']);raw=stage.read_bytes();ast.parse(raw)
 for e in reversed(prep['edits']):
  ck('stage replacement count '+e['old'][:80],raw.count(e['new'].encode())==e['actual_count']);raw=raw.replace(e['new'].encode(),e['old'].encode())
 ck('stage full byte inverse',raw==originalstage.read_bytes())
 generator=OLD/'prepare-r330-stage.py';ref(generator);ast.parse(generator.read_bytes())
 ck('source597 preserved',read(N/'source-inputs.json')==read(OLD/'source-inputs.json') and len(read(N/'source-inputs.json')['files'])==597)
 for name in ['binding-build.invocation.json','scope-build.invocation.json']:
  x=read(N/name);verify(x['stdout_ref']);verify(x['stderr_ref']);ck('actual metadata0 '+name,x['actual_native_exit']==0 and 'error' in x and x['error'] is None and x['product_executed'] is False and x['automatic_retry'] is False)
 stable=['limits','launch_limits','ordered_cases','public_environment','roster_ref','compiler_resources_ref','catalog_ref','main_git','python_flags']
 ck('caps business resources unchanged',all(s[k]==old[k] for k in stable))
 ck('no acceptance retry',s['source_acceptance'] is False and s['Main_integration_authorized'] is False and s['formal_increment']==0 and s['same_input_automatic_retry'] is False and s['first_unexpected_stop'] is True)
 reused=[ref(P/'cli43_current_bound_scope_independent_review_codex/2770189c101441f39fcbe8fd83d98ffd/review.json'),prov['ownership_preparation_review_ref'],prov['prior_run_independent_failed_closure_ref']]
 for x in reused:verify(x)
 for x in list(refs.values()):
  raw=path(x['path']).read_bytes();ck('after unchanged '+x['path'],hashlib.sha256(raw).hexdigest()==x['sha256'] and len(raw)==x['bytes'])
 save('audit.json',{'checks':checks,'failed_checks':[x for x in checks if not x['passed']],'input_refs':list(refs.values()),'facts':{'scope_delta_keys':sorted(delta),'template_delta_keys':sorted(td),'canonical_before':c['entries'],'before':b['before'],'after':b['after'],'cut_origin_refs':[x['evidence_ref'] for x in cut['origins']],'mapping':mapping,'reused_review_refs':reused,'fresh_roots':roots,'backing_compiler_OS_trees_rehashed':False,'future_graph_complete':None,'future_OS_lifecycle_complete':None,'future_time_fit':None,'source_status_index_basis':'Existing frozen Main status/index facts unchanged in scope; four current canonical bytes and direct HEAD checked, no new Git status command'},'target_executions':0,'new_failure_origins':[]})
 print(json.dumps({'checks':len(checks),'failed_checks':[x for x in checks if not x['passed']],'audit_ref':ref(O/'audit.json')},ensure_ascii=False))
except BaseException as e:
 save('audit.failure.json',{'error':repr(e),'traceback':traceback.format_exc(),'checks':checks,'input_refs':list(refs.values()),'target_executions':0});raise
