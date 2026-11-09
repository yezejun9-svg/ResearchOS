import hashlib, json, uuid
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path('D:/作品集/ResearchOS/research-os')
BASE = ROOT / 'execution/v2.4/receipts/W05/W05-99/cli_exact8_independent_replay_codex'
OUT = BASE / 'cli44-r309-c927f880'
OLD = BASE / 'cli47-r308-7d5925db'
LAUNCH = Path(__file__).resolve().parent
AUDIT = BASE / ('cli44-r309-final-' + uuid.uuid4().hex)
def ref(p):
    p=Path(p); raw=p.read_bytes()
    return dict(path=str(p), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
def load(p): return json.loads(Path(p).read_bytes())
def save(name, data):
    p=AUDIT/name
    with p.open('xb') as f: f.write((json.dumps(data, ensure_ascii=False, indent=2)+'\n').encode())
    return ref(p)
def check(condition, reason):
    if not condition: raise RuntimeError(reason)
def case(root, index):
    c=root/'cases'/f'{index:02d}'
    i=root/'invocations'/f'case-{index:02d}'/'invocation.json'
    inv=load(i); proc=inv['owned_process']; job=proc['job_cleanup']
    check(proc['actual_exit']==0 and not proc['timed_out'] and proc['error'] is None, str(i))
    check(proc['resumed'] and all(job[k] is True for k in ['assigned_before_resume','primary_exit_confirmed','job_idle_confirmed','handles_closed']) and job['errors']==[], 'JOB:'+str(i))
    raw=i.parent/'stdout.raw'
    events=[json.loads(x) for x in raw.read_text(encoding='utf-8').splitlines() if x.strip()]
    terminal=[e for e in events if e.get('Test') and e.get('Action') in ('pass','fail','skip')]
    leaves=[e for e in terminal if not any(x['Test'].startswith(e['Test']+'/') for x in terminal)]
    check(terminal and all(e['Action']=='pass' for e in terminal), 'TERMINAL:'+str(i))
    r=load(c/'result.json')
    check(sorted(r['actual_leaves'])==sorted(e['Test'] for e in leaves), 'ROSTER:'+str(i))
    frozen=load(root/'execution.inputs.before-first-case.json')
    for phase in (('before','after') if root==OLD else ('before','after-native','after-fixtures')):
        check(load(c/f'inputs.{phase}.json')==frozen, 'CLOSURE:'+str(c)+phase)
    if root==OLD:
        runtime_before=load(i.parent/'runtime.before.json')
        runtime_after=load(i.parent/'runtime.after.json')
        check(runtime_before==runtime_after, 'OLD_RUNTIME:'+str(i))
        by_path={x['path']:x for x in frozen}
        check(all(by_path.get(x['path'])==x for x in runtime_before), 'OLD_RUNTIME_CONTAINMENT')
    return dict(index=index, original_index=r.get('original_index',index), selector=r['selector'], actual_leaf_count=len(leaves), leaves=[e['Test'] for e in leaves], invocation=ref(i), raw=ref(raw), result=ref(c/'result.json'), closure_verified=True, job_verified=True)

AUDIT.mkdir(exist_ok=False)
completed=load(OUT/'execute.completed.json')
check(load(LAUNCH/'execute.outer.json')['actual_native_exit']==0, 'OUTER')
check(not (OUT/'execute.stopped.json').exists(), 'STOPPED')
new=[case(OUT,i) for i in range(44)]
old=[case(OLD,i) for i in range(3)]
check(sum(x['actual_leaf_count'] for x in new)==145 and sum(x['actual_leaf_count'] for x in old)==76,'COUNTS')
check([x['original_index'] for x in new]==list(range(3,47)), 'ORIGINAL_INDEX')
check(len({leaf for x in old+new for leaf in x['leaves']})==221,'UNIQUE_LEAVES')
frozen=load(OUT/'execution.inputs.before-first-case.json')
check(load(OUT/'inputs.after-all.json')==frozen, 'FINAL_INPUTS')
current=[ref(x['path']) for x in frozen]
check(current==frozen,'CURRENT_DRIFT')
current_ref=save('current.inputs.json',current)
dbs=[]
for p in sorted((OUT/'cases').rglob('*.independent-alltables.json')):
    d=load(p); original=d['closed_database']; actual=ref(original['path'])
    check(actual==original,'DB_CHANGED:'+str(p))
    dbs.append(dict(database=actual,alltables=ref(p)))
matrix=save('typed_case_union.json',dict(original_complete_76=old,new_complete_145=new,unique_leaf_pass=221,unique_leaf_fail=0,unique_leaf_skip=0,cohorts_distinct=True,retained_extra_native_pass_leaves=2,retained_prior_controller_failure=1,not_single_run_221=True))
db_ref=save('closed_fixture_refs.json',dbs)
failure=save('failure_origins.json',dict(new_origins=[],old_controller_origin='CLI47-r308-execute-4d65b6-2caf3a',old_origin_already_registered=True))
review=save('review.json',dict(schema='researchos.cli44-independent-execution-review.v1', reviewer='codex:/root/w05_merge_review',decision='BOUNDED_CLI44_REPLAY_COMPLETED_SOURCE_ACCEPTANCE_WITHHELD',candidate='b98738ac093ea55bb8700cfa724ddd9e6b2a1251',at=datetime.now(timezone.utc).isoformat(),new_selector_processes=44,new_leaf_pass=145,new_leaf_fail=0,new_leaf_skip=0,original_qualified_selectors=3,original_qualified_leaves=76,unique_selector_union=47,unique_leaf_union=221,actual_native_selector_processes_across_attempts=49,actual_pass_leaves_across_attempts=223,prior_controller_failure_preserved=1,new_controller_exit=0,new_primary_compile_count=0,input_count=len(frozen),input_drift=0,current_inputs=current_ref,case_union=matrix,closed_public_fixture_count=len(dbs),closed_fixtures=db_ref,failure_origins=failure,execution_completed=ref(OUT/'execute.completed.json'),outer=ref(LAUNCH/'execute.outer.json'),effects=dict(SDK_Node_worker_model_external_provider_paid_calls=0,loopback_HTTP_request_count=None,loopback_count_limitation='No aggregate request instrumentation; actual fixture records and method controls retained.'),source_acceptance=False,Main_integration=False,formal_increment=0,held=['existing2 nonnull session.list500 in this pinned base','P01-03 actual API layer gap','P02','actual attach durable completion','fullharness','Main integration','parent/formal']))
entries=[]
for base in (OUT,LAUNCH,AUDIT):
    for p in sorted(base.rglob('*')):
        if p.is_file(): entries.append(ref(p))
manifest=save('manifest.json',dict(schema='researchos.receipt-manifest.v1',entries=entries,count=len(entries),includes_self=False))
handoff=save('handoff.json',dict(review=review,manifest=manifest,current_inputs=current_ref,case_union=matrix,closed_fixtures=db_ref,failure_origins=failure,scope=ref(ROOT/'execution/v2.4/receipts/W05/W05-99/integration_codex/closure-and-finite-continuation-r309/cli_continuation_scope.v2.json'),source_acceptance=False,actual_registration_executed=False))
print(json.dumps(dict(namespace=str(AUDIT),review=review,manifest=manifest,handoff=handoff),ensure_ascii=False))
