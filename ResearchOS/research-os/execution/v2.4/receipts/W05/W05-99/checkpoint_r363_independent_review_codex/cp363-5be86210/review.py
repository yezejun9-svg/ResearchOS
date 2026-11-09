import sys
sys.dont_write_bytecode=True
import pathlib,json,hashlib,importlib.util,re,traceback
P=pathlib.Path
O=P(__file__).resolve().parent;R=P('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99'
N=B/'sdk_five_go_root_adoption_preparation_codex/04a454a98b164aa2983f16245f273e9d/checkpoint-r363-native-grant-expired-fixture-lost-attach-source-ready'
G=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
checks=[];g=None;reference_sources={};allrefs={}
def save(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
def pin(p):
 p=P(p);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def norm(v):return dict(path=str(P(v['path'])),sha256=v['sha256'].removeprefix('sha256:'),bytes=v['bytes'])
def add(v,source):
 v=norm(v);key=v['path'].casefold()
 if key in allrefs:assert allrefs[key]==v,'conflicting current declaration: '+v['path']
 else:allrefs[key]=v
 reference_sources.setdefault(key,[]).append(source)
def rawrefs(v):
 if isinstance(v,dict):
  if {'path','sha256','bytes'}.issubset(v) and isinstance(v['path'],str) and isinstance(v['sha256'],str) and type(v['bytes']) is int:yield v
  else:
   for x in v.values():yield from rawrefs(x)
 elif isinstance(v,list):
  for x in v:yield from rawrefs(x)
def ck(n,v,d=None):checks.append(dict(check=n,passed=bool(v),detail=d))
def members(x):
 v=x['members'];return list(v.values()) if isinstance(v,dict) else v
def good(c):return c.get('schema')=='researchos.source-read-guard-observation.v1' and c['closed'] is True and c['retained_handles_count']==0 and c['verification']=='PASSED' and c['failure'] is None and not c['errors'] and all(v['verified'] and v['final_path_match'] and v['closed'] for v in c['entries'])
def main():
 global g
 facts0=json.loads((N/'checkpoint.execution.facts.json').read_bytes());pa0=json.loads((N/'canonical_pair.actual.json').read_bytes());J=P(pa0['transaction']['transaction_journal'])
 for p in list(N.iterdir())+list(J.iterdir()):
  if p.is_file():add(pin(p),'checkpoint-public-package-or-transaction')
 for r in rawrefs(facts0):add(r,'facts-declared-reference')
 for r in rawrefs(json.loads((N/'handoff.json').read_bytes())):add(r,'new-handoff')
 for r in members(json.loads((N/'manifest.json').read_bytes())):add(r,'new-manifest-member')
 manifest_counts=[]
 for e in facts0['reviews']:
  rs=members(json.loads(P(e['manifest_ref']['path']).read_bytes()));manifest_counts.append(dict(scope=e['scope'],members=len(rs)))
  for r in rs:add(r,'review-manifest:'+e['scope'])
 # New Source-only handoffs are declared in the checkpoint WIP. Read only their explicit manifest members.
 w0=facts0['work_in_progress']['mu_sdk_r363']
 for h in [w0['attach_T11']['sparse_revision_source_ref'],w0['native_phase_helpers_source']['handoff_ref']]:
  hj=json.loads(P(h['path']).read_bytes())
  for rr in rawrefs(hj):
   if P(rr['path']).name.casefold() in ['mf.json','manifest.json']:
    add(rr,'WIP-Source-manifest')
    for r in members(json.loads(P(rr['path']).read_bytes())):add(r,'WIP-Source-manifest-member')
 # Necessary direct execution receipt descendants; do not recursively reopen historical canonical aliases or private resources.
 U=B/'integration_codex/python-broker4-public-units-root-1791512710000'
 qual=json.loads((U/'failure879.exit-qualification.json').read_bytes());add(qual['invocation_ref'],'879-no-child-evidence')
 uc=json.loads((U/'revision-explicit-binary-handles/validation.closed.json').read_bytes());add(uc['results_ref'],'public17-results')
 ur=json.loads(P(uc['results_ref']['path']).read_bytes())
 for r in rawrefs(ur):add(r,'public17-result-descendant')
 for n,h,b in [('checkpoint','9e67531bd3b1f0fbd9bc5e239b3a240a39f668db2d367714a399ba4fd8bfeb25',4223052),('path_ownership','48c5641956b5f22bb48f7775e46d90494bd95944027f55070e430e207a506452',192861),('step_state','fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149',257446),('commands','b357f60a9463b1a7504487bd8debf2b55f87f35938a26fe68a495aa834794129',68156)]:
  add(dict(path=str(R/'execution/v2.4'/(n+'.json')),sha256=h,bytes=b),'current-canonical')
 for p in [G,P(__file__),R/'execution/project_identity.json']:add(pin(p),'review-support')
 assert pin(G)['sha256']=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
 refs=list(allrefs.values())
 spec=importlib.util.spec_from_file_location('cp363_readonly_guard',G);gm=importlib.util.module_from_spec(spec);spec.loader.exec_module(gm)
 g=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);g.acquire(refs)
 def raw(p):return g.get_buffer(str(P(p)))
 def obj(p):return json.loads(raw(p))
 def verify(r):
  b=raw(r['path']);return hashlib.sha256(b).hexdigest()==r['sha256'].removeprefix('sha256:') and len(b)==r['bytes']
 def actualpin(p):
  b=raw(p);return dict(path=str(P(p)),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
 save('input-pins.json',refs);save('reference-provenance.json',reference_sources);save('manifest-member-counts.json',manifest_counts)
 for r in refs:ck('exact-input:'+r['path'],verify(r))
 facts=obj(N/'checkpoint.execution.facts.json');cp=obj(R/'execution/v2.4/checkpoint.json');old=obj(J/'0.before.json');w=cp['work_in_progress'];ww=w['mu_sdk_r363']
 ck('HDF-exact',actualpin(N/'handoff.json')['sha256']=='25ab56d26b0000db75f1fde9aaedafed46a4f86e6338d3290b5a5526526ea951' and len(raw(N/'handoff.json'))==1124)
 ck('facts-exact',actualpin(N/'checkpoint.execution.facts.json')['sha256']=='4a0d3e9657904a5d48414d8e1ce5d612942407da91fab93c93e6b72f4b41d919' and len(raw(N/'checkpoint.execution.facts.json'))==31071)
 ck('oldCP362-exact',actualpin(J/'0.before.json')['sha256']=='84c970d86ab96b78a7621595839005f68a440fc9a540d3b619500c7cbed2669b' and len(raw(J/'0.before.json'))==4195882)
 ck('same-project-and-head',cp['project_id']==old['project_id']=='aede0678-7308-43dc-b9f2-cfe3d90cfdfb' and cp['head']==old['head']=='adc460c2138528f163f7fdab5e8d81dde157b7fb')
 ck('revision362-to363',old['revision']==362 and cp['revision']==363 and cp['expected_previous_revision']==362)
 allowed={'revision','expected_previous_revision','updated_at','updated_by','failure_counters','work_in_progress','note'}
 changed=[k for k in cp.keys()|old.keys() if cp.get(k)!=old.get(k)]
 ck('only-authorized-top-level-delta',set(changed).issubset(allowed),changed)
 ck('all-old-WIP-values-preserved',all(k in w and w[k]==v for k,v in old['work_in_progress'].items()))
 ck('new-WIP-equals-facts',ww==facts['work_in_progress']['mu_sdk_r363'] and verify(w['mu_sdk_r363_facts_ref']))
 ck('old873-whole-objects-identical',len(old['failure_counters'])==873 and cp['failure_counters'][:873]==old['failure_counters'] and len(cp['failure_counters'])==893)
 def array(rawbytes):
  t=rawbytes.decode();start=t.index('[',t.index('"failure_counters":'));v,end=json.JSONDecoder().raw_decode(t[start:]);return t[start:start+end]
 oa=array(raw(J/'0.before.json'));na=array(raw(R/'execution/v2.4/checkpoint.json'));prefix=oa.rstrip()[:-1].rstrip()
 ck('old873-raw-array-prefix-identical',na.startswith(prefix+','))
 origs={};quals=[];chunks=[];diagnostics=facts['diagnostics'];new=cp['failure_counters'][873:];oldkeys={v.get('origin_key') for v in old['failure_counters'] if v.get('origin_key') is not None}
 ck('twenty-distinct-ordinals876-through895',[d['ordinal'] for d in diagnostics]==list(range(876,896)) and len(new)==20)
 def origin_value(o,names):
  v=[o[k] for k in names if k in o];assert v,'missing explicit origin exit'
  assert all(x==v[0] for x in v);return v[0]
 def primary(o,n):
  if n==878:return None
  if n==892:
   t=obj(o['original_terminal_tool_io_ref']['path']);v=t['output'];return json.loads(v) if isinstance(v,str) else v
  if n==894:return [x['output'] for x in o['original_tool_io'] if isinstance(x.get('output'),dict) and 'exit_code' in x['output']][-1]
  if 'result' in o:return o['result']
  return o['entries'][0]['result']
 for d,c in zip(diagnostics,new):
  n=d['ordinal'];o=obj(d['origin_ref']['path']);origs[n]=o
  ex=(origin_value(o,['actual_outer_exit','actualOuter','outer_exit']),origin_value(o,['actual_python_exit','actualPython','python_exit']),origin_value(o,['actual_native_exit','native','native_exit']))
  expected=(d['actual_outer_exit'],d['actual_python_exit'],d['actual_native_exit'])
  ck(str(n)+':origin-explicit-exits',ex==expected,dict(outer=ex[0],python=ex[1],native=ex[2]))
  ck(str(n)+':origin-ordinal',o.get('ordinal',o.get('failure_ordinal'))==n)
  expectedkey=hashlib.sha256((d['origin_ref']['sha256'].removeprefix('sha256:')+'#'+str(n)).encode()).hexdigest()
  ck(str(n)+':origin-key-exact-once',c.get('origin_key')==expectedkey and expectedkey not in oldkeys and sum(x.get('origin_key')==expectedkey for x in new)==1)
  payload=c['original_payload']
  ck(str(n)+':counter-preserves-origin-and-exits',norm(c['evidence_ref'])==norm(d['origin_ref'])==norm(payload['immutable_origin_ref']) and payload['observed_ordinal']==n and tuple(payload[k] for k in ['actual_outer_exit','actual_python_exit','actual_native_exit'])==expected and payload['diagnostic']==d['description'] and c['counted_once'] is True and c['counter_reset'] is False and c['automatic_retry'] is False)
  t=primary(o,n);q=dict(ordinal=n,actual_outer_exit=ex[0],actual_python_exit=ex[1],actual_native_exit=ex[2],origin_ref=norm(d['origin_ref']))
  if t is not None:
   ck(str(n)+':raw-terminal-outer-exit',t['exit_code']==ex[0]);q['chunk_id']=t['chunk_id'];chunks.append(t['chunk_id']);out=t['output']
   if ex[1] is not None:
    markers=re.findall(r'(?:ROOT|REVIEW|SOURCE)_PYTHON_EXIT=(-?\d+)',out);ck(str(n)+':raw-explicit-Python-marker',bool(markers) and int(markers[-1])==ex[1],markers)
   q['raw_output_truncated']='truncated output' in out.lower()
  else:ck('878:rejected-before-any-tool-execution',ex==(None,None,None) and o['functions_script_started'] is False and o['exec_command_called'] is False and o['apply_patch_called'] is False and 'SyntaxError' in o['returned_text'])
  quals.append(q)
 ck('raw-terminal-chunks-distinct',len(chunks)==len(set(chunks))==19)
 ck('cutoff-counts-and-later-not-added',w['r363_registered_failure_count']==893 and w['r363_highest_observed_diagnostic_ordinal_at_cutoff']==895 and w['r363_next_failure_ordinal_at_cutoff']==896 and not any(c['original_payload']['observed_ordinal']>=896 for c in new))
 post=obj(N/'postwrite-original-root-tool-io.json')
 ck('writer-actual-exit0-and-marker',post['writer_actual']['exit_code']==0 and post['writer_actual']['chunk_id']=='511395' and 'ROOT_PYTHON_EXIT=0' in post['writer_actual']['output'] and post['explicit_python_exit']==0)
 out=json.loads(post['writer_actual']['output'].splitlines()[0]);ck('writer-terminal-binds-new-canonical-and-handoff',verify(out['checkpoint_ref']) and verify(out['resume_ref']) and verify(out['handoff_ref']) and out['registered_failures']==893 and out['highest_registered_ordinal']==895)
 ck('later899-is-postwrite-not-current-cutoff',w['later_diagnostics_observed_after_cutoff']==[896,897,898] and w['root_next_failure_ordinal_live']==899 and post['later_failures_pending']==[896,897,898,899] and post['next_failure_ordinal']==900)
 intent=obj(J/'intent.json');committed=obj(J/'committed.json')
 for r in intent['before_refs']+intent['after_refs']+committed['after_refs']:ck('transaction-ref:'+r['path'],verify(r))
 ck('transaction-committed-exclusively',committed['written_indices']==[0,1] and committed['both_verified_while_exclusively_held'] is True and intent['mandatory_share_mode']==0 and intent['automatic_inverse'] is False)
 ck('proposed-checkpoint-equals-current',raw(J/'0.after.proposed.json')==raw(R/'execution/v2.4/checkpoint.json'))
 ck('ownership168-byte-unchanged',raw(J/'1.before.json')==raw(J/'1.after.proposed.json')==raw(R/'execution/v2.4/path_ownership.json') and obj(R/'execution/v2.4/path_ownership.json')['revision']==168)
 # Exact selected qualification details, never infer a child from Python or an error count from number of findings.
 q879=obj(U/'failure879.exit-qualification.json');u879=obj(q879['invocation_ref']['path'])['owned_process']
 ck('879-no-child-no-tests-nativeNULL',u879['owned_child_pid'] is None and u879['creation_time_100ns'] is None and u879['actual_exit'] is None and not u879['resumed'] and u879['stage']=='PREPARE_EXPLICIT_STD_HANDLES' and "'str' object has no attribute 'flush'" in u879['error'] and q879['unit_tests_executed']==0 and q879['actual_native_exit'] is None and u879['job_cleanup']['handles_closed'] is True and not u879['job_cleanup']['errors'])
 o891=origs[891];j891=json.loads(o891['result']['output'].splitlines()[0])
 ck('891-two-false-findings-one-invocation',o891['result']['chunk_id']=='0535b2' and j891['decision']=='REQUEST_CHANGES' and len(j891['failed'])==2 and len([q for q in quals if q['ordinal']==891])==1)
 ck('893-two-diagnostics-one-invocation',origs[893]['result']['output'].count('You cannot call a method on a null-valued expression.')==2)
 q895=origs[895]
 ck('895-preserves-truncation-and-unknown-rg-exit',q895['output_truncated_by_tool'] is True and q895['rg_exit']=='NOT_SEPARATELY_CAPTURED' and 'ops/recovery_root' in q895['args']['cmd'] and primary(q895,895)['exit_code']==0)
 quals[-1]['qualification_limit']='Original tool output truncated; internal rg exit not separately captured and missing-path diagnostic is absent from retained output. Keep recorded outer0/PythonNULL/nativeNULL; do not infer rg numerical exit.'
 # Native T10 actual closed failed execution.
 n892=origs[892];ni=obj(n892['native_invocation_ref']['path']);oi=obj(n892['outer_invocation_ref']['path'])
 for label,inv,pid,ft in [('Go',ni,42244,134359866411023123),('outerPython',oi,79092,134359866284665514)]:
  rr=inv['result'];jc=rr['job_cleanup']
  ck('892:'+label+'-real-exit1-identity',rr['actual_exit']==1 and rr['owned_child_pid']==pid and type(rr['creation_time_100ns']) is int and rr['creation_time_100ns']==ft)
  ck('892:'+label+'-natural-failure-owned-job-closed',rr['timed_out'] is False and rr['error'] is None and jc['termination_requested'] is False and jc['active_processes_last_observed']==0 and all(jc[k] for k in ['job_idle_confirmed','primary_exit_confirmed','handles_closed']) and not jc['errors'])
 stdout=raw(n892['native_stdout_ref']['path']).decode()
 ck('892:same-20min-attempt-main-and-cleanup-failure',stdout.count('Root review window ended context deadline exceeded')==2 and 'windows_test.go:626:' in stdout and 'windows_test.go:468:' in stdout and 1200<=ni['result']['elapsed_seconds']<1260)
 t10=next(e for e in facts['reviews'] if e['scope']=='T10_FAILED_CLOSURE_FIXTURE_LOST');th=obj(t10['handoff_ref']['path']);tr=obj(th['review_ref']['path'])
 ck('892:independent-closure-only-no-SQL-release-positive',th['decision']=='FAILED_EXECUTION_CLOSURE_CONFIRMED_FIXTURE_LOST_NO_SQL_OR_SPECIFIC_RELEASE' and tr['whole_SQL_after_failure_accepted'] is False and tr['specific_release_accepted'] is False and tr['native_positive_Owner_nine_original_business_formal_accepted'] is False)
 fixture=P(t10['handoff_ref']['path']).parent/'fixture-current-state.json';fv=obj(fixture)
 ck('892:original-fixture-loss-recorded-no-afterSQL',fv['database_live_available'] is False and fv['whole_SQL_after_failure_available'] is False and fv['specific_release_performed'] is False and all(not p['exists'] for p in fv['current_paths']))
 ck('892:checkpoint-preserves-failure-boundary',ww['native_T10']['status']=='FAILED_NATURAL_EXIT1_JOB_GUARDS_CLOSED' and ww['native_T10']['grant_published'] is False and ww['native_T10']['apply_and_replay']=='NOT_STARTED' and ww['native_T10']['fixture_lost_before_wholeSQL'] is True and ww['native_T10']['specific_fixture_release']=='NOT_COMPLETED')
 # T11 first fullcheckout failure, not a target-test run.
 I=B/'integration_codex/attach-fixture-current-two-parent-isolation-root-t11-1a11e7f5205729390aaee9f47b28ce6'
 for name,ex in [('head-before',0),('tracked-status',0),('staged-status',0),('create-worktree',128)]:
  inv=obj(I/(name+'.invocation.json'));rr=inv['result'];jc=rr['job_cleanup']
  ck('894:'+name+'-exit-and-owned-job-closed',rr['actual_exit']==ex and not rr['timed_out'] and rr['error'] is None and jc['active_processes_last_observed']==0 and all(jc[k] for k in ['job_idle_confirmed','primary_exit_confirmed','handles_closed']) and not jc['errors'])
  ck('894:'+name+'-raw-stdout-stderr-bound',verify(inv['stdout_ref']) and verify(inv['stderr_ref']))
 err=raw(I/'create-worktree.stderr.raw').decode()
 ck('894:real-ENOSPC',bool(re.search(r'no space left|not enough space|disk full',err,re.I)))
 for name in ['runtime-source-guard.cleanup.actual.json','source-guard.cleanup.actual.json']:ck('894:guard-closed:'+name,good(obj(I/name)))
 ck('894:not-overlay-or-target-execution',ww['attach_T11']['original_isolation_status']=='FAILED_ENOSPC_GIT128' and ww['attach_T11']['original_source_overlay'] is False and ww['attach_T11']['tests']=='NOT_EXECUTED')
 # Public units are a narrow component result.
 uc=obj(U/'revision-explicit-binary-handles/validation.closed.json');ur=obj(uc['results_ref']['path'])
 ck('public17-component-only',ur['pass_count']==17 and ur['fail_count']==ur['skip_count']==0 and len(set(ur['test_method_names']))==17 and ur['actual_python_child_exit']==0 and ur['formal_acceptance'] is False and ww['broker4_pure_unit_tests']['native_acceptance'] is False)
 ut=raw(ur['stderr_ref']['path']).decode();names=re.findall(r'^(test_\w+) \([^\n]+\) \.\.\. ok\r?$',ut,re.M)
 ck('public17-actual-raw-names-and-OK',set(names)==set(ur['test_method_names']) and 'Ran 17 tests' in ut and ut.rstrip().endswith('OK'))
 for e in facts['reviews']:
  h=obj(e['handoff_ref']['path']);ck('review-not-product-authority:'+e['scope'],h.get('formal_acceptance') is False)
 sparseH=obj(ww['attach_T11']['sparse_revision_source_ref']['path']);helperH=obj(ww['native_phase_helpers_source']['handoff_ref']['path'])
 ck('source-only-pending-claims-honest-at-cutoff',ww['attach_T11']['sparse_revision']=='PENDING_INDEPENDENT_SOURCE_REVIEW_AND_ROOT_ACTUAL' and sparseH['formal_acceptance'] is False and ww['native_phase_helpers_source']['independent_review']=='PENDING' and ww['native_phase_helpers_source']['actual_generated_approvals']==0 and helperH['new_approval_generated'] is False)
 ck('six22-formalzero42-unchanged',ww['historical_accepted_parents']==6 and ww['required_parents']==22 and ww['current_formal_accepted']==0 and ww['required_formal']==42 and cp['current_effective_formal_status']==old['current_effective_formal_status'] and cp['current_effective_formal_status']['formal_cases_accepted']==0)
 ck('paid-business-open-providerunknown-costs-unchanged',ww['original_trial_business']=='OPEN' and ww['original_trial_provider_requests'] is None and ww['financial_closed'] is False and cp['cost_unknown']==old['cost_unknown'] and ww['counter_reset'] is False)
 resume=obj(N/'RESUME.r363.original.json')
 ck('resume-conservative-boundaries',resume['original_trial_once_consumed'] is True and resume['original_trial_clock_expired'] is True and resume['original_trial_provider_requests'] is None and resume['financial_closed'] is False and resume['original_trial_business_open'] is True and resume['current_formal_accepted']==0 and resume['required_formal']==42 and resume['required_parents']==22 and resume['native_T10_wholeSQL_after_observed'] is False and resume['native_T10_specific_release'] is False and resume['completion_asserted'] is False)
 ck('writer-declared-sourceguard-closed',good(obj(N/'source_guard.cleanup.actual.json')))
 save('failure-exit-qualifications.json',quals)
 save('semantic-delta.json',{'changed_top_level':changed,'new_work_in_progress_keys':sorted(set(w)-set(old['work_in_progress'])),'old873_objects_equal':cp['failure_counters'][:873]==old['failure_counters'],'old873_raw_array_prefix_equal':na.startswith(prefix+','),'historical_records_without_origin_key':sum('origin_key' not in c for c in old['failure_counters']),'registered_before':873,'registered_after':893,'registered_ordinal_cutoff':895,'canonical_live_field_at_write':899,'postwrite_live_next':900,'later896_to899_are_not_registered_in_CP363':True,'snapshot_not_live_execution_authority':True})
 closure=g.close();save('guard.final.json',closure);ck('review-all-inputs-and-canonical-closed',good(closure))
 result={'schema':'researchos.independent-cp363-consistency-review.v1','decision':'CP363_CANONICAL_CONSISTENCY_ACCEPTED_NO_PRODUCT_AUTHORITY' if all(x['passed'] for x in checks) else 'CP363_CONSISTENCY_FINDINGS','checks':checks,'remaining_findings':[x for x in checks if not x['passed']],'guarded_input_count':len(refs),'declared_input_bytes':sum(r['bytes'] for r in refs),'no_evidence_tree_copy':True,'registered_failures':893,'registered_ordinal_cutoff':895,'later896_to899_not_registered':True,'postwrite_next_ordinal':900,'new_review_execution_failures':0,'reviewer_is_not_checkpoint_author':True,'formal_acceptance':False,'authority':'CHECKPOINT_CONSISTENCY_ONLY','product_authority':'NONE','no_Git_Go_SQL_native_model_execution':True,'no_private_key_or_original_trial_read':True,'canonical_writes':False,'known_evidence_limitations':['895 original tool output truncated; internal rg exit unknown.','Historical and cutoff states are not claims of current T11 process completion.'],'stop':True}
 save('review.json',result)
 print(json.dumps({k:result[k] for k in ['decision','remaining_findings','guarded_input_count','declared_input_bytes','registered_failures','registered_ordinal_cutoff','postwrite_next_ordinal','new_review_execution_failures','stop']}|{'checks_passed':sum(x['passed'] for x in checks),'checks_total':len(checks),'all_guards_closed':closure['closed']},ensure_ascii=False))
code=0
try:main()
except Exception:traceback.print_exc();code=1
finally:
 if g is not None:
  closure=g.close()
  if not (O/'guard.final.json').exists():save('guard.final.json',closure)
 print('ROOT_PYTHON_EXIT='+str(code))
sys.exit(code)

