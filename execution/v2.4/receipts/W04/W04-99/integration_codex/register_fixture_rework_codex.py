"""Preserve the first actual W04 failure and register one disjoint root test fix."""
from pathlib import Path
import copy, datetime as dt, hashlib, json, subprocess, sys

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[5]; V24=ROOT/'execution/v2.4'
CANDIDATE=ROOT/'.local/worktrees/codex-w0299'
RUN=CANDIDATE/'execution/v2.4/receipts/W04/W04-99/executor_codex/runs/20261005T224949Z-418d17844405'
SPEC=ROOT/'.local/worktrees/v24-continuation/spec/v2.4'
def load(p): return json.loads(p.read_bytes())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p): return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as f: json.dump(v,f,ensure_ascii=False,indent=2); f.write('\n')
def replace(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
cp_path,path_path,state_path=(V24/n for n in ['checkpoint.json','path_ownership.json','step_state.json'])
cp,paths=load(cp_path),load(path_path); state_raw=state_path.read_bytes(); old_failures=copy.deepcopy(cp['failure_counters'])
assert cp['revision']==215 and paths['revision']==50 and len(old_failures)==73
assert sha(RUN/'go.json')=='345199f192c0ba2a22168c684cf15f7a0a87ad9d1a0b22a13d45e1f63b8ace9b'
retained=HERE/'first_go_failure'; retained.mkdir(exist_ok=True)
for name in ['go.json','go.stdout','go.stderr','version_vector.json','tool_identity.json']:
    (retained/name).write_bytes((RUN/name).read_bytes())
proof=load(retained/'go.json'); assert proof['status']=='FAIL' and type(proof['exit_code']) is int and proof['exit_code']==1
origin_details={
    'SCANNER_SKIP_ABSENCE_FIXTURE':'The actual scanner correctly refuses NOT_FOUND when subtrees were not checked; root fixture must observe true absence in a separate complete scan.',
    'W03_ARTIFACT_GUARD_BASELINE_FIXTURE':'Current project policy adds a legitimate initial Artifact; historical guard must compare before/after per-project counts rather than assume zero.',
    'REQUIRED_CONTRACT_IMMUTABLE_VERSION_INJECTION':'Deleting immutable domain_versions was blocked; remove only the required current row and report the actual typed refusal.',
    'SEALED_RULE_TRIGGER_FAULT_INJECTION':'Sealed content mutation was blocked before materialization; isolated test injection must explicitly cross the trigger boundary and also exercise real raw removal.',
    'OPTIONAL_RECALL_STALE_BUNDLE_FIXTURE':'Capturing optional source changes the profile revision; freeze current required context after capture/refresh rather than silently reuse stale context.'}
for origin,detail in origin_details.items():
    cp['failure_counters'].append({'origin_key':'W04-first-Go-'+origin,'attempts':1,'candidate_id':subprocess.check_output(['git','rev-parse','HEAD'],cwd=CANDIDATE,text=True).strip(),
        'input_hash':sha(retained/'version_vector.json'),'status':'OPEN_CHANGED_FIXTURE_REQUIRED','classification':'FIXTURE_HARNESS_FAILURE_NOT_PRODUCT',
        'evidence':ref(retained/'go.json'),'product_failure_count_delta':0,'detail':detail})
root_test='internal/domain/w03_current_binding_test.go'
binding=paths['card_path_bindings']['W04-99']; assert root_test not in binding['paths'] and root_test not in binding['root_only_paths']
binding['root_only_paths'].append(root_test)
binding['subtasks']['legacy_guard_baseline']={'owner':'codex:/root','worktree':'.local/worktrees/codex-w0299','paths':[root_test],
    'scope':'Only TestW03CurrentEvaluationArtifactGuard: capture actual per-project Artifact count after current project creation, then prove every refused seal leaves that exact count unchanged. No W03 production/other tests change.'}
now=dt.datetime.now(dt.timezone.utc).isoformat(); record=HERE/'fixture_rework_scope_codex.json'
save(record,{'schema':'researchos.fixture-rework-scope.v1','step_id':'W04-99','registered_at':now,'actor':'codex:/root',
    'first_failed_proof':ref(retained/'go.json'),'raw_retained':[ref(retained/n) for n in ['go.stdout','go.stderr','version_vector.json','tool_identity.json']],
    'fixture_failures':origin_details,'root_additional_test_scope':binding['subtasks']['legacy_guard_baseline'],'root_test_before_sha256':sha(CANDIDATE/root_test),
    'review_findings':['Bind source assertion test names to exact package; reject fail/skip/missing package completion.','Require type(exit_code) is int and zero; JSON false is not an exit code.'],
    'formal_case_count_delta':0,'failure_origin_delta':5,'immutable_failed_attempt':True})
paths.update(revision=51,amended_at=now,amended_by='codex:/root',updated_at=now,updated_by='codex:/root'); replace(path_path,paths)
cp.update(updated_at=now,updated_by='codex:/root',note='First W04 actual Go proof preserved with5 fixture failures; minimal W03 test baseline correction scope registered. Static evidence parser defects pending correction. No unchanged retry, no formal acceptance.')
cp['integrity_events'].append({'at':now,'actor':'codex:/root','event':'W04_FIRST_ACTUAL_FIXTURE_FAILURE_RETAINED','evidence':ref(record)})
cp['evidence_index'].append(record.relative_to(ROOT).as_posix()); replace(cp_path,cp)
event=HERE/'fixture_rework_value_round_codex.json'; save(event,{'schema':'researchos.value-round.v1','round_id':'W04-first-failed-proof-scoped-rework-20261006','delta':'INFRASTRUCTURE',
    'summary':'Actual first failed Go proof retained;5 fixture failures recorded and one scoped root guard correction registered before edit. No parent or formal case acceptance.',
    'evidence_refs':[ref(record)]})
r=subprocess.run([sys.executable,'-B','-X','utf8',str(ROOT/'bootstrap/v24_checkpoint.py'),'--checkpoint',str(cp_path),'--state',str(state_path),'--plan',str(SPEC/'contracts/execution.plan.json'),
    '--delivery',str(SPEC/'contracts/delivery.contract.json'),'--expected-revision','215','--round-event',str(event),'--actor','codex:/root'],cwd=ROOT,capture_output=True)
(HERE/'checkpoint216.stdout.txt').write_bytes(r.stdout); (HERE/'checkpoint216.stderr.txt').write_bytes(r.stderr)
assert r.returncode==0,r.stderr.decode('utf8','replace')
after=load(cp_path); assert after['revision']==216 and after['failure_counters'][:73]==old_failures and len(after['failure_counters'])==78 and state_path.read_bytes()==state_raw
print(json.dumps({'status':'PASS_SCOPED_CHANGED_FIXTURE_REWORK','checkpoint':216,'path_revision':51,'failure_origins':78,'formal_accepted':0}))
