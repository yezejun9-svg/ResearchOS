"""Preserve the actual failed review-phase check before a scoped integrity repair."""
from pathlib import Path
import copy, datetime as dt, hashlib, json, subprocess, sys
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[5]; V24=ROOT/'execution/v2.4'
SPEC=ROOT/'.local/worktrees/v24-continuation/spec/v2.4'
def load(p): return json.loads(p.read_bytes())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p): return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(p,v):
    with p.open('x',encoding='utf8',newline='\n') as f: json.dump(v,f,ensure_ascii=False,indent=2); f.write('\n')
def replace(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
cp_path,state_path,path_path=(V24/n for n in ['checkpoint.json','step_state.json','path_ownership.json'])
cp,paths=load(cp_path),load(path_path); old=copy.deepcopy(cp); state_raw=state_path.read_bytes()
assert cp['revision']==217 and len(cp['failure_counters'])==79 and paths['revision']==51
assert next(r for r in load(state_path)['steps'] if r['id']=='W04-99')['status']=='IN_PROGRESS'
failed=load(HERE/'reviewed_integrity.stdout.json'); assert failed['integrity']=='FAIL' and failed['reason_code']=='DISPATCHER_CHANGED'
attempt=load(HERE/'reviewed_integrity_invocation_codex.json'); assert attempt['exit_code']==1
native=load(ROOT/'execution/invocations/a64c00b7-0ea6-4469-911e-f135cc37f64d/receipt.json')
dispatcher=ROOT/'execution/command_dispatcher/dispatch.py'
assert sha(dispatcher)==native['dispatcher_sha256']=='69c94d63050fb2274a4d995742e934e85c52bd43e9afd5bf9640a5f3404061e4'
archive=HERE/'accept_parent_attempt1_source.py'
with archive.open('xb') as stream: stream.write((HERE/'accept_parent_codex.py').read_bytes())
now=dt.datetime.now(dt.timezone.utc).isoformat(); record=HERE/'registration_integrity_failure_codex.json'
save(record,{'schema':'researchos.root-registration-integrity-failure.v1','observed_at':now,
    'step_id':'W04-99','status':'OPEN_CHANGED_VALIDATOR_INPUT_REQUIRED',
    'classification':'CONSTRUCTION_EVIDENCE_MODEL_FAILURE_NOT_PRODUCT',
    'actual_failed_check':ref(HERE/'reviewed_integrity_invocation_codex.json'),'actual_failure_output':ref(HERE/'reviewed_integrity.stdout.json'),
    'root_failed_script':ref(archive),'validator_before':ref(HERE.parent/'formal_validator_codex/validate.py'),
    'public_reader_before':ref(V24/'formal_case_index.py'),'actual_current_dispatcher':ref(dispatcher),
    'native_receipt':ref(ROOT/'execution/invocations/a64c00b7-0ea6-4469-911e-f135cc37f64d/receipt.json'),
    'original_context':ref(HERE/'current_context_codex.json'),'original_independent_review':ref(HERE.parent/'independent_review_codex.json'),
    'root_tool_exit_code':1,'root_tool_chunk_id':'5589c3',
    'finding':'Registered construction dispatcher matches its actual native receipt hash but is absent from the earlier Go product execution vector. Do not rewrite the original product vector; separately verify actual registered source with current byte tracking and CAS.',
    'product_reexecutions':0,'canonical_state_changed':False,'formal_count_delta':0,
    'proposed_repair_scope':'Exact registered_dispatch source verification plus focused integrity controls; independent design confirmation and new round2 issuance required. No product, raw evidence or original review/context/issuance edits.'})
cp['failure_counters'].append({'origin_key':'W04-root-registration-SEPARATE_DISPATCHER_SOURCE_COVERAGE','attempts':1,
    'candidate_id':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
    'input_hash':sha(HERE.parent/'formal_validator_codex/validate.py'),'status':'OPEN_CHANGED_VALIDATOR_INPUT_REQUIRED',
    'classification':'CONSTRUCTION_EVIDENCE_MODEL_FAILURE_NOT_PRODUCT','evidence':ref(record),
    'product_failure_count_delta':0,'detail':'Actual review-phase integrity check rejects missing product-vector dispatcher despite identical current/native dispatcher bytes; preserve failure and require new scoped integrity implementation.'})
binding=paths['card_path_bindings']['W04-99']
binding['subtasks']['formal_integrity']['repair_owner']='codex:/root'
binding['subtasks']['formal_integrity']['repair_scope']='Only registered construction dispatcher source byte verification and focused controls; former executed Go vector/context/review/raw are immutable.'
paths.update(revision=52,updated_at=now,updated_by='codex:/root',amended_at=now,amended_by='codex:/root'); replace(path_path,paths)
cp.update(updated_at=now,updated_by='codex:/root',note='Actual root reviewed-phase registration rejected separate construction dispatcher coverage. Canonical W04 remains IN_PROGRESS; parent4/22 formal0/42.80 origins retained. Scoped validator repair and new independent issuance pending.')
cp['work_in_progress']['status']='REGISTRATION_INTEGRITY_REPAIR_PENDING'
cp['work_in_progress']['next_action']='Confirm construction-vs-product source boundary, retain actual rejection, repair only integrity layer, run focused changed-input controls and issue new independent round2 review.'
cp['integrity_events'].append({'at':now,'actor':'codex:/root','event':'W04_ACTUAL_REGISTRATION_INTEGRITY_REJECTION_RETAINED','evidence':ref(record)})
cp['evidence_index'].append(record.relative_to(ROOT).as_posix()); replace(cp_path,cp)
event=HERE/'registration_integrity_failure_value_round_codex.json'
save(event,{'schema':'researchos.value-round.v1','round_id':'W04-root-registration-integrity-actual-rejection-20261006',
    'delta':'INFRASTRUCTURE','summary':'Real review-phase rejection preserved and minimal integrity-only repair scope registered. No product failure/reexecution or formal acceptance.', 'evidence_refs':[ref(record)]})
r=subprocess.run([sys.executable,'-B','-X','utf8',str(ROOT/'bootstrap/v24_checkpoint.py'),'--checkpoint',str(cp_path),'--state',str(state_path),
    '--plan',str(SPEC/'contracts/execution.plan.json'),'--delivery',str(SPEC/'contracts/delivery.contract.json'),
    '--expected-revision','217','--round-event',str(event),'--actor','codex:/root'],cwd=ROOT,capture_output=True)
for name,raw in [('checkpoint218_integrity_rejection.stdout.json',r.stdout),('checkpoint218_integrity_rejection.stderr.txt',r.stderr)]:
    with (HERE/name).open('xb') as stream: stream.write(raw)
assert r.returncode==0,r.stderr.decode('utf8','replace')
after=load(cp_path)
assert after['revision']==218 and len(after['failure_counters'])==80 and after['failure_counters'][:79]==old['failure_counters']
assert state_path.read_bytes()==state_raw and after['value_checkpoint']['formal_gate']['formal_cases_accepted']==0
assert after['value_checkpoint']['history'][:len(old['value_checkpoint']['history'])]==old['value_checkpoint']['history']
print(json.dumps({'status':'PASS_ACTUAL_FAILURE_PRESERVED_SCOPED_REPAIR','checkpoint':218,'path_revision':52,'failure_origins':80,'formal_accepted':0}))
