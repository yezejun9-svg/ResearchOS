"""Start only the independently verified U09-selected W03 parent card."""
from pathlib import Path
import copy
import datetime as dt
import hashlib
import json
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
CARD = HERE.parent
V24 = ROOT / 'execution/v2.4'
SPEC = ROOT / '.local/worktrees/v24-continuation/spec/v2.4'
WORKTREE = ROOT / '.local/worktrees/codex-w0199'
OWNER = 'codex:/root/w0199_impl'

def read(path): return json.loads(path.read_bytes())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def ref(path): return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path)}
def save(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2); stream.write('\n')
def rewrite(path, value): path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

cp_path, state_path, ownership_path = (V24 / n for n in ('checkpoint.json','step_state.json','path_ownership.json'))
cp, state, ownership = read(cp_path), read(state_path), read(ownership_path)
assert cp['revision'] == 206 and len(cp['failure_counters']) == 65
old_failures, old_rows = copy.deepcopy(cp['failure_counters']), copy.deepcopy(state['steps'])
packet_path = ROOT / 'execution/v2.4/receipts/W02/W02-99/integration_codex/u09-priority-repair/checkpoint206_next_packet.json'
packet = read(packet_path)
assert packet['eligible'] is True and packet['state_source'] == 'VALIDATED_FILE'
assert packet['step']['id'] == 'W03-99' and packet['value_checkpoint_policy']['checkpoint_revision'] == 206
assert packet['value_checkpoint_policy']['selection']['candidates'][0]['capability_id'] == 'U02'
statuses = {row['id']:row['status'] for row in state['steps']}
assert all(statuses.get(dep) == 'ACCEPTED' for dep in packet['step']['dependencies'])
assert 'W03-99' not in statuses
assert ownership['revision'] == 45 and 'W03-99' not in ownership['card_path_bindings']
source = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
assert source == '81d668d94f85fc1961ee53bf439a36ab95048d15'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=WORKTREE,text=True).strip() == source
assert subprocess.check_output(['git','branch','--show-current'],cwd=WORKTREE,text=True).strip() == 'work/codex-w0399'
assert not subprocess.check_output(['git','status','--porcelain'],cwd=WORKTREE)
now = dt.datetime.now(dt.timezone.utc).isoformat()
binding = {'owner': OWNER, 'worktree': '.local/worktrees/codex-w0199',
    'branch': 'work/codex-w0399', 'source_head': source,
    'paths': ['execution/v2.4/receipts/W03/W03-99/**'],
    'read_only_context': ['current accepted domain/API/store/contracts source and tests',
        'frozen v2.4 package', 'execution/v2.4/commands.json', 'W03 child immutable evidence'],
    'shared_registry_writer': 'codex:/root',
    'root_only_paths': ['execution/v2.4/step_state.json','execution/v2.4/checkpoint.json',
        'execution/v2.4/path_ownership.json','execution/v2.4/commands.json'],
    'rationale': 'Frozen receipt-only W03 parent scope. Reuse current Go/SQLite/HTTP production fixtures and add bounded current schema/OpenAPI/type/hash probes in receipts. Root serializes two command entries for three exact gates. No final-owned formal case.',
    'model': 'gpt-6-astra', 'reasoning_effort': 'high',
    'reason_for_model': 'Current frozen domain/API/storage contract projection and dispatcher preservation are architecture decisions; reuse existing Astra executor without repeating prior Sol capacity failures.',
    'limits': ['No product/source/test/contract edits outside receipts without exact root issue registration.',
        'Do not run legacy fixed20 total checkers or inherit old whole PASS after input drift.',
        'No GUI/provider/protected service/NVDA/old W13 audit/resource retries.',
        'No independent-signed acceptance or final case ownership; A03/C04/C19 remain with W06/W04/W09.',
        'Archive actual per-attempt commands/raw/assertions/input hashes; reject empty/missing assertions.']}
ownership['card_path_bindings']['W03-99'] = binding
ownership.update(revision=46, amended_at=now, amended_by='codex:/root', updated_at=now, updated_by='codex:/root')
rewrite(ownership_path, ownership)
binding_path = CARD / 'path_binding_codex.json'
save(binding_path, {'schema':'researchos.parent-card-path-binding.v1','step_id':'W03-99',
    'registered_at':now,'integrator':'codex:/root','binding':binding,
    'ownership_revision':46,'ownership_sha256':sha(ownership_path),
    'selection_proof':ref(packet_path),'owned_acceptance_ids':[],
    'allowed_gates': {'W03-G01':'DEVELOPMENT','W03-G02':'FIXTURE','W03-G03':'FIXTURE'}})
