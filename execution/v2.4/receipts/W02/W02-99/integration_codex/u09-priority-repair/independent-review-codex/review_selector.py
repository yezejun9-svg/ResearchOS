"""Independent, bounded constructor review. Never updates shared checkpoint/state."""
import ast,copy,datetime,hashlib,json,pathlib,subprocess,sys,types
R=pathlib.Path('D:/作品集/ResearchOS/research-os');O=pathlib.Path(__file__).resolve().parent;B=O.parent
F='9f7739f554d8f05cef0a37895671011fc08ab07c';SOURCE='bootstrap/v24_checkpoint.py'
SOURCE_SHA='319b4ad73e69577f70bd1775e4d2aed9f1d1af69c801fa4bcdf0e07508dc1d39'
SPEC=R/'.local/worktrees/v24-continuation/spec/v2.4';CP=R/'execution/v2.4/checkpoint.json';STATE=R/'execution/v2.4/step_state.json'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
digest=lambda b:hashlib.sha256(b).hexdigest()
def save(p,value):
 with p.open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2)
checks=[];case_outputs={}
def check(id,ok,detail=None):
 checks.append({'id':id,'ok':bool(ok),'detail':detail});assert ok,id
scope=read(B/'issue_scope_codex.json');handoff=read(B/'handoff_codex.json');worker=B/'regression-20261006-b';wm=read(worker/'manifest.json')
check('frozen-main-source',subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()==F and sha(R/SOURCE)==SOURCE_SHA)
check('frozen-handoff-and-latest-manifest',sha(B/'handoff_codex.json')=='c0e8c42ff6c3bf89906ed2a61eefdec5e2b4daea559b78fd986641cb54679c4e' and sha(worker/'manifest.json')=='19841361cbd69b1a6ef3e8366bf18032d1c04b81d435e0a8418fafd7aa1c7ec8')
check('worker-latest-source-and-raw',wm['source_sha256']==SOURCE_SHA and wm['test_source_sha256']==sha(B/'selector_tests_codex.py') and all(sha(worker/x['path'])==x['sha256'] for x in wm['artifacts']) and wm['tests_run']==12 and wm['failures']==wm['errors']==0 and 'Ran 12 tests' in (worker/'unittest.txt').read_text())
check('worker-protected-before-after-equal',read(worker/'protected_inputs_before.json')==read(worker/'protected_inputs_after.json') and len(read(worker/'protected_inputs_before.json'))==797)
historypins=[]
for item in scope['baseline_inputs']:
 p=R/item['path']
 if sha(p)==item['sha256']:historypins.append(dict(item,classification='UNCHANGED_BASELINE_ALSO_CURRENT'))
 else:
  raw=subprocess.check_output(['git','show',scope['source_head']+':'+item['path']],cwd=R)
  check('historical-baseline-'+item['path'],digest(raw)==item['sha256'])
  historypins.append(dict(item,classification='HISTORICAL_PRE_REGISTRATION_OR_PRE_REPAIR',historical_revision=scope['source_head'],current_sha256=sha(p)))
save(O/'historical_pin_classification.json',historypins)
watched=[R/SOURCE,CP,STATE,R/'execution/v2.4/commands.json',R/'execution/commands.json',R/'execution/v2.4/path_ownership.json',R/'execution/path_ownership.json',R/'execution/toolchains/locked.json',B/'issue_scope_codex.json']+sorted(p for p in SPEC.rglob('*') if p.is_file())
before={str(p):sha(p) for p in watched};save(O/'current_vector_before.json',before)
cp=types.ModuleType('independent_checkpoint');cp.__file__=str(R/SOURCE);exec(compile((R/SOURCE).read_bytes(),cp.__file__,'exec'),cp.__dict__)
baseline_source=subprocess.check_output(['git','show',scope['source_head']+':'+SOURCE],cwd=R)
old=types.ModuleType('baseline_checkpoint');old.__file__=str(R/SOURCE);exec(compile(baseline_source,old.__file__,'exec'),old.__dict__)
oldast=ast.parse(baseline_source);newast=ast.parse((R/SOURCE).read_bytes())
oldfunctions={x.name:ast.dump(x,include_attributes=False) for x in oldast.body if isinstance(x,ast.FunctionDef)}
newfunctions={x.name:ast.dump(x,include_attributes=False) for x in newast.body if isinstance(x,ast.FunctionDef)}
allowed={'prioritized_step','next_packet','update_value'}
check('unchanged-direct-counting-threshold-write-and-validation-functions',all(newfunctions[k]==v for k,v in oldfunctions.items() if k not in allowed) and set(newfunctions)-set(oldfunctions)=={'flow_priority'})
def node(id,deps=(),priority=100,phase='PARENT_FINAL_GATE'):
 return {'id':id,'parent_task':id.split('-')[0],'phase':phase,'dependencies':list(deps),'priority':priority}
