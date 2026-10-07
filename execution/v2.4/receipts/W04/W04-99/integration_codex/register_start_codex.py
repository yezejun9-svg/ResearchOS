"""Start the U09-selected W04 card with non-overlapping evidence subowners."""
from pathlib import Path
import copy
import datetime as dt
import hashlib
import json
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[5]
V24=ROOT/'execution/v2.4'
SPEC=ROOT/'.local/worktrees/v24-continuation/spec/v2.4'
CARD=HERE.parent
WORKTREE=ROOT/'.local/worktrees/codex-w0299'
def load(path): return json.loads(path.read_bytes())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def ref(path,base=ROOT): return {'path':path.relative_to(base).as_posix(),'sha256':sha(path)}
def save(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
def replace(path,value): path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

cp_path,state_path,path_path=(V24/n for n in ['checkpoint.json','step_state.json','path_ownership.json'])
cp,state,paths=(load(p) for p in [cp_path,state_path,path_path])
assert cp['revision']==212 and len(cp['failure_counters'])==73 and paths['revision']==47
old_failures,old_rows=copy.deepcopy(cp['failure_counters']),copy.deepcopy(state['steps'])
packet_path=ROOT/'execution/v2.4/receipts/W03/W03-99/integration_codex/checkpoint212_next_packet.json'
packet=load(packet_path)
assert packet['eligible'] is True and packet['state_source']=='VALIDATED_FILE' and packet['step']['id']=='W04-99'
assert packet['value_checkpoint_policy']['checkpoint_revision']==212
statuses={r['id']:r['status'] for r in state['steps']}
assert all(statuses.get(x)=='ACCEPTED' for x in packet['step']['dependencies'])
assert 'W04-99' not in statuses and 'W04-99' not in paths['card_path_bindings']
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
assert head=='58781d7d63a3a0ba057554912d0896b6134e6f95'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=WORKTREE,text=True).strip()==head
assert subprocess.check_output(['git','branch','--show-current'],cwd=WORKTREE,text=True).strip()=='work/codex-w0499'
assert not subprocess.check_output(['git','status','--porcelain'],cwd=WORKTREE)
now=dt.datetime.now(dt.timezone.utc).isoformat()
binding={'owner':'codex:/root/w1102_impl','worktree':'.local/worktrees/codex-w0299','branch':'work/codex-w0499','source_head':head,
    'paths':['execution/v2.4/receipts/W04/W04-99/executor_codex/**'],
    'subtasks':{'formal_integrity':{'owner':'codex:/root/w0199_impl','workspace':'main','paths':['execution/v2.4/receipts/W04/W04-99/formal_validator_codex/**'],
        'scope':'Read-only evidence validator implementation and explicitly synthetic controls; no source, raw product evidence or shared-state writes.'}},
    'root_only_paths':['execution/v2.4/checkpoint.json','execution/v2.4/step_state.json','execution/v2.4/path_ownership.json','execution/v2.4/commands.json','execution/v2.4/receipts/W04/W04-99/integration_codex/**'],
    'read_only_context':['current accepted product/domain/host/CLI source','frozen v2.4 contracts and rules','W04 child history and original legacy handlers','W03 independent acceptance'],
    'shared_registry_writer':'codex:/root','model':'gpt-6-astra','reasoning_effort':'high',
    'reason_for_model':'Current workflow rules/context authority and formal independent evidence integrity require architecture reasoning; reuse existing agents without old Sol capacity retries.',
    'rationale':'Start current owned-case construction after W03 independent acceptance. Root registers concrete production source/embedded assets only after separate architecture review; until then evidence subpaths only.',
    'limits':['Do not edit production source until exact root registration arrives.','C03/C04/A01 FIXTURE only, all frozen assertions and GLOBAL_EVIDENCE required; no independent self-acceptance.',
        'Preserve old handlers/legacy forwarding and previous failure receipts; no unchanged failed-input retries.','No provider/service/GUI/NVDA/old W13 audit/W14 UNKNOWN effect or protected labels.']}
