import sys
sys.dont_write_bytecode=True
import base64,copy,hashlib,json,types
from pathlib import Path
N=Path(__file__).resolve().parent;W=N.parents[1]
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99'
C=B/'checkpoint_r367_transaction_operation_v5_source_root/cp367-operation-v5-20261009'
M=W/'main_c19_source_registry_v2_source_codex/Mainv2-1a11fbc'
S=W/'integration_codex/root-main-v2-scope-20261009'
pins={};checks=[]
def pin(p):
 p=Path(p).resolve(strict=True);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def read(r):
 r=dict(path=str(Path(r['path']).resolve(strict=True)),sha256=r['sha256'].removeprefix('sha256:'),bytes=r['bytes']);assert pin(r['path'])==r
 assert r['path'] not in pins or pins[r['path']]==r
 pins[r['path']]=r;return Path(r['path']).read_bytes()
def load(r):return json.loads(read(r))
def local(p):return load(pin(p))
def save(n,v):
 with (N/n).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def ck(n,v):
 assert v,n
 checks.append(n)
ch=load(dict(path=str(C/'HDF.json'),sha256='49cdedad9104347f5bd66af35c63ce9b9e920b78d3181540ff9e2d62b64ddb2b',bytes=2667))
mh=load(dict(path=str(M/'HDF.json'),sha256='bfcb5010778c27ed4065bc6cda5d963e8f568f2207a413e7b5029b541f0613e7',bytes=9816))
for h in (ch,mh):
 for r in load(h['manifest_ref'])['members']:read(r)
facts=load(ch['facts_ref']);scope=load(ch['scope_ref']);contract=load(facts['calling_contract_ref']);change=load(mh['change_set_ref'])
adminh=local(C/'handoff.actual.json');proof=load(adminh['proof_ref']);resume=load(adminh['resume_ref']);admin_guard=load(adminh['guard_cleanup_ref'])
cpref=dict(path=str(R/'execution/v2.4/checkpoint.json'),sha256='5783d88c6f8841e32cc328e1fe1332162fad8ffdcf8125fecdb491a46a198a0f',bytes=4336749)
owref=dict(path=str(R/'execution/v2.4/path_ownership.json'),sha256='d307def27771aba3e07351e553ad562003bbf57bb885bf0efb650ea7c721239c',bytes=200160)
cpraw,owraw=read(cpref),read(owref);cp,ow=json.loads(cpraw),json.loads(owraw)
read(facts['canonical_refs'][2])
journal=Path(proof['transaction']['transaction_journal']);assert journal.is_relative_to(C)
ji=local(journal/'intent.json');jc=local(journal/'committed.json')
before=[read(r) for r in ji['before_refs']];after=[read(r) for r in ji['after_refs']];oldcp,oldow=[json.loads(b) for b in before]
outref=dict(path=str(M/'actual-adoption/outcome.json'),sha256='8ea1c5bfbc09f2c4458780169368753f20807acdb058f16d921514cd79c10ba7',bytes=98048)
out=load(outref);O=M/'actual-adoption';intent=local(O/'intent.json');committed=local(O/'committed.json');owned=local(O/'owned-handles.cleanup.actual.json');guard_report=local(O/'input-guard.cleanup.actual.json')
for r in out['final_target_refs']:read(r)
reqref=dict(path=str(S/'adoption-request.actual.root.json'),sha256='10f5439d1d0ee08fa8f8ad5d77a4bb638485109ad1294b378e17068c5e813990',bytes=1020)
request=load(reqref);vector=load(request['canonical_vector_ref']);read(request['scope_ref']);read(request['caller_ref'])
for pair in (dict(handoff_ref=scope['source_review_handoff_ref'],manifest_ref=scope['source_review_manifest_ref']),dict(handoff_ref=scope['component_review_handoff_ref'],manifest_ref=scope['component_review_manifest_ref'])):
 load(pair['handoff_ref'])
 for r in load(pair['manifest_ref'])['members']:read(r)
decision=load(scope['source_review_decision_ref']);read(proof['live_context_ref'])
for row in guard_report['entries']:read({k:row[k] for k in ('path','sha256','bytes')})
for d in facts['diagnostics']:read(d['origin_ref'])
for row in change['source21']:
 ref=row.get('current_ref',row.get('desired_ref'));read(ref)
