"""Finish partial W03 registration, preserving its original path-lookup failure."""
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
def read(p): return json.loads(p.read_bytes())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p): return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def rewrite(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

cp_path,state_path=V24/'checkpoint.json',V24/'step_state.json'
cp,state=read(cp_path),read(state_path)
ownership=read(V24/'path_ownership.json')
binding_path=CARD/'path_binding_codex.json'
binding=read(binding_path)
assert cp['revision']==206 and len(cp['failure_counters'])==65
assert ownership['revision']==46 and binding['ownership_sha256']==sha(V24/'path_ownership.json')
assert ownership['card_path_bindings']['W03-99']==binding['binding']
assert not any(r['id']=='W03-99' for r in state['steps'])
source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
assert source==binding['binding']['source_head']=='81d668d94f85fc1961ee53bf439a36ab95048d15'
packet_path=ROOT/binding['selection_proof']['path']
assert sha(packet_path)==binding['selection_proof']['sha256']
packet=read(packet_path)
assert packet['eligible'] is True and packet['step']['id']=='W03-99'
statuses={r['id']:r['status'] for r in state['steps']}
assert all(statuses.get(dep)=='ACCEPTED' for dep in packet['step']['dependencies'])
assert not (ROOT/'execution/toolchain.json').exists()
paths=['execution/command_dispatcher/dispatch.py','execution/v2.4/client_mapping.json',
    'execution/toolchains/locked.json','ops/ci/contracts.py','ops/ci/domain.py',
    'tests/contracts/check/main.go','tests/domain/check/main.go']
protected={p:sha(ROOT/p) for p in paths}
registry=read(V24/'commands.json')
assert registry['revision']==36
old_failures,old_rows=copy.deepcopy(cp['failure_counters']),copy.deepcopy(state['steps'])
now=dt.datetime.now(dt.timezone.utc).isoformat()
failure_path=HERE/'registration_round1_failure_codex.json'
save(failure_path,{'status':'PRESERVED_ROOT_REGISTRATION_FAILURE','exit_code':1,
    'actual_command':[sys.executable,'-B','-X','utf8','execution/v2.4/receipts/W03/W03-99/integration_codex/register_start_codex.py'],
    'cwd':str(ROOT),'failed_script':ref(HERE/'register_start_codex.py'),
    'failed_line':74,'exception':'FileNotFoundError',
    'missing_path':'execution/toolchain.json','actual_existing_path':'execution/toolchains/locked.json',
    'console_evidence':'Original traceback is preserved in the Codex exec_command result; no filesystem stdout/stderr capture was made for that registration call.',
    'partial_effects':{'ownership_revision':46,'path_binding_written':True,
        'state_unchanged':True,'checkpoint_revision':206,'worker_not_dispatched':True},
    'repair':'Validate correct existing locked toolchain path before further writes, keep original script and partial binding, finish remaining metadata once.',
    'state_sha256_before':sha(state_path),'product_tests_or_resource_retries':0})
save(HERE/'binding_baseline_codex.json',{'commands_revision':36,
    'v24_decoded_commands':registry['commands'],'v24_registry_sha256':sha(V24/'commands.json'),
    'legacy_registry_sha256':sha(ROOT/'execution/commands.json'),'protected_source_hashes':protected})
state['steps'].append({'id':'W03-99','status':'IN_PROGRESS','executor_id':'codex:/root/w0199_impl',
    'started_at':now,'evidence':[{'path':binding_path.relative_to(V24).as_posix(),'sha256':sha(binding_path)}],
    'execution_note':'Required U02 prerequisite selected after independent U09 repair. Three local construction gates; no final-owned formal cases. Original root registration path failure preserved.'})
assert state['steps'][:-1]==old_rows
cp['failure_counters'].append({'origin_key':'W03-root-registration-toolchain-path',
    'attempts':1,'status':'RESOLVED_CORRECT_EXISTING_PATH_METADATA_FINALIZER',
    'evidence':ref(failure_path),'detail':'Root registration referenced nonexistent execution/toolchain.json. Correct existing execution/toolchains/locked.json validated; original partial ownership/binding retained. No original script rerun or product test.'})
cp.update(updated_at=now,updated_by='codex:/root',head=source,current_step_id='W03-99',next_step_id='W03-99',
    candidate_worktree='.local/worktrees/codex-w0199',candidate_branch='work/codex-w0399',
    next_command='Implement W03 receipt-contained current gate evidence; root registers and runs frozen exact selectors, independent verifier accepts.',
    work_in_progress={'step_id':'W03-99','status':'IN_PROGRESS','owner':'codex:/root/w0199_impl',
        'worktree':'.local/worktrees/codex-w0199','branch':'work/codex-w0399',
        'next_action':'Current schema/OpenAPI and isolated migration/domain/type/hash verification; no formal case acceptance.'},
    note='W03 required U02 prerequisite started in clean reused worktree.37 accepted rows,parent3/22,formal0/42 unchanged.66 failure origins preserved including original root metadata error; U09 pause/history retained.')
cp['workers'].append({'step_id':'W03-99','owner':'codex:/root/w0199_impl',
    'worktree':'.local/worktrees/codex-w0199','state':'IN_PROGRESS_PARENT_LOCAL_GATES'})
cp['integrity_events'].append({'at':now,'actor':'codex:/root',
    'event':'W03_PARENT_SCOPE_REGISTERED_AFTER_U09_INDEPENDENT_SELECTION',
    'evidence':ref(binding_path),'registration_error':ref(failure_path)})
cp['evidence_index'].extend([binding_path.relative_to(ROOT).as_posix(),failure_path.relative_to(ROOT).as_posix()])
rewrite(state_path,state)
rewrite(cp_path,cp)
event=HERE/'start_value_round_codex.json'
save(event,{'schema':'researchos.value-round.v1','round_id':'W03-parent-local-gates-start-20261006',
    'delta':'INFRASTRUCTURE','summary':'Start required U02 W03 prerequisite in exact receipt-only scope, preserving root registration error and all formal gates.',
    'evidence_refs':[ref(binding_path),ref(packet_path),ref(failure_path)]})
argv=[sys.executable,'-B','-X','utf8',str(ROOT/'bootstrap/v24_checkpoint.py'),
    '--checkpoint',str(cp_path),'--state',str(state_path),'--plan',str(SPEC/'contracts/execution.plan.json'),
    '--delivery',str(SPEC/'contracts/delivery.contract.json'),'--expected-revision','206',
    '--round-event',str(event),'--actor','codex:/root']
result=subprocess.run(argv,cwd=ROOT,capture_output=True)
(HERE/'checkpoint207.stdout.txt').write_bytes(result.stdout)
(HERE/'checkpoint207.stderr.txt').write_bytes(result.stderr)
assert result.returncode==0
after=read(cp_path)
assert after['revision']==207 and after['failure_counters'][:65]==old_failures
assert len(after['failure_counters'])==66 and after['value_checkpoint']['pause_nonblocking_expansion'] is True
assert sum(r['status']=='ACCEPTED' for r in read(state_path)['steps'])==37
print(json.dumps({'status':'PASS_W03_REGISTRATION_FINALIZED','checkpoint':207,
    'ownership_revision':46,'failure_origins':66,'owned_cases':[]}))
