import copy,datetime,hashlib,json,os,pathlib,subprocess
R=pathlib.Path(r'D:/作品集/ResearchOS/research-os');W=R/'.local/worktrees/codex-w0599-model-stream';L=R/'.local/worktrees/codex-w0599-cli-read-interrupt';D=pathlib.Path(__file__).parent;BASE='execution/v2.4/receipts/W05/W05-99/'
CP=R/'execution/v2.4/checkpoint.json';OW=R/'execution/v2.4/path_ownership.json';ST=R/'execution/v2.4/step_state.json';CM=R/'execution/v2.4/commands.json'
def enc(x):return (json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode('utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p,expected=None):
 p=pathlib.Path(p);h=sha(p)
 if expected:assert h==expected,(str(p),h,expected)
 return {'path':p.relative_to(R).as_posix(),'sha256':h}
def go_copy(rel,expected=None):
 p=W/rel
 if expected:assert sha(p)==expected
 target=D/'go-origin-originals'/pathlib.Path(rel).relative_to('execution/v2.4/receipts/W05/W05-99/model_stream_executor_codex');target.parent.mkdir(parents=True,exist_ok=True)
 if target.exists():assert target.read_bytes()==p.read_bytes()
 else:target.write_bytes(p.read_bytes())
 return ref(target)
before={p:p.read_bytes() for p in [CP,OW,ST,CM]};cp=json.loads(before[CP]);ow=json.loads(before[OW]);assert cp['revision']==266 and ow['revision']==94 and len(cp['failure_counters'])==174
assert hashlib.sha256(before[ST]).hexdigest()=='fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149'
assert hashlib.sha256(before[CM]).hexdigest()=='b357f60a9463b1a7504487bd8debf2b55f87f35938a26fe68a495aa834794129'
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R).decode().strip();assert head=='4ba293847072069cd99154e5054f6ef4ae2b92e1'
for p,data in before.items():
 t=D/(p.stem+'.original.json')
 if t.exists():assert t.read_bytes()==data
 else:t.write_bytes(data)
reviewref=ref(R/(BASE+'cli_read_interrupt_cause_scope_review_codex/00e37c35a102474f99e1561404ade9d8/scope_review.json'),'8e02de213e0fae9942f2ec34f8efed0630c89ab2044d9e5c6a00ba5969390544');review=json.loads((R/reviewref['path']).read_bytes());assert review['decision']=='SOURCE_SCOPE_READY_EXACT4_WITH_MANDATORY_GUARDS'
proposalref=ref(R/(BASE+'cli_read_interrupt_executor_codex/cause-amendment-r266/proposal.json'),'e41f9599f723eb65851860e0fa7365f8b7ed90d5bfab99b1ee0162c69b86c188');proposal=json.loads((R/proposalref['path']).read_bytes())
now=datetime.datetime.now(datetime.timezone.utc).isoformat();subs=ow['card_path_bindings']['W05-99']['subtasks'];binding=subs['cli_read_interruption'];oldbinding=copy.deepcopy(binding)
paths=proposal['exact_paths'];assert binding['paths']==paths[:3] and len(paths)==4;assert sha(R/paths[-1])==sha(L/paths[-1])=='072afeb88f1a2f028df1c99b55735b3c583c729e86b2a53b9e60e889e6a2c304'
transfers=[]
for name,b in subs.items():
 if name!='cli_read_interruption' and paths[-1] in b.get('paths',[]):transfers.append({'subtask':name,'owner':b.get('owner'),'state':b.get('state'),'paths':[paths[-1]]})
assert {x['subtask'] for x in transfers}=={'cli_goal_follower','cli_http_classification'}
scope=dict(schema='researchos.root.cli-read-interrupt-causal-exact4-scope.v1',actor='codex:/root',registered_at=now,owner='codex:/root',verifier='codex:/root/w05_merge_review',independent_scope_reviewer='codex:/root/sources_parent_impl',model='gpt-6-astra',reasoning_effort='high',base_head=head,worktree=str(L),exact_paths=paths,source_before=proposal['source_before'],prior_exact3_scope_ref=binding['scope_ref'],proposal_ref=proposalref,independent_scope_review_ref=reviewref,adopted_mandatory_conditions=review,transferred_historical_bindings=transfers,protected='Only private actual I/O cancellation cause and status finalization; original 3tuple/active callers/L01 non2xx before body/strict identities/bounds/continuation Background8s/original old tests preserved. No SDK/provider/shared contract edits.',composition_gate='No SOURCE_READY/MAIN until fresh exact4 freeze + independent combined current source/CLI proof; prior209/39050 isolated test remains historical, not repaired proof.',formal_increment=0)
(D/'scope_registration.json').write_bytes(enc(scope));scoperef=ref(D/'scope_registration.json')
for x in transfers:subs[x['subtask']].setdefault('historical_integrated_source_path_transfers',[]).append(dict(paths=x['paths'],new_owner='codex:/root',new_subtask='W05-99/cli_read_interruption',scope_ref=scoperef,old_evidence_and_other_paths_preserved=True,transferred_at=now))
binding.setdefault('historical_scope_revisions',[]).append(oldbinding);binding.update(paths=paths,state='IN_PROGRESS_EXACT4_CAUSAL_REPAIR_SOURCE_UNACCEPTED',scope_ref=scoperef,independent_cause_scope_review_ref=reviewref)
new=[]
def add(key,evidence,detail,status='ACTUAL_FAILURE_PRESERVED',attempts=1):new.append(dict(origin_key='W05-99/'+key,attempts=attempts,retries_used=0,status=status,evidence_ref=evidence,detail=detail,counter_reset=False,formal_increment=0))
obsref=ref(R/(BASE+'integration_codex/continuation-observations-r266/root-observations.json'),'fc875852ee0a1ae28c323604a3ab7b477f6efac29e2cc9544461d78dfc58e7cd')
for item in json.loads((R/obsref['path']).read_bytes())['observations']:add('root/'+item['id'],obsref,item,'ACTUAL_TOOL_FAILURE_OR_QUERY_ERROR_PRESERVED')
l02=R/(BASE+'cli_read_interrupt_executor_codex/implementation-20261006-r266')
for name,detail in [('focused-7276de159b3944c7ad81c438c6c47564','Actualexit1/18PASS/5FAIL: initial fixture config used2space JSON vs original1space product serialization; corrected fixture only, original stdout not rewritten.'),('full-0a7346f5adf5428989a7b3d9379ca207','Actualexit1/206PASS/3FAIL: original harness omitted explicit pinned Node/bundle environment required by existing three actualSDK fixture tests. Separate run-v2/full209 and closure39050 current stable/209PASS0skip prove corrected inputs; no skip or old assertions changed.')]:
 inv=json.loads((l02/name/'invocation.json').read_bytes());assert inv['actual_exit']==1;add('cli-read-interruption/'+name,ref(l02/name/'invocation.json'),{'description':detail,'stdout':ref(l02/name/'stdout.raw'),'stderr':ref(l02/name/'stderr.raw')})
pre=R/(BASE+'cli_read_interrupt_source_precheck_codex/fbc5e37c-b117-4717-b249-0e9e44309775/failure_origins.json');pr=json.loads(pre.read_bytes())
for x in pr['origins']:add('cli-read-precheck/'+x['id'],ref(pre),x,'INDEPENDENT_ACTUAL_RED_SCOPE_AMENDMENT_ADOPTED')
add('cli-read-precheck/readonly-locator',ref(pre),pr['tooling_read_error'],'REVIEW_READ_LOCATOR_ERROR_PRESERVED')
go_ns='execution/v2.4/receipts/W05/W05-99/model_stream_executor_codex/'
repair=go_ns+'quarantine-repair-d0b997f135f24c748c6e99e98a5e7f01/'
f=json.loads((W/(repair+'failure_origins.json')).read_bytes());fref=go_copy(repair+'failure_origins.json')
for x in f['new_actual_failures']:
 inv=x['invocation_ref'];out=x['stdout_ref'];copied=go_copy(inv['path'],inv['sha256']);stdout=go_copy(out['path'],out['sha256']);add('model-stream-repair/'+pathlib.Path(x['directory']).name,copied,{**x,'original_failure_file_ref':fref,'archived_stdout_ref':stdout})
add('model-stream-repair/assembly-counter',go_copy(repair+'finalize-failure.json'),f['receipt_assembly_failure'],'ACTUAL_ASSEMBLY_ERROR_NO_NEW_PRODUCT_FAILURE')
add('model-stream-repair/windows-stage-argv206',go_copy(repair+'stage-command-failure.json'),json.loads((W/(repair+'stage-command-failure.json')).read_bytes()),'ACTUAL_CREATEPROCESS_FAILURE_NO_GIT_INDEX_MUTATION')
signed=go_ns+'signed-zero-repair-437e95d3f0ef47b486f0c29594d3f6d2/';s=json.loads((W/(signed+'failure_origins.json')).read_bytes());sref=go_copy(signed+'failure_origins.json')
add('model-stream-signed-zero/owner-red',go_copy(s['new_expected_pre_fix_red']['path'],s['new_expected_pre_fix_red']['sha256']),{'actual_exit':1,'same_independent_red_is_not_this_run':True,'failure_origins_ref':sref},'ACTUAL_PRE_FIX_RED_PRESERVED_GREEN_SEPARATE')
add('model-stream-signed-zero/readonly-parser',sref,s['diagnostic_read_failure'],'ACTUAL_READ_PARSER_ERROR_PRESERVED')
add('model-stream-signed-zero/broad-raw-whitespace-check',go_copy(signed+'commit_check_failure.json'),json.loads((W/(signed+'commit_check_failure.json')).read_bytes()),'ACTUAL_GIT_CHECK_EXIT2_RAW_BYTES_PRESERVED_SOURCE_CHECK0')
for name in ['broad-check.stdout.gz','broad-check.stderr.gz']:go_copy(signed+name)
sr=R/(BASE+'streaming_repaired_source_review_codex/5455e415-03a4-466e-9cd1-0b0b5e691d87/failure_origins.json');v=json.loads(sr.read_bytes())
for x in v['entries']:add('model-stream-independent/'+x['origin_id'],ref(sr),x,'INDEPENDENT_ACTUAL_PRODUCT_OR_REVIEW_FAILURE_PRESERVED')
live=R/(BASE+'provider_live_plan_review_codex/9c160a80-7639-46fe-af30-44bc1bb8bffa/failure_origins.json');v=json.loads(live.read_bytes())
add('provider-live-plan/B01-evidence-refusal',ref(live),v['preexecution_refusal'],'PREEXECUTION_EVIDENCE_REFUSAL_NOT_PAID_ATTEMPT')
add('provider-live-plan/readonly-locator',ref(live),v['readonly_locator_errors'],'REVIEW_READ_LOCATOR_ERROR_PRESERVED')
assert not set(x['origin_key'] for x in new).intersection(x['origin_key'] for x in cp['failure_counters']);old=copy.deepcopy(cp['failure_counters']);cp['failure_counters'].extend(new);assert cp['failure_counters'][:174]==old
candidate=go_copy(signed+'handoff.json','8f45bf32b2687c9fadc71fccfc84ce10e1c89dd3a4c7935ed4120eea661c9629');subs['real_model_streaming'].update(state='CANDIDATE_SIGNED_ZERO_REPAIRED_INDEPENDENT_REVIEW_PENDING',repair_candidate_commit='c571781e9703bc7a96fa63629e0cc3bee7f3deec',repair_candidate_handoff_ref=candidate)
cp.update(revision=267,expected_previous_revision=266,head=head,updated_at=now,updated_by='codex:/root');ow.update(revision=95,amended_at=now,amended_by='codex:/root')
cp['next_command']='Implement registered L02 exact4 actual-I/O cause + synchronous ordering controls; await independent c571 T08 source review then exact source integrations and provider9 freshscope. LIVE only blockedB01 genuine upper bound, preserve strict policy. No formal increment or failure reset.'
cp['note']='L02 isolated209/39050 source+compiled inputs stable but independent1048577-byte terminal oversize counterexample is actualNEEDS_FIX; exact4 cause amendment independently accepted and old L01 lease narrowly transferred. T08 c571286core194CLI/39051 frozen candidate awaits independent review; SDK image absence is recorded, no unowned deletion restoration. LIVE B01 factual upper bound not established from public gateway source, only that branch blocked. All174 prior origins retained and new originals incrementally imported; old W14UNKNOWN/401 untouched.'
cp['work_in_progress'].update(status='L02_CAUSAL_EXACT4_REGISTERED_T08_SIGNED_ZERO_REVIEW_PENDING_LIVE_B01_ONLY_BLOCKED',main_source_head=head,next_action=cp['next_command'],cli_read_interruption_scope_ref=scoperef)
cp['integrity_events'].append(dict(at=now,actor='codex:/root',event='L02_CAUSAL_EXACT4_SCOPED_AND_T08_SIGNED_ZERO_FAILURES_PRESERVED',scope_ref=scoperef,failure_origins=[174,len(cp['failure_counters'])],formal_increment=0))
for worker in cp['workers']:
 if worker.get('slice_id')=='CLI_READ_INTERRUPTION':worker.update(state=binding['state'],scope_ref=scoperef)
for rr in [scoperef,reviewref,candidate,ref(sr),ref(live)]:
 if rr['path'] not in cp['evidence_index']:cp['evidence_index'].append(rr['path'])
record=dict(schema='researchos.root.resume-checkpoint.v1',actor='codex:/root',at=now,checkpoint=[266,267],ownership=[94,95],failure_origins=[174,len(cp['failure_counters'])],scope_ref=scoperef,candidate_handoff_ref=candidate,state_registry_unchanged=True,main_product_source_unchanged=True,formal_increment=0)
(D/'record.json').write_bytes(enc(record));(D/'new_failure_origins.json').write_bytes(enc(new))
for p,data in before.items():assert p.read_bytes()==data,('FOREIGN_WRITE',str(p))
for p,obj in [(CP,cp),(OW,ow)]:
 tmp=p.with_name(p.name+'.root267.tmp');tmp.write_bytes(enc(obj));assert p.read_bytes()==before[p];os.replace(tmp,p)
assert ST.read_bytes()==before[ST] and CM.read_bytes()==before[CM]
print(json.dumps({'checkpoint':267,'ownership':95,'failure_origins':len(cp['failure_counters']),'scope_ref':scoperef,'record_ref':ref(D/'record.json'),'formal_increment':0},ensure_ascii=False))