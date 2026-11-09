import sys
sys.dont_write_bytecode=True
import ast,copy,hashlib,json,types
from pathlib import Path,PureWindowsPath
N=Path(__file__).resolve().parent;B=N.parents[1]
R=Path('D:/作品集/ResearchOS/research-os')
C=B/'checkpoint_r368_restored21_source_root/cp368-w05-20261009'
ACTOR='codex:/root/attach_fixture_source_review'
pins={};checks=[];controls=[]
def fixed(p,h,z):return dict(path=str(p.resolve()),sha256=h,bytes=z)
def pin(p):
 p=Path(p).resolve(strict=True);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def norm(r):return dict(path=str(Path(r['path']).resolve(strict=True)),sha256=r['sha256'].removeprefix('sha256:'),bytes=r['bytes'])
def read(r):
 r=norm(r);assert pin(r['path'])==r,r['path']
 assert r['path'] not in pins or pins[r['path']]==r
 pins[r['path']]=r;return Path(r['path']).read_bytes()
def load(r):return json.loads(read(r))
def save(name,v):
 with (N/name).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def ck(name,v):
 assert v,name
 checks.append(name)
hr=fixed(C/'HDF.json','f66d684e007a71a77e42f040b02de916053258e0fafb6aa58205f78c55ddabc3',2173)
mr=fixed(C/'MF.json','c910cdd4677d6ceeb3e9260f26918e5203ed935139fcac91aca175a7ea211fb9',2506)
h,m=load(hr),load(mr)
for r in m['members']:read(r)
f,scope,proof=load(h['facts_ref']),load(h['scope_ref']),load(h['source_proof_ref'])
def member(name):return next(r for r in m['members'] if Path(r['path']).name==name)
live=load(member('live-context.source-check.root.json'))
sourceguard=load(member('source_guard.cleanup.check.json'))
for pair in f['pairs']:
 ph,pm=load(pair['handoff_ref']),load(pair['manifest_ref'])
 ck('pair_'+Path(pair['handoff_ref']['path']).parent.name,ph['manifest_ref']==pair['manifest_ref'])
 members=pm['members'];members=list(members.values()) if type(members) is dict else members
 for r in members:read(r)
