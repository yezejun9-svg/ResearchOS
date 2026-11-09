from pathlib import Path
import json,ast,hashlib,traceback
R=Path('D:/作品集/ResearchOS/research-os');P=R/'execution/v2.4/receipts/W05/W05-99';O=Path(__file__).parent
N=P/'integration_codex/cli43-fresh-held2-r326-477e329b79944cb0b33f9ead24811760';OLD=P/'integration_codex/cli43-fresh-held2-r325-71b091d20d94443bbf4e732d201eeb29'
checks=[];refs={}
def path(x):
 p=Path(x);return p if p.is_absolute() else R/p
def ref(p):
 p=path(p);raw=p.read_bytes();r={'path':p.as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)};refs[r['path']]=r;return r
def ck(n,v):checks.append({'check':n,'passed':bool(v)})
def verify(x):
 p=path(x['path']);r=ref(p);ck('bytes '+r['path'],r['sha256']==x['sha256'] and r['bytes']==x['bytes']);return p
def read(p):ref(p);return json.loads(path(p).read_text(encoding='utf-8'))
def write(n,x):
 with (O/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
try:
 pins={'scope_registration.json':'68a0986a0bfcf39948ab2f696e33ef9ec05b39bb5a23f8787f92bf0129fe3566','bound-scope.manifest.json':'2765d881e585672395d68e68256f0520b93fc4bde6a174a55bd9a5376bdbc9c5','runtime-with-root-metadata.v4.json':'efeaa5f0464f28874de6a3bb55885f16c608d06d6717a7ccc166a8b135ff8cbc'}
 for n,h in pins.items():ck('Root pin '+n,ref(N/n)['sha256']==h)
 mf=read(N/'bound-scope.manifest.json')
 for x in mf['entries']:verify(x)
 s=read(N/'scope_registration.json');b=read(N/'binding.pre-review.json');old=read(OLD/'scope_registration.json');inp=read(N/'root-inputs.runtime-bound.json')
 for k,v in s.items():
  if k.endswith('_ref') and isinstance(v,dict) and 'sha256' in v:verify(v)
 for k,v in inp.items():
  if k.endswith('_ref') and isinstance(v,dict) and 'sha256' in v:verify(v)
 ck('scope fixed schema',s['schema']=='researchos.cli43-fresh-compiler-held2-scope.v2')
 ck('review exact path',path(s['controller_review_path'])==O/'review.json' and b['controller_review_path']==s['controller_review_path'] and b['controller_review_ref'] is None)
 ck('before after scope binding',s['expected_before_registration']==b['before']==[325,153,442] and s['expected_registration']==b['after']==[326,154,450])
 delta={k for k in s if s[k]!=old[k]}
 expected={'run_uuid','new_output_root','new_wrapper_root','new_export_root','new_authorization_root','registration_namespace','expected_registration','expected_before_registration','runner_ref','runtime_resources_ref','controller_review_path','new_grant_preflight_root'}
 ck('only intended scope delta',delta==expected)
 leaves=[s[k] for k in ['new_output_root','new_wrapper_root','new_export_root','new_authorization_root','new_grant_preflight_root']]
 ck('five distinct absent fresh leaves',len(set(leaves))==5 and all(not path(x).exists() for x in leaves))
 ck('prepare authorization not begun',not (N/'binding.json').exists() and not (N/'prepare.started.json').exists())
 c=read(N/'canonical-before.json');cp=read(R/'execution/v2.4/checkpoint.json');ow=read(R/'execution/v2.4/path_ownership.json')
 ck('actual current tuple head',[cp['revision'],ow['revision'],len(cp['failure_counters'])]==b['before'] and cp['head']==s['source_commit'])
 for x in c['entries']:
  p=verify(x['ref']);verify(x['live_original_ref']);ck('canonical copy live exact '+x['canonical_path'],p.read_bytes()==(R/x['canonical_path']).read_bytes())
 prefix=read(N/'failure-prefix430.json');ck('original430 preserved',prefix['actual_origin_count']==430 and cp['failure_counters'][:430]==prefix['failure_counters'])
 cut=read(N/'failure-origins.cut.json');ck('eight origins tuple',cut['before']==b['before'] and cut['after']==b['after'] and len(cut['origins'])==8 and cut['counter_reset'] is False)
 hashes=[]
 for x in cut['origins']:
  raw=read(verify(x['evidence_ref']));ck('original payload exact '+x['evidence_ref']['sha256'],raw==x['original_payload']);hashes.append(x['evidence_ref']['sha256']);ck('origin not in old442 '+hashes[-1],all(y.get('evidence_ref',{}).get('sha256')!=hashes[-1] for y in cp['failure_counters']))
 ck('eight unique / full442 preserved prospective',len(set(hashes))==8 and len(cp['failure_counters']+cut['origins'])==450)
 ck('one old GoList underlying cause',hashes.count('4910f5bebb70616f7b3dffa4b824540ed2e9917c7f268364359b26ca46c473fe')==1)
 controls=b['metadata_code_refs'];ck('metadata eight matching inventory',len(controls)==8 and controls==read(N/'metadata-code-refs.json')['entries'])
 runtime=read(path(s['runtime_resources_ref']['path']));prior_runtime=read(path(old['runtime_resources_ref']['path']));ck('old1242 resources exact',len(runtime['files'])==1250 and runtime['files'][:1242]==prior_runtime['files'][:1242])
 projected=[]
 for x in controls:
  p=verify(x);ck('relative serialized metadata pin '+p.name,x=={'path':p.relative_to(R).as_posix(),'sha256':ref(p)['sha256'],'bytes':ref(p)['bytes']});projected.append({**x,'path':str(p.absolute())});ast.parse(p.read_bytes())
  if p.parent==N:ck('six wrapper old byte equality '+p.name,p.read_bytes()==(OLD/p.name).read_bytes())
 ck('metadata runtime ABS exact eight',runtime['files'][1242:]==projected)
 for key in ['runner_ref','launcher_ref','authorization_gate_ref','owned_process_helper_ref','debug_tree_helper_ref']:
  x=s[key];p=verify(x);ck('actual Windows ABS serialized '+key,x=={'path':str(p.absolute()),'sha256':ref(p)['sha256'],'bytes':ref(p)['bytes']})
 runner=path(s['runner_ref']['path']);prev=path(old['runner_ref']['path']);newraw=runner.read_bytes();oldraw=prev.read_bytes();needle=b"run('go-list',[go,'list','-buildvcs=false','-mod=readonly'";replacement=b"run('go-list',[go,'list','-mod=readonly'"
 ck('runner one exact flag inverse',newraw.count(needle)==1 and newraw.replace(needle,replacement,1)==oldraw)
 ck('runner AST inverse',ast.dump(ast.parse(newraw.replace(needle,replacement,1)))==ast.dump(ast.parse(oldraw)))
 pack=runner.parent;pm=read(pack/'manifest.json')
 for x in pm['members']:verify(x)
 evidence=read(pack/'source-evidence.json')
 for x in evidence:
  p=verify(x['source']);lines=p.read_text(encoding='utf-8').splitlines();actual='\n'.join(str(i)+': '+lines[i-1] for i in range(x['first_line'],x['last_line']+1));ck('Go source exact lines '+p.name+':'+str(x['first_line']),actual==x['text'])
 template=read(N/'scope.template.runner-v5.json');oldtemplate=read(P/'cli43_root_binding_preparation_revision_codex/c16c5b73941e4e8a89b189594e53b4c5/scope.v5.proposed.json');td={k for k in template if template[k]!=oldtemplate[k]};ck('template changes runner only',td=={'runner_ref'} and template['runner_ref']==s['runner_ref'])
 driver=(N/'root-metadata-phase.py').read_bytes();prevdriver=(OLD/'root-metadata-phase.py').read_bytes();ck('outer driver only scope hash',driver.replace(pins['scope_registration.json'].encode(),ref(OLD/'scope_registration.json')['sha256'].encode())==prevdriver);ast.parse(driver)
 sources=read(N/'source-inputs.json');oldsources=read(OLD/'source-inputs.json');ck('source597 sealed rows same',len(sources['files'])==597 and sources==oldsources)
 for name in ['binding-build.invocation.json','scope-build.invocation.json']:
  x=read(N/name);verify(x['stdout_ref']);verify(x['stderr_ref']);ck('metadata native0 '+name,x['actual_native_exit']==0 and x['error'] is None and x['product_executed'] is False)
 # Reuse the already-sealed full compatibility review, not a fresh execution claim.
 reused=[P/'cli43_current_bound_scope_independent_review_codex/362294226719402294e4e3f5f2e5275c/review.json',P/'cli43_root_binding_static_independent_review_codex/c1a6b02b51ac427eb35ea000155db1c7/review.json',P/'cli43_current_bound_scope_independent_review_codex/46bfd2f723c84ad68e321774d6e08b30/review.json']
 reusedrefs=[ref(p) for p in reused]
 for x in inp['r326_changed_input_provenance'].values():
  if isinstance(x,dict) and 'sha256' in x:verify(x)
 module=path(controls[6]['path']).read_text(encoding='utf-8');ck('strict successful marker and nonlifecycle unchanged',"observation['all_observed_inputs_pre_pinned']=True" in module or "observation['all_observed_inputs_pre_pinned'] = True" in module)
 facts={'scope_delta_keys':sorted(delta),'template_delta_keys':sorted(td),'bound_manifest_members':len(mf['entries']),'runner_manifest_members':len(pm['members']),'scope_ref':ref(N/'scope_registration.json'),'canonical_before':c['entries'],'before':b['before'],'after':b['after'],'cut_origins':cut['origins'],'runtime_old1242_rows_reused':True,'metadata8_current_bytes_verified':True,'source597_rows_reused':True,'compiler22138_backing_files_not_rehashed':True,'full_previous_compatibility_reviews':reusedrefs,'old_failed_execution_ref':inp['r326_changed_input_provenance']['prior_run_independent_failed_closure_ref'],'fresh_leaves':leaves,'old_rejected_executable_identity':None,'scope_ref_serialization':'Root-relative remains exact because outerdriver differs only SCOPE_SHA from previously reviewed driver; v7 and gate bytes unchanged.'}
 write('audit.json',{'checks':checks,'failed_checks':[x for x in checks if not x['passed']],'facts':facts,'input_refs':list(refs.values()),'actual_target_executions':0,'new_failure_origins':[]})
 print(json.dumps({'checks':len(checks),'failed':[x for x in checks if not x['passed']],'audit_ref':ref(O/'audit.json')},ensure_ascii=False))
except Exception as e:
 write('audit.failure.json',{'error':repr(e),'traceback':traceback.format_exc(),'completed_checks':checks,'input_refs':list(refs.values()),'actual_target_executions':0});raise
