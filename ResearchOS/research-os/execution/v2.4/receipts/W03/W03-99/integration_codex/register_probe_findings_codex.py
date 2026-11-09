"""Preserve actual W03 probe failures before authorizing production repair."""
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
CANDIDATE=ROOT/'.local/worktrees/codex-w0199'
RUNS=CANDIDATE/'execution/v2.4/receipts/W03/W03-99/executor_codex/runs'
def read(p): return json.loads(p.read_bytes())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p): return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(v,f,ensure_ascii=False,indent=2); f.write('\n')

cp_path=V24/'checkpoint.json'
cp=read(cp_path)
assert cp['revision']==207 and len(cp['failure_counters'])==66
old=copy.deepcopy(cp['failure_counters'])
state_raw=(V24/'step_state.json').read_bytes()
stems=['W03-G01-probe-96a520670f4449088c26185f001d21d4','W03-G01-probe-f53b30a4e02d48cebe13e8650af76aa5']
assert sha(RUNS/stems[1]/'receipt.json')=='7b657efb2d9828749ceb00252efd9a5a1cfe93a447b1b62e11434d7273a9e893'
assert sha(RUNS/stems[1]/'manifest.json')=='531799dfdee48f70065e47afa00b1b6c396d7abea018c8d3cf93b6acedec5eea'
mirrors=[]
for stem in stems:
    source=RUNS/stem
    receipt=read(source/'receipt.json')
    assert receipt['status']=='FAIL' and receipt['exit_code']==1
    assert sha(source/'stdout.txt')==receipt['stdout_sha256']
    assert sha(source/'stderr.txt')==receipt['stderr_sha256']
    destination=HERE/'observed-probe-failures'/stem
    destination.mkdir(parents=True,exist_ok=False)
    refs=[]
    for name in ['receipt.json','manifest.json','stdout.txt','stderr.txt']:
        raw=(source/name).read_bytes()
        (destination/name).write_bytes(raw)
        assert sha(destination/name)==sha(source/name)
        refs.append(ref(destination/name))
    mirrors.append({'original_path':str(source),'source_head':receipt['source_head'],
        'input_digest':receipt['input_digest'],'artifacts':refs})
actual=read(HERE/'observed-probe-failures'/stems[1]/'stdout.txt')
checks=actual['checks']
failed=[row for row in checks if row['passed'] is not True]
assert len(checks)==124 and len(failed)==3
assert len({row['id'] for row in checks})==124
now=dt.datetime.now(dt.timezone.utc).isoformat()
issue_path=HERE/'runtime_domain_contract_issue_codex.json'
save(issue_path,{'schema':'researchos.real-issue-observation.v1',
    'origin_problem_id':'W03-RUNTIME-DOMAIN-V24-PROJECTION-001',
    'status':'CONFIRMED_PENDING_FINAL_PRODUCTION_PATH_MAPPING',
    'observed_at':now,'integrator':'codex:/root','executor':'codex:/root/w0199_impl',
    'mode':'DEVELOPMENT','parent_gate':'W03-G01','observed_checks':124,
    'satisfied_checks':121,'failed_checks':failed,'original_evidence':mirrors,
    'observation':'Frozen current MU_FORK ProjectBinding and2.4 EvaluationSummary validate against v2.4 but fail the production legacy-loaded contracts. ProjectBinding has no schema_version and is nested by ProjectState/Goal/Task, so top-level version dispatch alone is insufficient.',
    'scope_now':'Executor remains receipt-only; final source mapping follows narrow independent architecture review before any production edits.',
    'requirements':['Preserve old objects and explicit v2.0 schema behavior.',
        'Current fixed Mu host creates and validates its legitimate binding through the sole domain authority.',
        'Use exact frozen transitive definitions, not arbitrary schema relaxation or global replacement.',
        'Do not add client-controlled route/version authority or alter the Mu choice.',
        'Separate formal/parent acceptance from these actual developmental failures.'],
    'formal_case_count_delta':0,'parent_accepted':False})