for r in f['input_refs']:read(r)
raw=[read(r) for r in f['canonical_refs']];oldc,oldo=[json.loads(b) for b in raw[:2]]
ad=load(f['adoption_review_decision_ref']);out=load(f['adoption_outcome_ref']);origin=load(f['diagnostic']['origin_ref'])
sh=load(scope['source_handoff_ref']);rh=load(scope['source_review_handoff_ref']);sd=load(rh['source_decision_ref'])
contract=load(scope['contract_ref']);guidance=load(scope['root_execution_guidance_ref']);roster=load(scope['exact_source_roster_ref'])
rejected=load(f['W09_producer_request_changes_handoff_ref'])
wr=read(h['writer_ref']);wt=ast.parse(wr)
prepare=read(scope['prepare_caller_ref']).decode();validator=read(scope['validator_ref']).decode()
tp=B/'mu_sdk_controller_revision_v5_codex/e5953a6723c44426a05b5bb540186cdc/canonical_transactions.py'
tr=read(fixed(tp,'094e1a97fb00d01412b4e71e2d740b800accfce00e607c6853cb634280b12ba9',6877))
gp=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
gr=read(fixed(gp,'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85',11404))
failref=fixed(N/'failure953.original-tool-io.json','5526df6a460b1541612533ba44dca285bb756180568d1cc5766efb13d11f0015',1375)
ownfailure=load(failref)
for r in sourceguard['entries']:read({k:r[k] for k in ('path','sha256','bytes')})
gm=types.ModuleType('cp368_independent_read_guard');gm.__file__=str(gp);sys.modules[gm.__name__]=gm;exec(compile(gr,str(gp),'exec'),gm.__dict__)
guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
try:
 guard.acquire(list(pins.values()))
 ck('finite_input_guard_held',all(hashlib.sha256(guard.get_buffer(r['path'])).hexdigest()==r['sha256'] for r in pins.values()))
 # Only these writer functions execute; execute/main/save/module and update_pair do not.
 names={'require','encoded','normalized','scope_bindings','validate_live','transform'}
 ns=dict(Path=Path,copy=copy,json=json,hashlib=hashlib,ACTOR='codex:/root',KEY='restored21_v3_root_development',SLICE='RESTORED21_V3_BOUNDED_DEVELOPMENT',STATE='ROOT_REGISTERED_PENDING_RESTORED21_V3_DEVELOPMENT',pin=pin,read=read,load=load)
 functions=[v for v in wt.body if isinstance(v,ast.FunctionDef) and v.name in names]
 ck('exact_pure_writer_function_set',{v.name for v in functions}==names)
 exec(compile(ast.Module(body=functions,type_ignores=[]),str(Path(h['writer_ref']['path']))+'#pure-review','exec'),ns)
 proposed=ns['transform'](copy.deepcopy(oldc),copy.deepcopy(oldo),copy.deepcopy(f),h['facts_ref'],oldc,oldo,copy.deepcopy(live))
 pc,po=proposed;pr=[dict(path=r['path'],sha256=hashlib.sha256(ns['encoded'](v)).hexdigest(),bytes=len(ns['encoded'](v))) for r,v in zip(f['canonical_refs'],proposed)]
 ck('Source_proof_recomputed_exact',pr==proof['proposed_refs'] and proof['transaction'] is None and proof['mode']=='check')
 ck('Source_handoff_pair',h['manifest_ref']==mr and h['scope_ref']==f['scope_ref'] and h['actual_executed'] is False)
 ck('before_exact_revisions_367_171',oldc['revision']==367 and oldo['revision']==171 and json.loads(raw[3])['revision']==39)
 ck('after_exact_typed_revisions_368_172',type(pc['revision']) is int and pc['revision']==368 and type(po['revision']) is int and po['revision']==172)
 # Independent inverse, not the writer's claimed inverse.
 ic,io=copy.deepcopy(pc),copy.deepcopy(po)
 del ic['work_in_progress']['mu_sdk_r368']
 ic['failure_counters']=copy.deepcopy(oldc['failure_counters']);ic['workers']=copy.deepcopy(oldc['workers'])
 for k in ('expected_previous_revision','revision','updated_at','updated_by','note'):ic[k]=copy.deepcopy(oldc[k])
 del io['card_path_bindings']['W05-99']['subtasks']['restored21_v3_root_development']
 for k in ('revision','updated_at','updated_by'):io[k]=copy.deepcopy(oldo[k])
 ck('independent_complete_inverse',ic==oldc and io==oldo)
 ck('old949_semantic_and_950_once',len(oldc['failure_counters'])==949 and pc['failure_counters'][:949]==oldc['failure_counters'] and len(pc['failure_counters'])==950)
 def failure_array(b):
  t=b.decode();start=t.index('[',t.index('"failure_counters":'));_,count=json.JSONDecoder().raw_decode(t[start:]);return t[start:start+count]
 ck('old949_raw_prefix_preserved',failure_array(ns['encoded'](pc)).startswith(failure_array(raw[0]).rstrip()[:-1].rstrip()+','))
 row=pc['failure_counters'][-1];p=row['original_payload']
 ck('original952_exact_semantics',origin['root_assigned_ordinal']==p['observed_ordinal']==952 and origin['original_chunk_id']=='b2f026' and origin['outer_exit']==p['actual_outer_exit']==1 and all(origin[k] is None for k in ('SourcePython_exit','Go_exit','Native_exit','Model_exit')) and p['actual_python_exit'] is None and p['actual_native_exit'] is None and p['immutable_origin_ref']==f['diagnostic']['origin_ref'])
 ck('original952_once_no_reset_retry',row['counted_once'] is True and row['counter_reset'] is False and row['automatic_retry'] is False and row['origin_key'] not in {v.get('origin_key') for v in oldc['failure_counters']})
 ck('original_workers_and_WIP_preserved',pc['workers'][:-1]==oldc['workers'] and set(pc['work_in_progress'])==set(oldc['work_in_progress'])|{'mu_sdk_r368'})
 ck('two_active_parents',pc['work_in_progress']['construction_active_parents']==['W05','W09'])
 ck('historical_W05_parent_preserved',po['card_path_bindings']['W05-99']['owner']==oldo['card_path_bindings']['W05-99']['owner']==scope['historical_W05_parent_owner']=='codex:/root/w1102_impl')
 owner=po['card_path_bindings']['W05-99']['subtasks']['restored21_v3_root_development']
 ck('new_W05_exclusive_Root_subtask',owner['owner']=='codex:/root' and owner['current_source_writer'] is None and pc['workers'][-1]==f['worker'] and owner==f['owner'])
 ck('W09_ownership_wholly_unchanged',po['card_path_bindings']['W09-99']==oldo['card_path_bindings']['W09-99'])
 ck('review_W05_source_exact_nonself',rh['actor_id']!='codex:/root' and sd['actor_id']==rh['actor_id'] and sd['source_author'] is False and sd['actor_role']=='INDEPENDENT_NON_AUTHOR' and rh['source_handoff_ref']==scope['source_handoff_ref'] and rh['source_manifest_ref']==scope['source_manifest_ref'] and rh['status']=='SOURCE_ACCEPTED_FOR_ROOT_DEVELOPMENT_TESTS_ONLY')
 ck('W05_source_decision_same_package',sd['source_handoff_ref']==scope['source_handoff_ref'] and sd['source_manifest_ref']==scope['source_manifest_ref'])
 ck('scope_fixed4_and_pins',all(scope[k]==contract[k]==guidance[k]==owner[k] for k in ('worktree','environment','isolation_output','validation_output')) and scope['exact_source_roster_ref']==norm(contract['exact_source_roster']))
 ck('scope_13_once_partial_typed',type(scope['maximum_unique_tests']) is int and scope['maximum_unique_tests']==13 and type(scope['maximum_actual_attempts']) is int and scope['maximum_actual_attempts']==1 and scope['qualification_ceiling']==guidance['max_qualification']=='DEVELOPMENT_TESTS_13_ACTUAL_PASS_COMPONENT_PARTIAL_NATIVE_QUALIFICATION_OPEN')
 ck('scope_false_gates_and_int0',all(scope[k] is False for k in ('formal_dispatcher','formal_acceptance','Main_adoption','production_DB_writes','external_model_calls','automatic_retry','parent_acceptance')) and type(scope['formal_case_accepted_delta']) is int and scope['formal_case_accepted_delta']==0)
 ck('external_scope_owner_gate_explicit',guidance['caller_does_not_parse_RootScope_or_verify_owner_fields'] is True and guidance['prepare_argv']==contract['prepare_argv'] and guidance['validate_argv']==contract['validate_argv'])
 ck('argument_order_exact10_plus2',len(contract['prepare_argv'])==10 and len(contract['validate_argv'])==12 and contract['validate_argv'][:10]==contract['prepare_argv'] and contract['validate_argv'][-2:]==['ISOLATION_READY_SHA256','ISOLATION_READY_BYTES'])
 ck('prepare_argument_types_and_order',all(s in prepare for s in ("len(sys.argv) == 11","for i in (0, 3, 5, 7)","for i in (1, 2, 4, 6, 8)","type(checkpoint_revision) is int","checkpoint_revision == int(values[2])","type(ownership_revision) is int")))
 ck('validate_argument_types_same_vector',all(s in validator for s in ("len(sys.argv) == 13","isolated['canonical_refs'] == expected","isolated['head'] == head","preparation_cleanup['canonical_refs'] == expected","type(checkpoint_revision) is int","type(ownership_revision) is int")))
 ck('devtests_exact13_partial_no_native_acceptance',all(s in validator for s in ("len(terminals) == C['expected_unique_test_runs'] == 13","len(actions) == 13","'-test.count=1'","'native_qualification_accepted': False","'individual_descendant_PID_FILETIME_and_raw_streams': None","closed('DEVELOPMENT_TESTS_13_ACTUAL_PASS_COMPONENT_PARTIAL_NATIVE_QUALIFICATION_OPEN')")))
 ck('adoption_true_binding_current21_and7',ad['decision']=='ACTUAL_SEVEN_TARGET_ADOPTION_VERIFIED' and ad['adoption_outcome_ref']==f['adoption_outcome_ref'] and ad['final_target_refs']==out['final_target_refs'] and all(pin(r['path'])==r for r in ad['source21']+ad['final_target_refs']))
 ck('W09_native_source_rejection_no_owner',rejected['status']=='REQUEST_CHANGES' and pc['work_in_progress']['mu_sdk_r368']['W09_Main_native_status']=='SOURCE_REJECTED_PENDING_CLEANUP_REPAIR_NO_ACTUAL')
 wip=pc['work_in_progress']['mu_sdk_r368']
 ck('Source_cut952_next953_distinct_from_live',wip['highest_registered_ordinal_at_cutoff']==952 and wip['next_failure_ordinal_at_cutoff']==953 and wip['root_next_failure_ordinal_live']==953 and wip['later_diagnostics_observed_after_cutoff']==[])
 # Pure current reviewer context demonstrates later diagnostics retained separately.
 current=copy.deepcopy(live);current.update(next_original_failure_ordinal=954,pending=[dict(ordinal=953,origin_ref=failref,description='Root assigned reviewer read-only missing filename diagnostic c3b898')])
 nc,no=ns['transform'](copy.deepcopy(oldc),copy.deepcopy(oldo),copy.deepcopy(f),h['facts_ref'],oldc,oldo,current)
 nw=nc['work_in_progress']['mu_sdk_r368']
 shared_before={k:oldc['work_in_progress'][k] for k in ('root_next_failure_ordinal_live','later_diagnostics_observed_after_cutoff')}
 shared_after={k:nc['work_in_progress'][k] for k in shared_before}
 ck('finding_shared_live_stale_reproduced',shared_after==shared_before==dict(root_next_failure_ordinal_live=952,later_diagnostics_observed_after_cutoff=[]) and nw['root_next_failure_ordinal_live']==954 and len(nw['later_diagnostics_observed_after_cutoff'])==1)
 finding=dict(id='CP368-W05-P1-SHARED-LIVE-STALE',priority='P1',file=h['writer_ref']['path'],function='transform',summary='New revision leaves shared current live fields at old952/empty while new mu_sdk_r368 says live954/pending953',impact='A continuation reading work_in_progress.root_next_failure_ordinal_live can reuse assigned original ordinal952 and overlook pending953; unversioned shared fields conflict with new authoritative context.',observed_before=shared_before,observed_after=shared_after,new_nested_live=nw['root_next_failure_ordinal_live'],new_nested_pending=nw['later_diagnostics_observed_after_cutoff'],required_fix='Update both unversioned shared live fields from validated live context; inverse must restore whole old work_in_progress; preserve all r367 named cutoff fields and historical mu_sdk_r367 package.',source_finding_is_original_failure=False)
 save('findings.json',[finding])
 ck('fresh_context_953_pending_without_cut_rewrite',nw['root_next_failure_ordinal_live']==954 and nw['later_diagnostics_observed_after_cutoff']==current['pending'] and nw['highest_registered_ordinal_at_cutoff']==952 and nw['next_failure_ordinal_at_cutoff']==953 and nc['failure_counters']==pc['failure_counters'] and no==po)
 nc['work_in_progress']['mu_sdk_r368']['root_next_failure_ordinal_live']=953;nc['work_in_progress']['mu_sdk_r368']['later_diagnostics_observed_after_cutoff']=[]
 ck('postcut_context_only_changes_live_WIP',nc==pc)
 # Meaningful negative controls execute only pure transforms with expected exceptions.
 def reject(name,fn):
  try:fn()
  except (ValueError,AssertionError,KeyError,TypeError) as e:controls.append(dict(name=name,rejected=True,error_type=type(e).__name__,error=str(e)))
  else:raise AssertionError('negative control accepted '+name)
 def transformed(c=oldc,o=oldo,facts=f,ctx=live):
  return ns['transform'](copy.deepcopy(c),copy.deepcopy(o),copy.deepcopy(facts),h['facts_ref'],c,o,copy.deepcopy(ctx))
 for name,patch in [('counter_reset',dict(next_original_failure_ordinal=952)),('boolean_live',dict(next_original_failure_ordinal=True)),('omitted_pending953',dict(next_original_failure_ordinal=954)),('skipped_pending',dict(next_original_failure_ordinal=954,pending=[dict(ordinal=954,origin_ref=failref,description='negative')]))]:
  v=copy.deepcopy(live);v.update(patch);reject(name,lambda v=v:transformed(ctx=v))
 c=copy.deepcopy(oldc);c['work_in_progress']['construction_active_parents'].append('W10');reject('third_active_parent',lambda:transformed(c=c))
 o=copy.deepcopy(oldo);o['card_path_bindings']['W05-99']['owner']='codex:/root';reject('historical_parent_owner_replaced',lambda:transformed(o=o))
 c=copy.deepcopy(oldc);c['workers'].append(f['worker']);reject('duplicate_worker',lambda:transformed(c=c))
 o=copy.deepcopy(oldo);o['card_path_bindings']['W05-99']['subtasks']['restored21_v3_root_development']=f['owner'];reject('duplicate_subtask',lambda:transformed(o=o))
 altered=copy.deepcopy(f);altered['owner']['owner']='another-actor';reject('changed_owner_fact',lambda:transformed(facts=altered))
 altered=copy.deepcopy(f);altered['worker']['scope_ref']=h['facts_ref'];reject('changed_worker_fact',lambda:transformed(facts=altered))
 altered=copy.deepcopy(f);altered['diagnostic']['actual_python_exit']=1;reject('invented_SourcePython_exit',lambda:transformed(facts=altered))
 altered=copy.deepcopy(f);altered['diagnostic']['actual_native_exit']=0;reject('invented_Native_exit',lambda:transformed(facts=altered))
 # Real helper AST prefix; stub only the DLL boundary, no real update_pair.
 update=copy.deepcopy(next(v for v in ast.parse(tr).body if isinstance(v,ast.FunctionDef) and v.name=='update_pair'))
 index=next(i for i,v in enumerate(update.body) if isinstance(v,ast.Assign) and isinstance(v.value,ast.Call) and isinstance(v.value.func,ast.Attribute) and v.value.func.attr=='WinDLL')
 update.body=update.body[:index+1]
 class StubPath(PureWindowsPath):
  def is_dir(self):return True
 class BoundaryReached(Exception):pass
 calls=[]
 def dll(*args,**kwargs):calls.append(dict(args=list(args),kwargs=kwargs));raise BoundaryReached()
 tn=dict(Path=StubPath,PATHS=tuple(StubPath(r['path']) for r in f['canonical_refs'][:2]),os=types.SimpleNamespace(name='nt'),ctypes=types.SimpleNamespace(WinDLL=dll))
 exec(compile(ast.Module(body=[update],type_ignores=[]),'<trusted-helper-pure-prelude>','exec'),tn)
 try:tn['update_pair'](f['canonical_refs'][:2],None,str(C),'register')
 except RuntimeError as e:ck('real_helper_rejects_illegal_register',str(e)=='unknown canonical transaction' and calls==[])
 else:raise AssertionError('illegal operation')
 try:tn['update_pair'](f['canonical_refs'][:2],None,str(C),'activate')
 except BoundaryReached:ck('real_helper_activate_reaches_stub_DLL',calls==[dict(args=['kernel32'],kwargs={'use_last_error':True})])
 else:raise AssertionError('activate missed boundary')
 txcalls=[x for x in ast.walk(wt) if isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and isinstance(x.func.value,ast.Name) and x.func.value.id=='tm' and x.func.attr=='update_pair']
 ck('writer_calls_only_legal_activate',len(txcalls)==1 and isinstance(txcalls[0].args[-1],ast.Constant) and txcalls[0].args[-1].value=='activate')
 ck('trusted_helper_exclusive_and_durable_intent',all(x in tr.decode() for x in ('0x80000000|0x40000000,0,None,3','result=transform(','journal.mkdir()','"intent.json"','"mandatory_share_mode":0','"automatic_inverse":False','"requires_root_reconciliation":True','if failures:raise RuntimeError')))
 pairpaths={r['path'].casefold() for r in f['canonical_refs'][:2]}
 ck('writer_guard_excludes_pair',not pairpaths.intersection(v['path'].casefold() for v in sourceguard['entries']) and 'CANON_PAIR_EXCLUSIVELY_OWNED_BY_TRANSACTION_ONLY' in wr.decode())
 ck('Source_guard_closed0',sourceguard['closed'] is True and sourceguard['errors']==[] and sourceguard['retained_handles_count']==0 and sourceguard['verification']=='PASSED')
 ck('SS_commands_and_pair_unchanged',all(Path(r['path']).read_bytes()==b for r,b in zip(f['canonical_refs'],raw)))
 save('proposed.checkpoint.source-review.json',pc);save('proposed.ownership.source-review.json',po)
 save('external-caller-contract-review.json',dict(scope_ref=h['scope_ref'],source_handoff_ref=scope['source_handoff_ref'],source_manifest_ref=scope['source_manifest_ref'],source_review_handoff_ref=scope['source_review_handoff_ref'],source_review_manifest_ref=scope['source_review_manifest_ref'],guidance_ref=scope['root_execution_guidance_ref'],prepare_argv=contract['prepare_argv'],validate_argv=contract['validate_argv'],same_fresh_postregistration_vector_required=True,actual_calls=0,fixed_outputs={k:scope[k] for k in ('worktree','environment','isolation_output','validation_output')},scope_and_owner_enforcement='External Root authorization; W05 callers verify exact canonical vector, not RootScope fields',qualification_ceiling=scope['qualification_ceiling']))