save(HERE / 'binding_baseline_codex.json', {'commands_revision':read(V24/'commands.json')['revision'],
    'v24_decoded_commands':read(V24/'commands.json')['commands'],
    'v24_registry_sha256':sha(V24/'commands.json'),
    'legacy_registry_sha256':sha(ROOT/'execution/commands.json'),
    'protected_source_hashes':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in [
        ROOT/'execution/command_dispatcher/dispatch.py', ROOT/'execution/v2.4/client_mapping.json',
        ROOT/'execution/toolchain.json', ROOT/'ops/ci/contracts.py', ROOT/'ops/ci/domain.py',
        ROOT/'tests/contracts/check/main.go', ROOT/'tests/domain/check/main.go']}})
state['steps'].append({'id':'W03-99','status':'IN_PROGRESS','executor_id':OWNER,
    'started_at':now,'evidence':[{'path':binding_path.relative_to(V24).as_posix(),'sha256':sha(binding_path)}],
    'execution_note':'Required U02 prerequisite selected after independent U09 repair. Three local construction gates; no final-owned formal cases.'})
assert state['steps'][:-1] == old_rows
rewrite(state_path,state)
cp.update(updated_at=now,updated_by='codex:/root',head=source,current_step_id='W03-99',next_step_id='W03-99',
    candidate_worktree='.local/worktrees/codex-w0199',candidate_branch='work/codex-w0399',
    next_command='Implement current receipt-contained W03 gates, then root registers and runs frozen exact selectors and independent verifier reviews.',
    work_in_progress={'step_id':'W03-99','status':'IN_PROGRESS','owner':OWNER,
        'worktree':binding['worktree'],'branch':binding['branch'],
        'next_action':'Current contract projection and isolated domain/migration/type/hash gate evidence; no formal case acceptance.'},
    note='W03 required U02 prerequisite started in clean reused worktree.37 accepted rows,parent3/22,formal0/42 remain.65 failure origins retained; U09 priority active; no resource-dependent branch retried.')
cp['workers'].append({'step_id':'W03-99','owner':OWNER,'worktree':binding['worktree'],'state':'IN_PROGRESS_PARENT_LOCAL_GATES'})
cp['integrity_events'].append({'at':now,'actor':'codex:/root','event':'W03_PARENT_SCOPE_REGISTERED_AFTER_U09_INDEPENDENT_SELECTION','evidence':ref(binding_path)})
cp['evidence_index'].append(binding_path.relative_to(ROOT).as_posix())
rewrite(cp_path,cp)
event = HERE/'start_value_round_codex.json'
save(event,{'schema':'researchos.value-round.v1','round_id':'W03-parent-local-gates-start-20261006',
    'delta':'INFRASTRUCTURE','summary':'Start required U02 W03 prerequisite with exact receipt-only ownership; no user capability inferred.',
    'evidence_refs':[ref(binding_path),ref(packet_path)]})
argv=[sys.executable,'-B','-X','utf8',str(ROOT/'bootstrap/v24_checkpoint.py'),
    '--checkpoint',str(cp_path),'--state',str(state_path),'--plan',str(SPEC/'contracts/execution.plan.json'),
    '--delivery',str(SPEC/'contracts/delivery.contract.json'),'--expected-revision','206',
    '--round-event',str(event),'--actor','codex:/root']
result=subprocess.run(argv,cwd=ROOT,capture_output=True)
(HERE/'checkpoint207.stdout.txt').write_bytes(result.stdout)
(HERE/'checkpoint207.stderr.txt').write_bytes(result.stderr)
assert result.returncode==0
after=read(cp_path)
assert after['revision']==207 and after['failure_counters']==old_failures
assert after['value_checkpoint']['pause_nonblocking_expansion'] is True
assert sum(row['status']=='ACCEPTED' for row in read(state_path)['steps'])==37
print(json.dumps({'status':'PASS_W03_REGISTERED_IN_PROGRESS','checkpoint':207,
    'ownership_revision':46,'failure_origins':65,'owned_cases':[]}))