def context(rows,caps):
 p={x['id']:x for x in rows};return p,{k:'NOT_STARTED' for k in p},{'capabilities':[{'id':c,'task_id':t} for c,t in caps]}
paused={'value_checkpoint':{'pause_nonblocking_expansion':True}}
# A diamond counts the shared ancestor once; a shorter blocked branch must not
# displace the complete executable branch. An unrelated ready card is ignored.
p,s,d=context([node('W70-99',['W71-99','W72-99']),node('W71-99',['W73-99']),node('W72-99',['W73-99']),node('W73-99',priority=50),node('W80-99',['W81-99','W82-99']),node('W81-99',priority=1),node('W82-99'),node('W90-01',priority=0,phase='IMPLEMENTATION_SLICE')],[('U02','W70'),('U06','W80')])
s['W82-99']='BLOCKED';r=cp.flow_priority(s,p,d);case_outputs['diamond_vs_shorter_blocked']=r
check('diamond-unique-complete-count-free-before-blocked',r['candidates'][0]['capability_id']=='U02' and r['candidates'][0]['remaining_required_cards']==4 and set(r['candidates'][0]['unaccepted_dependency_closure'])=={'W70-99','W71-99','W72-99','W73-99'} and r['candidates'][0]['next_step_id']=='W73-99' and r['candidates'][1]['remaining_required_cards']==3)
s['W82-99']='ACCEPTED';r=cp.flow_priority(s,p,d);case_outputs['shorter_now_unblocked']=r
check('complete-unaccepted-length-reranks-without-unrelated-default',r['candidates'][0]['capability_id']=='U06' and r['candidates'][0]['remaining_required_cards']==2 and cp.prioritized_step(paused,s,p,d,'W90-01')=='W81-99')
# Both flows now have the same length and ready priority. ID wins before the
# capability ID, and a same-owner capability tie resolves by capability ID.
p,s,d=context([node('W70-99',['W74-99']),node('W74-99',priority=8),node('W80-99',['W73-99']),node('W73-99',priority=8)],[('U02','W70'),('U07','W80'),('U06','W80')])
r=cp.flow_priority(s,p,d);reverse=cp.flow_priority(s,dict(reversed(list(p.items()))),{'capabilities':list(reversed(d['capabilities']))});case_outputs['stable_multilevel_tie']=r
check('equal-length-priority-id-capability-stable-tie',r==reverse and [x['capability_id'] for x in r['candidates']]==['U06','U07','U02'])
p['W70-01']=node('W70-01',priority=999,phase='IMPLEMENTATION_SLICE');s['W70-01']='IN_PROGRESS'
r=cp.flow_priority(s,p,d);case_outputs['direct_slice_preempts_parent_frontier']=r
check('existing-direct-selection-byte-equivalent-structure',r['candidates']==old.ready_flows(s,p,d) and r['candidates'][0]['next_step_id']=='W70-01' and r['required_parent_closures']==[])
check('pause-disabled-keeps-arbitrary-frozen-default',cp.prioritized_step({'value_checkpoint':{'pause_nonblocking_expansion':False}},s,p,d,'W90-01')=='W90-01')
# A non-runnable shared ancestor leaves no eligible frontier; a child whose
# dependency is not accepted is not ready merely because it is IN_PROGRESS.
p,s,d=context([node('W70-99',['W71-99']),node('W71-99',['W72-99']),node('W72-99')],[('U02','W70')]);s['W71-99']='IN_PROGRESS'
for bad in ['BLOCKED','FAILED','CANCELLED','EXECUTION_REPORTED','UNKNOWN_REVIEW_STATUS']:
 s['W72-99']=bad;r=cp.flow_priority(s,p,d);case_outputs['no_frontier_'+bad]=r
 check('reject-status-and-unaccepted-dependency-'+bad,not r['candidates'] and r['blocking_reason']=='NO_ELIGIBLE_FRONTIER_IN_REQUIRED_PARENT_CLOSURES' and cp.prioritized_step(paused,s,p,d,'W90-01') is None)
