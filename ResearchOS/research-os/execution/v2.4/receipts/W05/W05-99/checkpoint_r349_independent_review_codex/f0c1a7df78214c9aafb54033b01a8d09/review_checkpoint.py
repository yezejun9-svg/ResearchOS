import json, pathlib, hashlib
B=pathlib.Path(r"D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/sdk_five_go_root_adoption_preparation_codex/04a454a98b164aa2983f16245f273e9d/checkpoint-r349-trial-failure-preserved")
O=pathlib.Path(__file__).parent
inputs={};checks=[]
def ref(p):
 p=pathlib.Path(p);raw=p.read_bytes()
 return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def read(p,expected=None):
 p=pathlib.Path(p)
 assert p.is_absolute()
 assert p.name!='trusted-qualification-coordinator.json'
 raw=p.read_bytes();r=dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
 if expected: assert r['sha256']==expected['sha256'] and r['bytes']==expected['bytes'],str(p)
 key=str(p.resolve()).lower()
 if key in inputs: assert inputs[key]==r
 inputs[key]=r
 return raw
def obj(p,expected=None):return json.loads(read(p,expected))
def rr(r):return obj(r['path'],r)
def check(name,ok):
 checks.append(dict(check=name,passed=bool(ok)))
 assert ok,name
def put(n,d):
 with (O/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
h=obj(B/'handoff.json')
m=rr(h['manifest_ref'])
for r in m['members']:read(r['path'],r)
pair=obj(B/'canonical_pair.actual.json');resume=rr(h['resume_ref'])
j=pathlib.Path(pair['transaction']['transaction_journal']);intent=obj(j/'intent.json');committed=obj(j/'committed.json')
old=rr(intent['before_refs'][0]);after=rr(intent['after_refs'][0])
oldow=rr(intent['before_refs'][1]);afterow=rr(intent['after_refs'][1])
cp=rr(pair['checkpoint_ref']);ow=rr(pair['ownership_ref'])
for r in pair['other_canonical_refs']:read(r['path'],r)
check('exact_authorized_CP349_pin',pair['checkpoint_ref']['sha256']=='6c0d3468f9c55a69b9bd488c88bfeb7002333be970bb24160ba902982fba9a6b' and pair['checkpoint_ref']['bytes']==3942384)
check('exact_authorized_OW168_pin',pair['ownership_ref']['sha256']=='48c5641956b5f22bb48f7775e46d90494bd95944027f55070e430e207a506452' and pair['ownership_ref']['bytes']==192861)
check('journal_actual_CP_bytes_match',read(j/'0.after.proposed.json')==read(pair['checkpoint_ref']['path']))
check('OW168_three_way_bytes_unchanged',read(j/'1.before.json')==read(j/'1.after.proposed.json')==read(pair['ownership_ref']['path']) and ow['revision']==168)
check('CP348_exact_before',old['revision']==348 and intent['before_refs'][0]['sha256']=='5991855edd56cea2042cbb0231226e46ce574adbb54d783507d7573036a69f6d')
check('CP_revision_chain',cp['revision']==349 and cp['expected_previous_revision']==348)
check('journal_exclusive_commit',intent['mandatory_share_mode']==0 and intent['automatic_inverse'] is False and committed['written_indices']==[0,1] and committed['both_verified_while_exclusively_held'] is True)
check('journal_expected_before_pins',all(a['sha256']==b['sha256'] and a['bytes']==b['bytes'] for a,b in zip(intent['before_refs'],intent['expected_refs'])))
check('journal_after_actual_pins',committed['after_refs']==[pair['checkpoint_ref'],pair['ownership_ref']])
check('canonical_changed_fields_bounded',{k for k in old if old[k]!=cp[k]}=={'revision','expected_previous_revision','failure_counters','updated_at','note','work_in_progress'} and set(old)==set(cp))
check('old742_exact_prefix',len(old['failure_counters'])==742 and cp['failure_counters'][:742]==old['failure_counters'])
new=cp['failure_counters'][742:]
check('five_new_ordinals_exact',[r['original_payload']['observed_ordinal'] for r in new]==list(range(745,750)) and len(cp['failure_counters'])==747)
check('new_origin_keys_unique',len({r['origin_key'] for r in new})==5 and not ({r['origin_key'] for r in new}&{r.get('origin_key') for r in old['failure_counters']}))
origins={}
for f in new:
 p=f['original_payload'];n=p['observed_ordinal'];origins[n]=rr(f['evidence_ref'])
 check('failure_%s_immutable_once'%n,p['immutable_origin_ref']==f['evidence_ref'] and f['origin_key']==hashlib.sha256((f['evidence_ref']['sha256']+'#'+str(n)).encode()).hexdigest() and f['counted_once'] is True and f['counter_reset'] is False and f['automatic_retry'] is False)
expected=[(0,0,1,None),(1,None,None,0),(0,None,None,0),(1,None,None,0),(None,None,None,0)]
check('failure_exit_layers_exact',[(x['original_payload']['actual_outer_exit'],x['original_payload']['actual_python_exit'],x['original_payload']['actual_native_exit'],x['original_payload']['provider_requests']) for x in new]==expected)
check('745_native_failure_original',origins[745]['original_result']['exit_code']==0 and origins[745]['actual_python_exit']==0 and origins[745]['actual_native_exit_host_execute']==1 and origins[745]['provider_count'] is None and origins[745]['structured_state']=='FAILED_EXECUTION_CLOSED')
check('746_original_gap_preserved',origins[746]['original_result']['exit_code']==1 and bool(origins[746]['capture_gap']) and origins[746]['failure745_recounted'] is False)
check('747_two_diagnostics_one_call',origins[747]['original_io']['result']['exit_code']==0 and origins[747]['original_io']['result']['output'].count('(os error 2)')==2 and origins[747]['exit_interpretation']['rg_exit_code'] is None)
check('748_four_diagnostics_one_call',origins[748]['original_io']['result']['exit_code']==1 and origins[748]['original_io']['result']['output'].count('(os error 3)')==4)
check('749_pre_tool_gap_preserved',origins[749]['actual_outer_exit'] is None and origins[749]['actual_python_exit'] is None and origins[749]['actual_native_exit'] is None and bool(origins[749]['capture_gap']) and 'before any tool call' in origins[749]['execution_position'])
w=cp['work_in_progress']
check('counter_summaries_consistent',w['r349_registered_failure_count']==h['registered_failures']==resume['registered_failures']==747 and w['r349_highest_observed_diagnostic_ordinal']==h['highest_diagnostic_ordinal']==resume['highest_diagnostic_ordinal']==749)
life=rr(w['mu_sdk_actual_model_trial_output_ref']);fh=rr(w['mu_sdk_actual_model_trial_failure_independent_handoff_ref']);fm=rr(fh['manifest_ref'])
for r in fm['members']:read(r['path'],r)
rh=rr(w['mu_sdk_actual_model_trial_recovery_design_handoff_ref']);rm=rr(rh['manifest_ref'])
for r in rm['members']:read(r['path'],r)
business=rr(w['mu_sdk_actual_model_trial_business_state_ref'])
support={pathlib.Path(r['path']).name:r for r in fm['input_refs']}
wrapper=rr(support['wrapper.source-guard.cleanup.actual.json'])
once=rr(support['host-go.once.json']);clock=rr(support['whole-trial-clock.json'])
check('trial_structured_failure',life['state']=='FAILED_EXECUTION_CLOSED' and life['go_sent'] is True and life['automatic_retry'] is False and life['formal_acceptance'] is False and life['C7_actual_lifecycle_proven'] is False)
check('two_job_lifecycle_proofs',len(life['jobs'])==2 and all(x['cleanup']['closed'] is True and x['cleanup']['proof']['active_processes']==0 and x['cleanup']['proof']['primary_exit_confirmed'] is True and x['cleanup']['proof']['pid_match'] is True and x['cleanup']['proof']['creation_match'] is True and x['cleanup']['watchdog']['duplicate_handle_closed'] is True and x['cleanup']['producer']['closed'] is True and x['cleanup']['producer']['job_handle_closed'] is True and x['cleanup']['producer']['primary_handle_closed'] is True for x in life['jobs']))
check('native_exit_0_then_1',[x['cleanup']['proof']['primary_exit_code'] for x in life['jobs']]==[0,1])
guards=life['source_guard_cleanup']+[wrapper]
check('all86_guard_entries_closed',sum(len(g['entries']) for g in guards)==86 and all(g['closed'] is True and g['retained_handles_count']==0 and not g['errors'] and all(e['closed'] is True for e in g['entries']) for g in guards))
writer_guard=obj(B/'source_guard.cleanup.actual.json')
check('checkpoint_writer_guards_closed',writer_guard['closed'] is True and writer_guard['retained_handles_count']==0 and not writer_guard['errors'] and all(e['closed'] is True for e in writer_guard['entries']))
check('business_admitted_open',business['run']['status']==w['mu_sdk_qualification_run_status']==resume['qualification_run_status']=='QUEUED' and business['task']['status']==w['mu_sdk_qualification_task_status']==resume['qualification_task_status']=='RUNNING' and business['run']['id']==business['task']['active_run_id']==w['mu_sdk_qualification_run_id']==resume['qualification_run_id'])
check('business_predispatch_no_worker',len(business['dispatch'])==1 and business['dispatch'][0]['state']==w['mu_sdk_runtime_dispatch_state']==resume['dispatch_state']=='PREPARED' and business['dispatch'][0]['worker']==business['dispatch'][0]['journal_locator']==w['mu_sdk_runtime_dispatch_worker']==resume['dispatch_worker']=='')
check('provider_unknown_distinct_recorded_zero',life['provider_requests'] is None and business['provider_requests_total'] is None and w['mu_sdk_actual_external_provider_requests_current_trial'] is None and resume['provider_requests_current_trial'] is None and w['mu_sdk_current_trial_recorded_model_effects']==business['model_requests_recorded_as_resource_effects']==resume['recorded_model_effects']==0)
check('business_no_acceptance',business['counts']['project_Acceptance']==0 and business['counts']['runtime_observations']==0 and business['counts']['resource_effects']==0 and business['task']['acceptance_id'] is None)
check('grant_consumed_clock_not_reset',w['mu_sdk_current_go_once_consumed'] is True and resume['once_consumed'] is True and w['mu_sdk_original_trial_clock_reset_permitted'] is False and resume['clock_reset_permitted'] is False and w['mu_sdk_current_live_execution_grant_active'] is False and resume['automatic_retry'] is False and 'CONSUMED_FOR_HOST_GO' in json.dumps(once))
check('business_open_c7_unstarted',w['mu_sdk_business_reconciliation_state']=='OPEN_PRE_DISPATCH_ADMITTED_RUN_NO_WORKER_JOURNAL' and w['mu_sdk_controller_state']=='C7_O4_SOURCE_READY_C7_ACTUAL_NOT_STARTED' and w['mu_sdk_c7_actual_lifecycle_proven'] is False)
check('qualification_and_formal_not_promoted',w['mu_sdk_runtime_qualification'] is False and h['qualification'] is False and h['formal_acceptance'] is False and resume['completion_asserted'] is False and resume['current_formal_accepted']==0 and resume['formal_required']==42 and resume['historical_accepted_parents']==6 and cp['current_effective_formal_status']==old['current_effective_formal_status'] and cp['current_effective_formal_status']['formal_cases_accepted']==0)
check('resume_actual_refs_consistent',resume['checkpoint_ref']==pair['checkpoint_ref'] and resume['failed_trial_ref']==w['mu_sdk_actual_model_trial_output_ref'] and resume['failure_review_ref']==w['mu_sdk_actual_model_trial_failure_independent_handoff_ref'] and resume['recovery_design_ref']==w['mu_sdk_actual_model_trial_recovery_design_handoff_ref'])
# Validate every input again, without traversing private paths inside public receipts.
for r in list(inputs.values()):read(r['path'],r)
check('input_drift_zero',True)
put('input-intake.json',{'refs':list(inputs.values()),'input_drift':0,'private_targets_opened':False})
put('evidence-checks.json',checks)
put('review.json',dict(schema='researchos.checkpoint-independent-review.v1',decision='PASS_CP349_CHECKPOINT_TRUTH_ONLY_BUSINESS_OPEN',actor_id='codex:/root/command_queue_impl',checkpoint_ref=pair['checkpoint_ref'],ownership_ref=pair['ownership_ref'],verified_checks=len(checks),unique_inputs=len(inputs),input_drift=0,old_failure_entries_preserved=742,added_failure_ordinals=list(range(745,750)),registered_failure_count=747,highest_observed_diagnostic_ordinal=749,trial_status='FAILED_EXECUTION_CLOSED',owned_jobs_closed=2,source_guard_entries_closed=86,Run_status='QUEUED',Task_status='RUNNING',dispatch_state='PREPARED',business_reconciliation='OPEN',provider_requests=None,recorded_model_effects=0,current_formal_acceptance=0,formal_required=42,historical_parent_registrations=6,historical_parent_total=22,qualification=False,C7_actual_started=False,once_consumed=True,clock_reset=False,automatic_retry=False,reviewer_new_failures=[],reviewer_sql_native_provider_calls=0,reviewer_Source_canonical_private_state_mutations=0,notes=['Accepts checkpoint fidelity only; not business closure or runtime qualification.','Business evidence is the pinned prior read-only observation; this review performed no fresh SQL.','Lifecycle evidence is historical original held-handle observations; no new OS probe.','Historical live_execution_grant_issued=true does not authorize another execution; current_live_execution_grant_active=false.','749 full functions.exec input gap remains explicit; no invented exits.','Public receipt metadata mentions private state; the private target was never opened or hashed.']))
print(json.dumps({'decision':'PASS_CP349_CHECKPOINT_TRUTH_ONLY_BUSINESS_OPEN','checks':len(checks),'unique_inputs':len(inputs),'input_drift':0,'review_ref':ref(O/'review.json')}))

