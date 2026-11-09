"""Freeze W04 executed/current inputs without accepting the parent or cases."""
from pathlib import Path
import ast, copy, datetime as dt, hashlib, json, subprocess, sys
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[5]; V24=ROOT/'execution/v2.4'; SPEC=ROOT/'.local/worktrees/v24-continuation/spec/v2.4'
def load(p): return json.loads(p.read_bytes())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p): return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(p,v):
    with p.open('x',encoding='utf8',newline='\n') as f: json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def replace(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
cp_path,state_path=V24/'checkpoint.json',V24/'step_state.json'; cp=load(cp_path); state_bytes=state_path.read_bytes(); old=copy.deepcopy(cp)
assert cp['revision']==216 and len(cp['failure_counters'])==78 and load(V24/'commands.json')['revision']==38
assert load(HERE/'execution_integrity.stdout.json')['integrity']=='PASS'
assert sha(V24/'formal_case_index.py')=='101241f1f06c2e0b8c472ced25fbaebe046e87e62dd58620fd08e46865af77b1'
assert sha(ROOT/'bootstrap/v24_checkpoint.py')=='3b648383c64091821c8274cb08323ca41da47deb5ab1ed69cb032e2112292ee8'
assert sha(V24/'parent_gate_ledger.py')=='5cb708317a24eebac00173f6ae52c3e4cda41ce08d8a0d9f60a53dcd22b176a8'
controls=HERE.parent/'formal_validator_codex'; expected_controls={
    controls/'synthetic-runs/controls-9714cb682e004c188edf523961283188/receipt.json':'0392ec9ea2ce30edc7503cb4aa2e92b6fed6a6e57c965d8fee9f9a0fc23f88b2',
    controls/'generic-controls/runs/controls-ad01f33f58554c5ba2ebb601db3966c7/receipt.json':'cc4cc87b40e9df03c78f9fe6693174c7267dfd2a441ff3b16f36b0d5fd53ce04',
    controls/'generic-controls/runs/controls-0402346f0fc24bcd9d4c8572f89b9293/receipt.json':'c6fbc046b9d1e36dc68bbcce43766ff305b5ec27249e8c9639dcdc7a7729c9d2'}
for path,digest in expected_controls.items(): assert sha(path)==digest
before=ast.parse((HERE/'baseline_v24_checkpoint_before_accounting.py').read_bytes()); after=ast.parse((ROOT/'bootstrap/v24_checkpoint.py').read_bytes())
def functions(tree): return {node.name:ast.dump(node,include_attributes=False) for node in tree.body if isinstance(node,ast.FunctionDef)}
for name in ['prioritized_step','flow_priority','ready_flows','next_packet']: assert functions(before)[name]==functions(after)[name],name
now=dt.datetime.now(dt.timezone.utc).isoformat(); record=HERE/'current_input_freeze_codex.json'
save(record,{'schema':'researchos.root-current-input-freeze.v1','step_id':'W04-99','status':'EXECUTED_PENDING_INDEPENDENT_REVIEW','frozen_at':now,'actor':'codex:/root',
    'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
    'current_context':ref(HERE/'current_context_codex.json'),'registered_commands':ref(HERE/'commands_registration_codex.json'),'actual_dispatches':ref(HERE/'registered_dispatch_summary_codex.json'),
    'execution_integrity':ref(HERE/'execution_integrity_invocation_codex.json'),
    'shared_source_refs':[ref(V24/'formal_case_index.py'),ref(V24/'parent_gate_ledger.py'),ref(ROOT/'bootstrap/v24_checkpoint.py')],
    'control_receipts':[ref(path) for path in expected_controls], 'formal_assertion_ids_unique':10,'formal_case_bindings':6,'registered_invocations':11,
    'parent_gate_ids':['W04-G01','W04-G02','W04-G03','W04-H01','W04-B01'],'implementation_mode':'FIXTURE',
    'current_counts':{'parent_accepted':4,'formal_cases_accepted':0},'first_go_fixture_failures_retained':5,
    'unchanged_u09_priority_ast':True,'known_baseline_unit_failure':ref(HERE/'baseline_priority_attribution_codex.json'),
    'trust_boundary':'Actual root-observed independent delivery and canonical owner acceptance remain pending. Synthetic controls create no real business acceptance.'})
cp['failure_counters'].append({'origin_key':'W04-accounting-STALE_U09_UNIT_EXPECTATION_PREEXISTING','attempts':1,
    'candidate_id':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
    'input_hash':sha(ROOT/'tests/resources/value_checkpoint_test.py'),'status':'KNOWN_BASELINE_FAILURE_NOT_CHANGED_BY_ACCOUNTING',
    'classification':'PREEXISTING_UNIT_EXPECTATION_FAILURE_NOT_PRODUCT','evidence':ref(HERE/'baseline_priority_attribution_codex.json'),
    'product_failure_count_delta':0,'detail':'Focused baseline replay reproduces unchanged parent-frontier return W17-99 versus stale None expectation; all4 U09 priority/selection functions retain exact AST. No retry of blocked cards.'})
cp.update(updated_at=now,updated_by='codex:/root',note='W04 current rules and complete3 owned FIXTURE cases executed;11 real registered bindings PASS; public accounting65+30+2 integrity controls PASS. Independent semantic review and formal registration pending. Parents4/22/formal0/42;79 failure origins retained.')
cp['integrity_events'].append({'at':now,'actor':'codex:/root','event':'W04_CURRENT_INPUTS_AND_PUBLIC_ACCOUNTING_FROZEN','evidence':ref(record)})
cp['evidence_index'].append(record.relative_to(ROOT).as_posix()); replace(cp_path,cp)
event=HERE/'current_inputs_value_round_codex.json'; save(event,{'schema':'researchos.value-round.v1','round_id':'W04-current-owned-cases-and-readonly-formal-accounting-20261006','delta':'FIXTURE',
    'summary':'Real current C03/C04/A01 observations and11 registered dispatches verified; independent formal counting integrity65+30+2 controls passed. No independent business acceptance yet.',
    'evidence_refs':[ref(record)]})
r=subprocess.run([sys.executable,'-B','-X','utf8',str(ROOT/'bootstrap/v24_checkpoint.py'),'--checkpoint',str(cp_path),'--state',str(state_path),'--plan',str(SPEC/'contracts/execution.plan.json'),
    '--delivery',str(SPEC/'contracts/delivery.contract.json'),'--expected-revision','216','--round-event',str(event),'--actor','codex:/root'],cwd=ROOT,capture_output=True)
(HERE/'checkpoint217.stdout.txt').write_bytes(r.stdout); (HERE/'checkpoint217.stderr.txt').write_bytes(r.stderr)
assert r.returncode==0,r.stderr.decode('utf8','replace')
after=load(cp_path); assert after['revision']==217 and after['failure_counters'][:78]==old['failure_counters'] and len(after['failure_counters'])==79 and state_path.read_bytes()==state_bytes
assert after['value_checkpoint']['formal_gate']['formal_cases_accepted']==0 and after['value_checkpoint']['formal_gate']['formal_evidence_integrity']=='PASS'
assert after['value_checkpoint']['history'][:len(old['value_checkpoint']['history'])]==old['value_checkpoint']['history']
print(json.dumps({'status':'PASS_CURRENT_INPUT_FREEZE','checkpoint':217,'failure_origins':79,'parent_accepted':4,'formal_accepted':0}))
