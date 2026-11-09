import sys
sys.dont_write_bytecode=True
import ast,copy,hashlib,json
from datetime import datetime
from pathlib import Path
import types
N=Path(__file__).resolve().parent;B=N.parents[1]
R=Path('D:/作品集/ResearchOS/research-os')
C=B/'checkpoint_r368_restored21_v2_source_root/cp368-w05v2-20261009'
S=B/'checkpoint_r368_w05_v2_independent_review_codex/cp368v2r-01a11fea'
ACTOR='codex:/root/attach_fixture_source_review'
pins={};checks=[]
def fixed(p,h,z):return dict(path=str(p.resolve()),sha256=h,bytes=z)
def pin(p):
 p=Path(p).resolve(strict=True);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def norm(r):return dict(path=str(Path(r['path']).resolve(strict=True)),sha256=r['sha256'].removeprefix('sha256:'),bytes=r['bytes'])
def read(r):
 r=norm(r);assert pin(r['path'])==r,r['path'];assert r['path'] not in pins or pins[r['path']]==r
 pins[r['path']]=r;return Path(r['path']).read_bytes()
def load(r):return json.loads(read(r))
def local(p):return load(pin(p))
def save(n,v):
 with (N/n).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def ck(n,v):
 assert v,n
 checks.append(n)
hr=fixed(C/'HDF.json','ff68cc7c813e1932df8351995251b6bd99ff47a6f7bd69f8fa0913b5c608e4fa',2203)
mr=fixed(C/'MF.json','efb2ddaf6af93a087a932f07033d696b9649fea4d2efff74364b41373a6af0af',3143)
shr=fixed(S/'HDF.json','0e4e6ce7d0f80c6357c05e68f23197ca5868a3f8731d993c19009ff0842404c9',4609)
smr=fixed(S/'MF.json','db49bb6cec19bd724203099c682b30359c70cc74566af8aa9d037fc41815a1cf',4031)
spr=fixed(S/'postseal.json','7f23ded00c9e4913bc96e8de22430e97e0741b51b4302cf586d91c9b97cc968e',988)
pr=fixed(C/'canonical_pair.activate.json','a781ae1626259eb7c2039fc78c242e01cdbeda181043b36c2b75a07a92f6e00f',2351)
lr=fixed(C/'live-context.reconciled958.actual.root.json','841b3c3b9b9f128664d0d83c7dbbf105e3f6dddb1250669efbe0c4fa3eb95c3e',3060)
ar=fixed(C/'actual-argv.reconciled958.root.json','f498d6f5672b6b7eed840127c3cef4f31f42563ebf4f61e116eb74e03f9be0f7',2101)
h,m,sh,sm,sp,proof,live,argv=[load(r) for r in (hr,mr,shr,smr,spr,pr,lr,ar)]
for v in m['members']+sm['members']:read(v)
f=load(h['facts_ref']);scope=load(h['scope_ref']);sd=load(sh['source_decision_ref'])
registration=local(C/'registration.actual.original-tool-io.root.json')
reconcile=local(C/'context957-reconcile.original-tool-io.root.json')
auth=local(C/'postseal-authorization-check.root.json')
read(pin(C/'reconcile_957_prepare.root.py'))
oldlive=load(auth['live_context_ref'])
origins={v['ordinal']:load(v['origin_ref']) for v in live['pending']}
sourceguard=local(C/'source_guard.cleanup.activate.json')
for v in sourceguard['entries']:read({k:v[k] for k in ('path','sha256','bytes')})
J=Path(proof['transaction']['transaction_journal']);assert J.parent==C
ji,jc=local(J/'intent.json'),local(J/'committed.json')
before=[read(v) for v in ji['before_refs']];after=[read(v) for v in ji['after_refs']]
oldc,oldo=[json.loads(v) for v in before]
currentrefs=[
 fixed(R/'execution/v2.4/checkpoint.json','51c038a8f6de8415f66dfd0122241989591dd7ba0dad4adf0560e2bf6d7f52ac',4347568),
 fixed(R/'execution/v2.4/path_ownership.json','07b0aeea2b6bb84acde4982be576f7a7cbb22e04a76e5c89216ae3e43231048d',202735),
 *f['canonical_refs'][2:]]
current=[read(v) for v in currentrefs];cp,ow=[json.loads(v) for v in current[:2]]
for pair in f['pairs']:
 ph,pm=load(pair['handoff_ref']),load(pair['manifest_ref']);assert ph['manifest_ref']==pair['manifest_ref']
 members=pm['members'];members=list(members.values()) if type(members) is dict else members
 for r in members:read(r)