p,s,d=context([node('W12-99')],[('U09','W12')]);r=cp.flow_priority(s,p,d);case_outputs['exclude_U09']=r
check('U09-never-becomes-user-flow-frontier',not r['candidates'] and not r['required_parent_closures'])
for label,rows,needle in [('cycle',[node('W70-99',['W71-99']),node('W71-99',['W70-99'])],'dependency cycle'),('unknown',[node('W70-99',['W404-99'])],'unknown dependency step')]:
 p,s,d=context(rows,[('U02','W70')])
 try:cp.flow_priority(s,p,d);reason='ACCEPT'
 except cp.CheckpointError as error:reason=str(error)
 check('fail-closed-'+label,needle in reason,reason)
# Apply two synthetic infrastructure events only in memory. The first reaches
# the real CP205 two-round threshold; the second adds a parent acceptance only
# and must preserve that history/streak while refreshing the pending frontier.
current=read(CP);state=read(STATE);plan=read(SPEC/'contracts/execution.plan.json');delivery=read(SPEC/'contracts/delivery.contract.json')
accepted,statuses,plans=cp.accepted_and_status(state,plan);snapshot=copy.deepcopy(current)
check('actual-input-is-CP205-paused',current['revision']==205 and current['value_checkpoint']['pause_nonblocking_expansion'] is True and len(current['value_checkpoint']['pending_rounds'])==1)
def event(n):return {'round_id':'INDEPENDENT_SYNTHETIC_ONLY_'+str(n),'delta':'INFRASTRUCTURE','summary':'in-memory reviewer lifecycle only','evidence_refs':[],'event_ref':{'path':'SYNTHETIC_NOT_SAVED','sha256':'0'*64}}
first=cp.update_value(current,accepted,statuses,plans,delivery,baseline=False,round_record=event(1),force=False,reason=None,now='SYNTHETIC')
check('infrastructure-threshold-retains-history-and-user-observations',first['history'][:-1]==current['value_checkpoint']['history'] and first['capabilities_observed']==current['value_checkpoint']['capabilities_observed'] and first['documentation_only_checkpoints']==current['value_checkpoint']['documentation_only_checkpoints']+1 and first['pause_nonblocking_expansion'] is True and first['history'][-1]['observed_user_capability'] is False)
altered_state=copy.deepcopy(state)
for row in altered_state['steps']:
 if row['id']=='W03-99':row['status']='ACCEPTED'
if not any(row['id']=='W03-99' for row in altered_state['steps']):
 altered_state['steps'].append({'id':'W03-99','status':'ACCEPTED'})
