import sys
sys.dont_write_bytecode=True
import ast,copy,hashlib,json,types
from pathlib import Path,PureWindowsPath
N=Path(__file__).resolve().parent;B=N.parents[1]
R=Path('D:/作品集/ResearchOS/research-os')
C=B/'checkpoint_r368_restored21_v2_source_root/cp368-w05v2-20261009'
A=B/'checkpoint_r368_w05_independent_review_codex/cp368r-01a11fea'
ACTOR='codex:/root/attach_fixture_source_review'
pins={};checks=[];controls=[]
def fixed(p,h,z):return dict(path=str(p.resolve()),sha256=h,bytes=z)
def pin(p):
 p=Path(p).resolve(strict=True);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def norm(r):return dict(path=str(Path(r['path']).resolve(strict=True)),sha256=r['sha256'].removeprefix('sha256:'),bytes=r['bytes'])
def read(r):
 r=norm(r);assert pin(r['path'])==r,r['path']
 assert r['path'] not in pins or pins[r['path']]==r
 pins[r['path']]=r;return Path(r['path']).read_bytes()
def load(r):return json.loads(read(r))
def save(name,v):
 with (N/name).open('x',encoding='utf-8',newline='\n') as s:s.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def ck(name,v):
 assert v,name
 checks.append(name)
hr=fixed(C/'HDF.json','ff68cc7c813e1932df8351995251b6bd99ff47a6f7bd69f8fa0913b5c608e4fa',2203)
mr=fixed(C/'MF.json','efb2ddaf6af93a087a932f07033d696b9649fea4d2efff74364b41373a6af0af',3143)
ahr=fixed(A/'HDF.json','5fe6208d5d56b02f1754b40c45314c000bc0e71d1a48555ea60ba81b1082763c',2881)
amr=fixed(A/'MF.json','86158b843c8ff2255aba0ec6a58b7926d68447720b06f3187bb00cbd5d6a4c63',4580)
apr=fixed(A/'postseal.json','3dc8fb9e33c4346a7660262bac875738739ebde1e6b3007a264897f82816a5de',974)
h,m,ah,am,ap=[load(r) for r in (hr,mr,ahr,amr,apr)]
for r in m['members']+am['members']:read(r)
def member(name):return next(r for r in m['members'] if Path(r['path']).name==name)
inv=load(member('source-byte-inverse.json'));oldh=load(inv['v1_handoff_ref']);oldmf=load(inv['v1_manifest_ref'])
for r in oldmf['members']:read(r)
f,scope,proof=load(h['facts_ref']),load(h['scope_ref']),load(h['source_proof_ref'])
oldf,oldscope=load(oldh['facts_ref']),load(oldh['scope_ref'])
live=load(member('live-context.source-check.root.json'));sg=load(member('source_guard.cleanup.check.json'))
for pair in f['pairs']:
 ph,pm=load(pair['handoff_ref']),load(pair['manifest_ref'])
 ck('pair_'+Path(pair['handoff_ref']['path']).parent.name,ph['manifest_ref']==pair['manifest_ref'])
 members=pm['members'];members=list(members.values()) if type(members) is dict else members
 for r in members:read(r)
