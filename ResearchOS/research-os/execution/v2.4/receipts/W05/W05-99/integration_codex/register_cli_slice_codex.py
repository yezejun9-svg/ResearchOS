"""Register the independently reviewed six-file current CLI implementation slice."""
from pathlib import Path
import copy, datetime as dt, hashlib, json, subprocess, sys
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[5]; V24=ROOT/'execution/v2.4'
WORKTREE=ROOT/'.local/worktrees/codex-w0599'; SOURCE=WORKTREE/'execution/v2.4/receipts/W05/W05-99/executor_codex'
SPEC=ROOT/'.local/worktrees/v24-continuation/spec/v2.4'
def load(p): return json.loads(p.read_bytes())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p): return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(p,v):
    with p.open('x',encoding='utf8',newline='\n') as stream: json.dump(v,stream,ensure_ascii=False,indent=2); stream.write('\n')
def replace(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
cp_path,path_path,state_path=(V24/n for n in ['checkpoint.json','path_ownership.json','step_state.json'])
cp,paths=load(cp_path),load(path_path); old_cp=copy.deepcopy(cp); state_raw=state_path.read_bytes()
assert cp['revision']==220 and paths['revision']==53 and len(cp['failure_counters'])==84
assert cp['current_step_id']=='W05-99'
expected={'source_proposal.md':'c1d7394888b62a568985ea9e2eb431e0b1e57f605d9279be7551b69883099ee3',
    'source_proposal.json':'801348f44782746ccfe044ae4ffb2e177184f4e68160d4fa7b12f728d2b01988',
    'source_slice1.json':'b054f6a1d5f69df613b6307d836805cecf02f15709d00cb0d0131b238453cf66'}
for name,digest in expected.items():
    assert sha(SOURCE/name)==digest,name
    with (HERE/name).open('xb') as stream: stream.write((SOURCE/name).read_bytes())
proposal=load(HERE/'source_slice1.json')
assert proposal['candidate_head']=='f68c83c2918ae25d9811e4e9f703f1a158e143d2'
new_paths=[r['path'] for r in proposal['existing_files']]+proposal['new_files']
assert new_paths==['apps/cli/cli_verbs.go','apps/cli/cli_v2.go','apps/cli/cli_contract.go','apps/cli/cli_sessions_test.go','apps/cli/cli_stream.go','apps/cli/cli_stream_test.go']
for row in proposal['existing_files']:
    assert sha(ROOT/row['path'])==sha(WORKTREE/row['path'])==row['sha256'],row
for name in proposal['new_files']: assert not (ROOT/name).exists() and not (WORKTREE/name).exists()
context=load(V24/'receipts/W04/W04-99/integration_codex/current_context_codex.json')
covered={r['path'] for group in ('spec_files','source_files','input_files','lock_files','tool_files') for r in context['version_vector'][group]}
assert not set(new_paths)&covered
now=dt.datetime.now(dt.timezone.utc).isoformat()
approval=HERE/'observed_cli_scope_approval_codex.json'
save(approval,{'schema':'researchos.root-observed-architecture-scope-approval.v1','observer':'codex:/root',
    'observed_at':now,'reviewer':'codex:/root/w1702_review','channel':'independent_agent_message',
    'actual_delivered_content':'第一slice明确通过架构scope审查：仅6文件 apps/cli/cli_verbs.go、cli_v2.go、cli_contract.go、cli_sessions_test.go、新cli_stream.go、新cli_stream_test.go。已完整读取primary proposal SHA c1d7394888b62a568985ea9e2eb431e0b1e57f605d9279be7551b69883099ee3 + manifest SHA801348f44782746ccfe044ae4ffb2e177184f4e68160d4fa7b12f728d2b01988，21源码/10冻结hash/6新文件absent全符合。建议root即登记该6路径开展CLI实施，无需等待Goal/工具事件/LIVE。限定实际修改：本轮绑定/分页/结清退出/边读stdin与slash/Ctrl+C向当前host run取消；goal nullable-CAS逻辑第一slice只可做envelope兼容，不冒称缺失host handler已补。pending未有Run的取消可明确非成功CANCEL_UNCONFIRMED并保留身份，A04 pending_queue_cancel保持未完成。完整W05不接受、本次数量delta0。正在写路径级签发意见到我的receipt目录。',
    'initial_architecture_ref':ref(V24/'receipts/W05/W05-99/architecture_review_codex/initial_architecture_review.md'),
    'exact_paths':new_paths,'formal_acceptance':False})
binding=paths['card_path_bindings']['W05-99']; assert binding['owner']=='codex:/root/w1102_impl'
binding['paths'].extend(new_paths)
binding['source_slice1']={'id':proposal['slice_id'],'source_proposal':ref(HERE/'source_slice1.json'),
    'independent_scope_approval':ref(approval),'rationale':'Actual admitted turn event pagination, authoritative settled exits, interactive dispatch and host cancellation. No separate runtime/writer path.',
    'deferred_same_final_goal':proposal['deferred_same_final_W05_goal']}
paths.update(revision=54,updated_at=now,updated_by='codex:/root',amended_at=now,amended_by='codex:/root'); replace(path_path,paths)
record=HERE/'cli_source_scope_codex.json'
save(record,{'schema':'researchos.w05.root-source-scope.v1','step_id':'W05-99','slice_id':proposal['slice_id'],
    'status':'AUTHORIZED_EXACT_SOURCE_SLICE','registered_at':now,'actor':'codex:/root','owner':binding['owner'],
    'worktree':binding['worktree'],'exact_paths':new_paths,'existing_source_refs':proposal['existing_files'],'new_paths':proposal['new_files'],
    'scope_approval':ref(approval),'proposal_ref':ref(HERE/'source_slice1.json'),
    'completion_criteria':proposal['completion_criteria'],'required_negative_tests':proposal['required_negative_tests'],
    'implementation_mode':'CURRENT_SOURCE_WITH_EXPLICIT_FIXTURE_VALIDATION_NOT_FULL_LIVE_ACCEPTANCE',
    'w04_current_vector_intersection':[],'formal_case_count_delta':0,
    'limits':['No Goal/runtime/sandbox/schema/lock/route or sharedregistry edits in this six-file slice.',
        'Do not claim token streaming from splitting final output; emit only actual host events.',
        'Interrupted CLI exit or cancel request alone does not prove child/process/effect settlement.',
        'Complete W05 includes deferred Goal/runtime and all actual LIVE requirements; current slice cannot sign parent/formal A04.']})
cp.update(updated_at=now,updated_by='codex:/root',note='W05 exact6-file CLI slice independently reviewed and authorized. Current3 W04 formalcases remain byte-current; parent5/22 formal3/42,84 failures unchanged. Full W05 Goal/runtime/LIVE still required.')
cp['work_in_progress'].update(status='REGISTERED_CURRENT_CLI_SOURCE_SLICE',next_action='Implement6 exact CLI source/tests paths and prove current turn binding/event pagination/settled exits/host cancellation; independently review before merging. Continue separate Goal/runtime/LIVE slices afterwards.')
cp['integrity_events'].append({'at':now,'actor':'codex:/root','event':'W05_EXACT_CURRENT_CLI_SOURCE_SLICE_REGISTERED','evidence':ref(record)})
cp['evidence_index'].append(record.relative_to(ROOT).as_posix()); replace(cp_path,cp)
event=HERE/'cli_scope_value_round_codex.json'
save(event,{'schema':'researchos.value-round.v1','round_id':'W05-exact-current-cli-flow-slice-20261006','delta':'INFRASTRUCTURE',
    'summary':'Independent6-file minimum current CLI flow scope registered; production source and real LIVE not yet executed.',
    'evidence_refs':[ref(record),ref(approval)]})
r=subprocess.run([sys.executable,'-B','-X','utf8',str(ROOT/'bootstrap/v24_checkpoint.py'),'--checkpoint',str(cp_path),'--state',str(state_path),
    '--plan',str(SPEC/'contracts/execution.plan.json'),'--delivery',str(SPEC/'contracts/delivery.contract.json'),
    '--expected-revision','220','--round-event',str(event),'--actor','codex:/root'],cwd=ROOT,capture_output=True)
for name,raw in [('checkpoint221.stdout.json',r.stdout),('checkpoint221.stderr.txt',r.stderr)]:
    with (HERE/name).open('xb') as stream: stream.write(raw)
assert r.returncode==0,r.stderr.decode('utf8','replace')
after=load(cp_path)
assert after['revision']==221 and after['failure_counters']==old_cp['failure_counters'] and state_path.read_bytes()==state_raw
assert after['value_checkpoint']['history'][:len(old_cp['value_checkpoint']['history'])]==old_cp['value_checkpoint']['history']
assert after['value_checkpoint']['formal_gate']['formal_cases_accepted']==3
print(json.dumps({'status':'PASS_EXACT_CLI_SLICE_AUTHORIZED','checkpoint':221,'path_revision':54,'source_paths':6,'formal_accepted':3}))