accepted2,statuses2,plans2=cp.accepted_and_status(altered_state,plan)
check('parent-acceptance-not-implementation-count',accepted2==accepted and len(cp.gates(statuses2,plans2)['accepted_parent_step_ids'])==len(cp.gates(statuses,plans)['accepted_parent_step_ids'])+1)
intermediate={**current,'value_checkpoint':first}
second=cp.update_value(intermediate,accepted2,statuses2,plans2,delivery,baseline=False,round_record=event(2),force=False,reason=None,now='SYNTHETIC')
check('pending-update-preserves-history-streak-pause-and-refreshes',second['status']=='PENDING_THRESHOLD' and second['history']==first['history'] and second['documentation_only_checkpoints']==first['documentation_only_checkpoints'] and second['pause_nonblocking_expansion'] is True and second['capabilities_observed']==first['capabilities_observed'] and second['recommended_flow']==cp.flow_priority(statuses2,plans2,delivery)['candidates'][0] and second['recommended_flow']['next_step_id']=='W04-99' and second['recommended_flow']['remaining_required_cards']==2)
check('formal22-42-and-memory-input-unchanged',second['formal_gate']['required_parent_tasks']==22 and second['formal_gate']['required_formal_cases']==42 and second['formal_gate']['formal_cases_accepted']=='NOT_DERIVABLE_FROM_STEP_STATE' and current==snapshot)
case_outputs['synthetic_update_lifecycle']={'starting_history':len(current['value_checkpoint']['history']),'after_first_history':len(first['history']),'after_second_history':len(second['history']),'implementation_count_before':len(accepted),'implementation_count_after_parent':len(accepted2),'pause':second['pause_nonblocking_expansion'],'pending_status':second['status'],'recommendation':second['recommended_flow'],'synthetic_only':True,'shared_files_written':False}
save(O/'in_memory_cases.json',case_outputs)
# The only new real selector invocation. It internally calls frozen task_packet
# next/show and remains a read-only construction query, not a product dispatch.
argv=[sys.executable,'-B','-X','utf8',str(R/SOURCE),'--checkpoint',str(CP),'--state',str(STATE),'--plan',str(SPEC/'contracts/execution.plan.json'),'--delivery',str(SPEC/'contracts/delivery.contract.json'),'--next-packet']
started=datetime.datetime.now(datetime.timezone.utc).isoformat();run=subprocess.run(argv,cwd=R,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=90,shell=False)
(O/'actual_next.stdout.json').write_bytes(run.stdout);(O/'actual_next.stderr.txt').write_bytes(run.stderr)
save(O/'actual_next.command.json',{'argv':argv,'cwd':str(R),'started_at':started,'exit_code':run.returncode,'stdout_sha256':sha(O/'actual_next.stdout.json'),'stderr_sha256':sha(O/'actual_next.stderr.txt'),'scope':'READ_ONLY_CONSTRUCTION_QUERY_NOT_PRODUCT_DISPATCH'})
actual=cp.strict_json(run.stdout);pol=actual['value_checkpoint_policy'];pick=pol['selection']['candidates'][0]
check('actual-next-frozen-show-eligible-CP205-U02-W03-3',run.returncode==0 and not run.stderr and actual['state_source']=='VALIDATED_FILE' and actual['eligible'] is True and actual['step']['id']=='W03-99' and pol['checkpoint_revision']==205 and pol['priority_consumed'] is True and pick['capability_id']=='U02' and pick['target_parent']=='W05-99' and pick['next_step_id']=='W03-99' and pick['unaccepted_dependency_closure']==['W03-99','W04-99','W05-99'] and pick['remaining_required_cards']==3 and pick['scope']=='PREREQUISITE_FOR_USER_FLOW')
check('actual-selection-equals-shared-helper',pol['selection']==cp.flow_priority(statuses,plans,delivery) and cp.prioritized_step(current,statuses,plans,delivery,pol['default_step_id'])=='W03-99')
for folder in ['no-frontier','all-accepted']:
 command=read(worker/folder/'invocation.json');out=read(worker/folder/'stdout.txt')
 check('archived-cli-code3-'+folder,command['exit_code']==3 and out['step'] is None and out['status']=='NO_READY_USER_FLOW' and out['value_checkpoint_policy']['selected_step_id'] is None)