for r in f['input_refs']:read(r)
for r in sg['entries']:read({k:r[k] for k in ('path','sha256','bytes')})
raw=[read(r) for r in f['canonical_refs']];oldc,oldo=[json.loads(b) for b in raw[:2]]
ad=load(f['adoption_review_decision_ref']);out=load(f['adoption_outcome_ref']);origin=load(f['diagnostic']['origin_ref'])
rh=load(scope['source_review_handoff_ref']);sd=load(rh['source_decision_ref'])
contract=load(scope['contract_ref']);guidance=load(scope['root_execution_guidance_ref'])
wr=read(h['writer_ref']);wt=ast.parse(wr)
tp=B/'mu_sdk_controller_revision_v5_codex/e5953a6723c44426a05b5bb540186cdc/canonical_transactions.py'
tr=read(fixed(tp,'094e1a97fb00d01412b4e71e2d740b800accfce00e607c6853cb634280b12ba9',6877))
gp=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
gr=read(fixed(gp,'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85',11404))
gm=types.ModuleType('cp368_v2_independent_guard');gm.__file__=str(gp);sys.modules[gm.__name__]=gm;exec(compile(gr,str(gp),'exec'),gm.__dict__)
guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
try:
 guard.acquire(list(pins.values()))
 ck('all_finite_inputs_held',all(hashlib.sha256(guard.get_buffer(r['path'])).hexdigest()==r['sha256'] for r in pins.values()))
 ck('prior_review_exact_final',ah['manifest_ref']==amr and ap['handoff_ref']==ahr and ap['manifest_ref']==amr and ah['status']=='REQUEST_CHANGES' and ah['P1_findings']==1 and ah['independent_checks']==45 and ah['negative_controls']==12)
 ck('prior_finding_exact',load(ah['findings_ref'])[0]['id']=='CP368-W05-P1-SHARED-LIVE-STALE')
 ck('source_pair_exact',h['manifest_ref']==mr and h['scope_ref']==f['scope_ref'])
 ck('scope_same_content_new_path',scope==oldscope and h['scope_ref']['sha256']==oldh['scope_ref']['sha256'] and h['scope_ref']['path']!=oldh['scope_ref']['path'])
 fc=copy.deepcopy(f);fc['created_utc']=oldf['created_utc'];fc['scope_ref']=oldf['scope_ref'];fc['owner']['scope_ref']=oldf['scope_ref'];fc['worker']['scope_ref']=oldf['scope_ref']
 ck('facts_only_scope_paths_and_timestamp_changed',fc==oldf)
 ck('inverse_source_pair_bindings',inv['v1_handoff_ref']==ah['source_handoff_ref'] and inv['v1_manifest_ref']==ah['source_manifest_ref'])
 for change in inv['changes']:
  oldref=next(r for r in oldmf['members'] if Path(r['path']).name==change['path'])
  newref=member(change['path']);before,after=read(oldref),read(newref)
  ck('inverse_exact_refs_'+change['path'],oldref['sha256']==change['before_sha256'] and oldref['bytes']==change['before_bytes'] and newref['sha256']==change['after_sha256'] and newref['bytes']==change['after_bytes'])
  forward=before
  for span in change['spans']:
   b,a=span['before'].encode(),span['after'].encode();ck('unique_forward_span_'+change['path']+str(len(checks)),forward.count(b)==1);forward=forward.replace(b,a,1)
  ck('complete_forward_'+change['path'],forward==after)
  backward=after
  for span in reversed(change['spans']):
   b,a=span['before'].encode(),span['after'].encode();ck('unique_reverse_span_'+change['path']+str(len(checks)),backward.count(a)==1);backward=backward.replace(a,b,1)
  ck('complete_inverse_'+change['path'],backward==before)
 names={'require','encoded','normalized','scope_bindings','validate_live','transform'}
 fs=[v for v in wt.body if isinstance(v,ast.FunctionDef) and v.name in names]
 ns=dict(Path=Path,copy=copy,json=json,hashlib=hashlib,ACTOR='codex:/root',KEY='restored21_v3_root_development',SLICE='RESTORED21_V3_BOUNDED_DEVELOPMENT',STATE='ROOT_REGISTERED_PENDING_RESTORED21_V3_DEVELOPMENT',pin=pin,read=read,load=load)
 exec(compile(ast.Module(body=fs,type_ignores=[]),str(Path(h['writer_ref']['path']))+'#pure-review','exec'),ns)
 pc,po=ns['transform'](copy.deepcopy(oldc),copy.deepcopy(oldo),copy.deepcopy(f),h['facts_ref'],oldc,oldo,copy.deepcopy(live))
 pr=[dict(path=r['path'],sha256=hashlib.sha256(ns['encoded'](v)).hexdigest(),bytes=len(ns['encoded'](v))) for r,v in zip(f['canonical_refs'],(pc,po))]
 ck('new_source_proof_recomputed',pr==proof['proposed_refs'] and proof['mode']=='check' and proof['transaction'] is None)
 w=pc['work_in_progress'];nw=w['mu_sdk_r368']
 ck('shared_and_nested_live_repaired',type(w['root_next_failure_ordinal_live']) is int and w['root_next_failure_ordinal_live']==nw['root_next_failure_ordinal_live']==live['next_original_failure_ordinal']==954 and w['later_diagnostics_observed_after_cutoff']==nw['later_diagnostics_observed_after_cutoff']==live['pending'] and [v['ordinal'] for v in live['pending']]==[953])
 ck('sourcecut_retained',nw['highest_registered_ordinal_at_cutoff']==952 and nw['next_failure_ordinal_at_cutoff']==953 and live['source_cutoff']==dict(highest_ordinal=952,next_failure_ordinal=953))
 for k in oldc['work_in_progress']:
  if k not in ('root_next_failure_ordinal_live','later_diagnostics_observed_after_cutoff'):ck('oldWIP_preserved_'+k,w[k]==oldc['work_in_progress'][k])
 ck('r367_historical_named_fields_exact',all(w[k]==v for k,v in oldc['work_in_progress'].items() if 'r367' in k))
 # Strong inverse: only restore the two intentionally changed shared fields and remove new WIP.
 ic,io=copy.deepcopy(pc),copy.deepcopy(po);del ic['work_in_progress']['mu_sdk_r368']
 for k in ('root_next_failure_ordinal_live','later_diagnostics_observed_after_cutoff'):ic['work_in_progress'][k]=copy.deepcopy(oldc['work_in_progress'][k])
 ic['failure_counters']=copy.deepcopy(oldc['failure_counters']);ic['workers']=copy.deepcopy(oldc['workers'])
 for k in ('expected_previous_revision','revision','updated_at','updated_by','note'):ic[k]=copy.deepcopy(oldc[k])
 del io['card_path_bindings']['W05-99']['subtasks']['restored21_v3_root_development']
 for k in ('revision','updated_at','updated_by'):io[k]=copy.deepcopy(oldo[k])
 ck('complete_independent_inverse_only_allowed_fields',ic==oldc and io==oldo)
 ck('old949_semantic_exact_new952_once',len(oldc['failure_counters'])==949 and pc['failure_counters'][:949]==oldc['failure_counters'] and len(pc['failure_counters'])==950 and pc['failure_counters'][-1]['original_payload']['observed_ordinal']==952)
 def arr(b):
  t=b.decode();s=t.index('[',t.index('"failure_counters":'));_,n=json.JSONDecoder().raw_decode(t[s:]);return t[s:s+n]
 ck('old949_raw_prefix_exact',arr(ns['encoded'](pc)).startswith(arr(raw[0]).rstrip()[:-1].rstrip()+','))
 added=pc['failure_counters'][-1];pay=added['original_payload']
 ck('original952_exits_and_binding',pay['immutable_origin_ref']==f['diagnostic']['origin_ref'] and origin['root_assigned_ordinal']==952 and origin['outer_exit']==pay['actual_outer_exit']==1 and pay['actual_python_exit'] is None and pay['actual_native_exit'] is None and all(origin[k] is None for k in ('SourcePython_exit','Go_exit','Native_exit','Model_exit')) and added['counted_once'] is True and added['counter_reset'] is False)
 ck('old_parents_owner_workers_unchanged',w['construction_active_parents']==['W05','W09'] and pc['workers'][:-1]==oldc['workers'] and po['card_path_bindings']['W05-99']['owner']==oldo['card_path_bindings']['W05-99']['owner']=='codex:/root/w1102_impl' and po['card_path_bindings']['W09-99']==oldo['card_path_bindings']['W09-99'])
 owner=po['card_path_bindings']['W05-99']['subtasks']['restored21_v3_root_development']
 ck('new_owner_scope_exact',owner==f['owner'] and owner['owner']=='codex:/root' and owner['current_source_writer'] is None and pc['workers'][-1]==f['worker'] and owner['scope_ref']==h['scope_ref'])
 ck('W05_review_binding_nonself',rh['actor_id']==sd['actor_id'] and sd['source_author'] is False and sd['actor_role']=='INDEPENDENT_NON_AUTHOR' and rh['source_handoff_ref']==scope['source_handoff_ref'] and rh['source_manifest_ref']==scope['source_manifest_ref'])
 ck('external_W05_argument_contract',scope['root_execution_guidance_ref']==rh['root_execution_guidance_ref'] and guidance['caller_does_not_parse_RootScope_or_verify_owner_fields'] is True and guidance['prepare_argv']==contract['prepare_argv']==contract['validate_argv'][:10] and guidance['validate_argv']==contract['validate_argv'] and len(contract['prepare_argv'])==10 and len(contract['validate_argv'])==12)
 ck('four_outputs_13once_partial',all(scope[k]==contract[k]==guidance[k]==owner[k] for k in ('worktree','environment','isolation_output','validation_output')) and scope['maximum_unique_tests']==13 and type(scope['maximum_unique_tests']) is int and scope['maximum_actual_attempts']==1 and type(scope['maximum_actual_attempts']) is int and scope['qualification_ceiling']==guidance['max_qualification'])
 ck('source_adoption_proof_current21and7',ad['decision']=='ACTUAL_SEVEN_TARGET_ADOPTION_VERIFIED' and ad['adoption_outcome_ref']==f['adoption_outcome_ref'] and ad['final_target_refs']==out['final_target_refs'] and all(pin(r['path'])==r for r in ad['source21']+ad['final_target_refs']))
 ck('formal_and_native_boundaries',all(scope[k] is False for k in ('formal_dispatcher','formal_acceptance','Main_adoption','production_DB_writes','external_model_calls','automatic_retry','parent_acceptance')) and type(scope['formal_case_accepted_delta']) is int and scope['formal_case_accepted_delta']==0 and nw['W09_Main_native_status']=='SOURCE_REJECTED_PENDING_CLEANUP_REPAIR_NO_ACTUAL')
 # Finite synthetic negative controls require no additional origin paths.
 for label,patch in [('reset_live',dict(next_original_failure_ordinal=952)),('boolean_live',dict(next_original_failure_ordinal=True)),('new955_missing954',dict(next_original_failure_ordinal=955)),('drop953',dict(pending=[]))]:
  bad=copy.deepcopy(live);bad.update(patch)
  try:ns['validate_live'](bad)
  except ValueError as e:controls.append(dict(name=label,rejected=True,error=str(e)))
  else:raise AssertionError(label)
 # Accepted source snapshot can change descriptions only when precisely bound by future live ref;
 # both current fields must follow the new list and cannot alias nested list.
 changed=copy.deepcopy(live);changed['pending'][0]['description']='Independent pure Source test of exact pending propagation'
 cc,oo=ns['transform'](copy.deepcopy(oldc),copy.deepcopy(oldo),copy.deepcopy(f),h['facts_ref'],oldc,oldo,changed)
 ck('both_pending_fields_follow_validated_input',cc['work_in_progress']['later_diagnostics_observed_after_cutoff']==cc['work_in_progress']['mu_sdk_r368']['later_diagnostics_observed_after_cutoff']==changed['pending'])
 cc['work_in_progress']['later_diagnostics_observed_after_cutoff'][0]['description']='local alias probe'
 ck('pending_deepcopy_no_alias',changed['pending'][0]['description']=='Independent pure Source test of exact pending propagation' and cc['work_in_progress']['mu_sdk_r368']['later_diagnostics_observed_after_cutoff']==changed['pending'])
 # Trusted helper real prefix, DLL boundary replaced before filesystem/native activity.
 update=copy.deepcopy(next(v for v in ast.parse(tr).body if isinstance(v,ast.FunctionDef) and v.name=='update_pair'))
 i=next(i for i,v in enumerate(update.body) if isinstance(v,ast.Assign) and isinstance(v.value,ast.Call) and isinstance(v.value.func,ast.Attribute) and v.value.func.attr=='WinDLL')
 update.body=update.body[:i+1]
 class StubPath(PureWindowsPath):
  def is_dir(self):return True
 class Boundary(Exception):pass
 calls=[]
 def dll(*a,**k):calls.append((a,k));raise Boundary()
 tn=dict(Path=StubPath,PATHS=tuple(StubPath(r['path']) for r in f['canonical_refs'][:2]),os=types.SimpleNamespace(name='nt'),ctypes=types.SimpleNamespace(WinDLL=dll))
 exec(compile(ast.Module(body=[update],type_ignores=[]),'<trusted-helper-pure-prelude>','exec'),tn)
 try:tn['update_pair'](f['canonical_refs'][:2],None,str(C),'activate')
 except Boundary:ck('trusted_helper_activate_prefix_no_actual',calls==[(('kernel32',),{'use_last_error':True})])
 else:raise AssertionError('missing pure boundary')
 calls2=[v for v in ast.walk(wt) if isinstance(v,ast.Call) and isinstance(v.func,ast.Attribute) and isinstance(v.func.value,ast.Name) and v.func.value.id=='tm' and v.func.attr=='update_pair']
 ck('writer_activate_and_pair_guard_exclusion',len(calls2)==1 and calls2[0].args[-1].value=='activate' and not {r['path'].casefold() for r in f['canonical_refs'][:2]}.intersection(v['path'].casefold() for v in sg['entries']))
 ck('source_guard_closed0',sg['closed'] is True and not sg['errors'] and sg['retained_handles_count']==0 and sg['verification']=='PASSED')
 ck('all_Canon_unchanged_commands39',all(Path(r['path']).read_bytes()==b for r,b in zip(f['canonical_refs'],raw)) and json.loads(raw[3])['revision']==39)
 save('proposed.checkpoint.source-review.json',pc);save('proposed.ownership.source-review.json',po)
 save('resolved-finding.json',dict(id='CP368-W05-P1-SHARED-LIVE-STALE',status='RESOLVED_IN_V2',shared_live_next=w['root_next_failure_ordinal_live'],nested_live_next=nw['root_next_failure_ordinal_live'],shared_pending=w['later_diagnostics_observed_after_cutoff'],source_snapshot_only=True,requires_fresh_Root_context=True,required_known_postcut_ordinals=[953,954,955],Root_reported_live_next=956,original_Canon_unchanged=True))
