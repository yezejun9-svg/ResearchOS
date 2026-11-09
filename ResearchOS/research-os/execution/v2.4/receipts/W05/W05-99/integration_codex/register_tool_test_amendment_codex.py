from pathlib import Path
import copy,datetime,hashlib,json,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[6];BASE=ROOT/'execution/v2.4/receipts/W05/W05-99';HERE=BASE/'integration_codex';WT=ROOT/'.local/worktrees/codex-w0599-tools'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def create(p,v):
 with p.open('x',encoding='utf8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def replace(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
proposal=HERE/'tool_recovery_test_scope_proposal_codex.json';review=BASE/'architecture_review_codex/tool_recovery_test_scope_review.json'
assert sha(proposal)=='039c8498845ba84beee041bc4b3899aa35d5af1fe957c06c3c1bd1a1a3ae8aaf'
assert sha(review)=='c7d2db796054c76dcd94fbd3bd717979934b81a7c0f503aa8cb7041843af0f0b'
v=load(review);assert v['decision']=='APPROVE_EXACT_TEST_SCOPE_FOR_ROOT_REGISTRATION'
p=Path('internal/domain/runtime_sessions_windows_test.go');before='e4361827e0b3315a3a9ef26584200e728efcebb66b31e794550aa3e4592ca897';assert sha(ROOT/p)==sha(WT/p)==before
cp_path=ROOT/'execution/v2.4/checkpoint.json';path_path=ROOT/'execution/v2.4/path_ownership.json';state=ROOT/'execution/v2.4/step_state.json'
cp,paths=load(cp_path),load(path_path);old=copy.deepcopy(cp);state_bytes=state.read_bytes();assert cp['revision']==223 and paths['revision']==56 and len(cp['failure_counters'])==86
now=datetime.datetime.now(datetime.timezone.utc).isoformat();source=WT/'execution/v2.4/receipts/W05/W05-99/tool_executor_codex';dest=BASE/'tool_executor_codex';dest.mkdir(exist_ok=True)
# Retain only immutable completed raw runs and original format failure now;
# mutable runner/receipt will be imported with the later reviewed source commit.
for run in sorted((source/'runs').iterdir()):
 assert (run/'result.json').is_file()
 target=dest/'runs'/run.name
 if not target.exists():shutil.copytree(run,target)
for name in ('format_failure.json','format_failure_original_source.go.txt'):
 target=dest/name
 if not target.exists():shutil.copyfile(source/name,target)
 else:assert sha(target)==sha(source/name)
origins=[]
def failure(key,path,classification,detail):
 data=load(path);assert data.get('exit_code')==1
 input_hash=data.get('inputs_sha256',data.get('source_sha256'))
 origins.append({'origin_key':key,'attempts':1,'candidate_id':'W05-99-S1' if '/executor_codex/' in str(path).replace('\\','/') else 'W05-99-S3','input_hash':input_hash,'status':'RECORDED_WITH_CHANGED_INPUT_AWAITING_FINAL_REVIEW','classification':classification,'evidence':ref(path),'product_failure_count_delta':1 if classification=='PRODUCT_SOURCE_COMPILE_FAILURE' else 0,'detail':detail})
failure('W05-S1-SOURCE_CLIP_COMPILE',BASE/'executor_codex/runs/20261005T234603Z-e02be6d2f4/result.json','PRODUCT_SOURCE_COMPILE_FAILURE','Actual undefined clip compile failure retained. Final independently reviewed63-test S1 restores the helper inside authorized source.')
failure('W05-S1-FIXTURE_NULL_EVENT_ARRAY',BASE/'executor_codex/runs/20261005T234626Z-d2c01773b0/result.json','FIXTURE_INPUT_FAILURE_NOT_PRODUCT','Cancellation fixture supplied null events instead of schema array; real follower rejected it. Corrected actual empty array and exact reasons; final S1 independently reviewed.')
failure('W05-S3-SOURCE_COMPOSITE_LITERAL_FORMAT',dest/'format_failure.json','PRODUCT_SOURCE_FORMAT_FAILURE','Actual gofmt stopped on range composite literal syntax; original bytes retained, repaired with legal parenthesized literal before build.')
failure('W05-S3-SPARSE_LOCAL_IMPORTS',dest/'runs/20261006T000147Z-f7ce827c4a/result.json','CANDIDATE_SETUP_FAILURE_NOT_PRODUCT','Existing repo-local evaluation/ops imports absent from sparse checkout. Added existing directories, no go get/provider/lock/source change.')
failure('W05-S3-TEST_UNUSED_IMPORT_COMPILE',dest/'runs/20261006T000210Z-de9540c557/result.json','TEST_SOURCE_COMPILE_FAILURE','Actual unused path/filepath test import after SQL blob-reader correction. Removed unused import before new tests.')
multi=dest/'runs/20261006T000233Z-094fc222bd/result.json'
failure('W05-S3-FIXTURE_USAGE_BASELINE',multi,'FIXTURE_INPUT_FAILURE_NOT_PRODUCT','Fixture already has canonical qualification budget entry; initial hardcoded usage count1 was wrong. New assertions inspect each actual unknown entry and require one new ACTUAL entry, without relaxing money truth.')
failure('W05-S3-FIXTURE_MISSING_DURABLE_LOCATOR',multi,'FIXTURE_INPUT_FAILURE_NOT_PRODUCT','Lower-level journal fixture provided only callback fact and no durable journal locator/file; historical scan rejected it. Fixture now persists actual immutable fact at recorded dispatch locator.')
failure('W05-S3-FIXTURE_SSE_TERMINATOR_SHAPE',multi,'FIXTURE_INPUT_FAILURE_NOT_PRODUCT','Fixture combined content and finish in a shape that real SDK did not produce a report for; qualification helper panicked on empty artifacts. Restored actual two-chunk delta/finish loopback wire shape.')
failure('W05-S3-RECOVERY_TEST_OLD_EVENT_TOTAL',dest/'runs/20261006T000444Z-02df48b5b6/result.json','TEST_CONTRACT_AMENDMENT_REQUIRED','45 current tests passed, one old total2 assertion rejected legitimate third usage. Independent review authorizes only exact ledger-bound recovery-test amendment; old raw retained, no blind2to3 change.')
failure('W05-S3-FIXTURE_REPORT_RUN_BINDING',dest/'runs/20261006T000905Z-8d30d92779/result.json','FIXTURE_INPUT_FAILURE_NOT_PRODUCT','Native fixture r.run still referenced qualification. New diagnostic binds actual reported Task.active_run_id; next run 000945-b2b327b211 passes and records actual usage/ledger bytes.')
assert not {x['origin_key'] for x in origins}&{x.get('origin_key') for x in cp['failure_counters']};cp['failure_counters'].extend(origins)
scope=HERE/'tool_recovery_test_source_scope_codex.json'
create(scope,{'schema':'researchos.w05.root-test-scope-amendment.v1','status':'AUTHORIZED_EXACT_TEST_AMENDMENT','registered_at':now,'registered_by':'codex:/root','owner':'codex:/root','step_id':'W05-99','worktree':'.local/worktrees/codex-w0599-tools','exact_paths':[p.as_posix()],'existing_source_refs':[{'path':p.as_posix(),'sha256':before}],'proposal_ref':ref(proposal),'independent_scope_review_ref':ref(review),'allowed_test':'TestW14SessionProjectionRecoveryAfterReportCommit','formal_case_count_delta':0,'w04_revalidation_required_after_source_integration':True})
binding=paths['card_path_bindings']['W05-99']['subtasks']['durable_tool_projection'];assert p.as_posix() not in binding['paths'];binding['paths'].append(p.as_posix());binding.setdefault('scope_amendment_refs',[]).append(ref(scope))
paths.update(revision=57,updated_at=now,updated_by='codex:/root',amended_at=now,amended_by='codex:/root');replace(path_path,paths)
cp.update(updated_at=now,updated_by='codex:/root',note='S1 six CLI source paths independently reviewed and integrated; S2/S3 remain candidates. Ten actual construction failure origins retained, no resets. One old recovery-test amendment independently scoped. Main current3 W04 cases unchanged before domain integration.')
cp['work_in_progress'].update(status='CLI_S1_INTEGRATED_GOAL_AND_TOOL_CANDIDATES',next_action='Finish independently scoped recovery test; freeze tested tools candidate and independently review source. Finish Goal candidate, independently register S4, integrate reviewed source only, derive W04 drift honestly. W05 and fullLIVE remain unfinished.')
cp['evidence_index'].extend([scope.relative_to(ROOT).as_posix(),(HERE/'cli_slice_integrated_codex.json').relative_to(ROOT).as_posix()]);cp['integrity_events'].append({'at':now,'actor':'codex:/root','event':'W05_S1_INTEGRATED_AND_S3_TEST_SCOPE_AMENDED','evidence':ref(scope)});replace(cp_path,cp)
event=HERE/'checkpoint224_value_round_codex.json';create(event,{'schema':'researchos.value-round.v1','round_id':'W05-S1-integration-and-S3-test-amendment-20261006','delta':'FIXTURE','summary':'Reviewed S1 CLI source integrated, original construction failures retained, exact recovery-test scope amended; no fullLIVE/formal acceptance.','evidence_refs':[ref(scope),ref(HERE/'cli_slice_integrated_codex.json')]})
spec=ROOT/'.local/worktrees/v24-continuation/spec/v2.4';args=[sys.executable,'-B','-X','utf8',str(ROOT/'bootstrap/v24_checkpoint.py'),'--checkpoint',str(cp_path),'--state',str(state),'--plan',str(spec/'contracts/execution.plan.json'),'--delivery',str(spec/'contracts/delivery.contract.json'),'--expected-revision','223','--round-event',str(event),'--actor','codex:/root']
result=subprocess.run(args,cwd=ROOT,capture_output=True)
for name,raw in [('stdout.json',result.stdout),('stderr.txt',result.stderr)]:
 with (HERE/f'checkpoint224.{name}').open('xb') as f:f.write(raw)
assert result.returncode==0,result.stderr.decode('utf8','replace')
after=load(cp_path);assert after['revision']==224 and after['failure_counters'][:86]==old['failure_counters'] and len(after['failure_counters'])==96 and state.read_bytes()==state_bytes
assert after['value_checkpoint']['formal_gate']['formal_cases_accepted']==3
print(json.dumps({'status':'PASS_REGISTERED_EXACT_TEST_AMENDMENT','checkpoint':224,'paths_revision':57,'failure_origins':96,'formal_count':3}))