paths['card_path_bindings']['W04-99']=binding
paths.update(revision=48,amended_at=now,amended_by='codex:/root',updated_at=now,updated_by='codex:/root')
replace(path_path,paths)
binding_path=CARD/'path_binding_codex.json'
save(binding_path,{'schema':'researchos.parent-card-path-binding.v1','step_id':'W04-99','registered_at':now,'integrator':'codex:/root','binding':binding,
    'ownership_revision':48,'ownership_sha256':sha(path_path),'selection_proof':ref(packet_path),'owned_acceptance_ids':['C03','C04','A01'],
    'allowed_gates':{gid:'FIXTURE' for gid in ['W04-G01','W04-G02','W04-G03','W04-H01','W04-B01']},'formal_case_count_delta':0})
save(HERE/'binding_baseline_codex.json',{'source_head':head,'commands_revision':load(V24/'commands.json')['revision'],
    'decoded_commands':load(V24/'commands.json')['commands'],'commands_sha256':sha(V24/'commands.json'),
    'protected_sha256':{p:sha(ROOT/p) for p in ['execution/commands.json','execution/toolchains/locked.json','execution/command_dispatcher/dispatch.py','bootstrap/v24_checkpoint.py','execution/v2.4/client_mapping.json']},
    'before_failure_origins':73,'before_parent_accepted':4,'before_formal_accepted':0})
state['steps'].append({'id':'W04-99','status':'IN_PROGRESS','executor_id':binding['owner'],'started_at':now,'evidence':[ref(binding_path,V24)],
    'execution_note':'Required U02 prerequisite. Five FIXTURE parent gates plus owned C03/C04/A01 full cases; architecture source mapping pending, no formal verdict yet.'})
assert state['steps'][:-1]==old_rows
replace(state_path,state)
cp.update(head=head,current_step_id='W04-99',next_step_id='W04-99',updated_at=now,updated_by='codex:/root',candidate_worktree=binding['worktree'],candidate_branch=binding['branch'],
    work_in_progress={'step_id':'W04-99','owner':binding['owner'],'status':'REGISTERED_EVIDENCE_PREPARATION_SOURCE_MAPPING_PENDING','worktree':binding['worktree'],
        'next_action':'Independent minimum rule/context architecture review, exact source registration and production FIXTURE owned-case implementation.'},
    next_command='Complete current W04 rule/context source slice and actual owned FIXTURE cases, then exact registered gates and independent review.',
    note='W04 sole active engineering card after W03 acceptance.38 accepted rows,parent4/22,formal0/42.73 failure origins retained; independent evidence validator subowner disjoint; no unrelated resource branch retry.')
cp['workers'].append({'step_id':'W04-99','owner':binding['owner'],'worktree':binding['worktree'],'state':'IN_PROGRESS_EVIDENCE_AND_ARCHITECTURE'})
cp['integrity_events'].append({'at':now,'actor':'codex:/root','event':'W04_PARENT_SCOPE_REGISTERED_AFTER_W03_INDEPENDENT_ACCEPTANCE','evidence':ref(binding_path)})
cp['evidence_index'].append(binding_path.relative_to(ROOT).as_posix())
replace(cp_path,cp)
event=HERE/'start_value_round_codex.json'
save(event,{'schema':'researchos.value-round.v1','round_id':'W04-owned-formal-and-context-start-20261006','delta':'INFRASTRUCTURE',
    'summary':'Start exact U09-required W04 card with disjoint formal validator ownership; source registration pending architecture; no formal case accepted.',
    'evidence_refs':[ref(binding_path),ref(packet_path)]})
argv=[sys.executable,'-B','-X','utf8',str(ROOT/'bootstrap/v24_checkpoint.py'),'--checkpoint',str(cp_path),'--state',str(state_path),
    '--plan',str(SPEC/'contracts/execution.plan.json'),'--delivery',str(SPEC/'contracts/delivery.contract.json'),'--expected-revision','212','--round-event',str(event),'--actor','codex:/root']
result=subprocess.run(argv,cwd=ROOT,capture_output=True)
(HERE/'checkpoint213.stdout.txt').write_bytes(result.stdout);(HERE/'checkpoint213.stderr.txt').write_bytes(result.stderr)
assert result.returncode==0,result.stderr.decode('utf-8','replace')
after=load(cp_path)
assert after['revision']==213 and after['failure_counters']==old_failures
assert sum(r['status']=='ACCEPTED' for r in load(state_path)['steps'])==38
print(json.dumps({'status':'PASS_W04_REGISTERED_IN_PROGRESS','checkpoint':213,'path_revision':48,'failure_origins':73,'owned_cases':['C03','C04','A01']}))