cp['failure_counters'].extend([
    {'origin_key':'W03-executor-probe-Go-module-boundary','attempts':1,
     'candidate_id':'work/codex-w0399@81d668d9','input_hash':mirrors[0]['input_digest'],
     'status':'RESOLVED_CHANGED_EXPLICIT_MAIN_GO_INVOCATION',
     'evidence':mirrors[0]['artifacts'][0],
     'detail':'Execution subtree contains a separate Go module; directory go run failed before assertions. Explicit main.go invocation produced the separately preserved actual124 checks. No original failed argv retry.'},
    {'origin_key':'W03-current-runtime-domain-v24-projection','attempts':1,
     'candidate_id':'work/codex-w0399@81d668d9','input_hash':mirrors[1]['input_digest'],
     'status':'OPEN_CONFIRMED_PRODUCTION_CONTRACT_GAP',
     'evidence':mirrors[1]['artifacts'][0],'issue':ref(issue_path),
     'detail':'124 actual developmental checks:121 satisfied,3 failures in ProjectBinding/EvaluationSummary production projection. New source repair must be registered; no unchanged retry or acceptance.'}])
cp.update(updated_at=now,updated_by='codex:/root',
    work_in_progress={'step_id':'W03-99','status':'CONFIRMED_SOURCE_GAP_MAPPING_IN_PROGRESS',
        'origin_problem_id':'W03-RUNTIME-DOMAIN-V24-PROJECTION-001',
        'worktree':'.local/worktrees/codex-w0199',
        'next_action':'Complete exact nested binding/producer compatibility architecture mapping, register specific files, then repair and verify changed inputs.'},
    note='W03 actual current production probe121/124 with3 preserved failures.68 original failure origins retained. Parent3/22 formal0/42 unchanged; source repair not yet authorized until exact mapping. U09 required U02 prerequisite still active.')
cp['integrity_events'].append({'at':now,'actor':'codex:/root',
    'event':'W03_REAL_CURRENT_CONTRACT_GAP_RECORDED_BEFORE_SOURCE_EDITS','evidence':ref(issue_path)})
cp['evidence_index'].append(issue_path.relative_to(ROOT).as_posix())
cp_path.write_text(json.dumps(cp,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
event=HERE/'probe_findings_value_round_codex.json'
save(event,{'schema':'researchos.value-round.v1','round_id':'W03-current-domain-probe-findings-20261006',
    'delta':'INFRASTRUCTURE','summary':'Preserve failed real production contract comparison and freeze necessary source mapping; no user capability or acceptance inferred.',
    'evidence_refs':[ref(issue_path),mirrors[0]['artifacts'][0],mirrors[1]['artifacts'][0]]})
argv=[sys.executable,'-B','-X','utf8',str(ROOT/'bootstrap/v24_checkpoint.py'),
    '--checkpoint',str(cp_path),'--state',str(V24/'step_state.json'),
    '--plan',str(SPEC/'contracts/execution.plan.json'),'--delivery',str(SPEC/'contracts/delivery.contract.json'),
    '--expected-revision','207','--round-event',str(event),'--actor','codex:/root']
result=subprocess.run(argv,cwd=ROOT,capture_output=True)
(HERE/'checkpoint208.stdout.txt').write_bytes(result.stdout)
(HERE/'checkpoint208.stderr.txt').write_bytes(result.stderr)
assert result.returncode==0
after=read(cp_path)
assert after['revision']==208 and len(after['failure_counters'])==68
assert after['failure_counters'][:66]==old and (V24/'step_state.json').read_bytes()==state_raw
assert after['value_checkpoint']['pause_nonblocking_expansion'] is True
print(json.dumps({'status':'PASS_W03_FAILED_PROBE_EVIDENCE_PRESERVED','checkpoint':208,
    'failure_origins':68,'observed_checks':124,'failed_checks':3,'production_edits_authorized':False}))