finally:
 cleanup=guard.close();save('source-guard.cleanup.actual.json',cleanup)
ck('independent_guard_closed0',cleanup['closed'] is True and not cleanup['errors'] and cleanup['retained_handles_count']==0 and cleanup['verification']=='PASSED')
ck('all_inputs_stable',all(pin(r['path'])==r for r in pins.values()))
save('input-pins.json',list(pins.values()));save('checks.json',checks);save('negative-controls.json',controls)
save('source-decision.json',dict(schema='researchos.cp368-w05-registration-independent-source-decision.v1',decision='SOURCE_ACCEPTED_FOR_ROOT_CP368_W05_REGISTRATION',actor_id=ACTOR,actor_role='INDEPENDENT_NON_AUTHOR',source_handoff_ref=hr,source_manifest_ref=mr,writer_ref=h['writer_ref'],facts_ref=h['facts_ref'],scope_ref=h['scope_ref'],source_proof_ref=h['source_proof_ref'],prior_review_handoff_ref=ahr,prior_review_manifest_ref=amr,prior_review_postseal_ref=apr,resolved_findings=['CP368-W05-P1-SHARED-LIVE-STALE'],findings=[],all_handles_closed=True,actual_executed=False,formal_acceptance=False,formal_case_accepted_delta=0,source_cutoff=dict(highest_ordinal=952,next_failure_ordinal=953),reviewed_source_snapshot_live=954,Root_reported_live_next=956,required_known_postcut_ordinals=[953,954,955],fresh_Root_postseal_context_required=True,qualification='Exact reviewed writer may activate once after fresh Root context with exact origins for every ordinal from953 to live-1 and unchanged four current Canon refs; Source snapshot is not actual execution context.',product_execution_grant=False,Main_Canon_written=False,new_reviewer_original_failures=[]))
save('result.json',dict(status='SOURCE_ACCEPTED_FOR_ROOT_CP368_W05_REGISTRATION',checks=len(checks),negative_controls=len(controls),pins=len(pins),all_handles_closed=True,new_reviewer_original_failures=[],Root_reported_live_next=956,actual_executed=False))
print(json.dumps(dict(status='SOURCE_ACCEPTED_FOR_ROOT_CP368_W05_REGISTRATION',checks=len(checks),controls=len(controls),pins=len(pins),new_failures=0,next_failure=956)))

