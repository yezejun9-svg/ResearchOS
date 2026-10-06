from pathlib import Path
import copy, datetime, hashlib, json, subprocess, sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
BASE = HERE.parent
WT = ROOT/'.local/worktrees/codex-w0599'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_bytes())
def ref(p): return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def create(p,v):
    with p.open('x',encoding='utf8',newline='\n') as f:
        json.dump(v,f,ensure_ascii=False,indent=2)
        f.write('\n')
def replace(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

original = WT/'execution/v2.4/receipts/W05/W05-99/executor_codex/s4_goal_follow_scope_proposal_codex.json'
assert sha(original) == '10dfb696a201ac57432ed6bdf3f0d1f80896ea5c2b3991a3f66c19d7e816175d'
proposal = HERE/'s4_goal_follow_scope_proposal_codex.json'
with proposal.open('xb') as f: f.write(original.read_bytes())
review_path = BASE/'architecture_review_codex/s4_goal_scope_review.json'
review = read(review_path)
assert review['reviewer'] == 'codex:/root/w1101_map'
assert review['decision'] == 'APPROVED_FOR_ROOT_PATH_REGISTRATION' and not review['input_mismatches']
assert review['proposal_sha256'] == sha(proposal)
data = read(proposal)
assert [r['path'] for r in data['source_paths']] == review['approved_exact_paths']
for row in data['source_paths']:
    assert sha(ROOT/row['path']) == sha(WT/row['path']) == row['before_sha256'] == review['verified_existing_source_hashes'][row['path']]
cp_path,path_path,state_path = [ROOT/'execution/v2.4'/n for n in ('checkpoint.json','path_ownership.json','step_state.json')]
cp,paths = read(cp_path),read(path_path)
old = copy.deepcopy(cp)
state_bytes = state_path.read_bytes()
assert cp['revision'] == 225 and paths['revision'] == 57 and len(cp['failure_counters']) == 99
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
scope = HERE/'s4_cli_goal_source_scope_codex.json'
create(scope, {'schema':'researchos.w05.root-additional-source-scope.v1',
    'status':'AUTHORIZED_EXACT_SOURCE_SLICE','slice_id':data['slice_id'],
    'owner':data['owner'],'registered_at':now,'registered_by':'codex:/root',
    'worktree':'.local/worktrees/codex-w0599','source_head':data['current_head'],
    'exact_paths':review['approved_exact_paths'],'existing_source_refs':[{'path':r['path'],'sha256':r['before_sha256']} for r in data['source_paths']],
    'proposal_ref':ref(proposal),'independent_scope_review_ref':ref(review_path),
    'implementation_contract':data['bounded_behavior'],
    'required_independent_review_guards':review['required_implementation_checks'],
    'required_tests':data['required_tests'],'additional_paths':False,
    'scope_currentness':'All four current main and candidate bytes still match independently reviewed before hashes; intervening integration changed disjoint domain paths only.',
    'provider_calls':0,'formal_case_count_delta':0,'parent_or_formal_acceptance':False})
subtasks = paths['card_path_bindings']['W05-99']['subtasks']
assert 'cli_goal_follower' not in subtasks
subtasks['cli_goal_follower'] = {'owner':data['owner'],'worktree':'.local/worktrees/codex-w0599',
    'branch':'work/codex-w0599','paths':[*review['approved_exact_paths'],'execution/v2.4/receipts/W05/W05-99/executor_codex/**'],
    'scope_ref':ref(scope),'model':'gpt-6-astra','reasoning_effort':'high',
    'reason':'Typed actual Goal session adoption and existing canonical CLI follower; exact four-path continuation after independent scope review.'}
paths.update(revision=58,updated_at=now,updated_by='codex:/root',amended_at=now,amended_by='codex:/root')
replace(path_path,paths)
cp.update(updated_at=now,updated_by='codex:/root',
    note='Reviewed S1 CLI and S3 tools integrated; S4 exact four CLI continuation paths independently scoped and root registered. S2 Goal direct tool/permission proof and raw-byte evidence amendment underway. Current W04 formal0 requires explicit revalidation; W05 remains IN_PROGRESS.')
cp['work_in_progress'].update(status='S1_S3_INTEGRATED_S2_PROOF_AMENDMENT_S4_AUTHORIZED',
    next_action='Complete S2 actual goal-created tool/permission positive and negative checks with fresh raw/source snapshots, then independent review. Implement S4 typed Goal follower in registered four paths, retain S1 frozen proof. Complete remaining durable queue/nested cancel/LIVE flows and explicitly revalidate W04.')
cp['evidence_index'].append(scope.relative_to(ROOT).as_posix())
cp['integrity_events'].append({'at':now,'actor':'codex:/root','event':'W05_S4_EXACT_CLI_GOAL_FOLLOWER_SCOPE_REGISTERED','evidence':ref(scope)})
replace(cp_path,cp)
event = HERE/'checkpoint226_value_round_codex.json'
create(event,{'schema':'researchos.value-round.v1','round_id':'W05-S4-exact-cli-goal-scope-20261006',
    'delta':'INFRASTRUCTURE','summary':'Independent four-file CLI Goal follower scope registered, preserving current0 formal status and all prior execution failure origins.',
    'evidence_refs':[ref(scope),ref(review_path)]})
frozen = ROOT/'.local/worktrees/v24-continuation/spec/v2.4'
args = [sys.executable,'-B','-X','utf8',str(ROOT/'bootstrap/v24_checkpoint.py'),
    '--checkpoint',str(cp_path),'--state',str(state_path),'--plan',str(frozen/'contracts/execution.plan.json'),
    '--delivery',str(frozen/'contracts/delivery.contract.json'),'--expected-revision','225',
    '--round-event',str(event),'--actor','codex:/root']
proc = subprocess.run(args,cwd=ROOT,capture_output=True)
for name,raw in [('stdout.json',proc.stdout),('stderr.txt',proc.stderr)]:
    with (HERE/f'checkpoint226.{name}').open('xb') as f:f.write(raw)
assert proc.returncode == 0,proc.stderr.decode('utf8','replace')
after = read(cp_path)
assert after['revision'] == 226 and after['failure_counters'] == old['failure_counters'] and state_path.read_bytes() == state_bytes
assert after['value_checkpoint']['formal_gate']['formal_cases_accepted'] == 0
print(json.dumps({'status':'PASS_REGISTERED_S4_EXACT_FOUR_SOURCE_PATHS','checkpoint':226,'paths_revision':58,'source_scope':ref(scope),'review':ref(review_path)},ensure_ascii=True))