after={str(p):sha(p) for p in watched};save(O/'current_vector_after.json',after)
check('current-source-state-CP-commands-path-entire-frozen-spec-unchanged',before==after,{'file_count':len(before),'revision_after':read(CP)['revision']})
save(O/'assertion_results.json',checks)
artifact_paths=[O/'review_selector.py',O/'historical_pin_classification.json',O/'current_vector_before.json',O/'current_vector_after.json',O/'in_memory_cases.json',O/'actual_next.command.json',O/'actual_next.stdout.json',O/'actual_next.stderr.txt',O/'assertion_results.json',B/'issue_scope_codex.json',B/'handoff_codex.json',worker/'manifest.json',worker/'unittest.txt']
manifest={'scope':'INDEPENDENT_CONSTRUCTION_SELECTOR_REVIEW','source_revision':F,'source_sha256':SOURCE_SHA,'review_script_sha256':sha(O/'review_selector.py'),'assertion_count':len(checks),'artifacts':[{'path':str(p),'sha256':sha(p)} for p in artifact_paths]}
save(O/'manifest.json',manifest)
review={'schema':'researchos.independent-construction-repair-review.v1','origin_problem_id':'U09-REQUIRED-PARENT-FRONTIER-001','reviewer':'codex:/root/w1702_review','actual_model':'gpt-6-astra','reasoning_effort':'high','independent_of_executor':True,'source_revision':F,'executor_revision':'2759e0244f79f922684bd70086bb743ca748ae4e','source_path':SOURCE,'source_sha256':SOURCE_SHA,'checkpoint_revision_observed':205,'verdict':'PASS_IN_SCOPE','recommendation':'ACCEPT_REQUIRED_PARENT_FRONTIER_TOOLING_REPAIR','authority':'CONSTRUCTION_SELECTOR_ONLY_NOT_DISPATCH_OR_PARENT_OR_FORMAL_ACCEPTANCE','assertion_count':len(checks),'passed_assertions':sum(x['ok'] for x in checks),'failed_assertions':sum(not x['ok'] for x in checks),'assertion_results':{'path':str(O/'assertion_results.json'),'sha256':sha(O/'assertion_results.json')},'evidence_manifest':{'path':str(O/'manifest.json'),'sha256':sha(O/'manifest.json')},'current_input_vector':{'path':str(O/'current_vector_before.json'),'sha256':sha(O/'current_vector_before.json'),'after_sha256':sha(O/'current_vector_after.json'),'file_count':len(before),'unchanged':before==after},'historical_baseline_classification':{'path':str(O/'historical_pin_classification.json'),'sha256':sha(O/'historical_pin_classification.json'),'rule':'CP204/pre-repair helper pins verified at their historical revision; not falsely compared with CP205/repaired current inputs.'},'actual_readonly_result':{'new_calls':1,'exit_code':run.returncode,'step_id':actual['step']['id'],'capability_id':pick['capability_id'],'scope':pick['scope'],'complete_remaining_required_cards':pick['remaining_required_cards'],'validated_file':actual['state_source'],'eligible':actual['eligible'],'stdout_sha256':sha(O/'actual_next.stdout.json')},'implementation_assessment':['Existing direct READY implementation slice ranking is preserved exactly and precedes prerequisite fallback.','Only U01-U08 unfinished owner-parent complete dependency closures enter fallback; shared ancestors deduplicate, cross-parent dependencies remain and own parent counts.','Blocker-free closures precede blocked closures; remaining count then frozen next-card priority/ID and capability ID provide stable selection. Blocked closures may expose an independent legal READY frontier when no blocker-free candidate is available; nonrunnable cards themselves are never selected.','next_packet always checks the selected priority card with frozen show eligibility; next/update/prioritized_step share flow_priority. No candidate retains code3 and explicit reason without arbitrary default.','Parent acceptance does not inflate implementation-card count; infrastructure round updates retain history/streak/observations/pause and refresh pending recommendations. No USER_FLOW observation is inferred.','Unknown dependencies and cycles fail closed within examined closures. Frozen plan remains authoritative; this is not validation of arbitrary external plan documents.'],'open_findings':[],'formal_cases_accepted':[],'formal_case_count_delta':0,'parent_cards_accepted':[],'state_counter_registry_writes_by_reviewer':0,'product_Go_GUI_provider_service_private_label_operations':0,'limitations':['Worker regression-b 12 results were checked as archived evidence, not rerun; earlier regression-a retained as history.','Synthetic DAG/update cases ran only in memory; no synthetic state or acceptance replaced current shared files.','One actual CP205 read-only selection verifies eligibility and routing only. W03 execution, independent parent acceptance and 42-case product acceptance remain separate.','No old W13 workspace/NVDA/resource audit or service operation performed.'],'reviewed_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
save(B/'independent_review_codex.json',review)
print(json.dumps({'verdict':review['verdict'],'assertions':len(checks),'protected_file_count':len(before),'actual_readonly_calls':1,'next':'U02/W03-99/3','review_sha256':sha(B/'independent_review_codex.json'),'manifest_sha256':sha(O/'manifest.json')}))