finally:
 cleanup=guard.close();save('source-guard.cleanup.actual.json',cleanup)
ck('independent_guard_closed0',cleanup['closed'] is True and cleanup['errors']==[] and cleanup['retained_handles_count']==0 and cleanup['verification']=='PASSED')
ck('all_pins_stable',all(pin(r['path'])==r for r in pins.values()))
save('input-pins.json',list(pins.values()));save('checks.json',checks);save('negative-controls.json',controls)
save('source-decision.json',dict(schema='researchos.cp368-w05-registration-independent-source-decision.v1',decision='REQUEST_CHANGES',actor_id=ACTOR,actor_role='INDEPENDENT_NON_AUTHOR',source_handoff_ref=hr,source_manifest_ref=mr,writer_ref=h['writer_ref'],facts_ref=h['facts_ref'],scope_ref=h['scope_ref'],source_proof_ref=h['source_proof_ref'],all_handles_closed=True,actual_executed=False,formal_acceptance=False,formal_case_accepted_delta=0,source_cutoff=dict(highest_ordinal=952,next_failure_ordinal=953),Root_reported_live_next=954,pending_after_cutoff=[dict(ordinal=953,origin_ref=failref)],fresh_Root_postseal_context_required=True,execution_grant=False,product_calls=0,Main_Canon_written=False,new_reviewer_original_failures=[dict(ordinal=953,origin_ref=failref)],findings_ref=pin(N/'findings.json')))
save('result.json',dict(status='REQUEST_CHANGES',checks=len(checks),negative_controls=len(controls),pins=len(pins),P1_findings=1,new_reviewer_original_failure_ordinals=[953],Root_reported_live_next=954,all_handles_closed=True,actual_executed=False))
print(json.dumps(dict(status='REQUEST_CHANGES',checks=len(checks),controls=len(controls),pins=len(pins),P1_findings=1,new_reviewer_original_failures=[953],next_failure=954)))