for row in change['targets']:
 read(row['after_source_ref'])
 if row['before_archive_ref'] is not None:read(row['before_archive_ref'])
ios=[local(C/'canonical-registration.original-tool-io.root.json'),local(S/'postregistration-request.original-tool-io.root.json'),local(S/'main7-adoption.original-tool-io.root.json')]
baseline=load(dict(path=str(W/'integration_codex/w09c19v7-root-scope-20261009/pre-main-adoption.git-baseline.original-tool-io.root.json'),sha256='cfdd5898eaba16e3f0dd8fe01ff382834370dd903b6d187438f06f377cba0230',bytes=2526))
git=local(N/'current-git.original-tool-io.json')
gp=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
graw=read(dict(path=str(gp),sha256='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85',bytes=11404))
gm=types.ModuleType('combined_actual_review_guard');gm.__file__=str(gp);sys.modules[gm.__name__]=gm;exec(compile(graw,str(gp),'exec'),gm.__dict__)
guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);guard.acquire(list(pins.values()))
try:
 ck('exact_actual_CP367_OW171',cp['revision']==367 and ow['revision']==171 and proof['checkpoint_ref']==cpref and proof['ownership_ref']==owref and jc['after_refs']==[cpref,owref])
 ck('canonical_journal_before_exact',ji['expected_refs']==facts['canonical_refs'][:2] and all(hashlib.sha256(b).hexdigest()==r['sha256'] and len(b)==r['bytes'] for b,r in zip(before,facts['canonical_refs'])))
 ck('canonical_journal_after_exact',after==[cpraw,owraw] and jc['written_indices']==[0,1] and jc['both_verified_while_exclusively_held'] is True)
 ck('canonical_no_automatic_inverse',ji['mandatory_share_mode']==0 and ji['automatic_inverse'] is False)
 ck('canonical_journal_success_only',set(p.name for p in journal.iterdir())=={'0.before.json','1.before.json','0.after.proposed.json','1.after.proposed.json','intent.json','committed.json'})
 ck('old934_exact_and15_once',len(oldcp['failure_counters'])==934 and cp['failure_counters'][:934]==oldcp['failure_counters'] and len(cp['failure_counters'])==949 and [v['original_payload']['observed_ordinal'] for v in cp['failure_counters'][934:]]==list(range(937,952)))
 ck('registered15_payloads_exact',all(row['original_payload']['immutable_origin_ref']==d['origin_ref'] and row['original_payload']['actual_outer_exit']==d['actual_outer_exit'] and row['original_payload']['actual_python_exit']==d['actual_python_exit'] and row['original_payload']['actual_native_exit']==d['actual_native_exit'] and row['counted_once'] is True and row['counter_reset'] is False for row,d in zip(cp['failure_counters'][934:],facts['diagnostics'])))
 def arr(b):
  t=b.decode();s=t.index('[',t.index('"failure_counters":'));_,n=json.JSONDecoder().raw_decode(t[s:]);return t[s:s+n]
 ck('old934_raw_prefix_exact',arr(cpraw).startswith(arr(before[0]).rstrip()[:-1].rstrip()+','))
 ck('Source_cut951_next952_live_at_invocation952',proof['highest_registered_ordinal']==951 and proof['next_at_cutoff']==proof['next_original_failure_ordinal_live']==952 and proof['pending_after_cutoff']==[] and resume['next_original_failure_ordinal_live']==952)
 sourcepreview=load(ch['source_preview_ref']);pc=load(sourcepreview['proposed_checkpoint_ref']);po=load(sourcepreview['proposed_ownership_ref']);cpc,owc=copy.deepcopy(cp),copy.deepcopy(ow)
 for d in (pc,po,cpc,owc):d.pop('updated_at',None)
 ck('actual_Canon_equals_reviewed_preview_except_timestamp',cpc==pc and owc==po)
 ic,io=copy.deepcopy(cp),copy.deepcopy(ow)
 for k in ('failure_counters','workers','work_in_progress','expected_previous_revision','revision','updated_at','updated_by','note'):ic[k]=copy.deepcopy(oldcp[k])
 del io['card_path_bindings']['W09-99']['subtasks']['c19_main_source_registry_adoption']
 for k in ('revision','updated_at','updated_by'):io[k]=oldow[k]
 ck('actual_full_Canon_inverse_only_W09_addition',ic==oldcp and io==oldow and cp['workers'][:-1]==oldcp['workers'] and cp['workers'][-1]['step_id']=='W09-99')
 ck('actual_Main_request_SourceDecision_binding',request['issued_by']=='codex:/root' and request['scope_ref']==ch['scope_ref'] and request['caller_ref']==mh['caller_ref'] and scope['source_handoff_ref']==pin(M/'HDF.json') and scope['source_manifest_ref']==mh['manifest_ref'] and decision['decision']=='SOURCE_ACCEPTED_FOR_ROOT_SEVEN_TARGET_ADOPTION' and decision['caller_ref']==mh['caller_ref'])
 ck('actual_vector_before_CP_OW_SS_unchanged',vector['refs'][:3]==[cpref,owref,facts['canonical_refs'][2]] and vector['refs'][3]==change['targets'][6]['before_ref'] and out['canonical_vector_before_ref']==request['canonical_vector_ref'])
 ck('Main_actual_success',out['status']=='SOURCE_ADOPTED_PENDING_REAL_DISPATCH_AND_FORMAL_REVIEW' and out['error'] is None and out['transaction']['status']=='SEVEN_SOURCE_TARGETS_COMMITTED' and out['transaction']['written_indices']==list(range(7)) and out['transaction']['rollback_attempted'] is False)
 ck('seven_after_refs_exact',out['final_target_refs']==committed['after_refs']==[row['after_target_ref'] for row in change['targets']] and committed['all_seven_verified_while_held'] is True)
 ck('intent_exact_seven_targets',intent['exact_targets']==scope['exact_targets']==[r['path'] for r in out['final_target_refs']] and len(intent['before_base64'])==len(intent['after_base64'])==7)
 for i,row in enumerate(change['targets']):
  expected_after=read(row['after_source_ref']);ck('intent_after'+str(i)+'_matches_current',base64.b64decode(intent['after_base64'][i])==expected_after==read(out['final_target_refs'][i]))
  if i in (3,4,5):ck('intent_before'+str(i)+'_absent',intent['before_base64'][i] is None and row['before_ref'] is None)
  else:ck('intent_before'+str(i)+'_exact_archive',base64.b64decode(intent['before_base64'][i])==read(row['before_archive_ref']))
 ck('only_three_created_absent_targets',owned['created_indices']==[3,4,5] and owned['delete_marked_indices']==[] and owned['exact_targets']==scope['exact_targets'])
 ck('adoption_journal_only_expected_receipts',set(p.name for p in O.iterdir())=={'intent.json','committed.json','owned-handles.cleanup.actual.json','input-guard.cleanup.actual.json','outcome.json'})
 for label,g in [('admin_input',admin_guard),('main_input',guard_report),('main_owned_files_directories',owned)]:
  ck(label+'_closed0',g['closed'] is True and g['errors']==[] and g['retained_handles_count']==0)
 ck('outcome_guard_receipts_exact',out['guard_cleanup']==guard_report and out['owned_cleanup']==owned)
 ck('all_main_input_entries_verified_closed',guard_report['verification']=='PASSED' and all(e['verified'] is True and e['closed'] is True and e['final_path_match'] is True for e in guard_report['entries']))
 ck('all_admin_input_entries_verified_closed',admin_guard['verification']=='PASSED' and all(e['verified'] is True and e['closed'] is True and e['final_path_match'] is True for e in admin_guard['entries']))
 for i,row in enumerate(change['source21']):
  r=row.get('current_ref',row.get('desired_ref'));ck('Main_source21_'+str(i),hashlib.sha256((R/row['path']).read_bytes()).hexdigest()==r['sha256'])
 old_commands=json.loads(read(change['targets'][6]['before_archive_ref']));new_commands=json.loads(read(out['final_target_refs'][6]))
 altered=[key for key in old_commands['commands'] if old_commands['commands'][key]!=new_commands['commands'][key]]
 ck('commands_exactly_two_entries_changed',set(old_commands)==set(new_commands) and all(old_commands[k]==new_commands[k] for k in old_commands if k!='commands') and set(old_commands['commands'])==set(new_commands['commands']) and len(altered)==2)
 ck('commands_revision_remains39',old_commands['revision']==new_commands['revision']==39)
 ck('commands_unchanged_required_env',all(old_commands['commands'][k].get('required_env')==new_commands['commands'][k].get('required_env') for k in altered))
 iv=load(mh['registry_full_byte_inverse_ref']);ck('commands_whole_before_after_inverse_evidence',base64.b64decode(iv['whole_original_base64'])==read(change['targets'][6]['before_archive_ref']) and base64.b64decode(iv['whole_proposed_base64'])==read(out['final_target_refs'][6]))
 ck('no_product_or_formal_grant',out['checkpoint_ownership_step_state_written'] is False and out['producer_report_copied'] is False and out['formal_case_accepted_delta']==0 and out['formal_dispatcher'] is False and out['new_Go_SQL_API_model_calls']==0 and committed['product_execution'] is False)
 ck('source21_original_candidate_report_retained',pin(mh['source21_report_ref']['path'])==mh['source21_report_ref'])
 ck('three_original_invocations_exact_success',[(j['original_result']['chunk_id'],j['original_result']['exit_code']) for j in ios]==[('90cf3e',0),('493e47',0),('a2f433',0)] and all(j['replayed'] is False and 'ROOT_SOURCE_PYTHON_EXIT=0' in j['original_result']['output'] for j in ios))
 oldstatus=[x for x in baseline['result']['output'].splitlines() if x.startswith((' D ',' M '))];newstatus=[x for x in git['result']['output'].splitlines() if x.startswith((' D ',' M '))]
 ck('original13_dirty_preserved_plus4_authorized',len(oldstatus)==13 and set(oldstatus)<=set(newstatus) and set(newstatus)-set(oldstatus)=={' M execution/v2.4/commands.json',' M internal/domain/domain_test.go',' M internal/domain/retrieval_test.go',' M ops/ci/retrieval.py'})
 deleted=[line[3:] for line in oldstatus if line.startswith(' D ')];ck('eleven_preexisting_deletions_still_absent',len(deleted)==11 and all(not (R/p).exists() for p in deleted))
 gout=git['result']['output'].replace('\r\n','\n');ck('current_git_HEAD_main_empty_index',git['result']['exit_code']==0 and '\nmain\nGIT_BRANCH_EXIT=0\n' in gout and '\nadc460c2138528f163f7fdab5e8d81dde157b7fb\nGIT_HEAD_EXIT=0\nGIT_INDEX_EXIT=0\n' in gout)
 save('actual-summary.json',dict(checkpoint_ref=cpref,ownership_ref=owref,step_state_ref=facts['canonical_refs'][2],commands_ref=out['final_target_refs'][6],commands_document_revision=39,changed_command_ids=altered,registered_diagnostic_count=949,highest_registered_ordinal=951,next_at_source_cutoff=952,root_live_at_original_invocations=952,current_Root_reported_live=953,post_adoption_pending_ordinals=[952],old13_dirty_preserved=True,current_tracked_dirty_count=len(newstatus),preexisting_deleted_paths=deleted,actual_source21_byte_applicability=True,Main_native_packet_current=False,dispatcher_current=False,formal_current=False,formal_case_accepted_delta=0,product_native_calls=0))
finally:
 cleanup=guard.close();save('source-guard.cleanup.actual.json',cleanup);assert cleanup['closed'] and not cleanup['errors'] and cleanup['retained_handles_count']==0
ck('all_review_input_pins_stable',all(pin(r['path'])==r for r in pins.values()))
save('input-pins.json',list(pins.values()));save('checks.json',checks)
save('result.json',dict(status='ACTUAL_CP367_OW171_AND_MAIN7_SOURCE_ADOPTION_VERIFIED_PASS',checks=len(checks),pins=len(pins),new_reviewer_original_failures=[],admin_and_Main_product_execution=False,actual_Main_source_adoption=True,Main_native_packet_current=False,formal_acceptance=False,formal_case_accepted_delta=0,post_adoption_external_diagnostic_pending=[952],Root_reported_current_live=953))
print(json.dumps(dict(status='ACTUAL_CP367_OW171_AND_MAIN7_SOURCE_ADOPTION_VERIFIED_PASS',checks=len(checks),pins=len(pins),reviewer_new_failures=0)))