for r in f['input_refs']:read(r)
ad=load(f['adoption_review_decision_ref']);out=load(f['adoption_outcome_ref']);origin952=load(f['diagnostic']['origin_ref'])
wr=read(h['writer_ref']);wt=ast.parse(wr)
gp=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
gr=read(fixed(gp,'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85',11404))
ownorigins=[local(N/f'failure{i}.original-tool-io.json') for i in range(959,964)]
gm=types.ModuleType('cp368_actual_review_guard');gm.__file__=str(gp);sys.modules[gm.__name__]=gm;exec(compile(gr,str(gp),'exec'),gm.__dict__)
guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
try:
 guard.acquire(list(pins.values()))
 ck('all_finite_inputs_held_exact',all(hashlib.sha256(guard.get_buffer(v['path'])).hexdigest()==v['sha256'] for v in pins.values()))
 ck('accepted_exact_Source_pair',sh['status']==sd['decision']=='SOURCE_ACCEPTED_FOR_ROOT_CP368_W05_REGISTRATION' and sh['manifest_ref']==smr and sd['source_handoff_ref']==hr and sd['source_manifest_ref']==mr and sd['writer_ref']==h['writer_ref'] and sd['facts_ref']==h['facts_ref'] and sd['scope_ref']==h['scope_ref'] and sp['handoff_ref']==shr and sp['manifest_ref']==smr)
 ck('Root_authorization_accepted_Source_binding',auth['source_review_handoff_ref']==shr and auth['source_review_manifest_ref']==smr and auth['source_decision_ref']==sh['source_decision_ref'] and auth['source_handoff_ref']==hr and auth['facts_ref']==h['facts_ref'] and auth['writer_ref']==h['writer_ref'])
 ck('proof_actual_mode_and_current_pair',proof['mode']=='activate' and proof['transaction']['checkpoint_ref']==currentrefs[0] and proof['transaction']['ownership_ref']==currentrefs[1] and proof['proposed_refs']==currentrefs[:2])
 ck('journal_before_exact_source_pins',ji['expected_refs']==f['canonical_refs'][:2] and all(hashlib.sha256(b).hexdigest()==r['sha256'] and len(b)==r['bytes'] for b,r in zip(before,f['canonical_refs'])))
 ck('journal_after_actual_current_exact',after==current[:2] and jc['after_refs']==currentrefs[:2] and jc['written_indices']==[0,1] and jc['both_verified_while_exclusively_held'] is True)
 ck('only_success_transaction_files',set(p.name for p in J.iterdir())=={'intent.json','committed.json','0.before.json','1.before.json','0.after.proposed.json','1.after.proposed.json'})
 ck('exclusive_intent_no_automatic_inverse',ji['mandatory_share_mode']==0 and ji['automatic_inverse'] is False)
 ck('sourceguard_actual_closed0',sourceguard['closed'] is True and not sourceguard['errors'] and sourceguard['retained_handles_count']==0 and sourceguard['verification']=='PASSED' and all(v['closed'] is True and v['verified'] is True and v['final_path_match'] is True for v in sourceguard['entries']))
 ck('sourceguard_excludes_transaction_pair',not {r['path'].casefold() for r in currentrefs[:2]}.intersection(v['path'].casefold() for v in sourceguard['entries']))
 names={'require','encoded','normalized','scope_bindings','validate_live','transform'}
 fs=[v for v in wt.body if isinstance(v,ast.FunctionDef) and v.name in names]
 ns=dict(Path=Path,copy=copy,json=json,hashlib=hashlib,ACTOR='codex:/root',KEY='restored21_v3_root_development',SLICE='RESTORED21_V3_BOUNDED_DEVELOPMENT',STATE='ROOT_REGISTERED_PENDING_RESTORED21_V3_DEVELOPMENT',pin=pin,read=read,load=load)
 exec(compile(ast.Module(body=fs,type_ignores=[]),str(Path(h['writer_ref']['path']))+'#pure-actual-review','exec'),ns)
 wanted=ns['transform'](copy.deepcopy(oldc),copy.deepcopy(oldo),copy.deepcopy(f),h['facts_ref'],oldc,oldo,copy.deepcopy(live))
 ck('actual_full_bytes_match_qualified_transform',[ns['encoded'](v) for v in wanted]==current[:2])
 ic,io=copy.deepcopy(cp),copy.deepcopy(ow);del ic['work_in_progress']['mu_sdk_r368']
 for k in ('root_next_failure_ordinal_live','later_diagnostics_observed_after_cutoff'):ic['work_in_progress'][k]=copy.deepcopy(oldc['work_in_progress'][k])
 ic['workers']=copy.deepcopy(oldc['workers']);ic['failure_counters']=copy.deepcopy(oldc['failure_counters'])
 for k in ('expected_previous_revision','revision','updated_at','updated_by','note'):ic[k]=copy.deepcopy(oldc[k])
 del io['card_path_bindings']['W05-99']['subtasks']['restored21_v3_root_development']
 for k in ('revision','updated_at','updated_by'):io[k]=copy.deepcopy(oldo[k])
 ck('complete_independent_inverse',ic==oldc and io==oldo)
 ck('actual_revisions_and_int0',cp['revision']==368 and ow['revision']==172 and type(cp['revision']) is int and type(ow['revision']) is int)
 ck('old949_preserved_append952_once',len(cp['failure_counters'])==950 and cp['failure_counters'][:949]==oldc['failure_counters'] and cp['failure_counters'][-1]['original_payload']['observed_ordinal']==952)
 def arr(b):
  t=b.decode();i=t.index('[',t.index('"failure_counters":'));_,n=json.JSONDecoder().raw_decode(t[i:]);return t[i:i+n]
 ck('old949_raw_prefix_preserved',arr(current[0]).startswith(arr(before[0]).rstrip()[:-1].rstrip()+','))
 row=cp['failure_counters'][-1];pay=row['original_payload']
 ck('original952_exact_exit_and_identity',pay['immutable_origin_ref']==f['diagnostic']['origin_ref'] and origin952['root_assigned_ordinal']==952 and origin952['outer_exit']==pay['actual_outer_exit']==1 and pay['actual_python_exit'] is None and pay['actual_native_exit'] is None and row['counted_once'] is True and row['counter_reset'] is False and row['origin_key'] not in {v.get('origin_key') for v in oldc['failure_counters']})
 w=cp['work_in_progress'];nw=w['mu_sdk_r368'];pending=list(range(953,958))
 ck('actual_sourcecut952_next953',nw['highest_registered_ordinal_at_cutoff']==952 and nw['next_failure_ordinal_at_cutoff']==953 and live['source_cutoff']==dict(highest_ordinal=952,next_failure_ordinal=953))
 ck('actual_shared_and_nested_live958_pending953to957',w['root_next_failure_ordinal_live']==nw['root_next_failure_ordinal_live']==live['next_original_failure_ordinal']==proof['live_next']==958 and w['later_diagnostics_observed_after_cutoff']==nw['later_diagnostics_observed_after_cutoff']==live['pending'] and [v['ordinal'] for v in live['pending']]==pending)
 ck('all_other_WIP_history_preserved',all(w[k]==v for k,v in oldc['work_in_progress'].items() if k not in ('root_next_failure_ordinal_live','later_diagnostics_observed_after_cutoff')))
 ck('two_parents_original_W05_owner_and_W09_unchanged',w['construction_active_parents']==['W05','W09'] and ow['card_path_bindings']['W05-99']['owner']==oldo['card_path_bindings']['W05-99']['owner']=='codex:/root/w1102_impl' and ow['card_path_bindings']['W09-99']==oldo['card_path_bindings']['W09-99'])
 owner=ow['card_path_bindings']['W05-99']['subtasks']['restored21_v3_root_development']
 ck('new_Root_worker_owner_exact',owner==f['owner'] and owner['owner']=='codex:/root' and owner['current_source_writer'] is None and cp['workers'][:-1]==oldc['workers'] and cp['workers'][-1]==f['worker'])
 ck('Source_adoption_current21and7',ad['adoption_outcome_ref']==f['adoption_outcome_ref'] and ad['final_target_refs']==out['final_target_refs'] and all(pin(v['path'])==v for v in ad['source21']+ad['final_target_refs']))
 ck('no_formal_or_parent_acceptance',nw['formal_case_accepted_delta']==owner['formal_case_accepted_delta']==proof['formal_case_accepted_delta']==0 and type(nw['formal_case_accepted_delta']) is int and nw['parent_acceptance'] is owner['parent_acceptance'] is proof['formal_acceptance'] is False and proof['Main_native_executed'] is False)
 ck('SS_commands_unchanged_revision39',currentrefs[2:]==f['canonical_refs'][2:] and json.loads(current[3])['revision']==39)
 ck('actual_Root_command_original_success',registration['original_result']['chunk_id']=='a30a15' and registration['original_result']['exit_code']==0 and registration['original_result']['output'].endswith('ROOT_SOURCE_PYTHON_EXIT=0\r\n') and json.loads(registration['original_result']['output'].splitlines()[0])==pr)
 expected_cmd="& "+" ".join("'"+v+"'" for v in argv['argv'])
 ck('actual_original_argv_exact',registration['original_args']['cmd'].splitlines()[0]==expected_cmd and argv['argv'][6]==h['writer_ref']['path'] and argv['argv'][7]=='activate' and argv['argv'][8:10]==[h['facts_ref']['sha256'],str(h['facts_ref']['bytes'])] and argv['argv'][10:]==[lr['path'],lr['sha256'],str(lr['bytes'])])
 ck('fresh_context_and_argv_canonical',argv['live_context_ref']==lr and argv['next_original_failure_ordinal']==958 and argv['complete_pending']==pending and argv['argv'][10]==str(Path(argv['argv'][10]).resolve(strict=True)) and datetime.fromisoformat(live['created_utc'])>datetime.fromisoformat(oldlive['created_utc']))
 ck('context_after_Source_seal',datetime.fromisoformat(live['created_utc']).timestamp()>Path(spr['path']).stat().st_mtime)
 recout=json.loads(reconcile['original_result']['output'].splitlines()[0])
 ck('reconcile_original_success_exact_refs',reconcile['original_result']['chunk_id']=='b52eda' and reconcile['original_result']['exit_code']==0 and reconcile['original_result']['output'].endswith('ROOT_SOURCE_PYTHON_EXIT=0\r\n') and recout['argv_receipt_ref']==ar and recout['live_context_ref']==lr and recout['origin957_ref']==argv['origin957_ref'] and recout['all_Canon_before_unchanged'] is True)
 ck('957_original_pretransaction_failure',origins[957]['original_result']['chunk_id']=='aeafbc' and origins[957]['actual_outer_exit']==origins[957]['actual_python_exit']==1 and origins[957]['actual_native_exit'] is None and origins[957]['actual_model_exit'] is None and 'ValueError: CANONICAL_REF_PATH' in origins[957]['original_result']['output'] and 'update_pair' not in origins[957]['original_result']['output'])
 reconcile_src=read(pin(C/'reconcile_957_prepare.root.py')).decode()
 ck('reconciliation_checks_no_prior_transaction',all(s in reconcile_src for s in ("for ref in facts['canonical_refs']:m.read(ref)","not (N/'source_guard.cleanup.activate.json').exists()","not list(N.glob('activate.transaction.*'))","NO_GUARD_TRANSACTION_OR_WRITES")))
 ck('953954_outer1_other_exits_NULL',all(origins[i]['outer_exit']==1 and all(origins[i][k] is None for k in ('SourcePython_exit','Go_exit','Native_exit','Model_exit')) for i in (953,954)))
 cls=origins[955]['diagnostic_classification']
 ck('955_outer0_child2_preserved',origins[955]['original_result']['exit_code']==cls['outer_exit_code']==0 and cls['first_rg_child_exit_code']==2 and all(cls[k] is None for k in ('python_exit_code','native_exit_code','model_exit_code')))
 cls=origins[956]['diagnostic_classification']
 ck('956_outer1_child_unknown_preserved',origins[956]['original_result']['exit_code']==cls['outer_exit_code']==1 and cls['child_exit_codes_not_captured'] is True and all(cls[k] is None for k in ('python_exit_code','native_exit_code','model_exit_code')))
 ck('reviewer_five_origins_preserved_once',[(v['root_assigned_ordinal'],v['original_result']['chunk_id']) for v in ownorigins]==list(zip(range(959,964),('6cfa1a','ccf906','ffbd3a','2c3a6e','c74e98'))) and all(v['outer_exit']==v['original_result']['exit_code']==1 and all(v[k] is None for k in ('SourcePython_exit','Go_exit','Native_exit','Model_exit')) for v in ownorigins))
 save('actual-summary.json',dict(checkpoint_ref=currentrefs[0],ownership_ref=currentrefs[1],step_state_ref=currentrefs[2],commands_ref=currentrefs[3],commands_revision=39,actual_proof_ref=pr,actual_live_context_ref=lr,actual_global_nested_live=958,actual_pending_ordinals=pending,registered_failure_count=950,highest_registered_cutoff=952,next_at_cutoff=953,Root_current_reported_live=964,post_registration_pending_ordinals=list(range(958,964)),new_reviewer_failure_ordinals=list(range(959,964)),Source_review_ref=shr,all_actual_handles_closed=True,formal_acceptance=False,formal_case_accepted_delta=0,Main_or_Canon_written_by_reviewer=False,W05_actual_outputs_not_read_or_guarded=True))
finally:
 cleanup=guard.close();save('source-guard.cleanup.actual.json',cleanup)
ck('reviewer_guard_closed0',cleanup['closed'] is True and not cleanup['errors'] and cleanup['retained_handles_count']==0 and cleanup['verification']=='PASSED')
ck('all_inputs_stable',all(pin(r['path'])==r for r in pins.values()))
save('input-pins.json',list(pins.values()));save('checks.json',checks)
save('result.json',dict(status='ACTUAL_CP368_OW172_W05_REGISTRATION_VERIFIED_PASS',checks=len(checks),pins=len(pins),all_handles_closed=True,new_reviewer_failure_ordinals=list(range(959,964)),current_Root_reported_live=964,actual_registration_replayed=False,product_commands=0))
print(json.dumps(dict(status='ACTUAL_CP368_OW172_W05_REGISTRATION_VERIFIED_PASS',checks=len(checks),pins=len(pins),reviewer_failures=[959,960,961,962,963],Root_reported_live=964)))

